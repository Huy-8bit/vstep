"""Run a real, blind model calibration benchmark: python -m app.evals.writing_models."""

import argparse
import asyncio
import copy
import hashlib
import json
import statistics
from collections import Counter
from pathlib import Path
from uuid import uuid4

from sqlalchemy import select

from app.common.errors import AppError
from app.common.words import count_words
from app.core.config import settings
from app.db.base import utcnow
from app.db.session import SessionLocal, engine
from app.llm.openai_client import OpenAILLMClient
from app.llm.usage import PRICE_VERSION, ai_context
from app.models import WritingCalibrationSample
from app.models.evaluation import GradingModelEvaluation
from app.prompts.writing_core import WRITING_CORE_VERSION
from app.schemas.writing_assessment import CRITERIA
from app.services.grading_escalation_service import ESCALATION_VERSION, GradingEscalationService
from app.services.writing_core_service import WritingCoreService
from app.vstep_reference.scoring_reference import writing_reference_level

DEFAULT_DATASET = Path(__file__).parent / "data/writing-v1.json"


def thresholds():
    return {
        "overall_mae_max": settings.eval_overall_mae_max,
        "criterion_mae_max": settings.eval_criterion_mae_max,
        "within_half_min": settings.eval_within_half_min,
        "within_one_min": settings.eval_within_one_min,
        "serious_overscore_max": settings.eval_serious_overscore_max,
        "structured_success_min": settings.eval_structured_success_min,
        "min_samples": settings.eval_min_samples,
    }


def evaluate_metrics(rows):
    n = len(rows)
    valid = [r for r in rows if r.get("scores")]
    diffs = [r["scores"]["overall"] - r["reference"]["overall"] for r in valid]

    def mean(values):
        return statistics.mean(values) if values else None

    calls = [c for r in rows for c in r["calls"]]
    cost_known = all(c["estimated_cost_usd"] is not None for c in calls) and bool(calls)
    # Preserve partial known spend while explicitly flagging incomplete metering.
    costs = [sum(c["estimated_cost_usd"] or 0 for c in r["calls"]) for r in rows]
    m = {
        "sample_count": n,
        "valid_samples": len(valid),
        "overall_mae": mean([abs(d) for d in diffs]),
        "criterion_mae": {
            k: mean([abs(r["scores"][k] - r["reference"][k]) for r in valid]) for k in CRITERIA
        },
        "within_half_rate": sum(abs(d) <= 0.5 for d in diffs) / n,
        "within_one_rate": sum(abs(d) <= 1 for d in diffs) / n,
        "band_agreement": sum(
            writing_reference_level(r["scores"]["overall"])
            == writing_reference_level(r["reference"]["overall"])
            for r in valid
        )
        / n,
        "overscore_rate": sum(d > 0.5 for d in diffs) / n,
        "underscore_rate": sum(d < -0.5 for d in diffs) / n,
        "serious_overscore_rate": sum(d > 1 for d in diffs) / n,
        "mean_signed_error": mean(diffs),
        "structured_success_rate": len(valid) / n,
        "invalid_output_rate": sum(c["status"] == "invalid_output" for c in calls) / max(1, len(calls)),
        "avg_latency_ms": mean([sum(c["latency_ms"] for c in r["calls"]) for r in rows]),
        "avg_input_tokens": mean([sum(c["input_tokens"] for c in r["calls"]) for r in rows]),
        "avg_cached_input_tokens": mean([sum(c["cached_input_tokens"] for c in r["calls"]) for r in rows]),
        "avg_output_tokens": mean([sum(c["output_tokens"] for c in r["calls"]) for r in rows]),
        "avg_reasoning_tokens": mean([sum(c["reasoning_tokens"] for c in r["calls"]) for r in rows]),
        "avg_requests": len(calls) / n,
        "avg_cost_usd": mean(costs),
        "cost_per_100": mean(costs) * 100,
        "cost_per_1000": mean(costs) * 1000,
        "cost_fully_metered": cost_known,
        "new_provider_requests": sum(not c.get("replayed") for c in calls),
        "new_known_cost_usd": sum(c["estimated_cost_usd"] or 0 for c in calls if not c.get("replayed")),
        "escalation_rate": sum(bool(r.get("escalation_reasons")) for r in rows) / n,
    }
    t = thresholds()
    checks = {
        "overall_mae": m["overall_mae"] is not None and m["overall_mae"] <= t["overall_mae_max"],
        "criterion_mae": all(
            v is not None and v <= t["criterion_mae_max"] for v in m["criterion_mae"].values()
        ),
        "within_half": m["within_half_rate"] >= t["within_half_min"],
        "within_one": m["within_one_rate"] >= t["within_one_min"],
        "serious_overscore": m["serious_overscore_rate"] <= t["serious_overscore_max"],
        "structured_success": m["structured_success_rate"] >= t["structured_success_min"],
        "sample_count": n >= t["min_samples"],
        "reference_provenance": all(r["source"] != "model_baseline" for r in rows),
    }
    m.update(quality_pass=all(checks.values()), checks=checks)
    return m


