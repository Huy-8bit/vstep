"""Global simulator assembly, not an official CEFR difficulty mapping."""

from collections import Counter
from dataclasses import dataclass
from itertools import product

from app.common.test_profiles import VSTEP_3_5, ItemDifficultyBand
from app.vstep_reference.specification import OFFICIAL_FORMAT, SIMULATOR_HEURISTICS

READING_TAXONOMY = {
    "DETAIL": "detail",
    "MAIN_IDEA_OR_TITLE": "main_idea",
    "VOCABULARY_IN_CONTEXT": "vocabulary",
    "REFERENCE": "reference",
    "INFERENCE": "inference",
    "AUTHOR_PURPOSE": "purpose",
    "AUTHOR_ATTITUDE": "attitude",
    "TONE": "tone",
    "NEGATIVE_DETAIL": "negative_detail",
    "QUOTE_OR_SENTENCE_INTERPRETATION": "sentence_meaning",
    "SENTENCE_INSERTION": "sentence_insertion",
    "PARAGRAPH_OR_PASSAGE_COMPLETION": "paragraph_completion",
    "ORGANIZATION": "organization",
}


@dataclass(frozen=True)
class ReadingSlot:
    position: int
    internal_difficulty_band: ItemDifficultyBand
    required_question_types: tuple[str, ...]
    text_demand: str


class ReadingFullTestBlueprint:
    version = "3.0.0"
    test_profile = VSTEP_3_5
    passage_count = OFFICIAL_FORMAT["reading"]["passages"]
    question_count = OFFICIAL_FORMAT["reading"]["questions"]
    duration_minutes = OFFICIAL_FORMAT["reading"]["minutes"]
    total_words = SIMULATOR_HEURISTICS["reading_total_words"]
    slots = (
        ReadingSlot(
            1,
            "ACCESSIBLE",
            ("main_idea", "detail", "vocabulary", "reference"),
            "Concrete text with clear referents; include paraphrase.",
        ),
        ReadingSlot(
            2,
            "MODERATE",
            ("detail", "inference", "vocabulary", "negative_detail"),
            "Connected explanations and supported implications.",
        ),
        ReadingSlot(
            3,
            "CHALLENGING",
            ("inference", "purpose", "sentence_meaning"),
            "Cross-paragraph links and qualified arguments.",
        ),
        ReadingSlot(
            4,
            "ADVANCED",
            ("inference", "organization"),
            "Nuanced stance and limits of evidence without specialist knowledge.",
        ),
    )

    def accepts(self, passage, slot):
        return (
            passage.test_profile == self.test_profile
            and passage.generation_diagnostics.get("quality_valid") is True
            and passage.internal_difficulty_band == slot.internal_difficulty_band
            and len(passage.questions) == 10
            and 430 <= passage.word_count <= 600
            and set(slot.required_question_types).issubset({q.question_type for q in passage.questions})
            and len({q.internal_difficulty_band for q in passage.questions} - {None}) >= 2
        )

    def diagnostics(self, plan):
        questions = [q for p in plan if p for q in p.questions]
        return {
            "blueprint_version": self.version,
            "total_word_count": sum(p.word_count for p in plan if p),
            "topic_diversity": len({p.topic for p in plan if p}),
            "question_type_distribution": dict(Counter(q.question_type for q in questions)),
            "correct_answer_distribution": dict(Counter(q.correct_answer for q in questions)),
            "internal_difficulty": [p.internal_difficulty_band for p in plan if p],
        }

    def complete(self, plan):
        if len(plan) != 4 or any(p is None or not self.accepts(p, slot) for p, slot in zip(plan, self.slots)):
            return False
        d = self.diagnostics(plan)
        keys = d["correct_answer_distribution"]
        return (
            len({p.id for p in plan}) == 4
            and self.total_words[0] <= d["total_word_count"] <= self.total_words[1]
            and d["topic_diversity"] >= 3
            and len(d["question_type_distribution"]) >= 8
            and set(keys) == set("ABCD")
            and min(keys.values()) >= 5
            and max(keys.values()) <= 15
            and bool({"tone", "attitude"} & set(d["question_type_distribution"]))
        )

    def select(self, ordered_bank):
        candidates = [[p for p in ordered_bank if self.accepts(p, slot)][:16] for slot in self.slots]
        # Bounded search evaluates the complete test, preserving the unseen-first input ordering.
        if all(candidates):
            for plan in product(*candidates):
                if self.complete(plan):
                    return list(plan)
        plan = []
        used_topics = set()
        for group in candidates:
            pick = next((p for p in group if p.topic not in used_topics), None)
            if pick:
                used_topics.add(pick.topic)
            plan.append(pick)
        if all(plan):
            plan[-1] = None  # Explicitly report a missing globally compatible slot, not a false-ready bank.
        # Keep enough space for every unfilled slot; long legacy companions can otherwise
        # make the last slot impossible even though each passage is individually valid.
        while any(plan):
            fixed = sum(p.word_count for p in plan if p)
            missing = sum(p is None for p in plan)
            if fixed + missing * 430 <= self.total_words[1] and fixed + missing * 600 >= self.total_words[0]:
                break
            largest = max((i for i, p in enumerate(plan) if p), key=lambda i: plan[i].word_count)
            plan[largest] = None
        return plan

    def context(self, slot, plan):
        companions = [p for i, p in enumerate(plan) if p and i + 1 != slot.position]
        missing = 4 - len(companions)
        remaining_min = self.total_words[0] - sum(p.word_count for p in companions)
        remaining_max = self.total_words[1] - sum(p.word_count for p in companions)
        minimum = max(430, remaining_min - (missing - 1) * 600)
        maximum = min(600, remaining_max - (missing - 1) * 430)
        return {
            "blueprint_version": self.version,
            "test_profile": self.test_profile,
            "passage_count": 4,
            "total_question_count": 40,
            "passage_position": slot.position,
            "total_word_target": self.total_words,
            "passage_word_range": [minimum, maximum],
            "recommended_words": min(
                max(round((remaining_min + remaining_max) / (2 * missing)), minimum), maximum
            ),
            "required_question_types": list(slot.required_question_types),
            "text_demand": slot.text_demand,
            "difficulty_progression": [s.internal_difficulty_band for s in self.slots],
            "current_balance": self.diagnostics(companions),
            "taxonomy": READING_TAXONOMY,
            "selected_passages": [
                {
                    "title": p.title,
                    "topic": p.topic,
                    "words": p.word_count,
                    "question_types": [q.question_type for q in p.questions],
                }
                for p in companions
            ],
        }


READING_BLUEPRINT = ReadingFullTestBlueprint()
