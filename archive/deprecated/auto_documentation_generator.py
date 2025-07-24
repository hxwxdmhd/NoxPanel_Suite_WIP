#!/usr/bin/env python3
"""
Auto-Generated Documentation System - Audit 3 Phase 3
=====================================================

This system automatically generates comprehensive documentation:
- Plugin API documentation
- Configuration reference
- Security documentation
- Performance specifications
- Usage examples
- HTML/Markdown output

Essential for plugin ecosystem documentation and developer onboarding
"""

import os
import sys
import json
import time
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from dataclasses import dataclass, field
import re
import ast
import inspect

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Import required components
try:
    from plugin_manifest_system import PluginManifest, PluginManifestManager
    from plugin_registry_db import PluginRegistryDatabase, PluginMetadata
except ImportError as e:
    logging.error(f"Failed to import required components: {e}")
    sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class DocumentationSection:
    """Documentation section structure"""
    title: str
    content: str
    level: int = 1
    anchor: str = ""
    
    def __post_init__(self):
        if not self.anchor:
            self.anchor = self.title.lower().replace(' ', '-').replace('_', '-')

@dataclass
class APIEndpointDoc:
    """API endpoint documentation"""
    path: str
    method: str
    description: str
    parameters: List[Dict[str, Any]] = field(default_factory=list)
    response_schema: Dict[str, Any] = field(default_factory=dict)
    examples: List[Dict[str, Any]] = field(default_factory=list)
    requires_auth: bool = False

