from __future__ import annotations

import re
from typing import Any

from schemas import ToolResult


def _detect_salary_band(text: str) -> str | None:
    match = re.search(r"\$?([0-9]{2,3}[,0-9]{0,6})\s*(?:-|to|–)\s*\$?([0-9]{2,3}[,0-9]{0,6})", text)
    if not match:
        return None
    low, high = match.groups()
    return f"${low} - ${high}"


def extract_role_requirements(job_description: str) -> ToolResult:
    text = job_description.lower()
    themes = []
    for keyword in ["ai", "agents", "developer productivity", "python", "typescript", "manager", "remote"]:
        if keyword in text:
            themes.append(keyword)

    seniority = "leadership" if "manager" in text or "lead " in text else "ic"
    requirements = {
        "themes": themes,
        "salary_band": _detect_salary_band(job_description),
        "remote": "remote" in text,
        "seniority": seniority,
        "ambiguity_flags": [
            flag
            for flag in ["team structure", "success metrics", "reporting line"]
            if flag not in text
        ],
    }
    confidence = 0.72 if themes else 0.58
    return ToolResult(
        tool_name="extract_role_requirements",
        status="success",
        output=requirements,
        confidence=confidence,
    )


def retrieve_company_context(company_name: str, company_context: dict[str, Any] | None) -> ToolResult:
    if company_context is None:
        return ToolResult(
            tool_name="retrieve_company_context",
            status="failure",
            output={},
            confidence=0.25,
            failure_reason=f"No bundled company context for {company_name}",
        )

    return ToolResult(
        tool_name="retrieve_company_context",
        status="success",
        output={
            "summary": company_context["summary"],
            "strengths": company_context.get("strengths", []),
            "risks": company_context.get("risks", []),
            "unknowns": company_context.get("unknowns", []),
        },
        confidence=company_context.get("score", 0.82),
    )


def compare_role_to_profile(role_requirements: dict[str, Any], profile: dict[str, Any], evidence: list[dict[str, Any]]) -> ToolResult:
    themes = set(role_requirements.get("themes", []))
    profile_keywords = set(profile.get("keywords", []))
    overlap = sorted(themes & profile_keywords)

    fit_score = 0.45 + (0.08 * len(overlap))
    if role_requirements.get("remote"):
        fit_score += 0.05
    if role_requirements.get("seniority") == "leadership" and profile.get("leadership_scope"):
        fit_score += 0.1
    if evidence:
        fit_score += 0.05

    fit_score = min(fit_score, 0.92)

    output = {
        "fit_score": round(fit_score, 2),
        "overlap": overlap,
        "strengths": [
            "Role themes overlap with control-systems-for-intelligent-software thesis"
            if overlap
            else "Limited theme overlap with the bundled profile"
        ],
        "gaps": [
            gap for gap in ["team scope", "org leverage", "day-to-day delivery model"] if gap not in overlap
        ],
    }
    return ToolResult(
        tool_name="compare_role_to_profile",
        status="success",
        output=output,
        confidence=round(fit_score, 2),
    )


def assess_unknowns(role_requirements: dict[str, Any], comparison: dict[str, Any], company_context: dict[str, Any] | None) -> ToolResult:
    unknowns = set(role_requirements.get("ambiguity_flags", []))
    risks = []
    if company_context:
        unknowns.update(company_context.get("unknowns", []))
        risks.extend(company_context.get("risks", []))
    if comparison.get("fit_score", 0) < 0.7:
        risks.append("Role fit is not yet strong enough to justify a high-confidence pursue verdict")

    return ToolResult(
        tool_name="assess_unknowns",
        status="success",
        output={
            "unknowns": sorted(unknowns),
            "risks": risks,
        },
        confidence=0.7 if company_context else 0.55,
    )


def generate_verdict(intent: dict[str, Any], comparison: dict[str, Any], unknowns: dict[str, Any], evidence_ids: list[str]) -> ToolResult:
    fit_score = comparison.get("fit_score", 0)
    if fit_score >= 0.82:
        verdict = "pursue"
    elif fit_score >= 0.68:
        verdict = "conditionally_pursue"
    else:
        verdict = "pass"

    reasoning = [
        {
            "claim": "The role aligns with the operator's control-systems thesis and current profile.",
            "evidence_ids": evidence_ids,
        },
        {
            "claim": "The recommendation remains bounded by explicit unknowns rather than hidden assumptions.",
            "evidence_ids": evidence_ids,
        },
    ]

    output = {
        "verdict": verdict,
        "reasoning": reasoning,
        "risks": unknowns.get("risks", []),
        "unknowns": unknowns.get("unknowns", []),
        "next_actions": [
            "Clarify team structure and reporting line with recruiter",
            "Validate performance expectations and success metrics",
        ],
        "confidence": round(min(max(fit_score, 0.45), 0.9), 2),
        "objective": intent.get("objective"),
    }
    return ToolResult(
        tool_name="generate_verdict",
        status="success",
        output=output,
        confidence=output["confidence"],
    )
