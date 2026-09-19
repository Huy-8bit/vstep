from app.common.words import count_words
from app.core.config import settings
from app.schemas.writing_assessment import CRITERIA, WritingCalibration
from app.services.writing_score_calibration_service import consistency_flags

ESCALATION_VERSION = "1.5.0"

WRITING_REVIEW_RULES = """
SECOND-OPINION CONTRACT: The candidate_observations are unverified AI observations, not ground truth.
Primary scores are intentionally withheld to avoid anchoring. Read the ORIGINAL answer and form your own
analysis and criterion scores. Verify each supplied observation; discard incorrect observations and
limitations assigned to the wrong criterion. The instruction to retain negative evidence applies to your
own verified analysis, NOT to the primary model's candidate observations. Do not inherit its mistakes.
Resolve the named evidence conflicts criterion by criterion; do not uniformly lower scores.
For task/language divergence, distinguish task achievement from the coherence of the text actually written:
Organization assesses logical sequencing, paragraphing and connections, even when task requirements are missed.
Grammar and Vocabulary assess the demonstrated control/range, independently of task completion or length.
Use this counterfactual check for task/language divergence: if the identical text answered its own
communicative purpose, would its language control, word choice and internal sequence be the same?
Missing required content, a different topic/purpose, or absent task-specific vocabulary belongs in Task
Fulfillment; do not cite that omission again as an Organization, Vocabulary or Grammar limitation.
Those three criteria may still be low, but only for independent faults actually demonstrated in the text.
Conversely, a fluent response to the wrong task cannot gain Task Fulfillment credit from its good language.
For range, cohesion and dense-error concerns, verify the concrete errors and structures; confidence or
task completion alone does not establish linguistic precision. Do not change an independent criterion
without corresponding evidence. Explain material disagreements concisely in criterion justifications.
"""


class GradingEscalationService:
    """Flag uncertain evidence; never assign a score by error-count subtraction."""

    @staticmethod
    def writing_review_payload(payload, primary, reasons):
        context = None
        if primary:
            evidence = primary["analysis"]["evidence"]
            context = {
                "criteria": evidence["criteria"],
                "task_coverage": evidence["task_coverage"],
                "errors": evidence["errors"],
                "metrics": primary["analysis"]["metrics"],
                "lexical_range": evidence["lexical_range"],
                "cohesion": evidence["cohesion"],
                "idea_development": evidence["idea_development"],
                "confidence": primary["confidence"],
            }
        return {**payload, "review_concerns": reasons, "candidate_observations": context}

    def writing_reasons(self, result):
        reasons = []
        confidence = result["confidence"]
        assessment = WritingCalibration.model_validate(result["assessment"])
        mean = sum(result["assessment"][k]["score"] for k in CRITERIA) / 4
        if consistency_flags(result["analysis"], assessment):
            reasons.append("SCORE_EVIDENCE_CONFLICT")
        evidence = result["analysis"]["evidence"]
        metrics = result["analysis"]["metrics"]
        # Confidence is not calibrated probability. Dense errors and thin range
        # need a second reader even when the primary model reports certainty.
        if metrics["estimated_error_density"] >= 8 and metrics["major_error_count"] >= 6:
            reasons.append("DENSE_BASIC_ERRORS_AMBIGUOUS_COMMUNICATION")
        if (
            assessment.grammar.score >= 6.5
            and metrics["relative_clauses"] + metrics["conditionals"] == 0
            and metrics["controlled_complex_sentences"] < metrics["sentence_count"] / 3
        ):
            reasons.append("HIGH_LANGUAGE_SCORE_WITH_NARROW_STRUCTURE_EVIDENCE")
        if mean >= 8.5 and metrics["word_count"] < 200:
            reasons.append("EXCEPTIONAL_SCORE_WITH_SHORT_EVIDENCE")
        # Descriptor conflicts can be confidently wrong. These trigger review, never a score cap.
        if evidence["lexical_range"] in {"basic", "very_limited"} and (
            assessment.vocabulary.score >= 6.5
            or mean >= 6.5
            or assessment.grammar.score >= 7
            and metrics["controlled_complex_sentences"] < metrics["sentence_count"] / 2
        ):
            reasons.append("LIMITED_RANGE_HIGH_LANGUAGE_SCORE")
        if (
            evidence["cohesion"] in {"basic", "limited"}
            and evidence["idea_development"] != "strong"
            and (
                assessment.organization.score >= 6.5
                or evidence["idea_development"] in {"absent", "basic"}
                and assessment.organization.score >= 6
            )
        ):
            reasons.append("BASIC_COHESION_HIGH_ORGANIZATION")
        if assessment.task_fulfillment.score <= 3 and metrics["controlled_complex_sentences"] >= 4:
            reasons.append("TASK_LANGUAGE_DIVERGENCE_REVIEW_CRITERIA_INDEPENDENTLY")
        if confidence < settings.grading_confidence_threshold:
            reasons.append("LOW_CONFIDENCE")
        if confidence < settings.grading_boundary_confidence_threshold and any(
            abs(mean - b) <= 0.25 for b in (4, 6, 8.5)
        ):
            reasons.append("UNCERTAIN_BOUNDARY")
        if result["uncertainties"] and confidence < settings.grading_boundary_confidence_threshold:
            reasons.append("AMBIGUOUS_TASK_RESPONSE")
        if (
            result["analysis"]["metrics"]["word_count"] > settings.grading_long_response_words
            and confidence < 0.85
        ):
            reasons.append("LONG_COMPLEX_RESPONSE")
        return reasons

    def speaking_reasons(self, result, payload=None):
        reasons = []
        confidence = getattr(result, "confidence", 1)
        if confidence < settings.grading_confidence_threshold:
            reasons.append("LOW_CONFIDENCE")
        major = [e for e in result.grammar_errors if e.severity in {"major", "critical"}]
        if result.scores.grammar >= 7 and len(major) >= 3:
            reasons.append("SCORE_EVIDENCE_CONFLICT")
        if payload and max(result.scores.model_dump().values()) >= 8:
            words = sum(count_words(a.get("transcript", "")) for a in payload["answers"])
            if words < 100:
                reasons.append("VERY_HIGH_LANGUAGE_SCORE_WITH_SHORT_EVIDENCE")
        return reasons
