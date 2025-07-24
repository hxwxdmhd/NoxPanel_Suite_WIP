"""
NoxPanel v5.0 - Centralized Blueprint Registration System
Standardized blueprint management for consistent route registration
"""

import logging
from typing import Dict, List, Tuple, Optional, Any
from flask import Flask, Blueprint
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class BlueprintConfig:
    """Configuration for blueprint registration"""
    blueprint: Blueprint
    url_prefix: str
    subdomain: Optional[str] = None
    url_defaults: Optional[Dict[str, Any]] = None
    static_folder: Optional[str] = None
    static_url_path: Optional[str] = None
    template_folder: Optional[str] = None
    root_path: Optional[str] = None
    
class BlueprintRegistry:
    """Centralized registry for all application blueprints"""
    
    def __init__(self):
        self.blueprints: Dict[str, BlueprintConfig] = {}
        self.registration_order: List[str] = []
        self.registered_count = 0
        
    def register_blueprint(self, 
                         name: str,
                         blueprint: Blueprint, 
                         url_prefix: Optional[str] = None,
                         **kwargs) -> None:
        """Register a blueprint with configuration"""
        
        if name in self.blueprints:
            logger.warning(f"Blueprint '{name}' already registered, skipping")
            return
            
        config = BlueprintConfig(
            blueprint=blueprint,
            url_prefix=url_prefix or f"/{name}",
            **kwargs
        )
        
        self.blueprints[name] = config
        self.registration_order.append(name)
        
        logger.debug(f"📝 Blueprint registered: {name} -> {config.url_prefix}")
        
    def get_blueprint(self, name: str) -> Optional[BlueprintConfig]:
        """Get blueprint configuration by name"""
        return self.blueprints.get(name)
        
    def init_app(self, app: Flask) -> None:
        """Initialize the blueprint registry with a Flask app (Flask extension pattern)"""
        logger.info(f"🔗 Initializing BlueprintRegistry with Flask app...")
        
        # Store app reference for later use
        if not hasattr(app, 'extensions'):
            app.extensions = {}
        app.extensions['blueprint_registry'] = self
        
        # Auto-register core blueprints if requested
        if app.config.get('BLUEPRINT_AUTO_REGISTER', True):
            register_core_blueprints()
            
        # Apply all registered blueprints
        self.apply_to_app(app)
        
        logger.info(f"✅ BlueprintRegistry initialized with {len(self.blueprints)} blueprints")
        
    def list_blueprints(self) -> List[str]:
        """Get list of registered blueprint names"""
        return list(self.blueprints.keys())
        
    def register_core_blueprint(self, name_or_blueprint, blueprint=None, url_prefix: Optional[str] = None, **kwargs) -> None:
        """Legacy method for backwards compatibility - supports multiple calling patterns"""
        
        # Handle different calling patterns
        if blueprint is None:
            # Called with just blueprint object: register_core_blueprint(blueprint)
            if hasattr(name_or_blueprint, 'name'):
                blueprint_obj = name_or_blueprint
                name = blueprint_obj.name
            else:
                logger.error("Invalid blueprint object - no name attribute")
                return
        else:
            # Called with name and blueprint: register_core_blueprint(name, blueprint)
            name = name_or_blueprint
            blueprint_obj = blueprint
        
        logger.debug(f"🔄 Using legacy register_core_blueprint method for: {name}")
        self.register_blueprint(name, blueprint_obj, url_prefix, **kwargs)
        
    def apply_to_app(self, app: Flask) -> None:
        """Apply all registered blueprints to Flask app"""
        logger.info(f"🔗 Registering {len(self.blueprints)} blueprints with Flask app...")
        
        for name in self.registration_order:
            config = self.blueprints[name]
            
            try:
                # Register blueprint with Flask app
                app.register_blueprint(
                    config.blueprint,
                    url_prefix=config.url_prefix,
                    subdomain=config.subdomain,
                    url_defaults=config.url_defaults,
                    static_folder=config.static_folder,
                    static_url_path=config.static_url_path,
                    template_folder=config.template_folder,
                    root_path=config.root_path
                )
                
                self.registered_count += 1
                logger.info(f"✅ {name} -> {config.url_prefix}")
                
            except Exception as e:
                logger.error(f"❌ Failed to register blueprint '{name}': {e}")
                
        logger.info(f"🎯 Blueprint registration complete: {self.registered_count}/{len(self.blueprints)} successful")

# Global blueprint registry
blueprint_registry = BlueprintRegistry()

