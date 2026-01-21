import logging
import os
from fastapi import APIRouter, HTTPException, Request, Depends
from src.models import SearchRequest, SearchResponse
from src.models.pagination import PaginationParams, PaginatedResponse
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
MAX_SEARCH_LIMIT = int(os.environ.get('MAX_SEARCH_LIMIT', '500'))


@router.post("", response_model=PaginatedResponse[dict])
@limiter.limit(f"{RATE_LIMIT_SEARCH}/minute")
async def search_files(
    body: SearchRequest,
    request: Request,
    pagination: PaginationParams = Depends()
):
    """
    Search for files by semantic similarity with pagination.

    Args:
        body: Search request with query and parameters
        request: FastAPI request object (required for rate limiting)
        pagination: Pagination parameters (page, limit)

    Returns:
        Paginated search results with scores and file metadata
    """
    query = body.query
    score_threshold = body.score_threshold

    try:
        if not query or query.strip() == "":
            raise HTTPException(status_code=400, detail="Query cannot be empty")

        redis = await RedisClient.get()
        query_cache = QueryCache(redis)

        # Check cache for full result set (with high limit)
        cached_results = await query_cache.get_query_results(
            query=query,
            score_threshold=score_threshold,
            limit=MAX_SEARCH_LIMIT
        )

        if cached_results is None:
            # Cache miss - query Qdrant with max limit
            cached_results = await Searcher.search(
                query=query,
                collection_name=COLLECTION_NAME,
                limit=MAX_SEARCH_LIMIT,
                score_threshold=score_threshold
            )

            # Cache the full result set
            await query_cache.cache_query_results(
                query=query,
                results=cached_results,
                score_threshold=score_threshold,
                limit=MAX_SEARCH_LIMIT
            )
            logger.info(f"Searched and cached {len(cached_results)} results for query: {query[:50]}")

        # Paginate results from cache
        total = len(cached_results)
        start = pagination.offset
        end = start + pagination.limit
        paginated_results = cached_results[start:end]

        return PaginatedResponse.create(
            items=paginated_results,
            total=total,
            page=pagination.page,
            limit=pagination.limit
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching: {e}")
        raise HTTPException(status_code=500, detail=str(e))
