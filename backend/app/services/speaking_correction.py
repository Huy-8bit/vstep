from app.core.config import settings
from app.schemas.speaking import SpeakingGradingOutput


class SpeakingCorrectionService:
    """Apply evidence gates without making a second paid correction/grading call."""

    def finalize(self, result: SpeakingGradingOutput, answers: list[dict]):
        by_sequence = {a["sequence_number"]: a for a in answers}
        threshold = settings.pronunciation_confidence_threshold
        recorded = [a for a in answers if a["audio_hash"]]
        covered = {a["sequence_number"] for a in recorded if a["audio_analysis"].get("available")}
        all_covered = bool(recorded) and len(covered) == len(recorded)
        if not all_covered or result.pronunciation_confidence < threshold:
            result.scores.pronunciation = None
        if not all_covered or result.fluency_confidence < threshold:
            result.scores.fluency = None
        result.pronunciation_feedback = [
            p
            for p in result.pronunciation_feedback
            if p.sequence_number in covered and p.confidence >= threshold
        ]
        for p in result.pronunciation_feedback:
            if p.confidence < 0.9:
                p.ipa = None
        result.other_errors = [
            e
            for e in result.other_errors
            if e.category not in {"pronunciation", "fluency"}
            or (e.sequence_number in covered and e.confidence is not None and e.confidence >= threshold)
        ]
        # JSON transcription does not promise reliable word timestamps.
        for sentence in result.sentence_corrections:
            sentence.start_seconds = None
        result.vocabulary_suggestions = [
            v
            for v in result.vocabulary_suggestions
            if v.sequence_number in by_sequence and v.original in by_sequence[v.sequence_number]["transcript"]
        ]
        if not all_covered or result.fluency_confidence < threshold:
            result.fluency_feedback = [
                type(result.priority_improvements[0])(
                    title_vi="Chưa đủ bằng chứng âm thanh",
                    explanation_vi="Chưa thể đánh giá nhịp nói, ngập ngừng và phát âm cho toàn bộ bài. Số từ/phút chỉ là thông tin mô tả.",
                    example="",
                )
            ]
        scores = result.scores
        scores.overall = (
            (scores.grammar + scores.vocabulary + scores.pronunciation + scores.fluency + scores.structures)
            / 5
            if scores.pronunciation is not None and scores.fluency is not None
            else None
        )
        return {
            "recordings": len(recorded),
            "analyzed": len(covered),
            "complete": scores.overall is not None,
            "pronunciation_confidence": result.pronunciation_confidence,
            "fluency_confidence": result.fluency_confidence,
        }


def speaking_level(score: float | None) -> str:
    if score is None:
        return "Chưa đủ dữ liệu"
    # Resolve gaps in the product's half-point reference ranges by rounding for LEVEL ONLY.
    rounded = int(score * 2 + 0.5) / 2
    return (
        "C1 / Bậc 5"
        if rounded >= 8.5
        else "B2 / Bậc 4"
        if rounded >= 6
        else "B1 / Bậc 3"
        if rounded >= 4
        else "Chưa xét"
    )
