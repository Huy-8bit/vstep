"""Original synthetic style fragments; no official examination corpus."""

WRITING_STYLE_EXAMPLES = {
    1: {
        "relationship": "club",
        "register": "semi-formal",
        "context": "A community club writes to a new member about its weekend programme.",
        "stimulus": "Thank you for joining our community club. We are planning next month's weekend activities and would like to hear from our new members before we arrange them. Which kind of activity would you most enjoy, and what makes it interesting to you? Please also tell us whether Saturday or Sunday would be more convenient. If you have a skill you could share with the group, we would love to hear about it. We look forward to your reply.",
        "instruction": "Write an email responding to the club organiser.",
    },
    2: {
        "stimulus": "In many towns, small neighbourhood shops face competition from larger shopping centres. Some residents appreciate the lower prices and wider choice offered by large stores, while others value the personal service and convenience of local shops.",
        "instruction": "Write an essay to an educated reader discussing the effects of this change on local communities. Support your answer with reasons and relevant examples.",
    },
}
SPEAKING_STYLE_EXAMPLES = {
    1: [
        "Let's talk about daily journeys.",
        "How do you usually travel to work or study?",
        "Would you like to change anything about your journey?",
    ],
    2: {
        "situation": "Your study group wants to celebrate finishing a course within a limited budget.",
        "options": [
            "a picnic in a local park",
            "a meal at a small restaurant",
            "a film evening at someone's home",
        ],
    },
    3: {
        "topic": "Learning practical skills can benefit young people.",
        "ideas": [
            "greater independence",
            "confidence in everyday situations",
            "more opportunities to help others",
        ],
        "own_ideas": True,
    },
}
