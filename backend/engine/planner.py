from __future__ import annotations

from schemas import Intent, Plan, PlanStep


def build_plan(intent: Intent, needs_retrieval: bool) -> Plan:
    steps = [
        PlanStep(
            id="step_extract_requirements",
            label="Extract role requirements",
            kind="execution",
        ),
        PlanStep(
            id="step_retrieve_context",
            label="Retrieve company context",
            kind="retrieval",
            depends_on=["step_extract_requirements"],
            notes="Only execute when retrieval is required or operator forces it.",
        ),
        PlanStep(
            id="step_compare_fit",
            label="Compare role to profile",
            kind="execution",
            depends_on=["step_extract_requirements"],
        ),
        PlanStep(
            id="step_assess_unknowns",
            label="Assess risks and unknowns",
            kind="analysis",
            depends_on=["step_compare_fit"],
        ),
        PlanStep(
            id="step_generate_artifact",
            label="Generate structured artifact",
            kind="output",
            depends_on=["step_assess_unknowns"],
        ),
    ]

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
