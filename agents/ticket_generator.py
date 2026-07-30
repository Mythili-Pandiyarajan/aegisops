"""
AegisOps Ticket Generator Agent

Creates a structured incident ticket payload.

This is a mocked ticket creation flow:
- No Jira/ServiceNow API call
- Captures all agent outputs
- Preserves audit information
"""

from graph.state import AegisOpsState
from datetime import datetime


def run_ticket_generator(state: AegisOpsState) -> dict:

    ticket_payload = {

        # Incident details
        "incident_id": state.get(
            "incident_id",
            "INC-UNKNOWN"
        ),

        "created_at": datetime.now().isoformat(),


        # ML predictions
        "priority": state.get(
            "predicted_priority",
            "Unknown"
        ),

        "priority_confidence": state.get(
            "priority_confidence",
            0.0
        ),

        "category": state.get(
            "predicted_category",
            "Unknown"
        ),

        "category_confidence": state.get(
            "category_confidence",
            0.0
        ),


        # Diagnosis
        "root_cause": state.get(
            "suspected_root_cause",
            "Not available"
        ),

        "log_evidence": state.get(
            "log_findings",
            "No evidence available"
        ),


        # Shell agent output
        "diagnostic_command": state.get(
            "proposed_command",
            None
        ),

        "command_status": state.get(
            "command_status",
            "Not available"
        ),


        # Approval
        "approval_required": state.get(
            "approval_required",
            False
        ),


        # Ticket status
        "status": "open",

    }


    return {

        "ticket_payload": ticket_payload

    }
