"""
NoxSuite Custom Components Registration System for Langflow
Handles dynamic loading and registration of custom NoxSuite components
"""

import os
import json
import importlib.util
from typing import Dict, List, Any, Optional
from pathlib import Path

class NoxSuiteComponentRegistry:
    """Registry for managing custom NoxSuite components in Langflow"""
    
    def __init__(self, components_dir: str = None):
        self.components_dir = components_dir or os.path.join(os.path.dirname(__file__), "components")
        self.registered_components = {}
        self.component_metadata = {}
        
    def discover_components(self) -> List[str]:
        """Discover all NoxSuite components in the components directory"""
        components = []
        if not os.path.exists(self.components_dir):
            print(f"Components directory not found: {self.components_dir}")
            return components
            
        for file in os.listdir(self.components_dir):
            if file.startswith("noxsuite_") and file.endswith(".py"):
                component_name = file[:-3]  # Remove .py extension
                components.append(component_name)
                
        return components
    
    def load_component(self, component_name: str) -> Optional[Any]:
        """Load a specific component module"""
        try:
            component_path = os.path.join(self.components_dir, f"{component_name}.py")
            if not os.path.exists(component_path):
                print(f"Component file not found: {component_path}")
                return None
                
            spec = importlib.util.spec_from_file_location(component_name, component_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            return module
            
        except Exception as e:
            print(f"Error loading component {component_name}: {str(e)}")
            return None
    
    def register_component(self, component_name: str, component_class: Any) -> bool:
        """Register a component with the registry"""
        try:
            self.registered_components[component_name] = component_class
            
            # Extract metadata from component
            metadata = {
                "name": component_name,
                "class_name": component_class.__name__,
                "description": getattr(component_class, "description", ""),
                "category": getattr(component_class, "category", "NoxSuite"),
                "inputs": getattr(component_class, "inputs", []),
                "outputs": getattr(component_class, "outputs", []),
                "documentation": getattr(component_class, "__doc__", "")
            }
            
            self.component_metadata[component_name] = metadata
            print(f"✅ Registered component: {component_name}")
            return True
            
        except Exception as e:
            print(f"❌ Error registering component {component_name}: {str(e)}")
            return False
    
    def auto_register_all(self) -> Dict[str, bool]:
        """Automatically discover and register all NoxSuite components"""
        results = {}
        components = self.discover_components()
        
        print(f"🔍 Discovered {len(components)} NoxSuite components")
        
        for component_name in components:
            module = self.load_component(component_name)
            if module:
                # Look for component classes in the module
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (isinstance(attr, type) and 
                        hasattr(attr, 'display_name') and 
                        'NoxSuite' in attr_name):
                        
                        success = self.register_component(component_name, attr)
                        results[component_name] = success
                        break
                else:
                    print(f"⚠️ No valid component class found in {component_name}")
                    results[component_name] = False
            else:
                results[component_name] = False
                
        return results
    
    def get_component_info(self, component_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific component"""
        return self.component_metadata.get(component_name)
    
    def list_registered_components(self) -> List[str]:
        """List all registered component names"""
        return list(self.registered_components.keys())
    
    def generate_langflow_config(self) -> Dict[str, Any]:
        """Generate Langflow configuration for all registered components"""
        config = {
            "custom_components": {},
            "component_paths": [self.components_dir],
            "auto_load": True,
            "noxsuite_integration": {
                "version": "1.0.0",
                "emergency_throttling": True,
                "tool_usage_monitoring": True,
                "docker_integration": True,
                "mcp_integration": True
            }
        }
        
        for component_name, metadata in self.component_metadata.items():
            config["custom_components"][component_name] = {
                "module_path": f"components.{component_name}",
                "class_name": metadata["class_name"],
                "category": metadata["category"],
                "enabled": True,
                "priority": "high" if "emergency" in component_name.lower() else "normal"
            }
            
        return config
    
    def save_registry_state(self, output_file: str = None) -> bool:
        """Save the current registry state to a JSON file"""
        try:
            output_file = output_file or os.path.join(self.components_dir, "registry_state.json")
            
            state = {
                "timestamp": str(pd.Timestamp.now()),
                "components_directory": self.components_dir,
                "registered_components": list(self.registered_components.keys()),
                "component_metadata": self.component_metadata,
                "langflow_config": self.generate_langflow_config()
            }
            
            with open(output_file, 'w') as f:
                json.dump(state, f, indent=2)
                
            print(f"💾 Registry state saved to: {output_file}")
            return True
            
        except Exception as e:
            print(f"❌ Error saving registry state: {str(e)}")
            return False

def initialize_noxsuite_components() -> NoxSuiteComponentRegistry:
    """Initialize and register all NoxSuite components for Langflow"""
    print("🚀 Initializing NoxSuite Component Registry...")
    
    # Create registry instance
    registry = NoxSuiteComponentRegistry()
    
    # Auto-register all components
    registration_results = registry.auto_register_all()
    
    # Print registration summary
    successful = sum(1 for success in registration_results.values() if success)
    total = len(registration_results)
    
    print(f"\n📊 Registration Summary:")
    print(f"   ✅ Successfully registered: {successful}/{total} components")
    
    for component_name, success in registration_results.items():
        status = "✅" if success else "❌"
        print(f"   {status} {component_name}")
    
    # Generate and save configuration
    registry.save_registry_state()
    
    print(f"\n🎯 NoxSuite Component Registry initialized successfully!")
    print(f"   📁 Components directory: {registry.components_dir}")
    print(f"   🔧 Registered components: {len(registry.registered_components)}")
    
    return registry

def get_component_documentation() -> str:
    """Generate comprehensive documentation for all NoxSuite components"""
    registry = NoxSuiteComponentRegistry()
    registry.auto_register_all()
    
    docs = []
    docs.append("# NoxSuite Custom Components Documentation")
    docs.append("## Available Components\n")
    
    for component_name, metadata in registry.component_metadata.items():
        docs.append(f"### {metadata['name']}")
        docs.append(f"**Class:** `{metadata['class_name']}`")
        docs.append(f"**Category:** {metadata['category']}")
        docs.append(f"**Description:** {metadata['description']}")
        
        if metadata.get('documentation'):
            docs.append(f"**Details:**\n{metadata['documentation']}")
        
        docs.append("")
    
    return "\n".join(docs)

if __name__ == "__main__":
    # Import required dependencies
    try:
        import pandas as pd
    except ImportError:
        # Fallback timestamp
        class pd:
            @staticmethod
            class Timestamp:
                @staticmethod
                def now():
                    from datetime import datetime
                    return datetime.now().isoformat()
    
    # Initialize the component registry
    registry = initialize_noxsuite_components()
    
    # Generate documentation
    documentation = get_component_documentation()
    docs_file = os.path.join(registry.components_dir, "COMPONENTS_DOCUMENTATION.md")
    
    try:
        with open(docs_file, 'w') as f:
            f.write(documentation)
        print(f"📚 Component documentation saved to: {docs_file}")
    except Exception as e:
        print(f"⚠️ Could not save documentation: {str(e)}")
    
    print("\n🎉 NoxSuite components are ready for Langflow integration!")
