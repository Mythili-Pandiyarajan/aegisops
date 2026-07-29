"""
AegisOps Streamlit Dashboard

Shows the multi-agent pipeline running live: each agent's status and
output streams into its own panel as it completes, rather than waiting
for the whole pipeline and dumping a final JSON blob. This is the
"live agent-activity view" from the roadmap.

Run with:
    streamlit run app.py
"""

import streamlit as st

from graph.build_graph import build_graph

st.set_page_config(page_title="AegisOps", page_icon="🛡️", layout="wide")

# --- font styling to match the ITSM project's Space Mono / DM Sans convention ---
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Mono&family=DM+Sans&display=swap');
    html, body, [class*="css"]  { font-family: 'DM Sans', sans-serif; }
    code, pre, .stCodeBlock { font-family: 'Space Mono', monospace; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🛡️ AegisOps — Autonomous IT Incident Copilot")
st.caption(
    "Multi-agent pipeline: Priority Prediction (XGBoost) + Category Classification, "
    "RAG over SOPs/past incidents, Log Analysis, sandboxed Shell diagnostics, "
    "and a Manager Summary — watch each agent run below."
)

# --- display labels + a formatter per node, so each agent's panel shows
#     something meaningful rather than a raw dict ---

NODE_LABELS = {
    "priority_predictor": "🎯 Priority Predictor",
    "category_classifier": "🏷️ Category Classifier",
    "merge_node": "🔀 Merge",
    "rag_agent": "📚 Knowledge / RAG Agent",
    "log_analysis_agent": "🔍 Log Analysis Agent",
    "shell_agent": "🖥️ Shell Agent",
    "ticket_generator": "🎫 Ticket Generator",
    "manager_summary_agent": "📋 Manager Summary",
}

NODE_ORDER = list(NODE_LABELS.keys())


def _format_node_output(node_name: str, output: dict) -> str:
    if node_name == "priority_predictor":
        return f"**Priority:** {output.get('predicted_priority')}  \n**Confidence:** {output.get('priority_confidence'):.2f}"
    if node_name == "category_classifier":
        return f"**Category:** {output.get('predicted_category')}  \n**Confidence:** {output.get('category_confidence'):.2f}"
    if node_name == "merge_node":
        review = output.get("needs_human_review")
        return f"**Needs human review:** {'Yes ⚠️' if review else 'No'}"
    if node_name == "rag_agent":
        docs = ", ".join(output.get("retrieved_docs", [])) or "none"
        return f"**Retrieved:** {docs}\n\n**Summary:** {output.get('rag_summary')}"
    if node_name == "log_analysis_agent":
        return f"**Suspected root cause:**\n\n{output.get('suspected_root_cause')}"
    if node_name == "shell_agent":
        cmds = output.get("proposed_commands") or []
        command_output = output.get("command_output")
        if not cmds:
            if command_output and str(command_output).startswith("blocked:"):
                return f"⚠️ **Command blocked by safety validation:**\n\n{command_output}"
            return "No diagnostic command proposed."
        text = f"**Proposed command:** `{cmds[0]}`"
        if command_output:
            text += f"\n\n**Output:**\n```\n{command_output}\n```"
        else:
            text += "\n\n_Awaiting human approval before execution._"
        return text
    if node_name == "ticket_generator":
        payload = output.get("ticket_payload", {})
        return f"**Ticket:** `{payload.get('incident_id')}` | {payload.get('priority')} | {payload.get('category')} | {payload.get('status')}"
    if node_name == "manager_summary_agent":
        return f"**Risk level:** {output.get('risk_level')}\n\n{output.get('manager_summary')}"
    return str(output)


def run_pipeline(incident_text: str, ticket_fields: dict, human_approved: bool):
    """
    Streams the graph node-by-node, updating a status panel per agent as
    each one completes. Returns the final accumulated state.
    """
    app = build_graph()
    panels = {name: st.status(NODE_LABELS[name], expanded=False) for name in NODE_ORDER}

    final_state = {}
    initial_input = {
        "incident_text": incident_text,
        "incident_id": "INC-DEMO-001",
        "ticket_fields": ticket_fields,
        "human_approved": human_approved,
    }

    for chunk in app.stream(initial_input, stream_mode="updates"):
        for node_name, output in chunk.items():
            final_state.update(output)
            panel = panels.get(node_name)
            if panel is not None:
                panel.update(label=f"{NODE_LABELS[node_name]} ✅", state="complete")
                panel.write(_format_node_output(node_name, output))

    return final_state


# --- UI ---

incident_text = st.text_area(
    "Incident description",
    value="Users cannot connect to VPN since this morning.",
    height=100,
)

with st.expander("Advanced: structured ticket fields (optional)"):
    ci_cat = st.selectbox("CI Category", ["Software", "Hardware", "Network", "Database", "Security", "Application", "Infrastructure"])
    category = st.selectbox("Ticket Category", ["incident", "problem", "change", "service request"])
    open_hour = st.slider("Hour opened", 0, 23, 9)

ticket_fields = {"ci_cat": ci_cat, "category": category, "open_hour": open_hour}

if "last_state" not in st.session_state:
    st.session_state.last_state = None

if st.button("🚀 Analyze Incident", type="primary"):
    st.session_state.last_state = run_pipeline(incident_text, ticket_fields, human_approved=False)

state = st.session_state.last_state

if state and state.get("proposed_commands"):
    st.divider()
    st.warning(f"Diagnostic command awaiting approval: `{state['proposed_commands'][0]}`")
    if st.button("✅ Approve & Execute Diagnostic"):
        st.session_state.last_state = run_pipeline(incident_text, ticket_fields, human_approved=True)
        st.rerun()
