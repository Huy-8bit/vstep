import re

from . import grammar, pronunciation, reading, speaking, vocabulary, writing

LABELS = {
    k: v
    for module in (grammar, vocabulary, writing, speaking, reading, pronunciation)
    for k, v in module.CONCEPTS.items()
}


def normalize(category, subtype, original="", corrected="", *, skill=None):
    """Classify already validated grader errors; never diagnose new errors here."""
    before, after = original.casefold(), corrected.casefold()
    if (
        "internet" in before
        and re.search(r"\bon the internet\b", after)
        and not re.search(r"\bon the internet\b", before)
    ):
        return "GRAMMAR", "PREPOSITION", "INTERNET_EXPRESSION"
    if re.search(r"\b(?:am|is|are|was|were)\s+(?:very\s+)?agree\b", before):
        return "GRAMMAR", "VERB_FORM", "AGREE_USAGE"
    if (
        "advantage" in before
        and re.search(r"\badvantages\b", after)
        and not re.search(r"\badvantages\b", before)
    ):
        return "GRAMMAR", "SINGULAR_PLURAL", "ADVANTAGE_COUNTABILITY"
    for phrase, key, group in (
        ("interested in", "PREPOSITION_INTERESTED_IN", "PREPOSITION"),
        ("depend on", "PREPOSITION_DEPEND_ON", "PREPOSITION"),
    ):
        if phrase in after and not (
            re.search(r"\bdepend\w* on\b", before) if key == "PREPOSITION_DEPEND_ON" else phrase in before
        ):
            return "GRAMMAR", group, key
    if (
        "enjoy" in before
        and re.search(r"enjoy\w*\s+\w+ing\b", after)
        and not re.search(r"enjoy\w*\s+\w+ing\b", before)
    ):
        return "GRAMMAR", "GERUND_INFINITIVE", "GERUND_ENJOY_DOING"
    if "want" in before and re.search(r"want\w*\s+to\s", after) and not re.search(r"want\w*\s+to\s", before):
        return "GRAMMAR", "GERUND_INFINITIVE", "INFINITIVE_WANT_TO_DO"
    if re.search(r"\bpeople\s+(?:is|was|has)\b", before) and re.search(
        r"\bpeople\s+(?:are|were|have)\b", after
    ):
        return "GRAMMAR", "SUBJECT_VERB_AGREEMENT", "SUBJECT_VERB_AGREEMENT"
    cat = category.upper()
    direct = {
        "SPELLING": ("VOCABULARY", "SPELLING"),
        "COLLOCATION": ("VOCABULARY", "COLLOCATION"),
        "WORD_CHOICE": ("VOCABULARY", "WORD_CHOICE"),
        "PUNCTUATION": ("GRAMMAR", "PUNCTUATION"),
        "COHESION": ("COHESION", "WEAK_COHESION" if skill == "WRITING" else "COHESION_WEAK"),
        "REGISTER": ("REGISTER", "REGISTER_MISMATCH") if skill == "WRITING" else ("VOCABULARY", "REGISTER"),
    }
    if cat in direct:
        mapped, key = direct[cat]
        if (
            key == "COLLOCATION"
            and "make people healthy" in before
            and any(p in after for p in ("stay healthy", "improve", "health benefits"))
        ):
            key = "NATURAL_HEALTH_COLLOCATION"
        return mapped, key, key
    if cat == "SENTENCE_STRUCTURE":
        cat = "GRAMMAR"
        if not subtype:
            subtype = "CLAUSE_STRUCTURE"
    if cat == "TASK_RESPONSE" and skill == "WRITING":
        return "TASK_FULFILLMENT", "TASK_REQUIREMENT_MISSING", "TASK_REQUIREMENT_MISSING"
    token = subtype.lower().replace("-", "_").replace(" ", "_")
    module = grammar if cat == "GRAMMAR" else vocabulary if cat == "VOCABULARY" else speaking
    concept = (
        token.upper()
        if token.upper() in module.CONCEPTS
        else next(
            (v for k, v in getattr(module, "ALIASES", {}).items() if k.replace(" ", "_") in token), None
        )
    )
    if not concept:
        concept = (
            "GRAMMAR_USAGE"
            if cat == "GRAMMAR"
            else "WORD_CHOICE"
            if cat == "VOCABULARY"
            else "COHESION_WEAK"
            if cat == "COHERENCE"
            else "IDEA_NOT_DEVELOPED"
        )
    return cat, concept, concept


def label(concept):
    return LABELS.get(concept, concept.replace("_", " ").title())
