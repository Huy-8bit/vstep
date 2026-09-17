"""Original teaching materials; no extracts from copyrighted exam papers."""

import asyncio

from sqlalchemy import select

from app.db.session import SessionLocal, engine
from app.models.reading import ReadingPassage
from app.schemas.reading import GeneratedReadingPassage
from app.services.reading_question_generator import passage_from_generated

ARTICLES = []


def article(title, topic, level, paragraphs, questions):
    # Authored correct option is first; position rotates in a nonsequential pattern.
    pattern = [1, 3, 0, 2, 0, 1, 3, 2, 1, 0]
    items = []
    offset = len(ARTICLES) % 4
    for i, (kind, text, paragraph, answers) in enumerate(questions):
        position = (pattern[i] + offset) % 4
        arranged = answers[1:].copy()
        arranged.insert(position, answers[0])
        key = "ABCD"[position]
        items.append(
            dict(
                question_number=i + 1,
                question_type=kind,
                question_text=text,
                options={letter: option[0] for letter, option in zip("ABCD", arranged)},
                correct_answer=key,
                explanation_vi=f"Đáp án {key} đúng. {answers[0][1]}",
                option_explanations={
                    letter: {"is_correct": letter == key, "explanation_vi": option[1]}
                    for letter, option in zip("ABCD", arranged)
                },
                evidence={"paragraph_id": f"p{paragraph}", "quote": paragraphs[paragraph - 1]},
            )
        )
    ARTICLES.append(
        dict(
            title=title,
            topic=topic,
            difficulty=level,
            paragraphs=[{"id": f"p{i + 1}", "text": text} for i, text in enumerate(paragraphs)],
            questions=items,
        )
    )


article(
    "A Library Beyond Its Walls",
    "education",
    "B1",
    [
        "When the library in the small town of Bellford reviewed its visitor numbers, staff noticed a problem. Many adults said they wanted to read more, but they rarely entered the building. Some finished work after the library closed. Others lived too far away to visit regularly. The manager, Anna, decided that the answer was not simply to buy more books. She first needed to understand how people used their time. For two weeks, library staff spoke to passengers at the bus station and parents waiting outside a primary school. Their conversations helped shape a different kind of library service.",
        "The staff then placed small shelves in three locations: a bus station, a community centre and a local bakery. Each shelf held about sixty books, including short novels, practical guides and books for children. People could take a book without showing a library card and return it to any of the three shelves. There was no fixed return date. Anna hoped this simple arrangement would attract people who worried about late fees. A notice asked readers to return books when they had finished, so that someone else could enjoy them. The books remained public property rather than gifts to individual readers.",
        "At first, a few volunteers worried that all the books would disappear. However, most readers brought them back, and some donated books of their own. They also left short messages recommending stories to the next reader. The volunteers visited each shelf twice a week to tidy it and check the books. Damaged copies were removed, while books that nobody borrowed were moved to another location. Children's stories were particularly popular at the bakery, where families often waited for fresh bread. The staff learned that the same collection did not work equally well in every place.",
        "The project did not replace the main library. Instead, it introduced new readers to services they had not known about. A leaflet inside each book described free computer classes and evening reading groups. Several people who first borrowed a book at the bus station later joined these activities. Nevertheless, Anna did not judge success only by the number of new library members. A person who enjoyed one story during a long journey had also benefited. The shelves offered a convenient way to make reading part of an ordinary day, even for someone who never attended a formal library event.",
        "After six months, the library asked local people what should happen next. Many wanted more shelves, but the volunteers preferred to improve the existing ones before expanding. They suggested clearer signs and more books in languages spoken by local families. Anna agreed to make these changes first. The project had shown that a useful reading service could be small and flexible. It had also shown the value of listening before spending money. The town did not need an impressive new building to reach more readers; it needed to put suitable books where people already spent time.",
    ],
    [
        (
            "main_idea",
            "What is the passage mainly about?",
            1,
            [
                (
                    "Making library books easier to reach in everyday places",
                    "Bài mô tả cách đưa sách đến những nơi người dân thường có mặt.",
                ),
                (
                    "Replacing public libraries with private bookshops",
                    "Dự án vẫn duy trì thư viện chính; không thay bằng hiệu sách.",
                ),
                (
                    "Teaching children to write their own novels",
                    "Không có hoạt động dạy viết tiểu thuyết trong bài.",
                ),
                (
                    "Raising money for a larger library building",
                    "Kết luận nói không cần một tòa nhà mới ấn tượng.",
                ),
            ],
        ),
        (
            "detail",
            "Where could readers return a borrowed book?",
            2,
            [
                ("To any of the three shelves", "Đoạn 2 cho phép trả sách ở bất kỳ kệ nào trong ba kệ."),
                ("Only to the main library desk", "Quy định không yêu cầu đến quầy thư viện chính."),
                ("Only to the shelf where they borrowed it", "Bài nói bất kỳ kệ nào, không chỉ kệ ban đầu."),
                ("To the primary school office", "Trường học là nơi khảo sát, không phải điểm trả sách."),
            ],
        ),
        (
            "vocabulary",
            "The word 'convenient' in paragraph 4 is closest in meaning to...",
            4,
            [
                (
                    "easy to use",
                    "Trong ngữ cảnh này, convenient là thuận tiện để đưa việc đọc vào sinh hoạt.",
                ),
                ("expensive to maintain", "Từ này không nói đến chi phí duy trì."),
                ("difficult to understand", "Convenient nhấn mạnh sự thuận tiện, không phải khó hiểu."),
                ("available only at night", "Không có giới hạn chỉ dùng vào ban đêm."),
            ],
        ),
        (
            "reference",
            "The word 'They' in the third sentence of paragraph 3 refers to...",
            3,
            [
                ("readers", "Chủ thể trước đó là những người đọc mang sách trở lại; họ để lại lời nhắn."),
                ("library managers", "Không phải những người quản lý; câu trước nói về readers."),
                ("children's stories", "Truyện không thể để lại lời nhắn cho người đọc."),
                (
                    "bus passengers interviewed by staff",
                    "Nhóm khảo sát không phải chủ thể được nhắc ngay trước đại từ.",
                ),
            ],
        ),
        (
            "inference",
            "What can be inferred about choosing books for the shelves?",
            3,
            [
                (
                    "The location can influence which books are useful",
                    "Truyện thiếu nhi được ưa thích tại tiệm bánh; bộ sách cần phù hợp từng nơi.",
                ),
                (
                    "Every shelf should contain exactly the same books",
                    "Đoạn 3 trực tiếp nói bộ sách giống nhau không hiệu quả như nhau ở mọi nơi.",
                ),
                (
                    "Practical guides should never be included",
                    "Đoạn 2 có sách hướng dẫn; không có yêu cầu loại bỏ.",
                ),
                (
                    "Readers prefer damaged books to new copies",
                    "Sách hỏng được loại ra; không có sở thích như vậy.",
                ),
            ],
        ),
        (
            "purpose",
            "Why does the author mention the leaflet inside each book?",
            4,
            [
                (
                    "To show how the shelves connect readers with other library services",
                    "Tờ giới thiệu giúp người đọc biết đến lớp máy tính và nhóm đọc.",
                ),
                (
                    "To explain how late fees are calculated",
                    "Dự án không có ngày trả cố định hoặc cách tính phí như vậy.",
                ),
                ("To advertise books for sale", "Sách thuộc tài sản công, không được rao bán."),
                (
                    "To describe a compulsory membership form",
                    "Tờ giới thiệu không phải mẫu đăng ký bắt buộc.",
                ),
            ],
        ),
        (
            "negative_detail",
            "Which service is NOT mentioned in paragraph 4?",
            4,
            [
                ("Paid writing courses", "Đoạn 4 không đề cập khóa viết có thu phí."),
                ("Free computer classes", "Lớp máy tính miễn phí được nêu rõ."),
                ("Evening reading groups", "Nhóm đọc buổi tối được nêu rõ."),
                ("Borrowing books at the bus station", "Việc mượn sách ở bến xe được mô tả ngay trong đoạn."),
            ],
        ),
        (
            "sentence_meaning",
            "What does 'The project did not replace the main library' mean?",
            4,
            [
                (
                    "The main library continued while the project added another way to borrow",
                    "Kệ sách bổ sung cách tiếp cận, còn thư viện chính vẫn hoạt động.",
                ),
                ("The main library closed when the shelves opened", "Điều này trái với did not replace."),
                ("Only existing members could use the shelves", "Đoạn 2 không yêu cầu thẻ thư viện."),
                (
                    "All books were moved out of the main library",
                    "Không có thông tin chuyển toàn bộ sách ra ngoài.",
                ),
            ],
        ),
        (
            "organization",
            "How is paragraph 5 mainly organized?",
            5,
            [
                (
                    "Feedback is presented, followed by a decision and a lesson",
                    "Đoạn nêu góp ý, quyết định cải thiện trước, rồi kết luận bài học.",
                ),
                (
                    "Several authors are compared by their sales",
                    "Không có số liệu bán sách hay so sánh tác giả.",
                ),
                ("A book is described chapter by chapter", "Đoạn nói về dự án, không tóm tắt một cuốn sách."),
                (
                    "Rules are listed without any explanation",
                    "Đoạn có lý do và bài học, không phải danh sách quy tắc.",
                ),
            ],
        ),
        (
            "tone",
            "What is the author's attitude towards the project?",
            5,
            [
                (
                    "Positive about its practical benefits",
                    "Tác giả đánh giá tích cực sự linh hoạt và khả năng tiếp cận người đọc.",
                ),
                (
                    "Angry about the loss of all library books",
                    "Hầu hết sách được trả; không có giọng tức giận này.",
                ),
                (
                    "Certain that it has solved every reading problem",
                    "Bài vẫn đề cập cải thiện và không tuyên bố giải quyết mọi vấn đề.",
                ),
                (
                    "Uninterested in what local people think",
                    "Lắng nghe người dân là bài học nổi bật của đoạn cuối.",
                ),
            ],
        ),
    ],
)

