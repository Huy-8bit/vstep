# AI routing, metering and operations

All model calls pass through the operation registry in `backend/app/llm/routing.py` or the existing speech provider. `OPENAI_MODEL` is retained only as a legacy settings field; it no longer silently overrides every operation. Model and reasoning choices are environment configurable. See [benchmark evidence](../MODEL_EVALUATION.md) for the selected configuration and its limits.

Selected defaults: Writing uses Luna with `OPENAI_REASONING_WRITING=medium`; Speaking text and question-quality review use pinned Mini with `OPENAI_REASONING_GRADING=low`; conditional Terra reviews use `OPENAI_REASONING_ESCALATION=none`. Other helpers default to low. `OPENAI_REASONING_OVERRIDES` can override individual operations; changes need reevaluation. Keep Writing core and calibration identities equal to retain the single-call normal path. Routing model version is `2026-09-19-routing-v2`.

## Operation inventory

| Operation | Work and routing role | When it runs |
| --- | --- | --- |
| `generate_question`, `speaking_question` | Luna generation | Explicit generation or bank shortage; existing format/quality checks and bank persistence retained |
| `reading_generate` | Luna generation | Same; answer keys, option explanations and evidence saved with the passage |
| `question_quality` | Independent Mini review | Existing semantic format/content gate; failing candidates are not published |
| `question_import` | Configurable Mini | User requests extraction from text/image/PDF |
| `writing_core` | Combined evidence + four criterion scores | Once per uncached original question/answer |
| `writing_escalation` | Conditional Terra review | Evidence conflicts, uncertain boundaries/task coverage, low confidence, long uncertain answers, invalid primary output |
| `writing_calibration` | Optional separate scoring override | Only if its model/effort differs from the core route; default shares the single core call |
| `writing_feedback`, `writing_sentences`, `writing_corrected`, `writing_improved` | Luna detail prose; Mini corrections/examples | Explicit independent user action; stored artifacts reused |
| `vocabulary_coach`, `vocabulary_usage`, `reading_vocabulary` | Luna | Requested recommendations/explanations or concept-only practice assessment |
| `learning_lesson`, `learning_exercises`, `learning_feedback`, `learning_weekly_summary` | Luna | Requested learning content; numeric aggregation stays in Python/SQL |
| `speaking_grade`, `speaking_escalation` | Mini text, conditional Terra | Original transcripts only; no acoustic scores in the text schema |
| Speech transcription, acoustic analysis, TTS | Existing separately configured providers/models | Actual recordings or requested cached reference audio |
| `writing_shadow` | Optional Terra comparison | Development only, disabled by default, deterministic 5% sample when enabled |

The old normal Writing path could perform analysis, calibration, calibration retry, feedback, vocabulary and corrections in separate calls. The result page now sends one grading request. Successful normal grading contains scores, exact-source evidence, representative errors, three priorities and a brief summary. No essays or vocabulary batch are eagerly generated. Invalid structured output has one bounded retry; every returned provider response, including rejected output, is metered.

Reading answer comparison, score means, word counts, content hashing, weakness counts, trends and priorities use Python/PostgreSQL. Normal Reading submission calls no model.

## Cache and versions

Writing cache identity includes the full question/context, original answer, model and reasoning identities, grader/core-prompt/model versions, temperature and escalation configuration/version. Reuse is limited to the owning account. PostgreSQL advisory locks cover both attempt and content identity, so concurrent identical attempts can share a completed core snapshot. Published historical grades stay immutable until an explicit version upgrade; old snapshots remain in grading history.

Optional artifacts have independent kind/content/model/effort/version keys and locks. Requesting the corrected essay never generates the B2 example. Repeating a request reuses its artifact. Vocabulary, Reading vocabulary, lessons and weekly summaries include their relevant model/effort identity. Paid calls can still recur if a process dies after the provider responds but before persistence; there is no distributed exactly-once provider contract.

Static instructions/rubric/schema precede question/answer JSON to permit provider prompt-prefix caching. Actual cached token counts are recorded; a warm-cache saving is never assumed for a cold request. Output budgets are operation-specific and include reasoning tokens. The benchmark records truncation failures rather than increasing budgets without measuring the cost.

## Cost view

Set `AI_COST_ADMIN_EMAILS` to the authenticated admin email(s), then open `/internal/ai-costs`. The existing `WRITING_CALIBRATION_ADMIN_EMAILS` allowlist is also recognized. Both default to empty; API authorization is enforced independently of navigation visibility.

