# 0004: Dashboard for Distributed Runs and Remediation

- Status: Accepted
- Date: 2026-05-02

## Context

The current frontend is a single-run operator console for a bounded decision workflow. It
proves the control-surface thesis, but the intended product is broader: an operational
dashboard for distributed agent runs, runtime visibility, and intervention.

As agents and workflows become code-defined and distributed, the frontend must stop thinking
primarily in terms of one local execution session and instead present the health and progress
of many runs, many agents, and many remediation opportunities.

## Decision

The frontend will evolve into a dashboard for monitoring distributed agent runs and executing
remediation actions.

The dashboard is an operations product, not a chat interface.

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

## Remediation Model

Remediations are executed by code-defined remediation agents.

Remediation actions may be:

- operator initiated
- policy initiated
- triggered from telemetry or eval thresholds

Each remediation must be observable as part of the run history, including who or what
triggered it, what context it received, what it changed, and what happened afterward.

## Dashboard Responsibilities

- monitor active and historical distributed runs
- surface blocked, failed, degraded, or drifting executions
- provide entry points for remediation actions
- show runtime telemetry and eval traces in context
- make workflow and remediation history auditable

## Consequences

Positive:

- the UI aligns to the real target system rather than the prototype scenario
- operator intervention becomes a first-class runtime behavior
- remediation can be measured as part of overall system reliability
- the same dashboard can support both single-run debugging and production monitoring

Tradeoffs:

- the frontend data model becomes broader than the current run state schema
- live updates and historical querying become more important than one-shot page fetches
- UI complexity increases because monitoring and remediation are distinct operator tasks

## Non-Goals

This ADR does not define:

- detailed visual design
- auth or RBAC behavior
- incident-management integrations

Those can be added later without changing the decision that the dashboard is centered on
distributed run monitoring and remediation.

## Migration Notes

The current page can evolve into an initial run-detail view within the future dashboard. The
existing telemetry, reconciliation, and operator action panels should be preserved as useful
detail views, but they should no longer define the entire frontend information architecture.
