# Learning — Manual Prompts

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
| Phân tích nhu cầu học từ lịch sử tóm tắt | [learning/learning-analysis.md](learning-analysis.md) | LEARNER_HISTORY_SUMMARY | ManualLearningAnalysis | Có | Không | Không |
| Đối chiếu và ưu tiên điểm yếu | [learning/weakness-analysis.md](weakness-analysis.md) | LEARNER_HISTORY_SUMMARY | ManualLearningAnalysis | Có | Không | Không |
| Bài học ngữ pháp theo lỗi | [learning/grammar-lesson.md](grammar-lesson.md) | GRAMMAR_CONCEPT | PersonalizedLessonOutput | Có | Không | Không |
| Bài học từ vựng theo ngữ cảnh | [learning/vocabulary-lesson.md](vocabulary-lesson.md) | VOCABULARY_ITEMS | PersonalizedLessonOutput | Có | Không | Không |
| Bài học chiến lược Reading | [learning/reading-strategy-lesson.md](reading-strategy-lesson.md) | READING_CONCEPT | PersonalizedLessonOutput | Có | Không | Không |
| Bài học Speaking có mục tiêu | [learning/speaking-coach.md](speaking-coach.md) | SPEAKING_CONCEPT | PersonalizedLessonOutput | Có | Không | Không |
| Tạo bài tập cá nhân hóa | [learning/personalized-exercise-generation.md](personalized-exercise-generation.md) | CONCEPT_KEY, USER_CONTEXT | PersonalizedExercisesOutput | Có | Không | Không |
| Phản hồi bài luyện một concept | [learning/exercise-feedback.md](exercise-feedback.md) | CONCEPT_KEY, EXERCISE_AND_RUBRIC, LEARNER_ANSWER | ExerciseAssessment | Có | Không | Không |
| Lập lịch học có bằng chứng | [learning/daily-study-plan.md](daily-study-plan.md) | LEARNER_HISTORY_SUMMARY | Báo cáo Markdown | Có | Không | Không |
| Tổng kết học tập hàng tuần | [learning/weekly-review.md](weekly-review.md) | LEARNER_HISTORY_SUMMARY | WeeklyCoachOutput | Có | Không | Không |
| Tạo đề luyện để kiểm tra khả năng áp dụng | [learning/targeted-practice.md](targeted-practice.md) | TARGET_SKILL_AND_CONCEPT, EVIDENCE_SUMMARY | Báo cáo Markdown | Có | Không | Không |

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
