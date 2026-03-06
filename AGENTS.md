# AGENTS.md — urbanIQ

## Project Purpose

NLP-driven geodata aggregation platform for Berlin urban planning. Users submit natural language
requests (German or English) → OpenAI GPT parses district + dataset intent → connectors fetch
data from Berlin Geoportal WFS and OpenStreetMap → processing harmonizes CRS/schema → ZIP packages
with GeoJSON/Shapefile exports and LLM-generated metadata reports.

FastAPI backend, SQLite (Alembic migrations), HTMX/Tailwind frontend.

## Directory Structure

```
urbanIQ/
├── app/
│   ├── main.py             # App factory, middleware, lifespan
│   ├── config.py           # Pydantic Settings, env var validation
│   ├── database.py         # SQLite engine, session management
│   ├── api/                # FastAPI routers
│   │   ├── chat.py         # POST /api/chat/message
│   │   ├── chat_background.py  # Async job orchestration
│   │   ├── jobs.py         # Job status endpoints
│   │   ├── packages.py     # Download management
│   │   ├── data_sources.py # Data source registry
│   │   ├── frontend.py     # Web interface routes
│   │   ├── health.py       # GET /api/health
│   │   └── deps.py         # FastAPI dependencies
│   ├── connectors/         # External API clients
│   │   ├── base.py         # Abstract base with retry/error handling
│   │   ├── geoportal.py    # Berlin WFS: buildings, district boundaries
│   │   ├── geoportal_extended.py   # Berlin WFS: cycling, streets, Ortsteile
│   │   ├── geoportal_extended2.py  # Berlin WFS: population density, floors
│   │   └── osm.py          # OpenStreetMap Overpass API
│   ├── models/             # SQLModel ORM models
│   │   ├── job.py          # Job lifecycle and status
│   │   ├── package.py      # Download package management
│   │   └── data_source.py  # Data source registry
│   ├── services/           # Business logic
│   │   ├── nlp_service.py      # LangChain + GPT-4o-mini request parsing
│   │   ├── data_service.py     # Parallel connector orchestration
│   │   ├── processing_service.py # CRS standardization, spatial clipping
│   │   ├── metadata_service.py   # LLM metadata report generation
│   │   └── export_service.py     # ZIP package creation
│   ├── utils/              # Empty placeholder module
│   └── frontend/           # Static assets and Jinja2 templates
├── alembic/                # Database migration scripts
├── tests/                  # pytest test suite
│   ├── conftest.py         # Fixtures (temp DB, session override)
│   ├── test_config.py      # Settings validation tests
│   ├── test_database.py    # DB connection/session tests
│   ├── test_health.py      # Health endpoint tests
│   └── test_models/        # SQLModel model unit tests
├── doc/                    # Archived dev documentation
│   └── README.md           # Notes that doc/ contains outdated Gemini/GH secrets refs
├── data/                   # Runtime data (gitignored except .gitkeep)
├── .github/workflows/ci.yml  # GitHub Actions CI
├── pyproject.toml          # Project config: uv, ruff, mypy, pytest
├── uv.lock                 # Locked dependencies
└── CLAUDE.md               # Legacy Claude Code agent file (candidate for removal)
```

## Key Conventions

- **Async**: All connector methods and most service methods are `async`. Background tasks use
  `asyncio.run()` wrapper (`process_geodata_request_sync`).
- **Logging**: `structlog` for API/export layers, `logging` stdlib for services/connectors.
  Logger names follow `urbaniq.<module>` pattern.
- **Error handling**: Custom exception hierarchy in `connectors/base.py`
  (`ConnectorError` → `ServiceUnavailableError`, `InvalidParameterError`, `RateLimitError`).
- **Config**: Single `settings` singleton from `app.config`. API key via `SecretStr`.
- **ORM**: SQLModel (SQLAlchemy + Pydantic). Models in `app/models/`, imported via
  `app/models/__init__.py`.
- **Type hints**: Full coverage. mypy in strict mode. Two `# type: ignore[arg-type]` suppressions
  for LangChain's `openai_api_key` parameter.
- **Tests**: pytest with class-based test organization (`Test*` classes). No external API calls
  in CI tests — mocked via `unittest.mock.patch`.
- **Tooling**: uv (package manager), ruff (lint + format), mypy (type checking). No nox yet.

## Constraints for This Polish Pass

- No logic or algorithm changes
- No directory restructuring or file renames
- No runtime dependency additions or removals
- No error handling changes
- Code must function identically after polish
- English for all code, comments, docs, commits

For global coding standards, see ~/.pi/agent/AGENTS.md
