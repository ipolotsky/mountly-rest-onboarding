import uuid
from pathlib import Path

from app.config import settings

_uploads_root = Path(settings.uploads_directory)


def _onboarding_dir(onboarding_id: str) -> Path:
    directory = _uploads_root / onboarding_id
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def new_file_id() -> str:
    return f"file_{uuid.uuid4().hex[:16]}"


def save_file(onboarding_id: str, file_id: str, content: bytes) -> str:
    directory = _onboarding_dir(onboarding_id)
    path = directory / file_id
    path.write_bytes(content)
    return str(path)


def read_file(path: str) -> bytes:
    return Path(path).read_bytes()
