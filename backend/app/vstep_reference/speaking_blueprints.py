from app.vstep_reference.specification import REFERENCE_VERSION

SPEAKING_BLUEPRINTS = {
    1: {
        "id": f"speaking_social_interaction_{REFERENCE_VERSION}",
        "topics": 2,
        "questions_total": [3, 6],
        "style": "Short conversational personal/general questions, around three per topic; no mini-essays.",
    },
    2: {
        "id": f"speaking_solution_discussion_{REFERENCE_VERSION}",
        "options": 3,
        "style": "One situation, three distinct plausible solutions, a debatable choice with reasons and less suitable alternatives.",
    },
    3: {
        "id": f"speaking_topic_development_{REFERENCE_VERSION}",
        "suggested_ideas": 3,
        "own_ideas": True,
        "followups": [2, 3],
        "style": "One topic statement and idea map; broaden discussion after the main talk.",
    },
}
