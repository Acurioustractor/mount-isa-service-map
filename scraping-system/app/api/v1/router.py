"""
Main API router for v1 endpoints
"""

from fastapi import APIRouter
from app.api.v1.endpoints import services, agents, validation, discovery, research

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(
    services.router,
    prefix="/services",
    tags=["services"]
)

api_router.include_router(
    agents.router,
    prefix="/agents", 
    tags=["agents"]
)

api_router.include_router(
    validation.router,
    prefix="/validation",
    tags=["validation"]
)

api_router.include_router(
    discovery.router,
    prefix="/discovery",
    tags=["discovery"]
)

api_router.include_router(
    research.router,
    prefix="/research",
    tags=["research"]
)