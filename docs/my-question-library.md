# Đề của tôi / My Question Library

Mở **Đề của tôi** ở thanh điều hướng, hoặc `/my-questions`. Thư viện thuộc từng tài khoản. Đề nhập vào đây không được đưa vào ngân hàng đề AI dùng chung.

## Thêm đề

- **Dán văn bản**: dán nguyên văn đề, các lựa chọn và đáp án nếu có; bấm **Phân tích đề**. AI chỉ trích xuất và phân loại, không giải bài. Các gợi ý nhận diện từ số từ, nhãn Speaking Part và bài đọc có MCQ chỉ là heuristic, không thay thế phân loại AI hoặc quyết định của người dùng.
- **Ảnh/PDF**: tải JPG/JPEG/PNG/WEBP hoặc PDF (20 MB; PDF tối đa 20 trang; ảnh tĩnh tối đa 25 megapixel). Tệp có mật khẩu, hỏng hoặc giả phần mở rộng bị từ chối. OpenAI đọc trực tiếp ảnh/PDF; không chỉ dựa vào OCR. Tệp nguồn lưu riêng để đối chiếu, hạn mức 500 MB/tài khoản.
- **Nhập thủ công**: chọn kỹ năng/phần thi; biểu mẫu thay đổi theo Writing, Speaking hoặc Reading. Có thể lưu bản nháp thiếu nội dung, nhưng cần bổ sung đủ đề và lựa chọn trước khi luyện. Reading không cần sẵn đáp án.

Luôn có bản xem trước và biểu mẫu sửa trước khi lưu. Chọn những mục cần nhập. Có thể gộp Task 1+2, Speaking Part 1+2+3 hoặc các bài Reading cùng kỹ năng. Mỗi đề Reading có tối đa 4 bài đọc/40 câu; một bài 7 hoặc 8 câu vẫn dùng được. **Full Reading** yêu cầu 4 bài/40 câu; 2–4 bài ngắn hơn dùng **Reading mini**.

Đối chiếu cảnh báo và độ tin cậy trước khi bấm lưu. Không có thao tác tự lưu kết quả AI. Đề trùng nội dung hiện liên kết tới bản đã có và nút **Vẫn lưu thêm bản mới**.

Trong biểu mẫu có thể chọn tệp nguồn cần hiển thị khi luyện, chẳng hạn hình hoặc sơ đồ. Tệp chứa đáp án nên chỉ giữ trong thư viện. Ảnh đã chọn được hiển thị trong màn hình luyện; PDF mở dưới dạng tải tệp. Tệp không được công khai hoặc tải từ URL bên ngoài tự động.

## Chỉnh sửa, tổ chức và luyện

Tìm theo tên/nguồn/ghi chú, kỹ năng, phần thi, chủ đề, tag, bộ sưu tập, yêu thích, đã luyện/chưa luyện và thời gian tạo. Mỗi thẻ có số lượt luyện, lần gần nhất, điểm gần nhất và tốt nhất. Bấm vào đề để xem, sửa, đặt đáp án, nhân bản hoặc xóa. Có thể tạo bộ sưu tập và chuyển đề vào đó trong biểu mẫu.

**Luyện đề này** mở chính engine của kỹ năng:

- Writing: nguyên instruction, thư/tình huống, các yêu cầu và số từ; cùng autosave, timer, phân tích, hiệu chỉnh điểm, phản hồi, chữa bài và Vocabulary Coach.
- Speaking: cùng chuỗi câu, thời gian chuẩn bị, ghi âm, tải âm thanh, phiên âm và chấm. Pronunciation/fluency dựa trên pipeline âm thanh hiện có, không suy từ transcript. Part 1 hỗ trợ nhiều chủ đề; Part 2 giữ ba lựa chọn và ngữ cảnh; Part 3 giữ sơ đồ ý và follow-up.
- Reading: cùng bố cục bài đọc/câu hỏi, navigator, đánh dấu, chọn đáp án, timer, nộp và xem lại. Vocabulary Coach dùng các bài đọc trong chính phiên đã nộp.

Các kết quả đi vào lịch sử và tiến độ hiện có. Chúng được gắn nhãn **Đề của tôi**. Nút **Luyện lại đúng đề này** trên trang kết quả sử dụng phiên bản của lượt cũ.

