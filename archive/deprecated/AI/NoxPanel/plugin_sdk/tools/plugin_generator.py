#!/usr/bin/env python3
"""
NoxPanel Plugin Generator
Generates new plugin projects from templates
"""

import os
import json
import argparse
from pathlib import Path
import shutil

def generate_plugin(name: str, category: str, author: str, description: str):
    """Generate a new plugin from template"""
    try:
        print(f"🔧 Generating plugin: {name}")

        # Create plugin directory
        plugin_dir = Path(f"./plugins/{name}")
        plugin_dir.mkdir(parents=True, exist_ok=True)

        # Load template
        template_path = Path("../templates/python_plugin_template.py")
        with open(template_path, 'r') as f:
            template_content = f.read()

        # Replace placeholders
        plugin_content = template_content.format(
            plugin_name=name,
            version="1.0.0",
            author=author,
            description=description,
            category=category,
            plugin_class=f"{name.replace('_', '').title()}Plugin",
            plugin_description=description
        )

        # Save plugin file
        plugin_file = plugin_dir / f"{name}.py"
        with open(plugin_file, 'w') as f:
            f.write(plugin_content)

        # Create plugin manifest
        manifest = {
            "name": name,
            "version": "1.0.0",
            "author": author,
            "description": description,
            "category": category,
            "entry_point": f"{name}.py",
            "permissions": ["read", "write"],
            "dependencies": []
        }

        manifest_file = plugin_dir / "manifest.json"
        with open(manifest_file, 'w') as f:
            json.dump(manifest, f, indent=2)

        print(f"✅ Plugin generated successfully: {plugin_dir}")

    except Exception as e:
        print(f"❌ Plugin generation failed: {str(e)}")
        raise

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate NoxPanel plugin")
    parser.add_argument("name", help="Plugin name")
    parser.add_argument("--category", default="Utilities", help="Plugin category")
    parser.add_argument("--author", default="Developer", help="Plugin author")
    parser.add_argument("--description", default="A NoxPanel plugin", help="Plugin description")

    args = parser.parse_args()
    generate_plugin(args.name, args.category, args.author, args.description)
