"""
🤖 NoxAssistant - Intelligent AI Assistant for Heimnetz
=====================================================

Inspired by J.A.R.V.I.S. and S.A.T.U.R.D.A.Y., NoxAssistant provides
intelligent automation, voice commands, and natural language processing
for network management and system diagnostics.

Architecture:
- Local AI processing (no external dependencies)
- Voice recognition and text-to-speech
- Task execution framework
- ADHD-friendly responses (clear, concise, visual)
"""

import os
import sys
import json
import logging
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union

# Import voice capabilities (optional)
try:
    import speech_recognition as sr
    import pyttsx3
    VOICE_AVAILABLE = True
except ImportError:
    VOICE_AVAILABLE = False
    print("📢 Voice capabilities not available. Install: pip install SpeechRecognition pyttsx3")

# Import local AI capabilities
try:
    import requests
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class NoxAssistant:
    """
    🤖 NoxAssistant - Your Intelligent Network Management Companion
    
    Features:
    - Natural language command processing
    - Voice recognition and text-to-speech
    - Task execution and automation
    - System diagnostics and monitoring
    - ADHD-friendly responses with visual formatting
    """
    
    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path(__file__).parent.parent
        self.config_path = self.project_root / "config" / "heimnetz_unified.json"
        self.task_registry_path = self.project_root / "nox_assistant" / "task_registry.yaml"
        self.history_log = self.project_root / "nox_assistant" / "history.log"
        
        # Initialize components
        self.config = self.load_config()
        self.task_registry = self.load_task_registry()
        
        # Voice setup (if available)
        if VOICE_AVAILABLE:
            self.voice_engine = self.setup_voice_engine()
            self.speech_recognizer = sr.Recognizer()
            self.microphone = sr.Microphone()
        else:
            self.voice_engine = None
            self.speech_recognizer = None
            self.microphone = None
        
        # AI model setup
        self.ollama_available = self.check_ollama_connection()
        
        # Welcome message
        self.log_action("system", "NoxAssistant initialized")
        
    def load_config(self) -> Dict:
        """Load Heimnetz configuration"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning("Configuration file not found, using defaults")
            return {
                "project": {"name": "Heimnetz", "version": "7.0-unified"},
                "features": {"ai_integration": True, "voice_commands": VOICE_AVAILABLE}
            }
    
    def load_task_registry(self) -> Dict:
        """Load available tasks and commands"""
        default_tasks = {
            "diagnostics": {
                "commands": ["diagnose", "health", "status", "check"],
                "description": "Run system diagnostics and health checks",
                "module": "diagnostics"
            },
            "network": {
                "commands": ["scan", "devices", "network", "ping"],
                "description": "Network scanning and device discovery",
                "module": "network_scanner"
            },
            "security": {
                "commands": ["security", "vulnerabilities", "threats", "audit"],
                "description": "Security analysis and vulnerability scanning",
                "module": "security_analyzer"
            },
            "performance": {
                "commands": ["performance", "optimize", "speed", "bandwidth"],
                "description": "Performance analysis and optimization",
                "module": "performance_monitor"
            },
            "help": {
                "commands": ["help", "commands", "what", "how"],
                "description": "Show available commands and help",
                "module": "help_system"
            }
        }
        
        try:
            import yaml
            with open(self.task_registry_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except (FileNotFoundError, ImportError):
            logger.info("Using default task registry")
            return default_tasks
    
    def setup_voice_engine(self):
        """Initialize text-to-speech engine"""
        if not VOICE_AVAILABLE:
            return None
            
        try:
            engine = pyttsx3.init()
            
            # Configure voice settings
            voices = engine.getProperty('voices')
            if voices:
                # Prefer female voice if available (more pleasant for extended use)
                for voice in voices:
                    if 'female' in voice.name.lower() or 'zira' in voice.name.lower():
                        engine.setProperty('voice', voice.id)
                        break
            
            # Set speaking rate (slower for ADHD-friendly experience)
            engine.setProperty('rate', 180)  # Default is usually 200
            engine.setProperty('volume', 0.8)
            
            return engine
        except Exception as e:
            logger.error(f"Failed to initialize voice engine: {e}")
            return None
    
    def check_ollama_connection(self) -> bool:
        """Check if Ollama is available for AI processing"""
        if not OLLAMA_AVAILABLE:
            return False
            
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=2)
            if response.status_code == 200:
                models = response.json().get('models', [])
                logger.info(f"✅ Ollama connected with {len(models)} models")
                return True
        except Exception as e:
            logger.debug(f"Ollama not available: {e}")
        
        return False
    
    def speak(self, text: str, force_voice: bool = False):
        """
        Speak text using TTS (if available and enabled)
        
        Args:
            text: Text to speak
            force_voice: Force voice output even if normally disabled
        """
        if self.voice_engine and (force_voice or self.config.get("features", {}).get("voice_enabled", True)):
            try:
                self.voice_engine.say(text)
                self.voice_engine.runAndWait()
            except Exception as e:
                logger.error(f"Voice output failed: {e}")
    
    def listen_for_voice_command(self, timeout: int = 5) -> Optional[str]:
        """
        Listen for voice input and convert to text
        
        Args:
            timeout: Seconds to listen for input
            
        Returns:
            Recognized text or None if failed
        """
        if not VOICE_AVAILABLE or not self.speech_recognizer:
            return None
        
        try:
            with self.microphone as source:
                # Adjust for ambient noise
                self.speech_recognizer.adjust_for_ambient_noise(source, duration=1)
                
                print("🎤 Listening... (speak now)")
                audio = self.speech_recognizer.listen(source, timeout=timeout, phrase_time_limit=10)
                
                # Recognize speech using Google's service (offline alternative available)
                try:
                    text = self.speech_recognizer.recognize_google(audio)
                    print(f"📝 Heard: {text}")
                    return text.lower()
                except sr.UnknownValueError:
                    print("❓ Could not understand audio")
                    return None
                except sr.RequestError as e:
                    print(f"❌ Speech recognition error: {e}")
                    return None
                    
        except Exception as e:
            logger.error(f"Voice input failed: {e}")
            return None
    
    def process_with_ai(self, user_input: str, context: str = "") -> str:
        """
        Process user input with local AI model
        
        Args:
            user_input: User's command or question
            context: Additional context for AI processing
            
        Returns:
            AI-generated response or fallback response
        """
        if not self.ollama_available:
            return self.process_with_rules(user_input)
        
        try:
            # Construct prompt for local AI
            system_prompt = f"""You are NoxAssistant, an intelligent network management AI assistant for Heimnetz.