class GradingModelEvaluationService:
    def __init__(self, dataset):
        self.dataset = dataset
        self.dataset_hash = hashlib.sha256(
            json.dumps(dataset, sort_keys=True, ensure_ascii=False).encode()
        ).hexdigest()
        ids = [s["id"] for s in dataset["samples"]]
        if not ids:
            raise ValueError("Dataset must contain reference samples")
        if len(set(ids)) != len(ids):
            raise ValueError("Duplicate dataset sample IDs")
        for s in dataset["samples"]:
            if s["source"] not in {
                "human_reviewed",
                "manually_reviewed",
                "internal_reference",
                "model_baseline",
            }:
                raise ValueError("Explicit reference provenance is required")
            if s["source"] == "human_reviewed" and not s.get("reviewer_count"):
                raise ValueError("Human reference must identify actual review provenance")
            if any(not 0 <= s["reference"][k] <= 10 for k in (*CRITERIA, "overall")):
                raise ValueError("Reference outside 0–10")

    async def run(
        self,
        model,
        effort,
        output,
        semaphore,
        escalation_model=None,
        escalation_effort="low",
        primary_replay=None,
    ):
        replay = {}
        if primary_replay:
            if (
                primary_replay["dataset_hash"] != self.dataset_hash
                or primary_replay["versions"]["core_prompt"] != WRITING_CORE_VERSION
                or primary_replay["model"].split("+")[0] != model
                or primary_replay["reasoning_effort"] != effort
            ):
                raise ValueError(
                    "Replay must use the identical dataset, core prompt, primary model and effort"
                )
            replay = {r["sample_id"]: r for r in primary_replay["results"]}
            if set(replay) != {s["id"] for s in self.dataset["samples"]}:
                raise ValueError("Replay requires every sample; partial subset selection is not allowed")
        run_id = str(uuid4())
        result = {
            "id": run_id,
            "model": model if not escalation_model else f"{model}+conditional-{escalation_model}",
            "reasoning_effort": effort,
            "dataset_version": self.dataset["version"],
            "dataset_hash": self.dataset_hash,
            "quality_targets": thresholds(),
            "primary_replay_run_id": primary_replay["id"] if primary_replay else None,
            "created_at": utcnow().isoformat(),
            "versions": {
                "core_prompt": WRITING_CORE_VERSION,
                "price": PRICE_VERSION,
                "model_version": settings.model_version,
                "escalation": ESCALATION_VERSION,
                "escalation_model": escalation_model,
                "escalation_effort": escalation_effort,
            },
            "results": [],
        }
        quota_exhausted = asyncio.Event()

        async def sample(s):
            async with semaphore:
                llm = OpenAILLMClient(model=model, reasoning_effort=effort)
                row = {
                    "sample_id": s["id"],
                    "source": s["source"],
                    "reference": s["reference"],
                    "tags": s.get("tags", []),
                }
                if quota_exhausted.is_set():
                    row.update(
                        error_code="evaluation_skipped_provider_quota", calls=[], escalation_reasons=[]
                    )
                    result["results"].append(row)
                    return
                try:
                    if replay:
                        original = replay[s["id"]]
                        core = copy.deepcopy(
                            original.get("primary_result")
                            if "primary_result" in original
                            else original.get("result")
                        )
                        llm.calls = [
                            {**copy.deepcopy(c), "replayed": True}
                            for c in original["calls"]
                            if c["operation"] == "writing_core"
                        ]
                        if not llm.calls or any(
                            c["status"] not in {"success", "invalid_output"} for c in llm.calls
                        ):
                            raise ValueError(
                                "Only completed primary analyses can be replayed; rerun provider failures"
                            )
                        if not core:
                            primary_error = original.get("primary_error", original.get("error_code"))
                            if (
                                primary_error == "ai_invalid_output"
                                and llm.calls[-1]["status"] == "invalid_output"
                            ):
                                raise AppError(502, "Replayed invalid primary output", "ai_invalid_output")
                            raise ValueError("Replay is missing a validated primary analysis")
                    else:
                        with ai_context(evaluation_id=run_id):
                            core = await WritingCoreService(llm).analyze(
                                {
                                    "task": s["task"],
                                    "question": s["question"],
                                    "requirements": s.get("requirements", []),
                                    "user_answer": s["answer"],
                                    "minimum_words": s.get("minimum_words", 120 if s["task"] == 1 else 250),
                                    "word_count": count_words(s["answer"]),
                                },
                                None,
                            )
                    scores = {k: core["assessment"][k]["score"] for k in CRITERIA}
                    row.update(
                        scores={**scores, "overall": sum(scores.values()) / 4},
                        result=core,
                        escalation_reasons=GradingEscalationService().writing_reasons(core),
                    )
                except Exception as e:
                    code = getattr(e, "code", type(e).__name__)
                    row.update(
                        error_code=code,
                        escalation_reasons=["INVALID_PRIMARY_OUTPUT"] if code == "ai_invalid_output" else [],
                    )
                row["calls"] = llm.calls
                if row.get("error_code") == "ai_quota_exhausted":
                    quota_exhausted.set()
                    result["blocked_reason"] = "ai_quota_exhausted"
                if escalation_model and row["escalation_reasons"]:
                    review = OpenAILLMClient(model=escalation_model, reasoning_effort=escalation_effort)
                    row["primary_result"] = row.pop("result", None)
                    row["primary_scores"] = row.pop("scores", None)
                    row["primary_error"] = row.pop("error_code", None)
                    try:
                        with ai_context(evaluation_id=run_id):
                            core = await WritingCoreService(review).analyze(
                                GradingEscalationService.writing_review_payload(
                                    {
                                        "task": s["task"],
                                        "question": s["question"],
                                        "requirements": s.get("requirements", []),
                                        "user_answer": s["answer"],
                                        "minimum_words": s.get(
                                            "minimum_words", 120 if s["task"] == 1 else 250
                                        ),
                                        "word_count": count_words(s["answer"]),
                                    },
                                    row["primary_result"],
                                    row["escalation_reasons"],
                                ),
                                None,
                                "writing_escalation",
                            )
                        scores = {k: core["assessment"][k]["score"] for k in CRITERIA}
                        row.update(
                            scores={**scores, "overall": sum(scores.values()) / 4},
                            result=core,
                            final_consistency_reasons=GradingEscalationService().writing_reasons(core),
                        )
                    except Exception as e:
                        row["error_code"] = getattr(e, "code", type(e).__name__)
                        if row["error_code"] == "ai_quota_exhausted":
                            quota_exhausted.set()
                            result["blocked_reason"] = "ai_quota_exhausted"
                    row["calls"] += review.calls
                result["results"].append(row)
                output.write_text(json.dumps(result, ensure_ascii=False, indent=2, default=str) + "\n")
                print(model, effort, s["id"], row.get("scores", row.get("error_code")), flush=True)

        await asyncio.gather(*(sample(s) for s in self.dataset["samples"]))
        result["results"].sort(key=lambda r: r["sample_id"])
        result["metrics"] = evaluate_metrics(result["results"])
        result["source_counts"] = dict(Counter(s["source"] for s in self.dataset["samples"]))
        output.write_text(json.dumps(result, ensure_ascii=False, indent=2, default=str) + "\n")
        async with SessionLocal() as db:
            db.add(
                GradingModelEvaluation(
                    id=run_id,
                    model=result["model"],
                    reasoning_effort=effort,
                    dataset_version=self.dataset["version"],
                    dataset_hash=self.dataset_hash,
                    sample_count=len(result["results"]),
                    metrics=result["metrics"],
                    results=result["results"],
                    versions=result["versions"],
                )
            )
            await db.commit()
        return result


