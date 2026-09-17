# VSTEP Practice Platform — implementation status

The existing Writing application has been extended with the Speaking and Reading MVPs. Keep this project, Python/FastAPI, PostgreSQL, Next.js and the working Writing flows; do not replace the stack.

Speaking implementation includes all five modes, 45 original VSTEP.3-5 seed prompts (15 per part), AI generation with recent-topic avoidance, ordered full-test sessions and hidden follow-ups, MediaRecorder with input meter and Vietnamese microphone errors, practice preview/retake, no replacement of committed Full Test recordings, upload retry with IndexedDB backup, private persistent WAV audio, genuine OpenAI transcription/audio analysis, structured five-criterion grading, sentence corrections and natural spoken B2 answers, audio playback, history, progress and settings. The homepage and navigation include Writing, Speaking and Reading.

Backend: five new tables and Alembic revision `008c2258fea3`; services under `backend/app/services/*speaking*`, `audio_storage_service.py`, `speech_transcription_service.py`, `text_to_speech_service.py`; adapters in `backend/app/speech`; versioned prompts; authenticated APIs in `backend/app/api/routes/speaking.py`. Frontend: `frontend/src/features/speaking` and `/speaking` routes. Audio storage uses a Docker volume and FFmpeg; PostgreSQL volume/project naming is preserved.

Speaking grading now uses the normalized audio provider scores directly for pronunciation and fluency; the text model only grades the three language criteria. If audio analysis is missing or uncertain, those scores and the total remain null. The backend computes the equal-weight average only with five available criteria. Full Test language assessment includes all answers and follow-ups holistically. Acoustic aggregation averages available recording scores only when every submitted recording has reliable evidence; no official VSTEP part weighting is claimed. Audio/text/model/version caches and PostgreSQL locks prevent duplicate work under normal retries; unknown provider outcomes can still incur retry costs. No mock AI provider is included.

This task intentionally adds and runs no unit, integration or E2E tests, as requested. TypeScript compilation, Python imports/OpenAPI construction, database migration/seed and Docker production builds are used to make the product runnable. The host Turbopack build encountered a sandbox port-binding restriction; the frontend production build succeeds in Docker. Backend Docker includes FFmpeg. Existing Writing tests were neither modified nor run for this task.

No paid OpenAI validation calls were made during implementation. Browser microphone capture and actual model response quality have not been verified interactively. The running configuration has an API key, gpt-5.6 text, gpt-4o-transcribe, gpt-audio and gpt-4o-mini-tts enabled; no secret was displayed. Browser TTS remains a fallback for exam question playback; pronunciation reference playback uses OpenAI TTS.

Run `docker compose up -d --build` from the root. Website: http://localhost:3000/speaking. Backend docs: http://localhost:8000/docs. Setup and limitations are documented in README.md and docs/speaking.md. Do not use `docker compose down -v` when preserving user data/audio.


## Reading

Implemented:

- Full Test: four approximately 500-word passages, exactly 40 A/B/C/D questions, 60-minute server deadline. Passage Practice, Quick Practice and Question Type Practice with optional timers and topic filters in the shared VSTEP.3-5 profile.
- Reusable question bank, prefer unseen passages, explicit AI generation or bank-shortage generation. Eight original seed passages (two in each internal editorial band), 80 questions, 490–534 words per passage; ten question types and Vietnamese explanations for every option.
- OpenAI Responses Structured Outputs with versioned generator/vocabulary prompts, deterministic schema/content validation and one invalid-output retry. No AI call for submission, scoring, strategy feedback or progress.
- Authenticated session APIs with explicit safe DTO allowlists. Answer keys, correctness, explanations and evidence only returned through owned submitted results. Vocabulary restricted to an owned submitted session.
- Server-locked saves/submissions, revision conflicts, idempotent retries, deterministic scores, permanent result snapshots, late-answer rejection and expiry finalization.
- Split-pane exam, mobile tabs, question/passage navigation, mark for review, answer counts, A/B/C/D shortcuts, submit dialog, reload-safe countdown, debounced autosave with offline local backup and retry/conflict resolution.
- Results with correct/wrong/unanswered filters, all option explanations, scroll/highlight evidence paragraphs, contextual vocabulary on request, unsynced-choice notice, passage timing and strategy feedback based on actual results.
- Reading history with pagination/mode filters, score timeline, weighted accuracy, average time, type/topic analytics and weakness practice CTAs. Homepage, navigation and shared history/progress skill switch include Reading.

Remaining:

- No core Reading implementation placeholder. Docker production build/startup completed successfully: frontend Ready, backend and PostgreSQL healthy.
- Live OpenAI generation/vocabulary quality and interactive browser behavior have not been verified. No unit/integration/E2E tests were added or run, per the user's instruction.
- Seed-only Full Test works with the random-topic VSTEP.3-5 bank. Narrow topics may need AI to fill missing blueprint slots. Target-type practice uses available matching questions (up to five) across the shared bank instead of duplicating questions.

Models:

