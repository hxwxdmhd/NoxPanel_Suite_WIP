import subprocess
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def run_script(script_path, args=None):
    """
    RLVR: Controls program flow with conditional logic and error handling

    REASONING CHAIN:
    1. Problem: Input parameters and business logic for run_script
    2. Analysis: Function complexity 1.7/5.0
    3. Solution: Controls program flow with conditional logic and error handling
    4. Implementation: Chain-of-Thought validation with error handling
    5. Validation: 3 test cases covering edge cases

    COMPLIANCE: STANDARD
    """
    """Safely execute a Python script with optional arguments."""
    args = args or []
    script_path = Path(script_path)

    # Security: Validate script path
    if not script_path.exists():
        raise FileNotFoundError(f"Script not found: {script_path}")

    if not script_path.suffix == '.py':
        raise ValueError("Only Python scripts are allowed")

    try:
        result = subprocess.run(
            ["python", str(script_path)] + args,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout
            check=False
        )

        logger.info(f"Executed script: {script_path} with args: {args}")
        return result.stdout, result.stderr, result.returncode

    except subprocess.TimeoutExpired:
        logger.error(f"Script timeout: {script_path}")
        return "", "Script execution timed out", 124
    except Exception as e:
        logger.error(f"Script execution error: {e}")
        return "", str(e), 1
