import time

import httpx
from pydantic import BaseModel

from app.config import settings
from app.validators import holder_matches_legal_name

_CIRCUIT_FAILURE_THRESHOLD = 3
_CIRCUIT_RESET_SECONDS = 30.0


class RegistryResult(BaseModel):
    status: str
    name_match: bool | None = None
    matched_name: str | None = None
    latency_ms: int = 0
    cached: bool = False


class _CircuitBreaker:
    def __init__(self, failure_threshold: int, reset_seconds: float) -> None:
        self._failure_threshold = failure_threshold
        self._reset_seconds = reset_seconds
        self._failure_count = 0
        self._opened_at: float | None = None

    def is_open(self) -> bool:
        if self._opened_at is None:
            return False
        if time.monotonic() - self._opened_at >= self._reset_seconds:
            self._failure_count = 0
            self._opened_at = None
            return False
        return True

    def record_success(self) -> None:
        self._failure_count = 0
        self._opened_at = None

    def record_failure(self) -> None:
        self._failure_count += 1
        if self._failure_count >= self._failure_threshold:
            self._opened_at = time.monotonic()


_breaker = _CircuitBreaker(_CIRCUIT_FAILURE_THRESHOLD, _CIRCUIT_RESET_SECONDS)
_cache: dict[str, RegistryResult] = {}


def reset_state() -> None:
    global _breaker
    _breaker = _CircuitBreaker(_CIRCUIT_FAILURE_THRESHOLD, _CIRCUIT_RESET_SECONDS)
    _cache.clear()


def verify_siren(siren: str, legal_name: str | None) -> RegistryResult:
    cached = _cache.get(siren)
    if cached is not None:
        return cached.model_copy(update={"cached": True})

    if _breaker.is_open():
        return RegistryResult(status="unavailable", name_match=None)

    started = time.monotonic()
    try:
        response = httpx.get(
            f"{settings.registry_base_url}/search",
            params={"q": siren},
            timeout=settings.registry_timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()
    except Exception:
        _breaker.record_failure()
        return RegistryResult(
            status="unavailable",
            name_match=None,
            latency_ms=int((time.monotonic() - started) * 1000),
        )

    _breaker.record_success()
    result = _interpret(payload, siren, legal_name)
    result.latency_ms = int((time.monotonic() - started) * 1000)
    _cache[siren] = result
    return result


def _interpret(payload: dict, siren: str, legal_name: str | None) -> RegistryResult:
    results = payload.get("results") or []
    match = next((entry for entry in results if str(entry.get("siren")) == siren), None)
    if match is None and results:
        match = results[0]
    if match is None:
        return RegistryResult(status="no_match", name_match=None)

    matched_name = match.get("nom_complet") or match.get("nom_raison_sociale")
    name_match = holder_matches_legal_name(legal_name, matched_name) if legal_name else None
    return RegistryResult(status="match", name_match=name_match, matched_name=matched_name)
