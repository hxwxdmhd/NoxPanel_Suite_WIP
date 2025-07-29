#!/usr/bin/env python3
"""
Heimnetz Ultimate Suite v11.0 - Microservices Gateway
Advanced API Gateway with service mesh integration, load balancing, and enterprise features.
"""

import os
import sys
import time
import json
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from urllib.parse import urlparse
import hashlib
import hmac

# Core Framework
from flask import Flask, request, jsonify, Response, stream_with_context
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS
from flask_compress import Compress
from werkzeug.middleware.proxy_fix import ProxyFix

# Async and Networking
import aiohttp
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Security
from cryptography.fernet import Fernet
import jwt
from passlib.hash import bcrypt

# Monitoring and Metrics
from prometheus_client import Counter, Histogram, Gauge, generate_latest
import structlog

# Service Discovery
import consul
from kubernetes import client, config

# Message Queue
import redis
import asyncio
from celery import Celery

# Configuration
from pydantic import BaseSettings, Field
from pydantic_settings import SettingsConfigDict

# Circuit Breaker
from pybreaker import CircuitBreaker

class GatewayConfig(BaseSettings):
    """Configuration for the API Gateway"""
    model_config = SettingsConfigDict(env_file=".env")
    
    # Core settings
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=5005)
    debug: bool = Field(default=False)
    
    # Security
    secret_key: str = Field(default="gateway-secret-key-v11.0")
    jwt_secret: str = Field(default="gateway-jwt-secret-v11.0")
    
    # Service Discovery
    consul_host: str = Field(default="consul-service")
    consul_port: int = Field(default=8500)
    
    # Kubernetes
    kubernetes_namespace: str = Field(default="heimnetz")
    kubernetes_enabled: bool = Field(default=True)
    
    # Redis
    redis_url: str = Field(default="redis://redis-service:6379")
    
    # Rate Limiting
    rate_limit_default: str = Field(default="1000 per hour")
    rate_limit_burst: str = Field(default="100 per minute")
    
    # Circuit Breaker
    circuit_breaker_threshold: int = Field(default=5)
    circuit_breaker_timeout: int = Field(default=60)
    
    # Load Balancing
    load_balancer_algorithm: str = Field(default="round_robin")
    health_check_interval: int = Field(default=30)
    
    # Monitoring
    metrics_enabled: bool = Field(default=True)
    tracing_enabled: bool = Field(default=True)
    
    # SSL/TLS
    ssl_cert_path: str = Field(default="")
    ssl_key_path: str = Field(default="")

@dataclass
class ServiceEndpoint:
    """Represents a service endpoint in the service mesh"""
    name: str
    host: str
    port: int
    path: str
    health_check_path: str
    weight: int = 1
    healthy: bool = True
    last_check: Optional[datetime] = None
    response_time: float = 0.0
    
    @property
    def url(self) -> str:
        return f"http://{self.host}:{self.port}{self.path}"
    
    @property
    def health_url(self) -> str:
        return f"http://{self.host}:{self.port}{self.health_check_path}"

