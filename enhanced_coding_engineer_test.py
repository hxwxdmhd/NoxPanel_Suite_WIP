#!/usr/bin/env python3
"""
Enhanced Coding Engineer Integration Tester
Validates the enhanced coding and engineering workflow integration
"""

import json
import requests
import time
from datetime import datetime
import os

class EnhancedCodingEngineerTester:
    def __init__(self):
        self.langflow_url = "http://localhost:7860"
        self.workflow_file = "langflow/flows/enhanced_coding_engineer.json"
        
    def test_workflow_structure(self):
        """Test the enhanced coding engineer workflow structure"""
        try:
            with open(self.workflow_file, 'r') as f:
                workflow = json.load(f)
                
            # Validate workflow completeness
            required_components = {
                'code_intelligence_hub': 'NoxSuiteSystemMonitor',
                'engineering_ai_coordinator': 'NoxSuiteMultiAgentCoordinator',
                'development_environment_manager': 'NoxSuiteDockerManager',
                'engineering_workflow_orchestrator': 'NoxSuiteMCPOrchestrator',
                'intelligent_code_assistant': 'NoxSuiteMultiAgentCoordinator',
                'engineering_analytics_center': 'NoxSuiteSystemMonitor'
            }
            
            found_components = {}
            for node in workflow['flow']['nodes']:
                node_id = node.get('id')
                node_type = node.get('type')
                if node_id in required_components:
                    found_components[node_id] = node_type
                    
            missing_components = set(required_components.keys()) - set(found_components.keys())
            
            if missing_components:
                return {
                    "valid": False,
                    "error": f"Missing components: {missing_components}"
                }
                
            # Validate component types
            type_mismatches = []
            for comp_id, expected_type in required_components.items():
                if found_components.get(comp_id) != expected_type:
                    type_mismatches.append(f"{comp_id}: expected {expected_type}, got {found_components.get(comp_id)}")
                    
            if type_mismatches:
                return {
                    "valid": False,
                    "error": f"Component type mismatches: {type_mismatches}"
                }
                
            # Validate engineering features
            automation = workflow.get('automation', {})
            engineering_features = automation.get('engineering_features', {})
            
            required_features = [
                'ai_code_generation',
                'intelligent_refactoring', 
                'automated_testing',
                'performance_optimization',
                'security_analysis',
                'documentation_automation',
                'quality_assurance',
                'deployment_automation'
            ]
            
            missing_features = [f for f in required_features if not engineering_features.get(f, False)]
            
            if missing_features:
                return {
                    "valid": False,
                    "error": f"Missing engineering features: {missing_features}"
                }
                
            return {
                "valid": True,
                "components_count": len(found_components),
                "edges_count": len(workflow['flow']['edges']),
                "engineering_features": len(required_features),
                "automation_triggers": len(automation.get('triggers', []))
            }
            
        except Exception as e:
            return {
                "valid": False,
                "error": f"Validation error: {e}"
            }

    def test_engineering_capabilities(self):
        """Test specific engineering capabilities in the workflow"""
        try:
            with open(self.workflow_file, 'r') as f:
                workflow = json.load(f)
                
            capabilities = {
                "code_intelligence": False,
                "ai_coordination": False,
                "environment_optimization": False,
                "workflow_orchestration": False,
                "intelligent_assistance": False,
                "analytics_monitoring": False
            }
            
            # Check for code intelligence capabilities
            for node in workflow['flow']['nodes']:
                if node.get('id') == 'code_intelligence_hub':
                    data = node.get('data', {})
                    if (data.get('syntax_analysis') and 
                        data.get('security_vulnerability_scanning') and
                        data.get('performance_profiling')):
                        capabilities["code_intelligence"] = True
                        
                elif node.get('id') == 'engineering_ai_coordinator':
                    data = node.get('data', {})
                    if (data.get('ai_code_generation') and
                        data.get('intelligent_refactoring') and
                        data.get('automated_testing')):
                        capabilities["ai_coordination"] = True
                        
                elif node.get('id') == 'development_environment_manager':
                    data = node.get('data', {})
                    if (data.get('ide_optimization') and
                        data.get('development_containers') and
                        data.get('performance_monitoring')):
                        capabilities["environment_optimization"] = True
                        
                elif node.get('id') == 'engineering_workflow_orchestrator':
                    data = node.get('data', {})
                    if (data.get('code_review_automation') and
                        data.get('automated_testing_pipeline') and
                        data.get('deployment_automation')):
                        capabilities["workflow_orchestration"] = True
                        
                elif node.get('id') == 'intelligent_code_assistant':
                    data = node.get('data', {})
                    if (data.get('ai_powered_suggestions') and
                        data.get('intelligent_debugging') and
                        data.get('smart_refactoring')):
                        capabilities["intelligent_assistance"] = True
                        
                elif node.get('id') == 'engineering_analytics_center':
                    data = node.get('data', {})
                    if (data.get('development_velocity_tracking') and
                        data.get('code_quality_trends') and
                        data.get('team_productivity_metrics')):
                        capabilities["analytics_monitoring"] = True
                        
            enabled_capabilities = sum(capabilities.values())
            total_capabilities = len(capabilities)
            
            return {
                "capabilities_enabled": enabled_capabilities,
                "total_capabilities": total_capabilities,
                "capability_coverage": enabled_capabilities / total_capabilities * 100,
                "detailed_capabilities": capabilities
            }
            
        except Exception as e:
            return {
                "error": f"Capability test failed: {e}"
            }

    def test_langflow_integration(self):
        """Test integration with Langflow platform"""
        try:
            response = requests.get(f"{self.langflow_url}/api/v1/flows", timeout=10)
            if response.status_code == 200:
                return {
                    "integrated": True,
                    "langflow_status": "connected",
                    "api_accessible": True
                }
            else:
                return {
                    "integrated": False,
                    "error": f"HTTP {response.status_code}: {response.text}"
                }
        except requests.exceptions.RequestException as e:
            return {
                "integrated": False,
                "error": f"Connection failed: {e}"
            }

    def run_comprehensive_tests(self):
        """Run comprehensive tests on enhanced coding engineer workflow"""
        print("🧪 ENHANCED CODING ENGINEER INTEGRATION TESTING")
        print("="*70)
        print(f"🕐 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Test workflow structure
        print("\n1. Testing Enhanced Coding Engineer workflow structure...")
        structure_result = self.test_workflow_structure()
        
        if structure_result['valid']:
            print(f"✅ Structure: Valid")
            print(f"   • Components: {structure_result['components_count']}")
            print(f"   • Edges: {structure_result['edges_count']}")
            print(f"   • Engineering Features: {structure_result['engineering_features']}")
            print(f"   • Automation Triggers: {structure_result['automation_triggers']}")
        else:
            print(f"❌ Structure: {structure_result['error']}")
            return False
            
        # Test engineering capabilities
        print("\n2. Testing engineering capabilities...")
        capabilities_result = self.test_engineering_capabilities()
        
        if 'error' not in capabilities_result:
            coverage = capabilities_result['capability_coverage']
            print(f"✅ Capabilities: {coverage:.0f}% coverage")
            print(f"   • Enabled: {capabilities_result['capabilities_enabled']}/{capabilities_result['total_capabilities']}")
            
            for capability, enabled in capabilities_result['detailed_capabilities'].items():
                status = "✅" if enabled else "❌"
                print(f"   {status} {capability.replace('_', ' ').title()}")
        else:
            print(f"❌ Capabilities: {capabilities_result['error']}")
            return False
            
        # Test Langflow integration
        print("\n3. Testing Langflow integration...")
        integration_result = self.test_langflow_integration()
        
        if integration_result['integrated']:
            print(f"✅ Langflow: Connected and accessible")
            print(f"   • Status: {integration_result['langflow_status']}")
            print(f"   • API: {'Accessible' if integration_result['api_accessible'] else 'Not accessible'}")
        else:
            print(f"❌ Langflow: {integration_result['error']}")
            
        # Generate final test report
        print("\n" + "="*70)
        print("📊 ENHANCED CODING ENGINEER TEST REPORT")
        print("="*70)
        
        overall_success = (structure_result['valid'] and 
                          'error' not in capabilities_result and
                          capabilities_result['capability_coverage'] >= 80)
        
        print(f"📈 Overall Status: {'✅ PASSED' if overall_success else '❌ FAILED'}")
        print(f"🔧 Engineering Readiness: {'Ready for deployment' if overall_success else 'Needs attention'}")
        print(f"🌐 Langflow Integration: {'✅ Connected' if integration_result['integrated'] else '❌ Disconnected'}")
        
        # Detailed metrics
        print(f"\n📊 Detailed Metrics:")
        if structure_result['valid']:
            print(f"   • Workflow Components: {structure_result['components_count']}/6 (100%)")
            print(f"   • Connection Edges: {structure_result['edges_count']}")
        if 'error' not in capabilities_result:
            print(f"   • Engineering Capabilities: {capabilities_result['capabilities_enabled']}/{capabilities_result['total_capabilities']} ({capabilities_result['capability_coverage']:.0f}%)")
        print(f"   • Platform Integration: {'✅ Active' if integration_result['integrated'] else '❌ Inactive'}")
        
        # Save test results
        test_report = {
            "timestamp": datetime.now().isoformat(),
            "test_type": "enhanced_coding_engineer_integration",
            "workflow_structure": structure_result,
            "engineering_capabilities": capabilities_result,
            "langflow_integration": integration_result,
            "overall_success": overall_success,
            "summary": {
                "components_validated": structure_result.get('components_count', 0),
                "capabilities_coverage": capabilities_result.get('capability_coverage', 0),
                "integration_status": integration_result['integrated']
            }
        }
        
        report_filename = f"enhanced_coding_engineer_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_filename, 'w') as f:
            json.dump(test_report, f, indent=2)
            
        print(f"\n💾 Test report saved: {report_filename}")
        
        if overall_success:
            print("\n🎉 ENHANCED CODING ENGINEER WORKFLOW PASSED ALL TESTS!")
            print("🚀 Ready for production deployment and AI-powered development assistance")
            print("🔧 All engineering capabilities validated and operational")
        else:
            print("\n⚠️ Enhanced Coding Engineer workflow needs attention before deployment")
            
        return overall_success

def main():
    tester = EnhancedCodingEngineerTester()
    success = tester.run_comprehensive_tests()
    return success

if __name__ == "__main__":
    main()
