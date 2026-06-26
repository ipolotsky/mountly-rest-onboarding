import base64
from typing import Literal

from pydantic import BaseModel

from app.llm import ContentBlock

PDF_MEDIA_TYPE = "application/pdf"
IMAGE_MEDIA_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_UPLOAD_BYTES = 20 * 1024 * 1024


class UnsupportedFileError(ValueError):
    pass


class FileTooLargeError(ValueError):
    pass


class IngestedFile(BaseModel):
    file_id: str
    filename: str
    media_type: str
    kind: Literal["pdf", "image"]
    block: ContentBlock


def _classify(media_type: str, filename: str) -> Literal["pdf", "image"]:
    normalized = (media_type or "").lower()
    if normalized == PDF_MEDIA_TYPE:
        return "pdf"
    if normalized in IMAGE_MEDIA_TYPES:
        return "image"
    lowered = filename.lower()
    if lowered.endswith(".pdf"):
        return "pdf"
    if lowered.endswith((".jpg", ".jpeg", ".png", ".webp", ".gif")):
        return "image"
    raise UnsupportedFileError(f"Unsupported file type: {media_type or filename}")


def _normalize_media_type(kind: Literal["pdf", "image"], media_type: str, filename: str) -> str:
    if kind == "pdf":
        return PDF_MEDIA_TYPE
    lowered = (media_type or "").lower()
    if lowered in IMAGE_MEDIA_TYPES:
        return lowered
    name = filename.lower()
    if name.endswith(".png"):
        return "image/png"
    if name.endswith(".webp"):
        return "image/webp"
    if name.endswith(".gif"):
        return "image/gif"
    return "image/jpeg"


def ingest_file(file_id: str, filename: str, media_type: str, content: bytes) -> IngestedFile:
    if len(content) > MAX_UPLOAD_BYTES:
        raise FileTooLargeError(f"File {filename} exceeds the {MAX_UPLOAD_BYTES} byte limit")

    kind = _classify(media_type, filename)
    resolved_media_type = _normalize_media_type(kind, media_type, filename)
    encoded = base64.standard_b64encode(content).decode("ascii")

    block = ContentBlock(
        role="document" if kind == "pdf" else "image",
        media_type=resolved_media_type,
        data=encoded,
    )
    return IngestedFile(
        file_id=file_id,
        filename=filename,
        media_type=resolved_media_type,
        kind=kind,
        block=block,
    )
