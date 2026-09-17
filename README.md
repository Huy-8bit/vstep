# VSTEP Practice Platform

Ứng dụng luyện VSTEP Writing, Speaking và Reading dành cho người Việt. Reading có thi thử 4 bài đọc/40 câu/60 phút, luyện passage/dạng câu/chủ đề, chấm điểm ngay, giải thích từng phương án và bằng chứng trong bài. Speaking gồm thi thử ba phần, luyện từng Part, ghi âm, nhận dạng giọng nói, chữa từng câu và theo dõi tiến độ. Writing gồm: thi thử hai Task, luyện riêng thư/email hoặc bài luận, lưu nháp, chấm và chữa bài bằng AI, lịch sử và biểu đồ tiến độ. Toàn bộ giao diện và giải thích bằng tiếng Việt; đề và bài viết bằng tiếng Anh.

## Chạy bằng Docker

Yêu cầu Docker với Compose v2. Từ thư mục gốc:

```sh
cp .env.example .env
docker compose up --build
```

- Website: http://localhost:3000
- Backend: http://localhost:8000
- Swagger: http://localhost:8000/docs

Backend tự chạy Alembic và nạp **10 đề Task 1 + 10 đề Task 2 + 45 đề Speaking (15 mỗi Part) + 8 bài Reading (80 câu)** khi khởi động. Seed có thể chạy lại an toàn. PostgreSQL lưu dữ liệu trong volume `postgres_data`; audio Speaking nằm trong volume `speaking_audio`. `docker compose down` giữ dữ liệu; không dùng `down -v` nếu cần giữ bài viết.

Không cần OpenAI key để đăng ký, lấy đề mẫu, làm và lưu/nộp bài, ghi âm và nghe lại trong Practice. Chấm AI và sinh đề AI yêu cầu key thật; khi thiếu key, ứng dụng báo **“Chưa cấu hình OpenAI API.”** và giữ bài đã nộp. Reading chấm đúng/sai bằng Python từ đáp án có sẵn và không cần gọi AI khi nộp. Không có điểm giả lập trong ứng dụng.

## Cấu hình

| Biến | Ý nghĩa |
| --- | --- |
| `APP_ENV` | `development` hoặc `production`; production bật Secure cookie |
| `DATABASE_URL` | URL SQLAlchemy `postgresql+asyncpg://...` cho chạy backend ngoài Docker |
| `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` | Thông tin DB dùng trong Docker Compose |
| `OPENAI_API_KEY` | Key chỉ đọc ở backend; để trống nếu chỉ dùng đề mẫu |
| `OPENAI_MODEL` | Model hỗ trợ Responses API + Structured Outputs; ví dụ cấu hình `gpt-5.6` |
| `OPENAI_TRANSCRIBE_MODEL` | Audio Transcriptions, mặc định `gpt-transcribe`; tùy quyền tài khoản |
| `OPENAI_SPEAKING_AUDIO_MODEL` | Model nhận audio WAV qua Chat Completions; để trống thì chưa chấm phát âm/fluency/tổng điểm |
| `OPENAI_TTS_MODEL`, `OPENAI_TTS_VOICE` | Đọc câu hỏi tùy chọn; bỏ trống model để dùng giọng trình duyệt |
| `AUDIO_STORAGE_DIR` | Backend ngoài Docker: `data/audio`; Docker mount `/app/data/audio` |
| `MAX_SPEAKING_AUDIO_MB`, `MAX_SPEAKING_AUDIO_SECONDS` | Mặc định 20 MB và 360 giây mỗi bản ghi |
| `PRONUNCIATION_CONFIDENCE_THRESHOLD` | Mặc định 0.75; IPA chỉ khi confidence ≥0.9 |
| `JWT_SECRET` | Secret ký JWT; thay giá trị phát triển trước khi triển khai production |
| `JWT_ACCESS_EXPIRE_MINUTES` | Mặc định 15 phút |
| `JWT_REFRESH_EXPIRE_DAYS` | Mặc định 7 ngày |
| `FRONTEND_URL` | Origin frontend, mặc định `http://localhost:3000` |
| `BACKEND_INTERNAL_URL` | URL nội bộ cho Next.js proxy; Docker đặt thành `http://backend:8000` |

Trong Compose, `DATABASE_URL` được tạo từ ba biến `POSTGRES_*` để trỏ đúng service `postgres`; URL `localhost` trong `.env` dành cho chạy backend trực tiếp. Nếu password chứa ký tự đặc biệt trong URL, cần URL-encode khi tự cấu hình.

