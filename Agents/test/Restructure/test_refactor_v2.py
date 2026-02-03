"""
Test script for refactored IMP-10-0-0-00 checker - ASCII only version.
Tests all 4 Type scenarios with different configurations.
"""

import sys
from pathlib import Path

# Add common module to path
_SCRIPT_DIR = Path(__file__).resolve().parent
_CHECK_MODULES_DIR = _SCRIPT_DIR / 'Check_modules'
_COMMON_DIR = _CHECK_MODULES_DIR / 'common'
if str(_COMMON_DIR) not in sys.path:
    sys.path.insert(0, str(_COMMON_DIR))

from base_checker import CheckResult

# Import checker module dynamically
checker_path = _CHECK_MODULES_DIR / '10.0_STA_DCD_CHECK' / 'scripts' / 'checker'
sys.path.insert(0, str(checker_path))

import importlib.util
spec = importlib.util.spec_from_file_location("checker_module", checker_path / "IMP-10-0-0-00.py")
checker_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker_module)
NetlistSpefVersionChecker = checker_module.NetlistSpefVersionChecker


def load_item_yaml(yaml_path: Path) -> dict:
    """Load item YAML configuration"""
    import yaml
    with open(yaml_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def test_checker_with_config(yaml_path: Path, test_name: str):
    """Test checker with specific configuration"""
    print(f"\n{'='*80}")
    print(f"Test: {test_name}")
    print(f"Config: {yaml_path.name}")
    print('='*80)
    
    try:
        # Load configuration
        config = load_item_yaml(yaml_path)
        
        # Create checker instance
        checker = NetlistSpefVersionChecker()
        
        # Manually set item_data (bypass init_checker for testing)
        checker.item_data = config
        checker._initialized = True  # Mark as initialized
        checker.root = _SCRIPT_DIR
        
        print(f"\nConfig Info:")
        print(f"  requirements.value: {config.get('requirements', {}).get('value', 'N/A')}")
        print(f"  pattern_items: {config.get('requirements', {}).get('pattern_items', [])}")
        print(f"  waivers.value: {config.get('waivers', {}).get('value', 'N/A')}")
        print(f"  waive_items: {config.get('waivers', {}).get('waive_items', [])}")
        
        # Execute checker
        result = checker.execute_check()
        
        # Display results
        print(f"\nCheck Result:")
        print(f"  is_pass: {result.is_pass}")
        print(f"  Value: {result.value}")
        
        print(f"\nDetails ({len(result.details)} items):")
        severity_counts = {'INFO': 0, 'WARN': 0, 'FAIL': 0}
        for detail in result.details[:10]:  # Show first 10 only
            severity_counts[detail.severity.name] += 1
            print(f"  [{detail.severity.name}] {detail.name[:80]}")
        
        if len(result.details) > 10:
            print(f"  ... and {len(result.details) - 10} more items")
        
        print(f"\nSeverity Counts:")
        for severity, count in severity_counts.items():
            if count > 0:
                print(f"  {severity}: {count}")
        
        # Test status
        expected_pass = test_name not in ["TC02_Type2"]  # TC02 should FAIL
        actual_pass = result.is_pass
        status = "PASS" if actual_pass == expected_pass else "FAIL"
        print(f"\nTest Status: {status}")
        if actual_pass != expected_pass:
            print(f"  Expected: {'PASS' if expected_pass else 'FAIL'}, Actual: {'PASS' if actual_pass else 'FAIL'}")
        
        return actual_pass == expected_pass
        
    except Exception as e:
        print(f"\nTest FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("="*80)
    print("IMP-10-0-0-00 Refactored Checker Test - 4 Type Scenarios")
    print("="*80)
    
    # Test configurations
    items_dir = _CHECK_MODULES_DIR / '10.0_STA_DCD_CHECK' / 'inputs' / 'items'
    
    tests = [
        (items_dir / 'IMP-10-0-0-00_TC01_Type1.yaml', 'TC01_Type1'),
        (items_dir / 'IMP-10-0-0-00_TC02_Type2.yaml', 'TC02_Type2'),
        (items_dir / 'IMP-10-0-0-00_TC03_Type3.yaml', 'TC03_Type3'),
        (items_dir / 'IMP-10-0-0-00_TC04_Type4.yaml', 'TC04_Type4'),
    ]
    
    results = []
    for yaml_path, test_name in tests:
        if not yaml_path.exists():
            print(f"\nERROR: Config file not found: {yaml_path}")
            results.append(False)
            continue
        
        success = test_checker_with_config(yaml_path, test_name)
        results.append(success)
    
    # Summary
    print(f"\n{'='*80}")
    print("Test Summary")
    print('='*80)
    passed = sum(results)
    total = len(results)
    print(f"Total: {total} tests")
    print(f"Passed: {passed} / {total}")
    print(f"Failed: {total - passed} / {total}")
    
    if passed == total:
        print("\nAll tests PASSED! Refactoring successful!")
        return 0
    else:
        print(f"\n{total - passed} test(s) FAILED, needs debugging")
        return 1


if __name__ == '__main__':
    sys.exit(main())
