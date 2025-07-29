#!/usr/bin/env python3
"""
Analytics Dashboard System - Audit 4 Advanced Features
=====================================================

This system provides comprehensive analytics and reporting capabilities:
- Real-time metrics collection
- Interactive dashboards
- Performance monitoring
- User behavior tracking
- Security analytics
- Custom reports
- Data visualization

Essential for system monitoring and business intelligence
"""

import os
import sys
import json
import time
import asyncio
import logging
import threading
from typing import Dict, List, Optional, Any, Union, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import sqlite3
import hashlib
import uuid
from collections import defaultdict, deque
import statistics

# Optional imports with fallbacks
try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

try:
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

try:
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MetricType(Enum):
    """Types of metrics"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"
    RATE = "rate"

class AlertLevel(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class TimeRange(Enum):
    """Time range options"""
    LAST_HOUR = "1h"
    LAST_24H = "24h"
    LAST_7D = "7d"
    LAST_30D = "30d"
    LAST_90D = "90d"
    CUSTOM = "custom"

@dataclass
class Metric:
    """Individual metric data point"""
    name: str
    value: float
    timestamp: datetime
    labels: Dict[str, str] = field(default_factory=dict)
    metric_type: MetricType = MetricType.GAUGE
    unit: str = ""
    description: str = ""

@dataclass
class Alert:
    """Alert configuration"""
    id: str
    name: str
    condition: str
    threshold: float
    level: AlertLevel
    enabled: bool = True
    notification_channels: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    last_triggered: Optional[datetime] = None
    trigger_count: int = 0

@dataclass
class Dashboard:
    """Dashboard configuration"""
    id: str
    name: str
    description: str
    widgets: List[Dict[str, Any]] = field(default_factory=list)
    layout: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    owner: str = ""
    is_public: bool = False

class MetricsCollector:
    """
    Metrics collection and storage system
    """
    
    def __init__(self, storage_path: str = "analytics.db"):
        self.storage_path = storage_path
        self.metrics_buffer = deque(maxlen=10000)
        self.real_time_metrics = {}
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Initialize database
        self._init_database()
        
        # Start background tasks
        self._start_background_tasks()
    
    def _init_database(self) -> None:
        """Initialize SQLite database"""
        try:
            conn = sqlite3.connect(self.storage_path)
            cursor = conn.cursor()
            
            # Create tables
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    value REAL NOT NULL,
                    timestamp DATETIME NOT NULL,
                    labels TEXT,
                    metric_type TEXT,
                    unit TEXT,
                    description TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS alerts (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    condition TEXT NOT NULL,
                    threshold REAL NOT NULL,
                    level TEXT NOT NULL,
                    enabled INTEGER DEFAULT 1,
                    notification_channels TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_triggered DATETIME,
                    trigger_count INTEGER DEFAULT 0
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS dashboards (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    widgets TEXT,
                    layout TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    owner TEXT,
                    is_public INTEGER DEFAULT 0
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    user_id TEXT,
                    session_id TEXT,
                    data TEXT,
                    timestamp DATETIME NOT NULL,
                    ip_address TEXT,
                    user_agent TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_metrics_name_timestamp ON metrics (name, timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_type_timestamp ON events (event_type, timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_user_timestamp ON events (user_id, timestamp)")
            
            conn.commit()
            conn.close()
            
            self.logger.info("Database initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize database: {e}")
    
    def _start_background_tasks(self) -> None:
        """Start background tasks"""
        try:
            # Start metrics flushing task
            threading.Thread(target=self._flush_metrics_loop, daemon=True).start()
            
            # Start real-time metrics cleanup task
            threading.Thread(target=self._cleanup_real_time_metrics, daemon=True).start()
            
            self.logger.info("Background tasks started")
            
        except Exception as e:
            self.logger.error(f"Failed to start background tasks: {e}")
    
    def collect_metric(self, name: str, value: float, labels: Dict[str, str] = None,
                      metric_type: MetricType = MetricType.GAUGE, unit: str = "",
                      description: str = "") -> None:
        """
        Collect a metric data point
        
        Args:
            name: Metric name
            value: Metric value
            labels: Optional labels
            metric_type: Type of metric
            unit: Unit of measurement
            description: Metric description
        """
        try:
            metric = Metric(
                name=name,
                value=value,
                timestamp=datetime.now(),
                labels=labels or {},
                metric_type=metric_type,
                unit=unit,
                description=description
            )
            
            # Add to buffer for batch processing
            self.metrics_buffer.append(metric)
            
            # Update real-time metrics
            self._update_real_time_metrics(metric)
            
        except Exception as e:
            self.logger.error(f"Error collecting metric: {e}")
    
    def _update_real_time_metrics(self, metric: Metric) -> None:
        """Update real-time metrics cache"""
        try:
            key = f"{metric.name}:{json.dumps(metric.labels, sort_keys=True)}"
            
            if key not in self.real_time_metrics:
                self.real_time_metrics[key] = {
                    'current_value': metric.value,
                    'history': deque(maxlen=100),
                    'last_updated': metric.timestamp,
                    'count': 1,
                    'sum': metric.value,
                    'min': metric.value,
                    'max': metric.value
                }
            else:
                rt_metric = self.real_time_metrics[key]
                rt_metric['current_value'] = metric.value
                rt_metric['history'].append((metric.timestamp, metric.value))
                rt_metric['last_updated'] = metric.timestamp
                rt_metric['count'] += 1
                rt_metric['sum'] += metric.value
                rt_metric['min'] = min(rt_metric['min'], metric.value)
                rt_metric['max'] = max(rt_metric['max'], metric.value)
            
        except Exception as e:
            self.logger.error(f"Error updating real-time metrics: {e}")
    
    def _flush_metrics_loop(self) -> None:
        """Flush metrics to database periodically"""
        while True:
            try:
                time.sleep(10)  # Flush every 10 seconds
                self._flush_metrics()
            except Exception as e:
                self.logger.error(f"Error in metrics flush loop: {e}")
    
    def _flush_metrics(self) -> None:
        """Flush metrics buffer to database"""
        try:
            if not self.metrics_buffer:
                return
            
            # Get metrics to flush
            metrics_to_flush = []
            while self.metrics_buffer and len(metrics_to_flush) < 1000:
                metrics_to_flush.append(self.metrics_buffer.popleft())
            
            if not metrics_to_flush:
                return
            
            # Insert into database
            conn = sqlite3.connect(self.storage_path)
            cursor = conn.cursor()
            
            for metric in metrics_to_flush:
                cursor.execute("""
                    INSERT INTO metrics (name, value, timestamp, labels, metric_type, unit, description)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    metric.name,
                    metric.value,
                    metric.timestamp.isoformat(),
                    json.dumps(metric.labels),
                    metric.metric_type.value,
                    metric.unit,
                    metric.description
                ))
            
            conn.commit()
            conn.close()
            
            self.logger.debug(f"Flushed {len(metrics_to_flush)} metrics to database")
            
        except Exception as e:
            self.logger.error(f"Error flushing metrics: {e}")
    
    def _cleanup_real_time_metrics(self) -> None:
        """Clean up old real-time metrics"""
        while True:
            try:
                time.sleep(300)  # Cleanup every 5 minutes
                
                cutoff_time = datetime.now() - timedelta(minutes=30)
                
                # Remove old metrics
                keys_to_remove = []
                for key, metric in self.real_time_metrics.items():
                    if metric['last_updated'] < cutoff_time:
                        keys_to_remove.append(key)
                
                for key in keys_to_remove:
                    del self.real_time_metrics[key]
                
                if keys_to_remove:
                    self.logger.debug(f"Cleaned up {len(keys_to_remove)} old real-time metrics")
                    
            except Exception as e:
                self.logger.error(f"Error cleaning up real-time metrics: {e}")
    
    def get_metrics(self, name: str, time_range: TimeRange = TimeRange.LAST_24H,
                   start_time: Optional[datetime] = None, end_time: Optional[datetime] = None,
                   labels: Dict[str, str] = None) -> List[Dict[str, Any]]:
        """
        Get metrics from database
        
        Args:
            name: Metric name
            time_range: Time range
            start_time: Custom start time
            end_time: Custom end time
            labels: Filter by labels
            
        Returns:
            List of metric data points
        """
        try:
            conn = sqlite3.connect(self.storage_path)
            cursor = conn.cursor()
            
            # Calculate time range
            if time_range == TimeRange.CUSTOM:
                if not start_time or not end_time:
                    raise ValueError("start_time and end_time required for custom range")
            else:
                end_time = datetime.now()
                if time_range == TimeRange.LAST_HOUR:
                    start_time = end_time - timedelta(hours=1)
                elif time_range == TimeRange.LAST_24H:
                    start_time = end_time - timedelta(days=1)
                elif time_range == TimeRange.LAST_7D:
                    start_time = end_time - timedelta(days=7)
                elif time_range == TimeRange.LAST_30D:
                    start_time = end_time - timedelta(days=30)
                elif time_range == TimeRange.LAST_90D:
                    start_time = end_time - timedelta(days=90)
            
            # Build query
            query = """
                SELECT name, value, timestamp, labels, metric_type, unit, description
                FROM metrics
                WHERE name = ? AND timestamp >= ? AND timestamp <= ?
            """
            params = [name, start_time.isoformat(), end_time.isoformat()]
            
            # Add labels filter
            if labels:
                for key, value in labels.items():
                    query += " AND labels LIKE ?"
                    params.append(f'%"{key}": "{value}"%')
            
            query += " ORDER BY timestamp ASC"
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            conn.close()
            
            # Convert to list of dictionaries
            metrics = []
            for row in rows:
                metrics.append({
                    'name': row[0],
                    'value': row[1],
                    'timestamp': datetime.fromisoformat(row[2]),
                    'labels': json.loads(row[3]) if row[3] else {},
                    'metric_type': row[4],
                    'unit': row[5],
                    'description': row[6]
                })
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error getting metrics: {e}")
            return []
    
    def get_real_time_metrics(self, name_pattern: str = "*") -> Dict[str, Dict[str, Any]]:
        """
        Get real-time metrics
        
        Args:
            name_pattern: Pattern to match metric names
            
        Returns:
            Dictionary of real-time metrics
        """
        try:
            if name_pattern == "*":
                return self.real_time_metrics.copy()
            
            # Filter by pattern
            filtered_metrics = {}
            for key, metric in self.real_time_metrics.items():
                metric_name = key.split(':')[0]
                if name_pattern in metric_name:
                    filtered_metrics[key] = metric
            
            return filtered_metrics
            
        except Exception as e:
            self.logger.error(f"Error getting real-time metrics: {e}")
            return {}
    
    def track_event(self, event_type: str, user_id: str = None, session_id: str = None,
                   data: Dict[str, Any] = None, ip_address: str = None,
                   user_agent: str = None) -> None:
        """
        Track an event
        
        Args:
            event_type: Type of event
            user_id: User identifier
            session_id: Session identifier
            data: Event data
            ip_address: IP address
            user_agent: User agent string
        """
        try:
            conn = sqlite3.connect(self.storage_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO events (event_type, user_id, session_id, data, timestamp, ip_address, user_agent)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                event_type,
                user_id,
                session_id,
                json.dumps(data) if data else None,
                datetime.now().isoformat(),
                ip_address,
                user_agent
            ))
            
            conn.commit()
            conn.close()
            
            self.logger.debug(f"Tracked event: {event_type}")
            
        except Exception as e:
            self.logger.error(f"Error tracking event: {e}")

