from pydantic import BaseModel, Field
from typing import Any, Generic, TypeVar
from math import ceil

T = TypeVar("T")


class PaginationParams(BaseModel):
    """Pagination query parameters."""

    limit: int = Field(default=20, ge=1, le=100, description="Items per page")
    page: int = Field(default=1, ge=1, description="Page number (1-indexed)")

    @property
    def offset(self) -> int:
        """Calculate offset from page and limit."""
        return (self.page - 1) * self.limit


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response."""

    items: list[T]
    total: int
    limit: int
    page: int
    total_pages: int
    has_next: bool
    has_prev: bool

    @classmethod
    def create(
        cls, items: list[T], total: int, page: int, limit: int
    ) -> "PaginatedResponse[T]":
        """
        Create a paginated response.

        Args:
            items: Items for current page
            total: Total number of items
            page: Current page number
            limit: Items per page

        Returns:
            PaginatedResponse instance
        """
        total_pages = ceil(total / limit) if limit > 0 else 0
        has_next = page < total_pages
        has_prev = page > 1

        return cls(
            items=items,
            total=total,
            limit=limit,
            page=page,
            total_pages=total_pages,
            has_next=has_next,
            has_prev=has_prev,
        )
