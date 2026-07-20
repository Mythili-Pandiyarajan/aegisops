# AegisOps — Multi-Agent IT Operations Copilot

A multi-agent system that handles an IT incident the way an IT support engineer
would: classify it, predict its priority, retrieve relevant knowledge, read the
logs, propose (and, with approval, run) diagnostic commands, and produce a
manager-ready summary — instead of just answering a question about it.

> Status: 🚧 in active development. See [Roadmap](#roadmap) for what's built
> vs. planned.

## Demo

[Demo video link — add once recorded]

## Why this exists

Most "AI IT support" demos are a single LLM call wrapped in a chat UI. AegisOps
is built as a pipeline of specialized agents, each with a narrow job and a
clear boundary on what it's allowed to do — closer to how a real on-call
workflow is structured than to a chatbot.

It also deliberately combines a **traditional supervised ML model** (XGBoost,
trained on historical ticket data) with the agentic layer, rather than asking
an LLM to guess priority from scratch. The ML model and the LLM-based
classifier run in **parallel**, because priority ("how urgent") and category
("what kind of problem") are independent signals extracted from the same
incident text, not a dependency chain.

## Architecture

```
                    Incident (free text)
                           │
             ┌─────────────┴─────────────┐
             ▼                           ▼
   Priority Predictor            Incident Classifier Agent
   (existing XGBoost model,      (network / hardware / database /
    reused from the ITSM          security / email)
    priority project)
             │                           │
             └─────────────┬─────────────┘
                           ▼
                     Merge Node
                (priority + category)
                           │
                           ▼
                 Knowledge / RAG Agent
        (internal docs, SOPs, past resolved incidents)
                           │
                           ▼
                  Log Analysis Agent
         (server.log, nginx.log, docker logs → root cause)
                           │
                           ▼
              Shell Agent  🔒 sandboxed, read-only,
              allowlisted commands only, human
              approval required before execution
                           │
                           ▼
               Ticket Generator (mocked)
                           │
                           ▼
                 Manager Summary Agent
     (root cause, fix, time taken, priority, confidence, risk)
```

(Architecture diagram shown above — a rendered image version can be added later.)

## What this deliberately does NOT do (and why)

Being explicit about scope is part of the design, not a gap in it:

- **No arbitrary shell execution.** The Shell Agent can only run a fixed
  allowlist of read-only diagnostic commands (`ping`, `df -h`,
  `systemctl status`, `docker ps`, etc.), inside an isolated Docker sandbox
  with no host access, and only after human approval. It cannot construct
  commands from free-form LLM output.
- **No live Jira / ServiceNow integration.** The Ticket Generator produces a
  structured ticket payload and logs it. The point being demonstrated is that
  the agent knows *when* and *how* to escalate — not a production ticketing
  integration.
- **No voice input, no live Grafana/Kubernetes monitoring.** Out of scope for
  what this project is trying to prove; noted here so it's a deliberate cut,
  not an oversight.

## Tech stack

- **Orchestration:** LangGraph (state graph, explicit nodes/edges, checkpointing)
- **ML:** scikit-learn / XGBoost (reused priority model), FAISS (RAG retrieval)
- **LLM:** [provider — e.g. Groq / free-tier model]
- **Sandbox:** Docker (isolated container for the Shell Agent)
- **UI:** Streamlit (includes a live agent-activity view — which agent is
  running, messages between agents, decisions/confidence at each step)
- **Tests:** pytest
- **CI:** GitHub Actions (lint + tests on push)

## Project structure

```
aegisops/
├── agents/          # one file per agent — classifier, RAG, log analysis,
│                    # shell, ticket generator, manager summary
├── graph/           # LangGraph state schema + graph definition
├── tools/           # tool wrappers (priority model, FAISS retriever, etc.)
├── sandbox/         # Docker sandbox config + command allowlist
├── rag/             # knowledge corpus + FAISS index build scripts
├── data/
│   └── sample_logs/ # realistic sample logs used for the Log Analysis Agent
├── tests/           # pytest suite
├── docs/            # architecture notes, diagrams
└── .github/workflows/ci.yml
```

## Running locally

```bash
git clone <repo-url>
cd aegisops
pip install -r requirements.txt
docker build -t aegisops-sandbox ./sandbox
streamlit run app.py
```

## Roadmap

- [ ] Priority Predictor + Classifier Agent (parallel) + merge node
- [ ] Knowledge/RAG Agent over sample SOPs + incident history
- [ ] Log Analysis Agent (realistic sample logs)
- [ ] Manager Summary Agent
- [ ] Shell Agent (sandboxed, allowlisted, approval-gated)
- [ ] Ticket Generator (mocked)
- [ ] Streamlit dashboard with live agent-activity view
- [ ] Tests + CI
- [ ] Docker Compose for full local stack
- [ ] Demo video

## Author

Mythili Pandiyarajan — [GitHub](https://github.com/Mythili-Pandiyarajan)
