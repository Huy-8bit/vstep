"""Central access and usage policy for learner operations."""

from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import func, select

from app.common.errors import AppError
from app.core.config import settings
from app.db.base import utcnow
from app.models import User
from app.models.commerce import ProductEvent, TrialUsage, UserEntitlement, VipDailyUsage

BUSINESS_TZ = ZoneInfo("Asia/Ho_Chi_Minh")
TRIAL_FEATURES = {"WRITING_TASK1", "SPEAKING_PART1"}
VIP_ONLY = {
    "WRITING_TASK2",
    "WRITING_FULL",
    "SPEAKING_PART2",
    "SPEAKING_PART3",
    "SPEAKING_FULL",
    "READING",
    "PRONUNCIATION",
    "LEARNING",
    "VOCABULARY",
    "AI_GENERATION",
}


@dataclass(frozen=True)
class EntitlementDecision:
    allowed: bool
    reason: str
    upgrade_required: bool = False
    trial_remaining: int = 0
    vip_expires_at: datetime | None = None

    def as_dict(self):
        return vars(self)


class UsageQuotaService:
    def __init__(self, db):
        self.db = db

    @staticmethod
    def trial_limit(feature: str) -> int:
        return {
            "WRITING_TASK1": settings.free_trial_writing_task1_attempts,
            "SPEAKING_PART1": settings.free_trial_speaking_part1_attempts,
        }.get(feature, 0)

    @staticmethod
    def daily_group(feature: str):
        return (
            "WRITING"
            if feature.startswith("WRITING")
            else "SPEAKING"
            if feature.startswith("SPEAKING") or feature == "PRONUNCIATION"
            else "FREE_READING"
            if feature == "READING_QUICK"
            else "READING"
            if feature == "READING"
            else "AI_GENERATION"
            if feature == "AI_GENERATION"
            else None
        )

    @staticmethod
    def daily_limit(group: str) -> int:
        return {
            "WRITING": settings.vip_writing_daily_limit,
            "SPEAKING": settings.vip_speaking_daily_limit,
            "READING": settings.vip_reading_daily_limit,
            "AI_GENERATION": settings.vip_ai_generation_daily_limit,
            "FREE_READING": settings.free_reading_daily_limit,
        }[group]

    async def trial_remaining(self, user_id: str, feature: str):
        used = await self.db.scalar(
            select(TrialUsage.used_count).where(
                TrialUsage.user_id == user_id, TrialUsage.feature_code == feature
            )
        )
        return max(0, self.trial_limit(feature) - (used or 0))

    async def vip_remaining(self, user_id: str, group: str):
        day = utcnow().astimezone(BUSINESS_TZ).date()
        used = await self.db.scalar(
            select(VipDailyUsage.used_count).where(
                VipDailyUsage.user_id == user_id,
                VipDailyUsage.feature_code == group,
                VipDailyUsage.day == day,
            )
        )
        return max(0, self.daily_limit(group) - (used or 0))

    async def consume(self, user_id: str, feature: str, vip: bool):
        # Serializing on the existing user row protects first-use inserts and counters.
        await self.db.scalar(select(User).where(User.id == user_id).with_for_update())
        if vip:
            group = self.daily_group(feature)
            if not group or not settings.vip_fair_use_enabled:
                return
            day = utcnow().astimezone(BUSINESS_TZ).date()
            row = await self.db.scalar(
                select(VipDailyUsage).where(
                    VipDailyUsage.user_id == user_id,
                    VipDailyUsage.feature_code == group,
                    VipDailyUsage.day == day,
                )
            )
            if not row:
                row = VipDailyUsage(user_id=user_id, feature_code=group, day=day, used_count=0)
                self.db.add(row)
            if row.used_count >= self.daily_limit(group):
                raise AppError(
                    429,
                    "Bạn đã sử dụng rất nhiều lượt luyện tập hôm nay. Vui lòng quay lại sau.",
                    "DAILY_LIMIT_REACHED",
                )
            row.used_count += 1
        else:
            row = await self.db.scalar(
                select(TrialUsage).where(TrialUsage.user_id == user_id, TrialUsage.feature_code == feature)
            )
            if not row:
                row = TrialUsage(
                    user_id=user_id, feature_code=feature, max_uses=self.trial_limit(feature), used_count=0
                )
                self.db.add(row)
            if row.used_count >= row.max_uses:
                raise AppError(403, "Bạn đã dùng lượt luyện miễn phí cho kỹ năng này.", "TRIAL_USED")
            row.used_count += 1
            self.db.add(
                ProductEvent(
                    user_id=user_id,
                    name=f"TRIAL_{'WRITING' if feature == 'WRITING_TASK1' else 'SPEAKING'}_STARTED",
                    details={"feature": feature},
                )
            )
        await self.db.flush()


