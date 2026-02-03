"""
Comparison test: Original Golden vs Refactored version.
Objective analysis of code coverage and test scenarios.
"""

import sys
from pathlib import Path
import importlib.util

# Add common module to path
_SCRIPT_DIR = Path(__file__).resolve().parent
_CHECK_MODULES_DIR = _SCRIPT_DIR / 'Check_modules'
_COMMON_DIR = _CHECK_MODULES_DIR / 'common'
if str(_COMMON_DIR) not in sys.path:
    sys.path.insert(0, str(_COMMON_DIR))


def load_checker_module(py_file: Path, module_name: str):
    """Load checker module dynamically"""
    spec = importlib.util.spec_from_file_location(module_name, py_file)
    module = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(py_file.parent))
    spec.loader.exec_module(module)
    return module


def load_item_yaml(yaml_path: Path) -> dict:
    """Load item YAML configuration"""
    import yaml
    with open(yaml_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def test_checker(checker_class, config: dict, checker_name: str):
    """Test a checker with configuration"""
    try:
        # Create checker instance
        checker = checker_class()
        
        # Manually set item_data (bypass init_checker for testing)
        checker.item_data = config
        checker._initialized = True
        checker.root = _SCRIPT_DIR
        
        # Execute checker
        result = checker.execute_check()
        
        return {
            'success': True,
            'is_pass': result.is_pass,
            'value': result.value,
            'details_count': len(result.details),
            'severity_counts': {
                'INFO': sum(1 for d in result.details if d.severity.name == 'INFO'),
                'WARN': sum(1 for d in result.details if d.severity.name == 'WARN'),
                'FAIL': sum(1 for d in result.details if d.severity.name == 'FAIL')
            }
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def compare_results(original_result: dict, refactored_result: dict):
    """Compare two results and return differences"""
    if not original_result['success'] or not refactored_result['success']:
        return {
            'match': False,
            'reason': 'One or both executions failed'
        }
    
    differences = []
    
    # Compare is_pass
    if original_result['is_pass'] != refactored_result['is_pass']:
        differences.append(f"is_pass: {original_result['is_pass']} vs {refactored_result['is_pass']}")
    
    # Compare value
    if str(original_result['value']) != str(refactored_result['value']):
        differences.append(f"value: {original_result['value']} vs {refactored_result['value']}")
    
    # Compare severity counts
    for severity in ['INFO', 'WARN', 'FAIL']:
        orig_count = original_result['severity_counts'][severity]
        ref_count = refactored_result['severity_counts'][severity]
        if orig_count != ref_count:
            differences.append(f"{severity}: {orig_count} vs {ref_count}")
    
    return {
        'match': len(differences) == 0,
        'differences': differences
    }


def main():
    """Run comparison test"""
    print("="*80)
    print("COMPARISON TEST: Original Golden vs Refactored")
    print("="*80)
    
    # Load modules
    golden_file = Path(r"c:\Users\wentao\AAI_local\AAI\Main_Work\ACL\Golden\IMP-10-0-0-00.py")
    refactored_file = _CHECK_MODULES_DIR / '10.0_STA_DCD_CHECK' / 'scripts' / 'checker' / 'IMP-10-0-0-00.py'
    
    print(f"\nLoading modules:")
    print(f"  Original: {golden_file}")
    print(f"  Refactored: {refactored_file}")
    
    # Load Golden module
    golden_module = load_checker_module(golden_file, "golden_checker")
    GoldenChecker = golden_module.NetlistSpefVersionChecker
    
    # Load Refactored module
    refactored_module = load_checker_module(refactored_file, "refactored_checker")
    RefactoredChecker = refactored_module.NetlistSpefVersionChecker
    
    # Test configurations
    items_dir = _CHECK_MODULES_DIR / '10.0_STA_DCD_CHECK' / 'inputs' / 'items'
    
    tests = [
        ('IMP-10-0-0-00_TC01_Type1.yaml', 'TC01_Type1'),
        ('IMP-10-0-0-00_TC02_Type2.yaml', 'TC02_Type2'),
        ('IMP-10-0-0-00_TC03_Type3.yaml', 'TC03_Type3'),
        ('IMP-10-0-0-00_TC04_Type4.yaml', 'TC04_Type4'),
    ]
    
    results = []
    
    for yaml_file, test_name in tests:
        yaml_path = items_dir / yaml_file
        if not yaml_path.exists():
            print(f"\n[SKIP] {test_name}: Config file not found")
            continue
        
        print(f"\n{'='*80}")
        print(f"Test: {test_name}")
        print('='*80)
        
        # Load configuration
        config = load_item_yaml(yaml_path)
        
        print(f"Config: value={config.get('requirements', {}).get('value', 'N/A')}, "
              f"waiver={config.get('waivers', {}).get('value', 'N/A')}")
        
        # Test Original
        print(f"\n  [Original Golden]")
        original_result = test_checker(GoldenChecker, config, "Golden")
        if original_result['success']:
            print(f"    is_pass: {original_result['is_pass']}")
            print(f"    value: {original_result['value']}")
            print(f"    details: {original_result['details_count']} items")
            print(f"    severity: INFO={original_result['severity_counts']['INFO']}, "
                  f"WARN={original_result['severity_counts']['WARN']}, "
                  f"FAIL={original_result['severity_counts']['FAIL']}")
        else:
            print(f"    ERROR: {original_result['error']}")
        
        # Test Refactored
        print(f"\n  [Refactored Version]")
        refactored_result = test_checker(RefactoredChecker, config, "Refactored")
        if refactored_result['success']:
            print(f"    is_pass: {refactored_result['is_pass']}")
            print(f"    value: {refactored_result['value']}")
            print(f"    details: {refactored_result['details_count']} items")
            print(f"    severity: INFO={refactored_result['severity_counts']['INFO']}, "
                  f"WARN={refactored_result['severity_counts']['WARN']}, "
                  f"FAIL={refactored_result['severity_counts']['FAIL']}")
        else:
            print(f"    ERROR: {refactored_result['error']}")
        
        # Compare
        comparison = compare_results(original_result, refactored_result)
        print(f"\n  [Comparison]")
        if comparison['match']:
            print(f"    Status: MATCH - Results are identical")
            results.append(True)
        else:
            print(f"    Status: MISMATCH")
            for diff in comparison['differences']:
                print(f"    Difference: {diff}")
            results.append(False)
    
    # Summary
    print(f"\n{'='*80}")
    print("SUMMARY")
    print('='*80)
    matched = sum(results)
    total = len(results)
    print(f"Total tests: {total}")
    print(f"Matched: {matched} / {total}")
    print(f"Mismatched: {total - matched} / {total}")
    
    if matched == total:
        print("\nCONCLUSION: Refactoring maintains behavior correctly!")
        return 0
    else:
        print(f"\nCONCLUSION: {total - matched} test(s) have different behavior")
        return 1


if __name__ == '__main__':
    sys.exit(main())
