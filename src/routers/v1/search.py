import logging
import os
from fastapi import APIRouter, HTTPException, Request
from src.models import SearchRequest, SearchResponse
from src.search.searcher import Searcher
from src.cache import QueryCache
from src.clients import RedisClient
from slowapi import Limiter
from slowapi.util import get_remote_address

logger = logging.getLogger(__name__)
router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

COLLECTION_NAME = os.environ.get('COLLECTION_NAME', 'default')
RATE_LIMIT_SEARCH = os.environ.get('RATE_LIMIT_SEARCH', '30')


@router.post("", response_model=SearchResponse)
@limiter.limit(f"{RATE_LIMIT_SEARCH}/minute")
async def search_files(
    body: SearchRequest,
    request: Request,
):
    """
    Search for files by semantic similarity.

    Args:
        body: Search request with query and parameters
        request: FastAPI request object (required for rate limiting)

    Returns:
        Search results with scores and file metadata
    """

    query = body.query
    limit = body.limit
    score_threshold = body.score_threshold

    # check for hits on cache
    redis = await RedisClient.get()
    query_cache = QueryCache(redis)
    results = await query_cache.get_query_results(query, score_threshold, limit)
    if results is not None:
        return SearchResponse(
            query=query,
            results=results,
            count=len(results)
        )

    try:
        if not query or query.strip() == "":
            raise HTTPException(status_code=400, detail="Query cannot be empty")

        results = await Searcher.search(
            query=query,
            collection_name=COLLECTION_NAME,
            limit=limit,
            score_threshold=score_threshold
        )

        await query_cache.cache_query_results(query, results, score_threshold, limit)
        return SearchResponse(
            query=query,
            results=results,
            count=len(results)
        )

    except Exception as e:
        logger.error(f"Error searching: {e}")
        raise HTTPException(status_code=500, detail=str(e))
