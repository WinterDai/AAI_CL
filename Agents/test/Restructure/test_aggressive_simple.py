"""
简化版测试脚本：直接对比Golden vs Aggressive
"""

import sys
from pathlib import Path
import yaml

# Setup paths
test_dir = Path(__file__).resolve().parent
acl_root = test_dir.parent.parent.parent.parent.parent
golden_file = acl_root / 'Golden' / 'IMP-10-0-0-00.py'
aggressive_file = test_dir / 'IMP-10-0-0-00_aggressive.py'

# Add common module path
latest_common = acl_root / 'Latest' / 'CHECKLIST' / 'Check_modules' / 'common'
test_common = test_dir / 'Check_modules' / 'common'
sys.path.insert(0, str(latest_common))
sys.path.insert(0, str(test_common))  # For Aggressive checker's imports

print("="*70)
print("AGGRESSIVE REFACTORING TEST - Golden vs Aggressive")
print("="*70)

# Test configurations
test_configs = {
    'TC01_Type1': {
        'check_module': '10.0_STA_DCD_CHECK',
        'item_id': 'IMP-10-0-0-00',
        'item_desc': 'Confirm the netlist/spef version is correct',
        'input_files': [r'c:\Users\wentao\AAI_local\AAI\Main_Work\ACL\Latest\CHECKLIST\IP_project_folder\logs\sta_post_syn.log'],
        'requirements': {'value': 'N/A', 'unit': '', 'pattern_items': []},
        'waivers': {'value': 'N/A', 'unit': '', 'waive_items': []}
    },
    'TC02_Type2': {
        'check_module': '10.0_STA_DCD_CHECK',
        'item_id': 'IMP-10-0-0-00',
        'item_desc': 'Confirm the netlist/spef version is correct',
        'input_files': [r'c:\Users\wentao\AAI_local\AAI\Main_Work\ACL\Latest\CHECKLIST\IP_project_folder\logs\sta_post_syn.log'],
        'requirements': {'value': 1, 'unit': '', 'pattern_items': ['Generated on:*2025*']},
        'waivers': {'value': 'N/A', 'unit': '', 'waive_items': []}
    },
    'TC03_Type3': {
        'check_module': '10.0_STA_DCD_CHECK',
        'item_id': 'IMP-10-0-0-00',
        'item_desc': 'Confirm the netlist/spef version is correct',
        'input_files': [r'c:\Users\wentao\AAI_local\AAI\Main_Work\ACL\Latest\CHECKLIST\IP_project_folder\logs\sta_post_syn.log'],
        'requirements': {'value': 1, 'unit': '', 'pattern_items': ['Generated on:*2025*', 'Tool:*Quantus*']},
        'waivers': {'value': 1, 'unit': '', 'waive_items': ['Tool:*Quantus*']}
    },
    'TC04_Type4': {
        'check_module': '10.0_STA_DCD_CHECK',
        'item_id': 'IMP-10-0-0-00',
        'item_desc': 'Confirm the netlist/spef version is correct',
        'input_files': [r'c:\Users\wentao\AAI_local\AAI\Main_Work\ACL\Latest\CHECKLIST\IP_project_folder\logs\sta_post_syn.log'],
        'requirements': {'value': 'N/A', 'unit': '', 'pattern_items': []},
        'waivers': {'value': 1, 'unit': '', 'waive_items': ['SPEF Reading was skipped']}
    }
}

