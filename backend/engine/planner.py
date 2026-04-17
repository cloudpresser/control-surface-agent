from __future__ import annotations

from engine.base import AgentInvocation, invoke_structured
from schemas import Intent, Plan, PlanStep, RetrievalDecision


CANONICAL_STEPS = [
    {
        "id": "step_extract_requirements",
        "label": "Extract role requirements",
        "kind": "execution",
        "depends_on": [],
        "notes": None,
    },
    {
        "id": "step_retrieve_context",
        "label": "Retrieve company context",
        "kind": "retrieval",
        "depends_on": ["step_extract_requirements"],
        "notes": "Only execute when retrieval is required or operator forces it.",
    },
    {
        "id": "step_compare_fit",
        "label": "Compare role to profile",
        "kind": "execution",
        "depends_on": ["step_extract_requirements"],
        "notes": None,
    },
    {
        "id": "step_assess_unknowns",
        "label": "Assess risks and unknowns",
        "kind": "analysis",
        "depends_on": ["step_compare_fit"],
        "notes": None,
    },
    {
        "id": "step_generate_artifact",
        "label": "Generate structured artifact",
        "kind": "output",
        "depends_on": ["step_assess_unknowns"],
        "notes": None,
    },
]


def _stub_plan(intent: Intent, needs_retrieval: bool) -> Plan:
    steps = [PlanStep(**step) for step in CANONICAL_STEPS]

    if not needs_retrieval:
        steps[1].notes = "Planner marked retrieval optional; operator can still force it."

    return Plan(
        steps=steps,
        needs_retrieval=needs_retrieval,
        assumptions=[
            "The bundled profile is representative of the operator's current priorities.",
            "The job description text is current enough for a decision pass.",
        ],
        confidence=0.72 if needs_retrieval else 0.68,
    )


def _normalize_plan(plan: Plan, needs_retrieval: bool) -> Plan:
    candidate_steps = list(plan.steps)
    normalized_steps: list[PlanStep] = []

    for index, canonical in enumerate(CANONICAL_STEPS):
        candidate = candidate_steps[index] if index < len(candidate_steps) else None
        label = candidate.label if candidate and candidate.label else canonical["label"]
        notes = candidate.notes if candidate and candidate.notes else canonical["notes"]
        normalized_steps.append(
            PlanStep(
                id=canonical["id"],
                label=label,
                kind=canonical["kind"],
                depends_on=list(canonical["depends_on"]),
                notes=notes,
                status="pending",
            )
        )

    if not needs_retrieval:
        normalized_steps[1].notes = "Planner marked retrieval optional; operator can still force it."

    return Plan(
        steps=normalized_steps,
        needs_retrieval=needs_retrieval,
        assumptions=plan.assumptions,
        confidence=plan.confidence,
    )


def build_plan(intent: Intent, retrieval_decision: RetrievalDecision) -> AgentInvocation[Plan]:
    invocation = invoke_structured(
        "planner",
        {
            "intent": intent.model_dump(),
            "retrieval_decision": retrieval_decision.model_dump(),
        },
        Plan,
        lambda: _stub_plan(intent, retrieval_decision.needs_retrieval),
    )
    return AgentInvocation(
        value=_normalize_plan(invocation.value, retrieval_decision.needs_retrieval),
        usage=invocation.usage,
    )
