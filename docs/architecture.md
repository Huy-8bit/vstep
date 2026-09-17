# Kiến trúc

Browser → Next.js App Router → API proxy cùng origin → FastAPI → PostgreSQL. FastAPI services gọi `LLMClient`; chỉ adapter OpenAI biết về SDK. UI sử dụng dữ liệu thật, có trạng thái trống, chờ và lỗi.

- Auth: Argon2; JWT access + refresh trong HttpOnly cookies. `auth_sessions` giữ hash refresh token, ngày hết hạn và trạng thái thu hồi. Refresh xoay vòng dưới row lock; logout thu hồi session và xóa cookie. Access token cũng kiểm tra session để logout có hiệu lực ngay.
- Next proxy chuyển các cookie và origin cần thiết, không chứa API key. Cookie SameSite=Lax; backend kiểm tra Origin trên write requests. Dùng HTTPS và Secure cookie khi `APP_ENV=production`.
- Exam service khóa hàng phiên thi khi lưu/chốt; revision phát hiện ghi đè từ nhiều tab. Đồng hồ frontend đồng bộ server mỗi 30 giây; backend kiểm tra thời hạn mỗi lần đọc/lưu/nộp.
- Phiên không mở lại sau hạn được chốt khi có request tiếp theo; không có scheduler chạy nền. Dữ liệu đã lưu không được thay đổi sau thời hạn.
- Grading đồng bộ, transaction-scoped advisory lock + row lock; không giữ trạng thái GRADING vĩnh viễn nếu provider lỗi. Grading thành công và errors commit cùng transaction.
- Autosave lưu local ngay khi gõ, debounce network một giây, serialize PATCH, retry sau tám giây / online. Nháp được phân vùng theo user/attempt. Bản chưa đồng bộ không được tính vào bài thi sau hạn nhưng có thể xuất văn bản.
- Frontend route `/result/[attemptId]` khởi chạy chấm các Task còn thiếu và tải lại dữ liệu đã lưu. Không có trợ giúp AI trước khi nộp.

Speaking và Reading được tích hợp bằng models/services/routes riêng, dùng chung auth và API proxy. Listening chưa được triển khai. Trước khi scale: quota, shared rate limit, job queue nếu cần và cơ chế khôi phục tác vụ AI. Rate limit hiện tại theo IP nhìn từ backend (qua proxy có thể dùng chung IP), phù hợp local MVP.


## Profile bài thi và năng lực người học

Các kỹ năng dùng chung `VSTEP_3_5` trong `common/test_profiles.py`. Public generation không nhận CEFR difficulty. Mức ước tính là kết quả sau chấm; mục tiêu người học không đổi profile bài thi. Reading có `ReadingTestBlueprint` chọn bốn passage với độ phân hóa và độ phủ dạng câu, đưa ngữ cảnh toàn đề vào mỗi lần sinh passage. Metadata passage/item chỉ dùng nội bộ, không được serializer trả về API làm bài. `legacy_difficulty` lưu dữ liệu cũ, không tham gia luồng tạo đề mới.


Writing v2 có checkpoint phân tích/hiệu chỉnh riêng; feedback chỉ sinh sau khi điểm chốt. Bộ chấm mới không thay điểm cũ khi mở trang; explicit regrade lưu snapshot trước khi nâng phiên bản. Speaking dùng audio provider riêng trả schema chuẩn hóa, text model chỉ chấm ngôn ngữ; backend hợp nhất năm tiêu chí. Pronunciation practice lưu từng lần ghi độc lập, TTS cache dùng khóa PostgreSQL và ghi tệp nguyên tử. Chi tiết trong `writing-assessment.md` và `speaking.md`.
