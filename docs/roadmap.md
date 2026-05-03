# Roadmap

This roadmap describes the intended evolution of `control-surface-agent` from the current
single-run prototype into a control layer for agent systems.

It is organized around milestones rather than exact dates. The goal is to make the sequence of
architectural work explicit without pretending the implementation order is already fixed in
detail.

## Current State

Today the repository is still a compact thesis prototype.

It currently demonstrates:

- a single-run control surface
- bounded agentic execution in one backend process
- structured telemetry and reconciliation
- operator intervention on a live run
- file-backed run state for local iteration

The target state is larger:

- wrapped execution systems such as Strands
- event-driven control and run-state projection
- code-defined custom workflows
- product-facing execution APIs beyond the dashboard
- remediation-driven system evolution
- external governance integration

## Adoption Path

Teams should be able to adopt the framework incrementally:

1. add verification and telemetry around an existing loop
2. introduce pause and human gating for low-confidence cases
3. capture remediation as structured signals
4. use signals to influence routing decisions
5. extract shared control logic into a dedicated control layer when needed

The roadmap below describes the evolution of the framework itself. It is not a claim that teams
must adopt the full target architecture upfront.

## Milestones

### Milestone 0: Thesis Prototype Baseline

Goal:

- preserve the current single-run prototype as the baseline proving the control-surface thesis

Scope:

- bounded workflow execution
- telemetry and reconciliation
- operator intervention and rerun behavior
- local deterministic stub mode

Exit criteria:

- the repo remains useful as a compact end-to-end demonstration of supervised agent execution

### Milestone 1: Wrap a Real Strands Loop

Goal:

- prove the control-layer thesis around an existing framework rather than a replacement runtime

Scope:

- choose one real Strands loop as the example integration target
- capture run lifecycle, tool, and model events
- normalize those events into the framework event model
- build a minimal run-state projection

Exit criteria:

- a real Strands run can be observed as a structured run through the control layer

### Milestone 2: Verification and Telemetry Wedge

Goal:

- make the wrapped loop useful without requiring much architectural change

Scope:

- add verification steps to the wrapped Strands loop
- emit confidence scores and failure reasons
- emit a structured trace of tool calls and major decisions
- establish causal linkage between execution events and projected run state

Exit criteria:

- low-confidence or failed runs can be identified from signals alone

### Milestone 3: Human Gate and Remediation Signal

Goal:

- add trust boundaries and capture repeated operational pain

Scope:

- confidence threshold to pause or approval gate
- operator action captured as a structured remediation record
- remediation reasons normalized into the event model

Exit criteria:

- human approval and remediation signals are visible in projected run state

### Milestone 4: Run-State Projection and Dashboard Slice

Goal:

- make the control layer legible as an operational surface

Scope:

- projected run timeline and current status
- gate state and remediation history
- lightweight dashboard or run viewer over the wrapped Strands example
- ADRs and docs that reflect the control-layer framing

Exit criteria:

- one wrapped Strands loop is inspectable end-to-end through the control layer

### Milestone 5: Signal-Driven Routing

Goal:

- use observed signals to alter behavior without replacing the execution framework

Scope:

- low confidence to alternate model, retrieval, or policy path
- repeated remediation to stronger path or human gate
- routing decisions logged causally in the event model

Exit criteria:

- the control layer can influence execution behavior from observed signals

### Milestone 6: Extract Shared Control Logic

Goal:

- centralize what is repeated across wrapped workflows

Scope:

- reusable gate logic
- reusable remediation projection logic
- reusable routing policy logic
- normalized run-state projection contracts

Exit criteria:

- multiple wrapped loops can share common control behavior

### Milestone 7: Generalized Control APIs

Goal:

- expose the control layer to products and supervisory clients

Scope:

- transport-neutral control semantics
- product-facing control clients
- dashboard clients
- query, resume, cancel, and gate responses across the same control model

Exit criteria:

- the control layer is usable by both product and dashboard clients

### Milestone 8: Remediation-Driven System Evolution

Goal:

- make run remediation the controlled starting point for future system evolution

Scope:

- escalation from run remediation to broader scope
- explicit operator choice between `run-class` and `workflow-version`
- default `evolution candidate` artifacts
- overrideable remediation agents that can produce `repo_change` outcomes

Exit criteria:

- the framework can turn observed runtime issues into structured, reviewable evolution outputs

### Milestone 9: External Governance and Optional Distributed Adapters

Goal:

- integrate with external governance while keeping distributed execution optional and
  implementation-specific

Scope:

- export of structured evolution artifacts
- references to external evaluation, approval, and governance state
- documented golden paths for repository and governance automation
- optional adapters for more distributed execution topologies when scale requires them

Exit criteria:

- system evolution can move through external governance without making governance a core
  framework-owned subsystem

## Guiding Principles

- all durable behavior is defined in code
- the framework should own control semantics, not a mutable config store
- telemetry and causality are core concerns, not optional add-ons
- remediation is both a runtime correction mechanism and the start of broader system evolution
- alignment and deployment governance should integrate externally rather than being fully owned
  by the framework

## Near-Term Focus

The near-term focus should stay on the parts that define the framework's identity:

- wrapping a real Strands loop
- establishing the event model and run-state projection
- making verification, gates, and remediation explicit
- preserving a clean boundary between control and external governance

That keeps the project focused on control-system infrastructure rather than expanding too early
into a full governance platform.
