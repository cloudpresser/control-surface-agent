# Architecture Overview

This document summarizes the target architecture for `control-surface-agent` as it evolves
from a single-run thesis prototype into a distributed agent control system.

For the detailed decisions, see [`docs/adr/`](adr/README.md).

## Core Idea

The framework is modeled as a control loop for distributed agent systems.

- telemetry senses runtime behavior
- routing and orchestration decide what should happen next
- the agent runtime executes work in sandboxed workers
- remediation lets operators correct runs and shape future behavior
- the dashboard exposes monitoring and supervisory control

The framework is not just a workflow runner. It is meant to keep agent behavior legible,
auditable, and correctable over time.

## Main Components

### Control Plane

The control plane owns workflow coordination, run state transitions, routing decisions,
operator actions, and causal event handling.

### Agent Runtime

Agents execute behind a narrow, event-driven runtime seam. Workers are sandboxed and
independently scalable. The framework standardizes runtime semantics without locking itself to
one substrate.

### Code-Defined Workflows

All durable behavior is defined in code. Workflow structure, workflow-bound human gates,
routing allowances, and remediation entry points are versioned and reviewable in the
repository.

### Telemetry and Causality

The framework uses a normalized event model as the source of truth for runtime facts and causal
traceability. This covers execution, routing, remediation, escalation, and operator actions.

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

- distributed sandboxed agents
- event-driven execution and backpressure-aware control
- code-defined custom workflows
- product integrations beyond the dashboard
- remediation-driven system evolution with external governance
