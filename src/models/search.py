from pydantic import BaseModel


class SearchRequest(BaseModel):
    """Search request payload."""
    query: str
    limit: int = 5
    score_threshold: float = 0.5


class SearchResponse(BaseModel):
    """Search response."""
    query: str
    results: list[dict]
    count: int
