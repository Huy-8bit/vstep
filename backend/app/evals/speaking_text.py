"""Small transcript-only routing check, not an acoustic or examiner validation study."""

import argparse
import asyncio
import json
from pathlib import Path
from uuid import uuid4

from app.common.errors import AppError
from app.db.session import engine
from app.llm.openai_client import OpenAILLMClient
from app.llm.routing import route_for
from app.llm.usage import ai_context
from app.services.grading_escalation_service import ESCALATION_VERSION, GradingEscalationService
from app.services.speaking_correction import SpeakingCorrectionService

CASES = [
    {
        "id": "basic-errors",
        "part": 1,
        "question": "What do you usually do at weekends, and why?",
        "transcript": "I usually go park with my friend. We plays football because it make me happy. Last Sunday I go there and meet many people. I like this activity because good for health.",
        "reference": {"grammar": 4.0, "vocabulary": 4.5, "structures": 5.0},
    },
    {
        "id": "connected-simple-answer",
        "part": 1,
        "question": "Do you prefer studying alone or with other people? Why?",
        "transcript": "I prefer studying alone because I can choose my own time. When I study with friends, we sometimes talk about other things and forget our work. Last week I had an English exam, so I studied in my room every evening. This helped me finish all the exercises. However, I sometimes ask a friend for help when I do not understand a difficult question.",
        "reference": {"grammar": 6.5, "vocabulary": 6.0, "structures": 6.5},
    },
    {
        "id": "developed-comparison",
        "part": 2,
        "question": "Your class has a free afternoon. Choose a museum visit, a picnic, or a sports tournament. Explain your choice and why the other options are less suitable.",
        "transcript": "I would choose the museum visit, mainly because it combines a shared experience with something useful to learn. Our class has recently studied local history, so seeing the objects in person would make those lessons more memorable. It would also suit students who do not enjoy competitive sports. A picnic would certainly be relaxing, but the weather has been unpredictable, and we might end up cancelling at the last minute. A sports tournament could bring people together, although differences in fitness might leave some students feeling excluded. The museum does charge an entrance fee; however, if we booked as a school group, we could probably get a discount. On balance, it seems the most inclusive and reliable option.",
        "reference": {"grammar": 8.0, "vocabulary": 7.5, "structures": 8.0},
    },
]


async def main(destination):
    route = route_for("speaking_grade")
    rows = []
    for case in CASES:
        client = OpenAILLMClient()
        source = {
            "sequence_number": 0,
            "part": case["part"],
            "question": case["question"],
            "transcript": case["transcript"],
            "status": "TRANSCRIBED",
        }
        row = {"id": case["id"], "reference": case["reference"], "source": "internal_reference"}
        try:
            with ai_context(evaluation_id=str(uuid4())):
                payload = {"part": case["part"], "mode": f"PART{case['part']}", "answers": [source]}
                try:
                    result = await client.grade_speaking(payload, None)
                    reasons = GradingEscalationService().speaking_reasons(result, payload)
                    row["primary_scores"] = result.scores.model_dump()
                except AppError as exc:
                    if exc.code != "ai_invalid_output":
                        raise
                    reasons = ["INVALID_PRIMARY_OUTPUT"]
                    row["primary_error"] = exc.code
                row["escalation_reasons"] = reasons
                if reasons:
                    result = await client.grade_speaking(
                        {**payload, "review_concerns": reasons}, None, "speaking_escalation"
                    )
            merged, _ = SpeakingCorrectionService().finalize(result, [{**source, "audio_hash": None}])
            row.update(
                scores=result.scores.model_dump(),
                result=result.model_dump(),
                no_acoustic_scores=merged.scores.pronunciation is None
                and merged.scores.fluency is None
                and merged.scores.overall is None,
            )
        except Exception as exc:
            row["error"] = getattr(exc, "code", type(exc).__name__)
        row["calls"] = client.calls
        rows.append(row)
        print(case["id"], row.get("scores", row.get("error")), flush=True)
        if row.get("error") == "ai_quota_exhausted":
            break
    valid = [r for r in rows if r.get("scores")]
    calls = [c for r in rows for c in r["calls"]]
    output = {
        "model": route.model,
        "effort": route.reasoning_effort,
        "escalation_version": ESCALATION_VERSION,
        "cases": CASES,
        "results": rows,
        "metrics": {
            "completed_cases": len(valid),
            "expected_cases": len(CASES),
            "criterion_mae": {
                key: sum(abs(r["scores"][key] - r["reference"][key]) for r in valid) / len(valid)
                if valid
                else None
                for key in ("grammar", "vocabulary", "structures")
            },
            "known_cost_usd": sum(c["estimated_cost_usd"] or 0 for c in calls),
            "unknown_cost_calls": sum(c["estimated_cost_usd"] is None for c in calls),
            "escalated_cases": sum(bool(r.get("escalation_reasons")) for r in rows),
            "audio_separation_pass": len(valid) == len(CASES) and all(r["no_acoustic_scores"] for r in valid),
        },
        "limitation": "Three internal references; no human ratings or audio. A routing/schema check, not full Speaking calibration.",
    }
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n")
    await engine.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("app/evals/runs/speaking-text.json"))
    asyncio.run(main(parser.parse_args().output))
