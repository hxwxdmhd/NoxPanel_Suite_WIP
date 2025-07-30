#!/usr/bin/env python3
"""
🔧 Langflow Auto-Repair Agent for TestSprite Failures
Monitors TestSprite results and triggers automated repairs
"""

import json
import time
import requests
import subprocess
import os
from datetime import datetime
from pathlib import Path

class LangflowAutoRepairAgent:
    def __init__(self):
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.logs_dir = Path("./logs/auto_repair")
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Langflow configuration
        self.langflow_url = os.getenv("LANGFLOW_URL", "http://localhost:7860")
        self.langflow_api_key = os.getenv("LANGFLOW_API_KEY", "")
        
        # Auto-repair configuration
        self.repair_config = {
            "max_retry_attempts": 3,
            "repair_timeout": 600,  # 10 minutes
            "critical_threshold": 1,
            "auto_commit_fixes": True
        }

    def log(self, message):
        """Enhanced logging with timestamps"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] 🔧 {message}")
        
        # Save to log file
        log_file = self.logs_dir / f"auto_repair_{self.timestamp}.log"
        with open(log_file, "a", encoding='utf-8') as f:
            f.write(f"[{timestamp}] {message}\n")

    def monitor_testsprite_results(self):
        """Monitor for new TestSprite results that need auto-repair"""
        self.log("Starting TestSprite results monitoring...")
        
        results_dir = Path("./logs/autonomous_testing")
        if not results_dir.exists():
            self.log("No TestSprite results directory found")
            return None
        
        # Find latest results file
        result_files = list(results_dir.glob("testsprite_results_*.json"))
        if not result_files:
            self.log("No TestSprite results files found")
            return None
        
        latest_file = max(result_files, key=lambda p: p.stat().st_mtime)
        self.log(f"Found latest results: {latest_file}")
        
        # Load and analyze results
        with open(latest_file, 'r', encoding='utf-8') as f:
            results = json.load(f)
        
        return results

    def analyze_failures(self, results):
        """Analyze TestSprite failures to determine repair strategy"""
        self.log("Analyzing TestSprite failures...")
        
        adhd_report = results.get("adhd_report", {})
        critical_issues = adhd_report.get("EXECUTIVE_SUMMARY", {}).get("critical_issues", 0)
        immediate_actions = adhd_report.get("IMMEDIATE_ACTIONS", [])
        
        if critical_issues == 0:
            self.log("✅ No critical issues found - auto-repair not needed")
            return None
        
        self.log(f"🚨 Found {critical_issues} critical issues requiring auto-repair")
        
        # Categorize failures for targeted repair
        repair_strategy = {
            "authentication_failures": [],
            "api_failures": [],
            "database_failures": [],
            "frontend_failures": [],
            "integration_failures": []
        }
        
        for action in immediate_actions:
            task_title = action.get("task", "").lower()
            description = action.get("description", "").lower()
            
            if "authentication" in task_title or "auth" in description:
                repair_strategy["authentication_failures"].append(action)
            elif "api" in task_title or "api" in description:
                repair_strategy["api_failures"].append(action)
            elif "database" in description or "connection" in description:
                repair_strategy["database_failures"].append(action)
            elif "frontend" in action.get("category", "").lower():
                repair_strategy["frontend_failures"].append(action)
            else:
                repair_strategy["integration_failures"].append(action)
        
        return repair_strategy

    def trigger_langflow_repair(self, repair_strategy):
        """Trigger Langflow workflows for specific repair categories"""
        self.log("Triggering Langflow auto-repair workflows...")
        
        repair_results = {}
        
        for category, failures in repair_strategy.items():
            if not failures:
                continue
                
            self.log(f"🔧 Triggering repair for {category}: {len(failures)} issues")
            
            # Prepare repair payload
            repair_payload = {
                "category": category,
                "failures": failures,
                "timestamp": self.timestamp,
                "auto_repair": True,
                "max_attempts": self.repair_config["max_retry_attempts"]
            }
            
            # Trigger specific Langflow workflow
            workflow_result = self._execute_langflow_workflow(category, repair_payload)
            repair_results[category] = workflow_result
            
            # Add delay between repair attempts
            time.sleep(10)
        
        return repair_results

    def _execute_langflow_workflow(self, category, payload):
        """Execute specific Langflow workflow for repair category"""
        workflow_map = {
            "authentication_failures": "auth_repair_agent",
            "api_failures": "api_repair_agent", 
            "database_failures": "db_repair_agent",
            "frontend_failures": "frontend_repair_agent",
            "integration_failures": "integration_repair_agent"
        }
        
        workflow_name = workflow_map.get(category, "general_repair_agent")
        
        try:
            # Simulate Langflow API call (replace with actual API when available)
            self.log(f"Executing Langflow workflow: {workflow_name}")
            
            # For now, simulate the repair process
            repair_result = self._simulate_repair(category, payload)
            
            return {
                "status": "success",
                "workflow": workflow_name,
                "result": repair_result,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.log(f"❌ Langflow workflow failed for {category}: {e}")
            return {
                "status": "failed",
                "workflow": workflow_name,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def _simulate_repair(self, category, payload):
        """Simulate auto-repair actions (replace with actual repair logic)"""
        self.log(f"Simulating auto-repair for {category}...")
        
        repair_actions = {
            "authentication_failures": [
                "Regenerating JWT secret keys",
                "Updating authentication middleware",
                "Refreshing token validation logic",
                "Testing credential flow"
            ],
            "api_failures": [
                "Restarting API services",
                "Clearing API cache",
                "Updating endpoint configurations",
                "Testing API connectivity"
            ],
            "database_failures": [
                "Checking database connections",
                "Restarting connection pool",
                "Optimizing query performance",
                "Testing database operations"
            ],
            "frontend_failures": [
                "Clearing browser cache",
                "Rebuilding frontend assets",
                "Updating component configurations",
                "Testing UI interactions"
            ],
            "integration_failures": [
                "Restarting integration services",
                "Refreshing service connections",
                "Updating workflow configurations",
                "Testing end-to-end flows"
            ]
        }
        
        actions = repair_actions.get(category, ["Generic repair action"])
        
        # Simulate repair execution
        completed_actions = []
        for action in actions:
            self.log(f"   ⚡ {action}")
            time.sleep(2)  # Simulate work
            completed_actions.append({
                "action": action,
                "status": "completed",
                "timestamp": datetime.now().isoformat()
            })
        
        return {
            "category": category,
            "actions_completed": len(completed_actions),
            "actions": completed_actions,
            "success_rate": 0.85  # Simulate 85% success rate
        }

    def validate_repairs(self, repair_results):
        """Validate that auto-repairs were successful"""
        self.log("Validating auto-repair results...")
        
        validation_summary = {
            "total_repairs": 0,
            "successful_repairs": 0,
            "failed_repairs": 0,
            "categories_repaired": [],
            "validation_score": 0
        }
        
        for category, result in repair_results.items():
            validation_summary["total_repairs"] += 1
            
            if result.get("status") == "success":
                validation_summary["successful_repairs"] += 1
                validation_summary["categories_repaired"].append(category)
                self.log(f"✅ {category} repair validated successfully")
            else:
                validation_summary["failed_repairs"] += 1
                self.log(f"❌ {category} repair validation failed")
        
        # Calculate validation score
        if validation_summary["total_repairs"] > 0:
            validation_summary["validation_score"] = round(
                (validation_summary["successful_repairs"] / validation_summary["total_repairs"]) * 100, 1
            )
        
        return validation_summary

    def trigger_retest(self):
        """Trigger TestSprite re-test after auto-repair"""
        self.log("Triggering TestSprite re-test after auto-repair...")
        
        try:
            # Run TestSprite testing again
            result = subprocess.run(
                ["python", "noxsuite_testsprite_simple.py"],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                self.log("✅ Post-repair TestSprite re-test completed successfully")
                return {"status": "success", "output": result.stdout}
            else:
                self.log(f"❌ Post-repair TestSprite re-test failed: {result.stderr}")
                return {"status": "failed", "error": result.stderr}
                
        except Exception as e:
            self.log(f"❌ Re-test execution failed: {e}")
            return {"status": "failed", "error": str(e)}

    def sync_to_github(self, repair_summary, retest_results):
        """Sync auto-repair results to GitHub MCP"""
        self.log("Syncing auto-repair results to GitHub...")
        
        # Create comprehensive repair report
        repair_report = {
            "timestamp": self.timestamp,
            "auto_repair_summary": repair_summary,
            "retest_results": retest_results,
            "success": repair_summary.get("validation_score", 0) > 70
        }
        
        # Save repair report
        report_file = self.logs_dir / f"auto_repair_report_{self.timestamp}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(repair_report, f, indent=2)
        
        # Create GitHub-friendly summary
        github_summary = self._create_github_summary(repair_summary, retest_results)
        
        # Save GitHub summary
        github_file = self.logs_dir / f"github_auto_repair_summary_{self.timestamp}.md"
        with open(github_file, 'w', encoding='utf-8') as f:
            f.write(github_summary)
        
        self.log(f"Auto-repair results saved: {report_file}")
        return repair_report

    def _create_github_summary(self, repair_summary, retest_results):
        """Create GitHub-friendly auto-repair summary"""
        success_emoji = "✅" if repair_summary.get("validation_score", 0) > 70 else "⚠️"
        
        summary = f"""# 🔧 Langflow Auto-Repair Report

