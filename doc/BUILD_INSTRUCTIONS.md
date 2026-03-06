> ⚠️ **Archived** — This document was written during initial development and
> references the Gemini API. The system now uses OpenAI. See root `README.md`
> for current setup instructions.

# Build Instructions

This document provides step-by-step instructions for building and running the urbanIQ Berlin geodata aggregation system.

## Prerequisites

### System Requirements

- **Python**: 3.11 or higher
- **UV Package Manager**: Latest version (0.4.18+)
- **System Dependencies**: GDAL library for geodata processing
- **API Keys**: Google Gemini API key for NLP processing

### System Dependencies Installation

**macOS**:

```bash
# Install GDAL using Homebrew
brew install gdal

# Or using MacPorts
sudo port install gdal
```

**Ubuntu/Debian**:

```bash
sudo apt-get update
sudo apt-get install gdal-bin libgdal-dev gcc g++
```

**Windows**:

```bash
# Using conda
conda install -c conda-forge gdal

# Or download OSGeo4W installer
# https://trac.osgeo.org/osgeo4w/
```

## Project Setup

### 1. Clone and Initialize

```bash
# Clone repository
git clone <repository-url>
cd urbanIQ

# Install UV package manager
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment
uv venv

# Activate environment (optional, uv run handles this)
source .venv/bin/activate  # macOS/Linux
# or
.venv\Scripts\activate     # Windows
```

### 2. Install Dependencies

```bash
# Install all dependencies (including dev dependencies)
uv sync --all-extras

# Or install only production dependencies
uv sync
```

### 3. Environment Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env file with your configuration
nano .env
```

**Required Environment Variables**:

```bash
# Database Configuration
DATABASE_URL=sqlite:///./geodaten_assistent.db

# Google Gemini API Key (REQUIRED)
GOOGLE_API_KEY=your-gemini-api-key-here

# Logging Configuration
LOG_LEVEL=INFO

# File Storage Paths
TEMP_DIR=./data/temp
EXPORT_DIR=./data/exports
CACHE_DIR=./data/cache

# Production Settings (optional for development)
SECRET_KEY=your-secret-key-for-sessions
CORS_ORIGINS=["http://localhost:3000"]
MAX_EXPORT_SIZE_MB=100
CLEANUP_INTERVAL_HOURS=24
```

### 4. Database Setup

```bash
# Create data directories
mkdir -p data/{temp,cache,exports}

# Initialize database (run initial migrations)
uv run python scripts/setup.py

# Seed with initial data sources
uv run python scripts/seed_data.py
```

## Development Build

### 1. Run Development Server

```bash
# Start FastAPI development server with hot reload
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Server will be available at http://localhost:8000
# API documentation at http://localhost:8000/docs
```

### 2. Verify Installation

```bash
# Run health check
curl http://localhost:8000/health

# Expected response:
# {
#   "status": "healthy",
#   "timestamp": "2025-01-15T10:30:00Z",
#   "services": {
#     "database": "ok",
#     "gemini_api": "ok"
#   }
# }
```

### 3. Run Tests

```bash
# Run all tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=app --cov-report=html

# Run specific test categories
uv run pytest tests/test_api/           # API tests
uv run pytest tests/test_services/      # Service tests
uv run pytest tests/test_connectors/    # Integration tests
```

### 4. Code Quality Checks

```bash
# Format code
uv run ruff format .

# Check linting
uv run ruff check .

# Fix linting issues automatically
uv run ruff check --fix .

# Type checking
uv run mypy app/
```

## Production Build

### 1. Docker Build

```bash
# Build Docker image
docker build -t urbaniq:latest .

# Run container
docker run -d \
  --name urbaniq \
  -p 8000:8000 \
  -e GOOGLE_API_KEY=your-api-key \
  -v $(pwd)/data:/app/data \
  urbaniq:latest
```

### 2. Docker Compose

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### 3. Production Configuration

**Production Environment Variables**:

```bash
# Security
SECRET_KEY=your-production-secret-key

# Database (consider PostgreSQL for production)
DATABASE_URL=postgresql://user:password@localhost/urbaniq

# CORS (restrict to your domain)
CORS_ORIGINS=["https://yourdomain.com"]

# Performance
WORKER_CONNECTIONS=1000
WORKER_TIMEOUT=120

# Monitoring
LOG_LEVEL=INFO
```

## Key Components Build Order

### 1. Database Models

```bash
# Create database models first
uv run python -c "from app.models import *; print('Models loaded successfully')"
```

### 2. Services

```bash
# Test service initialization
uv run python -c "
from app.services.nlp_service import GeodataRequestParser
parser = GeodataRequestParser('test-key')
print('NLP Service initialized')
"
```

### 3. API Endpoints

```bash
# Test API routes
uv run python -c "
from app.main import app
print('FastAPI app routes:')
for route in app.routes:
    print(f'  {route.path}')
"
```

### 4. Frontend Templates

```bash
# Verify template loading
uv run python -c "
from app.frontend.templates import templates
print('Template engine initialized')
"
```

## Troubleshooting

### Common Issues

**GDAL Installation Problems**:

```bash
# Check GDAL installation
python -c "import gdal; print(gdal.__version__)"

# If failing, install system GDAL first, then:
uv pip install --force-reinstall --no-binary :all: GDAL
```

**Import Errors**:

```bash
# Verify Python path
uv run python -c "import sys; print('\n'.join(sys.path))"

# Check if in virtual environment
uv run which python
```

**Database Connection Issues**:

```bash
# Check database file permissions
ls -la geodaten_assistent.db

# Test database connection
uv run python -c "
from app.database import engine
from sqlmodel import text
with engine.connect() as conn:
    result = conn.execute(text('SELECT 1'))
    print('Database connection OK')
"
```

**API Key Issues**:

```bash
# Test Gemini API connection
uv run python -c "
import os
from langchain_google_genai import ChatGoogleGenerativeAI
llm = ChatGoogleGenerativeAI(
    model='gemini-1.5-pro',
    google_api_key=os.getenv('GOOGLE_API_KEY')
)
print('Gemini API connection OK')
"
```

### Performance Optimization

**Development**:

- Use `--reload` flag for hot reloading
- Set `LOG_LEVEL=DEBUG` for detailed logging
- Use smaller test datasets

**Production**:

- Set `LOG_LEVEL=INFO` to reduce log volume
- Configure proper worker count based on CPU cores
- Use PostgreSQL instead of SQLite for better concurrency
- Enable response compression
- Configure proper caching headers

## Build Verification

### Smoke Tests

```bash
# 1. Start the application
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 &

# 2. Wait for startup
sleep 5

# 3. Test health endpoint
curl -f http://localhost:8000/health || exit 1

# 4. Test chat endpoint
curl -X POST http://localhost:8000/api/chat/message \
  -H "Content-Type: application/json" \
  -d '{"text": "Pankow Verkehrsdaten"}' || exit 1

# 5. Check documentation
curl -f http://localhost:8000/docs || exit 1

echo "Build verification successful!"
```

### Continuous Integration

The project includes GitHub Actions CI/CD pipeline that:

1. Tests across multiple Python versions
2. Runs full test suite with coverage
3. Performs code quality checks
4. Builds Docker image
5. Deploys to production (on main branch)

See `.github/workflows/ci.yml` for complete CI configuration.
