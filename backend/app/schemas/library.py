"""Import schemas intentionally accept incomplete drafts, unlike generated-question validators."""

from typing import Literal

from pydantic import Field, field_validator, model_validator

from app.schemas.writing import StrictModel

Skill = Literal["writing", "speaking", "reading"]
KeySource = Literal["provided", "user_confirmed", "ai_suggested", "unknown"]


class LibraryWriting(StrictModel):
    task_type: Literal[1, 2]
    instruction: str = Field(default="", max_length=20000)
    stimulus_type: Literal[
        "letter", "email", "announcement", "situation", "request", "invitation", "complaint", "other"
    ] = "other"
    stimulus_text: str = Field(default="", max_length=20000)
    requirements: list[str] = Field(default_factory=list, max_length=30)
    minimum_words: int | None = Field(default=None, ge=1, le=5000)
    essay_family: str = Field(default="other", max_length=50)


class LibraryTopic(StrictModel):
    topic: str = Field(default="", max_length=300)
    questions: list[str] = Field(default_factory=list, max_length=15)


class LibrarySpeaking(StrictModel):
    part: Literal[1, 2, 3]
    topic: str = Field(default="", max_length=300)
    topic_sets: list[LibraryTopic] = Field(default_factory=list, max_length=6)
    situation: str = Field(default="", max_length=15000)
    options: list[str] = Field(default_factory=list, max_length=3)
    candidate_task: str = Field(default="", max_length=10000)
    optional_context: str = Field(default="", max_length=10000)
    central_idea: str = Field(default="", max_length=10000)
    suggested_ideas: list[str] = Field(default_factory=list, max_length=15)
    follow_up_questions: list[str] = Field(default_factory=list, max_length=15)


class LibraryOptions(StrictModel):
    A: str = Field(default="", max_length=5000)
    B: str = Field(default="", max_length=5000)
    C: str = Field(default="", max_length=5000)
    D: str = Field(default="", max_length=5000)


class LibraryReadingQuestion(StrictModel):
    question_number: int = Field(ge=1, le=200)
    question_text: str = Field(default="", max_length=10000)
    question_type: str = Field(default="other", max_length=40)
    options: LibraryOptions = Field(default_factory=LibraryOptions)
    correct_answer: Literal["A", "B", "C", "D"] | None = None
    answer_key_source: KeySource = "unknown"
    answer_key_evidence: str | None = Field(default=None, max_length=2000)
    explanation: str | None = Field(default=None, max_length=10000)

    @model_validator(mode="after")
    def key_consistent(self):
        if self.correct_answer is None:
            self.answer_key_source = "unknown"
        elif self.answer_key_source == "unknown":
            # An unconfirmed value cannot accidentally become a trusted key.
            self.correct_answer = None
        return self


class LibraryReadingPassage(StrictModel):
    title: str = Field(default="", max_length=300)
    passage_text: str = Field(default="", max_length=60000)
    questions: list[LibraryReadingQuestion] = Field(default_factory=list, max_length=40)

    @model_validator(mode="after")
    def unique_numbers(self):
        numbers = [q.question_number for q in self.questions]
        if len(numbers) != len(set(numbers)):
            raise ValueError("Số câu hỏi trong một bài đọc phải khác nhau.")
        return self


class LibraryContent(StrictModel):
    practice_asset_ids: list[str] = Field(default_factory=list, max_length=10)
    writing: list[LibraryWriting] = Field(default_factory=list, max_length=2)
    speaking: list[LibrarySpeaking] = Field(default_factory=list, max_length=3)
    reading: list[LibraryReadingPassage] = Field(default_factory=list, max_length=4)


class LibraryDocument(StrictModel):
    title: str = Field(min_length=1, max_length=300)
    skill: Skill
    part: Literal["task_1", "task_2", "part_1", "part_2", "part_3", "passage", "mini", "full"]
    topic: str = Field(default="other", min_length=1, max_length=40)
    tags: list[str] = Field(default_factory=list, max_length=20)
    favorite: bool = False
    collection_id: str | None = None
    source_type: Literal["manual", "copied_text", "image", "pdf", "teacher", "website", "book", "other"] = (
        "manual"
    )
    source_name: str | None = Field(default=None, max_length=300)
    source_url: str | None = Field(default=None, max_length=2000)
    notes: str | None = Field(default=None, max_length=10000)
    asset_ids: list[str] = Field(default_factory=list, max_length=10)
    content: LibraryContent

    @field_validator("source_url")
    @classmethod
    def safe_url(cls, value):
        if value and not value.startswith(("https://", "http://")):
            raise ValueError("URL nguồn phải dùng https hoặc http.")
        return value or None

    @field_validator("tags")
    @classmethod
    def tags_valid(cls, value):
        if any(not t.strip() or len(t) > 60 for t in value):
            raise ValueError("Tag phải có 1–60 ký tự.")
        return list(dict.fromkeys(t.strip() for t in value))

    @model_validator(mode="after")
    def consistent(self):
        allowed = {
            "writing": {"task_1", "task_2", "full"},
            "speaking": {"part_1", "part_2", "part_3", "full"},
            "reading": {"passage", "mini", "full"},
        }
        if not set(self.content.practice_asset_ids).issubset(self.asset_ids):
            raise ValueError("Tệp hiển thị khi luyện phải thuộc các tệp nguồn của đề.")
        if self.part not in allowed[self.skill]:
            raise ValueError("Phần thi không khớp kỹ năng.")
        if any(getattr(self.content, skill) for skill in allowed if skill != self.skill):
            raise ValueError("Một đề chỉ chứa một kỹ năng.")
        if sum(len(p.questions) for p in self.content.reading) > 40:
            raise ValueError("Tối đa 40 câu Reading trong một đề.")
        return self


