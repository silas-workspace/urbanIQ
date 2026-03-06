> ⚠️ **Archived** — This document was written during initial development and
> references the Gemini API or earlier MVP assumptions. The system now uses OpenAI.
> Use the root `README.md` for setup and `doc/README.md` for document status.

# Deployment Configuration

This document defines deployment strategies and configuration for urbanIQ Berlin geodata aggregation system.

## Environment Configuration

### Environment Variables

**Core Application Settings**:

```bash
# Database Configuration
DATABASE_URL=sqlite:///./geodaten_assistent.db

# External API Keys
GOOGLE_API_KEY=your-gemini-api-key-here

# Logging Configuration
LOG_LEVEL=INFO

# File Storage Paths
TEMP_DIR=./data/temp
EXPORT_DIR=./data/exports
CACHE_DIR=./data/cache
```

**Production-Specific Settings**:

```bash
# Security
SECRET_KEY=your-secret-key-for-sessions

# CORS Configuration
CORS_ORIGINS=["https://yourdomain.com"]

# Resource Limits
MAX_EXPORT_SIZE_MB=100
CLEANUP_INTERVAL_HOURS=24

# Performance Tuning
WORKER_CONNECTIONS=1000
WORKER_TIMEOUT=120
```

## Docker Configuration

### Dockerfile

Multi-stage build optimized for Python geodata processing:

```dockerfile
FROM python:3.11-slim as base

# System dependencies for GeoPandas
RUN apt-get update && apt-get install -y \
    gdal-bin \
    libgdal-dev \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install uv package manager
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

# Dependencies installation stage
FROM base as deps
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-cache

# Application stage
FROM deps as app
COPY . .

# Security: non-root user
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app
USER app

# Data directories
RUN mkdir -p data/{temp,cache,exports}

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose

Development and production orchestration:

```yaml
version: "3.8"

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=sqlite:///./data/production.db
      - GOOGLE_API_KEY=${GOOGLE_API_KEY}
      - LOG_LEVEL=INFO
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    restart: unless-stopped
    depends_on:
      - nginx

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - app
    restart: unless-stopped

  # Optional: PostgreSQL for production scaling
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: urbaniq
      POSTGRES_USER: urbaniq
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

volumes:
  postgres_data:
```

## CI/CD Pipeline

### GitHub Actions Workflow

```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v2
        with:
          version: "0.4.18"

      - name: Set up Python
        run: uv python install 3.11

      - name: Install dependencies
        run: uv sync --all-extras

      - name: Install system dependencies for GeoPandas
        run: |
          sudo apt-get update
          sudo apt-get install -y gdal-bin libgdal-dev

      - name: Run linting
        run: |
          uv run ruff check .
          uv run ruff format --check .

      - name: Run type checking
        run: uv run mypy app/

      - name: Run unit tests
        run: uv run pytest tests/ -v --cov=app --cov-report=xml

      - name: Run integration tests
        run: uv run pytest tests/test_connectors/ tests/test_services/ -v
        env:
          INTEGRATION_TESTS: true

      - name: Upload coverage reports
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml

  build:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'

    steps:
      - uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v2

      - name: Login to Container Registry
        uses: docker/login-action@v2
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Build and push Docker image
        uses: docker/build-push-action@v4
        with:
          context: .
          push: true
          tags: ghcr.io/${{ github.repository }}:latest
          cache-from: type=gha
          cache-to: type=gha,mode=max

  deploy:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'

    steps:
      - name: Deploy to production
        run: |
          # Deployment script for your infrastructure
          echo "Deploying to production..."
```

## Production Nginx Configuration

### nginx.conf

```nginx
events {
    worker_connections 1024;
}

http {
    upstream app {
        server app:8000;
    }

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;

    server {
        listen 80;
        server_name yourdomain.com;

        # Redirect HTTP to HTTPS
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name yourdomain.com;

        # SSL Configuration
        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers HIGH:!aNULL:!MD5;

        # Security headers
        add_header X-Frame-Options DENY;
        add_header X-Content-Type-Options nosniff;
        add_header X-XSS-Protection "1; mode=block";

        # API proxy
        location /api/ {
            limit_req zone=api burst=20 nodelay;
            proxy_pass http://app;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Static files
        location / {
            proxy_pass http://app;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Large file downloads
        location /api/downloads/ {
            proxy_pass http://app;
            proxy_buffering off;
            proxy_request_buffering off;
            proxy_max_temp_file_size 0;
        }
    }
}
```

## Monitoring and Logging

### Application Logging

**Structured JSON logging**:

```python
import structlog

logger = structlog.get_logger("urbaniq")

# Example usage
logger.info(
    "Geodata request processed",
    job_id=job.id,
    bezirk=bezirk,
    categories=categories,
    processing_time_ms=elapsed_ms
)
```

### Health Monitoring

**Health check endpoint** (`/health`):

```json
{
  "status": "healthy",
  "timestamp": "2025-01-15T10:30:00Z",
  "services": {
    "database": "ok",
    "gemini_api": "ok",
    "geoportal_wfs": "ok",
    "osm_overpass": "ok"
  },
  "system": {
    "cpu_usage": "15%",
    "memory_usage": "512MB",
    "disk_usage": "2.1GB"
  }
}
```

## Scaling Considerations

### Horizontal Scaling

- **Load Balancer**: Multiple FastAPI instances behind nginx
- **Database**: PostgreSQL with connection pooling
- **File Storage**: Shared filesystem or object storage (S3)
- **Caching**: Redis for API response caching

### Performance Optimization

- **Async Processing**: Background job queue (Celery/RQ)
- **Database Indexing**: Optimized queries for job status polling
- **CDN**: Static asset delivery optimization
- **Compression**: Gzip encoding for API responses

## Security

### Application Security

- **Input Validation**: Pydantic model validation
- **SQL Injection**: SQLModel ORM protection
- **CORS**: Restricted origins in production
- **Rate Limiting**: API endpoint protection

### Infrastructure Security

- **SSL/TLS**: HTTPS encryption for all traffic
- **Firewall**: Restricted port access
- **Container Security**: Minimal base images, non-root user
- **Secrets management**: Environment variable injection
