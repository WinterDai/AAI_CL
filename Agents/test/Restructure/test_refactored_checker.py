"""
Test script for refactored IMP-10-0-0-00 checker.
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

# Import the checker
checker_path = _CHECK_MODULES_DIR / '10.0_STA_DCD_CHECK' / 'scripts' / 'checker'
sys.path.insert(0, str(checker_path))

# Import checker module dynamically
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
        checker.root = Path('c:/Users/wentao/AAI_local/AAI/Main_Work/ACL/CHECKLIST/Tool/Agent/test/Restructure')
        
        print(f"\nConfig Info:")
        print(f"  requirements.value: {config.get('requirements', {}).get('value', 'N/A')}")
        print(f"  pattern_items: {config.get('requirements', {}).get('pattern_items', [])}")
        print(f"  waivers.value: {config.get('waivers', {}).get('value', 'N/A')}")
        print(f"  waive_items: {config.get('waivers', {}).get('waive_items', [])}")
        print(f"  input_files: {config.get('input_files', [])}")
        
        # Execute checker
        result = checker.execute_check()
        
        # Display results
        print(f"\nCheck Result:")
        print(f"  Result: {result.result}")
        print(f"  Value: {result.value}")
        print(f"  Detected Type: Type {checker.detect_type()}")
        
        print(f"\nDetails ({len(result.details)} items):")
        severity_counts = {'INFO': 0, 'WARN': 0, 'FAIL': 0}
        for detail in result.details:
            severity_counts[detail.severity.name] += 1
            print(f"  [{detail.severity.name}] {detail.name}")
            if detail.reason:
                print(f"      Reason: {detail.reason}")
        
        print(f"\nSeverity Counts:")
        for severity, count in severity_counts.items():
            print(f"  {severity}: {count}")
        
        # Test status
        expected_pass = test_name != "TC02_Type2"  # TC02 should FAIL (unwaived missing)
        actual_pass = result.result == 'PASS'
        status = "PASS" if actual_pass == expected_pass else "FAIL"
        print(f"\nTest Status: {status}")
        if actual_pass != expected_pass:
            print(f"  Expected: {'PASS' if expected_pass else 'FAIL'}, Actual: {result.result}")
        
        return actual_pass == expected_pass
        
    except Exception as e:
        print(f"\nTest FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("="*80)
    print("IMP-10-0-0-00 重构测试 - 4种Type场景")
    print("="*80)
    
    # Test configurations
    items_dir = _CHECK_MODULES_DIR / '10.0_STA_DCD_CHECK' / 'inputs' / 'items'
    
    tests = [
        (items_dir / 'IMP-10-0-0-00_TC01_Type1.yaml', 'TC01_Type1 (Boolean check, waiver.value=N/A)'),
        (items_dir / 'IMP-10-0-0-00_TC02_Type2.yaml', 'TC02_Type2 (Value check, waiver.value=N/A)'),
        (items_dir / 'IMP-10-0-0-00_TC03_Type3.yaml', 'TC03_Type3 (Value check with waiver)'),
        (items_dir / 'IMP-10-0-0-00_TC04_Type4.yaml', 'TC04_Type4 (Boolean check with waiver)'),
    ]
    
    results = []
    for yaml_path, test_name in tests:
        if not yaml_path.exists():
            print(f"\n❌ 配置文件不存在: {yaml_path}")
            results.append(False)
            continue
        
        success = test_checker_with_config(yaml_path, test_name)
        results.append(success)
    
    # Summary
    print(f"\n{'='*80}")
    print("测试摘要")
    print('='*80)
    passed = sum(results)
    total = len(results)
    print(f"总计: {total} 测试")
    print(f"通过: {passed} / {total}")
    print(f"失败: {total - passed} / {total}")
    
    if passed == total:
        print("\n🎉 所有测试通过！重构成功！")
        return 0
    else:
        print(f"\n⚠️  {total - passed} 个测试失败，需要调试")
        return 1


if __name__ == '__main__':
    sys.exit(main())
