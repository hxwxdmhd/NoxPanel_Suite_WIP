#!/usr/bin/env python3
"""
Langflow Workflow Uploader
Uploads all NoxSuite workflows to Langflow platform
"""

import requests
import json
import os
import time
from datetime import datetime
from typing import Dict, List

class LangflowUploader:
    def __init__(self):
        self.base_url = "http://localhost:7860"
        self.flows_dir = "langflow/flows"
        self.session = requests.Session()
        
        # Set up authentication if needed
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        
    def get_existing_flows(self):
        """Get list of existing flows in Langflow"""
        try:
            response = self.session.get(f"{self.base_url}/api/v1/flows")
            if response.status_code == 200:
                data = response.json()
                return data.get('flows', [])
            else:
                print(f"⚠️ Could not fetch existing flows: {response.status_code}")
                return []
        except Exception as e:
            print(f"⚠️ Error fetching flows: {e}")
            return []
    
    def upload_workflow(self, workflow_file: str) -> Dict:
        """Upload a single workflow to Langflow"""
        try:
            workflow_path = os.path.join(self.flows_dir, workflow_file)
            
            if not os.path.exists(workflow_path):
                return {
                    "success": False,
                    "error": f"File not found: {workflow_path}"
                }
            
            # Load workflow JSON
            with open(workflow_path, 'r', encoding='utf-8') as f:
                workflow_data = json.load(f)
            
            # Extract workflow name and description
            workflow_name = workflow_data.get('name', workflow_file.replace('.json', ''))
            workflow_description = workflow_data.get('description', '')
            
            # Prepare the flow data for Langflow API
            flow_data = {
                "name": workflow_name,
                "description": workflow_description,
                "data": workflow_data.get('flow', {}),
                "is_component": False
            }
            
            # Try to upload the flow
            response = self.session.post(
                f"{self.base_url}/api/v1/flows",
                json=flow_data,
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                return {
                    "success": True,
                    "name": workflow_name,
                    "response": response.json()
                }
            else:
                # Try alternative upload method
                return self.upload_workflow_alternative(workflow_data, workflow_name)
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Upload failed: {e}"
            }
    
    def upload_workflow_alternative(self, workflow_data: Dict, workflow_name: str) -> Dict:
        """Alternative upload method for Langflow"""
        try:
            # Try uploading as a JSON file
            import_data = {
                "flow": workflow_data,
                "name": workflow_name
            }
            
            response = self.session.post(
                f"{self.base_url}/api/v1/flows/upload",
                json=import_data,
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                return {
                    "success": True,
                    "name": workflow_name,
                    "method": "alternative",
                    "response": response.json()
                }
            else:
                return {
                    "success": False,
                    "error": f"Alternative upload failed: {response.status_code} - {response.text}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Alternative upload error: {e}"
            }
    
    def update_workflow_metadata(self, workflow_file: str):
        """Update workflow with enhanced metadata for Langflow compatibility"""
        try:
            workflow_path = os.path.join(self.flows_dir, workflow_file)
            
            with open(workflow_path, 'r', encoding='utf-8') as f:
                workflow = json.load(f)
            
            # Add Langflow-specific metadata
            if 'flow' in workflow:
                # Ensure nodes have proper IDs and types
                for node in workflow['flow'].get('nodes', []):
                    if 'data' not in node:
                        node['data'] = {}
                    
                    # Add Langflow node metadata
                    node['data']['langflow_id'] = node['id']
                    node['data']['display_name'] = node['id'].replace('_', ' ').title()
                    
                    # Ensure position data
                    if 'position' not in node:
                        node['position'] = {'x': 100, 'y': 100}
                
                # Ensure edges have proper structure
                for edge in workflow['flow'].get('edges', []):
                    if 'type' not in edge:
                        edge['type'] = 'default'
                    if 'animated' not in edge:
                        edge['animated'] = False
            
            # Add Langflow flow metadata
            workflow['updated_at'] = datetime.now().isoformat()
            workflow['langflow_version'] = '1.0'
            workflow['noxsuite_version'] = '2.0'
            
            # Save updated workflow
            with open(workflow_path, 'w', encoding='utf-8') as f:
                json.dump(workflow, f, indent=2, ensure_ascii=False)
                
            return True
            
        except Exception as e:
            print(f"⚠️ Error updating metadata for {workflow_file}: {e}")
            return False
    
    def upload_all_workflows(self):
        """Upload all workflows to Langflow"""
        print("🚀 LANGFLOW WORKFLOW UPLOADER")
        print("="*60)
        print(f"🕐 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Get list of workflow files
        workflow_files = [
            'enhanced_coding_engineer.json',
            'cyber_defense_matrix.json',
            'edge_iot_commander.json', 
            'devops_automation_engine.json',
            'autonomous_self_healing.json',
            'copilot_ai_hub.json',
            'devenv_optimizer.json',
            'distributed_orchestrator.json',
            'ai_code_scanner.json',
            'smart_autoscaler.json',
            'security_guardian.json',
            'smart_data_pipeline.json'
        ]
        
        # Check Langflow connectivity
        print("\n1. Testing Langflow connectivity...")
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=10)
            if response.status_code == 200:
                print("✅ Langflow: Connected and healthy")
            else:
                print(f"⚠️ Langflow health check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Cannot connect to Langflow: {e}")
            return False
        
        # Get existing flows
        print("\n2. Checking existing flows...")
        existing_flows = self.get_existing_flows()
        print(f"📊 Found {len(existing_flows)} existing flows in Langflow")
        
        # Update workflow metadata
        print("\n3. Updating workflow metadata...")
        for workflow_file in workflow_files:
            workflow_path = os.path.join(self.flows_dir, workflow_file)
            if os.path.exists(workflow_path):
                if self.update_workflow_metadata(workflow_file):
                    print(f"✅ Updated: {workflow_file}")
                else:
                    print(f"⚠️ Failed to update: {workflow_file}")
        
        # Upload workflows
        print("\n4. Uploading workflows to Langflow...")
        upload_results = []
        successful_uploads = 0
        
        for workflow_file in workflow_files:
            workflow_path = os.path.join(self.flows_dir, workflow_file)
            
            if not os.path.exists(workflow_path):
                print(f"⚠️ Skipping {workflow_file}: File not found")
                continue
            
            print(f"\n📤 Uploading: {workflow_file}")
            
            result = self.upload_workflow(workflow_file)
            upload_results.append(result)
            
            if result['success']:
                successful_uploads += 1
                print(f"✅ Success: {result['name']}")
                if 'method' in result:
                    print(f"   Method: {result['method']}")
            else:
                print(f"❌ Failed: {result['error']}")
            
            # Brief pause between uploads
            time.sleep(1)
        
        # Generate upload report
        print("\n" + "="*60)
        print("📊 LANGFLOW UPLOAD REPORT")
        print("="*60)
        
        total_workflows = len(workflow_files)
        success_rate = (successful_uploads / total_workflows) * 100
        
        print(f"📈 Upload Success Rate: {successful_uploads}/{total_workflows} ({success_rate:.1f}%)")
        print(f"🌐 Langflow Status: Connected and operational")
        print(f"📦 Total Workflows Available: {total_workflows}")
        
        # Detailed results
        print(f"\n📋 Detailed Results:")
        for i, (workflow_file, result) in enumerate(zip(workflow_files, upload_results), 1):
            status = "✅" if result['success'] else "❌"
            print(f"   {i:2d}. {status} {workflow_file}")
            if not result['success']:
                print(f"       Error: {result['error']}")
        
        # Save upload report
        upload_report = {
            "timestamp": datetime.now().isoformat(),
            "upload_type": "langflow_workflows",
            "total_workflows": total_workflows,
            "successful_uploads": successful_uploads,
            "success_rate": success_rate,
            "langflow_url": self.base_url,
            "results": dict(zip(workflow_files, upload_results))
        }
        
        report_filename = f"langflow_upload_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_filename, 'w') as f:
            json.dump(upload_report, f, indent=2)
        
        print(f"\n💾 Upload report saved: {report_filename}")
        
        if successful_uploads == total_workflows:
            print("\n🎉 ALL WORKFLOWS SUCCESSFULLY UPLOADED TO LANGFLOW!")
            print("🌐 Access your workflows at: http://localhost:7860")
            print("🔧 Login credentials: noxsuite_admin / noxsuite_secure_2024")
        else:
            print(f"\n⚠️ {total_workflows - successful_uploads} workflows need attention")
            print("💡 Check the upload report for detailed error information")
        
        return successful_uploads == total_workflows

def main():
    uploader = LangflowUploader()
    success = uploader.upload_all_workflows()
    
    if success:
        print("\n🚀 Langflow upload completed successfully!")
        print("🎯 All NoxSuite workflows are now available in Langflow")
    else:
        print("\n⚠️ Some uploads failed - check the report for details")
    
    return success

if __name__ == "__main__":
    main()
