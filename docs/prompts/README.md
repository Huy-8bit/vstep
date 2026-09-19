# VSTEP Manual AI Prompt Kit

Đồng bộ 2026-09-19 · manual kit 1.0.0 · code commit `658986a`.

## Purpose

Bộ prompt dự phòng/thủ công cho chức năng AI của nền tảng VSTEP hiện có: dùng khi API/quota không sẵn sàng, muốn kiểm tra điểm hoặc so sánh các chatbot. Không cần API key để đọc/sao chép bộ này.

## When to use

Chọn đúng kỹ năng và loại đầu vào. ChatGPT/Claude/Gemini hoặc chatbot khác đều có thể dùng bản text; chức năng audio/ảnh chỉ dùng khi chatbot thực sự truy cập được tệp.

## Required input

- Mục tiêu đang học và các ô dữ liệu bắt buộc trong prompt đã chọn.

## Optional input

- Lịch sử đã tóm tắt, bài chấm trước, chủ đề và từ đã học khi prompt cho phép.

## Bắt đầu trong một phút

1. Chọn một file `quick` dưới đây; bản thường có thêm chế độ JSON và giải thích khác biệt.
2. Sao chép đúng một block hoàn chỉnh. Thay `{{QUESTION}}`, `{{STUDENT_ANSWER}}`... bằng dữ liệu thật. Xóa cả dấu `{{ }}` khi thay. Ô tùy chọn không dùng thì để trống hoặc ghi “không có”; không bỏ quên mẫu placeholder.
3. Với audio/ảnh/PDF, đính kèm **file thật**: một đường dẫn trên máy hoặc tên file trong text không cho chatbot truy cập nội dung.
4. Nhận báo cáo và kiểm lại phép tính, trích dẫn, key. Không cần ghép một rubric từ file khác; không yêu cầu chain-of-thought.

[Quick Writing 1](quick/quick-grade-writing-task1.md) · [Quick Writing 2](quick/quick-grade-writing-task2.md) · [Quick Speaking](quick/quick-grade-speaking.md) · [Quick Reading](quick/quick-explain-reading.md) · [Quick Vocabulary](quick/quick-vocabulary-coach.md) · [Quick Learning](quick/quick-learning-analysis.md)

Ví dụ thay ô dữ liệu: vùng QUESTION chứa toàn bộ đề; vùng STUDENT_ANSWER chỉ chứa bài **gốc**, không phải bài đã được sửa. WORD_COUNT tùy chọn, chatbot có thể đếm không chính xác như Python. Một task Writing chưa cho bậc kỹ năng; full Writing cần hai task và trọng số 1:2.

Không đưa credentials hoặc dữ liệu cá nhân không cần thiết vào chatbot. Kết quả ngoài chatbot không tự cập nhật ngân hàng đề, điểm, lịch sử, vocabulary/mastery hoặc kế hoạch trong ứng dụng. Tham khảo [quy trình](reference/manual-workflows.md), [công thức](reference/scoring-rules.md) và [JSON contracts](reference/output-schemas.md).

## Navigation

