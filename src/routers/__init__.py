from fastapi import APIRouter
from slowapi import Limiter
from slowapi.util import get_remote_address

# Shared rate limiter for entire application
limiter = Limiter(key_func=get_remote_address)

from .v1 import router as v1_router
from .v2 import router as v2_router

router = APIRouter()
router.include_router(v1_router, prefix="/v1")
router.include_router(v2_router, prefix="/v2")
