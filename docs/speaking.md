# Speaking MVP

Speaking mở rộng project hiện tại; giữ FastAPI, PostgreSQL, Next.js và toàn bộ luồng Writing. Điểm là ước tính để luyện tập, không phải điểm thi VSTEP chính thức.

## Sử dụng

Mở `/speaking`, chọn Thi thử, Part 1, Part 2, Part 3 hoặc Luyện nhanh. Đề mẫu B2 có sẵn không cần API key. Part 1/Luyện nhanh chọn một câu cho mỗi lượt; Full Test lấy hai topics với sáu câu Part 1, một tình huống ba phương án Part 2, một chủ đề Part 3 với ba ý gợi ý/ý riêng và hai follow-ups. AI có thể tạo 3–6 câu Part 1 và 2–3 follow-ups trong giới hạn schema.

Full Test hiển thị đồng hồ đã trôi qua với mốc khoảng 12 phút; đây là mốc luyện tập, không tự cắt bài ở phút 12. Mỗi câu chỉ nhận một bản ghi đã lưu; không có transcript, audio playback hay grading cho Full Test đang diễn ra. Backend chỉ trả các câu đã mở; mỗi follow-up được mở sau khi chốt bước trước. Bỏ qua được lưu rõ là `SKIPPED` và đưa vào đánh giá toàn bài.

Practice cho nghe lại, thu lại trước khi chuyển câu; Part 3 lưu bài nói chính và các follow-up trong cùng phiên. Nộp xong, giao diện xử lý từng audio rồi yêu cầu **một** grading tổng thể cho phiên. Route chấm một answer riêng cũng có sẵn cho trải nghiệm luyện tập khác; dashboard chỉ thống kê grading của phiên để không đếm hai lần.

Ghi âm cần HTTPS hoặc `localhost`, microphone và MediaRecorder. Trình duyệt tự chọn WebM/Opus, MP4 hoặc Ogg được hỗ trợ. TTS đọc câu hỏi tùy chọn; khi OpenAI TTS không có hoặc thất bại, dùng SpeechSynthesis. Tốc độ giọng đọc trình duyệt chỉnh tại `/settings`.

## Cấu hình máy chủ

```dotenv
OPENAI_API_KEY=
OPENAI_MODEL=gpt-5.6
OPENAI_TRANSCRIBE_MODEL=gpt-transcribe
OPENAI_SPEAKING_AUDIO_MODEL=
OPENAI_TTS_MODEL=
OPENAI_TTS_VOICE=alloy
AUDIO_STORAGE_DIR=data/audio
MAX_SPEAKING_AUDIO_MB=20
MAX_SPEAKING_AUDIO_SECONDS=360
PRONUNCIATION_CONFIDENCE_THRESHOLD=0.75
```

Model IDs phải được tài khoản OpenAI cấp quyền. `OPENAI_MODEL` cần Responses + Structured Outputs. Transcription model cần Audio Transcriptions với English và JSON. Audio analyzer cần Chat Completions hỗ trợ `input_audio` WAV và đầu ra text, chẳng hạn dòng `gpt-audio` nếu tài khoản có quyền. Không điền text-only model vào `OPENAI_SPEAKING_AUDIO_MODEL`. TTS model cần Audio Speech API. Không đặt key ở frontend.

`OPENAI_SPEAKING_AUDIO_MODEL` để trống nghĩa là chỉ có phản hồi ngôn ngữ; phát âm, độ trôi chảy và tổng điểm để `null`, mức tham khảo là chưa đủ dữ liệu. Trang kết quả có nút thử phân tích audio lại sau khi cấu hình được cập nhật. Thiếu key, sai model, timeout hoặc lỗi hạn mức được trả bằng lỗi tiếng Việt và giữ audio đã nộp.

