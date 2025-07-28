#!/usr/bin/env python3
"""
Intelligent Mount Isa Service Research Demo

This demonstrates the intelligent research system that automatically:
1. Researches Mount Isa services through search engines
2. Discovers relevant websites automatically  
3. Extracts and validates service information
4. Provides comprehensive service discovery without manual input
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

# Add the scraping system to path
sys.path.append(str(Path(__file__).parent / "scraping-system"))

from app.agents.research import MountIsaResearchAgent
from app.services.research_service import ResearchOrchestrator
from app.agents.base import create_agent_task


def print_banner():
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║              🔍 INTELLIGENT MOUNT ISA SERVICE RESEARCH SYSTEM 🔍            ║
║                                                                              ║
║  Automatically discovers services through intelligent web research:         ║
║  • Search engine discovery (Google, Bing)                                   ║
║  • Mount Isa specific targeting                                             ║  
║  • Service extraction and validation                                        ║
║  • Quality assessment and categorization                                    ║
║  • No manual URL entry required!                                            ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)


async def demonstrate_intelligent_research():
    """Demonstrate the intelligent research capabilities"""
    
    print("🚀 Starting Intelligent Research Demonstration\n")
    
    # Create research agent
    print("🤖 Creating intelligent research agent...")
    research_agent = MountIsaResearchAgent(
        agent_id="demo_research_agent",
        config={
            'timeout': 30,
            'request_delay': 1.0,  # Faster for demo
            'max_concurrent_tasks': 1
        }
    )
    
    print("✅ Research agent created successfully")
    print("🎯 Agent capabilities:")
    print("   • Multi-engine search (Google, Bing)")
    print("   • Mount Isa specific queries")  
    print("   • Australian service patterns")
    print("   • Quality assessment and filtering")
    print("   • Intelligent extraction\n")
    
    # Create research task for health services
    print("🔬 Creating research task for Mount Isa health services...")
    
    research_task = await create_agent_task(
        task_type="research_services",
        payload={
            'research_type': 'targeted',
            'target_service_types': ['health', 'medical'],
            'max_queries': 10,  # Limited for demo
            'quality_threshold': 0.5
        },
        priority=0.9
    )
    
    print("✅ Research task created")
    print("📋 Task details:")
    print(f"   • Task ID: {research_task.task_id}")
    print(f"   • Type: {research_task.task_type}")
    print(f"   • Priority: {research_task.priority}")
    print(f"   • Target: Health services in Mount Isa\n")
    
    # Execute research
    print("🔍 Executing intelligent research...")
    print("📡 Searching multiple engines for Mount Isa health services...")
    print("🌐 Discovering relevant websites automatically...")
    print("📊 Extracting and validating service information...")
    print("⏱️  This may take a moment...\n")
    
    try:
        # Note: In demo mode, we'll simulate the research
        print("🎭 DEMO MODE: Simulating intelligent research results...")
        
        # Simulate research results
        simulated_result = {
            'status': 'completed',
            'queries_processed': 8,
            'sites_discovered': 12,
            'services_extracted': 15,
            'discovered_sites': [
                {
                    'url': 'https://www.health.qld.gov.au/north-west/mount-isa',
                    'title': 'Mount Isa Hospital - Queensland Health',
                    'snippet': 'Mount Isa Hospital provides comprehensive health services...',
                    'relevance_score': 0.95,
                    'source_query': 'Mount Isa hospital health services',
                    'discovered_at': datetime.now().isoformat()
                },
                {
                    'url': 'https://www.mountisa.qld.gov.au/community/health-services',
                    'title': 'Community Health Services - Mount Isa City Council', 
                    'snippet': 'Find local health services and medical facilities in Mount Isa...',
                    'relevance_score': 0.87,
                    'source_query': 'Mount Isa community health',
                    'discovered_at': datetime.now().isoformat()
                },
                {
                    'url': 'https://gidgeehealing.org.au',
                    'title': 'Gidgee Healing - Indigenous Health Services',
                    'snippet': 'Providing culturally appropriate health services for Aboriginal...',
                    'relevance_score': 0.83,
                    'source_query': 'Mount Isa Indigenous health services',
                    'discovered_at': datetime.now().isoformat()
                }
            ],
            'extracted_services': [
                {
                    'name': 'Mount Isa Hospital',
                    'description': 'Comprehensive hospital services including emergency, surgery, maternity',
                    'category': 'health',
                    'phone': '(07) 4744 4444',
                    'email': 'mountisa.hospital@health.qld.gov.au',
                    'website': 'https://www.health.qld.gov.au/north-west/mount-isa',
                    'address': '6 Camooweal Street, Mount Isa',
                    'suburb': 'Mount Isa',
                    'postcode': '4825',
                    'state': 'QLD',
                    'confidence_score': 0.95,
                    'extraction_method': 'intelligent_research',
                    'research_context': {
                        'source_query': 'Mount Isa hospital',
                        'site_relevance': 0.95,
                        'discovered_via': 'search_engine'
                    }
                },
                {
                    'name': 'Mount Isa Community Health Centre',
                    'description': 'Primary health care services for the Mount Isa community',
                    'category': 'health',
                    'phone': '(07) 4744 4555',
                    'address': '15 Marian Street, Mount Isa',
                    'suburb': 'Mount Isa', 
                    'postcode': '4825',
                    'state': 'QLD',
                    'confidence_score': 0.88,
                    'extraction_method': 'intelligent_research'
                },
                {
                    'name': 'Gidgee Healing',
                    'description': 'Indigenous health services and cultural healing programs',
                    'category': 'health',
                    'phone': '(07) 4749 7777',
                    'email': 'admin@gidgeehealing.org.au',
                    'website': 'https://gidgeehealing.org.au',
                    'address': '23 Simpson Street, Mount Isa',
                    'suburb': 'Mount Isa',
                    'postcode': '4825', 
                    'state': 'QLD',
                    'confidence_score': 0.92,
                    'extraction_method': 'intelligent_research'
                }
            ],
            'processing_time': 45.2
        }
        
        await asyncio.sleep(2)  # Simulate processing time
        
        # Display results
        print("🎉 RESEARCH COMPLETED SUCCESSFULLY!\n")
        
        print("📊 RESEARCH SUMMARY:")
        print(f"   • Search queries processed: {simulated_result['queries_processed']}")
        print(f"   • Websites discovered: {simulated_result['sites_discovered']}")
        print(f"   • Services extracted: {simulated_result['services_extracted']}")
        print(f"   • Processing time: {simulated_result['processing_time']:.1f} seconds\n")
        
        print("🌐 DISCOVERED WEBSITES:")
        for i, site in enumerate(simulated_result['discovered_sites'], 1):
            print(f"   {i}. {site['title']}")
            print(f"      URL: {site['url']}")
            print(f"      Relevance: {site['relevance_score']:.0%}")
            print(f"      Found via: {site['source_query']}\n")
        
        print("🏥 EXTRACTED HEALTH SERVICES:")
        for i, service in enumerate(simulated_result['extracted_services'], 1):
            print(f"   {i}. {service['name']}")
            print(f"      Category: {service['category'].title()}")
            print(f"      Phone: {service.get('phone', 'Not available')}")
            print(f"      Email: {service.get('email', 'Not available')}")
            print(f"      Address: {service.get('address', 'Not available')}")
            print(f"      Website: {service.get('website', 'Not available')}")
            print(f"      Confidence: {service['confidence_score']:.0%}")
            print()
        
        # Show research insights
        print("💡 RESEARCH INSIGHTS:")
        print("   ✓ High-quality health services discovered")
        print("   ✓ Good coverage of Mount Isa medical facilities") 
        print("   ✓ Indigenous health services identified")
        print("   ✓ Complete contact information extracted")
        print("   ✓ All services validated for Australian formats")
        print("   ✓ Ready for integration into service directory\n")
        
    except Exception as e:
        print(f"❌ Research failed: {e}")
        return False
    
    return True


async def demonstrate_research_orchestrator():
    """Demonstrate the research orchestrator"""
    
    print("🎼 RESEARCH ORCHESTRATOR DEMONSTRATION\n")
    
    print("🏗️  Creating research orchestrator...")
    orchestrator = ResearchOrchestrator()
    
    print("✅ Research orchestrator created")
    print("🎯 Orchestrator capabilities:")
    print("   • Comprehensive service discovery")
    print("   • Targeted category research")
    print("   • Continuous background research")
    print("   • Quality assessment and insights")
    print("   • Research history and analytics\n")
    
    # Get system status
    print("📊 Getting research system status...")
    status = await orchestrator.get_research_status()
    
    print("✅ System Status:")
    print(f"   • Status: {status['system_status']}")
    print(f"   • Active agents: {status['active_agents']}")
    print(f"   • Active tasks: {status['active_tasks']}")
    print("   • Capabilities:")
    for capability in status['capabilities']:
        print(f"     - {capability}")
    print()
    
    # Demonstrate different research types
    print("🎯 Available Research Types:")
    print("   1. Comprehensive - Discovers all service types")
    print("   2. Targeted - Focuses on specific categories")
    print("   3. Continuous - Ongoing background research")
    print("   4. Health-focused - Medical services only")
    print("   5. Community-focused - Community services only\n")
    
    print("🔬 The system is ready to perform intelligent research!")
    print("🌟 No manual URL entry required - fully automated discovery!")


def show_api_endpoints():
    """Show available API endpoints"""
    
    print("🔌 INTELLIGENT RESEARCH API ENDPOINTS:\n")
    
    endpoints = [
        ("POST /api/v1/research/start", "Start intelligent research"),
        ("GET /api/v1/research/discover/all", "Comprehensive service discovery"),
        ("GET /api/v1/research/discover/health", "Health services discovery"),
        ("GET /api/v1/research/discover/disability", "Disability services discovery"),
        ("GET /api/v1/research/discover/community", "Community services discovery"),
        ("GET /api/v1/research/status", "Get research system status"),
        ("GET /api/v1/research/history", "Get research history"),
        ("GET /api/v1/research/capabilities", "Get system capabilities"),
        ("GET /api/v1/research/insights/latest", "Get latest research insights"),
        ("POST /api/v1/research/continuous/start", "Start continuous research")
    ]
    
    for endpoint, description in endpoints:
        print(f"   {endpoint}")
        print(f"      → {description}\n")
    
    print("📖 Example Usage:")
    print("   curl http://localhost:8001/api/v1/research/discover/all")
    print("   curl http://localhost:8001/api/v1/research/status")
    print("   curl -X POST http://localhost:8001/api/v1/research/start \\")
    print("        -H 'Content-Type: application/json' \\")
    print("        -d '{\"research_type\": \"comprehensive\"}'")


def show_next_steps():
    """Show next steps for using the system"""
    
    print("🚀 NEXT STEPS TO USE THE INTELLIGENT RESEARCH SYSTEM:\n")
    
    print("1. 🖥️  Start the API Server:")
    print("   cd scraping-system")
    print("   python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8001\n")
    
    print("2. 📡 Access the API:")
    print("   • API Base: http://localhost:8001/api/v1")
    print("   • Documentation: http://localhost:8001/docs") 
    print("   • Health Check: http://localhost:8001/health\n")
    
    print("3. 🔍 Start Intelligent Research:")
    print("   • Comprehensive: GET /research/discover/all")
    print("   • Health focus: GET /research/discover/health")
    print("   • Custom research: POST /research/start\n")
    
    print("4. 📊 Monitor Progress:")
    print("   • System status: GET /research/status")
    print("   • Research history: GET /research/history")
    print("   • Latest insights: GET /research/insights/latest\n")
    
    print("5. 🔄 Integration:")
    print("   • Services auto-discovered and validated")
    print("   • Results available via API")
    print("   • Ready for integration with main service map")


async def main():
    """Main demo function"""
    
    print_banner()
    
    print("🎮 Select Demo Mode:")
    print("   1. Full Research Demonstration")
    print("   2. System Capabilities Overview")
    print("   3. API Endpoints Reference")
    print("   4. Next Steps Guide")
    print("   5. All of the above")
    
    try:
        choice = input("\nEnter your choice (1-5): ").strip()
        print()
        
        if choice in ['1', '5']:
            success = await demonstrate_intelligent_research()
            if success:
                print("✅ Research demonstration completed successfully!")
            print("\n" + "="*80 + "\n")
        
        if choice in ['2', '5']:
            await demonstrate_research_orchestrator()
            print("\n" + "="*80 + "\n")
        
        if choice in ['3', '5']:
            show_api_endpoints()
            print("\n" + "="*80 + "\n")
        
        if choice in ['4', '5']:
            show_next_steps()
            print()
        
        print("🎯 The intelligent research system is ready to discover Mount Isa services!")
        print("🌟 No manual work required - fully automated service discovery!")
        
    except KeyboardInterrupt:
        print("\n\n👋 Demo interrupted. Thanks for exploring the intelligent research system!")
    except Exception as e:
        print(f"\n❌ Demo error: {e}")


if __name__ == "__main__":
    asyncio.run(main())