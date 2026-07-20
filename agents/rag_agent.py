"""
Knowledge / RAG Agent — retrieves relevant internal docs, SOPs, and past
resolved incidents via FAISS, given the merged incident state.
"""

from graph.state import AegisOpsState

# TODO: load FAISS index built by rag/build_index.py
# from rag.retriever import retrieve


def run_rag_agent(state: AegisOpsState) -> dict:
    query = f"{state['incident_text']} category={state.get('predicted_category')}"

    # TODO: retrieved = retrieve(query, k=5)
    retrieved_docs: list[str] = []
    rag_summary = ""

    return {
        "retrieved_docs": retrieved_docs,
        "rag_summary": rag_summary,
    }
