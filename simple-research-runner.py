#!/usr/bin/env python3
"""
Simplified Mount Isa Service Discovery Runner
Works without complex dependencies - just needs requests and psycopg2
"""

import json
import time
import random
import re
from datetime import datetime
from urllib.parse import quote_plus, urlparse
import requests
from bs4 import BeautifulSoup
import psycopg2
from psycopg2.extras import RealDictCursor
import os


class SimpleMountIsaResearcher:
    """Simplified researcher that finds Mount Isa services"""
    
    def __init__(self, db_config=None):
        self.db_config = db_config or {
            'host': os.getenv('DB_HOST', 'localhost'),
            'database': os.getenv('DB_NAME', 'mount_isa_services'), 
            'user': os.getenv('DB_USER', 'benknight'),
            'port': os.getenv('DB_PORT', '5432')
        }
        
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        ]
        
        # Mount Isa specific searches
        self.search_queries = self._build_search_queries()
        
    def _build_search_queries(self):
        """Build targeted Mount Isa service searches"""
        
        base_queries = [
            "Mount Isa Hospital health services",
            "Mount Isa Community Health Centre",
            "Mount Isa medical centre GP doctor",
            "Mount Isa disability services NDIS",
            "Mount Isa aged care services",
            "Mount Isa youth services PCYC",
            "Mount Isa community centre",
            "Mount Isa family services childcare",
            "Mount Isa mental health counselling",
            "Mount Isa Indigenous health Gidgee",
            "Mount Isa neighbourhood centre",
            "Mount Isa emergency services",
            "Mount Isa legal aid services",
            "Mount Isa employment services",
            "Mount Isa housing accommodation",
            "Salvation Army Mount Isa",
            "Red Cross Mount Isa",
            "Centrelink Mount Isa services",
            "Mount Isa pharmacy medical",
            "Mount Isa therapy physiotherapy"
        ]
        
        return base_queries
    
    def search_google(self, query, max_results=10):
        """Search Google for Mount Isa services"""
        
        search_url = f"https://www.google.com/search?q={quote_plus(query)}&num={max_results}"
        
        headers = {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        }
        
        try:
            response = requests.get(search_url, headers=headers, timeout=10)
            if response.status_code == 200:
                return self._parse_google_results(response.text, query)
            else:
                print(f"⚠️  Google search failed with status {response.status_code}")
                return []
        except Exception as e:
            print(f"⚠️  Google search error: {e}")
            return []
    
    def _parse_google_results(self, html, query):
        """Parse Google search results"""
        
        soup = BeautifulSoup(html, 'html.parser')
        results = []
        
        # Find search result containers
        result_containers = soup.find_all('div', class_='g') or soup.find_all('div', {'data-ved': True})
        
        for container in result_containers[:5]:  # Limit to top 5 results
            try:
                # Get title and URL
                link_element = container.find('a', href=True)
                if not link_element:
                    continue
                
                url = link_element.get('href', '')
                if url.startswith('/url?q='):
                    url = url.split('/url?q=')[1].split('&')[0]
                
                if not url.startswith('http'):
                    continue
                
                # Get title
                title_element = container.find('h3')
                title = title_element.get_text(strip=True) if title_element else ""
                
                # Get snippet
                snippet_element = container.find('span', {'data-ved': True}) or container.find('div', class_='s')
                snippet = snippet_element.get_text(strip=True) if snippet_element else ""
                
                # Calculate relevance
                relevance = self._calculate_relevance(url, title, snippet, query)
                
                if relevance > 0.2:  # Minimum relevance
                    results.append({
                        'url': url,
                        'title': title,
                        'snippet': snippet,
                        'relevance': relevance,
                        'query': query
                    })
                    
            except Exception as e:
                continue
        
        return results
    
    def _calculate_relevance(self, url, title, snippet, query):
        """Calculate how relevant a result is to Mount Isa services"""
        
        score = 0.0
        text = f"{title} {snippet} {url}".lower()
        
        # Mount Isa mentions
        mount_isa_terms = ['mount isa', 'mt isa', 'mountisa', '4825']
        for term in mount_isa_terms:
            if term in text:
                score += 0.4
        
        # Queensland mentions
        if any(term in text for term in ['queensland', 'qld']):
            score += 0.2
        
        # Service indicators
        service_terms = ['service', 'centre', 'center', 'health', 'community', 'support', 'care']
        for term in service_terms:
            if term in text:
                score += 0.1
        
        # Government/official domains
        domain = urlparse(url).netloc.lower()
        if any(d in domain for d in ['qld.gov.au', 'mountisa.qld.gov.au', 'health.qld.gov.au']):
            score += 0.3
        
        return min(score, 1.0)
    
    def extract_service_info(self, url, title, snippet):
        """Extract service information from a website"""
        
        try:
            headers = {'User-Agent': random.choice(self.user_agents)}
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code != 200:
                return None
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract basic info
            service = {
                'name': self._extract_service_name(soup, title),
                'description': self._extract_description(soup, snippet),
                'phone': self._extract_phone(soup),
                'email': self._extract_email(soup),
                'website': url,
                'address': self._extract_address(soup),
                'category': self._determine_category(title, snippet, soup.get_text()),
                'confidence_score': 0.7  # Base confidence for extracted services
            }
            
            # Validate we got some useful info
            if service['name'] and (service['phone'] or service['email'] or service['address']):
                return service
            
            return None
            
        except Exception as e:
            print(f"⚠️  Failed to extract from {url}: {e}")
            return None
    
    def _extract_service_name(self, soup, fallback_title):
        """Extract service name"""
        
        # Try common title patterns
        title_tag = soup.find('title')
        if title_tag:
            title_text = title_tag.get_text(strip=True)
            if 'mount isa' in title_text.lower():
                return title_text
        
        # Try h1 tags
        h1_tag = soup.find('h1')
        if h1_tag:
            h1_text = h1_tag.get_text(strip=True)
            if h1_text and len(h1_text) < 100:
                return h1_text
        
        return fallback_title or "Unknown Service"
    
    def _extract_description(self, soup, fallback_snippet):
        """Extract service description"""
        
        # Try meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            return meta_desc['content']
        
        # Try first paragraph
        p_tags = soup.find_all('p')
        for p in p_tags:
            text = p.get_text(strip=True)
            if len(text) > 50 and len(text) < 500:
                return text
        
        return fallback_snippet or "Service in Mount Isa"
    
    def _extract_phone(self, soup):
        """Extract phone number"""
        
        text = soup.get_text()
        # Australian phone patterns
        phone_patterns = [
            r'\(07\)\s*\d{4}\s*\d{4}',  # (07) 4744 4444
            r'07\s*\d{4}\s*\d{4}',      # 07 4744 4444
            r'\d{2}\s*\d{4}\s*\d{4}',   # 07 4744 4444
        ]
        
        for pattern in phone_patterns:
            match = re.search(pattern, text)
            if match:
                phone = match.group().strip()
                if '4744' in phone or '4749' in phone:  # Mount Isa area codes
                    return phone
        
        return None
    
    def _extract_email(self, soup):
        """Extract email address"""
        
        text = soup.get_text()
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        
        match = re.search(email_pattern, text)
        if match:
            email = match.group()
            # Filter out obvious non-contact emails
            if not any(word in email.lower() for word in ['noreply', 'donotreply', 'no-reply']):
                return email
        
        return None
    
    def _extract_address(self, soup):
        """Extract address"""
        
        text = soup.get_text()
        
        # Look for Mount Isa addresses
        address_patterns = [
            r'[0-9]+[A-Za-z]?\s+[A-Za-z\s]+(?:Street|St|Road|Rd|Avenue|Ave|Drive|Dr|Place|Pl|Court|Ct)[^,\n]*(?:Mount Isa|Mt Isa)',
            r'[A-Za-z\s]+(?:Street|St|Road|Rd|Avenue|Ave|Drive|Dr|Place|Pl|Court|Ct)[^,\n]*(?:Mount Isa|Mt Isa)'
        ]
        
        for pattern in address_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                address = match.group().strip()
                if len(address) < 200:  # Reasonable length
                    return address
        
        return None
    
    def _determine_category(self, title, snippet, content):
        """Determine service category"""
        
        text = f"{title} {snippet} {content}".lower()
        
        categories = {
            'health': ['health', 'medical', 'hospital', 'clinic', 'doctor', 'gp', 'mental health'],
            'disability': ['disability', 'ndis', 'accessible', 'special needs'],
            'aged_care': ['aged care', 'elderly', 'seniors', 'retirement'],
            'youth': ['youth', 'young people', 'pcyc', 'teenagers'],
            'community': ['community', 'neighbourhood', 'volunteer'],
            'family': ['family', 'childcare', 'children', 'parenting'],
            'emergency': ['emergency', 'crisis', 'urgent']
        }
        
        for category, keywords in categories.items():
            if any(keyword in text for keyword in keywords):
                return category
        
        return 'general'
    
    def save_service_to_db(self, service):
        """Save service to database"""
        
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            
            # Insert or update service
            query = """
                INSERT INTO services (
                    name, description, category, phone, email, website,
                    address, suburb, postcode, state, last_updated,
                    data_source, confidence_score
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                ON CONFLICT (name, COALESCE(address, '')) DO UPDATE SET
                    description = EXCLUDED.description,
                    phone = COALESCE(EXCLUDED.phone, services.phone),
                    email = COALESCE(EXCLUDED.email, services.email),
                    website = COALESCE(EXCLUDED.website, services.website),
                    last_updated = EXCLUDED.last_updated,
                    confidence_score = EXCLUDED.confidence_score
                RETURNING id;
            """
            
            cursor.execute(query, (
                service['name'],
                service['description'],
                service['category'],
                service.get('phone'),
                service.get('email'),
                service['website'],
                service.get('address'),
                'Mount Isa',
                '4825',
                'QLD',
                datetime.now(),
                'intelligent_research',
                service['confidence_score']
            ))
            
            service_id = cursor.fetchone()[0]
            conn.commit()
            
            print(f"✅ Saved: {service['name']}")
            return service_id
            
        except Exception as e:
            print(f"❌ DB Error for {service['name']}: {e}")
            return None
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()
    
    def run_research(self, max_queries=10):
        """Run the research process"""
        
        print("🔍 Starting Mount Isa Service Discovery")
        print(f"📊 Processing {min(max_queries, len(self.search_queries))} search queries")
        print()
        
        discovered_services = []
        saved_count = 0
        
        queries_to_run = self.search_queries[:max_queries]
        
        for i, query in enumerate(queries_to_run, 1):
            print(f"🔎 [{i}/{len(queries_to_run)}] Searching: {query}")
            
            # Search Google
            search_results = self.search_google(query)
            
            if search_results:
                print(f"   Found {len(search_results)} relevant results")
                
                # Extract info from top results
                for result in search_results[:2]:  # Top 2 per query
                    service = self.extract_service_info(
                        result['url'], 
                        result['title'], 
                        result['snippet']
                    )
                    
                    if service:
                        discovered_services.append(service)
                        
                        # Save to database
                        service_id = self.save_service_to_db(service)
                        if service_id:
                            saved_count += 1
            else:
                print("   No relevant results found")
            
            # Be respectful - wait between searches
            time.sleep(random.uniform(2, 4))
            print()
        
        # Summary
        print("="*60)
        print("📈 DISCOVERY COMPLETE")
        print("="*60)  
        print(f"🔍 Services discovered: {len(discovered_services)}")
        print(f"💾 Services saved to database: {saved_count}")
        print()
        
        if discovered_services:
            print("🏆 DISCOVERED SERVICES:")
            for i, service in enumerate(discovered_services, 1):
                print(f"   {i}. {service['name']}")
                print(f"      📞 {service.get('phone', 'No phone')}")
                print(f"      🌐 {service['website']}")
                print(f"      📍 {service.get('address', 'No address')}")
                print()
        
        return discovered_services


def main():
    """Main function"""
    
    print("""
╔═══════════════════════════════════════════════════════════════════════════════╗
║              🔍 SIMPLE MOUNT ISA SERVICE DISCOVERY TOOL 🔍                   ║
║                                                                               ║
║  Automatically finds Mount Isa services and saves them to your database      ║
╚═══════════════════════════════════════════════════════════════════════════════╝
    """)
    
    # Create researcher
    researcher = SimpleMountIsaResearcher()
    
    # Test database connection
    try:
        conn = psycopg2.connect(**researcher.db_config)
        print("✅ Database connection successful")
        conn.close()
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("Make sure PostgreSQL is running and your credentials are correct")
        return
    
    print()
    
    # Get number of queries to run
    try:
        max_queries = input("How many search queries to run? (default 10): ").strip()
        max_queries = int(max_queries) if max_queries else 10
        max_queries = min(max_queries, 20)  # Cap at 20 to be respectful
    except ValueError:
        max_queries = 10
    
    print()
    
    # Run research
    try:
        discovered_services = researcher.run_research(max_queries)
        
        print("🎉 Research completed!")
        print("📊 Check your 'services' table in the database for new entries")
        
    except KeyboardInterrupt:
        print("\n\n👋 Research interrupted by user")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()