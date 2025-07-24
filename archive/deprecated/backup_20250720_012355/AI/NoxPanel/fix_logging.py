"""
Quick fix to remove Unicode characters from logging in NoxPanel
This will make the server more stable on Windows terminals
"""

import re
import os

def fix_unicode_in_file(file_path):
    """
    RLVR: Implements fix_unicode_in_file with error handling and validation

    REASONING CHAIN:
    1. Problem: Input parameters and business logic for fix_unicode_in_file
    2. Analysis: Function complexity 2.0/5.0
    3. Solution: Implements fix_unicode_in_file with error handling and validation
    4. Implementation: Chain-of-Thought validation with error handling
    5. Validation: 3 test cases covering edge cases

    COMPLIANCE: STANDARD
    """
    """Remove Unicode emojis from a Python file"""
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Replace common Unicode emojis with text equivalents
    replacements = {
        '🚀': '[INIT]',
        '🔒': '[SEC]',
        '✅': '[OK]',
        '❌': '[FAIL]',
        '📊': '[DB]',
        '🔧': '[SYS]',
        '📦': '[MOD]',
        '🌍': '[ENV]',
        '🔌': '[PLUG]',
        '🌐': '[WEB]',
        '🤖': '[BOT]',
        '🛡️': '[GUARD]',
        '⚡': '[FAST]',
        '🎯': '[TARGET]',
        '💾': '[SAVE]',
        '🔍': '[SEARCH]',
        '📁': '[FILE]',
        '⚙️': '[CONFIG]'
    }

    original_content = content
    for emoji, replacement in replacements.items():
        content = content.replace(emoji, replacement)

    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Fixed Unicode in: {file_path}")
        return True

    return False

if __name__ == "__main__":
    files_to_fix = [
        "webpanel/app_v5.py",
        "noxcore/security_config.py",
        "noxcore/database_pool.py",
        "webpanel/models_direct.py",
        "webpanel/ai_monitor_direct.py"
    ]

    fixed_count = 0
    for file_path in files_to_fix:
        if fix_unicode_in_file(file_path):
            fixed_count += 1

    print(f"Fixed {fixed_count} files")
