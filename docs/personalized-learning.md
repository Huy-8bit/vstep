# Personalized learning and study coach

The `/learning` area explains what to learn next from submitted, graded practice. `/progress` remains the score dashboard. Existing graders, private imports, question banks, notebook, recordings and history remain authoritative.

## Evidence and lifecycle

After Writing grading, Speaking grading or Reading submission/expiry, `LearningSignalService` runs in a separate transaction. It makes **no AI call**. Failed extraction never rolls back a submitted exam; `/learning/recalculate` retries from stored grades. Opening the overview schedules an initial background backfill in batches of 50, then reads stored aggregates. Job state is persisted; a failed job can be retried and a stale running job can be resumed. This uses FastAPI background tasks in the current single-worker application, not a separate durable queue.

`learning_attempts` stores exposure (words or scorable questions), criterion scores, timestamps and meaningful lexical counts. `learning_signals` keeps normalized concept, exact evidence, provenance, grader/model/analysis/taxonomy version and outcome. Reading creates both successful and unsuccessful observations; untrusted/missing answer keys are excluded. Unanswered questions with trusted keys count as unsuccessful exposures. Wrong-option explanations come from the question rationale and never purport to reveal the learner's reasoning.

Signals deduplicate by user, skill, source attempt, extraction version and evidence fingerprint (including supplied sentence/answer/question location). Regrading archives the old version via `active=false`; historical evidence remains auditable but only the current snapshot contributes to aggregates. Writing attempts are units; Speaking sessions are units, with sequence metadata per answer, so individual-answer and whole-session grading do not double-count recurrence.

Taxonomies are under `backend/app/learning/taxonomy/`. Specific patterns such as `INTERNET_EXPRESSION`, `AGREE_USAGE`, `ADVANTAGE_COUNTABILITY` and `PREPOSITION_DEPEND_ON` merge equivalent validated errors. Uncertain historical feedback remains broad; the backfill never fabricates detailed diagnoses. Structural signals use explicit assessment fields or narrowly recognized negative feedback. Frequency counts exclude function words and are shown as observations, not automatic errors.

Audio-only pronunciation/fluency signals require a real audio hash, available assessment, sufficient confidence and audible evidence. Transcript grammar/vocabulary are separate. Missing audio remains unknown, never a zero score or inferred pronunciation diagnosis.

## Aggregation, trends and priorities

`user_weaknesses` provides structured per-concept aggregates. Grammar/vocabulary share a CROSS row with per-skill evidence counts. One affected attempt is NEW, two OBSERVED, three RECURRING by default. Repeated errors within one essay do not establish cross-attempt recurrence. Confidence wording reflects available evidence rather than false numerical precision.

The trend service compares disjoint groups of five attempts by default. Grammar/vocabulary use errors per 100 words, Reading uses wrong/scorable questions and other categories use occurrences per assessed attempt. Zero-error graded attempts contribute exposure, but their existence alone does not establish mastery. Audio trends exclude attempts without reliable corresponding acoustic scores. Fewer than two complete windows yields INSUFFICIENT_DATA.

Priority is a configurable product heuristic, not an official VSTEP score: recency-weighted frequency, severity, recency, confidence, criterion impact and persistence. Occurrences decay with a default 30-day half-life. Historical mistakes are never deleted. Strengths require several criterion observations or at least ten objective Reading questions.

## Lessons, exercises and transfer

Lessons are generated only on explicit action, from at most five relevant evidence records. Their cache is private and keyed by source evidence, prompt version and model. The service validates every learner quotation, correction and source id. All learner text is untrusted input to the prompt. Lessons contain Vietnamese rules, natural B1–B2 English examples, traps, quick checks and practice suggestions.

Exercise sets contain 5, 8 or 10 items. Supported forms include grammar choices/gaps/corrections/transformations; vocabulary collocations, contextual recall and rewrites; Writing sentence/paragraph/introduction/idea tasks; targeted Reading; and Speaking short, timed, comparison, development, vocabulary-reuse and pronunciation drills. Exact choices/finite keys are checked deterministically. Open answers receive bounded feedback on the target concept, with no new VSTEP score. Uncertain feedback does not grant success. Keys, sample answers, rubrics and explanations remain server-side until the item is answered. Answers are immutable and retries are idempotent.

Speaking items launch the existing recorder and grader; pronunciation items launch the existing pronunciation coach. Results are linked back to the exercise. Where an existing grader provides no sufficiently specific positive evidence, completion is recorded with an unknown concept result, rather than granting mastery for mere submission. Writing/Reading/Speaking transfer tasks use the existing generation, validation, session and grading services. Reading offers ten trusted questions of the requested type from the existing bank (preferring unseen questions), or explicit AI generation combining two five-question short passages for varied contexts. Both use the existing Reading engine and quality gates. An insufficient bank returns a clear message and lets the learner choose AI generation. Focused timed Speaking drills pass their time limit to the existing recorder.