class PluginDocumentationGenerator:
    """
    Automatic plugin documentation generator
    """
    
    def __init__(self, plugin_dir: str = "plugins"):
        self.plugin_dir = plugin_dir
        self.manifest_manager = PluginManifestManager()
        self.registry_db = PluginRegistryDatabase()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Documentation templates
        self.html_template = self._load_html_template()
        self.markdown_template = self._load_markdown_template()
    
    def generate_plugin_documentation(self, plugin_name: str) -> Dict[str, str]:
        """
        Generate comprehensive documentation for a plugin
        
        Args:
            plugin_name: Name of the plugin
            
        Returns:
            Dict[str, str]: Documentation in different formats
        """
        try:
            # Load plugin manifest
            plugin_path = os.path.join(self.plugin_dir, plugin_name)
            manifest = self.manifest_manager.load_manifest(plugin_path)
            
            if not manifest:
                raise ValueError(f"No manifest found for plugin: {plugin_name}")
            
            # Load plugin metadata from registry
            plugin_metadata = self.registry_db.get_plugin(plugin_name)
            
            # Generate documentation sections
            sections = self._generate_documentation_sections(manifest, plugin_metadata)
            
            # Generate different formats
            documentation = {
                "html": self._generate_html_documentation(sections, manifest),
                "markdown": self._generate_markdown_documentation(sections, manifest),
                "json": self._generate_json_documentation(sections, manifest),
                "api": self._generate_api_documentation(manifest)
            }
            
            return documentation
            
        except Exception as e:
            self.logger.error(f"Failed to generate documentation for {plugin_name}: {e}")
            raise
    
    def _generate_documentation_sections(self, manifest: PluginManifest, 
                                       metadata: Optional[PluginMetadata]) -> List[DocumentationSection]:
        """Generate all documentation sections"""
        sections = []
        
        # Overview section
        sections.append(self._generate_overview_section(manifest))
        
        # Installation section
        sections.append(self._generate_installation_section(manifest))
        
        # Configuration section
        sections.append(self._generate_configuration_section(manifest))
        
        # Security section
        sections.append(self._generate_security_section(manifest))
        
        # API section (if applicable)
        if manifest.provides_api:
            sections.append(self._generate_api_section(manifest))
        
        # Performance section
        sections.append(self._generate_performance_section(manifest))
        
        # Usage examples section
        sections.append(self._generate_usage_examples_section(manifest))
        
        # Troubleshooting section
        sections.append(self._generate_troubleshooting_section(manifest))
        
        # Changelog section
        sections.append(self._generate_changelog_section(manifest))
        
        return sections
    
    def _generate_overview_section(self, manifest: PluginManifest) -> DocumentationSection:
        """Generate overview section"""
        content = f"""
# {manifest.name}

**Version:** {manifest.version}  
**Author:** {manifest.author}  
**License:** {manifest.license.value}  
**Category:** {manifest.category}

## Description

{manifest.description}

## Key Features

- **API Version:** {manifest.api_version.value}
- **Python Version:** {manifest.python_version}
- **Platform:** {', '.join(manifest.platform)}
- **Security Level:** {manifest.security_level}
- **Sandbox Required:** {'Yes' if manifest.sandbox_required else 'No'}
- **Network Access:** {'Yes' if manifest.network_access else 'No'}

## Tags

{', '.join(f'`{tag}`' for tag in manifest.tags)}

## Keywords

{', '.join(f'`{keyword}`' for keyword in manifest.keywords)}
        """
        
        return DocumentationSection("Overview", content.strip())
    
    def _generate_installation_section(self, manifest: PluginManifest) -> DocumentationSection:
        """Generate installation section"""
        content = f"""
## Installation

### Requirements

- Python {manifest.python_version}
- Platform: {', '.join(manifest.platform)}

### Dependencies

"""
        
        if manifest.dependencies:
            content += "#### Python Dependencies\n\n"
            for dep in manifest.dependencies:
                content += f"- **{dep.name}** {dep.version}"
                if dep.optional:
                    content += " (optional)"
                if dep.reason:
                    content += f" - {dep.reason}"
                content += "\n"
        else:
            content += "No external dependencies required.\n"
        
        if manifest.system_dependencies:
            content += "\n#### System Dependencies\n\n"
            for dep in manifest.system_dependencies:
                content += f"- {dep}\n"
        
        content += f"""
### Installation Steps

1. Copy the plugin files to your plugins directory
2. Install dependencies: `pip install {' '.join(dep.name for dep in manifest.dependencies if not dep.optional)}`
3. Configure the plugin (see Configuration section)
4. Enable the plugin in your plugin manager

### File Structure

```
{manifest.name}/
├── {manifest.main_module}
├── plugin.json
├── README.md
├── CHANGELOG.md
└── examples/
    ├── basic_usage.py
    └── advanced_config.py
```
        """
        
        return DocumentationSection("Installation", content.strip())
    
    def _generate_configuration_section(self, manifest: PluginManifest) -> DocumentationSection:
        """Generate configuration section"""
        content = """
## Configuration

### Configuration Options

The plugin supports the following configuration options:

"""
        
        for option in manifest.config_options:
            content += f"#### `{option.name}`\n\n"
            content += f"- **Type:** {option.type}\n"
            content += f"- **Default:** `{option.default}`\n"
            content += f"- **Required:** {'Yes' if option.required else 'No'}\n"
            content += f"- **Description:** {option.description}\n"
            
            if option.validation:
                content += f"- **Validation:** {self._format_validation_rules(option.validation)}\n"
            
            content += "\n"
        
        # Add configuration schema
        content += f"""
### Configuration Schema

```json
{json.dumps(manifest.config_schema, indent=2)}
```

### Example Configuration

```json
{{
"""
        
        for option in manifest.config_options:
            if option.default is not None:
                content += f'  "{option.name}": {json.dumps(option.default)},\n'
        
        content = content.rstrip(',\n') + '\n}\n```\n'
        
        return DocumentationSection("Configuration", content.strip())
    
    def _generate_security_section(self, manifest: PluginManifest) -> DocumentationSection:
        """Generate security section"""
        content = f"""
## Security

### Security Level: {manifest.security_level}

### Permissions Required

The plugin requires the following permissions:

"""
        
        for permission in manifest.permissions:
            content += f"#### `{permission.name}`\n\n"
            content += f"- **Description:** {permission.description}\n"
            content += f"- **Required:** {'Yes' if permission.required else 'No'}\n"
            content += f"- **Risk Level:** {permission.risk_level}\n\n"
        
        content += f"""
### Security Features

- **Sandbox Environment:** {'Enabled' if manifest.sandbox_required else 'Disabled'}
- **Network Access:** {'Allowed' if manifest.network_access else 'Restricted'}
- **File Access:** {', '.join(manifest.file_access) if manifest.file_access else 'None'}

### Resource Limits

- **Maximum Memory:** {manifest.max_memory / 1024 / 1024:.0f} MB
- **Maximum CPU:** {manifest.max_cpu}%
- **Maximum Execution Time:** {manifest.max_execution_time} seconds

### Security Best Practices

1. **Input Validation:** All input data is validated before processing
2. **Output Sanitization:** All output data is sanitized to prevent injection
3. **Error Handling:** Comprehensive error handling prevents information leakage
4. **Logging:** All security-relevant events are logged
5. **Resource Monitoring:** Resource usage is continuously monitored
        """
        
        return DocumentationSection("Security", content.strip())
    
    def _generate_api_section(self, manifest: PluginManifest) -> DocumentationSection:
        """Generate API section"""
        if not manifest.provides_api:
            return DocumentationSection("API", "This plugin does not provide an API.")
        
        content = """
## API Reference

This plugin provides the following API endpoints:

"""
        
        for endpoint in manifest.api_endpoints:
            content += f"### `{endpoint.method} {endpoint.path}`\n\n"
            content += f"**Description:** {endpoint.description}\n\n"
            
            if endpoint.requires_auth:
                content += "**Authentication:** Required\n\n"
            
            if endpoint.parameters:
                content += "**Parameters:**\n\n"
                for param in endpoint.parameters:
                    content += f"- `{param.get('name', 'unknown')}` ({param.get('type', 'unknown')}): {param.get('description', 'No description')}\n"
                content += "\n"
            
            if endpoint.response_schema:
                content += "**Response Schema:**\n\n"
                content += f"```json\n{json.dumps(endpoint.response_schema, indent=2)}\n```\n\n"
            
            content += "**Example Request:**\n\n"
            content += f"```bash\ncurl -X {endpoint.method} http://localhost:5000{endpoint.path}\n```\n\n"
            
            content += "---\n\n"
        
        return DocumentationSection("API Reference", content.strip())
    
    def _generate_performance_section(self, manifest: PluginManifest) -> DocumentationSection:
        """Generate performance section"""
        content = f"""
## Performance

### Resource Usage

- **Memory Limit:** {manifest.max_memory / 1024 / 1024:.0f} MB
- **CPU Limit:** {manifest.max_cpu}%
- **Execution Timeout:** {manifest.max_execution_time} seconds

### Performance Characteristics

- **Startup Time:** Typically < 1 second
- **Response Time:** Target < 100ms
- **Throughput:** Depends on configuration and system resources

### Optimization Tips

1. **Configuration Tuning:** Adjust configuration parameters based on your use case
2. **Resource Monitoring:** Monitor resource usage and adjust limits as needed
3. **Caching:** Enable caching if available to improve response times
4. **Batch Processing:** Use batch operations for better throughput

### Health Monitoring

"""
        
        if manifest.health_check.get('enabled', False):
            content += f"""
The plugin supports health monitoring with the following configuration:

- **Health Check Interval:** {manifest.health_check.get('interval', 60)} seconds
- **Health Check Timeout:** {manifest.health_check.get('timeout', 10)} seconds
- **Health Check Retries:** {manifest.health_check.get('retries', 3)}
- **Health Check Endpoint:** `{manifest.health_check.get('endpoint', 'get_health_status')}`
"""
        else:
            content += "Health monitoring is not enabled for this plugin."
        
        return DocumentationSection("Performance", content.strip())
    
    def _generate_usage_examples_section(self, manifest: PluginManifest) -> DocumentationSection:
        """Generate usage examples section"""
        content = f"""
## Usage Examples

### Basic Usage

```python
from {manifest.name} import {manifest.entry_point}

# Initialize the plugin
plugin = {manifest.entry_point}()

# Configure the plugin
config = {{
    "enabled": True,
    # Add other configuration options
}}

# Execute the plugin
result = plugin.execute(config)
print(result)
```

### Advanced Configuration

```python
from {manifest.name} import {manifest.entry_point}

# Advanced configuration
config = {{
"""
        
        for option in manifest.config_options:
            if option.default is not None:
                content += f'    "{option.name}": {json.dumps(option.default)},  # {option.description}\n'
        
        content += """}}

# Initialize with advanced configuration
plugin = {manifest.entry_point}(config)

# Execute with custom parameters
result = plugin.execute(custom_input_data)
```

### Error Handling

```python
from {manifest.name} import {manifest.entry_point}

try:
    plugin = {manifest.entry_point}()
    result = plugin.execute(config)
    print(f"Success: {result}")
except Exception as e:
    print(f"Error: {e}")
    # Handle error appropriately
```

### Integration Example

```python
# Integration with plugin management system
from plugin_system import PluginManager

manager = PluginManager()
plugin = manager.load_plugin("{manifest.name}")

# Configure and execute
result = plugin.execute({{
    "enabled": True,
    # Add configuration
}})
```
        """
        
        return DocumentationSection("Usage Examples", content.strip())
    
    def _generate_troubleshooting_section(self, manifest: PluginManifest) -> DocumentationSection:
        """Generate troubleshooting section"""
        content = f"""
## Troubleshooting

### Common Issues

#### Plugin Not Loading

**Symptoms:** Plugin fails to load or initialize

**Solutions:**
1. Check that all dependencies are installed
2. Verify the plugin.json manifest is valid
3. Ensure the main module file exists
4. Check file permissions

#### Configuration Errors

**Symptoms:** Plugin fails with configuration-related errors

**Solutions:**
1. Validate configuration against the schema
2. Check that all required configuration options are provided
3. Verify data types match the expected types
4. Review configuration documentation

#### Performance Issues

**Symptoms:** Plugin runs slowly or times out

**Solutions:**
1. Check resource limits (memory: {manifest.max_memory / 1024 / 1024:.0f}MB, CPU: {manifest.max_cpu}%)
2. Monitor system resources
3. Optimize configuration parameters
4. Consider increasing timeout limits

#### Security Warnings

**Symptoms:** Security-related warnings or errors

**Solutions:**
1. Review required permissions
2. Check file access restrictions
3. Verify network access requirements
4. Ensure sandbox environment is properly configured

### Debugging

#### Enable Debug Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Run your plugin code
```

#### Check Plugin Health

```python
from {manifest.name} import get_health_status

health = get_health_status()
print(f"Plugin health: {{health}}")
```

#### Validate Configuration

```python
from {manifest.name} import validate_config

config = {{
    # Your configuration
}}

if validate_config(config):
    print("Configuration is valid")
else:
    print("Configuration is invalid")
```

### Getting Help

- **Documentation:** {manifest.documentation_url if manifest.documentation_url else 'Check plugin README'}
- **Repository:** {manifest.repository if manifest.repository else 'Check plugin repository'}
- **Issues:** Report issues to the plugin repository
- **Contact:** {manifest.email if manifest.email else 'Contact plugin author'}
        """
        
        return DocumentationSection("Troubleshooting", content.strip())
    
    def _generate_changelog_section(self, manifest: PluginManifest) -> DocumentationSection:
        """Generate changelog section"""
        content = f"""
## Changelog

### Version {manifest.version}

- Current version
- See {manifest.changelog if manifest.changelog else 'CHANGELOG.md'} for detailed changes

### Version History

To see the complete version history and detailed changes, please refer to the {manifest.changelog if manifest.changelog else 'CHANGELOG.md'} file in the plugin directory.

### Upgrade Notes

When upgrading from previous versions:

1. **Backup Configuration:** Always backup your current configuration
2. **Review Changes:** Check the changelog for breaking changes
3. **Test Configuration:** Validate your configuration against the new schema
4. **Monitor Performance:** Monitor plugin performance after upgrade
        """
        
        return DocumentationSection("Changelog", content.strip())
    
    def _generate_html_documentation(self, sections: List[DocumentationSection], 
                                   manifest: PluginManifest) -> str:
        """Generate HTML documentation"""
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{manifest.name} Documentation</title>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; margin: 40px; }}
        .header {{ background: #f4f4f4; padding: 20px; border-radius: 5px; margin-bottom: 30px; }}
        .toc {{ background: #f9f9f9; padding: 15px; border-radius: 5px; margin-bottom: 30px; }}
        .toc ul {{ margin: 0; padding-left: 20px; }}
        .section {{ margin-bottom: 30px; }}
        .section h2 {{ color: #333; border-bottom: 2px solid #333; padding-bottom: 5px; }}
        .section h3 {{ color: #666; }}
        .section h4 {{ color: #888; }}
        code {{ background: #f4f4f4; padding: 2px 4px; border-radius: 3px; }}
        pre {{ background: #f4f4f4; padding: 10px; border-radius: 5px; overflow-x: auto; }}
        .metadata {{ display: flex; flex-wrap: wrap; gap: 10px; }}
        .metadata-item {{ background: #e9e9e9; padding: 5px 10px; border-radius: 3px; }}
        .security-level {{ padding: 5px 10px; border-radius: 3px; color: white; }}
        .security-low {{ background: #4CAF50; }}
        .security-medium {{ background: #FF9800; }}
        .security-high {{ background: #F44336; }}
        .security-critical {{ background: #9C27B0; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{manifest.name} Documentation</h1>
        <div class="metadata">
            <div class="metadata-item">Version: {manifest.version}</div>
            <div class="metadata-item">Author: {manifest.author}</div>
            <div class="metadata-item">License: {manifest.license.value}</div>
            <div class="metadata-item">Category: {manifest.category}</div>
            <div class="security-level security-{manifest.security_level.lower()}">
                Security: {manifest.security_level}
            </div>
        </div>
    </div>
    
    <div class="toc">
        <h2>Table of Contents</h2>
        <ul>
"""
        
        for section in sections:
            html_content += f'            <li><a href="#{section.anchor}">{section.title}</a></li>\n'
        
        html_content += """        </ul>
    </div>
"""
        
        for section in sections:
            html_content += f"""
    <div class="section" id="{section.anchor}">
        {self._markdown_to_html(section.content)}
    </div>
"""
        
        html_content += f"""
    <footer style="margin-top: 50px; padding-top: 20px; border-top: 1px solid #ccc; color: #666;">
        <p>Documentation generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>Plugin: {manifest.name} v{manifest.version}</p>
    </footer>
</body>
</html>
"""
        
        return html_content
    
    def _generate_markdown_documentation(self, sections: List[DocumentationSection], 
                                       manifest: PluginManifest) -> str:
        """Generate Markdown documentation"""
        markdown_content = f"# {manifest.name} Documentation\n\n"
        
        # Add metadata
        markdown_content += f"**Version:** {manifest.version}  \n"
        markdown_content += f"**Author:** {manifest.author}  \n"
        markdown_content += f"**License:** {manifest.license.value}  \n"
        markdown_content += f"**Category:** {manifest.category}  \n"
        markdown_content += f"**Security Level:** {manifest.security_level}  \n\n"
        
        # Add table of contents
        markdown_content += "## Table of Contents\n\n"
        for section in sections:
            markdown_content += f"- [{section.title}](#{section.anchor})\n"
        markdown_content += "\n"
        
        # Add sections
        for section in sections:
            markdown_content += f"{section.content}\n\n"
        
        # Add footer
        markdown_content += "---\n\n"
        markdown_content += f"*Documentation generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*  \n"
        markdown_content += f"*Plugin: {manifest.name} v{manifest.version}*\n"
        
        return markdown_content
    
    def _generate_json_documentation(self, sections: List[DocumentationSection], 
                                   manifest: PluginManifest) -> str:
        """Generate JSON documentation"""
        json_doc = {
            "plugin": {
                "name": manifest.name,
                "version": manifest.version,
                "author": manifest.author,
                "license": manifest.license.value,
                "category": manifest.category,
                "security_level": manifest.security_level,
                "description": manifest.description
            },
            "sections": [
                {
                    "title": section.title,
                    "content": section.content,
                    "anchor": section.anchor
                }
                for section in sections
            ],
            "generated_at": datetime.now().isoformat()
        }
        
        return json.dumps(json_doc, indent=2)
    
    def _generate_api_documentation(self, manifest: PluginManifest) -> str:
        """Generate OpenAPI specification"""
        if not manifest.provides_api:
            return "{}"
        
        openapi_spec = {
            "openapi": "3.0.0",
            "info": {
                "title": f"{manifest.name} API",
                "version": manifest.version,
                "description": manifest.description,
                "contact": {
                    "name": manifest.author,
                    "email": manifest.email
                },
                "license": {
                    "name": manifest.license.value
                }
            },
            "paths": {}
        }
        
        for endpoint in manifest.api_endpoints:
            path = endpoint.path
            method = endpoint.method.lower()
            
            if path not in openapi_spec["paths"]:
                openapi_spec["paths"][path] = {}
            
            openapi_spec["paths"][path][method] = {
                "summary": endpoint.description,
                "description": endpoint.description,
                "parameters": endpoint.parameters,
                "responses": {
                    "200": {
                        "description": "Success",
                        "content": {
                            "application/json": {
                                "schema": endpoint.response_schema
                            }
                        }
                    }
                }
            }
            
            if endpoint.requires_auth:
                openapi_spec["paths"][path][method]["security"] = [{"bearerAuth": []}]
        
        return json.dumps(openapi_spec, indent=2)
    
    def _format_validation_rules(self, validation: Dict[str, Any]) -> str:
        """Format validation rules for display"""
        rules = []
        for key, value in validation.items():
            if key == "type":
                continue
            rules.append(f"{key}: {value}")
        return ", ".join(rules) if rules else "None"
    
    def _markdown_to_html(self, markdown: str) -> str:
        """Convert markdown to HTML (basic implementation)"""
        # This is a simplified markdown to HTML converter
        # In production, you'd use a proper markdown library
        html = markdown
        
        # Headers
        html = re.sub(r'^# (.*)', r'<h1>\1</h1>', html, flags=re.MULTILINE)
        html = re.sub(r'^## (.*)', r'<h2>\1</h2>', html, flags=re.MULTILINE)
        html = re.sub(r'^### (.*)', r'<h3>\1</h3>', html, flags=re.MULTILINE)
        html = re.sub(r'^#### (.*)', r'<h4>\1</h4>', html, flags=re.MULTILINE)
        
        # Code blocks
        html = re.sub(r'```(\w+)?\n(.*?)\n```', r'<pre><code>\2</code></pre>', html, flags=re.DOTALL)
        
        # Inline code
        html = re.sub(r'`([^`]+)`', r'<code>\1</code>', html)
        
        # Bold
        html = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html)
        
        # Lists
        html = re.sub(r'^\- (.*)', r'<li>\1</li>', html, flags=re.MULTILINE)
        html = re.sub(r'(<li>.*</li>)', r'<ul>\1</ul>', html, flags=re.DOTALL)
        
        # Paragraphs
        html = re.sub(r'\n\n', '</p><p>', html)
        html = f'<p>{html}</p>'
        
        return html
    
    def _load_html_template(self) -> str:
        """Load HTML template"""
        return ""  # Template loaded above
    
    def _load_markdown_template(self) -> str:
        """Load Markdown template"""
        return ""  # Template loaded above
    
    def generate_all_plugin_documentation(self) -> Dict[str, Dict[str, str]]:
        """Generate documentation for all plugins"""
        all_docs = {}
        
        if not os.path.exists(self.plugin_dir):
            self.logger.warning(f"Plugin directory not found: {self.plugin_dir}")
            return all_docs
        
        for plugin_name in os.listdir(self.plugin_dir):
            plugin_path = os.path.join(self.plugin_dir, plugin_name)
            
            if os.path.isdir(plugin_path):
                try:
                    docs = self.generate_plugin_documentation(plugin_name)
                    all_docs[plugin_name] = docs
                    self.logger.info(f"Generated documentation for {plugin_name}")
                except Exception as e:
                    self.logger.error(f"Failed to generate documentation for {plugin_name}: {e}")
        
        return all_docs
    
    def save_documentation(self, plugin_name: str, documentation: Dict[str, str], 
                          output_dir: str = "docs") -> None:
        """Save documentation to files"""
        os.makedirs(output_dir, exist_ok=True)
        
        # Save HTML documentation
        html_path = os.path.join(output_dir, f"{plugin_name}.html")
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(documentation["html"])
        
        # Save Markdown documentation
        md_path = os.path.join(output_dir, f"{plugin_name}.md")
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(documentation["markdown"])
        
        # Save JSON documentation
        json_path = os.path.join(output_dir, f"{plugin_name}.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            f.write(documentation["json"])
        
        # Save API documentation
        api_path = os.path.join(output_dir, f"{plugin_name}_api.json")
        with open(api_path, 'w', encoding='utf-8') as f:
            f.write(documentation["api"])
        
        self.logger.info(f"Documentation saved for {plugin_name} in {output_dir}")

def main():
    """Main function for testing the documentation generator"""
    try:
        # Initialize documentation generator
        doc_generator = PluginDocumentationGenerator()
        
        # Generate documentation for all plugins
        all_docs = doc_generator.generate_all_plugin_documentation()
        
        print(f"Generated documentation for {len(all_docs)} plugins")
        
        # Save documentation
        for plugin_name, docs in all_docs.items():
            doc_generator.save_documentation(plugin_name, docs)
            print(f"Saved documentation for {plugin_name}")
        
        print("Documentation generation completed successfully!")
        
    except Exception as e:
        print(f"Error generating documentation: {e}")
        logger.error(f"Documentation generation error: {e}")

if __name__ == "__main__":
    main()