article(
    "Saturday at the Repair Table",
    "lifestyle",
    "B1",
    [
        "Every second Saturday, a room above the market in Mill Lane becomes a repair café. Visitors bring broken household objects and sit beside volunteers who help them understand what has gone wrong. There is tea and coffee, but repairing things is the main activity. The café began when a retired engineer called Ben noticed how many small appliances his neighbours threw away. Some needed only a new wire or a simple cleaning. He invited two friends to spend a morning helping local people. Their first event attracted twelve visitors, and several asked when they could come again with other objects.",
        "The café now uses a booking system because the room is small. A visitor describes the object when making an appointment, and a volunteer decides whether someone at the café has the right skills. Furniture, clothes and simple electrical items are common, but dangerous equipment is not accepted. Visitors do not pay for the volunteer's time, although they must buy any new parts that are needed. Sometimes a repair cannot be finished on the same day. In that case, the volunteer writes down which part is missing and explains where the visitor might find it. No successful repair is promised in advance.",
        "Ben insists that owners stay at the table while their objects are examined. He wants the café to be a learning place rather than a free shop where customers leave things and collect them later. The volunteers explain each step in everyday language. They may ask the owner to hold a tool or try a safe part of the repair. One visitor, Lucy, learned to replace a button on her coat. The following month she returned with another coat, but this time she helped a new visitor do the same job. A small lesson had already travelled from one person to another.",
        "Keeping useful objects out of the rubbish is an important aim, but the social side matters too. People who might never speak in the street often share stories while waiting for a repair. Older volunteers bring practical experience, while younger visitors sometimes know more about finding instructions online. Neither group has all the answers. When a radio could not be repaired, its owner still said the visit was worthwhile because he understood the problem and knew which questions to ask at a professional repair shop. For Ben, that kind of confidence is also a useful result of the morning's work.",
        "The café has limits. Volunteers cannot provide the same service as a business with specialist machines and a full range of spare parts. Organisers therefore display clear safety rules and send complicated cases to professionals. They also keep a notebook recording the objects brought in and whether repairs were completed. These notes help them decide which skills future volunteers should have. Ben would like more people to repair things, but he does not claim that every object can be saved. His message is simpler: before replacing something, find out whether a small repair could give it a longer life.",
    ],
    [
        (
            "main_idea",
            "What is the main purpose of the passage?",
            1,
            [
                (
                    "To describe a community place for repairing and learning",
                    "Bài giới thiệu repair café với hai chức năng sửa đồ và chia sẻ kỹ năng.",
                ),
                (
                    "To explain how to open an appliance factory",
                    "Không có hướng dẫn xây dựng nhà máy thiết bị.",
                ),
                ("To compare the prices of local coffee shops", "Trà và cà phê chỉ là hoạt động phụ."),
                (
                    "To argue that professional repair shops are unnecessary",
                    "Đoạn cuối vẫn chuyển ca phức tạp tới thợ chuyên nghiệp.",
                ),
            ],
        ),
        (
            "detail",
            "What must visitors pay for?",
            2,
            [
                (
                    "New parts needed for their objects",
                    "Đoạn 2 quy định khách trả tiền linh kiện mới nếu cần.",
                ),
                ("Every hour of the volunteer's work", "Thời gian tình nguyện viên là miễn phí."),
                ("A yearly membership card", "Không nêu thẻ thành viên hằng năm."),
                ("An examination before making a booking", "Không có phí kiểm tra trước khi đặt chỗ."),
            ],
        ),
        (
            "vocabulary",
            "The word 'worthwhile' in paragraph 4 means...",
            4,
            [
                (
                    "useful enough to be worth the effort",
                    "Dù radio chưa sửa được, chuyến đi vẫn đáng công vì người chủ hiểu vấn đề.",
                ),
                ("certain to produce money", "Lợi ích ở đây là hiểu biết, không phải tiền kiếm được."),
                (
                    "too difficult to continue",
                    "Chủ đồ đánh giá trải nghiệm hữu ích chứ không quá khó để tiếp tục.",
                ),
                ("possible only for experts", "Người chủ thông thường cũng hưởng lợi từ buổi gặp."),
            ],
        ),
        (
            "reference",
            "The word 'They' in paragraph 3 refers to...",
            3,
            [
                ("the volunteers", "Tình nguyện viên là người giải thích và yêu cầu chủ đồ hỗ trợ."),
                ("the broken objects", "Đồ vật không thể yêu cầu người chủ cầm dụng cụ."),
                ("the customers who have left", "Khách phải ở lại; câu đang nói về tình nguyện viên."),
                ("the local businesses", "Doanh nghiệp không phải chủ thể trong đoạn 3."),
            ],
        ),
        (
            "inference",
            "What does Lucy's second visit suggest?",
            3,
            [
                (
                    "Visitors can pass on skills they have learned",
                    "Lucy dùng kỹ năng đã học để giúp người mới, thể hiện việc truyền đạt kiến thức.",
                ),
                (
                    "Only clothing can be repaired at the café",
                    "Các đoạn khác còn có đồ nội thất và thiết bị điện đơn giản.",
                ),
                (
                    "Volunteers must all be retired engineers",
                    "Không có yêu cầu tất cả tình nguyện viên phải là kỹ sư nghỉ hưu.",
                ),
                (
                    "Lucy was required to pay for the first lesson",
                    "Bài không nêu học phí; thời gian hướng dẫn là miễn phí.",
                ),
            ],
        ),
        (
            "purpose",
            "Why does the author mention the radio that could not be repaired?",
            4,
            [
                (
                    "To show that a visit can help even without a completed repair",
                    "Người chủ vẫn hiểu vấn đề và tự tin trao đổi với cửa hàng sửa chữa.",
                ),
                (
                    "To prove that radios are always impossible to repair",
                    "Một trường hợp không chứng minh mọi radio đều không sửa được.",
                ),
                ("To explain why Ben closed the café", "Café không đóng cửa trong bài."),
                (
                    "To show that visitors dislike receiving explanations",
                    "Người chủ chính là người đánh giá lời giải thích hữu ích.",
                ),
            ],
        ),
        (
            "negative_detail",
            "Which item is NOT listed as common at the café?",
            2,
            [
                ("Dangerous equipment", "Đoạn 2 nói thiết bị nguy hiểm không được nhận."),
                ("Furniture", "Đồ nội thất được liệt kê rõ."),
                ("Clothes", "Quần áo được liệt kê rõ."),
                ("Simple electrical items", "Đồ điện đơn giản được liệt kê rõ."),
            ],
        ),
        (
            "sentence_meaning",
            "What does 'Neither group has all the answers' mean in paragraph 4?",
            4,
            [
                (
                    "Both age groups have useful knowledge and can learn from each other",
                    "Người lớn tuổi có kinh nghiệm thực hành, người trẻ biết tìm hướng dẫn; hai bên bổ sung nhau.",
                ),
                ("Nobody at the café knows anything useful", "Bài nêu rõ kiến thức hữu ích của cả hai nhóm."),
                (
                    "Young visitors should never help older volunteers",
                    "Điều này trái với việc chia sẻ kỹ năng giữa các nhóm.",
                ),
                (
                    "All repairs require two professional engineers",
                    "Không có quy định về hai kỹ sư chuyên nghiệp.",
                ),
            ],
        ),
        (
            "organization",
            "What does paragraph 5 do?",
            5,
            [
                (
                    "Explains limitations and ways the organisers manage them",
                    "Đoạn cuối nêu giới hạn, quy tắc an toàn, chuyển ca khó và ghi chép để cải thiện.",
                ),
                ("Gives a detailed history of the market building", "Không kể lịch sử tòa nhà chợ."),
                ("Lists the steps for repairing a particular radio", "Không có chỉ dẫn kỹ thuật sửa radio."),
                (
                    "Presents only visitors' complaints",
                    "Đoạn trình bày giải pháp quản lý, không chỉ lời phàn nàn.",
                ),
            ],
        ),
        (
            "tone",
            "Which best describes the writer's tone?",
            5,
            [
                (
                    "Encouraging but realistic",
                    "Bài khuyến khích sửa đồ nhưng thừa nhận không thể cứu mọi món đồ.",
                ),
                ("Hostile towards all new products", "Không thể hiện thái độ thù địch với mọi sản phẩm mới."),
                ("Certain that every repair will succeed", "Đoạn 2 và 5 đều bác bỏ sự bảo đảm này."),
                (
                    "Amused by people who lack practical skills",
                    "Người học được tôn trọng và giúp đỡ, không bị chế giễu.",
                ),
            ],
        ),
    ],
)

