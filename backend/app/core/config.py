from functools import lru_cache

from pydantic import AliasChoices, Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=("../.env", ".env"), extra="ignore")
    app_env: str = "development"
    database_url: str = "postgresql+asyncpg://vstep:vstep_dev@localhost:5432/vstep"
    openai_api_key: str = ""
    # Legacy OPENAI_MODEL is deliberately not a fallback for operation routes.
    openai_model: str = "gpt-5.6-luna"
    openai_model_default: str = "gpt-5.6-luna"
    openai_model_question_generation: str = "gpt-5.6-luna"
    openai_model_reading_generation: str = "gpt-5.6-luna"
    openai_model_question_quality: str = "gpt-5.4-mini-2026-03-17"
    openai_model_writing_analysis: str = "gpt-5.6-luna"
    openai_model_writing_scoring: str = "gpt-5.6-luna"
    openai_model_writing_escalation: str = "gpt-5.6-terra"
    openai_model_writing_corrections: str = "gpt-5.4-mini-2026-03-17"
    openai_model_vocabulary: str = "gpt-5.6-luna"
    openai_model_learning_coach: str = "gpt-5.6-luna"
    openai_model_exercise_generator: str = "gpt-5.6-luna"
    openai_model_speaking_text_grading: str = "gpt-5.4-mini-2026-03-17"
    openai_model_speaking_escalation: str = "gpt-5.6-terra"
    openai_model_import: str = "gpt-5.4-mini-2026-03-17"
    openai_reasoning_default: str = "low"
    openai_reasoning_grading: str = "low"
    openai_reasoning_writing: str = "medium"
    openai_reasoning_escalation: str = "none"
    openai_reasoning_overrides: dict[str, str] = Field(default_factory=dict)
    openai_price_overrides: dict[str, dict[str, float]] = Field(default_factory=dict)
    model_version: str = "2026-09-19-routing-v2"
    grading_escalation_enabled: bool = True
    grading_confidence_threshold: float = Field(default=0.70, ge=0, le=1)
    grading_boundary_confidence_threshold: float = Field(default=0.80, ge=0, le=1)
    grading_long_response_words: int = Field(default=650, ge=300, le=5000)
    grading_shadow_enabled: bool = False
    grading_shadow_sample_rate: float = Field(default=0.05, ge=0, le=1)
    ai_cost_admin_emails: str = ""
    eval_overall_mae_max: float = Field(default=0.5, ge=0, le=10)
    eval_criterion_mae_max: float = Field(default=0.75, ge=0, le=10)
    eval_within_half_min: float = Field(default=0.70, ge=0, le=1)
    eval_within_one_min: float = Field(default=0.90, ge=0, le=1)
    eval_serious_overscore_max: float = Field(default=0.02, ge=0, le=1)
    eval_structured_success_min: float = Field(default=0.99, ge=0, le=1)
    eval_min_samples: int = Field(default=12, ge=1)
    openai_transcribe_model: str = "gpt-4o-transcribe"
    openai_audio_model: str = Field(
        default="gpt-audio",
        validation_alias=AliasChoices("OPENAI_AUDIO_MODEL", "OPENAI_SPEAKING_AUDIO_MODEL"),
    )
    audio_analysis_enabled: bool = True
    speaking_part1_seconds: int = Field(default=180, ge=60, le=600)
    speaking_part2_seconds: int = Field(default=240, ge=60, le=600)
    speaking_part3_seconds: int = Field(default=300, ge=60, le=900)
    vocabulary_review_days: str = "1,3,7,14,30"
    openai_tts_model: str = "gpt-4o-mini-tts"
    openai_tts_voice: str = "alloy"
    question_import_storage_dir: str = "data/question_imports"
    audio_storage_dir: str = "data/audio"
    max_speaking_audio_mb: int = Field(
        default=20,
        ge=1,
        le=24,
        validation_alias=AliasChoices("SPEAKING_AUDIO_MAX_MB", "MAX_SPEAKING_AUDIO_MB"),
    )
    max_speaking_audio_seconds: int = Field(
        default=360,
        ge=15,
        le=600,
        validation_alias=AliasChoices("SPEAKING_AUDIO_MAX_SECONDS", "MAX_SPEAKING_AUDIO_SECONDS"),
    )
    audio_feedback_min_confidence: float = Field(
        default=0.70,
        ge=0.5,
        le=1,
        validation_alias=AliasChoices("AUDIO_FEEDBACK_MIN_CONFIDENCE", "PRONUNCIATION_CONFIDENCE_THRESHOLD"),
    )
    openai_grading_temperature: float | None = Field(default=None, ge=0, le=0.3)
    writing_calibration_admin_emails: str = ""
    learning_observed_attempts: int = Field(default=2, ge=2, le=20)
    learning_recurring_attempts: int = Field(default=3, ge=3, le=30)
    learning_recency_half_life_days: int = Field(default=30, ge=7, le=365)
    learning_trend_window: int = Field(default=5, ge=2, le=20)
    learning_trend_delta: float = Field(default=0.2, ge=0.05, le=0.8)
    learning_mastery_exercises: int = Field(default=20, ge=10, le=100)
    learning_mastery_sessions: int = Field(default=3, ge=2, le=10)
    learning_mastery_reuses: int = Field(default=3, ge=2, le=10)
    learning_priority_weights: dict[str, float] = Field(
        default_factory=lambda: {
            "frequency": 25,
            "recency": 15,
            "severity": 15,
            "confidence": 15,
            "impact": 15,
            "persistence": 15,
        }
    )

    @field_validator("openai_reasoning_overrides", "openai_price_overrides", mode="before")
    @classmethod
    def empty_routing_maps(cls, value):
        return {} if value == "" else value

    @field_validator("vocabulary_review_days")
    @classmethod
    def validate_review_schedule(cls, value):
        days = [int(v.strip()) for v in value.split(",")]
        if not days or any(d < 1 or d > 365 for d in days) or days != sorted(set(days)):
            raise ValueError("Vocabulary review days must be ascending distinct days between 1 and 365")
        return value

    @field_validator("openai_grading_temperature", mode="before")
    @classmethod
    def optional_temperature(cls, value):
        return None if value == "" else value

    @property
    def pronunciation_confidence_threshold(self):
        return self.audio_feedback_min_confidence

    @property
    def openai_speaking_audio_model(self):
        return self.openai_audio_model if self.audio_analysis_enabled else ""

    jwt_secret: str = "local-development-secret-change-before-production-2026"
    jwt_access_expire_minutes: int = 15
    jwt_refresh_expire_days: int = 7
    frontend_url: str = "http://localhost:3000"

    @model_validator(mode="after")
    def production_secret(self):
        if self.app_env == "production" and (
            len(self.jwt_secret) < 32 or self.jwt_secret.startswith("local-development")
        ):
            raise ValueError("JWT_SECRET must be a unique secret of at least 32 characters.")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
