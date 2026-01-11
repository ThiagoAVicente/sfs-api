from .index import router as index_router
from .search import router as search_router
from .files import router as files_router
from fastapi import APIRouter
from slowapi import Limiter
from slowapi.util import get_remote_address

# Rate limiter configuration
limiter = Limiter(key_func=get_remote_address)

router = APIRouter()

# Apply rate limits to routers
router.include_router(
    index_router,
    prefix="/index",
    tags=["indexing"]
)
router.include_router(
    search_router,
    prefix="/search",
    tags=["search"]
)
router.include_router(
    files_router,
    prefix="/files",
    tags=["files"]
)


@router.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Semantic File Search API",
        "version": "0.1.0",
        "docs": "/docs"
    }


@router.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}
