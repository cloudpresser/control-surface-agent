from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field


StepStatus = Literal["pending", "in_progress", "completed", "skipped", "failed"]
RunStatus = Literal["ready", "in_progress", "needs_operator", "completed", "escalated"]
ReconciliationScope = Literal["lightweight", "full"]
AlignmentLevel = Literal["strong", "partial", "weak"]
CoverageLevel = Literal["sufficient", "partial", "insufficient"]
AgentMode = Literal["live", "stub"]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class RunInput(BaseModel):
    example_id: str | None = None
    company_name: str
    job_description: str
    profile_id: str
    constraints: list[str] = Field(default_factory=list)


class Intent(BaseModel):
    intent: str
    objective: str
    constraints: list[str] = Field(default_factory=list)
    success_criteria: list[str] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)


class PlanStep(BaseModel):
    id: str
    label: str
    status: StepStatus = "pending"
    kind: Literal["analysis", "retrieval", "execution", "reconciliation", "output"]
    depends_on: list[str] = Field(default_factory=list)
    notes: str | None = None


class Plan(BaseModel):
    steps: list[PlanStep]
    needs_retrieval: bool
    assumptions: list[str] = Field(default_factory=list)
    confidence: float


class RetrievalDecision(BaseModel):
    query: str
    purpose: str
    needs_retrieval: bool
    sufficiency: CoverageLevel
    confidence: float


class RoleRequirements(BaseModel):
    themes: list[str] = Field(default_factory=list)
    salary_band: str | None = None
    remote: bool = False
    seniority: str
    ambiguity_flags: list[str] = Field(default_factory=list)


class FitComparison(BaseModel):
    fit_score: float
    overlap: list[str] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)


class UnknownAssessment(BaseModel):
    unknowns: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)


class UsageMetrics(BaseModel):
    model: str
    agent_mode: AgentMode
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    latency_ms: int = 0


class EvidenceItem(BaseModel):
    id: str
    source_type: str
    title: str
    summary: str
    score: float
    purpose: str
    sufficiency: CoverageLevel | None = None
    content_ref: str | None = None


class ToolResult(BaseModel):
    tool_name: str
    status: Literal["success", "failure"]
    output: dict[str, Any]
    confidence: float
    failure_reason: str | None = None
    usage: UsageMetrics | None = None


class TelemetryEvent(BaseModel):
    timestamp: str = Field(default_factory=utc_now)
    step_id: str
    action: str
    status: str
    summary: str
    confidence_before: float
    confidence_after: float
    evidence_ids: list[str] = Field(default_factory=list)
    usage: UsageMetrics | None = None


class ReconciliationReport(BaseModel):
    timestamp: str = Field(default_factory=utc_now)
    scope: ReconciliationScope
    intent_alignment: AlignmentLevel
    evidence_coverage: CoverageLevel
    plan_drift: bool
    unknowns_detected: list[str] = Field(default_factory=list)
    confidence_adjustment: float = 0.0
    recommended_action: str | None = None
    summary: str


class FeedbackEvent(BaseModel):
    target: str
    target_id: str | None = None
    feedback_type: str
    note: str


class OperatorAction(BaseModel):
    action: str
    payload: dict[str, Any] = Field(default_factory=dict)
    feedback: FeedbackEvent | None = None
    timestamp: str = Field(default_factory=utc_now)


class ReasoningClaim(BaseModel):
    claim: str
    evidence_ids: list[str] = Field(default_factory=list)


class DecisionArtifact(BaseModel):
    verdict: str
    reasoning: list[ReasoningClaim] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    unknowns: list[str] = Field(default_factory=list)
    next_actions: list[str] = Field(default_factory=list)
    confidence: float


class RunState(BaseModel):
    run_id: str
    status: RunStatus
    input: RunInput
    intent: Intent | None = None
    plan: Plan | None = None
    current_step_id: str | None = None
    evidence: list[EvidenceItem] = Field(default_factory=list)
    telemetry: list[TelemetryEvent] = Field(default_factory=list)
    reconciliation_reports: list[ReconciliationReport] = Field(default_factory=list)
    operator_actions: list[OperatorAction] = Field(default_factory=list)
    artifacts_by_step: dict[str, dict[str, Any]] = Field(default_factory=dict)
    artifact: DecisionArtifact | None = None
    confidence: float = 0.5
    usage_summary: UsageMetrics | None = None


class ExecuteRequest(BaseModel):
    mode: Literal["next", "all"]


class FeedbackRequest(BaseModel):
    action: str
    payload: dict[str, Any] = Field(default_factory=dict)
    feedback: FeedbackEvent | None = None


class ExampleMetadata(BaseModel):
    id: str
    label: str
    company_name: str
    profile_id: str
    description: str
    job_description: str
