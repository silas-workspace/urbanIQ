"""
Package model for downloadable ZIP packages containing geodata and metadata.

Manages ZIP packages with geodata files and LLM-generated metadata reports,
including download tracking and automatic expiration.
"""

from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

from pydantic import field_validator
from sqlmodel import Field, SQLModel


class Package(SQLModel, table=True):
    """
    Package model for downloadable geodata ZIP files.

    Represents ZIP packages containing harmonized geodata and metadata reports,
    with automatic expiration and download tracking.
    """

    __tablename__ = "packages"

    id: str = Field(
        default_factory=lambda: str(uuid4()),
        primary_key=True,
        description="Unique package identifier",
    )
    job_id: str = Field(
        foreign_key="jobs.id",
        description="Reference to originating job",
    )
    file_path: str = Field(
        description="Local filesystem path to ZIP package",
    )
    file_size: int | None = Field(
        default=None,
        ge=0,
        description="Package size in bytes",
    )
    download_count: int = Field(
        default=0,
        ge=0,
        description="Number of times package was downloaded",
    )
    metadata_report: str | None = Field(
        default=None,
        description="LLM-generated markdown metadata report",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Package creation timestamp",
    )
    expires_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC) + timedelta(hours=24),
        description="Automatic cleanup timestamp (24h default)",
    )

    # Relationships will be added after Job import to avoid circular import

    @field_validator("file_path")
    @classmethod
    def validate_file_path(cls, v: str) -> str:
        """Validate file path is absolute and has .zip extension."""
        path = Path(v)
        if not path.suffix.lower() == ".zip":
            raise ValueError("file_path must have .zip extension")
        return v

    @field_validator("file_size")
    @classmethod
    def validate_file_size(cls, v: int | None) -> int | None:
        """Validate file size is non-negative."""
        if v is not None and v < 0:
            raise ValueError("file_size must be non-negative")
        return v

    def is_expired(self) -> bool:
        """Check if package has expired."""
        return datetime.now(UTC) > self.expires_at

    def increment_download(self) -> None:
        """Increment download counter."""
        self.download_count += 1

    def extend_expiration(self, hours: int = 24) -> None:
        """Extend package expiration time."""
        self.expires_at = datetime.now(UTC) + timedelta(hours=hours)

    def get_file_size_mb(self) -> float | None:
        """Get file size in megabytes."""
        if self.file_size is None:
            return None
        return round(self.file_size / (1024 * 1024), 2)
