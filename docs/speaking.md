# Speaking MVP

Speaking mở rộng project hiện tại; giữ FastAPI, PostgreSQL, Next.js và toàn bộ luồng Writing. Điểm là ước tính để luyện tập, không phải điểm thi VSTEP chính thức.

## Sử dụng

Mở `/speaking`, chọn Thi thử, Part 1, Part 2, Part 3 hoặc Luyện nhanh. Đề mẫu VSTEP.3–5 có sẵn không cần API key. Part 1/Luyện nhanh chọn một câu cho mỗi lượt; Full Test lấy hai topics với sáu câu Part 1, một tình huống ba phương án Part 2, một chủ đề Part 3 với ba ý gợi ý/ý riêng và hai follow-ups. AI có thể tạo 3–6 câu Part 1 và 2–3 follow-ups trong giới hạn schema.

Full Test hiển thị đồng hồ đã trôi qua với mốc khoảng 12 phút; đây là mốc luyện tập, không tự cắt bài ở phút 12. Mỗi câu chỉ nhận một bản ghi đã lưu; không có transcript, audio playback hay grading cho Full Test đang diễn ra. Backend chỉ trả các câu đã mở; mỗi follow-up được mở sau khi chốt bước trước. Bỏ qua được lưu rõ là `SKIPPED` và đưa vào đánh giá toàn bài.

Practice cho nghe lại, thu lại trước khi chuyển câu; Part 3 lưu bài nói chính và các follow-up trong cùng phiên. Nộp xong, giao diện xử lý từng audio rồi yêu cầu **một** grading tổng thể cho phiên. Route chấm một answer riêng cũng có sẵn cho trải nghiệm luyện tập khác; dashboard chỉ thống kê grading của phiên để không đếm hai lần.

Ghi âm cần HTTPS hoặc `localhost`, microphone và MediaRecorder. Trình duyệt tự chọn WebM/Opus, MP4 hoặc Ogg được hỗ trợ. TTS đọc câu hỏi tùy chọn; khi OpenAI TTS không có hoặc thất bại, dùng SpeechSynthesis. Tốc độ giọng đọc trình duyệt chỉnh tại `/settings`.

## Cấu hình máy chủ

```dotenv
OPENAI_API_KEY=
OPENAI_MODEL=gpt-5.6
OPENAI_TRANSCRIBE_MODEL=gpt-4o-transcribe
OPENAI_AUDIO_MODEL=gpt-audio
AUDIO_ANALYSIS_ENABLED=true
OPENAI_TTS_MODEL=gpt-4o-mini-tts
OPENAI_TTS_VOICE=alloy
AUDIO_STORAGE_DIR=data/audio
SPEAKING_AUDIO_MAX_MB=20
SPEAKING_AUDIO_MAX_SECONDS=360
AUDIO_FEEDBACK_MIN_CONFIDENCE=0.70
```

Model IDs phải được tài khoản OpenAI cấp quyền. `OPENAI_MODEL` cần Responses + Structured Outputs. Transcription model cần Audio Transcriptions với English và JSON. Audio analyzer cần Chat Completions hỗ trợ `input_audio` WAV và đầu ra text, chẳng hạn dòng `gpt-audio` nếu tài khoản có quyền. Không điền text-only model vào `OPENAI_AUDIO_MODEL`. TTS model cần Audio Speech API. Không đặt key ở frontend.

`OPENAI_AUDIO_MODEL` để trống nghĩa là chỉ có phản hồi ngôn ngữ; phát âm, độ trôi chảy và tổng điểm để `null`, mức tham khảo là chưa đủ dữ liệu. Trang kết quả có nút thử phân tích audio lại sau khi cấu hình được cập nhật. Thiếu key, sai model, timeout hoặc lỗi hạn mức được trả bằng lỗi tiếng Việt và giữ audio đã nộp.

Docker tự cài FFmpeg, migrate và nạp hai bộ seed Writing/Speaking. Chạy backend trực tiếp phải tự cài FFmpeg và chạy `python -m app.db.speaking_seed` sau `alembic upgrade head`. Docker dùng volume `speaking_audio` ở `/app/data/audio`; thiết lập này được cố định trong Compose để khớp mount. `AUDIO_STORAGE_DIR` dùng cho backend ngoài Docker. Giữ Compose project name `vstep-writing-lab` để tiếp tục dùng volume PostgreSQL cũ.

