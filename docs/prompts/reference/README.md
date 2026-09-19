# Reference — Manual Prompts

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
| Kiểm duyệt độc lập đề sinh | [reference/question-quality-review.md](question-quality-review.md) | SKILL, MATERIAL | QuestionQualityReview | Có | Không | Không |
| Định dạng VSTEP.3–5 mà ứng dụng sử dụng | [reference/vstep-format.md](vstep-format.md) | MATERIAL | Báo cáo Markdown | Có | Không | Không |
| Quy tắc tính điểm và giới hạn quy đổi | [reference/scoring-rules.md](scoring-rules.md) | SCORES_AND_EVIDENCE | Báo cáo Markdown | Có | Không | Không |
| Output schemas và cách dùng JSON | [reference/output-schemas.md](output-schemas.md) | JSON_SCHEMA, CANDIDATE_JSON | Báo cáo Markdown | Có | Không | Không |
| Bản đồ nguồn và phiên bản | [reference/prompt-version-map.md](prompt-version-map.md) | SOURCE_CHANGE, CURRENT_MANUAL_PROMPT | Báo cáo Markdown | Có | Không | Không |
| Quy trình học thủ công khi API không dùng được | [reference/manual-workflows.md](manual-workflows.md) | GOAL_AND_AVAILABLE_INPUT | Báo cáo Markdown | Có | Không | Không |

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
