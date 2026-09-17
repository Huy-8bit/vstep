# Implementation status

Core MVP implemented: FastAPI + PostgreSQL migrations, Argon2/JWT rotating sessions, 20 seed questions, OpenAI Responses structured generation/grading, versioned prompts/cache/usage, server-deadline exams, atomic full submission, local drafts/debounced autosave/revision conflicts, Vietnamese Next.js pages, detailed result tabs, history, Recharts progress, Docker Compose and docs.

Validation completed: frontend ESLint + TypeScript/Next.js production build; backend Ruff + 5 focused PostgreSQL integration tests; Alembic schema check; Python 3.12 and Node 22 Docker image builds. All three Compose services started successfully. HTTP smoke through localhost:3000 verified all page routes, auth cookies/rotation/logout, seed selection, exam creation, autosave/reload, submission, history and progress. Temporary smoke users were removed.

No live API key was provided, so paid OpenAI responses could not be verified in this session. Tests exercise the real SDK with HTTP transport fixtures, including structured-output retry, concurrent grading/cache, stored errors and progress. The production app contains no mock AI provider. Missing key returns a clean 503 while preserving the submitted answer.

Browser runtime returned no available browsers; interactive/visual browser QA could not be performed. Frontend HTTP/render checks succeeded, but do not substitute for interactive UI verification.

Main paths: `backend/app/services`, `backend/app/llm/openai_client.py`, `backend/app/api/routes`, `backend/alembic/versions`, `frontend/src/hooks/use-autosave.ts`, `frontend/src/features/*`, `docker-compose.yml`.

Core implementation is complete. Local Docker services are left running at localhost:3000 (frontend), localhost:8000 (API/docs), localhost:5432 (PostgreSQL). To enable AI, copy .env.example to .env, configure OPENAI_API_KEY / OPENAI_MODEL and recreate backend. Do not add modules beyond Writing or replace Python backend.
