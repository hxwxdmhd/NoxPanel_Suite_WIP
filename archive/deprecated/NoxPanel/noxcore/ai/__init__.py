"""NoxCore AI Module - Ollama Integration & AI Assistant System"""

from .ollama_client import OllamaClient
from .nox_assistant import NoxAssistant
from .task_registry import TaskRegistry

__version__ = "1.0.0"
__all__ = ['OllamaClient', 'NoxAssistant', 'TaskRegistry']

# AI Module Configuration
AI_CONFIG = {
    "ollama_url": "http://localhost:11434",
    "default_model": "llama2:7b",
    "recommended_models": [
        "codellama:7b",      # Code generation and analysis
        "llama2:7b",         # General conversation
        "mistral:7b",        # Fast responses
        "neural-chat:7b",    # Natural conversations
        "starcode:7b",       # Code understanding
        "wizardcoder:7b",    # Programming assistance
        "phind-codellama:34b", # Advanced code help
        "deepseek-coder:6.7b", # Code analysis
        "magicoder:7b"       # Multi-language coding
    ],
    "conversation_history_limit": 20,
    "response_timeout": 60,
    "system_personality": "J.A.R.V.I.S.-inspired professional assistant"
}
