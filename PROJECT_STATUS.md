# VSTEP Practice Platform — implementation status

The existing Writing application has been extended with the Speaking MVP. Keep this project, Python/FastAPI, PostgreSQL, Next.js and the working Writing flows; do not replace the stack.

Speaking implementation includes all five modes, 45 original B2 seed prompts (15 per part), AI generation with recent-topic avoidance, ordered full-test sessions and hidden follow-ups, MediaRecorder with input meter and Vietnamese microphone errors, practice preview/retake, no replacement of committed Full Test recordings, upload retry with IndexedDB backup, private persistent WAV audio, genuine OpenAI transcription/audio analysis, structured five-criterion grading, sentence corrections and natural spoken B2 answers, audio playback, history, progress and settings. The homepage and navigation include both Writing and Speaking.

Backend: five new tables and Alembic revision `008c2258fea3`; services under `backend/app/services/*speaking*`, `audio_storage_service.py`, `speech_transcription_service.py`, `text_to_speech_service.py`; adapters in `backend/app/speech`; versioned prompts; authenticated APIs in `backend/app/api/routes/speaking.py`. Frontend: `frontend/src/features/speaking` and `/speaking` routes. Audio storage uses a Docker volume and FFmpeg; PostgreSQL volume/project naming is preserved.

Speaking grading uses real audio evidence for pronunciation and fluency. If audio analysis is missing or uncertain, those scores and the total remain null. The backend computes the equal-weight average only with five available criteria. Full Test includes all answers and follow-ups holistically, without part weights. Audio/text/model/version caches and PostgreSQL locks prevent duplicate work under normal retries; unknown provider outcomes can still incur retry costs. No mock AI provider is included.

This task intentionally adds and runs no unit, integration or E2E tests, as requested. TypeScript compilation, Python imports/OpenAPI construction, database migration/seed and Docker production builds are used to make the product runnable. The host Turbopack build encountered a sandbox port-binding restriction; the frontend production build succeeds in Docker. Backend Docker includes FFmpeg. Existing Writing tests were neither modified nor run for this task.

No live OpenAI key was supplied or used for paid Speaking validation. Browser microphone capture and actual model response quality have not been verified interactively. Configure OPENAI_API_KEY and appropriate OPENAI_MODEL / OPENAI_TRANSCRIBE_MODEL / OPENAI_SPEAKING_AUDIO_MODEL before using complete AI grading. OPENAI_TTS_MODEL is optional; browser TTS is the fallback.

Run `docker compose up -d --build` from the root. Website: http://localhost:3000/speaking. Backend docs: http://localhost:8000/docs. Setup and limitations are documented in README.md and docs/speaking.md. Do not use `docker compose down -v` when preserving user data/audio.
