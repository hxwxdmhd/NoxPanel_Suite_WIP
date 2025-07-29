# 🚀 NoxPanel Suite API Documentation

## Overview

The NoxPanel Suite provides a comprehensive REST API for network management, monitoring, and automation. This API follows RESTful principles and provides JSON responses.

## Authentication

All API endpoints require authentication. Include your API token in the header:

```
Authorization: Bearer <your-api-token>
```

## Base URL

```
https://your-noxpanel-instance/api/
```

## Error Handling

The API uses standard HTTP status codes and returns error details in JSON format:

```json
{
  "success": false,
  "error": "Error description",
  "error_code": "ERROR_CODE",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

## Rate Limiting

API requests are limited to:
- 1000 requests per hour for authenticated users
- 100 requests per hour for unauthenticated requests

## API Endpoints


### General API

#### GET `/`

**Function:** `index`

**Description:** Main dashboard with embedded HTML

**Example Response:**
```json
{
  "success": true,
  "data": {},
  "timestamp": "2024-01-01T00:00:00Z"
}
```

---

#### GET `/status`

**Function:** `status_page`

**Description:** Detailed status page

**Example Response:**
```json
{
  "success": true,
  "data": {},
  "timestamp": "2024-01-01T00:00:00Z"
}
```

---

#### GET `/crawler`

**Function:** `crawler_page`

**Description:** NoxCrawler web interface

**Example Response:**
```json
{
  "success": true,
  "data": {},
  "timestamp": "2024-01-01T00:00:00Z"
}
```

---

#### GET `/plugins`

**Function:** `plugins_page`

**Description:** Git Plugin System interface

**Example Response:**
```json
{
  "success": true,
  "data": {},
  "timestamp": "2024-01-01T00:00:00Z"
}
```

---


### Health API

#### GET `/api/health`

**Function:** `health_check`

**Description:** Health check endpoint
return jsonify({
"status": "healthy",
"timestamp": datetime.now().isoformat(),
"version": "5.0.2",
"mode": "simplified_functional"
})

@app.route('/api/test')
def test_endpoint():

**Example Response:**
```json
{
  "success": true,
  "data": {},
  "timestamp": "2024-01-01T00:00:00Z"
}
```

---


### Test API

#### GET `/api/test`

**Function:** `test_endpoint`

**Description:** Test API endpoint
return jsonify({
"message": "API is working correctly",
"timestamp": datetime.now().isoformat(),
"endpoints": [
"/api/health",
"/api/test",
"/api/crawler/crawl",
"/api/crawler/data",
"/api/plugins/status",
"/api/plugins/available",

**Example Response:**
```json
{
  "success": true,
  "data": {},
  "timestamp": "2024-01-01T00:00:00Z"
}
```

---


### Crawler API

#### POST `/api/crawler/crawl`

**Function:** `api_crawler_crawl`

**Description:** Start a web crawl
try:
data = request.get_json()
url = data.get('url')
depth = data.get('depth', 1)

if not url:
return jsonify({"success": False, "error": "URL is required"}), 400

# Import and use NoxCrawler
try:
from noxcrawler import NoxCrawler
crawler = NoxCrawler()
results = crawler.crawl_url(url, max_depth=depth)
return jsonify({"success": True, "results": results})
except Exception as e:
return jsonify({"success": False, "error": str(e)}), 500
except Exception as e:
return jsonify({"success": False, "error": str(e)}), 500

**Example Request:**
```bash
curl -X POST \
  /api/crawler/crawl \
  -H 'Authorization: Bearer <token>' \
  -H 'Content-Type: application/json' \
  -d '{}'
```

**Example Response:**
```json
{
  "success": true,
  "data": {},
  "timestamp": "2024-01-01T00:00:00Z"
}
```

---

#### GET `/api/crawler/data`

**Function:** `api_crawler_data`

**Description:** Get stored crawler data

**Example Response:**
```json
{
  "success": true,
  "data": {},
  "timestamp": "2024-01-01T00:00:00Z"
}
```

---


### Plugins API

#### POST `/api/plugins/install`

**Function:** `api_plugins_install`

**Description:** Install a plugin
try:
data = request.get_json()
plugin_name = data.get('plugin_name')

if not plugin_name:
return jsonify({"success": False, "error": "Plugin name is required"}), 400

# Plugin installation logic would go here
return jsonify({"success": True, "message": f"Plugin {plugin_name} installed"})
except Exception as e:
return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/plugins/uninstall', methods=['POST'])
def api_plugins_uninstall():

**Example Request:**
```bash
curl -X POST \
  /api/plugins/install \
  -H 'Authorization: Bearer <token>' \
  -H 'Content-Type: application/json' \
  -d '{}'