class ServiceRegistry:
    """Service registry for managing microservices"""
    
    def __init__(self, config: GatewayConfig):
        self.config = config
        self.services: Dict[str, List[ServiceEndpoint]] = {}
        self.consul_client = None
        self.k8s_client = None
        
        # Initialize service discovery
        self._init_consul()
        self._init_kubernetes()
        
    def _init_consul(self):
        """Initialize Consul client"""
        try:
            self.consul_client = consul.Consul(
                host=self.config.consul_host,
                port=self.config.consul_port
            )
            logger.info("Consul client initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize Consul: {e}")
    
    def _init_kubernetes(self):
        """Initialize Kubernetes client"""
        try:
            if self.config.kubernetes_enabled:
                config.load_incluster_config()
                self.k8s_client = client.CoreV1Api()
                logger.info("Kubernetes client initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize Kubernetes: {e}")
    
    def register_service(self, service_name: str, endpoint: ServiceEndpoint):
        """Register a service endpoint"""
        if service_name not in self.services:
            self.services[service_name] = []
        
        self.services[service_name].append(endpoint)
        logger.info(f"Registered service: {service_name} -> {endpoint.url}")
    
    def discover_services(self):
        """Discover services from Consul and Kubernetes"""
        # Discover from Consul
        if self.consul_client:
            self._discover_consul_services()
        
        # Discover from Kubernetes
        if self.k8s_client:
            self._discover_k8s_services()
    
    def _discover_consul_services(self):
        """Discover services from Consul"""
        try:
            services = self.consul_client.catalog.services()[1]
            for service_name in services:
                service_info = self.consul_client.catalog.service(service_name)[1]
                for service in service_info:
                    endpoint = ServiceEndpoint(
                        name=service_name,
                        host=service['ServiceAddress'] or service['Address'],
                        port=service['ServicePort'],
                        path=service.get('ServiceMeta', {}).get('path', '/'),
                        health_check_path=service.get('ServiceMeta', {}).get('health_path', '/health')
                    )
                    self.register_service(service_name, endpoint)
        except Exception as e:
            logger.error(f"Failed to discover Consul services: {e}")
    
    def _discover_k8s_services(self):
        """Discover services from Kubernetes"""
        try:
            services = self.k8s_client.list_namespaced_service(
                namespace=self.config.kubernetes_namespace
            )
            for service in services.items:
                if service.metadata.labels and 'app' in service.metadata.labels:
                    service_name = service.metadata.labels['app']
                    for port in service.spec.ports:
                        endpoint = ServiceEndpoint(
                            name=service_name,
                            host=service.spec.cluster_ip,
                            port=port.port,
                            path=service.metadata.annotations.get('path', '/'),
                            health_check_path=service.metadata.annotations.get('health_path', '/health')
                        )
                        self.register_service(service_name, endpoint)
        except Exception as e:
            logger.error(f"Failed to discover Kubernetes services: {e}")
    
    def get_service_endpoint(self, service_name: str) -> Optional[ServiceEndpoint]:
        """Get a healthy service endpoint using load balancing"""
        if service_name not in self.services:
            return None
        
        endpoints = [ep for ep in self.services[service_name] if ep.healthy]
        if not endpoints:
            return None
        
        # Load balancing algorithm
        if self.config.load_balancer_algorithm == "round_robin":
            return self._round_robin_select(endpoints)
        elif self.config.load_balancer_algorithm == "least_connections":
            return self._least_connections_select(endpoints)
        elif self.config.load_balancer_algorithm == "weighted":
            return self._weighted_select(endpoints)
        else:
            return endpoints[0]
    
    def _round_robin_select(self, endpoints: List[ServiceEndpoint]) -> ServiceEndpoint:
        """Round-robin load balancing"""
        # Simple round-robin implementation
        import random
        return random.choice(endpoints)
    
    def _least_connections_select(self, endpoints: List[ServiceEndpoint]) -> ServiceEndpoint:
        """Least connections load balancing"""
        # For now, return the endpoint with best response time
        return min(endpoints, key=lambda ep: ep.response_time)
    
    def _weighted_select(self, endpoints: List[ServiceEndpoint]) -> ServiceEndpoint:
        """Weighted load balancing"""
        import random
        weights = [ep.weight for ep in endpoints]
        return random.choices(endpoints, weights=weights)[0]

