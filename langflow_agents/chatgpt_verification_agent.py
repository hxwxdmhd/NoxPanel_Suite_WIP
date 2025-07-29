"""
ChatGPT Cross-Verification Agent - Core implementation

Submits summarized system audits and diagnostics to OpenAI ChatGPT API for
independent reasoning and validation, comparing ChatGPT's recommendations
to MCP findings and flagging discrepancies.
"""

import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import requests
import hashlib

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Path(__file__).parent / 'chatgpt_verification.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("ChatGPTVerificationAgent")

class ChatGPTVerificationAgent:
    """
    ChatGPT Cross-Verification Agent that submits system audits to OpenAI ChatGPT API
    for independent reasoning and validation, comparing recommendations to findings.
    """
    
    def __init__(self, 
                 openai_api_key: str = None,
                 api_base_url: str = "https://api.openai.com/v1",
                 model: str = "gpt-4o",
                 output_dir: str = None):
        """
        Initialize the ChatGPT Cross-Verification Agent
        
        Args:
            openai_api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            api_base_url: OpenAI API base URL
            model: Model to use for verification
            output_dir: Directory to store verification results
        """
        # Use provided API key or environment variable
        self.api_key = openai_api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            logger.warning("No OpenAI API key provided, agent will not function correctly")
        
        self.api_base_url = api_base_url
        self.model = model
        self.output_dir = output_dir or str(Path(__file__).parent / 'verification_results')
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Store verification history
        self.verification_history = []
        self.last_verification_result = {}
        
        # Cache for API responses to avoid redundant queries
        self.response_cache = {}
        self.cache_hits = 0
        self.api_calls = 0
        
        logger.info(f"ChatGPT Verification Agent initialized with model: {self.model}")
    
    def verify_system_audit(self, audit_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Submit system audit data to ChatGPT for verification
        
        Args:
            audit_data: System audit data
            
        Returns:
            Dictionary containing verification results
        """
        results = {
            "timestamp": datetime.now().isoformat(),
            "source": "system_audit",
            "verification_success": False,
            "openai_response": None,
            "discrepancies": [],
            "recommendations": [],
            "issues": []
        }
        
        try:
            if not self.api_key:
                results["issues"].append("OpenAI API key not provided")
                return results
            
            # Prepare audit summary for API
            audit_summary = self._prepare_audit_summary(audit_data)
            
            # Create prompt for OpenAI
            prompt = self._create_audit_verification_prompt(audit_summary)
            
            # Get verification from OpenAI
            openai_response = self._query_openai_api(prompt)
            
            if not openai_response:
                results["issues"].append("Failed to get response from OpenAI API")
                return results
            
            # Process the verification response
            processed_response = self._process_verification_response(openai_response, audit_data)
            
            results["verification_success"] = True
            results["openai_response"] = processed_response["response"]
            results["discrepancies"] = processed_response["discrepancies"]
            results["recommendations"] = processed_response["recommendations"]
            
            # Save verification results
            self._save_verification_results(results)
            
            # Update verification history
            self.last_verification_result = results
            self.verification_history.append({
                "timestamp": results["timestamp"],
                "source": results["source"],
                "discrepancies_count": len(results["discrepancies"]),
                "recommendations_count": len(results["recommendations"])
            })
            
            # Trim history to keep it manageable
            if len(self.verification_history) > 50:
                self.verification_history = self.verification_history[-50:]
            
            logger.info(f"System audit verification completed with {len(results['discrepancies'])} discrepancies and {len(results['recommendations'])} recommendations")
            
        except Exception as e:
            error_msg = f"Error verifying system audit: {str(e)}"
            logger.error(error_msg)
            results["issues"].append(error_msg)
        
        return results
    
    def verify_integration_status(self, integration_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Submit integration status data to ChatGPT for verification
        
        Args:
            integration_data: Integration status data
            
        Returns:
            Dictionary containing verification results
        """
        results = {
            "timestamp": datetime.now().isoformat(),
            "source": "integration_status",
            "verification_success": False,
            "openai_response": None,
            "discrepancies": [],
            "recommendations": [],
            "issues": []
        }
        
        try:
            if not self.api_key:
                results["issues"].append("OpenAI API key not provided")
                return results
            
            # Prepare integration summary for API
            integration_summary = self._prepare_integration_summary(integration_data)
            
            # Create prompt for OpenAI
            prompt = self._create_integration_verification_prompt(integration_summary)
            
            # Get verification from OpenAI
            openai_response = self._query_openai_api(prompt)
            
            if not openai_response:
                results["issues"].append("Failed to get response from OpenAI API")
                return results
            
            # Process the verification response
            processed_response = self._process_verification_response(openai_response, integration_data)
            
            results["verification_success"] = True
            results["openai_response"] = processed_response["response"]
            results["discrepancies"] = processed_response["discrepancies"]
            results["recommendations"] = processed_response["recommendations"]
            
            # Save verification results
            self._save_verification_results(results)
            
            # Update verification history
            self.verification_history.append({
                "timestamp": results["timestamp"],
                "source": results["source"],
                "discrepancies_count": len(results["discrepancies"]),
                "recommendations_count": len(results["recommendations"])
            })
            
            logger.info(f"Integration status verification completed with {len(results['discrepancies'])} discrepancies and {len(results['recommendations'])} recommendations")
            
        except Exception as e:
            error_msg = f"Error verifying integration status: {str(e)}"
            logger.error(error_msg)
            results["issues"].append(error_msg)
        
        return results
    
    def verify_workflow_results(self, workflow_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Submit workflow execution results to ChatGPT for verification
        
        Args:
            workflow_data: Workflow execution results
            
        Returns:
            Dictionary containing verification results
        """
        results = {
            "timestamp": datetime.now().isoformat(),
            "source": "workflow_results",
            "verification_success": False,
            "openai_response": None,
            "discrepancies": [],
            "recommendations": [],
            "issues": []
        }
        
        try:
            if not self.api_key:
                results["issues"].append("OpenAI API key not provided")
                return results
            
            # Prepare workflow summary for API
            workflow_summary = self._prepare_workflow_summary(workflow_data)
            
            # Create prompt for OpenAI
            prompt = self._create_workflow_verification_prompt(workflow_summary)
            
            # Get verification from OpenAI
            openai_response = self._query_openai_api(prompt)
            
            if not openai_response:
                results["issues"].append("Failed to get response from OpenAI API")
                return results
            
            # Process the verification response
            processed_response = self._process_verification_response(openai_response, workflow_data)
            
            results["verification_success"] = True
            results["openai_response"] = processed_response["response"]
            results["discrepancies"] = processed_response["discrepancies"]
            results["recommendations"] = processed_response["recommendations"]
            
            # Save verification results
            self._save_verification_results(results)
            
            # Update verification history
            self.verification_history.append({
                "timestamp": results["timestamp"],
                "source": results["source"],
                "discrepancies_count": len(results["discrepancies"]),
                "recommendations_count": len(results["recommendations"])
            })
            
            logger.info(f"Workflow results verification completed with {len(results['discrepancies'])} discrepancies and {len(results['recommendations'])} recommendations")
            
        except Exception as e:
            error_msg = f"Error verifying workflow results: {str(e)}"
            logger.error(error_msg)
            results["issues"].append(error_msg)
        
        return results
    
    def verify_overall_system_status(self) -> Dict[str, Any]:
        """
        Submit overall system status to ChatGPT for verification
        
        Returns:
            Dictionary containing verification results
        """
        results = {
            "timestamp": datetime.now().isoformat(),
            "source": "overall_system",
            "verification_success": False,
            "openai_response": None,
            "discrepancies": [],
            "recommendations": [],
            "issues": []
        }
        
        try:
            if not self.api_key:
                results["issues"].append("OpenAI API key not provided")
                return results
            
            # Collect system status data from various sources
            system_status = self._collect_system_status_data()
            
            # Create prompt for OpenAI
            prompt = self._create_system_status_verification_prompt(system_status)
            
            # Get verification from OpenAI
            openai_response = self._query_openai_api(prompt)
            
            if not openai_response:
                results["issues"].append("Failed to get response from OpenAI API")
                return results
            
            # Process the verification response
            processed_response = self._process_verification_response(openai_response, system_status)
            
            results["verification_success"] = True
            results["openai_response"] = processed_response["response"]
            results["discrepancies"] = processed_response["discrepancies"]
            results["recommendations"] = processed_response["recommendations"]
            
            # Save verification results
            self._save_verification_results(results)
            
            # Update verification history
            self.last_verification_result = results
            self.verification_history.append({
                "timestamp": results["timestamp"],
                "source": results["source"],
                "discrepancies_count": len(results["discrepancies"]),
                "recommendations_count": len(results["recommendations"])
            })
            
            logger.info(f"Overall system status verification completed with {len(results['discrepancies'])} discrepancies and {len(results['recommendations'])} recommendations")
            
        except Exception as e:
            error_msg = f"Error verifying overall system status: {str(e)}"
            logger.error(error_msg)
            results["issues"].append(error_msg)
        
        return results
    
    def _prepare_audit_summary(self, audit_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare a summarized version of audit data for the API
        
        Args:
            audit_data: Raw audit data
            
        Returns:
            Dictionary containing summarized audit data
        """
        summary = {
            "timestamp": audit_data.get("timestamp", "unknown"),
            "system_overview": {}
        }
        
        # Extract system info
        if "system_info" in audit_data:
            summary["system_overview"]["os"] = audit_data["system_info"].get("os", "unknown")
            summary["system_overview"]["python_version"] = audit_data["system_info"].get("python_version", "unknown")
        
        # Extract Docker status
        if "docker" in audit_data:
            docker_data = audit_data["docker"]
            summary["docker"] = {
                "containers": docker_data.get("containers", {}),
                "nox_services": docker_data.get("container_details", {}).get("nox_services", {}),
                "errors": docker_data.get("errors", [])
            }
        
        # Extract MCP status
        if "mcp" in audit_data:
            mcp_data = audit_data["mcp"]
            summary["mcp"] = {
                "health": mcp_data.get("health", False),
                "errors": mcp_data.get("errors", [])
            }
        
        # Extract Langflow status
        if "langflow" in audit_data:
            langflow_data = audit_data["langflow"]
            summary["langflow"] = {
                "health": langflow_data.get("health", False),
                "flows": langflow_data.get("flows", {}),
                "errors": langflow_data.get("errors", [])
            }
        
        # Extract Copilot tools status
        if "copilot" in audit_data:
            copilot_data = audit_data["copilot"]
            summary["copilot"] = {
                "tool_usage": copilot_data.get("tool_usage", {}),
                "constraints": copilot_data.get("constraints", {}),
                "errors": copilot_data.get("errors", [])
            }
        
        # Extract regressions
        if "regressions" in audit_data:
            summary["regressions"] = {
                "detected": audit_data["regressions"].get("detected", False),
                "issues": audit_data["regressions"].get("issues", [])
            }
        
        return summary
    
    def _prepare_integration_summary(self, integration_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare a summarized version of integration data for the API
        
        Args:
            integration_data: Raw integration data
            
        Returns:
            Dictionary containing summarized integration data
        """
        summary = {
            "timestamp": integration_data.get("timestamp", "unknown"),
            "connectivity": integration_data.get("connectivity_established", False),
            "agent_definitions_synced": integration_data.get("agent_definitions_synced", False),
            "copilot_integration_active": integration_data.get("copilot_integration_active", False),
            "errors": integration_data.get("errors", [])
        }
        
        return summary
    
    def _prepare_workflow_summary(self, workflow_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare a summarized version of workflow data for the API
        
        Args:
            workflow_data: Raw workflow data
            
        Returns:
            Dictionary containing summarized workflow data
        """
        summary = {
            "timestamp": workflow_data.get("timestamp", "unknown"),
            "workflows_total": workflow_data.get("workflows_total", 0),
            "workflows_passed": workflow_data.get("workflows_passed", 0),
            "workflows_failed": workflow_data.get("workflows_failed", 0),
            "errors": workflow_data.get("errors", [])
        }
        
        # Include summarized workflow results
        if "workflow_results" in workflow_data:
            summary["workflow_results"] = {}
            for workflow_name, result in workflow_data["workflow_results"].items():
                summary["workflow_results"][workflow_name] = {
                    "success": result.get("success", False),
                    "steps_passed": result.get("steps_passed", 0),
                    "steps_total": result.get("steps_total", 0)
                }
        
        return summary
    
    def _collect_system_status_data(self) -> Dict[str, Any]:
        """
        Collect system status data from various sources
        
        Returns:
            Dictionary containing system status data
        """
        system_status = {
            "timestamp": datetime.now().isoformat(),
            "audit": None,
            "integration": None,
            "workflow": None,
            "data_sources": []
        }
        
        try:
            # Try to find the latest audit results
            audit_dir = Path(__file__).parent.parent / "langflow_agents" / "audit_results"
            if audit_dir.exists():
                latest_audit = None
                latest_time = 0
                
                for audit_file in audit_dir.glob("*.json"):
                    if "latest" in audit_file.name:
                        try:
                            with open(audit_file, 'r') as f:
                                latest_audit = json.load(f)
                            system_status["audit"] = self._prepare_audit_summary(latest_audit)
                            system_status["data_sources"].append(str(audit_file))
                            break
                        except Exception as e:
                            logger.error(f"Error reading latest audit file: {e}")
                    
                    # If no "latest" file, find the most recent one
                    file_time = os.path.getmtime(audit_file)
                    if file_time > latest_time:
                        latest_time = file_time
                        try:
                            with open(audit_file, 'r') as f:
                                latest_audit = json.load(f)
                        except:
                            pass
                
                if not system_status["audit"] and latest_audit:
                    system_status["audit"] = self._prepare_audit_summary(latest_audit)
                    system_status["data_sources"].append("most_recent_audit_file")
            
            # Try to find system status file
            status_file = Path(__file__).parent.parent / "system_status.json"
            if status_file.exists():
                try:
                    with open(status_file, 'r') as f:
                        status_data = json.load(f)
                    system_status["system"] = status_data
                    system_status["data_sources"].append(str(status_file))
                except:
                    pass
            
            # Try to find agent collaboration config
            config_file = Path(__file__).parent.parent / "agent_collaboration_config.json"
            if config_file.exists():
                try:
                    with open(config_file, 'r') as f:
                        config_data = json.load(f)
                    system_status["agent_config"] = config_data
                    system_status["data_sources"].append(str(config_file))
                except:
                    pass
            
            # Try to find agent collaboration results
            results_file = Path(__file__).parent.parent / "agent_coordination_results.json"
            if results_file.exists():
                try:
                    with open(results_file, 'r') as f:
                        results_data = json.load(f)
                    system_status["coordination_results"] = results_data
                    system_status["data_sources"].append(str(results_file))
                except:
                    pass
            
            # If we don't have any data, add a note
            if len(system_status["data_sources"]) == 0:
                system_status["warning"] = "No system status data sources found"
                
        except Exception as e:
            logger.error(f"Error collecting system status data: {e}")
            system_status["error"] = str(e)
        
        return system_status
    
    def _create_audit_verification_prompt(self, audit_summary: Dict[str, Any]) -> str:
        """
        Create a prompt for OpenAI to verify audit data
        
        Args:
            audit_summary: Summarized audit data
            
        Returns:
            String containing the prompt
        """
        prompt = """
You are a specialized AI expert system diagnostician with deep knowledge of Docker, Python, MCP Server, Langflow, and agent-based systems. You're asked to independently analyze and verify this system audit data to identify issues, potential problems, and recommend improvements.

System Audit Data:
```json
{audit_data}
```

Please provide a structured analysis including:

1. **Verification Results**: Confirm which parts of the system appear healthy and which have issues
2. **Discrepancies**: Identify any logical inconsistencies or concerning patterns in the data
3. **Recommendations**: Suggest specific actions to resolve issues or improve system health
4. **Critical Issues**: Flag any urgent problems that require immediate attention
5. **Overall Assessment**: Provide a one-paragraph summary of the system's overall health

Format your response in a structured way, with clear sections and bullet points for each category. Focus on actionable insights rather than just repeating the data.
""".replace("{audit_data}", json.dumps(audit_summary, indent=2))
        
        return prompt
    
    def _create_integration_verification_prompt(self, integration_summary: Dict[str, Any]) -> str:
        """
        Create a prompt for OpenAI to verify integration status
        
        Args:
            integration_summary: Summarized integration data
            
        Returns:
            String containing the prompt
        """
        prompt = """
You are a specialized AI expert in system integration with deep knowledge of Docker, Python, MCP Server, Langflow, and agent-based systems. You're asked to independently analyze and verify this integration status data to identify connection issues, sync problems, and recommend improvements.

Integration Status Data:
```json
{integration_data}
```

Please provide a structured analysis including:

1. **Verification Results**: Confirm which integration aspects are working properly and which have issues
2. **Discrepancies**: Identify any logical inconsistencies or concerning patterns in the integration data
3. **Recommendations**: Suggest specific actions to resolve integration issues
4. **Critical Issues**: Flag any urgent integration problems that require immediate attention
5. **Overall Assessment**: Provide a one-paragraph summary of the system's integration health

Format your response in a structured way, with clear sections and bullet points for each category. Focus on actionable insights rather than just repeating the data.
""".replace("{integration_data}", json.dumps(integration_summary, indent=2))
        
        return prompt
    
    def _create_workflow_verification_prompt(self, workflow_summary: Dict[str, Any]) -> str:
        """
        Create a prompt for OpenAI to verify workflow execution results
        
        Args:
            workflow_summary: Summarized workflow data
            
        Returns:
            String containing the prompt
        """
        prompt = """
You are a specialized AI expert in workflow systems with deep knowledge of Docker, Python, MCP Server, Langflow, and agent-based systems. You're asked to independently analyze and verify these workflow execution results to identify failures, execution problems, and recommend improvements.

Workflow Execution Data:
```json
{workflow_data}
```

Please provide a structured analysis including:

1. **Verification Results**: Confirm which workflows executed successfully and which failed
2. **Discrepancies**: Identify any logical inconsistencies or concerning patterns in the workflow executions
3. **Recommendations**: Suggest specific actions to resolve workflow failures or improve execution
4. **Critical Issues**: Flag any urgent workflow problems that require immediate attention
5. **Overall Assessment**: Provide a one-paragraph summary of the workflow execution health

Format your response in a structured way, with clear sections and bullet points for each category. Focus on actionable insights rather than just repeating the data.
""".replace("{workflow_data}", json.dumps(workflow_summary, indent=2))
        
        return prompt
    
    def _create_system_status_verification_prompt(self, system_status: Dict[str, Any]) -> str:
        """
        Create a prompt for OpenAI to verify overall system status
        
        Args:
            system_status: System status data
            
        Returns:
            String containing the prompt
        """
        prompt = """
You are a specialized AI expert system diagnostician with deep knowledge of Docker, Python, MCP Server, Langflow, and agent-based systems. You're asked to independently analyze and verify this comprehensive system status data to provide an overall assessment, identify issues, and recommend improvements.

System Status Data:
```json
{system_data}
```

Please provide a structured analysis including:

1. **Verification Results**: Confirm the overall system health across all components
2. **Discrepancies**: Identify any logical inconsistencies or concerning patterns across the system
3. **Recommendations**: Suggest specific actions to resolve issues or improve overall system health
4. **Critical Issues**: Flag any urgent problems that require immediate attention
5. **Overall Assessment**: Provide a one-paragraph executive summary of the system's health

Format your response in a structured way, with clear sections and bullet points for each category. Focus on actionable insights rather than just repeating the data. Be sure to highlight any potential security issues or performance bottlenecks.
""".replace("{system_data}", json.dumps(system_status, indent=2))
        
        return prompt
    
    def _query_openai_api(self, prompt: str) -> Dict[str, Any]:
        """
        Query the OpenAI API with a prompt
        
        Args:
            prompt: The prompt to send to the API
            
        Returns:
            Dictionary containing API response or None if failed
        """
        # Check cache first to avoid redundant API calls
        prompt_hash = hashlib.md5(prompt.encode()).hexdigest()
        if prompt_hash in self.response_cache:
            self.cache_hits += 1
            logger.info(f"Using cached response (hit {self.cache_hits}, calls {self.api_calls})")
            return self.response_cache[prompt_hash]
        
        try:
            url = f"{self.api_base_url}/chat/completions"
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": "You are an AI expert system diagnostician specializing in Docker, Python, MCP Server, Langflow, and agent-based systems. Your task is to analyze system data and provide verification, identify discrepancies, and recommend improvements."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.2,
                "max_tokens": 1024
            }
            
            logger.info(f"Sending request to OpenAI API using model {self.model}")
            response = requests.post(url, headers=headers, json=data, timeout=30)
            self.api_calls += 1
            
            if response.status_code == 200:
                response_data = response.json()
                
                # Extract content from response
                content = response_data["choices"][0]["message"]["content"]
                
                result = {
                    "response": content,
                    "model": self.model,
                    "timestamp": datetime.now().isoformat()
                }
                
                # Cache the response
                if len(self.response_cache) > 50:
                    # Remove oldest cache entry if cache is too large
                    oldest_key = next(iter(self.response_cache))
                    del self.response_cache[oldest_key]
                
                self.response_cache[prompt_hash] = result
                return result
            else:
                logger.error(f"OpenAI API request failed with status {response.status_code}: {response.text}")
                return None
        except Exception as e:
            logger.error(f"Error querying OpenAI API: {e}")
            return None
    
    def _process_verification_response(self, openai_response: Dict[str, Any], source_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the response from OpenAI to extract discrepancies and recommendations
        
        Args:
            openai_response: Response from OpenAI API
            source_data: Original data that was verified
            
        Returns:
            Dictionary containing processed response with discrepancies and recommendations
        """
        result = {
            "response": openai_response.get("response", ""),
            "discrepancies": [],
            "recommendations": []
        }
        
        try:
            content = openai_response.get("response", "")
            
            # Extract discrepancies section
            if "Discrepancies:" in content or "**Discrepancies**" in content:
                discrepancies_section = content.split("Discrepancies:", 1)[-1].split("Recommendations:", 1)[0]
                discrepancies_section = discrepancies_section.split("**Recommendations**", 1)[0]
                
                # Extract bullet points
                for line in discrepancies_section.split("\n"):
                    line = line.strip()
                    if line.startswith("- ") or line.startswith("* "):
                        result["discrepancies"].append(line[2:])
            
            # Extract recommendations section
            if "Recommendations:" in content or "**Recommendations**" in content:
                recommendations_section = content.split("Recommendations:", 1)[-1].split("Critical Issues:", 1)[0]
                recommendations_section = recommendations_section.split("**Critical Issues**", 1)[0]
                
                # Extract bullet points
                for line in recommendations_section.split("\n"):
                    line = line.strip()
                    if line.startswith("- ") or line.startswith("* "):
                        result["recommendations"].append(line[2:])
            
            # Extract critical issues and add to discrepancies if they exist
            if "Critical Issues:" in content or "**Critical Issues**" in content:
                critical_section = content.split("Critical Issues:", 1)[-1].split("Overall Assessment:", 1)[0]
                critical_section = critical_section.split("**Overall Assessment**", 1)[0]
                
                # Extract bullet points
                for line in critical_section.split("\n"):
                    line = line.strip()
                    if line.startswith("- ") or line.startswith("* "):
                        # Add critical issues to discrepancies with a marker
                        result["discrepancies"].append("[CRITICAL] " + line[2:])
        except Exception as e:
            logger.error(f"Error processing verification response: {e}")
        
        return result
    
    def _save_verification_results(self, results: Dict[str, Any]) -> None:
        """
        Save verification results to output directory
        
        Args:
            results: Verification results to save
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(self.output_dir, f"verification_{results['source']}_{timestamp}.json")
        
        try:
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2)
            logger.info(f"Verification results saved to {output_file}")
            
            # Also save latest verification result for quick access
            latest_file = os.path.join(self.output_dir, f"latest_{results['source']}_verification.json")
            with open(latest_file, 'w') as f:
                json.dump(results, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save verification results: {e}")
    
    def run_continuous_verification(self, interval: int = 1800, run_once: bool = False) -> None:
        """
        Run continuous verification at specified intervals
        
        Args:
            interval: Time between verifications in seconds (default: 30 minutes)
            run_once: If True, run only one verification and return
        """
        logger.info(f"Starting {'single' if run_once else 'continuous'} verification")
        
        try:
            while True:
                # Verify overall system status
                self.verify_overall_system_status()
                
                if run_once:
                    logger.info("Single verification completed, exiting loop")
                    break
                
                logger.info(f"Sleeping for {interval} seconds until next verification")
                time.sleep(interval)
        except KeyboardInterrupt:
            logger.info("Verification process interrupted by user")
        except Exception as e:
            logger.error(f"Error in continuous verification loop: {e}")
    
    def get_verification_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the latest verification results
        
        Returns:
            Dictionary containing verification summary
        """
        summary = {
            "timestamp": datetime.now().isoformat(),
            "verification_history": len(self.verification_history),
            "last_verification": None,
            "total_api_calls": self.api_calls,
            "cache_hits": self.cache_hits
        }
        
        if self.last_verification_result:
            summary["last_verification"] = {
                "timestamp": self.last_verification_result.get("timestamp", "unknown"),
                "source": self.last_verification_result.get("source", "unknown"),
                "discrepancies_count": len(self.last_verification_result.get("discrepancies", [])),
                "recommendations_count": len(self.last_verification_result.get("recommendations", [])),
                "success": self.last_verification_result.get("verification_success", False)
            }
        
        # Get recent history
        if self.verification_history:
            summary["recent_verifications"] = self.verification_history[-5:]
        
        return summary


# For importing as module
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="ChatGPT Cross-Verification Agent")
    parser.add_argument("--once", action="store_true", help="Run verification once and exit")
    parser.add_argument("--api-key", type=str, help="OpenAI API key (will use OPENAI_API_KEY env var if not provided)")
    args = parser.parse_args()
    
    api_key = args.api_key or os.environ.get("OPENAI_API_KEY") or "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"
    
    if not api_key:
        print("Error: No OpenAI API key provided. Please provide with --api-key or set OPENAI_API_KEY environment variable.")
        sys.exit(1)
    
    verifier = ChatGPTVerificationAgent(openai_api_key=api_key)
    
    if args.once:
        print("Running verification once")
        results = verifier.verify_overall_system_status()
        print(f"Verification completed - Success: {results['verification_success']}")
        
        if results["discrepancies"]:
            print("\nDiscrepancies found:")
            for item in results["discrepancies"]:
                print(f"  - {item}")
        
        if results["recommendations"]:
            print("\nRecommendations:")
            for item in results["recommendations"]:
                print(f"  - {item}")
        
        if results["issues"]:
            print("\nIssues:")
            for item in results["issues"]:
                print(f"  - {item}")
    else:
        print("Starting verification agent")
        print("Press Ctrl+C to stop")
        verifier.run_continuous_verification()
