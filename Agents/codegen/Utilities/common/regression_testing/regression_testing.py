"""
Regression Testing Runner

This script discovers and runs all tests in the 'tests' directory.
It serves as the main entry point for the regression testing suite.

Usage:
    python regression_testing.py

Author: yyin
Date: 2025-12-08
"""

import unittest
import sys
import os
from pathlib import Path

# Add workspace root to path to allow absolute imports (e.g. from Check_modules...)
_SCRIPT_DIR = Path(__file__).resolve().parent
_WORKSPACE_ROOT = _SCRIPT_DIR.parents[2]  # Go up 3 levels: regression_testing -> common -> Check_modules -> CHECKLIST
_COMMON_DIR = _SCRIPT_DIR.parent

if str(_WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(_WORKSPACE_ROOT))
if str(_COMMON_DIR) not in sys.path:
    sys.path.insert(0, str(_COMMON_DIR))

def run_tests():
    """Discover and run all tests."""
    # Define test directory
    test_dir = _SCRIPT_DIR / 'tests'
    
    if not test_dir.exists():
        print(f"Error: Test directory not found: {test_dir}")
        return 1

    # Discover tests
    loader = unittest.TestLoader()
    suite = loader.discover(start_dir=str(test_dir), pattern='test_*.py')

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Return 0 if successful, 1 otherwise
    return 0 if result.wasSuccessful() else 1

if __name__ == '__main__':
    sys.exit(run_tests())
