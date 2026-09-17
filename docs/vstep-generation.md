# Sinh đề VSTEP và cổng chất lượng

`app/vstep_reference` là nguồn cấu trúc dùng chung: format, blueprint Writing/Speaking/Reading, taxonomy và ví dụ tổng hợp. Generator/validator hiện mang phiên bản **3.0.0**.

## Luồng sinh đề

1. Mặc định dùng **BANK**: đề mẫu đã biên soạn hoặc đề AI đã qua kiểm tra. Chọn câu chưa làm trước, tránh chủ đề/câu vừa gặp. Writing và Speaking chỉ sinh mới khi chọn AI; Reading có thể bổ sung AI khi ngân hàng thiếu slot phù hợp.
2. Generator nhận profile VSTEP_3_5, blueprint, chủ đề/dạng câu, ID và nội dung gần đây. Fingerprint chống trùng chính xác; so sánh văn bản chuẩn hóa chống gần trùng. Không dùng embedding hay chọn độ khó B1/B2/C1.
3. Pydantic và validators kiểm tra cấu trúc, số lượng, stimulus, yêu cầu giao tiếp, quote bằng chứng và options. `WritingTask1QuestionValidator` kiểm tra thư/email, quan hệ người nhận, register và 2–4 nhu cầu (`communicative_requirements` trong schema sinh đề, lưu tương thích trong cột `requirements`); `SpeakingQuestionValidator` kiểm tra hai chủ đề, ba giải pháp phân biệt, ý riêng/follow-up và loại cue-card IELTS.
4. Một lượt LLM độc lập kiểm tra ngữ nghĩa: tình huống thực tế, nhất quán, không cần kiến thức chuyên môn, không chứa bài mẫu. Reading giải độc lập từng câu và đối chiếu key, tính duy nhất, evidence và distractors. Mọi item phải đạt ngưỡng tin cậy nội bộ 0,8. Không đạt thì không lưu đề vừa sinh.
5. Đề hợp lệ được lưu kèm `generation_diagnostics`: generator/validator version, source blueprint, model, format/quality flags, review notes. `created_at` thuộc bản ghi đề. Đề mẫu có nguồn kiểm tra `authored_synthetic_seed`, không giả là đã được LLM kiểm tra.

Kiểm tra AI giảm lỗi, không đảm bảo tuyệt đối mọi đáp án đều hoàn hảo. Threshold/kiểm tra tương đồng là heuristic sản phẩm.

## Reading toàn đề

`ReadingFullTestBlueprint` ghép bốn slot có độ yêu cầu tăng dần; kiểm tra cùng lúc 40 câu, 1.900–2.050 từ, ≥3 chủ đề, ≥8 dạng câu, mỗi key A–D có 5–15 lần. Dạng câu và mức yêu cầu cũng thay đổi trong từng passage. Nếu thiếu slot, generator nhận các passage đã chọn, phân bổ key/dạng câu và ngân sách từ còn lại. Full Test luôn đa chủ đề; bộ lọc chủ đề dành cho luyện riêng.

Taxonomy gồm detail, main idea/title, vocabulary, reference, inference, purpose, attitude, tone, negative detail, sentence interpretation, insertion, paragraph/passage completion và organization. Insertion lưu bốn vị trí A–D bằng quote mốc chính xác và câu cần chèn; UI hiển thị các mốc cạnh đoạn. Completion là chọn một câu kết nối phù hợp sau đoạn được chỉ định. Không dùng True/False/Not Given hay matching headings trong simulator.

API làm bài chỉ trả allowlist công khai; không trả key, evidence, rationales, quality review hoặc internal difficulty. API kết quả chỉ mở sau nộp và kiểm tra quyền sở hữu.

## Writing calibration

`WritingEvidenceAnalysisService` kiểm tra quote, lỗi và phát triển ý; `WritingScoreCalibrationService` dùng anchor tự biên soạn cho cả Task 1/2, bằng chứng tích cực/tiêu cực và lượt rà soát khi điểm chưa nhất quán. Điểm ≥7 cần bằng chứng tích cực cụ thể; không cộng điểm chỉ vì đủ từ hay nhắc đủ yêu cầu. Feedback/Vocabulary/Correction chỉ chạy sau khi điểm đã chốt, không được đổi điểm.

Mỗi pha lưu checkpoint; lỗi Vocabulary có thể được thử lại ở tab kết quả và không chặn công bố điểm đã hiệu chỉnh. Lưu `grader_version`, `analysis_prompt_version`, `calibration_prompt_version` (API alias `calibration_version`), model, timestamps và revisions. `writing_calibration_samples` đã có question_id, task_type, answer, bốn human_*_score, human_overall_score, reviewer_count, notes, created_at; chưa có dữ liệu chấm người được giả lập.
