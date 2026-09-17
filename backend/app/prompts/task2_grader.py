from app.prompts.task1_grader import COMMON_GRADER

TASK2_GRADER_PROMPT_VERSION = "1.0.0"
TASK2_GRADER_PROMPT = (
    COMMON_GRADER
    + """
TASK 2: assess every part of the question, a clear thesis/position, body paragraphs, topic sentences,
supporting ideas and examples, logical progression, cohesion, conclusion, vocabulary range,
grammar range and accuracy and minimum 250 words. It is an essay, not a letter.
"""
)
