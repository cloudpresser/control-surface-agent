from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from engine.executors import (
    assess_unknowns,
    compare_role_to_profile,
    extract_role_requirements,
    generate_verdict,
    retrieve_company_context,
)
from engine.feedback_loop import apply_operator_action
from engine.base import get_agent_mode, get_model
from engine.intent_framer import frame_intent
from engine.planner import build_plan
from engine.reconciler import full_reconcile, lightweight_reconcile
from engine.retrieval_router import build_evidence_item, decide_retrieval
from engine.run_state import create_run, load_run_state, save_run_state
from engine.telemetry import record_event
from schemas import (
    DecisionArtifact,
    ExampleMetadata,
    ExecuteRequest,
    FeedbackRequest,
    OperatorAction,
    ReasoningClaim,
    RunInput,
    RunState,
    UsageMetrics,
)


BASE_DIR = Path(__file__).resolve().parent
FIXTURES_DIR = BASE_DIR / "fixtures"
NORMALIZED_DIR = FIXTURES_DIR / "normalized"

app = FastAPI(title="control-surface-agent")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _load_example(example_id: str) -> dict:
    path = NORMALIZED_DIR / f"{example_id}.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Unknown example {example_id}")
    return json.loads(path.read_text(encoding="utf-8"))


def _example_metadata() -> list[ExampleMetadata]:
    return [
        ExampleMetadata(
            id="stripe_em_dev_productivity_ai",
            label="Stripe EM, Developer Productivity AI (bundled example)",
            company_name="Stripe",
            profile_id="luiz_default",
            description="High-alignment role with strong company context and manageable uncertainty.",
            job_description="Engineering Manager, Developer Productivity AI. Remote US. Compensation $214,600 - $321,800. Lead a new team focused on LLM agents for engineering workflow automation and transform how engineers work.",
        ),
        ExampleMetadata(
            id="clear_pass_low_alignment",
            label="Low-alignment enterprise security role",
            company_name="LegacySecure",
            profile_id="luiz_default",
            description="Obvious pass due to thesis mismatch and weak compensation alignment.",
            job_description="Senior Security Engineer. Hybrid in office three days a week. Compensation $130,000 - $170,000. Focus on security operations, compliance controls, and incident response.",
        ),
        ExampleMetadata(
            id="ambiguous_needs_retrieval",
            label="Ambiguous agent platform role",
            company_name="OrbitFlow",
            profile_id="luiz_default",
            description="Planner should retrieve more company context before deciding.",
            job_description="Senior AI Platform Engineer. Remote possible. Build agent workflows and orchestration systems. Compensation not listed.",
        ),
        ExampleMetadata(
            id="profile_mismatch",
            label="Strong company, weaker role fit",
            company_name="Pinecone Labs",
            profile_id="luiz_default",
            description="Good company context but weaker fit to the bundled profile.",
            job_description="Senior Applied ML Researcher. Remote US. Compensation $220,000 - $260,000. Focus on retrieval modeling, ranking, and experimentation.",
        ),
    ]


def _step_by_id(run_state: RunState, step_id: str):
    if run_state.plan is None:
        return None
    for step in run_state.plan.steps:
        if step.id == step_id:
            return step
    return None


def _next_pending_step(run_state: RunState):
    if run_state.plan is None:
        return None
    for step in run_state.plan.steps:
        if step.status == "pending":
            return step
    return None


def _profile_for_run(run_state: RunState) -> dict:
    example = _load_example(run_state.input.example_id) if run_state.input.example_id else {}
    return example.get("profile", {})


def _company_context_for_run(run_state: RunState) -> dict | None:
    example = _load_example(run_state.input.example_id) if run_state.input.example_id else {}
    return example.get("company_context")


def _merge_usage(run_state: RunState, usage: UsageMetrics | None) -> None:
    if usage is None:
        return
    if run_state.usage_summary is None:
        run_state.usage_summary = UsageMetrics(
            model=usage.model,
            agent_mode=usage.agent_mode,
            prompt_tokens=usage.prompt_tokens,
            completion_tokens=usage.completion_tokens,
            total_tokens=usage.total_tokens,
            latency_ms=usage.latency_ms,
        )
        return
    run_state.usage_summary.prompt_tokens += usage.prompt_tokens
    run_state.usage_summary.completion_tokens += usage.completion_tokens
    run_state.usage_summary.total_tokens += usage.total_tokens
    run_state.usage_summary.latency_ms += usage.latency_ms
    run_state.usage_summary.model = usage.model
    run_state.usage_summary.agent_mode = usage.agent_mode


