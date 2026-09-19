# Reading — Manual Prompts

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
| Vocabulary Coach từ Reading | [reading/reading-vocabulary-coach.md](reading-vocabulary-coach.md) | QUESTION, READING_PASSAGE | VocabularyCoachOutput | Có | Không | Không |
| Giải thích một câu Reading | [reading/answer-explanation.md](answer-explanation.md) | PASSAGE, QUESTION, OPTIONS | ManualReadingExplanation | Có | Không | Không |
| Phân tích kết quả Reading | [reading/reading-analysis.md](reading-analysis.md) | READING_PASSAGE, QUESTIONS_AND_OPTIONS, USER_ANSWERS | ManualReadingAnalysis | Có | Không | Không |
| Reading: chấm, giải thích và học trong một lượt | [reading/all-in-one-reading.md](all-in-one-reading.md) | READING_PASSAGE, QUESTIONS_AND_OPTIONS, USER_ANSWERS | ManualReadingAnalysis | Có | Không | Không |
| Sinh một passage Reading | [reading/reading-question-generation.md](reading-question-generation.md) | TOPIC | GeneratedReadingPassage | Có | Không | Không |
| Sinh Full Reading 4 passages / 40 câu | [reading/reading-full-test-generation.md](reading-full-test-generation.md) | TOPIC | ManualReadingFullTest | Có | Không | Không |
| Giải nghĩa một từ trong đoạn đọc | [reading/selected-term-explanation.md](selected-term-explanation.md) | TERM, PARAGRAPH | ReadingVocabulary | Có | Không | Không |

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
