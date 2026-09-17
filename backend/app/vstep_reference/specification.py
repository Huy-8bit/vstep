REFERENCE_VERSION = "3.0.0"
TEST_PROFILE = "VSTEP_3_5"
SOURCES = {
    "decision": "Decision 729/QĐ-BGDĐT, 11 March 2015",
    "university_format": "https://vstep.vnu.edu.vn/test-format/",
    "illustrative_publication": "https://vstep.vnu.edu.vn/dinh-dang-de-thi-vstep-3-5/",
}
OFFICIAL_FORMAT = {
    "writing": {
        "minutes": 60,
        "tasks": 2,
        "minimum_words": {1: 120, 2: 250},
        "weights": {1: 1 / 3, 2: 2 / 3},
    },
    "speaking": {
        "approximate_minutes": 12,
        "parts": 3,
        "part1_topics": 2,
        "part1_questions": [3, 6],
        "part2_options": 3,
    },
    "reading": {"minutes": 60, "passages": 4, "questions": 40, "options": ["A", "B", "C", "D"]},
}
# Narrower product targets, not claims about a confidential examiner specification.
SIMULATOR_HEURISTICS = {
    "writing_task_minutes": {1: 20, 2: 40},
    "incoming_message_words": [60, 120],
    "speaking_part_minutes": {1: 3, 2: 4, 3: 5},
    "reading_total_words": [1900, 2050],
    "reading_items_per_passage": 10,
    "independent_quality_confidence": 0.8,
}