class EntitlementService:
    def __init__(self, db):
        self.db = db
        self.quota = UsageQuotaService(db)

    async def vip_expiry(self, user_id: str, now: datetime | None = None):
        now = now or utcnow()
        current = await self.db.scalar(
            select(func.max(UserEntitlement.expires_at)).where(
                UserEntitlement.user_id == user_id,
                UserEntitlement.entitlement_type == "VIP",
                UserEntitlement.status == "ACTIVE",
                UserEntitlement.starts_at <= now,
                UserEntitlement.expires_at > now,
            )
        )
        if not current:
            return None
        # Renewals are adjacent intervals; report the effective end of the chain.
        rows = await self.db.scalars(
            select(UserEntitlement)
            .where(
                UserEntitlement.user_id == user_id,
                UserEntitlement.entitlement_type == "VIP",
                UserEntitlement.status == "ACTIVE",
                UserEntitlement.expires_at > current,
            )
            .order_by(UserEntitlement.starts_at)
        )
        for row in rows:
            if row.starts_at > current:
                break
            current = max(current, row.expires_at)
        return current

    async def decision(self, user: User, feature: str) -> EntitlementDecision:
        if user.status != "ACTIVE":
            return EntitlementDecision(False, "ACCOUNT_DISABLED")
        if user.role == "ADMIN":
            return EntitlementDecision(True, "ALLOWED")
        vip_expiry = await self.vip_expiry(user.id)
        if vip_expiry:
            group = self.quota.daily_group("READING" if feature == "READING_QUICK" else feature)
            if group and settings.vip_fair_use_enabled and not await self.quota.vip_remaining(user.id, group):
                return EntitlementDecision(False, "DAILY_LIMIT_REACHED", vip_expires_at=vip_expiry)
            if feature == "AI_GENERATION" and not settings.vip_ai_question_generation_enabled:
                return EntitlementDecision(False, "VIP_REQUIRED", vip_expires_at=vip_expiry)
            return EntitlementDecision(True, "ALLOWED", vip_expires_at=vip_expiry)
        if feature in TRIAL_FEATURES:
            remaining = await self.quota.trial_remaining(user.id, feature)
            return EntitlementDecision(
                bool(remaining),
                "TRIAL_AVAILABLE" if remaining else "TRIAL_USED",
                not bool(remaining),
                remaining,
            )
        if feature == "READING_QUICK" and settings.free_reading_enabled:
            remaining = await self.quota.vip_remaining(user.id, "FREE_READING")
            return EntitlementDecision(bool(remaining), "ALLOWED" if remaining else "DAILY_LIMIT_REACHED")
        if feature == "AI_GENERATION" and settings.free_ai_question_generation_enabled:
            return EntitlementDecision(True, "ALLOWED")
        return EntitlementDecision(False, "VIP_REQUIRED", True)

    async def require(self, user: User, feature: str, *, consume: bool = False):
        decision = await self.decision(user, feature)
        if not decision.allowed:
            status = 429 if decision.reason == "DAILY_LIMIT_REACHED" else 403
            message = (
                "Bạn đã sử dụng rất nhiều lượt luyện tập hôm nay. Vui lòng quay lại sau."
                if status == 429
                else "Nâng cấp VIP để mở tính năng này."
                if decision.upgrade_required
                else "Tài khoản đã bị vô hiệu hóa."
            )
            raise AppError(status, message, decision.reason)
        if (
            consume
            and user.role != "ADMIN"
            and (feature in TRIAL_FEATURES or self.quota.daily_group(feature))
        ):
            counted_feature = "READING" if decision.vip_expires_at and feature == "READING_QUICK" else feature
            await self.quota.consume(
                user.id, counted_feature, bool(decision.vip_expires_at) or feature == "READING_QUICK"
            )
        return decision

    async def require_existing(self, user: User, feature: str, access_source: str):
        if access_source == "TRIAL" and feature in TRIAL_FEATURES and user.status == "ACTIVE":
            return EntitlementDecision(True, "TRIAL_AVAILABLE")
        return await self.require(user, feature)

    async def summary(self, user: User):
        expires_at = await self.vip_expiry(user.id) if user.role != "ADMIN" else None
        return {
            "tier": "VIP" if user.role == "ADMIN" or expires_at else "FREE",
            "vip_expires_at": expires_at,
            "trial_remaining": {
                key: await self.quota.trial_remaining(user.id, key) for key in TRIAL_FEATURES
            },
            "free_reading_enabled": settings.free_reading_enabled,
        }


def writing_feature(mode: str):
    return {"TASK1": "WRITING_TASK1", "TASK2": "WRITING_TASK2", "FULL_TEST": "WRITING_FULL"}[mode]


def speaking_feature(mode: str):
    return {
        "PART1": "SPEAKING_PART1",
        "QUICK_PRACTICE": "SPEAKING_PART1",
        "PART2": "SPEAKING_PART2",
        "PART3": "SPEAKING_PART3",
        "FULL_TEST": "SPEAKING_FULL",
    }[mode]