## Đáp án Reading

Mỗi câu lưu `correct_answer` có thể null và `answer_key_source`:

| Giá trị | Ý nghĩa | Tính điểm |
| --- | --- | --- |
| `provided` | Trích từ đáp án có trong nguồn | Có |
| `user_confirmed` | Người dùng tự đặt hoặc xác nhận | Có |
| `ai_suggested` | Giá trị đề xuất chưa xác nhận | Không |
| `unknown` | Chưa có đáp án | Không |

Chức năng này **không tự giải hoặc đề xuất đáp án bằng AI**. Khi trích đáp án, parser phải chỉ ra mẩu nguồn có số câu và chữ đáp án; văn bản được kiểm tra lại với nguồn đã dán. Các nội dung câu hỏi không khớp nguyên văn nguồn cũng bị để trống kèm cảnh báo. Với ảnh/PDF, chủ sở hữu cần đối chiếu bản xem trước với tệp gốc, nhất là ảnh mờ.

Trong **Sửa đề / đặt đáp án**, chọn A–D từng câu hoặc dán `1A 2C 3B` (cũng nhận từng dòng). Số trong công cụ này là thứ tự từ 1 đến tổng số câu trong đề. Xem trước, xác nhận áp dụng, rồi **Lưu đề**. Số câu gốc vẫn giữ trong bản thư viện; engine đánh số navigator theo thứ tự liên tục và trả thêm `source_question_number` để đối chiếu.

Khi thiếu đáp án, toàn bài có `score=null`, `accuracy=null`. `scorable_count` đếm câu có đáp án tin cậy; `unscored_count` đếm phần còn lại. Chọn đáp án ở câu chưa có key không bị tính sai hoặc tính là bỏ trống. Breakdown/tiến độ chỉ dùng câu có key trong mẫu số và ghi rõ phạm vi; điểm trung bình chỉ dùng những phiên có đủ key. Không tạo điểm 0 giả hoặc suy diễn điểm toàn bài từ một phần có đáp án.

Giải thích từ nguồn/ghi chú được phân biệt với giải thích AI của ngân hàng đề. Câu không có giải thích hoặc bằng chứng vẫn xem lại được. Không tự tạo lời giải rồi trình bày như nội dung nguồn.

## Dữ liệu và phiên bản

`library_questions` là mục thư viện riêng với metadata và JSONB theo kỹ năng. `library_revisions` giữ document bất biến cho mỗi lần lưu. Khi bắt đầu luyện, `LibraryPracticeService` chuyển phiên bản thành snapshot trong các bảng hiện có `writing_questions`, `speaking_questions`, `reading_passages`/`reading_questions`, rồi gọi các ExamService hiện có. Không có grader riêng cho đề nhập.

Các snapshot có `owner_id`, `library_question_id`, `library_revision`, `library_title` và presentation metadata. Tất cả truy vấn ngân hàng/gợi ý cho AI chỉ lấy `owner_id IS NULL`. Đọc câu hỏi riêng qua ID cũng kiểm tra chủ sở hữu. Các phiên và vocabulary vẫn dùng cơ chế xác thực/quyền sở hữu cũ.

Sửa nội dung hoặc đáp án tạo phiên bản mới; câu hỏi và kết quả cũ không bị sửa. Xóa thư viện là soft-delete: lịch sử và khả năng luyện lại phiên bản từ lịch sử được giữ. PUT yêu cầu `expected_revision` để tránh ghi đè giữa các tab. Favorite/tag/collection có thể PATCH riêng, không đổi phiên bản đề.

Migration `ab812d97c641` bổ sung thư viện, snapshot metadata và nullable Reading keys/results; backfill số câu chấm được của kết quả cũ. `bcdf7614289e` giữ tương thích việc dọn tài khoản. Không xóa bảng hoặc dữ liệu hiện có. Cấu trúc/quality gate nghiêm ngặt của đề AI giữ nguyên; đề người dùng nhập dùng validator phù hợp, không bị ép vào word range hay mẫu ba bullet của generator.

## API và JSON schema

Prefix: `/api/v1/my-questions`; tất cả route yêu cầu đăng nhập.

