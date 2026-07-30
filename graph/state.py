"""
Shared state schema for the AegisOps LangGraph pipeline.

Every node reads from and writes to this single typed state object.
Keeping it explicit (rather than a free-form dict) makes the
graph auditable and easier to debug.
"""

from typing import TypedDict, Optional, List, Literal

IncidentCategory = Literal[
    "network",
    "hardware",
    "database",
    "security",
    "email",
    "application",
]

RiskLevel = Literal[
    "low",
    "medium",
    "high",
    "critical",
]


class AegisOpsState(TypedDict, total=False):

    # ==========================================================
    # INPUT
    # ==========================================================

    incident_id: str

    incident_text: str

    uploaded_log_path: Optional[str]

    ticket_fields: Optional[dict]

    # ==========================================================
    # PRIORITY MODEL
    # ==========================================================

    predicted_priority: Optional[str]

    priority_confidence: Optional[float]

    # ==========================================================
    # CLASSIFIER
    # ==========================================================

    predicted_category: Optional[IncidentCategory]

    category_confidence: Optional[float]

    needs_human_review: Optional[bool]

    # ==========================================================
    # KNOWLEDGE / RAG
    # ==========================================================

    retrieved_docs: Optional[List[str]]

    rag_summary: Optional[str]

    # ==========================================================
    # LOG ANALYSIS
    # ==========================================================

    log_findings: Optional[str]

    suspected_root_cause: Optional[str]

    log_confidence: Optional[float]

    # ==========================================================
    # SHELL AGENT
    # ==========================================================

    command_name: Optional[str]

    target: Optional[str]

    proposed_command: Optional[str]

    approval_required: Optional[bool]

    command_status: Optional[str]

    command_output: Optional[str]

    # ==========================================================
    # TICKET
    # ==========================================================

    ticket_payload: Optional[dict]

    # ==========================================================
    # FINAL SUMMARY
    # ==========================================================

    manager_summary: Optional[str]

    risk_level: Optional[RiskLevel]

    time_taken_seconds: Optional[float]
