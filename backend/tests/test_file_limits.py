import io

import pytest

from app.ingest import (
    MAX_UPLOAD_BYTES,
    FileTooLargeError,
    UnsupportedFileError,
    ingest_file,
)


def test_rejects_non_pdf_non_image():
    with pytest.raises(UnsupportedFileError):
        ingest_file("f1", "contract.docx", "application/msword", b"data")


def test_rejects_oversize_file():
    oversize = b"0" * (MAX_UPLOAD_BYTES + 1)
    with pytest.raises(FileTooLargeError):
        ingest_file("f1", "huge.pdf", "application/pdf", oversize)


def test_accepts_pdf_as_document_block():
    result = ingest_file("f1", "kbis.pdf", "application/pdf", b"%PDF-1.4")
    assert result.kind == "pdf"
    assert result.block.role == "document"
    assert result.media_type == "application/pdf"


def test_accepts_image_as_image_block():
    result = ingest_file("f1", "menu.png", "image/png", b"\x89PNG")
    assert result.kind == "image"
    assert result.block.role == "image"
    assert result.media_type == "image/png"


def test_classifies_by_extension_when_media_type_missing():
    result = ingest_file("f1", "menu.jpg", "", b"\xff\xd8\xff")
    assert result.kind == "image"
    assert result.media_type == "image/jpeg"


def _image(name: str):
    return (name, io.BytesIO(b"\x89PNG"), "image/png")


def test_api_rejects_unsupported_upload(client):
    onboarding_id = client.post("/api/onboarding", json={}).json()["id"]
    response = client.post(
        f"/api/onboarding/{onboarding_id}/menu/parse",
        files={"files": ("notes.txt", io.BytesIO(b"hello"), "text/plain")},
    )
    assert response.status_code == 415
