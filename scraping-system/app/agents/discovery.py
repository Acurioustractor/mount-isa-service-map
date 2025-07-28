"""
Discovery Agent - Intelligent service discovery and extraction
"""

import re
import asyncio
import hashlib
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from urllib.parse import urljoin, urlparse
from dataclasses import dataclass

import aiohttp
from bs4 import BeautifulSoup
import spacy
from textblob import TextBlob
import phonenumbers

from app.agents.base import BaseAgent
from app.models.agent import AgentType, AgentTask
from app.models.service import ServiceCreate
from app.core.exceptions import ExtractionException


@dataclass
class ExtractionPattern:
    """Pattern for extracting specific data types"""
    name: str
    pattern: str
    confidence: float
    examples: List[str]


class ServicePatternLibrary:
    """Library of patterns for service information extraction"""
    
    def __init__(self):
        self.patterns = {
            'contact': {
                'phone': [
                    ExtractionPattern(
                        name="australian_phone",
                        pattern=r'(?:\+?61\s?)?(?:\(0\d\)\s?|\(0\d{1,2}\)\s?|0\d)\s?\d{4}\s?\d{4}',
                        confidence=0.9,
                        examples=["(07) 4744 4444", "0747444444", "+61 7 4744 4444"]
                    ),
                    ExtractionPattern(
                        name="mobile_phone", 
                        pattern=r'(?:\+?61\s?)?4\d{2}\s?\d{3}\s?\d{3}',
                        confidence=0.8,
                        examples=["0412 345 678", "61412345678", "412 345 678"]
                    )
                ],
                'email': [
                    ExtractionPattern(
                        name="standard_email",
                        pattern=r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
                        confidence=0.9,
                        examples=["info@example.com", "contact@service.org.au"]
                    )
                ],
                'website': [
                    ExtractionPattern(
                        name="standard_url",
                        pattern=r'https?://[^\s<>"{}|\\^`\[\]]+',
                        confidence=0.9,
                        examples=["https://example.com", "http://service.org.au"]
                    )
                ]
            },
            'location': {
                'address': [
                    ExtractionPattern(
                        name="australian_address",
                        pattern=r'\d+\s+[A-Za-z\s]+(?:Street|St|Road|Rd|Avenue|Ave|Drive|Dr|Place|Pl|Boulevard|Blvd|Lane|Ln|Court|Ct|Crescent|Cres|Close|Cl|Terrace|Tce|Highway|Hwy)\b',
                        confidence=0.8,
                        examples=["123 Main Street", "45 Smith Road", "67 Queen Ave"]
                    )
                ],
                'postcode': [
                    ExtractionPattern(
                        name="qld_postcode",
                        pattern=r'\b4[0-9]{3}\b',
                        confidence=0.9,
                        examples=["4825", "4000", "4670"]
                    )
                ]
            },
            'service_indicators': {
                'operating_hours': [
                    ExtractionPattern(
                        name="business_hours",
                        pattern=r'(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday|mon|tue|wed|thu|fri|sat|sun)[\s:-]*(?:\d{1,2}(?::\d{2})?\s*(?:am|pm)?)\s*-?\s*(?:\d{1,2}(?::\d{2})?\s*(?:am|pm)?)',
                        confidence=0.7,
                        examples=["Monday 9:00 AM - 5:00 PM", "Mon-Fri: 8am-6pm"]
                    )
                ],
                'services_offered': [
                    ExtractionPattern(
                        name="service_list",
                        pattern=r'(?:services?|programs?|offerings?|we provide|we offer)[\s:]*([^.]+)',
                        confidence=0.6,
                        examples=["Services: counselling, support groups", "We offer mental health services"]
                    )
                ]
            }
        }
        
        # Service category keywords
        self.category_keywords = {
            'health': ['health', 'medical', 'doctor', 'clinic', 'hospital', 'gp', 'healthcare'],
            'mental_health': ['mental health', 'psychology', 'counselling', 'therapy', 'psychiatric', 'wellbeing'],
            'disability': ['disability', 'ndis', 'accessible', 'special needs', 'inclusive', 'support'],
            'aged_care': ['aged care', 'elderly', 'seniors', 'retirement', 'nursing home'],
            'youth': ['youth', 'young people', 'teenagers', 'adolescent', 'teen'],
            'family': ['family', 'children', 'parenting', 'childcare', 'kids', 'child'],
            'housing': ['housing', 'accommodation', 'rental', 'homeless', 'shelter'],
            'employment': ['employment', 'job', 'career', 'training', 'work', 'jobseeker'],
            'education': ['education', 'school', 'training', 'learning', 'university', 'tafe'],
            'legal': ['legal', 'law', 'advice', 'court', 'justice', 'solicitor'],
            'emergency': ['emergency', 'crisis', 'urgent', '24 hour', 'hotline'],
            'transport': ['transport', 'bus', 'taxi', 'mobility', 'travel']
        }


