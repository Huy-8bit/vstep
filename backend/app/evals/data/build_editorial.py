"""Rebuild the authored baseline. Scores are editorial estimates, NOT teacher ratings."""

import json
from pathlib import Path

from app.prompts.writing_calibration_anchors import ALEX_QUESTION, CALIBRATION_ANCHORS

KEYS = ("task_fulfillment", "organization", "vocabulary", "grammar")
samples = []


def add(identifier, task, question, answer, scores, tags, rationale, requirements):
    samples.append(
        dict(
            id=identifier,
            task=task,
            question=question,
            answer=answer,
            requirements=requirements,
            minimum_words=120 if task == 1 else 250,
            reference={**dict(zip(KEYS, scores)), "overall": sum(scores) / 4},
            source="internal_reference",
            reviewer_count=0,
            tags=tags,
            rationale=rationale,
        )
    )


alex_req = [
    "Suggest best time and transport with reasons",
    "Recommend two places and explain why",
    "Invite Alex to an activity together",
]
anchor_scores = {
    "weak": [2.5, 3, 2.5, 2],
    "borderline_b1": [5, 4.5, 4, 3.5],
    "solid_b1": [6, 6, 5.5, 6],
    "alex_manual_regression": [6.5, 6, 5.5, 5.5],
    "solid_b2": [7.5, 7.5, 7.5, 7.5],
    "strong_b2_c1": [8.5, 8.5, 8.5, 8.5],
    "essay_limited_development": [5, 5, 4.5, 4],
    "essay_developed_controlled": [8, 8, 8, 8],
}
for a in CALIBRATION_ANCHORS:
    if a["id"] in anchor_scores:
        add(
            a["id"],
            a["task"],
            a["question"],
            a["response"],
            anchor_scores[a["id"]],
            ["editorial_anchor", a["quality_reference"]],
            str(a["criterion_evidence"]),
            alex_req
            if a["task"] == 1
            else [
                "Discuss advantages of free public transport",
                "Discuss investment in service quality",
                "Explain your own view",
            ],
        )

add(
    "t1_short_controlled",
    1,
    ALEX_QUESTION,
    """Dear Alex,
I suggest coming on Saturday because I can meet you at the station. Take the direct train; it is cheaper than flying. Visit the market for local food and the museum to learn about our town. Would you like to join my family for dinner? Let me know when you arrive.
Best wishes,
Mai""",
    [4.5, 5.5, 5, 6],
    ["short_task1", "accurate_but_undeveloped"],
    "Clear and mostly accurate; only about half the required length, little support and limited grammatical range.",
    alex_req,
)

add(
    "t1_long_repetitive",
    1,
    ALEX_QUESTION,
    """Dear Alex,
Thank you for your email. I am very happy about your visit and I want to give you some ideas. I think Saturday is a good day because Saturday is a good day for visiting. I am free on Saturday and many other people are free on Saturday too. You can come by bus. The bus is good because it is cheap. It takes two hours, so you can leave early and arrive before lunch.
The market is a good place to visit. There are many shops and many people. You can buy food and clothes. I go to this market every week and I think it is a good market. Another place is the museum. The museum has pictures and old things. The pictures are interesting and the old things are interesting too. You can see many things and learn about our town.
I want to invite you to dinner at my house. My mother can cook some food. We can eat the food and talk about your trip. After dinner, we can watch television. It will be a good evening because we can spend time together. Please tell me what time you will arrive. I am looking forward to seeing you and I hope you will enjoy the trip.
Best wishes,
Mai""",
    [6, 5.5, 4.5, 5.5],
    ["long_task1", "basic_vocabulary", "repetition"],
    "Length does not establish sophistication: all requests addressed with generic reasons, repeated lexis and almost exclusively simple structures.",
    alex_req,
)

