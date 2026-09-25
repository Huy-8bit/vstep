from pydantic import EmailStr, Field

from app.schemas.writing import StrictModel


class CheckoutCreate(StrictModel):
    plan_code: str = Field(pattern=r"^VIP_(3|7|30)_DAYS$")


class GrantVip(StrictModel):
    duration_days: int = Field(ge=1, le=365)
    reason: str = Field(min_length=3, max_length=500)


class RevokeVip(StrictModel):
    reason: str = Field(min_length=3, max_length=500)


class ManualConfirm(StrictModel):
    reference: str = Field(min_length=3, max_length=120)
    reason: str = Field(min_length=3, max_length=500)


class TestUserCreate(StrictModel):
    email: EmailStr
    password: str | None = Field(default=None, min_length=8, max_length=128)
    name: str | None = Field(default=None, max_length=160)
    duration_days: int = Field(default=7, ge=1, le=365)


class UserStatusUpdate(StrictModel):
    status: str = Field(pattern=r"^(ACTIVE|DISABLED)$")


class TestFlagUpdate(StrictModel):
    is_test_account: bool


class ProfileUpdate(StrictModel):
    name: str | None = Field(default=None, max_length=160)
    learning_goal: str | None = Field(default=None, max_length=240)


class PlanUpdate(StrictModel):
    name: str | None = Field(default=None, min_length=2, max_length=100)
    duration_days: int | None = Field(default=None, ge=1, le=365)
    price_vnd: int | None = Field(default=None, ge=0, le=100000000)
    is_active: bool | None = None


class QuestionPublication(StrictModel):
    is_published: bool | None = None
    access_tier: str | None = Field(default=None, pattern=r"^(FREE_TRIAL|VIP|INTERNAL)$")
    available_for_free_trial: bool | None = None
    is_featured: bool | None = None


class ProductEventCreate(StrictModel):
    name: str = Field(pattern=r"^(PRICING_VIEWED)$")


class AdminQuestionEdit(StrictModel):
    topic: str | None = Field(default=None, min_length=2, max_length=50)
    source: str | None = Field(default=None, pattern=r"^(SEED|AI|CUSTOM)$")
    question_type: str | None = Field(default=None, min_length=2, max_length=50)
    title: str | None = Field(default=None, min_length=3, max_length=300)
    instruction: str | None = Field(default=None, min_length=15, max_length=5000)
    question_text: str | None = Field(default=None, min_length=15, max_length=5000)
    stimulus: str | None = Field(default=None, max_length=4000)


class ReadingKeyUpdate(StrictModel):
    correct_answer: str = Field(pattern=r"^[ABCD]$")
    answer_key_source: str = Field(default="provided", min_length=2, max_length=20)
    explanation_vi: str | None = Field(default=None, max_length=5000)