Đặt `OPENAI_API_KEY` và đổi `OPENAI_MODEL` nếu model mẫu không được cấp cho tài khoản của bạn. Sau khi sửa `.env`, chạy `docker compose up -d --force-recreate backend`. API key không có tiền tố `NEXT_PUBLIC_` và không được đưa vào frontend. Bài viết và audio/transcript đã nộp được gửi đến OpenAI để xử lý; Responses request dùng `store=False`. Xem [cấu hình và luồng Speaking](docs/speaking.md).

## Chạy để phát triển

Python **3.12+**, Node **22+**, PostgreSQL **16**, **FFmpeg** trong PATH để xử lý audio. Terminal đầu:

```sh
docker compose up -d postgres
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
alembic upgrade head
python -m app.db.seed
python -m app.db.speaking_seed
python -m app.db.reading_seed
uvicorn app.main:app --reload --port 8000
```

Terminal thứ hai:

```sh
cd frontend
npm ci
npm run dev
```

Backend đọc `.env` ở thư mục gốc hoặc backend. Next.js có mặc định proxy tới `localhost:8000`; nếu thay đổi, export `BACKEND_INTERNAL_URL` vào shell hoặc tạo `frontend/.env.local`. Không sao chép OpenAI key sang `.env.local` của frontend.

## Kiến trúc & cấu trúc

Modular monolith: **Next.js / TypeScript / Tailwind / shadcn/ui / Recharts → FastAPI / Pydantic v2 → SQLAlchemy 2 / Alembic / PostgreSQL**. Application service gọi abstraction `LLMClient`; adapter `OpenAILLMClient` dùng OpenAI Python SDK và Responses Structured Outputs. Không queue/Redis/microservices trong MVP.

```text
backend/
  app/
    api/           # Routes, dependency xác thực, serializers
    core/          # Settings, Argon2, JWT
    db/            # Async sessions và bộ đề mẫu
    models/        # SQLAlchemy models
    schemas/       # Pydantic request + structured AI output
    repositories/  # Truy vấn theo quyền sở hữu
    services/      # Đề, phiên thi, chấm, tiến độ
    llm/           # LLMClient và OpenAI adapter
    prompts/       # Prompts có version
    common/        # Đếm từ, lỗi ứng dụng
  alembic/         # Migration schema PostgreSQL
  tests/           # 5 kiểm tra tích hợp trọng tâm
frontend/src/
  app/             # Các trang và proxy API cùng origin
  components/      # Layout + shadcn/ui primitives
  features/        # Auth, exam, writing, speaking, reading, grading, history, progress
  hooks/           # Autosave, phục hồi nháp, giải quyết xung đột
  services/        # API client + refresh token
  lib/             # Helpers và nhãn tiếng Việt
  types/           # Hợp đồng dữ liệu frontend
docs/              # Ghi chú thiết kế ngắn
```

## Luồng bài thi & chấm

- Thi full: 60 phút cho hai Task; luyện riêng có thể bật 20/40 phút **đề xuất**.
- Backend lưu `started_at` / `expires_at`; reload không đặt lại đồng hồ. Sau hạn, máy chủ chốt bản đã lưu và từ chối sửa.
- Nháp lưu trên thiết bị theo user + attempt và gửi PATCH sau 1 giây ngừng gõ, thử lại khi có mạng. `revision` ngăn tab cũ ghi đè bài mới. Bản nháp chưa đồng bộ khi hết giờ vẫn tải được từ trang kết quả.
- Nộp full bằng một transaction cho cả hai Task. Sau nộp, result page yêu cầu chấm từng bài; có thể thử lại từ lịch sử khi dịch vụ AI gặp lỗi.
- Bốn tiêu chí 0–10: Task Fulfillment, Organization, Vocabulary, Grammar. Điểm Task = trung bình bốn tiêu chí. Backend tự tính; Writing = `(Task1 + 2 × Task2) / 3`.
- Cache theo nội dung đề, bài viết, model, prompt version; giới hạn trong tài khoản. PostgreSQL locks tránh trả phí lặp cho yêu cầu chấm đồng thời.
- Phản hồi gồm 3 ưu tiên cải thiện, điểm mạnh, bố cục, đáp ứng yêu cầu, lỗi, từ vựng, từng câu, bản sửa tối thiểu và bản tham khảo B2.
- Dashboard tách điểm Writing đủ hai Task và điểm luyện Task. Mức B1/B2/C1 hiển thị là tham khảo riêng kỹ năng viết, không chứng nhận bậc tổng thể.

**Kết quả được AI ước tính nhằm phục vụ luyện tập và không phải điểm chính thức của kỳ thi VSTEP.**

## Speaking

