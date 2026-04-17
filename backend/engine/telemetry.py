from __future__ import annotations

from schemas import TelemetryEvent


def record_event(
    step_id: str,
    action: str,
    status: str,
    summary: str,
    confidence_before: float,
    confidence_after: float,
    evidence_ids: list[str] | None = None,
) -> TelemetryEvent:
    return TelemetryEvent(
        step_id=step_id,
        action=action,
        status=status,
        summary=summary,
        confidence_before=round(confidence_before, 2),
        confidence_after=round(confidence_after, 2),
        evidence_ids=evidence_ids or [],
    )
