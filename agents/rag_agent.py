"""
Knowledge / RAG Agent — retrieves relevant internal docs, SOPs, and past
resolved incidents via FAISS, given the merged incident state, then asks
the LLM to synthesize a short summary of what's relevant -- this is the
"generation" half of RAG, not just the retrieval half.
"""

import os
from groq import Groq

from graph.state import AegisOpsState
from rag.retriever import retrieve

_client = None


def _get_client():
    global _client
    if _client is None:
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError("GROQ_API_KEY not set.")
        _client = Groq(api_key=api_key)
    return _client


def _summarize(incident_text: str, docs: list) -> str:
    if not docs:
        return "No relevant SOPs or past incidents found in the knowledge base."

    context = "\n\n".join(
        f"[{d['type'].upper()} {d['id']}] {d['text']}" for d in docs
    )

    prompt = (
        f"Incident: {incident_text}\n\n"
        f"Relevant knowledge base entries:\n{context}\n\n"
        "In 2-3 sentences, summarize what these entries suggest about likely "
        "root cause and next diagnostic step for this incident. Be specific, "
        "reference the entry IDs where relevant."
    )

    client = _get_client()
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=200,
    )
    return response.choices[0].message.content.strip()


def run_rag_agent(state: AegisOpsState):

    query = (
        f"{state['incident_text']} "
        f"{state.get('predicted_category','')} "
        f"{state.get('predicted_priority','')}"
    )

    retrieved_docs = retrieve(query, k=3)

    rag_summary = _summarize(
        state["incident_text"],
        retrieved_docs,
    )

    return {

        "retrieved_docs": retrieved_docs,

        "rag_summary": rag_summary,

    }
