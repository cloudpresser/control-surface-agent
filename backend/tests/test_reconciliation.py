from schemas import (
    DecisionArtifact,
    FeedbackEvent,
    OperatorAction,
    Plan,
    PlanStep,
    ReasoningClaim,
    RunInput,
    RunState,
)

from engine.feedback_loop import apply_operator_action
from engine.reconciler import full_reconcile, lightweight_reconcile


def test_lightweight_reconciliation_flags_missing_context_on_compare_step() -> None:
    run_state = {
        "current_step_id": "step_compare_fit",
        "confidence": 0.81,
        "evidence": [],
    }

    report = lightweight_reconcile(run_state, "Checked fit without context.")

    assert report.plan_drift is True
    assert report.recommended_action == "force_retrieval"
    assert report.evidence_coverage == "insufficient"
    assert "company context" in report.unknowns_detected


def test_full_reconciliation_flags_claims_without_evidence() -> None:
    run_state = {
        "evidence": [],
        "artifact": {
            "verdict": "pursue",
            "reasoning": [{"claim": "Strong fit", "evidence_ids": []}],
            "unknowns": ["team structure"],
        },
    }

    report = full_reconcile(run_state)

    assert report.plan_drift is True
    assert report.recommended_action == "force_retrieval"
    assert report.intent_alignment == "partial"


def test_retry_with_constraint_resets_downstream_steps_and_updates_intent() -> None:
    run_state = RunState(
        run_id="test-run",
        status="completed",
        input=RunInput(
            example_id="stripe_em_dev_productivity_ai",
            company_name="Stripe",
            job_description="Engineering Manager, Developer Productivity AI",
            profile_id="luiz_default",
            constraints=[],
        ),
        intent={
            "intent": "evaluate_opportunity",
            "objective": "Determine whether this role is worth pursuing",
            "constraints": [],
            "success_criteria": ["clear recommendation"],
            "missing_information": ["team structure"],
        },
        plan=Plan(
            steps=[
                PlanStep(id="step_extract_requirements", label="Extract", kind="execution", status="completed"),
                PlanStep(id="step_retrieve_context", label="Retrieve", kind="retrieval", status="completed"),
                PlanStep(id="step_compare_fit", label="Compare", kind="execution", status="completed"),
                PlanStep(id="step_assess_unknowns", label="Unknowns", kind="analysis", status="completed"),
                PlanStep(id="step_generate_artifact", label="Artifact", kind="output", status="completed"),
            ],
            needs_retrieval=True,
            assumptions=[],
            confidence=0.8,
        ),
        current_step_id="step_generate_artifact",
        artifact=DecisionArtifact(
            verdict="conditionally_pursue",
            reasoning=[ReasoningClaim(claim="Strong fit", evidence_ids=["ctx_stripe_1"])],
            risks=[],
            unknowns=[],
            next_actions=[],
            confidence=0.8,
        ),
        confidence=0.8,
    )

    updated = apply_operator_action(
        run_state,
        OperatorAction(
            action="retry_with_constraint",
            payload={"constraint": "must retrieve company context before verdict"},
            feedback=FeedbackEvent(
                target="plan_step",
                target_id="step_retrieve_context",
                feedback_type="missing_evidence",
                note="Need more context before final verdict.",
            ),
        ),
    )

    assert updated.status == "ready"
    assert updated.artifact is None
    assert updated.current_step_id == "step_retrieve_context"
    assert "must retrieve company context before verdict" in updated.intent.constraints

    statuses = {step.id: step.status for step in updated.plan.steps}
    assert statuses["step_extract_requirements"] == "completed"
    assert statuses["step_retrieve_context"] == "pending"
    assert statuses["step_compare_fit"] == "pending"
    assert statuses["step_assess_unknowns"] == "pending"
    assert statuses["step_generate_artifact"] == "pending"


def test_force_retrieval_resets_downstream_steps_and_clears_artifact() -> None:
    run_state = RunState(
        run_id="test-run-force",
        status="completed",
        input=RunInput(
            example_id="stripe_em_dev_productivity_ai",
            company_name="Stripe",
            job_description="Engineering Manager, Developer Productivity AI",
            profile_id="luiz_default",
            constraints=[],
        ),
        intent={
            "intent": "evaluate_opportunity",
            "objective": "Determine whether this role is worth pursuing",
            "constraints": [],
            "success_criteria": ["clear recommendation"],
            "missing_information": ["team structure"],
        },
        plan=Plan(
            steps=[
                PlanStep(id="step_extract_requirements", label="Extract", kind="execution", status="completed"),
                PlanStep(id="step_retrieve_context", label="Retrieve", kind="retrieval", status="completed"),
                PlanStep(id="step_compare_fit", label="Compare", kind="execution", status="completed"),
                PlanStep(id="step_assess_unknowns", label="Unknowns", kind="analysis", status="completed"),
                PlanStep(id="step_generate_artifact", label="Artifact", kind="output", status="completed"),
            ],
            needs_retrieval=False,
            assumptions=[],
            confidence=0.8,
        ),
        current_step_id="step_generate_artifact",
        artifact=DecisionArtifact(
            verdict="pursue",
            reasoning=[ReasoningClaim(claim="Strong fit", evidence_ids=["ctx_stripe_1"])],
            risks=[],
            unknowns=[],
            next_actions=[],
            confidence=0.9,
        ),
        confidence=0.9,
    )

    updated = apply_operator_action(
        run_state,
        OperatorAction(
            action="force_retrieval",
            feedback=FeedbackEvent(
                target="plan_step",
                target_id="step_retrieve_context",
                feedback_type="missing_evidence",
                note="Recheck context before deciding.",
            ),
        ),
    )

    statuses = {step.id: step.status for step in updated.plan.steps}
    assert updated.plan.needs_retrieval is True
    assert updated.artifact is None
    assert updated.current_step_id == "step_retrieve_context"
    assert statuses["step_extract_requirements"] == "completed"
    assert statuses["step_retrieve_context"] == "pending"
    assert statuses["step_compare_fit"] == "pending"
    assert statuses["step_assess_unknowns"] == "pending"
    assert statuses["step_generate_artifact"] == "pending"
