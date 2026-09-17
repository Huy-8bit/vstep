WRITING_CRITERIA = ("task_fulfillment", "organization", "vocabulary", "grammar")
SPEAKING_CRITERIA = ("grammar", "vocabulary", "pronunciation", "fluency", "structures")
SCORING_REFERENCE = {
    "label": "AI-estimated VSTEP-oriented practice score",
    "confidential_rubric_claim": False,
    "writing": {
        "criteria": WRITING_CRITERIA,
        "criterion_weight": 0.25,
        "score_step": 0.5,
        "full_formula": "(Task1 + 2 * Task2) / 3",
        "standalone_proficiency_level": False,
    },
    "speaking": {
        "criteria": SPEAKING_CRITERIA,
        "criterion_weight": 0.2,
        "audio_only": ["pronunciation", "fluency"],
    },
    "calibration": "Internal conservative evidence-based heuristics and editorial anchors; not certified examiner scoring.",
}


def writing_reference_level(score):
    # Only call for complete two-task Writing; this is a skill-level product reference.
    if score is None:
        return None
    return "C1" if score >= 8.5 else "B2" if score >= 6 else "B1" if score >= 4 else "Dưới B1"
