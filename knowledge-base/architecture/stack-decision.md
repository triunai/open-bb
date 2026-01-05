# Stack Decision Record

> **ADR: Choosing the right stack for OpenBB + OFAC Scanner cornerstone system**
>
> *Status: Accepted*  
> *Date: 2026-01-05*

---

## Context

We need to choose a stack for building a long-term "cornerstone" system that integrates:
1. **OpenBB Workspace** (market decision cockpit)
2. **OFAC Scanner** (Venezuela sanctions monitoring)
3. **Custom data surfaces** (thesis validation widgets)

The question: Streamlit? React? Something else?

---

## Decision

**OpenBB Workspace (UI) + FastAPI backends (openbb-api + custom OFAC service)**

Add React/Vite later **only** if we genuinely need an admin console.

---

## Rationale

### What the OpenBB community/docs actually imply

#### ✅ The "Happy Path" OpenBB Designs For

**FastAPI + Uvicorn** is the default examples + tooling path:

| Evidence | Source |
|----------|--------|
| `openbb-api` / `openbb-platform-api` is built to convert FastAPI/OpenAPI into Workspace backends + widget definitions | [ODP API Docs](https://docs.openbb.co/python/extensions/interface/openbb-api) |
| Workspace "Hello World" backend example uses FastAPI with required endpoints (`/`, `/widgets.json`, `/apps.json`) | [Data Integration](https://docs.openbb.co/workspace/developers/data-integration) |
| Official backend template repo: *"examples use FastAPI because familiarity, but it can be any language"* | [GitHub](https://github.com/OpenBB-finance/backends-for-openbb) |

**Conclusion:** FastAPI is community-aligned because **Workspace wants an API backend**, and OpenBB gives you batteries for FastAPI.

---

#### ⚠️ Streamlit ≠ Future Cornerstone

OpenBB historically showcased Streamlit dashboards (Terminal era), but they've moved toward:
- **Platform / data integration / standardization** focus
- **Sunsetting the old Terminal direction**

📖 Reference: [Sunsetting OpenBB Terminal](https://openbb.co/blog/sunsetting-openbb-terminal-why-how-and-what-now)

If this is a *cornerstone system*, Streamlit is fine for quick internal prototypes, but **not the default long-term OpenBB architecture anymore**.

---

## Decision Matrix

| Option | Best For | Why It Matches (or Doesn't) |
|--------|----------|----------------------------|
| **A: Workspace UI + FastAPI backends** ✅ | Long-term cornerstone, clean integration, minimal front-end burden | Custom backend spec + FastAPI tooling + widgets.json |
| **B: React/Vite + FastAPI** | You want to own the UX and not rely on Workspace | You'll likely still keep Workspace for market verification anyway |
| **C: Streamlit + OpenBB Python** | Solo prototype | Not ideal for cornerstone—you'll outgrow it |

---

## Streamlit: When It's Good vs. When It's Not

### ✅ Streamlit Good For
- 1–2 day prototypes
- Personal dashboards
- Quick charting + forms
- "Internal tool" vibe

### ❌ Streamlit Weak For Cornerstone
- Auth + permissions + multi-user (gets messy fast)
- Modular UI at scale
- Embedding into other systems
- Long-lived maintainability as system grows

**Key Point:** OpenBB's current "first-class integration surface" is **Workspace ↔ backends**, not "Streamlit app deployment".

---

## Recommended Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────────┐
│                     OpenBB Workspace (UI)                       │
│                   "Decision Cockpit"                            │
└────────────────────────┬───────────────────────────────────────┘
                         │
         ┌───────────────┴───────────────┐
         │                               │
         ▼                               ▼
┌─────────────────────┐       ┌─────────────────────┐
│   openbb-api        │       │  OFAC Scanner       │
│   (Market Data)     │       │  Service (FastAPI)  │
│                     │       │                     │
│ • ODP connectors    │       │ • /widgets.json     │
│ • Provider data     │       │ • /ofac/venezuela   │
│ • Standard models   │       │ • /ofac/latest      │
│ • 127.0.0.1:6900    │       │ • /health           │
└─────────────────────┘       └──────────┬──────────┘
                                         │
                                         ▼
                              ┌─────────────────────┐
                              │   Postgres          │
                              │   (Storage)         │
                              │                     │
                              │ • Events            │
                              │ • Diffs             │
                              │ • Audit trail       │
                              └─────────────────────┘
```

### Component Breakdown

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Decision UI** | OpenBB Workspace | Market verification cockpit |
| **Market Data Backend** | OpenBB ODP (`openbb-api`) | FastAPI server (localhost or hosted) |
| **Thesis Backend** | FastAPI "OFAC Scanner Service" | Custom data + alerts |
| **Storage** | Postgres | Events, diffs, runs, audit trail |
| **Queue/Scheduler** | APScheduler or Celery/RQ | Start simple, upgrade later |
| **Deployment** | Docker Compose | Local first, then small VPS |
| **Auth** | API key header | Workspace → OFAC service (supported pattern) |
| **Integration Contract** | `widgets.json` + JSON endpoints | Table/chart/markdown widgets |

---

### Optional: React/Vite Admin Panel

**Only if you need:**
- Managing rules ("policy pistol thresholds")
- Managing watchlists
- Viewing logs / diffs / audit trail
- Manual overrides / annotations

**If you don't need those → skip React entirely.** Workspace is your UI.

---

## References

| Resource | URL |
|----------|-----|
| Data Integration | https://docs.openbb.co/workspace/developers/data-integration |
| ODP API | https://docs.openbb.co/python/extensions/interface/openbb-api |
| Backend Templates | https://github.com/OpenBB-finance/backends-for-openbb |
| Terminal Sunsetting | https://openbb.co/blog/sunsetting-openbb-terminal-why-how-and-what-now |
| Platform Installer (Auth) | https://docs.openbb.co/workspace/getting-started/platform-installer |
| widgets.json Reference | https://docs.openbb.co/workspace/developers/json-specs/widgets-json-reference |

---

*Decision recorded: 2026-01-05*
