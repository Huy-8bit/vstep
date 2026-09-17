import base64
import json

from pydantic import ValidationError
from starlette.concurrency import run_in_threadpool

from app.common.errors import AppError
from app.core.config import settings
from app.prompts.audio_assessment import AUDIO_ASSESSMENT_PROMPT
from app.schemas.audio_assessment import AUDIO_SCORE_FIELDS, AudioAssessment, unavailable_audio
from app.speech.audio_analysis_provider import AudioAnalysisProvider
from app.speech.openai_speech_client import OpenAISpeechClient


class OpenAIAudioAnalysisProvider(AudioAnalysisProvider):
    async def assess(self, audio_path, context, user_id):
        model = settings.openai_speaking_audio_model
        if not model:
            return unavailable_audio("Phân tích audio đang tắt hoặc chưa cấu hình OPENAI_AUDIO_MODEL.")
        encoded = base64.b64encode(await run_in_threadpool(audio_path.read_bytes)).decode("ascii")
        schema = AudioAssessment.model_json_schema()
        for attempt in range(2):

            async def send(client):
                return await client.chat.completions.create(
                    model=model,
                    modalities=["text"],
                    temperature=0,
                    store=False,
                    messages=[
                        {"role": "system", "content": AUDIO_ASSESSMENT_PROMPT},
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": json.dumps(
                                        {"context": context, "schema_retry": bool(attempt)},
                                        ensure_ascii=False,
                                    ),
                                },
                                {"type": "input_audio", "input_audio": {"data": encoded, "format": "wav"}},
                            ],
                        },
                    ],
                    tools=[
                        {
                            "type": "function",
                            "function": {
                                "name": "record_audio_assessment",
                                "description": "Record the audio-grounded assessment only; no external action.",
                                "parameters": schema,
                            },
                        }
                    ],
                    tool_choice={"type": "function", "function": {"name": "record_audio_assessment"}},
                )

            response = await OpenAISpeechClient().call("speaking_audio", model, user_id, send)
            try:
                calls = response.choices[0].message.tool_calls if response.choices else []
                if not calls or len(calls) != 1 or calls[0].function.name != "record_audio_assessment":
                    raise ValueError("Missing audio assessment function output")
                result = AudioAssessment.model_validate_json(calls[0].function.arguments)
                threshold = settings.audio_feedback_min_confidence
                result.issues = [
                    i
                    for i in result.issues
                    if i.confidence >= threshold and i.target.casefold() in result.heard_text.casefold()
                ]
                if result.confidence < threshold:
                    result.available = False
                    result.reason_vi = "Bản ghi chưa đủ rõ để đưa ra nhận xét âm thanh đáng tin cậy. Hãy ghi lại ở nơi yên tĩnh."
                for field in AUDIO_SCORE_FIELDS:
                    confidence = (
                        result.fluency_confidence
                        if field in {"fluency_score", "rhythm_score"}
                        else result.pronunciation_confidence
                    )
                    if not result.available or confidence < threshold:
                        setattr(result, field, None)
                if not result.available or result.pronunciation_confidence < threshold:
                    result.pronunciation_summary_vi = ""
                    result.stress_feedback_vi = ""
                    result.issue_vi = ""
                    result.practice_tip_vi = ""
                if not result.available or result.fluency_confidence < threshold:
                    result.fluency_summary_vi = ""
                result.issues = [
                    issue
                    for issue in result.issues
                    if result.available
                    and (
                        result.fluency_confidence
                        if issue.type in {"rhythm", "hesitation"}
                        else result.pronunciation_confidence
                    )
                    >= threshold
                ]
                if (
                    result.available
                    and all(getattr(result, field) is None for field in AUDIO_SCORE_FIELDS)
                    and not result.reason_vi
                ):
                    result.reason_vi = (
                        "Chưa đủ bằng chứng âm thanh tin cậy để chấm điểm. Hãy thử bản ghi rõ và dài hơn."
                    )
                if (
                    result.available
                    and context.get("mode") == "SCRIPTED_PRACTICE"
                    and (result.reference_coverage is None or result.reference_coverage < 0.8)
                ):
                    for field in AUDIO_SCORE_FIELDS:
                        setattr(result, field, None)
                    result.issues = []
                    result.pronunciation_summary_vi = ""
                    result.fluency_summary_vi = ""
                    result.stress_feedback_vi = ""
                    result.issue_vi = ""
                    result.practice_tip_vi = "Đọc lại trọn vẹn từ/câu mẫu trước khi so sánh điểm."
                    result.reason_vi = (
                        "Chưa nhận được đủ nội dung câu mẫu trong bản ghi. Hãy đọc lại đúng từ/câu được chọn."
                    )
                return result
            except (ValidationError, ValueError, AttributeError):
                if attempt:
                    raise AppError(
                        502,
                        "Model audio chưa trả kết quả có cấu trúc hợp lệ. Bản ghi đã được giữ để thử lại.",
                        "audio_analysis_invalid",
                    ) from None
        raise AppError(502, "Chưa nhận được phân tích audio.")
