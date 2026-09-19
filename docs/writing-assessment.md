# Writing assessment 4.1.0 — calibrated task routing

Giữ rubric và yêu cầu bằng chứng, gộp phân tích và chấm thành một Structured Output. Cấu hình được chọn là **Luna / medium**, chấm lại có điều kiện bằng **Terra / none**, chính sách 1.5. Hai lượt kiểm định trên 13 mẫu nội bộ đều vượt ngưỡng; đây chưa phải xác nhận chất lượng bởi giám khảo độc lập. Xem kết quả, chi phí và trạng thái triển khai tại [MODEL_EVALUATION.md](../MODEL_EVALUATION.md).

## Luồng chấm

1. `WritingCoreService` nhận đề, requirements, bài **gốc** và sentence ID do backend tạo. Model phân tích độ phủ, phát triển ý, register, cohesion, range, lỗi, cấu trúc rồi cho bốn điểm theo bước 0.5. Không truyền bài đã sửa, target level hoặc nhãn tham chiếu benchmark vào request.
2. Bằng chứng tham chiếu sentence ID; backend lấy nguyên văn câu gốc. Lỗi phải trích một đoạn liên tục trong đúng câu. ID không tồn tại, trích dẫn sai hoặc thiếu phân tích câu đều bị từ chối; tối đa một retry. Điểm 7+ vẫn cần hai trích dẫn tích cực khác nhau và giải thích có nội dung.
3. Python loại lỗi trùng vùng trích dẫn và tính word count, mật độ lỗi, major/minor và thống kê cấu trúc. Phát hiện lỗi/cấu trúc vẫn dựa trên AI. Lỗi là các ví dụ tiêu biểu, không bảo đảm liệt kê mọi lỗi. Không trừ điểm cố định theo số lỗi.
4. `GradingEscalationService` kiểm tra confidence, mâu thuẫn điểm với range/cohesion/control, lỗi dày đặc, điểm cao khi bằng chứng ngắn, task/language khác biệt rõ, ranh giới năng lực thiếu chắc chắn và output sai schema. Chỉ trường hợp bị đánh dấu mới gọi Terra. Lưu điểm gốc, lý do chuyển tiếp, model cuối và confidence. Không tự trừ điểm hay ép phân phối.
5. Backend tính overall bằng trung bình bốn tiêu chí, lưu kết quả cùng evidence, metrics, summary ngắn và ba ưu tiên. Đồng bộ Personalized Learning từ kết quả đã lưu. Reading vẫn chấm bằng Python.
6. Người học yêu cầu riêng **Chữa từng câu**, **Bài đã sửa**, **Bài tham khảo**, **Giải thích chi tiết**, **Vocabulary nâng cao**. Schema phản hồi bổ sung không chứa điểm. Mỗi phần lưu và tái sử dụng riêng; mở phần này không sinh các phần khác.

Rubric calibration được giữ trong prompt chung. Bài anchor đầy đủ được dùng làm dữ liệu đánh giá, không được đưa vào prompt core để model nhìn thấy đáp án tham chiếu. Chưa có dữ liệu giáo viên; toàn bộ 13 nhãn hiện tại là ước lượng editorial, không phải chuẩn VSTEP chính thức. Email Alex là một mẫu hồi quy, không được tìm theo câu chữ hoặc gán cứng điểm.

## Cache, lịch sử và lỗi

`writing_attempts.grading_work` lưu checkpoint core, routing và artifact tùy chọn. Cache key chứa đề/ngữ cảnh/bài gốc, model/effort, MODEL_VERSION, grader/prompt version, temperature và cấu hình/phiên bản chuyển tiếp. Chỉ tái sử dụng trong cùng tài khoản. PostgreSQL advisory lock theo attempt và content ngăn gọi trùng đồng thời; phần phản hồi tùy chọn có content lock riêng.

Mở bài chấm cũ không gọi lại AI. **Chấm lại với bộ chấm mới** lưu snapshot cũ vào `writing_grading_revisions`, giữ IDs và bài đã nộp. Gọi lại phiên bản hiện hành là idempotent. Mất kết nối sau khi provider xử lý nhưng trước khi lưu vẫn có thể phát sinh phí tiếp khi retry.

Nếu model phản hồi không hợp lệ, không xuất bản điểm mới. Lỗi mạng/hạn mức không tự chuyển model để né lỗi tài khoản; bài đã nộp vẫn giữ nguyên. Hết credit có mã `ai_quota_exhausted`.

## API

Các endpoint dưới `/api/v1` yêu cầu xác thực và ownership:

| Method | Route | Mục đích |
| --- | --- | --- |
| POST | `/attempts/{id}/grade` | Một request chạy core/có thể review, rồi lưu điểm |
| POST | `/attempts/{id}/analyze?upgrade=false` | Compatibility endpoint lưu core checkpoint |
| POST | `/attempts/{id}/calibrate?upgrade=false` | Compatibility endpoint, tái sử dụng core |
| POST | `/attempts/{id}/regrade` | Nâng grader version, lưu lịch sử |
| POST | `/attempts/{id}/optional-feedback/{kind}` | `sentences`, `corrected`, `improved`, `detailed` |
| POST | `/attempts/{id}/vocabulary` | Tạo Vocabulary Coach theo yêu cầu |
| GET | `/attempts/{id}/grading-history` | Phiên bản hiện tại và snapshots |
| GET | `/internal/writing-calibration/{id}` | Inspection theo admin allowlist |
| POST | `/internal/ai-costs/human-references/{id}` | Admin lưu điểm người chấm riêng biệt |

`OPENAI_MODEL_WRITING_ANALYSIS` và `OPENAI_MODEL_WRITING_SCORING` giống model/effort thì dùng chung một call. Nếu quản trị viên cố ý đặt khác nhau, backend gọi calibration riêng và kiểm tra mâu thuẫn trước khi chuyển tiếp. Cấu hình tùy chỉnh này cần benchmark lại. Xem [operation inventory và cấu hình cost](ai-operations.md).
