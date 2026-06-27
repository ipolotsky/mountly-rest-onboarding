from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Event, Onboarding
from app.schemas import (
    AdminCost,
    AdminFeedbackRow,
    AdminMetrics,
    AdminOnboardingRow,
    AdminQuality,
    AnalyticsEvent,
    FrictionStage,
    FunnelStage,
)

SCHEMA_VERSION = 1


def track(
    session: Session,
    kind: str,
    onboarding_id: str | None = None,
    props: dict | None = None,
    device: str | None = None,
    locale: str | None = None,
    session_id: str | None = None,
    note: str | None = None,
) -> None:
    event = Event(
        kind=kind,
        onboarding_id=onboarding_id,
        session_id=session_id,
        device=device,
        locale=locale,
        props=props or {},
        note=note,
    )
    session.add(event)
    session.flush()
    _forward_to_amplitude(kind, onboarding_id, props or {})


def track_client_event(session: Session, event: AnalyticsEvent) -> None:
    track(
        session=session,
        kind=event.name,
        onboarding_id=event.onboarding_id,
        props=event.props or {},
        device=event.device,
        locale=event.locale,
        session_id=event.session_id,
    )


def _forward_to_amplitude(kind: str, onboarding_id: str | None, props: dict) -> None:
    if not settings.amplitude_api_key:
        return
    # Amplitude integration is scaffolded but intentionally not provisioned for the take-home.
    # With a key set this is where the HTTP forward to the Amplitude HTTP v2 API would happen.
    return


def _is_publishable(row: Onboarding) -> bool:
    if row.step < 4:
        return False
    confirmed = row.confirmed or {}
    if not (confirmed.get("legal") and confirmed.get("banking") and confirmed.get("menu")):
        return False
    legal = row.legal or {}
    banking = row.banking or {}
    legal_fields = legal.get("fields", {})
    banking_fields = banking.get("fields", {})
    legal_ok = bool((legal_fields.get("siren") or {}).get("valid"))
    banking_ok = bool((banking_fields.get("iban") or {}).get("valid"))
    menu = row.menu or {}
    groups = menu.get("groups", [])
    menu_ok = any(group.get("items") for group in groups)
    return legal_ok and banking_ok and menu_ok


def _row_status(row: Onboarding) -> str:
    if _is_publishable(row):
        return "publishable"
    if row.step >= 4:
        return "completed"
    return "in_progress"


def admin_onboardings(session: Session) -> list[AdminOnboardingRow]:
    rows = session.execute(select(Onboarding)).scalars().all()
    cost_by_onboarding = _cost_by_onboarding(session)

    output: list[AdminOnboardingRow] = []
    for row in rows:
        legal = row.legal or {}
        registry = legal.get("registry")
        registry_status = registry.get("status") if isinstance(registry, dict) else None
        output.append(
            AdminOnboardingRow(
                id=row.id,
                status=_row_status(row),
                device=row.device,
                step=row.step,
                created_at=row.created_at.isoformat(),
                ttv_ms=_time_to_value_ms(session, row.id),
                ai_cost_eur=round(cost_by_onboarding.get(row.id, 0.0), 6),
                registry_status=registry_status,
                csat=row.csat,
            )
        )
    return output


def admin_feedback(session: Session) -> list[AdminFeedbackRow]:
    events = (
        session.execute(
            select(Event)
            .where(Event.kind == "feedback_submitted")
            .order_by(Event.created_at.desc(), Event.id.desc())
        )
        .scalars()
        .all()
    )
    onboardings = {row.id: row for row in session.execute(select(Onboarding)).scalars().all()}

    output: list[AdminFeedbackRow] = []
    seen: set[str] = set()
    for event in events:
        # Events are newest-first; keep only the most recent feedback per onboarding.
        if event.onboarding_id is None or event.onboarding_id in seen:
            continue
        seen.add(event.onboarding_id)
        props = event.props or {}
        answers = props.get("answers")
        answers = answers if isinstance(answers, dict) else {}
        csat = props.get("csat")
        row = onboardings.get(event.onboarding_id)
        output.append(
            AdminFeedbackRow(
                id=event.onboarding_id,
                csat=csat if isinstance(csat, int) else None,
                helped=_clean_text(answers.get("helped")),
                improve=_clean_text(answers.get("improve")),
                submitted_at=event.created_at.isoformat(),
                device=row.device if row is not None else "desktop",
                status=_row_status(row) if row is not None else "in_progress",
            )
        )
    return output


