"""
NoxSuite FastAPI - Configuration Settings
Application configuration and environment settings
"""

class Settings:
    """Application settings"""
    app_name: str = "NoxSuite API"
    debug: bool = False
    version: str = "1.0.0"

settings = Settings()