class AlertManager:
    """
    Alert management system
    """
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics_collector = metrics_collector
        self.alerts = {}
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Load alerts from database
        self._load_alerts()
        
        # Start alert evaluation loop
        threading.Thread(target=self._alert_evaluation_loop, daemon=True).start()
    
    def _load_alerts(self) -> None:
        """Load alerts from database"""
        try:
            conn = sqlite3.connect(self.metrics_collector.storage_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM alerts")
            rows = cursor.fetchall()
            
            for row in rows:
                alert = Alert(
                    id=row[0],
                    name=row[1],
                    condition=row[2],
                    threshold=row[3],
                    level=AlertLevel(row[4]),
                    enabled=bool(row[5]),
                    notification_channels=json.loads(row[6]) if row[6] else [],
                    created_at=datetime.fromisoformat(row[7]) if row[7] else datetime.now(),
                    last_triggered=datetime.fromisoformat(row[8]) if row[8] else None,
                    trigger_count=row[9] or 0
                )
                self.alerts[alert.id] = alert
            
            conn.close()
            
            self.logger.info(f"Loaded {len(self.alerts)} alerts")
            
        except Exception as e:
            self.logger.error(f"Error loading alerts: {e}")
    
    def create_alert(self, name: str, condition: str, threshold: float,
                    level: AlertLevel, notification_channels: List[str] = None) -> str:
        """
        Create a new alert
        
        Args:
            name: Alert name
            condition: Alert condition (e.g., "cpu_usage > threshold")
            threshold: Alert threshold value
            level: Alert level
            notification_channels: List of notification channels
            
        Returns:
            Alert ID
        """
        try:
            alert_id = str(uuid.uuid4())
            
            alert = Alert(
                id=alert_id,
                name=name,
                condition=condition,
                threshold=threshold,
                level=level,
                notification_channels=notification_channels or []
            )
            
            # Save to database
            conn = sqlite3.connect(self.metrics_collector.storage_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO alerts (id, name, condition, threshold, level, notification_channels)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                alert.id,
                alert.name,
                alert.condition,
                alert.threshold,
                alert.level.value,
                json.dumps(alert.notification_channels)
            ))
            
            conn.commit()
            conn.close()
            
            # Add to memory
            self.alerts[alert_id] = alert
            
            self.logger.info(f"Created alert: {name} ({alert_id})")
            return alert_id
            
        except Exception as e:
            self.logger.error(f"Error creating alert: {e}")
            return ""
    
    def _alert_evaluation_loop(self) -> None:
        """Evaluate alerts periodically"""
        while True:
            try:
                time.sleep(60)  # Evaluate every minute
                self._evaluate_alerts()
            except Exception as e:
                self.logger.error(f"Error in alert evaluation loop: {e}")
    
    def _evaluate_alerts(self) -> None:
        """Evaluate all alerts"""
        try:
            for alert_id, alert in self.alerts.items():
                if not alert.enabled:
                    continue
                
                # Get current metrics
                real_time_metrics = self.metrics_collector.get_real_time_metrics()
                
                # Evaluate condition
                if self._evaluate_condition(alert.condition, alert.threshold, real_time_metrics):
                    self._trigger_alert(alert)
                    
        except Exception as e:
            self.logger.error(f"Error evaluating alerts: {e}")
    
    def _evaluate_condition(self, condition: str, threshold: float,
                          metrics: Dict[str, Dict[str, Any]]) -> bool:
        """Evaluate alert condition"""
        try:
            # Simple condition evaluation
            # In production, this would be more sophisticated
            
            # Extract metric name from condition
            if ">" in condition:
                metric_name = condition.split(">")[0].strip()
                operator = ">"
            elif "<" in condition:
                metric_name = condition.split("<")[0].strip()
                operator = "<"
            elif "==" in condition:
                metric_name = condition.split("==")[0].strip()
                operator = "=="
            else:
                return False
            
            # Find metric in real-time metrics
            for key, metric in metrics.items():
                if key.startswith(metric_name):
                    value = metric['current_value']
                    
                    if operator == ">" and value > threshold:
                        return True
                    elif operator == "<" and value < threshold:
                        return True
                    elif operator == "==" and value == threshold:
                        return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error evaluating condition: {e}")
            return False
    
    def _trigger_alert(self, alert: Alert) -> None:
        """Trigger an alert"""
        try:
            # Update alert statistics
            alert.last_triggered = datetime.now()
            alert.trigger_count += 1
            
            # Update database
            conn = sqlite3.connect(self.metrics_collector.storage_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE alerts
                SET last_triggered = ?, trigger_count = ?
                WHERE id = ?
            """, (
                alert.last_triggered.isoformat(),
                alert.trigger_count,
                alert.id
            ))
            
            conn.commit()
            conn.close()
            
            # Send notifications
            self._send_notifications(alert)
            
            self.logger.warning(f"Alert triggered: {alert.name} ({alert.level.value})")
            
        except Exception as e:
            self.logger.error(f"Error triggering alert: {e}")
    
    def _send_notifications(self, alert: Alert) -> None:
        """Send alert notifications"""
        try:
            # In production, this would send actual notifications
            # via email, Slack, SMS, etc.
            
            message = f"Alert: {alert.name} - Level: {alert.level.value} - Threshold: {alert.threshold}"
            
            for channel in alert.notification_channels:
                self.logger.info(f"Sending notification to {channel}: {message}")
                
        except Exception as e:
            self.logger.error(f"Error sending notifications: {e}")

class DashboardManager:
    """
    Dashboard management system
    """
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics_collector = metrics_collector
        self.dashboards = {}
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Load dashboards from database
        self._load_dashboards()
    
    def _load_dashboards(self) -> None:
        """Load dashboards from database"""
        try:
            conn = sqlite3.connect(self.metrics_collector.storage_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM dashboards")
            rows = cursor.fetchall()
            
            for row in rows:
                dashboard = Dashboard(
                    id=row[0],
                    name=row[1],
                    description=row[2] or "",
                    widgets=json.loads(row[3]) if row[3] else [],
                    layout=json.loads(row[4]) if row[4] else {},
                    created_at=datetime.fromisoformat(row[5]) if row[5] else datetime.now(),
                    updated_at=datetime.fromisoformat(row[6]) if row[6] else datetime.now(),
                    owner=row[7] or "",
                    is_public=bool(row[8])
                )
                self.dashboards[dashboard.id] = dashboard
            
            conn.close()
            
            self.logger.info(f"Loaded {len(self.dashboards)} dashboards")
            
        except Exception as e:
            self.logger.error(f"Error loading dashboards: {e}")
    
    def create_dashboard(self, name: str, description: str = "", owner: str = "",
                        is_public: bool = False) -> str:
        """
        Create a new dashboard
        
        Args:
            name: Dashboard name
            description: Dashboard description
            owner: Dashboard owner
            is_public: Whether dashboard is public
            
        Returns:
            Dashboard ID
        """
        try:
            dashboard_id = str(uuid.uuid4())
            
            dashboard = Dashboard(
                id=dashboard_id,
                name=name,
                description=description,
                owner=owner,
                is_public=is_public
            )
            
            # Save to database
            conn = sqlite3.connect(self.metrics_collector.storage_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO dashboards (id, name, description, widgets, layout, owner, is_public)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                dashboard.id,
                dashboard.name,
                dashboard.description,
                json.dumps(dashboard.widgets),
                json.dumps(dashboard.layout),
                dashboard.owner,
                int(dashboard.is_public)
            ))
            
            conn.commit()
            conn.close()
            
            # Add to memory
            self.dashboards[dashboard_id] = dashboard
            
            self.logger.info(f"Created dashboard: {name} ({dashboard_id})")
            return dashboard_id
            
        except Exception as e:
            self.logger.error(f"Error creating dashboard: {e}")
            return ""
    
    def add_widget(self, dashboard_id: str, widget_config: Dict[str, Any]) -> bool:
        """
        Add widget to dashboard
        
        Args:
            dashboard_id: Dashboard identifier
            widget_config: Widget configuration
            
        Returns:
            True if successful
        """
        try:
            if dashboard_id not in self.dashboards:
                raise ValueError(f"Dashboard not found: {dashboard_id}")
            
            dashboard = self.dashboards[dashboard_id]
            
            # Add widget ID
            widget_config['id'] = str(uuid.uuid4())
            
            # Add widget to dashboard
            dashboard.widgets.append(widget_config)
            dashboard.updated_at = datetime.now()
            
            # Update database
            conn = sqlite3.connect(self.metrics_collector.storage_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE dashboards
                SET widgets = ?, updated_at = ?
                WHERE id = ?
            """, (
                json.dumps(dashboard.widgets),
                dashboard.updated_at.isoformat(),
                dashboard_id
            ))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"Added widget to dashboard: {dashboard_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error adding widget: {e}")
            return False
    
    def generate_chart(self, chart_type: str, metric_name: str, time_range: TimeRange,
                      labels: Dict[str, str] = None) -> Optional[str]:
        """
        Generate chart for metrics
        
        Args:
            chart_type: Type of chart (line, bar, pie, etc.)
            metric_name: Metric name
            time_range: Time range
            labels: Optional labels filter
            
        Returns:
            Chart HTML or None if failed
        """
        try:
            if not HAS_PLOTLY:
                self.logger.warning("Plotly not installed - using fallback")
                return self._generate_fallback_chart(metric_name, time_range, labels)
            
            # Get metrics data
            metrics = self.metrics_collector.get_metrics(metric_name, time_range, labels=labels)
            
            if not metrics:
                return None
            
            # Extract data
            timestamps = [m['timestamp'] for m in metrics]
            values = [m['value'] for m in metrics]
            
            # Create chart
            if chart_type == "line":
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=timestamps,
                    y=values,
                    mode='lines+markers',
                    name=metric_name
                ))
                fig.update_layout(
                    title=f"{metric_name} - {time_range.value}",
                    xaxis_title="Time",
                    yaxis_title="Value"
                )
                
            elif chart_type == "bar":
                fig = go.Figure()
                fig.add_trace(go.Bar(
                    x=timestamps,
                    y=values,
                    name=metric_name
                ))
                fig.update_layout(
                    title=f"{metric_name} - {time_range.value}",
                    xaxis_title="Time",
                    yaxis_title="Value"
                )
                
            else:
                # Default to line chart
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=timestamps,
                    y=values,
                    mode='lines',
                    name=metric_name
                ))
            
            # Convert to HTML
            chart_html = fig.to_html(include_plotlyjs='cdn')
            return chart_html
            
        except Exception as e:
            self.logger.error(f"Error generating chart: {e}")
            return None
    
    def _generate_fallback_chart(self, metric_name: str, time_range: TimeRange,
                                labels: Dict[str, str] = None) -> str:
        """Generate fallback chart without Plotly"""
        try:
            # Get metrics data
            metrics = self.metrics_collector.get_metrics(metric_name, time_range, labels=labels)
            
            if not metrics:
                return "<div>No data available</div>"
            
            # Generate simple HTML table
            html = f"""
            <div class="chart-container">
                <h3>{metric_name} - {time_range.value}</h3>
                <table border="1" style="border-collapse: collapse; width: 100%;">
                    <tr>
                        <th>Timestamp</th>
                        <th>Value</th>
                    </tr>
            """
            
            for metric in metrics[-20:]:  # Show last 20 points
                html += f"""
                    <tr>
                        <td>{metric['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}</td>
                        <td>{metric['value']}</td>
                    </tr>
                """
            
            html += """
                </table>
            </div>
            """
            
            return html
            
        except Exception as e:
            self.logger.error(f"Error generating fallback chart: {e}")
            return "<div>Error generating chart</div>"

