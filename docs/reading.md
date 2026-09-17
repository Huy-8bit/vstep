# Reading MVP

Reading dùng chung tài khoản, PostgreSQL, FastAPI, Next.js và OpenAI adapter của Writing/Speaking. Mở `http://localhost:3000/reading` sau khi chạy `docker compose up -d --build`.

## Ngân hàng đề và các chế độ

| Mode | Nội dung | Đồng hồ |
| --- | --- | --- |
| `FULL_TEST` | 4 passages, mỗi passage 10 câu A/B/C/D, tổng 40 | Bắt buộc 60 phút |
| `PASSAGE_PRACTICE` | 1 passage, 10 câu | Tùy chọn 15 phút |
| `QUICK_PRACTICE` | 5 câu trên một passage có sẵn; đề AI mới khoảng 250–350 từ | Tùy chọn 8 phút |
| `QUESTION_TYPE_PRACTICE` | Các câu cùng dạng từ một hoặc nhiều passage, tối đa 5 | Tùy chọn 8 phút |

Ngân hàng chung **VSTEP.3–5** có 15 bộ lọc chủ đề, không có lựa chọn B1/B2/C1. Bộ mẫu gồm **8 bài gốc, 80 câu**, mỗi bài 490–534 từ; giữ nguyên nội dung, đáp án, giải thích và ID từ trước refactor.

`ReadingTestBlueprint` phiên bản `2.0.0` ghép một bài cho mỗi vị trí theo nhóm nội bộ ACCESSIBLE → MODERATE → CHALLENGING → ADVANCED. Đây là phân loại biên soạn theo nội dung cụ thể, không phải phép quy đổi CEFR chính thức. Mỗi vị trí yêu cầu các dạng câu nhất định; cả đề phủ mười dạng. Mỗi bài phải có 10 câu và ít nhất hai nhóm yêu cầu ở cấp câu hỏi. Đề thiếu độ phủ hoặc metadata không được ghép chỉ để đủ số lượng.

Full Test/chủ đề ngẫu nhiên dùng được ngay khi không có key. Một chủ đề riêng có thể cần thêm bài; API bank báo số passage cần bổ sung theo blueprint, không tiết lộ nhãn nội bộ. Luyện dạng câu lấy tối đa năm câu có thật từ một hoặc nhiều passage, không lặp câu để tăng số lượng. Chọn một passage chỉ lấy các câu đúng dạng trong bài đó.

Bank ưu tiên bài người dùng chưa mở trong phiên trước, cho phép làm lại khi hết bài mới. Không gọi AI mỗi lần bắt đầu nếu có đủ bài. Nút **Tạo đề mới bằng AI** tạo một passage rồi lưu dùng lại cho nhiều người; ở Full Test, passage được tạo cho vị trí còn thiếu (hoặc một vị trí thay thế khi đã đủ) trong blueprint toàn đề. Khi phải bổ sung nhiều passage, frontend gọi từng lần trước khi bắt đầu đồng hồ. Đề đã dùng không được chỉnh sửa qua API. Seed dùng fingerprint nội dung và có thể chạy lại an toàn:

```sh
cd backend
alembic upgrade head
python -m app.db.reading_seed
```

## Lưu bài, đồng hồ và nộp bài

Backend lưu `started_at` và `expires_at`; frontend căn đồng hồ theo `server_now`. Reload không cấp lại thời gian. Full Test bắt buộc đủ 4 bài/40 câu trước khi tạo phiên.

Mỗi lựa chọn hoặc đánh dấu được lưu vào localStorage theo user/session ngay, rồi gửi batch sau 400 ms. Câu đang xem được ghi thời gian ước lượng khi cửa sổ đang hoạt động; batch được thử lại mỗi 5 giây và khi có mạng. `revision` và khóa PostgreSQL trên phiên ngăn tab cũ ghi đè lựa chọn mới. UI cho chọn bản thiết bị hoặc máy chủ khi có xung đột. Trước nộp, frontend dừng autosave và đợi request đang chạy; những lựa chọn còn lại được gửi cùng request nộp.

