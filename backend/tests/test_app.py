from fastapi.testclient import TestClient

from app import app


client = TestClient(app)


def test_examples_available() -> None:
    response = client.get("/examples")
    assert response.status_code == 200
    assert any(example["id"] == "stripe_em_dev_productivity_ai" for example in response.json())


def test_run_flow_and_artifact() -> None:
    create_response = client.post(
        "/runs",
        json={
            "example_id": "stripe_em_dev_productivity_ai",
            "company_name": "Stripe",
            "job_description": "Engineering Manager, Developer Productivity AI. Remote US. Salary $214,600 - $321,800.",
            "profile_id": "luiz_default",
            "constraints": ["optimize for long-term growth"],
        },
    )
    assert create_response.status_code == 200
    run_id = create_response.json()["run_id"]

    execute_response = client.post(f"/runs/{run_id}/execute", json={"mode": "all"})
    assert execute_response.status_code == 200
    run_state = execute_response.json()
    assert run_state["artifact"]["verdict"] in {"pursue", "conditionally_pursue"}
    assert len(run_state["reconciliation_reports"]) >= 2

    artifact_response = client.get(f"/runs/{run_id}/artifact")
    assert artifact_response.status_code == 200
    artifact = artifact_response.json()
    assert artifact["reasoning"]
    assert all(claim["evidence_ids"] for claim in artifact["reasoning"])


def test_intent_constraints_are_deduplicated() -> None:
    response = client.post(
        "/runs",
        json={
            "example_id": "stripe_em_dev_productivity_ai",
            "company_name": "Stripe",
            "job_description": "Engineering Manager, Developer Productivity AI. Remote US.",
            "profile_id": "luiz_default",
            "constraints": ["optimize for long-term growth", "avoid generic advice"],
        },
    )

    assert response.status_code == 200
    constraints = response.json()["run_state"]["intent"]["constraints"]
    assert constraints.count("optimize for long-term growth") == 1
    assert constraints.count("avoid generic advice") == 1


def test_feedback_resets_retrieval_step() -> None:
    create_response = client.post(
        "/runs",
        json={
            "example_id": "clear_pass_low_alignment",
            "company_name": "LegacySecure",
            "job_description": "Senior Security Engineer. Hybrid. Salary $130,000 - $170,000.",
            "profile_id": "luiz_default",
            "constraints": [],
        },
    )
    run_id = create_response.json()["run_id"]
    client.post(f"/runs/{run_id}/execute", json={"mode": "next"})

    feedback_response = client.post(
        f"/runs/{run_id}/feedback",
        json={
            "action": "force_retrieval",
            "payload": {},
            "feedback": {
                "target": "plan_step",
                "target_id": "step_retrieve_context",
                "feedback_type": "missing_evidence",
                "note": "Need context before deciding.",
            },
        },
    )
    assert feedback_response.status_code == 200
    run_state = feedback_response.json()
    statuses = {step["id"]: step["status"] for step in run_state["plan"]["steps"]}
    assert statuses["step_retrieve_context"] == "pending"
    assert statuses["step_compare_fit"] == "pending"
    assert statuses["step_assess_unknowns"] == "pending"
    assert statuses["step_generate_artifact"] == "pending"
