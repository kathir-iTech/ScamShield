from routers.health import router as health_router
from routers.analyze import router as analyze_router
from routers.auth import router as auth_router

__all__ = [
    "health_router",
    "analyze_router",
    "auth_router",
]
