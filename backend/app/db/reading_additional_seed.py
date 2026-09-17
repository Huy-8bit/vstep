"""Original reading material illustrating insertion, completion and attitude items."""

PARAGRAPHS = [
    "On the first Saturday of each month, a community hall in Marlow becomes a repair cafe. Residents bring broken household objects and work alongside volunteers to repair them. The organisers initially measured success by counting the objects that left in working order. After three months, however, they noticed something puzzling. Several visitors whose repairs had failed still returned, while some people with repaired objects did not. Coordinator Mina decided to ask visitors what they valued. She discovered that learning to recognise a problem could matter as much as taking home a working appliance. The project needed a broader understanding of success.",
    "The conversations also revealed practical barriers. Some visitors could not describe the fault clearly, and volunteers sometimes began repairing an object without explaining their decisions. A new booking form asked people to describe what happened just before the object stopped working. It did not ask them to identify a technical cause. Visitors could also bring a photograph of an item that was too large to carry. These changes helped volunteers prepare, although they could not guarantee a repair. The cafe still refused dangerous electrical work and directed those cases to qualified professionals. Safety remained more important than increasing the number of completed jobs.",
    "The team changed the way they explained repairs. They printed a sequence of photographs showing how to remove the parts of a common bicycle brake. These numbers also appeared on small trays, so visitors could keep the removed parts in the same order. Volunteers asked each visitor to describe the next step before trying it. If the explanation was unclear, they demonstrated that step again. This took longer than doing everything themselves, but it gave visitors a chance to notice and correct misunderstandings. The aim was not to turn every visitor into an expert during a single afternoon.",
    "Not everyone welcomed the slower approach. A volunteer who had repaired bicycles for years worried that fewer visitors would be served. Mina acknowledged this concern and arranged separate places for quick assessments and longer learning sessions. Visitors were told how long each option might take before joining a queue. The team also stopped treating repeat visits as evidence that earlier teaching had failed. Someone might return with a different problem, or simply need reassurance before working independently. Attendance records alone could not show which explanation applied. Short conversations provided useful context that the numbers did not contain.",
    "After a year, the cafe reported both completed repairs and visitors' accounts of what they had learned. The reports did not establish that the new approach had caused every improvement: visitor numbers and volunteer availability had changed too. Nevertheless, many residents described feeling more confident about checking simple faults safely. Mina kept the old repair count because it was useful for planning supplies, but placed it beside these accounts instead of presenting it as the whole story. Other community projects could use the same principle when deciding what to measure. A convenient number may describe an activity without fully explaining its value.",
]


