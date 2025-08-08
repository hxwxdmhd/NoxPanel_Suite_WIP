"""
NoxSuite FastAPI - Logging Configuration
Centralized logging setup and configuration
"""
import logging

def setup_logging():
    """Setup application logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )