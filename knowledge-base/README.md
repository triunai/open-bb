# 📚 OpenBB Knowledge Base

> **Documentation homebase for all OpenBB-related specs, guides, and architecture decisions.**

---

## Directory Structure

```
knowledge-base/
├── README.md                    # This file - index of all docs
├── specs/                       # Functional & technical specifications
│   └── openbb-workspace-spec.md # Main build spec for Workspace + OFAC integration
├── guides/                      # How-to guides and tutorials
├── architecture/                # System design and architecture docs
└── reference/                   # Quick reference sheets and cheatsheets
```

---

## Quick Links

### Specifications
- **[OpenBB Workspace Build Spec](./specs/openbb-workspace-spec.md)** - Complete short/medium/long-term build spec for OpenBB Workspace with OFAC scanner integration
- **[Spec Audit Record](./specs/spec-audit-record.md)** - Validation record: what was confirmed correct, corrected, and added
- **[OFAC Scanner Technical Spec](./specs/ofac-scanner-technical-spec.md)** - 🔧 Implementation guide: architecture, DB schema, API endpoints, widgets.json, poller algorithm

### Architecture
- **[Stack Decision Record](./architecture/stack-decision.md)** - ADR: Why Workspace + FastAPI over Streamlit for cornerstone system

---

## Purpose

This knowledge base serves as the single source of truth for:

1. **Build Specifications** - What we're building and why
2. **Architecture Decisions** - How components fit together
3. **Integration Guides** - Connecting external systems (OFAC scanner, custom backends)
4. **Reference Material** - Quick lookups for common patterns and configs

---

*Last updated: 2026-01-05*