article(
    "When the Field Sends a Message",
    "technology",
    "B2",
    [
        "For years, farmers in the fictional Green Valley cooperative decided when to water their vegetables by examining the soil and watching the weather. Their methods were based on experience, but fields that looked similar from the road sometimes held very different amounts of moisture. During a particularly dry summer, the cooperative began a small project using electronic sensors. The devices measured moisture below the surface and sent readings to a shared phone application. The aim was not to remove farmers from the decision. It was to give them another source of information when water supplies were limited and a mistake could damage a crop.",
        "The first sensors were installed in only two fields, one sandy and one containing heavier soil. A technician explained that a single reading could not represent an entire farm. Water moved quickly through the sandy field, while the heavier soil held it for longer. Sensors were therefore placed at several depths and locations. Farmers compared their measurements with observations made during ordinary field walks. They discovered that a patch near an old drainage channel dried faster than the rest. Watering every part of the field for the same amount of time would have supplied too much water in some places and too little in others.",
        "The application displayed an alert when moisture fell below a level chosen for each crop. However, the alerts were recommendations rather than instructions. Before turning on irrigation, farmers considered whether rain was likely and whether the plants were at a stage when extra water was especially important. One morning, a sensor reported unusually dry soil immediately after heavy rain. A farmer checked the device and found that it had become loose. This incident helped the group understand why surprising data should be investigated rather than followed automatically. A precise number on a screen could still come from an incorrectly positioned instrument.",
        "The project also brought practical difficulties. Some farmers had weak phone signals, and others were not comfortable interpreting graphs. The cooperative responded by printing weekly summaries and holding short meetings where members discussed the readings together. A younger member often helped neighbours open the application, while experienced growers explained why the same moisture level could mean different things at different stages of growth. These exchanges made the system more useful than the equipment alone would have been. Training and local knowledge were not additional decorations on a technical project; they were part of what allowed it to function in everyday conditions.",
        "By the end of the season, the two trial fields had used less irrigation water than in the previous year. The farmers welcomed this result but avoided claiming that sensors alone had caused the reduction. Weather conditions and the choice of vegetables had also changed. The cooperative planned to compare similar fields over several seasons before buying equipment for every member. Its experience suggested that digital tools could support careful farming when measurements were interpreted in context. The most valuable change was not a field that could send messages, but a group of farmers who had learned which messages deserved further attention.",
    ],
    [
        (
            "main_idea",
            "Which statement best expresses the main idea of the passage?",
            5,
            [
                (
                    "Sensors can support farming when combined with human knowledge and careful interpretation",
                    "Kết luận nhấn mạnh diễn giải dữ liệu theo bối cảnh, kết hợp kinh nghiệm thay vì thay thế người nông dân.",
                ),
                (
                    "Farmers should replace all traditional observations with phone applications",
                    "Ngay đoạn 1 đã nói mục tiêu không loại người nông dân khỏi quyết định.",
                ),
                (
                    "Electronic equipment guarantees identical results in every field",
                    "Bài mô tả khác biệt giữa đất và lỗi thiết bị.",
                ),
                (
                    "The main obstacle to farming is the lack of weather forecasts",
                    "Dự án tập trung thông tin độ ẩm, không quy mọi vấn đề về dự báo.",
                ),
            ],
        ),
        (
            "detail",
            "Why were sensors placed at several depths and locations?",
            2,
            [
                (
                    "Moisture conditions varied within and between the fields",
                    "Đất cát, đất nặng và vùng gần rãnh thoát nước giữ nước khác nhau.",
                ),
                (
                    "All sensors had to remain above the soil",
                    "Thiết bị đo độ ẩm dưới mặt đất, không bắt buộc ở trên.",
                ),
                (
                    "The application could not display more than one field",
                    "Không nêu giới hạn ứng dụng như vậy.",
                ),
                (
                    "Farmers wanted to avoid walking through their fields",
                    "Nông dân vẫn đối chiếu dữ liệu với quan sát khi đi thăm ruộng.",
                ),
            ],
        ),
        (
            "vocabulary",
            "The word 'interpreting' in paragraph 4 is closest in meaning to...",
            4,
            [
                (
                    "understanding the meaning of",
                    "Interpreting graphs là hiểu và diễn giải ý nghĩa biểu đồ trong bối cảnh.",
                ),
                (
                    "changing the appearance of",
                    "Đoạn này nói khó hiểu dữ liệu, không phải sửa giao diện biểu đồ.",
                ),
                ("copying without checking", "Diễn giải đòi hỏi hiểu chứ không sao chép máy móc."),
                ("removing from a device", "Không nói đến việc xóa biểu đồ khỏi thiết bị."),
            ],
        ),
        (
            "reference",
            "The word 'They' in paragraph 2 refers to...",
            2,
            [
                (
                    "the farmers",
                    "Những người so sánh số đo và đi thăm ruộng chính là chủ thể phát hiện vùng khô nhanh.",
                ),
                ("the measurements", "Số đo không tự phát hiện một vùng đất."),
                ("the different crops", "Cây trồng không phải chủ thể của các hành động quan sát."),
                ("the drainage channels", "Rãnh thoát nước không thể thực hiện việc phát hiện."),
            ],
        ),
        (
            "inference",
            "What can be inferred from the loose sensor incident?",
            3,
            [
                (
                    "Unexpected measurements may require checking the equipment",
                    "Số liệu bất thường sau mưa được giải thích bằng thiết bị lỏng; cần kiểm tra thay vì làm theo ngay.",
                ),
                (
                    "Rain always causes soil to become drier",
                    "Kết quả đó là bất thường do thiết bị, không phải quy luật về mưa.",
                ),
                (
                    "All moisture measurements are useless",
                    "Bài chỉ nhấn mạnh kiểm tra dữ liệu bất thường, không phủ nhận mọi phép đo.",
                ),
                (
                    "The farmer should have irrigated immediately",
                    "Làm theo cảnh báo ngay có thể dẫn đến quyết định sai.",
                ),
            ],
        ),
        (
            "purpose",
            "Why does the writer describe the exchanges between younger and experienced members?",
            4,
            [
                (
                    "To show that technical skills and local experience complement each other",
                    "Kỹ năng dùng ứng dụng và kinh nghiệm cây trồng cùng giúp hệ thống hoạt động.",
                ),
                (
                    "To argue that older growers should stop farming",
                    "Kinh nghiệm của họ được xem là có ích, không phải trở ngại cần loại bỏ.",
                ),
                (
                    "To prove that printed summaries are always better than applications",
                    "Tài liệu in là giải pháp bổ sung cho một số người, không phải kết luận tuyệt đối.",
                ),
                ("To explain how to manufacture a sensor", "Đoạn không mô tả quy trình chế tạo thiết bị."),
            ],
        ),
        (
            "negative_detail",
            "Which consideration is NOT mentioned before farmers decide to irrigate in paragraph 3?",
            3,
            [
                (
                    "The selling price of the phone application",
                    "Đoạn 3 không nhắc giá bán ứng dụng khi quyết định tưới.",
                ),
                ("The likelihood of rain", "Khả năng có mưa được nêu rõ."),
                ("The plants' stage of growth", "Giai đoạn cây cần thêm nước được đề cập."),
                (
                    "Whether an unusual reading should be checked",
                    "Ví dụ cảm biến lỏng cho thấy cần kiểm tra số liệu bất thường.",
                ),
            ],
        ),
        (
            "sentence_meaning",
            "Which best restates 'the alerts were recommendations rather than instructions'?",
            3,
            [
                (
                    "Farmers were expected to judge an alert before acting on it",
                    "Cảnh báo là gợi ý để cân nhắc cùng thời tiết và cây trồng, không phải mệnh lệnh.",
                ),
                (
                    "Farmers were required to obey every alert immediately",
                    "Điều này đảo ngược sự phân biệt recommendations và instructions.",
                ),
                (
                    "The application never offered information about watering",
                    "Ứng dụng có cảnh báo liên quan trực tiếp đến tưới nước.",
                ),
                (
                    "The alerts could be understood only by technicians",
                    "Nông dân được hướng dẫn để tự cân nhắc các cảnh báo.",
                ),
            ],
        ),
        (
            "organization",
            "How is paragraph 4 mainly developed?",
            4,
            [
                (
                    "Practical problems are followed by responses and their significance",
                    "Đoạn nêu tín hiệu yếu/khó đọc biểu đồ, rồi giải pháp họp và hỗ trợ, sau đó giải thích ý nghĩa.",
                ),
                (
                    "A sequence of laboratory experiments is listed",
                    "Đoạn nói về khó khăn sử dụng thực tế, không liệt kê thí nghiệm phòng lab.",
                ),
                ("Two farming regions are compared by population", "Không có so sánh dân số giữa hai vùng."),
                (
                    "A prediction is presented without any supporting examples",
                    "Có nhiều ví dụ cụ thể về khó khăn và trao đổi kỹ năng.",
                ),
            ],
        ),
        (
            "tone",
            "What is the writer's attitude towards the reported water savings?",
            5,
            [
                (
                    "Encouraged but cautious about attributing the result to sensors alone",
                    "Tác giả ghi nhận giảm nước nhưng nhắc thời tiết và loại rau cũng thay đổi.",
                ),
                (
                    "Certain that the same savings will occur everywhere",
                    "Nhóm muốn so sánh thêm trước khi mở rộng, không bảo đảm mọi nơi.",
                ),
                (
                    "Dismissive of any value from the project",
                    "Bài thừa nhận giá trị công cụ khi diễn giải đúng.",
                ),
                (
                    "Convinced that the measurements were deliberately falsified",
                    "Không có lời cáo buộc cố tình làm giả số liệu.",
                ),
            ],
        ),
    ],
)

