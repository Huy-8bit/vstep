from app.db.base import utcnow


def reading_question_view(question, number=None):
    # Explicit allowlist: answer keys, evidence, explanations and correctness never enter exam DTOs.
    return {
        "id": question.id,
        "passage_id": question.passage_id,
        "question_number": number or question.question_number,
        "question_type": question.question_type,
        "question_text": question.question_text,
        "options": question.options,
    }


def reading_passage_view(passage, selected_ids=None, numbers=None):
    return {
        **{
            key: getattr(passage, key)
            for key in ("id", "title", "topic", "difficulty", "paragraphs", "word_count", "source")
        },
        "questions": [
            reading_question_view(q, (numbers or {}).get(q.id))
            for q in passage.questions
            if selected_ids is None or q.id in selected_ids
        ],
    }


def reading_answer_view(answer):
    return {
        key: getattr(answer, key)
        for key in (
            "question_id",
            "selected_answer",
            "is_marked_for_review",
            "revision",
            "time_spent_seconds",
            "answered_at",
            "updated_at",
        )
    }


def reading_session_view(session, passages):
    return {
        **{
            key: getattr(session, key)
            for key in (
                "id",
                "mode",
                "difficulty",
                "topic",
                "started_at",
                "expires_at",
                "submitted_at",
                "status",
                "question_count",
                "question_ids",
            )
        },
        "server_now": utcnow(),
        "passages": [
            reading_passage_view(
                p, set(session.question_ids), {qid: i + 1 for i, qid in enumerate(session.question_ids)}
            )
            for p in passages
        ],
        "answers": [reading_answer_view(a) for a in session.answers],
    }


def reading_result_view(session, passages):
    result = session.result
    numbers = {qid: i + 1 for i, qid in enumerate(session.question_ids)}
    return {
        "session": reading_session_view(session, passages),
        "result": {
            key: getattr(result, key)
            for key in (
                "id",
                "correct_count",
                "incorrect_count",
                "unanswered_count",
                "accuracy",
                "score",
                "duration_seconds",
                "question_type_breakdown",
                "passage_breakdown",
                "strategy_feedback",
            )
        },
        "review": [
            {
                **reading_question_view(a.question, numbers[a.question_id]),
                **reading_answer_view(a),
                "is_correct": a.is_correct,
                "correct_answer": a.question.correct_answer,
                "explanation_vi": a.question.explanation_vi,
                "option_explanations": a.question.option_explanations,
                "evidence": a.question.evidence,
            }
            for a in sorted(session.answers, key=lambda a: numbers[a.question_id])
        ],
    }
