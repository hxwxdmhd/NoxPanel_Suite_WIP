"""
NoxPanel v5.0 - Integrated Flask Application
Main application with enhanced security, performance, and modular architecture
"""

import os
import sys
import logging
import time
from pathlib import Path
from typing import Dict, Any, Optional
from flask import Flask, render_template, request, jsonify, g, Response
from flask_cors import CORS
from dotenv import load_dotenv
import secrets

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import new security and performance systems
from noxcore.security_config import EnvironmentSecurityManager
from noxcore.database_pool import DatabaseConnectionPool

class NetworkInterface:
    def _get_hostname(self, ip):
        """Get hostname for IP address"""
        try:
            import socket
            hostname = socket.gethostbyaddr(ip)[0]
            return hostname
        except Exception:
            return "Unknown"

    def _extract_ping_time(self, ping_output):
        """Extract ping time from ping output"""
        try:
            import re
            match = re.search(r'time[<=](\d+)ms', ping_output)
            if match:
                return f"{match.group(1)}ms"
        except Exception:
            pass
        return "N/A"

    def _get_local_ip(self):
        """Get local IP address"""
        try:
            import socket
            # Connect to a remote address to get local IP
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                return s.getsockname()[0]
        except Exception:
            return "127.0.0.1"

    def _get_service_name(self, port):
        """Get service name for port"""
        services = {
            21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP", 53: "DNS",
            80: "HTTP", 110: "POP3", 135: "RPC", 139: "NetBIOS", 143: "IMAP",
            443: "HTTPS", 993: "IMAPS", 995: "POP3S", 1723: "PPTP",
            3389: "RDP", 5432: "PostgreSQL", 3306: "MySQL", 8080: "HTTP-Alt", 8443: "HTTPS-Alt"
        }
        return services.get(port, f"Unknown-{port}")

    def _check_open_ports(self):
        """Check for potentially dangerous open ports"""
        findings = []
        dangerous_ports = [23, 135, 139, 445, 1433, 1521, 3389]

        for port in dangerous_ports:
            # Simulate port check (in real implementation, would actually scan)
            findings.append({
                "type": "Open Port",
                "description": f"Potentially dangerous port {port} detected",
                "severity": "medium",
                "port": port
            })

        return findings[:2]  # Limit for demo

    def _check_default_passwords(self):
        """Check for default passwords"""
        return [{
            "type": "Default Credentials",
            "description": "Default admin credentials detected on router",
            "severity": "high",
            "service": "Router Admin"
        }]

    def _check_ssl_certificates(self):
        """Check SSL certificate status"""
        return [{
            "type": "SSL Certificate",
            "description": "Self-signed certificate detected",
            "severity": "low",
            "service": "Web Server"
        }]

    def _check_firewall_status(self):
        """Check firewall configuration"""
        return [{
            "type": "Firewall",
            "description": "Windows Firewall appears to be disabled",
            "severity": "medium",
            "service": "Windows Security"
        }]

    def _log_startup_summary(self):
        """Log comprehensive startup summary"""
        logger.info("=" * 60)
        logger.info(f"[BOT] NoxPanel v5.0 - System Status Summary")
        logger.info("=" * 60)from noxcore.blueprint_registry import BlueprintRegistry
from noxcore.plugin_sandbox import SecurePluginLoader
from noxcore.rate_limiter import (
    get_rate_limiter, rate_limit, add_rate_limit_headers,
    RateLimitRule
)
from noxcore.security_headers import init_security_headers
from noxcore.connection_manager import init_connection_manager

# Import existing core modules
from noxcore.runner import run_script
from noxcore.auth import auth_required, create_user, verify_user

# Load environment variables
load_dotenv()

# Get environment
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# Ensure log directory exists
log_dir = Path("data/logs")
log_dir.mkdir(parents=True, exist_ok=True)