```

**Example Response:**
```json
{
  "success": true,
  "data": {},
  "timestamp": "2024-01-01T00:00:00Z"
}
```

---

#### POST `/api/plugins/uninstall`

**Function:** `api_plugins_uninstall`

**Description:** Uninstall a plugin
try:
data = request.get_json()
plugin_name = data.get('plugin_name')

if not plugin_name:
return jsonify({"success": False, "error": "Plugin name is required"}), 400

# Plugin uninstallation logic would go here
return jsonify({"success": True, "message": f"Plugin {plugin_name} uninstalled"})
except Exception as e:
return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/plugins/load', methods=['POST'])
def api_plugins_load():

**Example Request:**
```bash
curl -X POST \
  /api/plugins/uninstall \
  -H 'Authorization: Bearer <token>' \
  -H 'Content-Type: application/json' \
  -d '{}'
```

**Example Response:**
```json
{
  "success": true,
  "data": {},
  "timestamp": "2024-01-01T00:00:00Z"
}
```

---

#### POST `/api/plugins/load`

**Function:** `api_plugins_load`

**Description:** Load/activate a plugin

RLVR: Implements api_plugins_load with error handling and validation

REASONING CHAIN:
1. Problem: Input parameters and business logic for api_plugins_load
2. Analysis: Function complexity 1.8/5.0
3. Solution: Implements api_plugins_load with error handling and validation
4. Implementation: Chain-of-Thought validation with error handling
5. Validation: 3 test cases covering edge cases

COMPLIANCE: STANDARD

**Example Request:**
```bash
curl -X POST \
  /api/plugins/load \
  -H 'Authorization: Bearer <token>' \
  -H 'Content-Type: application/json' \
  -d '{}'
```

**Example Response:**
```json
{
  "success": true,
  "data": {},
  "timestamp": "2024-01-01T00:00:00Z"
}
```

---

#### GET `/api/plugins/status`

**Function:** `api_plugins_status`

**Description:** Get plugin system status
try:
# Try to import the plugin manager
try:
from git_plugin_system import GitPluginManager
manager = GitPluginManager()

return jsonify({
"status": "active",
"plugins_dir": str(manager.plugins_dir),
"available_count": len(manager.plugin_configs),
"loaded_count": len(manager.loaded_plugins)
})
except ImportError:
return jsonify({
"status": "ready",
"plugins_dir": "external_plugins",
"available_count": 0,
"loaded_count": 0,
"note": "Git plugin system ready for configuration"

**Example Response:**
```json
{
  "success": true,
  "data": {},
  "timestamp": "2024-01-01T00:00:00Z"
}
```

---

#### GET `/api/plugins/available`

**Function:** `api_plugins_available`

**Description:** Get available plugins
try:
try:
from git_plugin_system import GitPluginManager
manager = GitPluginManager()

plugins = []
for name, config in manager.plugin_configs.items():
plugin_info = {
"name": name,
"repo": config.get("repo", ""),
"type": config.get("type", "unknown"),
"description": config.get("description", ""),
"installed": manager.is_plugin_installed(name)
}
plugins.append(plugin_info)

return jsonify(plugins)
except ImportError:
# Return demo data when plugin system not available

**Example Response:**
```json
{
  "success": true,
  "data": {},
  "timestamp": "2024-01-01T00:00:00Z"
}
```

---

#### GET `/api/plugins/loaded`

**Function:** `api_plugins_loaded`

**Description:** Get loaded plugins
try:
try:
from git_plugin_system import GitPluginManager
manager = GitPluginManager()
return jsonify(manager.loaded_plugins)
except ImportError:
return jsonify({})

except Exception as e:
logger.error(f"Loaded plugins error: {e}")
return jsonify({"error": str(e)}), 500

@app.route('/api/plugins/add', methods=['POST'])
def api_plugins_add():

**Example Response:**
```json
{
  "success": true,
  "data": {},
  "timestamp": "2024-01-01T00:00:00Z"
}
```

---

#### POST `/api/plugins/add`

**Function:** `api_plugins_add`

**Description:** Add a new plugin configuration
try:
data = request.get_json()

required_fields = ['name', 'repo', 'type']
for field in required_fields:
if not data.get(field):
return jsonify({"success": False, "error": f"Field '{field}' is required"}), 400

try:
from git_plugin_system import GitPluginManager
manager = GitPluginManager()

# Add plugin configuration
manager.add_plugin_config(
name=data['name'],
repo_url=data['repo'],
plugin_type=data['type'],
description=data.get('description', '')
)

**Example Request:**
```bash
curl -X POST \
  /api/plugins/add \
  -H 'Authorization: Bearer <token>' \
  -H 'Content-Type: application/json' \
  -d '{}'