article(
    "A Garden Above the Street",
    "environment",
    "B2",
    [
        "From the pavement, the Hartwell office building looked much like the others on its crowded street. Above its top floor, however, a shallow garden had replaced part of a dark, unused roof. The building manager hoped the plants would make the roof more attractive and reduce the amount of rainwater flowing directly into the drains. During heavy storms, the street's drainage system often struggled to carry water away. A roof garden would not solve that problem by itself, but it offered a way to slow some of the water before it reached the ground. The project began with a practical question rather than a purely decorative ambition.",
        "Before planting anything, the owners asked an engineer to examine the roof. Wet soil can be considerably heavier than dry soil, so the structure had to support the garden after a storm, not just on a sunny afternoon. The design used a lightweight growing material and plants that could survive dry periods. Below the plants, a protective layer prevented roots from damaging the roof surface. Channels allowed excess water to leave safely. Without these preparations, an attractive garden could have created expensive problems for the offices below. The most important early work was therefore largely invisible once the plants had grown.",
        "When rain fell, the growing material absorbed some of it and the plants used part of the stored water. The remaining water reached the drainage channels more slowly than it would have crossed a bare roof. This delay mattered even when the garden could not hold all the rain. It reduced the sudden rush arriving in the street's drains at the same time. However, after several wet days, the material could already be full of water. The garden's ability to absorb more then became limited. Its performance depended on previous weather as well as on the size and intensity of the latest storm.",
        "Office workers also noticed changes during lunch breaks. They had once eaten beside noisy traffic, but now they could sit among plants when the weather allowed. A small group volunteered to check for dead plants and report blocked channels. Their interest helped the manager identify maintenance problems early. Yet public access remained restricted because the roof had limited space and only one suitable entrance. Some neighbours were disappointed, while others accepted that a private roof could not serve the same role as a public park. The garden provided a useful shared space for workers, although its social benefits did not reach everyone equally.",
        "After the first year, the owners compared maintenance costs and staff feedback with the goals they had set. They decided to keep the garden but did not recommend copying its design onto every building. Roof strength, access, local rainfall and the capacity to maintain plants all needed consideration. In their view, the project worked because its ambitions matched the site. Green roofs could form one part of a city's response to rainwater and limited outdoor space, alongside better drains and accessible parks. Treating them as a complete replacement for those services would misunderstand both what the Hartwell garden achieved and what it could not do.",
    ],
    [
        (
            "main_idea",
            "What is the central message of the passage?",
            5,
            [
                (
                    "Roof gardens can offer benefits when designed for a site's conditions and limits",
                    "Kết luận nêu lợi ích có điều kiện theo kết cấu, mưa, tiếp cận và bảo trì.",
                ),
                (
                    "Roof gardens should replace all public parks",
                    "Đoạn cuối bác bỏ việc xem chúng là sự thay thế hoàn toàn.",
                ),
                (
                    "Decorative plants are the only useful part of a green roof",
                    "Bài tập trung cả nước mưa, kết cấu và không gian nghỉ.",
                ),
                (
                    "Every office roof can support the same garden",
                    "Sức chịu tải và điều kiện mỗi mái phải được xem xét riêng.",
                ),
            ],
        ),
        (
            "detail",
            "Why did an engineer examine the roof before planting?",
            2,
            [
                (
                    "To check whether it could support the weight of wet growing material",
                    "Đất ướt nặng hơn nên phải kiểm tra sức chịu tải sau mưa.",
                ),
                ("To select the colours of flowers", "Màu hoa không phải mục đích kiểm tra kết cấu."),
                (
                    "To decide the price of office lunches",
                    "Không liên quan đến công việc của kỹ sư trong đoạn.",
                ),
                ("To measure the number of nearby pedestrians", "Không có khảo sát số người đi bộ ở đây."),
            ],
        ),
        (
            "vocabulary",
            "The word 'restricted' in paragraph 4 is closest in meaning to...",
            4,
            [
                ("limited", "Restricted access là việc tiếp cận bị giới hạn do không gian và lối vào."),
                ("advertised", "Đoạn không nói quảng bá quyền vào mái."),
                ("made free of charge", "Restricted không có nghĩa là miễn phí."),
                ("completely forgotten", "Giới hạn tiếp cận là quyết định có lý do, không phải bị quên."),
            ],
        ),
        (
            "reference",
            "The word 'It' in the fourth sentence of paragraph 3 refers to...",
            3,
            [
                (
                    "the delay in water reaching the drains",
                    "Câu trước nói This delay; sự chậm lại làm giảm lượng nước dồn đến cùng lúc.",
                ),
                ("a worker's lunch break", "Giờ nghỉ trưa chỉ xuất hiện ở đoạn sau."),
                ("a bare roof's dark colour", "Màu sắc mái không phải chủ thể giảm dòng nước dồn."),
                ("the latest storm's name", "Bài không đặt tên cơn bão."),
            ],
        ),
        (
            "inference",
            "What can be inferred about a garden after several rainy days?",
            3,
            [
                (
                    "It may have less capacity to take in additional rainwater",
                    "Vật liệu đã đầy nước nên khả năng hút thêm giảm.",
                ),
                (
                    "It will absorb an unlimited amount of water",
                    "Khả năng hấp thụ được mô tả là có giới hạn.",
                ),
                ("It no longer needs any drainage channels", "Kênh thoát vẫn cần để nước dư thoát an toàn."),
                ("It becomes lighter than it was in dry weather", "Đoạn 2 cho biết vật liệu ướt nặng hơn."),
            ],
        ),
        (
            "purpose",
            "Why does the author mention disappointed neighbours?",
            4,
            [
                (
                    "To show that the garden's social benefits were not equally accessible",
                    "Hàng xóm không được tiếp cận như nhân viên; lợi ích xã hội phân bố không đều.",
                ),
                (
                    "To prove that workers disliked the garden",
                    "Nhân viên thích không gian nghỉ và tham gia chăm sóc.",
                ),
                ("To explain why all plants were removed", "Chủ tòa nhà quyết định giữ lại khu vườn."),
                (
                    "To suggest that public parks should restrict entry",
                    "Bài phân biệt mái riêng với công viên công cộng, không đề xuất hạn chế công viên.",
                ),
            ],
        ),
        (
            "negative_detail",
            "Which factor is NOT listed in paragraph 5 as relevant to copying the design?",
            5,
            [
                (
                    "The nationality of office workers",
                    "Quốc tịch nhân viên không nằm trong các yếu tố được nêu.",
                ),
                ("The strength of the roof", "Sức chịu tải của mái được liệt kê."),
                ("Local rainfall", "Lượng mưa địa phương được liệt kê."),
                ("The ability to maintain the plants", "Khả năng bảo trì cây được liệt kê."),
            ],
        ),
        (
            "sentence_meaning",
            "What does 'The most important early work was therefore largely invisible once the plants had grown' mean?",
            2,
            [
                (
                    "Essential preparation remained hidden beneath the visible garden",
                    "Kết cấu, lớp bảo vệ và thoát nước rất quan trọng nhưng nằm dưới cây.",
                ),
                (
                    "The garden was impossible to see from any location",
                    "Bài không nói toàn bộ khu vườn vô hình; chỉ công tác chuẩn bị bị che.",
                ),
                (
                    "Planting had begun before safety preparations",
                    "Các bước kiểm tra và chuẩn bị diễn ra trước khi trồng.",
                ),
                (
                    "The engineer's work became unnecessary after plants grew",
                    "Bị che khuất không có nghĩa là không còn cần thiết.",
                ),
            ],
        ),
        (
            "organization",
            "How does paragraph 3 explain the garden's effect on rainwater?",
            3,
            [
                (
                    "It describes a process and then a condition that limits it",
                    "Đoạn mô tả giữ/làm chậm nước rồi giới hạn khi vật liệu đã bão hòa.",
                ),
                (
                    "It lists several unrelated building materials",
                    "Các chi tiết gắn với cùng một quá trình nước mưa.",
                ),
                ("It compares the opinions of two engineers", "Không có hai ý kiến kỹ sư được đối chiếu."),
                (
                    "It tells the history of drainage over many centuries",
                    "Đoạn chỉ giải thích cơ chế của khu vườn hiện tại.",
                ),
            ],
        ),
        (
            "tone",
            "Which best describes the author's overall attitude?",
            5,
            [
                (
                    "Supportive of the benefits while acknowledging practical limits",
                    "Bài ghi nhận lợi ích và nhấn mạnh giới hạn, điều kiện phù hợp.",
                ),
                (
                    "Uncritically enthusiastic about any green roof",
                    "Có nhiều lưu ý về tải trọng, bảo trì và tiếp cận.",
                ),
                (
                    "Opposed to every attempt to improve city roofs",
                    "Không phản đối mọi dự án; trường hợp Hartwell được đánh giá hữu ích.",
                ),
                (
                    "Indifferent to the project's environmental effects",
                    "Tác động nước mưa là nội dung chính xuyên suốt.",
                ),
            ],
        ),
    ],
)