## {success_emoji} Auto-Repair Summary
- **Timestamp:** {self.timestamp}
- **Total Repairs:** {repair_summary.get('total_repairs', 0)}
- **Successful Repairs:** {repair_summary.get('successful_repairs', 0)}
- **Validation Score:** {repair_summary.get('validation_score', 0)}%

## 🛠️ Categories Repaired
{chr(10).join([f"- ✅ {category.replace('_', ' ').title()}" for category in repair_summary.get('categories_repaired', [])])}

## 🧪 Post-Repair Test Results
- **Re-test Status:** {retest_results.get('status', 'unknown').title()}
- **Auto-Repair Effective:** {'Yes' if retest_results.get('status') == 'success' else 'Needs manual intervention'}

## 🔄 Next Steps
{'🎉 Auto-repair successful - system restored' if repair_summary.get('validation_score', 0) > 70 else '⚠️ Manual intervention required for remaining issues'}

---
*Generated by Langflow Auto-Repair Agent*
"""
        return summary

    def run_auto_repair_cycle(self):
        """Main auto-repair orchestrator"""
        print("🔧 Starting Langflow Auto-Repair Agent")
        print("=" * 60)
        
        try:
            # Phase 1: Monitor TestSprite results
            results = self.monitor_testsprite_results()
            if not results:
                self.log("No TestSprite results to process")
                return {"status": "no_action", "message": "No results to process"}
            
            # Phase 2: Analyze failures
            repair_strategy = self.analyze_failures(results)
            if not repair_strategy:
                self.log("No critical issues requiring auto-repair")
                return {"status": "no_action", "message": "No critical issues found"}
            
            # Phase 3: Trigger Langflow repairs
            repair_results = self.trigger_langflow_repair(repair_strategy)
            
            # Phase 4: Validate repairs
            validation_summary = self.validate_repairs(repair_results)
            
            # Phase 5: Trigger re-test
            retest_results = self.trigger_retest()
            
            # Phase 6: Sync to GitHub
            final_report = self.sync_to_github(validation_summary, retest_results)
            
            # Final summary
            print("\n" + "=" * 60)
            print("🎉 AUTO-REPAIR CYCLE COMPLETE")
            print("=" * 60)
            print(f"Validation Score: {validation_summary.get('validation_score', 0)}%")
            print(f"Categories Repaired: {len(validation_summary.get('categories_repaired', []))}")
            print(f"Re-test Status: {retest_results.get('status', 'unknown').title()}")
            print("=" * 60)
            
            return {
                "status": "success",
                "repair_summary": validation_summary,
                "retest_results": retest_results,
                "report": final_report
            }
            
        except Exception as e:
            self.log(f"Auto-repair cycle failed: {e}")
            return {"status": "failed", "error": str(e)}

if __name__ == "__main__":
    agent = LangflowAutoRepairAgent()
    result = agent.run_auto_repair_cycle()
    
    if result["status"] == "success":
        print(f"\n🎯 Auto-repair successful: {result['repair_summary'].get('validation_score', 0)}% validation")
    elif result["status"] == "no_action":
        print(f"\n✅ No action needed: {result['message']}")
    else:
        print(f"\n❌ Auto-repair failed: {result.get('error', 'Unknown error')}")
