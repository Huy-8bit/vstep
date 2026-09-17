import asyncio
import hashlib
import math
import wave
from abc import ABC, abstractmethod
from array import array
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import UploadFile
from starlette.concurrency import run_in_threadpool

from app.common.errors import AppError
from app.core.config import settings

SUPPORTED_MIMES = {
    "audio/webm",
    "audio/ogg",
    "audio/mp4",
    "audio/m4a",
    "audio/x-m4a",
    "audio/mpeg",
    "audio/mp3",
    "audio/wav",
    "audio/x-wav",
    "audio/aac",
    "video/mp4",
    "video/webm",
}


@dataclass
class StoredAudio:
    path: str
    sha256: str
    duration_ms: int
    size: int
    mime_type: str
    metrics: dict


class AudioStorageService(ABC):
    @abstractmethod
    async def store(self, upload: UploadFile, user_id: str) -> StoredAudio: ...

    @abstractmethod
    def resolve(self, key: str) -> Path: ...

    @abstractmethod
    def remove(self, key: str) -> None: ...


def measure_wav(path: Path) -> dict:
    with wave.open(str(path), "rb") as audio:
        rate = audio.getframerate()
        duration = audio.getnframes() / rate
        samples = array("h", audio.readframes(audio.getnframes()))
    # 20 ms energy windows. These are approximate silence metrics, not linguistic diagnoses.
    frame_size = max(1, rate // 50)
    levels = [
        math.sqrt(sum(v * v for v in samples[i : i + frame_size]) / max(1, len(samples[i : i + frame_size])))
        / 32768
        for i in range(0, len(samples), frame_size)
    ]
    threshold = max(0.008, min(0.025, (max(levels) if levels else 0) * 0.08))
    voiced = [i for i, level in enumerate(levels) if level > threshold]
    pauses = []
    if voiced:
        count = 0
        for level in levels[voiced[0] : voiced[-1] + 1]:
            if level <= threshold:
                count += 1
            else:
                if count >= 15:
                    pauses.append(round(count * 0.02, 2))
                count = 0
    return {
        "duration_seconds": round(duration, 2),
        "peak_rms_estimate": round(max(levels, default=0), 6),
        "pause_count": len(pauses),
        "long_pause_count": sum(p >= 1.2 for p in pauses),
        "pause_seconds": round(sum(pauses), 2),
        "voiced_seconds_estimate": round(len(voiced) * 0.02, 2),
        "silence_ratio_estimate": round(1 - len(voiced) / max(1, len(levels)), 3),
        "timing_source": "audio_energy_estimate",
        "metrics_note_vi": "Khoảng lặng ước lượng theo năng lượng âm thanh (từ 0,3 giây; khoảng dài từ 1,2 giây), có thể bao gồm khoảng nghỉ tự nhiên hoặc nhiễu.",
    }


class LocalAudioStorageService(AudioStorageService):
    def __init__(self):
        self.root = Path(settings.audio_storage_dir).resolve()

    def resolve(self, key: str) -> Path:
        path = (self.root / key).resolve()
        if not path.is_relative_to(self.root) or path == self.root:
            raise AppError(404, "Không tìm thấy bản ghi.")
        return path

    def remove(self, key: str) -> None:
        self.resolve(key).unlink(missing_ok=True)

    async def store(self, upload: UploadFile, user_id: str) -> StoredAudio:
        mime = (upload.content_type or "").split(";")[0].strip().lower()
        if mime not in SUPPORTED_MIMES:
            raise AppError(
                415,
                "Định dạng ghi âm chưa được hỗ trợ. Vui lòng dùng WebM, MP4, Ogg, MP3 hoặc WAV.",
                "audio_format",
            )
        directory = self.root / str(UUID(user_id))
        directory.mkdir(parents=True, exist_ok=True)
        identifier = uuid4().hex
        raw, normalized = directory / f"{identifier}.upload", directory / f"{identifier}.wav"
        total, digest = 0, hashlib.sha256()
        completed = False
        try:
            with raw.open("xb") as target:
                while chunk := await upload.read(1024 * 1024):
                    total += len(chunk)
                    if total > settings.max_speaking_audio_mb * 1024 * 1024:
                        raise AppError(
                            413, f"Bản ghi vượt quá {settings.max_speaking_audio_mb} MB.", "audio_too_large"
                        )
                    digest.update(chunk)
                    await run_in_threadpool(target.write, chunk)
            if total < 100:
                raise AppError(422, "Bản ghi trống hoặc quá ngắn.", "empty_audio")
            try:
                process = await asyncio.create_subprocess_exec(
                    "ffmpeg",
                    "-nostdin",
                    "-hide_banner",
                    "-loglevel",
                    "error",
                    "-protocol_whitelist",
                    "file,pipe",
                    "-i",
                    str(raw),
                    "-map",
                    "0:a:0",
                    "-vn",
                    "-ac",
                    "1",
                    "-ar",
                    "16000",
                    "-t",
                    str(settings.max_speaking_audio_seconds + 1),
                    "-c:a",
                    "pcm_s16le",
                    "-y",
                    str(normalized),
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.DEVNULL,
                )
            except FileNotFoundError:
                raise AppError(
                    503,
                    "Dịch vụ xử lý audio chưa sẵn sàng. Cần cài FFmpeg trên backend.",
                    "audio_processor_missing",
                ) from None
            try:
                await asyncio.wait_for(process.wait(), timeout=60)
            except (TimeoutError, asyncio.CancelledError):
                process.kill()
                await process.wait()
                raise AppError(
                    422, "Không thể xử lý bản ghi này. Hãy thử bản ghi ngắn hơn.", "audio_decode_error"
                ) from None
            if process.returncode != 0 or not normalized.exists():
                raise AppError(422, "Tệp không chứa audio hợp lệ hoặc bị hỏng.", "audio_decode_error")
            metrics = await run_in_threadpool(measure_wav, normalized)
            duration = metrics["duration_seconds"]
            if duration < 0.5 or duration > settings.max_speaking_audio_seconds:
                raise AppError(
                    422,
                    f"Bản ghi phải dài từ 0,5 đến {settings.max_speaking_audio_seconds} giây.",
                    "audio_duration",
                )
            completed = True
            return StoredAudio(
                str(normalized.relative_to(self.root)),
                digest.hexdigest(),
                round(duration * 1000),
                normalized.stat().st_size,
                "audio/wav",
                metrics,
            )
        finally:
            await upload.close()
            raw.unlink(missing_ok=True)
            if not completed:
                normalized.unlink(missing_ok=True)