## Pipeline audio và chấm

1. MediaRecorder tạo Blob; IndexedDB giữ bản dự phòng theo user/session/sequence. Trong khi ghi, snapshot các chunk được lưu mỗi khoảng ba giây; khi dừng, lưu Blob hoàn chỉnh. Chỉ xóa sau khi server xác nhận upload. Nếu browser không cho IndexedDB, vẫn giữ Blob trong bộ nhớ và thông báo không đóng trang. Khôi phục phiên giữa lúc ghi phụ thuộc định dạng/container của trình duyệt; bản ghi đã dừng được giữ để retry upload.
2. Next proxy chuyển multipart bằng bytes, giới hạn body 25 MiB kể cả luồng đọc và bảo toàn content type. FastAPI yêu cầu Content-Length cho audio, chặn theo giới hạn cấu hình; storage đọc giới hạn số bytes và kiểm tra MIME. Tên tệp client không dùng làm đường dẫn.
3. `AudioStorageService` cung cấp `store/resolve/remove`. Local adapter tạo UUID, FFmpeg giải mã audio thật về WAV mono 16 kHz, đo thời lượng từ số mẫu thay vì tin client. WAV này giữ toàn bộ nội dung âm thanh để nghe lại/STT/analyze; upload gốc tạm thời được xóa. Muốn thay bằng S3/MinIO/R2 có thể viết adapter cùng hợp đồng và materialize WAV vào staging khi speech provider cần file.
4. `SpeechTranscriptionService` gọi `SpeechClient.transcribe`; adapter OpenAI dùng Audio Transcriptions. Transcript là dữ liệu nhận dạng, không được user sửa để thay thế phần nói. Không giả timestamp từ JSON transcription.
5. `AudioAnalysisProvider` tách khỏi transcription/TTS. `OpenAIAudioAnalysisProvider` gửi **WAV thật** qua `input_audio` cho model audio. Model trả function call `record_audio_assessment`, adapter kiểm tra bằng Pydantic và thử lại một lần nếu cấu trúc sai. Dòng `gpt-audio` hỗ trợ function calling nhưng không hỗ trợ Structured Outputs `json_schema`; không có lời gọi text-model để đoán/chuẩn hóa điểm audio. Kết quả chuẩn hóa gồm pronunciation, intelligibility, clarity, stress, intonation, rhythm, fluency và nhận xét tiếng Việt. Target phải xuất hiện trong lời mà audio model nghe được; chỉ giữ issue đủ confidence, không dựng IPA/phoneme/timestamp.
6. Text model chỉ nhận câu hỏi/transcript/trạng thái trả lời, chấm Grammar, Vocabulary, Structures bằng schema riêng; không nhận hoặc tự đặt điểm phát âm. `SpeakingCorrectionService` lấy acoustic scores từ kết quả audio đã kiểm tra, trung bình các recording và làm tròn đến nửa điểm. Đây là phép tổng hợp cho luyện tập, không phải trọng số Part chính thức. Mỗi recording đã nộp phải có điểm audio đáng tin cậy để cho điểm tiêu chí tổng hợp; thiếu dữ liệu thì `null`. Overall là trung bình năm tiêu chí 20%. Phần ngôn ngữ Full Test vẫn được chấm holistically trên tất cả answer/follow-up. Lỗi acoustic trong analytics chỉ được tạo từ issue audio.
7. Kết quả lưu feedback/điểm/correction/errors/model/prompt version; frontend hiện ba ưu tiên rồi mới phân tích chi tiết. Mỗi audio có play/pause/seek; transcript và chữa câu liên kết qua sequence. Bản sửa giữ ý gốc; bản B2 dùng spoken English, không biến thành essay.

Mức tham khảo dùng khoảng nửa điểm theo yêu cầu sản phẩm: 0–3.5 Chưa xét, 4–5.5 B1, 6–8 B2, 8.5–10 C1. Với trung bình không nằm đúng nửa điểm (ví dụ 5.8), chỉ làm tròn tới nửa điểm để tra mức; điểm trung bình gốc giữ nguyên. UI hiển thị một chữ số thập phân. Đây là mapping luyện tập, không quy tắc cấp chứng chỉ.

