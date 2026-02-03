#!/usr/bin/env python3
"""Simple test runner - just run generated checker like Golden"""
import sys
from pathlib import Path

# Add paths
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root / "CHECKLIST" / "CHECKLIST"))
sys.path.insert(0, str(Path(__file__).parent / "test_output_no_golden"))

from generated_checker import NetlistSpefVersionChecker

def init_checker() -> NetlistSpefVersionChecker:
    """Initialize and return the checker instance (Golden pattern)."""
    checker = NetlistSpefVersionChecker()
    checker.init_checker()
    return checker

if __name__ == '__main__':
    print("="*70)
    print("Generated Checker Test")
    print("="*70)
    
    checker = init_checker()
    result = checker.execute_check()
    checker.write_output(result)
    
    print("\n" + "="*70)
    print("Done! Output written successfully.")
    print("="*70)
