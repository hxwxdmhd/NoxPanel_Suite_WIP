"""
🧠 LLM Wrapper for NoxAssistant
==============================

Interface for local AI models via Ollama, providing intelligent
natural language processing and task routing for the assistant.

Supports multiple local models for different use cases:
- General conversation and help
- Network analysis and diagnostics
- Security analysis and recommendations
- Code generation and analysis
"""

import json
import logging
import time
from typing import Dict, List, Optional, Union, Any
from pathlib import Path

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

logger = logging.getLogger(__name__)

class LLMWrapper:
    """
    🧠 Local LLM Interface for NoxAssistant
    
    Provides intelligent natural language processing using local models
    via Ollama API, with fallback to rule-based processing.
    """
    
    def __init__(self, ollama_url: str = "http://localhost:11434"):
        self.ollama_url = ollama_url
        self.available_models = []
        self.model_preferences = {
            "general": "llama2:7b",
            "diagnostics": "llama2:7b",
            "security": "mistral",
            "performance": "orca-mini",
            "code": "codellama",
            "networking": "neural-chat",
            "conversation": "dolphin"
        }
        
        # Model capabilities and specializations
        self.model_specs = {
            "llama2:7b": {
                "description": "General purpose conversational AI",
                "strengths": ["conversation", "general_knowledge", "reasoning"],
                "size": "3.8GB"
            },
            "codellama": {
                "description": "Code-focused language model",
                "strengths": ["code_generation", "debugging", "programming"],
                "size": "3.8GB"
            },
            "mistral": {
                "description": "Efficient and capable language model",
                "strengths": ["analysis", "security", "reasoning"],
                "size": "4.1GB"
            },
            "orca-mini": {
                "description": "Fast and lightweight model",
                "strengths": ["quick_responses", "performance_analysis"],
                "size": "1.9GB"
            },
            "neural-chat": {
                "description": "Chat-optimized model",
                "strengths": ["conversation", "helpdesk", "instructions"],
                "size": "4.1GB"
            },
            "dolphin": {
                "description": "Helpful and harmless assistant",
                "strengths": ["assistance", "explanations", "safety"],
                "size": "3.8GB"
            }
        }
        
        # Check connection and available models
        self.connected = self.check_connection()
        if self.connected:
            self.refresh_available_models()
    
    def check_connection(self) -> bool:
        """Check if Ollama is running and accessible"""
        if not REQUESTS_AVAILABLE:
            logger.warning("Requests library not available")
            return False
        
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=3)
            return response.status_code == 200
        except Exception as e:
            logger.debug(f"Ollama connection failed: {e}")
            return False
    
    def refresh_available_models(self) -> List[str]:
        """Get list of available models from Ollama"""
        if not self.connected:
            return []
        
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            if response.status_code == 200:
                data = response.json()
                models = [model.get('name', '') for model in data.get('models', [])]
                self.available_models = [m for m in models if m]
                logger.info(f"🤖 Found {len(self.available_models)} available models: {', '.join(self.available_models)}")
                return self.available_models
        except Exception as e:
            logger.error(f"Failed to get model list: {e}")
        
        return []
    
    def get_best_model_for_task(self, task_type: str) -> str:
        """
        Select the best available model for a specific task
        
        Args:
            task_type: Type of task (diagnostics, security, performance, etc.)
            
        Returns:
            Model name to use
        """
        # Get preferred model for this task
        preferred_model = self.model_preferences.get(task_type, "llama2:7b")
        
        # Check if preferred model is available
        if preferred_model in self.available_models:
            return preferred_model
        
        # Fallback to any available model
        if self.available_models:
            return self.available_models[0]
        
        # No models available
        return None
    
    def generate_system_prompt(self, task_type: str, context: Dict[str, Any] = None) -> str:
        """
        Generate system prompt based on task type and context
        
        Args:
            task_type: Type of task being performed
            context: Additional context information
            
        Returns:
            System prompt for the AI model
        """
        context = context or {}
        
        base_prompt = """You are NoxAssistant, an intelligent network management AI assistant for Heimnetz.

Your role is to help users with network management, system diagnostics, and automation tasks.

Key guidelines:
- Be helpful, concise, and accurate
- Use ADHD-friendly formatting with bullet points and clear structure
- Include relevant emojis for visual clarity
- Provide actionable recommendations
- If you cannot complete a task, explain what's needed

"""
        
        task_specific_prompts = {
            "diagnostics": """
You specialize in system diagnostics and health monitoring.
Focus on:
- System performance metrics
- Hardware status
- Software health
- Configuration issues
- Troubleshooting steps
""",
            "security": """
You specialize in cybersecurity and threat analysis.
Focus on:
- Security vulnerabilities
- Threat assessment
- Best practices
- Risk mitigation
- Compliance requirements
""",
            "networking": """
You specialize in network analysis and connectivity.
Focus on:
- Network topology
- Device connectivity
- Performance optimization
- Protocol analysis
- Troubleshooting network issues
""",
            "performance": """
You specialize in system performance and optimization.
Focus on:
- Resource utilization
- Performance bottlenecks
- Optimization recommendations
- Capacity planning
- Efficiency improvements
""",
            "general": """
You provide general assistance and information.
Focus on:
- Clear explanations
- Step-by-step guidance
- Educational content
- Problem-solving approaches
"""
        }
        
        task_prompt = task_specific_prompts.get(task_type, task_specific_prompts["general"])
        
        # Add context information
        if context:
            context_str = "\nCurrent context:\n"
            for key, value in context.items():
                context_str += f"- {key}: {value}\n"
            base_prompt += context_str
        
        return base_prompt + task_prompt
    
    def query_model(self, 
                   prompt: str, 
                   model: str = None, 
                   task_type: str = "general",
                   context: Dict[str, Any] = None,
                   max_tokens: int = 500) -> str:
        """
        Query a local AI model with the given prompt
        
        Args:
            prompt: User's question or command
            model: Specific model to use (auto-selected if None)
            task_type: Type of task for model selection
            context: Additional context for the AI
            max_tokens: Maximum tokens in response
            
        Returns:
            AI-generated response or fallback message
        """
        if not self.connected:
            return self.fallback_response(prompt, task_type)
        
        # Select model
        if not model:
            model = self.get_best_model_for_task(task_type)
        
        if not model:
            return self.fallback_response(prompt, task_type)
        
        try:
            # Prepare the request
            system_prompt = self.generate_system_prompt(task_type, context)
            full_prompt = f"{system_prompt}\n\nUser request: {prompt}\n\nResponse:"
            
            payload = {
                "model": model,
                "prompt": full_prompt,
                "stream": False,
                "options": {
                    "num_predict": max_tokens,
                    "temperature": 0.7,
                    "top_p": 0.9
                }
            }
            
            logger.info(f"🧠 Querying {model} for {task_type} task")
            start_time = time.time()
            
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json=payload,
                timeout=30
            )
            
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                ai_response = result.get('response', '').strip()
                
                if ai_response:
                    logger.info(f"✅ AI response generated in {response_time:.2f}s")
                    return self.format_ai_response(ai_response, model, response_time)
                else:
                    logger.warning("Empty response from AI model")
            else:
                logger.error(f"AI query failed: {response.status_code}")
                
        except requests.exceptions.Timeout:
            logger.error("AI query timed out")
            return "⏰ AI processing timed out. Using fallback response.\n\n" + self.fallback_response(prompt, task_type)
        except Exception as e:
            logger.error(f"AI query error: {e}")
        
        return self.fallback_response(prompt, task_type)
    
    def format_ai_response(self, response: str, model: str, response_time: float) -> str:
        """
        Format AI response with metadata for transparency
        
        Args:
            response: Raw AI response
            model: Model that generated the response
            response_time: Time taken to generate response
            
        Returns:
            Formatted response with metadata
        """
        # Clean up response
        cleaned_response = response.strip()
        
        # Add metadata footer
        metadata = f"\n\n---\n🤖 *Generated by {model} in {response_time:.2f}s*"
        
        return cleaned_response + metadata
    
    def fallback_response(self, prompt: str, task_type: str) -> str:
        """
        Generate fallback response when AI is not available
        
        Args:
            prompt: User's original prompt
            task_type: Type of task
            
        Returns:
            Rule-based fallback response
        """
        fallback_responses = {
            "diagnostics": """
🔍 **System Diagnostics** (Fallback Mode)

I'd normally use AI analysis, but I can still help with basic diagnostics:

• Run `python main.py --status` for system overview
• Check system logs for errors
• Monitor CPU and memory usage
• Verify network connectivity
• Review recent changes or updates

💡 **Tip**: Install and configure Ollama for AI-enhanced diagnostics.
""",
            "security": """
🔒 **Security Analysis** (Fallback Mode)

Basic security checks I can suggest:

• Update all software and operating system
• Check firewall status and configuration  
• Review user accounts and permissions
• Scan for malware and vulnerabilities
• Verify backup integrity and accessibility

💡 **Tip**: Enable AI models for advanced threat analysis.
""",
            "networking": """
🌐 **Network Analysis** (Fallback Mode)

Basic network troubleshooting steps:

• Check physical connections
• Verify IP configuration (ipconfig/ifconfig)
• Test connectivity (ping, traceroute)
• Review network settings
• Check for interference or conflicts

💡 **Tip**: AI models can provide advanced network analysis.
""",
            "performance": """
📊 **Performance Analysis** (Fallback Mode)

Basic performance checks:

• Monitor CPU usage and processes
• Check memory utilization
• Review disk space and I/O
• Analyze network bandwidth usage
• Identify resource-intensive applications

💡 **Tip**: AI analysis provides deeper performance insights.
""",
            "general": """
💬 **NoxAssistant** (Basic Mode)

I'm running in fallback mode without AI processing.

Available commands:
• System diagnostics and status
• Network device scanning
• Security checks and analysis
• Performance monitoring
• Configuration management

💡 **Tip**: Install Ollama and AI models for enhanced capabilities.
"""
        }
        
        return fallback_responses.get(task_type, fallback_responses["general"])
    
    def get_model_status(self) -> Dict[str, Any]:
        """
        Get status of all available models
        
        Returns:
            Dictionary with model status information
        """
        status = {
            "connected": self.connected,
            "ollama_url": self.ollama_url,
            "available_models": self.available_models,
            "model_count": len(self.available_models),
            "preferred_models": self.model_preferences
        }
        
        if self.connected:
            # Add model details
            status["model_details"] = {}
            for model in self.available_models:
                if model in self.model_specs:
                    status["model_details"][model] = self.model_specs[model]
        
        return status
    
    def test_model(self, model: str = None) -> Dict[str, Any]:
        """
        Test a specific model with a simple query
        
        Args:
            model: Model to test (uses best available if None)
            
        Returns:
            Test results
        """
        if not model:
            model = self.get_best_model_for_task("general")
        
        if not model:
            return {"error": "No models available"}
        
        test_prompt = "Hello! Please respond with 'NoxAssistant AI test successful' to confirm you're working correctly."
        
        start_time = time.time()
        response = self.query_model(
            prompt=test_prompt,
            model=model,
            task_type="general",
            max_tokens=50
        )
        test_time = time.time() - start_time
        
        success = "test successful" in response.lower()
        
        return {
            "model": model,
            "success": success,
            "response_time": test_time,
            "response": response[:100] + "..." if len(response) > 100 else response
        }

# CLI interface for testing LLM capabilities
def main():
    """Test LLM wrapper functionality"""
    print("🧠 Testing NoxAssistant LLM Wrapper")
    print("=" * 50)
    
    llm = LLMWrapper()
    
    # Connection status
    print(f"🔗 Ollama Connection: {'✅ Connected' if llm.connected else '❌ Not available'}")
    
    if llm.connected:
        print(f"🤖 Available Models: {', '.join(llm.available_models)}")
        
        # Test model selection
        for task_type in ["diagnostics", "security", "performance"]:
            best_model = llm.get_best_model_for_task(task_type)
            print(f"  📋 {task_type}: {best_model}")
        
        # Test query
        if llm.available_models:
            print("\n🧪 Testing AI query...")
            response = llm.query_model(
                "What is the current system status?",
                task_type="diagnostics"
            )
            print(f"Response preview: {response[:200]}...")
    else:
        print("💡 Install and start Ollama to enable AI capabilities")
        print("   Visit: https://ollama.ai")
    
    # Test fallback
    print("\n🔄 Testing fallback response...")
    fallback = llm.fallback_response("Check system health", "diagnostics")
    print(f"Fallback preview: {fallback[:200]}...")

if __name__ == "__main__":
    main()
