# Speaking — Manual Prompts

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
| Chấm Speaking Part 1 từ transcript | [speaking/part1-grading.md](part1-grading.md) | QUESTION, TRANSCRIPT | SpeakingTextGradingOutput | Có | Không | Không |
| Chấm Speaking Part 2 từ transcript | [speaking/part2-grading.md](part2-grading.md) | QUESTION, TRANSCRIPT | SpeakingTextGradingOutput | Có | Không | Không |
| Chấm Speaking Part 3 từ transcript | [speaking/part3-grading.md](part3-grading.md) | QUESTION, TRANSCRIPT | SpeakingTextGradingOutput | Có | Không | Không |
| Chấm Full Speaking từ transcript | [speaking/full-speaking-grading.md](full-speaking-grading.md) | ANSWERS | SpeakingTextGradingOutput | Có | Không | Không |
| Speaking all-in-one — chỉ văn bản | [speaking/all-in-one-text.md](all-in-one-text.md) | QUESTION, TRANSCRIPT | SpeakingTextGradingOutput | Có | Không | Không |
| Phân tích phát âm từ audio thật | [speaking/pronunciation-audio-analysis.md](pronunciation-audio-analysis.md) | AUDIO_FILE | AudioAssessment | Không | Bắt buộc | Không |
| Luyện phát âm theo câu mẫu | [speaking/pronunciation-practice.md](pronunciation-practice.md) | REFERENCE_TEXT, AUDIO_FILE | AudioAssessment | Không | Bắt buộc | Không |
| Speaking all-in-one — có audio | [speaking/all-in-one-audio.md](all-in-one-audio.md) | QUESTION, AUDIO_FILE | ManualSpeakingAudio | Không | Bắt buộc | Không |
| Sửa câu Speaking và câu trả lời mẫu | [speaking/speaking-correction.md](speaking-correction.md) | QUESTION, TRANSCRIPT | Báo cáo Markdown | Có | Không | Không |
| Chuyển audio thành transcript | [speaking/audio-transcription.md](audio-transcription.md) | AUDIO_FILE | Báo cáo Markdown | Không | Bắt buộc | Không |
| Nghe câu mẫu bằng giọng đọc | [speaking/reference-audio.md](reference-audio.md) | REFERENCE_TEXT | Báo cáo Markdown | Chỉ hướng dẫn bằng chữ | Cần khả năng phát audio; không cần file đầu vào | Không |
| Vocabulary Coach từ Speaking | [speaking/speaking-vocabulary-coach.md](speaking-vocabulary-coach.md) | QUESTION, TRANSCRIPT | VocabularyCoachOutput | Có | Không | Không |
| Sinh đề Speaking từng part | [speaking/speaking-question-generation.md](speaking-question-generation.md) | PART | GeneratedSpeakingQuestion | Có | Không | Không |

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
