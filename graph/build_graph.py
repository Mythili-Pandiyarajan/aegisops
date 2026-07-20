"""
Builds the AegisOps LangGraph pipeline.

Structure:
    incident
       |-- priority_predictor  --\
       |-- category_classifier --+--> merge_node
                                        |
                                  rag_agent
                                        |
                                  log_analysis_agent
                                        |
                                  shell_agent (human-approval gated)
                                        |
                                  ticket_generator (mocked)
                                        |
                                  manager_summary_agent

Priority prediction and category classification run in parallel because
they are independent signals extracted from the same incident text —
NOT a dependency chain. This is a deliberate structural choice, not an
oversight (see README).
"""

from langgraph.graph import StateGraph, START, END
from graph.state import AegisOpsState

# Placeholder imports — implement each of these in agents/
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

    graph.add_node("priority_predictor", run_priority_predictor)
    graph.add_node("category_classifier", run_category_classifier)
    graph.add_node("merge_node", merge_priority_and_category)
    graph.add_node("rag_agent", run_rag_agent)
    graph.add_node("log_analysis_agent", run_log_analysis_agent)
    graph.add_node("shell_agent", run_shell_agent)
    graph.add_node("ticket_generator", run_ticket_generator)
    graph.add_node("manager_summary_agent", run_manager_summary_agent)

    # Fan out from START into both branches — LangGraph runs them
    # concurrently since neither depends on the other's output.
    # merge_node only fires once BOTH edges into it have completed.
    graph.add_edge(START, "priority_predictor")
    graph.add_edge(START, "category_classifier")
    graph.add_edge("priority_predictor", "merge_node")
    graph.add_edge("category_classifier", "merge_node")

    graph.add_edge("merge_node", "rag_agent")
    graph.add_edge("rag_agent", "log_analysis_agent")
    graph.add_edge("log_analysis_agent", "shell_agent")
    graph.add_edge("shell_agent", "ticket_generator")
    graph.add_edge("ticket_generator", "manager_summary_agent")
    graph.add_edge("manager_summary_agent", END)

    return graph.compile()
