# VSTEP Practice Platform — implementation status

The existing Writing application has been extended with the Speaking and Reading MVPs. Keep this project, Python/FastAPI, PostgreSQL, Next.js and the working Writing flows; do not replace the stack.

Speaking implementation includes all five modes, 45 original B2 seed prompts (15 per part), AI generation with recent-topic avoidance, ordered full-test sessions and hidden follow-ups, MediaRecorder with input meter and Vietnamese microphone errors, practice preview/retake, no replacement of committed Full Test recordings, upload retry with IndexedDB backup, private persistent WAV audio, genuine OpenAI transcription/audio analysis, structured five-criterion grading, sentence corrections and natural spoken B2 answers, audio playback, history, progress and settings. The homepage and navigation include Writing, Speaking and Reading.

Backend: five new tables and Alembic revision `008c2258fea3`; services under `backend/app/services/*speaking*`, `audio_storage_service.py`, `speech_transcription_service.py`, `text_to_speech_service.py`; adapters in `backend/app/speech`; versioned prompts; authenticated APIs in `backend/app/api/routes/speaking.py`. Frontend: `frontend/src/features/speaking` and `/speaking` routes. Audio storage uses a Docker volume and FFmpeg; PostgreSQL volume/project naming is preserved.

Speaking grading uses real audio evidence for pronunciation and fluency. If audio analysis is missing or uncertain, those scores and the total remain null. The backend computes the equal-weight average only with five available criteria. Full Test includes all answers and follow-ups holistically, without part weights. Audio/text/model/version caches and PostgreSQL locks prevent duplicate work under normal retries; unknown provider outcomes can still incur retry costs. No mock AI provider is included.

This task intentionally adds and runs no unit, integration or E2E tests, as requested. TypeScript compilation, Python imports/OpenAPI construction, database migration/seed and Docker production builds are used to make the product runnable. The host Turbopack build encountered a sandbox port-binding restriction; the frontend production build succeeds in Docker. Backend Docker includes FFmpeg. Existing Writing tests were neither modified nor run for this task.

No live OpenAI key was supplied or used for paid Speaking validation. Browser microphone capture and actual model response quality have not been verified interactively. Configure OPENAI_API_KEY and appropriate OPENAI_MODEL / OPENAI_TRANSCRIBE_MODEL / OPENAI_SPEAKING_AUDIO_MODEL before using complete AI grading. OPENAI_TTS_MODEL is optional; browser TTS is the fallback.

Run `docker compose up -d --build` from the root. Website: http://localhost:3000/speaking. Backend docs: http://localhost:8000/docs. Setup and limitations are documented in README.md and docs/speaking.md. Do not use `docker compose down -v` when preserving user data/audio.


## Reading

Implemented:

- Full Test: four approximately 500-word passages, exactly 40 A/B/C/D questions, 60-minute server deadline. Passage Practice, Quick Practice and Question Type Practice with optional timers, B1/B2/C1 and topic filters.
- Reusable question bank, prefer unseen passages, explicit AI generation or bank-shortage generation. Eight original seed passages (2 B1, 4 B2, 2 C1), 80 questions, 490–534 words per passage; ten question types and Vietnamese explanations for every option.
- OpenAI Responses Structured Outputs with versioned generator/vocabulary prompts, deterministic schema/content validation and one invalid-output retry. No AI call for submission, scoring, strategy feedback or progress.
- Authenticated session APIs with explicit safe DTO allowlists. Answer keys, correctness, explanations and evidence only returned through owned submitted results. Vocabulary restricted to an owned submitted session.
- Server-locked saves/submissions, revision conflicts, idempotent retries, deterministic scores, permanent result snapshots, late-answer rejection and expiry finalization.
- Split-pane exam, mobile tabs, question/passage navigation, mark for review, answer counts, A/B/C/D shortcuts, submit dialog, reload-safe countdown, debounced autosave with offline local backup and retry/conflict resolution.
- Results with correct/wrong/unanswered filters, all option explanations, scroll/highlight evidence paragraphs, contextual vocabulary on request, unsynced-choice notice, passage timing and strategy feedback based on actual results.
- Reading history with pagination/mode filters, score timeline, weighted accuracy, average time, type/topic/difficulty analytics and weakness practice CTAs. Homepage, navigation and shared history/progress skill switch include Reading.

Remaining:

- No core Reading implementation placeholder. Docker production build/startup completed successfully: frontend Ready, backend and PostgreSQL healthy.
- Live OpenAI generation/vocabulary quality and interactive browser behavior have not been verified. No unit/integration/E2E tests were added or run, per the user's instruction.
- Seed-only Full Test works at B2/random. B1/C1 or narrower topics may need AI to add enough passages. Target-type practice uses available matching questions (up to five, currently two/four from the unfiltered seed levels) instead of duplicating questions.

Models:

- `ReadingPassage`, `ReadingQuestion`, `ReadingExamSession`, `ReadingAnswer`, `ReadingResult` in `backend/app/models/reading.py`.
- Alembic `5c96e8660369` follows Speaking revision `008c2258fea3`. Applied locally; seed validated and loaded. Backend startup now seeds all three skills. Existing database/audio volumes and Compose project name are preserved.

Routes:

- `/api/v1/reading`: GET `/bank`; POST `/questions/generate`; GET `/passages/{id}`; POST `/sessions`; GET `/sessions/{id}`; PATCH `/sessions/{id}/answers`; PUT `/sessions/{id}/answers/{question_id}`; POST `/sessions/{id}/submit`; GET `/results/{id}`, `/history`, `/progress`; POST `/vocabulary/explain`.

Frontend:

- `frontend/src/features/reading`; `/reading`, `/reading/exam/[id]`, `/reading/result/[id]`, `/reading/history`, `/reading/progress`. Shared UI and auth/API client are reused. TypeScript compilation and the final Docker Next.js production build passed, including all five Reading routes; Python imports/OpenAPI construction passed (45 total API paths).

Important decisions:

- Score utility is `correct / total * 10`, labeled a practice estimate, never an official VSTEP score. Unanswered questions remain in the denominator. Analytics and feedback derive from stored answers; perfect results do not get a fabricated weakness.
- Session stores ordered passage/question IDs in JSONB; normalized question/answer tables retain keys. Published bank passages are immutable through the API; sharing them across users is intentional.
- No background worker: at deadline the browser submits, and later backend reads/saves/history/progress finalize overdue sessions using the original deadline. Offline choices received after expiry are not scored; the client preserves and shows the local difference.
- Time per question/passage estimates active browser time; total duration uses server timestamps. AI vocabulary caches by passage/paragraph/term/model/prompt version. Generator receives recent titles/topics and rejects duplicate content fingerprints.
- Configuration reuses OPENAI_API_KEY / OPENAI_MODEL. Default seed/scoring/review/history/progress work without a key. Writing and Speaking modules were not rewritten.
- See `docs/reading.md` and README for setup, endpoint details, bank limitations and recovery behavior.
