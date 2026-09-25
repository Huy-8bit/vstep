from datetime import timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import select

from app.common.errors import AppError
from app.db.base import utcnow
from app.learning.analysis import PersonalizedLearningAnalysisService
from app.learning.signals import profile_for
from app.models.learning import StudyPlan, StudyPlanItem
from app.services.speech_transcription_service import speech_lock


def today_date():
    return utcnow().astimezone(ZoneInfo("Asia/Ho_Chi_Minh")).date()


def item_view(item):
    return {
        **{
            k: getattr(item, k)
            for k in (
                "id",
                "date",
                "skill",
                "concept_key",
                "weakness_id",
                "activity_type",
                "estimated_minutes",
                "status",
            )
        },
        **item.details,
    }


class StudyPlanService:
    def __init__(self, db):
        self.db = db

    async def current(self, user_id):
        plan = await self.db.scalar(
            select(StudyPlan)
            .where(StudyPlan.user_id == user_id, StudyPlan.status == "ACTIVE")
            .order_by(StudyPlan.created_at.desc())
            .limit(1)
        )
        if not plan:
            return None
        items = list(
            await self.db.scalars(
                select(StudyPlanItem)
                .where(StudyPlanItem.user_id == user_id, StudyPlanItem.plan_id == plan.id)
                .order_by(StudyPlanItem.date, StudyPlanItem.created_at)
            )
        )
        return {
            **{
                k: getattr(plan, k)
                for k in (
                    "id",
                    "duration_days",
                    "daily_minutes",
                    "start_date",
                    "end_date",
                    "status",
                    "profile_revision",
                )
            },
            "items": [item_view(i) for i in items],
        }

    async def create(self, user_id, data):
        await speech_lock(self.db, f"learning:{user_id}")
        priorities = [
            w
            for w in (await PersonalizedLearningAnalysisService(self.db).weaknesses(user_id))["items"]
            if w["status"] != "MASTERED"
        ][:6]
        if not priorities:
            raise AppError(
                409,
                "Chưa đủ bằng chứng để lập kế hoạch cá nhân. Hãy hoàn thành một bài luyện rồi quay lại.",
                "learning_evidence_required",
            )
        profile = await profile_for(self.db, user_id)
        for old in await self.db.scalars(
            select(StudyPlan).where(StudyPlan.user_id == user_id, StudyPlan.status == "ACTIVE")
        ):
            old.status = "ARCHIVED"
        today = today_date()
        plan = StudyPlan(
            user_id=user_id,
            duration_days=data.duration_days,
            daily_minutes=data.daily_minutes,
            start_date=today,
            end_date=today + timedelta(days=data.duration_days - 1),
            profile_revision=profile.revision,
        )
        self.db.add(plan)
        await self.db.flush()
        for day in range(data.duration_days):
            w = priorities[day % len(priorities)]
            review = day >= len(priorities)
            lesson_minutes = 5
            schedule = [
                ("REVIEW" if review else "LESSON", lesson_minutes),
                ("TRANSFER" if review and day % 3 == 0 else "PRACTICE", data.daily_minutes - lesson_minutes),
            ]
            for activity, minutes in schedule:
                self.db.add(
                    StudyPlanItem(
                        user_id=user_id,
                        plan_id=plan.id,
                        weakness_id=w["id"],
                        date=today + timedelta(days=day),
                        skill=w["skill"],
                        concept_key=w["concept_key"],
                        activity_type=activity,
                        estimated_minutes=minutes,
                        details={
                            "title": w["display_name_vi"],
                            "url": f"/learning/weaknesses?id={w['id']}",
                            "reason_vi": f"Ưu tiên từ {w['affected_attempt_count']} bài có bằng chứng; {'ôn cách dùng trong ngữ cảnh mới' if review else 'học quy tắc và luyện có phản hồi'}.",
                            "exercise_count": 5
                            if data.daily_minutes == 15
                            else 10
                            if data.daily_minutes == 40
                            else 8,
                        },
                    )
                )
        await self.db.commit()
        return await self.current(user_id)

    async def update_item(self, identifier, user_id, data):
        item = await self.db.scalar(
            select(StudyPlanItem)
            .where(StudyPlanItem.id == identifier, StudyPlanItem.user_id == user_id)
            .with_for_update()
        )
        if not item:
            raise AppError(404, "Không tìm thấy hoạt động học.")
        item.status = data.status
        # Manual completion tracks plan adherence only, never mastery or measured learning time.
        await self.db.commit()
        return item_view(item)

    async def today(self, user_id):
        today = today_date()
        plan = await self.current(user_id)
        priorities = [
            w
            for w in (await PersonalizedLearningAnalysisService(self.db).weaknesses(user_id))["items"]
            if w["status"] != "MASTERED"
        ]
        items = [i for i in plan["items"] if i["date"] == today and i["status"] == "PENDING"] if plan else []
        # Keep the committed plan stable, but recommend current priorities separately as evidence evolves.
        recommendations = [
            {
                "weakness_id": w["id"],
                "title": w["display_name_vi"],
                "skill": w["skill"],
                "estimated_minutes": 15 if n == 0 else 10,
                "url": f"/learning/weaknesses?id={w['id']}",
                "reason_vi": "Ôn lại sau khi lỗi xuất hiện trở lại."
                if w["status"] == "REGRESSED"
                else "Học quy tắc ngắn, luyện và áp dụng vào một ngữ cảnh mới.",
            }
            for n, w in enumerate(priorities[:2])
        ]
        return {
            "date": today,
            "items": items[:3],
            "recommendations": recommendations,
            "estimated_minutes": sum(i["estimated_minutes"] for i in items[:3])
            if items
            else sum(r["estimated_minutes"] for r in recommendations),
            "plan_id": plan["id"] if plan else None,
        }
