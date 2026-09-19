"""Pure, bounded extraction from immutable grader evidence. No LLM calls."""

import hashlib
import json
import re
from collections import Counter
from types import SimpleNamespace

from app.core.config import settings
from app.learning.taxonomy import normalize
from app.learning.taxonomy.reading import TYPES
from app.services.reading_scoring_service import trusted_key


def digest(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, ensure_ascii=False, default=str).encode()
    ).hexdigest()


def signal(
    category,
    concept,
    original=None,
    corrected=None,
    *,
    subcategory=None,
    severity="minor",
    confidence=0.8,
    outcome="ERROR",
    **details,
):
    return dict(
        category=category,
        subcategory=subcategory or concept,
        concept_key=concept,
        original_text=original,
        corrected_text=corrected,
        severity=severity,
        confidence=confidence,
        outcome=outcome,
        details=details,
    )


def error_signals(errors, text, *, speaking=False, sequence=None):
    found = []
    for e in errors:
        if speaking and e.sequence_number != sequence:
            continue
        if e.category.upper() in {"PRONUNCIATION", "FLUENCY"}:
            continue  # Audio evidence is processed separately, never transcript errors.
        original = e.original if speaking else e.original_text
        corrected = e.corrected if speaking else e.corrected_text
        if not original or original not in text:
            continue
        cat, sub, key = normalize(
            e.category, e.subtype, original, corrected, skill="SPEAKING" if speaking else "WRITING"
        )
        # An error without a reliable span is counted once, not at every identical substring.
        offset = text.find(original)
        found.append(
            signal(
                cat,
                key,
                original,
                corrected,
                subcategory=sub,
                severity=e.severity,
                confidence=(e.confidence if e.confidence is not None else 0.8) if speaking else 0.85,
                offset=offset,
                sentence_id=getattr(e, "sentence_id", None),
                sequence=sequence,
                explanation_vi=e.explanation_vi,
                evidence_kind="transcript" if speaking else "writing",
            )
        )
    return found


PHRASES = ("i think", "very important", "very good", "very bad")
STOPWORDS = set(
    "a an the i you he she it we they me my your his her its our their this that these those is am are was were be been being do does did have has had to of in on at for with as and or but so if because than then from by about into can could will would shall should may might must not no yes also there here which who what when where how all some any such more most much many very one two other people things just only".split()
)


def lexical_counts(text):
    words = re.findall(r"[a-z]+(?:'[a-z]+)?", text.casefold())
    counts = Counter(w for w in words if len(w) >= 4 and w not in STOPWORDS)
    counts = {word: n for word, n in counts.most_common(30) if n >= 2}
    for phrase in PHRASES:
        n = len(re.findall(r"\b" + re.escape(phrase) + r"\b", text, re.I))
        if n:
            counts[phrase] = n
    return counts