article(
    "The Meeting That Began in Silence",
    "work",
    "B2",
    [
        "At a small design company, Monday meetings had become predictable. Two or three confident speakers usually introduced ideas, while other employees listened and contributed only when invited. The manager initially assumed that the quieter members had little to add. That assumption changed when a junior designer sent a detailed proposal after a meeting in which she had barely spoken. Several of her suggestions addressed problems the group had overlooked. The manager began to wonder whether the meeting format, rather than the quality of people's ideas, was influencing whose views received attention. Instead of asking everyone to speak more loudly, she decided to change how discussions began.",
        "For the next month, each meeting opened with eight minutes of silent reading and writing. A short document described the decision to be made, and everyone wrote down questions or possible solutions before discussion started. Employees could add their notes to a shared board without speaking immediately. The manager then invited different people to explain the notes, taking care not to let the first response determine the entire conversation. The change gave participants time to organise their thoughts. It also meant that a person entering the discussion later could refer to an idea already recorded, rather than struggling to find a gap between louder voices.",
        "The new format did not eliminate disagreement. In fact, more differences became visible because people committed their initial views to writing before hearing the opinions of senior colleagues. The team treated this as useful information rather than evidence that the experiment had failed. When several notes described the same concern in different words, participants could discuss whether they were identifying one shared problem or several separate ones. Writing made the starting points easier to compare. It did not make the final decision automatic, and the manager still had to explain why some proposals were accepted while others were set aside for another project.",
        "There were difficulties as well. Preparing a clear document took time, and some employees felt that eight minutes was too long for a simple update. The team therefore reserved the format for meetings involving a decision or a complicated problem. Routine announcements were sent as short messages instead. One employee who found writing in English difficult was allowed to contribute a diagram and a few labels. This adjustment mattered because a method intended to include more voices could otherwise have created a different barrier. The aim was to make thinking visible, not to reward the fastest writer or the person with the most polished sentences.",
        "At the end of the trial, the company asked employees whether they felt better able to contribute. Most reported an improvement, although the small group and short trial could not establish how the approach would work elsewhere. The company kept the silent opening for selected meetings and continued adapting it. Its experience offered a modest lesson: participation depends partly on the opportunities a discussion provides. A quieter employee may need a different route into the conversation rather than a stronger personality. Silence, when used deliberately and briefly, can prepare a group for a more informative exchange instead of preventing communication altogether.",
    ],
    [
        (
            "main_idea",
            "What is the passage mainly concerned with?",
            5,
            [
                (
                    "How changing a meeting format can broaden participation",
                    "Bài mô tả đổi cách mở đầu cuộc họp để nhiều người đóng góp hơn.",
                ),
                (
                    "Why every workplace should stop holding meetings",
                    "Công ty vẫn họp khi cần quyết định hay giải quyết vấn đề.",
                ),
                (
                    "How to train all employees to become faster writers",
                    "Mục tiêu không phải thưởng cho người viết nhanh nhất.",
                ),
                (
                    "Why senior employees always have the best ideas",
                    "Bài cho thấy ý tưởng từ người ít nói có thể bị bỏ qua.",
                ),
            ],
        ),
        (
            "detail",
            "What happened during the first eight minutes of the new meetings?",
            2,
            [
                (
                    "Participants read a document and wrote their own thoughts",
                    "Mọi người đọc tài liệu ngắn rồi viết câu hỏi hoặc giải pháp.",
                ),
                (
                    "The manager read all employees' notes aloud",
                    "Giải thích các ghi chú diễn ra sau giai đoạn đọc và viết yên lặng.",
                ),
                (
                    "Senior colleagues gave instructions without interruption",
                    "Mọi người chuẩn bị ý riêng trước khi nghe ý kiến cấp cao.",
                ),
                (
                    "Employees voted on a finished decision",
                    "Quyết định cuối không tự động được đưa ra trong tám phút này.",
                ),
            ],
        ),
        (
            "vocabulary",
            "The word 'barrier' in paragraph 4 is closest in meaning to...",
            4,
            [
                (
                    "an obstacle to participation",
                    "Yêu cầu viết tiếng Anh có thể trở thành trở ngại tham gia cho một số người.",
                ),
                ("a reward for good performance", "Barrier là cản trở, không phải phần thưởng."),
                ("a record of previous decisions", "Bài không dùng từ này để chỉ biên bản."),
                ("an agreement between managers", "Không chỉ thỏa thuận giữa những người quản lý."),
            ],
        ),
        (
            "reference",
            "The word 'they' in paragraph 3 refers to...",
            3,
            [
                (
                    "the participants",
                    "Người tham gia đang thảo luận xem các ghi chú chỉ một hay nhiều vấn đề.",
                ),
                ("the senior colleagues' opinions", "Ý kiến không thể tự nhận diện và thảo luận vấn đề."),
                ("the final decisions", "Quyết định cuối chưa được đưa ra tại thời điểm này."),
                (
                    "the different words",
                    "Những từ ngữ không phải chủ thể của identifying trong cấu trúc này.",
                ),
            ],
        ),
        (
            "inference",
            "What does the junior designer's proposal suggest?",
            1,
            [
                (
                    "Speaking little in a meeting does not necessarily mean having few ideas",
                    "Nhà thiết kế ít nói vẫn gửi đề xuất chi tiết giải quyết vấn đề bị bỏ sót.",
                ),
                (
                    "Ideas sent after meetings are always better",
                    "Một trường hợp không chứng minh mọi ý tưởng gửi sau đều tốt hơn.",
                ),
                (
                    "The designer did not understand the company's problems",
                    "Đề xuất của cô xử lý những vấn đề nhóm đã bỏ qua.",
                ),
                (
                    "The manager had already considered every suggestion",
                    "Bài nói một số vấn đề trước đó bị bỏ sót.",
                ),
            ],
        ),
        (
            "purpose",
            "Why is the employee who used a diagram mentioned?",
            4,
            [
                (
                    "To illustrate an adaptation that kept the format inclusive",
                    "Cho dùng sơ đồ giúp người khó viết tiếng Anh vẫn trình bày suy nghĩ.",
                ),
                (
                    "To show that written notes were banned",
                    "Ghi chú không bị cấm; sơ đồ là lựa chọn bổ sung.",
                ),
                (
                    "To argue that language ability is the only valuable skill",
                    "Mục tiêu là thể hiện suy nghĩ chứ không phải câu văn trau chuốt.",
                ),
                ("To prove that all meetings must use drawings", "Bài chỉ nói một điều chỉnh cho một người."),
            ],
        ),
        (
            "negative_detail",
            "Which change is NOT described in paragraph 4?",
            4,
            [
                (
                    "Removing the manager from all decisions",
                    "Đoạn không nói loại người quản lý khỏi quyết định.",
                ),
                (
                    "Using the format mainly for decisions and complicated problems",
                    "Việc giới hạn vào loại cuộc họp này được nêu rõ.",
                ),
                ("Sending routine announcements as messages", "Thông báo thường lệ được gửi bằng tin nhắn."),
                (
                    "Allowing a diagram instead of extensive writing",
                    "Ví dụ nhân viên dùng sơ đồ và vài nhãn được nêu rõ.",
                ),
            ],
        ),
        (
            "sentence_meaning",
            "Which best restates 'Writing made the starting points easier to compare'?",
            3,
            [
                (
                    "Written notes helped the group compare initial perspectives",
                    "Ghi lại ý ban đầu giúp nhóm nhìn ra điểm chung và khác biệt.",
                ),
                (
                    "Writing removed the need to discuss different proposals",
                    "Nhóm vẫn cần thảo luận và quyết định.",
                ),
                (
                    "The first person to write decided the final answer",
                    "Bài tránh để phản hồi đầu tiên chi phối cả cuộc trao đổi.",
                ),
                (
                    "Every employee began with exactly the same opinion",
                    "Nhiều khác biệt trở nên rõ hơn, không phải mọi người cùng quan điểm.",
                ),
            ],
        ),
        (
            "organization",
            "How does the passage develop its argument?",
            1,
            [
                (
                    "It presents a participation problem, an intervention, and its benefits and limits",
                    "Bố cục đi từ vấn đề người ít nói đến thử nghiệm, tác dụng và giới hạn.",
                ),
                (
                    "It ranks several companies by financial success",
                    "Không có bảng xếp hạng doanh nghiệp hay lợi nhuận.",
                ),
                (
                    "It gives only a list of meeting rules without context",
                    "Bài có bối cảnh, ví dụ và kết luận từ thử nghiệm.",
                ),
                (
                    "It describes an unrelated event in each paragraph",
                    "Mọi đoạn đều phát triển cùng thử nghiệm họp.",
                ),
            ],
        ),
        (
            "tone",
            "Which best describes the author's conclusion?",
            5,
            [
                (
                    "Measured support for a potentially useful approach",
                    "Kết luận tích cực nhưng gọi bài học là modest và thừa nhận giới hạn mẫu nhỏ.",
                ),
                (
                    "Absolute certainty that the approach works everywhere",
                    "Bài nói chưa thể xác định hiệu quả ở nơi khác.",
                ),
                (
                    "Disapproval of any silence during communication",
                    "Sự yên lặng ngắn có chủ đích được xem là hữu ích.",
                ),
                (
                    "Blame directed at employees with quiet personalities",
                    "Bài nhấn mạnh cơ hội tham gia thay vì đổ lỗi tính cách.",
                ),
            ],
        ),
    ],
)

