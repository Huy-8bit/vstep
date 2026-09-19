"""Compare Reading generation using the same schema and an independent fixed reviewer."""

import asyncio
import json
from pathlib import Path
from uuid import uuid4

from app.db.session import engine
from app.llm.openai_client import OpenAILLMClient
from app.llm.usage import ai_context
from app.validators.quality import ReadingQuestionQualityValidator
from app.vstep_reference.reading_blueprints import READING_TAXONOMY

CASES = [
    {
        "id": "inference-work",
        "mode": "QUESTION_TYPE_PRACTICE",
        "topic": "work",
        "question_count": 5,
        "target_question_types": ["inference"],
    },
    {
        "id": "attitude-education",
        "mode": "QUESTION_TYPE_PRACTICE",
        "topic": "education",
        "question_count": 5,
        "target_question_types": ["attitude"],
    },
    {
        "id": "mixed-environment",
        "mode": "PASSAGE_PRACTICE",
        "topic": "environment",
        "question_count": 10,
        "target_question_types": [],
    },
]


async def main():
    results = []
    output = Path("app/evals/runs/reading-generation.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    for model in ("gpt-5.6-luna", "gpt-5.4-mini-2026-03-17"):
        for case in CASES:
            llm = OpenAILLMClient(model=model, reasoning_effort="low")
            reviewer = OpenAILLMClient(model="gpt-5.4-mini-2026-03-17", reasoning_effort="low")
            row = {
                "model": model,
                "reasoning_effort": "low",
                "case": case["id"],
                "reviewer": "gpt-5.4-mini-2026-03-17",
                "valid": False,
            }
            with ai_context(evaluation_id=str(uuid4())):
                try:
                    payload = {
                        **case,
                        "test_profile": "VSTEP_3_5",
                        "internal_difficulty_band": "MODERATE",
                        "recent_titles": [],
                        "recent_topics": [],
                        "generation_context": {"practice_mode": case["mode"]},
                        "taxonomy": READING_TAXONOMY,
                    }
                    payload.pop("id")
                    generated = await llm.generate_reading(payload, None)
                    review = await ReadingQuestionQualityValidator().validate(
                        reviewer,
                        generated,
                        None,
                        practice_context={
                            k: case[k] for k in ("mode", "question_count", "target_question_types")
                        },
                    )
                    row.update(valid=True, review=review, passage=generated.model_dump())
                except Exception as e:
                    row["error_code"] = getattr(e, "code", type(e).__name__)
            row["calls"] = llm.calls + reviewer.calls
            row["cost_usd"] = sum(c["estimated_cost_usd"] or 0 for c in row["calls"])
            row["latency_ms"] = sum(c["latency_ms"] for c in row["calls"])
            results.append(row)
            output.write_text(
                json.dumps({"cases": CASES, "results": results}, ensure_ascii=False, indent=2) + "\n"
            )
            print(model, case["id"], row["valid"], row.get("error_code"), row["cost_usd"], flush=True)
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
