"""
Discovery API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
from uuid import UUID
import json

from app.core.database import get_async_session
from app.models.discovery import (
    DiscoveryRequest, DiscoveryResponse, DiscoveryResult,
    DiscoveryBatchRequest, DiscoveryBatchResponse, DiscoveryTask
)
from app.services.discovery_service import DiscoveryService
from app.agents.discovery import DiscoveryAgent
from app.agents.base import create_agent_task, submit_task_to_queue
from app.models.agent import AgentType
from app.core.config import settings
import redis.asyncio as redis

router = APIRouter()


@router.post("/url", response_model=DiscoveryResponse)
async def discover_services_from_url(
    discovery_request: DiscoveryRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_async_session)
):
    """Discover services from a specific URL"""
    discovery_service = DiscoveryService(db)
    
    try:
        # Submit discovery task to queue
        redis_client = redis.from_url(settings.REDIS_URL)
        
        task = await create_agent_task(
            task_type="discover_url",
            payload={
                "url": discovery_request.url,
                "max_depth": discovery_request.max_depth,
                "current_depth": 0,
                "discovery_options": discovery_request.options.__dict__ if discovery_request.options else {}
            }
        )
        
        await submit_task_to_queue(AgentType.DISCOVERY, task, redis_client)
        await redis_client.close()
        
        return DiscoveryResponse(
            task_id=task.task_id,
            status="queued",
            message="Discovery task submitted for processing",
            url=discovery_request.url
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to submit discovery task: {str(e)}"
        )


@router.get("/url/{task_id}", response_model=DiscoveryResponse)
async def get_discovery_result(
    task_id: str,
    db: AsyncSession = Depends(get_async_session)
):
    """Get discovery result by task ID"""
    try:
        redis_client = redis.from_url(settings.REDIS_URL)
        
        # Check if task result exists
        result_data = await redis_client.get(f"task_result:{task_id}")
        
        if not result_data:
            return DiscoveryResponse(
                task_id=task_id,
                status="processing",
                message="Discovery still in progress"
            )
        
        # Parse result data
        result_dict = json.loads(result_data.decode() if isinstance(result_data, bytes) else result_data)
        
        await redis_client.close()
        
        if result_dict['status'] == 'completed':
            discovery_result = result_dict['result']
            
            return DiscoveryResponse(
                task_id=task_id,
                status="completed",
                message="Discovery completed successfully",
                url=discovery_result.get('url'),
                services_found=discovery_result.get('services_found', 0),
                services=discovery_result.get('services', []),
                additional_urls=discovery_result.get('additional_urls', []),
                processing_time=result_dict.get('processing_time')
            )
        else:
            return DiscoveryResponse(
                task_id=task_id,
                status="failed",
                message=f"Discovery failed: {result_dict.get('error_message', 'Unknown error')}",
                processing_time=result_dict.get('processing_time')
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve discovery result: {str(e)}"
        )


@router.post("/batch", response_model=DiscoveryBatchResponse)
async def discover_services_batch(
    batch_request: DiscoveryBatchRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_async_session)
):
    """Discover services from multiple URLs in batch"""
    discovery_service = DiscoveryService(db)
    
    if len(batch_request.urls) > 50:
        raise HTTPException(
            status_code=400,
            detail="Batch size cannot exceed 50 URLs"
        )
    
    try:
        redis_client = redis.from_url(settings.REDIS_URL)
        task_ids = []
        
        # Submit each URL for discovery
        for url in batch_request.urls:
            task = await create_agent_task(
                task_type="discover_url",
                payload={
                    "url": url,
                    "max_depth": batch_request.max_depth,
                    "current_depth": 0,
                    "discovery_options": batch_request.options.__dict__ if batch_request.options else {}
                }
            )
            
            await submit_task_to_queue(AgentType.DISCOVERY, task, redis_client)
            task_ids.append(task.task_id)
        
        await redis_client.close()
        
        return DiscoveryBatchResponse(
            batch_id=f"batch_{len(task_ids)}_{task_ids[0][:8]}",
            task_ids=task_ids,
            status="queued",
            total_urls=len(batch_request.urls)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to submit batch discovery: {str(e)}"
        )


@router.get("/batch/{batch_id}/status")
async def get_batch_discovery_status(
    batch_id: str,
    db: AsyncSession = Depends(get_async_session)
):
    """Get status of batch discovery"""
    try:
        # In a full implementation, this would track batch progress
        return {
            "message": "Use individual task IDs to check discovery status",
            "batch_id": batch_id
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get batch status: {str(e)}"
        )


@router.post("/extract", response_model=DiscoveryResponse)
async def extract_service_from_content(
    content_data: Dict[str, Any],
    background_tasks: BackgroundTasks
):
    """Extract service information from provided content"""
    try:
        redis_client = redis.from_url(settings.REDIS_URL)
        
        task = await create_agent_task(
            task_type="extract_service",
            payload={
                "content": content_data.get("content", ""),
                "url": content_data.get("url", ""),
                "content_type": content_data.get("content_type", "html")
            }
        )
        
        await submit_task_to_queue(AgentType.DISCOVERY, task, redis_client)
        await redis_client.close()
        
        return DiscoveryResponse(
            task_id=task.task_id,
            status="queued",
            message="Service extraction task submitted"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to extract service from content: {str(e)}"
        )


@router.get("/patterns/list")
async def get_discovery_patterns():
    """Get list of discovery patterns used by agents"""
    # Create temporary discovery agent to get patterns
    temp_agent = DiscoveryAgent("temp", {})
    
    patterns_info = {
        'contact_patterns': {
            'phone': [
                {
                    'name': pattern.name,
                    'pattern': pattern.pattern,
                    'confidence': pattern.confidence,
                    'examples': pattern.examples
                }
                for pattern in temp_agent.pattern_library.patterns['contact']['phone']
            ],
            'email': [
                {
                    'name': pattern.name,
                    'pattern': pattern.pattern,
                    'confidence': pattern.confidence,
                    'examples': pattern.examples
                }
                for pattern in temp_agent.pattern_library.patterns['contact']['email']
            ],
            'website': [
                {
                    'name': pattern.name,
                    'pattern': pattern.pattern,
                    'confidence': pattern.confidence,
                    'examples': pattern.examples
                }
                for pattern in temp_agent.pattern_library.patterns['contact']['website']
            ]
        },
        'location_patterns': {
            'address': [
                {
                    'name': pattern.name,
                    'pattern': pattern.pattern,
                    'confidence': pattern.confidence,
                    'examples': pattern.examples
                }
                for pattern in temp_agent.pattern_library.patterns['location']['address']
            ],
            'postcode': [
                {
                    'name': pattern.name,
                    'pattern': pattern.pattern,
                    'confidence': pattern.confidence,
                    'examples': pattern.examples
                }
                for pattern in temp_agent.pattern_library.patterns['location']['postcode']
            ]
        },
        'service_categories': temp_agent.pattern_library.category_keywords
    }
    
    return patterns_info


@router.get("/stats/performance")
async def get_discovery_performance():
    """Get discovery system performance statistics"""
    try:
        redis_client = redis.from_url(settings.REDIS_URL)
        
        # Get all discovery agents
        discovery_agents = await redis_client.smembers("agents:type:discovery")
        
        total_stats = {
            'pages_processed': 0,
            'services_discovered': 0,
            'extraction_failures': 0,
            'success_rate': 0.0,
            'active_agents': len(discovery_agents),
            'avg_services_per_page': 0.0
        }
        
        # Aggregate stats from all agents (simplified implementation)
        # In a real system, this would query actual agent statistics
        
        await redis_client.close()
        
        return total_stats
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get performance stats: {str(e)}"
        )


@router.post("/test/extraction")
async def test_service_extraction(
    test_data: Dict[str, Any]
):
    """Test service extraction on provided content"""
    content = test_data.get('content')
    url = test_data.get('url', 'test-url')
    
    if not content:
        raise HTTPException(
            status_code=400,
            detail="Content is required for testing"
        )
    
    try:
        # Create temporary discovery agent
        temp_agent = DiscoveryAgent("temp", {})
        
        # Extract services from content
        services = await temp_agent._extract_services_from_content(content, url)
        
        # Calculate page relevance
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(content, 'html.parser')
        text_content = soup.get_text().lower()
        relevance_score = temp_agent._calculate_page_relevance(text_content)
        
        return {
            'url': url,
            'relevance_score': relevance_score,
            'services_found': len(services),
            'services': services,
            'extraction_method': 'test'
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Extraction test failed: {str(e)}"
        )


@router.get("/queue/status")
async def get_discovery_queue_status():
    """Get current discovery queue status"""
    try:
        redis_client = redis.from_url(settings.REDIS_URL)
        
        # Get queue length
        queue_length = await redis_client.llen("tasks:discovery")
        
        # Get active agents
        active_agents = await redis_client.smembers("agents:type:discovery")
        
        await redis_client.close()
        
        return {
            'pending_tasks': queue_length,
            'active_agents': len(active_agents),
            'estimated_wait_time': queue_length * 30 if queue_length > 0 else 0  # Rough estimate
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get queue status: {str(e)}"
        )


@router.post("/crawl")
async def start_website_crawl(
    crawl_request: Dict[str, Any],
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_async_session)
):
    """Start a comprehensive website crawl for service discovery"""
    start_url = crawl_request.get('start_url')
    max_pages = crawl_request.get('max_pages', 10)
    max_depth = crawl_request.get('max_depth', 2)
    
    if not start_url:
        raise HTTPException(
            status_code=400,
            detail="start_url is required"
        )
    
    if max_pages > 100:
        raise HTTPException(
            status_code=400,
            detail="max_pages cannot exceed 100"
        )
    
    try:
        redis_client = redis.from_url(settings.REDIS_URL)
        
        # Create crawl task
        task = await create_agent_task(
            task_type="discover_url",
            payload={
                "url": start_url,
                "max_depth": max_depth,
                "current_depth": 0,
                "max_pages": max_pages,
                "crawl_mode": True
            }
        )
        
        await submit_task_to_queue(AgentType.DISCOVERY, task, redis_client)
        await redis_client.close()
        
        return {
            'crawl_id': task.task_id,
            'status': 'started',
            'start_url': start_url,
            'max_pages': max_pages,
            'max_depth': max_depth,
            'message': 'Website crawl started'
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start website crawl: {str(e)}"
        )


@router.get("/recent")
async def get_recent_discoveries(
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_async_session)
):
    """Get recently discovered services"""
    discovery_service = DiscoveryService(db)
    
    try:
        recent_discoveries = await discovery_service.get_recent_discoveries(limit)
        return {
            'recent_discoveries': recent_discoveries,
            'total_count': len(recent_discoveries)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get recent discoveries: {str(e)}"
        )