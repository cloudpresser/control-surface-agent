# 0006: Execution API and Human Control Modes

- Status: Accepted
- Date: 2026-05-03

## Context

Invoking agents from the dashboard is useful for testing and supervision, but it is not a
sufficient execution model for the framework. The framework must integrate cleanly into real
products while still supporting the control surface as a first-class runtime client.

The system must also distinguish between workflow-bound human input during execution and
broader supervisory control over runs. Those concerns share a common event model, but they do
not have the same timing or structure.

## Decision

The framework will expose a transport-neutral execution and control model that supports both
product integrations and dashboard-driven supervision.

The execution model must support:

- starting a run with intent or input
- receiving streamed run and step events
- responding to workflow-bound gates
- issuing supervisory control actions over active or completed runs
- querying, resuming, and cancelling runs

The dashboard is one control client over this model. Product clients are another.

## Workflow-Bound Control

Workflow-bound human control is the structured part of human intervention that is declared in
the workflow definition.

This mode is used for cases such as:

- initial intent or prompt capture
- required approvals during execution
- required clarifications before a step can continue

The initial framework model for workflow-bound human control is paused execution.

## Paused Execution Model

When a workflow-bound gate is reached, execution pauses and emits a normalized event that
describes:

- the gate type
- the expected response shape
- the affected run and step
- any relevant context for the responder

Execution resumes when an authorized control client provides the required response, or when the
workflow's timeout or escalation behavior is triggered.

This model supports synchronous human-in-the-loop behavior from the product perspective without
requiring the architecture to commit to a specific transport or long-lived session model.

## Supervisory Async Control

Not all human control is workflow-bound. The framework must also support supervisory async
control that is not required to be encoded as workflow structure.

Supervisory control may include:

- run remediation
- escalation of remediation into future system evolution
- cancellation or pausing of runs
- annotations or control actions that alter how a run is handled

Supervisory async control uses the same event and causality model as workflow-bound control,
but it is not limited to predefined gates inside workflow definitions.

## Event and Control Semantics

The execution API must preserve a unified control model across clients.

That means:

- workflow-bound responses and supervisory actions should enter the same normalized event model
- product clients and dashboard clients should participate in the same causal trace when they
  act on a run
- control messages should be attributable to an actor and linked to the resulting run behavior

The framework intentionally leaves the underlying transport open. Different implementations may
choose different transports while preserving the same control semantics.

## Non-Goals

This ADR does not choose:

- a specific transport such as WebSocket, SSE, or gRPC
- a specific client SDK shape
- a product-specific UX for handling streamed text or live interaction

The architectural commitment is to streaming and bidirectional control semantics, not to a
particular wire protocol.

## Migration Notes

The current dashboard-triggered execution flow can remain as an early control client while the
framework evolves a more general execution API. Future work should ensure that product-facing
control and dashboard-facing control remain different clients over the same underlying runtime
model rather than diverging into separate execution paths.
