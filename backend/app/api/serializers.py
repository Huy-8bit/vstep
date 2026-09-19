from app.api.library_metadata import library_metadata
from app.db.base import utcnow
from app.prompts.writing_analysis import WRITING_GRADER_VERSION
from app.vstep_reference.scoring_reference import writing_reference_level


def question_view(q):
    view = {
        key: getattr(q, key)
        for key in (
            "id",
            "task_type",
            "question_type",
            "topic",
            "test_profile",
            "instruction",
            "stimulus",
            "response_instruction",
            "genre",
            "register",
            "recipient_relationship",
            "purpose",
            "minimum_words",
            "source",
            "created_at",
        )
    }

    view["requirements"] = q.requirements if not q.stimulus or q.owner_id else []
    view.update(library_metadata(q))
    view["presentation"] = q.presentation or {}
    return view


def grading_view(g):
    if not g:
        return None
    return {
        "id": g.id,
        "current_grader_version": WRITING_GRADER_VERSION,
        "calibration_version": g.calibration_prompt_version,
        "scores": {
            key: getattr(g, f"{key}_score")
            for key in (
                "task_fulfillment",
                "organization",
                "vocabulary",
                "grammar",
                "overall",
            )
        },
        **{
            key: getattr(g, key)
            for key in (
                "summary_vi",
                "strengths",
                "priority_improvements",
                "structure_feedback",
                "task_fulfillment_feedback",
                "vocabulary_suggestions",
                "sentence_feedback",
                "corrected_version",
                "improved_b2_version",
                "ai_model",
                "prompt_version",
                "grader_version",
                "analysis_prompt_version",
                "calibration_prompt_version",
                "criterion_evidence",
                "analysis_snapshot",
                "created_at",
            )
        },
        "errors": [
            {
                "id": e.id,
                "category": e.category,
                "subtype": e.subtype,
                "original": e.original_text,
                "corrected": e.corrected_text,
                "explanation_vi": e.explanation_vi,
                "severity": e.severity,
            }
            for e in g.errors
        ],
    }


def attempt_view(a):
    return {
        **{
            key: getattr(a, key)
            for key in (
                "id",
                "exam_session_id",
                "task_type",
                "answer",
                "word_count",
                "revision",
                "started_at",
                "submitted_at",
                "duration_seconds",
                "status",
                "created_at",
                "updated_at",
            )
        },
        "question": question_view(a.question),
        "grading": grading_view(a.grading),
    }


def exam_view(e):
    grades = {a.task_type: a.grading.overall_score for a in e.attempts if a.grading}
    overall = (
        (grades[1] + grades[2] * 2) / 3 if e.mode == "FULL_TEST" and 1 in grades and 2 in grades else None
    )
    return {
        **library_metadata(e),
        **{
            key: getattr(e, key)
            for key in (
                "id",
                "mode",
                "test_profile",
                "started_at",
                "expires_at",
                "submitted_at",
                "status",
            )
        },
        "server_now": utcnow(),
        "overall_score": overall,
        "writing_reference_level": writing_reference_level(overall),
        "attempts": [attempt_view(a) for a in e.attempts],
    }
