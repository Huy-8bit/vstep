# Writing — Manual Prompts

Đồng bộ 2026-09-19 · manual kit 1.0.0 · code commit `658986a`.

## Purpose

Bộ prompt dự phòng/thủ công cho chức năng AI của nền tảng VSTEP hiện có: dùng khi API/quota không sẵn sàng, muốn kiểm tra điểm hoặc so sánh các chatbot. Không cần API key để đọc/sao chép bộ này.

## When to use

Chọn đúng kỹ năng và loại đầu vào. ChatGPT/Claude/Gemini hoặc chatbot khác đều có thể dùng bản text; chức năng audio/ảnh chỉ dùng khi chatbot thực sự truy cập được tệp.

## Required input

- Mục tiêu đang học và các ô dữ liệu bắt buộc trong prompt đã chọn.

## Optional input

- Lịch sử đã tóm tắt, bài chấm trước, chủ đề và từ đã học khi prompt cho phép.

## Navigation

| Function | File | Required input | Expected output | Text chatbot? | Audio? | Image/PDF? |
| --- | --- | --- | --- | --- | --- | --- |
| Chấm Writing Task 1 | [writing/task1-grading.md](task1-grading.md) | QUESTION, STUDENT_ANSWER | WritingCoreOutput | Có | Không | Không |
| Chấm Writing Task 2 | [writing/task2-grading.md](task2-grading.md) | QUESTION, STUDENT_ANSWER | WritingCoreOutput | Có | Không | Không |
| Writing một bài: chấm và học trong một lượt | [writing/all-in-one-writing.md](all-in-one-writing.md) | QUESTION, STUDENT_ANSWER | ManualWritingBundle | Có | Không | Không |
| Chấm Full Writing: Task 1 + Task 2 | [writing/full-writing-grading.md](full-writing-grading.md) | TASK1_QUESTION, TASK1_ANSWER, TASK2_QUESTION, TASK2_ANSWER | ManualFullWriting | Có | Không | Không |
| Chữa từng câu Writing | [writing/sentence-correction.md](sentence-correction.md) | QUESTION, STUDENT_ANSWER | SentenceCorrections | Có | Không | Không |
| Bài Writing đã sửa | [writing/corrected-version.md](corrected-version.md) | QUESTION, STUDENT_ANSWER | CorrectedAnswer | Có | Không | Không |
| Bài tham khảo B2/B2+ | [writing/improved-answer.md](improved-answer.md) | QUESTION, STUDENT_ANSWER | ImprovedAnswer | Có | Không | Không |
| Giải thích Writing chi tiết | [writing/detailed-feedback.md](detailed-feedback.md) | QUESTION, STUDENT_ANSWER | WritingFeedback | Có | Không | Không |
| Writing: đánh giá lại độc lập | [writing/second-opinion.md](second-opinion.md) | QUESTION, STUDENT_ANSWER, REVIEW_CONCERNS | WritingCoreOutput | Có | Không | Không |
| Vocabulary Coach từ Writing | [writing/writing-vocabulary-coach.md](writing-vocabulary-coach.md) | QUESTION, STUDENT_ANSWER | VocabularyCoachOutput | Có | Không | Không |
| Sinh đề Writing VSTEP.3–5 | [writing/writing-question-generation.md](writing-question-generation.md) | TASK | GeneratedQuestion | Có | Không | Không |

## Copy-Paste Prompt

```text
Bạn giúp tôi chọn quy trình luyện VSTEP.3–5 thủ công từ đầu vào sau:
================ GOAL_AND_INPUT ================
{{GOAL_AND_INPUT}}
================================================
Nếu Writing có đề+bài gốc: chấm bốn tiêu chí trước khi sửa; riêng một task không có bậc Writing đầy đủ. Speaking có transcript: chỉ grammar/vocabulary/structures và content feedback, không pronunciation/fluency; muốn acoustic phải có audio thực nghe được. Reading có passage/options/key/user answers: so đáp án, evidence và công thức; thiếu key thì tổng điểm unavailable, AI Suggested Answer chỉ gợi ý. Vocabulary cần source context thật. Learning cần summary có lỗi/số bài/rates, không bịa history. Import chỉ chép nguồn, không suy key bị thiếu.
Nêu một quy trình phù hợp, dữ liệu cần dán và capability cần có; không chấm dữ liệu chưa cung cấp hoặc giả đã nghe/đọc tệp. Không tạo kỳ thi riêng B1/B2/C1, không yêu cầu chain-of-thought. Chỉ hướng dẫn ngắn tiếng Việt, không tự lưu vào app.
```

## Production source

- [Bản đồ nguồn và phiên bản](../reference/prompt-version-map.md).
- [Schema snapshots](../reference/output-schemas.md).

## Differences from production

Chatbot không có backend tự đếm/tính/xác thực/caching và không tự biết lịch sử của bạn. Bản manual all-in-one gộp các phản hồi mà production có thể tạo riêng để tiết kiệm phí. JSON gần schema không đảm bảo điểm identical hoặc có thể import; chưa có UI/API nhập grading thủ công. Audio/transcript phải giữ tách bằng chứng; unknown không biến thành 0. Các mô tả analytics/lịch học là đối chiếu logic Python/SQL, không phải một AI grader mới.
