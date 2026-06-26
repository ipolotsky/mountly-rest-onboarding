from pathlib import Path

import pytest

from app.config import settings
from app.ingest import ingest_file
from app.parsers import parse_banking, parse_legal, parse_menu_file

SAMPLES = Path(__file__).resolve().parent / "fixtures" / "samples"

pytestmark = pytest.mark.live


def _require_key():
    if not settings.anthropic_api_key or settings.anthropic_api_key == "test-key":
        pytest.skip("ANTHROPIC_API_KEY not set")


def _require(path: Path):
    if not path.exists():
        pytest.skip(f"Sample {path.name} not present")


def test_live_legal_parse():
    _require_key()
    path = SAMPLES / "mock_kbis.pdf"
    _require(path)
    ingested = ingest_file("live", path.name, "application/pdf", path.read_bytes())
    output = parse_legal([ingested.block])
    assert output.block.status == "ready"
    assert output.block.fields.legal_name.value
    assert output.block.fields.siren.value


def test_live_banking_parse():
    _require_key()
    path = SAMPLES / "mock_rib.pdf"
    _require(path)
    ingested = ingest_file("live", path.name, "application/pdf", path.read_bytes())
    output = parse_banking([ingested.block])
    assert output.block.status == "ready"
    assert output.block.fields.iban.value


def test_live_menu_parse():
    _require_key()
    menu_files = sorted(
        path
        for path in SAMPLES.glob("*")
        if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}
    )
    if not menu_files:
        pytest.skip("No menu samples present")
    path = menu_files[0]
    media_type = "image/png" if path.suffix.lower() == ".png" else "image/jpeg"
    ingested = ingest_file("live", path.name, media_type, path.read_bytes())
    output = parse_menu_file(ingested)
    assert output.status == "ready"
    assert any(group.items for group in output.groups)