def _apply_reconciliation(run_state: RunState, scope: str, summary: str) -> None:
    invocation = lightweight_reconcile(run_state.model_dump(), summary) if scope == "lightweight" else full_reconcile(run_state.model_dump())
    report = invocation.value
    run_state.reconciliation_reports.append(report)
    _merge_usage(run_state, invocation.usage)
    run_state.confidence = round(max(0.1, min(0.95, run_state.confidence + report.confidence_adjustment)), 2)
    if report.recommended_action in {"force_retrieval", "retry_with_constraint"} and run_state.status != "completed":
        run_state.status = "needs_operator"


def _complete_step(run_state: RunState, step_id: str) -> None:
    step = _step_by_id(run_state, step_id)
    if step:
        step.status = "completed"


def _run_step(run_state: RunState) -> RunState:
    step = _next_pending_step(run_state)
    if step is None:
        run_state.status = "completed"
        return run_state

    run_state.current_step_id = step.id
    step.status = "in_progress"
    run_state.status = "in_progress"
    confidence_before = run_state.confidence

    if step.id == "step_extract_requirements":
        result = extract_role_requirements(run_state.input.job_description)
        run_state.artifacts_by_step[step.id] = result.output
        run_state.confidence = round(result.confidence, 2)
        run_state.telemetry.append(
            record_event(step.id, result.tool_name, result.status, "Extracted role requirements from job description.", confidence_before, run_state.confidence, usage=result.usage)
        )
        _merge_usage(run_state, result.usage)
        _complete_step(run_state, step.id)
        _apply_reconciliation(run_state, "lightweight", "Checked whether the extracted requirements support the current plan.")

        if run_state.plan and not run_state.plan.needs_retrieval:
            retrieval_step = _step_by_id(run_state, "step_retrieve_context")
            if retrieval_step and retrieval_step.status == "pending":
                retrieval_step.status = "skipped"
        return run_state

    if step.id == "step_retrieve_context":
        company_context = _company_context_for_run(run_state)
        result = retrieve_company_context(run_state.input.company_name, company_context)
        run_state.artifacts_by_step[step.id] = result.output
        if result.status == "success" and company_context is not None:
            evidence = build_evidence_item(company_context)
            run_state.evidence = [evidence]
        run_state.confidence = round(min(0.9, max(run_state.confidence, result.confidence)), 2)
        run_state.telemetry.append(
            record_event(
                step.id,
                result.tool_name,
                result.status,
                "Retrieved bundled company context.",
                confidence_before,
                run_state.confidence,
                [item.id for item in run_state.evidence],
                result.usage,
            )
        )
        _merge_usage(run_state, result.usage)
        _complete_step(run_state, step.id)
        _apply_reconciliation(run_state, "lightweight", "Checked whether evidence coverage is sufficient after retrieval.")
        return run_state

    if step.id == "step_compare_fit":
        requirements = run_state.artifacts_by_step.get("step_extract_requirements", {})
        profile = _profile_for_run(run_state)
        result = compare_role_to_profile(requirements, profile, [item.model_dump() for item in run_state.evidence])
        run_state.artifacts_by_step[step.id] = result.output
        run_state.confidence = round(result.confidence, 2)
        run_state.telemetry.append(
            record_event(
                step.id,
                result.tool_name,
                result.status,
                "Compared role requirements against bundled profile.",
                confidence_before,
                run_state.confidence,
                [item.id for item in run_state.evidence],
                result.usage,
            )
        )
        _merge_usage(run_state, result.usage)
        _complete_step(run_state, step.id)
        _apply_reconciliation(run_state, "lightweight", "Checked whether the fit analysis drifted from the original objective.")
        return run_state

    if step.id == "step_assess_unknowns":
        requirements = run_state.artifacts_by_step.get("step_extract_requirements", {})
        comparison = run_state.artifacts_by_step.get("step_compare_fit", {})
        company_context = _company_context_for_run(run_state)
        result = assess_unknowns(requirements, comparison, company_context)
        run_state.artifacts_by_step[step.id] = result.output
        run_state.confidence = round(min(run_state.confidence, result.confidence), 2)
        run_state.telemetry.append(
            record_event(
                step.id,
                result.tool_name,
                result.status,
                "Assessed risks, gaps, and unresolved questions.",
                confidence_before,
                run_state.confidence,
                [item.id for item in run_state.evidence],
                result.usage,
            )
        )
        _merge_usage(run_state, result.usage)
        _complete_step(run_state, step.id)
        _apply_reconciliation(run_state, "lightweight", "Checked whether the risk analysis surfaced enough uncertainty.")
        return run_state

    if step.id == "step_generate_artifact":
        comparison = run_state.artifacts_by_step.get("step_compare_fit", {})
        unknowns = run_state.artifacts_by_step.get("step_assess_unknowns", {})
        intent = run_state.intent.model_dump() if run_state.intent else {}
        evidence_ids = [item.id for item in run_state.evidence]
        result = generate_verdict(intent, comparison, unknowns, evidence_ids)
        artifact_output = result.output
        run_state.artifact = DecisionArtifact.model_validate(artifact_output)
        run_state.confidence = artifact_output["confidence"]
        run_state.telemetry.append(
            record_event(
                step.id,
                result.tool_name,
                result.status,
                "Generated structured decision artifact.",
                confidence_before,
                run_state.confidence,
                evidence_ids,
                result.usage,
            )
        )
        _merge_usage(run_state, result.usage)
        _complete_step(run_state, step.id)
        _apply_reconciliation(run_state, "full", "")
        if run_state.status != "needs_operator":
            run_state.status = "completed"
        return run_state

    return run_state


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "model": get_model(), "agent_mode": get_agent_mode()}