article(
    "Whose Words Are Beside the Object?",
    "culture",
    "B2",
    [
        "In the Northbridge town museum, a wooden fishing boat had stood behind a rope for many years. Its label gave the date it was built, the type of wood used and the name of its maker. Although these facts were accurate, visitors often passed it without stopping. When the museum prepared a new exhibition about working life, a curator asked former fishers what they remembered about boats like this one. Their answers included difficult journeys, repairs made in bad weather and jokes shared while waiting for the tide. The curator realised that the existing label described the object but said little about the people who had used it.",
        "The museum invited several residents to help write new labels for selected objects. A historian checked dates and names, while participants discussed memories and chose which details might interest visitors. The task was not simply to replace professional knowledge with personal stories. Memories could be incomplete, and two people sometimes described the same event differently. When an exact detail could not be confirmed, the label made that uncertainty clear. For example, one account of a journey was introduced as a fisher's recollection rather than as an established fact. This distinction allowed the museum to include a personal voice without presenting every remembered detail as certain.",
        "The labels also had to be short enough to read while standing in a busy gallery. Participants initially wanted to include every story, but long drafts were difficult to follow. The editor encouraged them to choose one main point for each object and move additional material into recorded interviews. Visitors could listen to those recordings if they wanted greater detail. A short label beside a repaired net, for instance, explained how families shared the work of maintaining equipment. The associated interview described the process at length. The two formats served different needs instead of competing to contain exactly the same information.",
        "After the exhibition opened, staff observed how visitors used the gallery. More people stopped near the boat, and several discussed similar experiences from their own families. These observations were encouraging, but they did not reveal whether every visitor preferred the new labels. People who hurried through the room were less likely to leave comments. The museum therefore combined informal conversations with a short questionnaire available at the exit. Staff also asked whether the language was clear to visitors unfamiliar with fishing. Community involvement would have limited value if the resulting labels could be understood only by those who already knew the local stories.",
        "The project changed the curator's view of expertise. Historians remained responsible for checking evidence, and editors still shaped the writing. Residents contributed knowledge that was difficult to find in official records, including the ordinary routines surrounding work. None of these contributions was sufficient on its own. Together, they produced an exhibition that offered both reliable information and a stronger sense of human experience. The museum did not conclude that every label needed a personal memory. Instead, it learned to ask whose perspective was missing, what that perspective could add, and how to present it honestly within the space available.",
    ],
    [
        (
            "main_idea",
            "What is the main idea of the passage?",
            5,
            [
                (
                    "Museum labels can benefit from combining professional knowledge with community perspectives",
                    "Bài nhấn mạnh sự bổ sung giữa kiểm chứng chuyên môn và trải nghiệm cư dân.",
                ),
                (
                    "Personal memories should replace all historical evidence",
                    "Đoạn 2 và 5 đều duy trì trách nhiệm kiểm chứng sử liệu.",
                ),
                (
                    "Museums should display only objects still used today",
                    "Không có yêu cầu loại bỏ đồ vật xưa.",
                ),
                (
                    "Long labels are always better than short labels",
                    "Đoạn 3 giải thích hạn chế của nhãn quá dài.",
                ),
            ],
        ),
        (
            "detail",
            "How did the museum handle an unconfirmed detail in a fisher's story?",
            2,
            [
                (
                    "It identified the account as a recollection rather than a confirmed fact",
                    "Nhãn phân biệt ký ức cá nhân với sự kiện đã xác lập.",
                ),
                (
                    "It presented the detail as completely certain",
                    "Cách này trái với yêu cầu thể hiện sự không chắc chắn.",
                ),
                (
                    "It removed every personal voice from the exhibition",
                    "Bảo tàng vẫn dùng ký ức nhưng chú thích đúng bản chất.",
                ),
                (
                    "It asked visitors to decide the boat's construction date",
                    "Ngày tháng do nhà sử học kiểm tra, không giao khách quyết định.",
                ),
            ],
        ),
        (
            "vocabulary",
            "The word 'recollection' in paragraph 2 is closest in meaning to...",
            2,
            [
                ("a remembered account", "Recollection ở đây là lời kể từ trí nhớ cá nhân."),
                ("a financial calculation", "Không liên quan tính toán tài chính."),
                ("an official instruction", "Ký ức cá nhân khác với chỉ thị chính thức."),
                ("a newly built object", "Từ này chỉ nội dung nhớ lại, không phải hiện vật mới."),
            ],
        ),
        (
            "reference",
            "The word 'them' in the third sentence of paragraph 3 refers to...",
            3,
            [
                ("the participants", "Biên tập viên khuyến khích những người tham gia chọn một ý chính."),
                ("the recorded interviews", "Phỏng vấn không phải người có thể chọn ý theo khuyến khích."),
                ("the museum objects", "Hiện vật không phải chủ thể đưa ra lựa chọn nội dung."),
                ("the additional stories", "Các câu chuyện không phải người được khuyến khích biên tập."),
            ],
        ),
        (
            "inference",
            "Why might visitor comments alone give an incomplete picture?",
            4,
            [
                (
                    "People who did not stop were less likely to provide comments",
                    "Người đi nhanh ít để lại phản hồi nên ý kiến thu được có thể thiên lệch.",
                ),
                (
                    "All visitors were required to praise the exhibition",
                    "Không nêu yêu cầu khen ngợi bắt buộc.",
                ),
                (
                    "Visitors were not allowed to discuss their own experiences",
                    "Nhiều người đã trò chuyện về trải nghiệm gia đình.",
                ),
                ("The staff refused to use questionnaires", "Bảo tàng kết hợp thêm bảng hỏi ở lối ra."),
            ],
        ),
        (
            "purpose",
            "Why does the author describe the label and interview about the repaired net?",
            3,
            [
                (
                    "To illustrate how different formats can provide different levels of detail",
                    "Nhãn ngắn nêu ý chính, phỏng vấn mở rộng quy trình nên hai hình thức bổ sung nhau.",
                ),
                ("To demonstrate that all labels should be removed", "Bài vẫn giữ nhãn ngắn cạnh hiện vật."),
                (
                    "To explain how to repair a fishing net step by step",
                    "Ví dụ nói về cách trình bày thông tin, không dạy kỹ thuật vá lưới.",
                ),
                (
                    "To show that recordings contain less information than labels",
                    "Phỏng vấn mô tả quy trình dài hơn nhãn.",
                ),
            ],
        ),
        (
            "negative_detail",
            "Which task is NOT mentioned as part of creating the new labels?",
            2,
            [
                ("Selling the objects to former fishers", "Bài không nói bán hiện vật cho cư dân."),
                ("Checking dates and names", "Nhà sử học kiểm tra ngày tháng và tên."),
                ("Discussing residents' memories", "Người tham gia thảo luận các ký ức."),
                (
                    "Making uncertainty clear when necessary",
                    "Nhãn thể hiện rõ khi chi tiết chưa được xác nhận.",
                ),
            ],
        ),
        (
            "sentence_meaning",
            "Which best expresses 'None of these contributions was sufficient on its own'?",
            5,
            [
                (
                    "Each kind of contribution needed support from the others",
                    "Kiểm chứng, biên tập và ký ức cộng đồng đều có ích nhưng cần kết hợp.",
                ),
                (
                    "Every contribution was completely useless",
                    "Không đủ riêng lẻ không có nghĩa là hoàn toàn vô dụng.",
                ),
                (
                    "The historian could create the exhibition without anyone else",
                    "Điều này phủ nhận vai trò bổ sung được nhấn mạnh.",
                ),
                (
                    "Residents were asked to stop contributing",
                    "Cư dân tiếp tục được ghi nhận về kiến thức trải nghiệm.",
                ),
            ],
        ),
        (
            "organization",
            "What is the function of paragraph 4 in the passage?",
            4,
            [
                (
                    "It discusses how the museum assessed the exhibition and limitations of the feedback",
                    "Đoạn nêu quan sát tích cực, thiên lệch phản hồi và thêm bảng hỏi.",
                ),
                ("It introduces a completely different museum project", "Vẫn là triển lãm vừa mô tả."),
                (
                    "It lists the technical materials used to build the boat",
                    "Thông tin vật liệu nằm ở nhãn cũ, không phải nội dung đoạn 4.",
                ),
                (
                    "It presents a fictional visitor's diary without analysis",
                    "Đây là đánh giá cách thu phản hồi, không phải nhật ký.",
                ),
            ],
        ),
        (
            "tone",
            "Which best describes the author's attitude to community participation?",
            5,
            [
                (
                    "Positive, provided that evidence and presentation are handled carefully",
                    "Bài ủng hộ đóng góp cộng đồng cùng yêu cầu kiểm chứng và trình bày trung thực.",
                ),
                (
                    "Certain that local memories are always accurate",
                    "Đoạn 2 cho biết ký ức có thể thiếu và khác nhau.",
                ),
                (
                    "Dismissive because only professionals have useful knowledge",
                    "Bài ghi nhận kiến thức cư dân khó tìm trong hồ sơ chính thức.",
                ),
                ("Concerned only with increasing ticket prices", "Không bàn việc tăng giá vé."),
            ],
        ),
    ],
)

