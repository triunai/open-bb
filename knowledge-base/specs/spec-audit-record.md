# Spec Audit Record

> **Audit of: OpenBB Workspace Build Specification**
>
> *Audit Date: 2026-01-05*  
> *Status: ✅ Passed (with patches applied)*

---

## Summary

The spec was validated against current OpenBB docs + community patterns. It is **correct enough to build immediately**, and with patches applied becomes **cornerstone-grade**.

---

## ✅ Confirmed Correct (No Changes Needed)

| Item | Validation | Source |
|------|------------|--------|
| **Parameter-linking / grouping** | "Shared ticker/date ripples across widgets" matches Workspace design | [Widgets Overview](https://docs.openbb.co/workspace/analysts/widgets/overview) |
| **Custom backend model (`widgets.json`)** | Accurate: Workspace expects API + `widgets.json`, any tech stack works | [Data Integration](https://docs.openbb.co/workspace/developers/data-integration) |
| **`openbb-api` defaults** | Default `127.0.0.1:6900`, falls back to another port if taken | [openbb-api](https://docs.openbb.co/python/extensions/interface/openbb-api) |
| **Static asset rebuild footgun** | Correctly captured: `openbb-build`, `openbb.build()`, `OPENBB_AUTO_BUILD` | [Basic Usage](https://docs.openbb.co/python/basic_usage) |
| **Mobile + ngrok header** | `ngrok-skip-browser-warning` header matches official guidance | [Platform Installer](https://docs.openbb.co/workspace/getting-started/platform-installer) |
| **OFAC RSS retirement** | Notice (Nov 22, 2024), retired (Jan 31, 2025), GovDelivery for email | [OFAC Notice](https://ofac.treasury.gov/recent-actions/20241122) |

---

## 🔧 Corrections Applied

### 1) "Two Modes" → "Two Apps"

**Problem:** Workspace doesn't have a literal "mode switch" in one dashboard.

**Fix:** Changed to "Two Apps" (Event Response + Monitoring) as first-class Workspace concept.

📖 **Reference:** [Apps](https://docs.openbb.co/workspace/analysts/apps)

---

### 2) Provider Discipline Reference

**Problem:** Original pointed only to CLI Data Sources.

**Fix:** Added ODP Python Providers as primary reference (matches Workspace + openbb-api architecture).

📖 **Reference:** [Providers](https://docs.openbb.co/python/extensions/providers)

---

### 3) CORS Configuration

**Problem:** Hardcoded `https://pro.openbb.co` only.

**Fix:** Made configurable allowed origins (enterprise/self-host scenarios).

---

### 4) Added `/apps.json` to Backend Contract

**Problem:** Implied but not explicitly required.

**Fix:** Added to required endpoints table (recommended, not mandatory).

📖 **Reference:** [Data Integration](https://docs.openbb.co/workspace/developers/data-integration)

---

## ➕ Additions Made

### 1) OFAC Coverage Scope + Limitations (Section 4G)

**Critical addition:** Not all authorizations are public.

- Private/narrow authorizations may not appear in OFAC page diffs
- Mitigation: verify via reputable news sources when price reacts but no OFAC diff

📖 **Reference:** [Reuters - Chevron narrow authorization](https://www.reuters.com/business/energy/us-grants-chevron-narrow-authorization-keep-assets-venezuela-sources-say-2025-05-27/)

---

### 2) Cornerstone-Grade Non-Functional Requirements

**Added for 6-12 month survival:**

#### Reliability / Correctness
- Idempotency (dedupe by hash)
- Backoff + jitter on polling
- Audit trail (raw HTML snapshots)
- Clock discipline (UTC storage, local display)

#### Security
- API key rotation plan
- Deny by default
- No secret logging

#### Observability
- `/health` and `/metrics` endpoints
- Last poll time surfaced in widget

---

## 📋 Validation Checklist

| Check | Result |
|-------|--------|
| Mental model matches OpenBB architecture | ✅ |
| Widget linking documented correctly | ✅ |
| Custom backend pattern accurate | ✅ |
| `openbb-api` details correct | ✅ |
| Static asset rebuild documented | ✅ |
| Mobile access pattern correct | ✅ |
| OFAC RSS retirement noted | ✅ |
| Private authorization risk noted | ✅ (added) |
| `/apps.json` included | ✅ (added) |
| Cornerstone NFRs included | ✅ (added) |

---

## Reference Links (Validation Sources)

| Resource | URL |
|----------|-----|
| Widgets Overview | https://docs.openbb.co/workspace/analysts/widgets/overview |
| Data Integration | https://docs.openbb.co/workspace/developers/data-integration |
| openbb-api | https://docs.openbb.co/python/extensions/interface/openbb-api |
| Basic Usage | https://docs.openbb.co/python/basic_usage |
| Platform Installer | https://docs.openbb.co/workspace/getting-started/platform-installer |
| Apps | https://docs.openbb.co/workspace/analysts/apps |
| Providers | https://docs.openbb.co/python/extensions/providers |
| OFAC RSS Retirement | https://ofac.treasury.gov/recent-actions/20241122 |
| Reuters (Private Auth) | https://www.reuters.com/business/energy/us-grants-chevron-narrow-authorization-keep-assets-venezuela-sources-say-2025-05-27/ |

---

*Audit completed: 2026-01-05*