- `ReadingPassage`, `ReadingQuestion`, `ReadingExamSession`, `ReadingAnswer`, `ReadingResult` in `backend/app/models/reading.py`.
- Alembic `5c96e8660369` follows Speaking revision `008c2258fea3`; profile refactor `c87e4a932b61` follows it; assessment revision `e41b6d0a9f22` is now the head. Applied locally; seed validated and loaded. Backend startup now seeds all three skills. Existing database/audio volumes and Compose project name are preserved.

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


## VSTEP.3–5 multilevel correction

Implemented:

- All public Writing/Speaking/Reading generation and session requests now use `test_profile=VSTEP_3_5`. Removed public CEFR difficulty selection, hardcoded B2 generation input and CEFR badges on questions/history/progress. Public JSON schemas reject the obsolete difficulty field; GET bank no longer filters on difficulty.
- Shared domain profile in `backend/app/common/test_profiles.py` and frontend profile constant. Generator prompts bumped to 2.0.0: Writing/Speaking differentiate by response performance, not separate exam versions or obscure topics.
- `ReadingTestBlueprint` (2.0.0) enforces four distinct approximately 500-word passages, 10 questions each, 40 questions total and a 60-minute deadline. Ordered internal text demands and required question-type coverage span the entire test. Every eligible passage contains at least two item demand bands. The generator receives full-test context, companion passages, position and required types for each missing slot.
- Full Reading bank selection uses the blueprint instead of random same-level passages. Frontend asks the backend how many blueprint slots are missing, generates them one at a time if configured, then creates the session. Practice modes and topic/question-type filters remain.
- Non-destructive migration `c87e4a932b61` adds profile columns, internal Reading passage/item metadata and session blueprint version. Old difficulty values remain nullable under ORM name `legacy_difficulty`; new code never queries them. Existing IDs, content, answer keys, sessions, grades and audio are retained.
- Seed metadata now assigns the eight original texts to four editorial bands (two each), with varied question demand metadata. This is not a CEFR mapping. Old AI material without metadata remains usable for individual practice and historical review, but cannot fill a Full Test blueprint slot until calibrated internally.
- Estimated result levels and B2 learning examples remain intact. Result labels explicitly say “Mức năng lực AI ước tính”. No existing target_level feature was found, and no outcome/learner-goal fields were repurposed as generation inputs.
- README, docs/vstep-format.md, docs/reading.md, docs/speaking.md and docs/database.md updated to describe one multilevel test and legacy-data semantics.

Validation and remaining:

- TypeScript compilation passed. Docker production build and startup succeeded; migration and all seed commands completed, backend/PostgreSQL healthy and frontend Ready. The final frontend rebuild, including the result/history label updates, also completed and is running.
- No new tests, unit/integration/E2E runs or separate testing phase, as requested. No paid OpenAI call or interactive browser verification performed.
- No core refactor TODO. Internal bands are editorial balancing aids, not official VSTEP/CEFR item calibration. Existing sessions continue with their original content; only newly created full Reading sessions use the new blueprint. Automatic adaptive practice and overall four-skill proficiency are outside this correction.


## Writing calibration v2 + OpenAI pronunciation coach

Implemented end to end:

- Writing evidence analysis → deterministic error/structure metrics → conservative calibration with six editorial anchors → conditional consistency review → feedback/corrections after score freeze. Exact Alex email included as an editorial reference only; no hardcoded matching, final score, or per-error deductions.
- Half-point criterion scores and deterministic four-criterion mean; 7+ requires specific original positive evidence and a substantive justification. Calibration must retain negative evidence from analysis. Separate Task 1/2 analysis context replaced the old one-call scoring prompts.
- Durable checkpoints, grader/model/prompt versions, explicit upgrade action and full previous result snapshots. Results display evidence, metrics, versions and grading history. Authenticated admin inspection allowlist and unpopulated human calibration sample schema.
- `AudioAnalysisProvider` / `OpenAIAudioAnalysisProvider`: real WAV through Chat Completions input_audio; function-call result parsed/validated with Pydantic, confidence gates and bounded invalid-output retry. No transcript-only pronunciation, invented IPA or text-generated pronunciation scores.
- Speaking text model schema limited to Grammar/Vocabulary/Structures; acoustic scores and diagnoses merged by backend from audio output. Per-recording UI shows pronunciation, intelligibility, clarity, stress, intonation, rhythm, fluency and replay.
- `/speaking/pronunciation`: issue → reference → cached OpenAI TTS sample → MediaRecorder → private saved audio → scripted audio assessment → repeat as a separate attempt. Saved history/recovery, wrong-reference/insufficient-evidence handling, nullable scores, source-answer ownership.
- Speaking History includes pronunciation attempts. Progress includes pronunciation/fluency timeline, recurring audible issues, difficult words and first-versus-latest improvement on the same reference. Existing exam modes and Reading behavior retained; no CEFR test difficulty was reintroduced.
- Canonical audio configuration plus legacy aliases, audio/TTS enabled defaults, TTS advisory locking/atomic cache writes. Migration `e41b6d0a9f22` applied without replacing database/audio volumes.

Build/startup: Python imports/model mappings and frontend production compilation passed; Docker startup and database migration succeeded. No tests added or run. No live paid AI scoring call or microphone/browser validation; actual Alex scores and pronunciation quality remain unmeasured. See `docs/writing-assessment.md` and updated `docs/speaking.md` for configuration, flow, routes and limitations.
