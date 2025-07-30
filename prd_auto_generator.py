#!/usr/bin/env python3
"""
PRD Auto-Generator
Automatically generates Product Requirement Documents from test results
"""

import json
import datetime
from pathlib import Path
from typing import Dict, List, Any

class PRDAutoGenerator:
    def __init__(self):
        self.timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
    def load_test_results(self) -> Dict[str, Any]:
        """Load latest test results from various sources"""
        results = {
            "testsprite": None,
            "comprehensive": None,
            "performance": None,
            "security": None
        }
        
        # Load TestSprite results
        testsprite_dir = Path("logs/autonomous_testing")
        if testsprite_dir.exists():
            testsprite_files = list(testsprite_dir.glob("testsprite_results_*.json"))
            if testsprite_files:
                latest_testsprite = max(testsprite_files, key=lambda x: x.stat().st_mtime)
                with open(latest_testsprite, 'r', encoding='utf-8') as f:
                    results["testsprite"] = json.load(f)
        
        # Load comprehensive test results
        comprehensive_dir = Path("logs/comprehensive_testing")
        if comprehensive_dir.exists():
            comprehensive_files = list(comprehensive_dir.glob("comprehensive_results_*.json"))
            if comprehensive_files:
                latest_comprehensive = max(comprehensive_files, key=lambda x: x.stat().st_mtime)
                with open(latest_comprehensive, 'r', encoding='utf-8') as f:
                    results["comprehensive"] = json.load(f)
        
        # Load performance results
        performance_dir = Path("logs/performance_testing")
        if performance_dir.exists():
            performance_files = list(performance_dir.glob("performance_results_*.json"))
            if performance_files:
                latest_performance = max(performance_files, key=lambda x: x.stat().st_mtime)
                with open(latest_performance, 'r', encoding='utf-8') as f:
                    results["performance"] = json.load(f)
        
        return results
    
    def extract_requirements_from_failures(self, test_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract product requirements from test failures"""
        requirements = []
        
        # Analyze TestSprite results
        if test_results.get("testsprite"):
            ts_results = test_results["testsprite"]
            
            for suite_name, suite_data in ts_results.get("test_suites", {}).items():
                for test in suite_data.get("tests", []):
                    if test.get("status") == "FAIL":
                        requirements.append({
                            "id": f"REQ-{len(requirements)+1:03d}",
                            "title": f"Fix {test['name']} Functionality",
                            "description": f"Address failure in {test['name']} to ensure {suite_name} operates correctly",
                            "priority": "HIGH" if "critical" in test.get("category", "").lower() else "MEDIUM",
                            "source": "TestSprite Failure",
                            "category": suite_name,
                            "acceptance_criteria": [
                                f"{test['name']} test passes consistently",
                                f"No regressions in {suite_name} functionality",
                                "Performance within acceptable thresholds"
                            ]
                        })
        
        # Analyze comprehensive test results
        if test_results.get("comprehensive"):
            comp_results = test_results["comprehensive"]
            
            for test_type in ["edge_cases", "security_tests", "chaos_tests", "performance_metrics"]:
                if test_type in comp_results:
                    for test_name, test_data in comp_results[test_type].items():
                        if test_data.get("status") == "FAIL":
                            requirements.append({
                                "id": f"REQ-{len(requirements)+1:03d}",
                                "title": f"Improve {test_name.replace('_', ' ').title()}",
                                "description": f"Address {test_type.replace('_', ' ')} failure in {test_name}",
                                "priority": "CRITICAL" if test_data.get("severity") == "HIGH" else "HIGH",
                                "source": f"Comprehensive Testing - {test_type}",
                                "category": test_type,
                                "acceptance_criteria": [
                                    f"{test_name} test achieves >85% score",
                                    "System demonstrates resilience under stress",
                                    "Security vulnerabilities are resolved"
                                ]
                            })
        
        return requirements
    
    def extract_performance_requirements(self, test_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract performance-related requirements"""
        requirements = []
        
        if test_results.get("performance"):
            perf_results = test_results["performance"]
            
            # Scalability requirements
            if "scalability_tests" in perf_results:
                for scenario_name, scenario_data in perf_results["scalability_tests"].items():
                    if scenario_data.get("scalability_score", 0) < 0.8:
                        requirements.append({
                            "id": f"REQ-{len(requirements)+1:03d}",
                            "title": f"Optimize {scenario_name.replace('_', ' ').title()} Performance",
                            "description": f"Improve system performance under {scenario_name} conditions",
                            "priority": "MEDIUM",
                            "source": "Performance Testing",
                            "category": "Performance",
                            "acceptance_criteria": [
                                f"Scalability score >0.8 for {scenario_name}",
                                f"Throughput >{scenario_data.get('throughput', 0) * 1.2} ops/s",
                                "Resource utilization <80%"
                            ]
                        })
            
            # Resource optimization requirements
            if "resource_monitoring" in perf_results:
                rm = perf_results["resource_monitoring"]
                if rm.get("resource_efficiency") == "NEEDS_OPTIMIZATION":
                    requirements.append({
                        "id": f"REQ-{len(requirements)+1:03d}",
                        "title": "Optimize System Resource Usage",
                        "description": "Reduce CPU and memory consumption for better efficiency",
                        "priority": "MEDIUM",
                        "source": "Resource Monitoring",
                        "category": "Performance",
                        "acceptance_criteria": [
                            "Average CPU usage <50%",
                            "Average memory usage <70%", 
                            "Resource efficiency rated as EXCELLENT"
                        ]
                    })
        
        return requirements
    
    def generate_feature_roadmap(self, requirements: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Generate feature roadmap based on requirements"""
        roadmap = {
            "immediate": [],
            "short_term": [],
            "medium_term": [],
            "long_term": []
        }
        
        for req in requirements:
            priority = req.get("priority", "MEDIUM")
            category = req.get("category", "General")
            
            if priority == "CRITICAL":
                roadmap["immediate"].append(req)
            elif priority == "HIGH":
                roadmap["short_term"].append(req)
            elif priority == "MEDIUM":
                roadmap["medium_term"].append(req)
            else:
                roadmap["long_term"].append(req)
        
        return roadmap
    
    def generate_prd_document(self, test_results: Dict[str, Any]) -> str:
        """Generate complete PRD document"""
        
        # Extract requirements
        failure_requirements = self.extract_requirements_from_failures(test_results)
        performance_requirements = self.extract_performance_requirements(test_results)
        all_requirements = failure_requirements + performance_requirements
        
        # Generate roadmap
        roadmap = self.generate_feature_roadmap(all_requirements)
        
        # Generate document
        prd = f"""# 📋 **PRODUCT REQUIREMENTS DOCUMENT**

**Generated**: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}  
**Source**: Automated Test Analysis  
**Version**: 1.0  
**Status**: Auto-Generated

---

## 📊 **EXECUTIVE SUMMARY**

This PRD has been automatically generated based on comprehensive testing results from NoxSuite's autonomous development workflow. The requirements outlined below address identified failures, performance bottlenecks, and enhancement opportunities discovered through:

- ✅ TestSprite Autonomous Testing
- ✅ Comprehensive Edge Case & Security Testing  
- ✅ Performance Load Scenarios
- ✅ Chaos Engineering Tests

**Total Requirements Identified**: {len(all_requirements)}

---

## 🎯 **CORE REQUIREMENTS**

"""
        
        for i, req in enumerate(all_requirements, 1):
            prd += f"""### {req['id']}: {req['title']}

**Priority**: {req['priority']}  
**Category**: {req['category']}  
**Source**: {req['source']}

**Description**: {req['description']}

**Acceptance Criteria**:
"""
            for criteria in req['acceptance_criteria']:
                prd += f"- {criteria}\n"
            
            prd += "\n---\n\n"
        
        prd += f"""## 🗓️ **DEVELOPMENT ROADMAP**

### 🚨 **IMMEDIATE (Critical Priority)**
*Timeline: Within 1 week*

"""
        for req in roadmap["immediate"]:
            prd += f"- **{req['id']}**: {req['title']}\n"
        
        prd += f"""
### ⚡ **SHORT TERM (High Priority)**  
*Timeline: 2-4 weeks*

"""
        for req in roadmap["short_term"]:
            prd += f"- **{req['id']}**: {req['title']}\n"
        
        prd += f"""
### 📈 **MEDIUM TERM (Medium Priority)**
*Timeline: 1-3 months*

"""
        for req in roadmap["medium_term"]:
            prd += f"- **{req['id']}**: {req['title']}\n"
        
        prd += f"""
### 🚀 **LONG TERM (Low Priority)**
*Timeline: 3+ months*

"""
        for req in roadmap["long_term"]:
            prd += f"- **{req['id']}**: {req['title']}\n"
        
        prd += f"""
---

## 📋 **IMPLEMENTATION GUIDELINES**

### 🔧 **Development Process**
1. Address critical requirements first
2. Implement comprehensive testing for each requirement
3. Validate fixes through automated testing pipeline
4. Monitor performance impact of changes

### 🧪 **Testing Strategy**
- All requirements must pass TestSprite validation
- Comprehensive testing suite execution required
- Performance regression testing mandatory
- Security validation for security-related requirements

### 📊 **Success Metrics**
- TestSprite pass rate >95%
- Comprehensive testing score >90%
- Performance efficiency rating: EXCELLENT
- Zero critical security vulnerabilities

---

## 🎯 **APPENDIX**

### 📈 **Test Results Summary**
"""
        
        if test_results.get("testsprite"):
            ts = test_results["testsprite"]
            prd += f"- **TestSprite Pass Rate**: {ts.get('summary', {}).get('pass_rate', 'N/A')}%\n"
            prd += f"- **Critical Issues**: {ts.get('summary', {}).get('critical_issues', 'N/A')}\n"
        
        if test_results.get("comprehensive"):
            comp = test_results["comprehensive"]
            prd += f"- **Comprehensive Testing**: {comp.get('summary', {}).get('overall_health', 'N/A')}\n"
        
        if test_results.get("performance"):
            perf = test_results["performance"]
            if "resource_monitoring" in perf:
                prd += f"- **Resource Efficiency**: {perf['resource_monitoring'].get('resource_efficiency', 'N/A')}\n"
        
        prd += f"""
### 🔗 **Related Documents**
- TestSprite Testing Results
- Comprehensive Testing Reports  
- Performance Analysis Reports
- Security Vulnerability Assessments

---

**📋 AUTO-GENERATED PRD - READY FOR DEVELOPMENT PLANNING**
"""
        
        return prd
    
    def save_prd_document(self, prd_content: str):
        """Save PRD document to docs directory"""
        docs_dir = Path("docs")
        docs_dir.mkdir(parents=True, exist_ok=True)
        
        prd_file = docs_dir / f"auto_generated_prd_{self.timestamp}.md"
        
        with open(prd_file, 'w', encoding='utf-8') as f:
            f.write(prd_content)
        
        # Also save as latest
        latest_file = docs_dir / "auto_generated_prd.md"
        with open(latest_file, 'w', encoding='utf-8') as f:
            f.write(prd_content)
        
        print(f"📋 PRD generated:")
        print(f"   📄 Versioned: {prd_file}")
        print(f"   📄 Latest: {latest_file}")
        
        return prd_file

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="PRD Auto-Generator")
    parser.add_argument("--from-test-results", action="store_true", help="Generate PRD from test results")
    
    args = parser.parse_args()
    
    generator = PRDAutoGenerator()
    
    if args.from_test_results:
        print("📋 Generating PRD from test results...")
        
        # Load test results
        test_results = generator.load_test_results()
        
        # Generate PRD
        prd_content = generator.generate_prd_document(test_results)
        
        # Save PRD
        prd_file = generator.save_prd_document(prd_content)
        
        print(f"✅ PRD generation complete: {prd_file}")
    
    return generator

if __name__ == "__main__":
    main()
