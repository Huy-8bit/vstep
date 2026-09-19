from app.prompts.task1_grader import TASK1_ANALYSIS_CONTEXT
from app.prompts.task2_grader import TASK2_ANALYSIS_CONTEXT
from app.prompts.writing_core import WRITING_CORE_PROMPT
from app.schemas.writing_assessment import CRITERIA, WritingAnalysis, WritingCalibration
from app.schemas.writing_core import WritingCoreOutput
from app.services.grading_escalation_service import WRITING_REVIEW_RULES
from app.services.writing_analysis_service import (
    WritingEvidenceAnalysisService,
    sentence_segments,
    validate_analysis,
)


def source_analysis(result, payload):
    sentences = {s["sentence_id"]: s["text"] for s in payload["sentences"]}
    data = result.analysis.model_dump()

    def evidence(item):
        identifier = item["sentence_id"]
        if identifier is not None and identifier not in sentences:
            raise ValueError("Evidence sentence_id must occur in the supplied original sentences")
        return {
            "quote": sentences[identifier] if identifier else "",
            "explanation_vi": item["explanation_vi"],
        }

    for c in data["criteria"].values():
        for key in ("positive_evidence", "negative_evidence"):
            c[key] = [evidence(e) for e in c[key]]
    for coverage in data["task_coverage"]:
        coverage["evidence"] = [evidence(e) for e in coverage["evidence"]]
    for error in data["errors"]:
        if error["original"] and error["original"] not in sentences.get(error["sentence_id"], ""):
            matches = [k for k, v in sentences.items() if error["original"] in v]
            if len(matches) == 1:
                error["sentence_id"] = matches[0]
    return WritingAnalysis.model_validate(data)


def core_assessment(result, analysis):
    assessment = {}
    for name in CRITERIA:
        score = getattr(result.scores, name)
        assessment[name] = {
            **getattr(analysis.criteria, name).model_dump(),
            "initial_score": score.score,
            "score": score.score,
            "score_justification_vi": score.justification_vi,
            "consistency_review_vi": score.justification_vi,
            "high_score_justification_vi": score.justification_vi if score.score >= 7 else "",
        }
    return WritingCalibration(**assessment, calibration_summary_vi=result.summary_vi).model_dump()


class WritingCoreService:
    def __init__(self, llm):
        self.llm = llm

    async def analyze(self, payload, user_id, operation="writing_core"):
        payload = {**payload, "sentences": sentence_segments(payload["user_answer"])}

        def validate(result):
            analysis = source_analysis(result, payload)
            validate_analysis(analysis, payload)
            core_assessment(result, analysis)

        result = await self.llm._structured(
            WritingCoreOutput,
            WRITING_CORE_PROMPT
            + "\n"
            + (TASK1_ANALYSIS_CONTEXT if payload["task"] == 1 else TASK2_ANALYSIS_CONTEXT)
            + (WRITING_REVIEW_RULES if operation == "writing_escalation" else ""),
            payload,
            user_id,
            operation,
            validate,
        )
        original_analysis = source_analysis(result, payload)
        analysis = WritingEvidenceAnalysisService.aggregate(original_analysis, payload)
        return {
            "analysis": analysis,
            "assessment": core_assessment(result, original_analysis),
            "confidence": result.confidence,
            "uncertainties": result.uncertainties,
            "feedback": {
                "summary_vi": result.summary_vi,
                "priority_improvements": [i.model_dump() for i in result.top_improvements],
                "strengths": [
                    c["positive_evidence"][0]["explanation_vi"]
                    for c in analysis["evidence"]["criteria"].values()
                    if c["positive_evidence"]
                ][:3],
                "structure_feedback": [
                    {
                        "title_vi": "Bố cục và phát triển ý",
                        "explanation_vi": analysis["evidence"]["criteria"]["organization"]["assessment_vi"],
                        "example": "",
                    }
                ],
                "task_fulfillment_feedback": [
                    {
                        "title_vi": "Đáp ứng yêu cầu",
                        "explanation_vi": analysis["evidence"]["criteria"]["task_fulfillment"][
                            "assessment_vi"
                        ],
                        "example": "",
                    }
                ],
                "vocabulary_suggestions": [],
            },
        }
