# Model evaluation — 2026-09-19

## Decision

**Selected Writing route: gpt-5.6-luna / medium, with conditional gpt-5.6-terra / none.** This is the cheapest tested conditional configuration that passed the unchanged development-set gates on two complete primary draws, each with new policy-1.5 reviews. These controlled replays are not a fresh end-to-end replication. Mini was evaluated, not forced to win. Terra is not called for every attempt.

The second-draw confirmation achieved MAE **0.337**, within ±0.5 **84.6%**, within ±1 **100.0%**, serious overscore **0.0%**, and validated final output **100.0%**. Mean measured cost was **$0.02990/task**, including primary calls, conditional reviews and retries. This is 87.0% below the user-reported $0.23 baseline, not an invoice comparison or a production cost guarantee. Optional feedback is additional.

Selection provenance: [selection.json](backend/app/evals/runs/selection.json). Local deployment status: **running locally; health and proxy verified**.

- Cheap helpers and question generation: **Luna / low**. Reading generation passed 3/3 checked sets versus Mini's 2/3. Numeric scoring/learning aggregation uses Python/PostgreSQL.
- Speaking text: **Mini / low with conditional Terra / none**. The resumed three-case probe completed, including correction of the previously inflated short answer. Real acoustic analysis remains separate.
- Corrections and example essays: pinned **Mini / low**, requested independently on demand. Detailed prose and vocabulary use Luna. Sol is not a default route.
- Terra / none was also the cheapest passing standalone model ($0.03126/task), but was not selected as the ordinary grader because the requested architecture reserves it for conditional reviews.

## Dataset and method

The frozen [13-sample dataset](backend/app/evals/data/writing-v1.json) covers weak, borderline, solid and strong Task 1/2 writing; short and repetitive long responses; strong task content with poor language; accurate language with weak task response; basic vocabulary and unnatural collocations. All labels are `internal_reference`, reviewer count zero. No teacher-rated samples were available. Labels were recorded before the experiments and have not been changed to make a configuration pass. The Alex regression reference is 5.875; no phrase-matched score rule exists.

All primary candidates use the same rubric, core schema/prompt 4.1.0 and 7,000-token output budget, including reasoning. Invalid structured output gets at most one retry; reviewer budget is 9,000 tokens. Sentence IDs retrieve verbatim original evidence in Python, and criterion scores are averaged deterministically. Reference scores, editorial rationales and full calibration anchor answers are withheld from all model requests.

This is a **development calibration set**, not an independent examiner validation study. Prompt/schema and routing rules were refined after inspecting its failures. Repeating these samples measures variability, not generalization. Passing 13 internal references does not establish population accuracy; an independently rated holdout remains necessary for stronger claims. Every failed run is retained rather than selectively removed.

Unchanged product gates: overall MAE ≤0.5; each criterion MAE ≤0.75; within ±0.5 ≥70%; within ±1 ≥90%; serious overscore (>1) ≤2%; final structured success ≥99%; at least 12 samples. These are configurable engineering targets, not official VSTEP requirements. On 13 samples, 9/13 = 69.2% fails the 70% gate and one serious overscore fails the 2% gate.

## Same-schema standalone comparison

All rows contain 13 samples. Over means error >+0.5; under means error <−0.5. Failed samples remain in rate denominators. MAE uses validated results; no valid result means undefined MAE, not zero error.

| Model / effort | Overall MAE | ±0.5 | ±1 | Over | Under | Over >1 | Signed | Final valid | Gate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| gpt-5.4-mini-2026-03-17 / low | 0.615 | 46.2% | 69.2% | 30.8% | 15.4% | 15.4% | 0.115 | 92.3% | FAIL |
| gpt-5.4-mini-2026-03-17 / medium | — | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | — | 0.0% | FAIL |
| gpt-5.4-mini-2026-03-17 / none | 0.602 | 53.8% | 69.2% | 15.4% | 15.4% | 15.4% | 0.080 | 84.6% | FAIL |
| gpt-5.6-luna / low | 0.490 | 53.8% | 84.6% | 38.5% | 7.7% | 15.4% | 0.260 | 100.0% | FAIL |
| gpt-5.6-luna / medium | 0.462 | 61.5% | 84.6% | 30.8% | 7.7% | 15.4% | 0.327 | 100.0% | FAIL |
| gpt-5.6-luna / none | 0.481 | 53.8% | 84.6% | 23.1% | 23.1% | 7.7% | 0.077 | 100.0% | FAIL |
| gpt-5.6-terra / low | 0.346 | 84.6% | 92.3% | 7.7% | 7.7% | 0.0% | 0.038 | 100.0% | PASS |
| gpt-5.6-terra / medium | 0.346 | 84.6% | 92.3% | 0.0% | 15.4% | 0.0% | -0.058 | 100.0% | PASS |
| gpt-5.6-terra / none | 0.356 | 84.6% | 92.3% | 7.7% | 7.7% | 0.0% | 0.087 | 100.0% | PASS |

