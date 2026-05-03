# 0002: Domain Boundaries and Bounded Contexts

- Status: Accepted
- Date: 2026-05-02

## Context

The current prototype keeps intent framing, planning, execution, reconciliation, telemetry,
operator feedback, and persistence close together. That is appropriate for a compact thesis
artifact, but it will not support independent evolution of the framework's major concerns.

The target system needs clear domain boundaries so that orchestration, inference,
telemetry-driven governance, and operator remediation can evolve and scale independently.
Authentication is an example of a separate concern, but it is not being designed into the
framework at this stage.

Because the framework is modeled as a control loop, these boundaries must preserve a clean
split between sensing, decision, actuation, and operator intervention.

## Decision

The framework will adopt bounded contexts aligned to core runtime responsibilities.

The initial bounded contexts are:

- Orchestration: workflow state transitions, step scheduling, dependency handling, and run
  lifecycle management, including routing and control-policy application
- Inference: model invocation, prompt execution, model usage reporting, and provider-specific
  adaptation
- Telemetry: runtime event capture, eval hook results, causal event history, audit traces,
  observability integration, confidence signals, and metrics derived from runs
- Remediation: operator-triggered or policy-triggered recovery actions executed by
  code-defined remediation agents
- Operator Control Surface: monitoring views, intervention actions, and operator-facing run
  state presentation

Authentication and authorization are treated as external integrations for now, not as a
first-class bounded context inside this repository.

## Boundary Rules

- bounded contexts communicate through explicit APIs, commands, or events
- cross-context dependencies must flow through contracts, not internal imports into private
  implementation details
- domain language should be specific to each context and not overloaded across the system
- scaling decisions should be possible per context without requiring a full-system redeploy

## Why This Boundary Set

Orchestration is the core domain because it owns workflow progress and policy application.
Inference is separated because model providers, invocation semantics, and cost controls will
change faster than workflow semantics. Telemetry is separated because runtime observability
and eval data must remain available even when execution strategies change. It is the sensing
layer of the control loop and owns the causal event history needed to explain decisions across
the stack. Remediation is separated because corrective actions are part of the runtime system,
not just an operator UI detail. The operator surface is separated because it serves monitoring
and intervention rather than workflow execution.

Routing stays inside orchestration rather than telemetry. Telemetry reports the facts and
signals that the control loop observes. Orchestration applies policy to those signals and
chooses the next action.

## Consequences

Positive:

- the framework can replace or expand model providers without rewriting orchestration
- remediation logic can grow into a distinct subsystem instead of being embedded in UI
- telemetry and eval capture become reusable across workflows and agents
- the frontend can evolve from a single-run console into a run operations product

Tradeoffs:

- more contracts need to be maintained between contexts
- some current code paths will feel more indirect after refactoring
- local prototype simplicity is reduced in exchange for long-term modularity

## Non-Goals

This ADR does not define:

- the final repository layout for these bounded contexts
- a service-per-context deployment topology
- auth domain behavior beyond stating that it is out of scope for now

Those choices can vary while preserving the core decision to keep these domains separate.
