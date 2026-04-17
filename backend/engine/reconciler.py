from __future__ import annotations

from typing import Any

from schemas import ReconciliationReport


def lightweight_reconcile(run_state: dict[str, Any], summary: str) -> ReconciliationReport:
    evidence_count = len(run_state.get("evidence", []))
    confidence = run_state.get("confidence", 0.5)
    plan_drift = False
    unknowns = []
    recommended_action = None
    coverage = "sufficient" if evidence_count >= 1 else "insufficient"
    alignment = "strong"
    adjustment = 0.0

    if run_state.get("current_step_id") in {"step_compare_fit", "step_generate_artifact"} and evidence_count == 0:
        plan_drift = True
        alignment = "partial"
        coverage = "insufficient"
        unknowns.append("company context")
        adjustment = -0.1
        recommended_action = "force_retrieval"
    elif confidence > 0.8 and evidence_count < 1:
        alignment = "partial"
        coverage = "partial"
        adjustment = -0.08
        recommended_action = "retry_with_constraint"

    return ReconciliationReport(
        scope="lightweight",
        intent_alignment=alignment,
        evidence_coverage=coverage,
        plan_drift=plan_drift,
        unknowns_detected=unknowns,
        confidence_adjustment=adjustment,
        recommended_action=recommended_action,
        summary=summary,
    )


def full_reconcile(run_state: dict[str, Any]) -> ReconciliationReport:
    artifact = run_state.get("artifact") or {}
    evidence_count = len(run_state.get("evidence", []))
    claims = artifact.get("reasoning", [])
    claim_coverage_ok = all(claim.get("evidence_ids") for claim in claims)
    unknowns = artifact.get("unknowns", [])

    alignment = "strong"
    coverage = "sufficient"
    drift = False
    adjustment = 0.0
    recommended_action = None

    if evidence_count == 0 or not claim_coverage_ok:
        alignment = "partial"
        coverage = "insufficient"
        drift = True
        adjustment = -0.15
        recommended_action = "force_retrieval"
    elif unknowns:
        alignment = "partial"
        coverage = "partial"
        adjustment = -0.05
        recommended_action = "approve_step"

    return ReconciliationReport(
        scope="full",
        intent_alignment=alignment,
        evidence_coverage=coverage,
        plan_drift=drift,
        unknowns_detected=unknowns,
        confidence_adjustment=adjustment,
        recommended_action=recommended_action,
        summary="Full reconciliation before final artifact presentation.",
    )
