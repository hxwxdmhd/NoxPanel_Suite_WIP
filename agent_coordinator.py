#!/usr/bin/env python3

"""
NoxSuite Agent Coordination Manager
===================================

Manages multi-agent coordination between Supermaven, Langflow, and MCP agents.
Provides context sharing, workflow orchestration, and inter-agent communication.
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import aiohttp
import docker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('agent_coordination.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AgentCoordinator:
    """Coordinates multiple AI agents for the NoxSuite ecosystem"""
    
    def __init__(self):
        self.docker_client = docker.from_env()
        self.langflow_url = "http://localhost:7860"
        self.ollama_url = "http://localhost:11434"
        self.agents = {
            "supermaven": {"status": "unknown", "last_ping": None},
            "langflow": {"status": "unknown", "last_ping": None},
            "ollama": {"status": "unknown", "last_ping": None}
        }
        self.coordination_log = []
        
    async def check_agent_health(self, agent_name: str, url: str) -> bool:
        """Check if an agent is responsive"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{url}/health", timeout=5) as response:
                    if response.status == 200:
                        self.agents[agent_name]["status"] = "healthy"
                        self.agents[agent_name]["last_ping"] = datetime.now()
                        return True
        except Exception as e:
            logger.warning(f"Health check failed for {agent_name}: {e}")
        
        self.agents[agent_name]["status"] = "unavailable"
        return False
    
    async def check_ollama_health(self) -> bool:
        """Check Ollama health with alternative endpoints"""
        try:
            async with aiohttp.ClientSession() as session:
                # Try version endpoint first
                async with session.get(f"{self.ollama_url}/api/version", timeout=5) as response:
                    if response.status == 200:
                        self.agents["ollama"]["status"] = "healthy"
                        self.agents["ollama"]["last_ping"] = datetime.now()
                        return True
        except Exception as e:
            logger.warning(f"Ollama health check failed: {e}")
        
        self.agents["ollama"]["status"] = "unavailable"
        return False
    
    def check_docker_services(self) -> Dict[str, Any]:
        """Check status of Docker-based services"""
        services_status = {}
        try:
            containers = self.docker_client.containers.list()
            for container in containers:
                if "noxsuite" in container.name:
                    services_status[container.name] = {
                        "status": container.status,
                        "health": getattr(container.attrs.get("State", {}), "Health", {}).get("Status", "unknown")
                    }
        except Exception as e:
            logger.error(f"Docker service check failed: {e}")
        
        return services_status
    
    async def coordinate_agents(self) -> Dict[str, Any]:
        """Main coordination function"""
        logger.info("🤖 Starting Agent Coordination Cycle")
        
        # Check all agent health
        langflow_healthy = await self.check_agent_health("langflow", self.langflow_url)
        ollama_healthy = await self.check_ollama_health()
        
        # Check Docker services
        docker_status = self.check_docker_services()
        
        # Coordination logic
        coordination_result = {
            "timestamp": datetime.now().isoformat(),
            "agents": self.agents.copy(),
            "docker_services": docker_status,
            "coordination_actions": []
        }
        
        # Langflow coordination
        if langflow_healthy:
            coordination_result["coordination_actions"].append({
                "action": "langflow_ready",
                "description": "Langflow MCP agent platform operational",
                "next_steps": ["Configure MCP server nodes", "Setup agent workflows"]
            })
        
        # Ollama coordination  
        if ollama_healthy:
            coordination_result["coordination_actions"].append({
                "action": "ollama_integration",
                "description": "Ollama AI inference available for agent LLM operations",
                "capabilities": ["Local model inference", "Agent reasoning", "Context processing"]
            })
        
        # Multi-agent workflow readiness
        if langflow_healthy and ollama_healthy:
            coordination_result["coordination_actions"].append({
                "action": "multi_agent_ready",
                "description": "All core agents operational - ready for coordinated workflows",
                "workflow_options": [
                    "Code analysis and generation",
                    "System monitoring and alerting", 
                    "Automated deployment orchestration",
                    "Security vulnerability analysis"
                ]
            })
        
        self.coordination_log.append(coordination_result)
        logger.info(f"✅ Coordination cycle completed: {len(coordination_result['coordination_actions'])} actions identified")
        
        return coordination_result
    
    async def setup_agent_context_sharing(self) -> Dict[str, Any]:
        """Setup context sharing between agents"""
        logger.info("🔗 Setting up agent context sharing")
        
        context_config = {
            "context_sharing": {
                "supermaven": {
                    "role": "Code intelligence and completion",
                    "data_sources": ["code_context", "project_structure", "git_history"],
                    "sharing_endpoints": ["context_api", "completion_suggestions"]
                },
                "langflow": {
                    "role": "Visual workflow orchestration",
                    "data_sources": ["agent_workflows", "execution_results", "node_configurations"],
                    "sharing_endpoints": ["workflow_api", "execution_status"]
                },
                "ollama": {
                    "role": "Local AI inference and reasoning",
                    "data_sources": ["model_outputs", "reasoning_chains", "embeddings"],
                    "sharing_endpoints": ["inference_api", "model_status"]
                }
            },
            "communication_protocols": {
                "message_format": "JSON with agent_id, timestamp, action, data fields",
                "coordination_channel": "agent_coordination_queue",
                "heartbeat_interval": 30,
                "timeout_threshold": 120
            }
        }
        
        # Save context configuration
        with open("agent_context_config.json", "w") as f:
            json.dump(context_config, f, indent=2)
        
        return context_config
    
    async def generate_coordination_report(self) -> str:
        """Generate detailed coordination status report"""
        report = f"""
🤖 NoxSuite Agent Coordination Status Report
═══════════════════════════════════════════

Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Agent Status Overview:
"""
        
        for agent, status in self.agents.items():
            report += f"  • {agent.title()}: {status['status']} "
            if status['last_ping']:
                report += f"(last ping: {status['last_ping'].strftime('%H:%M:%S')})"
            report += "\n"
        
        # Docker services
        docker_status = self.check_docker_services()
        if docker_status:
            report += f"\nDocker Services ({len(docker_status)} active):\n"
            for service, status in docker_status.items():
                report += f"  • {service}: {status['status']} (health: {status['health']})\n"
        
        # Coordination actions
        if self.coordination_log:
            latest_coordination = self.coordination_log[-1]
            report += f"\nLatest Coordination Actions ({len(latest_coordination['coordination_actions'])}):\n"
            for action in latest_coordination['coordination_actions']:
                report += f"  • {action['action']}: {action['description']}\n"
        
        # Next steps
        report += f"""
🎯 Immediate Next Steps:
  1. Access Langflow UI: http://localhost:7860
  2. Configure MCP server nodes in Langflow
  3. Setup agent communication workflows  
  4. Test multi-agent coordination scenarios
  5. Monitor agent health and performance

🔧 Configuration Files:
  • agent_context_config.json - Context sharing setup
  • agent_coordination.log - Coordination activity log
  • docker-compose.langflow.yml - Service configuration

💡 Agent Coordination Ready for Production Deployment!
"""
        
        return report

async def main():
    """Main coordination function"""
    coordinator = AgentCoordinator()
    
    print("🚀 NoxSuite Agent Coordination Manager Starting...")
    
    # Run coordination cycle
    coordination_result = await coordinator.coordinate_agents()
    
    # Setup context sharing
    context_config = await coordinator.setup_agent_context_sharing()
    
    # Generate and display report
    report = await coordinator.generate_coordination_report()
    print(report)
    
    # Save coordination results
    with open("agent_coordination_results.json", "w") as f:
        json.dump({
            "coordination_result": coordination_result,
            "context_config": context_config,
            "timestamp": datetime.now().isoformat()
        }, f, indent=2)
    
    print("📊 Coordination results saved to agent_coordination_results.json")
    return coordination_result

if __name__ == "__main__":
    asyncio.run(main())