def writing_data(attempt):
    grading = attempt.grading
    evidence = (grading.analysis_snapshot or {}).get("evidence", {})
    located = [
        SimpleNamespace(**{**e, "original_text": e["original"], "corrected_text": e["corrected"]})
        for e in evidence.get("errors", [])
    ]
    signals = error_signals(located or grading.errors, attempt.answer)
    criteria = evidence.get("criteria", {})

    def structural(category, concept, explanation, quotes=None):
        quote = next(
            (q.get("quote") for q in (quotes or []) if q.get("quote") and q["quote"] in attempt.answer), None
        )
        signals.append(
            signal(category, concept, quote, explanation_vi=explanation, evidence_kind="grader_analysis")
        )

    if evidence.get("idea_development") in {"absent", "basic"}:
        structural(
            "IDEA_DEVELOPMENT",
            "BODY_IDEA_UNDERDEVELOPED",
            "Phân tích bài chấm ghi nhận ý chưa được triển khai đầy đủ.",
            criteria.get("task_fulfillment", {}).get("negative_evidence"),
        )
    if evidence.get("cohesion") == "limited":
        structural(
            "COHESION",
            "WEAK_COHESION",
            "Phân tích bài chấm ghi nhận liên kết ý còn hạn chế.",
            criteria.get("organization", {}).get("negative_evidence"),
        )
    missing = [v["requirement"] for v in evidence.get("task_coverage", []) if v.get("coverage") == "missing"]
    if missing:
        structural("TASK_FULFILLMENT", "TASK_REQUIREMENT_MISSING", "Chưa đáp ứng: " + "; ".join(missing))
    sentences = evidence.get("sentences", [])
    if len(sentences) >= 6 and sum(s.get("structure") == "simple" for s in sentences) / len(sentences) > 0.85:
        structural(
            "SENTENCE_VARIETY",
            "OVERUSE_SIMPLE_SENTENCE",
            "Hơn 85% cấu trúc trong phân tích bài này là câu đơn. Đây là gợi ý mở rộng cách diễn đạt, không phải mọi câu đơn đều sai.",
        )
    # Only map explicit negative feedback, never infer a weakness from a score alone.
    explicit = {
        "INTRODUCTION_TOO_GENERIC": ("mở bài còn chung chung", "generic introduction"),
        "THESIS_UNCLEAR": ("luận điểm chưa rõ", "unclear thesis"),
        "EXAMPLE_MISSING": ("thiếu ví dụ", "missing example"),
        "PARAGRAPH_LOGIC_WEAK": ("logic đoạn", "paragraph logic"),
        "CONCLUSION_REPETITIVE": ("kết luận lặp", "repetitive conclusion"),
        "REGISTER_MISMATCH": ("văn phong chưa phù hợp", "register mismatch"),
    }
    for item in [*(grading.structure_feedback or []), *(grading.task_fulfillment_feedback or [])]:
        content = (item.get("title_vi", "") + " " + item.get("explanation_vi", "")).casefold()
        for key, needles in explicit.items():
            if any(n in content for n in needles):
                structural(
                    "REGISTER" if key == "REGISTER_MISMATCH" else "ORGANIZATION",
                    key,
                    item.get("explanation_vi", ""),
                )
    positives = [
        q.get("quote", "")
        for criterion in criteria.values()
        if isinstance(criterion, dict)
        for q in criterion.get("positive_evidence", [])
    ]
    for category, concept, passed, criterion in (
        (
            "IDEA_DEVELOPMENT",
            "BODY_IDEA_UNDERDEVELOPED",
            evidence.get("idea_development") == "strong",
            "task_fulfillment",
        ),
        (
            "COHESION",
            "WEAK_COHESION",
            evidence.get("cohesion") in {"effective", "sophisticated"},
            "organization",
        ),
        (
            "TASK_FULFILLMENT",
            "TASK_REQUIREMENT_MISSING",
            bool(evidence.get("task_coverage"))
            and all(
                c.get("coverage") in {"developed", "well_developed"}
                for c in evidence.get("task_coverage", [])
            ),
            "task_fulfillment",
        ),
    ):
        quote = next(
            (
                q.get("quote")
                for q in criteria.get(criterion, {}).get("positive_evidence", [])
                if q.get("quote") and q["quote"] in attempt.answer
            ),
            None,
        )
        if passed and quote:
            signals.append(
                signal(
                    category,
                    concept,
                    quote,
                    outcome="SUCCESS",
                    confidence=0.9,
                    context_hash=digest(quote),
                    evidence_kind="positive_grader_evidence",
                )
            )
    return {
        "signals": signals,
        "text": attempt.answer,
        "positive_quotes": positives,
        "exposure": max(1, attempt.word_count),
        "lexical_counts": lexical_counts(attempt.answer),
        "scores": {
            k: getattr(grading, k + "_score")
            for k in ("task_fulfillment", "organization", "vocabulary", "grammar", "overall")
        },
        "source_version": digest([grading.cache_key, grading.grader_version]),
        "grader_version": grading.grader_version,
        "model": grading.ai_model,
        "occurred_at": attempt.submitted_at or grading.created_at,
        "source_url": f"/result/{attempt.id}",
    }


