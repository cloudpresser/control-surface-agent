# 0003: Code-Defined Workflow Definitions

- Status: Accepted
- Date: 2026-05-02

## Context

The current prototype uses a single canonical workflow encoded directly in the planner and
backend execution loop. That is enough for one scenario, but the target framework must support
custom workflows without turning each new workflow into a fork of the framework.

The system also needs to support operator intervention, remediation paths, eval hook points,
and runtime routing decisions. Those concerns cannot remain hidden in ad hoc imperative logic.

All durable behavior is defined in code. Workflow structure, gates, routing allowances,
remediation entry points, and related control semantics should remain versioned, repo-visible,
and reviewable as code-defined behavior.

## Decision

Workflows will be defined in code as versioned compositions of steps, transitions, and
policies.

Workflow definitions are framework inputs. They are not generated at runtime as the sole
source of truth, and they are not embedded as one-off orchestration branches in the control
plane.

Workflows define structured execution and workflow-bound human control. They do not need to
encode the entire supervisory surface of the system.

## Workflow Model

A workflow definition must include:

- workflow identifier and version
- declared step graph and dependency rules
- step kinds and execution contracts
- workflow-bound gate definitions where human input is required
- allowed routing options per step
- remediation entry points
- telemetry and eval hook points
- human intervention gates when required

Initial step kinds should support at least:

- agent execution
- retrieval
- analysis
- routing decision
- remediation
- eval hook
- human approval or escalation
- artifact emission

Workflow-bound gates should define at least:

- the expected response shape
- pause and resume semantics
- timeout or escalation behavior when no response arrives

Async supervisory control, including remediation escalation into future system evolution, is
not required to be encoded as workflow structure.

## Why Code-Defined

Code-defined workflows provide:

- version control and reviewability
- type-checked contracts where the host language allows it
- reusable workflow building blocks
- explicit integration with agent definitions and remediation handlers
- a clear migration path from the current hardcoded workflow

The goal is extensibility with discipline, not a free-form workflow DSL at the start.

## Consequences

Positive:

- new domains can add workflows without rewriting the framework core
- workflow versions can be tied to run history and audit traces
- the dashboard can render workflow topology from definitions rather than special-casing a
  single scenario
- remediation and routing become declared capabilities rather than hidden control flow

Tradeoffs:

- workflow authoring becomes a framework surface that must remain stable
- execution state must be carefully distinguished from workflow definition state
- code review for workflow changes becomes part of operations safety

## Non-Goals

This ADR does not require:

- a visual workflow builder
- user-authored runtime scripting
- a generic low-code automation product

The first objective is a robust code-defined workflow framework for engineering teams.

## Migration Notes

The current canonical plan can be treated as the first workflow definition and moved behind a
workflow abstraction. Existing planner behavior can then evolve from generating one fixed plan
to selecting and instantiating workflow definitions with runtime policy attached.

As execution evolves beyond the current prototype, workflow definitions should absorb explicit
workflow-bound pause and resume behavior while leaving broader supervisory controls outside the
workflow graph unless those controls are intentionally promoted into durable code-defined
behavior.
