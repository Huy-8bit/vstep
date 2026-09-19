from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import func, select

from app.common.errors import AppError
from app.core.config import settings
from app.llm.routing import ROUTES, route_for
from app.models import AIUsageLog


def is_cost_admin(user):
    allowed = {
        x.strip().lower()
        for x in (settings.ai_cost_admin_emails + "," + settings.writing_calibration_admin_emails).split(",")
        if x.strip()
    }
    return user.email.lower() in allowed


def require_cost_admin(user):
    if not is_cost_admin(user):
        raise AppError(403, "Trang này chỉ dành cho quản trị viên.", "admin_required")


class AICostService:
    def __init__(self, db):
        self.db = db

    async def overview(self, days=1):
        now = datetime.now(ZoneInfo("Asia/Ho_Chi_Minh"))
        since = datetime.combine(now.date() - timedelta(days=days - 1), time.min, tzinfo=now.tzinfo)
        query = (
            select(
                AIUsageLog.category,
                AIUsageLog.operation,
                AIUsageLog.model,
                func.count().label("calls"),
                func.sum(AIUsageLog.estimated_cost_usd).label("cost"),
                func.count().filter(AIUsageLog.estimated_cost_usd.is_(None)).label("unknown"),
                func.sum(AIUsageLog.input_tokens).label("input"),
                func.sum(AIUsageLog.cached_input_tokens).label("cached"),
                func.sum(AIUsageLog.output_tokens).label("output"),
                func.sum(AIUsageLog.reasoning_tokens).label("reasoning"),
                func.avg(AIUsageLog.latency_ms).label("latency"),
            )
            .where(AIUsageLog.created_at >= since)
            .group_by(AIUsageLog.category, AIUsageLog.operation, AIUsageLog.model)
        )
        groups = [
            {
                "category": r.category,
                "operation": r.operation,
                "model": r.model,
                "calls": r.calls,
                "estimated_cost_usd": float(r.cost or 0),
                "unknown_cost_calls": r.unknown,
                "input_tokens": r.input,
                "cached_input_tokens": r.cached,
                "output_tokens": r.output,
                "reasoning_tokens": r.reasoning,
                "avg_latency_ms": round(r.latency),
            }
            for r in (await self.db.execute(query))
        ]
        product = [r for r in groups if r["category"] not in {"evaluation", "shadow", "legacy"}]
        users = await self.db.scalar(
            select(func.count(func.distinct(AIUsageLog.user_id))).where(
                AIUsageLog.created_at >= since, AIUsageLog.category.not_in(["evaluation", "shadow", "legacy"])
            )
        )
        attempts = await self.db.scalar(
            select(func.count(func.distinct(AIUsageLog.attempt_id))).where(
                AIUsageLog.created_at >= since, AIUsageLog.category == "writing_grading"
            )
        )
        known = sum(r["estimated_cost_usd"] for r in product)
        writing = sum(r["estimated_cost_usd"] for r in product if r["category"] == "writing_grading")
        recent = await self.db.execute(
            select(
                AIUsageLog.attempt_id,
                func.sum(AIUsageLog.estimated_cost_usd),
                func.count(),
                func.max(AIUsageLog.created_at),
            )
            .where(
                AIUsageLog.created_at >= since,
                AIUsageLog.attempt_id.is_not(None),
                AIUsageLog.category.not_in(["evaluation", "shadow"]),
            )
            .group_by(AIUsageLog.attempt_id)
            .order_by(func.max(AIUsageLog.created_at).desc())
            .limit(30)
        )
        return {
            "since": since,
            "days": days,
            "known_product_cost_usd": round(known, 6),
            "unknown_cost_calls": sum(r["unknown_cost_calls"] for r in product),
            "avg_writing_task_cost_usd": writing / attempts if attempts else None,
            "avg_user_cost_usd": known / users if users else None,
            "evaluation_cost_usd": sum(
                r["estimated_cost_usd"] for r in groups if r["category"] == "evaluation"
            ),
            "groups": groups,
            "attempts": [
                {"attempt_id": a, "known_cost_usd": float(c or 0), "calls": n, "last_call": d}
                for a, c, n, d in recent
            ],
            "routes": [{"operation": op, **vars(route_for(op))} for op in ROUTES],
            "note_vi": "Chi phí ước tính theo token và bảng giá cấu hình; lượt thiếu dữ liệu được ghi riêng, không coi là miễn phí. Benchmark, shadow và log cũ tách khỏi tổng sản phẩm.",
        }

    async def attempt(self, identifier, user_id=None):
        query = select(AIUsageLog).where(AIUsageLog.attempt_id == identifier)
        if user_id:
            query = query.where(AIUsageLog.user_id == user_id)
        rows = list(await self.db.scalars(query.order_by(AIUsageLog.created_at)))
        return {
            "attempt_id": identifier,
            "known_total_usd": sum(float(r.estimated_cost_usd or 0) for r in rows),
            "unknown_cost_calls": sum(r.estimated_cost_usd is None for r in rows),
            "calls": [
                {
                    "id": r.id,
                    "operation": r.operation,
                    "model": r.model,
                    "reasoning_effort": r.reasoning_effort,
                    "input_tokens": r.input_tokens,
                    "cached_input_tokens": r.cached_input_tokens,
                    "output_tokens": r.output_tokens,
                    "reasoning_tokens": r.reasoning_tokens,
                    "estimated_cost_usd": r.estimated_cost_usd,
                    "status": r.status,
                    "latency_ms": r.latency_ms,
                    "created_at": r.created_at,
                }
                for r in rows
            ],
        }
