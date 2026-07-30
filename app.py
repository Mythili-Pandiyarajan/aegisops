"""
AegisOps Streamlit Dashboard

A SOC-style command center for the autonomous IT incident copilot:
  - Dashboard: live KPI cards, severity breakdown, and recent activity —
    all driven by incidents actually analyzed in this session (plus a
    small baseline so the dashboard doesn't look empty on first load).
  - File new incident: intake form that runs the real multi-agent
    pipeline (Priority + Category prediction, RAG, Log Analysis, Shell
    diagnostics, Manager Summary) and streams each agent's status live.
  - Active Incidents / Approvals Center / Audit Center / SOC Analytics:
    session-backed views over the same incident records.

Run with:
    streamlit run app.py
"""

import json
import os
from datetime import datetime

import streamlit as st

from graph.build_graph import build_graph

st.set_page_config(page_title="AegisOps", page_icon="🛡️", layout="wide", initial_sidebar_state="expanded")

# =========================================================================
# Design tokens — clean, light, professional command-center theme.
# Space Mono for labels/eyebrows/status pills (terminal-readout feel),
# DM Sans for body copy — matching the existing ITSM project convention.
# =========================================================================
BG = "#F4F2EC"
PANEL = "#FFFFFF"
INK = "#16171B"
MUTED = "#6E7178"
BORDER = "#E7E3D8"
RED = "#D5402C"
RED_SOFT = "#FBEAE6"
AMBER = "#C7912B"
AMBER_SOFT = "#FBF2DC"
GREEN = "#2E9E6D"
GREEN_SOFT = "#E6F5EE"
BLUE = "#3D6FD1"
BLUE_SOFT = "#EAF0FC"

NODE_LABELS = {
    "priority_predictor": "🎯 Priority Predictor",
    "category_classifier": "🏷️ Category Classifier",
    "merge_node": "🔀 Merge",
    "rag_agent": "📚 Knowledge / RAG Agent",
    "log_analysis": "🔍 Log Analysis Agent",
    "shell_agent": "🖥️ Shell Agent",
    "ticket_generator": "🎫 Ticket Generator",
    "manager_summary": "📋 Manager Summary",
}
NODE_ORDER = list(NODE_LABELS.keys())

# These must exactly match the string values LabelEncoder was fit on during
# training (confirmed against the real itsm_data.csv), not made-up labels —
# an unseen category here would break scaler.transform()/model.predict().
CI_CAT_OPTIONS = [
    "application",
    "subapplication",
    "computer",
    "storage",
    "hardware",
    "software",
    "database",
    "displaydevice",
    "officeelectronics",
    "networkcomponents",
]
CATEGORY_OPTIONS = ["incident", "request for information", "complaint", "request for change"]

# Most common CI_Subcat per CI_Cat, from the real training data — use this
# in tools/priority_model.py in place of a single hardcoded constant.
CI_SUBCAT_DEFAULTS = {
    "application": "Server Based Application",
    "subapplication": "Web Based Application",
    "computer": "Laptop",
    "storage": "SAN",
    "hardware": "DataCenterEquipment",
    "software": "System Software",
    "database": "Database",
    "displaydevice": "Monitor",
    "officeelectronics": "Printer",
    "networkcomponents": "Network Component",
}

SEVERITY_OPTIONS = {
    "P1 — Critical: service down / major impact": "P1",
    "P2 — High: significant degradation": "P2",
    "P3 — Medium: moderate degradation": "P3",
    "P4 — Low: minor / cosmetic": "P4",
    "P5 — Planning: informational / no impact": "P5",
}

TEAL = "#2E8C8C"
TEAL_SOFT = "#E4F1F1"

PRIORITY_COLORS = {
    "P1": (RED, RED_SOFT),
    "P2": (AMBER, AMBER_SOFT),
    "P3": (BLUE, BLUE_SOFT),
    "P4": (GREEN, GREEN_SOFT),
    "P5": (TEAL, TEAL_SOFT),
}
PRIORITY_DESC = {"P1": "Critical", "P2": "High", "P3": "Medium", "P4": "Low", "P5": "Planning"}

