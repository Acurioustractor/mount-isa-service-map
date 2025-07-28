#!/usr/bin/env python3
"""
Simple runner for the intelligent Mount Isa service research system
Stores discovered services directly in your existing PostgreSQL database
"""

import asyncio
import json
import sys
import os
from datetime import datetime
from pathlib import Path

# Database connection
import psycopg2
from psycopg2.extras import RealDictCursor
import aiohttp

# Add the scraping system to path
sys.path.append(str(Path(__file__).parent / "scraping-system"))

from app.agents.research import MountIsaResearchAgent, SearchQuery
from app.agents.base import create_agent_task


class SimpleResearchRunner:
    """Simple runner that connects to your existing database"""
    
    def __init__(self, db_config=None):
        # Use your existing database configuration
        self.db_config = db_config or {
            'host': os.getenv('DB_HOST', 'localhost'),
            'database': os.getenv('DB_NAME', 'mount_isa_services'),
            'user': os.getenv('DB_USER', 'benknight'),
            'port': os.getenv('DB_PORT', '5432')
        }
        
        print(f"🗄️  Connecting to database: {self.db_config['database']} at {self.db_config['host']}")
    
    def get_db_connection(self):
        """Get database connection"""
        return psycopg2.connect(**self.db_config)
    
    def save_discovered_service(self, service_data):
        """Save a discovered service to your existing services table"""
        
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Insert into your existing services table
            insert_query = """
                INSERT INTO services (
                    name, description, category, phone, email, website, 
                    address, suburb, postcode, state, latitude, longitude,
                    accessibility_features, opening_hours, last_updated,
                    data_source, confidence_score
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                ON CONFLICT (name, address) DO UPDATE SET
                    description = EXCLUDED.description,
                    phone = EXCLUDED.phone,
                    email = EXCLUDED.email,
                    website = EXCLUDED.website,
                    last_updated = EXCLUDED.last_updated,
                    confidence_score = EXCLUDED.confidence_score
                RETURNING id;
            """
            
            cursor.execute(insert_query, (
                service_data.get('name', ''),
                service_data.get('description', ''),
                service_data.get('category', 'general'),
                service_data.get('phone', ''),
                service_data.get('email', ''),
                service_data.get('website', ''),
                service_data.get('address', ''),
                service_data.get('suburb', 'Mount Isa'),
                service_data.get('postcode', '4825'),
                service_data.get('state', 'QLD'),
                service_data.get('latitude'),
                service_data.get('longitude'),
                json.dumps(service_data.get('accessibility_features', [])),
                json.dumps(service_data.get('opening_hours', {})),
                datetime.now(),
                'intelligent_research',
                service_data.get('confidence_score', 0.5)
            ))
            
            service_id = cursor.fetchone()[0]
            conn.commit()
            
            print(f"✅ Saved service: {service_data.get('name')} (ID: {service_id})")
            return service_id
            
        except Exception as e:
            print(f"❌ Failed to save service {service_data.get('name', 'Unknown')}: {e}")
            if 'conn' in locals():
                conn.rollback()
            return None
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()
    
    async def run_intelligent_research(self, research_type="comprehensive", max_services=50):
        """Run intelligent research and save results to database"""
        
        print("🚀 Starting Intelligent Mount Isa Service Research")
        print(f"📊 Research Type: {research_type}")
        print(f"🎯 Max Services: {max_services}")
        print()
        
        start_time = datetime.now()
        
        try:
            # Create research agent with simplified config
            research_agent = MountIsaResearchAgent(
                agent_id="simple_research_agent",
                config={
                    'timeout': 30,
                    'max_concurrent_tasks': 1,
                    'request_delay': 2.0,  # Be respectful to servers
                    'skip_redis': True,    # Skip Redis for simplicity
                    'skip_db': True        # Skip complex DB for now
                }
            )
            
            print("🤖 Research agent created")
            
            # Create research task
            task_payload = {
                'research_type': research_type,
                'target_service_types': [],
                'max_queries': 20 if research_type == "comprehensive" else 10,
                'quality_threshold': 0.6
            }
            
            research_task = await create_agent_task(
                task_type="research_services",
                payload=task_payload,
                priority=0.8
            )
            
            print("📋 Research task created")
            print("🔍 Discovering Mount Isa services through intelligent search...")
            print("⏱️  This will take a few minutes...")
            print()
            
            # Execute research
            result = await research_agent.execute_task(research_task)
            
            if result.get('status') == 'completed':
                discovered_services = result.get('extracted_services', [])
                
                print(f"🎉 Research completed successfully!")
                print(f"📊 Found {len(discovered_services)} services")
                print()
                
                # Save services to database
                saved_count = 0
                for service in discovered_services:
                    service_id = self.save_discovered_service(service)
                    if service_id:
                        saved_count += 1
                
                # Show summary
                processing_time = (datetime.now() - start_time).total_seconds()
                
                print()
                print("="*60)
                print("📈 RESEARCH SUMMARY")
                print("="*60)
                print(f"🔍 Services discovered: {len(discovered_services)}")
                print(f"💾 Services saved to database: {saved_count}")
                print(f"⏱️  Processing time: {processing_time:.1f} seconds")
                print(f"🎯 Success rate: {(saved_count/max(1, len(discovered_services)))*100:.1f}%")
                print()
                
                # Show top services
                if discovered_services:
                    print("🏆 TOP DISCOVERED SERVICES:")
                    for i, service in enumerate(discovered_services[:5], 1):
                        print(f"   {i}. {service.get('name', 'Unknown')}")
                        print(f"      📞 {service.get('phone', 'No phone')}")
                        print(f"      🌐 {service.get('website', 'No website')}")
                        print(f"      📍 {service.get('address', 'No address')}")
                        print(f"      ⭐ Confidence: {service.get('confidence_score', 0):.0%}")
                        print()
                
                return {
                    'success': True,
                    'services_discovered': len(discovered_services),
                    'services_saved': saved_count,
                    'processing_time': processing_time
                }
                
            else:
                print(f"❌ Research failed: {result.get('error', 'Unknown error')}")
                return {'success': False, 'error': result.get('error')}
                
        except Exception as e:
            print(f"❌ Research system error: {e}")
            return {'success': False, 'error': str(e)}


