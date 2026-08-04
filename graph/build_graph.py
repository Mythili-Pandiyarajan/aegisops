"""
Builds the AegisOps LangGraph pipeline.

Structure:

    START
      |
      ↓
  category_classifier
      |
      ↓
  priority_predictor
      |
      ↓
   merge_node
      |
      ↓
   rag_agent
      |
      ↓
   log_analysis
      |
      ↓
   shell_agent
      |
      ↓
   ticket_generator
      |
      ↓
   manager_summary
      |
      ↓
     END


Category classification now runs before priority prediction (previously
they ran in parallel). The priority model was trained on resolution-time
ITSM fields that don't exist for a brand-new incident (handle time,
reassignment count, closure code, etc.), so the intake form alone could
only ever populate a handful of static/default features — meaning
priority predictions barely varied across incidents of very different
severity. Running category_classifier first lets priority_predictor map
the classified category into a real CI_Cat feature and populate real
open_dow/open_month/open_year values, giving the model at least some
signal that's actually derived from the incident rather than defaults.
"""

from langgraph.graph import StateGraph, START, END

from graph.state import AegisOpsState

from agents.priority_predictor import run_priority_predictor
from agents.category_classifier import run_category_classifier
from agents.merge_node import merge_priority_and_category
from agents.rag_agent import run_rag_agent
from agents.log_analysis_agent import run_log_analysis_agent
from agents.shell_agent import run_shell_agent
from agents.ticket_generator import run_ticket_generator
from agents.manager_summary_agent import run_manager_summary_agent


def build_graph():

    graph = StateGraph(AegisOpsState)

    # -------------------------
    # Register Nodes
    # -------------------------

    graph.add_node(
        "priority_predictor",
        run_priority_predictor
    )

    graph.add_node(
        "category_classifier",
        run_category_classifier
    )

    graph.add_node(
        "merge_node",
        merge_priority_and_category
    )

    graph.add_node(
        "rag_agent",
        run_rag_agent
    )

    graph.add_node(
        "log_analysis_agent",
        run_log_analysis_agent
    )

    graph.add_node(
        "shell_agent",
        run_shell_agent
    )

    graph.add_node(
        "ticket_generator",
        run_ticket_generator
    )

    graph.add_node(
        "manager_summary_agent",
        run_manager_summary_agent
    )


    # -------------------------
    # Workflow Connections
    # -------------------------

    # Sequential: category must be classified before priority is
    # predicted, so priority_predictor can use predicted_category
    # to derive a real CI_Cat feature instead of a static default.
    graph.add_edge(
        START,
        "category_classifier"
    )

    graph.add_edge(
        "category_classifier",
        "priority_predictor"
    )


    # Merge after category + priority are both available
    graph.add_edge(
        "priority_predictor",
        "merge_node"
    )


    # Main pipeline
    graph.add_edge(
        "merge_node",
        "rag_agent"
    )

    graph.add_edge(
        "rag_agent",
        "log_analysis_agent"
    )

    graph.add_edge(
        "log_analysis_agent",
        "shell_agent"
    )

    graph.add_edge(
        "shell_agent",
        "ticket_generator"
    )

    graph.add_edge(
        "ticket_generator",
        "manager_summary_agent"
    )

    graph.add_edge(
        "manager_summary_agent",
        END
    )


    return graph.compile()