Pause count ước lượng năng lượng ở cửa sổ 20 ms: khoảng lặng ≥0.3s, khoảng dài ≥1.2s, bỏ silence trước/sau đoạn có năng lượng. Số từ/phút dùng tổng thời gian recording. Filler rõ (`uh/um/erm`), filler có thể đúng ngữ cảnh (`well/actually/like/you know/I mean`) và lặp từ liên tiếp được phân biệt. Metrics có thể bị nhiễu/nhận dạng thiếu, không dùng ngưỡng WPM để kết luận B2.

## API

Tất cả dưới `/api/v1/speaking`, bắt buộc cookie xác thực. Audio chỉ thuộc người sở hữu session. Không mount thư mục audio thành static public, không trả đường dẫn filesystem.

| Method | Path | Nội dung |
| --- | --- | --- |
| GET | `/config` | Khả năng AI/TTS và giới hạn, không có secrets |
| POST | `/questions/generate` | Đề mẫu hoặc AI, nhận part/source/topic/test_profile/recent history |
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


Tạo đề và phiên Speaking dùng `test_profile=VSTEP_3_5`, không nhận difficulty B1/B2/C1. Cùng prompt có thể đánh giá các bậc năng lực khác nhau thông qua chất lượng câu trả lời; mức AI ước tính vẫn hiện sau chấm. Nhãn difficulty cũ được giữ riêng trong DB để bảo toàn dữ liệu, không hiển thị ở đề hoặc lịch sử.


## Pronunciation coach

Trang `/speaking/pronunciation` nhận từ/câu tham chiếu (tối đa 500 ký tự), có thể liên kết từ lỗi trong bài Speaking. Người học nghe mẫu AI OpenAI TTS, ghi âm, nghe lại và phân tích. Một lượt đã upload là bất biến; luyện lại tạo lượt mới và không ghi đè lịch sử. Bản ghi tạm có IndexedDB backup, URL chứa ID lượt luyện để mở lại; lỗi API vẫn giữ audio đã tải lên. Audio model so sánh bản ghi thật với reference, trả `heard_text`, mức phủ nội dung, phản hồi trọng âm, vấn đề chính, cách luyện và độ tin cậy. Không có điểm nếu thiếu nội dung tham chiếu; từ đơn có thể chưa đủ để chấm fluency/intonation.

TTS cache chung theo text + voice + model, khóa PostgreSQL chống tạo trùng và ghi tệp nguyên tử. Giọng mẫu được ghi rõ là AI. Coach cần OpenAI TTS, không thay mẫu bằng giả lập. SpeechSynthesis vẫn là phương án dự phòng cho **đọc câu hỏi** trong bài thi.

Các route mới, dưới `/api/v1/speaking/pronunciation`, đều xác thực và kiểm tra quyền sở hữu:

| Method | Path | Nội dung |
| --- | --- | --- |
| POST | `/practices` | Tạo lượt với reference_text, optional source_answer_id/source_issue_type, client_request_id chống lặp |
| GET | `/practices/{id}` | Nội dung, kết quả, ngày luyện và URL audio riêng tư |
| POST / GET | `/practices/{id}/audio` | Lưu / nghe lại WAV |
| POST | `/practices/{id}/tts` | Mẫu OpenAI TTS có cache |
| POST | `/practices/{id}/analyze` | Chấm bản ghi thật, có cache theo user/audio/reference/model/version/confidence |
| GET | `/history` | reference_hash tùy chọn, offset/limit |
| GET | `/progress` | Timeline phát âm/trôi chảy, vấn đề lặp lại, từ khó và từ tiến bộ |

`pronunciation_practices` được thêm bởi migration `e41b6d0a9f22`. UI History/Progress tích hợp các lượt này. Tiến bộ so sánh lần đầu và lần gần nhất **cùng reference**; điểm dưới 7 được gợi ý luyện tiếp, không phải kết luận rớt VSTEP. Confidence là tự đánh giá của model, chưa được hiệu chuẩn thành xác suất chính xác. Scores cũng là ước tính luyện tập; cần dữ liệu audio có người chấm để đánh giá chất lượng thực tế.

Tham khảo triển khai TTS: [OpenAI Text to Speech](https://developers.openai.com/api/docs/guides/text-to-speech).
