#!/usr/bin/env python3
"""
📡 GitHub MCP Integration for TestSprite Results
Syncs TestSprite results and auto-repair status to GitHub MCP
"""

import json
import os
import requests
from datetime import datetime
from pathlib import Path
import subprocess

class GitHubMCPSync:
    def __init__(self):
        self.github_token = os.getenv("GITHUB_TOKEN")
        self.repo_owner = os.getenv("GITHUB_REPOSITORY_OWNER", "hxwxdmhd")
        self.repo_name = os.getenv("GITHUB_REPOSITORY_NAME", "NoxPanel_Suite_WIP")
        self.github_api_base = "https://api.github.com"
        
        # MCP sync configuration
        self.sync_config = {
            "auto_commit": True,
            "branch_name": "testsprite-automation",
            "commit_prefix": "🧪 TestSprite:",
            "issue_labels": ["testsprite", "automated-testing", "auto-repair"]
        }

    def log(self, message):
        """Simple logging"""
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 📡 {message}")

    def collect_testsprite_data(self):
        """Collect all TestSprite-related data for GitHub sync"""
        self.log("Collecting TestSprite data for GitHub sync...")
        
        data = {
            "timestamp": datetime.now().isoformat(),
            "testsprite_results": None,
            "auto_repair_results": None,
            "system_health": {},
            "sync_metadata": {}
        }
        
        # Collect TestSprite results
        results_dir = Path("./logs/autonomous_testing")
        if results_dir.exists():
            result_files = list(results_dir.glob("testsprite_results_*.json"))
            if result_files:
                latest_file = max(result_files, key=lambda p: p.stat().st_mtime)
                with open(latest_file, 'r', encoding='utf-8') as f:
                    data["testsprite_results"] = json.load(f)
                self.log(f"Loaded TestSprite results: {latest_file}")
        
        # Collect auto-repair results
        repair_dir = Path("./logs/auto_repair")
        if repair_dir.exists():
            repair_files = list(repair_dir.glob("auto_repair_report_*.json"))
            if repair_files:
                latest_repair = max(repair_files, key=lambda p: p.stat().st_mtime)
                with open(latest_repair, 'r', encoding='utf-8') as f:
                    data["auto_repair_results"] = json.load(f)
                self.log(f"Loaded auto-repair results: {latest_repair}")
            else:
                self.log("No auto-repair results found")
        else:
            self.log("Auto-repair directory not found")
        
        # Collect system health
        data["system_health"] = self._get_system_health_summary(data)
        
        return data

    def _get_system_health_summary(self, data):
        """Generate system health summary"""
        health = {
            "overall_status": "unknown",
            "pass_rate": 0,
            "critical_issues": 0,
            "auto_repair_effective": False,
            "last_test_timestamp": None
        }
        
        if data["testsprite_results"]:
            tr = data["testsprite_results"]
            summary = tr.get("summary", {})
            adhd_report = tr.get("adhd_report", {})
            
            health["pass_rate"] = summary.get("pass_rate", 0)
            health["critical_issues"] = adhd_report.get("EXECUTIVE_SUMMARY", {}).get("critical_issues", 0)
            health["last_test_timestamp"] = tr.get("metadata", {}).get("timestamp")
            
            # Determine overall status
            if health["pass_rate"] >= 95:
                health["overall_status"] = "excellent"
            elif health["pass_rate"] >= 85:
                health["overall_status"] = "good"
            elif health["pass_rate"] >= 70:
                health["overall_status"] = "needs_attention"
            else:
                health["overall_status"] = "critical"
        
        if data["auto_repair_results"]:
            ar = data["auto_repair_results"]
            health["auto_repair_effective"] = ar.get("success", False)
        else:
            health["auto_repair_effective"] = False
        
        return health

    def create_github_issue(self, data):
        """Create GitHub issue for critical TestSprite failures"""
        if not self.github_token:
            self.log("No GitHub token - skipping issue creation")
            return None
        
        health = data["system_health"]
        
        # Only create issue for critical problems
        if health["critical_issues"] == 0:
            self.log("No critical issues - skipping GitHub issue creation")
            return None
        
        self.log(f"Creating GitHub issue for {health['critical_issues']} critical issues...")
        
        # Prepare issue content
        title = f"🚨 TestSprite Critical Issues: {health['critical_issues']} failures ({health['pass_rate']}% pass rate)"
        
        body = self._generate_issue_body(data)
        
        # Create issue via GitHub API
        issue_data = {
            "title": title,
            "body": body,
            "labels": self.sync_config["issue_labels"] + ["critical", "needs-attention"]
        }
        
        try:
            response = requests.post(
                f"{self.github_api_base}/repos/{self.repo_owner}/{self.repo_name}/issues",
                headers={
                    "Authorization": f"token {self.github_token}",
                    "Accept": "application/vnd.github.v3+json"
                },
                json=issue_data
            )
            
            if response.status_code == 201:
                issue = response.json()
                self.log(f"✅ GitHub issue created: #{issue['number']}")
                return issue
            else:
                self.log(f"❌ Failed to create GitHub issue: {response.status_code}")
                return None
                
        except Exception as e:
            self.log(f"❌ GitHub issue creation failed: {e}")
            return None

    def _generate_issue_body(self, data):
        """Generate GitHub issue body content"""
        health = data["system_health"]
        testsprite_results = data.get("testsprite_results", {})
        auto_repair_results = data.get("auto_repair_results", {})
        
        # Get immediate actions from TestSprite results
        immediate_actions = []
        if testsprite_results:
            immediate_actions = testsprite_results.get("adhd_report", {}).get("IMMEDIATE_ACTIONS", [])
        
        body = f"""# 🧪 TestSprite Critical Issues Report

## 🎯 Summary
- **Pass Rate:** {health['pass_rate']}%
- **Critical Issues:** {health['critical_issues']}
- **Overall Status:** {health['overall_status'].title()}
- **Auto-Repair Status:** {'✅ Effective' if health['auto_repair_effective'] else '⚠️ Manual intervention needed'}

## 🚨 Critical Issues Requiring Attention

"""
        
        for i, action in enumerate(immediate_actions, 1):
            body += f"""### {i}. {action.get('task', 'Unknown task')} ({action.get('priority', 'UNKNOWN')})
- **Effort:** {action.get('effort', 'Unknown')}
- **Issue:** {action.get('description', 'No description')}

"""
        
        if auto_repair_results:
            body += f"""## 🔧 Auto-Repair Status
- **Validation Score:** {auto_repair_results.get('auto_repair_summary', {}).get('validation_score', 0)}%
- **Categories Repaired:** {len(auto_repair_results.get('auto_repair_summary', {}).get('categories_repaired', []))}
- **Successful:** {'Yes' if auto_repair_results.get('success', False) else 'No'}

"""
        
        body += f"""## 📊 Full Test Results
View complete results in the [TestSprite logs](./logs/autonomous_testing/).

## 🔄 Next Steps
1. Review and address critical issues listed above
2. Run manual fixes if auto-repair was ineffective
3. Trigger re-test after fixes: `python noxsuite_testsprite_simple.py`
4. Monitor system health dashboard

---
*Auto-generated by TestSprite GitHub MCP Integration*
*Timestamp: {data['timestamp']}*
"""
        
        return body

    def commit_results_to_repo(self, data):
        """Commit TestSprite results to repository"""
        if not self.sync_config["auto_commit"]:
            self.log("Auto-commit disabled - skipping repository commit")
            return None
        
        self.log("Committing TestSprite results to repository...")
        
        try:
            # Prepare commit message
            health = data["system_health"]
            commit_msg = f"{self.sync_config['commit_prefix']} {health['pass_rate']}% pass rate"
            
            if health["critical_issues"] > 0:
                commit_msg += f" - {health['critical_issues']} critical issues"
                if health["auto_repair_effective"]:
                    commit_msg += " (auto-repaired)"
                else:
                    commit_msg += " (needs manual fix)"
            else:
                commit_msg += " - all tests passing ✅"
            
            # Stage files
            files_to_commit = [
                "logs/autonomous_testing/",
                "logs/auto_repair/",
                "NOXSUITE_TESTSPRITE_AUTONOMOUS_TESTING_COMPLETE.md"
            ]
            
            # Configure git
            subprocess.run(["git", "config", "--local", "user.email", "testsprite@automation.local"], check=True)
            subprocess.run(["git", "config", "--local", "user.name", "TestSprite Automation"], check=True)
            
            # Add files (ignore .gitignore for logs)
            for file_path in files_to_commit:
                if Path(file_path).exists():
                    try:
                        subprocess.run(["git", "add", "-f", file_path], check=True)
                        self.log(f"Added {file_path} to commit")
                    except subprocess.CalledProcessError:
                        self.log(f"Warning: Could not add {file_path}")
                        continue
            
            # Check if there are changes to commit
            result = subprocess.run(["git", "diff", "--staged", "--quiet"], capture_output=True)
            if result.returncode == 0:
                self.log("No changes to commit")
                return None
            
            # Commit changes
            subprocess.run(["git", "commit", "-m", commit_msg], check=True)
            self.log(f"✅ Committed changes: {commit_msg}")
            
            # Push to remote (if configured)
            try:
                subprocess.run(["git", "push", "origin", "HEAD"], check=True, timeout=30)
                self.log("✅ Pushed changes to remote repository")
            except subprocess.TimeoutExpired:
                self.log("⚠️ Push timed out - changes committed locally")
            except subprocess.CalledProcessError:
                self.log("⚠️ Push failed - changes committed locally")
            
            return {"status": "success", "commit_message": commit_msg}
            
        except Exception as e:
            self.log(f"❌ Repository commit failed: {e}")
            return {"status": "failed", "error": str(e)}

    def update_status_badge(self, data):
        """Update status badge/shield for repository"""
        self.log("Updating TestSprite status badge...")
        
        health = data["system_health"]
        
        # Generate badge data
        badge_data = {
            "pass_rate": health["pass_rate"],
            "status": health["overall_status"],
            "critical_issues": health["critical_issues"],
            "last_updated": datetime.now().isoformat()
        }
        
        # Save badge data
        badge_file = Path("./testsprite_status.json")
        with open(badge_file, 'w', encoding='utf-8') as f:
            json.dump(badge_data, f, indent=2)
        
        self.log(f"✅ Status badge updated: {health['pass_rate']}% ({health['overall_status']})")
        return badge_data

    def generate_mcp_summary(self, data):
        """Generate MCP-compatible summary for integration"""
        self.log("Generating MCP integration summary...")
        
        health = data["system_health"]
        
        mcp_summary = {
            "mcp_integration": "testsprite",
            "timestamp": data["timestamp"],
            "status": health["overall_status"],
            "metrics": {
                "pass_rate": health["pass_rate"],
                "critical_issues": health["critical_issues"],
                "auto_repair_effective": health["auto_repair_effective"]
            },
            "actions_required": health["critical_issues"] > 0,
            "github_integration": {
                "repository": f"{self.repo_owner}/{self.repo_name}",
                "auto_commit": self.sync_config["auto_commit"],
                "issue_tracking": True
            },
            "langflow_integration": {
                "auto_repair_enabled": True,
                "validation_score": (data.get("auto_repair_results") or {}).get("auto_repair_summary", {}).get("validation_score", 0)
            }
        }
        
        # Save MCP summary
        mcp_file = Path("./logs/mcp_integration_summary.json")
        mcp_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(mcp_file, 'w', encoding='utf-8') as f:
            json.dump(mcp_summary, f, indent=2)
        
        self.log(f"✅ MCP summary generated: {mcp_file}")
        return mcp_summary

    def run_github_sync(self):
        """Main GitHub MCP sync orchestrator"""
        print("📡 Starting GitHub MCP Sync for TestSprite")
        print("=" * 60)
        
        try:
            # Phase 1: Collect data
            data = self.collect_testsprite_data()
            
            # Phase 2: Create GitHub issue if needed
            github_issue = self.create_github_issue(data)
            
            # Phase 3: Commit results to repository
            commit_result = self.commit_results_to_repo(data)
            
            # Phase 4: Update status badge
            badge_data = self.update_status_badge(data)
            
            # Phase 5: Generate MCP summary
            mcp_summary = self.generate_mcp_summary(data)
            
            # Final summary
            health = data["system_health"]
            print("\n" + "=" * 60)
            print("🎉 GITHUB MCP SYNC COMPLETE")
            print("=" * 60)
            print(f"System Health: {health['overall_status'].title()}")
            print(f"Pass Rate: {health['pass_rate']}%")
            print(f"Critical Issues: {health['critical_issues']}")
            print(f"GitHub Issue: {'Created' if github_issue else 'Not needed'}")
            print(f"Repository Sync: {'Success' if commit_result else 'Skipped'}")
            print("=" * 60)
            
            return {
                "status": "success",
                "github_issue": github_issue,
                "commit_result": commit_result,
                "badge_data": badge_data,
                "mcp_summary": mcp_summary,
                "system_health": health
            }
            
        except Exception as e:
            self.log(f"GitHub MCP sync failed: {e}")
            return {"status": "failed", "error": str(e)}

if __name__ == "__main__":
    sync = GitHubMCPSync()
    result = sync.run_github_sync()
    
    if result["status"] == "success":
        health = result["system_health"]
        print(f"\n🎯 Sync successful: {health['overall_status']} status, {health['pass_rate']}% pass rate")
    else:
        print(f"\n❌ Sync failed: {result.get('error', 'Unknown error')}")
