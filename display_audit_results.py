#!/usr/bin/env python3
"""
NoxPanel Suite - Comprehensive Code Audit Results
Displays structured audit findings in requested format
"""

import json
from pathlib import Path

def main():
    """Display audit findings"""
    findings_file = Path("comprehensive_audit_findings.json")
    
    if not findings_file.exists():
        print("❌ Audit findings file not found!")
        return
    
    with open(findings_file, 'r', encoding='utf-8') as f:
        findings = json.load(f)
    
    print("🔍 NoxPanel Suite - Comprehensive Code Audit Report")
    print("=" * 60)
    print(f"📊 Total Issues Found: {len(findings)}")
    
    # Count by category
    categories = {}
    priorities = {"high": 0, "medium": 0, "low": 0}
    
    for finding in findings:
        category = finding["type"]
        priority = finding["priority"]
        
        categories[category] = categories.get(category, 0) + 1
        priorities[priority] = priorities.get(priority, 0) + 1
    
    print("\n📈 Issues by Category:")
    for category, count in sorted(categories.items()):
        print(f"  • {category}: {count}")
    
    print("\n🎯 Issues by Priority:")
    for priority, count in priorities.items():
        print(f"  • {priority.title()}: {count}")
    
    print("\n" + "=" * 60)
    print("📋 JSON Output (as requested):")
    print(json.dumps(findings, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()