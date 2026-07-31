"""
Shared state schema for the AegisOps LangGraph pipeline.

All agents read/write through this state object.

Flow:

Incident
   |
Priority Predictor
Category Classifier
   |
Merge
   |
RAG Agent
   |
Log Analysis Agent
   |
Shell Agent
   |
Ticket Generator
   |
Manager Summary
"""

from typing import TypedDict, Optional, List, Any


class AegisOpsState(TypedDict, total=False):

    # ==========================================================
    # INPUT
    # ==========================================================

    incident_id: str

    incident_text: str

    uploaded_log_path: Optional[str]

    ticket_fields: Optional[dict]

    human_approved: Optional[bool]


    # ==========================================================
    # PRIORITY PREDICTION
    # ==========================================================

    predicted_priority: Optional[str]

    priority_confidence: Optional[float]


    # ==========================================================
    # CATEGORY CLASSIFICATION
    # ==========================================================

    predicted_category: Optional[str]

    category_confidence: Optional[float]

    needs_human_review: Optional[bool]


    # ==========================================================
    # RAG KNOWLEDGE AGENT
    # ==========================================================

    retrieved_docs: Optional[List[str]]

    rag_summary: Optional[str]


    # ==========================================================
    # LOG ANALYSIS AGENT
    # ==========================================================

    log_findings: Optional[str]

    suspected_root_cause: Optional[str]

    log_confidence: Optional[float]

    llm_response: Optional[str]


    # ==========================================================
    # SHELL AGENT
    # ==========================================================

    command_name: Optional[str]

    target: Optional[str]

    # Single command (backward compatibility)
    proposed_command: Optional[str]

    # Multiple commands support (UI + future expansion)
    proposed_commands: Optional[List[str]]

    approval_required: Optional[bool]

    command_status: Optional[str]

    command_output: Optional[str]


    # ==========================================================
    # TICKET GENERATOR
    # ==========================================================

    ticket_payload: Optional[dict]


    # ==========================================================
    # MANAGER SUMMARY
    # ==========================================================

    manager_summary: Optional[str]

    risk_level: Optional[str]

    incident_status: Optional[str]


    # ==========================================================
    # PIPELINE METADATA
    # ==========================================================

    current_agent: Optional[str]

    error_message: Optional[str]

    time_taken_seconds: Optional[float]