def comparison_report(runs, destination):
    table = [
        "# Writing model calibration benchmark",
        "",
        "References are editorial estimates unless explicitly labelled human reviewed. This small set cannot establish population-level reliability or certify VSTEP accuracy.",
        "",
        "| Model | Effort | N | MAE | ±0.5 | ±1 | Over >1 | Signed error | Valid | $ / task | $ / 100 | Pass |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for r in runs:
        m = r["metrics"]

        def fmt(v):
            return f"{v:.3f}" if v is not None else "unknown"

        table.append(
            f"| {r['model']} | {r['reasoning_effort']} | {m['sample_count']} | {fmt(m['overall_mae'])} | {m['within_half_rate']:.1%} | {m['within_one_rate']:.1%} | {m['serious_overscore_rate']:.1%} | {fmt(m['mean_signed_error'])} | {m['structured_success_rate']:.1%} | {m['avg_cost_usd']:.4f} | {m['cost_per_100']:.2f} | {m['quality_pass']} |"
        )
    passing = [r for r in runs if r["metrics"]["quality_pass"] and r["metrics"]["cost_fully_metered"]]
    best = min(passing, key=lambda r: r["metrics"]["avg_cost_usd"], default=None)
    table += [
        "",
        "Cheapest passing candidate on this dataset: "
        + (
            f"**{best['model']} / {best['reasoning_effort']}**."
            if best
            else "**none**; do not claim a cheaper model has passed."
        ),
        "",
        "Product thresholds (not official exam requirements):",
        "```json",
        json.dumps(thresholds(), indent=2),
        "```",
        "",
        "Band agreement is an internal comparison bucket; a single Writing task does not certify a proficiency level. Invalid-output rate counts each provider response; structured success counts validated final sample results including bounded retry cost. Failed samples remain in rate denominators. Full criterion errors, token/cache/reasoning usage, calls, latency, cost/1,000, source provenance and raw results are saved in the run JSON and database.",
    ]
    if any(r.get("primary_replay_run_id") for r in runs):
        table += [
            "",
            "Primary replay fixes all original primary outputs while measuring fresh conditional reviews. It is not a new end-to-end run. Full-route cost/tokens/latency include the original measured primary calls; only new review calls incur additional charges. The JSON records the source run ID, replayed calls, new_provider_requests and new_known_cost_usd. No sample subsets or reference labels are sent to reviewers.",
        ]
    destination.write_text("\n".join(table) + "\n")


async def main(args):
    dataset = json.loads(args.dataset.read_text())
    if args.human_db:
        async with SessionLocal() as db:
            reviewed = list(
                await db.scalars(
                    select(WritingCalibrationSample).where(WritingCalibrationSample.reviewer_count > 0)
                )
            )
        human = []
        for s in reviewed:
            values = [
                s.human_task_score,
                s.human_organization_score,
                s.human_vocabulary_score,
                s.human_grammar_score,
                s.human_overall_score,
            ]
            if any(v is None for v in values) or s.task_type not in (1, 2):
                continue
            human.append(
                {
                    "id": f"human-{s.id}",
                    "task": s.task_type,
                    "question": s.question,
                    "answer": s.answer,
                    "reference": dict(zip((*CRITERIA, "overall"), values)),
                    "source": "human_reviewed",
                    "reviewer_count": s.reviewer_count,
                    "tags": ["human_reviewed"],
                }
            )
        if not human:
            raise ValueError(
                "No complete human-reviewed samples exist. Nothing was labelled as teacher ground truth."
            )
        # Human evidence has priority: this run selects against human references alone.
        dataset = {"version": dataset["version"] + "-human", "samples": human}
    if args.limit:
        dataset = {**dataset, "samples": dataset["samples"][: args.limit]}
    service = GradingModelEvaluationService(dataset)
    primary_replay = json.loads(args.primary_replay.read_text()) if args.primary_replay else None
    args.output.mkdir(parents=True, exist_ok=True)
    semaphore = asyncio.Semaphore(args.concurrency)
    runs = []
    for model in args.models.split(","):
        for effort in args.efforts.split(","):
            suffix = f"-routed-{args.escalation_effort}" if args.escalation_model else ""
            path = args.output / f"{model}-{effort}{suffix}.json"
            if args.resume and path.exists():
                stored = json.loads(path.read_text())
                if (
                    stored.get("metrics")
                    and not stored.get("blocked_reason")
                    and not any(
                        c["status"] in {"http_429", "timeout", "error"}
                        for r in stored["results"]
                        for c in r["calls"]
                    )
                    and stored["dataset_hash"] == service.dataset_hash
                    and stored.get("quality_targets") == thresholds()
                    and stored.get("primary_replay_run_id")
                    == (primary_replay["id"] if primary_replay else None)
                    and stored["versions"]["core_prompt"] == WRITING_CORE_VERSION
                    and stored["versions"].get("model_version") == settings.model_version
                    and stored["versions"].get("escalation_model") == args.escalation_model
                    and (
                        not args.escalation_model
                        or stored["versions"].get("escalation") == ESCALATION_VERSION
                    )
                ):
                    runs.append(stored)
                    continue
            runs.append(
                await service.run(
                    model,
                    effort,
                    path,
                    semaphore,
                    args.escalation_model,
                    args.escalation_effort,
                    primary_replay,
                )
            )
            comparison_report(runs, args.output / "REPORT.md")
            if runs[-1].get("blocked_reason"):
                print("Provider quota exhausted; remaining candidates were not requested.", flush=True)
                await engine.dispose()
                return
    comparison_report(runs, args.output / "REPORT.md")
    print("Report:", args.output / "REPORT.md", flush=True)
    await engine.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--models", default="gpt-5.6-luna,gpt-5.4-mini-2026-03-17,gpt-5.6-terra")
    parser.add_argument("--efforts", default="low")
    parser.add_argument("--concurrency", type=int, default=3)
    parser.add_argument("--output", type=Path, default=Path("app/evals/runs/writing-v1"))
    parser.add_argument("--limit", type=int)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument(
        "--primary-replay",
        type=Path,
        help="Reuse all measured primary analyses from an identical run; make fresh conditional reviews. Full route cost still includes primary calls.",
    )
    parser.add_argument(
        "--escalation-model",
        help="Benchmark actual conditional second opinions, including both calls' costs.",
    )
    parser.add_argument("--escalation-effort", default="low")
    parser.add_argument(
        "--human-db",
        action="store_true",
        help="Use stored human references exclusively; never relabel internal estimates.",
    )
    asyncio.run(main(parser.parse_args()))
