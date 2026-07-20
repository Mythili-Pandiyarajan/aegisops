"""
Shared state schema for the AegisOps LangGraph pipeline.

Every node reads from and writes to this single typed state object.
Keeping it explicit (rather than a free-form dict) is what makes the
graph auditable — you can log the full state at any checkpoint and know
exactly what each agent saw and produced.
"""

from typing import TypedDict, Optional, List, Literal

IncidentCategory = Literal["network", "hardware", "database", "security", "email"]
RiskLevel = Literal["low", "medium", "high", "critical"]


class AegisOpsState(TypedDict, total=False):
    # ---- input ----
    incident_text: str
    incident_id: str

    # ---- parallel stage: ML priority model + LLM classifier ----
    predicted_priority: Optional[str]       # from the existing XGBoost model
    priority_confidence: Optional[float]
    predicted_category: Optional[IncidentCategory]
    category_confidence: Optional[float]
    needs_human_review: Optional[bool]

    # ---- knowledge / RAG stage ----
    retrieved_docs: Optional[List[str]]     # SOPs / past incidents / internal docs
    rag_summary: Optional[str]

    # ---- log analysis stage ----
    log_findings: Optional[str]
    suspected_root_cause: Optional[str]

    # ---- shell agent stage ----
    proposed_commands: Optional[List[str]]  # must be a subset of the allowlist
    human_approved: Optional[bool]
    command_output: Optional[str]

    # ---- ticket generation stage (mocked) ----
    ticket_payload: Optional[dict]

    # ---- final summary ----
    manager_summary: Optional[str]
    risk_level: Optional[RiskLevel]
    time_taken_seconds: Optional[float]
