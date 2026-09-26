import httpx
import pytest
from openai import AuthenticationError
from pydantic import BaseModel

from app.common.errors import AppError
from app.core.config import settings
from app.llm import openai_client


class ExampleOutput(BaseModel):
    answer: str


@pytest.mark.asyncio
async def test_invalidated_api_key_reports_actionable_error(monkeypatch):
    request = httpx.Request("POST", "https://api.openai.com/v1/responses")
    response = httpx.Response(
        401,
        request=request,
        json={"error": {"code": "token_invalidated", "message": "Invalid token"}},
    )
    usage_events = []

    class FakeClient:
        responses = None

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_):
            return None

        async def create(self, **_):
            raise AuthenticationError(
                "Invalid token", response=response, body=response.json()["error"]
            )

    client = FakeClient()
    client.responses = client

    async def fake_record_usage(**kwargs):
        usage_events.append(kwargs)

    monkeypatch.setattr(settings, "openai_api_key", "test-key")
    monkeypatch.setattr(openai_client, "AsyncOpenAI", lambda **_: client)
    monkeypatch.setattr(openai_client, "record_usage", fake_record_usage)

    with pytest.raises(AppError) as raised:
        await openai_client.OpenAILLMClient(max_attempts=1)._structured(
            ExampleOutput, "prompt", {}, "test-user", "writing_analysis"
        )

    assert raised.value.status == 503
    assert raised.value.code == "ai_credentials_invalid"
    assert "khóa" in raised.value.message.lower()
    assert usage_events[0]["status"] == "http_401"
    assert usage_events[0]["provider_error_code"] == "token_invalidated"
