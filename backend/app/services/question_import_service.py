import base64
import hashlib
import io
import re
import warnings
from pathlib import Path
from uuid import uuid4

from fastapi.concurrency import run_in_threadpool
from PIL import Image, UnidentifiedImageError
from pypdf import PdfReader
from sqlalchemy import func, select

from app.common.errors import AppError
from app.core.config import settings
from app.models.library import QuestionImportFile
from app.schemas.library import LibraryDocument
from app.validators.library_import import guard_source_wording

MAX_FILE_BYTES = 20 * 1024 * 1024
MAX_PAGES = 20
MIMES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
    ".pdf": "application/pdf",
}


def inspect_file(data, filename, mime):
    suffix = Path(filename).suffix.lower()
    expected = MIMES.get(suffix)
    if not expected or mime not in (expected, "application/octet-stream", "", None):
        raise AppError(422, "Chỉ nhận JPG, JPEG, PNG, WEBP hoặc PDF đúng định dạng.")
    try:
        if expected == "application/pdf":
            if not data.startswith(b"%PDF-"):
                raise ValueError()
            pdf = PdfReader(io.BytesIO(data), strict=True)
            if pdf.is_encrypted:
                raise AppError(422, "PDF có mật khẩu. Hãy xuất bản không có mật khẩu trước khi nhập.")
            count = len(pdf.pages)
            if not 1 <= count <= MAX_PAGES:
                raise AppError(422, f"Mỗi PDF cần có 1–{MAX_PAGES} trang.")
            return expected, count
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(data)) as img:
                if (
                    Image.MIME.get(img.format) != expected
                    or img.width * img.height > 25_000_000
                    or getattr(img, "n_frames", 1) != 1
                ):
                    raise ValueError()
                img.verify()
        return expected, 1
    except AppError:
        raise
    except (Exception, UnidentifiedImageError):
        raise AppError(
            422, "Tệp hỏng, không đúng định dạng, ảnh động hoặc ảnh vượt 25 megapixel.", "invalid_import_file"
        ) from None


def normalize(text):
    return re.sub(r"\s+", " ", text or "").strip()


def guard_extracted_keys(parsed, raw_text=None):
    """Require an explicit extracted key citation; text imports additionally verify it against source."""
    for item in parsed.items:
        for passage in item.content.reading:
            for question in passage.questions:
                evidence = normalize(question.answer_key_evidence)
                visible = bool(evidence) and (raw_text is None or evidence in normalize(raw_text))
                # A citation must actually pair the source question number with the claimed letter.
                pair = (
                    re.search(
                        rf"(?<!\d){question.question_number}\s*[.)\-:=]?\s*{question.correct_answer}\b",
                        evidence,
                        re.IGNORECASE,
                    )
                    if question.correct_answer
                    else None
                )
                if question.correct_answer and (
                    not visible or not pair or question.answer_key_source != "provided"
                ):
                    question.correct_answer = None
                    question.answer_key_source = "unknown"
                    question.answer_key_evidence = None
                    item.warnings.append(
                        f"Câu {question.question_number}: chưa xác minh được đáp án trong nguồn; đã để trống."
                    )
                if question.correct_answer is None:
                    question.answer_key_source = "unknown"
        if item.content.reading and any(
            q.correct_answer is None for p in item.content.reading for q in p.questions
        ):
            item.warnings.append("Chưa có đủ đáp án. Bạn có thể bổ sung thủ công sau khi lưu.")
    return parsed


def detection_hints(raw):
    """Weak deterministic hints supplement, never override, AI classification."""
    text = (raw or "").casefold()
    hints = []
    for count, task in ((120, "task_1"), (250, "task_2")):
        if re.search(rf"(?:at least|minimum|tối thiểu)\s+{count}\s+(?:words|từ)", text):
            hints.append({"skill": "writing", "part": task, "cue": f"minimum {count} words"})
    if re.search(r"(?:reading|passage)", text) and all(
        re.search(rf"\b{letter}[.)]", text) for letter in "abcd"
    ):
        hints.append({"skill": "reading", "part": "passage", "cue": "passage and multiple-choice options"})
    if "speaking" in text:
        for part in (1, 2, 3):
            if re.search(rf"part\s*{part}\b", text):
                hints.append({"skill": "speaking", "part": f"part_{part}", "cue": f"Speaking Part {part}"})
    return hints


