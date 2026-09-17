"""Idempotent, original VSTEP.3-5 practice prompts: 15 sets per VSTEP Speaking part."""

import asyncio

from sqlalchemy.dialects.postgresql import insert

from app.db.session import SessionLocal, engine
from app.models.speaking import SpeakingQuestion
from app.schemas.speaking import GeneratedSpeakingQuestion
from app.services.speaking_question_generator import speaking_fingerprint
from app.validators.questions import SpeakingQuestionValidator
from app.vstep_reference.speaking_blueprints import SPEAKING_BLUEPRINTS

# Each Part 1 set has two familiar topics and six short questions.
PART1 = [
    (
        "sports",
        "Sports",
        [
            "Do you enjoy playing sports?",
            "What sport do you play most often?",
            "How does playing sports help you?",
        ],
        "Shopping",
        [
            "Where do you usually go shopping?",
            "Do you prefer shopping online or in a shop?",
            "What did you buy recently?",
        ],
    ),
    (
        "family",
        "Family",
        [
            "Who do you live with?",
            "What do you enjoy doing with your family?",
            "Who in your family do you talk to most?",
        ],
        "Food",
        [
            "What is your favourite food?",
            "Do you often cook at home?",
            "What food would you recommend to a visitor?",
        ],
    ),
    (
        "travel",
        "Travel",
        [
            "Do you enjoy travelling?",
            "Where did you go on your last trip?",
            "Who do you prefer to travel with?",
        ],
        "Holidays",
        [
            "What do you usually do during public holidays?",
            "Which holiday do you like most?",
            "Would you like to spend a holiday abroad?",
        ],
    ),
    (
        "education",
        "Study",
        [
            "What subject do you enjoy studying?",
            "Do you prefer studying alone or with friends?",
            "Where do you usually study?",
        ],
        "Music",
        [
            "What kind of music do you listen to?",
            "When do you usually listen to music?",
            "Would you like to learn a musical instrument?",
        ],
    ),
    (
        "work",
        "Work",
        [
            "What kind of work would you like to do?",
            "What makes a workplace enjoyable?",
            "Do you prefer working indoors or outdoors?",
        ],
        "Daily routines",
        [
            "What time do you usually get up?",
            "What do you do after work or study?",
            "What would you like to change about your routine?",
        ],
    ),
    (
        "technology",
        "Technology",
        [
            "What do you use your phone for?",
            "Which app do you find most useful?",
            "Could you spend a day without your phone?",
        ],
        "Friends",
        [
            "How often do you meet your friends?",
            "What do you usually do together?",
            "What do you value in a friend?",
        ],
    ),
    (
        "books",
        "Books",
        [
            "Do you like reading books?",
            "What kind of books interest you?",
            "Do you prefer printed books or e-books?",
        ],
        "Films",
        [
            "What kinds of films do you enjoy?",
            "Do you prefer watching films at home or at the cinema?",
            "Tell me about a film you watched recently.",
        ],
    ),
    (
        "health",
        "Health",
        [
            "What do you do to stay healthy?",
            "Do you get enough sleep?",
            "Is there a healthy habit you would like to develop?",
        ],
        "Weekends",
        [
            "What do you usually do at weekends?",
            "Do you prefer a busy or a quiet weekend?",
            "What did you do last weekend?",
        ],
    ),
    (
        "hometown",
        "Hometown",
        [
            "Where is your hometown?",
            "What do you like most about it?",
            "Has your hometown changed since you were a child?",
        ],
        "Transportation",
        [
            "How do you usually get around?",
            "Do you often use public transport?",
            "What is your favourite way to travel short distances?",
        ],
    ),
    (
        "shopping",
        "Shopping",
        [
            "How often do you shop online?",
            "What do you consider before buying clothes?",
            "Do you enjoy shopping with other people?",
        ],
        "Gifts",
        [
            "What gifts do you like receiving?",
            "When did you last give someone a gift?",
            "Do you prefer making or buying gifts?",
        ],
    ),
    (
        "leisure",
        "Free time",
        [
            "What do you do in your free time?",
            "Do you prefer relaxing at home or going out?",
            "Is there a hobby you would like to try?",
        ],
        "Weather",
        [
            "What is the weather like where you live?",
            "What do you enjoy doing on sunny days?",
            "Does the weather affect your plans?",
        ],
    ),
    (
        "community",
        "Neighbours",
        [
            "Do you know your neighbours?",
            "What do you like about your neighbourhood?",
            "Is there anything you would improve in your local area?",
        ],
        "Pets",
        [
            "Do you like animals?",
            "Have you ever kept a pet?",
            "What should people consider before getting a pet?",
        ],
    ),
    (
        "environment",
        "Nature",
        [
            "Do you enjoy spending time in nature?",
            "Is there a park near your home?",
            "What do you do to keep your surroundings clean?",
        ],
        "Walking",
        [
            "Do you walk every day?",
            "Where do you enjoy walking?",
            "Do you prefer walking alone or with someone?",
        ],
    ),
    (
        "career",
        "Future plans",
        [
            "What skill would you like to learn?",
            "Where would you like to work in the future?",
            "Who helps you make important decisions?",
        ],
        "English",
        [
            "Why are you learning English?",
            "How do you practise speaking English?",
            "Which part of learning English do you enjoy most?",
        ],
    ),
    (
        "social_activities",
        "Celebrations",
        [
            "Do you enjoy attending parties?",
            "How do you usually celebrate your birthday?",
            "Do you prefer small gatherings or large parties?",
        ],
        "Photography",
        [
            "Do you often take photos?",
            "What do you like taking photos of?",
            "Do you prefer taking photos or being in them?",
        ],
    ),
]
PART2 = [
    (
        "education",
        "Your final examination is in two weeks. You have one free weekend and need to decide how to spend it.",
        ["Revise with a study group", "Join a family trip", "Attend a friend's sleepover"],
    ),
    (
        "family",
        "Your family would like to celebrate your grandparents' wedding anniversary on a modest budget.",
        ["Cook a special meal at home", "Book a meal at a restaurant", "Organise a weekend trip"],
    ),
    (
        "travel",
        "You and two friends have three days off and want a relaxing trip that everyone can afford.",
        ["Visit a nearby beach", "Go camping in the mountains", "Explore a large city"],
    ),
    (
        "shopping",
        "Your younger cousin needs a useful birthday gift for starting university. You have a limited budget.",
        ["A backpack", "A pair of wireless headphones", "A bookshop voucher"],
    ),
    (
        "health",
        "A friend wants to become more active but works long hours and has little money to spend.",
        ["Walk for thirty minutes each day", "Join a gym", "Take weekend swimming lessons"],
    ),
    (
        "work",
        "Your team wants to improve communication between colleagues who rarely meet in person.",
        [
            "Hold a short weekly video meeting",
            "Create a shared online discussion board",
            "Arrange a monthly team lunch",
        ],
    ),
    (
        "technology",
        "A small language club wants to help members practise English outside its weekly meetings.",
        ["Start a voice-message group", "Build a club website", "Buy subscriptions to a learning app"],
    ),
    (
        "leisure",
        "After a stressful semester, your class wants to organise a low-cost activity together.",
        ["Have a picnic in a local park", "Watch a film at the cinema", "Attend a live music show"],
    ),
    (
        "community",
        "Your neighbourhood has some funding for a project that should benefit residents of different ages.",
        [
            "Improve the public playground",
            "Create a small community library",
            "Organise free weekend exercise classes",
        ],
    ),
    (
        "transportation",
        "You have moved five kilometres from your workplace and need a reliable way to commute.",
        ["Take the bus", "Cycle to work", "Share a car with a colleague"],
    ),
    (
        "environment",
        "Your university wants students to produce less waste and can introduce one new programme this term.",
        [
            "Install water refill stations",
            "Hold a monthly second-hand market",
            "Run a reusable-container campaign",
        ],
    ),
    (
        "books",
        "Your local library wants to attract more young adults with a limited events budget.",
        ["Start a monthly book club", "Invite a local author to give a talk", "Organise a book exchange day"],
    ),
    (
        "sports",
        "Your school wants to choose one sports activity that most students can take part in after class.",
        ["A walking and running club", "A football tournament", "Weekly badminton sessions"],
    ),
    (
        "holidays",
        "You want to spend a public holiday with a visiting friend who has never been to your city.",
        ["Visit cultural landmarks", "Try local food at a market", "Take a day trip to the countryside"],
    ),
    (
        "career",
        "A final-year student wants to gain useful experience before applying for a first job.",
        [
            "Take a short internship",
            "Volunteer for a community project",
            "Complete an online professional course",
        ],
    ),
]
PART3 = [
    (
        "sports",
        "Playing sports brings several benefits to young people.",
        ["Improving physical health", "Reducing stress", "Making friends"],
        [
            "How can schools encourage students who do not enjoy competitive sports?",
            "Do you think exercising alone is as beneficial as playing team sports?",
        ],
    ),
    (
        "education",
        "Learning in groups can help students make progress.",
        ["Sharing knowledge", "Staying motivated", "Developing communication skills"],
        [
            "What problems can students face when working in groups?",
            "Should teachers let students choose their own study groups?",
        ],
    ),
    (
        "family",
        "Sharing housework can improve family life.",
        ["Saving time", "Building responsibility", "Strengthening relationships"],
        [
            "At what age should children start helping with housework?",
            "How has technology changed the way families do housework?",
        ],
    ),
    (
        "travel",
        "Travelling can be a valuable learning experience.",
        ["Understanding other cultures", "Becoming more independent", "Learning practical skills"],
        [
            "Can people learn about other cultures without travelling?",
            "How can travellers behave responsibly in local communities?",
        ],
    ),
    (
        "technology",
        "Technology has changed the way people communicate.",
        [
            "Keeping in touch over long distances",
            "Sharing information quickly",
            "Connecting people with similar interests",
        ],
        [
            "What are the disadvantages of relying on online communication?",
            "Will face-to-face communication become less important in the future?",
        ],
    ),
    (
        "books",
        "Reading regularly can improve people's lives.",
        ["Expanding knowledge", "Developing imagination", "Helping people relax"],
        [
            "How can parents encourage children to read?",
            "Do you think digital books will replace printed books?",
        ],
    ),
    (
        "health",
        "A healthy lifestyle depends on everyday habits.",
        ["Eating a balanced diet", "Getting enough sleep", "Being physically active"],
        [
            "Why do people sometimes find it difficult to maintain healthy habits?",
            "What can workplaces do to support employees' health?",
        ],
    ),
    (
        "community",
        "Volunteering is beneficial for both individuals and communities.",
        ["Helping people in need", "Learning new skills", "Building social connections"],
        [
            "Should volunteering be a requirement for university students?",
            "How can local organisations attract more volunteers?",
        ],
    ),
    (
        "environment",
        "Small changes at home can help protect the environment.",
        ["Saving electricity", "Reducing plastic waste", "Reusing household items"],
        [
            "What prevents some people from adopting environmentally friendly habits?",
            "Who should take more responsibility for environmental protection: individuals or businesses?",
        ],
    ),
    (
        "work",
        "Working from home offers several advantages.",
        ["Saving commuting time", "Having a flexible schedule", "Creating a comfortable workspace"],
        [
            "What challenges might remote workers face?",
            "Which kinds of jobs still need people to work in person?",
        ],
    ),
    (
        "transportation",
        "Good public transport can improve life in cities.",
        ["Reducing traffic congestion", "Lowering travel costs", "Improving access to work and study"],
        [
            "What would encourage more people to use public transport?",
            "Should public transport be free for students?",
        ],
    ),
    (
        "leisure",
        "Having a hobby is important for a balanced life.",
        ["Managing stress", "Developing creativity", "Meeting new people"],
        [
            "Why do some adults give up their hobbies?",
            "Can a hobby become less enjoyable when it turns into a job?",
        ],
    ),
    (
        "shopping",
        "Buying local products can benefit a community.",
        ["Supporting small businesses", "Creating local jobs", "Reducing transport distances"],
        [
            "Why do some shoppers prefer large international brands?",
            "How can local shops compete with online retailers?",
        ],
    ),
    (
        "career",
        "Learning new skills throughout life is increasingly useful.",
        ["Improving job opportunities", "Adapting to change", "Building confidence"],
        [
            "What difficulties do working adults face when returning to education?",
            "Should employers pay for their employees to learn new skills?",
        ],
    ),
    (
        "social_activities",
        "Community events can bring people together.",
        ["Celebrating local culture", "Helping neighbours meet", "Creating a sense of belonging"],
        [
            "How can organisers make events accessible to different age groups?",
            "Can online events create the same sense of community as in-person events?",
        ],
    ),
]


