"""
Test CodeGen Aggressive Refactoring vs Golden

This script compares the CodeGen aggressive refactoring with Golden implementation
to ensure behavior is identical across all 4 Type scenarios.
"""

import sys
from pathlib import Path
import importlib.util

# Setup paths
acl_root = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(acl_root / "Latest" / "CHECKLIST" / "Check_modules" / "common"))
sys.path.insert(0, str(acl_root / "CHECKLIST" / "Tool" / "Agent" / "test" / "Restructure" / "Check_modules" / "common"))

def load_checker_module(file_path: Path, module_name: str):
    """Dynamically load a checker module"""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def load_yaml_config(file_path: Path):
    """Load YAML configuration"""
    import yaml
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def run_checker(checker_class, config, checker_path):
    """Run a checker with given configuration"""
    try:
        checker = checker_class()
        # Manually set up the checker (avoid DATA_INTERFACE dependency)
        checker.root = checker_path.parents[5]  # ACL root
        checker.item_data = config
        checker._initialized = True
        
        # Initialize output paths manually
        module_dir = checker.root / 'Check_modules' / checker.check_module
        logs = module_dir / 'logs'
        reports = module_dir / 'reports'
        
        logs.mkdir(parents=True, exist_ok=True)
        reports.mkdir(parents=True, exist_ok=True)
        
        checker.log_path = logs / f'{checker.item_id}.log'
        checker.rpt_path = reports / f'{checker.item_id}.rpt'
        
        result = checker.execute_check()
        return result, None
    except Exception as e:
        import traceback
        error_msg = f"{str(e)}\n{traceback.format_exc()}"
        return None, error_msg

def compare_results(golden_result, test_result, test_name):
    """Compare two CheckResult objects"""
    print(f"\nCOMPARISON: {test_name}")
    
    # Compare is_pass
    g_pass = golden_result.is_pass
    t_pass = test_result.is_pass
    pass_match = "OK" if g_pass == t_pass else "MISMATCH!"
    print(f"  is_pass: G={g_pass}, T={t_pass} -> {pass_match}")
    
    # Compare value
    g_value = golden_result.value
    t_value = test_result.value
    value_match = "OK" if str(g_value) == str(t_value) else "MISMATCH!"
    print(f"  value: G={g_value}, T={t_value} -> {value_match}")
    
    # Compare detail count
    g_count = len(golden_result.details)
    t_count = len(test_result.details)
    count_match = "OK" if g_count == t_count else "MISMATCH!"
    print(f"  detail_count: G={g_count}, T={t_count} -> {count_match}")
    
    # Compare severities
    g_severities = {}
    for detail in golden_result.details:
        sev = detail.severity.name
        g_severities[sev] = g_severities.get(sev, 0) + 1
    
    t_severities = {}
    for detail in test_result.details:
        sev = detail.severity.name
        t_severities[sev] = t_severities.get(sev, 0) + 1
    
    sev_match = "OK" if g_severities == t_severities else "MISMATCH!"
    print(f"  severities: {sev_match}")
    if g_severities != t_severities:
        print(f"    Golden: {g_severities}")
        print(f"    Test: {t_severities}")
    
    # Overall result
    all_match = (g_pass == t_pass and str(g_value) == str(t_value) and 
                 g_count == t_count and g_severities == t_severities)
    
    result = "PASS - Results are identical" if all_match else "FAIL - Results differ"
    print(f"  Result: {result}")
    
    return all_match