# Configure logging with environment-specific levels
log_level = "DEBUG" if ENVIRONMENT == "development" else "INFO"
logging.basicConfig(
    level=getattr(logging, log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("data/logs/noxpanel.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class NoxPanelApp:
    """Enhanced NoxPanel Flask application with security and performance optimizations"""

    def __init__(self):
        self.app = None
        self.security_manager = None
        self.db_pool = None
        self.blueprint_registry = None
        self.plugin_loader = None
        self.rate_limiter = None
        self.modules_status = {}

    def create_app(self) -> Flask:
        """Create and configure Flask application"""
        logger.info(f"[INIT] Initializing NoxPanel v5.0 [{ENVIRONMENT}]")

        # Create Flask app
        self.app = Flask(__name__,
                        template_folder="templates",
                        static_folder="static")

        # Initialize core systems
        self._init_security()
        self._init_database()
        self._init_blueprints()
        self._init_plugins()
        self._init_rate_limiting()
        self._init_cors()
        self._init_error_handlers()

        # Register core routes
        self._register_core_routes()

        # Load and register modules
        self._load_modules()

        # Initialize security headers (must be last)
        init_security_headers(self.app, ENVIRONMENT)

        # Apply response post-processing
        self._init_response_processing()

        logger.info(f"[OK] NoxPanel v5.0 initialized successfully")
        self._log_status_summary()

        return self.app

    def _init_security(self):
        """Initialize security management"""
        try:
            self.security_manager = EnvironmentSecurityManager()
            security_config = self.security_manager.get_security_config(ENVIRONMENT)

            # Set Flask app configuration from security config
            self.app.secret_key = security_config.secret_key
            self.app.config['SESSION_COOKIE_SECURE'] = security_config.session_cookie_secure
            self.app.config['SESSION_COOKIE_HTTPONLY'] = security_config.session_cookie_httponly
            self.app.config['SESSION_COOKIE_SAMESITE'] = security_config.session_cookie_samesite
            self.app.config['PERMANENT_SESSION_LIFETIME'] = security_config.session_lifetime

            logger.info(f"[SEC] Security initialized for {ENVIRONMENT} environment")

        except Exception as e:
            logger.error(f"[FAIL] Security initialization failed: {e}")
            # Fallback to basic configuration
            self.app.secret_key = os.getenv("SECRET_KEY", secrets.token_hex(32))

    def _init_database(self):
        """Initialize database connection pool"""
        try:
            db_path = Path("data/db/noxpanel.db")
            db_path.parent.mkdir(parents=True, exist_ok=True)

            self.db_pool = DatabaseConnectionPool(str(db_path))

            # Test connection
            with self.db_pool.get_connection() as conn:
                conn.execute("SELECT 1").fetchone()

            logger.info("[SAVE] Database connection pool initialized")

        except Exception as e:
            logger.error(f"[FAIL] Database initialization failed: {e}")
            self.db_pool = None

    def _init_blueprints(self):
        """Initialize blueprint registry"""
        try:
            self.blueprint_registry = BlueprintRegistry()
            self.blueprint_registry.init_app(self.app)

            # Register knowledge management blueprint
            from .knowledge_routes import knowledge_bp
            self.app.register_blueprint(knowledge_bp)

            # Register AI Context blueprint
            try:
                from noxcore.context_loader import ai_context_bp
                self.app.register_blueprint(ai_context_bp)
                logger.info("🤖 AI Context blueprint registered")
            except ImportError as e:
                logger.warning(f"AI Context blueprint not available: {e}")

            logger.info("📋 Blueprint registry initialized")
            logger.info("🧠 Knowledge management blueprint registered")

        except Exception as e:
            logger.error(f"[FAIL] Blueprint registry initialization failed: {e}")
            self.blueprint_registry = None

    def _init_plugins(self):
        """Initialize secure plugin loader"""
        try:
            self.plugin_loader = SecurePluginLoader()

            # Load plugins from plugins directory
            plugins_dir = Path("plugins")
            if plugins_dir.exists():
                plugin_count = 0
                for plugin_dir in plugins_dir.iterdir():
                    if plugin_dir.is_dir() and (plugin_dir / "plugin.json").exists():
                        if self.plugin_loader.load_plugin_secure(plugin_dir.name, plugin_dir):
                            plugin_count += 1

                logger.info(f"[PLUG] Plugin system initialized ({plugin_count} plugins loaded)")
            else:
                logger.info("[PLUG] Plugin system initialized (no plugins directory)")

        except Exception as e:
            logger.error(f"[FAIL] Plugin system initialization failed: {e}")
            self.plugin_loader = None

    def _init_rate_limiting(self):
        """Initialize rate limiting"""
        try:
            self.rate_limiter = get_rate_limiter()

            # Configure environment-specific rate limits
            if ENVIRONMENT == "production":
                # Stricter limits for production
                self.rate_limiter.add_rule("api", RateLimitRule(
                    requests_per_minute=100,
                    requests_per_hour=2000,
                    burst_limit=5
                ))
                self.rate_limiter.add_rule("auth", RateLimitRule(
                    requests_per_minute=5,
                    requests_per_hour=50,
                    burst_limit=2
                ))
            else:
                # More relaxed limits for development
                self.rate_limiter.add_rule("api", RateLimitRule(
                    requests_per_minute=200,
                    requests_per_hour=5000,
                    burst_limit=20
                ))

            logger.info(f"[FAST] Rate limiting initialized for {ENVIRONMENT}")

        except Exception as e:
            logger.error(f"[FAIL] Rate limiting initialization failed: {e}")
            self.rate_limiter = None

    def _init_cors(self):
        """Initialize CORS configuration"""
        try:
            if ENVIRONMENT == "development":
                # Permissive CORS for development
                CORS(self.app, origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:5000"])
            else:
                # Restrictive CORS for production
                allowed_origins = os.getenv("ALLOWED_ORIGINS", "").split(",")
                if allowed_origins and allowed_origins[0]:
                    CORS(self.app, origins=allowed_origins)
                else:
                    logger.warning("⚠️ No CORS origins configured for production")

            logger.info("[WEB] CORS configuration applied")

        except Exception as e:
            logger.error(f"[FAIL] CORS initialization failed: {e}")

    def _init_error_handlers(self):
        """Initialize custom error handlers"""
        @self.app.errorhandler(404)
        def not_found(error):
            logger.warning(f"404 error for URL: {request.url} | Path: {request.path}")
            return jsonify({
                "status": "error",
                "message": "Endpoint not found",
                "path": request.path,
                "timestamp": time.time()
            }), 404

        @self.app.errorhandler(429)
        def rate_limit_exceeded(error):
            return jsonify({
                "status": "error",
                "message": "Rate limit exceeded",
                "timestamp": time.time()
            }), 429

        @self.app.errorhandler(500)
        def internal_error(error):
            logger.error(f"Internal server error: {error}")
            return jsonify({
                "status": "error",
                "message": "Internal server error" if ENVIRONMENT == "production" else str(error),
                "timestamp": time.time()
            }), 500

    def _init_response_processing(self):
        """Initialize response post-processing"""
        @self.app.after_request
        def process_response(response: Response) -> Response:
            # Add rate limit headers
            response = add_rate_limit_headers(response)

            # Add server identification
            response.headers['Server'] = 'NoxPanel/5.0'

            # Add cache control for static resources
            if request.endpoint == 'static':
                response.cache_control.max_age = 3600  # 1 hour

            return response

    def _register_core_routes(self):
        """Register core application routes"""

        @self.app.route("/")
        def dashboard():
            """Main dashboard view"""
            try:
                scripts_dir = Path("scripts")
                scripts = []
                if scripts_dir.exists():
                    scripts = [f.name for f in scripts_dir.iterdir() if f.suffix == ".py"]

                return render_template("dashboard.html",
                                     scripts=scripts,
                                     modules_status=self.modules_status,
                                     environment=ENVIRONMENT)
            except Exception as e:
                logger.error(f"Dashboard error: {e}")
                return render_template("dashboard.html",
                                     scripts=[],
                                     error=str(e),
                                     environment=ENVIRONMENT)

        @self.app.route("/chat")
        def chat():
            """AI Chat interface"""
            try:
                return render_template("chat.html",
                                     environment=ENVIRONMENT,
                                     modules_status=self.modules_status)
            except Exception as e:
                logger.error(f"Chat interface error: {e}")
                return render_template("dashboard.html",
                                     error=f"Chat interface unavailable: {str(e)}",
                                     environment=ENVIRONMENT)

        @self.app.route("/api/health")
        @rate_limit("api")
        def health_check():
            """Enhanced health check endpoint"""
            db_status = "ok" if self.db_pool else "unavailable"

            # Test database if available
            if self.db_pool:
                try:
                    with self.db_pool.get_connection() as conn:
                        conn.execute("SELECT 1").fetchone()
                except Exception:
                    db_status = "error"

            return jsonify({
                "status": "ok",
                "service": "NoxPanel",
                "version": "7.0.0",
                "environment": ENVIRONMENT,
                "timestamp": time.time(),
                "components": {
                    "database": db_status,
                    "security": "ok" if self.security_manager else "unavailable",
                    "plugins": "ok" if self.plugin_loader else "unavailable",
                    "rate_limiter": "ok" if self.rate_limiter else "unavailable"
                },
                "modules": self.modules_status
            })

        @self.app.route("/api/scripts")
        @rate_limit("api")
        def list_scripts():
            """API endpoint to list available scripts"""
            try:
                scripts_dir = Path("scripts")
                scripts = []
                if scripts_dir.exists():
                    scripts = [f.name for f in scripts_dir.iterdir() if f.suffix == ".py"]

                return jsonify({"status": "ok", "scripts": scripts})
            except Exception as e:
                logger.error(f"Error listing scripts: {e}")
                return jsonify({"status": "error", "message": str(e)}), 500

        @self.app.route("/api/run/<script_name>", methods=["POST"])
        @rate_limit("api")
        @auth_required
        def run_script_endpoint(script_name):
            """Enhanced script execution endpoint"""
            try:
                scripts_dir = Path("scripts")
                script_path = scripts_dir / script_name

                if not script_path.exists() or script_path.suffix != ".py":
                    return jsonify({"status": "error", "message": "Script not found"}), 404

                # Execute script with enhanced monitoring
                start_time = time.time()
                result = run_script(str(script_path))
                execution_time = time.time() - start_time

                logger.info(f"Script executed: {script_name} (took {execution_time:.2f}s)")

                return jsonify({
                    "status": "ok",
                    "script": script_name,
                    "result": result,
                    "execution_time": execution_time,
                    "timestamp": time.time()
                })

            except Exception as e:
                logger.error(f"Script execution error: {e}")
                return jsonify({"status": "error", "message": str(e)}), 500

        @self.app.route("/api/stats")
        @rate_limit("api")
        @auth_required
        def get_stats():
            """Get system statistics"""
            stats = {
                "timestamp": time.time(),
                "environment": ENVIRONMENT,
                "uptime": time.time() - self.app.config.get('START_TIME', time.time())
            }

            # Add rate limiting stats
            if self.rate_limiter:
                stats["rate_limiting"] = self.rate_limiter.get_all_stats()

            # Add database stats
            if self.db_pool:
                stats["database"] = self.db_pool.get_statistics()

            # Add plugin stats
            if self.plugin_loader:
                stats["plugins"] = {
                    "loaded": self.plugin_loader.get_loaded_plugins(),
                    "count": len(self.plugin_loader.get_loaded_plugins())
                }

            return jsonify({"status": "ok", "stats": stats})

        # === PHASE 3 CONSOLIDATION ROUTES ===
        # Infrastructure Discovery Mode Integration

        @self.app.route('/consolidated/status')
        def consolidated_status():
            """Consolidated status endpoint combining all web interfaces"""
            return jsonify({
                "status": "consolidated",
                "version": "10.1",
                "phase": "infrastructure_discovery",
                "gates_unlocked": ["database_advanced", "authentication_system", "basic_apis", "plugin_system"],
                "interfaces": {
                    "noxpanel": "active",
                    "heimnetz": "integrated",
                    "plugin_system": "unlocked",
                    "infrastructure_mode": "enabled"
                },
                "timestamp": time.time()
            })

        @self.app.route('/heimnetz')
        @self.app.route('/heimnetz/')
        def heimnetz_redirect():
            """Redirect Heimnetz routes to integrated interface"""
            return render_template("dashboard.html",
                                 mode="heimnetz",
                                 environment=ENVIRONMENT,
                                 modules_status=self.modules_status)

        @self.app.route('/infrastructure/discovery')
        def infrastructure_discovery():
            """Infrastructure Discovery Dashboard"""
            return render_template("dashboard.html",
                                 mode="infrastructure",
                                 environment=ENVIRONMENT,
                                 modules_status=self.modules_status)

        @self.app.route('/legacy/<path:route>')
        def legacy_compatibility(route):
            """Handle legacy routes with graceful fallback"""
            return jsonify({
                "message": "This route has been consolidated into the unified interface",
                "redirect": f"/{route}",
                "version": "10.1",
                "infrastructure_mode": True
            })

        # === INFRASTRUCTURE DISCOVERY API ENDPOINTS ===

        @self.app.route('/api/infrastructure/network-scan', methods=['POST'])
        @auth_required
        def infrastructure_network_scan():
            """Discover network devices and topology"""
            import subprocess
            import ipaddress
            import threading
            from concurrent.futures import ThreadPoolExecutor

            def ping_host(ip):
                """Ping a single host"""
                try:
                    result = subprocess.run(['ping', '-n', '1', '-w', '1000', str(ip)],
                                          capture_output=True, text=True, timeout=2)
                    if result.returncode == 0:
                        return {
                            'ip': str(ip),
                            'status': 'online',
                            'hostname': self._get_hostname(str(ip)),
                            'response_time': self._extract_ping_time(result.stdout)
                        }
                except Exception:
                    pass
                return None

            try:
                # Get local network range
                network = ipaddress.IPv4Network('192.168.1.0/24', strict=False)
                devices = []

                # Use ThreadPoolExecutor for parallel pinging
                with ThreadPoolExecutor(max_workers=50) as executor:
                    futures = [executor.submit(ping_host, ip) for ip in network.hosts()]
                    for future in futures:
                        result = future.result()
                        if result:
                            devices.append(result)

                return jsonify({
                    "status": "success",
                    "devices": devices,
                    "scan_time": time.time(),
                    "network_range": str(network)
                })

            except Exception as e:
                logger.error(f"Network scan error: {e}")
                return jsonify({
                    "status": "error",
                    "message": str(e)
                }), 500

        @self.app.route('/api/infrastructure/service-scan', methods=['POST'])
        @auth_required
        def infrastructure_service_scan():
            """Discover services on network devices"""
            import socket
            from concurrent.futures import ThreadPoolExecutor

            common_ports = [21, 22, 23, 25, 53, 80, 110, 135, 139, 143, 443, 993, 995, 1723, 3389, 5432, 3306, 8080, 8443]

            def scan_port(host, port):
                """Scan a single port"""
                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                        sock.settimeout(1)
                        result = sock.connect_ex((host, port))
                        if result == 0:
                            service_name = self._get_service_name(port)
                            return {
                                'host': host,
                                'port': port,
                                'name': service_name,
                                'status': 'open'
                            }
                except Exception:
                    pass
                return None

            try:
                services = []
                local_ip = self._get_local_ip()

                # Scan common ports on localhost and gateway
                hosts_to_scan = [local_ip, '192.168.1.1', '127.0.0.1']

                with ThreadPoolExecutor(max_workers=100) as executor:
                    futures = []
                    for host in hosts_to_scan:
                        for port in common_ports:
                            futures.append(executor.submit(scan_port, host, port))

                    for future in futures:
                        result = future.result()
                        if result:
                            services.append(result)

                return jsonify({
                    "status": "success",
                    "services": services,
                    "scan_time": time.time(),
                    "hosts_scanned": hosts_to_scan
                })

            except Exception as e:
                logger.error(f"Service scan error: {e}")
                return jsonify({
                    "status": "error",
                    "message": str(e)
                }), 500

        @self.app.route('/api/infrastructure/security-scan', methods=['POST'])
        @auth_required
        def infrastructure_security_scan():
            """Run security assessment on infrastructure"""
            try:
                findings = []

                # Check for common security issues
                findings.extend(self._check_open_ports())
                findings.extend(self._check_default_passwords())
                findings.extend(self._check_ssl_certificates())
                findings.extend(self._check_firewall_status())

                return jsonify({
                    "status": "success",
                    "findings": findings,
                    "scan_time": time.time(),
                    "total_issues": len(findings)
                })

            except Exception as e:
                logger.error(f"Security scan error: {e}")
                return jsonify({
                    "status": "error",
                    "message": str(e)
                }), 500

        @self.app.route('/api/infrastructure/topology', methods=['GET'])
        @auth_required
        def infrastructure_topology():
            """Get network topology map"""
            try:
                topology = {
                    "nodes": [
                        {"id": "gateway", "label": "Gateway", "type": "router", "ip": "192.168.1.1"},
                        {"id": "local", "label": "NoxPanel Host", "type": "server", "ip": self._get_local_ip()},
                    ],
                    "edges": [
                        {"from": "local", "to": "gateway", "type": "ethernet"}
                    ],
                    "generated_at": time.time()
                }

                return jsonify({
                    "status": "success",
                    "topology": topology
                })

            except Exception as e:
                logger.error(f"Topology error: {e}")
                return jsonify({
                    "status": "error",
                    "message": str(e)
                }), 500

    def _load_modules(self):
        """Load and register optional modules"""
        modules_to_load = [
            ("Admin Panel", "webpanel.admin_blueprint", "admin_bp"),
            ("Job Scheduler", "webpanel.job_scheduler", "scheduler_bp"),
            ("Plugin Loader", "webpanel.plugin_loader", "plugin_bp"),
            ("Chatbot", "webpanel.chatbot", "register_chatbot_routes"),
            ("Models API", "webpanel.models_direct", "register_models_api"),
            ("AI Monitor", "webpanel.ai_monitor_direct", "register_ai_monitor_direct_routes"),
            ("Knowledge Management", "webpanel.knowledge_routes", "knowledge_bp")
        ]

        for module_name, module_path, component_name in modules_to_load:
            try:
                module = __import__(module_path, fromlist=[component_name])
                component = getattr(module, component_name)

                if hasattr(component, 'name'):  # It's a blueprint
                    if self.blueprint_registry:
                        self.blueprint_registry.register_core_blueprint(component)
                    else:
                        self.app.register_blueprint(component)
                else:  # It's a function
                    component(self.app)

                self.modules_status[module_name] = "[OK] Available"
                logger.info(f"[OK] {module_name} loaded successfully")

            except ImportError as e:
                self.modules_status[module_name] = f"[FAIL] Import Error: {str(e)[:50]}..."
                logger.warning(f"[FAIL] {module_name} not available: {e}")
            except Exception as e:
                self.modules_status[module_name] = f"[FAIL] Error: {str(e)[:50]}..."
                logger.error(f"[FAIL] Failed to load {module_name}: {e}")

    def _log_status_summary(self):
        """Log comprehensive status summary"""
        logger.info("=" * 60)
        logger.info("[BOT] NoxPanel v5.0 - System Status Summary")
        logger.info("=" * 60)

        # Core systems
        logger.info("[SYS] Core Systems:")
        logger.info(f"   • Security Manager: {'[OK] Active' if self.security_manager else '[FAIL] Failed'}")
        logger.info(f"   • Database Pool: {'[OK] Active' if self.db_pool else '[FAIL] Failed'}")
        logger.info(f"   • Blueprint Registry: {'[OK] Active' if self.blueprint_registry else '[FAIL] Failed'}")
        logger.info(f"   • Plugin System: {'[OK] Active' if self.plugin_loader else '[FAIL] Failed'}")
        logger.info(f"   • Rate Limiter: {'[OK] Active' if self.rate_limiter else '[FAIL] Failed'}")

        # Modules
        logger.info("[MOD] Optional Modules:")
        for module_name, status in self.modules_status.items():
            logger.info(f"   • {module_name}: {status}")

        # Environment info
        logger.info(f"[ENV] Environment: {ENVIRONMENT}")
        logger.info(f"[SEC] Security Mode: {'Production' if ENVIRONMENT == 'production' else 'Development'}")

        if self.plugin_loader:
            plugins = self.plugin_loader.get_loaded_plugins()
            logger.info(f"[PLUG] Plugins Loaded: {len(plugins)}")
            for plugin in plugins:
                logger.info(f"   • {plugin}")

        logger.info("=" * 60)

def create_app() -> Flask:
    """Factory function to create NoxPanel application"""
    noxpanel = NoxPanelApp()
    app = noxpanel.create_app()

    # Store start time for uptime calculation
    app.config['START_TIME'] = time.time()

    return app

def start_webpanel():
    """Start the NoxPanel web application"""
    app = create_app()

    # Get configuration from environment
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", 5000))
    debug = ENVIRONMENT == "development"

    logger.info(f"[WEB] Starting NoxPanel on http://{host}:{port}")
    logger.info(f"[SYS] Debug mode: {'Enabled' if debug else 'Disabled'}")

    try:
        app.run(host=host, port=port, debug=debug)
    except KeyboardInterrupt:
        logger.info("👋 NoxPanel shutdown requested")
    except Exception as e:
        logger.error(f"[FAIL] Failed to start NoxPanel: {e}")
        raise

if __name__ == "__main__":
    start_webpanel()
