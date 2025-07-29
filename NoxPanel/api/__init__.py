"""
API package initialization
Registers all API blueprints for the NoxPanel system
"""

from flask import Blueprint

# Import all blueprints
from .auth import auth_bp
from .dashboard import dashboard_bp
from .security import security_bp
from .plugins import plugins_bp
from .crawler import crawler_bp

# Export blueprints for easy importing
__all__ = [
    'auth_bp',
    'dashboard_bp', 
    'security_bp',
    'plugins_bp',
    'crawler_bp'
]