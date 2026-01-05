# OpenBB Workspace Build Specification

> **Complete build spec for OpenBB Workspace + OFAC Venezuela Scanner Integration**
>
> *Derived from OpenBB docs + real community usage patterns*

---

## Table of Contents

1. [Mental Model](#0-the-community-correct-mental-model-)
2. [Short-Term Functional Spec](#1-short-term-functional-spec-)
3. [Short-Term Non-Functional Spec](#2-short-term-non-functional-spec-)
4. [Medium-Term: Local Backend](#3-medium-term-local-backend-)
5. [Long-Term: OFAC Integration](#4-long-term-ofac-integration-)
6. [Build Checklist](#5-full-build-checklist-)
7. [Execution Order](#6-most-efficient-next-step-)

---

## 0) The "Community-Correct" Mental Model 🧭

OpenBB today is basically:

| Layer | What It Is | Reference |
|-------|-----------|-----------|
| **Workspace (UI)** | Dashboards + widgets + Copilot (the "cockpit") | [docs.openbb.co/workspace](https://docs.openbb.co/workspace) |
| **ODP / Platform (backend)** | Data connectors + standardized models + REST API (`openbb-api`) | [GitHub](https://github.com/OpenBB-finance/OpenBB) |
| **Custom backends** | *Your* APIs (OFAC scanner, proprietary feeds) exposed as widgets | [Data Integration Docs](https://docs.openbb.co/workspace/developers/data-integration) |

### Target Architecture Flow

**Current (Alert-driven):**
```
OFAC Scanner → (alert) → Workspace dashboard (market verification) → decision
```

**Future (Unified screen):**
```
OFAC Scanner → Workspace widget (same screen as market response)
```

---

## 1) Short-Term Functional Spec ✅

> *What actually helps your thesis this week*

### A. Dashboard Structure (Parameter-Linked)

OpenBB widgets become powerful when you **parameter-link** them (shared ticker/date inputs update everything together). This is a core intended workflow.

📖 **Reference:** [Widgets Overview](https://docs.openbb.co/workspace/analysts/widgets/overview)

#### Build Two Apps (Not "Modes" in One Dashboard)

> ⚠️ **Correction:** Workspace doesn't have a literal "mode switch" concept. The community-aligned implementation is **two separate Apps**.

📖 **Reference:** [Apps](https://docs.openbb.co/workspace/analysts/apps)

---

##### **App 1: "Event Response" (Primary)**

**Purpose:** "OFAC fired → what did the market do?"

| Widget | Purpose |
|--------|---------|
| **CVX price / returns / volume** | Primary equity response |
| **XLE price** | Sector benchmark |
| **Relative strength (CVX vs XLE)** | Outperformance validation |
| **Oil context (WTI + Brent)** | Commodity backdrop |
| **News panel** | Chevron/Venezuela/sanctions keywords |
| **Notes widget** | "Policy pistol rules", thesis invalidation criteria |

**Key Tactic:** Make sure the "symbol" / date range parameters are grouped/linked so one change ripples across all widgets.

---

##### **App 2: "Monitoring" (Secondary)**

**Purpose:** Watchlist + macro + news (ongoing surveillance)

| Widget | Purpose |
|--------|---------|
| **Watchlist** | CVX, XLE, oil majors |
| **Macro calendar** | Fed, OPEC, sanctions-related dates |
| **News feed** | Broader market context |

---

### B. Copilot Configuration

Copilot is strongest when you **control what context it can see** (you can manage widgets/data used as context; also add your own agents later).

📖 **Reference:** [Copilot Basics](https://docs.openbb.co/workspace/analysts/ai-features/copilot-basics)

#### Practical "Community Wisdom" Usage:

1. **Pin your Event Response widgets** into Copilot context
2. **Ask verification questions only** (not trading decisions):
   - "Did CVX outperform XLE since [date]?"
   - "Summarize today's catalyst headlines and list sources"
   - "What changed between the last two sessions?"

> **Mental Model:** Copilot = **structured summarizer**, not trading brain.

---

## 2) Short-Term Non-Functional Spec 🧱

> *The boring bits that decide whether you'll still be using this in 6 months*

### A. Data Reliability: Provider Discipline

OpenBB endpoints often support **multiple providers**, but coverage differs. You're expected to choose providers explicitly when needed.

📖 **References:**
- [ODP Python Providers](https://docs.openbb.co/python/extensions/providers) *(primary - matches Workspace + openbb-api architecture)*
- [CLI Data Sources](https://docs.openbb.co/cli/data-sources) *(secondary)*

#### Rule:
- Start with **free providers** (fine for prototyping)
- Upgrade only the **exact pieces that cause pain** (news/real-time/coverage)

---

### B. The #1 OpenBB Dev Footgun: Static Assets/Build

When you install providers/extensions, you may need to rebuild static assets, or you'll see missing-provider / missing-endpoint weirdness.

#### Known Fixes:

| Situation | Command |
|-----------|---------|
| After pip install | `openbb-build` |
| In containers/CI | `openbb-build` (explicitly) |
| Provider mappings wrong | `python -c "import openbb; openbb.build()"` |
| Auto-build (env flag) | `OPENBB_AUTO_BUILD="true"` (but manual build is still a known fix) |

📖 **References:**
- [Installation](https://docs.openbb.co/python/installation)
- [Errors FAQ](https://docs.openbb.co/python/faqs/errors)

> ⚠️ **Community Pain Pattern:** This trips up everyone. When in doubt, rebuild.

---

## 3) Medium-Term: Local Backend 🔌

> *Where Workspace stops being "a nice UI" and becomes your system*

### A. Run the Local Backend

```bash
# Install
pip install "openbb[all]"

# Run (FastAPI on 127.0.0.1:6900)
openbb-api
```

📖 **Reference:** [GitHub - OpenBB](https://github.com/OpenBB-finance/OpenBB)

---

### B. Connect to Workspace

1. Open Workspace
2. Navigate to **Apps** → **Connect backend**
3. Enter URL: `http://127.0.0.1:6900`
4. **Test** → **Add**

---

### C. Mobile Access (Optional)

They explicitly recommend **ngrok** for exposing your local backend to phone access.

#### ngrok Setup:
1. Expose local backend via ngrok
2. Add `ngrok-skip-browser-warning` header

#### Browser Quirks:
- **Brave/Safari** may require HTTPS

📖 **Reference:** [Platform Installer](https://docs.openbb.co/workspace/getting-started/platform-installer)

---

## 4) Long-Term: OFAC Integration 🧠

> *Your OFAC system becomes a widget - the real endgame*

### A. Custom Backend Architecture

OpenBB Workspace supports a "custom backend" API + `widgets.json` describing widgets (first-class feature).

📖 **References:**
- [Data Integration](https://docs.openbb.co/workspace/developers/data-integration)
- [Backend Templates](https://github.com/OpenBB-finance/backends-for-openbb)

---

### B. Authentication (Required)

Workspace can pass **custom headers or query parameters** to your backend on every request.

**Recommendation:** Use a custom header like `X-API-KEY`

📖 **Reference:** [FAQs - Auth](https://docs.openbb.co/workspace/getting-started/faqs)

---

### C. Live Updates

`widgets.json` supports a `wsEndpoint` for websocket-style live widgets.

**Use Case:** "New OFAC event" appears without refresh

📖 **Reference:** [widgets.json Reference](https://docs.openbb.co/workspace/developers/json-specs/widgets-json-reference)

---

### D. Critical OFAC Reality Check ⚠️

> **OFAC retired the RSS feed** (official notice, January 31, 2025)

📖 **Reference:** [OFAC RSS Retirement Notice](https://ofac.treasury.gov/recent-actions/20241122)

#### Your Scanner Should Be Based On:

1. **Polling/diffing** OFAC Recent Actions / General Licenses pages
   - [Recent Actions](https://ofac.treasury.gov/recent-actions/general-licenses)
2. **Email alerts** (GovDelivery subscription)

> ⚠️ Many older "OFAC RSS scraper" tutorials are now **broken**.

---

### E. Proposed OFAC API Endpoints

| Endpoint | Purpose |
|----------|---------|
| `/ofac/latest` | Latest items |
| `/ofac/diff` | What changed since last run |
| `/ofac/venezuela` | Filtered view for thesis |

---

### F. Custom Backend Contract (Required Endpoints)

Your backend **MUST** expose:

| Endpoint | Required | Purpose |
|----------|----------|--------|
| `/widgets.json` | ✅ Yes | Widget definitions for Workspace |
| `/apps.json` | ⚡ Recommended | Enables Apps as "mode" equivalents |
| `/health` | ⚡ Recommended | Debugging + uptime checks |

> OpenBB's own reference backend includes both `widgets.json` and `apps.json`.

📖 **Reference:** [Data Integration](https://docs.openbb.co/workspace/developers/data-integration)

---

### G. OFAC Coverage Scope + Limitations ⚠️

#### Sources to Monitor (Public)

| Source | URL | Notes |
|--------|-----|-------|
| **Recent Actions** | https://ofac.treasury.gov/recent-actions | Primary (General Licenses + Venezuela items) |
| **Venezuela Sanctions** | https://ofac.treasury.gov/sanctions-programs-and-country-information/venezuela-related-sanctions | Program-specific page |
| **Venezuela FAQ** | *(topic page)* | Explains changes more clearly |
| **OFAC Press Releases** | https://home.treasury.gov/news/press-releases | Sometimes explains changes more clearly |
| **Federal Register** | *(publication of web general licenses)* | Appears later, useful for audit trail |

#### Critical Limitation: Private Authorizations

> ⚠️ **Not all Chevron/Venezuela permissions appear as public general license updates.**

There are cases where Chevron-related Venezuela authorization has been described as **private / narrow** in reporting.

📖 **Reference:** [Reuters - US grants Chevron narrow authorization](https://www.reuters.com/business/energy/us-grants-chevron-narrow-authorization-keep-assets-venezuela-sources-say-2025-05-27/)

**If price reacts but OFAC pages show no diff:**

1. Treat as **possible private/specific authorization or guidance**
2. Verify via reputable news sources (Reuters, Bloomberg, WSJ)
3. Log as "unconfirmed catalyst" with news source attribution

---

## 5) Full Build Checklist 📋

### Functional (Now)

- [ ] Dashboard with **CVX, XLE, WTI, Brent, news, notes**
- [ ] Parameter linking for ticker/date cohesion
- [ ] Copilot uses dashboard widgets as controlled context

### Functional (Soon)

- [ ] Run `openbb-api` backend and connect to Workspace
- [ ] Add provider keys via env / settings if needed (provider discipline)

### Functional (Later / OFAC Integration)

- [ ] OFAC scanner service with endpoints:
  - [ ] `/ofac/latest`
  - [ ] `/ofac/diff`
  - [ ] `/ofac/venezuela`
- [ ] Workspace custom backend + `widgets.json`

### Non-Functional (The Stuff That Keeps It Alive)

| Requirement | Status | Notes |
|------------|--------|-------|
| 🔒 Auth headers from Workspace to backend | ⬜ | Use `X-API-KEY` |
| 🌐 CORS configurable allowed origins | ⬜ | Default `https://pro.openbb.co`, but make configurable for enterprise/self-host |
| 🧱 Rebuild assets after provider changes | ⬜ | `openbb-build` / `openbb.build()` |
| 📱 ngrok header + HTTPS for mobile | ⬜ | If remote/mobile needed |
| 🧾 Logging + timestamps on OFAC poller | ⬜ | Prove when you knew |

---

### Cornerstone-Grade Non-Functional Requirements

> *These are the items that make the system survive 6–12 months.*

#### Reliability / Correctness

| Requirement | Implementation |
|-------------|----------------|
| **Idempotency** | Dedupe events by stable hash (`title + url + date`) |
| **Backoff + jitter** | Exponential backoff on polling failures |
| **Audit trail** | Store raw HTML snapshots (or extracted text) for proof |
| **Clock discipline** | Store timestamps in **UTC**, display in local |

#### Security

| Requirement | Implementation |
|-------------|----------------|
| **API key rotation plan** | Document how to rotate keys without downtime |
| **Deny by default** | Reject requests with missing/invalid key |
| **No secret logging** | Ensure API keys never appear in logs |

#### Observability

| Requirement | Implementation |
|-------------|----------------|
| `/health` endpoint | Basic liveness check |
| `/metrics` endpoint | Or at least structured JSON logs |
| **Last poll time in widget** | Surface "last successful poll" in the widget itself |

---

## 6) Most Efficient Next Step 🎯

> *So you don't overbuild*

Execute in this order:

### Step 1: Build Event Response Dashboard ✅
- Parameter-linking enabled
- All 6 core widgets configured

### Step 2: Connect Local Backend
- Run `openbb-api`
- Connect Workspace to `127.0.0.1:6900`

### Step 3: Build OFAC Scanner Widget
- Tiny service with endpoints
- Expose as Workspace widget via custom backend
- `widgets.json` entry

---

## Next Up: Venezuela OFAC Widget Spec

Ready to build when you are:
- `widgets.json` entry (table + "last updated" badge)
- FastAPI endpoints
- Diffing strategy (RSS retirement accounted for)

---

## Reference Links

| Resource | URL |
|----------|-----|
| Workspace Overview | https://docs.openbb.co/workspace |
| OpenBB GitHub | https://github.com/OpenBB-finance/OpenBB |
| Data Integration | https://docs.openbb.co/workspace/developers/data-integration |
| Widgets Overview | https://docs.openbb.co/workspace/analysts/widgets/overview |
| Copilot Basics | https://docs.openbb.co/workspace/analysts/ai-features/copilot-basics |
| Data Sources | https://docs.openbb.co/cli/data-sources |
| Installation | https://docs.openbb.co/python/installation |
| Errors FAQ | https://docs.openbb.co/python/faqs/errors |
| Platform Installer | https://docs.openbb.co/workspace/getting-started/platform-installer |
| Backend Templates | https://github.com/OpenBB-finance/backends-for-openbb |
| FAQs | https://docs.openbb.co/workspace/getting-started/faqs |
| widgets.json Reference | https://docs.openbb.co/workspace/developers/json-specs/widgets-json-reference |
| OFAC RSS Retirement | https://ofac.treasury.gov/recent-actions/20241122 |
| OFAC Recent Actions | https://ofac.treasury.gov/recent-actions/general-licenses |

---

*Document created: 2026-01-05*  
*Last audit: 2026-01-05*  
*Status: Active specification (audited & patched)*
