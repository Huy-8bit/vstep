from app.prompts.writing_analysis import WRITING_ANALYSIS_PROMPT
from app.prompts.writing_calibration import WRITING_CALIBRATION_PROMPT

WRITING_CORE_VERSION = "4.1.0"

# Stable rubric/schema prefix precedes variable question/answer. Do not place the
# benchmark's reference answers/scores here; held-out evaluation must remain blind.
WRITING_CORE_PROMPT = (
    WRITING_ANALYSIS_PROMPT.replace(
        "Do not assign scores, estimate a CEFR level, or rewrite/improve the whole answer.",
        "Analyze evidence before assigning criterion scores; never rewrite the whole answer or estimate a CEFR level.",
    ).replace(
        "Do not return corrected_version, improved text or scores.",
        "Do not return corrected_version or improved essays.",
    )
    + "\n"
    + WRITING_CALIBRATION_PROMPT
    + """\nCOMPACT SINGLE-CALL CONTRACT:
The analysis object contains observed evidence; scores contains your final calibrated scores from THAT original evidence.
Do not duplicate quotes inside scores. Each justification_vi explains the score and reconciles limitations in 1-2 concise sentences.
For a score >=7 provide two exact positive quotations in analysis.criteria for that criterion and at least 80 characters of substantive justification.
Use at most 2 positive and 2 negative evidence entries per criterion. IMPORTANT: the compact schema replaces quote fields with sentence_id: cite a supplied original sentence ID, and the backend retrieves the exact original sentence. Use null ONLY for missing coverage or a whole-text observation. Never invent an ID or cite a sentence that does not support the explanation.
List up to 12 representative, real local errors; prefer recurring/significant issues, never omit basic errors to support a high score.
Sentence classification must still cover EVERY supplied sentence. Only errors contain original text snippets: copy an exact contiguous substring from its numbered sentence, without ellipses, added quotation marks, capitalization changes or joining separate pieces.
Do not repeat long wording across assessment, justification, summary and improvements. Three short actionable top_improvements only.
Return confidence in adequacy of this evidence for scoring, not the learner's competence. List at most 3 genuine ambiguities, empty when none.
Very short/blank/off-topic responses must score for demonstrated performance, not hypothetical potential; never invent language evidence.
For an already strong answer, improvements may be refinement or maintenance, not fabricated errors.
Do not produce vocabulary lists, sentence-by-sentence rewrites, full corrected/reference essays or motivational paragraphs.
Keep criteria independent: missing task requirements reduce Task Fulfillment; they do not by themselves make otherwise accurate English ungrammatical or its vocabulary poor. Score demonstrated language even in a response that misunderstood the task.
For Grammar and Vocabulary, distinguish accurate familiar/simple language (typically around 5.5–6.5) from sustained controlled range and precision (7+). Several clauses with 'because' alone do not establish flexible range. Do not force a lower score when the text actually demonstrates sustained flexibility.
At the low end, meaningful fragments may demonstrate partial communicative and lexical achievement; reserve zero for absence of assessable performance, not merely a short response. Length and task completion are supporting evidence, not a multiplier applied to every criterion.
If supplied review concerns identify conflicting evidence, reassess independently and resolve them. Never mechanically subtract points per error.
"""
)
