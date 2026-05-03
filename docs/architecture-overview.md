# Architecture Overview

This document summarizes the target architecture for `control-surface-agent` as it evolves
from a single-run thesis prototype into a control layer for agent systems.

For the detailed decisions, see [`docs/adr/`](adr/README.md).

## Core Idea

The framework is best understood as a control layer around agent execution, not as a
replacement runtime.

It is designed to wrap systems built with Strands, LangGraph, LangChain, or custom loops and
add verification, observability, human control, remediation, and learning.

The framework is modeled as a control loop for agent systems.

- telemetry senses runtime behavior
- routing and orchestration decide what should happen next
- an execution system performs the underlying agent work
- remediation lets operators correct runs and shape future behavior
- the dashboard exposes monitoring and supervisory control

This does not replace an agent framework. It wraps it with control, observability, and
learning.

## Main Components

### Execution System

The execution system is whatever framework or loop already performs the agent work. That may be
Strands, LangGraph, LangChain, a custom loop, or an internal orchestration system.

The control layer depends on clear integration boundaries, not on ownership of the execution
substrate.

### Control Plane

The control plane owns workflow coordination, run state transitions, routing decisions,
operator actions, and causal event handling.

### Integration Boundaries

The control layer integrates with execution systems through normalized boundaries such as:

- run started, completed, failed, or cancelled
- step, tool, or model events
- verification and evaluation results
- confidence and failure signals
- workflow-bound gate requests and responses
- remediation actions and outcomes

The control layer returns or records:

- projected run state
- human gate decisions
- routing outcomes
- remediation and escalation records
- causal links across the full control loop

### Code-Defined Workflows

All durable behavior is defined in code. Workflow structure, workflow-bound human gates,
routing allowances, and remediation entry points are versioned and reviewable in the
repository.

### Telemetry and Causality

The framework uses a normalized event model as the source of truth for execution facts and
causal traceability. This covers execution, routing, remediation, escalation, and operator
actions.

OpenTelemetry complements this with cross-stack tracing and observability.

### Dashboard

The dashboard is a control client over the framework, not the execution boundary. It supports:

- run monitoring
- run remediation
- escalation of remediation into broader system evolution
- visibility into governance and evaluation references when present

### External Governance

The framework does not own alignment or deployment governance. Instead, it emits structured
artifacts that external systems can evaluate, approve, and apply through repository and
delivery workflows.

## Adoption Path

This architecture is intended to be adopted incrementally.

1. Add verification and telemetry around an existing agent loop
2. Introduce pause and human gating for low-confidence cases
3. Capture remediation as a structured signal
4. Use signals to influence routing and retries
5. Extract shared control logic into a dedicated control layer when complexity justifies it

You do not adopt the full architecture upfront.

## Human Control

The framework distinguishes two kinds of human control.

### Workflow-Bound Control

This is declared in workflow definitions and uses paused execution. Product clients or the
dashboard can respond to gates and resume execution.

### Supervisory Control

This is broader async control over runs and remediations. When a run remediation reveals an
underspecified part of the system, the operator can escalate it into system evolution.

The operator must explicitly choose whether the escalation targets:

- `run-class`
- `workflow-version`

## System Evolution

Run remediation is the starting point for controlled self-mutation.

By default, escalation produces an `evolution candidate` artifact. Remediation agents can be
extended in code to produce a `repo_change` instead when a team wants a more concrete,
repo-targeted outcome.

The framework records the causal chain from runtime issue to remediation to evolution
artifact. External systems handle broader evaluation, approval, branch automation, and
deployment concerns.

## Current State vs Target State

Today the repository is still a compact single-run prototype with an in-process backend and a
single-page control surface.

The target architecture extends that prototype toward:

- a wrapped existing execution system such as Strands
- event-driven control and run-state projection
- code-defined custom workflows
- product integrations beyond the dashboard
- remediation-driven system evolution with external governance
- optional distributed execution adapters later when scale requires them
