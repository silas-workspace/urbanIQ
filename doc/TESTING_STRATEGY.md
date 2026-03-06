> ⚠️ **Archived** — This document was written during initial development and
> references the Gemini API. The system now uses OpenAI. See root `README.md`
> for current setup instructions.

# Testing Strategy

This document defines the comprehensive testing strategy for urbanIQ Berlin geodata aggregation system.

## Testing Philosophy

**Test-Driven Development**: Write tests before implementing features
**Test Pyramid**: Unit tests (70%) → Integration tests (20%) → E2E tests (10%)
**Async Testing**: Full async/await support for I/O-bound operations
**Mocking Strategy**: Mock external services, test internal logic

## Testing Framework

**Core Tools**:

- **pytest**: Primary testing framework with async support
- **pytest-asyncio**: Async test execution
- **httpx**: HTTP client for API testing
- **unittest.mock**: Mocking external dependencies

**Configuration** (pyproject.toml):

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"
python_classes = "Test*"
python_functions = "test_*"
asyncio_mode = "auto"
```

## Test Structure

### Test Organization

```
tests/
├── __init__.py
├── conftest.py              # Shared fixtures
├── test_api/               # API endpoint tests
│   ├── test_chat.py        # Chat interface tests
│   ├── test_jobs.py        # Job management tests
│   └── test_downloads.py   # Download endpoint tests
├── test_services/          # Business logic tests
│   ├── test_nlp_service.py     # NLP parsing tests
│   ├── test_data_service.py    # Data acquisition tests
│   ├── test_processing_service.py  # Data harmonization tests
│   └── test_metadata_service.py    # Metadata generation tests
├── test_connectors/        # External API integration tests
│   ├── test_geoportal.py   # Berlin WFS connector tests
│   └── test_osm.py         # OpenStreetMap connector tests
├── test_models/            # Database model tests
│   ├── test_job.py         # Job model tests
│   └── test_package.py     # Package model tests
└── test_utils/             # Utility function tests
    ├── test_geo_utils.py   # Geodata utility tests
    └── test_file_utils.py  # File management tests
```

## Test Fixtures

### Core Fixtures (conftest.py)

```python
import pytest
import tempfile
import asyncio
from sqlmodel import create_engine, SQLModel, Session
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db

@pytest.fixture
def test_db():
    """Test database with temporary SQLite file"""
    with tempfile.NamedTemporaryFile(suffix=".db") as tmp:
        engine = create_engine(f"sqlite:///{tmp.name}")
        SQLModel.metadata.create_all(engine)
        yield engine

@pytest.fixture
def client(test_db):
    """FastAPI TestClient with test database"""
    def override_get_db():
        with Session(test_db) as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()

@pytest.fixture
def mock_gemini_response():
    """Mock Gemini API response for NLP parsing"""
    return {
        "bezirk": "Pankow",
        "categories": ["transport", "administrative"],
        "confidence": 0.95,
        "analysis_type": "basic"
    }

@pytest.fixture
def sample_geodata():
    """Sample GeoDataFrame for testing"""
    import geopandas as gpd
    from shapely.geometry import Point

    data = {
        'name': ['Point A', 'Point B'],
        'category': ['transport', 'administrative'],
        'geometry': [Point(13.4, 52.5), Point(13.3, 52.4)]
    }
    return gpd.GeoDataFrame(data, crs="EPSG:4326")

@pytest.fixture
async def mock_external_services():
    """Mock all external service dependencies"""
    with patch('app.services.nlp_service.ChatGoogleGenerativeAI'), \
         patch('app.connectors.geoportal.requests.get'), \
         patch('app.connectors.osm.requests.get'):
        yield
```

## Unit Tests

### Service Layer Tests

#### NLP Service Tests (test_nlp_service.py)

```python
import pytest
from unittest.mock import patch, AsyncMock
import json
from app.services.nlp_service import GeodataRequestParser

@pytest.mark.asyncio
async def test_parse_user_request_success():
    """Test successful NLP parsing of user request"""
    service = GeodataRequestParser(api_key="test-key")

    # Mock Gemini response
    mock_response = AsyncMock()
    mock_response.content = json.dumps({
        "bezirk": "Pankow",
        "categories": ["transport"],
        "confidence": 0.95
    })

    with patch.object(service.llm, 'ainvoke', return_value=mock_response):
        result = await service.parse_user_request("Pankow Verkehrsdaten")

        assert result["bezirk"] == "Pankow"
        assert "transport" in result["categories"]
        assert result["confidence"] > 0.9

@pytest.mark.asyncio
async def test_parse_user_request_low_confidence():
    """Test handling of low confidence parsing"""
    service = GeodataRequestParser(api_key="test-key")

    mock_response = AsyncMock()
    mock_response.content = json.dumps({
        "bezirk": null,
        "categories": [],
        "confidence": 0.3
    })

    with patch.object(service.llm, 'ainvoke', return_value=mock_response):
        result = await service.parse_user_request("unclear request")

        assert result["confidence"] < 0.7
        assert result["bezirk"] is None
```

#### Data Service Tests (test_data_service.py)

```python
import pytest
from unittest.mock import patch, AsyncMock
from app.services.data_service import DataAcquisitionService

@pytest.mark.asyncio
async def test_fetch_datasets_for_request(sample_geodata):
    """Test coordinated dataset acquisition"""
    service = DataAcquisitionService(db_session=None, connectors={})

    # Mock database queries and connector calls
    with patch.object(service, '_get_datasets_by_categories') as mock_datasets, \
         patch.object(service, '_get_district_boundary') as mock_boundary, \
         patch.object(service, '_fetch_single_dataset') as mock_fetch:

        mock_datasets.return_value = [{"id": "test_dataset"}]
        mock_boundary.return_value = sample_geodata
        mock_fetch.return_value = {
            "dataset_id": "test_dataset",
            "geodata": sample_geodata,
            "runtime_stats": {"feature_count": 2}
        }

        results = await service.fetch_datasets_for_request("Pankow", ["transport"])

        assert len(results) == 1
        assert results[0]["dataset_id"] == "test_dataset"
        assert results[0]["runtime_stats"]["feature_count"] == 2