Backend khóa phiên, kiểm tra hạn và chấm trong cùng transaction. Nộp lại trả kết quả đã có. Sau nộp/hết hạn, các lần lưu mới không thay đổi điểm. Trình duyệt tự nộp khi đồng hồ về 0; nếu mất mạng hoặc đã đóng tab, backend chốt các đáp án nhận đúng hạn ở lần đọc/lưu/nộp/lịch sử/tiến độ tiếp theo. `submitted_at` của bài hết hạn vẫn là thời điểm deadline. Không có background worker trong MVP. Các lựa chọn offline chưa tới máy chủ trước deadline không được tính; bản trên thiết bị còn được hiển thị ở kết quả để người học nhận biết.

## Chấm điểm và quyền truy cập

`ReadingScoringService` so sánh trực tiếp lựa chọn với answer key bằng Python, **không gọi OpenAI**. Lưu riêng đúng/sai/bỏ trống; `accuracy = correct / total × 100`. Utility `practice_score()` tính `correct / total × 10`, không làm tròn theo quy đổi điểm kỳ thi. UI ghi rõ **điểm luyện tập tham khảo, không phải điểm VSTEP chính thức**.

Exam, passage, bank, generation và autosave API dùng serializer với danh sách trường cho phép; không trả `correct_answer`, `explanation_vi`, `option_explanations`, `evidence` hoặc `is_correct`. Answer DTO chỉ chứa lựa chọn của chính người học. Result chỉ mở cho chủ phiên sau khi nộp/hết hạn. Từ vựng cũng yêu cầu phiên của chính người học đã nộp và passage thuộc phiên đó. Đề trong bank được chia sẻ giữa tài khoản; phiên, đáp án, kết quả và analytics được giới hạn theo user.

## AI và từ vựng

`ReadingQuestionGeneratorService` gọi `LLMClient.generate_reading` qua OpenAI Responses Structured Outputs, cùng `OPENAI_API_KEY` / `OPENAI_MODEL` hiện có. Prompt `READING_GENERATOR_PROMPT_VERSION` hiện `2.0.0`. Pydantic kiểm tra số câu, số từ, đoạn có ID tuần tự, bốn phương án khác nhau, dạng câu hợp lệ, key A/B/C/D, cờ đúng/sai khớp key, câu không trùng và quote thực sự nằm trong đoạn. Adapter kiểm tra thêm test_profile, topic, số câu, band nội bộ, dạng đích và dạng câu bắt buộc của blueprint; đầu ra không hợp lệ được thử lại một lần. Fingerprint ngăn lưu passage trùng nội dung. Recent titles/topics được gửi để giảm lặp.

Prompt yêu cầu một đáp án tốt nhất, distractor hợp lý, không dùng kiến thức ngoài passage và phân hóa thực chất yêu cầu đọc trong cùng profile đa bậc. Kiểm tra xác định không bảo đảm mọi câu AI đều hết mơ hồ về ngữ nghĩa; không gọi thêm model chấm/kiểm định cho mỗi bài.

Sau nộp, người học chạm từ/bôi đen cụm từ hoặc nhập từ và chọn đoạn. `VocabularyService` chỉ gọi AI theo yêu cầu, trả nghĩa tiếng Việt, từ loại, nghĩa trong ngữ cảnh, ví dụ và từ gần nghĩa. Cache theo passage/paragraph/term/model/prompt version lưu trong PostgreSQL, dùng lại giữa người học. Khi không có key, giải thích đáp án mẫu vẫn đầy đủ; chức năng sinh đề/tra từ báo lỗi cấu hình rõ ràng. Không có provider giả hoặc kết quả AI giả lập.

## API và lưu trữ

Tất cả endpoint dưới `/api/v1/reading`, xác thực bằng JWT cookie hiện có.

| Method | Path | Nội dung |
| --- | --- | --- |
| GET | `/bank` | Metadata theo topic, số bài còn thiếu theo blueprint và trạng thái AI |
| POST | `/questions/generate` | Sinh và lưu một passage |
| GET | `/passages/{id}` | Passage/câu hỏi, không có answer key |
| POST | `/sessions` | Tạo phiên từ bank hoặc bổ sung đề thiếu |
| GET | `/sessions/{id}` | Đề, đáp án đã chọn, deadline |
| PATCH | `/sessions/{id}/answers` | Batch lưu đáp án và đánh dấu |
| PUT | `/sessions/{id}/answers/{question_id}` | Lưu một câu |
| POST | `/sessions/{id}/submit` | Chốt đáp án và chấm bằng Python |
| GET | `/results/{id}` | Điểm, review, giải thích từng option và evidence |
| GET | `/history` | Phân trang và lọc mode |
| GET | `/progress` | Thống kê theo mode/type/topic |
| POST | `/vocabulary/explain` | Giải thích từ vựng sau nộp |

