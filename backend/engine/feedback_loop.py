from __future__ import annotations

from schemas import OperatorAction, PlanStep, RunState


def apply_operator_action(run_state: RunState, operator_action: OperatorAction) -> RunState:
    run_state.operator_actions.append(operator_action)
    run_state.confidence = round(max(0.2, run_state.confidence - 0.08), 2)

    if run_state.plan is None:
        return run_state

    if operator_action.action == "force_retrieval":
        run_state.plan.needs_retrieval = True
        for step in run_state.plan.steps:
            if step.id == "step_retrieve_context":
                step.notes = "Operator forced retrieval before final verdict."
        _reset_steps_from(run_state, "step_retrieve_context")
        run_state.status = "ready"
    elif operator_action.action == "retry_with_constraint":
        constraint = operator_action.payload.get("constraint")
        if run_state.intent and constraint and constraint not in run_state.intent.constraints:
            run_state.intent.constraints.append(constraint)
        _reset_steps_from(run_state, operator_action.feedback.target_id if operator_action.feedback else "step_retrieve_context")
        run_state.status = "ready"
    elif operator_action.action == "revise_intent":
        objective = operator_action.payload.get("objective")
        if run_state.intent and objective:
            run_state.intent.objective = objective
        _reset_steps_from(run_state, "step_extract_requirements")
        run_state.status = "ready"
    elif operator_action.action == "approve_step":
        run_state.status = "ready"
    elif operator_action.action == "reject_step":
        _reset_steps_from(run_state, operator_action.feedback.target_id if operator_action.feedback else run_state.current_step_id)
        run_state.status = "ready"
    elif operator_action.action == "skip":
        for step in run_state.plan.steps:
            if step.id == (operator_action.feedback.target_id if operator_action.feedback else run_state.current_step_id):
                step.status = "skipped"
        run_state.status = "ready"
    elif operator_action.action == "escalate":
        run_state.status = "escalated"

    return run_state


def _reset_steps_from(run_state: RunState, step_id: str | None) -> None:
    if run_state.plan is None or step_id is None:
        return
    found = False
    for step in run_state.plan.steps:
        if step.id == step_id:
            found = True
        if found and step.status in {"completed", "failed", "skipped"}:
            step.status = "pending"
    run_state.current_step_id = step_id
    run_state.artifact = None
