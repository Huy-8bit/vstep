from statistics import mean

from app.core.config import settings
from app.schemas.audio_assessment import AUDIO_SCORE_FIELDS
from app.schemas.speaking import SpeakingGradingOutput


class SpeakingCorrectionService:
    """Text owns language feedback; validated audio owns every acoustic score."""

    def finalize(self, text_result, answers: list[dict]):
        recorded = [a for a in answers if a["audio_hash"]]
        threshold = settings.audio_feedback_min_confidence
        covered = [a for a in recorded if a["audio_analysis"].get("available")]

        def aggregate(field):
            values = [a["audio_analysis"].get(field) for a in recorded]
            if not values or any(v is None for v in values):
                return None
            # Equal recording contribution; no invented VSTEP part weights.
            return round(mean(values) * 2) / 2

        subscores = {field: aggregate(field) for field in AUDIO_SCORE_FIELDS}
        pronunciation, fluency = subscores["pronunciation_score"], subscores["fluency_score"]
        data = text_result.model_dump()
        data["scores"].update(pronunciation=pronunciation, fluency=fluency, overall=None)
        for key in ("pronunciation", "fluency"):
            data[f"{key}_confidence"] = min(
                (a["audio_analysis"].get(f"{key}_confidence", 0) for a in recorded), default=0
            )
        data["pronunciation_feedback"] = []
        data["fluency_feedback"] = []
        data["other_errors"] = [
            e for e in data["other_errors"] if e["category"] not in {"pronunciation", "fluency"}
        ]
        for answer in covered:
            audio = answer["audio_analysis"]
            sequence = answer["sequence_number"]
            if audio.get("fluency_summary_vi"):
                data["fluency_feedback"].append(
                    {
                        "title_vi": f"Câu {sequence + 1}",
                        "explanation_vi": audio["fluency_summary_vi"],
                        "example": "",
                    }
                )
            for issue in audio.get("issues", []):
                if issue["confidence"] < threshold:
                    continue
                category = "fluency" if issue["type"] in {"rhythm", "hesitation"} else "pronunciation"
                data["other_errors"].append(
                    {
                        "sequence_number": sequence,
                        "category": category,
                        "subtype": issue["type"],
                        "original": issue["target"],
                        "corrected": "",
                        "explanation_vi": issue["description_vi"],
                        "severity": "minor",
                        "confidence": issue["confidence"],
                    }
                )
                if category == "pronunciation":
                    data["pronunciation_feedback"].append(
                        {
                            "sequence_number": sequence,
                            "word": issue["target"],
                            "issue": "individual_sound"
                            if issue["type"] == "word_pronunciation"
                            else issue["type"],
                            "feedback_vi": issue["description_vi"],
                            "ipa": None,
                            "suggestion": issue["suggestion_vi"],
                            "confidence": issue["confidence"],
                        }
                    )
        if fluency is None:
            data["fluency_feedback"].append(
                {
                    "title_vi": "Chưa đủ bằng chứng âm thanh",
                    "explanation_vi": "Chưa đủ audio đáng tin cậy để chấm độ trôi chảy cho toàn bộ bản ghi.",
                    "example": "",
                }
            )
        for correction in data["sentence_corrections"]:
            correction["start_seconds"] = None
        if pronunciation is not None and fluency is not None:
            data["scores"]["overall"] = (
                sum(
                    data["scores"][key]
                    for key in ("grammar", "vocabulary", "structures", "pronunciation", "fluency")
                )
                / 5
            )
        result = SpeakingGradingOutput.model_validate(data)
        coverage = {
            "recordings": len(recorded),
            "analyzed": len(covered),
            "complete": result.scores.overall is not None,
            "pronunciation_confidence": result.pronunciation_confidence,
            "fluency_confidence": result.fluency_confidence,
            "subscores": subscores,
            "aggregation": "Mean of recording scores, rounded to 0.5; all recorded answers must have reliable audio scores.",
            "schema_version": "2.0.0",
        }
        return result, coverage


def speaking_level(score: float | None) -> str:
    if score is None:
        return "Chưa đủ dữ liệu"
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
