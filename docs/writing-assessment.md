# Writing assessment 2.0.0

Pipeline chấm điểm dùng bài **gốc**. `WritingAnalysisService` tạo structured evidence, `WritingScoreCalibrationService` hiệu chỉnh điểm, sau đó mới sinh hướng dẫn sửa bài. Không truyền target level, bản đã sửa hoặc bài cải thiện vào bước chấm.

1. Analysis nhận đề, requirements, bài gốc và sentence IDs. Model chỉ phân tích: độ phủ/phát triển ý, register, cohesion, positive/negative evidence, lỗi và loại cấu trúc. Backend kiểm tra trích dẫn nằm trong bài gốc/câu tương ứng và yêu cầu đủ IDs/requirements.
2. Python gộp các lỗi trùng vùng trích dẫn, tính word/sentence count, lỗi major/minor, lỗi trên 100 từ, cấu trúc simple/compound/complex/compound-complex, relative/conditional/subordinate clauses. Phát hiện lỗi và cấu trúc là model-assisted, không phải parser ngữ pháp hoàn hảo. Metrics là bằng chứng, không phải công thức trừ điểm.
3. Calibration chỉ nhận structured evidence/metrics, cùng sáu bài tham chiếu editorial từ yếu đến strong B2/C1. Có nguyên văn email Alex như một trường hợp hiệu chỉnh, không có so sánh chuỗi hay hardcode số điểm cho bài này. Mỗi tiêu chí có initial/final score, bằng chứng, justification và kiểm tra tính nhất quán; 7+ cần ít nhất hai trích dẫn tích cực khác nhau và giải thích đáng kể. Không được bỏ negative evidence từ bước phân tích. Điểm bốn tiêu chí là bội số 0.5; overall tính bằng Python, trung bình bằng nhau, không làm tròn dữ liệu gốc.
4. Khi điểm cao mâu thuẫn với basic range, lỗi cơ bản, ý chưa phát triển hoặc cohesion đơn giản, checkpoint có `consistency_flags` và một lượt review riêng. Model phải giảm mức điểm hoặc giải thích bằng bằng chứng đủ mạnh. Backend không tự trừ số điểm cố định và không ép phân phối điểm.
5. Sau khi điểm cố định, model mới sinh summary, ba ưu tiên, sửa từng câu, bản sửa tối thiểu và bài tham khảo B2. Schema feedback không chứa scores; feedback không thể thay đổi điểm.

Các anchor là hướng dẫn nội bộ, **không** phải dữ liệu người chấm hay điểm VSTEP chính thức. Alex nhắm đến khoảng mid-5 đến low-6 tùy bằng chứng, không bắt buộc một con số. Chất lượng và độ lặp lại của điểm thực tế cần được đối chiếu với người chấm; triển khai không tự chứng minh độ chính xác.

## Lưu trữ và retry

`writing_attempts.grading_work` lưu từng checkpoint và cache key theo đề/bài/model/các prompt versions/nhiệt độ. UI gọi từng bước để không gom nhiều API model chậm vào một HTTP request. Retry tiếp tục phần đã lưu, giữ bài và điểm cũ nếu xử lý thất bại. PostgreSQL locks chặn chấm đồng thời cùng attempt. Cache kết quả đã hoàn tất chỉ dùng trong cùng user. Nếu mất kết nối ngay sau khi provider xử lý nhưng trước khi lưu DB, retry có thể phát sinh phí tiếp.

`writing_gradings` lưu `grader_version`, `ai_model`, analysis/calibration/feedback prompt versions, criterion evidence và analysis snapshot. Migration đánh dấu kết quả cũ `1.0.0`; bài chấm mới dùng `2.0.0`. Mở bài cũ không tự chấm lại. Khi bấm **Chấm lại với bộ chấm mới**, lưu toàn bộ snapshot cũ vào `writing_grading_revisions` trước khi thay kết quả trong cùng transaction. History/progress dùng kết quả hiện hành; lịch sử phiên bản vẫn xem được tại trang kết quả. Chấm lại phiên bản hiện hành là idempotent.

## API

Dưới `/api/v1`, bắt buộc xác thực và ownership:

| Method | Route | Mục đích |
| --- | --- | --- |
| POST | `/attempts/{id}/analyze?upgrade=false` | Lưu evidence/metrics |
| POST | `/attempts/{id}/calibrate?upgrade=false` | Chấm hoặc review; trả `reviewed` |
| POST | `/attempts/{id}/grade` | Hoàn tất feedback; tự chạy các bước còn thiếu cho API clients |
| POST | `/attempts/{id}/regrade` | Nâng bộ chấm và lưu kết quả cũ; không thay bài nộp |
| GET | `/attempts/{id}/grading-history` | Kết quả hiện tại và snapshots cũ |
| GET | `/internal/writing-calibration/{id}` | Bài gốc, scores, evidence, versions và checkpoints, chỉ admin allowlist |

UI gọi analyze → calibrate → nếu chưa reviewed, calibrate thêm lần nữa → grade/regrade. Khi nâng phiên bản, hai bước đầu dùng `upgrade=true`.

Admin allowlist cấu hình `WRITING_CALIBRATION_ADMIN_EMAILS=email1,email2`; mặc định trống, không mở inspection. Admin vẫn phải đăng nhập. `writing_calibration_samples` chuẩn bị question/answer, năm human score fields, reviewer_count, created_at; chưa giả lập hoặc tự điền dữ liệu giáo viên.

`OPENAI_GRADING_TEMPERATURE` tùy chọn 0–0.3, chỉ đặt nếu model hỗ trợ temperature. Bỏ trống khi model không hỗ trợ tham số này. Backend dùng cùng model/config cho các giai đoạn, cache và version rõ ràng để hạn chế biến động; không hứa kết quả model luôn hoàn toàn xác định.
