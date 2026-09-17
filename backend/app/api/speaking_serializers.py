from app.core.config import settings
from app.db.base import utcnow

SPEAKING_GRADING_FIELDS = (
    "id",
    "estimated_level",
    "summary_vi",
    "strengths",
    "priority_improvements",
    "pronunciation_feedback",
    "fluency_feedback",
    "structure_feedback",
    "content_feedback",
    "vocabulary_suggestions",
    "sentence_corrections",
    "answer_feedback",
    "speaking_frame",
    "corrected_transcript",
    "improved_b2_answer",
    "audio_coverage",
    "ai_model",
    "audio_model",
    "transcription_model",
    "prompt_version",
    "created_at",
)


def speaking_question_view(question):
    fields = (
        "id",
        "part",
        "question_type",
        "topic",
        "question_text",
        "topic_sets",
        "situation",
        "options",
        "suggested_ideas",
        "follow_up_questions",
        "difficulty",
        "source",
    )
    return {**{key: getattr(question, key) for key in fields}, "allow_own_idea": question.part == 3}


def speaking_grading_view(grading):
    if not grading:
        return None
    return {
        **{key: getattr(grading, key) for key in SPEAKING_GRADING_FIELDS},
        "scores": {
            key: getattr(grading, f"{key}_score")
            for key in ("grammar", "vocabulary", "pronunciation", "fluency", "structures", "overall")
        },
        "errors": [
            {
                key: getattr(e, key)
                for key in (
                    "id",
                    "sequence_number",
                    "category",
                    "subtype",
                    "original",
                    "corrected",
                    "explanation_vi",
                    "severity",
                    "confidence",
                )
            }
            for e in grading.errors
        ],
    }


def speaking_answer_view(answer, review: bool):
    return {
        **{
            key: getattr(answer, key)
            for key in (
                "id",
                "session_id",
                "part",
                "question_text",
                "sequence_number",
                "status",
                "audio_duration_ms",
                "mime_type",
                "audio_size",
                "submitted_at",
            )
        },
        "has_audio": bool(answer.audio_path),
        "audio_url": f"/api/v1/speaking/answers/{answer.id}/audio" if review and answer.audio_path else None,
        "transcript": answer.transcript if review else None,
        "word_count": answer.word_count if review else None,
        "metrics": answer.metrics if review else {},
        "audio_analysis": {
            "available": answer.audio_analysis.get("available", False),
            "reason_vi": answer.audio_analysis.get("reason_vi"),
        }
        if review and answer.audio_analysis
        else None,
        "grading": speaking_grading_view(answer.grading) if review else None,
    }


def speaking_session_view(session):
    review = session.mode != "FULL_TEST" or session.status != "IN_PROGRESS"
    current = session.current_sequence
    visible = session.question_set if session.status != "IN_PROGRESS" else session.question_set[: current + 1]
    return {
        **{
            key: getattr(session, key)
            for key in (
                "id",
                "mode",
                "started_at",
                "completed_at",
                "status",
                "current_part",
                "current_sequence",
            )
        },
        "server_now": utcnow(),
        "suggested_duration_seconds": 720 if session.mode == "FULL_TEST" else None,
        "total_questions": len(session.question_set),
        "current_question": session.question_set[current] if current < len(session.question_set) else None,
        "visible_questions": visible,
        "answers": [speaking_answer_view(a, review) for a in session.answers],
        "grading": speaking_grading_view(session.grading) if session.status != "IN_PROGRESS" else None,
        "limits": {
            "max_audio_mb": settings.max_speaking_audio_mb,
            "max_audio_seconds": settings.max_speaking_audio_seconds,
        },
        "audio_analysis_configured": bool(settings.openai_speaking_audio_model),
        "tts_configured": bool(settings.openai_tts_model and settings.openai_api_key),
    }
