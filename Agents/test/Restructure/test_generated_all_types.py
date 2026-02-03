"""
Test Generated Checker - All 4 Types
Test the newly generated checker with fillable templates against reference implementation
"""

import sys
from pathlib import Path
import yaml
import json

# Add paths
test_dir = Path(__file__).resolve().parent
agent_test_root = test_dir.parent  # Up to Agent/test folder
agent_common = agent_test_root / 'Check_modules' / 'common'

# Add common module paths FIRST (use Agent/test framework, not Latest)
sys.path.insert(0, str(agent_common))
sys.path.insert(0, str(test_dir))

# Import checkers
import importlib.util

# Import Reference (Aggressive) checker
spec_ref = importlib.util.spec_from_file_location("ref_checker", test_dir / 'Check_10_0_0_00_aggressive.py')
ref_module = importlib.util.module_from_spec(spec_ref)
spec_ref.loader.exec_module(ref_module)
ReferenceChecker = ref_module.NetlistSpefVersionChecker

# Import Generated checker
spec_gen = importlib.util.spec_from_file_location("gen_checker", test_dir / 'Check_10_0_0_00_generated.py')
gen_module = importlib.util.module_from_spec(spec_gen)
spec_gen.loader.exec_module(gen_module)
GeneratedChecker = gen_module.NetlistSpefVersionChecker


def load_yaml_config(yaml_path):
    """Load YAML configuration file."""
    with open(yaml_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def test_checker(checker_class, config, checker_name):
    """Test a checker with given configuration."""
    print(f"\n{'='*70}")
    print(f"Testing: {checker_name}")
    print(f"{'='*70}")
    
    checker = checker_class()
    
    # IMPORTANT: Call init_checker FIRST, then override item_data
    # Because init_checker() calls load_item_data() which would overwrite our config
    checker.init_checker()
    checker.item_data = config  # Override with test configuration
    
    try:
        result = checker.execute_check()
        
        print(f"  [OK] is_pass: {result.is_pass}")
        print(f"  [OK] value: {result.value}")
        print(f"  [OK] details count: {len(result.details)}")
        
        # Count severity
        from collections import Counter
        severity_counts = Counter([d.severity for d in result.details])
        print(f"  [OK] severity counts: {dict(severity_counts)}")
        
        # Print first 3 details
        print(f"\n  First 3 details:")
        for i, detail in enumerate(result.details[:3], 1):
            print(f"    {i}. {detail.severity.name}: {detail.name}")
            print(f"       Reason: {detail.reason}")
        
        return {
            'is_pass': result.is_pass,
            'value': result.value,
            'details_count': len(result.details),
            'severity_counts': dict(severity_counts),
            'details': [(d.severity.name, d.name, d.reason) for d in result.details]
        }
    
    except Exception as e:
        print(f"  [X] ERROR: {str(e)}")
        import traceback
        print("\nFull traceback:")
        traceback.print_exc()
        return None


def compare_results(ref_result, gen_result, test_type):
    """Compare two checker results."""
    print(f"\n{'='*70}")
    print(f"COMPARISON: Reference vs Generated ({test_type})")
    print(f"{'='*70}")
    
    if ref_result is None or gen_result is None:
        print("  [X] Cannot compare - one or both checkers failed")
        return False
    
    all_match = True
    
    # Compare is_pass
    if ref_result['is_pass'] == gen_result['is_pass']:
        print(f"  [OK] is_pass: {ref_result['is_pass']} (MATCH)")
    else:
        print(f"  [X] is_pass: Reference={ref_result['is_pass']}, Generated={gen_result['is_pass']} (MISMATCH)")
        all_match = False
    
    # Compare value
    if ref_result['value'] == gen_result['value']:
        print(f"  [OK] value: {ref_result['value']} (MATCH)")
    else:
        print(f"  [X] value: Reference={ref_result['value']}, Generated={gen_result['value']} (MISMATCH)")
        all_match = False
    
    # Compare details count
    if ref_result['details_count'] == gen_result['details_count']:
        print(f"  [OK] details_count: {ref_result['details_count']} (MATCH)")
    else:
        print(f"  [X] details_count: Reference={ref_result['details_count']}, Generated={gen_result['details_count']} (MISMATCH)")
        all_match = False
    
    # Compare severity counts
    ref_severities = set(ref_result['severity_counts'].keys())
    gen_severities = set(gen_result['severity_counts'].keys())
    
    if ref_severities == gen_severities:
        print(f"  [OK] severity types match")
        for severity in ref_severities:
            ref_count = ref_result['severity_counts'][severity]
            gen_count = gen_result['severity_counts'][severity]
            if ref_count == gen_count:
                print(f"    [OK] {severity}: {ref_count}")
            else:
                print(f"    [X] {severity}: Reference={ref_count}, Generated={gen_count}")
                all_match = False
    else:
        print(f"  [X] severity types mismatch")
        print(f"    Reference: {ref_severities}")
        print(f"    Generated: {gen_severities}")
        all_match = False
    
    return all_match


def run_all_tests():
    """Run all 4 test types."""
    print("="*70)
    print("COMPREHENSIVE TEST: Generated Checker vs Reference")
    print("="*70)
    
    test_configs = [
        ('TC01_Type1.yaml', 'Type 1: Boolean Check (no waiver)'),
        ('TC02_Type2.yaml', 'Type 2: Value Check (no waiver)'),
        ('TC03_Type3.yaml', 'Type 3: Value Check with Waiver'),
        ('TC04_Type4.yaml', 'Type 4: Boolean Check with Waiver'),
    ]
    
    results_summary = []
    
    for config_file, test_name in test_configs:
        print(f"\n\n{'#'*70}")
        print(f"# {test_name}")
        print(f"# Config: {config_file}")
        print(f"{'#'*70}")
        
        config_path = test_dir / config_file
        if not config_path.exists():
            print(f"  [X] Config file not found: {config_file}")
            results_summary.append({
                'test': test_name,
                'status': 'SKIPPED',
                'reason': 'Config file not found'
            })
            continue
        
        config = load_yaml_config(config_path)
        
        # Test Reference checker
        ref_result = test_checker(ReferenceChecker, config, f"Reference - {test_name}")
        
        # Test Generated checker
        gen_result = test_checker(GeneratedChecker, config, f"Generated - {test_name}")
        
        # Compare
        match = compare_results(ref_result, gen_result, test_name)
        
        results_summary.append({
            'test': test_name,
            'config': config_file,
            'status': 'PASS' if match else 'FAIL',
            'reference': ref_result,
            'generated': gen_result
        })
    
    # Final Summary
    print(f"\n\n{'='*70}")
    print("FINAL SUMMARY")
    print(f"{'='*70}")
    
    for result in results_summary:
        status_icon = '[PASS]' if result['status'] == 'PASS' else '[FAIL]'
        print(f"{status_icon} {result['test']}: {result['status']}")
    
    pass_count = sum(1 for r in results_summary if r['status'] == 'PASS')
    total_count = len(results_summary)
    
    print(f"\nOverall: {pass_count}/{total_count} tests passed")
    
    # Save results to JSON
    output_file = test_dir / 'test_output_no_golden' / 'test_results_all_types.json'
    output_file.parent.mkdir(exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results_summary, f, indent=2, default=str)
    
    print(f"\nResults saved to: {output_file}")
    
    return pass_count == total_count


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