class APIGateway:
    """Advanced API Gateway with enterprise features"""
    
    def __init__(self, config: GatewayConfig):
        self.config = config
        self.app = Flask(__name__)
        self.service_registry = ServiceRegistry(config)
        
        # Initialize components
        self._init_security()
        self._init_middleware()
        self._init_monitoring()
        self._init_circuit_breakers()
        self._init_routes()
        
        # Start background tasks
        self._start_background_tasks()
    
    def _init_security(self):
        """Initialize security components"""
        self.app.config['SECRET_KEY'] = self.config.secret_key
        
        # CORS configuration
        CORS(self.app, origins=["*"], supports_credentials=True)
        
        # Rate limiting
        self.limiter = Limiter(
            key_func=get_remote_address,
            app=self.app,
            default_limits=[self.config.rate_limit_default],
            storage_uri=self.config.redis_url
        )
        
        # Compression
        Compress(self.app)
        
        # Proxy fix for load balancers
        self.app.wsgi_app = ProxyFix(self.app.wsgi_app, x_for=1, x_proto=1)
    
    def _init_middleware(self):
        """Initialize middleware"""
        @self.app.before_request
        def before_request():
            request.start_time = time.time()
            
            # Log request
            logger.info(
                "Request started",
                method=request.method,
                path=request.path,
                remote_addr=request.remote_addr,
                user_agent=request.user_agent.string
            )
        
        @self.app.after_request
        def after_request(response):
            # Calculate response time
            response_time = time.time() - request.start_time
            
            # Update metrics
            REQUEST_COUNT.labels(
                method=request.method,
                endpoint=request.endpoint or 'unknown',
                status=response.status_code
            ).inc()
            
            REQUEST_DURATION.labels(
                method=request.method,
                endpoint=request.endpoint or 'unknown'
            ).observe(response_time)
            
            # Log response
            logger.info(
                "Request completed",
                method=request.method,
                path=request.path,
                status=response.status_code,
                response_time=response_time
            )
            
            return response
    
    def _init_monitoring(self):
        """Initialize monitoring and metrics"""
        global REQUEST_COUNT, REQUEST_DURATION, ACTIVE_CONNECTIONS
        
        REQUEST_COUNT = Counter(
            'gateway_requests_total',
            'Total number of requests',
            ['method', 'endpoint', 'status']
        )
        
        REQUEST_DURATION = Histogram(
            'gateway_request_duration_seconds',
            'Request duration in seconds',
            ['method', 'endpoint']
        )
        
        ACTIVE_CONNECTIONS = Gauge(
            'gateway_active_connections',
            'Number of active connections'
        )
    
    def _init_circuit_breakers(self):
        """Initialize circuit breakers for each service"""
        self.circuit_breakers = {}
        
        def create_circuit_breaker(service_name: str):
            return CircuitBreaker(
                failure_threshold=self.config.circuit_breaker_threshold,
                recovery_timeout=self.config.circuit_breaker_timeout,
                name=f"{service_name}_circuit_breaker"
            )
        
        # Create circuit breakers for known services
        for service_name in ["heimnetz-production", "auth-service", "user-service"]:
            self.circuit_breakers[service_name] = create_circuit_breaker(service_name)
    
    def _init_routes(self):
        """Initialize API routes"""
        
        @self.app.route('/health', methods=['GET'])
        def health_check():
            """Gateway health check"""
            return jsonify({
                'status': 'healthy',
                'timestamp': datetime.utcnow().isoformat(),
                'version': '11.0',
                'services': len(self.service_registry.services)
            })
        
        @self.app.route('/metrics', methods=['GET'])
        def metrics():
            """Prometheus metrics endpoint"""
            return generate_latest()
        
        @self.app.route('/gateway/status', methods=['GET'])
        @self.limiter.limit("100 per minute")
        def gateway_status():
            """Gateway status and service information"""
            services_status = {}
            for service_name, endpoints in self.service_registry.services.items():
                healthy_count = sum(1 for ep in endpoints if ep.healthy)
                services_status[service_name] = {
                    'total_endpoints': len(endpoints),
                    'healthy_endpoints': healthy_count,
                    'circuit_breaker_state': (
                        self.circuit_breakers.get(service_name, {}).state
                        if service_name in self.circuit_breakers else 'N/A'
                    )
                }
            
            return jsonify({
                'gateway_status': 'operational',
                'services': services_status,
                'timestamp': datetime.utcnow().isoformat()
            })
        
        @self.app.route('/<service_name>/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
        @self.limiter.limit(self.config.rate_limit_burst)
        def proxy_request(service_name: str, path: str):
            """Proxy requests to microservices"""
            return self._proxy_to_service(service_name, path)
        
        @self.app.route('/<service_name>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
        @self.limiter.limit(self.config.rate_limit_burst)
        def proxy_request_root(service_name: str):
            """Proxy requests to microservices root"""
            return self._proxy_to_service(service_name, "")
    
    def _proxy_to_service(self, service_name: str, path: str):
        """Proxy request to a microservice"""
        # Get service endpoint
        endpoint = self.service_registry.get_service_endpoint(service_name)
        if not endpoint:
            return jsonify({'error': f'Service {service_name} not found'}), 404
        
        # Build target URL
        target_url = f"{endpoint.url.rstrip('/')}/{path.lstrip('/')}"
        
        # Get circuit breaker
        circuit_breaker = self.circuit_breakers.get(service_name)
        
        try:
            # Execute request through circuit breaker
            if circuit_breaker:
                response = circuit_breaker(self._make_request)(target_url)
            else:
                response = self._make_request(target_url)
            
            # Stream response
            return Response(
                stream_with_context(response.iter_content(chunk_size=8192)),
                content_type=response.headers.get('content-type', 'application/json'),
                status=response.status_code
            )
            
        except Exception as e:
            logger.error(f"Error proxying to {service_name}: {e}")
            return jsonify({'error': 'Service unavailable'}), 503
    
    def _make_request(self, target_url: str):
        """Make HTTP request with retry logic"""
        session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Make request
        response = session.request(
            method=request.method,
            url=target_url,
            headers=self._get_forwarded_headers(),
            data=request.get_data(),
            params=request.args,
            timeout=30,
            stream=True
        )
        
        return response
    
    def _get_forwarded_headers(self) -> Dict[str, str]:
        """Get headers to forward to the service"""
        headers = {}
        
        # Forward important headers
        for header in ['Authorization', 'Content-Type', 'Accept', 'User-Agent']:
            if header in request.headers:
                headers[header] = request.headers[header]
        
        # Add gateway headers
        headers['X-Forwarded-For'] = request.remote_addr
        headers['X-Forwarded-Proto'] = request.scheme
        headers['X-Gateway-Version'] = '11.0'
        
        return headers
    
    def _start_background_tasks(self):
        """Start background tasks"""
        import threading
        
        # Health check task
        def health_check_task():
            while True:
                try:
                    self._check_service_health()
                    time.sleep(self.config.health_check_interval)
                except Exception as e:
                    logger.error(f"Health check error: {e}")
        
        # Service discovery task
        def service_discovery_task():
            while True:
                try:
                    self.service_registry.discover_services()
                    time.sleep(60)  # Discover every minute
                except Exception as e:
                    logger.error(f"Service discovery error: {e}")
        
        # Start background threads
        threading.Thread(target=health_check_task, daemon=True).start()
        threading.Thread(target=service_discovery_task, daemon=True).start()
    
    def _check_service_health(self):
        """Check health of all registered services"""
        for service_name, endpoints in self.service_registry.services.items():
            for endpoint in endpoints:
                try:
                    start_time = time.time()
                    response = requests.get(
                        endpoint.health_url,
                        timeout=5,
                        headers={'User-Agent': 'Heimnetz-Gateway/11.0'}
                    )
                    
                    endpoint.response_time = time.time() - start_time
                    endpoint.healthy = response.status_code == 200
                    endpoint.last_check = datetime.utcnow()
                    
                except Exception as e:
                    endpoint.healthy = False
                    endpoint.last_check = datetime.utcnow()
                    logger.warning(f"Health check failed for {endpoint.name}: {e}")
    
    def run(self):
        """Run the gateway"""
        logger.info(f"Starting API Gateway on {self.config.host}:{self.config.port}")
        
        # SSL context
        ssl_context = None
        if self.config.ssl_cert_path and self.config.ssl_key_path:
            ssl_context = (self.config.ssl_cert_path, self.config.ssl_key_path)
        
        # Run the server
        self.app.run(
            host=self.config.host,
            port=self.config.port,
            debug=self.config.debug,
            ssl_context=ssl_context,
            threaded=True
        )

# Initialize logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

def main():
    """Main entry point"""
    logger.info("Initializing Heimnetz API Gateway v11.0")
    
    # Load configuration
    config = GatewayConfig()
    
    # Create and run gateway
    gateway = APIGateway(config)
    
    # Register some default services
    gateway.service_registry.register_service(
        "heimnetz-production",
        ServiceEndpoint(
            name="heimnetz-production",
            host="heimnetz-production-service",
            port=80,
            path="/",
            health_check_path="/health"
        )
    )
    
    # Run the gateway
    gateway.run()

if __name__ == "__main__":
    main()
