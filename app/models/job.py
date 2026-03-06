"""
Job model for asynchronous geodata processing requests.

Manages job lifecycle from user request through completion,
tracking progress and maintaining relationships to result packages.
"""

import json
from datetime import UTC, datetime
from enum import Enum
from uuid import uuid4

from pydantic import field_validator
from sqlmodel import Field, SQLModel


class JobStatus(str, Enum):
    """Job processing status enumeration."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Job(SQLModel, table=True):
    """
    Job model for tracking geodata processing requests.

    Represents asynchronous processing jobs initiated by user requests,
    tracking their progress from creation to completion.
    """

    __tablename__ = "jobs"

    id: str = Field(
        default_factory=lambda: str(uuid4()),
        primary_key=True,
        description="Unique job identifier",
    )
    status: JobStatus = Field(
        default=JobStatus.PENDING,
        description="Current processing status",
    )
    request_text: str = Field(
        description="Original user request in natural language",
    )
    bezirk: str | None = Field(
        default=None,
        description="Extracted Berlin district name",
    )
    datasets: str | None = Field(
        default=None,
        description="JSON array of requested datasets",
    )
    progress: int = Field(
        default=0,
        ge=0,
        le=100,
        description="Processing progress percentage (0-100)",
    )
    result_package_id: str | None = Field(
        default=None,
        description="Reference to generated package when completed",
    )
    error_message: str | None = Field(
        default=None,
        description="Error details when failed",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Job creation timestamp",
    )
    completed_at: datetime | None = Field(
        default=None,
        description="Job completion timestamp",
    )

    # Relationships will be added after Package import to avoid circular import

    @field_validator("datasets")
    @classmethod
    def validate_datasets(cls, v: str | list | None) -> str | None:
        """Validate datasets field contains valid JSON array."""
        if v is None:
            return v

        # Handle list input (convert to JSON string)
        if isinstance(v, list):
            return json.dumps(v)

        # Handle string input (validate JSON)
        if isinstance(v, str):
            try:
                parsed = json.loads(v)
                if not isinstance(parsed, list):
                    raise ValueError("datasets must be a JSON array")
                return v
            except json.JSONDecodeError as e:
                raise ValueError(f"datasets must be valid JSON: {e}") from e

        raise ValueError("datasets must be a list or JSON string")

    @field_validator("progress")
    @classmethod
    def validate_progress(cls, v: int) -> int:
        """Validate progress is between 0 and 100."""
        if not 0 <= v <= 100:
            raise ValueError("progress must be between 0 and 100")
        return v

    def is_finished(self) -> bool:
        """Check if job is in a finished state."""
        return self.status in (JobStatus.COMPLETED, JobStatus.FAILED)

    def mark_completed(self, package_id: str) -> None:
        """Mark job as completed with result package."""
        self.status = JobStatus.COMPLETED
        self.progress = 100
        self.result_package_id = package_id
        self.completed_at = datetime.now(UTC)

    def mark_failed(self, error_message: str) -> None:
        """Mark job as failed with error message."""
        self.status = JobStatus.FAILED
        self.error_message = error_message
        self.completed_at = datetime.now(UTC)
