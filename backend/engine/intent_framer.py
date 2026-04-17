from __future__ import annotations

from schemas import Intent, RunInput


DEFAULT_CONSTRAINTS = [
    "optimize for long-term growth",
    "avoid generic advice",
    "surface uncertainty explicitly",
]


def frame_intent(run_input: RunInput) -> Intent:
    combined_constraints = list(dict.fromkeys(DEFAULT_CONSTRAINTS + run_input.constraints))
    missing_information = [
        "team structure",
        "performance expectations",
    ]

    if "salary" not in run_input.job_description.lower() and "$" not in run_input.job_description:
        missing_information.append("compensation details")

    return Intent(
        intent="evaluate_opportunity",
        objective=f"Determine whether the {run_input.company_name} role is worth pursuing",
        constraints=combined_constraints,
        success_criteria=[
            "clear recommendation",
            "evidence-backed reasoning",
            "explicit uncertainty",
            "next actions for the operator",
        ],
        missing_information=missing_information,
    )
