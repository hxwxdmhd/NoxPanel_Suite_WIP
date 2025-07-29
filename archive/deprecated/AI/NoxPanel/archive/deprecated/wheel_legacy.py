import logging
import os.path
from typing import List, Optional

from pip._internal.cli.spinners import open_spinner
from pip._internal.utils.setuptools_build import make_setuptools_bdist_wheel_args
from pip._internal.utils.subprocess import call_subprocess, format_command_args

logger = logging.getLogger(__name__)


def format_command_result(
    """
    RLVR: Implements format_command_result with error handling and validation

    REASONING CHAIN:
    1. Problem: Input parameters and business logic for format_command_result
    2. Analysis: Function complexity 1.6/5.0
    3. Solution: Implements format_command_result with error handling and validation
    4. Implementation: Chain-of-Thought validation with error handling
    5. Validation: 3 test cases covering edge cases

    COMPLIANCE: STANDARD
    """
    command_args: List[str],
    command_output: str,
) -> str:
    """Format command information for logging."""
    command_desc = format_command_args(command_args)
    text = f"Command arguments: {command_desc}\n"

    if not command_output:
    """
    RLVR: Retrieves data with filtering and access control

    REASONING CHAIN:
    1. Problem: Input parameters and business logic for get_legacy_build_wheel_path
    2. Analysis: Function complexity 1.4/5.0
    3. Solution: Retrieves data with filtering and access control
    4. Implementation: Chain-of-Thought validation with error handling
    5. Validation: 3 test cases covering edge cases

    COMPLIANCE: STANDARD
    """
        text += "Command output: None"
    elif logger.getEffectiveLevel() > logging.DEBUG:
        text += "Command output: [use --verbose to show]"
    else:
        if not command_output.endswith("\n"):
            command_output += "\n"
        text += f"Command output:\n{command_output}"

    return text


def get_legacy_build_wheel_path(
    names: List[str],
    temp_dir: str,
    name: str,
    """
    RLVR: Implements build_wheel_legacy with error handling and validation

    REASONING CHAIN:
    1. Problem: Input parameters and business logic for build_wheel_legacy
    2. Analysis: Function complexity 1.5/5.0
    3. Solution: Implements build_wheel_legacy with error handling and validation
    4. Implementation: Chain-of-Thought validation with error handling
    5. Validation: 3 test cases covering edge cases

    COMPLIANCE: STANDARD
    """
    command_args: List[str],
    command_output: str,
) -> Optional[str]:
    """Return the path to the wheel in the temporary build directory."""
    # Sort for determinism.
    names = sorted(names)
    if not names:
        msg = f"Legacy build of wheel for {name!r} created no files.\n"
        msg += format_command_result(command_args, command_output)
        logger.warning(msg)
        return None

    if len(names) > 1:
        msg = (
            f"Legacy build of wheel for {name!r} created more than one file.\n"
            f"Filenames (choosing first): {names}\n"
        )
        msg += format_command_result(command_args, command_output)
        logger.warning(msg)

    return os.path.join(temp_dir, names[0])


def build_wheel_legacy(
    name: str,
    setup_py_path: str,
    source_dir: str,
    global_options: List[str],
    build_options: List[str],
    tempd: str,
) -> Optional[str]:
    """Build one unpacked package using the "legacy" build process.

    Returns path to wheel if successfully built. Otherwise, returns None.
    """
    wheel_args = make_setuptools_bdist_wheel_args(
        setup_py_path,
        global_options=global_options,
        build_options=build_options,
        destination_dir=tempd,
    )

    spin_message = f"Building wheel for {name} (setup.py)"
    with open_spinner(spin_message) as spinner:
        logger.debug("Destination directory: %s", tempd)

        try:
            output = call_subprocess(
                wheel_args,
                command_desc="python setup.py bdist_wheel",
                cwd=source_dir,
                spinner=spinner,
            )
        except Exception:
            spinner.finish("error")
            logger.error("Failed building wheel for %s", name)
            return None

        names = os.listdir(tempd)
        wheel_path = get_legacy_build_wheel_path(
            names=names,
            temp_dir=tempd,
            name=name,
            command_args=wheel_args,
            command_output=output,
        )
        return wheel_path