Docker tự cài FFmpeg, migrate và nạp hai bộ seed Writing/Speaking. Chạy backend trực tiếp phải tự cài FFmpeg và chạy `python -m app.db.speaking_seed` sau `alembic upgrade head`. Docker dùng volume `speaking_audio` ở `/app/data/audio`; thiết lập này được cố định trong Compose để khớp mount. `AUDIO_STORAGE_DIR` dùng cho backend ngoài Docker. Giữ Compose project name `vstep-writing-lab` để tiếp tục dùng volume PostgreSQL cũ.

## Pipeline audio và chấm

1. MediaRecorder tạo Blob; IndexedDB giữ bản dự phòng theo user/session/sequence. Trong khi ghi, snapshot các chunk được lưu mỗi khoảng ba giây; khi dừng, lưu Blob hoàn chỉnh. Chỉ xóa sau khi server xác nhận upload. Nếu browser không cho IndexedDB, vẫn giữ Blob trong bộ nhớ và thông báo không đóng trang. Khôi phục phiên giữa lúc ghi phụ thuộc định dạng/container của trình duyệt; bản ghi đã dừng được giữ để retry upload.
2. Next proxy chuyển multipart bằng bytes, giới hạn body 25 MiB kể cả luồng đọc và bảo toàn content type. FastAPI yêu cầu Content-Length cho audio, chặn theo giới hạn cấu hình; storage đọc giới hạn số bytes và kiểm tra MIME. Tên tệp client không dùng làm đường dẫn.
3. `AudioStorageService` cung cấp `store/resolve/remove`. Local adapter tạo UUID, FFmpeg giải mã audio thật về WAV mono 16 kHz, đo thời lượng từ số mẫu thay vì tin client. WAV này giữ toàn bộ nội dung âm thanh để nghe lại/STT/analyze; upload gốc tạm thời được xóa. Muốn thay bằng S3/MinIO/R2 có thể viết adapter cùng hợp đồng và materialize WAV vào staging khi speech provider cần file.
4. `SpeechTranscriptionService` gọi `SpeechClient.transcribe`; adapter OpenAI dùng Audio Transcriptions. Transcript là dữ liệu nhận dạng, không được user sửa để thay thế phần nói. Không giả timestamp từ JSON transcription.
5. `SpeechClient.analyze_audio` gửi **WAV thật** qua `input_audio`. Phản hồi acoustic là dữ liệu trung gian, không gửi cho frontend. Audio model không bắt buộc hỗ trợ JSON Schema. Model text nhận transcript, evidence audio, đề, metrics và trả grading qua Responses Structured Outputs, validate bằng Pydantic. Không parse JSON bằng regex và không tạo điểm mẫu.
6. `SpeakingCorrectionService` áp ngưỡng confidence, loại diagnostic thiếu evidence và IPA chưa đủ confidence. Backend tính `overall = (grammar + vocabulary + pronunciation + fluency + structures) / 5` nếu cả năm tiêu chí có điểm. Thiếu acoustic evidence cho bất kỳ recording được nộp thì không cho tổng điểm. Full Test được chấm holistically từ **mọi** answer/follow-up, không tự đặt trọng số Part.
7. Kết quả lưu feedback/điểm/correction/errors/model/prompt version; frontend hiện ba ưu tiên rồi mới phân tích chi tiết. Mỗi audio có play/pause/seek; transcript và chữa câu liên kết qua sequence. Bản sửa giữ ý gốc; bản B2 dùng spoken English, không biến thành essay.

Mức tham khảo dùng khoảng nửa điểm theo yêu cầu sản phẩm: 0–3.5 Chưa xét, 4–5.5 B1, 6–8 B2, 8.5–10 C1. Với trung bình không nằm đúng nửa điểm (ví dụ 5.8), chỉ làm tròn tới nửa điểm để tra mức; điểm trung bình gốc giữ nguyên. UI hiển thị một chữ số thập phân. Đây là mapping luyện tập, không quy tắc cấp chứng chỉ.