class AnalyticsEngine:
    """
    Main analytics engine coordinating all components
    """
    
    def __init__(self, storage_path: str = "analytics.db"):
        self.storage_path = storage_path
        self.metrics_collector = MetricsCollector(storage_path)
        self.alert_manager = AlertManager(self.metrics_collector)
        self.dashboard_manager = DashboardManager(self.metrics_collector)
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Start system monitoring
        self._start_system_monitoring()
    
    def _start_system_monitoring(self) -> None:
        """Start system monitoring"""
        try:
            # Start background system monitoring
            threading.Thread(target=self._system_monitoring_loop, daemon=True).start()
            
            self.logger.info("System monitoring started")
            
        except Exception as e:
            self.logger.error(f"Error starting system monitoring: {e}")
    
    def _system_monitoring_loop(self) -> None:
        """System monitoring loop"""
        while True:
            try:
                time.sleep(30)  # Monitor every 30 seconds
                
                # Collect system metrics
                self._collect_system_metrics()
                
            except Exception as e:
                self.logger.error(f"Error in system monitoring loop: {e}")
    
    def _collect_system_metrics(self) -> None:
        """Collect system performance metrics"""
        try:
            import psutil
            
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            self.metrics_collector.collect_metric(
                "system_cpu_usage",
                cpu_percent,
                metric_type=MetricType.GAUGE,
                unit="percent"
            )
            
            # Memory usage
            memory = psutil.virtual_memory()
            self.metrics_collector.collect_metric(
                "system_memory_usage",
                memory.percent,
                metric_type=MetricType.GAUGE,
                unit="percent"
            )
            
            # Disk usage
            disk = psutil.disk_usage('/')
            self.metrics_collector.collect_metric(
                "system_disk_usage",
                (disk.used / disk.total) * 100,
                metric_type=MetricType.GAUGE,
                unit="percent"
            )
            
            # Network I/O
            net_io = psutil.net_io_counters()
            self.metrics_collector.collect_metric(
                "system_network_bytes_sent",
                net_io.bytes_sent,
                metric_type=MetricType.COUNTER,
                unit="bytes"
            )
            self.metrics_collector.collect_metric(
                "system_network_bytes_recv",
                net_io.bytes_recv,
                metric_type=MetricType.COUNTER,
                unit="bytes"
            )
            
        except ImportError:
            # psutil not available
            pass
        except Exception as e:
            self.logger.error(f"Error collecting system metrics: {e}")
    
    def get_summary_report(self) -> Dict[str, Any]:
        """
        Generate summary report
        
        Returns:
            Summary report data
        """
        try:
            report = {
                "timestamp": datetime.now().isoformat(),
                "metrics": {
                    "total_metrics": len(self.metrics_collector.real_time_metrics),
                    "active_alerts": len([a for a in self.alert_manager.alerts.values() if a.enabled]),
                    "total_dashboards": len(self.dashboard_manager.dashboards)
                },
                "system_status": self._get_system_status(),
                "recent_alerts": self._get_recent_alerts(),
                "top_metrics": self._get_top_metrics()
            }
            
            return report
            
        except Exception as e:
            self.logger.error(f"Error generating summary report: {e}")
            return {}
    
    def _get_system_status(self) -> Dict[str, Any]:
        """Get system status"""
        try:
            real_time_metrics = self.metrics_collector.get_real_time_metrics()
            
            status = {
                "overall": "healthy",
                "cpu_usage": 0,
                "memory_usage": 0,
                "disk_usage": 0
            }
            
            # Get system metrics
            for key, metric in real_time_metrics.items():
                if "system_cpu_usage" in key:
                    status["cpu_usage"] = metric["current_value"]
                elif "system_memory_usage" in key:
                    status["memory_usage"] = metric["current_value"]
                elif "system_disk_usage" in key:
                    status["disk_usage"] = metric["current_value"]
            
            # Determine overall status
            if status["cpu_usage"] > 90 or status["memory_usage"] > 90 or status["disk_usage"] > 90:
                status["overall"] = "critical"
            elif status["cpu_usage"] > 70 or status["memory_usage"] > 70 or status["disk_usage"] > 70:
                status["overall"] = "warning"
            
            return status
            
        except Exception as e:
            self.logger.error(f"Error getting system status: {e}")
            return {"overall": "unknown"}
    
    def _get_recent_alerts(self) -> List[Dict[str, Any]]:
        """Get recent alerts"""
        try:
            recent_alerts = []
            
            for alert in self.alert_manager.alerts.values():
                if alert.last_triggered:
                    recent_alerts.append({
                        "name": alert.name,
                        "level": alert.level.value,
                        "last_triggered": alert.last_triggered.isoformat(),
                        "trigger_count": alert.trigger_count
                    })
            
            # Sort by last triggered
            recent_alerts.sort(key=lambda x: x["last_triggered"], reverse=True)
            
            return recent_alerts[:5]  # Return top 5
            
        except Exception as e:
            self.logger.error(f"Error getting recent alerts: {e}")
            return []
    
    def _get_top_metrics(self) -> List[Dict[str, Any]]:
        """Get top metrics by activity"""
        try:
            real_time_metrics = self.metrics_collector.get_real_time_metrics()
            
            top_metrics = []
            for key, metric in real_time_metrics.items():
                metric_name = key.split(':')[0]
                top_metrics.append({
                    "name": metric_name,
                    "current_value": metric["current_value"],
                    "count": metric["count"],
                    "last_updated": metric["last_updated"].isoformat()
                })
            
            # Sort by count (activity)
            top_metrics.sort(key=lambda x: x["count"], reverse=True)
            
            return top_metrics[:10]  # Return top 10
            
        except Exception as e:
            self.logger.error(f"Error getting top metrics: {e}")
            return []

