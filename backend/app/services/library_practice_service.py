"""Resolve a private revision to normal skill questions, then delegate to existing engines."""

import hashlib

from sqlalchemy import select

from app.common.errors import AppError
from app.common.words import count_words
from app.models import WritingQuestion
from app.models.reading import ReadingPassage, ReadingQuestion
from app.models.speaking import SpeakingQuestion
from app.repositories.library import QuestionRepository
from app.schemas.api import ExamCreate
from app.schemas.library import practice_issues
from app.schemas.reading import ReadingSessionCreate
from app.schemas.speaking import SpeakingSessionCreate
from app.services.exam_service import ExamService
from app.services.reading_exam_service import ReadingExamService
from app.services.speaking_exam_service import SpeakingExamService


def snapshot_fields(row, revision, doc, index):
    return dict(
        owner_id=row.user_id,
        library_question_id=row.id,
        library_revision=revision,
        library_title=doc.title,
        topic=doc.topic,
        test_profile="VSTEP_3_5",
        source="CUSTOM",
        fingerprint=hashlib.sha256(f"{row.id}:{revision}:{index}".encode()).hexdigest(),
        generation_diagnostics={"origin": "MANUAL" if doc.source_type == "manual" else "USER_IMPORTED"},
        presentation={"source_type": doc.source_type, "practice_asset_ids": doc.content.practice_asset_ids},
    )


class LibraryPracticeService:
    def __init__(self, db, llm):
        self.db, self.llm = db, llm

    async def start(self, question_id, data, user_id):
        repo = QuestionRepository(self.db, user_id)
        # This lock serializes materialization and concurrent edits; existing engines commit the transaction.
        row = await repo.get(question_id, lock=True, include_deleted=data.revision is not None)
        revision = data.revision or row.revision
        doc = await repo.revision(row, revision)
        issues = practice_issues(doc)
        if issues:
            raise AppError(422, " ".join(issues), "question_incomplete")
        meta = dict(library_question_id=row.id, library_revision=revision, library_title=doc.title)
        model = {"writing": WritingQuestion, "speaking": SpeakingQuestion, "reading": ReadingPassage}[
            doc.skill
        ]
        questions = list(
            await self.db.scalars(
                select(model)
                .where(
                    model.owner_id == user_id,
                    model.library_question_id == row.id,
                    model.library_revision == revision,
                )
                .order_by(model.created_at, model.id)
            )
        )
        if not questions:
            questions = self.materialize(row, revision, doc)
            self.db.add_all(questions)
            await self.db.flush()
        if doc.skill == "writing":
            session = await ExamService(self.db, self.llm).create(
                ExamCreate(
                    mode="FULL_TEST" if doc.part == "full" else f"TASK{doc.part[-1]}",
                    question_ids=[q.id for q in questions],
                    timed=data.timed,
                ),
                user_id,
                library=meta,
            )
            url = f"/exam/{session.id}"
        elif doc.skill == "speaking":
            session = await SpeakingExamService(self.db, self.llm, None).create(
                SpeakingSessionCreate(mode="FULL_TEST" if doc.part == "full" else f"PART{doc.part[-1]}"),
                user_id,
                resolved_questions=questions,
                library=meta,
            )
            url = f"/speaking/exam/{session.id}"
        else:
            questions.sort(key=lambda p: p.presentation["passage_index"])
            session = await ReadingExamService(self.db, self.llm).create(
                ReadingSessionCreate(
                    mode="FULL_TEST" if doc.part == "full" else "PASSAGE_PRACTICE", timed=data.timed
                ),
                user_id,
                selection=[(p, q) for p in questions for q in p.questions],
                library=meta,
            )
            url = f"/reading/exam/{session.id}"
        return {"id": session.id, "skill": doc.skill, "url": url, **meta}

    @staticmethod
    def materialize(row, revision, doc):
        questions = []
        for index, item in enumerate(getattr(doc.content, doc.skill)):
            fields = snapshot_fields(row, revision, doc, index)
            if doc.skill == "writing":
                fields["presentation"].update(
                    stimulus_type=item.stimulus_type, show_imported_requirements=True
                )
                question = WritingQuestion(
                    **fields,
                    task_type=item.task_type,
                    question_type=item.essay_family if item.task_type == 2 else item.stimulus_type,
                    instruction=item.instruction,
                    stimulus=item.stimulus_text or None,
                    response_instruction=None,
                    requirements=item.requirements,
                    minimum_words=item.minimum_words or (120 if item.task_type == 1 else 250),
                    genre=item.stimulus_type
                    if item.stimulus_type in ("letter", "email")
                    else ("essay" if item.task_type == 2 else None),
                )
            elif doc.skill == "speaking":
                fields["presentation"].update(optional_context=item.optional_context, topic_title=item.topic)
                question = SpeakingQuestion(
                    **fields,
                    part=item.part,
                    question_type={1: "social_interaction", 2: "solution_discussion", 3: "topic_development"}[
                        item.part
                    ],
                    question_text=item.candidate_task
                    if item.part == 2
                    else item.central_idea
                    if item.part == 3
                    else item.topic,
                    topic_sets=[t.model_dump() for t in item.topic_sets],
                    situation=item.situation or None,
                    options=item.options,
                    suggested_ideas=item.suggested_ideas,
                    follow_up_questions=item.follow_up_questions,
                )
            else:
                fields["presentation"].update(
                    passage_index=index, source_question_numbers=[q.question_number for q in item.questions]
                )
                question = ReadingPassage(
                    **fields,
                    title=item.title or doc.title,
                    content=item.passage_text,
                    paragraphs=[
                        {"id": f"p{i + 1}", "text": text}
                        for i, text in enumerate(item.passage_text.split("\n\n"))
                        if text.strip()
                    ],
                    word_count=count_words(item.passage_text),
                    vocabulary_cache={},
                )
                question.questions = [
                    ReadingQuestion(
                        question_number=number + 1,
                        question_type={
                            "vocabulary_in_context": "vocabulary",
                            "NOT_TRUE": "negative_detail",
                            "multiple_choice": "other",
                        }.get(q.question_type, q.question_type),
                        question_text=q.question_text,
                        options=q.options.model_dump(),
                        correct_answer=q.correct_answer,
                        answer_key_source=q.answer_key_source,
                        explanation_vi=q.explanation,
                        option_explanations={},
                        evidence=None,
                    )
                    for number, q in enumerate(item.questions)
                ]
            questions.append(question)
        return questions
