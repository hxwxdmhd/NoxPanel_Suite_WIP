"""
Diagnostic & Reporting Agent - Core implementation

Aggregates logs, agent outputs, audit data, and ChatGPT validations into a 
human-friendly, ADHD-optimized system health report.
"""

import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import shutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Path(__file__).parent / 'diagnostic_reporting.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("DiagnosticReportingAgent")

class DiagnosticReportingAgent:
    """
    Diagnostic & Reporting Agent that aggregates logs, agent outputs, audit data,
    and ChatGPT validations into human-friendly, ADHD-optimized system health reports.
    """
    
    def __init__(self, 
                 report_dir: str = None,
                 max_report_history: int = 10):
        """
        Initialize the Diagnostic & Reporting Agent
        
        Args:
            report_dir: Directory to store reports
            max_report_history: Maximum number of historical reports to keep
        """
        self.report_dir = report_dir or str(Path(__file__).parent / 'reports')
        os.makedirs(self.report_dir, exist_ok=True)
        
        self.max_report_history = max_report_history
        self.report_history = []
        self.last_report = {}
        
        # Create directories for each report type
        self.daily_report_dir = os.path.join(self.report_dir, 'daily')
        self.health_report_dir = os.path.join(self.report_dir, 'health')
        self.alert_report_dir = os.path.join(self.report_dir, 'alerts')
        self.summary_report_dir = os.path.join(self.report_dir, 'summary')
        
        os.makedirs(self.daily_report_dir, exist_ok=True)
        os.makedirs(self.health_report_dir, exist_ok=True)
        os.makedirs(self.alert_report_dir, exist_ok=True)
        os.makedirs(self.summary_report_dir, exist_ok=True)
        
        logger.info(f"Diagnostic & Reporting Agent initialized with report directory: {self.report_dir}")
        self._load_report_history()
    
    def _load_report_history(self) -> None:
        """
        Load report history from the report directory
        """
        try:
            history_file = os.path.join(self.report_dir, 'report_history.json')
            if os.path.exists(history_file):
                with open(history_file, 'r') as f:
                    self.report_history = json.load(f)
                logger.info(f"Loaded {len(self.report_history)} historical reports")
        except Exception as e:
            logger.error(f"Error loading report history: {e}")
            self.report_history = []
    
    def _save_report_history(self) -> None:
        """
        Save report history to the report directory
        """
        try:
            history_file = os.path.join(self.report_dir, 'report_history.json')
            with open(history_file, 'w') as f:
                json.dump(self.report_history, f, indent=2)
            logger.info(f"Saved {len(self.report_history)} reports to history")
        except Exception as e:
            logger.error(f"Error saving report history: {e}")
    
    def collect_agent_data(self) -> Dict[str, Any]:
        """
        Collect data from all agent sources for reporting
        
        Returns:
            Dictionary containing collected agent data
        """
        data = {
            "timestamp": datetime.now().isoformat(),
            "sources": [],
            "auditor_data": {},
            "integration_data": {},
            "workflow_data": {},
            "verification_data": {},
            "errors": []
        }
        
        try:
            # Collect System Auditor data
            try:
                audit_dir = Path(__file__).parent.parent / "langflow_agents" / "audit_results"
                if audit_dir.exists():
                    latest_file = audit_dir / "latest_audit.json"
                    if latest_file.exists():
                        with open(latest_file, 'r') as f:
                            data["auditor_data"] = json.load(f)
                        data["sources"].append("system_auditor")
                    else:
                        # Try to find most recent audit file
                        latest_time = 0
                        latest_audit_file = None
                        
                        for audit_file in audit_dir.glob("audit_*.json"):
                            file_time = os.path.getmtime(audit_file)
                            if file_time > latest_time:
                                latest_time = file_time
                                latest_audit_file = audit_file
                        
                        if latest_audit_file:
                            with open(latest_audit_file, 'r') as f:
                                data["auditor_data"] = json.load(f)
                            data["sources"].append("system_auditor")
            except Exception as e:
                logger.error(f"Error collecting auditor data: {e}")
                data["errors"].append(f"Auditor data collection error: {str(e)}")
            
            # Collect Integration Manager data
            try:
                # Check if integration status file exists
                integration_file = Path(__file__).parent.parent / "agent_status.json"
                if integration_file.exists():
                    with open(integration_file, 'r') as f:
                        status_data = json.load(f)
                        if "integration" in status_data:
                            data["integration_data"] = status_data["integration"]
                            data["sources"].append("integration_manager")
            except Exception as e:
                logger.error(f"Error collecting integration data: {e}")
                data["errors"].append(f"Integration data collection error: {str(e)}")
            
            # Collect Workflow Executor data
            try:
                workflow_dir = Path(__file__).parent / "workflows"
                if workflow_dir.exists():
                    latest_file = None
                    latest_time = 0
                    
                    for workflow_file in workflow_dir.glob("*_results.json"):
                        file_time = os.path.getmtime(workflow_file)
                        if file_time > latest_time:
                            latest_time = file_time
                            latest_file = workflow_file
                    
                    if latest_file:
                        with open(latest_file, 'r') as f:
                            data["workflow_data"] = json.load(f)
                        data["sources"].append("workflow_executor")
            except Exception as e:
                logger.error(f"Error collecting workflow data: {e}")
                data["errors"].append(f"Workflow data collection error: {str(e)}")
            
            # Collect ChatGPT Verification data
            try:
                verification_dir = Path(__file__).parent / "verification_results"
                if verification_dir.exists():
                    # Check for latest overall verification
                    latest_file = verification_dir / "latest_overall_system_verification.json"
                    if latest_file.exists():
                        with open(latest_file, 'r') as f:
                            data["verification_data"] = json.load(f)
                        data["sources"].append("chatgpt_verification")
                    else:
                        # Try to find any latest verification
                        for prefix in ["latest_system_audit", "latest_integration", "latest_workflow"]:
                            latest_file = verification_dir / f"{prefix}_verification.json"
                            if latest_file.exists():
                                with open(latest_file, 'r') as f:
                                    data["verification_data"] = json.load(f)
                                data["sources"].append("chatgpt_verification")
                                break
            except Exception as e:
                logger.error(f"Error collecting verification data: {e}")
                data["errors"].append(f"Verification data collection error: {str(e)}")
            
            # Collect system status data
            try:
                system_status_file = Path(__file__).parent.parent / "system_status.json"
                if system_status_file.exists():
                    with open(system_status_file, 'r') as f:
                        data["system_status"] = json.load(f)
                    data["sources"].append("system_status")
            except Exception as e:
                logger.error(f"Error collecting system status data: {e}")
                data["errors"].append(f"System status collection error: {str(e)}")
            
        except Exception as e:
            logger.error(f"Error collecting agent data: {e}")
            data["errors"].append(f"Data collection error: {str(e)}")
        
        return data
    
    def generate_health_report(self, agent_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Generate a comprehensive system health report
        
        Args:
            agent_data: Pre-collected agent data (if None, will collect fresh data)
            
        Returns:
            Dictionary containing the health report
        """
        if not agent_data:
            agent_data = self.collect_agent_data()
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "type": "health",
            "title": f"NoxSuite System Health Report - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "summary": "",
            "overall_health": "unknown",
            "components": {},
            "issues": [],
            "recommendations": [],
            "data_sources": agent_data["sources"],
            "errors": agent_data["errors"]
        }
        
        try:
            # Process Docker health
            if "system_status" in agent_data:
                docker_status = agent_data["system_status"].get("docker_status", {})
                
                # Docker component health
                docker_health = "healthy"
                docker_issues = []
                
                if "error" in docker_status:
                    docker_health = "error"
                    docker_issues.append(f"Docker error: {docker_status['error']}")
                elif "containers" in docker_status:
                    containers = docker_status["containers"]
                    if containers.get("running", 0) < 1:
                        docker_health = "critical"
                        docker_issues.append("No Docker containers are running")
                    
                    # Check NoxSuite containers
                    nox_containers = docker_status.get("noxsuite_status", {})
                    if not nox_containers.get("all_running", False):
                        docker_health = "warning" if docker_health == "healthy" else docker_health
                        not_running = [name for name, running in nox_containers.items() if not running]
                        docker_issues.append(f"NoxSuite containers not running: {', '.join(not_running)}")
                
                report["components"]["docker"] = {
                    "health": docker_health,
                    "details": {
                        "containers_running": docker_status.get("containers", {}).get("running", 0),
                        "containers_total": docker_status.get("containers", {}).get("total", 0)
                    }
                }
                
                report["issues"].extend(docker_issues)
            
            # Process Langflow health
            langflow_health = "unknown"
            
            if "auditor_data" in agent_data and "langflow" in agent_data["auditor_data"]:
                langflow_data = agent_data["auditor_data"]["langflow"]
                langflow_health = "healthy" if langflow_data.get("health", False) else "error"
                
                if not langflow_data.get("health", False):
                    report["issues"].append("Langflow health check failed")
                
                if langflow_data.get("errors", []):
                    report["issues"].extend([f"Langflow error: {error}" for error in langflow_data["errors"]])
                
                report["components"]["langflow"] = {
                    "health": langflow_health,
                    "details": {
                        "flows_count": langflow_data.get("flows", {}).get("count", 0),
                        "components_count": langflow_data.get("components", {}).get("count", 0)
                    }
                }
            
            # Process MCP Server health
            mcp_health = "unknown"
            
            if "auditor_data" in agent_data and "mcp" in agent_data["auditor_data"]:
                mcp_data = agent_data["auditor_data"]["mcp"]
                mcp_health = "healthy" if mcp_data.get("health", False) else "error"
                
                if not mcp_data.get("health", False):
                    report["issues"].append("MCP Server health check failed")
                
                if mcp_data.get("errors", []):
                    report["issues"].extend([f"MCP Server error: {error}" for error in mcp_data["errors"]])
                
                report["components"]["mcp_server"] = {
                    "health": mcp_health
                }
            
            # Process Copilot Tools health
            copilot_health = "unknown"
            
            if "auditor_data" in agent_data and "copilot" in agent_data["auditor_data"]:
                copilot_data = agent_data["auditor_data"]["copilot"]
                
                tool_usage = copilot_data.get("tool_usage", {})
                usage_percentage = tool_usage.get("usage_percentage", 0)
                
                if usage_percentage > 90:
                    copilot_health = "critical"
                    report["issues"].append(f"Critical Copilot tools usage: {usage_percentage}%")
                elif usage_percentage > 75:
                    copilot_health = "warning"
                    report["issues"].append(f"High Copilot tools usage: {usage_percentage}%")
                else:
                    copilot_health = "healthy"
                
                report["components"]["copilot_tools"] = {
                    "health": copilot_health,
                    "details": {
                        "usage": f"{tool_usage.get('current_count', 0)}/{tool_usage.get('max_limit', 128)} tools ({usage_percentage}%)",
                        "throttling_active": copilot_data.get("constraints", {}).get("throttling_active", False)
                    }
                }
            
            # Process Integration health
            if "integration_data" in agent_data:
                integration_data = agent_data["integration_data"]
                
                integration_health = "healthy"
                
                if not integration_data.get("mcp_langflow_connected", False):
                    integration_health = "warning"
                    report["issues"].append("MCP-Langflow connection issue")
                
                if not integration_data.get("agent_definitions_synced", False):
                    integration_health = "error" if integration_health == "healthy" else integration_health
                    report["issues"].append("Agent definitions not synchronized")
                
                report["components"]["integration"] = {
                    "health": integration_health,
                    "details": {
                        "mcp_connected": integration_data.get("mcp_langflow_connected", False),
                        "agents_synced": integration_data.get("agent_definitions_synced", False),
                        "copilot_integrated": integration_data.get("copilot_integration_active", False)
                    }
                }
            
            # Process Workflow health
            if "workflow_data" in agent_data:
                workflow_data = agent_data["workflow_data"]
                
                workflows_total = workflow_data.get("workflows_total", 0)
                workflows_passed = workflow_data.get("workflows_passed", 0)
                
                if workflows_total == 0:
                    workflow_health = "unknown"
                elif workflows_passed == workflows_total:
                    workflow_health = "healthy"
                elif workflows_passed == 0:
                    workflow_health = "critical"
                    report["issues"].append("All workflows failed")
                else:
                    workflow_health = "warning"
                    report["issues"].append(f"{workflows_total - workflows_passed} of {workflows_total} workflows failed")
                
                report["components"]["workflows"] = {
                    "health": workflow_health,
                    "details": {
                        "passed": workflows_passed,
                        "total": workflows_total
                    }
                }
            
            # Include ChatGPT verification insights
            if "verification_data" in agent_data:
                verification_data = agent_data["verification_data"]
                
                # Include discrepancies as issues
                if "discrepancies" in verification_data:
                    for discrepancy in verification_data["discrepancies"]:
                        if "[CRITICAL]" in discrepancy:
                            report["issues"].append(f"ChatGPT verification critical issue: {discrepancy.replace('[CRITICAL] ', '')}")
                        else:
                            report["issues"].append(f"ChatGPT verification discrepancy: {discrepancy}")
                
                # Include recommendations
                if "recommendations" in verification_data:
                    report["recommendations"].extend(verification_data["recommendations"])
            
            # Determine overall health based on component health
            health_statuses = [component["health"] for component in report["components"].values()]
            
            if "critical" in health_statuses:
                report["overall_health"] = "critical"
            elif "error" in health_statuses:
                report["overall_health"] = "error"
            elif "warning" in health_statuses:
                report["overall_health"] = "warning"
            elif all(status == "healthy" for status in health_statuses):
                report["overall_health"] = "healthy"
            else:
                report["overall_health"] = "unknown"
            
            # Generate overall summary
            issues_count = len(report["issues"])
            recommendations_count = len(report["recommendations"])
            components_count = len(report["components"])
            
            # ADHD-friendly summary with emoji indicators
            health_emoji = {
                "healthy": "✅",
                "warning": "⚠️",
                "error": "❌",
                "critical": "🚨",
                "unknown": "❓"
            }
            
            summary = f"{health_emoji[report['overall_health']]} SYSTEM HEALTH: {report['overall_health'].upper()}\n"
            summary += f"• Components checked: {components_count}\n"
            summary += f"• Issues detected: {issues_count}\n"
            summary += f"• Recommendations: {recommendations_count}\n\n"
            
            if issues_count > 0:
                summary += "TOP ISSUES:\n"
                for i, issue in enumerate(report["issues"][:3]):
                    summary += f"{i+1}. {issue}\n"
                if issues_count > 3:
                    summary += f"(+{issues_count - 3} more issues)\n"
            
            report["summary"] = summary
            
            # Save report
            self._save_health_report(report)
            
            # Update history
            self.report_history.append({
                "timestamp": report["timestamp"],
                "type": report["type"],
                "title": report["title"],
                "overall_health": report["overall_health"],
                "issues_count": issues_count,
                "file": f"health/health_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            })
            
            # Trim history if needed
            if len(self.report_history) > self.max_report_history:
                self.report_history = self.report_history[-self.max_report_history:]
            
            self._save_report_history()
            self.last_report = report
            
        except Exception as e:
            logger.error(f"Error generating health report: {e}")
            report["errors"].append(f"Report generation error: {str(e)}")
        
        return report
    
    def generate_alert_report(self, issues: List[str], severity: str = "warning") -> Dict[str, Any]:
        """
        Generate an alert report for critical issues
        
        Args:
            issues: List of issues to include in the alert
            severity: Alert severity (warning, error, critical)
            
        Returns:
            Dictionary containing the alert report
        """
        report = {
            "timestamp": datetime.now().isoformat(),
            "type": "alert",
            "title": f"NoxSuite Alert - {severity.upper()} - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "severity": severity,
            "issues": issues,
            "summary": ""
        }
        
        try:
            # Generate ADHD-friendly summary
            severity_emoji = {
                "warning": "⚠️",
                "error": "❌",
                "critical": "🚨"
            }
            
            summary = f"{severity_emoji.get(severity, '⚠️')} {severity.upper()} ALERT - {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
            
            for i, issue in enumerate(issues):
                summary += f"{i+1}. {issue}\n"
            
            report["summary"] = summary
            
            # Save report
            self._save_alert_report(report)
            
            # Update history
            self.report_history.append({
                "timestamp": report["timestamp"],
                "type": report["type"],
                "title": report["title"],
                "severity": severity,
                "issues_count": len(issues),
                "file": f"alerts/alert_{severity}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            })
            
            # Trim history if needed
            if len(self.report_history) > self.max_report_history:
                self.report_history = self.report_history[-self.max_report_history:]
            
            self._save_report_history()
            self.last_report = report
            
        except Exception as e:
            logger.error(f"Error generating alert report: {e}")
            report["errors"] = [f"Report generation error: {str(e)}"]
        
        return report
    
    def generate_daily_summary_report(self) -> Dict[str, Any]:
        """
        Generate a daily summary report of system status
        
        Returns:
            Dictionary containing the daily summary report
        """
        agent_data = self.collect_agent_data()
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "type": "daily",
            "title": f"NoxSuite Daily Summary - {datetime.now().strftime('%Y-%m-%d')}",
            "summary": "",
            "system_health": "unknown",
            "components_status": {},
            "issues_24h": [],
            "resolved_issues": [],
            "ongoing_issues": [],
            "data_sources": agent_data["sources"]
        }
        
        try:
            # First collect health information
            health_report = self.generate_health_report(agent_data)
            report["system_health"] = health_report["overall_health"]
            report["components_status"] = health_report["components"]
            
            # Collect issues from the past 24 hours
            past_24h_alerts = []
            yesterday = datetime.now().timestamp() - (24 * 3600)
            
            for report_entry in self.report_history:
                if report_entry["type"] == "alert":
                    report_time = datetime.fromisoformat(report_entry["timestamp"]).timestamp()
                    if report_time >= yesterday:
                        # Get full alert report
                        alert_file = os.path.join(self.report_dir, report_entry["file"])
                        if os.path.exists(alert_file):
                            with open(alert_file, 'r') as f:
                                alert_data = json.load(f)
                                past_24h_alerts.append(alert_data)
            
            # Extract issues from past alerts
            for alert in past_24h_alerts:
                report["issues_24h"].extend(alert.get("issues", []))
            
            # Check for resolved issues (issues from previous reports that are no longer present)
            current_issues = set(health_report["issues"])
            previous_health_reports = [entry for entry in self.report_history 
                                     if entry["type"] == "health" and 
                                     entry != self.report_history[-1]]
            
            if previous_health_reports:
                previous_report_file = os.path.join(self.report_dir, previous_health_reports[-1]["file"])
                if os.path.exists(previous_report_file):
                    with open(previous_report_file, 'r') as f:
                        previous_report = json.load(f)
                        previous_issues = set(previous_report.get("issues", []))
                        
                        # Issues that were in previous report but not in current one are resolved
                        resolved = previous_issues - current_issues
                        report["resolved_issues"] = list(resolved)
                        
                        # Issues that are in both reports are ongoing
                        ongoing = previous_issues.intersection(current_issues)
                        report["ongoing_issues"] = list(ongoing)
            
            # Generate ADHD-friendly summary
            health_emoji = {
                "healthy": "✅",
                "warning": "⚠️",
                "error": "❌",
                "critical": "🚨",
                "unknown": "❓"
            }
            
            summary = f"# NoxSuite Daily Summary - {datetime.now().strftime('%Y-%m-%d')}\n\n"
            summary += f"## Current Status: {health_emoji[report['system_health']]} {report['system_health'].upper()}\n\n"
            
            summary += "### Component Status\n"
            for component, status in report["components_status"].items():
                summary += f"- {component.replace('_', ' ').title()}: {health_emoji[status['health']]} {status['health'].upper()}\n"
            
            summary += "\n### Issue Summary\n"
            summary += f"- New issues in past 24h: {len(report['issues_24h'])}\n"
            summary += f"- Resolved issues: {len(report['resolved_issues'])}\n"
            summary += f"- Ongoing issues: {len(report['ongoing_issues'])}\n"
            
            if report["issues_24h"]:
                summary += "\n### Issues from Past 24 Hours\n"
                for i, issue in enumerate(report["issues_24h"]):
                    summary += f"{i+1}. {issue}\n"
            
            if report["resolved_issues"]:
                summary += "\n### Recently Resolved Issues\n"
                for i, issue in enumerate(report["resolved_issues"]):
                    summary += f"{i+1}. {issue}\n"
            
            if report["ongoing_issues"]:
                summary += "\n### Ongoing Issues\n"
                for i, issue in enumerate(report["ongoing_issues"]):
                    summary += f"{i+1}. {issue}\n"
            
            report["summary"] = summary
            
            # Save report
            self._save_daily_report(report)
            
            # Update history
            self.report_history.append({
                "timestamp": report["timestamp"],
                "type": report["type"],
                "title": report["title"],
                "system_health": report["system_health"],
                "issues_count": len(report["issues_24h"]) + len(report["ongoing_issues"]),
                "file": f"daily/daily_report_{datetime.now().strftime('%Y%m%d')}.json"
            })
            
            # Trim history if needed
            if len(self.report_history) > self.max_report_history:
                self.report_history = self.report_history[-self.max_report_history:]
            
            self._save_report_history()
            self.last_report = report
            
        except Exception as e:
            logger.error(f"Error generating daily summary report: {e}")
            report["errors"] = [f"Report generation error: {str(e)}"]
        
        return report
    
    def generate_mission_status_report(self) -> Dict[str, Any]:
        """
        Generate a mission status report to check if success criteria are met
        
        Returns:
            Dictionary containing the mission status report
        """
        agent_data = self.collect_agent_data()
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "type": "mission",
            "title": "NoxSuite Mission Status Report",
            "summary": "",
            "success_criteria": {
                "mcp_server_stable": False,
                "langflow_workflows_successful": False,
                "docker_container_connectivity": False,
                "copilot_agent_under_limit": False,
                "chatgpt_validation_confirms": False
            },
            "mission_accomplished": False,
            "missing_criteria": [],
            "data_sources": agent_data["sources"]
        }
        
        try:
            # Check MCP Server stability
            if "auditor_data" in agent_data and "mcp" in agent_data["auditor_data"]:
                report["success_criteria"]["mcp_server_stable"] = agent_data["auditor_data"]["mcp"].get("health", False)
                
                if not report["success_criteria"]["mcp_server_stable"]:
                    report["missing_criteria"].append("MCP Server stability not achieved")
            else:
                report["missing_criteria"].append("MCP Server status unknown")
            
            # Check Langflow workflows
            if "workflow_data" in agent_data:
                workflows_total = agent_data["workflow_data"].get("workflows_total", 0)
                workflows_passed = agent_data["workflow_data"].get("workflows_passed", 0)
                
                report["success_criteria"]["langflow_workflows_successful"] = (
                    workflows_total > 0 and workflows_passed == workflows_total
                )
                
                if not report["success_criteria"]["langflow_workflows_successful"]:
                    report["missing_criteria"].append(
                        f"Langflow workflows not all successful ({workflows_passed}/{workflows_total})"
                    )
            else:
                report["missing_criteria"].append("Langflow workflow status unknown")
            
            # Check Docker container connectivity
            if "auditor_data" in agent_data and "docker" in agent_data["auditor_data"]:
                docker_data = agent_data["auditor_data"]["docker"]
                
                nox_services = docker_data.get("containers", {}).get("nox_services", {})
                report["success_criteria"]["docker_container_connectivity"] = (
                    nox_services.get("noxsuite-langflow", {}).get("found", False) and
                    nox_services.get("noxsuite-postgres", {}).get("found", False) and
                    nox_services.get("noxsuite-redis", {}).get("found", False)
                )
                
                if not report["success_criteria"]["docker_container_connectivity"]:
                    report["missing_criteria"].append("Docker container connectivity not verified")
            else:
                report["missing_criteria"].append("Docker container status unknown")
            
            # Check Copilot agent under 128 tool limit
            if "auditor_data" in agent_data and "copilot" in agent_data["auditor_data"]:
                copilot_data = agent_data["auditor_data"]["copilot"]
                usage_percentage = copilot_data.get("tool_usage", {}).get("usage_percentage", 100)
                
                report["success_criteria"]["copilot_agent_under_limit"] = usage_percentage < 80
                
                if not report["success_criteria"]["copilot_agent_under_limit"]:
                    report["missing_criteria"].append(
                        f"Copilot agent approaching tool limit ({usage_percentage}%)"
                    )
            else:
                report["missing_criteria"].append("Copilot agent status unknown")
            
            # Check ChatGPT validation
            if "verification_data" in agent_data:
                verification_data = agent_data["verification_data"]
                
                # Check if there are critical discrepancies
                critical_issues = any("[CRITICAL]" in d for d in verification_data.get("discrepancies", []))
                
                report["success_criteria"]["chatgpt_validation_confirms"] = (
                    verification_data.get("verification_success", False) and
                    not critical_issues
                )
                
                if not report["success_criteria"]["chatgpt_validation_confirms"]:
                    report["missing_criteria"].append("ChatGPT external validation not confirming system health")
            else:
                report["missing_criteria"].append("ChatGPT validation status unknown")
            
            # Check if mission is accomplished
            report["mission_accomplished"] = all(report["success_criteria"].values())
            
            # Generate ADHD-friendly summary
            if report["mission_accomplished"]:
                summary = "🎯 MISSION ACCOMPLISHED!\n\n"
                summary += "All success criteria have been met:\n"
                for criterion, status in report["success_criteria"].items():
                    summary += f"✅ {criterion.replace('_', ' ').title()}: Achieved\n"
            else:
                summary = "🔄 MISSION IN PROGRESS\n\n"
                summary += "The following criteria have been met:\n"
                for criterion, status in report["success_criteria"].items():
                    if status:
                        summary += f"✅ {criterion.replace('_', ' ').title()}: Achieved\n"
                
                summary += "\nThe following criteria still need to be addressed:\n"
                for criterion in report["missing_criteria"]:
                    summary += f"❌ {criterion}\n"
            
            report["summary"] = summary
            
            # Save report
            self._save_summary_report(report)
            
            # Update history
            self.report_history.append({
                "timestamp": report["timestamp"],
                "type": report["type"],
                "title": report["title"],
                "mission_accomplished": report["mission_accomplished"],
                "missing_criteria": len(report["missing_criteria"]),
                "file": f"summary/mission_status_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            })
            
            # If mission accomplished, create special file
            if report["mission_accomplished"]:
                mission_file = os.path.join(Path(__file__).parent.parent, "MISSION_ACCOMPLISHED.txt")
                with open(mission_file, 'w') as f:
                    f.write(summary)
                    f.write("\n\nMission completed at: " + datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            
            # Trim history if needed
            if len(self.report_history) > self.max_report_history:
                self.report_history = self.report_history[-self.max_report_history:]
            
            self._save_report_history()
            self.last_report = report
            
        except Exception as e:
            logger.error(f"Error generating mission status report: {e}")
            report["errors"] = [f"Report generation error: {str(e)}"]
        
        return report
    
    def _save_health_report(self, report: Dict[str, Any]) -> None:
        """
        Save health report to file
        
        Args:
            report: Health report to save
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_file = os.path.join(self.health_report_dir, f"health_report_{timestamp}.json")
            
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2)
            
            # Also save as latest health report
            latest_file = os.path.join(self.health_report_dir, "latest_health_report.json")
            with open(latest_file, 'w') as f:
                json.dump(report, f, indent=2)
            
            # Generate markdown version
            md_file = os.path.join(self.health_report_dir, f"health_report_{timestamp}.md")
            with open(md_file, 'w') as f:
                f.write(f"# {report['title']}\n\n")
                f.write(report['summary'])
                
                f.write("\n## Component Status\n\n")
                for component, status in report["components"].items():
                    f.write(f"### {component.replace('_', ' ').title()}: {status['health'].upper()}\n")
                    if "details" in status:
                        for key, value in status["details"].items():
                            f.write(f"- {key.replace('_', ' ').title()}: {value}\n")
                    f.write("\n")
                
                if report["issues"]:
                    f.write("\n## Issues\n\n")
                    for issue in report["issues"]:
                        f.write(f"- {issue}\n")
                
                if report["recommendations"]:
                    f.write("\n## Recommendations\n\n")
                    for rec in report["recommendations"]:
                        f.write(f"- {rec}\n")
            
            logger.info(f"Health report saved to {report_file} and {md_file}")
            
        except Exception as e:
            logger.error(f"Error saving health report: {e}")
    
    def _save_alert_report(self, report: Dict[str, Any]) -> None:
        """
        Save alert report to file
        
        Args:
            report: Alert report to save
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_file = os.path.join(self.alert_report_dir, f"alert_{report['severity']}_{timestamp}.json")
            
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2)
            
            # Also save as latest alert report
            latest_file = os.path.join(self.alert_report_dir, "latest_alert.json")
            with open(latest_file, 'w') as f:
                json.dump(report, f, indent=2)
            
            # Generate markdown version
            md_file = os.path.join(self.alert_report_dir, f"alert_{report['severity']}_{timestamp}.md")
            with open(md_file, 'w') as f:
                f.write(f"# {report['title']}\n\n")
                f.write(report['summary'])
            
            logger.info(f"Alert report saved to {report_file} and {md_file}")
            
        except Exception as e:
            logger.error(f"Error saving alert report: {e}")
    
    def _save_daily_report(self, report: Dict[str, Any]) -> None:
        """
        Save daily report to file
        
        Args:
            report: Daily report to save
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d")
            report_file = os.path.join(self.daily_report_dir, f"daily_report_{timestamp}.json")
            
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2)
            
            # Also save as latest daily report
            latest_file = os.path.join(self.daily_report_dir, "latest_daily_report.json")
            with open(latest_file, 'w') as f:
                json.dump(report, f, indent=2)
            
            # Generate markdown version
            md_file = os.path.join(self.daily_report_dir, f"daily_report_{timestamp}.md")
            with open(md_file, 'w') as f:
                f.write(report['summary'])
            
            logger.info(f"Daily report saved to {report_file} and {md_file}")
            
        except Exception as e:
            logger.error(f"Error saving daily report: {e}")
    
    def _save_summary_report(self, report: Dict[str, Any]) -> None:
        """
        Save summary report to file
        
        Args:
            report: Summary report to save
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_file = os.path.join(self.summary_report_dir, f"{report['type']}_status_{timestamp}.json")
            
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2)
            
            # Also save as latest summary report
            latest_file = os.path.join(self.summary_report_dir, f"latest_{report['type']}_report.json")
            with open(latest_file, 'w') as f:
                json.dump(report, f, indent=2)
            
            # Generate markdown version
            md_file = os.path.join(self.summary_report_dir, f"{report['type']}_status_{timestamp}.md")
            with open(md_file, 'w') as f:
                f.write(f"# {report['title']}\n\n")
                f.write(report['summary'])
            
            logger.info(f"{report['type'].capitalize()} report saved to {report_file} and {md_file}")
            
        except Exception as e:
            logger.error(f"Error saving {report['type']} report: {e}")
    
    def run_continuous_reporting(self, health_interval: int = 900, daily_interval: int = 86400, run_once: bool = False) -> None:
        """
        Run continuous reporting at specified intervals
        
        Args:
            health_interval: Time between health reports in seconds (default: 15 minutes)
            daily_interval: Time between daily reports in seconds (default: 24 hours)
            run_once: If True, run each report once and return
        """
        logger.info(f"Starting {'single' if run_once else 'continuous'} reporting")
        
        try:
            # Track last report times
            last_health_time = 0
            last_daily_time = 0
            
            # Always run mission status report first
            self.generate_mission_status_report()
            
            # If run once, generate all reports and exit
            if run_once:
                self.generate_health_report()
                self.generate_daily_summary_report()
                logger.info("Single reporting run completed")
                return
            
            # Continuous reporting loop
            while True:
                current_time = time.time()
                
                # Check if it's time for a health report
                if current_time - last_health_time >= health_interval:
                    self.generate_health_report()
                    last_health_time = current_time
                    
                    # Also check mission status after each health report
                    mission_report = self.generate_mission_status_report()
                    if mission_report["mission_accomplished"]:
                        logger.info("🎯 MISSION ACCOMPLISHED! All success criteria met.")
                
                # Check if it's time for a daily report
                if current_time - last_daily_time >= daily_interval:
                    self.generate_daily_summary_report()
                    last_daily_time = current_time
                
                # Sleep for a shorter interval to be responsive
                time.sleep(min(60, health_interval / 10))
                
        except KeyboardInterrupt:
            logger.info("Reporting process interrupted by user")
        except Exception as e:
            logger.error(f"Error in continuous reporting loop: {e}")
    
    def get_reporting_status(self) -> Dict[str, Any]:
        """
        Get status of the reporting agent
        
        Returns:
            Dictionary containing reporting status
        """
        status = {
            "timestamp": datetime.now().isoformat(),
            "reports_generated": len(self.report_history),
            "latest_report": None,
            "report_types": {
                "health": sum(1 for r in self.report_history if r["type"] == "health"),
                "alert": sum(1 for r in self.report_history if r["type"] == "alert"),
                "daily": sum(1 for r in self.report_history if r["type"] == "daily"),
                "mission": sum(1 for r in self.report_history if r["type"] == "mission")
            },
            "mission_accomplished": False
        }
        
        # Get latest report info
        if self.last_report:
            status["latest_report"] = {
                "timestamp": self.last_report.get("timestamp", "unknown"),
                "type": self.last_report.get("type", "unknown"),
                "title": self.last_report.get("title", "unknown")
            }
            
            # Check if mission accomplished
            if self.last_report.get("type") == "mission":
                status["mission_accomplished"] = self.last_report.get("mission_accomplished", False)
        
        # Get most recent mission status
        mission_reports = [r for r in self.report_history if r["type"] == "mission"]
        if mission_reports:
            most_recent = mission_reports[-1]
            status["mission_accomplished"] = most_recent.get("mission_accomplished", False)
        
        return status


# For importing as module
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Diagnostic & Reporting Agent")
    parser.add_argument("--health", action="store_true", help="Generate health report")
    parser.add_argument("--daily", action="store_true", help="Generate daily summary report")
    parser.add_argument("--mission", action="store_true", help="Generate mission status report")
    parser.add_argument("--alert", action="store_true", help="Generate alert report")
    parser.add_argument("--alert-text", type=str, help="Text for alert report")
    parser.add_argument("--severity", type=str, choices=["warning", "error", "critical"], default="warning", help="Alert severity")
    parser.add_argument("--continuous", action="store_true", help="Run continuous reporting")
    args = parser.parse_args()
    
    reporter = DiagnosticReportingAgent()
    
    if args.health:
        print("Generating health report...")
        report = reporter.generate_health_report()
        print(f"Health report generated - Overall health: {report['overall_health']}")
        print(f"Issues: {len(report['issues'])}, Recommendations: {len(report['recommendations'])}")
    
    if args.daily:
        print("Generating daily summary report...")
        report = reporter.generate_daily_summary_report()
        print(f"Daily report generated - System health: {report['system_health']}")
        print(f"Issues in past 24h: {len(report['issues_24h'])}, Resolved: {len(report['resolved_issues'])}")
    
    if args.mission:
        print("Generating mission status report...")
        report = reporter.generate_mission_status_report()
        if report["mission_accomplished"]:
            print("🎯 MISSION ACCOMPLISHED! All success criteria met.")
        else:
            print(f"Mission in progress - {len(report['missing_criteria'])} criteria remaining")
            for criterion in report["missing_criteria"]:
                print(f"  - {criterion}")
    
    if args.alert and args.alert_text:
        print(f"Generating {args.severity} alert...")
        issues = [issue.strip() for issue in args.alert_text.split(";")]
        report = reporter.generate_alert_report(issues, args.severity)
        print(f"Alert generated with {len(issues)} issues")
    
    if args.continuous:
        print("Starting continuous reporting...")
        print("Press Ctrl+C to stop")
        reporter.run_continuous_reporting()
    
    if not any([args.health, args.daily, args.mission, args.alert, args.continuous]):
        print("No action specified. Use --health, --daily, --mission, --alert, or --continuous")
        print("For alerts, use --alert-text to provide the alert text (separate multiple issues with semicolons)")
        print("Example: --alert --alert-text 'Docker container crashed;Database connection failed'")
        parser.print_help()