article(
    "The Value of a Qualified Answer",
    "psychology",
    "C1",
    [
        "When an expert answers a public question with 'it depends', the response can sound evasive. Audiences accustomed to brief interviews may interpret qualification as a lack of knowledge, especially when another speaker offers a confident prediction. Yet certainty and expertise are not interchangeable. A specialist may recognise conditions that a less experienced observer overlooks, and those conditions can materially alter an outcome. The difficulty is not merely that experts know more facts. They may also have a more developed understanding of where available evidence stops. Communicating that boundary requires more effort than delivering a simple conclusion, but it can be central to giving useful advice.",
        "Consider a fictional advisory panel asked whether a town should introduce a new bus route. One consultant promises that the route will immediately reduce traffic. Another explains that its effect will depend on frequency, ticket prices and whether passengers can reach the stops safely. The second answer is harder to turn into a headline, but it identifies decisions the town can actually influence. Rather than withholding a recommendation, the consultant is describing the circumstances under which it might succeed. The distinction matters because an apparently decisive answer can conceal assumptions, leaving decision-makers unaware that they are committing themselves to conditions that have never been examined.",
        "Qualification can nevertheless become unhelpful when it is used without structure. A list of every imaginable complication may overwhelm listeners without improving their judgement. Useful uncertainty is selective: it distinguishes the factors likely to change a decision from those that are merely possible. An adviser might therefore give a provisional recommendation, identify the two conditions that matter most, and explain what additional information would lead to a revision. This approach does not remove uncertainty. It makes uncertainty actionable. Listeners can assess the recommendation against explicit assumptions instead of treating either complete confidence or total indecision as the only available positions.",
        "Trust also depends on what happens after an initial recommendation. If new evidence contradicts an earlier forecast, an expert may feel pressure to defend the original claim in order to appear consistent. However, consistency of method is different from consistency of conclusion. Revising a judgement in response to relevant evidence can demonstrate that the same standards are being applied over time. The problem arises when changes are unexplained or when inconvenient evidence is dismissed while favourable evidence is accepted without scrutiny. In those cases, the audience has little basis for distinguishing a reasoned update from an attempt to protect the speaker's reputation.",
        "None of this implies that every hesitant statement deserves trust or that confident conclusions are necessarily mistaken. Some questions are supported by strong, converging evidence, while others remain genuinely open. The task for the audience is to examine how a claim is connected to its evidence and how clearly its limitations are expressed. Institutions can help by giving advisers enough time to explain assumptions rather than rewarding the shortest possible answer. A qualified response is valuable when it clarifies what is known, what could change, and what can reasonably be done now. Its value lies in the quality of those distinctions, not in hesitation itself.",
    ],
    [
        (
            "main_idea",
            "Which statement best captures the author's central argument?",
            5,
            [
                (
                    "Well-structured qualifications can make expert advice more useful and accountable",
                    "Bài bảo vệ sự dè dặt có cấu trúc: làm rõ bằng chứng, điều kiện và khả năng cập nhật.",
                ),
                (
                    "Experts should always avoid making recommendations",
                    "Đoạn 3 vẫn khuyến khích khuyến nghị tạm thời có điều kiện.",
                ),
                (
                    "Public confidence is the most reliable measure of expertise",
                    "Đoạn 1 phân biệt sự chắc chắn với chuyên môn.",
                ),
                (
                    "Hesitation alone proves that a speaker is trustworthy",
                    "Đoạn cuối trực tiếp bác bỏ việc tin chỉ vì người nói do dự.",
                ),
            ],
        ),
        (
            "detail",
            "Which factor does the second consultant identify in the bus-route example?",
            2,
            [
                (
                    "Whether people can safely reach the stops",
                    "Khả năng tiếp cận điểm dừng an toàn được nêu là điều kiện ảnh hưởng hiệu quả.",
                ),
                (
                    "Whether the route can avoid all existing roads",
                    "Không có điều kiện tránh tất cả đường hiện hữu.",
                ),
                (
                    "Whether the town can stop publishing headlines",
                    "Khó viết tiêu đề chỉ là đối chiếu cách truyền thông, không phải điều kiện vận hành.",
                ),
                ("Whether every resident already owns a car", "Không nêu yêu cầu mọi cư dân sở hữu xe."),
            ],
        ),
        (
            "vocabulary",
            "In paragraph 3, 'actionable' most nearly means...",
            3,
            [
                (
                    "usable as a basis for practical decisions",
                    "Sự không chắc chắn được tổ chức để người nghe có thể hành động và đánh giá quyết định.",
                ),
                (
                    "guaranteed to produce the desired result",
                    "Có thể dùng để quyết định không có nghĩa là bảo đảm kết quả.",
                ),
                (
                    "too complex to communicate publicly",
                    "Đoạn nhấn mạnh cách làm rõ, không phải không thể truyền đạt.",
                ),
                (
                    "requiring the removal of every possible risk",
                    "Tác giả nói cách này không loại bỏ sự không chắc chắn.",
                ),
            ],
        ),
        (
            "reference",
            "The word 'those' in 'those that are merely possible' in paragraph 3 refers to...",
            3,
            [
                (
                    "factors",
                    "Cấu trúc đối chiếu các yếu tố có thể thay đổi quyết định với yếu tố chỉ có khả năng xảy ra.",
                ),
                ("listeners", "Đoạn không phân loại người nghe thành merely possible."),
                ("recommendations", "Danh từ được so sánh trực tiếp là factors."),
                ("headlines", "Tiêu đề thuộc ví dụ trước, không phải đối tượng của đối chiếu này."),
            ],
        ),
        (
            "inference",
            "What does the passage imply about changing an expert conclusion?",
            4,
            [
                (
                    "It can be compatible with a stable method when the evidence changes",
                    "Phương pháp nhất quán có thể dẫn đến kết luận mới khi có bằng chứng liên quan mới.",
                ),
                (
                    "It necessarily indicates that the expert was dishonest",
                    "Tác giả phân biệt cập nhật có lý do với bảo vệ danh tiếng.",
                ),
                (
                    "It should occur whenever the public dislikes a forecast",
                    "Cơ sở cập nhật là bằng chứng, không đơn thuần phản ứng công chúng.",
                ),
                (
                    "It is more trustworthy when no explanation is provided",
                    "Thay đổi không giải thích khiến khán giả khó đánh giá.",
                ),
            ],
        ),
        (
            "purpose",
            "Why does the author use the fictional bus-route example?",
            2,
            [
                (
                    "To contrast apparent decisiveness with advice that exposes relevant conditions",
                    "Hai chuyên gia minh họa lời chắc chắn che giả định và lời có điều kiện giúp ra quyết định.",
                ),
                (
                    "To establish that buses never reduce traffic",
                    "Ví dụ không kết luận hiệu quả xe buýt luôn bằng không.",
                ),
                (
                    "To give a detailed technical design for a transport system",
                    "Không có thiết kế kỹ thuật tuyến xe; trọng tâm là cách tư vấn.",
                ),
                (
                    "To show that all consultants deliberately mislead towns",
                    "Không quy mọi tư vấn viên cố tình đánh lừa.",
                ),
            ],
        ),
        (
            "negative_detail",
            "Which is NOT part of the structured advice proposed in paragraph 3?",
            3,
            [
                (
                    "Listing every conceivable complication with equal emphasis",
                    "Đoạn cảnh báo liệt kê mọi biến chứng tưởng tượng có thể làm người nghe quá tải.",
                ),
                ("Offering a provisional recommendation", "Khuyến nghị tạm thời được đề xuất rõ."),
                (
                    "Identifying the conditions that matter most",
                    "Hai điều kiện quan trọng nhất là một phần cách tiếp cận.",
                ),
                (
                    "Explaining what information could justify revision",
                    "Giải thích thông tin nào dẫn đến sửa khuyến nghị được nêu rõ.",
                ),
            ],
        ),
        (
            "sentence_meaning",
            "Which best restates 'certainty and expertise are not interchangeable'?",
            1,
            [
                (
                    "Being certain does not by itself establish that someone has expertise",
                    "Tự tin và năng lực chuyên môn không thể được xem là cùng một thứ.",
                ),
                (
                    "Experts are never able to reach clear conclusions",
                    "Đoạn cuối thừa nhận có câu hỏi được bằng chứng mạnh hỗ trợ.",
                ),
                (
                    "Only people without specialist knowledge can be confident",
                    "Bài không cấm chuyên gia có kết luận tự tin khi đủ bằng chứng.",
                ),
                (
                    "Expertise is irrelevant to the quality of an answer",
                    "Bài giải thích chuyên môn giúp hiểu điều kiện và giới hạn bằng chứng.",
                ),
            ],
        ),
        (
            "organization",
            "How does paragraph 5 relate to the preceding argument?",
            5,
            [
                (
                    "It limits possible overinterpretations and states criteria for evaluating advice",
                    "Đoạn cuối tránh cực đoan tin mọi do dự, rồi đưa tiêu chí gắn khẳng định với bằng chứng.",
                ),
                (
                    "It rejects every point made in the earlier paragraphs",
                    "Đoạn làm rõ điều kiện áp dụng chứ không phủ nhận toàn bộ lập luận.",
                ),
                (
                    "It introduces transport policy as the passage's main subject",
                    "Chính sách xe buýt chỉ là ví dụ ở đoạn 2.",
                ),
                (
                    "It replaces the argument with an unrelated personal story",
                    "Vẫn tiếp tục bàn cách đánh giá lời khuyên chuyên gia.",
                ),
            ],
        ),
        (
            "tone",
            "Which best describes the tone of the passage?",
            5,
            [
                (
                    "Analytical and carefully qualified",
                    "Tác giả phân biệt khái niệm, đưa điều kiện và tránh kết luận tuyệt đối.",
                ),
                (
                    "Mocking towards anyone who seeks expert advice",
                    "Không chế giễu người tìm lời khuyên; bài giúp họ đánh giá tốt hơn.",
                ),
                (
                    "Unreservedly approving of all uncertain statements",
                    "Đoạn cuối nói không phải mọi lời do dự đều đáng tin.",
                ),
                (
                    "Fatalistic about the possibility of making decisions",
                    "Đoạn 3 cho thấy vẫn có thể ra quyết định trong điều kiện không chắc chắn.",
                ),
            ],
        ),
    ],
)

