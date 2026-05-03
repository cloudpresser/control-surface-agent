# 0005: Telemetry, Causality, and Runtime Routing

- Status: Accepted
- Date: 2026-05-02

## Context

The framework is modeled as a control loop rather than as a simple workflow runner.
Telemetry, causality, and runtime routing are therefore core concerns, not secondary
implementation details.

As workflows become distributed and agent execution becomes more varied, static model
selection will not be sufficient. The system needs a telemetry layer that senses the runtime,
an event model that preserves causal explanation, and a routing layer that adapts execution
choices based on system signals.

Evals live inside telemetry for now. Routing consumes eval-derived signals but does not own
eval execution logic.

## Decision

The framework will use a normalized event stream as the canonical model for runtime facts and
control-loop causality.

Routing is defined as runtime policy-based selection of models, execution paths, and
escalation behaviors using telemetry-derived system signals.

Telemetry is the sensing layer of the control loop. Routing is the decision layer of the
control loop. The runtime is the actuation layer. Remediation is a corrective control action
that may be triggered by operators or by policy.

The event taxonomy may evolve, but every adapter and control-plane component must emit enough
normalized metadata to preserve causality across the stack.

## Canonical Event Model

The normalized event stream is the framework's source of truth for:

- execution lifecycle facts
- causal relationships between runtime and orchestration decisions
- telemetry-hosted eval results
- routing inputs and routing outcomes
- remediation triggers and remediation outcomes
- escalation decisions and explicit scope selections
- emitted `evolution candidate` artifacts
- emitted `repo_change` artifacts when present
- external governance, evaluation, or approval references when present
- operator interventions that change the control path

This event model is framework-native. It must not be replaced by runtime-specific or
vendor-specific event semantics.

## Minimum Causality Fields

The full event taxonomy may evolve, but normalized events must support at least:

- `event_id`
- `event_type`
- `timestamp`
- `run_id`
- `workflow_id`
- `workflow_version`
- `step_id`
- `trace_id`
- `caused_by_event_id`
- `actor_type`
- `actor_id`
- `payload`

These fields create a causal chain without forcing the framework to over-specify the entire
event vocabulary too early.

That causal chain must be able to explain not only why a run behaved the way it did, but also
how a run remediation became a candidate for future code-defined behavior.

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

Backpressure signals are first-class routing inputs. The framework must treat queue wait,
admission failure, saturation, and execution delay as control signals rather than as passive
observability data.

The causal chain for broader system evolution should be representable as:

- runtime signal
- remediation action
- escalation decision
- explicit scope selection
- `evolution candidate` emission or `repo_change` generation
- external validation or approval reference when available

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

Telemetry owns runtime facts, eval outputs, causal event history, and audit traces.
Workflows define the allowed execution structure. Agents execute work. Routing chooses among
the allowed runtime options based on policy and current signals.

## OpenTelemetry

OpenTelemetry fits this architecture as the cross-stack tracing and observability layer.

Every service and worker should propagate trace context so that a single run can be followed
across control plane, runtime adapter, workers, remediation agents, product clients,
dashboard clients, and supporting services.

OpenTelemetry complements the normalized event model by providing:

- distributed trace correlation
- metrics for queue pressure, latency, saturation, retries, and failures
- correlated logs and span context for debugging

OpenTelemetry does not replace the framework's canonical event model. Workflow state,
causality, and operator-visible decision history should not depend on reconstructing behavior
from span trees alone.

## Consequences

Positive:

- the control loop becomes explainable across orchestration, runtime, and operator actions
- model choice becomes explainable and auditable
- the system can trade off cost, latency, and reliability dynamically
- remediation and escalation can be policy-triggered instead of purely manual
- future routing policies can evolve without changing agent implementations
- causal tracing can extend across the stack without forcing a fixed event taxonomy too early

Tradeoffs:

- normalized events and OTEL traces must be kept aligned enough to remain useful together
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

The first implementation should prioritize a stable minimum causality contract and trace
propagation across the stack. The detailed event taxonomy can expand as new workflows,
runtime adapters, and remediation paths are introduced.