| Function | File | Required input | Expected output | Text chatbot? | Audio? | Image/PDF? |
| --- | --- | --- | --- | --- | --- | --- |
| Chấm Writing Task 1 | [writing/task1-grading.md](writing/task1-grading.md) | QUESTION, STUDENT_ANSWER | WritingCoreOutput | Có | Không | Không |
| Chấm Writing Task 2 | [writing/task2-grading.md](writing/task2-grading.md) | QUESTION, STUDENT_ANSWER | WritingCoreOutput | Có | Không | Không |
| Writing một bài: chấm và học trong một lượt | [writing/all-in-one-writing.md](writing/all-in-one-writing.md) | QUESTION, STUDENT_ANSWER | ManualWritingBundle | Có | Không | Không |
| Chấm Full Writing: Task 1 + Task 2 | [writing/full-writing-grading.md](writing/full-writing-grading.md) | TASK1_QUESTION, TASK1_ANSWER, TASK2_QUESTION, TASK2_ANSWER | ManualFullWriting | Có | Không | Không |
| Chữa từng câu Writing | [writing/sentence-correction.md](writing/sentence-correction.md) | QUESTION, STUDENT_ANSWER | SentenceCorrections | Có | Không | Không |
| Bài Writing đã sửa | [writing/corrected-version.md](writing/corrected-version.md) | QUESTION, STUDENT_ANSWER | CorrectedAnswer | Có | Không | Không |
| Bài tham khảo B2/B2+ | [writing/improved-answer.md](writing/improved-answer.md) | QUESTION, STUDENT_ANSWER | ImprovedAnswer | Có | Không | Không |
| Giải thích Writing chi tiết | [writing/detailed-feedback.md](writing/detailed-feedback.md) | QUESTION, STUDENT_ANSWER | WritingFeedback | Có | Không | Không |
| Writing: đánh giá lại độc lập | [writing/second-opinion.md](writing/second-opinion.md) | QUESTION, STUDENT_ANSWER, REVIEW_CONCERNS | WritingCoreOutput | Có | Không | Không |
| Chấm Speaking Part 1 từ transcript | [speaking/part1-grading.md](speaking/part1-grading.md) | QUESTION, TRANSCRIPT | SpeakingTextGradingOutput | Có | Không | Không |
| Chấm Speaking Part 2 từ transcript | [speaking/part2-grading.md](speaking/part2-grading.md) | QUESTION, TRANSCRIPT | SpeakingTextGradingOutput | Có | Không | Không |
| Chấm Speaking Part 3 từ transcript | [speaking/part3-grading.md](speaking/part3-grading.md) | QUESTION, TRANSCRIPT | SpeakingTextGradingOutput | Có | Không | Không |
| Chấm Full Speaking từ transcript | [speaking/full-speaking-grading.md](speaking/full-speaking-grading.md) | ANSWERS | SpeakingTextGradingOutput | Có | Không | Không |
| Speaking all-in-one — chỉ văn bản | [speaking/all-in-one-text.md](speaking/all-in-one-text.md) | QUESTION, TRANSCRIPT | SpeakingTextGradingOutput | Có | Không | Không |
| Phân tích phát âm từ audio thật | [speaking/pronunciation-audio-analysis.md](speaking/pronunciation-audio-analysis.md) | AUDIO_FILE | AudioAssessment | Không | Bắt buộc | Không |
| Luyện phát âm theo câu mẫu | [speaking/pronunciation-practice.md](speaking/pronunciation-practice.md) | REFERENCE_TEXT, AUDIO_FILE | AudioAssessment | Không | Bắt buộc | Không |
| Speaking all-in-one — có audio | [speaking/all-in-one-audio.md](speaking/all-in-one-audio.md) | QUESTION, AUDIO_FILE | ManualSpeakingAudio | Không | Bắt buộc | Không |
| Sửa câu Speaking và câu trả lời mẫu | [speaking/speaking-correction.md](speaking/speaking-correction.md) | QUESTION, TRANSCRIPT | Báo cáo Markdown | Có | Không | Không |
| Chuyển audio thành transcript | [speaking/audio-transcription.md](speaking/audio-transcription.md) | AUDIO_FILE | Báo cáo Markdown | Không | Bắt buộc | Không |
| Nghe câu mẫu bằng giọng đọc | [speaking/reference-audio.md](speaking/reference-audio.md) | REFERENCE_TEXT | Báo cáo Markdown | Chỉ hướng dẫn bằng chữ | Cần khả năng phát audio; không cần file đầu vào | Không |
| Vocabulary Coach từ Writing | [writing/writing-vocabulary-coach.md](writing/writing-vocabulary-coach.md) | QUESTION, STUDENT_ANSWER | VocabularyCoachOutput | Có | Không | Không |
| Vocabulary Coach từ Writing | [vocabulary/vocabulary-from-writing.md](vocabulary/vocabulary-from-writing.md) | QUESTION, STUDENT_ANSWER | VocabularyCoachOutput | Có | Không | Không |
| Vocabulary Coach từ Speaking | [speaking/speaking-vocabulary-coach.md](speaking/speaking-vocabulary-coach.md) | QUESTION, TRANSCRIPT | VocabularyCoachOutput | Có | Không | Không |
| Vocabulary Coach từ Speaking | [vocabulary/vocabulary-from-speaking.md](vocabulary/vocabulary-from-speaking.md) | QUESTION, TRANSCRIPT | VocabularyCoachOutput | Có | Không | Không |
| Vocabulary Coach từ Reading | [reading/reading-vocabulary-coach.md](reading/reading-vocabulary-coach.md) | QUESTION, READING_PASSAGE | VocabularyCoachOutput | Có | Không | Không |
| Vocabulary Coach từ Reading | [vocabulary/vocabulary-from-reading.md](vocabulary/vocabulary-from-reading.md) | QUESTION, READING_PASSAGE | VocabularyCoachOutput | Có | Không | Không |
| Kiểm tra câu mới dùng từ đã học | [vocabulary/usage-assessment.md](vocabulary/usage-assessment.md) | PHRASE, USER_SENTENCE | VocabularyUsageAssessment | Có | Không | Không |
| Giải thích một câu Reading | [reading/answer-explanation.md](reading/answer-explanation.md) | PASSAGE, QUESTION, OPTIONS | ManualReadingExplanation | Có | Không | Không |
| Phân tích kết quả Reading | [reading/reading-analysis.md](reading/reading-analysis.md) | READING_PASSAGE, QUESTIONS_AND_OPTIONS, USER_ANSWERS | ManualReadingAnalysis | Có | Không | Không |
| Reading: chấm, giải thích và học trong một lượt | [reading/all-in-one-reading.md](reading/all-in-one-reading.md) | READING_PASSAGE, QUESTIONS_AND_OPTIONS, USER_ANSWERS | ManualReadingAnalysis | Có | Không | Không |
| Sinh đề Writing VSTEP.3–5 | [writing/writing-question-generation.md](writing/writing-question-generation.md) | TASK | GeneratedQuestion | Có | Không | Không |
| Sinh đề Speaking từng part | [speaking/speaking-question-generation.md](speaking/speaking-question-generation.md) | PART | GeneratedSpeakingQuestion | Có | Không | Không |
| Sinh một passage Reading | [reading/reading-question-generation.md](reading/reading-question-generation.md) | TOPIC | GeneratedReadingPassage | Có | Không | Không |
| Sinh Full Reading 4 passages / 40 câu | [reading/reading-full-test-generation.md](reading/reading-full-test-generation.md) | TOPIC | ManualReadingFullTest | Có | Không | Không |
| Giải nghĩa một từ trong đoạn đọc | [reading/selected-term-explanation.md](reading/selected-term-explanation.md) | TERM, PARAGRAPH | ReadingVocabulary | Có | Không | Không |
| Phân tích nhu cầu học từ lịch sử tóm tắt | [learning/learning-analysis.md](learning/learning-analysis.md) | LEARNER_HISTORY_SUMMARY | ManualLearningAnalysis | Có | Không | Không |
| Đối chiếu và ưu tiên điểm yếu | [learning/weakness-analysis.md](learning/weakness-analysis.md) | LEARNER_HISTORY_SUMMARY | ManualLearningAnalysis | Có | Không | Không |
| Bài học ngữ pháp theo lỗi | [learning/grammar-lesson.md](learning/grammar-lesson.md) | GRAMMAR_CONCEPT | PersonalizedLessonOutput | Có | Không | Không |
| Bài học từ vựng theo ngữ cảnh | [learning/vocabulary-lesson.md](learning/vocabulary-lesson.md) | VOCABULARY_ITEMS | PersonalizedLessonOutput | Có | Không | Không |
| Học sâu một nhóm từ/cụm | [vocabulary/vocabulary-lesson.md](vocabulary/vocabulary-lesson.md) | VOCABULARY_ITEMS | PersonalizedLessonOutput | Có | Không | Không |
| Bài học chiến lược Reading | [learning/reading-strategy-lesson.md](learning/reading-strategy-lesson.md) | READING_CONCEPT | PersonalizedLessonOutput | Có | Không | Không |
| Bài học Speaking có mục tiêu | [learning/speaking-coach.md](learning/speaking-coach.md) | SPEAKING_CONCEPT | PersonalizedLessonOutput | Có | Không | Không |
| Tạo bài tập cá nhân hóa | [learning/personalized-exercise-generation.md](learning/personalized-exercise-generation.md) | CONCEPT_KEY, USER_CONTEXT | PersonalizedExercisesOutput | Có | Không | Không |
| Tạo bài tập từ vựng | [vocabulary/vocabulary-exercise-generation.md](vocabulary/vocabulary-exercise-generation.md) | CONCEPT_KEY, USER_CONTEXT | PersonalizedExercisesOutput | Có | Không | Không |
| Phản hồi bài luyện một concept | [learning/exercise-feedback.md](learning/exercise-feedback.md) | CONCEPT_KEY, EXERCISE_AND_RUBRIC, LEARNER_ANSWER | ExerciseAssessment | Có | Không | Không |
| Lập lịch học có bằng chứng | [learning/daily-study-plan.md](learning/daily-study-plan.md) | LEARNER_HISTORY_SUMMARY | Báo cáo Markdown | Có | Không | Không |
| Tổng kết học tập hàng tuần | [learning/weekly-review.md](learning/weekly-review.md) | LEARNER_HISTORY_SUMMARY | WeeklyCoachOutput | Có | Không | Không |
| Tạo đề luyện để kiểm tra khả năng áp dụng | [learning/targeted-practice.md](learning/targeted-practice.md) | TARGET_SKILL_AND_CONCEPT, EVIDENCE_SUMMARY | Báo cáo Markdown | Có | Không | Không |
| Trích xuất đề Writing nguyên văn | [question-import/parse-writing-question.md](question-import/parse-writing-question.md) | RAW_SOURCE_TEXT | ParsedImport | Có | Không | Tùy nguồn: ảnh/PDF cần chatbot đọc được |
| Trích xuất đề Speaking nguyên văn | [question-import/parse-speaking-question.md](question-import/parse-speaking-question.md) | RAW_SOURCE_TEXT | ParsedImport | Có | Không | Tùy nguồn: ảnh/PDF cần chatbot đọc được |
| Trích xuất đề Reading nguyên văn | [question-import/parse-reading-question.md](question-import/parse-reading-question.md) | RAW_SOURCE_TEXT | ParsedImport | Có | Không | Tùy nguồn: ảnh/PDF cần chatbot đọc được |
| Trích xuất đề Generic nguyên văn | [question-import/parse-generic-question.md](question-import/parse-generic-question.md) | RAW_SOURCE_TEXT | ParsedImport | Có | Không | Tùy nguồn: ảnh/PDF cần chatbot đọc được |
| Kiểm duyệt độc lập đề sinh | [reference/question-quality-review.md](reference/question-quality-review.md) | SKILL, MATERIAL | QuestionQualityReview | Có | Không | Không |
| Định dạng VSTEP.3–5 mà ứng dụng sử dụng | [reference/vstep-format.md](reference/vstep-format.md) | MATERIAL | Báo cáo Markdown | Có | Không | Không |
| Quy tắc tính điểm và giới hạn quy đổi | [reference/scoring-rules.md](reference/scoring-rules.md) | SCORES_AND_EVIDENCE | Báo cáo Markdown | Có | Không | Không |
| Output schemas và cách dùng JSON | [reference/output-schemas.md](reference/output-schemas.md) | JSON_SCHEMA, CANDIDATE_JSON | Báo cáo Markdown | Có | Không | Không |
| Bản đồ nguồn và phiên bản | [reference/prompt-version-map.md](reference/prompt-version-map.md) | SOURCE_CHANGE, CURRENT_MANUAL_PROMPT | Báo cáo Markdown | Có | Không | Không |
| Quy trình học thủ công khi API không dùng được | [reference/manual-workflows.md](reference/manual-workflows.md) | GOAL_AND_AVAILABLE_INPUT | Báo cáo Markdown | Có | Không | Không |
| Writing Task 1 | [quick/quick-grade-writing-task1.md](quick/quick-grade-writing-task1.md) | QUESTION, STUDENT_ANSWER | Báo cáo Markdown | Có | Không | Không |
| Writing Task 2 | [quick/quick-grade-writing-task2.md](quick/quick-grade-writing-task2.md) | QUESTION, STUDENT_ANSWER | Báo cáo Markdown | Có | Không | Không |
| Speaking text | [quick/quick-grade-speaking.md](quick/quick-grade-speaking.md) | QUESTION, TRANSCRIPT | Báo cáo Markdown | Có | Không | Không |
| Giải thích Reading | [quick/quick-explain-reading.md](quick/quick-explain-reading.md) | PASSAGE, QUESTION, OPTIONS | Báo cáo Markdown | Có | Không | Không |
| Vocabulary Coach | [quick/quick-vocabulary-coach.md](quick/quick-vocabulary-coach.md) | SOURCE_SKILL, SOURCE_TEXT | Báo cáo Markdown | Có | Không | Không |
| Phân tích học tập | [quick/quick-learning-analysis.md](quick/quick-learning-analysis.md) | LEARNER_HISTORY_SUMMARY | Báo cáo Markdown | Có | Không | Không |

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

- [Bản đồ nguồn và phiên bản](reference/prompt-version-map.md).
- [Schema snapshots](reference/output-schemas.md).

## Differences from production

Chatbot không có backend tự đếm/tính/xác thực/caching và không tự biết lịch sử của bạn. Bản manual all-in-one gộp các phản hồi mà production có thể tạo riêng để tiết kiệm phí. JSON gần schema không đảm bảo điểm identical hoặc có thể import; chưa có UI/API nhập grading thủ công. Audio/transcript phải giữ tách bằng chứng; unknown không biến thành 0. Các mô tả analytics/lịch học là đối chiếu logic Python/SQL, không phải một AI grader mới.