def _clean_text(value: object) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _cost_by_onboarding(session: Session) -> dict[str, float]:
    events = session.execute(select(Event).where(Event.kind == "parse_completed")).scalars().all()
    totals: dict[str, float] = defaultdict(float)
    for event in events:
        if event.onboarding_id is None:
            continue
        totals[event.onboarding_id] += float(event.props.get("cost_eur", 0.0))
    return totals


def _time_to_value_ms(session: Session, onboarding_id: str) -> int | None:
    # A resumed onboarding can carry more than one started/completed event; take the
    # earliest of each so this never raises MultipleResultsFound (which would 500 the
    # whole admin dashboard).
    started = (
        session.execute(
            select(Event)
            .where(Event.kind == "onboarding_started", Event.onboarding_id == onboarding_id)
            .order_by(Event.created_at.asc())
        )
        .scalars()
        .first()
    )
    completed = (
        session.execute(
            select(Event)
            .where(Event.kind == "onboarding_completed", Event.onboarding_id == onboarding_id)
            .order_by(Event.created_at.asc())
        )
        .scalars()
        .first()
    )
    if started is None or completed is None:
        return None
    return int((completed.created_at - started.created_at).total_seconds() * 1000)


def admin_metrics(session: Session) -> AdminMetrics:
    rows = session.execute(select(Onboarding)).scalars().all()
    return AdminMetrics(
        funnel=_funnel(rows),
        ai_cost=_ai_cost(session, rows),
        quality=_quality(session, rows),
        friction=_friction(session, rows),
    )


def _funnel(rows: list[Onboarding]) -> list[FunnelStage]:
    stages = ["started", "legal_done", "banking_done", "menu_done", "publishable"]
    counts: dict[str, dict[str, int]] = {stage: {"mobile": 0, "desktop": 0} for stage in stages}
    for row in rows:
        device = "mobile" if row.device == "mobile" else "desktop"
        counts["started"][device] += 1
        if row.step >= 2:
            counts["legal_done"][device] += 1
        if row.step >= 3:
            counts["banking_done"][device] += 1
        if row.step >= 4:
            counts["menu_done"][device] += 1
        if _is_publishable(row):
            counts["publishable"][device] += 1
    return [
        FunnelStage(step=stage, mobile=counts[stage]["mobile"], desktop=counts[stage]["desktop"])
        for stage in stages
    ]


def _ai_cost(session: Session, rows: list[Onboarding]) -> AdminCost:
    events = session.execute(select(Event).where(Event.kind == "parse_completed")).scalars().all()
    by_model: dict[str, float] = defaultdict(float)
    by_step: dict[str, float] = defaultdict(float)
    total_cost = 0.0
    for event in events:
        cost = float(event.props.get("cost_eur", 0.0))
        total_cost += cost
        by_model[str(event.props.get("model", "unknown"))] += cost
        by_step[str(event.props.get("step", "unknown"))] += cost

    publishable_count = sum(1 for row in rows if _is_publishable(row))
    per_publishable = round(total_cost / publishable_count, 6) if publishable_count else 0.0
    return AdminCost(
        per_publishable_eur=per_publishable,
        by_model={key: round(value, 6) for key, value in by_model.items()},
        by_step={key: round(value, 6) for key, value in by_step.items()},
    )


def _quality(session: Session, rows: list[Onboarding]) -> AdminQuality:
    field_events = (
        session.execute(select(Event).where(Event.kind == "field_resolved")).scalars().all()
    )
    accepted: dict[str, int] = defaultdict(int)
    total: dict[str, int] = defaultdict(int)
    for event in field_events:
        doc_type = event.props.get("doc_type")
        if doc_type not in ("legal", "banking", "menu"):
            continue
        if not event.props.get("parsed_value_present"):
            continue
        total[doc_type] += 1
        if event.props.get("resolution") == "accepted_as_is":
            accepted[doc_type] += 1

    auto_fill = {
        doc_type: round(accepted[doc_type] / total[doc_type], 4) if total[doc_type] else 0.0
        for doc_type in ("legal", "banking", "menu")
    }

    registry_events = (
        session.execute(select(Event).where(Event.kind == "registry_verification_result"))
        .scalars()
        .all()
    )
    registry_success = sum(
        1 for event in registry_events if event.props.get("lookup_status") == "match"
    )
    registry_rate = round(registry_success / len(registry_events), 4) if registry_events else 0.0

    menu_added, menu_total = _menu_hand_added(rows)
    menu_hand_added_share = round(menu_added / menu_total, 4) if menu_total else 0.0

    low_conf, field_total = _low_confidence_rate(rows)
    low_confidence_rate = round(low_conf / field_total, 4) if field_total else 0.0

    return AdminQuality(
        auto_fill_acceptance=auto_fill,
        menu_hand_added_share=menu_hand_added_share,
        registry_success_rate=registry_rate,
        low_confidence_rate=low_confidence_rate,
    )


