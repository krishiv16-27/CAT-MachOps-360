"""Shared Pydantic schema helpers."""
from typing import Any, Generic, TypeVar
from pydantic import BaseModel
from datetime import datetime

T = TypeVar("T")


class Meta(BaseModel):
    timestamp: str = ""
    total: int | None = None
    page: int | None = None
    page_size: int | None = None

    def model_post_init(self, __context: Any) -> None:
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat() + "Z"


class ApiResponse(BaseModel, Generic[T]):
    data: T
    meta: Meta = Meta()


class ErrorDetail(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorDetail
