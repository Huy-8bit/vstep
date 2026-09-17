SPEAKING_CORRECTION_PROMPT_VERSION = "1.0.0"
SPEAKING_CORRECTION_PROMPT = """
Correct every meaningful spoken utterance in original order. Each sentence_corrections item must identify
sequence_number, quote the original exactly, give corrected spoken English and explain in Vietnamese.
Only supply start_seconds if reliable source timestamps exist; otherwise null.
corrected_transcript preserves ideas, most wording and speaking style, fixing necessary grammar/lexis only.
improved_b2_answer develops the learner's OWN ideas into natural, learnable B2/B2+ SPOKEN English, not an essay.
Use short speakable sentences, practical vocabulary and natural links such as 'I think', 'One reason is',
'For example' and 'That's why' where appropriate. Do not force rigid templates or C1/C2 expressions.
Provide answer_feedback for EVERY sequence, including follow-ups. Keep each answer's corrections separate.
When there is no intelligible answer, say so and leave rewritten text empty; never invent what the learner said.
Global corrected_transcript/improved_b2_answer should label each answer by sequence and part, preserving order.
"""
