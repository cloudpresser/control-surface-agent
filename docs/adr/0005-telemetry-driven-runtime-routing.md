# 0005: Telemetry-Driven Runtime Routing

- Status: Accepted
- Date: 2026-05-02

## Context

The framework must support model routing based on system signals. As workflows become
distributed and agent execution becomes more varied, static model selection will not be
sufficient. The system needs a runtime policy layer that can adapt execution choices based on
latency, confidence, failures, cost, and other operating signals.

At the same time, evals should live inside telemetry for now. That means routing should
consume eval-derived runtime signals rather than own eval logic itself.

## Decision

Routing is defined as runtime policy-based selection of models, execution paths, and
escalation behaviors using telemetry-derived system signals.

Routing is a decision layer inside orchestration that reads telemetry state and chooses among
allowed runtime options declared by the workflow.

## Routing Inputs

Routing decisions may consider:

- task or step class
- workflow policy
- queue depth and backlog pressure
- latency pressure
- token or cost budget consumption
- prior step failures
- retry count
- confidence shifts across steps
- reconciliation results
- telemetry-hosted eval outputs
- evidence sufficiency
- agent health, availability, or saturation

## Routing Outputs

Routing decisions may choose:

- model family or tier
- execution priority
- stronger or cheaper inference path
- retry path with added constraints
- remediation agent invocation
- human review or escalation
- termination of autonomous progression

## Boundaries

Routing is not:

- prompt templating inside an agent
- generic service discovery
- infrastructure load balancing
- the owner of eval execution logic

Telemetry owns runtime facts, eval outputs, and audit traces. Workflows define the allowed
execution structure. Agents execute work. Routing chooses among the allowed runtime options
based on policy and current signals.

## Consequences

Positive:

- model choice becomes explainable and auditable
- the system can trade off cost, latency, and reliability dynamically
- remediation and escalation can be policy-triggered instead of purely manual
- future routing policies can evolve without changing agent implementations

Tradeoffs:

- routing policy needs careful observability so operators understand why choices were made
- poor policy design can create oscillation or excessive complexity
- workflow definitions must declare safe routing choices up front

## Non-Goals

This ADR does not choose:

- a specific routing algorithm
- a single global scoring formula
- a machine-learned policy engine

The immediate goal is an explicit routing concept with understandable policy inputs and
outputs, not an overly sophisticated optimizer.

## Migration Notes

The current `get_model()` behavior is effectively static configuration. That can remain as the
initial default policy while the framework introduces routing-aware step execution and richer
telemetry signals.
