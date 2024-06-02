from fastapi import APIRouter

from .endpoints import health_check, backend, frontend, crud


# Creates an API router and includes the router with the routes defined in endpoints.<service>.router
api_router = APIRouter()
api_router.include_router(health_check.router, tags=["health"])
api_router.include_router(backend.router, tags=["backend"])
api_router.include_router(frontend.router, tags=["frontend"])
api_router.include_router(crud.router)