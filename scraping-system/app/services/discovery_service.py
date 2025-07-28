"""
Discovery service for business logic
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc, func
import uuid

from app.models.discovery import (
    DiscoveryRequest, DiscoveryResponse, DiscoveredService,
    DiscoveryResult, DiscoveryMetrics, DiscoveryHistory,
    CrawlResult, PageAnalysis
)
from app.core.database import ServiceModel, DiscoveryResultModel
from app.core.exceptions import DiscoveryException


class DiscoveryService:
    """Service for managing discovery operations"""
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
    
    async def create_discovery_request(
        self, 
        url: str, 
        max_depth: int = 2,
        options: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create a new discovery request"""
        discovery_id = str(uuid.uuid4())
        
        # Store discovery request in database
        # This would typically create a DiscoveryRequest record
        # For now, we'll return the discovery ID
        
        return discovery_id
    
    async def get_discovery_result(self, discovery_id: str) -> Optional[DiscoveryResponse]:
        """Get discovery result by ID"""
        try:
            # Query discovery result from database
            stmt = select(DiscoveryResultModel).where(
                DiscoveryResultModel.discovery_id == discovery_id
            )
            result = await self.db.execute(stmt)
            discovery_record = result.scalar_one_or_none()
            
            if not discovery_record:
                return None
            
            # Convert database record to response model
            return DiscoveryResponse(
                task_id=discovery_record.discovery_id,
                status=discovery_record.status,
                message=discovery_record.message or "Discovery completed",
                url=discovery_record.url,
                services_found=discovery_record.services_found,
                services=discovery_record.services,
                processing_time=discovery_record.processing_time
            )
            
        except Exception as e:
            raise DiscoveryException(
                f"Failed to retrieve discovery result: {str(e)}",
                discovery_id=discovery_id
            )
    
    async def store_discovery_result(
        self, 
        discovery_id: str, 
        result: DiscoveryResult
    ) -> bool:
        """Store discovery results in database"""
        try:
            # Create discovery record
            discovery_record = DiscoveryResultModel(
                discovery_id=discovery_id,
                url=result.url,
                status=result.status.value,
                services_found=result.services_found,
                services=[service.dict() for service in result.services],
                additional_urls=result.additional_urls,
                processing_time=result.processing_time,
                error_message=result.error_message,
                page_relevance=result.page_relevance,
                depth=result.depth,
                discovered_at=datetime.utcnow()
            )
            
            self.db.add(discovery_record)
            
            # Store individual discovered services
            for service in result.services:
                await self._store_discovered_service(service, discovery_id)
            
            await self.db.commit()
            return True
            
        except Exception as e:
            await self.db.rollback()
            raise DiscoveryException(
                f"Failed to store discovery result: {str(e)}",
                discovery_id=discovery_id
            )
    
    async def _store_discovered_service(
        self, 
        service: DiscoveredService, 
        discovery_id: str
    ) -> bool:
        """Store a discovered service in the database"""
        try:
            # Check if service already exists
            existing_service = await self._find_similar_service(service)
            
            if existing_service:
                # Update existing service with new information
                await self._update_existing_service(existing_service.id, service)
            else:
                # Create new service
                service_record = ServiceModel(
                    id=str(uuid.uuid4()),
                    name=service.name,
                    description=service.description,
                    phone=service.phone,
                    email=service.email,
                    website=service.website,
                    address=service.address,
                    suburb=service.suburb or "Mount Isa",
                    postcode=service.postcode or "4825",
                    state=service.state or "QLD",
                    category=service.category or "general",
                    operating_hours=service.operating_hours,
                    services_offered=service.services_offered,
                    source_url=service.source_url,
                    extraction_method=service.extraction_method.value,
                    confidence_score=service.confidence_score,
                    discovery_id=discovery_id,
                    needs_validation=service.needs_validation,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                
                self.db.add(service_record)
            
            return True
            
        except Exception as e:
            raise DiscoveryException(
                f"Failed to store discovered service: {str(e)}",
                service_name=service.name
            )
    
    async def _find_similar_service(self, service: DiscoveredService) -> Optional[ServiceModel]:
        """Find similar existing service"""
        try:
            # Look for services with same name or phone number
            conditions = []
            
            if service.name:
                conditions.append(ServiceModel.name.ilike(f"%{service.name}%"))
            
            if service.phone:
                conditions.append(ServiceModel.phone == service.phone)
            
            if service.email:
                conditions.append(ServiceModel.email == service.email)
            
            if not conditions:
                return None
            
            stmt = select(ServiceModel).where(and_(*conditions))
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()
            
        except Exception as e:
            # If similarity check fails, assume no similar service
            return None
    
    async def _update_existing_service(
        self, 
        service_id: str, 
        new_service_data: DiscoveredService
    ) -> bool:
        """Update existing service with new discovery data"""
        try:
            stmt = select(ServiceModel).where(ServiceModel.id == service_id)
            result = await self.db.execute(stmt)
            existing_service = result.scalar_one_or_none()
            
            if not existing_service:
                return False
            
            # Update fields that are missing or have lower confidence
            if not existing_service.phone and new_service_data.phone:
                existing_service.phone = new_service_data.phone
            
            if not existing_service.email and new_service_data.email:
                existing_service.email = new_service_data.email
            
            if not existing_service.website and new_service_data.website:
                existing_service.website = new_service_data.website
            
            if not existing_service.address and new_service_data.address:
                existing_service.address = new_service_data.address
            
            if not existing_service.operating_hours and new_service_data.operating_hours:
                existing_service.operating_hours = new_service_data.operating_hours
            
            # Update confidence score if new discovery has higher confidence
            if new_service_data.confidence_score > existing_service.confidence_score:
                existing_service.confidence_score = new_service_data.confidence_score
                existing_service.extraction_method = new_service_data.extraction_method.value
            
            existing_service.updated_at = datetime.utcnow()
            
            await self.db.commit()
            return True
            
        except Exception as e:
            await self.db.rollback()
            raise DiscoveryException(
                f"Failed to update existing service: {str(e)}",
                service_id=service_id
            )
    
    async def get_discovery_metrics(
        self, 
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> DiscoveryMetrics:
        """Get discovery system metrics"""
        try:
            # Base query
            base_query = select(DiscoveryResultModel)
            
            # Add date filters if provided
            if start_date:
                base_query = base_query.where(DiscoveryResultModel.discovered_at >= start_date)
            if end_date:
                base_query = base_query.where(DiscoveryResultModel.discovered_at <= end_date)
            
            result = await self.db.execute(base_query)
            records = result.scalars().all()
            
            # Calculate metrics
            total_pages_processed = len(records)
            total_services_discovered = sum(r.services_found for r in records)
            total_extraction_failures = len([r for r in records if r.status == "failed"])
            
            # Calculate success rate
            successful_discoveries = len([r for r in records if r.status == "completed"])
            success_rate = successful_discoveries / total_pages_processed if total_pages_processed > 0 else 0.0
            
            # Calculate average services per page
            avg_services_per_page = total_services_discovered / total_pages_processed if total_pages_processed > 0 else 0.0
            
            # Calculate average processing time
            processing_times = [r.processing_time for r in records if r.processing_time]
            avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0.0
            
            return DiscoveryMetrics(
                total_pages_processed=total_pages_processed,
                total_services_discovered=total_services_discovered,
                total_extraction_failures=total_extraction_failures,
                success_rate=success_rate,
                avg_services_per_page=avg_services_per_page,
                avg_processing_time=avg_processing_time,
                pattern_match_rates={}  # Would be calculated from detailed pattern data
            )
            
        except Exception as e:
            raise DiscoveryException(f"Failed to calculate discovery metrics: {str(e)}")
    
    async def get_recent_discoveries(self, limit: int = 20) -> List[DiscoveredService]:
        """Get recently discovered services"""
        try:
            # Get recent services from discovery
            stmt = select(ServiceModel).where(
                ServiceModel.discovery_id.isnot(None)
            ).order_by(desc(ServiceModel.created_at)).limit(limit)
            
            result = await self.db.execute(stmt)
            records = result.scalars().all()
            
            recent_discoveries = []
            for record in records:
                recent_discoveries.append(DiscoveredService(
                    name=record.name,
                    description=record.description,
                    source_url=record.source_url,
                    extraction_method=record.extraction_method,
                    confidence_score=record.confidence_score,
                    phone=record.phone,
                    email=record.email,
                    website=record.website,
                    address=record.address,
                    suburb=record.suburb,
                    postcode=record.postcode,
                    state=record.state,
                    category=record.category,
                    operating_hours=record.operating_hours,
                    services_offered=record.services_offered,
                    discovered_at=record.created_at,
                    needs_validation=record.needs_validation
                ))
            
            return recent_discoveries
            
        except Exception as e:
            raise DiscoveryException(f"Failed to retrieve recent discoveries: {str(e)}")
    
    async def get_discovery_history(
        self, 
        url: Optional[str] = None,
        limit: int = 50
    ) -> List[DiscoveryHistory]:
        """Get discovery history"""
        try:
            base_query = select(DiscoveryResultModel)
            
            if url:
                base_query = base_query.where(DiscoveryResultModel.url == url)
            
            base_query = base_query.order_by(desc(DiscoveryResultModel.discovered_at)).limit(limit)
            
            result = await self.db.execute(base_query)
            records = result.scalars().all()
            
            history = []
            for record in records:
                history.append(DiscoveryHistory(
                    discovery_id=record.discovery_id,
                    url=record.url,
                    discovery_date=record.discovered_at,
                    services_found=record.services_found,
                    success=record.status == "completed",
                    processing_time=record.processing_time or 0.0,
                    agent_id=record.agent_id or "unknown"
                ))
            
            return history
            
        except Exception as e:
            raise DiscoveryException(f"Failed to retrieve discovery history: {str(e)}")
    
    async def get_urls_needing_discovery(self, limit: int = 100) -> List[str]:
        """Get URLs that need discovery or re-discovery"""
        try:
            # Find URLs that haven't been processed recently
            cutoff_date = datetime.utcnow() - timedelta(days=30)
            
            # This would typically query a URLs table or similar
            # For now, return empty list as placeholder
            return []
            
        except Exception as e:
            raise DiscoveryException(f"Failed to find URLs needing discovery: {str(e)}")
    
    async def mark_url_processed(self, url: str, discovery_id: str) -> bool:
        """Mark a URL as processed"""
        try:
            # Update URL processing status
            # This would typically update a URLs table
            return True
            
        except Exception as e:
            raise DiscoveryException(
                f"Failed to mark URL as processed: {str(e)}",
                url=url
            )
    
    async def get_failed_discoveries(self, limit: int = 50) -> List[DiscoveryHistory]:
        """Get failed discovery attempts"""
        try:
            stmt = select(DiscoveryResultModel).where(
                DiscoveryResultModel.status == "failed"
            ).order_by(desc(DiscoveryResultModel.discovered_at)).limit(limit)
            
            result = await self.db.execute(stmt)
            records = result.scalars().all()
            
            failed_discoveries = []
            for record in records:
                failed_discoveries.append(DiscoveryHistory(
                    discovery_id=record.discovery_id,
                    url=record.url,
                    discovery_date=record.discovered_at,
                    services_found=record.services_found,
                    success=False,
                    processing_time=record.processing_time or 0.0,
                    agent_id=record.agent_id or "unknown"
                ))
            
            return failed_discoveries
            
        except Exception as e:
            raise DiscoveryException(f"Failed to retrieve failed discoveries: {str(e)}")
    
    async def create_crawl_result(
        self, 
        crawl_id: str, 
        start_url: str,
        discovered_services: List[DiscoveredService]
    ) -> CrawlResult:
        """Create a crawl result summary"""
        try:
            total_services_found = len(discovered_services)
            
            crawl_result = CrawlResult(
                crawl_id=crawl_id,
                start_url=start_url,
                total_pages_crawled=1,  # Would be calculated from actual crawl data
                total_services_found=total_services_found,
                crawl_depth_reached=2,  # Would be calculated from actual crawl data
                crawl_duration=0.0,  # Would be calculated from actual crawl time
                status="completed",
                discovered_services=discovered_services,
                failed_urls=[],
                started_at=datetime.utcnow()
            )
            
            return crawl_result
            
        except Exception as e:
            raise DiscoveryException(f"Failed to create crawl result: {str(e)}")
    
    async def queue_discovery_task(
        self, 
        url: str, 
        priority: int = 5,
        max_depth: int = 2
    ) -> str:
        """Queue a discovery task"""
        queue_id = str(uuid.uuid4())
        
        # In a real implementation, this would add to a proper queue system
        # For now, we'll return the queue ID
        
        return queue_id
    
    async def get_discovery_queue_status(self) -> Dict[str, Any]:
        """Get current discovery queue status"""
        # In a real implementation, this would query the actual queue
        return {
            "pending_discoveries": 0,
            "active_discoveries": 0,
            "completed_today": 0,
            "average_wait_time": 0.0
        }