```

**Example Response:**
```json
{
  "success": true,
  "data": {},
  "timestamp": "2024-01-01T00:00:00Z"
}
```

---

#### POST `/api/plugins/install/<plugin_name>`

**Function:** `api_plugins_install`

**Description:** Install a plugin
try:
try:
from git_plugin_system import GitPluginManager
manager = GitPluginManager()

result = manager.install_plugin(plugin_name)
if result:
return jsonify({"success": True, "message": f"Plugin '{plugin_name}' installed successfully"})
else:
return jsonify({"success": False, "error": "Installation failed"})

except ImportError:
return jsonify({"success": False, "error": "Git plugin system not available"})

except Exception as e:
logger.error(f"Install plugin error: {e}")
return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/plugins/uninstall/<plugin_name>', methods=['POST'])

**Example Request:**
```bash
curl -X POST \
  /api/plugins/install/<plugin_name> \
  -H 'Authorization: Bearer <token>' \
  -H 'Content-Type: application/json' \
  -d '{}'
```

**Example Response:**
```json
{
  "success": true,
  "data": {},
  "timestamp": "2024-01-01T00:00:00Z"
}
```

---

#### POST `/api/plugins/uninstall/<plugin_name>`

**Function:** `api_plugins_uninstall`

**Description:** Uninstall a plugin
try:
try:
from git_plugin_system import GitPluginManager
manager = GitPluginManager()

result = manager.uninstall_plugin(plugin_name)
if result:
return jsonify({"success": True, "message": f"Plugin '{plugin_name}' uninstalled successfully"})
else:
return jsonify({"success": False, "error": "Uninstallation failed"})

except ImportError:
return jsonify({"success": False, "error": "Git plugin system not available"})

except Exception as e:
logger.error(f"Uninstall plugin error: {e}")
return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/plugins/load/<plugin_name>', methods=['POST'])

**Example Request:**
```bash
curl -X POST \
  /api/plugins/uninstall/<plugin_name> \
  -H 'Authorization: Bearer <token>' \
  -H 'Content-Type: application/json' \
  -d '{}'
```

**Example Response:**
```json
{
  "success": true,
  "data": {},
  "timestamp": "2024-01-01T00:00:00Z"
}
```

---

#### POST `/api/plugins/load/<plugin_name>`

**Function:** `api_plugins_load`

**Description:** Load a plugin
try:
try:
from git_plugin_system import GitPluginManager
manager = GitPluginManager()

result = manager.load_plugin(plugin_name)
if result:
return jsonify({"success": True, "message": f"Plugin '{plugin_name}' loaded successfully"})
else:
return jsonify({"success": False, "error": "Loading failed"})

except ImportError:
return jsonify({"success": False, "error": "Git plugin system not available"})

except Exception as e:
logger.error(f"Load plugin error: {e}")
return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/plugins/unload/<plugin_name>', methods=['POST'])

**Example Request:**
```bash
curl -X POST \
  /api/plugins/load/<plugin_name> \
  -H 'Authorization: Bearer <token>' \
  -H 'Content-Type: application/json' \
  -d '{}'
```

**Example Response:**
```json
{
  "success": true,
  "data": {},
  "timestamp": "2024-01-01T00:00:00Z"
}
```

---

#### POST `/api/plugins/unload/<plugin_name>`

**Function:** `api_plugins_unload`

**Description:** Unload a plugin
try:
try:
from git_plugin_system import GitPluginManager

# Security: Input validation utilities
import re
import html
from typing import Any, Optional

def validate_input(value: Any, pattern: str = None, max_length: int = 1000) -> str:

**Example Request:**
```bash
curl -X POST \
  /api/plugins/unload/<plugin_name> \
  -H 'Authorization: Bearer <token>' \
  -H 'Content-Type: application/json' \
  -d '{}'
```

**Example Response:**
```json
{
  "success": true,
  "data": {},
  "timestamp": "2024-01-01T00:00:00Z"
}
```

---