def main():
    print("CODEGEN AGGRESSIVE REFACTORING TEST - Golden vs CodeGen Aggressive")
    print("="*70)
    
    # Load checker modules
    print("\nLoading checkers...")
    restructure_dir = acl_root / "CHECKLIST" / "Tool" / "Agent" / "test" / "Restructure"
    golden_dir = acl_root / "Golden"
    
    golden_path = golden_dir / "IMP-10-0-0-00.py"
    codegen_aggressive_path = restructure_dir / "Check_10_0_0_00_aggressive.py"
    
    print(f"  Golden:     {golden_path}")
    print(f"  CodeGen Aggressive: {codegen_aggressive_path}")
    
    golden_module = load_checker_module(golden_path, "golden_checker")
    codegen_module = load_checker_module(codegen_aggressive_path, "codegen_aggressive_checker")
    
    golden_checker_class = golden_module.NetlistSpefVersionChecker
    codegen_checker_class = codegen_module.NetlistSpefVersionChecker
    
    print(f"  Golden checker loaded: {hasattr(golden_checker_class(), 'execute_check')}")
    print(f"  CodeGen Aggressive checker loaded: {hasattr(codegen_checker_class(), 'execute_check')}")
    
    # Test cases
    test_cases = [
        ("TC01_Type1", restructure_dir / "TC01_Type1.yaml"),
        ("TC02_Type2", restructure_dir / "TC02_Type2.yaml"),
        ("TC03_Type3", restructure_dir / "TC03_Type3.yaml"),
        ("TC04_Type4", restructure_dir / "TC04_Type4.yaml"),
    ]
    
    results = []
    
    for test_name, config_path in test_cases:
        print(f"\n{'='*70}")
        print(f"# TEST CASE: {test_name}")
        print(f"{'='*70}")
        
        config = load_yaml_config(config_path)
        
        # Run Golden
        print(f"\nTesting: Golden - {test_name}")
        golden_result, golden_error = run_checker(golden_checker_class, config, golden_path)
        if golden_error:
            print(f"  ERROR: {golden_error}")
            results.append((test_name, "Golden=ERROR", "CodeGen=?"))
            continue
        else:
            print(f"  is_pass: {golden_result.is_pass}")
            print(f"  value: {golden_result.value}")
            print(f"  details: {len(golden_result.details)} items")
            severities = {}
            for detail in golden_result.details:
                sev = detail.severity.name
                severities[sev] = severities.get(sev, 0) + 1
            print(f"  severities: {', '.join(f'{k}={v}' for k, v in severities.items())}")
        
        # Run CodeGen Aggressive
        print(f"\nTesting: CodeGen Aggressive - {test_name}")
        codegen_result, codegen_error = run_checker(codegen_checker_class, config, codegen_aggressive_path)
        if codegen_error:
            print(f"  ERROR: {codegen_error[:500]}")
            results.append((test_name, "Golden=OK", "CodeGen=ERROR"))
            continue
        else:
            print(f"  is_pass: {codegen_result.is_pass}")
            print(f"  value: {codegen_result.value}")
            print(f"  details: {len(codegen_result.details)} items")
            if codegen_result.details:
                detail = codegen_result.details[0]
                print(f"  First detail severity: {detail.severity.name}, reason: {detail.reason[:80] if detail.reason else 'N/A'}")
            severities = {}
            for detail in codegen_result.details:
                sev = detail.severity.name
                severities[sev] = severities.get(sev, 0) + 1
            print(f"  severities: {', '.join(f'{k}={v}' for k, v in severities.items())}")
        
        # Compare
        match = compare_results(golden_result, codegen_result, test_name)
        if match:
            results.append((test_name, "Golden=OK", "CodeGen=OK"))
        else:
            results.append((test_name, "Golden=OK", "CodeGen=FAIL"))
    
    # Final summary
    print(f"\n{'='*70}")
    print("FINAL SUMMARY")
    print(f"{'='*70}")
    print("\nTest Results:")
    for test_name, g_status, c_status in results:
        status = "PASS" if c_status == "CodeGen=OK" else "FAIL"
        print(f"  [{status}] {test_name}: {g_status}, {c_status}")
    
    print(f"\nStatistics:")
    total = len(results)
    passed = sum(1 for _, _, c in results if c == "CodeGen=OK")
    failed = total - passed
    print(f"  Total tests: {total}")
    print(f"  Passed: {passed}/{total} ({100*passed//total if total > 0 else 0}%)")
    print(f"  Failed: {failed}/{total}")
    
    # Count lines
    print(f"\nCODE METRICS")
    try:
        with open(golden_path, 'r', encoding='utf-8') as f:
            golden_lines = len(f.readlines())
        with open(codegen_aggressive_path, 'r', encoding='utf-8') as f:
            codegen_lines = len(f.readlines())
        saved = golden_lines - codegen_lines
        percent = (saved / golden_lines * 100) if golden_lines > 0 else 0
        print(f"  Golden:     {golden_lines} lines")
        print(f"  CodeGen Aggressive: {codegen_lines} lines")
        if saved > 0:
            print(f"  Saved:      {saved} lines ({percent:.1f}% reduction)")
        else:
            print(f"  Added:      {-saved} lines ({-percent:.1f}% increase)")
    except Exception as e:
        print(f"  Could not count lines: {e}")
    
    # Verdict
    print(f"\n{'='*70}")
    if passed == total:
        print(f"VERDICT: ALL TESTS PASSED - CodeGen aggressive refactoring successful!")
    else:
        print(f"VERDICT: {failed} TEST(S) FAILED - Review and fix required")
    print(f"{'='*70}")

if __name__ == '__main__':
    main()