def register_core_blueprints():
    """Register all core NoxPanel blueprints"""
    
    # Admin Panel Blueprint
    try:
        from webpanel.admin_blueprint import admin_bp
        blueprint_registry.register_blueprint(
            name="admin",
            blueprint=admin_bp,
            url_prefix="/admin"
        )
    except ImportError as e:
        logger.warning(f"Admin blueprint not available: {e}")
    
    # Job Scheduler Blueprint  
    try:
        from webpanel.job_scheduler import scheduler_bp
        blueprint_registry.register_blueprint(
            name="scheduler", 
            blueprint=scheduler_bp,
            url_prefix="/api/scheduler"
        )
    except ImportError as e:
        logger.warning(f"Scheduler blueprint not available: {e}")
    
    # Plugin Loader Blueprint
    try:
        from webpanel.plugin_loader import plugin_bp
        blueprint_registry.register_blueprint(
            name="plugins",
            blueprint=plugin_bp, 
            url_prefix="/api/plugins"
        )
    except ImportError as e:
        logger.warning(f"Plugin blueprint not available: {e}")
    
    # AI Monitor Blueprint
    try:
        from webpanel.ai_monitor_api import ai_monitor_bp
        blueprint_registry.register_blueprint(
            name="ai_monitor",
            blueprint=ai_monitor_bp,
            url_prefix="/api/ai-monitor"
        )
    except ImportError as e:
        logger.warning(f"AI Monitor blueprint not available: {e}")
    
    # Models API Blueprint (convert from direct registration)
    try:
        from webpanel.models_blueprint import models_bp
        blueprint_registry.register_blueprint(
            name="models",
            blueprint=models_bp,
            url_prefix="/api/models"
        )
    except ImportError as e:
        logger.warning(f"Models blueprint not available: {e}")
    
    # Chatbot Blueprint
    try:
        from webpanel.chatbot import chatbot_bp
        blueprint_registry.register_blueprint(
            name="chatbot",
            blueprint=chatbot_bp,
            url_prefix="/api/chat"
        )
    except ImportError as e:
        logger.warning(f"Chatbot blueprint not available: {e}")

def register_category_blueprints():
    """Register category-specific blueprints for multi-category expansion"""
    
    # Media Category Blueprint
    try:
        from webpanel.categories.media import media_bp
        blueprint_registry.register_blueprint(
            name="media",
            blueprint=media_bp,
            url_prefix="/media"
        )
    except ImportError:
        logger.debug("Media category blueprint not yet implemented")
    
    # Network Category Blueprint
    try:
        from webpanel.categories.network import network_bp
        blueprint_registry.register_blueprint(
            name="network", 
            blueprint=network_bp,
            url_prefix="/network"
        )
    except ImportError:
        logger.debug("Network category blueprint not yet implemented")
    
    # Scripts Category Blueprint
    try:
        from webpanel.categories.scripts import scripts_bp
        blueprint_registry.register_blueprint(
            name="scripts",
            blueprint=scripts_bp,
            url_prefix="/scripts"
        )
    except ImportError:
        logger.debug("Scripts category blueprint not yet implemented")
    
    # Dashboard Category Blueprint
    try:
        from webpanel.categories.dashboard import dashboard_bp
        blueprint_registry.register_blueprint(
            name="dashboard_category",
            blueprint=dashboard_bp, 
            url_prefix="/dashboard"
        )
    except ImportError:
        logger.debug("Dashboard category blueprint not yet implemented")
    
    # Setup Category Blueprint
    try:
        from webpanel.categories.setup import setup_bp
        blueprint_registry.register_blueprint(
            name="setup",
            blueprint=setup_bp,
            url_prefix="/setup"
        )
    except ImportError:
        logger.debug("Setup category blueprint not yet implemented")
    
    # Certificates Category Blueprint
    try:
        from webpanel.categories.certs import certs_bp
        blueprint_registry.register_blueprint(
            name="certs",
            blueprint=certs_bp,
            url_prefix="/certs"
        )
    except ImportError:
        logger.debug("Certs category blueprint not yet implemented")

def create_app_with_blueprints(app: Flask) -> Flask:
    """Configure Flask app with all registered blueprints"""
    
    logger.info("🚀 Initializing NoxPanel v5.0 with standardized blueprint architecture...")
    
    # Register core blueprints
    register_core_blueprints()
    
    # Register category blueprints (for future expansion)
    register_category_blueprints()
    
    # Apply all blueprints to the Flask app
    blueprint_registry.apply_to_app(app)
    
    # Log route summary
    log_route_summary(app)
    
    return app

def log_route_summary(app: Flask):
    """Log summary of all registered routes"""
    routes = []
    for rule in app.url_map.iter_rules():
        routes.append({
            'endpoint': rule.endpoint,
            'methods': list(rule.methods),
            'rule': str(rule)
        })
    
    logger.info(f"📋 Route registration summary: {len(routes)} total routes")
    
    # Group routes by blueprint
    blueprint_routes = {}
    for route in routes:
        blueprint_name = route['endpoint'].split('.')[0] if '.' in route['endpoint'] else 'main'
        if blueprint_name not in blueprint_routes:
            blueprint_routes[blueprint_name] = []
        blueprint_routes[blueprint_name].append(route)
    
    for blueprint_name, bp_routes in blueprint_routes.items():
        logger.info(f"  📂 {blueprint_name}: {len(bp_routes)} routes")

def get_blueprint_registry() -> BlueprintRegistry:
    """Get the global blueprint registry"""
    return blueprint_registry

def get_registered_blueprints() -> List[str]:
    """Get list of all registered blueprint names"""
    return blueprint_registry.list_blueprints()
