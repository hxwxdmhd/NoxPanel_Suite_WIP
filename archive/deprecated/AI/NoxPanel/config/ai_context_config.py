# AI Context Configuration
AI_CONTEXT_CONFIG = {
    "context_files": [
        "gpt_dump_context.txt",
        "training_data.jsonl"
    ],
    "auto_refresh_minutes": 10,
    "max_context_length": 8000,
    "search_limit": 50,
    "cache_enabled": True,
    "enable_logging": True
}

# Integration paths
CONTEXT_PATHS = {
    "base_dir": "./",
    "data_dir": "./data/",
    "logs_dir": "./logs/",
    "cache_dir": "./cache/ai_context/"
}

# AI Memory Settings
MEMORY_CONFIG = {
    "max_memory_items": 1000,
    "relevance_threshold": 0.3,
    "auto_cleanup": True,
    "backup_context": True
}
