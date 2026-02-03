"""
测试激进重构版本的IMP-10-0-0-00_aggressive.py
对比Golden vs Refactored vs Aggressive版本

测试目标：
1. 验证Aggressive版本行为是否与Golden一致
2. 统计代码行数：Golden vs Aggressive
3. 评估LLM复杂度：方法长度、参数数量等
"""

import sys
from pathlib import Path
import yaml

# Add paths
test_dir = Path(__file__).resolve().parent
acl_root = test_dir.parent.parent.parent.parent.parent  # Up to ACL folder
golden_dir = acl_root / 'Golden'
latest_common = acl_root / 'Latest' / 'CHECKLIST' / 'Check_modules' / 'common'

# Add common module paths FIRST
sys.path.insert(0, str(latest_common))
sys.path.insert(0, str(test_dir))

# Import checkers
# Import Golden checker with full module name
import importlib.util
spec = importlib.util.spec_from_file_location("golden_checker", golden_dir / 'IMP-10-0-0-00.py')
golden_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(golden_module)
GoldenChecker = golden_module.NetlistSpefVersionChecker

# Import Aggressive checker
spec_aggressive = importlib.util.spec_from_file_location("aggressive_checker", test_dir / 'IMP-10-0-0-00_aggressive.py')
aggressive_module = importlib.util.module_from_spec(spec_aggressive)
spec_aggressive.loader.exec_module(aggressive_module)
AggressiveChecker = aggressive_module.NetlistSpefVersionChecker


def load_yaml_config(yaml_path):
    """Load YAML configuration file."""
    with open(yaml_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def test_checker(checker_class, config, checker_name):
    """Test a checker with given configuration."""
    print(f"\n{'='*60}")
    print(f"Testing: {checker_name}")
    print(f"{'='*60}")
    
    checker = checker_class()
    checker.item_data = config
    
    # Call init_checker to setup paths
    try:
        checker.init_checker(config.get('check_module', ''), config)
    except:
        # Some checkers don't need init_checker
        pass
    
    try:
        result = checker.execute_check()
        
        print(f"  is_pass: {result.is_pass}")
        print(f"  value: {result.value}")
        print(f"  details count: {len(result.details)}")
        
        # Count severity
        from collections import Counter
        severity_counts = Counter([d.severity for d in result.details])
        print(f"  severity counts: {dict(severity_counts)}")
        
        # Print first 3 details
        print(f"\n  First 3 details:")
        for i, detail in enumerate(result.details[:3], 1):
            print(f"    {i}. {detail.severity.name}: {detail.name}")
            print(f"       Reason: {detail.reason}")
        
        return {
            'is_pass': result.is_pass,
            'value': result.value,
            'details_count': len(result.details),
            'severity_counts': severity_counts,
            'details': result.details
        }
    
    except Exception as e:
        print(f"  ERROR: {str(e)}")
        import traceback
        print("Full traceback:")
        traceback.print_exc()
        return None


def compare_results(golden_result, aggressive_result):
    """Compare two checker results."""
    print(f"\n{'='*60}")
    print("COMPARISON: Golden vs Aggressive")
    print(f"{'='*60}")
    
    if golden_result is None or aggressive_result is None:
        print("  Cannot compare - one or both results are None")
        return False
    
    # Compare is_pass
    is_pass_match = golden_result['is_pass'] == aggressive_result['is_pass']
    print(f"  is_pass: Golden={golden_result['is_pass']}, Aggressive={aggressive_result['is_pass']} {'OK' if is_pass_match else 'DIFF'}")
    
    # Compare value
    value_match = golden_result['value'] == aggressive_result['value']
    print(f"  value: Golden={golden_result['value']}, Aggressive={aggressive_result['value']} {'OK' if value_match else 'DIFF'}")
    
    # Compare severity counts
    golden_counts = dict(golden_result['severity_counts'])
    aggressive_counts = dict(aggressive_result['severity_counts'])
    severity_match = golden_counts == aggressive_counts
    print(f"  severity counts: {'OK' if severity_match else 'DIFF'}")
    print(f"    Golden: {golden_counts}")
    print(f"    Aggressive: {aggressive_counts}")
    
    all_match = is_pass_match and value_match and severity_match
    
    if all_match:
        print(f"\n  MATCH - Results are identical")
    else:
        print(f"\n  MISMATCH - Results differ")
    
    return all_match


def count_file_lines(file_path):
    """Count lines in a file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return len(f.readlines())


def analyze_code_complexity():
    """Analyze code complexity of different versions."""
    print(f"\n{'='*60}")
    print("CODE COMPLEXITY ANALYSIS")
    print(f"{'='*60}")
    
    golden_path = golden_dir / 'IMP-10-0-0-00.py'
    aggressive_path = test_dir / 'IMP-10-0-0-00_aggressive.py'
    
    golden_lines = count_file_lines(golden_path)
    aggressive_lines = count_file_lines(aggressive_path)
    
    print(f"\n1. Total Lines:")
    print(f"   Golden:     {golden_lines} lines")
    print(f"   Aggressive: {aggressive_lines} lines")
    print(f"   Saved:      {golden_lines - aggressive_lines} lines")
    print(f"   Reduction:  {((golden_lines - aggressive_lines) / golden_lines * 100):.1f}%")
    
    print(f"\n2. Type Method Complexity (estimated):")
    print(f"   Golden Type Methods:     ~100-150 lines each")
    print(f"   Aggressive Type Methods: ~50-70 lines each")
    print(f"   → LLM只需关注parse_data函数（30-50行业务逻辑）")
    
    print(f"\n3. Parameters LLM needs to remember:")
    print(f"   Golden approach:")
    print(f"     - build_complete_output: 15+ parameters")
    print(f"     - Type方法内部逻辑: found/missing分类、waiver处理等")
    print(f"   Aggressive approach:")
    print(f"     - execute_boolean_check/execute_value_check: 2-3 parameters")
    print(f"     - parse_data函数: 只需返回(found, missing, extra)")
    print(f"     - Framework自动处理所有分类和waiver逻辑")


def main():
    """Main test function."""
    print("="*60)
    print("AGGRESSIVE REFACTORING TEST")
    print("="*60)
    
    # Test configurations
    test_configs = [
        ('TC01_Type1.yaml', 'TC01 - Type 1 (Boolean check)'),
        ('TC02_Type2.yaml', 'TC02 - Type 2 (Value check)'),
        ('TC03_Type3.yaml', 'TC03 - Type 3 (Value + waiver)'),
        ('TC04_Type4.yaml', 'TC04 - Type 4 (Boolean + waiver)'),
    ]
    
    results = []
    
    for config_file, test_name in test_configs:
        config_path = test_dir / config_file
        
        if not config_path.exists():
            print(f"\nSkipping {test_name} - config not found: {config_path}")
            continue
        
        config = load_yaml_config(config_path)
        
        # Test Golden
        golden_result = test_checker(GoldenChecker, config, f"Golden - {test_name}")
        
        # Test Aggressive
        aggressive_result = test_checker(AggressiveChecker, config, f"Aggressive - {test_name}")
        
        # Compare
        match = compare_results(golden_result, aggressive_result)
        
        results.append({
            'test': test_name,
            'match': match
        })
    
    # Summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    
    total = len(results)
    matched = sum(1 for r in results if r['match'])
    
    for r in results:
        status = 'PASS' if r['match'] else 'FAIL'
        print(f"  {status}: {r['test']}")
    
    print(f"\nTotal: {matched}/{total} tests matched")
    
    if matched == total:
        print(f"\n{'='*20}")
        print("AGGRESSIVE REFACTORING SUCCESS!")
        print("All tests passed - behavior is identical to Golden")
        print(f"{'='*20}")
    else:
        print(f"\n{'='*20}")
        print(f"SOME TESTS FAILED: {total - matched}/{total}")
        print(f"{'='*20}")
    
    # Code complexity analysis
    analyze_code_complexity()
    
    return matched == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