The default reporting day is midnight in `Asia/Ho_Chi_Minh`; 7/30-day views are available. Categories separate Writing core, optional feedback, Speaking/audio/transcription, generation, vocabulary, learning, evaluation and shadow. The view lists model/operation counts, input/cache/output/reasoning tokens and per-attempt request ledgers. Average Writing cost uses distinct attempts with a metered core request; cache-only attempts are not charged and are not in that denominator.

`ai_usage_logs` records operation, actual response model, effort, user, attempt/session, evaluation ID, timestamp, status, latency, usage and estimated USD. Audio and transcript work is attributed to its Speaking session; pronunciation practice uses its practice ID. Evaluation costs are separated from product spend. Account deletion anonymizes the user reference and retains the ledger. Legacy rows have unknown cost; no retroactive fictitious totals are inserted.

Rates use standard USD per million tokens, with cached input separated. Output usage already includes reasoning: it is never counted twice. Token-based audio pricing uses the provider's audio/text breakdown. If usage is absent (including binary TTS responses), or a model's rate is unknown, cost is `null`, visibly excluded from the known subtotal. This is an estimate, not an invoice reconciliation. `OPENAI_PRICE_OVERRIDES` accepts a JSON map of model rates (`input`, `cached`, `output`, optional `audio_input`/`audio_output`).

## Calibration and human review

From `backend`, after configuring the real API key and migrated PostgreSQL:

```bash
.venv/bin/python -m app.evals.writing_models --efforts low,none,medium --concurrency 3 --output app/evals/runs/comparison
.venv/bin/python -m app.evals.writing_models --models gpt-5.6-luna --efforts medium --escalation-model gpt-5.6-terra --escalation-effort none --output app/evals/runs/routed-new
.venv/bin/python -m app.evals.reading_models
```

These commands make paid real API calls. Reference scores, source labels and editorial rationales are withheld from candidates. They all receive the same core rubric/schema. Complete Writing runs persist in `grading_model_evaluations` and JSON; interrupted runs remain visibly incomplete. `--resume` reuses only matching dataset/prompt/routing versions. A model-baseline reference can be compared, but cannot qualify a production selection. Do not loosen thresholds merely to approve a cheaper route.

For a controlled comparison of review policies, add `--primary-replay <completed-run.json>` with the same primary model/effort. It requires every sample and matching dataset/core prompt, reuses measured primary outputs (including genuine invalid-output failures), and calls the reviewer only when the current policy flags evidence. Provider/quota failures cannot be replayed as model errors. Full-route metrics include original primary costs and latency; `new_provider_requests` and `new_known_cost_usd` identify incremental spending. This is a review-policy comparison, not an independent end-to-end replication. Quota exhaustion stops subsequent candidates.

Writing policy 1.5 gives Terra the original answer, named conflicts and the primary model's fallible observations, while withholding primary scores to reduce anchoring. It explicitly permits rejecting faulty observations and requires independent criterion judgments, so weak task completion does not automatically reduce grammar, vocabulary or organization. Neither primary nor reference scores enter this review payload. Score adjustments remain model judgments supported by source evidence, not fixed error-count penalties.

Additional purpose-specific checks accept separate output paths to preserve earlier evidence:

```bash
.venv/bin/python -m app.evals.speaking_text --output app/evals/runs/speaking-text-new.json
.venv/bin/python scripts/check_routed_grading.py --output app/evals/runs/routed-flow-new.json
```

The Speaking probe uses three internal transcripts and checks that absent audio never creates acoustic scores. The cost/cache walkthrough creates and removes its own disposable account, retaining anonymized usage. Neither is a general test suite or a substitute for examiner-rated validation.

Authenticated admin `POST /api/v1/internal/ai-costs/human-references/{attempt_id}` accepts `task_fulfillment`, `organization`, `vocabulary`, `grammar`, `overall` and review `notes`. It stores a separate human reference and reviewer provenance without overwriting AI scores. Run `writing_models --human-db` to evaluate exclusively against complete stored human references; it fails explicitly when there are none. Exported human datasets/results contain learner work: keep them in private storage, not a public repository.

Configurable product targets: `EVAL_OVERALL_MAE_MAX`, `EVAL_CRITERION_MAE_MAX`, `EVAL_WITHIN_HALF_MIN`, `EVAL_WITHIN_ONE_MIN`, `EVAL_SERIOUS_OVERSCORE_MAX`, `EVAL_STRUCTURED_SUCCESS_MIN`, `EVAL_MIN_SAMPLES`. These are product thresholds, not official VSTEP requirements. New human evidence takes priority over editorial estimates.
