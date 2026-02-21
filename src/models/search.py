from pydantic import BaseModel


class SearchRequest(BaseModel):
    """Search request payload."""

    query: str
    limit: int = 5
    score_threshold: float = 0.5
    collections: list[str] | None = None  # If None, search all collections


class SearchResponse(BaseModel):
    """Search response."""

    query: str
    results: list[dict]
    count: int
