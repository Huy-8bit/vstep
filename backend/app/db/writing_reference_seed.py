"""Original correspondence and issue stimuli; never replace prompts attached to past attempts."""

from app.schemas.writing import GeneratedQuestion
from app.validators.questions import VALIDATOR_VERSION
from app.vstep_reference.specification import REFERENCE_VERSION
from app.vstep_reference.writing_blueprints import WRITING_BLUEPRINTS

TASK1 = [
    (
        "formal_email",
        "education",
        "course_organizer",
        "formal",
        "give_information",
        "Ms Carter, the organiser of a summer language course",
        "Thank you for your interest in our summer English programme. Before we suggest a suitable class, could you tell us a little about your reasons for studying English and the situations in which you expect to use it? We would also like to know whether morning or afternoon lessons would fit your other commitments. Some students stay with local families while others arrange their own accommodation. Please let us know which arrangement you would prefer and why.",
        [
            "Explain your reasons for studying English.",
            "Describe your availability for lessons.",
            "State and explain your accommodation preference.",
        ],
    ),
    (
        "informal_email",
        "tourism",
        "friend",
        "informal",
        "give_advice",
        "your English-speaking friend Oliver",
        "I have finally arranged some time off and would love to visit your town next month. I am still deciding whether to come by train or coach, so I would appreciate your advice about travelling there. I will only have two full days and would like to see something that tells me about local life, rather than just visit the busiest tourist spots. Which places would you recommend, and why? It would also be lovely to spend some time together if you are free.",
        [
            "Advise Oliver how to travel to your town.",
            "Recommend places that show local life and explain why.",
            "Suggest something to do together.",
        ],
    ),
    (
        "request",
        "work",
        "manager",
        "formal",
        "request_arrangements",
        "your manager, who is planning next month's work schedule",
        "I am preparing next month's schedule and would like everyone to tell me about any important commitments before I confirm the dates. If you need time away from work, please explain which days you would need and the reason for your request. I would also like to know how your current responsibilities could be managed while you are absent. We may need to contact somebody about urgent matters, so please suggest a practical arrangement for that as well.",
        [
            "Request time off and explain dates and reason.",
            "Explain how ongoing work will be managed.",
            "Suggest an arrangement for urgent matters.",
        ],
    ),
    (
        "complaint",
        "shopping",
        "service_provider",
        "formal",
        "report_problem",
        "the customer service team at a furniture shop",
        "We hope your new desk has arrived and would like to hear about your experience. Our delivery records show that there may have been a delay with some orders this week. If your purchase arrived late or in an unexpected condition, please describe what happened and explain how it affected your plans. We can discuss several ways of resolving a problem, so please also tell us what outcome you would consider reasonable. Your reply will help our team decide what to do next.",
        [
            "Describe the delivery or condition problem.",
            "Explain how the problem affected your plans.",
            "Request a reasonable resolution.",
        ],
    ),
    (
        "apology",
        "family",
        "relative",
        "informal",
        "apologize_and_rearrange",
        "your cousin, who is moving to a new flat",
        "Thanks again for offering to help me move this weekend. I am trying to work out who will be available and when, so could you confirm whether you can still come? I have several heavy boxes, but there are also smaller jobs that could be done on another day. If your plans have changed, please let me know what has happened and whether there is another way you could help. I would still love you to see the flat once everything is settled.",
        [
            "Apologize and explain why you cannot attend this weekend.",
            "Offer another way to help.",
            "Suggest a later visit.",
        ],
    ),
    (
        "invitation",
        "culture",
        "classmate",
        "informal",
        "invite",
        "your classmate Mia, who recently moved to your area",
        "I have enjoyed studying here so far, but I have not had many chances to meet people outside our class. You mentioned that there are sometimes community events near your home. Is there anything coming up that you think I might enjoy? I would be interested in learning about local food or traditions, especially if there are activities we could join together. If you have time to go with me, could you suggest when and where we might meet?",
        [
            "Invite Mia to a local event and give practical details.",
            "Explain which activities she might enjoy.",
            "Suggest how to meet and ask for a reply.",
        ],
    ),
    (
        "giving_information",
        "sports",
        "club",
        "semi-formal",
        "recommend_activities",
        "the coordinator of a sports club you attend",
        "We are preparing a welcome guide for new members and would value your experience of the club. Which facilities or activities do you think newcomers should know about first, and what makes them useful? Some people are worried that joining will be expensive or difficult to fit around work, so could you explain how you manage the cost and timing of your visits? We would also welcome a suggestion for an activity that existing and new members could enjoy together.",
        [
            "Describe useful club facilities and activities.",
            "Explain how visits fit your budget and schedule.",
            "Recommend a shared activity for members.",
        ],
    ),
    (
        "asking_for_information",
        "transport",
        "service_provider",
        "formal",
        "request_information",
        "a transport company after you enquired about a group trip",
        "Thank you for asking about transport for your group. We may be able to provide a small coach, but we need a few more details before preparing an offer. Could you tell us when you plan to travel, where you want to go and approximately how many people will join you? Please also let us know what you would like to find out about the price or services included. If you have questions about making or changing a booking, please include them in your reply.",
        [
            "Give travel date, route and group size.",
            "Ask about price and included services.",
            "Ask about booking or changes.",
        ],
    ),
    (
        "thank_you_letter",
        "communication",
        "host_family",
        "semi-formal",
        "thank_and_reflect",
        "the host family you stayed with during a short course",
        "It was lovely having you stay with us during your course, and we hope your journey home went smoothly. We would enjoy hearing which parts of your stay were most useful or memorable. Was there anything we did that particularly helped you feel comfortable or practise English? Please also tell us how you plan to use what you learned now that you are home. We hope we can stay in touch and perhaps see you again one day.",
        [
            "Thank the family for specific help.",
            "Explain what was useful or memorable and your plans to use it.",
            "Suggest how to stay in touch or meet again.",
        ],
    ),
    (
        "giving_advice",
        "health",
        "community_representative",
        "semi-formal",
        "give_advice",
        "a community centre organiser planning activities for office workers",
        "Several people who work in nearby offices have told us that they find it difficult to stay active during the week. We are considering a programme at the community centre and would welcome your suggestions. What activity would be suitable for people who have not exercised regularly for some time? We would also like your advice on when sessions should take place and how we could encourage people to attend. Please explain your suggestions so that we can plan something practical.",
        [
            "Suggest and explain a suitable activity.",
            "Recommend a practical time for sessions.",
            "Suggest how to encourage attendance.",
        ],
    ),
]
TASK2 = [
    (
        "opinion",
        "education",
        "Some schools are giving students more opportunities to learn practical skills, such as cooking, managing money and repairing everyday objects. Supporters believe these lessons prepare young people for independent life. Others feel that schools should devote most of their time to traditional academic subjects.",
        "give your opinion about the place of practical skills in school education",
        ["State your position.", "Develop reasons and relevant examples."],
    ),
    (
        "agree_disagree",
        "technology",
        "Digital devices allow people to complete many everyday tasks without asking another person for help. At the same time, online services can be difficult to use for people with limited access or experience. Some people believe that greater reliance on technology makes daily life easier for everyone.",
        "explain whether you agree with the view that technology makes daily life easier for everyone",
        ["State and maintain your position.", "Explain your reasons with relevant examples."],
    ),
    (
        "discussion",
        "work",
        "Working from home has become possible for more employees as communication tools have developed. Some workers value the flexibility and quieter environment. Others find it difficult to separate work from family life or to exchange ideas with colleagues when they rarely meet in person.",
        "discuss different views about working from home and give your own opinion",
        ["Discuss both perspectives.", "Explain your own position with reasons and examples."],
    ),
    (
        "advantages_disadvantages",
        "tourism",
        "Some towns now attract large numbers of visitors throughout the year. Tourism can create new opportunities for local businesses and encourage the restoration of public spaces. However, residents sometimes find that busy attractions, rising costs and changes to their neighbourhoods affect their daily lives.",
        "discuss the advantages and disadvantages of tourism for local residents",
        [
            "Develop advantages for residents.",
            "Develop disadvantages for residents.",
            "Support the discussion with relevant examples.",
        ],
    ),
    (
        "problems_solutions",
        "environment",
        "Many communities produce more household waste than their local services can easily manage. Packaging, unwanted food and items that are used only briefly all contribute to the problem. Although recycling facilities have expanded in some areas, a large amount of material is still thrown away.",
        "discuss problems caused by household waste and suggest practical solutions",
        ["Explain significant problems.", "Develop practical solutions with reasons and examples."],
    ),
    (
        "causes_solutions",
        "transport",
        "In many growing cities, journeys that once took a short time now involve long waits in traffic. Public transport is available in some neighbourhoods, but many residents continue to rely on private vehicles. Businesses and families both find it difficult to plan around unpredictable travel times.",
        "examine the causes of traffic congestion and suggest ways to reduce it",
        ["Explain causes of congestion.", "Develop solutions connected to those causes."],
    ),
    (
        "causes_effects",
        "social_media",
        "Young people can use social media to keep in touch, find entertainment and share their interests. For some, checking these services has become a frequent part of the day. Families and teachers have different opinions about why this habit develops and what it means for everyday relationships.",
        "examine why young people spend time on social media and the effects on their daily lives",
        ["Explain reasons for the trend.", "Develop effects with relevant examples."],
    ),
    (
        "two_part_question",
        "health",
        "Many adults say that regular exercise is important, yet struggle to make it part of their week. Long working hours, travel and family responsibilities can influence their choices. Some employers have begun offering activities or more flexible arrangements to support the health of their staff.",
        "explain why adults may struggle to exercise regularly and how employers could help",
        ["Explain barriers to regular exercise.", "Suggest and explain useful employer support."],
    ),
    (
        "opinion",
        "city_life",
        "As towns grow, local authorities must decide how to use limited space. New homes and workplaces are needed, but parks and other green areas also serve the community. People disagree about whether protecting public green space should take priority when new developments are being considered.",
        "give your opinion about protecting public green space in growing towns",
        ["Present a clear position.", "Develop reasons and relevant examples."],
    ),
    (
        "discussion",
        "family",
        "Living arrangements often change as people grow older. Some families prefer different generations to share a home, valuing daily contact and mutual support. Other older people wish to remain in their own homes, with assistance when necessary, because independence is important to them.",
        "discuss both living arrangements for older people and give your opinion",
        ["Discuss family living and independent living.", "Explain your view with supporting detail."],
    ),
]