def _menu_hand_added(rows: list[Onboarding]) -> tuple[int, int]:
    added = 0
    total = 0
    for row in rows:
        menu = row.menu or {}
        for group in menu.get("groups", []):
            for item in group.get("items", []):
                total += 1
                if item.get("provenance") in ("user_added",):
                    added += 1
    return added, total


def _low_confidence_rate(rows: list[Onboarding]) -> tuple[int, int]:
    low = 0
    total = 0
    for row in rows:
        for block_name in ("legal", "banking"):
            block = getattr(row, block_name) or {}
            for field in (block.get("fields") or {}).values():
                if not isinstance(field, dict):
                    continue
                if field.get("status") == "missing":
                    continue
                total += 1
                if field.get("status") == "low_confidence":
                    low += 1
        menu = row.menu or {}
        for group in menu.get("groups", []):
            for item in group.get("items", []):
                total += 1
                if (item.get("name") or {}).get("status") == "low_confidence":
                    low += 1
    return low, total


def _friction(session: Session, rows: list[Onboarding]) -> list[FrictionStage]:
    stage_steps = [("step1", 1), ("step2", 2), ("step3", 3)]
    error_events = session.execute(select(Event).where(Event.kind == "error_shown")).scalars().all()

    reason_by_step: dict[int, str | None] = {}
    for step in (1, 2, 3):
        reasons: dict[str, int] = defaultdict(int)
        for event in error_events:
            if event.props.get("step") == step:
                reasons[str(event.props.get("error_type", "unknown"))] += 1
        reason_by_step[step] = max(reasons, key=reasons.get) if reasons else None

    duration_by_step = _time_on_step_ms(session)

    output: list[FrictionStage] = []
    for label, step in stage_steps:
        reached = sum(1 for row in rows if row.step >= step)
        advanced = sum(1 for row in rows if row.step >= step + 1)
        drop_off = (reached - advanced) / reached if reached else 0.0
        durations = sorted(duration_by_step.get(step, []))
        median = durations[len(durations) // 2] if durations else None
        output.append(
            FrictionStage(
                step=label,
                drop_off=round(max(drop_off, 0.0), 4),
                top_reason=reason_by_step.get(step),
                median_ms=median,
            )
        )
    return output


def _time_on_step_ms(session: Session) -> dict[int, list[float]]:
    # Real time-on-step is the gap between landing on a step (step_viewed) and confirming
    # it (step_confirmed) for the same onboarding. The client's own duration_ms only timed
    # the confirm round-trip, so the median always collapsed to ~0; this measures dwell time.
    viewed = session.execute(select(Event).where(Event.kind == "step_viewed")).scalars().all()
    confirmed = session.execute(select(Event).where(Event.kind == "step_confirmed")).scalars().all()

    first_viewed: dict[tuple[str, int], object] = {}
    for event in viewed:
        key = _step_key(event)
        if key is None:
            continue
        current = first_viewed.get(key)
        if current is None or event.created_at < current:
            first_viewed[key] = event.created_at

    first_confirmed: dict[tuple[str, int], object] = {}
    for event in confirmed:
        key = _step_key(event)
        if key is None:
            continue
        current = first_confirmed.get(key)
        if current is None or event.created_at < current:
            first_confirmed[key] = event.created_at

    durations: dict[int, list[float]] = defaultdict(list)
    for key, viewed_at in first_viewed.items():
        confirmed_at = first_confirmed.get(key)
        if confirmed_at is None:
            continue
        delta_ms = (confirmed_at - viewed_at).total_seconds() * 1000
        if delta_ms > 0:
            durations[key[1]].append(delta_ms)
    return durations


def _step_key(event: Event) -> tuple[str, int] | None:
    step = event.props.get("step")
    if event.onboarding_id is None or not isinstance(step, int):
        return None
    return (event.onboarding_id, step)
