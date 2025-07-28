"""
Research Service - Orchestrates intelligent discovery of Mount Isa services
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from app.agents.research import MountIsaResearchAgent, SearchQuery
from app.agents.base import create_agent_task
from app.core.exceptions import ResearchException
from app.core.logging import get_logger

logger = get_logger(__name__)


class ResearchOrchestrator:
    """Orchestrates intelligent research and discovery of Mount Isa services"""
    
    def __init__(self, db_session: Optional[AsyncSession] = None):
        self.db = db_session
        self.research_agents = {}
        self.active_research_tasks = {}
        
        # Research configuration
        self.config = {
            'max_concurrent_research': 3,
            'research_cooldown_hours': 24,
            'max_sites_per_session': 50,
            'max_services_per_session': 200,
            'quality_threshold': 0.6
        }
    
    async def start_intelligent_research(
        self, 
        research_type: str = "comprehensive",
        target_service_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Start intelligent research to discover Mount Isa services"""
        
        research_id = str(uuid.uuid4())
        
        logger.info(f"Starting intelligent research session {research_id}")
        
        try:
            # Create research agent
            agent_id = f"research_agent_{research_id[:8]}"
            research_agent = MountIsaResearchAgent(
                agent_id=agent_id,
                config={
                    'timeout': 60,
                    'max_concurrent_tasks': 1,
                    'request_delay': 2.0
                }
            )
            
            self.research_agents[agent_id] = research_agent
            
            # Create research task
            task_payload = {
                'research_type': research_type,
                'target_service_types': target_service_types or [],
                'max_queries': 100 if research_type == "comprehensive" else 30,
                'quality_threshold': self.config['quality_threshold']
            }
            
            research_task = await create_agent_task(
                task_type="research_services",
                payload=task_payload,
                priority=0.8  # High priority
            )
            
            # Execute research
            logger.info(f"Executing research task for {research_type} discovery")
            
            result = await research_agent.execute_task(research_task)
            
            # Process and store results
            processed_result = await self._process_research_results(research_id, result, research_agent)
            
            # Clean up
            if agent_id in self.research_agents:
                del self.research_agents[agent_id]
            
            logger.info(
                f"Research session {research_id} completed: "
                f"{processed_result.get('services_discovered', 0)} services found"
            )
            
            return {
                'research_id': research_id,
                'status': 'completed',
                'research_type': research_type,
                **processed_result
            }
            
        except Exception as e:
            logger.error(f"Research session {research_id} failed: {e}")
            
            # Clean up failed agent
            if agent_id in self.research_agents:
                del self.research_agents[agent_id]
            
            return {
                'research_id': research_id,
                'status': 'failed',
                'error': str(e),
                'research_type': research_type
            }
    
    async def _process_research_results(
        self, 
        research_id: str, 
        raw_result: Dict[str, Any],
        research_agent: MountIsaResearchAgent
    ) -> Dict[str, Any]:
        """Process and analyze research results"""
        
        if raw_result.get('status') != 'completed':
            return {
                'services_discovered': 0,
                'high_quality_services': 0,
                'sites_researched': 0,
                'processing_error': raw_result.get('error', 'Unknown error')
            }
        
        extracted_services = raw_result.get('extracted_services', [])
        discovered_sites = raw_result.get('discovered_sites', [])
        
        # Filter high-quality services
        high_quality_services = [
            service for service in extracted_services
            if service.get('confidence_score', 0) >= self.config['quality_threshold']
        ]
        
        # Categorize services by type
        service_categories = {}
        for service in high_quality_services:
            category = service.get('category', 'unknown')
            if category not in service_categories:
                service_categories[category] = []
            service_categories[category].append(service)
        
        # Generate research insights
        insights = self._generate_research_insights(
            extracted_services, 
            discovered_sites, 
            research_agent.get_research_statistics()
        )
        
        # Store results for future reference
        await self._store_research_results(research_id, {
            'total_services': len(extracted_services),
            'high_quality_services': high_quality_services,
            'service_categories': service_categories,
            'discovered_sites': discovered_sites,
            'insights': insights,
            'timestamp': datetime.utcnow().isoformat()
        })
        
        return {
            'services_discovered': len(extracted_services),
            'high_quality_services': len(high_quality_services),
            'sites_researched': len(discovered_sites),
            'service_categories': {k: len(v) for k, v in service_categories.items()},
            'insights': insights,
            'processing_time': raw_result.get('processing_time', 0),
            'detailed_services': high_quality_services[:20],  # Return top 20 for review
            'research_statistics': research_agent.get_research_statistics()
        }
    
    def _generate_research_insights(
        self, 
        services: List[Dict[str, Any]], 
        sites: List[Dict[str, Any]],
        stats: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate insights from research results"""
        
        insights = {
            'service_coverage': {},
            'data_quality': {},
            'discovery_effectiveness': {},
            'recommendations': []
        }
        
        # Service coverage analysis
        total_services = len(services)
        if total_services > 0:
            # Analyze service distribution
            categories = {}
            contact_completeness = 0
            location_completeness = 0
            
            for service in services:
                category = service.get('category', 'unknown')
                categories[category] = categories.get(category, 0) + 1
                
                if service.get('phone') or service.get('email'):
                    contact_completeness += 1
                
                if service.get('address') or service.get('suburb'):
                    location_completeness += 1
            
            insights['service_coverage'] = {
                'total_services': total_services,
                'categories_found': len(categories),
                'category_distribution': categories,
                'contact_info_rate': contact_completeness / total_services,
                'location_info_rate': location_completeness / total_services
            }
        
        # Data quality analysis
        high_confidence_services = [s for s in services if s.get('confidence_score', 0) > 0.8]
        medium_confidence_services = [s for s in services if 0.5 <= s.get('confidence_score', 0) <= 0.8]
        
        insights['data_quality'] = {
            'high_confidence_count': len(high_confidence_services),
            'medium_confidence_count': len(medium_confidence_services),
            'low_confidence_count': total_services - len(high_confidence_services) - len(medium_confidence_services),
            'average_confidence': sum(s.get('confidence_score', 0) for s in services) / max(1, total_services)
        }
        
        # Discovery effectiveness
        insights['discovery_effectiveness'] = {
            'sites_discovered': len(sites),
            'services_per_site': total_services / max(1, len(sites)),
            'search_efficiency': stats.get('avg_sites_per_search', 0),
            'extraction_success_rate': stats.get('avg_services_per_site', 0)
        }
        
        # Generate recommendations
        recommendations = []
        
        if insights['data_quality']['average_confidence'] < 0.7:
            recommendations.append("Consider refining search queries for higher quality results")
        
        if insights['service_coverage']['contact_info_rate'] < 0.6:
            recommendations.append("Focus on sources with better contact information")
        
        if len(categories) < 5:
            recommendations.append("Expand search to cover more service categories")
        
        if insights['discovery_effectiveness']['services_per_site'] < 0.5:
            recommendations.append("Target more service-rich websites")
        
        insights['recommendations'] = recommendations
        
        return insights
    
    async def _store_research_results(self, research_id: str, results: Dict[str, Any]) -> bool:
        """Store research results for future reference"""
        
        try:
            # In a real implementation, this would store in database
            # For now, we'll log the results
            logger.info(f"Research {research_id} results: {json.dumps(results, indent=2, default=str)}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store research results for {research_id}: {e}")
            return False
    
    async def get_research_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get history of research sessions"""
        
        # In a real implementation, this would query the database
        # For now, return placeholder data
        return [
            {
                'research_id': 'research_001',
                'timestamp': (datetime.utcnow() - timedelta(hours=2)).isoformat(),
                'research_type': 'comprehensive',
                'services_discovered': 47,
                'high_quality_services': 32,
                'status': 'completed'
            },
            {
                'research_id': 'research_002',
                'timestamp': (datetime.utcnow() - timedelta(hours=6)).isoformat(),
                'research_type': 'health_focused',
                'services_discovered': 23,
                'high_quality_services': 18,
                'status': 'completed'
            }
        ]
    
    async def start_targeted_research(self, service_types: List[str]) -> Dict[str, Any]:
        """Start research focused on specific service types"""
        
        logger.info(f"Starting targeted research for: {', '.join(service_types)}")
        
        return await self.start_intelligent_research(
            research_type="targeted",
            target_service_types=service_types
        )
    
    async def start_continuous_research(self) -> Dict[str, Any]:
        """Start continuous background research"""
        
        logger.info("Starting continuous research mode")
        
        # This would typically run as a background task
        research_results = []
        
        # Stagger research across different service types
        service_batches = [
            ['health', 'mental_health'],
            ['disability', 'aged_care'],
            ['youth', 'family'],
            ['housing', 'employment'],
            ['legal', 'emergency', 'community']
        ]
        
        for batch in service_batches:
            try:
                result = await self.start_targeted_research(batch)
                research_results.append(result)
                
                # Wait between batches to avoid overwhelming servers
                await asyncio.sleep(300)  # 5 minutes
                
            except Exception as e:
                logger.error(f"Batch research failed for {batch}: {e}")
                continue
        
        return {
            'continuous_research_id': str(uuid.uuid4()),
            'status': 'completed',
            'batches_processed': len(research_results),
            'total_services_discovered': sum(r.get('services_discovered', 0) for r in research_results),
            'batch_results': research_results
        }
    
    async def get_research_status(self) -> Dict[str, Any]:
        """Get current research system status"""
        
        return {
            'active_agents': len(self.research_agents),
            'active_tasks': len(self.active_research_tasks),
            'system_status': 'operational',
            'last_research': 'Available on demand',
            'capabilities': [
                'Intelligent search engine discovery',
                'Multi-engine search (Google, Bing)',
                'Mount Isa specific targeting',
                'Service quality assessment',
                'Automated extraction and validation',
                'Continuous background research'
            ]
        }