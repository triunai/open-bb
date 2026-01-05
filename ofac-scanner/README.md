# OFAC Scanner Service

> Venezuela sanctions monitoring for OpenBB Workspace integration.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## Overview

This service monitors OFAC (Office of Foreign Assets Control) for Venezuela-related sanctions updates and integrates with OpenBB Workspace as a custom backend.

### Features

- 🔍 **Automated Polling**: Scrapes OFAC Recent Actions every 15 minutes
- 🇻🇪 **Venezuela Filtering**: Automatically tags Venezuela-related events
- ⛽ **Chevron Detection**: Highlights events mentioning Chevron/CVX
- 🚨 **Alert System**: Policy Pistol alerts for critical events
- 📊 **OpenBB Integration**: Pre-built widgets for Workspace dashboards

---

## Architecture

This project follows **Clean Architecture** principles:

```
src/ofac_scanner/
├── domain/           # Entities, value objects, exceptions
├── application/      # Use cases, interfaces, services
├── infrastructure/   # Database, scrapers, scheduler
└── presentation/     # FastAPI routes, OpenBB widgets
```

---

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 14+
- Docker (optional)

### Option 1: Docker Compose (Recommended)

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f api

# Access the API
curl http://localhost:8000/health
```

### Option 2: Local Development

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Install dependencies
pip install -e ".[dev]"

# Copy environment file
cp .env.example .env

# Start PostgreSQL (or use Docker)
docker-compose up -d db

# Run database migrations
alembic upgrade head

# Start the server
python -m ofac_scanner.main
```

---

## Configuration

All configuration is done via environment variables. See `.env.example` for all options.

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://...` | PostgreSQL connection string |
| `OFAC_API_KEY` | `None` | API key for auth (dev mode if empty) |
| `CORS_ORIGINS` | `https://pro.openbb.co` | Allowed CORS origins |
| `POLL_INTERVAL_MINUTES` | `15` | Polling frequency |
| `ENABLE_SCHEDULER` | `true` | Enable background polling |

---

## API Endpoints

### Health & Info

| Endpoint | Description |
|----------|-------------|
| `GET /` | Service info |
| `GET /health` | Health check with scheduler status |

### OFAC Data (requires API key in prod)

| Endpoint | Description |
|----------|-------------|
| `GET /ofac/latest` | Most recent OFAC events |
| `GET /ofac/venezuela` | Venezuela-related events |
| `GET /ofac/diff` | Events detected in last N hours |
| `GET /ofac/status` | Markdown-formatted status |
| `POST /ofac/poll` | Trigger immediate poll |

### OpenBB Integration

| Endpoint | Description |
|----------|-------------|
| `GET /widgets.json` | Widget definitions |
| `GET /apps.json` | App layouts |

---

## OpenBB Workspace Integration

### Connect Your Backend

1. Start the OFAC Scanner service
2. In OpenBB Workspace: **Apps** → **Connect backend**
3. Enter URL: `http://localhost:8000`
4. Add header `X-API-KEY: <your-key>` (if configured)
5. Click **Test** → **Add**

### Available Widgets

- **OFAC Venezuela Events**: Table of Venezuela-related actions
- **OFAC Scanner Status**: Markdown status widget
- **OFAC Changes (24h)**: Recent changes table
- **OFAC Latest Events**: All recent events

### Pre-built Apps

- **OFAC Scanner Dashboard**: Venezuela-focused view
- **OFAC Monitoring**: Full event monitoring

---

## Development

### Running Tests

```bash
# Run all tests
pytest

# With coverage
pytest --cov=ofac_scanner

# Run specific test file
pytest tests/unit/test_keyword_matcher.py
```

### Code Quality

```bash
# Format code
ruff format src tests

# Lint
ruff check src tests

# Type check
mypy src
```

### Database Migrations

```bash
# Create a new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback one step
alembic downgrade -1
```

---

## Project Structure

```
ofac-scanner/
├── pyproject.toml          # Python packaging
├── docker-compose.yml      # Docker services
├── Dockerfile              # Production image
├── alembic.ini             # Migration config
├── alembic/                # Migration scripts
│   ├── env.py
│   └── versions/
├── src/
│   └── ofac_scanner/
│       ├── __init__.py
│       ├── main.py         # Entry point
│       ├── config.py       # Settings
│       ├── domain/         # Domain layer
│       │   ├── entities/
│       │   ├── value_objects/
│       │   └── exceptions.py
│       ├── application/    # Application layer
│       │   ├── interfaces/
│       │   └── services/
│       ├── infrastructure/ # Infrastructure layer
│       │   ├── database/
│       │   ├── scrapers/
│       │   └── scheduler/
│       └── presentation/   # Presentation layer
│           ├── api/
│           │   └── routes/
│           └── openbb/
│               ├── widgets.json
│               └── apps.json
└── tests/
    ├── unit/
    └── integration/
```

---

## OFAC Data Sources

Since OFAC retired their RSS feed (January 31, 2025), this service scrapes:

- [OFAC Recent Actions](https://ofac.treasury.gov/recent-actions)
- Venezuela-related sanctions pages

### Important Limitation

Not all authorizations appear publicly. If markets move but no OFAC page changes are detected, it may indicate a private/specific authorization.

---

## License

MIT License - see LICENSE file for details.

---

## References

- [OpenBB Workspace Docs](https://docs.openbb.co/workspace)
- [OpenBB Data Integration](https://docs.openbb.co/workspace/developers/data-integration)
- [OFAC Recent Actions](https://ofac.treasury.gov/recent-actions)
- [widgets.json Reference](https://docs.openbb.co/workspace/developers/json-specs/widgets-json-reference)