Vocabulary Coach remains the sole notebook/review system. Its completed reviews create learning events, including historical backfill. Phrase reuse is observed in actual graded Writing/Speaking. A positive grading quotation or an explicit, bounded usage check can verify it; mere substring presence does not mean natural usage. The learning vocabulary panel distinguishes observed, verified, learned-but-not-reused and notebook mastery.

## Mastery and regression

Events include ERROR_DETECTED, LESSON_VIEWED, EXERCISE_ATTEMPTED/CORRECT/INCORRECT, CONCEPT_REUSED, CONCEPT_MASTERED and CONCEPT_REGRESSED. Lesson events are day-deduplicated and do not grant mastery. Study-plan completion is adherence only, not assessment evidence or measured time.

Default mastery requires at least 20 assessed exercises, three distinct exercise sessions over at least two days, 85% accuracy in the latest 40 assessed exercises, and verified success in at least three later attempts with distinct contexts since the most recent error. Positive evidence is deliberately conservative: structured positive grader evidence, narrow validated constructions in graded transcripts, verified vocabulary usage, trusted Reading answers or explicit acoustic assessments. Generic absence of a reported error is insufficient. Two later affected attempts regress a mastered concept and restore its recommendation priority. Further supported improvement can qualify it again.

Thresholds, trend windows, decay and priority weights live in Settings as `LEARNING_*` environment variables. `LEARNING_PRIORITY_WEIGHTS` accepts a JSON object. Defaults are documented in `backend/app/core/config.py`; Docker Compose exposes the evidence, recency, trend and mastery thresholds; custom weight JSON can also be supplied to the backend environment.

## Plans and UI

`/learning/plan` creates 7/14/30-day plans at 15/25/40 minutes per day from the highest-priority active concepts. Each day has a short lesson/review and targeted practice or transfer. New plans archive existing plans. “Học hôm nay” combines today's pending plan activities with current recommendations (maximum two priority concepts). Daily dates use Asia/Ho_Chi_Minh. The deterministic seven-day review shows completed graded attempts, recorded exercise time, new/improving/mastered concepts and next priority. It does not invent time spent reading lessons.

History results link their normalized signals to concept detail pages. Practice setup, Progress and navigation link to Learning Analysis. The lesson/exercise pages include loading, empty, retry and authorization states.

An explicit weekly AI summary action uses only bounded structured counts, criterion averages and top priorities. It does not send learner sentences or audio. Recommendations validate their weakness references. The private result and exact analytics snapshot are stored in a versioned learning event and reused for the same profile revision/local date/model. Opening the dashboard never calls AI. New graded evidence invalidates this cache; generating a summary does not alter mastery.

## Exam separation and ownership

Weakness-focused generated questions are private to their user and carry `generation_diagnostics.learning_focus`. Shared bank queries exclude private rows. Full Writing exams reject focused questions; the targeted endpoint only creates individual Writing tasks, Speaking parts or Reading question-type practice. Full Reading generation rejects learning focus. Full exam workspaces are unchanged and expose no learning hints, vocabulary helper or corrective feedback while in progress.

Every lesson, exercise, signal, plan and evidence lookup is scoped by the authenticated user. Tables cascade on account deletion; the learning migration adds tables/indexes and preserves existing attempts and private library revisions. A follow-up migration widens Writing purpose descriptions to Text so valid AI output cannot overflow a legacy 100-character column.

## Main API

- `GET /api/v1/learning/overview|weaknesses|strengths|writing|speaking|reading|grammar|vocabulary|weekly|today`
- `POST /api/v1/learning/recalculate` — persisted background backfill state
- `GET /api/v1/learning/weaknesses/{id}` — exact evidence, trends, cached lesson
- `POST /api/v1/learning/weaknesses/{id}/lesson|practice|targeted-practice`
- `GET /api/v1/learning/exercises` and `GET /exercises/{id}`
- `POST /api/v1/learning/exercises/{id}/answer`
- `GET /api/v1/learning/attempts/{skill}/{attempt_id}`
- `POST /api/v1/learning/study-plan`, `GET /study-plan/current`, `PATCH /study-plan/items/{id}`
- `POST /api/v1/learning/vocabulary/reuses/{event_id}/answer` — verify actual recorded phrase usage
- `POST /api/v1/learning/weekly/summary` — cached Vietnamese AI review of structured analytics

Focused checks: `cd backend && .venv/bin/pytest -q tests/test_learning.py`. Optional real OpenAI check: `.venv/bin/python scripts/check_learning_live.py` (creates and cleans up one disposable account). Run migrations with `alembic upgrade head` before starting the updated backend.