Pause count ước lượng năng lượng ở cửa sổ 20 ms: khoảng lặng ≥0.3s, khoảng dài ≥1.2s, bỏ silence trước/sau đoạn có năng lượng. Số từ/phút dùng tổng thời gian recording. Filler rõ (`uh/um/erm`), filler có thể đúng ngữ cảnh (`well/actually/like/you know/I mean`) và lặp từ liên tiếp được phân biệt. Metrics có thể bị nhiễu/nhận dạng thiếu, không dùng ngưỡng WPM để kết luận B2.

## API

Tất cả dưới `/api/v1/speaking`, bắt buộc cookie xác thực. Audio chỉ thuộc người sở hữu session. Không mount thư mục audio thành static public, không trả đường dẫn filesystem.

| Method | Path | Nội dung |
| --- | --- | --- |
| GET | `/config` | Khả năng AI/TTS và giới hạn, không có secrets |
| POST | `/questions/generate` | Đề mẫu hoặc AI, nhận part/source/topic/difficulty/recent history |
| POST | `/sessions` | Tạo phiên đủ câu hỏi |
| GET | `/sessions/{id}` | Tiến độ, câu hiện tại và câu đã mở |
| POST | `/sessions/{id}/answers` | Mở answer theo `sequence_number` |
| POST | `/answers/{id}/audio` | Multipart field `file`; retry cùng hash idempotent |
| GET | `/answers/{id}/audio` | WAV riêng tư, hỗ trợ Range; khóa khi Full Test đang thi |
| POST | `/answers/{id}/transcribe` | Lưu transcript/metrics; có cache |
| POST | `/answers/{id}/analyze?retry=true` | Phân tích audio hoặc thử lại nếu trước đó thất bại |
| POST | `/answers/{id}/grade` | Chấm riêng câu; không mở khi Full Test đang thi |
| POST | `/sessions/{id}/next` | Chốt câu, mở bước tiếp; `{sequence_number, skip}` |
| POST | `/sessions/{id}/complete` | Nộp sau khi đi hết các bước |
| POST | `/sessions/{id}/grade` | Một đánh giá tổng thể, lưu cache |
| POST | `/sessions/{id}/tts` | Đọc câu hiện tại, không nhận text tùy ý từ client |
| GET | `/results/{id}` | Kết quả theo session ID |
| GET | `/history` | `mode`, `offset`, `limit` |
| GET | `/progress` | `mode` tùy chọn; averages, timeline, weaknesses |

## Lưu trữ, đồng thời và giới hạn

Migration `008c2258fea3` thêm `speaking_questions`, `speaking_exam_sessions`, `speaking_answers`, `speaking_gradings`, `speaking_errors`. Không sửa bảng Writing. Audio hash, transcript hash, model và prompt versions tạo cache keys trong cùng tài khoản. Row locks chống đổi recording khi đang chấm; advisory locks tránh transcribe/analyze/grade lặp cùng nội dung. Thu lại ở Practice xóa kết quả cũ của answer. Next/start/complete có xử lý lặp request an toàn.

Grading đồng bộ có timeout; kết quả từng bước được lưu để retry. Nếu provider xử lý xong nhưng server mất kết nối trước khi lưu DB, retry vẫn có thể phát sinh phí. TTS cache theo model/voice/text; không là điều kiện của core flow. Snapshot IndexedDB là bản dự phòng trên thiết bị, không đồng bộ sang thiết bị khác. Dữ liệu thật chỉ bền sau upload; backup cần cả PostgreSQL **và** volume audio. Không chạy `docker compose down -v` nếu cần giữ dữ liệu.

Nguồn API dùng khi triển khai: [OpenAI speech-to-text](https://developers.openai.com/api/docs/guides/speech-to-text), [audio guide](https://developers.openai.com/api/docs/guides/audio), [gpt-audio capabilities](https://developers.openai.com/api/docs/models/gpt-audio). Quyền model và chi phí phụ thuộc tài khoản.
