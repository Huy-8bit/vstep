import asyncio

from sqlalchemy.dialects.postgresql import insert

from app.db.session import SessionLocal, engine
from app.models import WritingQuestion
from app.services.question_generator import question_fingerprint

# Original practice material, not reproduced official exam papers.
TASK1 = [
    (
        "formal_email",
        "education",
        "You are interested in a summer English course at a language centre. Write an email to the course coordinator.",
        [
            "Introduce yourself and explain why you want to attend.",
            "Ask about the timetable and course fees.",
            "Ask what accommodation is available for students.",
        ],
    ),
    (
        "informal_email",
        "tourism",
        "Your English-speaking friend Alex is visiting your hometown next month and has asked for advice. Write an email to Alex.",
        [
            "Suggest the best time and way to travel to your town.",
            "Recommend two places to visit and explain why.",
            "Invite your friend to do something with you.",
        ],
    ),
    (
        "request",
        "work",
        "You need to take two days off work to attend a family event. Write an email to your manager requesting permission.",
        [
            "Explain which days you need off and why.",
            "Describe how you will complete your current work.",
            "Offer a way to handle urgent tasks while you are away.",
        ],
    ),
    (
        "complaint",
        "shopping",
        "You recently bought a desk online, but it arrived damaged and later than promised. Write an email to the shop's customer service team.",
        [
            "Give details of your order and delivery.",
            "Explain the problems and how they affected you.",
            "Say what you would like the shop to do.",
        ],
    ),
    (
        "apology",
        "family",
        "You promised to help your cousin move into a new flat this weekend, but you can no longer go. Write an email to your cousin.",
        [
            "Apologize and explain why your plans changed.",
            "Describe another way you can help.",
            "Suggest a time to visit the new flat.",
        ],
    ),
    (
        "invitation",
        "culture",
        "Your community is organizing a local food festival. Write an email inviting an English-speaking friend to attend with you.",
        [
            "Explain when and where the festival takes place.",
            "Describe the activities your friend might enjoy.",
            "Suggest how you will meet and ask for a reply.",
        ],
    ),
    (
        "giving_information",
        "sports",
        "An English-speaking friend wants to join your local sports club and has asked you about it. Write a reply.",
        [
            "Describe the facilities and activities.",
            "Explain the cost and opening hours.",
            "Recommend an activity you could do together.",
        ],
    ),
    (
        "asking_for_information",
        "transport",
        "You are planning a group visit to a nearby city. Write an email to a transport company asking about hiring a small bus.",
        [
            "Explain the date, route and number of passengers.",
            "Ask about prices and what is included.",
            "Ask how to make and change a booking.",
        ],
    ),
    (
        "thank_you_letter",
        "communication",
        "An English-speaking colleague helped you prepare an important presentation. Write an email to thank them.",
        [
            "Thank your colleague for their specific help.",
            "Explain how the presentation went.",
            "Suggest a way to show your appreciation.",
        ],
    ),
    (
        "giving_advice",
        "health",
        "Your friend Sam has started a new office job and finds it difficult to stay healthy. Write an email offering advice.",
        [
            "Respond to your friend's concerns.",
            "Suggest practical changes to daily habits.",
            "Explain how you can support your friend.",
        ],
    ),
]
TASK2 = [
    (
        "opinion",
        "education",
        "Some people believe that schools should teach practical skills, such as cooking and managing money, as well as academic subjects. What is your opinion? Give reasons and examples to support your answer.",
    ),
    (
        "agree_disagree",
        "technology",
        "Online learning is becoming more common. Some people think it can completely replace classroom learning. To what extent do you agree or disagree? Give reasons and examples.",
    ),
    (
        "discussion",
        "work",
        "Some people prefer working from home, while others believe that working in an office is better. Discuss both views and give your own opinion. Support your answer with reasons and examples.",
    ),
    (
        "advantages_disadvantages",
        "tourism",
        "More tourists are visiting small towns and rural communities. Discuss the advantages and disadvantages of this development for local people. Give reasons and examples.",
    ),
    (
        "problems_solutions",
        "environment",
        "Many communities produce increasing amounts of household waste. What problems does this cause, and what can individuals and local authorities do to address them? Give reasons and examples.",
    ),
    (
        "causes_solutions",
        "transport",
        "Traffic congestion is becoming worse in many cities. What are the main causes, and what solutions could reduce this problem? Support your ideas with reasons and examples.",
    ),
    (
        "causes_effects",
        "social_media",
        "Young people are spending more of their free time on social media. What are the causes of this trend, and how does it affect their daily lives? Give reasons and examples.",
    ),
    (
        "two_part_question",
        "health",
        "Many adults find it difficult to exercise regularly. Why is this the case? What can employers do to help their staff become more physically active? Give reasons and examples.",
    ),
    (
        "opinion",
        "city_life",
        "Some people think cities should create more public parks even if this reduces space for new buildings. What is your opinion? Support your answer with reasons and examples.",
    ),
    (
        "discussion",
        "family",
        "Some people think older relatives should live with their families, while others believe independent living is better for them. Discuss both views and give your own opinion. Give reasons and examples.",
    ),
]


async def seed():
    async with SessionLocal() as db:
        for task, items in ((1, TASK1), (2, TASK2)):
            for item in items:
                kind, topic, instruction = item[:3]
                values = dict(
                    task_type=task,
                    question_type=kind,
                    topic=topic,
                    test_profile="VSTEP_3_5",
                    instruction=instruction,
                    requirements=item[3] if task == 1 else [],
                    minimum_words=120 if task == 1 else 250,
                    source="SEED",
                    fingerprint=question_fingerprint(instruction),
                )
                await db.execute(
                    insert(WritingQuestion)
                    .values(**values)
                    .on_conflict_do_nothing(index_elements=["fingerprint"])
                )
        await db.commit()
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed())