def additional_articles():
    # Answer keys and rationales are authored independently of option order.
    rows = [
        (
            "main_idea",
            "Which title best describes the passage?",
            1,
            "D",
            [
                ("Why local repair services should charge higher fees", "Bài không đề xuất thu phí cao hơn."),
                (
                    "How to become a qualified electrical engineer",
                    "Bài bàn một dự án cộng đồng, không hướng dẫn đào tạo kỹ sư.",
                ),
                (
                    "A method for repairing every broken appliance",
                    "Dự án thừa nhận có đồ không sửa được và giới hạn an toàn.",
                ),
                (
                    "Looking beyond repair totals to understand a community project's value",
                    "Toàn bài theo dõi việc bổ sung trải nghiệm học vào số đồ sửa được.",
                ),
            ],
        ),
        (
            "detail",
            "What did the new booking form ask visitors to do?",
            2,
            "B",
            [
                (
                    "State the technical cause of the fault",
                    "Mẫu không yêu cầu xác định nguyên nhân kỹ thuật.",
                ),
                (
                    "Describe what occurred just before the object stopped working",
                    "Đoạn 2 nêu chính xác yêu cầu mô tả sự việc trước khi đồ ngừng hoạt động.",
                ),
                (
                    "Promise that they would repair the object without help",
                    "Không có cam kết tự sửa trong mẫu.",
                ),
                (
                    "Confirm that the object was safe for electrical work",
                    "Việc điện nguy hiểm được chuyển cho chuyên gia, không giao khách xác nhận.",
                ),
            ],
        ),
        (
            "vocabulary",
            "The word 'barriers' in paragraph 2 is closest in meaning to",
            2,
            "A",
            [
                ("obstacles", "Những khó khăn thực tế cản trở việc tham gia và học cách sửa."),
                (
                    "boundaries of the building",
                    "Ngữ cảnh nói về mô tả lỗi và giải thích, không phải ranh giới nhà.",
                ),
                ("repair instructions", "Hướng dẫn là một giải pháp cho khó khăn, không phải nghĩa của từ."),
                ("measurements", "Các trở ngại thực tế không phải số đo."),
            ],
        ),
        (
            "reference",
            "The word 'those' in 'directed those cases' in paragraph 2 refers to",
            2,
            "C",
            [
                (
                    "items that were too large to carry",
                    "Đồ quá lớn được chụp ảnh, không nhất thiết cần chuyên gia điện.",
                ),
                ("faults described on every booking form", "Không phải tất cả lỗi đều được chuyển đi."),
                (
                    "cases involving dangerous electrical work",
                    "Cụm này nối trực tiếp với việc từ chối sửa điện nguy hiểm.",
                ),
                (
                    "visitors returning after a successful repair",
                    "Việc quay lại không phải đối tượng được chuyển cho chuyên gia.",
                ),
            ],
        ),
        (
            "sentence_insertion",
            "In which position in paragraph 3 would the following sentence best fit? Each photograph was numbered to show the order in which the parts should be removed.",
            3,
            "B",
            [
                (
                    "Position [A]",
                    "Ở A các bức ảnh chưa được giới thiệu, nên 'Each photograph' thiếu đối tượng rõ ràng.",
                ),
                (
                    "Position [B]",
                    "B nối việc giới thiệu ảnh với 'These numbers' và giải thích nguồn của các số trên khay.",
                ),
                ("Position [C]", "Ở C, 'These numbers' đã xuất hiện trước câu giải thích nguồn của các số."),
                (
                    "Position [D]",
                    "D chen vào phần đánh giá cách dạy và vẫn để 'These numbers' thiếu thông tin phía trước.",
                ),
            ],
        ),
        (
            "negative_detail",
            "Which action is NOT described as part of the cafe's revised approach?",
            4,
            "D",
            [
                ("Separating quick assessments from longer sessions", "Đoạn 4 nêu hai khu vực riêng."),
                (
                    "Telling visitors about likely waiting times",
                    "Khách được báo thời gian trước khi xếp hàng.",
                ),
                (
                    "Asking returning visitors about their circumstances",
                    "Những cuộc nói chuyện ngắn cung cấp bối cảnh của lần quay lại.",
                ),
                (
                    "Requiring returning visitors to complete a written examination",
                    "Không có kỳ kiểm tra viết bắt buộc trong cách làm mới.",
                ),
            ],
        ),
        (
            "inference",
            "What can be inferred about repeat visits from paragraph 4?",
            4,
            "A",
            [
                (
                    "Their meaning depends on information beyond attendance records",
                    "Một lần quay lại có thể do vấn đề mới hoặc cần tự tin; chỉ con số không phân biệt được.",
                ),
                (
                    "They usually prove that an earlier repair was unsafe",
                    "Đoạn không suy ra mất an toàn từ việc quay lại.",
                ),
                (
                    "They should count as successful repairs even if no object is repaired",
                    "Không đề xuất cộng lần ghé vào số sửa thành công.",
                ),
                (
                    "They show that visitors no longer want to learn independently",
                    "Cần sự trấn an trước khi tự làm không có nghĩa từ bỏ tự học.",
                ),
            ],
        ),
        (
            "attitude",
            "Which best describes the author's attitude towards the revised approach?",
            5,
            "C",
            [
                (
                    "Sceptical that visitors can learn anything useful",
                    "Tác giả ghi nhận sự tự tin và việc học của người tham gia.",
                ),
                (
                    "Convinced that it alone explains all reported improvements",
                    "Đoạn cuối nói chưa xác định được nguyên nhân của mọi cải thiện.",
                ),
                (
                    "Supportive of its wider perspective while cautious about causal claims",
                    "Tác giả đánh giá tích cực góc nhìn rộng nhưng lưu ý các yếu tố khác cũng thay đổi.",
                ),
                (
                    "Mainly concerned that it will eliminate professional repair work",
                    "Bài không lo thay thế thợ chuyên nghiệp, và vẫn chuyển ca nguy hiểm cho họ.",
                ),
            ],
        ),
        (
            "paragraph_completion",
            "Which sentence would best complete the final paragraph after its current last sentence?",
            5,
            "A",
            [
                (
                    "Listening to participants can therefore help a project interpret its figures more meaningfully.",
                    "Câu kết nối nguyên tắc đo lường ở cuối bài với việc thêm trải nghiệm của người tham gia.",
                ),
                (
                    "Community projects should therefore stop collecting numerical records altogether.",
                    "Mina vẫn giữ số lượng sửa để lên kế hoạch; bỏ toàn bộ số liệu trái thông điệp.",
                ),
                (
                    "The increase in confidence therefore proves that every visitor can safely repair electrical faults.",
                    "Không được suy ra năng lực sửa điện nguy hiểm từ sự tự tin.",
                ),
                (
                    "A project should therefore judge its value only by how quickly it serves its longest queue.",
                    "Chỉ đo tốc độ trái việc cần hiểu cả trải nghiệm học tập.",
                ),
            ],
        ),
        (
            "purpose",
            "Why does the author mention changes in visitor numbers and volunteer availability?",
            5,
            "D",
            [
                (
                    "To explain why the cafe abandoned its repair count",
                    "Cafe vẫn giữ số lượng sửa, không bỏ cách đo này.",
                ),
                (
                    "To argue that personal accounts should never be recorded",
                    "Những chia sẻ vẫn được dùng cùng số liệu.",
                ),
                (
                    "To show that every visitor had received identical support",
                    "Tình hình thay đổi không chứng minh hỗ trợ như nhau.",
                ),
                (
                    "To identify other factors that make a simple causal conclusion uncertain",
                    "Các yếu tố thay đổi khiến không thể quy mọi cải thiện cho phương pháp mới.",
                ),
            ],
        ),
    ]
    questions = []
    for index, (kind, stem, paragraph, key, choices) in enumerate(rows):
        q = {
            "question_number": index + 1,
            "question_type": kind,
            "question_text": stem,
            "internal_difficulty_band": "CHALLENGING"
            if kind in {"inference", "attitude", "sentence_insertion"}
            else "MODERATE",
            "options": dict(zip("ABCD", [c[0] for c in choices])),
            "correct_answer": key,
            "explanation_vi": choices["ABCD".index(key)][1],
            "option_explanations": {
                letter: {"is_correct": letter == key, "explanation_vi": explanation}
                for letter, (_, explanation) in zip("ABCD", choices)
            },
            "evidence": {"paragraph_id": f"p{paragraph}", "quote": PARAGRAPHS[paragraph - 1]},
            "placement": None,
        }
        if kind == "sentence_insertion":
            q["placement"] = {
                "paragraph_id": "p3",
                "sentence_to_insert": "Each photograph was numbered to show the order in which the parts should be removed.",
                "positions": [
                    {"label": label, "after_text": text}
                    for label, text in zip(
                        "ABCD",
                        [
                            "The team changed the way they explained repairs.",
                            "They printed a sequence of photographs showing how to remove the parts of a common bicycle brake.",
                            "These numbers also appeared on small trays, so visitors could keep the removed parts in the same order.",
                            "The aim was not to turn every visitor into an expert during a single afternoon.",
                        ],
                    )
                ],
            }
        questions.append(q)
    return [
        {
            "title": "A Repair Cafe Learns to Listen",
            "topic": "society",
            "test_profile": "VSTEP_3_5",
            "internal_difficulty_band": "MODERATE",
            "paragraphs": [{"id": f"p{i + 1}", "text": text} for i, text in enumerate(PARAGRAPHS)],
            "questions": questions,
        }
    ]