class QuestionImportService:
    def __init__(self, db, llm=None):
        self.db, self.llm = db, llm

    async def asset(self, asset_id, user_id):
        row = await self.db.scalar(
            select(QuestionImportFile).where(
                QuestionImportFile.id == asset_id, QuestionImportFile.user_id == user_id
            )
        )
        if not row:
            raise AppError(404, "Không tìm thấy tệp nguồn.")
        return row

    async def upload(self, file, user_id):
        data = await file.read(MAX_FILE_BYTES + 1)
        await file.close()
        if not data or len(data) > MAX_FILE_BYTES:
            raise AppError(413, "Tệp phải có nội dung và không vượt 20 MB.")
        filename = Path(file.filename or "upload").name[:250]
        mime, pages = await run_in_threadpool(inspect_file, data, filename, file.content_type)
        total = await self.db.scalar(
            select(func.coalesce(func.sum(QuestionImportFile.size), 0)).where(
                QuestionImportFile.user_id == user_id
            )
        )
        if total + len(data) > 500 * 1024 * 1024:
            raise AppError(413, "Tệp nguồn trong thư viện đã đạt giới hạn 500 MB.")
        asset_id = str(uuid4())
        folder = Path(settings.question_import_storage_dir).resolve() / user_id
        await run_in_threadpool(folder.mkdir, parents=True, exist_ok=True)
        path = folder / f"{asset_id}{Path(filename).suffix.lower()}"
        await run_in_threadpool(path.write_bytes, data)
        row = QuestionImportFile(
            id=asset_id,
            user_id=user_id,
            filename=filename,
            mime_type=mime,
            size=len(data),
            sha256=hashlib.sha256(data).hexdigest(),
            path=str(path),
            page_count=pages,
        )
        self.db.add(row)
        try:
            await self.db.commit()
        except Exception:
            path.unlink(missing_ok=True)
            raise
        return row

    async def parse(self, data, user_id):
        media, asset = [], None
        if data.asset_id:
            asset = await self.asset(data.asset_id, user_id)
            path = Path(asset.path)
            if not path.is_file():
                raise AppError(404, "Tệp nguồn không còn trên bộ lưu trữ.")
            encoded = base64.b64encode(await run_in_threadpool(path.read_bytes)).decode()
            url = f"data:{asset.mime_type};base64,{encoded}"
            media = (
                [{"type": "input_file", "filename": asset.filename, "file_data": url}]
                if asset.mime_type == "application/pdf"
                else [{"type": "input_image", "image_url": url, "detail": "high"}]
            )
        parsed = await self.llm.parse_library_question(
            {
                "source_text": data.text,
                "classification_hints": detection_hints(data.text),
                "source_filename": asset.filename if asset else None,
            },
            user_id,
            media,
        )
        parsed = guard_source_wording(guard_extracted_keys(parsed, data.text), data.text)
        items = []
        for item in parsed.items:
            item.content.practice_asset_ids = []
            doc = LibraryDocument(
                title=item.title[:300] or "Đề đã nhập",
                skill=item.skill,
                part=item.part,
                topic=item.topic[:40] or "other",
                tags=[tag[:60] for tag in item.tags[:20] if tag.strip()],
                content=item.content,
                source_type=("pdf" if asset.mime_type == "application/pdf" else "image")
                if asset
                else "copied_text",
                asset_ids=[asset.id] if asset else [],
                source_name=asset.filename if asset else None,
            )
            items.append(
                {
                    "document": doc.model_dump(),
                    "confidence": {
                        "skill": item.skill_confidence,
                        "part": item.part_confidence,
                        "answer_key": item.answer_key_confidence,
                    },
                    "warnings": list(dict.fromkeys(item.warnings)),
                }
            )
        return {"items": items, "warnings": parsed.warnings}
