# OFAC Scanner Technical Specification v1.0

> **Technical implementation guide for the OFAC Venezuela Scanner Service**
>
> *Part of the OpenBB Workspace + Custom Backend architecture*
>
> *Version: 1.0*  
> *Date: 2026-01-05*

---

## Table of Contents

1. [System Architecture](#1-system-architecture)
2. [Database Schema](#2-database-schema)
3. [API Endpoints](#3-api-endpoints)
4. [widgets.json Specification](#4-widgetsjson-specification)
5. [apps.json Specification](#5-appsjson-specification)
6. [Poller & Diff Algorithm](#6-poller--diff-algorithm)
7. [Alert Rules ("Policy Pistol")](#7-alert-rules-policy-pistol)
8. [Deployment](#8-deployment)

---

## 1) System Architecture

### High-Level Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      OpenBB Workspace (UI)                              │
│                      https://pro.openbb.co                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────┐  │
│  │ Event Response  │  │   Monitoring    │  │   OFAC Venezuela        │  │
│  │      App        │  │      App        │  │   Widget (custom)       │  │
│  └────────┬────────┘  └────────┬────────┘  └───────────┬─────────────┘  │
└───────────┼────────────────────┼───────────────────────┼────────────────┘
            │                    │                       │
            │ Market Data        │                       │ X-API-KEY header
            ▼                    ▼                       ▼
┌───────────────────────┐        │        ┌───────────────────────────────┐
│   openbb-api          │        │        │   OFAC Scanner Service        │
│   (ODP Backend)       │        │        │   (FastAPI)                   │
│                       │        │        │                               │
│   127.0.0.1:6900      │        │        │   127.0.0.1:8000              │
│                       │        │        │                               │
│ • /api/v1/equity/*    │◄───────┘        │ • GET  /                      │
│ • /api/v1/news/*      │                 │ • GET  /health                │
│ • /api/v1/index/*     │                 │ • GET  /widgets.json          │
│                       │                 │ • GET  /apps.json             │
└───────────────────────┘                 │ • GET  /ofac/latest           │
                                          │ • GET  /ofac/diff             │
                                          │ • GET  /ofac/venezuela        │
                                          │ • GET  /ofac/status           │
                                          │                               │
                                          └───────────────┬───────────────┘
                                                          │
                                                          ▼
                                          ┌───────────────────────────────┐
                                          │        PostgreSQL             │
                                          │                               │
                                          │ • ofac_events                 │
                                          │ • ofac_snapshots              │
                                          │ • poll_runs                   │
                                          │ • alert_log                   │
                                          └───────────────────────────────┘
                                                          ▲
                                                          │
                                          ┌───────────────┴───────────────┐
                                          │        OFAC Poller            │
                                          │     (APScheduler job)         │
                                          │                               │
                                          │ • Polls every 15 min          │
                                          │ • Diffs against last snapshot │
                                          │ • Writes new events           │
                                          └───────────────────────────────┘
                                                          │
                                                          │ HTTP GET
                                                          ▼
                                          ┌───────────────────────────────┐
                                          │      OFAC Recent Actions      │
                                          │  ofac.treasury.gov/recent-*   │
                                          └───────────────────────────────┘
```

---

### Component Responsibilities

| Component | Port | Responsibility |
|-----------|------|----------------|
| **OpenBB Workspace** | N/A (cloud) | UI, dashboards, widget rendering |
| **openbb-api** | 6900 | Market data (equity, news, indices) |
| **OFAC Scanner Service** | 8000 | Custom OFAC data, Venezuela filtering |
| **PostgreSQL** | 5432 | Persistent storage for events, diffs, audit |
| **OFAC Poller** | (in-process) | Scheduled polling of OFAC pages |

---

## 2) Database Schema

### Entity Relationship Diagram

```
┌─────────────────┐       ┌─────────────────┐
│   poll_runs     │       │ ofac_snapshots  │
├─────────────────┤       ├─────────────────┤
│ id (PK)         │       │ id (PK)         │
│ started_at      │       │ poll_run_id (FK)│───┐
│ completed_at    │───────│ source_url      │   │
│ status          │       │ raw_html        │   │
│ events_found    │       │ extracted_text  │   │
│ error_message   │       │ content_hash    │   │
└─────────────────┘       │ captured_at     │   │
                          └─────────────────┘   │
                                                │
┌───────────────────────────────────────────────┘
│
│       ┌─────────────────────────────────────┐
│       │           ofac_events               │
│       ├─────────────────────────────────────┤
└──────▶│ id (PK)                             │
        │ poll_run_id (FK)                    │
        │ event_hash (UNIQUE)                 │  ◄── Idempotency key
        │ title                               │
        │ url                                 │
        │ published_date                      │
        │ category                            │
        │ is_venezuela_related (BOOL)         │
        │ is_chevron_related (BOOL)           │
        │ keywords_matched (JSONB)            │
        │ first_seen_at                       │
        │ created_at                          │
        └─────────────────────────────────────┘

        ┌─────────────────────────────────────┐
        │           alert_log                 │
        ├─────────────────────────────────────┤
        │ id (PK)                             │
        │ event_id (FK)                       │
        │ alert_type                          │
        │ triggered_at                        │
        │ confidence_score                    │
        │ rule_matched                        │
        │ acknowledged                        │
        │ acknowledged_at                     │
        │ notes                               │
        └─────────────────────────────────────┘
```

---

### SQL Schema

```sql
-- Poll execution tracking
CREATE TABLE poll_runs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    started_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at    TIMESTAMPTZ,
    status          VARCHAR(20) NOT NULL DEFAULT 'running', -- running, success, failed
    events_found    INTEGER DEFAULT 0,
    error_message   TEXT,
    
    CONSTRAINT valid_status CHECK (status IN ('running', 'success', 'failed'))
);

-- Raw HTML snapshots for audit trail
CREATE TABLE ofac_snapshots (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    poll_run_id     UUID NOT NULL REFERENCES poll_runs(id),
    source_url      TEXT NOT NULL,
    raw_html        TEXT NOT NULL,
    extracted_text  TEXT,
    content_hash    VARCHAR(64) NOT NULL,  -- SHA-256 of extracted_text
    captured_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    INDEX idx_snapshots_hash (content_hash),
    INDEX idx_snapshots_poll (poll_run_id)
);

-- Parsed OFAC events
CREATE TABLE ofac_events (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    poll_run_id             UUID REFERENCES poll_runs(id),
    event_hash              VARCHAR(64) UNIQUE NOT NULL,  -- SHA-256(title + url + date)
    title                   TEXT NOT NULL,
    url                     TEXT NOT NULL,
    published_date          DATE,
    category                VARCHAR(100),  -- 'Sanctions List Updates', 'General Licenses', etc.
    is_venezuela_related    BOOLEAN NOT NULL DEFAULT FALSE,
    is_chevron_related      BOOLEAN NOT NULL DEFAULT FALSE,
    keywords_matched        JSONB DEFAULT '[]',
    first_seen_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    INDEX idx_events_hash (event_hash),
    INDEX idx_events_venezuela (is_venezuela_related) WHERE is_venezuela_related = TRUE,
    INDEX idx_events_date (published_date DESC)
);

-- Alert audit log
CREATE TABLE alert_log (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id            UUID NOT NULL REFERENCES ofac_events(id),
    alert_type          VARCHAR(50) NOT NULL,  -- 'policy_pistol', 'venezuela_gl', etc.
    triggered_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    confidence_score    DECIMAL(3,2),  -- 0.00 to 1.00
    rule_matched        TEXT NOT NULL,
    acknowledged        BOOLEAN DEFAULT FALSE,
    acknowledged_at     TIMESTAMPTZ,
    notes               TEXT,
    
    INDEX idx_alerts_event (event_id),
    INDEX idx_alerts_type (alert_type),
    INDEX idx_alerts_unacked (acknowledged) WHERE acknowledged = FALSE
);
```

---

## 3) API Endpoints

### Base Configuration

```python
# main.py
from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os

app = FastAPI(
    title="OFAC Scanner Service",
    description="Venezuela sanctions monitoring for OpenBB Workspace",
    version="1.0.0"
)

# Configurable CORS origins
ALLOWED_ORIGINS = os.getenv("CORS_ORIGINS", "https://pro.openbb.co").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Key authentication
API_KEY = os.getenv("OFAC_API_KEY")

async def verify_api_key(x_api_key: str = Header(None)):
    if not API_KEY:
        return  # Dev mode: no auth
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
```

---

### Endpoint Specifications

#### `GET /` - Root

```python
@app.get("/")
def root():
    return {"service": "OFAC Scanner", "version": "1.0.0"}
```

---

#### `GET /health` - Health Check

```python
@app.get("/health")
async def health():
    """Health check with last poll status."""
    last_poll = await get_last_poll()
    return {
        "status": "healthy",
        "last_poll_at": last_poll.completed_at.isoformat() if last_poll else None,
        "last_poll_status": last_poll.status if last_poll else "never",
        "events_total": await get_total_events(),
        "venezuela_events": await get_venezuela_events_count()
    }
```

**Response:**
```json
{
  "status": "healthy",
  "last_poll_at": "2026-01-05T02:00:00Z",
  "last_poll_status": "success",
  "events_total": 3009,
  "venezuela_events": 47
}
```

---

#### `GET /widgets.json` - Widget Definitions

```python
@app.get("/widgets.json")
def get_widgets():
    return JSONResponse(content=WIDGETS_CONFIG)
```

*(See Section 4 for full widgets.json)*

---

#### `GET /apps.json` - App Definitions

```python
@app.get("/apps.json")
def get_apps():
    return JSONResponse(content=APPS_CONFIG)
```

*(See Section 5 for full apps.json)*

---

#### `GET /ofac/latest` - Latest Events

```python
@app.get("/ofac/latest", dependencies=[Depends(verify_api_key)])
async def get_latest_events(limit: int = 20):
    """
    Returns the most recent OFAC events.
    
    Query params:
        limit: Max events to return (default 20, max 100)
    """
    events = await db.fetch_latest_events(min(limit, 100))
    return [event.to_dict() for event in events]
```

**Response:**
```json
[
  {
    "id": "uuid-here",
    "title": "Venezuela-related Designations; Issuance of Venezuela-related General License",
    "url": "https://ofac.treasury.gov/recent-actions/20251219",
    "published_date": "2025-12-19",
    "category": "Sanctions List Updates",
    "is_venezuela_related": true,
    "is_chevron_related": false,
    "keywords_matched": ["venezuela", "general license"],
    "first_seen_at": "2025-12-19T14:30:00Z"
  }
]
```

---

#### `GET /ofac/venezuela` - Venezuela-Filtered Events

```python
@app.get("/ofac/venezuela", dependencies=[Depends(verify_api_key)])
async def get_venezuela_events(
    limit: int = 50,
    since: Optional[date] = None,
    chevron_only: bool = False
):
    """
    Returns Venezuela-related OFAC events.
    
    Query params:
        limit: Max events (default 50)
        since: Only events after this date
        chevron_only: Filter to Chevron-mentioned events only
    """
    events = await db.fetch_venezuela_events(
        limit=min(limit, 200),
        since=since,
        chevron_only=chevron_only
    )
    return [event.to_dict() for event in events]
```

---

#### `GET /ofac/diff` - Changes Since Last Check

```python
@app.get("/ofac/diff", dependencies=[Depends(verify_api_key)])
async def get_diff(since_hours: int = 24):
    """
    Returns events first seen within the specified window.
    
    Query params:
        since_hours: Hours to look back (default 24, max 168)
    """
    cutoff = datetime.utcnow() - timedelta(hours=min(since_hours, 168))
    new_events = await db.fetch_events_since(cutoff)
    
    return {
        "since": cutoff.isoformat(),
        "new_count": len(new_events),
        "venezuela_count": sum(1 for e in new_events if e.is_venezuela_related),
        "events": [e.to_dict() for e in new_events]
    }
```

---

#### `GET /ofac/status` - Poller Status (Widget-Friendly)

```python
@app.get("/ofac/status", dependencies=[Depends(verify_api_key)])
async def get_status():
    """Returns status info formatted for the status widget."""
    last_poll = await get_last_poll()
    last_venezuela = await get_last_venezuela_event()
    
    return {
        "last_poll_utc": last_poll.completed_at.isoformat() if last_poll else None,
        "poll_status": last_poll.status if last_poll else "never",
        "last_venezuela_event": last_venezuela.title if last_venezuela else None,
        "last_venezuela_date": last_venezuela.published_date.isoformat() if last_venezuela else None,
        "confidence": "high" if last_poll and last_poll.status == "success" else "low"
    }
```

---

## 4) widgets.json Specification

```json
{
  "ofac_venezuela_events": {
    "name": "OFAC Venezuela Events",
    "description": "Recent OFAC actions related to Venezuela sanctions, including general licenses and designations. Critical for CVX thesis validation.",
    "category": "OFAC Scanner",
    "subCategory": "Venezuela",
    "type": "table",
    "endpoint": "ofac/venezuela",
    "gridData": {
      "w": 24,
      "h": 12,
      "minW": 16,
      "minH": 8
    },
    "data": {
      "table": {
        "enableCharts": false,
        "showAll": true,
        "columnsDefs": [
          {
            "field": "published_date",
            "headerName": "Date",
            "cellDataType": "date",
            "width": 100,
            "pinned": "left"
          },
          {
            "field": "title",
            "headerName": "Title",
            "cellDataType": "text",
            "width": 400,
            "renderFn": "cellOnClick",
            "renderFnParams": {
              "actionType": "url",
              "urlField": "url"
            }
          },
          {
            "field": "category",
            "headerName": "Category",
            "cellDataType": "text",
            "width": 150
          },
          {
            "field": "is_chevron_related",
            "headerName": "CVX?",
            "cellDataType": "boolean",
            "width": 80,
            "renderFn": "columnColor",
            "renderFnParams": {
              "colorRules": [
                { "condition": "equals", "value": true, "color": "green", "fill": true },
                { "condition": "equals", "value": false, "color": "gray", "fill": false }
              ]
            }
          },
          {
            "field": "keywords_matched",
            "headerName": "Keywords",
            "cellDataType": "text",
            "width": 200
          }
        ]
      }
    },
    "params": [
      {
        "paramName": "limit",
        "value": "50",
        "label": "Max Results",
        "type": "text",
        "show": true,
        "description": "Maximum events to display"
      },
      {
        "paramName": "chevron_only",
        "value": "false",
        "label": "Chevron Only",
        "type": "text",
        "show": true,
        "description": "Filter to Chevron-mentioned events",
        "options": [
          { "label": "All Venezuela", "value": "false" },
          { "label": "Chevron Only", "value": "true" }
        ]
      }
    ],
    "refetchInterval": 900000,
    "staleTime": 300000
  },

  "ofac_status": {
    "name": "OFAC Scanner Status",
    "description": "Live status of the OFAC polling service with last update time and confidence indicator.",
    "category": "OFAC Scanner",
    "subCategory": "Status",
    "type": "markdown",
    "endpoint": "ofac/status",
    "gridData": {
      "w": 8,
      "h": 4,
      "minW": 6,
      "minH": 3
    },
    "refetchInterval": 60000,
    "staleTime": 30000
  },

  "ofac_diff": {
    "name": "OFAC Changes (24h)",
    "description": "New OFAC events detected in the last 24 hours. Highlights Venezuela-related items.",
    "category": "OFAC Scanner",
    "subCategory": "Alerts",
    "type": "table",
    "endpoint": "ofac/diff",
    "gridData": {
      "w": 20,
      "h": 8,
      "minW": 12,
      "minH": 6
    },
    "data": {
      "dataKey": "events",
      "table": {
        "enableCharts": false,
        "showAll": true,
        "columnsDefs": [
          {
            "field": "first_seen_at",
            "headerName": "Detected",
            "cellDataType": "date",
            "width": 150
          },
          {
            "field": "title",
            "headerName": "Title",
            "cellDataType": "text",
            "width": 350
          },
          {
            "field": "is_venezuela_related",
            "headerName": "🇻🇪",
            "cellDataType": "boolean",
            "width": 60,
            "renderFn": "columnColor",
            "renderFnParams": {
              "colorRules": [
                { "condition": "equals", "value": true, "color": "yellow", "fill": true }
              ]
            }
          }
        ]
      }
    },
    "params": [
      {
        "paramName": "since_hours",
        "value": "24",
        "label": "Hours",
        "type": "text",
        "show": true,
        "description": "Look back window in hours"
      }
    ],
    "refetchInterval": 300000,
    "staleTime": 60000
  }
}
```

---

## 5) apps.json Specification

```json
{
  "ofac_scanner_dashboard": {
    "name": "OFAC Scanner Dashboard",
    "description": "Venezuela sanctions monitoring and CVX thesis validation",
    "version": "1.0.0",
    "img": "",
    "allowCustomization": true,
    "tabs": {
      "layout": [
        {
          "i": "ofac_status_1",
          "x": 0,
          "y": 0,
          "w": 8,
          "h": 4
        },
        {
          "i": "ofac_diff_1",
          "x": 8,
          "y": 0,
          "w": 20,
          "h": 8
        },
        {
          "i": "ofac_venezuela_events_1",
          "x": 0,
          "y": 4,
          "w": 28,
          "h": 12
        }
      ],
      "widgetsState": {
        "ofac_status_1": {
          "widgetId": "ofac_status"
        },
        "ofac_diff_1": {
          "widgetId": "ofac_diff",
          "params": {
            "since_hours": "24"
          }
        },
        "ofac_venezuela_events_1": {
          "widgetId": "ofac_venezuela_events",
          "params": {
            "limit": "50",
            "chevron_only": "false"
          }
        }
      }
    }
  }
}
```

---

## 6) Poller & Diff Algorithm

### Polling Strategy

Since OFAC **retired the RSS feed** (Jan 31, 2025), we poll HTML pages directly.

#### Pages to Poll

| Page | URL | Priority |
|------|-----|----------|
| Recent Actions | `https://ofac.treasury.gov/recent-actions` | Primary |
| Venezuela-related | `https://ofac.treasury.gov/sanctions-programs-and-country-information/venezuela-related-sanctions` | Secondary |
| General Licenses | `https://ofac.treasury.gov/recent-actions?...` (filtered) | Secondary |

---

### Polling Flow

```python
async def poll_ofac():
    """Main polling job - runs every 15 minutes."""
    poll_run = await create_poll_run()
    
    try:
        # 1. Fetch pages with exponential backoff
        pages = await fetch_with_retry(OFAC_URLS, max_retries=3)
        
        # 2. Store raw snapshots for audit
        for url, html in pages.items():
            await store_snapshot(poll_run.id, url, html)
        
        # 3. Extract events from HTML
        events = extract_events(pages)
        
        # 4. Compute hashes for idempotency
        for event in events:
            event.event_hash = compute_hash(event.title, event.url, event.published_date)
        
        # 5. Diff against existing events (upsert)
        new_events = await upsert_events(poll_run.id, events)
        
        # 6. Tag Venezuela/Chevron-related
        for event in new_events:
            event.is_venezuela_related = matches_venezuela_keywords(event)
            event.is_chevron_related = matches_chevron_keywords(event)
            await update_event(event)
        
        # 7. Trigger alerts for new Venezuela events
        for event in new_events:
            if event.is_venezuela_related:
                await trigger_alert(event, "venezuela_new")
            if event.is_chevron_related:
                await trigger_alert(event, "policy_pistol")
        
        # 8. Mark poll complete
        await complete_poll_run(poll_run.id, len(new_events))
        
    except Exception as e:
        await fail_poll_run(poll_run.id, str(e))
        raise
```

---

### Event Extraction

```python
from bs4 import BeautifulSoup
import hashlib

def extract_events(pages: dict[str, str]) -> list[OFACEvent]:
    """Parse OFAC Recent Actions page HTML."""
    events = []
    
    html = pages.get("https://ofac.treasury.gov/recent-actions", "")
    soup = BeautifulSoup(html, "html.parser")
    
    # OFAC Recent Actions are rendered as links in a list
    # Structure observed: <a href="/recent-actions/YYYYMMDD">Title</a>
    for link in soup.select("a[href^='/recent-actions/']"):
        href = link.get("href", "")
        title = link.get_text(strip=True)
        
        # Skip navigation/category links
        if not title or title in ["Sanctions List Updates", "Next", "Regulations and Guidance"]:
            continue
        
        # Extract date from URL pattern /recent-actions/YYYYMMDD
        date_match = re.search(r"/recent-actions/(\d{8})", href)
        published_date = None
        if date_match:
            try:
                published_date = datetime.strptime(date_match.group(1), "%Y%m%d").date()
            except ValueError:
                pass
        
        events.append(OFACEvent(
            title=title,
            url=f"https://ofac.treasury.gov{href}",
            published_date=published_date,
            category=detect_category(title)
        ))
    
    return events


def compute_hash(title: str, url: str, date: Optional[date]) -> str:
    """Stable idempotency key."""
    date_str = date.isoformat() if date else "unknown"
    content = f"{title}|{url}|{date_str}"
    return hashlib.sha256(content.encode()).hexdigest()
```

---

### Keyword Matching

```python
VENEZUELA_KEYWORDS = [
    "venezuela",
    "venezuelan",
    "maduro",
    "pdvsa",
    "citgo",
    "petroleo",
]

CHEVRON_KEYWORDS = [
    "chevron",
    "cvx",
    "oil license",
    "petroleum authorization",
]

def matches_venezuela_keywords(event: OFACEvent) -> bool:
    text = f"{event.title} {event.category or ''}".lower()
    return any(kw in text for kw in VENEZUELA_KEYWORDS)


def matches_chevron_keywords(event: OFACEvent) -> bool:
    text = f"{event.title} {event.category or ''}".lower()
    return any(kw in text for kw in CHEVRON_KEYWORDS)
```

---

### Backoff Strategy

```python
import asyncio
import random

async def fetch_with_retry(urls: list[str], max_retries: int = 3) -> dict[str, str]:
    results = {}
    
    for url in urls:
        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.get(url, timeout=30)
                    resp.raise_for_status()
                    results[url] = resp.text
                    break
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                # Exponential backoff with jitter
                delay = (2 ** attempt) + random.uniform(0, 1)
                await asyncio.sleep(delay)
    
    return results
```

---

## 7) Alert Rules ("Policy Pistol")

### Alert Types

| Alert Type | Trigger Condition | Confidence | Action |
|------------|-------------------|------------|--------|
| `venezuela_new` | Any new Venezuela-related event | Medium | Log + surface in Diff widget |
| `venezuela_gl` | New General License mentioning Venezuela | High | Log + push notification |
| `policy_pistol` | Chevron-related term detected | **Critical** | Log + push + flag for review |
| `possible_private` | Price moved but no OFAC diff | Low | Log with news attribution |

---

### Confidence Scoring

```python
def compute_confidence(event: OFACEvent) -> float:
    """
    Score 0.0 - 1.0 based on signal strength.
    """
    score = 0.0
    
    # Base: Venezuela mention
    if event.is_venezuela_related:
        score += 0.3
    
    # Boost: General License in title
    if "general license" in event.title.lower():
        score += 0.3
    
    # Boost: Chevron mention
    if event.is_chevron_related:
        score += 0.3
    
    # Boost: Recent date (within 7 days)
    if event.published_date:
        days_old = (date.today() - event.published_date).days
        if days_old <= 7:
            score += 0.1
    
    return min(score, 1.0)
```

---

### Alert Trigger

```python
async def trigger_alert(event: OFACEvent, alert_type: str):
    confidence = compute_confidence(event)
    
    await db.insert_alert(
        event_id=event.id,
        alert_type=alert_type,
        confidence_score=confidence,
        rule_matched=f"keywords: {event.keywords_matched}"
    )
    
    # Critical alerts get push notification (future: webhook)
    if alert_type == "policy_pistol":
        logger.critical(f"🔴 POLICY PISTOL: {event.title}")
```

---

## 8) Deployment

### Docker Compose

```yaml
version: "3.9"

services:
  ofac-scanner:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://ofac:ofac@db:5432/ofac
      - OFAC_API_KEY=${OFAC_API_KEY}
      - CORS_ORIGINS=https://pro.openbb.co
      - POLL_INTERVAL_MINUTES=15
    depends_on:
      - db
    restart: unless-stopped

  db:
    image: postgres:16
    environment:
      - POSTGRES_USER=ofac
      - POSTGRES_PASSWORD=ofac
      - POSTGRES_DB=ofac
    volumes:
      - pgdata:/var/lib/postgresql/data
    ports:
      - "5432:5432"

volumes:
  pgdata:
```

---

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | Yes | - | PostgreSQL connection string |
| `OFAC_API_KEY` | No | - | API key for auth (dev mode if unset) |
| `CORS_ORIGINS` | No | `https://pro.openbb.co` | Comma-separated allowed origins |
| `POLL_INTERVAL_MINUTES` | No | `15` | Polling frequency |
| `LOG_LEVEL` | No | `INFO` | Logging level |

---

### Connecting to OpenBB Workspace

1. Start the service: `docker-compose up -d`
2. In Workspace: **Apps** → **Connect backend**
3. URL: `http://localhost:8000` (or ngrok URL for remote)
4. Add header: `X-API-KEY: <your-key>`
5. Test connection
6. Add widgets from "OFAC Scanner" category

---

## Next Steps

- [ ] Implement FastAPI service skeleton
- [ ] Set up PostgreSQL with Alembic migrations
- [ ] Add APScheduler for polling
- [ ] Create `widgets.json` and `apps.json` files
- [ ] Test integration with OpenBB Workspace
- [ ] Add webhook/push notifications for critical alerts

---

## References

| Resource | URL |
|----------|-----|
| OpenBB Data Integration | https://docs.openbb.co/workspace/developers/data-integration |
| widgets.json Reference | https://docs.openbb.co/workspace/developers/json-specs/widgets-json-reference |
| Backend Examples | https://github.com/OpenBB-finance/backend-examples-for-openbb-workspace |
| OFAC Recent Actions | https://ofac.treasury.gov/recent-actions |
| OFAC Venezuela Sanctions | https://ofac.treasury.gov/sanctions-programs-and-country-information/venezuela-related-sanctions |

---

*Document version: 1.0*  
*Created: 2026-01-05*  
*Status: Ready for implementation*
