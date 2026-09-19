"""One operation registry for routes, cache identities and observability."""

from dataclasses import dataclass

from app.core.config import settings

ROUTES = {
    "generate_question": ("question_generation", "generation", 5000),
    "speaking_question": ("question_generation", "generation", 6000),
    "reading_generate": ("reading_generation", "generation", 16000),
    "question_quality": ("question_quality", "generation", 7000),
    "question_import": ("import", "imports", 28000),
    "writing_core": ("writing_analysis", "writing_grading", 7000),
    "writing_analysis": ("writing_analysis", "writing_grading", 7000),
    "writing_calibration": ("writing_scoring", "writing_grading", 5000),
    "writing_escalation": ("writing_escalation", "writing_grading", 9000),
    "writing_shadow": ("writing_escalation", "shadow", 9000),
    "writing_feedback": ("learning_coach", "writing_optional", 3500),
    "writing_corrections": ("writing_corrections", "writing_optional", 7000),
    "writing_sentences": ("writing_corrections", "writing_optional", 6000),
    "writing_corrected": ("writing_corrections", "writing_optional", 3000),
    "writing_improved": ("writing_corrections", "writing_optional", 3500),
    "improve_writing": ("writing_corrections", "writing_optional", 5000),
    "speaking_grade": ("speaking_text_grading", "speaking", 9000),
    "speaking_escalation": ("speaking_escalation", "speaking", 10000),
    "speaking_feedback": ("learning_coach", "speaking", 3000),
    "vocabulary_coach": ("vocabulary", "vocabulary", 5000),
    "vocabulary_usage": ("vocabulary", "vocabulary", 1500),
    "reading_vocabulary": ("vocabulary", "reading", 2000),
    "learning_lesson": ("learning_coach", "learning", 4500),
    "learning_exercises": ("exercise_generator", "learning", 8500),
    "learning_assess": ("learning_coach", "learning", 1800),
    "learning_feedback": ("learning_coach", "learning", 1800),
    "learning_weekly_summary": ("learning_coach", "learning", 2200),
}


@dataclass(frozen=True)
class ModelRoute:
    model: str
    reasoning_effort: str
    category: str
    max_output_tokens: int

    @property
    def identity(self):
        return f"{self.model}:{self.reasoning_effort}"


def route_for(operation: str) -> ModelRoute:
    role, category, limit = ROUTES.get(operation, ("default", "other", 5000))
    model = getattr(settings, f"openai_model_{role}")
    effort = settings.openai_reasoning_default
    if role in {"writing_analysis", "writing_scoring", "speaking_text_grading", "question_quality"}:
        effort = settings.openai_reasoning_grading
    if role in {"writing_analysis", "writing_scoring"}:
        effort = settings.openai_reasoning_writing
    if role.endswith("escalation"):
        effort = settings.openai_reasoning_escalation
    effort = settings.openai_reasoning_overrides.get(operation, effort)
    return ModelRoute(model, effort, category, limit)