def practice_issues(document: LibraryDocument) -> list[str]:
    """Only require supplied content needed by the engine; missing reading keys are allowed."""
    issues = []
    if document.skill == "writing":
        expected = [1, 2] if document.part == "full" else [int(document.part[-1])]
        if [q.task_type for q in document.content.writing] != expected:
            issues.append("Bổ sung đúng các Writing task đã chọn, theo thứ tự Task 1 rồi Task 2.")
        if any(not q.instruction.strip() for q in document.content.writing):
            issues.append("Writing cần có yêu cầu đề bài.")
    elif document.skill == "speaking":
        expected = [1, 2, 3] if document.part == "full" else [int(document.part[-1])]
        if [q.part for q in document.content.speaking] != expected:
            issues.append("Bổ sung đúng các Speaking part đã chọn, theo thứ tự 1, 2, 3.")
        for q in document.content.speaking:
            if q.part == 1 and (
                not q.topic_sets
                or any(not t.questions or any(not v.strip() for v in t.questions) for t in q.topic_sets)
            ):
                issues.append("Speaking Part 1 cần ít nhất một chủ đề có câu hỏi.")
            if q.part == 2 and (
                not q.situation.strip()
                or len(q.options) != 3
                or any(not v.strip() for v in q.options)
                or not q.candidate_task.strip()
            ):
                issues.append("Speaking Part 2 cần tình huống, đủ 3 lựa chọn và yêu cầu cho thí sinh.")
            if q.part == 3 and not q.central_idea.strip():
                issues.append("Speaking Part 3 cần có ý chính.")
    else:
        passages = document.content.reading
        if not passages or any(not p.passage_text.strip() or not p.questions for p in passages):
            issues.append("Reading cần bài đọc và ít nhất một câu hỏi.")
        if document.part == "passage" and len(passages) != 1:
            issues.append("Luyện một passage cần đúng một bài đọc; chọn Mini để gộp nhiều bài.")
        if document.part == "full" and (len(passages) != 4 or sum(len(p.questions) for p in passages) != 40):
            issues.append("Full Reading cần 4 bài đọc và tổng cộng 40 câu hỏi.")
        if any(
            not q.question_text.strip() or any(not v.strip() for v in q.options.model_dump().values())
            for p in passages
            for q in p.questions
        ):
            issues.append("Mỗi câu Reading cần nội dung câu hỏi và đủ lựa chọn A–D.")
    return issues


class LibrarySave(StrictModel):
    document: LibraryDocument
    expected_revision: int | None = None
    save_duplicate: bool = False


class LibraryPractice(StrictModel):
    revision: int | None = Field(default=None, ge=1)
    timed: bool = False


class LibraryOrganize(StrictModel):
    @field_validator("favorite", "tags")
    @classmethod
    def non_null_changes(cls, value):
        if value is None:
            raise ValueError("Favorite và tags không nhận null.")
        return value

    @field_validator("tags")
    @classmethod
    def valid_tags(cls, value):
        return LibraryDocument.tags_valid(value)

    favorite: bool | None = None
    tags: list[str] | None = Field(default=None, max_length=20)
    collection_id: str | None = None


class CollectionCreate(StrictModel):
    name: str = Field(min_length=1, max_length=120)


class ParseRequest(StrictModel):
    text: str | None = Field(default=None, min_length=10, max_length=160000)
    asset_id: str | None = None

    @model_validator(mode="after")
    def one_source(self):
        if bool(self.text) == bool(self.asset_id):
            raise ValueError("Cung cấp văn bản hoặc một tệp.")
        return self


class ParsedItem(StrictModel):
    title: str
    skill: Skill
    part: Literal["task_1", "task_2", "part_1", "part_2", "part_3", "passage", "mini", "full"]
    topic: str
    tags: list[str]
    content: LibraryContent
    skill_confidence: float = Field(ge=0, le=1)
    part_confidence: float = Field(ge=0, le=1)
    answer_key_confidence: float | None = Field(default=None, ge=0, le=1)
    warnings: list[str]


class ParsedImport(StrictModel):
    items: list[ParsedItem] = Field(max_length=12)
    warnings: list[str]