def main():
    """Main function for testing analytics system"""
    try:
        print("Analytics Dashboard System - Test Mode")
        print("=" * 45)
        
        # Initialize analytics engine
        analytics = AnalyticsEngine()
        
        print("Analytics engine initialized")
        
        # Test metrics collection
        print("\nTesting metrics collection...")
        for i in range(10):
            analytics.metrics_collector.collect_metric(
                "test_metric",
                i * 10,
                labels={"category": "test"},
                metric_type=MetricType.GAUGE
            )
            time.sleep(0.1)
        
        # Test alert creation
        print("Testing alert creation...")
        alert_id = analytics.alert_manager.create_alert(
            "Test Alert",
            "test_metric > threshold",
            50.0,
            AlertLevel.WARNING
        )
        print(f"Created alert: {alert_id}")
        
        # Test dashboard creation
        print("Testing dashboard creation...")
        dashboard_id = analytics.dashboard_manager.create_dashboard(
            "Test Dashboard",
            "Test dashboard description"
        )
        print(f"Created dashboard: {dashboard_id}")
        
        # Generate summary report
        print("Generating summary report...")
        report = analytics.get_summary_report()
        print(f"Report: {json.dumps(report, indent=2)}")
        
        print("\nAnalytics system test completed!")
        
    except Exception as e:
        print(f"Error in analytics system: {e}")
        logger.error(f"Analytics system error: {e}")

if __name__ == "__main__":
    main()
