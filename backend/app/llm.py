import json
import time
from typing import Literal, TypeVar

import anthropic
from pydantic import BaseModel

from app.config import compute_cost_eur, settings

T = TypeVar("T", bound=BaseModel)

ParseStatus = Literal["ok", "couldnt_parse"]


class ParseUsage(BaseModel):
    model: str
    tokens_in: int = 0
    tokens_out: int = 0
    latency_ms: int = 0
    cost_eur: float = 0.0


class ParseResult(BaseModel):
    status: ParseStatus
    data: dict | None = None
    usage: ParseUsage


class ContentBlock(BaseModel):
    role: Literal["document", "image", "text"]
    media_type: str | None = None
    data: str | None = None
    text: str | None = None


_client: anthropic.AsyncAnthropic | None = None


def _get_client() -> anthropic.AsyncAnthropic:
    global _client
    if _client is None:
        _client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    return _client


def _to_message_content(blocks: list[ContentBlock], instruction: str) -> list[dict]:
    content: list[dict] = []
    for block in blocks:
        if block.role == "document":
            content.append(
                {
                    "type": "document",
                    "source": {
                        "type": "base64",
                        "media_type": block.media_type or "application/pdf",
                        "data": block.data,
                    },
                }
            )
        elif block.role == "image":
            content.append(
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": block.media_type or "image/jpeg",
                        "data": block.data,
                    },
                }
            )
        elif block.role == "text" and block.text:
            content.append({"type": "text", "text": block.text})
    content.append({"type": "text", "text": instruction})
    return content


def _json_instruction(output_model: type[T]) -> str:
    keys = ", ".join(output_model.model_fields.keys())
    schema = json.dumps(output_model.model_json_schema(), ensure_ascii=False)
    return (
        "Respond with ONLY a single JSON object and nothing else: no prose, no explanation, "
        "no markdown code fences. The object must have exactly these top-level keys: "
        f"{keys}. Use null for any value that is not present on the document. "
        "Match this JSON schema for the types and nested structure:\n" + schema
    )


def _loads_lenient(text: str) -> dict:
    stripped = text.strip()
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        start = stripped.find("{")
        end = stripped.rfind("}")
        if start != -1 and end != -1 and end > start:
            return json.loads(stripped[start : end + 1])
        raise


# We intentionally do NOT use the strict structured-output grammar (messages.parse /
# output_config.format): on richer schemas the API can return 400 "Grammar compilation timed out".
# Prompting for a JSON object and validating it with Pydantic is one call, has no grammar
# compilation, and degrades to couldnt_parse on any failure (the UI always renders).
async def extract(
    model: str,
    output_model: type[T],
    blocks: list[ContentBlock],
    instruction: str,
    max_tokens: int = 4096,
) -> ParseResult:
    started = time.monotonic()
    usage = ParseUsage(model=model)
    client = _get_client()
    content = _to_message_content(blocks, instruction + "\n\n" + _json_instruction(output_model))

    try:
        response = await client.messages.create(
            model=model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": content}],
        )
        usage.latency_ms = int((time.monotonic() - started) * 1000)
        usage.tokens_in = getattr(response.usage, "input_tokens", 0) or 0
        usage.tokens_out = getattr(response.usage, "output_tokens", 0) or 0
        usage.cost_eur = compute_cost_eur(model, usage.tokens_in, usage.tokens_out)

        if response.stop_reason == "refusal":
            return ParseResult(status="couldnt_parse", data=None, usage=usage)

        text = next(
            (block.text for block in response.content if getattr(block, "type", None) == "text"),
            None,
        )
        if not text:
            return ParseResult(status="couldnt_parse", data=None, usage=usage)

        validated = output_model.model_validate(_loads_lenient(text))
        return ParseResult(status="ok", data=validated.model_dump(), usage=usage)
    except Exception:
        usage.latency_ms = int((time.monotonic() - started) * 1000)
        return ParseResult(status="couldnt_parse", data=None, usage=usage)
