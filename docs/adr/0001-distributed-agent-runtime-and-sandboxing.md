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

Without a strong execution boundary, agents become library calls inside one service. That
would couple deployment, resource usage, failure modes, and security posture across the
entire framework.

## Decision

Agents will execute as independently deployable containerized workers.

The system will be split into:

- a control plane responsible for workflow coordination, operator actions, policy decisions,
  telemetry ingestion, and state transitions
- a worker plane responsible for executing code-defined agents inside isolated containers

An agent is defined in code, packaged as a worker, and executed through an explicit runtime
contract rather than through in-process function calls.

## Consequences

Positive:

- agents can scale independently based on workload and queue pressure
- failures are contained to the worker boundary rather than crashing the control plane
- resource limits can be applied per agent class
- network and secret access can be restricted per worker type
- different agents can evolve on different deployment cadences

Tradeoffs:

- local development becomes more operationally complex than a single process
- the framework must support asynchronous execution and partial progress
- inter-agent communication must be explicit and observable
- packaging and deployment become first-class concerns earlier

## Runtime Contract

Each worker execution must receive:

- run identifier
- workflow identifier and version
- step identifier
- input payload
- policy and routing context
- correlation and tracing metadata

Each worker execution must produce:

- structured result payload
- structured telemetry events
- usage and cost data when available
- failure classification when execution does not succeed
- eval hook outputs when present

## Isolation Requirements

Containerized workers are the default isolation boundary. The runtime must support:

- per-worker CPU and memory limits
- constrained filesystem access
- explicit environment and secret injection
- default-deny network posture with allowlisted egress where needed
- execution timeouts and cancellation
- reproducible worker images per version

## Non-Goals

This ADR does not choose:

- a specific container orchestrator
- a specific queue or event bus technology
- a multi-tenant security model for third-party user code

Those choices can be made later without changing the primary decision that agents execute as
isolated, independently deployable workers.

## Migration Notes

The current backend orchestration loop can remain in-process while the framework is being
refactored, but that should be treated as a prototype implementation of the future control
plane. New agent capabilities should be designed against the worker contract, even if they
are temporarily executed locally during development.
