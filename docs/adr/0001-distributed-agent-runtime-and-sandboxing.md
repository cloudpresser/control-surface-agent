# 0001: Distributed Agent Runtime and Sandboxing

- Status: Accepted
- Date: 2026-05-02

## Context

The current repository demonstrates a single-run control surface with a monolithic backend,
file-backed run state, and in-process orchestration. That shape is useful for proving the
supervision thesis, but it is not the target runtime for a distributed agent framework.

The framework is intended to support multiple independently scalable agents, long-running
and parallel work, operator remediation, and runtime governance. Those goals require a clear
runtime boundary for what an agent is, how it executes, and how it is isolated from the rest
of the system.

The runtime is the actuation layer of the control loop. It must execute agent work safely,
surface saturation and failures early, and remain observable enough for routing,
remediation, and operator intervention to make correct decisions.

Without a strong execution boundary, agents become library calls inside one service. That
would couple deployment, resource usage, failure modes, and security posture across the
entire framework.

## Decision

Agents will execute as sandboxed, independently scalable workers behind a platform-agnostic
runtime contract.

The system will be split into:

- a control plane responsible for workflow coordination, operator actions, policy decisions,
  telemetry ingestion, and state transitions
- a worker plane responsible for executing code-defined agents in an isolated runtime

An agent is defined in code, packaged as a worker, and executed through an explicit runtime
contract rather than through in-process function calls.

The runtime contract must be event-driven. It must expose admission, execution lifecycle,
backpressure, cancellation, and failure signals without leaking substrate-specific semantics
into workflows, telemetry, remediation, or routing APIs.

## AgentRuntime Contract

The framework will standardize one narrow runtime seam, referred to here as `AgentRuntime`.

This seam is responsible for:

- submitting agent executions
- cancelling executions
- emitting normalized execution lifecycle events
- surfacing queue, admission, and backpressure signals
- attaching substrate metadata that can be observed without changing framework semantics

This seam is not responsible for:

- workflow definitions
- routing policy
- telemetry schema ownership
- eval logic
- remediation contracts

The purpose of the seam is to isolate runtime implementation choice, not to create a broad
plugin architecture.

## Consequences

Positive:

- agents can scale independently based on workload and queue pressure
- failures are contained to the worker boundary rather than crashing the control plane
- resource limits can be applied per agent class
- network and secret access can be restricted per worker type
- different agents can evolve on different deployment cadences
- the framework can ship on a managed substrate without making that substrate its identity

Tradeoffs:

- local development becomes more operationally complex than a single process
- the framework must support asynchronous, event-driven execution and partial progress
- inter-agent communication must be explicit and observable
- packaging and deployment become first-class concerns earlier
- a poorly designed runtime seam could add unnecessary abstraction layers

## Runtime Contract

Each worker execution must receive:

- run identifier
- workflow identifier and version
- step identifier
- input payload
- policy and routing context
- correlation and tracing metadata

Each worker execution must produce or emit:

- structured result payload
- normalized execution lifecycle events
- usage and cost data when available
- failure classification when execution does not succeed
- eval hook outputs when present

The runtime must also surface:

- execution accepted or rejected signals
- execution started, heartbeat, completed, failed, timed out, and cancelled signals
- queue wait and saturation signals needed for backpressure-aware control decisions

## Isolation Requirements

The sandbox boundary must support:

- per-worker CPU and memory limits
- constrained filesystem access
- explicit environment and secret injection
- default-deny network posture with allowlisted egress where needed
- execution timeouts and cancellation
- reproducible deployment artifacts per version

Self-managed containers are a strong reference implementation of this boundary, but they are
not the only allowed implementation.

## Event-Driven Requirement

The runtime must be event-driven from the start.

Backpressure is an early architectural concern, so the runtime must not hide queue pressure,
admission failure, or worker saturation behind synchronous request-response behavior. The
control plane needs those signals in time to route work safely, defer non-critical work,
trigger remediation, or escalate to operators.

## Alternatives Considered

### Self-managed container workers

Pros:

- strongest control over isolation, networking, and execution behavior
- easiest fit for arbitrary code-defined agents
- preserves maximum portability across environments

Cons:

- highest operational burden
- requires owning more worker lifecycle and platform concerns

### Managed runtime substrate such as AWS AgentCore

Pros:

- lower operational burden for worker execution and scaling
- easier integration with an AWS deployment model
- faster path to production operations

Cons:

- increased substrate lock-in risk
- pressure to let provider-specific execution semantics leak upward
- greater risk that the framework starts to look like an AWS-native control surface rather
  than a runtime-agnostic framework

Managed substrates are allowed as implementations behind the runtime contract, but they must
not define the framework's public execution model.

## Non-Goals

This ADR does not choose:

- a specific runtime substrate
- a specific container orchestrator
- a specific queue or event bus technology
- a multi-tenant security model for third-party user code

Those choices can be made later without changing the primary decision that agents execute as
sandboxed, independently scalable workers behind a narrow event-driven runtime seam.

## Migration Notes

The current backend orchestration loop can remain in-process while the framework is being
refactored, but that should be treated as a prototype implementation of the future control
plane. New agent capabilities should be designed against the worker contract, even if they
are temporarily executed locally during development.

The initial production implementation may choose a managed substrate such as AWS AgentCore for
operational simplicity, provided the framework keeps its execution contract, workflow model,
telemetry model, and remediation model substrate-agnostic.
