"""Record every provider request, including retries; unknown billing is never zero."""

import logging
from contextlib import contextmanager
from contextvars import ContextVar
from decimal import Decimal

from app.core.config import settings
from app.db.session import SessionLocal
from app.models import AIUsageLog

logger = logging.getLogger(__name__)
usage_context = ContextVar("ai_usage_context", default={})
PRICE_VERSION = "openai-standard-2026-09-19"
# USD per million tokens. Official model pages linked in MODEL_EVALUATION.md.
PRICES = {
    "gpt-5.6-luna": {"input": 0.20, "cached": 0.02, "output": 1.20},
    "gpt-5.4-mini": {"input": 0.75, "cached": 0.075, "output": 4.50},
    "gpt-5.6-terra": {"input": 2, "cached": 0.20, "output": 12},
    "gpt-5.6-sol": {"input": 4, "cached": 0.40, "output": 20},
    "gpt-5.6": {"input": 4, "cached": 0.40, "output": 20},
    "gpt-audio": {"input": 2.5, "output": 10, "audio_input": 32, "audio_output": 64},
    "gpt-4o-transcribe": {"input": 2.5, "output": 10, "audio_input": 2.5},
    "gpt-4o-mini-tts": {"input": 0.6, "output": 0, "audio_output": 12},
}


@contextmanager
def ai_context(**values):
    token = usage_context.set({**usage_context.get(), **values})
    try:
        yield
    finally:
        usage_context.reset(token)


def _dict(value):
    if hasattr(value, "model_dump"):
        return value.model_dump()
    return value if isinstance(value, dict) else vars(value) if value is not None else {}


def usage_metadata(usage, model):
    data = _dict(usage)
    input_tokens = data.get("input_tokens", data.get("prompt_tokens", 0)) or 0
    output_tokens = data.get("output_tokens", data.get("completion_tokens", 0)) or 0
    inp = _dict(data.get("input_tokens_details", data.get("prompt_tokens_details")))
    out = _dict(data.get("output_tokens_details", data.get("completion_tokens_details")))
    cached = min(input_tokens, inp.get("cached_tokens", 0) or 0)
    reasoning = out.get("reasoning_tokens", 0) or 0
    prices = {**PRICES, **settings.openai_price_overrides}
    rates = prices.get(model) or next(
        (prices[p] for p in sorted(prices, key=len, reverse=True) if model.startswith(p + "-20")), None
    )
    cost = None
    audio_in, audio_out = inp.get("audio_tokens", 0) or 0, out.get("audio_tokens", 0) or 0
    if rates and usage is not None and data.get("type") != "duration":
        # Output already includes reasoning tokens; do not bill them twice.
        cost = (
            max(0, input_tokens - cached - audio_in) * rates["input"]
            + cached * rates.get("cached", rates["input"])
            + max(0, output_tokens - audio_out) * rates["output"]
            + audio_in * rates.get("audio_input", rates["input"])
            + audio_out * rates.get("audio_output", rates["output"])
        ) / 1_000_000
        if model.startswith("gpt-5.6") and input_tokens > 272000:
            cost = (
                (input_tokens - cached) * rates["input"] * 2
                + cached * rates.get("cached", rates["input"]) * 2
                + output_tokens * rates["output"] * 1.5
            ) / 1_000_000
    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cached_input_tokens": cached,
        "reasoning_tokens": reasoning,
        "estimated_cost_usd": round(cost, 8) if cost is not None else None,
        "details": {
            "price_version": PRICE_VERSION,
            "rates": rates,
            "usage_available": usage is not None,
            "audio_input_tokens": audio_in,
            "audio_output_tokens": audio_out,
            "cached_input_tokens_available": "cached_tokens" in inp,
            "reasoning_tokens_available": "reasoning_tokens" in out,
        },
    }


async def record_usage(
    *,
    user_id,
    operation,
    model,
    reasoning_effort,
    usage,
    latency_ms,
    status,
    category,
    response_id=None,
    provider_error_code=None,
    retry_after_seconds=None,
):
    context = usage_context.get()
    item = {
        **usage_metadata(usage, model),
        "user_id": user_id,
        "operation": operation,
        "model": model,
        "reasoning_effort": reasoning_effort,
        "latency_ms": latency_ms,
        "status": status,
        "attempt_id": context.get("attempt_id"),
        "evaluation_id": context.get("evaluation_id"),
        "category": "evaluation" if context.get("evaluation_id") else category,
    }
    item["details"]["response_id"] = response_id
    item["details"]["provider_error_code"] = provider_error_code
    item["details"]["retry_after_seconds"] = retry_after_seconds
    logger.info(
        "AI operation=%s model=%s effort=%s status=%s attempt=%s cost=%s ms=%s",
        operation,
        model,
        reasoning_effort,
        status,
        item["attempt_id"],
        item["estimated_cost_usd"],
        latency_ms,
    )
    try:
        async with SessionLocal() as db:
            db.add(
                AIUsageLog(
                    **{
                        **item,
                        "estimated_cost_usd": Decimal(str(item["estimated_cost_usd"]))
                        if item["estimated_cost_usd"] is not None
                        else None,
                    }
                )
            )
            await db.commit()
    except Exception:
        logger.exception("Could not persist AI usage metadata")
    return item
