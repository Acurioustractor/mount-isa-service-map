#!/usr/bin/env python3
"""
Simple demo script to start the Mount Isa Service Map integrated system
"""

import os
import sys
import time
import subprocess
import signal
from pathlib import Path

def print_banner():
    print("""
╔══════════════════════════════════════════════════════════════════════╗
║                Mount Isa Service Map - Integrated System            ║
║                      Scraping & Validation Demo                     ║
╚══════════════════════════════════════════════════════════════════════╝
    """)

def check_ports():
    """Check if required ports are available"""
    import socket
    
    ports = [8888, 8001]  # Node.js and Python API ports
    for port in ports:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('127.0.0.1', port))
        sock.close()
        
        if result == 0:
            print(f"✓ Port {port} is already in use (service may be running)")
        else:
            print(f"○ Port {port} is available")

def start_simple_api():
    """Start a simple FastAPI demo server"""
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse
    import uvicorn
    
    app = FastAPI(
        title="Mount Isa Service Map - Scraping System Demo",
        description="Demo API for the integrated scraping and validation system",
        version="1.0.0"
    )
    
    @app.get("/")
    async def root():
        return {
            "message": "Mount Isa Service Map - Scraping System Demo",
            "status": "operational",
            "version": "1.0.0",
            "endpoints": {
                "health": "/health",
                "agents": "/api/v1/agents",
                "discovery": "/api/v1/discovery", 
                "validation": "/api/v1/validation",
                "services": "/api/v1/services"
            }
        }
    
    @app.get("/health")
    async def health_check():
        return {
            "status": "healthy",
            "timestamp": time.time(),
            "system": "scraping-system",
            "components": {
                "api": "operational",
                "agents": "simulated",
                "database": "simulated",
                "redis": "simulated"
            }
        }
    
    @app.get("/api/v1/agents/stats/performance")
    async def agent_stats():
        return {
            "total_agents": 3,
            "active_agents": 2,
            "inactive_agents": 1,
            "total_tasks_completed": 125,
            "total_tasks_failed": 8,
            "average_cpu_usage": 15.2,
            "average_memory_usage": 34.7,
            "success_rate": 0.94
        }
    
    @app.get("/api/v1/agents/queue/status")
    async def queue_status():
        return {
            "total_queued_tasks": 12,
            "queue_by_type": {
                "discovery": 7,
                "validation": 5,
                "monitoring": 0
            }
        }
    
    @app.get("/api/v1/discovery/stats/performance")
    async def discovery_stats():
        return {
            "pages_processed": 847,
            "services_discovered": 156,
            "extraction_failures": 23,
            "success_rate": 0.89,
            "avg_services_per_page": 0.18
        }
    
    @app.get("/api/v1/validation/stats/performance")
    async def validation_stats():
        return {
            "services_validated": 98,
            "total_checks_performed": 1456,
            "critical_failures": 3,
            "success_rate": 0.92
        }
    
    @app.get("/api/v1/discovery/recent")
    async def recent_discoveries(limit: int = 20):
        return {
            "recent_discoveries": [
                {
                    "id": "disc_001",
                    "name": "Mount Isa Community Health Centre",
                    "category": "Health Services",
                    "phone": "(07) 4744 4444",
                    "email": "info@michealth.com.au",
                    "website": "https://michealth.com.au",
                    "confidence_score": 0.87,
                    "discovered_at": "2024-07-28T10:30:00Z",
                    "needs_validation": True
                },
                {
                    "id": "disc_002", 
                    "name": "Neighbourhood Centre Mount Isa",
                    "category": "Community Support",
                    "phone": "(07) 4749 1432",
                    "email": "admin@ncmi.org.au",
                    "confidence_score": 0.92,
                    "discovered_at": "2024-07-28T09:15:00Z",
                    "needs_validation": True
                }
            ]
        }
    
    @app.get("/api/v1/agents/health/check")
    async def agents_health():
        return {
            "status": "healthy",
            "total_agents": 3,
            "active_agents": 2,
            "inactive_agents": 1,
            "system_operational": True
        }
    
    # Start the server
    print("🚀 Starting demo Python API on http://localhost:8001")
    print("📊 API Documentation: http://localhost:8001/docs")
    
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")

def main():
    print_banner()
    
    print("🔍 Checking system status...")
    check_ports()
    
    print("\n🎯 Demo Features Available:")
    print("   • Node.js Frontend: http://localhost:8888")
    print("   • Scraping Admin: http://localhost:8888/scraping-admin.html") 
    print("   • Python API: http://localhost:8001")
    print("   • API Docs: http://localhost:8001/docs")
    
    print("\n🛠  Integration Components:")
    print("   ✓ Service Discovery Agents")
    print("   ✓ Validation System with Australian patterns") 
    print("   ✓ Real-time monitoring dashboard")
    print("   ✓ Data synchronization between systems")
    
    print("\n⚡ Starting Python API server...")
    
    try:
        start_simple_api()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down demo system...")
        print("Thanks for exploring the Mount Isa Service Map integration!")

if __name__ == "__main__":
    main()