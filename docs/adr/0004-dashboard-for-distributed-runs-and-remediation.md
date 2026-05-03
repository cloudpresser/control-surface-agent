# 0004: Dashboard for Distributed Runs and Remediation

- Status: Accepted
- Date: 2026-05-02

## Context

The current frontend is a single-run operator console for a bounded decision workflow. It
proves the control-surface thesis, but the intended product is broader: an operational
dashboard for supervised runs, runtime visibility, and intervention across wrapped execution
systems.

As agents and workflows become code-defined and more operationally important, the frontend must
stop thinking primarily in terms of one local execution session and instead present the health
and progress of many runs, many workflows, and many remediation opportunities.

The dashboard is not the execution boundary of the framework. It is one control client over a
broader control layer and event model that must also integrate cleanly into real products.

## Decision

The frontend will evolve into a dashboard for monitoring supervised runs and executing
remediation actions.

The dashboard is an operations and supervisory control client, not a chat interface.

## Primary Entities

The dashboard should model and visualize at least:

- runs
- workflow versions
- step executions
- agents
- remediation actions
- telemetry timelines
- eval results surfaced through telemetry
- incidents, drift signals, and escalations

The dashboard should also make code-defined behavior legible by linking active runs to the
workflow versions and runtime policies that shaped them, even when the underlying execution is
owned by another framework such as Strands.

## Remediation Model

Remediations are executed by code-defined remediation agents.

Remediation actions may be:

- operator initiated
- policy initiated
- triggered from telemetry or eval thresholds

Each remediation must be observable as part of the run history, including who or what
triggered it, what context it received, what it changed, and what happened afterward.

## Remediation Escalation

Run remediation begins at the scope of a specific run. If the remediation exposes an
underspecified or weak part of the system, the operator may escalate that remediation into an
evolution path for future behavior.

When escalating a remediation, the operator must explicitly choose the target scope:

- `run-class`
- `workflow-version`

The dashboard should surface that choice clearly, show the evidence that motivated it, and
track whether the escalation yielded an `evolution candidate` or a rendered `repo_change`.

## Dashboard Responsibilities

- monitor active and historical runs across wrapped execution systems
- surface blocked, failed, degraded, or drifting executions
- provide entry points for remediation actions
- support escalation from run remediation into system evolution
- require explicit scope selection for escalated remediation
- show runtime telemetry and eval traces in context
- show `evolution candidate` and `repo_change` artifacts when produced
- show external evaluation, approval, or governance references when available
- make workflow and remediation history auditable

## Consequences

Positive:

- the UI aligns to the real target system rather than the prototype scenario
- operator intervention becomes a first-class runtime behavior
- remediation can be measured as part of overall system reliability
- the same dashboard can support both single-run debugging and production monitoring
- the dashboard can bridge concrete run issues to broader system evolution without becoming the
  final authority for deployment or governance

Tradeoffs:

- the frontend data model becomes broader than the current run state schema
- live updates and historical querying become more important than one-shot page fetches
- UI complexity increases because monitoring and remediation are distinct operator tasks

## Non-Goals

This ADR does not define:

- detailed visual design
- auth or RBAC behavior
- incident-management integrations

The dashboard is not the final approval authority for external governance and is not the
deployment authority for code-defined changes.

Those can be added later without changing the decision that the dashboard is centered on run
monitoring, remediation, and supervisory control.

## Migration Notes

The current page can evolve into an initial run-detail view within the future dashboard. The
existing telemetry, reconciliation, and operator action panels should be preserved as useful
detail views, but they should no longer define the entire frontend information architecture.

The future dashboard should preserve strong run-detail visibility while adding higher-level
surfaces for remediation escalation, scope selection, and external governance status.