@app.get("/examples", response_model=list[ExampleMetadata])
def examples() -> list[ExampleMetadata]:
    return _example_metadata()


@app.post("/runs")
def create_run_endpoint(run_input: RunInput) -> dict:
    if run_input.example_id:
        example = _load_example(run_input.example_id)
        if not run_input.job_description.strip():
            run_input.job_description = example["job"]["job_description"]
        if not run_input.company_name.strip():
            run_input.company_name = example["job"]["company_name"]

    run_state = create_run(run_input)
    intent_invocation = frame_intent(run_input)
    run_state.intent = intent_invocation.value
    _merge_usage(run_state, intent_invocation.usage)
    retrieval_invocation = decide_retrieval(run_input.company_name, run_input.job_description)
    run_state.artifacts_by_step["initial_retrieval_decision"] = retrieval_invocation.value.model_dump()
    _merge_usage(run_state, retrieval_invocation.usage)
    plan_invocation = build_plan(run_state.intent, retrieval_invocation.value)
    run_state.plan = plan_invocation.value
    _merge_usage(run_state, plan_invocation.usage)
    run_state.confidence = run_state.plan.confidence
    save_run_state(run_state)
    return {"run_id": run_state.run_id, "status": run_state.status, "run_state": run_state}


@app.get("/runs/{run_id}", response_model=RunState)
def get_run(run_id: str) -> RunState:
    try:
        return load_run_state(run_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Run not found") from exc


@app.post("/runs/{run_id}/execute", response_model=RunState)
def execute_run(run_id: str, request: ExecuteRequest) -> RunState:
    try:
        run_state = load_run_state(run_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Run not found") from exc

    if request.mode == "next":
        run_state = _run_step(run_state)
    else:
        while run_state.status not in {"completed", "needs_operator", "escalated"}:
            previous_step = run_state.current_step_id
            run_state = _run_step(run_state)
            if previous_step == run_state.current_step_id and _next_pending_step(run_state) is None:
                break

    save_run_state(run_state)
    return run_state


@app.post("/runs/{run_id}/feedback", response_model=RunState)
def feedback(run_id: str, request: FeedbackRequest) -> RunState:
    try:
        run_state = load_run_state(run_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Run not found") from exc

    operator_action = OperatorAction(action=request.action, payload=request.payload, feedback=request.feedback)
    run_state = apply_operator_action(run_state, operator_action)
    save_run_state(run_state)
    return run_state


@app.get("/runs/{run_id}/artifact", response_model=DecisionArtifact)
def artifact(run_id: str) -> DecisionArtifact:
    try:
        run_state = load_run_state(run_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Run not found") from exc
    if run_state.artifact is None:
        raise HTTPException(status_code=404, detail="Artifact not available yet")
    return run_state.artifact


@app.get("/evals")
def evals() -> dict:
    return {
        "focus": [
            "schema validity",
            "retrieval correctness",
            "artifact evidence coverage",
            "recovery after feedback",
        ],
        "headline": "The key evaluation is whether the system improves after operator correction.",
    }