| Model / effort | Task MAE | Organization MAE | Vocabulary MAE | Grammar MAE | Band agreement | Invalid outputs / calls |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| gpt-5.4-mini-2026-03-17 / low | 0.583 | 0.625 | 0.750 | 0.667 | 53.8% | 14.3% |
| gpt-5.4-mini-2026-03-17 / medium | — | — | — | — | 0.0% | 100.0% |
| gpt-5.4-mini-2026-03-17 / none | 0.545 | 0.682 | 0.545 | 0.636 | 61.5% | 26.7% |
| gpt-5.6-luna / low | 0.538 | 0.538 | 0.538 | 0.500 | 69.2% | 0.0% |
| gpt-5.6-luna / medium | 0.462 | 0.500 | 0.577 | 0.538 | 69.2% | 0.0% |
| gpt-5.6-luna / none | 0.538 | 0.462 | 0.538 | 0.462 | 76.9% | 0.0% |
| gpt-5.6-terra / low | 0.346 | 0.423 | 0.423 | 0.346 | 76.9% | 0.0% |
| gpt-5.6-terra / medium | 0.308 | 0.500 | 0.423 | 0.308 | 76.9% | 0.0% |
| gpt-5.6-terra / none | 0.385 | 0.385 | 0.423 | 0.385 | 84.6% | 0.0% |

Band agreement is an internal score bucket, not certification from one Writing task. Mini / medium exhausted the shared output budget on all samples, including retries; that configuration failed to return usable results. Earlier verbose-schema runs under `writing-v1/` are retained for audit and excluded from this schema 4.1 comparison.

## Observed standalone tokens and cost

Averages include retries. Latency sums provider request times, excluding queue time. Reasoning tokens are already part of output, never billed a second time. Cached tokens are measured, not assumed. Costs use standard estimated rates.

| Model / effort | Calls | Input | Cached | Output | Reasoning | Seconds | USD/task | USD/100 | USD/1,000 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| gpt-5.4-mini-2026-03-17 / low | 1.08 | 3456 | 2304 | 3425 | 500 | 22.3 | 0.01645 | 1.65 | 16.45 |
| gpt-5.4-mini-2026-03-17 / medium | 2.00 | 6482 | 4431 | 14000 | 13837 | 67.6 | 0.06487 | 6.49 | 64.87 |
| gpt-5.4-mini-2026-03-17 / none | 1.15 | 3696 | 2481 | 3116 | 0 | 14.7 | 0.01512 | 1.51 | 15.12 |
| gpt-5.6-luna / low | 1.00 | 3233 | 2147 | 2804 | 235 | 18.3 | 0.00362 | 0.36 | 3.62 |
| gpt-5.6-luna / medium | 1.00 | 3233 | 2147 | 3939 | 1387 | 29.0 | 0.00499 | 0.50 | 4.99 |
| gpt-5.6-luna / none | 1.00 | 3233 | 2147 | 2504 | 0 | 16.8 | 0.00327 | 0.33 | 3.27 |
| gpt-5.6-terra / low | 1.00 | 3233 | 2147 | 2716 | 367 | 31.2 | 0.03519 | 3.52 | 35.19 |
| gpt-5.6-terra / medium | 1.00 | 3233 | 2147 | 3411 | 1020 | 40.3 | 0.04354 | 4.35 | 43.54 |
| gpt-5.6-terra / none | 1.00 | 3233 | 1952 | 2359 | 0 | 23.3 | 0.03126 | 3.13 | 31.26 |

## Conditional routing experiments

Policies 1.1–1.3 added evidence checks for dense errors, thin structure range, basic cohesion at high scores, exceptional scores with short evidence and task/language divergence. Policy **1.4** added primary evidence/scores and independent-criterion instructions, but its fresh confirmation still penalized task failure across unrelated criteria. Policy **1.5** withholds primary scores to reduce anchoring, explicitly permits rejecting incorrect primary evidence, and distinguishes task omissions from actual language/coherence faults. Weak task completion alone must not drag down accurate grammar or logical organization. These checks request review; they never subtract fixed points or impose sample-specific scores.

Fresh runs obtain new primary outputs and reviews. **Replay** fixes every primary result from an identified completed run and makes new conditional review calls only. It controls primary variability and saves API spend, but is not a fresh end-to-end replication. Full-route cost/latency includes original primary measurements; new spend below counts only newly requested reviews. The actual usage ledger does not charge replayed calls again. Sample subsets are not allowed.

