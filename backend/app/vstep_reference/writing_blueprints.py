from app.vstep_reference.specification import OFFICIAL_FORMAT, REFERENCE_VERSION, SIMULATOR_HEURISTICS

RELATIONSHIPS = (
    "friend",
    "classmate",
    "host_family",
    "course_organizer",
    "club",
    "accommodation_provider",
    "school_office",
    "local_organization",
    "service_provider",
    "community_representative",
    "colleague",
    "manager",
    "relative",
)
WRITING_BLUEPRINTS = {
    1: {
        "id": f"writing_interactive_incoming_{REFERENCE_VERSION}",
        "genre": ["email", "letter"],
        "stimulus_words": SIMULATOR_HEURISTICS["incoming_message_words"],
        "requirements": [2, 4],
        "minutes": SIMULATOR_HEURISTICS["writing_task_minutes"][1],
        "minimum_words": OFFICIAL_FORMAT["writing"]["minimum_words"][1],
        "layout": [
            "communicative situation/relationship",
            "incoming message",
            "response instruction",
            "word requirement",
        ],
        "registers": ["informal", "semi-formal", "formal"],
        "relationships": RELATIONSHIPS,
    },
    2: {
        "id": f"writing_essay_stimulus_{REFERENCE_VERSION}",
        "genre": ["essay"],
        "stimulus_words": [35, 110],
        "minutes": SIMULATOR_HEURISTICS["writing_task_minutes"][2],
        "minimum_words": OFFICIAL_FORMAT["writing"]["minimum_words"][2],
        "layout": [
            "read a short text/statement",
            "issue or contrasting viewpoints",
            "essay to an educated reader",
            "reasons and examples",
            "word requirement",
        ],
    },
}
