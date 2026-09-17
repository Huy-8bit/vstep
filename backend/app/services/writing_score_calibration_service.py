from app.schemas.writing_assessment import CRITERIA, WritingCalibration


def consistency_flags(analysis, result):
    evidence, metrics = analysis["evidence"], analysis["metrics"]
    flags = []
    if result.grammar.score >= 7 and (
        metrics["major_error_count"] >= 2 or not metrics["controlled_complex_sentences"]
    ):
        flags.append(
            "Grammar 7+: reconcile detected basic errors and demonstrated range/control, not understandability."
        )
    if result.vocabulary.score >= 7 and (
        evidence["lexical_range"] in {"basic", "very_limited"}
        or metrics["errors_by_primary_criterion"].get("vocabulary", 0) >= 2
    ):
        flags.append(
            "Vocabulary 7+: reconcile basic range or repeated lexical problems with precise positive evidence."
        )
    if result.task_fulfillment.score >= 7.5 and any(
        c["coverage"] in {"missing", "mentioned"} for c in evidence["task_coverage"]
    ):
        flags.append(
            "Task Fulfillment 7.5+: mere mention/missing requirements cannot substitute for development."
        )
    if result.organization.score >= 7.5 and evidence["cohesion"] in {"limited", "basic"}:
        flags.append(
            "Organization 7.5+: reconcile limited/basic cohesion; paragraphs alone do not justify this score."
        )
    return flags


def validate_calibration(result, analysis):
    quotes = {
        e["quote"]
        for name in CRITERIA
        for key in ("positive_evidence", "negative_evidence")
        for e in analysis["evidence"]["criteria"][name][key]
    }
    for name in CRITERIA:
        criterion = getattr(result, name)
        required_negatives = {e["quote"] for e in analysis["evidence"]["criteria"][name]["negative_evidence"]}
        if not required_negatives.issubset({e.quote for e in criterion.negative_evidence}):
            raise ValueError("Calibration must retain the observed negative evidence for each criterion")
        for item in [*criterion.positive_evidence, *criterion.negative_evidence]:
            if item.quote and item.quote not in quotes:
                raise ValueError(
                    "Calibration may only cite supplied original evidence, never anchors or corrected text"
                )


class WritingScoreCalibrationService:
    def __init__(self, llm):
        self.llm = llm

    async def calibrate(self, analysis, user_id, previous=None):
        payload = {"structured_analysis": analysis}
        if previous:
            payload.update(
                previous_assessment=previous,
                consistency_flags=consistency_flags(analysis, WritingCalibration.model_validate(previous)),
            )
        result = await self.llm.calibrate_writing(payload, user_id)
        validate_calibration(result, analysis)
        flags = consistency_flags(analysis, result)
        return {
            "assessment": result.model_dump(),
            "consistency_flags": flags,
            "reviewed": bool(previous) or not flags,
        }
