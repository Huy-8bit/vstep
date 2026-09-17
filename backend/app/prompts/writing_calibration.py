"""Editorial practice anchors; not official or teacher-labelled VSTEP scores.

The Alex response is a manual regression reference, never a phrase-matching scoring rule.
"""

WRITING_CALIBRATION_PROMPT_VERSION = "2.0.0"
ALEX_QUESTION = """Your English-speaking friend Alex is visiting your hometown next month and has asked for advice. Write an email to Alex.
Suggest the best time and way to travel to your town.
Recommend two places to visit and explain why.
Invite your friend to do something with you.
Write at least 120 words."""
ALEX_RESPONSE = """Dear Alex,

I am so happy to hear that you will visit my hometown next month. I write this email to share you some advice for your trip.

I think the best time to visit is in spring because the weather is warm and not rain much. To get here, traveling by plane is the best way because it is very fast and comfortable.

When you arrive, there are two nice places you should visit. First, you can go to the local market to buy cheap souvenirs and try many tasty street food. Another place is the old museum. It have many interesting things about the history and culture of my city.

I would like to invite you to have dinner at my house with my family. We can talk a lot together.

Write back to me soon.

Best wishes,
Huy"""

CALIBRATION_ANCHORS = [
    {
        "id": "weak",
        "quality_reference": "weak response",
        "task": 1,
        "question": ALEX_QUESTION,
        "response": "Dear Alex, My town good. You come bus. Market is buy and museum is old. I like you visit. We dinner. Bye, Huy",
        "criterion_evidence": {
            "task_fulfillment": "Requirements are only fragments; timing and reasons are absent.",
            "organization": "Some task order, but little connection between fragments.",
            "vocabulary": "Very narrow repertoire; imprecise constructions.",
            "grammar": "Repeated missing verbs/articles and sentence fragments limit meaning.",
        },
        "approximate_practice_range": [2.0, 3.5],
    },
    {
        "id": "borderline_b1",
        "quality_reference": "borderline B1-like performance",
        "task": 1,
        "question": ALEX_QUESTION,
        "response": """Dear Alex,
I happy that you will come my town next month. You should go on Saturday because I not work. You can take bus because it cheap. The bus is near your house and stop in town. I can meet you there.
You should visit market. It have many food and clothes. I go there every week with my mother. The park is a good place too. You can walk and take photo. Many people likes the park because it is beautiful.
Please come my house for dinner. My mother cook very good and she want meet you. We can eat and watch a film. Tell me when you arrive and I will wait you.
Best wishes,
Huy""",
        "criterion_evidence": {
            "task_fulfillment": "Most requirements addressed with simple reasons, limited specificity.",
            "organization": "Recognisable email and grouping; repetitive links and short sequences.",
            "vocabulary": "Basic repeated vocabulary and unnatural constructions.",
            "grammar": "Frequent agreement, missing auxiliary, article and preposition errors.",
        },
        "approximate_practice_range": [3.5, 4.5],
    },
    {
        "id": "solid_b1",
        "quality_reference": "solid B1-like performance",
        "task": 1,
        "question": ALEX_QUESTION,
        "response": """Dear Alex,
Thanks for your email. I am glad you are coming to my town next month. The best time is the weekend because I will be free. You can take a bus from your city. It takes about two hours and is cheaper than the train.
I think you should visit the market. You can try local food there and buy gifts for your family. The park is another good place. It is quiet in the morning, and you can walk beside the lake. I often go there with my brother.
Would you like to have dinner at my house on Saturday? My family would be happy to meet you. We can eat together and talk about your trip. Please let me know your arrival time.
Best wishes,
Huy""",
        "criterion_evidence": {
            "task_fulfillment": "All points reasonably covered, though reasons stay predictable.",
            "organization": "Clear groups and order, with simple rather than flexible cohesion.",
            "vocabulary": "Generally appropriate common vocabulary, limited precision and variation.",
            "grammar": "Mostly controlled simple structures; limited evidence of wider range.",
        },
        "approximate_practice_range": [5.0, 6.0],
    },
    {
        "id": "alex_manual_regression",
        "quality_reference": "borderline B2-like task coverage with weaker language",
        "task": 1,
        "question": ALEX_QUESTION,
        "response": ALEX_RESPONSE,
        "criterion_evidence": {
            "task_fulfillment": "Reasonably covered and relevant, but recommendations have generic reasons. Spring may not match the next-month context; avoid inventing a date-based fault.",
            "organization": "Clear but simple paragraphing and First/Another sequencing, not a reason for 7.5.",
            "vocabulary": "Limited precision/repetition; 'share you some advice' is unnatural. Countability in 'many tasty street food' has one primary error, not two independent penalties.",
            "grammar": "'not rain much' and 'It have' show basic construction/agreement issues; modest structure range. Understandability does not erase these errors.",
        },
        "approximate_practice_range": [5.5, 6.25],
        "manual_acceptance_note": "Usually mid-5 to low-6 overall; a 7-style result requires unusually strong textual evidence. This range is a reference, not an exact expected number or cap.",
    },
    {
        "id": "solid_b2",
        "quality_reference": "solid B2-like performance",
        "task": 1,
        "question": ALEX_QUESTION,
        "response": """Dear Alex,
It was lovely to hear that you are planning a visit. If your dates are flexible, I suggest arriving on a Friday morning, when the roads are quieter. The direct coach would be more convenient than flying: it stops in the town centre, so you would avoid an expensive airport transfer.
For your first afternoon, the riverside market is worth exploring. Besides tasting local dishes, you can watch craftspeople make the pottery for which our town is known. You might also enjoy the history museum. Its collection is fairly small, but the photographs show how the river has shaped people's lives over the years.
Would you like to join my family for dinner on Saturday? My father has offered to cook his favourite dish, and afterwards I could take you for a walk along the river. Let me know whether that suits your plans.
Best wishes,
Huy""",
        "criterion_evidence": {
            "task_fulfillment": "Specific reasons and practical travel comparisons develop all requests.",
            "organization": "Purposeful progression with clear referencing and naturally connected details.",
            "vocabulary": "Appropriate precision and natural collocations across a familiar topic.",
            "grammar": "Controlled conditionals, relative clauses, comparison and varied sentence patterns.",
        },
        "approximate_practice_range": [7.0, 8.0],
    },
    {
        "id": "strong_b2_c1",
        "quality_reference": "strong B2/C1-like performance",
        "task": 1,
        "question": ALEX_QUESTION,
        "response": """Dear Alex,
I'm delighted that you'll be visiting next month. If you can choose your arrival time, aim for Friday before midday: you'll miss the weekend traffic without losing an afternoon. I'd take the direct train rather than fly. Although the journey itself is longer, the station is central, whereas getting from the airport can take another hour.
Since you enjoy discovering how people live, start with the covered market. Go early enough to see the stalls being set up, then have breakfast at one of the family-run counters; the owners are usually happy to explain their dishes. For a quieter contrast, try the local museum. The restored photographs are particularly worthwhile because they show the same streets before the riverfront was redeveloped.
Could you keep Saturday evening free for dinner with us? My sister would love to meet you, and, weather permitting, we could walk to the river afterwards. Send me your train details once you've booked, and I'll meet you at the station.
See you soon,
Huy""",
        "criterion_evidence": {
            "task_fulfillment": "Precisely tailored, practical advice with sufficiently developed reasons and invitation.",
            "organization": "Sustained natural progression, contrast and referential cohesion without formulaic excess.",
            "vocabulary": "Flexible, precise, idiomatic but appropriate vocabulary, not needless complexity.",
            "grammar": "Varied complex structures handled accurately, with controlled qualification and comparison.",
        },
        "approximate_practice_range": [8.0, 9.0],
    },
]