class DiscoveryAgent(BaseAgent):
    """Intelligent service discovery agent"""
    
    def __init__(self, agent_id: str, config: Optional[Dict[str, Any]] = None, **kwargs):
        super().__init__(agent_id, AgentType.DISCOVERY, config, **kwargs)
        
        # Initialize pattern library
        self.pattern_library = ServicePatternLibrary()
        
        # Initialize NLP components
        self.nlp = None
        self._initialize_nlp()
        
        # Extraction statistics
        self.extraction_stats = {
            'pages_processed': 0,
            'services_discovered': 0,
            'extraction_failures': 0,
            'pattern_matches': {}
        }
        
        # URL tracking
        self.processed_urls = set()
        self.failed_urls = set()
    
    def _initialize_nlp(self):
        """Initialize NLP components"""
        try:
            import spacy
            self.nlp = spacy.load("en_core_web_sm")
        except (ImportError, OSError):
            self.logger.warning("spaCy not available, using basic text processing")
            self.nlp = None
    
    async def execute_task(self, task: AgentTask) -> Dict[str, Any]:
        """Execute discovery task"""
        task_type = task.task_type
        payload = task.payload
        
        if task_type == "discover_url":
            return await self._discover_services_from_url(payload)
        elif task_type == "extract_service":
            return await self._extract_service_from_content(payload)
        elif task_type == "validate_extraction":
            return await self._validate_extracted_service(payload)
        else:
            raise ExtractionException(
                f"Unknown task type: {task_type}",
                url=payload.get('url', 'unknown')
            )
    
    async def _discover_services_from_url(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Discover services from a specific URL"""
        url = payload['url']
        max_depth = payload.get('max_depth', 2)
        current_depth = payload.get('current_depth', 0)
        
        if url in self.processed_urls:
            return {
                'status': 'skipped',
                'reason': 'already_processed',
                'url': url
            }
        
        if url in self.failed_urls:
            return {
                'status': 'skipped',
                'reason': 'previously_failed',
                'url': url
            }
        
        try:
            # Fetch page content
            content = await self._fetch_page_content(url)
            
            # Extract services from content
            services = await self._extract_services_from_content(content, url)
            
            # Find additional URLs for discovery
            additional_urls = []
            if current_depth < max_depth:
                additional_urls = await self._extract_relevant_links(content, url)
            
            # Update statistics
            self.extraction_stats['pages_processed'] += 1
            self.extraction_stats['services_discovered'] += len(services)
            
            # Mark URL as processed
            self.processed_urls.add(url)
            
            result = {
                'status': 'success',
                'url': url,
                'services_found': len(services),
                'services': services,
                'additional_urls': additional_urls,
                'depth': current_depth
            }
            
            self.logger.info(
                f"Successfully processed {url}",
                services_found=len(services),
                additional_urls=len(additional_urls)
            )
            
            return result
            
        except Exception as e:
            self.failed_urls.add(url)
            self.extraction_stats['extraction_failures'] += 1
            
            self.logger.error(f"Failed to process {url}", error=e)
            
            return {
                'status': 'failed',
                'url': url,
                'error': str(e),
                'depth': current_depth
            }
    
    async def _fetch_page_content(self, url: str) -> str:
        """Fetch content from a webpage"""
        try:
            # Respect rate limiting
            await asyncio.sleep(self.request_delay)
            
            async with self.http_session.get(url) as response:
                if response.status != 200:
                    raise ExtractionException(
                        f"HTTP {response.status} error for {url}",
                        url=url
                    )
                
                content = await response.text()
                
                # Basic content validation
                if len(content) < 100:
                    raise ExtractionException(
                        f"Content too short for {url}",
                        url=url
                    )
                
                return content
                
        except aiohttp.ClientError as e:
            raise ExtractionException(
                f"Network error fetching {url}: {str(e)}",
                url=url
            )
    
    async def _extract_services_from_content(self, content: str, url: str) -> List[Dict[str, Any]]:
        """Extract service information from webpage content"""
        soup = BeautifulSoup(content, 'html.parser')
        text_content = soup.get_text().lower()
        
        # Calculate page relevance
        relevance_score = self._calculate_page_relevance(text_content)
        
        if relevance_score < 0.3:  # Not relevant enough
            return []
        
        # Extract potential services
        services = []
        
        # Look for structured service information
        service_sections = self._identify_service_sections(soup)
        
        for section in service_sections:
            try:
                service_data = await self._extract_service_from_section(section, url)
                if service_data:
                    services.append(service_data)
            except Exception as e:
                self.logger.warning(f"Failed to extract service from section", error=e)
        
        # If no structured services found, try page-level extraction
        if not services and relevance_score > 0.7:
            service_data = await self._extract_service_from_page(soup, url)
            if service_data:
                services.append(service_data)
        
        return services
    
    def _calculate_page_relevance(self, text: str) -> float:
        """Calculate how relevant a page is to community services"""
        score = 0.0
        
        # Check for service keywords
        total_keywords = 0
        matched_keywords = 0
        
        for category, keywords in self.pattern_library.category_keywords.items():
            for keyword in keywords:
                total_keywords += 1
                if keyword in text:
                    matched_keywords += 1
                    score += 1.0 / len(keywords)  # Weight by category size
        
        # Boost score for common service indicators
        service_indicators = [
            'contact us', 'services', 'programs', 'support', 'help',
            'community', 'assistance', 'resources', 'information'
        ]
        
        for indicator in service_indicators:
            if indicator in text:
                score += 0.1
        
        # Check for contact information presence
        if re.search(self.pattern_library.patterns['contact']['phone'][0].pattern, text):
            score += 0.2
        if re.search(self.pattern_library.patterns['contact']['email'][0].pattern, text):
            score += 0.1
        if 'address' in text or 'location' in text:
            score += 0.1
        
        return min(score, 1.0)
    
    def _identify_service_sections(self, soup: BeautifulSoup) -> List[Any]:
        """Identify sections of the page that likely contain service information"""
        sections = []
        
        # Look for common service section patterns
        service_selectors = [
            'div[class*="service"]',
            'section[class*="service"]',
            'div[class*="program"]',
            'div[class*="offering"]',
            'article',
            'div[class*="card"]',
            '.service-item',
            '.program-item'
        ]
        
        for selector in service_selectors:
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text().lower()
                if len(text) > 50 and any(
                    keyword in text 
                    for keywords in self.pattern_library.category_keywords.values()
                    for keyword in keywords
                ):
                    sections.append(element)
        
        # If no specific sections found, try main content areas
        if not sections:
            main_selectors = ['main', '.main-content', '.content', 'article', '.page-content']
            for selector in main_selectors:
                element = soup.select_one(selector)
                if element:
                    sections.append(element)
                    break
        
        return sections[:5]  # Limit to 5 sections to avoid processing too much
    
    async def _extract_service_from_section(self, section: Any, url: str) -> Optional[Dict[str, Any]]:
        """Extract service information from a specific page section"""
        text_content = section.get_text()
        
        # Extract basic information
        service_data = {
            'source_url': url,
            'extraction_method': 'section_based',
            'confidence_score': 0.0
        }
        
        # Extract name (look for headings)
        name = self._extract_service_name(section)
        if not name:
            return None
        
        service_data['name'] = name
        
        # Extract description
        description = self._extract_description(section, text_content)
        service_data['description'] = description
        
        # Extract contact information
        contact_info = self._extract_contact_information(text_content)
        service_data.update(contact_info)
        
        # Extract location information
        location_info = self._extract_location_information(text_content)
        service_data.update(location_info)
        
        # Extract service details
        service_details = self._extract_service_details(text_content)
        service_data.update(service_details)
        
        # Classify service category
        service_data['category'] = self._classify_service_category(text_content)
        
        # Calculate confidence score
        service_data['confidence_score'] = self._calculate_extraction_confidence(service_data)
        
        # Only return if confidence is reasonable
        if service_data['confidence_score'] > 0.4:
            return service_data
        
        return None
    
    async def _extract_service_from_page(self, soup: BeautifulSoup, url: str) -> Optional[Dict[str, Any]]:
        """Extract service information from entire page"""
        text_content = soup.get_text()
        
        service_data = {
            'source_url': url,
            'extraction_method': 'page_based',
            'confidence_score': 0.0
        }
        
        # Extract page title as service name
        title_element = soup.find('title')
        if title_element:
            service_data['name'] = self._clean_service_name(title_element.get_text())
        else:
            # Try h1 tags
            h1_element = soup.find('h1')
            if h1_element:
                service_data['name'] = self._clean_service_name(h1_element.get_text())
            else:
                return None
        
        # Extract meta description as service description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            service_data['description'] = meta_desc['content']
        else:
            # Extract first substantial paragraph
            paragraphs = soup.find_all('p')
            for p in paragraphs:
                p_text = p.get_text().strip()
                if 50 < len(p_text) < 300:
                    service_data['description'] = p_text
                    break
        
        # Extract contact and location information
        contact_info = self._extract_contact_information(text_content)
        service_data.update(contact_info)
        
        location_info = self._extract_location_information(text_content)
        service_data.update(location_info)
        
        service_details = self._extract_service_details(text_content)
        service_data.update(service_details)
        
        # Classify service category
        service_data['category'] = self._classify_service_category(text_content)
        
        # Calculate confidence score
        service_data['confidence_score'] = self._calculate_extraction_confidence(service_data)
        
        if service_data['confidence_score'] > 0.5:
            return service_data
        
        return None
    
    def _extract_service_name(self, section: Any) -> Optional[str]:
        """Extract service name from section"""
        # Look for headings
        for tag in ['h1', 'h2', 'h3', 'h4']:
            heading = section.find(tag)
            if heading:
                name = heading.get_text().strip()
                if 3 < len(name) < 100:
                    return self._clean_service_name(name)
        
        # Look for elements with name-like classes
        name_selectors = [
            '.title', '.name', '.service-name', '.program-name',
            '[class*="title"]', '[class*="name"]'
        ]
        
        for selector in name_selectors:
            element = section.select_one(selector)
            if element:
                name = element.get_text().strip()
                if 3 < len(name) < 100:
                    return self._clean_service_name(name)
        
        return None
    
    def _clean_service_name(self, name: str) -> str:
        """Clean and normalize service name"""
        # Remove common website suffixes
        name = re.sub(r'\s*[-|]\s*.*$', '', name)
        name = re.sub(r'\s*\|\s*.*$', '', name)
        
        # Remove extra whitespace
        name = ' '.join(name.split())
        
        return name.strip()
    
    def _extract_description(self, section: Any, text_content: str) -> str:
        """Extract service description"""
        # Look for description in meta tags or structured data
        desc_selectors = [
            '.description', '.summary', '.about', '.overview',
            '[class*="description"]', '[class*="summary"]'
        ]
        
        for selector in desc_selectors:
            element = section.select_one(selector)
            if element:
                desc = element.get_text().strip()
                if 20 < len(desc) < 500:
                    return desc
        
        # Fall back to first substantial paragraph
        paragraphs = section.find_all('p')
        for p in paragraphs:
            desc = p.get_text().strip()
            if 20 < len(desc) < 500:
                return desc
        
        return "Service description not available"
    
    def _extract_contact_information(self, text: str) -> Dict[str, Any]:
        """Extract contact information from text"""
        contact_info = {}
        
        # Extract phone number
        for pattern_info in self.pattern_library.patterns['contact']['phone']:
            match = re.search(pattern_info.pattern, text)
            if match:
                phone = match.group().strip()
                try:
                    parsed_phone = phonenumbers.parse(phone, "AU")
                    if phonenumbers.is_valid_number(parsed_phone):
                        contact_info['phone'] = phonenumbers.format_number(
                            parsed_phone, phonenumbers.PhoneNumberFormat.NATIONAL
                        )
                        break
                except:
                    contact_info['phone'] = phone
                    break
        
        # Extract email
        for pattern_info in self.pattern_library.patterns['contact']['email']:
            match = re.search(pattern_info.pattern, text)
            if match:
                contact_info['email'] = match.group().strip()
                break
        
        # Extract website
        for pattern_info in self.pattern_library.patterns['contact']['website']:
            match = re.search(pattern_info.pattern, text)
            if match:
                website = match.group().strip()
                if not website.startswith(('http://', 'https://')):
                    website = 'https://' + website
                contact_info['website'] = website
                break
        
        return contact_info
    
    def _extract_location_information(self, text: str) -> Dict[str, Any]:
        """Extract location information from text"""
        location_info = {}
        
        # Extract address
        for pattern_info in self.pattern_library.patterns['location']['address']:
            match = re.search(pattern_info.pattern, text)
            if match:
                location_info['address'] = match.group().strip()
                break
        
        # Extract postcode
        for pattern_info in self.pattern_library.patterns['location']['postcode']:
            match = re.search(pattern_info.pattern, text)
            if match:
                location_info['postcode'] = match.group().strip()
                break
        
        # Default location values for Mount Isa region
        if 'postcode' not in location_info:
            location_info['postcode'] = '4825'
        
        location_info['suburb'] = location_info.get('suburb', 'Mount Isa')
        location_info['state'] = 'QLD'
        
        return location_info
    
    def _extract_service_details(self, text: str) -> Dict[str, Any]:
        """Extract service-specific details"""
        details = {}
        
        # Extract operating hours
        hours_pattern = self.pattern_library.patterns['service_indicators']['operating_hours'][0]
        hours_matches = re.findall(hours_pattern.pattern, text, re.IGNORECASE)
        if hours_matches:
            details['operating_hours'] = hours_matches[0]
        
        # Extract services offered
        services_pattern = self.pattern_library.patterns['service_indicators']['services_offered'][0]
        services_match = re.search(services_pattern.pattern, text, re.IGNORECASE)
        if services_match:
            services_text = services_match.group(1)
            # Simple service list extraction
            services_list = [s.strip() for s in re.split(r'[,;]', services_text) if s.strip()]
            details['services_offered'] = services_list[:5]  # Limit to 5 services
        
        return details
    
    def _classify_service_category(self, text: str) -> str:
        """Classify service into predefined categories"""
        category_scores = {}
        text_lower = text.lower()
        
        for category, keywords in self.pattern_library.category_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            if score > 0:
                category_scores[category] = score
        
        if category_scores:
            return max(category_scores, key=category_scores.get)
        
        return 'general'
    
    def _calculate_extraction_confidence(self, service_data: Dict[str, Any]) -> float:
        """Calculate confidence score for extracted service data"""
        score = 0.0
        
        # Name quality
        if service_data.get('name'):
            name_length = len(service_data['name'])
            if 5 <= name_length <= 50:
                score += 0.2
            elif name_length > 50:
                score += 0.1
        
        # Description quality
        if service_data.get('description'):
            desc_length = len(service_data['description'])
            if 50 <= desc_length <= 300:
                score += 0.2
            elif desc_length > 300:
                score += 0.15
        
        # Contact information
        if service_data.get('phone'):
            score += 0.2
        if service_data.get('email'):
            score += 0.15
        if service_data.get('website'):
            score += 0.1
        
        # Location information
        if service_data.get('address'):
            score += 0.15
        
        # Service details
        if service_data.get('operating_hours'):
            score += 0.1
        if service_data.get('services_offered'):
            score += 0.1
        
        return min(score, 1.0)
    
    async def _extract_relevant_links(self, content: str, base_url: str) -> List[str]:
        """Extract relevant links for further discovery"""
        soup = BeautifulSoup(content, 'html.parser')
        relevant_links = []
        
        links = soup.find_all('a', href=True)
        
        for link in links:
            href = link['href']
            full_url = urljoin(base_url, href)
            
            # Skip if already processed
            if full_url in self.processed_urls:
                continue
            
            # Check if link text suggests service-related content
            link_text = link.get_text().lower().strip()
            
            # Service-related link text indicators
            service_indicators = [
                'service', 'program', 'support', 'help', 'about',
                'contact', 'community', 'resource', 'assistance'
            ]
            
            if any(indicator in link_text for indicator in service_indicators):
                relevant_links.append(full_url)
            elif any(indicator in full_url.lower() for indicator in service_indicators):
                relevant_links.append(full_url)
        
        # Remove duplicates and limit
        unique_links = list(dict.fromkeys(relevant_links))
        return unique_links[:10]  # Limit to 10 links per page
    
    def get_extraction_statistics(self) -> Dict[str, Any]:
        """Get extraction performance statistics"""
        total_attempts = self.extraction_stats['pages_processed']
        success_rate = (
            (total_attempts - self.extraction_stats['extraction_failures']) / max(1, total_attempts)
        )
        
        return {
            'pages_processed': self.extraction_stats['pages_processed'],
            'services_discovered': self.extraction_stats['services_discovered'],
            'extraction_failures': self.extraction_stats['extraction_failures'],
            'success_rate': success_rate,
            'services_per_page': (
                self.extraction_stats['services_discovered'] / max(1, total_attempts)
            ),
            'pattern_matches': self.extraction_stats['pattern_matches']
        }