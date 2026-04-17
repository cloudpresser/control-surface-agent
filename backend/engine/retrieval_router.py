from __future__ import annotations

from typing import Any

from engine.base import AgentInvocation, invoke_structured
from schemas import CoverageLevel, EvidenceItem, RetrievalDecision


def _stub_retrieval_decision(company_name: str, job_description: str, forced: bool = False) -> RetrievalDecision:
    text = f"{company_name} {job_description}".lower()
    if forced:
        return RetrievalDecision(
            query=f"{company_name} company context and role expectations",
            purpose="operator forced retrieval before verdict",
            needs_retrieval=True,
            sufficiency="partial",
            confidence=0.9,
        )
    keywords = ["ai", "agent", "productivity", "platform", "developer", "manager"]
    needs_retrieval = any(keyword in text for keyword in keywords)
    return RetrievalDecision(
        query=f"{company_name} engineering culture expectations growth opportunities",
        purpose="understand company environment and calibrate recommendation confidence",
        needs_retrieval=needs_retrieval,
        sufficiency="partial" if needs_retrieval else "sufficient",
        confidence=0.74 if needs_retrieval else 0.66,
    )


def decide_retrieval(company_name: str, job_description: str, forced: bool = False) -> AgentInvocation[RetrievalDecision]:
    return invoke_structured(
        "retrieval_router",
        {
            "company_name": company_name,
            "job_description": job_description,
            "forced": forced,
        },
        RetrievalDecision,
        lambda: _stub_retrieval_decision(company_name, job_description, forced),
    )


def build_evidence_item(company_context: dict[str, Any]) -> EvidenceItem:
    return EvidenceItem(
        id=company_context["id"],
        source_type="company_context",
        title=company_context["title"],
        summary=company_context["summary"],
        score=company_context.get("score", 0.8),
        purpose=company_context.get("purpose", "understand company environment"),
        sufficiency=company_context.get("sufficiency", "partial"),
        content_ref=company_context.get("content_ref"),
    )


def merge_coverage(levels: list[CoverageLevel]) -> CoverageLevel:
    if not levels:
        return "insufficient"
    if "insufficient" in levels:
        return "insufficient"
    if "partial" in levels:
        return "partial"
    return "sufficient"
