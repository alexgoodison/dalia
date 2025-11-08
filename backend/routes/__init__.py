from fastapi import APIRouter

from .health import router as health_router
from .trading212 import router as trading212_router

router = APIRouter()
router.include_router(health_router)
router.include_router(trading212_router)

__all__ = ["router"]
