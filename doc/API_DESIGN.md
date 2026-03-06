> ⚠️ **Archived** — This document was written during initial development and
> references the Gemini API or earlier MVP assumptions. The system now uses OpenAI.
> Use the root `README.md` for setup and `doc/README.md` for document status.

# API Design Specification

This document defines the REST API design for urbanIQ Berlin geodata aggregation system.

## API Architecture

- **Framework**: FastAPI with automatic OpenAPI documentation
- **Authentication**: None (MVP phase, public access)
- **Response Format**: JSON with consistent error handling
- **Async Support**: Full async/await support for I/O operations

## Chat Interface Endpoints

### POST /api/chat/message

Processes natural language geodata requests and initiates async processing jobs.

**Request Body:**

```json
{
  "text": "Pankow Grunddaten für Mobilitätsanalyse",
  "user_id": "optional-user-identifier"
}
```

**Response:**

```json
{
  "job_id": "uuid-string",
  "status": "processing",
  "message": "Geodaten für Pankow werden abgerufen..."
}
```

**Process Flow:**

1. Parse user request with Gemini NLP service
2. Validate confidence threshold (>= 0.7)
3. Create job record in database
4. Start async geodata processing task
5. Return job ID for status polling

**Error Responses:**

- `400 Bad Request`: Low confidence parsing or invalid request
- `500 Internal Server Error`: Service unavailable or processing error

## Job Management Endpoints

### GET /api/jobs/status/{job_id}

Polls processing status for async geodata jobs.

**Path Parameters:**

- `job_id`: UUID of the processing job

**Response (Processing):**

```json
{
  "job_id": "uuid-string",
  "status": "processing",
  "progress": 65,
  "created_at": "2025-01-15T10:30:00Z"
}
```

**Response (Completed):**

```json
{
  "job_id": "uuid-string",
  "status": "completed",
  "progress": 100,
  "created_at": "2025-01-15T10:30:00Z",
  "completed_at": "2025-01-15T10:32:15Z",
  "download_url": "/api/downloads/package-uuid"
}
```

**Response (Failed):**

```json
{
  "job_id": "uuid-string",
  "status": "failed",
  "progress": 45,
  "created_at": "2025-01-15T10:30:00Z",
  "error": "Service timeout: Berlin Geoportal WFS not responding"
}
```

## Download Management Endpoints

### GET /api/downloads/{package_id}

Downloads generated geodata packages as ZIP files.

**Path Parameters:**

- `package_id`: UUID of the generated package

**Response:**

- **Content-Type**: `application/zip`
- **Content-Disposition**: `attachment; filename="geodata_pankow_20250115.zip"`
- **Body**: Binary ZIP file content

**Error Responses:**

- `404 Not Found`: Package expired or doesn't exist
- `410 Gone`: Package has been cleaned up

## Health Check Endpoints

### GET /health

System health check for monitoring and load balancing.

**Response:**

```json
{
  "status": "healthy",
  "timestamp": "2025-01-15T10:30:00Z",
  "services": {
    "database": "ok",
    "gemini_api": "ok",
    "geoportal_wfs": "ok",
    "osm_overpass": "ok"
  }
}
```

## Request/Response Models

### Pydantic Models

```python
from pydantic import BaseModel
from typing import Optional

class ChatMessage(BaseModel):
    text: str
    user_id: Optional[str] = None

class ChatResponse(BaseModel):
    job_id: str
    status: str
    message: str

class JobStatus(BaseModel):
    job_id: str
    status: str
    progress: int
    created_at: str
    completed_at: Optional[str] = None
    download_url: Optional[str] = None
    error: Optional[str] = None
```

## Error Handling

### HTTP Status Codes

- **200 OK**: Successful request
- **202 Accepted**: Job created and processing started
- **400 Bad Request**: Invalid request format or low confidence parsing
- **404 Not Found**: Resource not found
- **410 Gone**: Resource expired or cleaned up
- **422 Unprocessable Entity**: Validation error
- **500 Internal Server Error**: Service error
- **503 Service Unavailable**: External service dependency failure

### Error Response Format

```json
{
  "error": {
    "code": "PARSING_CONFIDENCE_TOO_LOW",
    "message": "Anfrage konnte nicht eindeutig verstanden werden",
    "details": {
      "confidence": 0.45,
      "threshold": 0.7,
      "suggestion": "Bitte spezifizieren Sie den gewünschten Bezirk genauer"
    }
  }
}
```

## OpenAPI Documentation

FastAPI automatically generates:

- **Swagger UI**: Available at `/docs`
- **ReDoc**: Available at `/redoc`
- **OpenAPI Schema**: Available at `/openapi.json`

## Rate Limiting

**MVP Phase**: No rate limiting implemented
**Future Considerations**:

- Per-IP request limits
- User-based quotas
- API key authentication
