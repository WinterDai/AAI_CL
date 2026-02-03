"""
Code Formatter - Postprocessor Skill for CodeGen Agent

Version: v1.0.0
Created: 2025-12-22

Formats Python code using black and isort for consistent style.
"""

import logging
from typing import Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class FormatResult:
    """Result of code formatting operation."""
    code: str
    success: bool
    isort_applied: bool = False
    black_applied: bool = False
    errors: list = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []


def format_code(
    code: str,
    line_length: int = 100,
    skip_isort: bool = False,
    skip_black: bool = False,
    target_version: str = "py38"
) -> str:
    """
    Format Python code using isort and black.
    
    Args:
        code: Python code to format
        line_length: Maximum line length (default: 100)
        skip_isort: Skip import sorting
        skip_black: Skip black formatting
        target_version: Python version target (default: py38)
        
    Returns:
        Formatted code string
    """
    result = format_code_detailed(
        code=code,
        line_length=line_length,
        skip_isort=skip_isort,
        skip_black=skip_black,
        target_version=target_version
    )
    return result.code


def format_code_detailed(
    code: str,
    line_length: int = 100,
    skip_isort: bool = False,
    skip_black: bool = False,
    target_version: str = "py38"
) -> FormatResult:
    """
    Format code with detailed result information.
    
    Returns:
        FormatResult with code, success status, and error details
    """
    result = FormatResult(code=code, success=True)
    formatted_code = code
    
    # Step 1: Apply isort
    if not skip_isort:
        formatted_code, isort_success, isort_error = _apply_isort(
            formatted_code, line_length
        )
        result.isort_applied = isort_success
        if isort_error:
            result.errors.append(f"isort: {isort_error}")
    
    # Step 2: Apply black
    if not skip_black:
        formatted_code, black_success, black_error = _apply_black(
            formatted_code, line_length, target_version
        )
        result.black_applied = black_success
        if black_error:
            result.errors.append(f"black: {black_error}")
    
    result.code = formatted_code
    result.success = not result.errors
    
    return result


def _apply_isort(code: str, line_length: int) -> Tuple[str, bool, Optional[str]]:
    """
    Apply isort to sort imports.
    
    Returns:
        (formatted_code, success, error_message)
    """
    try:
        import isort
        
        # isort configuration matching CHECKLIST project
        config = isort.Config(
            line_length=line_length,
            multi_line_output=3,  # Vertical Hanging Indent
            include_trailing_comma=True,
            force_grid_wrap=0,
            use_parentheses=True,
            ensure_newline_before_comments=True,
            sections=['FUTURE', 'STDLIB', 'THIRDPARTY', 'FIRSTPARTY', 'LOCALFOLDER'],
            known_first_party=['Check_modules', 'agents'],
        )
        
        formatted = isort.code(code, config=config)
        return formatted, True, None
        
    except ImportError:
        logger.warning("isort not installed. Skipping import sorting.")
        return code, False, "isort not installed"
    except Exception as e:
        logger.warning(f"isort failed: {e}")
        return code, False, str(e)


def _apply_black(
    code: str, 
    line_length: int, 
    target_version: str
) -> Tuple[str, bool, Optional[str]]:
    """
    Apply black formatting.
    
    Returns:
        (formatted_code, success, error_message)
    """
    try:
        import black
        
        # Parse target version
        target_versions = set()
        if target_version:
            version_map = {
                "py38": black.TargetVersion.PY38,
                "py39": black.TargetVersion.PY39,
                "py310": black.TargetVersion.PY310,
                "py311": black.TargetVersion.PY311,
                "py312": black.TargetVersion.PY312,
            }
            if target_version in version_map:
                target_versions.add(version_map[target_version])
        
        # Black mode configuration
        mode = black.Mode(
            target_versions=target_versions or {black.TargetVersion.PY38},
            line_length=line_length,
            string_normalization=True,
            is_pyi=False,
        )
        
        formatted = black.format_str(code, mode=mode)
        return formatted, True, None
        
    except ImportError:
        logger.warning("black not installed. Skipping code formatting.")
        return code, False, "black not installed"
    except black.InvalidInput as e:
        logger.warning(f"black InvalidInput: {e}")
        return code, False, f"Invalid Python syntax: {e}"
    except Exception as e:
        logger.warning(f"black failed: {e}")
        return code, False, str(e)


def check_formatters_available() -> dict:
    """
    Check if formatting tools are available.
    
    Returns:
        Dict with 'black' and 'isort' boolean availability
    """
    result = {'black': False, 'isort': False}
    
    try:
        import black
        result['black'] = True
    except ImportError:
        pass
    
    try:
        import isort
        result['isort'] = True
    except ImportError:
        pass
    
    return result


# ============================================================================
# Convenience Functions
# ============================================================================

def format_file(
    file_path: str,
    line_length: int = 100,
    in_place: bool = False
) -> FormatResult:
    """
    Format a Python file.
    
    Args:
        file_path: Path to Python file
        line_length: Maximum line length
        in_place: Write changes back to file
        
    Returns:
        FormatResult
    """
    from pathlib import Path
    
    path = Path(file_path)
    code = path.read_text(encoding='utf-8')
    
    result = format_code_detailed(code, line_length)
    
    if in_place and result.success:
        path.write_text(result.code, encoding='utf-8')
    
    return result


def quick_format(code: str) -> str:
    """
    Quick format with defaults, return code unchanged on any error.
    
    Use this for best-effort formatting without error handling complexity.
    """
    try:
        return format_code(code)
    except Exception:
        return code


if __name__ == "__main__":
    # Test
    test_code = '''
import json
import re
from typing import Dict,Any,List
from pathlib import Path
import sys


class TestClass:
    def method(self,arg1,arg2):
        result = {"key":"value","other":"data"}
        return result
'''
    
    print("Available formatters:", check_formatters_available())
    print("\n--- Original ---")
    print(test_code)
    print("\n--- Formatted ---")
    result = format_code_detailed(test_code)
    print(result.code)
    print(f"\nSuccess: {result.success}")
    print(f"isort applied: {result.isort_applied}")
    print(f"black applied: {result.black_applied}")
    if result.errors:
        print(f"Errors: {result.errors}")
