from __future__ import annotations

from typing import Any

from schemas import CoverageLevel, EvidenceItem


def decide_retrieval(company_name: str, job_description: str, forced: bool = False) -> bool:
    text = f"{company_name} {job_description}".lower()
    if forced:
        return True
    keywords = ["ai", "agent", "productivity", "platform", "developer", "manager"]
    return any(keyword in text for keyword in keywords)


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
