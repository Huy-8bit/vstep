import re


def count_words(text: str) -> int:
    return len(re.findall(r"[\w]+(?:['’\-][\w]+)*", text, re.UNICODE))
