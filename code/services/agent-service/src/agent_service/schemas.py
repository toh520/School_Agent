"""Public API envelope and pagination contracts."""

from datetime import datetime
from zoneinfo import ZoneInfo

from pydantic import BaseModel, Field

APPLICATION_ZONE = ZoneInfo("Asia/Shanghai")


class ApiError(BaseModel):
    code: str
    message: str


class ApiResponse[T](BaseModel):
    success: bool
    data: T | None
    error: ApiError | None
    request_id: str = Field(serialization_alias="requestId")
    timestamp: datetime

    @classmethod
    def ok(cls, data: T, request_id: str) -> "ApiResponse[T]":
        """Build a successful response in the project timezone."""

        return cls(
            success=True,
            data=data,
            error=None,
            request_id=request_id,
            timestamp=datetime.now(APPLICATION_ZONE),
        )


class PageResponse[T](BaseModel):
    items: list[T]
    page: int = Field(ge=0)
    size: int = Field(ge=1, le=200)
    total: int = Field(ge=0)
    total_pages: int = Field(ge=0, serialization_alias="totalPages")


class DatabaseStatus(BaseModel):
    status: str
    version: str


class AgentHealth(BaseModel):
    status: str
    version: str
    database: DatabaseStatus