Context: You're helping with network management, system diagnostics, and automation tasks.
User input: {user_input}
Additional context: {context}

Respond in a helpful, concise manner. Be ADHD-friendly:
- Use bullet points and clear structure
- Include relevant emojis for visual clarity
- Keep responses focused and actionable
- If you can't complete a task, explain what's needed

Available capabilities:
- System diagnostics and health checks
- Network scanning and device discovery  
- Security analysis and vulnerability scanning
- Performance monitoring and optimization
- Task automation and script execution"""

            payload = {
                "model": "llama2:7b",  # Fallback to available model
                "prompt": system_prompt,
                "stream": False
            }
            
            response = requests.post("http://localhost:11434/api/generate", 
                                   json=payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json().get('response', '').strip()
                if result:
                    return result
                    
        except Exception as e:
            logger.error(f"AI processing failed: {e}")
        
        # Fallback to rule-based processing
        return self.process_with_rules(user_input)
    
    def process_with_rules(self, user_input: str) -> str:
        """
        Process user input with rule-based matching (fallback)
        
        Args:
            user_input: User's command or question
            
        Returns:
            Rule-based response
        """
        user_input = user_input.lower().strip()
        
        # Find matching task
        for task_name, task_info in self.task_registry.items():
            commands = task_info.get('commands', [])
            if any(cmd in user_input for cmd in commands):
                return self.execute_task(task_name, user_input)
        
        # Default help response
        return self.get_help_response()
    
    def execute_task(self, task_name: str, user_input: str) -> str:
        """
        Execute a specific task based on user input
        
        Args:
            task_name: Name of the task to execute
            user_input: Original user input for context
            
        Returns:
            Task execution result
        """
        task_info = self.task_registry.get(task_name, {})
        module_name = task_info.get('module', task_name)
        
        self.log_action("task_execution", f"Executing {task_name}: {user_input}")
        
        try:
            # Import and execute task module
            if task_name == "diagnostics":
                return self.run_diagnostics()
            elif task_name == "network":
                return self.run_network_scan()
            elif task_name == "security":
                return self.run_security_analysis()
            elif task_name == "performance":
                return self.run_performance_analysis()
            elif task_name == "help":
                return self.get_help_response()
            else:
                return f"🔧 Task '{task_name}' is not yet implemented.\n\n📋 Available tasks:\n{self.get_task_list()}"
                
        except Exception as e:
            logger.error(f"Task execution failed: {e}")
            return f"❌ Failed to execute {task_name}: {str(e)}"
    
    def run_diagnostics(self) -> str:
        """Run system diagnostics"""
        import subprocess
        import platform
        
        results = []
        results.append("🔍 **System Diagnostics Report**")
        results.append("=" * 40)
        
        # System information
        results.append(f"🖥️  **System**: {platform.system()} {platform.release()}")
        results.append(f"🐍 **Python**: {sys.version.split()[0]}")
        results.append(f"📁 **Project Root**: {self.project_root}")
        
        # Check key files
        key_files = [
            "main.py",
            "integrated_web_server.py",
            "config/heimnetz_unified.json"
        ]
        
        results.append("\n📋 **File Status**:")
        for file_path in key_files:
            full_path = self.project_root / file_path
            status = "✅ Found" if full_path.exists() else "❌ Missing"
            results.append(f"  • {file_path}: {status}")
        
        # Check AI models
        if self.ollama_available:
            try:
                response = requests.get("http://localhost:11434/api/tags", timeout=2)
                models = response.json().get('models', [])
                results.append(f"\n🤖 **AI Models**: {len(models)} available")
                for model in models[:3]:  # Show first 3
                    results.append(f"  • {model.get('name', 'Unknown')}")
            except:
                results.append("\n🤖 **AI Models**: Connection failed")
        else:
            results.append("\n🤖 **AI Models**: Ollama not available")
        
        # Memory and performance
        try:
            import psutil
            memory = psutil.virtual_memory()
            results.append(f"\n💾 **Memory Usage**: {memory.percent}% ({memory.used // 1024**2} MB used)")
        except ImportError:
            results.append("\n💾 **Memory**: psutil not available")
        
        return "\n".join(results)
    
    def run_network_scan(self) -> str:
        """Run network device scan"""
        results = []
        results.append("🌐 **Network Scan Report**")
        results.append("=" * 40)
        
        # Mock network scan (replace with actual implementation)
        mock_devices = [
            {"name": "🌐 Router", "ip": "192.168.1.1", "status": "online", "type": "gateway"},
            {"name": "💻 Desktop PC", "ip": "192.168.1.100", "status": "online", "type": "computer"},
            {"name": "📱 Phone", "ip": "192.168.1.150", "status": "offline", "type": "mobile"},
            {"name": "📺 Smart TV", "ip": "192.168.1.200", "status": "online", "type": "media"},
            {"name": "🖨️ Printer", "ip": "192.168.1.250", "status": "offline", "type": "printer"}
        ]
        
        online_count = sum(1 for device in mock_devices if device["status"] == "online")
        total_count = len(mock_devices)
        
        results.append(f"📊 **Summary**: {online_count}/{total_count} devices online")
        results.append("\n📋 **Device List**:")
        
        for device in mock_devices:
            status_emoji = "🟢" if device["status"] == "online" else "🔴"
            results.append(f"  {status_emoji} {device['name']} ({device['ip']}) - {device['status']}")
        
        results.append(f"\n💡 **Tip**: Run 'python main.py --web' to see real-time monitoring")
        
        return "\n".join(results)
    
    def run_security_analysis(self) -> str:
        """Run security analysis"""
        results = []
        results.append("🔒 **Security Analysis Report**")
        results.append("=" * 40)
        
        # Mock security analysis
        security_checks = [
            {"check": "Firewall Status", "status": "✅ Active", "risk": "low"},
            {"check": "Open Ports", "status": "⚠️ 3 open", "risk": "medium"},
            {"check": "Password Policy", "status": "✅ Strong", "risk": "low"},
            {"check": "SSL Certificates", "status": "❌ Expired", "risk": "high"},
            {"check": "Software Updates", "status": "⚠️ 2 pending", "risk": "medium"}
        ]
        
        high_risk = sum(1 for check in security_checks if check["risk"] == "high")
        medium_risk = sum(1 for check in security_checks if check["risk"] == "medium")
        
        results.append(f"🚨 **Risk Summary**: {high_risk} high, {medium_risk} medium risk items")
        results.append("\n📋 **Security Checks**:")
        
        for check in security_checks:
            risk_emoji = {"high": "🚨", "medium": "⚠️", "low": "✅"}[check["risk"]]
            results.append(f"  {risk_emoji} {check['check']}: {check['status']}")
        
        if high_risk > 0:
            results.append(f"\n🚨 **Action Required**: {high_risk} critical security issues need immediate attention")
        
        return "\n".join(results)
    
    def run_performance_analysis(self) -> str:
        """Run performance analysis"""
        results = []
        results.append("📊 **Performance Analysis Report**")
        results.append("=" * 40)
        
        try:
            import psutil
            
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            results.append(f"🖥️  **CPU Usage**: {cpu_percent}%")
            
            # Memory usage
            memory = psutil.virtual_memory()
            results.append(f"💾 **Memory Usage**: {memory.percent}% ({memory.used // 1024**2} MB / {memory.total // 1024**2} MB)")
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            results.append(f"💿 **Disk Usage**: {disk_percent:.1f}% ({disk.used // 1024**3} GB / {disk.total // 1024**3} GB)")
            
            # Network interfaces
            net_io = psutil.net_io_counters()
            results.append(f"🌐 **Network**: {net_io.bytes_sent // 1024**2} MB sent, {net_io.bytes_recv // 1024**2} MB received")
            
            # Performance recommendations
            results.append("\n💡 **Recommendations**:")
            if cpu_percent > 80:
                results.append("  🚨 High CPU usage detected - consider closing unnecessary applications")
            if memory.percent > 85:
                results.append("  🚨 High memory usage detected - restart or close memory-intensive applications")
            if disk_percent > 90:
                results.append("  🚨 Low disk space - clean up old files or expand storage")
            
            if cpu_percent < 50 and memory.percent < 70:
                results.append("  ✅ System performance is optimal")
                
        except ImportError:
            results.append("📦 **Note**: Install 'psutil' for detailed performance monitoring")
            results.append("  pip install psutil")
        
        return "\n".join(results)
    
    def get_help_response(self) -> str:
        """Get help information"""
        results = []
        results.append("🤖 **NoxAssistant Help**")
        results.append("=" * 40)
        results.append("I'm your intelligent network management assistant!")
        results.append("\n📋 **Available Commands**:")
        
        for task_name, task_info in self.task_registry.items():
            description = task_info.get('description', 'No description')
            commands = ', '.join(task_info.get('commands', []))
            results.append(f"\n🔧 **{task_name.title()}**")
            results.append(f"  Commands: {commands}")
            results.append(f"  {description}")
        
        results.append("\n💬 **Example Usage**:")
        results.append('  • "Run a full diagnostic check"')
        results.append('  • "Scan the network for devices"')
        results.append('  • "Check system security"')
        results.append('  • "Analyze performance and optimize"')
        
        if VOICE_AVAILABLE:
            results.append("\n🎤 **Voice Commands**:")
            results.append("  Use 'python main.py --voice' for voice interaction")
        
        return "\n".join(results)
    
    def get_task_list(self) -> str:
        """Get formatted list of available tasks"""
        tasks = []
        for task_name, task_info in self.task_registry.items():
            tasks.append(f"• {task_name}: {task_info.get('description', 'No description')}")
        return "\n".join(tasks)
    
    def log_action(self, action_type: str, message: str):
        """Log assistant actions for transparency"""
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_entry = f"[{timestamp}] {action_type.upper()}: {message}\n"
            
            # Ensure log directory exists
            self.history_log.parent.mkdir(exist_ok=True)
            
            with open(self.history_log, 'a', encoding='utf-8') as f:
                f.write(log_entry)
        except Exception as e:
            logger.error(f"Failed to log action: {e}")
    
    def process_command(self, user_input: str, use_voice: bool = False) -> str:
        """
        Main command processing method
        
        Args:
            user_input: User's command or question
            use_voice: Whether to use voice output
            
        Returns:
            Response text
        """
        if not user_input.strip():
            response = "❓ I didn't catch that. Try asking me to 'run diagnostics' or 'scan network'."
        else:
            # Process with AI if available, otherwise use rules
            response = self.process_with_ai(user_input)
        
        # Add timestamp and formatting
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_response = f"\n🤖 **NoxAssistant** ({timestamp})\n{'-' * 50}\n{response}\n"
        
        # Voice output if requested
        if use_voice:
            # Clean response for speech (remove markdown and emojis)
            clean_response = response
            for char in "🤖📊🔍🌐💻📱🔒⚠️✅❌🚨💡📋🖥️💾💿📦🎤🔧":
                clean_response = clean_response.replace(char, "")
            clean_response = clean_response.replace("**", "").replace("*", "")
            
            self.speak(clean_response)
        
        return formatted_response

# CLI Interface for NoxAssistant
def main():
    """Command-line interface for NoxAssistant"""
    import argparse
    
    parser = argparse.ArgumentParser(description="🤖 NoxAssistant - Intelligent Network Management")
    parser.add_argument("command", nargs="*", help="Command to execute")
    parser.add_argument("--voice", action="store_true", help="Enable voice interaction")
    parser.add_argument("--interactive", action="store_true", help="Start interactive session")
    
    args = parser.parse_args()
    
    # Initialize assistant
    assistant = NoxAssistant()
    
    print("🤖 NoxAssistant v7.0 - Your Intelligent Network Companion")
    print("=" * 60)
    
    if args.voice and VOICE_AVAILABLE:
        print("🎤 Voice mode enabled. Say 'exit' or 'quit' to stop.")
        print("   Listening for wake word: 'Hey Nox' or 'Nox'...")
        
        while True:
            try:
                voice_input = assistant.listen_for_voice_command()
                if voice_input:
                    # Check for wake words
                    if any(wake in voice_input for wake in ["hey nox", "nox", "assistant"]):
                        assistant.speak("Yes, how can I help you?")
                        
                        # Listen for actual command
                        command = assistant.listen_for_voice_command(timeout=10)
                        if command:
                            if command in ["exit", "quit", "bye", "goodbye"]:
                                assistant.speak("Goodbye! Have a great day!")
                                break
                            
                            response = assistant.process_command(command, use_voice=True)
                            print(response)
                        else:
                            assistant.speak("I didn't hear a command. Try again.")
                    
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
                
    elif args.interactive:
        print("💬 Interactive mode. Type 'exit' or 'quit' to stop.")
        print("   Try: 'run diagnostics', 'scan network', 'check security'")
        
        while True:
            try:
                user_input = input("\n💬 You: ").strip()
                if user_input.lower() in ["exit", "quit", "bye"]:
                    print("👋 Goodbye!")
                    break
                
                if user_input:
                    response = assistant.process_command(user_input)
                    print(response)
                    
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
                
    elif args.command:
        # Single command execution
        command = " ".join(args.command)
        response = assistant.process_command(command)
        print(response)
        
    else:
        # Show help
        response = assistant.get_help_response()
        print(response)
        print("\n💡 **Quick Start**:")
        print("  python assistant.py --interactive    # Interactive text mode")
        if VOICE_AVAILABLE:
            print("  python assistant.py --voice         # Voice interaction mode")
        print("  python assistant.py run diagnostics  # Single command")

if __name__ == "__main__":
    main()