article(
    "Many Observers, Uneven Evidence",
    "science",
    "C1",
    [
        "A photograph of a bird beside a footpath may seem like a minor contribution to scientific knowledge. When thousands of observations are collected, however, they can reveal patterns that a small research team could not document alone. In citizen-science projects, members of the public record what they see and submit the information to a shared database. The resulting reach is attractive, but the size of a collection should not be confused with the strength of every conclusion drawn from it. Observations accumulate through human choices about where to go, what to notice and whether an encounter seems interesting enough to report. Those choices leave a trace in the data.",
        "A fictional project in the Alder district illustrates the issue. Volunteers recorded birds using an application that automatically attached a location and time to each photograph. Reports clustered around popular walking routes and the homes of enthusiastic participants. Remote farmland received relatively little attention, even though it occupied a large part of the district. A map of submissions therefore showed both where birds had been observed and where people had looked for them. Without separating these influences, a researcher might interpret an empty area on the map as evidence that birds were absent, when it could simply indicate that few observers had visited.",
        "The organisers responded by asking volunteers to record complete observation sessions, including occasions when they saw none of the species being studied. Participants noted how long they watched and which route they followed. These details provided a rough measure of effort, making some comparisons more defensible. A researcher could distinguish two reports produced by a brief visit from two reports collected during many hours of searching. The additional information did not make volunteers identical to trained surveyors, nor did it remove every source of bias. It did, however, reveal something about the process that generated the observations rather than treating each submission as an isolated fact.",
        "Improving consistency also required attention to participation. A complicated reporting form might produce richer data from each completed entry while discouraging less experienced volunteers from submitting anything at all. The organisers therefore separated essential fields from optional details and offered examples of useful photographs. They also explained why reports of unsuccessful searches mattered. When participants understood the purpose of an apparently uninteresting record, they were more willing to provide it. Data quality depended partly on this relationship between researchers and volunteers, not merely on technical checks applied after information arrived. A perfectly designed database would be of limited value if few people felt able to contribute to it.",
        "For the final analysis, the team described gaps in coverage and avoided making claims about locations with very little observation. It compared the volunteer records with a smaller set of planned surveys rather than assuming one source could replace the other. The two approaches supplied different strengths: public participation offered breadth, while systematic visits provided a more controlled basis for comparison. Citizen science was valuable precisely when these differences were recognised. More observations expanded what researchers could investigate, but only a careful account of how those observations were produced could justify conclusions about the wider district. Scale created an opportunity; it did not eliminate the need for judgement.",
    ],
    [
        (
            "main_idea",
            "What is the main argument of the passage?",
            5,
            [
                (
                    "Citizen-science data are useful when the process and limits of collection inform analysis",
                    "Tác giả khẳng định giá trị dữ liệu lớn phụ thuộc hiểu cách thu thập và giới hạn bao phủ.",
                ),
                (
                    "A large number of reports automatically guarantees valid conclusions",
                    "Bài phân biệt quy mô với sức mạnh kết luận ngay từ đầu.",
                ),
                (
                    "Volunteers should never take part in scientific projects",
                    "Bài ghi nhận phạm vi quan sát rộng do cộng đồng mang lại.",
                ),
                (
                    "Planned surveys should be completely replaced by photographs",
                    "Đoạn cuối phối hợp hai nguồn thay vì thay thế.",
                ),
            ],
        ),
        (
            "detail",
            "Where did reports in the Alder project tend to concentrate?",
            2,
            [
                (
                    "Near popular walking routes and keen participants' homes",
                    "Đoạn 2 nêu hai nơi này là vùng tập trung báo cáo.",
                ),
                ("Only in remote farmland", "Đất nông nghiệp xa nhận ít sự chú ý."),
                (
                    "At evenly spaced points throughout the district",
                    "Báo cáo phân bố không đều, không theo lưới đồng nhất.",
                ),
                ("Inside the researchers' offices", "Không nêu quan sát trong văn phòng nghiên cứu."),
            ],
        ),
        (
            "vocabulary",
            "The word 'defensible' in paragraph 3 is closest in meaning to...",
            3,
            [
                (
                    "capable of being reasonably justified",
                    "Thông tin về công sức quan sát giúp việc so sánh có cơ sở bảo vệ hơn.",
                ),
                (
                    "protected from physical damage",
                    "Đây là sự vững vàng của suy luận, không phải bảo vệ vật lý.",
                ),
                ("certain to be popular with everyone", "Có cơ sở không đồng nghĩa được mọi người ưa thích."),
                ("impossible to question", "Tác giả vẫn thừa nhận chưa loại bỏ mọi thiên lệch."),
            ],
        ),
        (
            "reference",
            "The phrase 'these influences' in paragraph 2 refers to...",
            2,
            [
                (
                    "Where birds occurred and where people chose to observe",
                    "Câu trước nói bản đồ phản ánh cả nơi có chim được thấy và nơi con người tìm chúng.",
                ),
                (
                    "The price and battery life of the application",
                    "Hai đặc tính này không được bàn trong đoạn.",
                ),
                ("Two different types of farmland", "Không có hai loại đất được đối chiếu theo cách này."),
                (
                    "The age and profession of the research team",
                    "Không có thông tin tuổi hay nghề của thành viên nhóm.",
                ),
            ],
        ),
        (
            "inference",
            "Why might an area with no submissions still contain birds?",
            2,
            [
                (
                    "The absence of submissions may reflect insufficient observation",
                    "Bản đồ trống có thể chỉ vì ít người từng đến quan sát.",
                ),
                (
                    "The application intentionally deletes all rural photographs",
                    "Không có thông tin xóa ảnh vùng nông thôn.",
                ),
                (
                    "Birds can be recorded only during planned surveys",
                    "Tình nguyện viên cũng ghi lại chim qua ứng dụng.",
                ),
                (
                    "Every volunteer was forbidden to enter farmland",
                    "Bài chỉ nói vùng xa ít được chú ý, không nêu lệnh cấm.",
                ),
            ],
        ),
        (
            "purpose",
            "Why does paragraph 4 discuss a complicated reporting form?",
            4,
            [
                (
                    "To illustrate a trade-off between richer individual records and wider participation",
                    "Biểu mẫu chi tiết có thể tăng thông tin mỗi báo cáo nhưng làm người ít kinh nghiệm ngại tham gia.",
                ),
                (
                    "To argue that no details should ever be requested",
                    "Nhóm vẫn giữ trường bắt buộc và thêm phần tùy chọn.",
                ),
                ("To explain the software code used for the database", "Không trình bày mã phần mềm."),
                (
                    "To show that experienced volunteers always refuse to report",
                    "Ví dụ nhấn mạnh người ít kinh nghiệm, không quy mọi người có kinh nghiệm từ chối.",
                ),
            ],
        ),
        (
            "negative_detail",
            "Which information was NOT requested as part of the complete sessions in paragraph 3?",
            3,
            [
                ("The volunteer's annual income", "Thu nhập cá nhân không được yêu cầu trong đoạn."),
                ("How long the volunteer watched", "Thời lượng quan sát được nêu rõ."),
                ("Which route the volunteer followed", "Tuyến đi được ghi lại."),
                (
                    "Whether the studied species were not seen",
                    "Lần không thấy loài nghiên cứu cũng cần báo cáo.",
                ),
            ],
        ),
        (
            "sentence_meaning",
            "Which best restates 'Scale created an opportunity; it did not eliminate the need for judgement'?",
            5,
            [
                (
                    "Large collections enabled more research but still required careful interpretation",
                    "Quy mô mở rộng khả năng nghiên cứu nhưng không thay thế phán đoán về dữ liệu.",
                ),
                (
                    "Increasing the number of records made interpretation unnecessary",
                    "Điều này trái trực tiếp với vế thứ hai.",
                ),
                (
                    "Judgement became possible only after volunteers stopped reporting",
                    "Không có yêu cầu ngừng thu thập để đánh giá.",
                ),
                (
                    "Large collections prevented researchers from asking useful questions",
                    "Bài nói dữ liệu nhiều mở rộng điều có thể nghiên cứu.",
                ),
            ],
        ),
        (
            "organization",
            "How is paragraph 3 structured?",
            3,
            [
                (
                    "A response to a data problem is explained, then its benefits and remaining limits are assessed",
                    "Đoạn mô tả ghi phiên quan sát đầy đủ, lý do hữu ích và thiên lệch còn lại.",
                ),
                ("A chronology of bird evolution is presented", "Không bàn quá trình tiến hóa loài chim."),
                (
                    "Several unrelated volunteer biographies are compared",
                    "Không có tiểu sử tình nguyện viên.",
                ),
                (
                    "A conclusion is repeated without explanation",
                    "Có ví dụ hai báo cáo từ thời gian tìm kiếm khác nhau để giải thích.",
                ),
            ],
        ),
        (
            "tone",
            "What is the author's attitude towards citizen science?",
            5,
            [
                (
                    "Constructively critical, recognising both its reach and methodological limitations",
                    "Tác giả coi trọng phạm vi rộng đồng thời yêu cầu thận trọng về phương pháp.",
                ),
                (
                    "Dismissive of all information collected by the public",
                    "Đoạn cuối khẳng định dữ liệu cộng đồng có giá trị khi hiểu đúng.",
                ),
                (
                    "Certain that technical checks alone solve every problem",
                    "Đoạn 4 nhấn mạnh quan hệ và sự tham gia, không chỉ kiểm tra kỹ thuật.",
                ),
                (
                    "Interested primarily in promoting one commercial application",
                    "Ứng dụng chỉ là công cụ trong ví dụ giả định; không quảng bá sản phẩm.",
                ),
            ],
        ),
    ],
)


async def seed():
    async with SessionLocal() as db:
        for raw in ARTICLES:
            generated = GeneratedReadingPassage.model_validate(raw)
            passage = passage_from_generated(generated, source="SEED")
            if not await db.scalar(
                select(ReadingPassage.id).where(ReadingPassage.fingerprint == passage.fingerprint)
            ):
                db.add(passage)
        await db.commit()
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed())