| Method/path | Chức năng |
| --- | --- |
| `GET /` | Lọc và phân trang (`skill`, `part`, `search`, `topic`, `tag`, `favorite`, `practiced`, `collection_id`, `order`, `offset`, `limit`) |
| `POST /` | `{document, save_duplicate?}` |
| `GET /{id}` | Document, revision, stats, tình trạng đáp án và nội dung còn thiếu |
| `PUT /{id}` | `{document, expected_revision, save_duplicate?}` |
| `PATCH /{id}` | Favorite, tags, collection_id |
| `DELETE /{id}` | Soft-delete |
| `POST /{id}/duplicate` | Bản sao riêng |
| `POST /{id}/practice` | `{revision?, timed?}` → `{id, skill, url, library_*}` |
| `GET/POST /collections` | Danh sách/tạo bộ sưu tập |
| `POST /assets` | Multipart `file` → metadata tệp riêng |
| `GET /assets/{id}` | Đọc tệp của chính tài khoản |
| `POST /parse` | `{text}` hoặc `{asset_id}` → `{items: [{document, confidence, warnings}], warnings}`; chưa lưu đề |

Schema nguồn: `backend/app/schemas/library.py`. Schema máy đọc được: [library-document.schema.json](library-document.schema.json) và [library-import.schema.json](library-import.schema.json). Payload mẫu tối giản:

```json
{
  "document": {
    "title": "Visit to London",
    "skill": "writing",
    "part": "task_1",
    "source_type": "copied_text",
    "content": {
      "writing": [{
        "task_type": 1,
        "instruction": "Write an email responding to Aldora.",
        "stimulus_type": "email",
        "stimulus_text": "Dear Alex, ...",
        "requirements": ["Say how long you will stay."],
        "minimum_words": 120
      }]
    }
  }
}
```

`content` có `writing[]`, `speaking[]`, `reading[]` và tùy chọn `practice_asset_ids[]`. Một document chỉ chứa một kỹ năng. Metadata `source_url` hiện chỉ dùng để tham khảo, tạo chỗ nối cho URL import sau này; không triển khai scraping, chia sẻ công khai, marketplace hay lớp học.

Tệp nằm trong `QUESTION_IMPORT_STORAGE_DIR` (mặc định `data/question_imports`), Docker dùng volume `question_imports`. OpenAI adapter dùng Responses structured outputs, ảnh `input_image`, PDF `input_file` dạng inline base64, `store=false`; không tạo file tồn đọng trên OpenAI Files API. Tham chiếu: [OpenAI file inputs](https://developers.openai.com/api/docs/guides/file-inputs), [Images and vision](https://developers.openai.com/api/docs/guides/images-vision).

## Kiểm tra trong quá trình phát triển

`backend/tests/test_library.py` kiểm tra quyền riêng tư giữa hai tài khoản, file MIME/nội dung/quyền truy cập, parser không tự lưu, Reading 7 câu không key, key chưa xác nhận, full 4/40, phiên bản/retry/soft-delete, nguyên văn Writing, full Speaking và tổ chức thư viện. Các tài khoản thử được dọn sau khi chạy. `backend/scripts/check_library_live.py` chạy thêm luồng Writing với OpenAI thật, bao gồm grader và Vocabulary Coach; cần API key và phát sinh sử dụng API.

Các smoke check bổ sung (chạy có chủ đích, OpenAI thật có tính phí):

- `check_library_files_live.py`: ảnh → Speaking Part 2 → sửa → audio upload/phiên âm/chấm phát âm → Vocabulary Coach; thêm PDF trực tiếp. Dùng âm thanh tổng hợp để kiểm tra pipeline, không kiểm tra microphone trình duyệt.
- `check_library_reading_live.py`: văn bản 10 câu có đáp án; 7 câu thiếu đáp án rồi tự xác nhận key; full 4 bài/40 câu. Kiểm tra parser và điểm qua engine thật.
- `check_library_http.py`: chạy trong backend container để kiểm tra đăng nhập và CRUD qua Next proxy, upload/download qua volume thật và DELETE forwarding. Không gọi AI.

Đã chạy thành công các smoke check AI trên trong quá trình triển khai ngày 18/09/2026. Giao diện đã qua TypeScript và production build; chưa kiểm tra thao tác bằng trình duyệt/microphone thực vì phiên công cụ không có trình duyệt kết nối.
