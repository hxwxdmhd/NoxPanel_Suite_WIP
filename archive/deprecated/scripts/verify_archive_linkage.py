#!/usr/bin/env python3
"""
Archive Linkage Verification System
Verifies external archive accessibility and integrity

Usage:
    python scripts/verify_archive_linkage.py
    
Returns:
    - Archive integrity status
    - File counts per category
    - Accessibility verification
"""

import os
from pathlib import Path
import sys
from datetime import datetime

ARCHIVE_PATH = "K:\\Projects_Archives\\Project_Heimnetz"
ARCHIVE_CATEGORIES = {
    "rlvr_backups": "RLVR backup files",
    "versioned_legacy": "Version-numbered legacy files", 
    "deprecated_modules": "Superseded Python modules",
    "documentation": "Archived reports and docs"
}

def verify_archive_integrity():
    """Verify archive location and structure exist"""
    print(f"🔍 Verifying archive integrity...")
    print(f"Archive Path: {ARCHIVE_PATH}")
    
    if not os.path.exists(ARCHIVE_PATH):
        return False, f"❌ Archive path not accessible: {ARCHIVE_PATH}"
    
    print(f"✅ Archive path accessible")
    
    missing_categories = []
    category_status = {}
    
    for category, description in ARCHIVE_CATEGORIES.items():
        category_path = os.path.join(ARCHIVE_PATH, category)
        if os.path.exists(category_path):
            file_count = len([f for f in Path(category_path).glob("*") if f.is_file()])
            category_status[category] = {"status": "✅", "count": file_count, "description": description}
            print(f"  ✅ {category}: {file_count} files ({description})")
        else:
            category_status[category] = {"status": "❌", "count": 0, "description": description}
            missing_categories.append(category)
            print(f"  ❌ {category}: Missing directory")
    
    if missing_categories:
        return False, f"Missing archive categories: {missing_categories}", category_status
    
    total_files = sum([cat["count"] for cat in category_status.values()])
    return True, f"✅ Archive integrity verified - {total_files} files archived", category_status

def get_archived_file_location(filename):
    """Get archive location for a specific file"""
    print(f"🔍 Searching for archived file: {filename}")
    
    for category in ARCHIVE_CATEGORIES:
        category_path = os.path.join(ARCHIVE_PATH, category)
        if os.path.exists(category_path):
            file_path = os.path.join(category_path, filename)
            if os.path.exists(file_path):
                print(f"  ✅ Found in {category}: {file_path}")
                return file_path
    
    print(f"  ❌ File not found in archive: {filename}")
    return None

def list_archived_files(category=None):
    """List files in archive category"""
    if category and category in ARCHIVE_CATEGORIES:
        category_path = os.path.join(ARCHIVE_PATH, category)
        if os.path.exists(category_path):
            files = [f.name for f in Path(category_path).glob("*") if f.is_file()]
            print(f"📁 {category} ({len(files)} files):")
            for file in sorted(files)[:10]:  # Show first 10 files
                print(f"  - {file}")
            if len(files) > 10:
                print(f"  ... and {len(files) - 10} more files")
            return files
        else:
            print(f"❌ Category not found: {category}")
            return []
    else:
        all_files = {}
        print(f"📁 All archived files:")
        for cat, desc in ARCHIVE_CATEGORIES.items():
            cat_path = os.path.join(ARCHIVE_PATH, cat)
            if os.path.exists(cat_path):
                files = [f.name for f in Path(cat_path).glob("*") if f.is_file()]
                all_files[cat] = files
                print(f"  {cat}: {len(files)} files ({desc})")
            else:
                all_files[cat] = []
                print(f"  {cat}: 0 files (directory missing)")
        return all_files

def generate_archive_report():
    """Generate comprehensive archive status report"""
    print(f"📊 Generating Archive Status Report...")
    print(f"=" * 50)
    print(f"Archive Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"=" * 50)
    
    success, message, status = verify_archive_integrity()
    
    if success:
        print(f"\n🎯 ARCHIVE STATUS: {message}")
        
        total_files = 0
        total_size = 0
        
        for category, info in status.items():
            if info["count"] > 0:
                category_path = os.path.join(ARCHIVE_PATH, category)
                try:
                    # Calculate directory size
                    size = sum(f.stat().st_size for f in Path(category_path).glob("**/*") if f.is_file())
                    size_mb = size / (1024 * 1024)
                    total_size += size
                    total_files += info["count"]
                    
                    print(f"\n📁 {category.upper()}:")
                    print(f"   Description: {info['description']}")
                    print(f"   Files: {info['count']}")
                    print(f"   Size: {size_mb:.2f} MB")
                    print(f"   Path: {category_path}")
                except Exception as e:
                    print(f"   Error calculating size: {e}")
        
        total_size_mb = total_size / (1024 * 1024)
        print(f"\n📊 SUMMARY:")
        print(f"   Total Files Archived: {total_files}")
        print(f"   Total Archive Size: {total_size_mb:.2f} MB")
        print(f"   Archive Categories: {len([c for c in status.values() if c['count'] > 0])}/{len(ARCHIVE_CATEGORIES)}")
        
    else:
        print(f"\n❌ ARCHIVE ERROR: {message}")
        
    print(f"\n" + "=" * 50)
    return success

def main():
    """Main archive verification function"""
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "verify":
            success, message, _ = verify_archive_integrity()
            print(message)
            sys.exit(0 if success else 1)
            
        elif command == "find" and len(sys.argv) > 2:
            filename = sys.argv[2]
            location = get_archived_file_location(filename)
            sys.exit(0 if location else 1)
            
        elif command == "list":
            category = sys.argv[2] if len(sys.argv) > 2 else None
            list_archived_files(category)
            sys.exit(0)
            
        elif command == "report":
            success = generate_archive_report()
            sys.exit(0 if success else 1)
            
        else:
            print(f"❌ Unknown command: {command}")
            print(f"Usage: {sys.argv[0]} [verify|find <filename>|list [category]|report]")
            sys.exit(1)
    else:
        # Default: run comprehensive verification
        success = generate_archive_report()
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
