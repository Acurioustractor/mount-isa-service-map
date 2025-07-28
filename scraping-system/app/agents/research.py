"""
Intelligent Research Agent - Automatically discovers Mount Isa service websites
through search engines and then scrapes them for information
"""

import asyncio
import aiohttp
import json
import re
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from urllib.parse import urljoin, urlparse, quote_plus
from dataclasses import dataclass
import random

from bs4 import BeautifulSoup
from app.agents.base import BaseAgent
from app.models.agent import AgentType, AgentTask
from app.core.exceptions import ResearchException


@dataclass
class SearchQuery:
    """A search query for finding services"""
    keywords: List[str]
    service_type: str
    location: str
    priority: int = 5
    max_results: int = 20


@dataclass
class ResearchTarget:
    """A discovered website to research"""
    url: str
    title: str
    snippet: str
    relevance_score: float
    source_query: str
    discovered_at: datetime


class MountIsaResearchAgent(BaseAgent):
    """Intelligent agent that researches Mount Isa services automatically"""
    
    def __init__(self, agent_id: str, config: Optional[Dict[str, Any]] = None, **kwargs):
        super().__init__(agent_id, AgentType.DISCOVERY, config, **kwargs)
        
        # Research configuration
        self.search_engines = [
            "https://www.google.com/search",
            "https://www.bing.com/search", 
            "https://duckduckgo.com/html"
        ]
        
        # Mount Isa specific search terms
        self.mount_isa_service_queries = self._build_search_queries()
        
        # Domain filters for Mount Isa area
        self.relevant_domains = [
            "mountisa.qld.gov.au",
            "health.qld.gov.au", 
            "communities.qld.gov.au",
            "ndis.gov.au",
            "centrelink.gov.au",
            "redcross.org.au",
            "salvationarmy.org.au",
            "beyondblue.org.au",
            "lifeline.org.au",
            "headspace.org.au"
        ]
        
        # User agents for web scraping
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0"
        ]
        
        # Research statistics
        self.research_stats = {
            'searches_performed': 0,
            'websites_discovered': 0,
            'services_extracted': 0,
            'failed_extractions': 0,
            'research_time_total': 0.0
        }
    
    def _build_search_queries(self) -> List[SearchQuery]:
        """Build comprehensive search queries for Mount Isa services"""
        
        service_categories = {
            'health': [
                'medical centre', 'doctor', 'GP', 'clinic', 'hospital', 'pharmacy',
                'mental health', 'psychology', 'counselling', 'therapy'
            ],
            'disability': [
                'disability support', 'NDIS', 'accessible services', 'special needs',
                'inclusion', 'disability advocacy', 'support workers'
            ],
            'aged_care': [
                'aged care', 'elderly support', 'seniors services', 'retirement',
                'home care', 'respite care', 'aged accommodation'
            ],
            'youth': [
                'youth services', 'young people', 'teenagers', 'youth centre',
                'youth support', 'adolescent services', 'teen programs'
            ],
            'family': [
                'family services', 'childcare', 'parenting support', 'child protection',
                'family counselling', 'playgroups', 'early childhood'
            ],
            'housing': [
                'housing services', 'accommodation', 'rental assistance', 'homeless support',
                'emergency accommodation', 'public housing'
            ],
            'employment': [
                'employment services', 'job centre', 'career support', 'training',
                'apprenticeships', 'job search', 'employment agency'
            ],
            'legal': [
                'legal aid', 'community legal centre', 'legal advice', 'court support',
                'family law', 'tenancy advice', 'consumer rights'
            ],
            'emergency': [
                'emergency services', 'crisis support', 'domestic violence',
                'suicide prevention', 'helpline', '24 hour support'
            ],
            'community': [
                'community centre', 'neighbourhood centre', 'community services',
                'volunteer services', 'community support', 'cultural services'
            ]
        }
        
        locations = [
            'Mount Isa', 'Mount Isa Queensland', 'Mount Isa QLD',
            'North West Queensland', 'Gulf Country', 'Cloncurry',
            'Camooweal', 'Dajarra', '4825'
        ]
        
        queries = []
        
        for category, terms in service_categories.items():
            for term in terms:
                for location in locations[:3]:  # Use top 3 locations to avoid too many queries
                    queries.append(SearchQuery(
                        keywords=[term, location],
                        service_type=category,
                        location=location,
                        priority=1 if location == 'Mount Isa' else 2,
                        max_results=15
                    ))
        
        # Add specific Mount Isa service searches
        specific_searches = [
            ['Mount Isa Hospital'],
            ['Mount Isa Community Health'],
            ['Mount Isa Neighbourhood Centre'],
            ['Gidgee Healing'],
            ['Kalkadoon Community Centre'],
            ['Mount Isa PCYC'],
            ['Salvation Army Mount Isa'],
            ['Red Cross Mount Isa'],
            ['Centrelink Mount Isa'],
            ['Mount Isa City Council services'],
            ['NAIDOC Mt Isa'],
            ['Indigenous services Mount Isa'],
            ['Mount Isa youth services'],
            ['Mount Isa aged care'],
            ['Mount Isa disability services']
        ]
        
        for keywords in specific_searches:
            queries.append(SearchQuery(
                keywords=keywords,
                service_type='specific',
                location='Mount Isa',
                priority=1,
                max_results=10
            ))
        
        return queries
    
    async def execute_task(self, task: AgentTask) -> Dict[str, Any]:
        """Execute research task"""
        task_type = task.task_type
        payload = task.payload
        
        if task_type == "research_services":
            return await self._research_mount_isa_services(payload)
        elif task_type == "deep_search":
            return await self._perform_deep_search(payload)
        elif task_type == "extract_from_discovered":
            return await self._extract_from_discovered_sites(payload)
        else:
            raise ResearchException(f"Unknown research task type: {task_type}")
    
    async def _research_mount_isa_services(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Main research function - discovers and extracts Mount Isa services"""
        
        start_time = datetime.utcnow()
        max_queries = payload.get('max_queries', 50)
        discovered_sites = []
        extracted_services = []
        
        self.logger.info(f"Starting comprehensive Mount Isa services research with {max_queries} queries")
        
        try:
            # Phase 1: Discover relevant websites
            priority_queries = sorted(self.mount_isa_service_queries, key=lambda x: x.priority)[:max_queries]
            
            for query in priority_queries:
                try:
                    self.logger.info(f"Searching: {' '.join(query.keywords)}")
                    
                    search_results = await self._perform_search(query)
                    discovered_sites.extend(search_results)
                    
                    # Add delay to avoid rate limiting
                    await asyncio.sleep(random.uniform(2, 5))
                    
                except Exception as e:
                    self.logger.error(f"Search failed for {query.keywords}: {e}")
                    continue
            
            # Remove duplicates and filter by relevance
            unique_sites = self._deduplicate_sites(discovered_sites)
            relevant_sites = [site for site in unique_sites if site.relevance_score > 0.3]
            
            self.logger.info(f"Discovered {len(relevant_sites)} relevant websites")
            
            # Phase 2: Extract services from discovered websites
            for site in relevant_sites[:30]:  # Limit to top 30 sites
                try:
                    self.logger.info(f"Extracting from: {site.url}")
                    
                    services = await self._extract_services_from_site(site)
                    extracted_services.extend(services)
                    
                    # Add delay between extractions
                    await asyncio.sleep(random.uniform(1, 3))
                    
                except Exception as e:
                    self.logger.error(f"Extraction failed for {site.url}: {e}")
                    continue
            
            # Update statistics
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            self.research_stats['searches_performed'] += len(priority_queries)
            self.research_stats['websites_discovered'] += len(relevant_sites)
            self.research_stats['services_extracted'] += len(extracted_services)
            self.research_stats['research_time_total'] += processing_time
            
            result = {
                'status': 'completed',
                'queries_processed': len(priority_queries),
                'sites_discovered': len(relevant_sites),
                'services_extracted': len(extracted_services),
                'discovered_sites': [site.__dict__ for site in relevant_sites],
                'extracted_services': extracted_services,
                'processing_time': processing_time
            }
            
            self.logger.info(f"Research completed: {len(extracted_services)} services found from {len(relevant_sites)} sites")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Research failed: {e}")
            return {
                'status': 'failed',
                'error': str(e),
                'processing_time': (datetime.utcnow() - start_time).total_seconds()
            }
    
    async def _perform_search(self, query: SearchQuery) -> List[ResearchTarget]:
        """Perform search using multiple search engines"""
        
        search_term = ' '.join(query.keywords)
        encoded_query = quote_plus(search_term)
        results = []
        
        # Try Google first (most comprehensive)
        try:
            google_results = await self._search_google(encoded_query, query)
            results.extend(google_results)
        except Exception as e:
            self.logger.warning(f"Google search failed: {e}")
        
        # Try Bing as backup
        if len(results) < 5:
            try:
                bing_results = await self._search_bing(encoded_query, query)
                results.extend(bing_results)
            except Exception as e:
                self.logger.warning(f"Bing search failed: {e}")
        
        return results
    
    async def _search_google(self, encoded_query: str, query: SearchQuery) -> List[ResearchTarget]:
        """Search Google for Mount Isa services"""
        
        # Use Google Custom Search API approach or scrape results
        search_url = f"https://www.google.com/search?q={encoded_query}&num={query.max_results}"
        
        headers = {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
        
        try:
            async with self.http_session.get(search_url, headers=headers) as response:
                if response.status != 200:
                    raise ResearchException(f"Google search returned status {response.status}")
                
                html = await response.text()
                return self._parse_google_results(html, query)
                
        except Exception as e:
            raise ResearchException(f"Google search failed: {e}")
    
    def _parse_google_results(self, html: str, query: SearchQuery) -> List[ResearchTarget]:
        """Parse Google search results"""
        
        soup = BeautifulSoup(html, 'html.parser')
        results = []
        
        # Find search result containers
        result_containers = soup.find_all('div', class_='g') or soup.find_all('div', {'data-ved': True})
        
        for container in result_containers:
            try:
                # Extract title and URL
                title_element = container.find('h3') or container.find('a')
                if not title_element:
                    continue
                
                # Get the URL
                link_element = container.find('a', href=True)
                if not link_element:
                    continue
                
                url = link_element.get('href', '')
                if url.startswith('/url?q='):
                    # Extract actual URL from Google redirect
                    url = url.split('/url?q=')[1].split('&')[0]
                
                if not url.startswith('http'):
                    continue
                
                # Extract title
                title = title_element.get_text(strip=True)
                
                # Extract snippet
                snippet_element = container.find('span', {'data-ved': True}) or container.find('div', class_='s')
                snippet = snippet_element.get_text(strip=True) if snippet_element else ""
                
                # Calculate relevance score
                relevance_score = self._calculate_relevance(url, title, snippet, query)
                
                if relevance_score > 0.1:  # Minimum relevance threshold
                    results.append(ResearchTarget(
                        url=url,
                        title=title,
                        snippet=snippet,
                        relevance_score=relevance_score,
                        source_query=' '.join(query.keywords),
                        discovered_at=datetime.utcnow()
                    ))
                
            except Exception as e:
                self.logger.debug(f"Error parsing search result: {e}")
                continue
        
        return results
    
    async def _search_bing(self, encoded_query: str, query: SearchQuery) -> List[ResearchTarget]:
        """Search Bing for Mount Isa services"""
        
        search_url = f"https://www.bing.com/search?q={encoded_query}&count={query.max_results}"
        
        headers = {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        }
        
        try:
            async with self.http_session.get(search_url, headers=headers) as response:
                if response.status != 200:
                    raise ResearchException(f"Bing search returned status {response.status}")
                
                html = await response.text()
                return self._parse_bing_results(html, query)
                
        except Exception as e:
            raise ResearchException(f"Bing search failed: {e}")
    
    def _parse_bing_results(self, html: str, query: SearchQuery) -> List[ResearchTarget]:
        """Parse Bing search results"""
        
        soup = BeautifulSoup(html, 'html.parser')
        results = []
        
        # Find Bing result containers
        result_containers = soup.find_all('li', class_='b_algo')
        
        for container in result_containers:
            try:
                # Extract title and URL
                title_element = container.find('h2')
                if not title_element:
                    continue
                
                link_element = title_element.find('a', href=True)
                if not link_element:
                    continue
                
                url = link_element.get('href', '')
                title = link_element.get_text(strip=True)
                
                # Extract snippet
                snippet_element = container.find('p') or container.find('div', class_='b_caption')
                snippet = snippet_element.get_text(strip=True) if snippet_element else ""
                
                # Calculate relevance score
                relevance_score = self._calculate_relevance(url, title, snippet, query)
                
                if relevance_score > 0.1:
                    results.append(ResearchTarget(
                        url=url,
                        title=title,
                        snippet=snippet,
                        relevance_score=relevance_score,
                        source_query=' '.join(query.keywords),
                        discovered_at=datetime.utcnow()
                    ))
                
            except Exception as e:
                self.logger.debug(f"Error parsing Bing result: {e}")
                continue
        
        return results
    
    def _calculate_relevance(self, url: str, title: str, snippet: str, query: SearchQuery) -> float:
        """Calculate relevance score for a search result"""
        
        score = 0.0
        text_content = f"{title} {snippet} {url}".lower()
        
        # Boost for Mount Isa mentions
        mount_isa_terms = ['mount isa', 'mt isa', 'mountisa', '4825']
        for term in mount_isa_terms:
            if term in text_content:
                score += 0.3
        
        # Boost for Queensland mentions
        qld_terms = ['queensland', 'qld', 'north west queensland', 'gulf country']
        for term in qld_terms:
            if term in text_content:
                score += 0.1
        
        # Boost for service-related terms
        for keyword in query.keywords:
            if keyword.lower() in text_content:
                score += 0.2
        
        # Boost for relevant domains
        domain = urlparse(url).netloc.lower()
        for relevant_domain in self.relevant_domains:
            if relevant_domain in domain:
                score += 0.4
        
        # Boost for specific service indicators
        service_indicators = [
            'service', 'centre', 'center', 'support', 'help', 'community',
            'health', 'medical', 'clinic', 'hospital', 'care', 'assistance'
        ]
        
        for indicator in service_indicators:
            if indicator in text_content:
                score += 0.1
        
        # Penalize irrelevant content
        irrelevant_terms = [
            'shopping', 'buy', 'sale', 'property', 'real estate',
            'mining', 'jobs', 'employment' # unless specifically searching for employment services
        ]
        
        if query.service_type != 'employment':
            for term in irrelevant_terms:
                if term in text_content:
                    score -= 0.2
        
        return min(max(score, 0.0), 1.0)
    
    def _deduplicate_sites(self, sites: List[ResearchTarget]) -> List[ResearchTarget]:
        """Remove duplicate sites and keep highest relevance"""
        
        seen_domains = {}
        unique_sites = []
        
        for site in sorted(sites, key=lambda x: x.relevance_score, reverse=True):
            domain = urlparse(site.url).netloc.lower()
            
            if domain not in seen_domains:
                seen_domains[domain] = site
                unique_sites.append(site)
            elif site.relevance_score > seen_domains[domain].relevance_score:
                # Replace with higher relevance site
                unique_sites.remove(seen_domains[domain])
                seen_domains[domain] = site
                unique_sites.append(site)
        
        return unique_sites
    
    async def _extract_services_from_site(self, site: ResearchTarget) -> List[Dict[str, Any]]:
        """Extract service information from a discovered website"""
        
        try:
            # Fetch the website content
            headers = {
                'User-Agent': random.choice(self.user_agents),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            }
            
            async with self.http_session.get(site.url, headers=headers, timeout=30) as response:
                if response.status != 200:
                    raise ResearchException(f"Site returned status {response.status}")
                
                html = await response.text()
                
                # Use the existing discovery agent's extraction logic
                from app.agents.discovery import DiscoveryAgent
                temp_discovery_agent = DiscoveryAgent("temp_research", {})
                
                services = await temp_discovery_agent._extract_services_from_content(html, site.url)
                
                # Enhance services with research context
                for service in services:
                    service['research_context'] = {
                        'source_query': site.source_query,
                        'site_relevance': site.relevance_score,
                        'discovered_via': 'intelligent_research',
                        'discovery_method': 'search_engine_research'
                    }
                
                return services
                
        except Exception as e:
            self.logger.error(f"Failed to extract from {site.url}: {e}")
            return []
    
    async def _perform_deep_search(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Perform deep search on specific service types"""
        
        service_type = payload.get('service_type', 'general')
        specific_queries = [q for q in self.mount_isa_service_queries if q.service_type == service_type]
        
        discovered_sites = []
        
        for query in specific_queries[:10]:  # Deep search with limited queries
            try:
                results = await self._perform_search(query)
                discovered_sites.extend(results)
                await asyncio.sleep(random.uniform(3, 6))  # Longer delays for deep search
            except Exception as e:
                continue
        
        return {
            'status': 'completed',
            'service_type': service_type,
            'sites_discovered': len(discovered_sites),
            'discovered_sites': [site.__dict__ for site in discovered_sites]
        }
    
    async def _extract_from_discovered_sites(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Extract services from a list of previously discovered sites"""
        
        sites_data = payload.get('sites', [])
        extracted_services = []
        
        for site_data in sites_data:
            try:
                site = ResearchTarget(**site_data)
                services = await self._extract_services_from_site(site)
                extracted_services.extend(services)
                await asyncio.sleep(random.uniform(1, 2))
            except Exception as e:
                continue
        
        return {
            'status': 'completed',
            'services_extracted': len(extracted_services),
            'extracted_services': extracted_services
        }
    
    def get_research_statistics(self) -> Dict[str, Any]:
        """Get research performance statistics"""
        
        total_searches = self.research_stats['searches_performed']
        avg_discovery_rate = (
            self.research_stats['websites_discovered'] / max(1, total_searches)
        )
        avg_extraction_rate = (
            self.research_stats['services_extracted'] / max(1, self.research_stats['websites_discovered'])
        )
        
        return {
            'searches_performed': total_searches,
            'websites_discovered': self.research_stats['websites_discovered'],
            'services_extracted': self.research_stats['services_extracted'],
            'failed_extractions': self.research_stats['failed_extractions'],
            'avg_sites_per_search': avg_discovery_rate,
            'avg_services_per_site': avg_extraction_rate,
            'total_research_time': self.research_stats['research_time_total'],
            'avg_research_time_per_search': (
                self.research_stats['research_time_total'] / max(1, total_searches)
            )
        }