| Run / primary | Policy / Terra effort | Mode | MAE | ±0.5 | ±1 | Over >1 | Escalated | USD/task | New USD | Gate |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| [writing-routed](backend/app/evals/runs/writing-routed/gpt-5.4-mini-2026-03-17-low-routed-low.json) / gpt-5.4-mini-2026-03-17 low | 1.1.0 / low | fresh | 0.413 | 61.5% | 92.3% | 7.7% | 15.4% | 0.02489 | 0.3236 | FAIL |
| [writing-routed](backend/app/evals/runs/writing-routed/gpt-5.6-luna-low-routed-low.json) / gpt-5.6-luna low | 1.1.0 / low | fresh | 0.337 | 84.6% | 84.6% | 7.7% | 38.5% | 0.01741 | 0.2264 | FAIL |
| [writing-routed-context](backend/app/evals/runs/writing-routed-context/gpt-5.6-luna-low-routed-none.json) / gpt-5.6-luna low | 1.4.0 / none | replay | 0.433 | 69.2% | 92.3% | 0.0% | 46.2% | 0.02023 | 0.2162 | FAIL |
| [writing-routed-context-medium](backend/app/evals/runs/writing-routed-context-medium/gpt-5.6-luna-medium-routed-none.json) / gpt-5.6-luna medium | 1.4.0 / none | replay | 0.346 | 76.9% | 100.0% | 0.0% | 53.8% | 0.02325 | 0.2374 | PASS |
| [writing-routed-context-mini](backend/app/evals/runs/writing-routed-context-mini/gpt-5.4-mini-2026-03-17-low-routed-none.json) / gpt-5.4-mini-2026-03-17 low | 1.4.0 / none | replay | 0.423 | 69.2% | 100.0% | 0.0% | 46.2% | 0.03336 | 0.2198 | FAIL |
| [writing-routed-independent-a](backend/app/evals/runs/writing-routed-independent-a/gpt-5.6-luna-medium-routed-none.json) / gpt-5.6-luna medium | 1.5.0 / none | replay | 0.356 | 76.9% | 100.0% | 0.0% | 53.8% | 0.02343 | 0.2397 | PASS |
| [writing-routed-independent-b](backend/app/evals/runs/writing-routed-independent-b/gpt-5.6-luna-medium-routed-none.json) / gpt-5.6-luna medium | 1.5.0 / none | replay | 0.337 | 84.6% | 100.0% | 0.0% | 69.2% | 0.02990 | 0.3249 | PASS |
| [writing-routed-none](backend/app/evals/runs/writing-routed-none/gpt-5.6-luna-none-routed-none.json) / gpt-5.6-luna none | 1.3.0 / none | replay | 0.471 | 69.2% | 92.3% | 0.0% | 30.8% | 0.01173 | 0.1101 | FAIL |
| [writing-routed-resumed](backend/app/evals/runs/writing-routed-resumed/gpt-5.6-luna-low-routed-none.json) / gpt-5.6-luna low | 1.3.0 / none | fresh | 0.442 | 69.2% | 92.3% | 0.0% | 46.2% | 0.01750 | 0.2275 | FAIL |
| [writing-routed-resumed-low](backend/app/evals/runs/writing-routed-resumed-low/gpt-5.6-luna-low-routed-low.json) / gpt-5.6-luna low | 1.3.0 / low | replay | 0.433 | 69.2% | 92.3% | 0.0% | 46.2% | 0.01904 | 0.2008 | FAIL |
| [writing-routed-v12](backend/app/evals/runs/writing-routed-v12/gpt-5.4-mini-2026-03-17-low-routed-none.json) / gpt-5.4-mini-2026-03-17 low | 1.2.0 / none | fresh | 0.688 | 23.1% | 38.5% | 0.0% | 69.2% | incomplete | 0.1414 | PROVIDER LIMIT |
| [writing-routed-v12](backend/app/evals/runs/writing-routed-v12/gpt-5.6-luna-low-routed-none.json) / gpt-5.6-luna low | 1.2.0 / none | fresh | 0.452 | 69.2% | 84.6% | 15.4% | 23.1% | 0.01042 | 0.1354 | FAIL |
| [writing-routed-v13](backend/app/evals/runs/writing-routed-v13/gpt-5.4-mini-2026-03-17-low-routed-none.json) / gpt-5.4-mini-2026-03-17 low | 1.3.0 / none | fresh | 0.667 | 7.7% | 15.4% | 0.0% | 100.0% | incomplete | 0.0875 | PROVIDER LIMIT |
| [writing-routed-v13](backend/app/evals/runs/writing-routed-v13/gpt-5.6-luna-low-routed-none.json) / gpt-5.6-luna low | 1.3.0 / none | fresh | 0.562 | 7.7% | 15.4% | 0.0% | 100.0% | incomplete | 0.0515 | PROVIDER LIMIT |
| [writing-selected-confirmation](backend/app/evals/runs/writing-selected-confirmation/gpt-5.6-luna-medium-routed-none.json) / gpt-5.6-luna medium | 1.4.0 / none | fresh | 0.365 | 69.2% | 100.0% | 0.0% | 69.2% | 0.03029 | 0.3938 | FAIL |

