#!/usr/bin/env python3
"""
Autonomous Agents Framework for Mount Isa Service Map
World-Class Intelligent Scraping and Information Gathering System
"""

import asyncio
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import aiohttp
from bs4 import BeautifulSoup
import spacy
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re
import phonenumbers
import email_validator
from urllib.parse import urljoin, urlparse
import hashlib


class AgentType(Enum):
    DISCOVERER = "discoverer"
    VERIFIER = "verifier" 
    MONITOR = "monitor"
    VALIDATOR = "validator"
    ANALYZER = "analyzer"


class DataConfidence(Enum):
    HIGH = 0.8
    MEDIUM = 0.6
    LOW = 0.4
    UNVERIFIED = 0.2


@dataclass
class ServiceData:
    """Core service information structure"""
    id: str
    name: str
    category: str
    description: str
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    address: Optional[str] = None
    suburb: str = "Mount Isa"
    state: str = "QLD"
    postcode: str = "4825"
    operating_hours: Optional[Dict] = None
    services_offered: List[str] = None
    eligibility: Optional[str] = None
    last_verified: Optional[datetime] = None
    confidence_score: float = 0.0
    sources: List[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.services_offered is None:
            self.services_offered = []
        if self.sources is None:
            self.sources = []
        if self.metadata is None:
            self.metadata = {}


@dataclass
class DiscoveryTask:
    """Task for service discovery agents"""
    url: str
    depth: int
    priority: float
    agent_type: AgentType
    metadata: Dict[str, Any]
    created_at: datetime
    scheduled_for: datetime


class BaseAgent:
    """Base class for all autonomous agents"""
    
    def __init__(self, agent_id: str, agent_type: AgentType, config: Dict[str, Any]):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.config = config
        self.logger = logging.getLogger(f"agent.{agent_id}")
        self.session = None
        self.is_running = False
        
        # Load NLP model for content analysis
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            self.logger.warning("spaCy model not found. Some features may be limited.")
            self.nlp = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={'User-Agent': 'Mount Isa Service Map Bot/1.0'}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def run(self):
        """Main agent execution loop"""
        self.is_running = True
        self.logger.info(f"Agent {self.agent_id} starting...")
        
        while self.is_running:
            try:
                task = await self.get_next_task()
                if task:
                    await self.execute_task(task)
                else:
                    await asyncio.sleep(self.config.get('idle_wait', 60))
            except Exception as e:
                self.logger.error(f"Error in agent {self.agent_id}: {e}")
                await asyncio.sleep(self.config.get('error_wait', 300))
    
    async def get_next_task(self) -> Optional[DiscoveryTask]:
        """Get next task from queue (to be implemented by orchestrator)"""
        raise NotImplementedError
    
    async def execute_task(self, task: DiscoveryTask):
        """Execute a specific task (to be implemented by subclasses)"""
        raise NotImplementedError
    
    def stop(self):
        """Stop the agent"""
        self.is_running = False


class DiscoveryAgent(BaseAgent):
    """Agent specialized in discovering new services and organizations"""
    
    def __init__(self, agent_id: str, config: Dict[str, Any]):
        super().__init__(agent_id, AgentType.DISCOVERER, config)
        self.service_patterns = self._load_service_patterns()
        self.seen_urls = set()
    
    def _load_service_patterns(self) -> Dict[str, Any]:
        """Load patterns for identifying service-related content"""
        return {
            'contact_patterns': {
                'phone': r'(?:\+?61\s?)?(?:\(0\d\)\s?|\(0\d{1,2}\)\s?|0\d)\s?\d{4}\s?\d{4}',
                'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
                'address': r'\d+\s+[A-Za-z\s]+(?:Street|St|Road|Rd|Avenue|Ave|Drive|Dr|Place|Pl|Boulevard|Blvd|Lane|Ln|Court|Ct|Crescent|Cres|Close|Cl|Terrace|Tce|Highway|Hwy)\b',
                'postcode': r'\b48[0-9]{2}\b'  # Mount Isa region postcodes
            },
            'service_keywords': [
                'services', 'support', 'help', 'assistance', 'programs',
                'community', 'health', 'mental health', 'disability',
                'aged care', 'youth', 'family', 'housing', 'employment',
                'education', 'legal', 'emergency', 'transport', 'childcare'
            ],
            'organization_indicators': [
                'about us', 'contact us', 'our services', 'what we do',
                'mission', 'vision', 'programs', 'eligibility', 'hours',
                'location', 'staff', 'volunteers', 'board', 'annual report'
            ],
            'exclude_patterns': [
                'privacy policy', 'terms of service', 'sitemap',
                'login', 'admin', 'internal', 'staff only'
            ]
        }
    
    async def execute_task(self, task: DiscoveryTask):
        """Execute discovery task on a specific URL"""
        self.logger.info(f"Discovering services at {task.url}")
        
        try:
            async with self.session.get(task.url) as response:
                if response.status != 200:
                    self.logger.warning(f"Failed to access {task.url}: {response.status}")
                    return
                
                content = await response.text()
                soup = BeautifulSoup(content, 'html.parser')
                
                # Extract potential service information
                service_data = await self._extract_service_info(soup, task.url)
                
                if service_data:
                    await self._submit_discovered_service(service_data)
                
                # Extract and queue additional URLs for discovery
                if task.depth > 0:
                    new_urls = await self._extract_relevant_links(soup, task.url)
                    await self._queue_new_discovery_tasks(new_urls, task.depth - 1)
                
        except Exception as e:
            self.logger.error(f"Error processing {task.url}: {e}")
    
    async def _extract_service_info(self, soup: BeautifulSoup, url: str) -> Optional[ServiceData]:
        """Extract service information from webpage content"""
        # Calculate relevance score
        text_content = soup.get_text().lower()
        relevance_score = self._calculate_relevance_score(text_content)
        
        if relevance_score < 0.3:  # Threshold for service relevance
            return None
        
        # Extract basic information
        title = self._extract_title(soup)
        description = self._extract_description(soup, text_content)
        contact_info = self._extract_contact_info(text_content)
        
        # Create service data object
        service_id = hashlib.md5(url.encode()).hexdigest()[:12]
        
        service_data = ServiceData(
            id=service_id,
            name=title,
            category=self._classify_service_category(text_content),
            description=description,
            phone=contact_info.get('phone'),
            email=contact_info.get('email'),
            website=url,
            address=contact_info.get('address'),
            confidence_score=relevance_score,
            sources=[url],
            last_verified=datetime.now(),
            metadata={
                'discovered_by': self.agent_id,
                'discovery_method': 'web_scraping',
                'raw_content_hash': hashlib.md5(text_content.encode()).hexdigest()
            }
        )
        
        return service_data
    
    def _calculate_relevance_score(self, text: str) -> float:
        """Calculate how relevant the content is to community services"""
        score = 0.0
        total_keywords = len(self.service_patterns['service_keywords'])
        
        # Check for service keywords
        for keyword in self.service_patterns['service_keywords']:
            if keyword in text:
                score += 1.0 / total_keywords
        
        # Check for organization indicators
        org_indicators = 0
        for indicator in self.service_patterns['organization_indicators']:
            if indicator in text:
                org_indicators += 1
        
        score += min(org_indicators / 5.0, 0.3)  # Cap organization score at 0.3
        
        # Check for contact information presence
        if re.search(self.service_patterns['contact_patterns']['phone'], text):
            score += 0.2
        if re.search(self.service_patterns['contact_patterns']['email'], text):
            score += 0.1
        if re.search(self.service_patterns['contact_patterns']['address'], text):
            score += 0.1
        
        return min(score, 1.0)
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract organization/service title from webpage"""
        # Try multiple sources for title
        title_candidates = []
        
        # Page title
        title_tag = soup.find('title')
        if title_tag:
            title_candidates.append(title_tag.get_text().strip())
        
        # H1 tags
        h1_tags = soup.find_all('h1')
        for h1 in h1_tags:
            title_candidates.append(h1.get_text().strip())
        
        # Organization name from structured data
        org_name = soup.find('span', {'itemprop': 'name'})
        if org_name:
            title_candidates.append(org_name.get_text().strip())
        
        # Return the shortest non-empty title (usually most specific)
        valid_titles = [t for t in title_candidates if t and len(t) < 100]
        return min(valid_titles, key=len) if valid_titles else "Unknown Service"
    
    def _extract_description(self, soup: BeautifulSoup, text_content: str) -> str:
        """Extract service description"""
        # Look for meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            return meta_desc['content'].strip()
        
        # Look for about/description sections
        desc_selectors = [
            'div[class*="about"]', 'div[class*="description"]',
            'section[class*="about"]', 'p[class*="description"]'
        ]
        
        for selector in desc_selectors:
            element = soup.select_one(selector)
            if element:
                desc_text = element.get_text().strip()
                if 50 < len(desc_text) < 500:  # Reasonable description length
                    return desc_text
        
        # Fall back to first substantial paragraph
        paragraphs = soup.find_all('p')
        for p in paragraphs:
            p_text = p.get_text().strip()
            if 50 < len(p_text) < 300:
                return p_text
        
        return "Service description not available"
    
    def _extract_contact_info(self, text: str) -> Dict[str, str]:
        """Extract contact information from text content"""
        contact_info = {}
        
        # Extract phone number
        phone_match = re.search(self.service_patterns['contact_patterns']['phone'], text)
        if phone_match:
            phone = phone_match.group().strip()
            # Validate and format phone number
            try:
                parsed_phone = phonenumbers.parse(phone, "AU")
                if phonenumbers.is_valid_number(parsed_phone):
                    contact_info['phone'] = phonenumbers.format_number(
                        parsed_phone, phonenumbers.PhoneNumberFormat.NATIONAL
                    )
            except:
                contact_info['phone'] = phone
        
        # Extract email
        email_match = re.search(self.service_patterns['contact_patterns']['email'], text)
        if email_match:
            email = email_match.group().strip()
            try:
                valid_email = email_validator.validate_email(email)
                contact_info['email'] = valid_email.email
            except:
                contact_info['email'] = email
        
        # Extract address
        address_match = re.search(self.service_patterns['contact_patterns']['address'], text)
        if address_match:
            contact_info['address'] = address_match.group().strip()
        
        return contact_info
    
    def _classify_service_category(self, text: str) -> str:
        """Classify the service into predefined categories"""
        categories = {
            'health': ['health', 'medical', 'doctor', 'clinic', 'hospital', 'gp'],
            'mental_health': ['mental health', 'psychology', 'counselling', 'therapy'],
            'disability': ['disability', 'ndis', 'accessible', 'special needs'],
            'aged_care': ['aged care', 'elderly', 'seniors', 'retirement'],
            'youth': ['youth', 'young people', 'teenagers', 'adolescent'],
            'family': ['family', 'children', 'parenting', 'childcare'],
            'housing': ['housing', 'accommodation', 'rental', 'homeless'],
            'employment': ['employment', 'job', 'career', 'training', 'work'],
            'education': ['education', 'school', 'training', 'learning'],
            'legal': ['legal', 'law', 'advice', 'court', 'justice'],
            'emergency': ['emergency', 'crisis', 'urgent', '24 hour'],
            'transport': ['transport', 'bus', 'taxi', 'mobility']
        }
        
        # Score each category
        category_scores = {}
        for category, keywords in categories.items():
            score = sum(1 for keyword in keywords if keyword in text.lower())
            if score > 0:
                category_scores[category] = score
        
        # Return category with highest score, or 'general' if none found
        if category_scores:
            return max(category_scores, key=category_scores.get)
        return 'general'
    
    async def _extract_relevant_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extract relevant links for further discovery"""
        relevant_links = []
        
        # Find all links
        links = soup.find_all('a', href=True)
        
        for link in links:
            href = link['href']
            full_url = urljoin(base_url, href)
            
            # Skip if already seen
            if full_url in self.seen_urls:
                continue
            
            # Check if link text suggests service-related content
            link_text = link.get_text().lower().strip()
            if any(keyword in link_text for keyword in self.service_patterns['service_keywords']):
                relevant_links.append(full_url)
                self.seen_urls.add(full_url)
            
            # Check if URL suggests service-related content
            elif any(keyword in full_url.lower() for keyword in ['service', 'support', 'help', 'contact']):
                relevant_links.append(full_url)
                self.seen_urls.add(full_url)
        
        return relevant_links[:10]  # Limit to top 10 relevant links
    
    async def _queue_new_discovery_tasks(self, urls: List[str], depth: int):
        """Queue new discovery tasks for found URLs"""
        # This would integrate with the task orchestrator
        # For now, just log the discovered URLs
        for url in urls:
            self.logger.info(f"Discovered relevant URL for future processing: {url}")
    
    async def _submit_discovered_service(self, service_data: ServiceData):
        """Submit discovered service for verification and storage"""
        self.logger.info(f"Discovered service: {service_data.name}")
        # This would integrate with the verification and storage systems
        # For now, just log the discovery
        print(f"DISCOVERED SERVICE: {json.dumps(asdict(service_data), indent=2, default=str)}")


class VerificationAgent(BaseAgent):
    """Agent specialized in verifying and validating service information"""
    
    def __init__(self, agent_id: str, config: Dict[str, Any]):
        super().__init__(agent_id, AgentType.VERIFIER, config)
    
    async def execute_task(self, task: DiscoveryTask):
        """Execute verification task"""
        # Implementation for verification logic
        pass
    
    async def verify_contact_info(self, service_data: ServiceData) -> Tuple[bool, Dict[str, Any]]:
        """Verify contact information accuracy"""
        verification_results = {}
        
        # Verify phone number
        if service_data.phone:
            phone_valid = await self._verify_phone_number(service_data.phone)
            verification_results['phone_valid'] = phone_valid
        
        # Verify email
        if service_data.email:
            email_valid = await self._verify_email_address(service_data.email)
            verification_results['email_valid'] = email_valid
        
        # Verify website accessibility
        if service_data.website:
            website_accessible = await self._verify_website_accessibility(service_data.website)
            verification_results['website_accessible'] = website_accessible
        
        overall_valid = all(verification_results.values())
        return overall_valid, verification_results
    
    async def _verify_phone_number(self, phone: str) -> bool:
        """Verify phone number is valid and reachable"""
        try:
            parsed = phonenumbers.parse(phone, "AU")
            return phonenumbers.is_valid_number(parsed)
        except:
            return False
    
    async def _verify_email_address(self, email: str) -> bool:
        """Verify email address format and domain"""
        try:
            valid_email = email_validator.validate_email(email)
            return True
        except:
            return False
    
    async def _verify_website_accessibility(self, url: str) -> bool:
        """Verify website is accessible"""
        try:
            async with self.session.head(url) as response:
                return response.status < 400
        except:
            return False


class MonitoringAgent(BaseAgent):
    """Agent specialized in monitoring existing services for changes"""
    
    def __init__(self, agent_id: str, config: Dict[str, Any]):
        super().__init__(agent_id, AgentType.MONITOR, config)
    
    async def execute_task(self, task: DiscoveryTask):
        """Execute monitoring task"""
        # Implementation for monitoring logic
        pass


class AgentOrchestrator:
    """Orchestrates and coordinates all agents"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.agents: List[BaseAgent] = []
        self.task_queue = asyncio.Queue()
        self.logger = logging.getLogger("orchestrator")
        
    def add_agent(self, agent: BaseAgent):
        """Add an agent to the orchestration system"""
        self.agents.append(agent)
    
    async def start_all_agents(self):
        """Start all registered agents"""
        tasks = []
        for agent in self.agents:
            async with agent:
                task = asyncio.create_task(agent.run())
                tasks.append(task)
        
        # Wait for all agents to complete (they run indefinitely)
        await asyncio.gather(*tasks)
    
    async def queue_discovery_task(self, url: str, depth: int = 2, priority: float = 0.5):
        """Queue a new discovery task"""
        task = DiscoveryTask(
            url=url,
            depth=depth,
            priority=priority,
            agent_type=AgentType.DISCOVERER,
            metadata={},
            created_at=datetime.now(),
            scheduled_for=datetime.now()
        )
        await self.task_queue.put(task)


async def main():
    """Main function to demonstrate the agent system"""
    # Configuration
    config = {
        'discovery_agent': {
            'idle_wait': 30,
            'error_wait': 60,
            'max_depth': 3
        },
        'verification_agent': {
            'idle_wait': 60,
            'error_wait': 120
        }
    }
    
    # Create orchestrator
    orchestrator = AgentOrchestrator(config)
    
    # Create and add agents
    discovery_agent = DiscoveryAgent("discovery_001", config['discovery_agent'])
    verification_agent = VerificationAgent("verification_001", config['verification_agent'])
    
    orchestrator.add_agent(discovery_agent)
    orchestrator.add_agent(verification_agent)
    
    # Queue initial discovery tasks
    seed_urls = [
        "https://www.mountisa.qld.gov.au/community/community-services",
        "https://www.health.qld.gov.au/north-west/services",
        "https://www.salvationarmy.org.au/find-us/qld/mount-isa/",
        "https://headspace.org.au/headspace-centres/mount-isa/"
    ]
    
    for url in seed_urls:
        await orchestrator.queue_discovery_task(url, depth=2, priority=1.0)
    
    # Start the orchestration system
    print("Starting autonomous agent system...")
    await orchestrator.start_all_agents()


if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run the agent system
    asyncio.run(main())