def seed_questions():
    for kind, topic, relationship, register, purpose, sender, message, requirements in TASK1:
        yield GeneratedQuestion(
            task=1,
            question_type=kind,
            topic=topic,
            test_profile="VSTEP_3_5",
            instruction=f"You have received an email from {sender}. Read part of the email below.",
            stimulus=message,
            response_instruction=f"Write an email responding to {sender}.",
            requirements=requirements,
            minimum_words=120,
            genre="email",
            register=register,
            recipient_relationship=relationship,
            purpose=purpose,
        )
    for kind, topic, stimulus, assignment, requirements in TASK2:
        yield GeneratedQuestion(
            task=2,
            question_type=kind,
            topic=topic,
            test_profile="VSTEP_3_5",
            instruction="Read the following text about an issue in everyday life.",
            stimulus=stimulus,
            response_instruction=f"Write an essay to an educated reader to {assignment}. Include reasons and relevant examples to support your answer.",
            requirements=requirements,
            minimum_words=250,
            genre="essay",
            register="formal",
            recipient_relationship="educated_reader",
            purpose=kind,
        )


def seed_diagnostics(task):
    return {
        "generator_version": REFERENCE_VERSION,
        "validator_version": VALIDATOR_VERSION,
        "source_blueprint": WRITING_BLUEPRINTS[task]["id"],
        "generation_model": None,
        "format_valid": True,
        "quality_valid": True,
        "quality_method": "authored_synthetic_seed",
        "validation_notes": ["Original authored stimulus, deterministic format validation."],
    }