Selected second-draw run criterion MAE: Task 0.462, Organization 0.423, Vocabulary 0.385, Grammar 0.231. Signed error -0.048; band agreement 76.9%. Average 1.69 requests, 7084 input / 3906 cached / 5581 output / 1246 reasoning tokens, 51.6s provider latency. USD/100 = 2.99; USD/1,000 = 29.90. Reviews occurred in 69.2% of this deliberately varied small set; that is not a measured production escalation rate.

Provider/network/quota failures never trigger a second model as if they were scoring uncertainty. Confirmed quota exhaustion stops subsequent candidates. The old [credit checkpoint](backend/app/evals/runs/credit-checkpoint.json) records the earlier $5.2002 known-spend total and 21 evaluation runs; it is not the current cumulative total.

The [completed ledger checkpoint](backend/app/evals/runs/completed-checkpoint.json) records $7.4859 total known evaluation spend, including $2.2857 after credit was replenished, and 30 stored Writing runs. 66 historical evaluation requests lack a known cost; they are not counted as free. Replayed primary calls do not create duplicate usage charges.

## Reading and Speaking

Reading used the same schema/content/evidence/distractor gates and fixed Mini / low reviewer for both generators. Cases: five inference questions, five attitude questions and one mixed ten-question passage. Luna passed 3/3 and Mini 2/3; mean complete cost including validation/retries was $0.00860 versus $0.02982. These are three generated sets with AI review, not teacher-rated validation. Publication gates and bank persistence remain intact; Reading scoring uses no LLM. [Artifacts](backend/app/evals/runs/reading-generation.json).

The resumed [Speaking transcript probe](backend/app/evals/runs/speaking-text-resumed.json) completed all three internal cases. Grammar/vocabulary/structures MAE was 0.500/0.333/0.667. One short, simple response triggered Terra review: primary 8/7.5/8 became 7/6.5/7 against references 6.5/6/6.5. All results kept pronunciation, fluency and overall null without audio. Total probe cost was $0.07299 including a structured-output retry. This limited text/routing check does not validate full Speaking exams or acoustic quality; the real audio path remains unchanged.

## Functional verification and delivery

The implementation has operation-specific routes; per-call tokens/cost/status/latency; an admin cost dashboard; independent lazy feedback; durable content/artifact caches and advisory locks; grading/version history; learning integration; separate teacher references; and JSON/database benchmark records. Migration `9534fb5bce3b` is additive. The dashboard at `/internal/ai-costs` requires an authenticated email in `AI_COST_ADMIN_EMAILS` or the existing calibration-admin allowlist.

The [selected-route live walkthrough](backend/app/evals/runs/routed-flow-selected.json) passed 9 targeted checks: initial core-only grading, repeated-grade and cross-attempt content reuse, independent lazy corrected text and cache, unchanged scores, admin denial/allowlisting, per-attempt cost ledger and learning integration. It used a disposable account; removal preserved anonymized evaluation metering. This verifies the integration, not examiner accuracy.

No generic unit/integration/E2E suite was added or run, as requested. No interactive browser/microphone validation was performed. Deployment and current verification evidence, when complete, is recorded in selection.json and PROJECT_STATUS.md.

## Pricing and reproducibility

USD/million tokens (input / cached / output), verified 2026-09-19: [Luna](https://developers.openai.com/api/docs/models/gpt-5.6-luna) 0.20 / 0.02 / 1.20; [Mini](https://developers.openai.com/api/docs/models/gpt-5.4-mini) 0.75 / 0.075 / 4.50; [Terra](https://developers.openai.com/api/docs/models/gpt-5.6-terra) 2 / 0.20 / 12. The ledger separately prices [audio](https://developers.openai.com/api/docs/models/gpt-audio) and [transcription](https://developers.openai.com/api/docs/pricing). Unknown prices or absent usage remain null, excluded from known subtotals. Use OPENAI_PRICE_OVERRIDES for changed rates.

Mini uses pinned snapshot `gpt-5.4-mini-2026-03-17`. The inspected Luna/Terra documentation listed no separate dated snapshot; configurable aliases require reevaluation when behavior changes. Core/grader version is 4.1.0, latest escalation policy 1.5.0. Raw runs store dataset hashes, models, efforts, versions, source provenance and exact measurements. The selected routing version is recorded in selection.json. [Commands and configuration](docs/ai-operations.md).
