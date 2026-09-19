"""Render saved benchmark evidence without making API calls or changing references."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
RUNS = Path(__file__).parent / "runs"


def read(path):
    return json.loads(path.read_text())


def number(value, places=3):
    return "—" if value is None else f"{value:.{places}f}"


def artifact(path):
    return path.relative_to(ROOT).as_posix()


def quality_row(label, run):
    m = run["metrics"]
    return (
        f"| {label} | {number(m['overall_mae'])} | {m['within_half_rate']:.1%} | "
        f"{m['within_one_rate']:.1%} | {m['overscore_rate']:.1%} | {m['underscore_rate']:.1%} | "
        f"{m['serious_overscore_rate']:.1%} | {number(m['mean_signed_error'])} | "
        f"{m['structured_success_rate']:.1%} | {'PASS' if m['quality_pass'] else 'FAIL'} |"
    )


def main():
    matrix = [read(p) for p in sorted((RUNS / "writing-v1-compact").glob("*.json"))]
    routed = [
        (p, read(p))
        for p in sorted(RUNS.glob("writing-*/*.json"))
        if "routed" in p.parent.name or "selected" in p.parent.name
    ]
    selection_path = RUNS / "selection.json"
    selection = read(selection_path) if selection_path.exists() else None
    lines = ["# Model evaluation — 2026-09-19", "", "## Decision", ""]
    if selection:
        confirmation = read(ROOT / selection["confirmation"])
        m = confirmation["metrics"]
        assert m["quality_pass"] and m["cost_fully_metered"]
        lines += [
            f"**Selected Writing route: {selection['model']} / {selection['effort']}, with conditional {selection['escalation_model']} / {selection['escalation_effort']}.** This is the cheapest tested conditional configuration that passed the unchanged development-set gates on two complete primary draws, each with new policy-1.5 reviews. These controlled replays are not a fresh end-to-end replication. Mini was evaluated, not forced to win. Terra is not called for every attempt.",
            "",
            f"The second-draw confirmation achieved MAE **{m['overall_mae']:.3f}**, within ±0.5 **{m['within_half_rate']:.1%}**, within ±1 **{m['within_one_rate']:.1%}**, serious overscore **{m['serious_overscore_rate']:.1%}**, and validated final output **{m['structured_success_rate']:.1%}**. Mean measured cost was **${m['avg_cost_usd']:.5f}/task**, including primary calls, conditional reviews and retries. This is {1 - m['avg_cost_usd'] / 0.23:.1%} below the user-reported $0.23 baseline, not an invoice comparison or a production cost guarantee. Optional feedback is additional.",
            "",
            f"Selection provenance: [selection.json]({artifact(selection_path)}). Local deployment status: **{selection.get('deployment_status', 'not yet deployed')}**.",
        ]
    else:
        lines += [
            "**No confirmed configuration has been selected for rollout yet.** API credit is available again and the resumed runs below supersede the old quota-blocked checkpoint. A passing review-policy comparison is checked against a second complete primary draw before changing the running application. The policy-1.4 fresh confirmation failed and is retained below.",
        ]
    lines += [
        "",
        "- Cheap helpers and question generation: **Luna / low**. Reading generation passed 3/3 checked sets versus Mini's 2/3. Numeric scoring/learning aggregation uses Python/PostgreSQL.",
        "- Speaking text: **Mini / low with conditional Terra / none**. The resumed three-case probe completed, including correction of the previously inflated short answer. Real acoustic analysis remains separate.",
        "- Corrections and example essays: pinned **Mini / low**, requested independently on demand. Detailed prose and vocabulary use Luna. Sol is not a default route.",
        "- Terra / none was also the cheapest passing standalone model ($0.03126/task), but was not selected as the ordinary grader because the requested architecture reserves it for conditional reviews.",
        "",
        "## Dataset and method",
        "",
        "The frozen [13-sample dataset](backend/app/evals/data/writing-v1.json) covers weak, borderline, solid and strong Task 1/2 writing; short and repetitive long responses; strong task content with poor language; accurate language with weak task response; basic vocabulary and unnatural collocations. All labels are `internal_reference`, reviewer count zero. No teacher-rated samples were available. Labels were recorded before the experiments and have not been changed to make a configuration pass. The Alex regression reference is 5.875; no phrase-matched score rule exists.",
        "",
        "All primary candidates use the same rubric, core schema/prompt 4.1.0 and 7,000-token output budget, including reasoning. Invalid structured output gets at most one retry; reviewer budget is 9,000 tokens. Sentence IDs retrieve verbatim original evidence in Python, and criterion scores are averaged deterministically. Reference scores, editorial rationales and full calibration anchor answers are withheld from all model requests.",
        "",
        "This is a **development calibration set**, not an independent examiner validation study. Prompt/schema and routing rules were refined after inspecting its failures. Repeating these samples measures variability, not generalization. Passing 13 internal references does not establish population accuracy; an independently rated holdout remains necessary for stronger claims. Every failed run is retained rather than selectively removed.",
        "",
        "Unchanged product gates: overall MAE ≤0.5; each criterion MAE ≤0.75; within ±0.5 ≥70%; within ±1 ≥90%; serious overscore (>1) ≤2%; final structured success ≥99%; at least 12 samples. These are configurable engineering targets, not official VSTEP requirements. On 13 samples, 9/13 = 69.2% fails the 70% gate and one serious overscore fails the 2% gate.",
        "",
        "## Same-schema standalone comparison",
        "",
        "All rows contain 13 samples. Over means error >+0.5; under means error <−0.5. Failed samples remain in rate denominators. MAE uses validated results; no valid result means undefined MAE, not zero error.",
        "",
        "| Model / effort | Overall MAE | ±0.5 | ±1 | Over | Under | Over >1 | Signed | Final valid | Gate |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    lines += [quality_row(f"{r['model']} / {r['reasoning_effort']}", r) for r in matrix]
    lines += [
        "",
        "| Model / effort | Task MAE | Organization MAE | Vocabulary MAE | Grammar MAE | Band agreement | Invalid outputs / calls |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for r in matrix:
        m = r["metrics"]
        criteria = " | ".join(number(v) for v in m["criterion_mae"].values())
        lines.append(
            f"| {r['model']} / {r['reasoning_effort']} | {criteria} | {m['band_agreement']:.1%} | {m['invalid_output_rate']:.1%} |"
        )
    lines += [
        "",
        "Band agreement is an internal score bucket, not certification from one Writing task. Mini / medium exhausted the shared output budget on all samples, including retries; that configuration failed to return usable results. Earlier verbose-schema runs under `writing-v1/` are retained for audit and excluded from this schema 4.1 comparison.",
        "",
        "## Observed standalone tokens and cost",
        "",
        "Averages include retries. Latency sums provider request times, excluding queue time. Reasoning tokens are already part of output, never billed a second time. Cached tokens are measured, not assumed. Costs use standard estimated rates.",
        "",
        "| Model / effort | Calls | Input | Cached | Output | Reasoning | Seconds | USD/task | USD/100 | USD/1,000 |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for r in matrix:
        m = r["metrics"]
        lines.append(
            f"| {r['model']} / {r['reasoning_effort']} | {m['avg_requests']:.2f} | {m['avg_input_tokens']:.0f} | {m['avg_cached_input_tokens']:.0f} | {m['avg_output_tokens']:.0f} | {m['avg_reasoning_tokens']:.0f} | {m['avg_latency_ms'] / 1000:.1f} | {m['avg_cost_usd']:.5f} | {m['cost_per_100']:.2f} | {m['cost_per_1000']:.2f} |"
        )
    lines += [
        "",
        "## Conditional routing experiments",
        "",
        "Policies 1.1–1.3 added evidence checks for dense errors, thin structure range, basic cohesion at high scores, exceptional scores with short evidence and task/language divergence. Policy **1.4** added primary evidence/scores and independent-criterion instructions, but its fresh confirmation still penalized task failure across unrelated criteria. Policy **1.5** withholds primary scores to reduce anchoring, explicitly permits rejecting incorrect primary evidence, and distinguishes task omissions from actual language/coherence faults. Weak task completion alone must not drag down accurate grammar or logical organization. These checks request review; they never subtract fixed points or impose sample-specific scores.",
        "",
        "Fresh runs obtain new primary outputs and reviews. **Replay** fixes every primary result from an identified completed run and makes new conditional review calls only. It controls primary variability and saves API spend, but is not a fresh end-to-end replication. Full-route cost/latency includes original primary measurements; new spend below counts only newly requested reviews. The actual usage ledger does not charge replayed calls again. Sample subsets are not allowed.",
        "",
        "| Run / primary | Policy / Terra effort | Mode | MAE | ±0.5 | ±1 | Over >1 | Escalated | USD/task | New USD | Gate |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for p, r in routed:
        if "metrics" not in r:
            continue
        m = r["metrics"]
        v = r["versions"]
        name = f"[{p.parent.name}]({artifact(p)}) / {r['model'].split('+')[0]} {r['reasoning_effort']}"
        mode = "replay" if r.get("primary_replay_run_id") else "fresh"
        cost = f"{m['avg_cost_usd']:.5f}" if m["cost_fully_metered"] else "incomplete"
        incremental = m.get(
            "new_known_cost_usd",
            sum(c.get("estimated_cost_usd") or 0 for row in r["results"] for c in row["calls"]),
        )
        provider_limited = r.get("blocked_reason") or any(
            c["status"] == "http_429" for row in r["results"] for c in row["calls"]
        )
        gate = "PROVIDER LIMIT" if provider_limited else "PASS" if m["quality_pass"] else "FAIL"
        lines.append(
            f"| {name} | {v.get('escalation', '—')} / {v.get('escalation_effort', '—')} | {mode} | {number(m['overall_mae'])} | {m['within_half_rate']:.1%} | {m['within_one_rate']:.1%} | {m['serious_overscore_rate']:.1%} | {m['escalation_rate']:.1%} | {cost} | {incremental:.4f} | {gate} |"
        )
    if selection:
        m = confirmation["metrics"]
        lines += [
            "",
            f"Selected second-draw run criterion MAE: Task {m['criterion_mae']['task_fulfillment']:.3f}, Organization {m['criterion_mae']['organization']:.3f}, Vocabulary {m['criterion_mae']['vocabulary']:.3f}, Grammar {m['criterion_mae']['grammar']:.3f}. Signed error {m['mean_signed_error']:+.3f}; band agreement {m['band_agreement']:.1%}. Average {m['avg_requests']:.2f} requests, {m['avg_input_tokens']:.0f} input / {m['avg_cached_input_tokens']:.0f} cached / {m['avg_output_tokens']:.0f} output / {m['avg_reasoning_tokens']:.0f} reasoning tokens, {m['avg_latency_ms'] / 1000:.1f}s provider latency. USD/100 = {m['cost_per_100']:.2f}; USD/1,000 = {m['cost_per_1000']:.2f}. Reviews occurred in {m['escalation_rate']:.1%} of this deliberately varied small set; that is not a measured production escalation rate.",
        ]
    lines += [
        "",
        "Provider/network/quota failures never trigger a second model as if they were scoring uncertainty. Confirmed quota exhaustion stops subsequent candidates. The old [credit checkpoint](backend/app/evals/runs/credit-checkpoint.json) records the earlier $5.2002 known-spend total and 21 evaluation runs; it is not the current cumulative total.",
    ]
    checkpoint_path = RUNS / "completed-checkpoint.json"
    if checkpoint_path.exists():
        checkpoint = read(checkpoint_path)
        lines += [
            "",
            f"The [completed ledger checkpoint]({artifact(checkpoint_path)}) records ${checkpoint['known_evaluation_spend_usd']:.4f} total known evaluation spend, including ${checkpoint['additional_known_spend_since_credit_checkpoint_usd']:.4f} after credit was replenished, and {checkpoint['stored_evaluation_runs']} stored Writing runs. {checkpoint['evaluation_calls_with_unknown_cost']} historical evaluation requests lack a known cost; they are not counted as free. Replayed primary calls do not create duplicate usage charges.",
        ]
    lines += [
        "",
        "## Reading and Speaking",
        "",
        "Reading used the same schema/content/evidence/distractor gates and fixed Mini / low reviewer for both generators. Cases: five inference questions, five attitude questions and one mixed ten-question passage. Luna passed 3/3 and Mini 2/3; mean complete cost including validation/retries was $0.00860 versus $0.02982. These are three generated sets with AI review, not teacher-rated validation. Publication gates and bank persistence remain intact; Reading scoring uses no LLM. [Artifacts](backend/app/evals/runs/reading-generation.json).",
        "",
        "The resumed [Speaking transcript probe](backend/app/evals/runs/speaking-text-resumed.json) completed all three internal cases. Grammar/vocabulary/structures MAE was 0.500/0.333/0.667. One short, simple response triggered Terra review: primary 8/7.5/8 became 7/6.5/7 against references 6.5/6/6.5. All results kept pronunciation, fluency and overall null without audio. Total probe cost was $0.07299 including a structured-output retry. This limited text/routing check does not validate full Speaking exams or acoustic quality; the real audio path remains unchanged.",
        "",
        "## Functional verification and delivery",
        "",
        "The implementation has operation-specific routes; per-call tokens/cost/status/latency; an admin cost dashboard; independent lazy feedback; durable content/artifact caches and advisory locks; grading/version history; learning integration; separate teacher references; and JSON/database benchmark records. Migration `9534fb5bce3b` is additive. The dashboard at `/internal/ai-costs` requires an authenticated email in `AI_COST_ADMIN_EMAILS` or the existing calibration-admin allowlist.",
    ]
    flow_path = RUNS / "routed-flow-selected.json"
    if flow_path.exists():
        flow = read(flow_path)
        lines += [
            "",
            f"The [selected-route live walkthrough]({artifact(flow_path)}) passed {len(flow['checks'])} targeted checks: initial core-only grading, repeated-grade and cross-attempt content reuse, independent lazy corrected text and cache, unchanged scores, admin denial/allowlisting, per-attempt cost ledger and learning integration. It used a disposable account; removal preserved anonymized evaluation metering. This verifies the integration, not examiner accuracy.",
        ]
    else:
        lines += [
            "",
            "The earlier [Mini walkthrough](backend/app/evals/runs/routed-flow.json) verified caching, lazy corrections, unchanged scores, admin authorization, costs and learning integration. It is not a selected-route confirmation.",
        ]
    lines += [
        "",
        "No generic unit/integration/E2E suite was added or run, as requested. No interactive browser/microphone validation was performed. Deployment and current verification evidence, when complete, is recorded in selection.json and PROJECT_STATUS.md.",
        "",
        "## Pricing and reproducibility",
        "",
        "USD/million tokens (input / cached / output), verified 2026-09-19: [Luna](https://developers.openai.com/api/docs/models/gpt-5.6-luna) 0.20 / 0.02 / 1.20; [Mini](https://developers.openai.com/api/docs/models/gpt-5.4-mini) 0.75 / 0.075 / 4.50; [Terra](https://developers.openai.com/api/docs/models/gpt-5.6-terra) 2 / 0.20 / 12. The ledger separately prices [audio](https://developers.openai.com/api/docs/models/gpt-audio) and [transcription](https://developers.openai.com/api/docs/pricing). Unknown prices or absent usage remain null, excluded from known subtotals. Use OPENAI_PRICE_OVERRIDES for changed rates.",
        "",
        "Mini uses pinned snapshot `gpt-5.4-mini-2026-03-17`. The inspected Luna/Terra documentation listed no separate dated snapshot; configurable aliases require reevaluation when behavior changes. Core/grader version is 4.1.0, latest escalation policy 1.5.0. Raw runs store dataset hashes, models, efforts, versions, source provenance and exact measurements. The selected routing version is recorded in selection.json. [Commands and configuration](docs/ai-operations.md).",
    ]
    (ROOT / "MODEL_EVALUATION.md").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