async def main():
    """Main function to run the research system"""
    
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║           🔍 MOUNT ISA INTELLIGENT SERVICE RESEARCH RUNNER 🔍               ║
║                                                                              ║
║  Automatically discovers Mount Isa services and saves to your database      ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)
    
    # Initialize runner
    runner = SimpleResearchRunner()
    
    # Test database connection
    try:
        conn = runner.get_db_connection()
        print("✅ Database connection successful")
        conn.close()
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("💡 Make sure PostgreSQL is running and your database exists")
        return
    
    print()
    print("🎯 Research Options:")
    print("   1. Health Services")
    print("   2. Disability Services") 
    print("   3. Community Services")
    print("   4. Comprehensive (All Services)")
    print()
    
    # Get user choice
    try:
        choice = input("Select research type (1-4, or Enter for comprehensive): ").strip()
        
        research_types = {
            '1': 'health',
            '2': 'disability', 
            '3': 'community',
            '4': 'comprehensive',
            '': 'comprehensive'
        }
        
        research_type = research_types.get(choice, 'comprehensive')
        
        print(f"🚀 Starting {research_type} service research...")
        print()
        
        # Run the research
        result = await runner.run_intelligent_research(research_type)
        
        if result['success']:
            print("🎉 Research completed successfully!")
            print("📊 Check your services table in the database for new records")
        else:
            print(f"❌ Research failed: {result.get('error')}")
        
    except KeyboardInterrupt:
        print("\n\n👋 Research interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())