@pytest.mark.asyncio
async def test_fetch_single_dataset_timeout():
    """Test timeout handling for individual datasets"""
    service = DataAcquisitionService(db_session=None, connectors={})

    mock_connector = AsyncMock()
    mock_connector.fetch_data.side_effect = asyncio.TimeoutError()

    with pytest.raises(Exception):  # Should handle timeout gracefully
        await service._fetch_single_dataset(
            {"connector_type": "geoportal"},
            (13.0, 52.0, 13.8, 52.8)
        )
```

### API Tests

#### Chat API Tests (test_chat.py)

```python
def test_chat_message_endpoint_success(client):
    """Test successful chat message processing"""
    with patch('app.services.nlp_service.GeodataRequestParser.parse_user_request') as mock_parse:
        mock_parse.return_value = {
            "bezirk": "Pankow",
            "categories": ["transport"],
            "confidence": 0.95
        }

        response = client.post(
            "/api/chat/message",
            json={"text": "Pankow Grunddaten für Analyse"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "processing"

def test_chat_message_low_confidence(client):
    """Test handling of low confidence parsing"""
    with patch('app.services.nlp_service.GeodataRequestParser.parse_user_request') as mock_parse:
        mock_parse.return_value = {
            "bezirk": None,
            "categories": [],
            "confidence": 0.3
        }

        response = client.post(
            "/api/chat/message",
            json={"text": "unclear request"}
        )

        assert response.status_code == 400
        assert "eindeutig verstanden" in response.json()["detail"]
```

## Integration Tests

### Connector Integration Tests

#### Geoportal Connector Tests (test_geoportal.py)

```python
import pytest
import os
from app.connectors.geoportal import GeoportalConnector

@pytest.mark.asyncio
@pytest.mark.skipif(
    os.getenv("INTEGRATION_TESTS") != "true",
    reason="Integration tests require INTEGRATION_TESTS=true"
)
async def test_geoportal_connector_real_data():
    """Integration test with real Berlin Geoportal WFS"""
    connector = GeoportalConnector()

    # Test with real WFS endpoint
    gdf = await connector.fetch_data(
        "bezirksgrenzen",
        (13.0, 52.3, 13.8, 52.7)
    )

    assert len(gdf) > 0
    assert gdf.crs is not None
    assert gdf.geometry.is_valid.all()

@pytest.mark.asyncio
async def test_geoportal_connector_mock():
    """Unit test with mocked WFS response"""
    connector = GeoportalConnector()

    mock_response = """<?xml version="1.0"?>
    <gml:FeatureCollection>
        <gml:featureMember>
            <test:feature>
                <test:geometry>
                    <gml:Point><gml:coordinates>13.4,52.5</gml:coordinates></gml:Point>
                </test:geometry>
            </test:feature>
        </gml:featureMember>
    </gml:FeatureCollection>"""

    with patch('requests.get') as mock_get:
        mock_get.return_value.text = mock_response
        mock_get.return_value.status_code = 200

        gdf = await connector.fetch_data("test_layer", (13.0, 52.0, 13.8, 52.8))

        assert len(gdf) == 1
```

## End-to-End Tests

### Complete Workflow Tests

```python
@pytest.mark.asyncio
async def test_complete_geodata_workflow(client):
    """End-to-end test of complete geodata request workflow"""
    # 1. Submit chat request
    response = client.post(
        "/api/chat/message",
        json={"text": "Pankow Verkehrsdaten"}
    )

    assert response.status_code == 200
    job_id = response.json()["job_id"]

    # 2. Poll job status (mock async processing completion)
    with patch('app.services.data_service.DataAcquisitionService.fetch_datasets_for_request'):
        # Wait for job completion (or mock it)
        import time
        time.sleep(0.1)  # Simulate processing time

        status_response = client.get(f"/api/jobs/status/{job_id}")
        assert status_response.status_code == 200

        # 3. Download result package (when completed)
        if status_response.json()["status"] == "completed":
            download_url = status_response.json()["download_url"]
            download_response = client.get(download_url)
            assert download_response.status_code == 200
            assert download_response.headers["content-type"] == "application/zip"
```

## Performance Tests

### Load Testing

```python
import asyncio
import aiohttp
import time

async def test_concurrent_requests():
    """Test system under concurrent load"""
    async def make_request(session, request_id):
        async with session.post(
            "http://localhost:8000/api/chat/message",
            json={"text": f"Pankow Verkehrsdaten {request_id}"}
        ) as response:
            return await response.json()

    async with aiohttp.ClientSession() as session:
        start_time = time.time()

        tasks = [make_request(session, i) for i in range(10)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        end_time = time.time()

        # Verify all requests succeeded
        successful = [r for r in results if not isinstance(r, Exception)]
        assert len(successful) >= 8  # Allow some failures under load

        # Verify reasonable response times
        total_time = end_time - start_time
        assert total_time < 30  # All requests should complete within 30s
```

## Test Automation

### Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: pytest
        name: pytest
        entry: uv run pytest
        language: system
        pass_filenames: false
        always_run: true
```

### Coverage Requirements

```bash
# Run tests with coverage
uv run pytest --cov=app --cov-report=html --cov-fail-under=80

# Coverage configuration in pyproject.toml
[tool.coverage.run]
source = ["app"]
omit = ["*/tests/*", "*/venv/*", "*/__pycache__/*"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError"
]
```
