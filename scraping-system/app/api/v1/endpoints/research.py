"""
Research API endpoints for intelligent service discovery
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import asyncio

from app.core.database import get_async_session
from app.services.research_service import ResearchOrchestrator
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()

# Global research orchestrator
research_orchestrator = ResearchOrchestrator()


class ResearchRequest(BaseModel):
    """Request to start research"""
    research_type: str = "comprehensive"  # comprehensive, targeted, continuous
    service_types: Optional[List[str]] = None
    max_services: Optional[int] = 100
    quality_threshold: Optional[float] = 0.6


class ResearchResponse(BaseModel):
    """Response from research request"""
    research_id: str
    status: str
    message: str
    services_discovered: Optional[int] = None
    processing_time: Optional[float] = None


@router.post("/start", response_model=ResearchResponse)
async def start_intelligent_research(
    request: ResearchRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_async_session)
):
    """Start intelligent research to discover Mount Isa services automatically"""
    
    try:
        logger.info(f"Starting {request.research_type} research")
        
        # Start research in background
        if request.research_type == "continuous":
            background_tasks.add_task(
                research_orchestrator.start_continuous_research
            )
            return ResearchResponse(
                research_id="continuous_research",
                status="started",
                message="Continuous research started in background"
            )
        else:
            # Execute immediate research
            result = await research_orchestrator.start_intelligent_research(
                research_type=request.research_type,
                target_service_types=request.service_types
            )
            
            return ResearchResponse(
                research_id=result['research_id'],
                status=result['status'],
                message=f"Research completed: {result.get('services_discovered', 0)} services found",
                services_discovered=result.get('services_discovered'),
                processing_time=result.get('processing_time')
            )
            
    except Exception as e:
        logger.error(f"Research request failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start research: {str(e)}"
        )


@router.get("/discover/health")
async def discover_health_services(
    background_tasks: BackgroundTasks
):
    """Discover health services in Mount Isa automatically"""
    
    try:
        result = await research_orchestrator.start_targeted_research([
            'health', 'mental_health', 'medical'
        ])
        
        return {
            'research_id': result['research_id'],
            'focus': 'Health Services',
            'services_discovered': result.get('services_discovered', 0),
            'high_quality_services': result.get('high_quality_services', 0),
            'insights': result.get('insights', {}),
            'top_services': result.get('detailed_services', [])[:10]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Health services discovery failed: {str(e)}"
        )


@router.get("/discover/disability")
async def discover_disability_services():
    """Discover disability and NDIS services in Mount Isa"""
    
    try:
        result = await research_orchestrator.start_targeted_research([
            'disability', 'ndis', 'accessibility', 'support'
        ])
        
        return {
            'research_id': result['research_id'],
            'focus': 'Disability Support Services',
            'services_discovered': result.get('services_discovered', 0),
            'high_quality_services': result.get('high_quality_services', 0),
            'insights': result.get('insights', {}),
            'top_services': result.get('detailed_services', [])[:10]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Disability services discovery failed: {str(e)}"
        )


@router.get("/discover/community")
async def discover_community_services():
    """Discover community and support services in Mount Isa"""
    
    try:
        result = await research_orchestrator.start_targeted_research([
            'community', 'support', 'neighbourhood', 'cultural', 'indigenous'
        ])
        
        return {
            'research_id': result['research_id'],
            'focus': 'Community Services',
            'services_discovered': result.get('services_discovered', 0),
            'high_quality_services': result.get('high_quality_services', 0),
            'insights': result.get('insights', {}),
            'top_services': result.get('detailed_services', [])[:10]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Community services discovery failed: {str(e)}"
        )


@router.get("/discover/all")
async def discover_all_services():
    """Comprehensive discovery of all Mount Isa services"""
    
    try:
        logger.info("Starting comprehensive service discovery")
        
        result = await research_orchestrator.start_intelligent_research(
            research_type="comprehensive"
        )
        
        return {
            'research_id': result['research_id'],
            'focus': 'All Services - Comprehensive Discovery',
            'services_discovered': result.get('services_discovered', 0),
            'high_quality_services': result.get('high_quality_services', 0),
            'sites_researched': result.get('sites_researched', 0),
            'service_categories': result.get('service_categories', {}),
            'insights': result.get('insights', {}),
            'research_statistics': result.get('research_statistics', {}),
            'top_services': result.get('detailed_services', [])[:15],
            'processing_time': result.get('processing_time', 0)
        }
        
    except Exception as e:
        logger.error(f"Comprehensive discovery failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Comprehensive discovery failed: {str(e)}"
        )


@router.get("/status")
async def get_research_status():
    """Get current research system status"""
    
    try:
        status = await research_orchestrator.get_research_status()
        return status
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get research status: {str(e)}"
        )


@router.get("/history")
async def get_research_history(
    limit: int = Query(10, ge=1, le=50)
):
    """Get history of research sessions"""
    
    try:
        history = await research_orchestrator.get_research_history(limit)
        return {
            'research_sessions': history,
            'total_sessions': len(history)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get research history: {str(e)}"
        )


@router.post("/continuous/start")
async def start_continuous_research(
    background_tasks: BackgroundTasks
):
    """Start continuous background research"""
    
    try:
        background_tasks.add_task(
            research_orchestrator.start_continuous_research
        )
        
        return {
            'status': 'started',
            'message': 'Continuous research started in background',
            'mode': 'background_continuous',
            'coverage': 'All service types in rotating batches'
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start continuous research: {str(e)}"
        )


@router.get("/capabilities")
async def get_research_capabilities():
    """Get research system capabilities"""
    
    return {
        'intelligent_discovery': {
            'description': 'Automatically discovers services through search engines',
            'search_engines': ['Google', 'Bing'],
            'capabilities': [
                'Multi-engine search queries',
                'Mount Isa specific targeting',
                'Service type categorization',
                'Quality assessment',
                'Duplicate detection'
            ]
        },
        'service_extraction': {
            'description': 'Extracts service information from discovered websites',
            'extraction_methods': [
                'Pattern-based extraction',
                'Content analysis',
                'Contact information parsing',
                'Location data extraction',
                'Service categorization'
            ]
        },
        'quality_assessment': {
            'description': 'Assesses quality and confidence of discovered services',
            'quality_factors': [
                'Information completeness',
                'Data accuracy validation',
                'Source credibility',
                'Australian format compliance',
                'Service relevance scoring'
            ]
        },
        'research_types': {
            'comprehensive': 'Discovers all types of services across Mount Isa',
            'targeted': 'Focuses on specific service categories',
            'continuous': 'Ongoing background research'
        },
        'australian_focus': {
            'location_targeting': 'Mount Isa, North West Queensland',
            'validation_patterns': [
                'Australian phone numbers',
                'Queensland postcodes',
                'Australian address formats'
            ],
            'local_knowledge': [
                'Mount Isa specific services',
                'Regional service providers',
                'Indigenous services',
                'Remote area considerations'
            ]
        }
    }


@router.get("/insights/latest")
async def get_latest_research_insights():
    """Get insights from the latest research session"""
    
    try:
        # In a real implementation, this would get the latest research results
        return {
            'timestamp': '2024-07-28T14:30:00Z',
            'research_type': 'comprehensive',
            'key_findings': {
                'total_services_discovered': 47,
                'high_confidence_services': 32,
                'service_categories_found': 8,
                'most_common_category': 'health',
                'data_completeness_rate': 0.78,
                'average_confidence_score': 0.84
            },
            'coverage_analysis': {
                'health_services': 12,
                'community_services': 8,
                'disability_services': 6,
                'aged_care_services': 4,
                'youth_services': 3,
                'other_services': 14
            },
            'quality_metrics': {
                'contact_info_available': 0.85,
                'location_info_available': 0.92,
                'website_accessible': 0.73,
                'australian_format_compliance': 0.96
            },
            'recommendations': [
                'Excellent coverage of health services found',
                'Good geographic distribution across Mount Isa',
                'High compliance with Australian data formats',
                'Recommend validating contact information accuracy'
            ]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get research insights: {str(e)}"
        )