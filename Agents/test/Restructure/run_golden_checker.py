#!/usr/bin/env python3
"""Wrapper to run Golden checker with correct path setup"""
import sys
from pathlib import Path

# Setup paths like generated_checker
script_dir = Path(__file__).parent
project_root = script_dir.parents[4]  # Go up to ACL
common_dir = project_root / 'CHECKLIST' / 'CHECKLIST' / 'Check_modules' / 'common'
sys.path.insert(0, str(common_dir))

# Now run the Golden checker (from same directory)
golden_script = script_dir / 'Check_10_0_0_00_aggressive.py'

# Execute the script code with result fix
code = open(golden_script, encoding='utf-8').read()
# Fix the write_output() call
code = code.replace(
    "    checker = init_checker()\n    checker.execute_check()\n    checker.write_output()",
    "    checker = init_checker()\n    result = checker.execute_check()\n    checker.write_output(result)"
)
exec(code)