WRITING_CALIBRATION_PROMPT = """You are an examiner, not a motivational coach. Score ORIGINAL VSTEP.3-5
performance from the supplied STRUCTURED EVIDENCE only. No target level, corrected essay or improved version is
supplied. Do not inflate scores to encourage the learner. Encouragement belongs in feedback, not scoring.
A response is not strong proficiency simply because it is understandable, long enough, has paragraphs or
mentions every bullet. 7+ must be positively demonstrated, not assumed for an average learner.
Use four equally weighted criteria, 0–10 in 0.5 increments. Backend calculates their arithmetic mean.
Task Fulfillment: separate mention from development; 5–6 mostly completed but basic, 6–7 reasonably explained,
7–8 clearly and sufficiently developed, 8+ strong precision/development. These are guidance, not mechanical caps.
Organization: logical progression, paragraph purpose, cohesion and referencing; First/Another plus paragraphs
alone are basic, not automatically 7.5. Vocabulary: range, precision, repetition, collocation and naturalness.
Grammar: accuracy AND range/control. Repeated basic errors in a short response materially limit accuracy.
Use verified word/sentence counts, deduplicated error density and observed structures as supporting evidence.
Never subtract a fixed number per error, reward complexity alone, double-penalize one local construction,
invent errors or force a target score distribution. Missing observed errors does not prove sophisticated range.
Compare with the editorial anchor qualities, not exact wording or a supposed official score table. Do not
memorize any sample's score; transfer standards to other tasks and topics. Task 2 requires a clear position,
developed reasoning/examples and sustained organization, beyond a Task 1 email's demands.
For each criterion first consider an initial_score, then check whether positive and negative evidence truly
justify it. Return the FINAL score after consistency review, with exact evidence quotes copied from analysis,
Vietnamese justification, and consistency_review_vi explaining any adjustment or retention. Retain every negative
evidence quote from each analysis criterion; do not drop limitations to support a higher score. Never quote anchors
as evidence for the candidate. If uncertain between adjacent half points choose the lower unless clear evidence
supports the higher. For 7+ provide at least two actual positive observations and a substantive explanation
of why they outweigh limitations. If consistency_flags are supplied, explicitly resolve each relevant concern.
Scores must reflect the original performance; no invented proficiency level or overall score.
"""
