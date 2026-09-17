"""Editorial synthetic calibration references, not certified examiner scores."""

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

# Task 2 references transfer the same standards to sustained argument.
ESSAY_QUESTION = """TASK 2. Read the following statement about free public transport.
Some cities are considering removing fares from buses to encourage residents to leave their cars at home.
Supporters expect cleaner air and easier access to jobs, while critics believe that limited funds should first
be spent on reliable services. Write an essay to an educated reader discussing these two views and giving
your opinion. Include reasons and relevant examples. Write at least 250 words."""
CALIBRATION_ANCHORS.extend(
    [
        {
            "id": "essay_limited_development",
            "quality_reference": "basic relevant argument with limited control",
            "task": 2,
            "question": ESSAY_QUESTION,
            "response": """Free buses is a good idea for cities. Many people use cars and there are much pollution. Some people think buses should free but other people want good services. I will discuss both sides.
First, free bus help people save money. They can go work and they do not pay. This is very good for students and poor people. For example my friend go to school by bus every day. If it free he save money. Also the environment will better because people do not drive cars.
On the other hand, bus services need be reliable. If the bus late, people are late too. People have jobs and they cannot wait long time. The government should buy more buses. More buses are better because it is convenient. Sometimes there are many passenger and we cannot get on.
In conclusion, both ideas have advantage. I think free buses is best because everybody can travel and the city have less pollution. The government should make good buses and free buses for all people.""",
            "criterion_evidence": {
                "task_fulfillment": "Both views and a position are present but largely asserted; the single example does little to develop the cost/reliability trade-off. The short response offers limited support.",
                "organization": "Predictable but identifiable progression; repeated claims and weak connections limit cohesion.",
                "vocabulary": "Relevant common terms but repeated 'good', 'people' and 'buses'; imprecise expressions and countability errors.",
                "grammar": "Frequent agreement, missing auxiliary, infinitive and plural errors; a few basic conditionals do not establish broad control.",
            },
            "approximate_practice_range": [4.0, 5.5],
        },
        {
            "id": "essay_developed_controlled",
            "quality_reference": "developed argument with controlled range",
            "task": 2,
            "question": ESSAY_QUESTION,
            "response": """Removing bus fares could make daily travel easier for many residents, but cheaper journeys are not necessarily more attractive journeys. In my view, cities should improve reliability first while offering targeted discounts to people who find current fares difficult to afford.
The strongest argument for free buses concerns access. For a worker on a low income, several journeys each week can consume money needed for food or rent. Removing that cost may widen the range of jobs the worker can realistically accept. Students could benefit in a similar way, especially when their courses require travel between different sites. These gains matter even if the policy produces only a small reduction in car use.
However, motorists often choose their cars because they cannot depend on the alternative. A free bus that arrives unpredictably may still be unsuitable for someone collecting a child after work. If fares disappear without replacement funding, operators could struggle to maintain frequent services, making the problem worse. Spending the same money on bus lanes or more frequent departures might therefore persuade more drivers to switch.
The appropriate choice depends partly on local conditions. A city with frequent but expensive buses may gain more from lower fares than one whose main problem is long gaps between services. Councils should consult passengers and compare these constraints before announcing a universal policy. They could also protect essential routes while testing reduced fares in a smaller area.
Overall, affordable transport is an important public goal, but affordability includes the time and uncertainty involved in travelling. Reliable services, combined with support for those who need it most, would offer a more convincing starting point than free travel alone.""",
            "criterion_evidence": {
                "task_fulfillment": "Discusses both views, develops mechanisms with concrete examples, qualifies the recommendation by local conditions and sustains a clear position.",
                "organization": "Purposeful paragraph progression; reference, contrast and conditional links connect the affordability and reliability arguments.",
                "vocabulary": "Precise accessible phrases such as 'replacement funding' and 'long gaps between services'; natural collocations without unnecessary rarity.",
                "grammar": "Controlled conditionals, relative clauses, qualification and varied sentence patterns; accuracy is sustained across the argument.",
            },
            "approximate_practice_range": [7.5, 8.5],
        },
    ]
)
