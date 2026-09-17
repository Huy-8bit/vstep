# Database

PostgreSQL 16, SQLAlchemy 2 async, Alembic. ID dạng UUID string, timestamps có timezone, các cấu trúc feedback dùng JSONB.

| Bảng | Dữ liệu / ràng buộc |
| --- | --- |
| users | Email unique, password_hash, timestamps |
| auth_sessions | User, refresh_hash, expires_at, revoked_at |
| writing_questions | Task/type/topic/test_profile, đề, requirements, minimum words, source, fingerprint unique, prompt version |
| exam_sessions | User, mode, started_at, expires_at, submitted_at, status |
| writing_attempts | User/question/exam, answer, word_count, revision, duration; unique exam + task |
| writing_gradings | Unique attempt, bốn điểm và trung bình, feedback JSONB, hai phiên bản, model/version/cache_key |
| writing_errors | Grading, category/subtype, original/corrected, giải thích, severity |
| ai_usage_logs | User, operation/model, input/output tokens, latency/status; không có key hoặc bài viết |

FK dùng cascade ở dữ liệu phụ thuộc người dùng/bài làm. Questions dùng chung, giữ nguyên sau khi tạo. Check constraints giới hạn task, số từ tối thiểu và điểm 0–10. Index cho user, mode lookup qua exam, task, topic, cache và error category.

Trạng thái phiên: IN_PROGRESS → SUBMITTED hoặc EXPIRED. Trạng thái bài: DRAFT → SUBMITTED → GRADED. Không đưa kết quả chưa chấm vào trung bình. Khi thiếu một Task đã chấm, điểm tổng Writing để null.

`alembic upgrade head` khởi tạo schema. `python -m app.db.seed` idempotent nhờ fingerprint + ON CONFLICT DO NOTHING. Không dùng `create_all` thay migration trong runtime.


Migration `c87e4a932b61` thêm `test_profile` cho questions/passages/sessions của ba kỹ năng; thêm `internal_difficulty_band` riêng cho passage/question Reading và `blueprint_version` cho Reading session. Cột `difficulty` được giữ nullable với thuộc tính ORM `legacy_difficulty`; không dùng cho API hay generation. Metadata mới của tám bài mẫu được cập nhật theo nội dung đã biên soạn, giữ nguyên ID, answer key, bài làm và kết quả. Đề AI cũ chưa được phân loại có band null, không được tự gán band từ nhãn CEFR cũ. `estimated_level` của Speaking vẫn là kết quả sau chấm; không bị thay đổi bởi migration.

## Assessment v2 migration

`e41b6d0a9f22` follows `c87e4a932b61` and adds:

- `writing_attempts.grading_work`: durable analysis/calibration checkpoints.
- `writing_gradings`: grader/analysis/calibration versions plus criterion evidence and structured analysis snapshot. Existing records retain grader `1.0.0`.
- `writing_grading_revisions`: immutable previous grading snapshots on explicit upgrade.
- `writing_calibration_samples`: question/answer and nullable teacher scores, reviewer_count, ready for future human calibration.
- `pronunciation_practices`: user/reference/source answer, immutable recording, analysis/model/version, pronunciation/fluency, dates, unique client_request_id per user.

Audio stays in the existing private speaking volume. This migration does not modify Reading data or existing submitted Writing answers. New tables use the same UUID strings and timestamps as the existing schema.
