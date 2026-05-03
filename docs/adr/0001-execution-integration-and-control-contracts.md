# 0001: Execution Integration and Control Contracts

- Status: Accepted
- Date: 2026-05-02

## Context

The current repository demonstrates a single-run control surface with a monolithic backend,
file-backed run state, and in-process orchestration. That shape is useful for proving the
supervision thesis, but it is not the target architecture for production adoption.

Teams already build agent systems with frameworks and runtimes such as Strands, LangGraph,
LangChain, and custom loops. The missing layer is usually not another execution runtime. The
missing layer is control: verification, observability, human gates, remediation, and a way to
learn from runtime interventions over time.

The framework should therefore be modeled as a control layer around existing execution systems,
not as a prescription to replace them. It needs clear integration boundaries for how wrapped
execution systems emit signals into the control layer and how the control layer responds with
gates, routing decisions, remediation, and projected run state.

## Decision

The framework standardizes control contracts around existing execution systems.

The system is split into:

- an execution system, which may be Strands, LangGraph, LangChain, a custom loop, or another
  runtime already in use by a team
- a control layer responsible for workflow coordination, verification, telemetry ingestion,
  run-state projection, routing decisions, operator actions, remediation, and causal history

The framework does not require teams to replace their execution system or infrastructure
substrate. Instead, it requires execution systems to integrate through explicit event and
control boundaries.

The control contract must be event-driven. It must expose execution lifecycle, interruption,
verification, remediation, and failure signals without leaking framework-specific or
substrate-specific semantics into workflows, telemetry, or governance integrations.

## Integration Targets

The control layer is designed to wrap systems built with:

- Strands
- LangGraph
- LangChain
- custom loops
- internal orchestration systems

These are examples, not required dependencies.

## Control Contract

The framework standardizes one narrow integration seam between the execution system and the
control layer.

This seam is responsible for:

- emitting normalized run and step lifecycle events
- surfacing tool, model, and verification signals
- surfacing gate requests, interruptions, and resumptions
- surfacing remediation actions and outcomes
- allowing the control layer to project run state and issue control decisions back into the run

This seam is not responsible for:

- replacing the execution framework's native programming model
- dictating where or how agents are deployed
- owning external governance or deployment workflows

The purpose of the seam is to make control portable across execution systems, not to create a
broad plugin architecture.

## Required Integration Boundaries

An execution system integrated with the control layer must be able to surface:

- run started, completed, failed, or cancelled
- step, tool, or model invocation events when relevant
- verification or evaluation results
- confidence and failure signals
- workflow-bound gate requests and responses
- remediation actions and operator interventions when they occur

The control layer must be able to provide back:

- projected run state
- human gate decisions
- routing decisions or policy outcomes
- remediation actions or escalation records
- causal links between observed events and resulting control actions

## Consequences

Positive:

- teams can adopt the framework around systems they already use
- the first useful integration can be a wrapped Strands loop rather than a runtime rewrite
- the framework's value becomes control, not ownership of execution infrastructure
- multiple execution systems can share a common control model and causal vocabulary

Tradeoffs:

- integration adapters must normalize different framework-specific event models
- some execution systems may expose weaker interruption or observability hooks than others
- a poorly designed control contract could become either too generic to be useful or too tied to
  one framework's behavior

## Event-Driven Requirement

The control contract must be event-driven from the start.

Backpressure, interruption frequency, repeated remediation, and verification failures are all
control signals. The architecture must not hide them behind synchronous request-response
behavior or framework-local callbacks that cannot be projected into shared run state.

## Alternatives Considered

### Replace the existing execution framework with a framework-native runtime

Pros:

- tighter control over execution semantics
- fewer integration adapters to build

Cons:

- higher adoption resistance
- makes the framework feel like stack replacement rather than control
- overemphasizes infrastructure instead of control semantics

### Wrap an existing execution system with a control layer

Pros:

- lower adoption friction
- supports incremental integration
- matches how teams actually evolve toward stronger control and trust boundaries

Cons:

- requires careful event normalization
- control capabilities are constrained by the hooks and signals an execution system exposes

This ADR chooses the second path.

## Non-Goals

This ADR does not choose:

- a specific agent framework or runtime
- a specific infrastructure substrate
- a specific deployment topology
- a specific queue or event bus technology

Those choices can vary without changing the primary decision that the framework is a control
layer around execution systems rather than a replacement execution runtime.

## Migration Notes

The first useful vertical slice should wrap a real loop built in an existing framework. Strands
is a strong initial target because it already exposes hooks, interrupts, trace attributes, and
observability signals that map well into the control layer.

More extracted or distributed execution paths can be added later if control requirements and
scale justify them, but they should remain optional evolution paths rather than the front door
for adoption.
