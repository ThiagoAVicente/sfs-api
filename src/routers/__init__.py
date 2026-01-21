from .v1 import router as v1_router
from .v2 import router as v2_router
from fastapi import APIRouter

router = APIRouter()
router.include_router(v1_router, prefix="/v1")
router.include_router(v2_router, prefix="/v2")
