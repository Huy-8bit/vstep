from functools import lru_cache

from pydantic import AliasChoices, Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=("../.env", ".env"), extra="ignore")
    app_env: str = "development"
    database_url: str = "postgresql+asyncpg://vstep:vstep_dev@localhost:5432/vstep"
    openai_api_key: str = ""
    openai_model: str = "gpt-5.6"
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
