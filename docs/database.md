# Database

PostgreSQL 16, SQLAlchemy 2 async, Alembic. ID dạng UUID string, timestamps có timezone, các cấu trúc feedback dùng JSONB.

| Bảng | Dữ liệu / ràng buộc |
| --- | --- |
| users | Email unique, password_hash, timestamps |
| auth_sessions | User, refresh_hash, expires_at, revoked_at |
| writing_questions | Task/type/topic/difficulty, đề, requirements, minimum words, source, fingerprint unique, prompt version |
| exam_sessions | User, mode, started_at, expires_at, submitted_at, status |
| writing_attempts | User/question/exam, answer, word_count, revision, duration; unique exam + task |
| writing_gradings | Unique attempt, bốn điểm và trung bình, feedback JSONB, hai phiên bản, model/version/cache_key |
| writing_errors | Grading, category/subtype, original/corrected, giải thích, severity |
| ai_usage_logs | User, operation/model, input/output tokens, latency/status; không có key hoặc bài viết |

FK dùng cascade ở dữ liệu phụ thuộc người dùng/bài làm. Questions dùng chung, giữ nguyên sau khi tạo. Check constraints giới hạn task, số từ tối thiểu và điểm 0–10. Index cho user, mode lookup qua exam, task, topic, cache và error category.

Trạng thái phiên: IN_PROGRESS → SUBMITTED hoặc EXPIRED. Trạng thái bài: DRAFT → SUBMITTED → GRADED. Không đưa kết quả chưa chấm vào trung bình. Khi thiếu một Task đã chấm, điểm tổng Writing để null.

`alembic upgrade head` khởi tạo schema. `python -m app.db.seed` idempotent nhờ fingerprint + ON CONFLICT DO NOTHING. Không dùng `create_all` thay migration trong runtime.
