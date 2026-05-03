# 0007: Run Remediation, System Evolution, and External Governance

- Status: Accepted
- Date: 2026-05-03

## Context

The framework is intended to support controlled self-mutation, but it should not own an entire
alignment or governance subsystem. At the same time, not every runtime issue should become a
future system change.

The right starting point is the run itself. When a run needs remediation, that remediation may
reveal an underspecified part of the system. Operators need a disciplined way to decide when a
local remediation should remain run-scoped and when it should become a candidate for broader
code-defined behavior change.

That remediation may originate inside a wrapped execution system such as Strands and then be
projected into the control layer as a structured control event.

## Decision

Run remediation is the starting point for broader system evolution.

If a remediation exposes a weakness in current code-defined behavior, the operator may escalate
that remediation into an evolution path. The operator must explicitly choose the scope of that
evolution:

- `run-class`
- `workflow-version`

The framework owns the remediation and escalation semantics. External systems own alignment,
governance evaluation, approval, and deployment concerns.

## Run Remediation

Run remediation is the process by which an operator or remediation agent corrects, constrains,
or redirects behavior for a specific run.

Examples include:

- forcing additional retrieval
- adding a runtime constraint
- changing how a blocked run should proceed
- synthesizing a correction that addresses the current run

Run remediation is part of the active control loop. It is grounded in concrete execution context
and should always be causally linked to the run signals that required it.

## Escalation for Evolution

If a run remediation reveals an underspecified or weak part of the system, the operator may
escalate that remediation for broader future use.

This escalation step is explicit because system evolution should not be inferred silently from
a single run incident.

The operator must choose whether the learned change is intended for:

- a `run-class`
- a `workflow-version`

The framework may recommend a scope, but it must not choose that scope silently.

## Remediation Outcomes

The default outcome of escalated remediation is an `evolution candidate` artifact.

An `evolution candidate` should describe:

- the originating remediation reference
- the chosen target scope
- the intended change to code-defined behavior
- the rationale for that change
- the causal evidence supporting it

Remediation agents may be extended in code to produce a `repo_change` outcome instead.

A `repo_change` is a repo-targeted change artifact that renders the proposed behavior change in
a form suitable for external tooling and repository workflows. This does not require the core
framework to standardize on one branching, editing, or deployment toolchain.

## External Governance Boundary

The framework does not own alignment evaluation, governance approval, branch automation, or
deployment rollout.

Instead, the framework should:

- emit `evolution candidate` or `repo_change` outcomes with strong causal linkage
- expose enough structured metadata for external systems to evaluate them
- record external evaluation, approval, or governance references when available

This keeps controlled self-mutation inside the framework while delegating large-scale
validation and release authority to external systems.

## Consequences

Positive:

- system evolution is grounded in concrete runtime remediation rather than abstract policy drift
- operators remain explicitly responsible for broadening a local remediation into future
  behavior
- all durable behavior changes remain tied to code-defined artifacts
- teams can integrate with their own governance and repository automation workflows

Tradeoffs:

- the escalation step adds explicit operator work
- external governance systems must understand enough of the emitted artifact model to be useful
- some teams may need custom remediation agents to render `repo_change` outcomes in a form that
  matches their repository practices

## Non-Goals

This ADR does not require the framework to own:

- an internal governance platform
- a mutable configuration store
- a specific patch or edit format
- a specific branching or pull request automation workflow
- deployment or rollout control

Those concerns may be addressed through external systems and documented golden paths without
becoming core framework responsibilities.

## Migration Notes

The current prototype already demonstrates run-level intervention. Future work should preserve
that run-focused control loop while extending remediation so that operators can explicitly lift
local learnings into `run-class` or `workflow-version` evolution paths.
