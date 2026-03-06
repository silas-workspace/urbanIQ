# urbanIQ Berlin

**Intelligent Geodata Aggregation System for Automated District Analysis in Berlin**

[![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Code style: Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

## 🏙️ Project Overview

urbanIQ Berlin is an intelligent geodata aggregation system that enables automated district analysis in Berlin through natural language input and LLM-based metadata aggregation. The system transforms complex geodata requests into professional data packages with comprehensive documentation.

### Key Features

- **Natural Language Interface**: Users can request geodata using plain German text
- **Multi-Source Integration**: Automated data retrieval from Berlin Geoportal WFS and OpenStreetMap
- **Intelligent Processing**: Automatic spatial filtering, CRS transformation, and data harmonization
- **Smart Metadata Generation**: LLM-powered metadata reports for data quality and usage guidance
- **Package Export**: ZIP packages with harmonized geodata and comprehensive documentation

### Target Users

- Urban planners and city administration
- GIS analysts and researchers
- Students and academics in urban studies
- Data scientists working with spatial data

## 🏗️ System Architecture

The system consists of four core services:

1. **NLP Service**: OpenAI GPT-based natural language processing for user request parsing
2. **Data Service**: Orchestrates geodata acquisition from multiple sources
3. **Processing Service**: Harmonizes geodata (CRS standardization, spatial clipping, schema normalization)
4. **Metadata Service**: Generates professional metadata reports using LLM analysis

### Technical Stack

- **Backend**: FastAPI with async/await patterns
- **Database**: SQLite with SQLModel ORM
- **Geodata Processing**: GeoPandas, Shapely, Fiona, GDAL
- **LLM Integration**: LangChain with OpenAI GPT-4
- **Frontend**: HTMX with Tailwind CSS
- **Package Management**: UV (ultra-fast Python package manager)

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- [UV package manager](https://github.com/astral-sh/uv) installed
- OpenAI API key for LLM services

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/SilasPignotti/urbanIQ.git
   cd urbanIQ
   ```

2. **Set up the environment**
   ```bash
   # Install UV if not already installed
   curl -LsSf https://astral.sh/uv/install.sh | sh

   # Create virtual environment and install dependencies
   uv sync
   ```

3. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env and add your OpenAI API key:
   # OPENAI_API_KEY=sk-your-openai-api-key-here
   ```

4. **Initialize the database**
   ```bash
   uv run python -c "from app.database import init_database; init_database()"
   ```

5. **Start the development server**
   ```bash
   uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

6. **Access the application**
   - Web interface: http://localhost:8000
   - API documentation: http://localhost:8000/docs
   - Interactive API: http://localhost:8000/redoc

## 📖 Usage Examples

### Web Interface

Navigate to http://localhost:8000 and enter natural language requests:

- "Pankow Gebäude und ÖPNV-Haltestellen"
- "Mitte buildings and transport stops"
- "Charlottenburg-Wilmersdorf Gebäudedaten für Stadtplanung"

### API Usage

```python
import httpx

# Submit a geodata request
async with httpx.AsyncClient() as client:
    response = await client.post(
        "http://localhost:8000/api/chat/message",
        data={"text": "Pankow Gebäude und ÖPNV-Haltestellen"}
    )
    job_data = response.json()
    job_id = job_data["job_id"]

    # Check job status
    status_response = await client.get(f"http://localhost:8000/api/jobs/status/{job_id}")
    print(status_response.json())
```

### Available Datasets

- **bezirksgrenzen**: Administrative district boundaries (always included)
- **gebaeude**: Building footprints and usage data from Berlin Geoportal
- **oepnv_haltestellen**: Public transport stops from OpenStreetMap

## 🧪 Development

### Testing

```bash
# Run all tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=app --cov-report=html

# Run specific test categories
uv run pytest -m "unit"  # Unit tests only
uv run pytest -m "integration"  # Integration tests
uv run pytest -m "external"  # External API tests (requires real API key)
```

### Code Quality

```bash
# Run lint, typecheck, and test sessions
uv run nox

# Run individual sessions
uv run nox -s lint
uv run nox -s typecheck
uv run nox -s test
```

### Project Structure

```
urbaniq/
├── app/                    # Main application package
│   ├── main.py            # FastAPI application entry point
│   ├── config.py          # Settings and environment management
│   ├── database.py        # Database setup and session management
│   ├── models/            # SQLModel database models
│   │   ├── job.py         # Job management models
│   │   ├── package.py     # Download package models
│   │   └── data_source.py # Data source registry models
│   ├── api/               # FastAPI routers and endpoints
│   │   ├── chat.py        # Natural language interface
│   │   ├── jobs.py        # Job status endpoints
│   │   ├── packages.py    # Download management
│   │   └── frontend.py    # Web interface routes
│   ├── services/          # Business logic layer
│   │   ├── nlp_service.py     # OpenAI-based text analysis
│   │   ├── data_service.py    # Geodata acquisition orchestration
│   │   ├── processing_service.py  # Data harmonization
│   │   ├── metadata_service.py    # LLM-based metadata generation
│   │   └── export_service.py     # ZIP package creation
│   ├── connectors/        # External API abstractions
│   │   ├── base.py        # Abstract base connector
│   │   ├── geoportal.py   # Berlin WFS/WMS client
│   │   └── osm.py         # OpenStreetMap Overpass API
│   └── frontend/          # Web interface assets
│       ├── templates/     # Jinja2 HTML templates
│       └── static/        # CSS, JavaScript, images
├── tests/                 # Comprehensive test suite
├── data/                  # Runtime data directories
│   ├── temp/             # Temporary processing files
│   ├── exports/          # Generated ZIP packages
│   └── cache/            # API response cache
├── pyproject.toml        # Project configuration and dependencies
├── .env.example          # Environment variables template
└── README.md             # This file
```

## 🔧 Configuration

### Environment Variables

Key configuration options in `.env`:

```bash
# Application
APP_NAME=urbaniq
APP_VERSION=0.1.0
ENVIRONMENT=development

# Database
DATABASE_URL=sqlite:///./data/urbaniq.db

# OpenAI Integration
OPENAI_API_KEY=sk-your-api-key-here

# Directories
TEMP_DIR=./data/temp
EXPORT_DIR=./data/exports
CACHE_DIR=./data/cache

# Server
HOST=127.0.0.1
PORT=8000
DEBUG=true

# Logging
LOG_LEVEL=INFO
```

### Advanced Configuration

The system uses Pydantic Settings for type-safe configuration management. See `app/config.py` for all available options.

## 📊 Data Sources

### Berlin Geoportal

- **Source**: Berlin Senate Department for Urban Development and Housing
- **License**: CC BY 3.0 DE
- **Update Frequency**: Monthly to quarterly
- **Coverage**: Complete Berlin administrative area

### OpenStreetMap

- **Source**: OpenStreetMap Contributors
- **License**: Open Database License (ODbL)
- **Update Frequency**: Real-time community updates
- **Coverage**: Global, high detail for Berlin

## 🔒 Security & Privacy

- API keys are handled securely through environment variables
- No personal data is stored or processed
- All requests are logged with correlation IDs for debugging
- Rate limiting and timeout protection for external APIs
- Input validation and sanitization for all user inputs

## 🚀 Deployment

### Production Deployment

1. **Environment Setup**
   ```bash
   export ENVIRONMENT=production
   export DATABASE_URL=postgresql://user:pass@localhost/urbaniq
   export OPENAI_API_KEY=your-production-key
   ```

2. **Install Production Dependencies**
   ```bash
   uv sync --group production
   ```

3. **Database Migration**
   ```bash
   uv run alembic upgrade head
   ```

4. **Start Production Server**
   ```bash
   uv run gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
   ```

### Docker Deployment

```dockerfile
FROM python:3.11-slim

# Install UV
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Copy project
COPY . /app
WORKDIR /app

# Install dependencies
RUN uv sync --frozen

# Run application
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 📚 Background

This project was built during a university GIS and urban data engineering course. It serves as a compact end-to-end example of:

- FastAPI backend development with SQLModel and Alembic
- Geospatial processing with GeoPandas, Shapely, Fiona, and GDAL
- Connector-based acquisition from Berlin Geoportal and OpenStreetMap
- Natural language request parsing with OpenAI models
- HTMX-based frontend delivery without a heavy JavaScript stack

## 📘 Further Documentation

If you want to go deeper than the project overview, these are the best files to open first:

- `doc/README.md` — quick index of what is still useful vs archived
- `doc/DATABASE_SCHEMA.md` — job, package, and data source storage model
- `doc/CONNECTOR_SPECIFICATIONS.md` — Berlin Geoportal and Overpass connector notes
- `doc/FRONTEND_IMPLEMENTATION.md` — HTMX/Jinja frontend structure and rendering approach

The rest of `doc/` is preserved mainly as development history and may reflect earlier Gemini-era assumptions.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Berlin Senate Department for Urban Development** for providing open geodata
- **OpenStreetMap Contributors** for comprehensive spatial data
- **OpenAI** for GPT API access enabling intelligent text processing
- **FastAPI Community** for excellent framework and documentation
- **GeoPandas Team** for powerful geospatial data processing tools

---

**urbanIQ Berlin** - Transforming urban planning through intelligent geodata aggregation