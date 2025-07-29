#!/usr/bin/env python3
"""
NoxPanel Main Entry Point
Unified entry point for different NoxPanel modes
"""

import argparse
import sys
from pathlib import Path


def main():
    """Main entry point for NoxPanel."""
    parser = argparse.ArgumentParser(description="NoxPanel Suite")
    parser.add_argument("--web", action="store_true", help="Start web interface")
    parser.add_argument("--install", action="store_true", help="Run installation")
    parser.add_argument("--validate", action="store_true", help="Validate installation")
    parser.add_argument(
        "--port", type=int, default=5000, help="Port for web interface (default: 5000)"
    )
    parser.add_argument(
        "--host", default="0.0.0.0", help="Host for web interface (default: 0.0.0.0)"
    )

    args = parser.parse_args()

    # Set up path
    project_root = Path(__file__).parent
    sys.path.insert(0, str(project_root))

    if args.web:
        print("🌐 Starting NoxPanel web interface...")
        try:
            from AI.NoxPanel.test_server_optimized import app

            app.run(host=args.host, port=args.port, debug=True)
        except ImportError as e:
            print(f"❌ Failed to import web app: {e}")
            return 1

    elif args.install:
        print("📦 Running NoxPanel installation...")
        try:
            import install

            return install.main()
        except ImportError as e:
            print(f"❌ Failed to import installer: {e}")
            return 1

    elif args.validate:
        print("✅ Validating NoxPanel installation...")
        try:
            import validate_installation

            return validate_installation.main()
        except ImportError as e:
            print(f"❌ Failed to import validator: {e}")
            return 1

    else:
        print("NoxPanel Suite")
        print("Available commands:")
        print("  --web      Start web interface")
        print("  --install  Run installation")
        print("  --validate Validate installation")
        print("")
        print("For more options, see:")
        print("  python install.py --help")
        print("  python start_noxpanel.py")
        print("  python validate_installation.py --help")
        return 0


if __name__ == "__main__":
    sys.exit(main())
