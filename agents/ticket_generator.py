"""
AegisOps Ticket Generator Agent

Creates a structured incident ticket payload.

This is a mocked ticket creation flow:
- No Jira/ServiceNow API call
- Captures all agent outputs
- Preserves audit information
"""

from datetime import datetime

from graph.state import AegisOpsState


def run_ticket_generator(state: AegisOpsState) -> dict:

    ticket_payload = {

        # ======================================================
        # Incident Metadata
        # ======================================================

        "incident_id": state.get(
            "incident_id",
            "INC-UNKNOWN",
        ),

        "created_at": datetime.now().isoformat(),

        "incident_text": state.get(
            "incident_text",
            "",
        ),

        # ======================================================
        # ML Predictions
        # ======================================================

        "priority": state.get(
            "predicted_priority",
            "Unknown",
        ),

        "priority_confidence": state.get(
            "priority_confidence",
            0.0,
        ),

        "category": state.get(
            "predicted_category",
            "Unknown",
        ),

        "category_confidence": state.get(
            "category_confidence",
            0.0,
        ),

        # ======================================================
        # Knowledge Base (RAG)
        # ======================================================

        "rag_summary": state.get(
            "rag_summary",
            "No relevant knowledge found.",
        ),

        "retrieved_docs": state.get(
            "retrieved_docs",
            [],
        ),

        # ======================================================
        # Log Analysis
        # ======================================================

        "root_cause": state.get(
            "suspected_root_cause",
            "Unknown",
        ),

        "log_evidence": state.get(
            "log_findings",
            "No evidence available.",
        ),

        "log_confidence": state.get(
            "log_confidence",
            0.0,
        ),

        # ======================================================
        # Shell Agent
        # ======================================================

        "diagnostic_commands": state.get(
            "proposed_commands",
            [],
        ),

        "command_status": state.get(
            "command_status",
            "Pending",
        ),

        "approval_required": state.get(
            "approval_required",
            False,
        ),

        # ======================================================
        # Manager Summary
        # ======================================================

        "manager_summary": state.get(
            "manager_summary",
            "",
        ),

        "risk_level": state.get(
            "risk_level",
            "Unknown",
        ),

        # ======================================================
        # Ticket Status
        # ======================================================

        "status": "open",

    }

    return {

        "ticket_payload": ticket_payload,

    }
