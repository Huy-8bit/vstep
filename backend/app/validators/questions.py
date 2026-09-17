import re
from difflib import SequenceMatcher

from app.common.words import count_words
from app.vstep_reference.writing_blueprints import RELATIONSHIPS

VALIDATOR_VERSION = "3.0.0"


def normalized(text):
    return " ".join(re.findall(r"[a-z0-9]+", text.casefold()))


def reject_near_duplicate(text, previous):
    candidate = normalized(text)
    for old in previous:
        if SequenceMatcher(None, candidate, normalized(old), autojunk=False).ratio() >= 0.88:
            raise ValueError("Near-duplicate prompt; choose a different communicative situation")


class WritingTask1QuestionValidator:
    def validate(self, question):
        if question.genre not in {"email", "letter"} or question.recipient_relationship not in RELATIONSHIPS:
            raise ValueError("Task 1 needs a real correspondence relationship")
        if question.register not in {"informal", "semi-formal", "formal"} or not question.purpose.strip():
            raise ValueError("Task 1 needs register and communicative purpose")
        if not 60 <= count_words(question.stimulus) <= 120:
            raise ValueError("Incoming correspondence requires 60–120 words")
        if not 2 <= len(question.requirements) <= 4 or len(
            set(map(normalized, question.requirements))
        ) != len(question.requirements):
            raise ValueError("Task 1 needs 2–4 distinct meaningful requirements")
        if question.minimum_words != 120 or not re.search(
            r"\b(email|letter)\b", question.response_instruction, re.I
        ):
            raise ValueError("Task 1 must ask for an email/letter response")
        if any(
            re.search(pattern, question.instruction + " " + question.response_instruction, re.I)
            for pattern in (r"summari[sz]e.{0,40}(chart|graph|map|diagram)", r"IELTS", r"model answer")
        ):
            raise ValueError("Not a VSTEP correspondence task")
        if len(question.instruction.split()) < 12 or len(question.response_instruction.split()) < 5:
            raise ValueError("Missing situation or response instruction")
        return True


class WritingQuestionValidator:
    def validate(self, question, recent=()):
        if question.task == 1:
            WritingTask1QuestionValidator().validate(question)
        elif (
            question.genre != "essay"
            or question.minimum_words != 250
            or not 35 <= count_words(question.stimulus) <= 110
            or "educated reader" not in question.response_instruction.lower()
        ):
            raise ValueError("Task 2 requires short issue stimulus and an essay to an educated reader")
        if question.task == 2 and not 1 <= len(question.requirements) <= 4:
            raise ValueError("Task 2 needs structured task requirements")
        reject_near_duplicate(question.instruction + " " + question.stimulus, recent)
        return True


class SpeakingQuestionValidator:
    def validate(self, question, recent=()):
        all_text = " ".join(
            [question.question_text, question.situation or "", *question.options, *question.suggested_ideas]
        )
        if re.search(r"cue.card|you should say|one minute to prepare|IELTS", all_text, re.I):
            raise ValueError("IELTS cue-card style is not accepted")
        if question.part == 1:
            if (
                len(question.topic_sets) != 2
                or not 3 <= sum(len(t.questions) for t in question.topic_sets) <= 6
            ):
                raise ValueError("Part 1 needs two conversational topics and 3–6 questions")
            questions = [q for t in question.topic_sets for q in t.questions]
            if len(set(map(normalized, questions))) != len(questions) or any(
                len(q.split()) > 30 or not (q.endswith("?") or q.lower().startswith("tell me about "))
                for q in questions
            ):
                raise ValueError("Part 1 needs short, distinct conversational questions")
            if any(
                re.search(r"evaluate the|critically analy[sz]e|discuss the extent", q, re.I)
                for q in questions
            ):
                raise ValueError("Part 1 cannot require an academic mini-essay")
            all_text = " ".join(questions)
        elif question.part == 2:
            if (
                not question.situation
                or len(question.options) != 3
                or len(set(map(normalized, question.options))) != 3
            ):
                raise ValueError("Part 2 needs a situation and three distinct solutions")
            if any(not o.strip() or len(o.split()) > 35 for o in question.options):
                raise ValueError("Solutions must be concise")
        elif question.part == 3:
            if (
                len(question.suggested_ideas) != 3
                or not question.allow_own_idea
                or not 2 <= len(question.follow_up_questions) <= 3
            ):
                raise ValueError("Part 3 needs topic, idea map, own ideas and follow-ups")
            if len(set(map(normalized, question.suggested_ideas))) != 3:
                raise ValueError("Suggested ideas must differ")
        reject_near_duplicate(all_text, recent)
        return True
