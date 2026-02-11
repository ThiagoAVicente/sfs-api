from .index import router as index_router
from .search import router as search_router
from .files import router as files_router
from fastapi import APIRouter

router = APIRouter()

# Include routers
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
