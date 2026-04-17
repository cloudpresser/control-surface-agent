# control-surface-agent

A control surface for supervised AI decision workflows.

This repository is a thesis artifact, not a chatbot demo. It demonstrates a bounded decision workflow through a real scenario, but the point is the supervision architecture: explicit intent framing, explicit planning, execution telemetry, reconciliation, operator intervention, and recovery after feedback.

## What This Repo Proves

- AI decision systems should expose a control surface, not just a chat transcript.
- The hard problem is not execution alone. It is reconciling intent against reality while the system runs.
- Reliability comes from telemetry, reconciliation, and human supervision.
- Feedback should change behavior visibly, not disappear into hidden prompt state.

## Why This Exists

This repo is an implementation companion to the `Control Systems for Intelligent Software` thesis:

- [Control Systems for Intelligent Software](https://cloudpresser.com/control-systems-for-ai)
- [AI Agents Are Control Systems](https://cloudpresser.com/writing/ai-agents-are-control-systems)

The example domain is job opportunity evaluation because it is real, evidence-rich, and inspectable. The architecture generalizes to any workflow where humans supervise non-deterministic agents.

## Control-System Architecture

This project maps directly onto the control-system architecture described in the essay:

```text
human intent -> explicit plan -> bounded execution -> telemetry -> reconciliation -> operator intervention -> recovery
```

In repo terms:

- execution: bounded evaluators extract requirements, retrieve context, compare fit, assess unknowns, and generate a verdict
- telemetry: every major step emits a structured event with confidence deltas and evidence refs
- interface: a single-page operator console surfaces live state instead of hiding it in chat
- supervision: the operator can approve, reject, revise intent, force retrieval, retry with constraints, skip, or escalate
- reconciliation: the system checks whether intent, evidence, and output still agree before presenting a final artifact

## What This Is / Is Not

This is:

- a control surface for supervised decision workflows
- a minimal but real end-to-end system with file-backed run state
- a demonstration of telemetry and reconciliation as first-class runtime concerns
- a feedback loop where operator correction changes downstream behavior

This is not:

- a generic chatbot
- an autonomous-agent theater demo
- a framework or template for every AI workflow
- a live job scraper or RAG system

## Scenario

The bundled scenario evaluates a role against a fixed profile and company context.

Inputs:

- job description
- company name
- profile fixture
- operator constraints

Outputs:

- framed intent
- revisable plan
- evidence set
- telemetry table
- reconciliation reports
- final decision artifact

The default bundled example is `Stripe EM, Developer Productivity AI`, but the input is editable before execution.

## Operator Console

The UI is intentionally closer to an operations console than a chat app.

Panels:

- Inputs
- Intent
- Plan
- Telemetry
- Evidence
- Reconciliation
- Decision Artifact
- Operator Controls

The reconciliation panel is central because it is the heart of the thesis: a script can execute, but a control system continuously checks divergence between plan and reality.

## Example Run

The normal flow is:

1. Initialize a bundled example or paste your own job description.
2. Run the workflow step by step or end to end.
3. Watch telemetry accumulate as confidence changes.
4. Review reconciliation reports after major steps.
5. Apply operator feedback when evidence is thin or intent has drifted.
6. Re-run affected steps and inspect the updated artifact.

The final artifact is structured, not just prose:

```json
{
  "verdict": "conditionally_pursue",
  "reasoning": [
    {
      "claim": "The role aligns with the operator's control-systems thesis and current profile.",
      "evidence_ids": ["ctx_stripe_1"]
    }
  ],
  "risks": ["High performance bar"],
  "unknowns": ["team structure", "performance expectations"],
  "next_actions": [
    "Clarify team structure and reporting line with recruiter"
  ],
  "confidence": 0.84
}
```

## Evals

The eval layer is small on purpose. It checks:

- schema validity
- retrieval behavior
- evidence coverage in the artifact
- recovery after operator correction

The most important evaluation is not accuracy in the abstract. It is whether the system improves after structured feedback.

## Project Structure

```text
backend/
  app.py
  schemas.py
  engine/
  fixtures/
  tests/

frontend/
  app/
  lib/

docs/
```

## Run Locally

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

If your backend is not on `http://127.0.0.1:8000`, set `NEXT_PUBLIC_API_BASE_URL` before running the frontend.

## Thesis

The architecture here is the point:

- explicit planning over hidden reasoning
- telemetry over opaque autonomy
- reconciliation over one-shot outputs
- supervision over “just trust the agent”

That is what makes an AI workflow production-worthy.
