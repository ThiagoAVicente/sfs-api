import logging
from fastapi import APIRouter, HTTPException, Request
from src.clients import QdrantClient

logger = logging.getLogger(__name__)
router = APIRouter()

# Import shared limiter
from src.routers import limiter

RATE_LIMIT = "60"


@router.get("")
@limiter.limit(f"{RATE_LIMIT}/minute")
async def list_collections(request: Request):
    """
    List all available collections in Qdrant.

    Returns:
        List of collection names
    """
    try:
        collections = await QdrantClient.get_collections()
        return {"collections": collections, "count": len(collections)}
    except Exception as e:
        logger.error(f"Error listing collections: {e}")
        raise HTTPException(status_code=500, detail=str(e))