Migration `5c96e8660369` nối sau Speaking `008c2258fea3`, thêm `reading_passages`, `reading_questions`, `reading_exam_sessions`, `reading_answers`, `reading_results`. Thứ tự passage/question lưu bằng JSONB ID trong session; câu hỏi và đáp án dùng bảng riêng với foreign key/unique constraint. Không đổi Compose project hoặc volumes cũ.

Frontend ở `frontend/src/features/reading`, routes `/reading`, `/reading/exam/[id]`, `/reading/result/[id]`, `/reading/history`, `/reading/progress`. Trang thi có hai khung cuộn riêng, navigator, keyboard A/B/C/D, đánh dấu xem lại, số câu chưa làm và hộp nộp. Mobile chuyển Bài đọc/Câu hỏi. Kết quả tô và cuộn tới paragraph bằng chứng; có lọc đúng/sai/bỏ trống.

## Analytics và phạm vi

Lịch sử lưu cả phiên đang làm để tiếp tục. Tiến độ chỉ tính bài đã chốt: điểm trung bình mỗi phiên, tổng đã trả lời, tỷ lệ đúng trên toàn bộ câu kể cả bỏ trống, thời gian phiên trung bình mỗi câu, biểu đồ điểm và breakdown type/topic. CTA chọn dạng có tỷ lệ thấp từ dữ liệu thực. Phản hồi từng bài nêu số đúng/tổng, câu bỏ trống và thời gian xem passage ước lượng; bài đúng toàn bộ không bị gán điểm yếu.

Reading dùng rate limit, logging và cấu hình chung. Mô hình hiện tại là một backend worker, truy vấn analytics trực tiếp; chưa thêm quota thương mại, queue, payment hoặc kỹ năng khác. Tác vụ AI vẫn đồng bộ; lỗi kết nối sau khi provider hoàn tất có thể phát sinh chi phí khi thử lại. Không dùng bài AI chưa duyệt làm đề thi có giá trị chứng nhận.

Theo yêu cầu, không thêm hoặc chạy unit/integration/E2E test suite. Việc đưa module vào ứng dụng dùng TypeScript compilation, Python import/OpenAPI, validation seed khi nạp, migration và Docker production build/startup. Chưa xác minh đầu ra AI bằng lời gọi trả phí hoặc thao tác trình duyệt.


## Refactor profile đa bậc

Request tạo đề/phiên nhận `test_profile` (mặc định `VSTEP_3_5`), topic, mode và dạng câu; không nhận `difficulty`. Frontend và backend đã đổi cùng lúc; request JSON cũ gửi trường difficulty bị từ chối do schema strict. API lấy bank bỏ query difficulty. Bộ chọn, badge đề, lịch sử và thống kê không còn nhãn CEFR cũ; các DTO công khai cũng không trả internal_difficulty_band.

Migration `c87e4a932b61` giữ cột difficulty cũ dưới tên ORM `legacy_difficulty`, thêm profile/band/blueprint version. Seed cập nhật riêng metadata cho tám bài gốc, không sửa answer key hoặc lịch sử. Đề AI legacy có band null vẫn dùng cho luyện riêng; cần metadata biên soạn hợp lệ trước khi tham gia Full Test mới. Phiên cũ tiếp tục với nội dung cũ; phiên mới dùng blueprint hiện hành. Bản mẫu có hai passage ở mỗi nhóm nội bộ, cho phép chọn bài chưa làm mà vẫn đủ cấu trúc.

Generator Full Test nhận tổng số passage/câu, progression, vị trí, yêu cầu văn bản, dạng câu bắt buộc và các passage đã chọn. Frontend bổ sung từng bài theo trạng thái bank, backend cũng tự hoàn thiện blueprint nếu được gọi trực tiếp. Điểm luyện tập, autosave, deadline và quyền xem answer key giữ nguyên.