def speaking_seed_data():
    common = dict(
        topic_sets=[],
        situation=None,
        options=[],
        suggested_ideas=[],
        follow_up_questions=[],
        allow_own_idea=False,
        test_profile="VSTEP_3_5",
    )
    for code, first, questions, second, more in PART1:
        yield GeneratedSpeakingQuestion(
            **{
                **common,
                "part": 1,
                "question_type": "social_interaction",
                "topic": code,
                "question_text": f"Let us talk about {first.lower()} and {second.lower()}.",
                "topic_sets": [
                    {"topic": first, "questions": questions},
                    {"topic": second, "questions": more},
                ],
            }
        )
    for code, situation, options in PART2:
        yield GeneratedSpeakingQuestion(
            **{
                **common,
                "part": 2,
                "question_type": "solution_discussion",
                "topic": code,
                "question_text": "Which option would be the best choice? Explain your reasons and discuss the other options.",
                "situation": situation,
                "options": options,
            }
        )
    for code, topic, ideas, followups in PART3:
        yield GeneratedSpeakingQuestion(
            **{
                **common,
                "part": 3,
                "question_type": "topic_development",
                "topic": code,
                "question_text": topic,
                "suggested_ideas": ideas,
                "allow_own_idea": True,
                "follow_up_questions": followups,
            }
        )


async def seed():
    async with SessionLocal() as db:
        for question in speaking_seed_data():
            SpeakingQuestionValidator().validate(question)
            diagnostics = {
                "generator_version": "3.0.0",
                "validator_version": "3.0.0",
                "source_blueprint": SPEAKING_BLUEPRINTS[question.part]["id"],
                "generation_model": None,
                "format_valid": True,
                "quality_valid": True,
                "quality_method": "authored_synthetic_seed",
                "validation_notes": ["Original conversational prompts with editorial structure."],
            }
            data = question.model_dump(exclude={"allow_own_idea"})
            await db.execute(
                insert(SpeakingQuestion)
                .values(
                    **data,
                    source="SEED",
                    fingerprint=speaking_fingerprint(data),
                    generation_diagnostics=diagnostics,
                )
                .on_conflict_do_update(
                    index_elements=["fingerprint"], set_={"generation_diagnostics": diagnostics}
                )
            )
        await db.commit()
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed())
