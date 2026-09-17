"""Editorial balancing for practice material, not official CEFR item calibration."""

from dataclasses import dataclass

from app.common.test_profiles import VSTEP_3_5, ItemDifficultyBand


@dataclass(frozen=True)
class ReadingSlot:
    position: int
    internal_difficulty_band: ItemDifficultyBand
    required_question_types: tuple[str, ...]
    text_demand: str


class ReadingTestBlueprint:
    version = "2.0.0"
    test_profile = VSTEP_3_5
    passage_count = 4
    question_count = 40
    duration_minutes = 60
    slots = (
        ReadingSlot(
            1,
            "ACCESSIBLE",
            ("main_idea", "detail", "vocabulary", "reference", "purpose"),
            "Clear referents, mainly concrete information; include paraphrase and some inference.",
        ),
        ReadingSlot(
            2,
            "MODERATE",
            ("detail", "inference", "vocabulary", "reference", "negative_detail"),
            "Varied clauses and connected explanations; distinguish stated information from implications.",
        ),
        ReadingSlot(
            3,
            "CHALLENGING",
            ("main_idea", "inference", "purpose", "sentence_meaning", "organization"),
            "Denser relationships and qualified arguments; integrate information across paragraphs.",
        ),
        ReadingSlot(
            4,
            "ADVANCED",
            ("inference", "vocabulary", "sentence_meaning", "organization", "tone"),
            "Nuanced stance, evidence limits and competing interpretations without specialist knowledge.",
        ),
    )

    def accepts(self, passage, slot):
        return (
            passage.test_profile == self.test_profile
            and passage.internal_difficulty_band == slot.internal_difficulty_band
            and len(passage.questions) == 10
            and 430 <= passage.word_count <= 650
            and set(slot.required_question_types).issubset({q.question_type for q in passage.questions})
            and len({q.internal_difficulty_band for q in passage.questions} - {None}) >= 2
        )

    def select(self, ordered_bank):
        # Bands are distinct per slot, so every chosen passage is unique.
        return [next((p for p in ordered_bank if self.accepts(p, slot)), None) for slot in self.slots]

    def context(self, slot, plan):
        return {
            "blueprint_version": self.version,
            "test_profile": self.test_profile,
            "passage_count": self.passage_count,
            "total_question_count": self.question_count,
            "passage_position": slot.position,
            "required_question_types": list(slot.required_question_types),
            "text_demand": slot.text_demand,
            "difficulty_progression": [s.internal_difficulty_band for s in self.slots],
            "test_skill_coverage": sorted({t for s in self.slots for t in s.required_question_types}),
            "selected_passages": [
                {
                    "position": i + 1,
                    "title": p.title,
                    "topic": p.topic,
                    "question_types": [q.question_type for q in p.questions],
                }
                for i, p in enumerate(plan)
                if p and i + 1 != slot.position
            ],
        }


READING_BLUEPRINT = ReadingTestBlueprint()
