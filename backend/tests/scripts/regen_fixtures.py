"""Regenerate the golden fixtures from the real sample documents and the Claude API.

Run from the backend directory with ANTHROPIC_API_KEY set and the sample files
present under tests/fixtures/samples/ (see that folder's README):

    python tests/scripts/regen_fixtures.py

The output is schema-validated against the parsers' extraction models so the
fixtures can never silently drift from the Pydantic schema.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from app import parsers  # noqa: E402
from app.config import settings  # noqa: E402
from app.ingest import ingest_file  # noqa: E402
from app.llm import extract  # noqa: E402

SAMPLES = ROOT / "tests" / "fixtures" / "samples"
FIXTURES = ROOT / "tests" / "fixtures"


def _media_type(path: Path) -> str:
    suffix = path.suffix.lower()
    return {
        ".pdf": "application/pdf",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
    }.get(suffix, "application/octet-stream")


def _write(name: str, data: dict) -> None:
    (FIXTURES / name).write_text(json.dumps(data, indent=2, ensure_ascii=False))
    print(f"Wrote {name}")


def _extract(path: Path, output_model, instruction, model, max_tokens):
    ingested = ingest_file("regen", path.name, _media_type(path), path.read_bytes())
    result = extract(
        model=model,
        output_model=output_model,
        blocks=[ingested.block],
        instruction=instruction,
        max_tokens=max_tokens,
    )
    if result.status != "ok" or result.data is None:
        raise SystemExit(f"Could not parse {path.name}: {result.status}")
    output_model.model_validate(result.data)
    return result.data


def main() -> None:
    if not settings.anthropic_api_key:
        raise SystemExit("ANTHROPIC_API_KEY is required to regenerate fixtures")

    kbis = SAMPLES / "mock_kbis.pdf"
    if kbis.exists():
        data = _extract(
            kbis,
            parsers._LegalExtraction,
            parsers.LEGAL_INSTRUCTION,
            settings.model_legal,
            4096,
        )
        _write("legal_extraction.json", data)

    rib = SAMPLES / "mock_rib.pdf"
    if rib.exists():
        data = _extract(
            rib,
            parsers._BankingExtraction,
            parsers.BANKING_INSTRUCTION,
            settings.model_banking,
            4096,
        )
        _write("banking_extraction.json", data)

    menu_files = sorted(
        path
        for path in SAMPLES.glob("*")
        if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}
    )
    if menu_files:
        data = _extract(
            menu_files[0],
            parsers._MenuExtraction,
            parsers.MENU_INSTRUCTION,
            settings.model_menu,
            8000,
        )
        _write("menu_extraction.json", data)


if __name__ == "__main__":
    main()
