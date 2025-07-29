import os
import shutil
import glob
import json
import time
from pathlib import Path
from tqdm import tqdm
from NoxPanel.noxcore.utils.logging_config import get_logger
from typing import Dict, List, Optional, Any, Union
logger = get_logger(__name__)


BACKUP_DIR = f"backup_{time.strftime('%Y%m%d_%H%M%S')}"
LOG_FILE = f"cleanup_log_{time.strftime('%Y%m%d_%H%M%S')}.txt"
TODO_FILE = f"cleanup_todo_{time.strftime('%Y%m%d_%H%M%S')}.md"
ROLLBACK_FILE = f"rollback_{time.strftime('%Y%m%d_%H%M%S')}.py"

DELETE_TARGETS = [
    ".pytest_cache",
    "*.rlvr_backup",
    "scripts/port_mapper.py",
    "scripts/frontend_backend_integrator.py",
    "validate_optimization.py",
    "app.py",
    "ultimate_suite_enhanced_v10.py",
    "rlvr_phase3_advanced_enhancer_fixed.py"
]
KEEP_PATHS = [
    "config/heimnetz_unified.json",
    "README.md",
    "requirements.txt"
]

MIGRATION_TASKS = [
    "Compare legacy_fritz_api.py logic and migrate to fritzwatcher_plugin.py",
    "Merge test_server.py dev/test logic into current test suite",
    "Integrate api_bridge.py routes into unified backend",
    "Migrate legacy .js features to .jsx/.ts",
    "Consolidate implementation_status_analyzer.py logic",
    "Archive superseded docs to /archive/deprecated/",
    "Validate all deletions with dry-run capability",
    "Update documentation references after cleanup"
]

AGENT_TASKS = [
    "Configure Supaermaven for code analysis orchestration",
    "Set up Langflow for dependency visualization",
    "Implement shared context pool in agents/",
    "Enable public changelog logging",
    "Validate migration completeness"
]

def write_log(message) -> bool:
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(message + "\n")
    logger.info(message)

def is_protected(path) -> bool:
    for keep in KEEP_PATHS:
        if Path(keep).resolve() == Path(path).resolve():
            return True
    return False

def backup_and_delete(path) -> bool:
    backup_path = os.path.join(BACKUP_DIR, os.path.relpath(path, start=os.getcwd()))
    os.makedirs(os.path.dirname(backup_path), exist_ok=True)
    try:
        if os.path.isdir(path):
            shutil.copytree(path, backup_path)
            shutil.rmtree(path)
        else:
            shutil.copy2(path, backup_path)
            os.remove(path)
        write_log(f"✅ Deleted and backed up: {path}")
        return True
    except Exception as e:
        write_log(f"❌ Failed to delete: {path} - Error: {e}")
        return False

def find_targets() -> bool:
    items = []
    for target in DELETE_TARGETS:
        if "*" in target:
            items.extend(glob.glob(target, recursive=True))
        else:
            if os.path.exists(target):
                items.append(target)
    return items

def cleanup_diagnostics() -> bool:
    diag_files = []
    for root, dirs, files in os.walk('.'):
        for file in files:
            if any(x in file for x in ["diagnostic", "debug", "temp", "log"]):
                if not any(x in root for x in ["node_modules", "essential", "config"]):
                    diag_files.append(os.path.join(root, file))
    return diag_files

def generate_todo(deleted, skipped) -> bool:
    lines = [
        "# Project Cleanup TODO Checklist",
        f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## Migration Tasks"
    ]
    for task in MIGRATION_TASKS:
        lines.append(f"- [ ] {task}")
    lines.append("")
    lines.append("## Agent Coordination Tasks")
    for task in AGENT_TASKS:
        lines.append(f"- [ ] {task}")
    lines.append("")
    lines.append("## Cleanup Summary")
    lines.append(f"- Files deleted: {len(deleted)}")
    lines.append(f"- Files skipped (protected): {len(skipped)}")
    with open(TODO_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    write_log(f"📝 TODO checklist generated: {TODO_FILE}")

def generate_rollback() -> bool:
    lines = [
        "import shutil, os",
        f"BACKUP_DIR = '{BACKUP_DIR}'",
        "for root, dirs, files in os.walk(BACKUP_DIR):",
        "    for file in files:",
        "        src = os.path.join(root, file)",
        "        dst = os.path.relpath(src, BACKUP_DIR)",
        "        os.makedirs(os.path.dirname(dst), exist_ok=True)",
        "        shutil.copy2(src, dst)",
logger.info('Rollback completed.')
    ]
    with open(ROLLBACK_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    write_log(f"🔄 Rollback script generated: {ROLLBACK_FILE}")

def main() -> bool:
    logger.info("\n=== PROJECT CLEANUP MIGRATION ===\n")
    logger.info(f"Backup directory: {BACKUP_DIR}")
    logger.info(f"Log file: {LOG_FILE}")
    logger.info("\nScanning for targets...")
    targets = find_targets()
    diagnostics = cleanup_diagnostics()
    deleted = []
    skipped = []
    logger.info(f"Found {len(targets)} cleanup targets and {len(diagnostics)} diagnostic files.")
    confirm = input("Proceed with deletion and backup? (y/N): ").strip().lower()
    if confirm != 'y':
        logger.info("Aborted by user.")
        return
    os.makedirs(BACKUP_DIR, exist_ok=True)
    logger.info("\nDeleting and backing up files:")
    for path in tqdm(targets + diagnostics, desc="Cleanup Progress"):
        if is_protected(path):
            write_log(f"🛡️  PROTECTED: Skipping {path} (in KEEP list)")
            skipped.append(path)
            continue
        if backup_and_delete(path):
            deleted.append(path)
        else:
            skipped.append(path)
    generate_todo(deleted, skipped)
    generate_rollback()
    logger.info("\nCleanup complete. See log and TODO checklist for details.")

if __name__ == "__main__":
    main()