complaint = "You recently attended a weekend photography course. Write to the manager explaining two problems with the course, describing their effects, and requesting a reasonable solution. Write at least 120 words."
add(
    "t1_grammar_strong_task_weak",
    1,
    complaint,
    """Dear Manager,
I am writing to thank you for the photography course that I attended last weekend. Although I had previously taken photographs with my phone, I had never used a professional camera, so the opportunity was particularly welcome.
The building, which stands near the railway station, was easy to find. I arrived early and spent some time looking at the photographs displayed in the entrance hall. Their striking colours encouraged me to experiment with different settings during the afternoon. I also enjoyed meeting the other participants, several of whom had travelled from neighbouring towns.
Since returning home, I have practised taking pictures of the garden whenever the light has been suitable. I would be grateful if you could let me know when your next course will be offered, as I would like to develop these skills further.
Yours faithfully,
Lan""",
    [2.5, 7, 7, 7.5],
    ["strong_grammar_weak_task", "register"],
    "Well-controlled formal letter; does not identify the requested course problems, effects or remedy. Language must not compensate for task failure.",
    [
        "Explain two problems with the course",
        "Describe effects of those problems",
        "Request a reasonable solution",
    ],
)

essay = "Some people believe university students should work part-time while studying. Others think they should focus entirely on their studies. Discuss both views and give your own opinion. Write at least 250 words."
req = [
    "Discuss reasons for part-time work",
    "Discuss reasons to focus only on studies",
    "Give and support your own opinion",
]
add(
    "t2_content_good_language_weak",
    2,
    essay,
    """Many student work when they study at university. Some people thinks this is useful while others says students should only learning. I believe a small job can help, but university work must be first because students come there for education.
There are several reason to take a job. First, students can earn money for food and books. For example, my cousin work in a cafe on Saturday and she use this money to buy her textbooks. Her parents does not have to pay all her costs. Working also teach responsibility. When a customer complain, students must listen and solve the problem. These experience may help them in a future job where teamwork are important.
However, a job can create serious problems if it takes too much time. A student who works every evening may sleep less and cannot concentrate in class. My friend missed a laboratory session because his manager ask him to cover another worker. He had to repeat the work and his result was lower. Students in medicine or engineering may need many hours for practical work, so a regular job is not always possible.
In my opinion, the best choice depend on the student and the course. Universities could help students find flexible jobs on campus. Employers should allow them reduce their hours before exams. Students should also check their marks and stop working if their study becomes worse.
In conclusion, part-time work offer useful money and practical skills, but too many hours can damage education. A limited and flexible job is sensible when the student can still meet the requirements of the course.""",
    [7, 6.5, 5.5, 4.5],
    ["task2", "good_content_poor_grammar", "multiple_basic_errors"],
    "Relevant position, both views and concrete mechanisms/examples; repeated subject-verb, determiner, plural and infinitive errors materially restrict grammar.",
    req,
)

add(
    "t2_collocation_boundary",
    2,
    essay,
    """Whether students should combine paid employment with university study is a difficult question. A job can give useful experience, but it can also make pressure on students. I think students should work only a few hours each week, and they should stop when examinations are close.
Supporters of part-time work often point to financial benefits. Students can make an income and pay for small daily expenses without asking their parents for everything. They can also obtain practical experience. For instance, a student working in a shop may learn to communicate with customers and organise tasks. This can make advantages when the student later applies for a full-time position. Work may therefore connect classroom learning with real situations.
On the other hand, studying already requires a considerable amount of time. If students accept too many shifts, they may not have enough time to prepare assignments. Some students also become tired and lose attention during lectures. This can cause a negative consequence on their academic results. A difficult course with long laboratory sessions may leave almost no space for regular employment. Financial independence is useful, but it should not be reached by damaging education.
I believe universities should give advice about balancing these responsibilities. Jobs on campus may be suitable because managers understand examination schedules. Students should choose a realistic number of hours and review this decision if their grades begin to fall. They should not feel that everyone must have a job simply because some classmates work.
To conclude, part-time work can benefit students, provided that it remains manageable. Flexible hours and careful planning are more important than earning as much money as possible.""",
    [7, 7, 5.5, 6.5],
    ["task2", "unnatural_collocations", "boundary_b2"],
    "Developed balanced discussion and generally controlled syntax, but repeated unnatural combinations and predictable range restrict lexical score.",
    req,
)

# Keep the dataset deliberately small and inspectable. References are authored before model runs.
path = Path(__file__).with_name("writing-v1.json")
path.write_text(
    json.dumps(
        {
            "version": "editorial-writing-2026-09-v1",
            "reference_policy": "Editorial estimates, not certified examiner scores. No evaluation references are sent to candidate models. Human reviews supersede these references.",
            "samples": samples,
        },
        ensure_ascii=False,
        indent=2,
    )
    + "\n"
)
print(f"{len(samples)} samples written to {path}")