Mở `/speaking` để bắt đầu. Có Full Test, Part 1/2/3 và Luyện nhanh; lịch sử và tiến độ có nút chuyển Writing/Speaking. Audio và transcript cùng được lưu; lỗi mạng cho phép tải lại bản ghi. Phát âm không được chấm từ transcript. Tổng điểm Speaking là trung bình năm tiêu chí 20%; chỉ có khi đủ dữ liệu audio.

Xem [tài liệu Speaking đầy đủ](docs/speaking.md) cho endpoint, schema, cấu hình OpenAI, lưu trữ, recovery và các giới hạn.

## Reading

Mở `/reading`: Thi thử (4 passages/40 câu/60 phút), Luyện 1 Passage, Luyện nhanh và Luyện theo dạng câu hỏi; lọc B1/B2/C1 và chủ đề. Bộ mẫu gồm 2 B1, 4 B2, 2 C1, mỗi bài khoảng 500 từ/10 câu. Chọn **B2 + chủ đề ngẫu nhiên** để thi full ngay khi chưa có OpenAI key.

Đáp án tự lưu, có dự phòng trên thiết bị, xử lý xung đột giữa tab và đồng hồ do backend quản lý. Sau nộp, xem điểm, giải thích đúng/sai từng lựa chọn, đoạn bằng chứng được tô sáng, lịch sử và biểu đồ tiến độ. Tạo đề mới và giải thích từ vựng theo ngữ cảnh dùng OpenAI; chấm điểm và analytics dùng Python/SQL. History/progress có nút chuyển Writing/Speaking/Reading.

Xem [tài liệu Reading](docs/reading.md) cho API, schema, ngân hàng đề, cách lưu/nộp, quy đổi điểm luyện tập và giới hạn MVP.

## API chính

Tất cả dưới `/api/v1`; Swagger mô tả body cụ thể. Auth dùng JWT cookie HttpOnly; frontend tự refresh khi access token hết hạn.

| Method | Path | Chức năng |
| --- | --- | --- |
| POST | `/auth/register`, `/auth/login`, `/auth/refresh`, `/auth/logout` | Xác thực và xoay vòng token |
| GET | `/auth/me`, `/health` | Tài khoản / trạng thái |
| POST | `/questions/generate` | Lấy đề mẫu theo bộ lọc hoặc sinh đề AI |
| GET | `/questions/{id}` | Xem đề |
| POST / GET | `/exams`, `/exams/{id}` | Tạo / đọc phiên thi |
| POST | `/exams/{id}/submit` | Nộp nguyên tử cả phiên |
| PATCH | `/attempts/{id}` | Lưu nháp kèm revision |
| POST | `/attempts/{id}/submit` | Nộp bài luyện riêng |
| POST | `/attempts/{id}/grade` | Chấm đồng bộ; có cache |
| GET | `/attempts`, `/attempts/{id}` | Lịch sử phân trang, lọc mode / chi tiết |
| GET | `/progress/summary`, `/progress/errors` | Thống kê tài khoản |

## Migration & kiểm tra

```sh
cd backend
alembic upgrade head
alembic revision --autogenerate -m describe_change
alembic check
pytest -q
ruff check app alembic tests

cd ../frontend
npm run lint
npm run build
```

Integration tests cần PostgreSQL đã migrate + seed. Tests tạo tài khoản riêng rồi xóa đúng tài khoản thử; không drop database hoặc xóa dữ liệu người dùng. HTTP fixture chỉ dùng trong test để xác minh OpenAI SDK parse/retry, lưu grading, cache và thống kê; không gọi API tính phí.

## Giới hạn MVP

Chạy một backend worker; rate limit đơn giản trong bộ nhớ theo IP/route. Khi scale nhiều worker cần rate limiter dùng shared storage và quota theo tài khoản. Chấm đồng bộ có thể chờ vài phút; nếu provider xử lý xong nhưng kết nối bị đứt trước khi lưu, lần thử lại có thể phát sinh phí. Bộ lọc đề mẫu chỉ có các tổ hợp đã seed; UI báo rõ nếu không có đề khớp. Không có phục hồi mật khẩu hoặc xác minh email. Speaking có giới hạn audio, xử lý đồng bộ và đánh giá phát âm phụ thuộc model audio thực sự được cấu hình.

Trước production: HTTPS, secret mạnh, CORS đúng origin, backup PostgreSQL và giới hạn chi phí OpenAI. Bản Compose hiện tại dành cho local, các cổng chỉ bind `127.0.0.1`.

Xem thêm: [kiến trúc](docs/architecture.md), [database](docs/database.md), [AI grading](docs/ai-grading.md), [format luyện thi](docs/vstep-format.md).
