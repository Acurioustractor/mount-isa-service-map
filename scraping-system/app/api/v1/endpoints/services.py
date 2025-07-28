"""
Services API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from uuid import UUID

from app.core.database import get_async_session
from app.models.service import (
    Service, ServiceCreate, ServiceUpdate, ServiceSummary,
    ServiceSearchRequest, ServiceSearchResponse
)
from app.services.service_service import ServiceService

router = APIRouter()


@router.get("/", response_model=ServiceSearchResponse)
async def search_services(
    query: Optional[str] = Query(None, description="Search query"),
    category: Optional[str] = Query(None, description="Service category"),
    location: Optional[str] = Query(None, description="Location filter"),
    postcode: Optional[str] = Query(None, description="Postcode filter"),
    verified_only: bool = Query(False, description="Only return verified services"),
    min_confidence: float = Query(0.0, ge=0, le=1, description="Minimum confidence score"),
    limit: int = Query(20, ge=1, le=100, description="Number of results per page"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: AsyncSession = Depends(get_async_session)
):
    """Search services with filters"""
    search_request = ServiceSearchRequest(
        query=query,
        category=category,
        location=location,
        postcode=postcode,
        verified_only=verified_only,
        min_confidence=min_confidence,
        limit=limit,
        offset=offset
    )
    
    service_service = ServiceService(db)
    return await service_service.search_services(search_request)


@router.get("/{service_id}", response_model=Service)
async def get_service(
    service_id: UUID,
    db: AsyncSession = Depends(get_async_session)
):
    """Get service by ID"""
    service_service = ServiceService(db)
    service = await service_service.get_service(service_id)
    
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    return service


@router.post("/", response_model=Service)
async def create_service(
    service_data: ServiceCreate,
    db: AsyncSession = Depends(get_async_session)
):
    """Create a new service"""
    service_service = ServiceService(db)
    return await service_service.create_service(service_data)


@router.put("/{service_id}", response_model=Service)
async def update_service(
    service_id: UUID,
    service_data: ServiceUpdate,
    db: AsyncSession = Depends(get_async_session)
):
    """Update an existing service"""
    service_service = ServiceService(db)
    service = await service_service.update_service(service_id, service_data)
    
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    return service


@router.delete("/{service_id}")
async def delete_service(
    service_id: UUID,
    db: AsyncSession = Depends(get_async_session)
):
    """Delete a service"""
    service_service = ServiceService(db)
    success = await service_service.delete_service(service_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Service not found")
    
    return {"message": "Service deleted successfully"}


@router.get("/categories/list", response_model=List[str])
async def get_categories(
    db: AsyncSession = Depends(get_async_session)
):
    """Get list of all service categories"""
    service_service = ServiceService(db)
    return await service_service.get_categories()


@router.get("/stats/summary")
async def get_service_stats(
    db: AsyncSession = Depends(get_async_session)
):
    """Get service statistics summary"""
    service_service = ServiceService(db)
    return await service_service.get_service_stats()


@router.post("/{service_id}/verify")
async def verify_service(
    service_id: UUID,
    db: AsyncSession = Depends(get_async_session)
):
    """Mark a service as verified"""
    service_service = ServiceService(db)
    service = await service_service.verify_service(service_id)
    
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    return {"message": "Service verified successfully"}


@router.post("/{service_id}/flag")
async def flag_service(
    service_id: UUID,
    reason: str = Query(..., description="Reason for flagging"),
    db: AsyncSession = Depends(get_async_session)
):
    """Flag a service for review"""
    service_service = ServiceService(db)
    success = await service_service.flag_service(service_id, reason)
    
    if not success:
        raise HTTPException(status_code=404, detail="Service not found")
    
    return {"message": "Service flagged for review"}