# =========================================================================
# Styling
# =========================================================================
st.markdown(
    f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@400;500;700&display=swap');

    html, body, [class*="css"] {{ font-family: 'DM Sans', sans-serif; color: {INK}; }}
    .mono {{ font-family: 'Space Mono', monospace; }}

    #MainMenu, header, footer {{ visibility: hidden; }}
    .stApp {{ background-color: {BG}; }}
    section[data-testid="stSidebar"] {{
        background-color: {PANEL};
        border-right: 1px solid {BORDER};
    }}
    div.block-container {{ padding-top: 1.5rem; max-width: 1200px; }}

    /* --- top status bar --- */
    .topbar {{
        display: flex; align-items: center; gap: 10px;
        margin-bottom: 1.2rem;
    }}
    .pill {{
        font-family: 'Space Mono', monospace; font-size: 0.72rem;
        padding: 5px 12px; border-radius: 20px; letter-spacing: 0.02em;
        border: 1px solid {BORDER}; background: {PANEL}; color: {MUTED};
    }}
    .pill.on {{ background: {GREEN_SOFT}; color: {GREEN}; border-color: {GREEN}; }}
    .dot {{
        height: 7px; width: 7px; border-radius: 50%; display: inline-block;
        background: {GREEN}; margin-right: 6px;
    }}

    /* --- cards --- */
    .card {{
        background: {PANEL}; border: 1px solid {BORDER}; border-radius: 14px;
        padding: 18px 20px; height: 100%;
    }}
    .kpi-label {{
        font-family: 'Space Mono', monospace; font-size: 0.68rem;
        color: {MUTED}; letter-spacing: 0.04em; text-transform: uppercase;
    }}
    .kpi-value {{ font-size: 2rem; font-weight: 700; margin: 6px 0 2px 0; }}
    .kpi-sub {{ font-size: 0.78rem; color: {MUTED}; }}

    .sev-row {{ margin-bottom: 12px; }}
    .sev-track {{
        height: 7px; border-radius: 5px; background: {BORDER}; overflow: hidden; margin-top: 4px;
    }}
    .sev-fill {{ height: 100%; border-radius: 5px; }}

    .empty-state {{
        color: {MUTED}; font-size: 0.88rem; padding: 24px 4px; text-align: center;
    }}

    /* --- sidebar nav --- */
    .brand {{ display: flex; align-items: center; gap: 10px; padding: 4px 4px 18px 4px; }}
    .brand-title {{ font-weight: 700; font-size: 1.05rem; line-height: 1; }}
    .brand-sub {{ font-family: 'Space Mono', monospace; font-size: 0.62rem; color: {MUTED}; letter-spacing: 0.05em; }}

    section[data-testid="stSidebar"] .stButton button {{
        width: 100%; text-align: left; background: transparent; border: none;
        color: {INK}; font-weight: 500; padding: 9px 12px; border-radius: 8px;
    }}
    section[data-testid="stSidebar"] .stButton button:hover {{
        background: {BG}; color: {INK}; border: none;
    }}
    .nav-current {{
        width: 100%; text-align: left; background: {RED_SOFT}; color: {RED};
        font-weight: 700; padding: 9px 12px; border-radius: 8px; margin-bottom: 2px;
        font-size: 0.95rem;
    }}

    /* --- primary red button (file new incident, analyze) --- */
    div[data-testid="stButton"] button[kind="primary"] {{
        background-color: {RED}; border-color: {RED}; border-radius: 8px;
        font-weight: 600;
    }}
    div[data-testid="stButton"] button[kind="primary"]:hover {{
        background-color: #b8331f; border-color: #b8331f;
    }}

    .status-chip {{
        font-family: 'Space Mono', monospace; font-size: 0.68rem;
        padding: 3px 10px; border-radius: 20px; display: inline-block;
    }}

    /* --- force readable, theme-independent contrast on native widgets ---
       Streamlit's inputs otherwise inherit the browser/OS color scheme,
       which can put light-mode text on our light cards (or vice versa). */
    .stTextInput input, .stTextArea textarea, .stNumberInput input {{
        background-color: {PANEL} !important; color: {INK} !important;
        border: 1px solid {BORDER} !important;
    }}
    div[data-baseweb="select"] > div {{
        background-color: {PANEL} !important; color: {INK} !important;
        border-color: {BORDER} !important;
    }}
    div[data-baseweb="select"] * {{ color: {INK} !important; }}
    ul[data-testid="stSelectboxVirtualDropdown"] {{ background-color: {PANEL} !important; }}
    ul[data-testid="stSelectboxVirtualDropdown"] li {{ color: {INK} !important; }}
    label, .stMarkdown, .stCaption, p, span, div {{ color: {INK}; }}
    small, .stCaption p, [data-testid="stCaptionContainer"] {{ color: {MUTED} !important; }}
    [data-testid="stFileUploaderDropzone"] {{
        background-color: {PANEL} !important; color: {INK} !important;
        border: 1px dashed {BORDER} !important;
    }}
    [data-testid="stFileUploaderDropzone"] * {{ color: {INK} !important; }}
    div[data-testid="stExpander"] {{
        background-color: {PANEL} !important; border: 1px solid {BORDER} !important; border-radius: 10px;
    }}
    div[data-testid="stExpander"] summary {{ color: {INK} !important; }}
    </style>
    """,
    unsafe_allow_html=True,
)

# =========================================================================
# Persistence — a plain JSON log file instead of a database.
# No server, no schema migrations: just a file next to the app that gets
# read on startup and rewritten after every change.
# =========================================================================
DATA_DIR = "data"
DATA_FILE = os.path.join(DATA_DIR, "incidents_log.json")
DEFAULT_BASELINE = {"active": 1, "resolved": 7, "pending": 1, "runs_total": 8, "runs_success": 8}


def load_persisted() -> dict:
    """Read incidents + baseline + run counter from disk, if the log exists."""
    if not os.path.exists(DATA_FILE):
        return {"incidents": [], "baseline": dict(DEFAULT_BASELINE), "run_counter": 0}
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
        data.setdefault("incidents", [])
        data.setdefault("baseline", dict(DEFAULT_BASELINE))
        data.setdefault("run_counter", 0)
        return data
    except Exception:
        # Corrupt or unreadable file — start clean rather than crashing the app.
        return {"incidents": [], "baseline": dict(DEFAULT_BASELINE), "run_counter": 0}


def save_persisted():
    """Write the current incidents + baseline + run counter to disk."""
    os.makedirs(DATA_DIR, exist_ok=True)
    payload = {
        "incidents": st.session_state.incidents,
        "baseline": st.session_state.baseline,
        "run_counter": st.session_state.run_counter,
    }
    try:
        with open(DATA_FILE, "w") as f:
            json.dump(payload, f, indent=2, default=str)
    except Exception as e:
        st.warning(f"Could not save incident log to disk: {e}")


# =========================================================================
# Session state — loaded from the JSON log on first run of each server
# process, then kept in sync with it on every change.
# =========================================================================
if "page" not in st.session_state:
    st.session_state.page = "dashboard"

if "incidents" not in st.session_state:
    _persisted = load_persisted()
    st.session_state.incidents = _persisted["incidents"]
    st.session_state.baseline = _persisted["baseline"]
    st.session_state.run_counter = _persisted["run_counter"]


def goto(page: str):
    st.session_state.page = page


# =========================================================================
# Pipeline execution
# =========================================================================
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
    if node_name == "log_analysis":
        root_cause = output.get(
            "suspected_root_cause",
            "No root cause generated"
        )

        evidence = output.get(
            "log_findings",
            "No log evidence found"
        )

        return f"""
**Suspected Root Cause**

{root_cause}


**Supporting Evidence**

{evidence}
"""
    if node_name == "shell_agent":
        cmds = output.get("proposed_command")
        cmds = [cmd] if cmd else []
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
    if node_name == "manager_summary":
        return f"**Risk level:** {output.get('risk_level')}\n\n{output.get('manager_summary')}"
    return str(output)


def run_pipeline(incident_text: str, incident_id: str, ticket_fields: dict, human_approved: bool):
    """Streams the graph node-by-node, rendering a status panel per agent."""
    app = build_graph()
    panels = {name: st.status(NODE_LABELS[name], expanded=False) for name in NODE_ORDER}

    final_state = {}
    initial_input = {
        "incident_text": incident_text,
        "incident_id": incident_id,
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


def derive_status(state: dict) -> str:
    """Decide which bucket an incident lands in after a pipeline run."""
    if state.get("needs_human_review"):
        return "pending_approval"
    cmds = state.get("proposed_commands") or []
    if cmds and not state.get("command_output"):
        return "pending_approval"
    risk = (state.get("risk_level") or "").lower()
    if risk in ("critical", "high"):
        return "active"
    return "resolved"


def record_run(record: dict, state: dict, success: bool):
    st.session_state.baseline["runs_total"] += 1
    if success:
        st.session_state.baseline["runs_success"] += 1
    record.update(
        {
            "predicted_priority": state.get("predicted_priority"),
            "priority_confidence": state.get("priority_confidence"),
            "predicted_category": state.get("predicted_category"),
            "risk_level": state.get("risk_level"),
            "manager_summary": state.get("manager_summary"),
            "proposed_commands": state.get("proposed_commands"),
            "command_output": state.get("command_output"),
            "needs_human_review": state.get("needs_human_review"),
            "status": derive_status(state) if success else "active",
        }
    )


# =========================================================================
# Shared computed metrics
# =========================================================================
def counts_by_status():
    inc = st.session_state.incidents
    base = st.session_state.baseline
    active = base["active"] + sum(1 for i in inc if i["status"] == "active")
    resolved = base["resolved"] + sum(1 for i in inc if i["status"] == "resolved")
    pending = base["pending"] + sum(1 for i in inc if i["status"] == "pending_approval")
    total_runs = base["runs_total"]
    success_runs = base["runs_success"]
    success_rate = round(100 * success_runs / total_runs) if total_runs else 100
    return active, resolved, pending, success_rate


def severity_breakdown():
    inc = st.session_state.incidents
    counts = {"P1": 0, "P2": 0, "P3": 0, "P4": 0, "P5": 0}
    for i in inc:
        p = i.get("predicted_priority")
        if p in counts:
            counts[p] += 1
    return counts


# =========================================================================
# Sidebar
# =========================================================================
with st.sidebar:
    st.markdown(
        """
        <div class="brand">
            <div style="font-size:1.5rem;">🛡️</div>
            <div>
                <div class="brand-title">AegisOps.</div>
                <div class="brand-sub">COMMAND CENTER</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    nav_items = [
        ("dashboard", "📊  Dashboard"),
        ("active", "⚠️  Active Incidents"),
        ("approvals", "✅  Approvals Center"),
        ("audit", "🗂️  Audit Center"),
        ("analytics", "📈  SOC Analytics"),
    ]
    for key, label in nav_items:
        if st.session_state.page == key:
            st.markdown(f'<div class="nav-current">{label}</div>', unsafe_allow_html=True)
        else:
            st.button(label, key=f"nav_{key}", on_click=goto, args=(key,))

# =========================================================================
# Top status bar (shown on every page)
# =========================================================================
st.markdown(
    f"""
    <div class="topbar">
        <span class="pill on"><span class="dot"></span>PIPELINE ONLINE</span>
        <span class="pill mono">SOC_AGENT_STATUS: ACTIVE</span>
    </div>
    """,
    unsafe_allow_html=True,
)

# =========================================================================
# PAGE: Dashboard
# =========================================================================
if st.session_state.page == "dashboard":
    top_l, top_r = st.columns([3, 1])
    with top_l:
        st.markdown("## SOC Command Dashboard")
        st.caption("Real-time monitoring and multi-agent mitigation overview")
    with top_r:
        st.write("")
        st.button("🚀  File new incident", type="primary", on_click=goto, args=("intake",), use_container_width=True)

    active, resolved, pending, success_rate = counts_by_status()

    k1, k2, k3, k4 = st.columns(4)
    kpi_data = [
        (k1, "ACTIVE INCIDENTS", active, "Needs investigation or response", RED),
        (k2, "RESOLVED INCIDENTS", resolved, "Resolved by automated remediation", GREEN),
        (k3, "PENDING APPROVALS", pending, "Awaiting manual manager check", AMBER),
        (k4, "AGENT RUN SUCCESS", f"{success_rate}%", "Pipeline run success rate", BLUE),
    ]
    for col, label, value, sub, color in kpi_data:
        with col:
            st.markdown(
                f"""
                <div class="card">
                    <div class="kpi-label">{label}</div>
                    <div class="kpi-value" style="color:{color}">{value}</div>
                    <div class="kpi-sub">{sub}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.write("")
    left, right = st.columns([1.6, 1])

    with left:
        st.markdown("#### Recent activity")
        st.caption("Live — reflects incidents analyzed in this session")
        if not st.session_state.incidents:
            st.markdown(
                '<div class="card empty-state">No incidents analyzed yet this session.<br>'
                'File a new incident to see it show up here.</div>',
                unsafe_allow_html=True,
            )
        else:
            rows = ""
            for i in reversed(st.session_state.incidents[-8:]):
                color, soft = PRIORITY_COLORS.get(i.get("predicted_priority"), (MUTED, BG))
                rows += (
                    f'<tr style="border-bottom:1px solid {BORDER};">'
                    f'<td style="padding:8px 6px;">{i["title"][:42]}</td>'
                    f'<td style="padding:8px 6px;"><span class="status-chip" style="background:{soft};color:{color};">'
                    f'{i.get("predicted_priority") or "—"}</span></td>'
                    f'<td style="padding:8px 6px;">{i.get("predicted_category") or "—"}</td>'
                    f'<td style="padding:8px 6px; text-transform:capitalize;">{i["status"].replace("_"," ")}</td>'
                    f'<td style="padding:8px 6px; color:{MUTED};">{i["created_at"]}</td>'
                    f"</tr>"
                )
            st.markdown(
                f"""
                <div class="card">
                <table style="width:100%; border-collapse:collapse; font-size:0.85rem;">
                    <tr style="color:{MUTED}; text-align:left; font-family:'Space Mono',monospace; font-size:0.68rem;">
                        <th style="padding:4px 6px;">TITLE</th><th>PRIORITY</th><th>CATEGORY</th><th>STATUS</th><th>TIME</th>
                    </tr>
                    {rows}
                </table>
                </div>
                """,
                unsafe_allow_html=True,
            )

    with right:
        st.markdown("#### Severity vector allocation")
        st.caption("Categorization of session-analyzed incidents")
        sev = severity_breakdown()
        total_sev = sum(sev.values())
        if total_sev == 0:
            st.markdown(
                '<div class="card empty-state">No severity data yet.<br>Runs a priority prediction on file.</div>',
                unsafe_allow_html=True,
            )
        else:
            rows_html = ""
            for label in ["P1", "P2", "P3", "P4", "P5"]:
                count = sev[label]
                pct = round(100 * count / total_sev)
                color, _ = PRIORITY_COLORS[label]
                rows_html += f"""
                <div class="sev-row">
                    <div style="display:flex; justify-content:space-between; font-size:0.85rem;">
                        <span>{label} — {PRIORITY_DESC[label]}</span><span class="mono">{count} ({pct}%)</span>
                    </div>
                    <div class="sev-track"><div class="sev-fill" style="width:{pct}%; background:{color};"></div></div>
                </div>
                """
            st.markdown(f'<div class="card">{rows_html}</div>', unsafe_allow_html=True)

# =========================================================================
# PAGE: File new incident
# =========================================================================
elif st.session_state.page == "intake":
    st.button("← Back to dashboard", on_click=goto, args=("dashboard",))
    st.markdown("## File operations incident ticket")
    st.caption("Initiate multi-agent automated assessment, triage, and resolution protocols.")

    with st.container():
        st.markdown('<div class="card">', unsafe_allow_html=True)

        title = st.text_input(
            "INCIDENT TITLE",
            placeholder="e.g. Database connection pool starved on auth worker node",
        )

        col_a, col_b = st.columns([1.6, 1])
        with col_a:
            severity_label = st.selectbox("INITIAL SEVERITY VECTOR", list(SEVERITY_OPTIONS.keys()), index=2)
            reported_severity = SEVERITY_OPTIONS[severity_label]
            st.caption("＊ P1 (critical) severity automatically flags the incident for human manager approval before applying resolution plans.")
        with col_b:
            st.markdown(
                f"""
                <div class="card" style="background:{BLUE_SOFT}; border-color:{BLUE};">
                    <b>🛡️ Pipeline automated protocol</b><br>
                    <span style="font-size:0.85rem; color:{MUTED};">
                    Submission runs sequential intake parsing, priority/category
                    prediction, knowledge-base retrieval, log analysis, and
                    root-cause evaluation.
                    </span>
                </div>
                """,
                unsafe_allow_html=True,
            )

        description = st.text_area(
            "DESCRIPTION & STEPS",
            placeholder="Detail the failure signs, transaction errors, or trace details here...",
            height=140,
        )

        log_file = st.file_uploader("LOG FILE UPLOAD (OPTIONAL)", type=["txt", "log"])

        with st.expander("Additional ticket details (optional — improves prediction accuracy)"):
            ac1, ac2, ac3 = st.columns(3)
            with ac1:
                ci_cat = st.selectbox("CI Category", CI_CAT_OPTIONS)
            with ac2:
                category = st.selectbox("Ticket Category", CATEGORY_OPTIONS)
            with ac3:
                open_hour = st.slider("Hour opened", 0, 23, datetime.now().hour)

        st.markdown("</div>", unsafe_allow_html=True)

    submitted = st.button("🚀  Analyze & file incident", type="primary")

    if submitted:
        if not title.strip() or not description.strip():
            st.warning("Please provide at least an incident title and description before filing.")
        else:
            st.session_state.run_counter += 1
            incident_id = f"INC-{datetime.now().strftime('%Y%m%d')}-{st.session_state.run_counter:03d}"

            incident_text = f"{title}\n\n{description}"
            if log_file is not None:
                try:
                    log_text = log_file.read().decode("utf-8", errors="ignore")[:4000]
                    incident_text += f"\n\n--- Uploaded log excerpt ---\n{log_text}"
                except Exception:
                    st.info("Could not read the uploaded log file as text — continuing without it.")

            ticket_fields = {
                "ci_cat": ci_cat,
                "ci_subcat": CI_SUBCAT_DEFAULTS.get(ci_cat, "Web Based Application"),
                "category": category,
                "open_hour": open_hour,
            }

            record = {
                "id": incident_id,
                "title": title.strip(),
                "reported_severity": reported_severity,
                "created_at": datetime.now().strftime("%H:%M:%S"),
                "incident_text": incident_text,
                "ticket_fields": ticket_fields,
            }

            st.divider()
            st.markdown(f"##### Running pipeline for `{incident_id}`")
            try:
                state = run_pipeline(incident_text, incident_id, ticket_fields, human_approved=False)
                record_run(record, state, success=True)
                st.session_state.incidents.append(record)
                save_persisted()
                st.success(f"Incident `{incident_id}` filed — status: **{record['status'].replace('_',' ')}**")
                st.button("View on dashboard →", on_click=goto, args=("dashboard",))
            except Exception as e:
                record_run(record, {}, success=False)
                st.session_state.incidents.append({**record, "status": "active", "predicted_priority": None})
                save_persisted()
                st.error(f"Pipeline run failed: {e}")

# =========================================================================
# PAGE: Active Incidents
# =========================================================================
elif st.session_state.page == "active":
    st.markdown("## Active Incidents")
    st.caption("Incidents currently open and needing investigation or response")

    active_inc = [i for i in st.session_state.incidents if i["status"] == "active"]
    base_active = st.session_state.baseline["active"]

    if base_active:
        st.info(f"{base_active} baseline active incident(s) from before this session — no live detail recorded yet.")

    if not active_inc:
        st.markdown(
            '<div class="card empty-state">No live active incidents in this session.</div>',
            unsafe_allow_html=True,
        )
    for i in active_inc:
        with st.expander(f"{i['id']} — {i['title']}"):
            color, _ = PRIORITY_COLORS.get(i.get("predicted_priority"), (MUTED, BG))
            st.markdown(f"**Predicted priority:** <span style='color:{color}'>{i.get('predicted_priority') or '—'}</span>", unsafe_allow_html=True)
            st.write(f"**Category:** {i.get('predicted_category') or '—'}")
            st.write(f"**Risk level:** {i.get('risk_level') or '—'}")
            if i.get("manager_summary"):
                st.write(f"**Manager summary:** {i['manager_summary']}")
            if i.get("proposed_commands") and not i.get("command_output"):
                st.caption("A diagnostic command is awaiting approval for this incident — see Approvals Center.")
            if st.button("Mark resolved", key=f"resolve_{i['id']}"):
                i["status"] = "resolved"
                save_persisted()
                st.rerun()

# =========================================================================
# PAGE: Approvals Center
# =========================================================================
elif st.session_state.page == "approvals":
    st.markdown("## Approvals Center")
    st.caption("Incidents awaiting manual manager sign-off before resolution plans are applied")

    pending_inc = [i for i in st.session_state.incidents if i["status"] == "pending_approval"]
    base_pending = st.session_state.baseline["pending"]

    if base_pending:
        st.info(f"{base_pending} baseline pending approval(s) from before this session — no live detail recorded yet.")

    if not pending_inc:
        st.markdown(
            '<div class="card empty-state">Nothing awaiting approval right now.</div>',
            unsafe_allow_html=True,
        )
    for i in pending_inc:
        with st.container():
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown(f"**{i['id']} — {i['title']}**")
            st.write(f"Risk level: **{i.get('risk_level') or '—'}**  |  Category: **{i.get('predicted_category') or '—'}**")
            if i.get("proposed_commands"):
                st.code(i["proposed_commands"][0])
            if i.get("manager_summary"):
                st.caption(i["manager_summary"])
            c1, c2 = st.columns([1, 3])
            with c1:
                if st.button("✅ Approve & execute", key=f"approve_{i['id']}"):
                    incident_text = i.get("incident_text", i["title"])
                    ticket_fields = i.get(
                        "ticket_fields",
                        {"ci_cat": "application", "ci_subcat": "Web Based Application", "category": "incident", "open_hour": datetime.now().hour},
                    )
                    st.divider()
                    st.markdown(f"##### Re-running pipeline for `{i['id']}` with approval")
                    try:
                        new_state = run_pipeline(incident_text, i["id"], ticket_fields, human_approved=True)
                        i.update(
                            {
                                "risk_level": new_state.get("risk_level", i.get("risk_level")),
                                "manager_summary": new_state.get("manager_summary", i.get("manager_summary")),
                                "command_output": new_state.get("command_output"),
                                "needs_human_review": False,
                                "status": derive_status(new_state),
                            }
                        )
                        save_persisted()
                        st.success(f"Approved and re-run — new status: **{i['status'].replace('_',' ')}**")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Re-run failed: {e}")
            st.markdown("</div>", unsafe_allow_html=True)

# =========================================================================
# PAGE: Audit Center
# =========================================================================
elif st.session_state.page == "audit":
    st.markdown("## Audit Center")
    st.caption("Full record of incidents analyzed in this session")

    if not st.session_state.incidents:
        st.markdown('<div class="card empty-state">No incidents recorded yet this session.</div>', unsafe_allow_html=True)
    else:
        for i in reversed(st.session_state.incidents):
            st.markdown(
                f"""
                <div class="card" style="margin-bottom:10px;">
                    <b>{i['id']}</b> — {i['title']}<br>
                    <span style="font-size:0.82rem; color:{MUTED};">
                    Reported severity: {i.get('reported_severity','—')} · Predicted: {i.get('predicted_priority','—')} ·
                    Category: {i.get('predicted_category','—')} · Status: {i['status'].replace('_',' ')} · Filed at {i['created_at']}
                    </span>
                </div>
                """,
                unsafe_allow_html=True,
            )

# =========================================================================
# PAGE: SOC Analytics
# =========================================================================
elif st.session_state.page == "analytics":
    st.markdown("## SOC Analytics")
    st.caption("Aggregate stats across incidents analyzed in this session")

    inc = st.session_state.incidents
    if not inc:
        st.markdown('<div class="card empty-state">No data yet — file an incident to populate analytics.</div>', unsafe_allow_html=True)
    else:
        cats = {}
        confidences = []
        for i in inc:
            c = i.get("predicted_category") or "Unknown"
            cats[c] = cats.get(c, 0) + 1
            if i.get("priority_confidence"):
                confidences.append(i["priority_confidence"])

        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### Incidents by category")
            rows_html = ""
            max_v = max(cats.values()) if cats else 1
            for cat, v in sorted(cats.items(), key=lambda x: -x[1]):
                pct = round(100 * v / max_v)
                rows_html += f"""
                <div class="sev-row">
                    <div style="display:flex; justify-content:space-between; font-size:0.85rem;">
                        <span>{cat}</span><span class="mono">{v}</span>
                    </div>
                    <div class="sev-track"><div class="sev-fill" style="width:{pct}%; background:{BLUE};"></div></div>
                </div>
                """
            st.markdown(f'<div class="card">{rows_html}</div>', unsafe_allow_html=True)
        with c2:
            avg_conf = round(100 * sum(confidences) / len(confidences)) if confidences else 0
            st.markdown(
                f"""
                <div class="card">
                    <div class="kpi-label">AVG. PRIORITY CONFIDENCE</div>
                    <div class="kpi-value" style="color:{BLUE}">{avg_conf}%</div>
                    <div class="kpi-sub">Across {len(inc)} session incident(s)</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
