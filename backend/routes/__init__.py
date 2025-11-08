from fastapi import APIRouter

from .chat import router as chat_router
from .health import router as health_router
from .trading212 import router as trading212_router

router = APIRouter()
router.include_router(health_router)
router.include_router(trading212_router)
router.include_router(chat_router)

__all__ = ["router"]
