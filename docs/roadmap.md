# Roadmap

This roadmap describes the intended evolution of `control-surface-agent` from the current
single-run prototype into a distributed control system for agentic software.

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

- distributed sandboxed agents
- event-driven execution
- code-defined custom workflows
- product-facing execution APIs beyond the dashboard
- remediation-driven system evolution
- external governance integration

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

### Milestone 1: Architecture and Runtime Contracts

Goal:

- define the architectural seams needed for a distributed control system

Scope:

- ADRs for runtime, workflows, telemetry, dashboard, execution control, and remediation
- narrow event-driven `AgentRuntime` seam
- normalized causal event model
- transport-neutral execution and human-control model

Exit criteria:

- the target architecture is documented clearly enough to guide refactoring work

### Milestone 2: Event-Driven Control Plane

Goal:

- evolve the monolithic execution loop into an event-driven control plane

Scope:

- explicit run lifecycle events
- queue-aware orchestration and backpressure handling
- pause and resume semantics for workflow-bound gates
- causal linkage across control actions, runtime events, and operator actions

Exit criteria:

- runs can progress through an event-driven control path rather than only an in-process loop

### Milestone 3: Sandboxed Distributed Agent Runtime

Goal:

- execute agents as independently scalable sandboxed workers

Scope:

- runtime adapter implementation behind the `AgentRuntime` contract
- worker lifecycle events
- cancellation, admission, and rejection signals
- substrate-specific execution hidden behind framework-native runtime semantics

Exit criteria:

- at least one sandboxed distributed runtime path exists without changing workflow semantics

### Milestone 4: Code-Defined Workflow Framework

Goal:

- move from one canonical workflow to a reusable workflow framework

Scope:

- workflow definitions in code
- workflow-bound gate definitions
- custom step graphs and routing allowances
- repo-visible durable behavior rather than framework-owned mutable config

Exit criteria:

- new workflows can be added without forking the framework core

### Milestone 5: Product-Facing Execution APIs

Goal:

- let real products invoke the framework directly, not only the dashboard

Scope:

- control-plane APIs for starting runs and receiving events
- workflow-bound synchronous HITL through paused execution
- supervisory async control over active and completed runs
- unified causality across product clients and dashboard clients

Exit criteria:

- the framework can serve as an execution/control layer for product integrations

### Milestone 6: Dashboard for Distributed Operations

Goal:

- evolve the UI from a single-run console into a distributed operations dashboard

Scope:

- many-run monitoring
- agent and workflow visibility
- remediation controls
- escalation from run remediation into system evolution
- visibility into `evolution candidate` and `repo_change` outcomes

Exit criteria:

- the dashboard can supervise distributed runs rather than only one local scenario

### Milestone 7: Remediation-Driven System Evolution

Goal:

- make run remediation the controlled starting point for future system evolution

Scope:

- escalation from run remediation to broader scope
- explicit operator choice between `run-class` and `workflow-version`
- default `evolution candidate` artifacts
- overrideable remediation agents that can produce `repo_change` outcomes

Exit criteria:

- the framework can turn observed runtime issues into structured, reviewable evolution outputs

### Milestone 8: External Governance and Evaluation Integration

Goal:

- integrate with external systems that evaluate and approve broader behavior changes

Scope:

- export of structured evolution artifacts
- references to external evaluation, approval, and governance state
- documented golden paths for repository and governance automation
- causal linkage from runtime incident to external review outcome

Exit criteria:

- system evolution can move through external governance without making governance a core
  framework-owned subsystem

## Guiding Principles

- all durable behavior is defined in code
- the framework should own runtime control semantics, not a mutable config store
- telemetry and causality are core concerns, not optional add-ons
- remediation is both a runtime correction mechanism and the start of broader system evolution
- alignment and deployment governance should integrate externally rather than being fully owned
  by the framework

## Near-Term Focus

The near-term focus should stay on the parts that define the framework's identity:

- refactoring toward an event-driven control plane
- establishing the runtime and event contracts
- making workflows and human-control modes explicit
- preserving a clean boundary between runtime control and external governance

That keeps the project focused on control-system infrastructure rather than expanding too early
into a full governance platform.
