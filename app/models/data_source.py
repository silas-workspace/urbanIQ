"""
DataSource model for geodata source registry.

Manages registry of available geodata sources with curated metadata
for Berlin Geoportal WFS and OpenStreetMap endpoints.
"""

import json
from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import field_validator
from sqlmodel import Field, SQLModel


class ConnectorType(str, Enum):
    """Data source connector type enumeration."""

    GEOPORTAL = "geoportal"
    OSM = "osm"


class HealthStatus(str, Enum):
    """Data source health check status enumeration."""

    OK = "ok"
    ERROR = "error"
    TIMEOUT = "timeout"


class DataSource(SQLModel, table=True):
    """
    DataSource model for geodata source registry.

    Registry of available geodata sources with curated metadata
    for automated data acquisition and quality tracking.
    """

    __tablename__ = "data_sources"

    id: str = Field(
        default_factory=lambda: str(uuid4()),
        primary_key=True,
        description="Unique source identifier",
    )
    name: str = Field(
        description="Human-readable source name",
    )
    description: str | None = Field(
        default=None,
        description="Source description for metadata reports",
    )
    connector_type: ConnectorType = Field(
        description="Connection method (geoportal for WFS, osm for Overpass API)",
    )
    service_url: str = Field(
        description="Base URL for data access",
    )
    layer_name: str | None = Field(
        default=None,
        description="Specific layer/dataset identifier",
    )
    category: str = Field(
        description="Primary data category (transport, environment, administrative)",
    )
    subcategory: str | None = Field(
        default=None,
        description="Refined categorization",
    )
    metadata_json: str = Field(
        description="Curated metadata (license, quality, update frequency)",
    )
    active: bool = Field(
        default=True,
        description="Whether source is currently available",
    )
    last_tested: datetime | None = Field(
        default=None,
        description="Last health check timestamp",
    )
    test_status: HealthStatus | None = Field(
        default=None,
        description="Health check status",
    )

    @field_validator("service_url")
    @classmethod
    def validate_service_url(cls, v: str) -> str:
        """Validate service URL format."""
        if not v.startswith(("http://", "https://")):
            raise ValueError("service_url must start with http:// or https://")
        return v

    @field_validator("metadata_json")
    @classmethod
    def validate_metadata_json(cls, v: str) -> str:
        """Validate metadata_json contains valid JSON."""
        try:
            parsed = json.loads(v)
            if not isinstance(parsed, dict):
                raise ValueError("metadata_json must be a JSON object")
            return v
        except json.JSONDecodeError as e:
            raise ValueError(f"metadata_json must be valid JSON: {e}") from e

    def get_metadata(self) -> dict[str, Any]:
        """Parse and return metadata as dictionary."""
        metadata: dict[str, Any] = json.loads(self.metadata_json)
        return metadata

    def update_health_status(self, status: HealthStatus) -> None:
        """Update health check status and timestamp."""
        self.test_status = status
        self.last_tested = datetime.now(UTC)

    def is_healthy(self) -> bool:
        """Check if data source is healthy and active."""
        return self.active and self.test_status == HealthStatus.OK

    def get_full_service_url(self) -> str:
        """Get complete service URL including layer if applicable."""
        if self.layer_name and self.connector_type == ConnectorType.GEOPORTAL:
            return f"{self.service_url}?service=WFS&request=GetFeature&typeName={self.layer_name}"
        return self.service_url
