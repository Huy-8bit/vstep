"""Text-grounding checks for editable import drafts, never content generation."""

import re


def normalized(text):
    return re.sub(r"\s+", " ", text or "").strip()


def guard_source_wording(parsed, source):
    if source is None:
        return parsed  # Image/PDF extraction is checked visually by the owner in the mandatory preview.
    raw = normalized(source)
    for item in parsed.items:

        def exact(value, label):
            if not value or normalized(value) in raw:
                return value
            item.warnings.append(
                f"{label}: nội dung AI trả về không khớp nguyên văn nguồn; đã để trống để bạn bổ sung."
            )
            return ""

        for q in item.content.writing:
            q.instruction = exact(q.instruction, "Yêu cầu Writing")
            q.stimulus_text = exact(q.stimulus_text, "Nội dung thư / tình huống")
            q.requirements = [v for v in (exact(v, "Yêu cầu riêng") for v in q.requirements) if v]
        for q in item.content.speaking:
            for field in ("situation", "candidate_task", "optional_context", "central_idea"):
                setattr(q, field, exact(getattr(q, field), field))
            # Keep empty option slots so the owner sees a missing choice, rather than renumbering it.
            q.options = [exact(v, "Lựa chọn Speaking") for v in q.options]
            q.suggested_ideas = [v for v in (exact(v, "Ý gợi ý") for v in q.suggested_ideas) if v]
            q.follow_up_questions = [
                v for v in (exact(v, "Câu hỏi mở rộng") for v in q.follow_up_questions) if v
            ]
            for topic in q.topic_sets:
                topic.questions = [exact(v, "Câu hỏi Part 1") for v in topic.questions]
        for p in item.content.reading:
            p.passage_text = exact(p.passage_text, "Bài đọc")
            for q in p.questions:
                q.question_text = exact(q.question_text, f"Câu {q.question_number}")
                for letter in "ABCD":
                    setattr(
                        q.options,
                        letter,
                        exact(getattr(q.options, letter), f"Lựa chọn {letter}, câu {q.question_number}"),
                    )
                q.explanation = exact(q.explanation, "Giải thích từ nguồn") or None
    return parsed