def speaking_data(session):
    signals, texts, positives, versions = [], [], [], []
    grades = [session.grading] if session.grading else [a.grading for a in session.answers if a.grading]
    for grade in grades:
        versions.append([grade.cache_key, grade.prompt_version])
    if not grades:
        return None
    for answer in session.answers:
        grade = session.grading or answer.grading
        if not grade:
            continue
        text = answer.transcript or ""
        texts.append(text)
        language = error_signals(grade.errors, text, speaking=True, sequence=answer.sequence_number)
        for s in language:
            if s["category"] in {"CONTENT", "TASK_RESPONSE"} and answer.part == 3:
                s["concept_key"] = s["subcategory"] = "PART3_STRUCTURE_WEAK"
        signals.extend(language)
        # Specific patterns are derived only from explicit negative grader feedback.
        for feedback in grade.answer_feedback or []:
            if feedback.get("sequence_number") != answer.sequence_number:
                continue
            context = " ".join(
                str(feedback.get(k, ""))
                for k in ("summary_vi", "reasons_developed_vi", "other_options_discussed_vi")
            ).casefold()
            patterns = {
                "ANSWER_TOO_SHORT": ("quá ngắn", "too short"),
                "IDEA_NOT_DEVELOPED": ("ý chưa phát triển", "chưa triển khai", "undeveloped"),
                "ALTERNATIVES_NOT_REJECTED": (
                    "chưa giải thích vì sao không chọn",
                    "chưa đề cập các phương án khác",
                ),
                "POOR_COMPARISON": ("chưa so sánh", "thiếu so sánh"),
                "PART3_STRUCTURE_WEAK": ("thiếu cấu trúc", "cấu trúc chưa rõ"),
            }
            for concept, needles in patterns.items():
                if any(n in context for n in needles) and not any(
                    s["concept_key"] == concept and s["details"].get("sequence") == answer.sequence_number
                    for s in signals
                ):
                    signals.append(
                        signal(
                            "TASK_DEVELOPMENT",
                            concept,
                            None,
                            sequence=answer.sequence_number,
                            part=answer.part,
                            evidence_kind="grader_feedback",
                            explanation_vi=context[:1500],
                        )
                    )
        audio = answer.audio_analysis or {}
        if audio.get("available") and audio.get("speech_present", True) and answer.audio_hash:
            for issue in audio.get("issues", []):
                if issue.get("confidence", 0) < settings.audio_feedback_min_confidence or not issue.get(
                    "audible_evidence_vi"
                ):
                    continue
                kind = issue["type"]
                cat = "FLUENCY" if kind in {"rhythm", "hesitation"} else "PRONUNCIATION"
                concept = kind.upper()
                explanation = issue.get("description_vi", "") + " " + issue["audible_evidence_vi"]
                if kind == "hesitation":
                    concept = (
                        "LONG_PAUSES"
                        if re.search(r"khoảng dừng|ngừng lâu|dừng dài|long pause", explanation, re.I)
                        else "HESITATION"
                    )
                if "θ" in explanation + issue.get("target", ""):
                    concept = "SOUND_TH"
                signals.append(
                    signal(
                        cat,
                        concept,
                        issue.get("target"),
                        confidence=issue["confidence"],
                        evidence_kind="audio",
                        audio_hash=answer.audio_hash,
                        answer_id=answer.id,
                        sequence=answer.sequence_number,
                        part=answer.part,
                        explanation_vi=issue.get("description_vi", ""),
                        audible_evidence_vi=issue["audible_evidence_vi"],
                        suggestion_vi=issue.get("suggestion_vi", ""),
                    )
                )
        for s in signals:
            if s["details"].get("sequence") == answer.sequence_number:
                s["details"]["part"] = answer.part
        if (
            audio.get("available")
            and audio.get("fluency_confidence", 0) >= settings.audio_feedback_min_confidence
            and audio.get("fluency_score") is not None
            and audio["fluency_score"] >= 7
            and len(text.split()) >= 40
            and not any(i.get("type") in {"rhythm", "hesitation"} for i in audio.get("issues", []))
        ):
            for concept in ("LONG_PAUSES", "HESITATION"):
                signals.append(
                    signal(
                        "FLUENCY",
                        concept,
                        audio.get("heard_text") or text,
                        outcome="SUCCESS",
                        confidence=audio["fluency_confidence"],
                        context_hash=digest(answer.question_text),
                        evidence_kind="positive_audio_assessment",
                        audio_hash=answer.audio_hash,
                        sequence=answer.sequence_number,
                        part=answer.part,
                        explanation_vi=audio.get("fluency_summary_vi", ""),
                    )
                )
        # Validated corrections are not positive evidence of successful original language use.
        # Speaking transfer is recognized only by an explicit vocabulary usage assessment below.
    text = "\n".join(texts)
    keys = ("grammar", "vocabulary", "pronunciation", "fluency", "structures", "overall")
    scores = {
        key: round(sum(values) / len(values), 2)
        if (values := [getattr(g, key + "_score") for g in grades if getattr(g, key + "_score") is not None])
        else None
        for key in keys
    }
    return dict(
        signals=signals,
        text=text,
        positive_quotes=positives,
        exposure=max(1, len(text.split())),
        lexical_counts=lexical_counts(text),
        scores=scores,
        source_version=digest(versions),
        grader_version=grades[0].prompt_version,
        model=grades[0].ai_model,
        occurred_at=session.completed_at or max(g.created_at for g in grades),
        source_url=f"/speaking/result/{session.id}",
    )


def reading_data(session):
    signals = []
    for answer in session.answers:
        q = answer.question
        if not trusted_key(q) or q.question_type not in TYPES:
            continue
        key, _ = TYPES[q.question_type]
        correct = answer.selected_answer == q.correct_answer
        rationale = (
            (q.option_explanations or {}).get(answer.selected_answer, {}) if answer.selected_answer else {}
        )
        signals.append(
            signal(
                "COMPREHENSION",
                key,
                q.question_text,
                confidence=1,
                outcome="SUCCESS" if correct else "ERROR",
                severity="major",
                evidence_kind="answer_key",
                question_id=q.id,
                question_type=q.question_type,
                selected_answer=answer.selected_answer,
                correct_answer=q.correct_answer,
                explanation_vi=rationale.get("explanation_vi", "")
                if isinstance(rationale, dict)
                else str(rationale),
                evidence=q.evidence,
                unanswered=answer.selected_answer is None,
            )
        )
    return dict(
        signals=signals,
        text="",
        positive_quotes=[],
        exposure=len(signals),
        lexical_counts={},
        scores={"overall": session.result.score},
        source_version=digest(
            [
                [a.question_id, a.selected_answer, a.question.correct_answer, a.question.answer_key_source]
                for a in session.answers
            ]
        ),
        grader_version="reading-1",
        model=None,
        occurred_at=session.submitted_at or session.created_at,
        source_url=f"/reading/result/{session.id}",
    )
