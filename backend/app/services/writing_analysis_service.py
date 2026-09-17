import re
from collections import Counter

from app.common.words import count_words
from app.schemas.writing_assessment import CRITERIA, WritingAnalysis


def sentence_segments(answer):
    # Keep original substrings/IDs, including short greeting/sign-off lines. Range summaries label these
    # as fragments rather than pretending this lightweight segmentation is a syntactic parser.
    return [
        {"sentence_id": i + 1, "text": value.strip()}
        for i, value in enumerate(
            part for part in re.split(r"(?<=[.!?])\s+|\n+", answer.strip()) if part.strip()
        )
    ]


def validate_analysis(result: WritingAnalysis, payload):
    sentences = {s["sentence_id"]: s["text"] for s in payload["sentences"]}
    if result.task != payload["task"] or sorted(s.sentence_id for s in result.sentences) != list(sentences):
        raise ValueError("Analysis must cover every original sentence exactly once")
    if len(result.task_coverage) < len(payload.get("requirements", [])):
        raise ValueError("Analysis must cover every task requirement")
    for item in [
        e
        for c in CRITERIA
        for e in [
            *getattr(result.criteria, c).positive_evidence,
            *getattr(result.criteria, c).negative_evidence,
        ]
    ] + [e for c in result.task_coverage for e in c.evidence]:
        if item.quote and item.quote not in payload["user_answer"]:
            raise ValueError("Invented original evidence")
    for error in result.errors:
        if not error.original or error.original not in sentences.get(error.sentence_id, ""):
            raise ValueError("Error does not quote the corresponding original sentence")


class WritingEvidenceAnalysisService:
    def __init__(self, llm):
        self.llm = llm

    async def analyze(self, payload, user_id):
        payload = {**payload, "sentences": sentence_segments(payload["user_answer"])}
        result = await self.llm.analyze_writing(payload, user_id)
        validate_analysis(result, payload)
        # Collapse overlapping descriptions of one local error. Detection is model-assisted; counting is Python.
        retained, occupied = [], {}
        severity = {"critical": 3, "major": 2, "minor": 1}
        for error in sorted(result.errors, key=lambda e: -severity[e.severity]):
            sentence = payload["sentences"][error.sentence_id - 1]["text"]
            start = sentence.find(error.original)
            end = start + len(error.original)
            spans = occupied.setdefault(error.sentence_id, [])
            if any(start < b and a < end for a, b in spans):
                continue
            spans.append((start, end))
            retained.append(error)
        result.errors = sorted(retained, key=lambda e: e.sentence_id)
        words = count_words(payload["user_answer"])
        structures = Counter(s.structure for s in result.sentences)
        severity_counts = Counter(e.severity for e in retained)
        primary = Counter(e.primary_criterion for e in retained)
        return {
            "evidence": result.model_dump(),
            "metrics": {
                "word_count": words,
                "sentence_count": len(payload["sentences"]),
                "number_of_detected_errors": len(retained),
                "major_error_count": severity_counts["major"] + severity_counts["critical"],
                "minor_error_count": severity_counts["minor"],
                "estimated_error_density": round(len(retained) / words * 100, 2) if words else 0,
                "errors_by_primary_criterion": dict(primary),
                "structures": dict(structures),
                "relative_clauses": sum(s.relative_clauses for s in result.sentences),
                "conditionals": sum(s.conditionals for s in result.sentences),
                "subordination": sum(s.subordination for s in result.sentences),
                "controlled_complex_sentences": sum(
                    s.structure in {"complex", "compound_complex"} and s.control == "controlled"
                    for s in result.sentences
                ),
                "note_vi": "Số lỗi/cấu trúc được tổng hợp từ phân tích AI đã đối chiếu trích dẫn. Mật độ tính trên 100 từ; không phải bộ dò lỗi hoàn hảo hay công thức trừ điểm. Số câu có thể gồm lời chào/kết thư.",
            },
        }


WritingAnalysisService = WritingEvidenceAnalysisService
