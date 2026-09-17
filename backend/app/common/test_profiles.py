"""Exam identity is separate from learner targets, outcomes and internal item metadata."""

from typing import Literal

TestProfile = Literal["VSTEP_3_5"]
VSTEP_3_5: TestProfile = "VSTEP_3_5"
ItemDifficultyBand = Literal["ACCESSIBLE", "MODERATE", "CHALLENGING", "ADVANCED"]
ITEM_DIFFICULTY_BANDS: tuple[ItemDifficultyBand, ...] = ("ACCESSIBLE", "MODERATE", "CHALLENGING", "ADVANCED")

MULTILEVEL_GENERATION_PRINCIPLE = """The test_profile is VSTEP_3_5: one multilevel examination
assessing Levels 3–5 of the Vietnamese six-level framework, broadly corresponding to B1/B2/C1.
These proficiency levels are PERFORMANCE OUTCOMES, never separate exam versions or user-selected difficulty.
The same realistic task allows candidates to demonstrate differing grammar range, accuracy, vocabulary,
coherence and task fulfilment through the quality of their response. Do not manufacture obscure academic
topics to create a purported C1 task. Never label a prompt as a B1/B2/C1 exam.
Return test_profile=VSTEP_3_5. Learner goals or past estimates must not change the exam format.
"""
