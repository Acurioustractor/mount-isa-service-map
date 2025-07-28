"""
Main FastAPI application for Mount Isa Service Map Intelligent Scraping System
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import sys
from pathlib import Path

# Add app directory to path
sys.path.append(str(Path(__file__).parent.parent))

from app.core.config import settings
from app.core.database import init_db
from app.core.logging import setup_logging
from app.api.v1.router import api_router
from app.core.exceptions import ScrapingSystemException


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Starting Mount Isa Service Map Scraping System...")
    
    # Initialize database
    await init_db()
    logger.info("Database initialized")
    
    # TODO: Initialize agent orchestrator
    # TODO: Start background tasks
    
    yield
    
    # Shutdown
    logger.info("Shutting down Mount Isa Service Map Scraping System...")


# Create FastAPI application
app = FastAPI(
    title="Mount Isa Service Map - Intelligent Scraping System",
    description="World-class intelligent web scraping and autonomous agent system for community service discovery and validation",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS
)

# Include API routes
app.include_router(api_router, prefix="/api/v1")


@app.exception_handler(ScrapingSystemException)
async def scraping_system_exception_handler(request: Request, exc: ScrapingSystemException):
    """Handle custom scraping system exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.error_code,
            "message": exc.message,
            "details": exc.details
        }
    )


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Mount Isa Service Map - Intelligent Scraping System",
        "version": "1.0.0",
        "status": "operational",
        "docs_url": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": "2025-07-28T12:00:00Z",
        "version": "1.0.0"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )