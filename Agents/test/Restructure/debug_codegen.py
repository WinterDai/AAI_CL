import sys
from pathlib import Path

# Setup paths
sys.path.insert(0, str(Path.cwd() / 'Check_modules' / 'common'))

import importlib.util
import yaml
import traceback

# Load the module
spec = importlib.util.spec_from_file_location('test', 'Check_10_0_0_00_aggressive.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

# Load config
config = yaml.safe_load(open('TC01_Type1.yaml'))

# Run checker
checker = mod.NetlistSpefVersionChecker()
checker.item_data = config
checker._initialized = True

try:
    result = checker.execute_check()
    print(f'Result: {result.is_pass}')
    print(f'Value: {result.value}')
    print(f'Details count: {len(result.details)}')
    if result.details:
        print(f'First detail: {result.details[0].content}')
except Exception as e:
    print(f'ERROR: {e}')
    traceback.print_exc()
