# Chấm và chữa bài bằng AI

`QuestionGeneratorService` và `WritingGradingService` phụ thuộc `LLMClient`. `OpenAILLMClient` dùng [Responses Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs) thông qua `AsyncOpenAI.responses.parse(text_format=PydanticModel)`. API key chỉ đọc từ backend settings, model đọc từ `OPENAI_MODEL`, không gắn model vào prompt/business logic.

Writing generator/evidence/calibration/feedback và blueprint/validators hiện ở phiên bản `3.0.0`. Pipeline: evidence → calibration → feedback → Vocabulary Coach → correction. Giai đoạn sau không sửa điểm đã hiệu chỉnh; dữ liệu lịch sử chỉ đổi qua thao tác chấm lại có lưu revision. Chi tiết tại [sinh đề và hiệu chỉnh](vstep-generation.md).

Output được validate bằng Pydantic, kiểm tra đúng task/metadata và trích dẫn lỗi có trong bài gốc. Invalid output retry tối đa một lần; timeout/API lỗi trả lỗi sạch, không xóa bài đã nộp. SDK retry mặc định bị tắt để kiểm soát số lần gọi. Model từ chối hoặc trả incomplete không được coi là bài chấm thành công.

Điểm Task = trung bình Task Fulfillment, Organization, Vocabulary, Grammar. Điểm Writing = `(Task1 + Task2 × 2) / 3`. Backend tính lại điểm tổng và số từ, không tin phép tính của model. Thiếu từ được phân tích trong Task Fulfillment, không có công thức trừ điểm theo số từ.

Schema gồm summary, strengths, đúng 3 priority improvements, structure feedback, task fulfillment feedback, categorized errors, vocabulary suggestions, sentence feedback, corrected version và improved B2 version. Bản sửa giữ ý/cách viết; bản B2 nâng cách trình bày vừa tầm. Toàn bộ giải thích bằng tiếng Việt.

Prompt xem answer/question như dữ liệu, không phải chỉ dẫn; hạn chế prompt injection bằng phân vai, schema, kiểm tra output và phép tính backend. Không coi prompt là biện pháp bảo vệ tuyệt đối. Điểm và sửa lỗi vẫn có thể không chính xác.

Cache SHA-256 trên đề/yêu cầu/loại, answer, model, version; chỉ reuse trong cùng tài khoản. Advisory lock theo user + hash, cùng row lock attempt, ngăn yêu cầu đồng thời gọi trùng. Usage ghi ở transaction riêng kể cả khi grading rollback. Nếu SDK không trả được usage do lỗi parse/network, token ghi 0 (không xác định), không diễn giải thành không tính phí.

Một Task Writing không có nhãn B1/B2/C1. Chỉ khi chấm đủ Task 1 + Task 2, giao diện có thể hiển thị “Năng lực Writing tham khảo” với ngưỡng sản phẩm 4/6/8,5, luôn kèm nhãn AI ước tính và không phải chứng nhận VSTEP.

Không có key: đề mẫu vẫn dùng được; AI operations trả HTTP 503 `ai_not_configured`. Không tạo feedback giả để thay API thật.