def load_checker_from_file(file_path):
    """Load checker class from file."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("checker_module", file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.NetlistSpefVersionChecker

def run_checker(checker_class, config, name):
    """Run a checker with config."""
    print(f"\n{'='*70}")
    print(f"Testing: {name}")
    print(f"{'='*70}")
    
    try:
        checker = checker_class()
        # Set item_data and call init_checker
        checker.item_data = config
        checker.check_module = config['check_module']
        checker.item_id = config['item_id']
        checker.item_desc = config['item_desc']
        
        # Call init_checker to set up root path
        try:
            checker.init_checker()
        except:
            pass  # Some checkers may not need this
        
        result = checker.execute_check()
        
        print(f"  is_pass: {result.is_pass}")
        print(f"  value: {result.value}")
        print(f"  details: {len(result.details)} items")
        
        # Count severities
        from collections import Counter
        from output_formatter import Severity
        severities = Counter([d.severity for d in result.details])
        print(f"  severities: ", end="")
        for sev, count in severities.items():
            print(f"{sev.name}={count} ", end="")
        print()
        
        # Show first 3 details
        print(f"\n  Sample details (first 3):")
        for i, detail in enumerate(result.details[:3], 1):
            print(f"    {i}. [{detail.severity.name}] {detail.name}")
            print(f"       {detail.reason}")
        
        return {
            'is_pass': result.is_pass,
            'value': result.value,
            'detail_count': len(result.details),
            'severities': dict(severities),
            'success': True
        }
        
    except Exception as e:
        print(f"  ERROR: {str(e)}")
        import traceback
        print("\nFull traceback:")
        traceback.print_exc()
        return {
            'success': False,
            'error': str(e)
        }

def compare_results(golden, aggressive, test_name):
    """Compare two results."""
    print(f"\n{'='*70}")
    print(f"COMPARISON: {test_name}")
    print(f"{'='*70}")
    
    if not golden['success'] or not aggressive['success']:
        print("  SKIP - One or both tests failed")
        return False
    
    # Compare is_pass
    is_pass_ok = golden['is_pass'] == aggressive['is_pass']
    print(f"  is_pass: G={golden['is_pass']}, A={aggressive['is_pass']} -> {'OK' if is_pass_ok else 'DIFF'}")
    
    # Compare value
    value_ok = golden['value'] == aggressive['value']
    print(f"  value: G={golden['value']}, A={aggressive['value']} -> {'OK' if value_ok else 'DIFF'}")
    
    # Compare detail count
    count_ok = golden['detail_count'] == aggressive['detail_count']
    print(f"  detail_count: G={golden['detail_count']}, A={aggressive['detail_count']} -> {'OK' if count_ok else 'DIFF'}")
    
    # Compare severities
    sev_ok = golden['severities'] == aggressive['severities']
    print(f"  severities: {'OK' if sev_ok else 'DIFF'}")
    if not sev_ok:
        print(f"    Golden:     {golden['severities']}")
        print(f"    Aggressive: {aggressive['severities']}")
    
    all_ok = is_pass_ok and value_ok and count_ok and sev_ok
    
    if all_ok:
        print(f"\n  Result: PASS - Results are identical")
    else:
        print(f"\n  Result: FAIL - Results differ")
    
    return all_ok

# Load checker classes
print("\nLoading checkers...")
print(f"  Golden:     {golden_file}")
print(f"  Aggressive: {aggressive_file}")

try:
    GoldenChecker = load_checker_from_file(golden_file)
    print("  Golden checker loaded OK")
except Exception as e:
    print(f"  ERROR loading Golden: {e}")
    sys.exit(1)

try:
    AggressiveChecker = load_checker_from_file(aggressive_file)
    print("  Aggressive checker loaded OK")
except Exception as e:
    print(f"  ERROR loading Aggressive: {e}")
    sys.exit(1)

# Run all tests
results = []

for test_name, config in test_configs.items():
    print(f"\n\n{'#'*70}")
    print(f"# TEST CASE: {test_name}")
    print(f"{'#'*70}")
    
    # Run Golden
    golden_result = run_checker(GoldenChecker, config, f"Golden - {test_name}")
    
    # Run Aggressive
    aggressive_result = run_checker(AggressiveChecker, config, f"Aggressive - {test_name}")
    
    # Compare
    match = compare_results(golden_result, aggressive_result, test_name)
    
    results.append({
        'test': test_name,
        'match': match,
        'golden_success': golden_result['success'],
        'aggressive_success': aggressive_result['success']
    })

# Final summary
print(f"\n\n{'='*70}")
print("FINAL SUMMARY")
print(f"{'='*70}")

total = len(results)
passed = sum(1 for r in results if r['match'])
golden_failed = sum(1 for r in results if not r['golden_success'])
aggressive_failed = sum(1 for r in results if not r['aggressive_success'])

print(f"\nTest Results:")
for r in results:
    status = 'PASS' if r['match'] else 'FAIL'
    g_status = 'OK' if r['golden_success'] else 'ERROR'
    a_status = 'OK' if r['aggressive_success'] else 'ERROR'
    print(f"  [{status}] {r['test']}: Golden={g_status}, Aggressive={a_status}")

print(f"\nStatistics:")
print(f"  Total tests: {total}")
print(f"  Passed: {passed}/{total}")
print(f"  Failed: {total - passed}/{total}")
print(f"  Golden errors: {golden_failed}")
print(f"  Aggressive errors: {aggressive_failed}")

# Code metrics
print(f"\n{'='*70}")
print("CODE METRICS")
print(f"{'='*70}")

golden_lines = len(open(golden_file, encoding='utf-8').read().splitlines())
aggressive_lines = len(open(aggressive_file, encoding='utf-8').read().splitlines())
saved = golden_lines - aggressive_lines

print(f"  Golden:     {golden_lines} lines")
print(f"  Aggressive: {aggressive_lines} lines")
print(f"  Saved:      {saved} lines ({saved/golden_lines*100:.1f}% reduction)")

# Final verdict
print(f"\n{'='*70}")
if passed == total:
    print("VERDICT: ALL TESTS PASSED - Aggressive refactoring successful!")
    print(f"{'='*70}")
    sys.exit(0)
else:
    print(f"VERDICT: {total - passed}/{total} TESTS FAILED - Need fixes")
    print(f"{'='*70}")
    sys.exit(1)
