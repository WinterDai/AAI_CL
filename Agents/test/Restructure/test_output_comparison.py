"""
Generate detailed output comparison between Golden and CodeGen Aggressive

This script runs all 4 test cases and generates:
1. Individual output files for each test case
2. Side-by-side comparison report
"""

import sys
from pathlib import Path
import importlib.util
import json

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
        checker.root = checker_path.parents[5]
        checker.item_data = config
        checker._initialized = True
        
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

def format_result_details(result):
    """Format CheckResult details into readable text"""
    lines = []
    lines.append(f"is_pass: {result.is_pass}")
    lines.append(f"value: {result.value}")
    lines.append(f"has_pattern_items: {result.has_pattern_items}")
    lines.append(f"has_waiver_value: {result.has_waiver_value}")
    lines.append(f"\nDetails ({len(result.details)} items):")
    lines.append("-" * 80)
    
    for i, detail in enumerate(result.details, 1):
        lines.append(f"\n[{i}] {detail.severity.name}")
        lines.append(f"    name: {detail.name}")
        lines.append(f"    line_number: {detail.line_number}")
        lines.append(f"    file_path: {detail.file_path}")
        lines.append(f"    reason: {detail.reason}")
    
    # Info groups
    if result.info_groups:
        lines.append(f"\n\nInfo Groups ({len(result.info_groups)} groups):")
        lines.append("-" * 80)
        for group_id, group_data in sorted(result.info_groups.items()):
            lines.append(f"\n{group_id}: {group_data['description']}")
            lines.append(f"  Items: {group_data['items']}")
    
    # Error groups
    if result.error_groups:
        lines.append(f"\n\nError Groups ({len(result.error_groups)} groups):")
        lines.append("-" * 80)
        for group_id, group_data in sorted(result.error_groups.items()):
            lines.append(f"\n{group_id}: {group_data['description']}")
            lines.append(f"  Items: {group_data['items']}")
    
    # Warn groups
    if result.warn_groups:
        lines.append(f"\n\nWarn Groups ({len(result.warn_groups)} groups):")
        lines.append("-" * 80)
        for group_id, group_data in sorted(result.warn_groups.items()):
            lines.append(f"\n{group_id}: {group_data['description']}")
            lines.append(f"  Items: {group_data['items']}")
    
    return "\n".join(lines)

def compare_results_detailed(golden_result, test_result, output_file):
    """Generate detailed side-by-side comparison"""
    lines = []
    lines.append("="*100)
    lines.append("DETAILED COMPARISON REPORT")
    lines.append("="*100)
    
    # High-level comparison
    lines.append("\n" + "="*100)
    lines.append("HIGH-LEVEL COMPARISON")
    lines.append("="*100)
    
    lines.append(f"\nis_pass:")
    lines.append(f"  Golden:    {golden_result.is_pass}")
    lines.append(f"  CodeGen:   {test_result.is_pass}")
    lines.append(f"  Match:     {'✓ YES' if golden_result.is_pass == test_result.is_pass else '✗ NO'}")
    
    lines.append(f"\nvalue:")
    lines.append(f"  Golden:    {golden_result.value}")
    lines.append(f"  CodeGen:   {test_result.value}")
    lines.append(f"  Match:     {'✓ YES' if str(golden_result.value) == str(test_result.value) else '✗ NO'}")
    
    lines.append(f"\nDetail Count:")
    lines.append(f"  Golden:    {len(golden_result.details)}")
    lines.append(f"  CodeGen:   {len(test_result.details)}")
    lines.append(f"  Match:     {'✓ YES' if len(golden_result.details) == len(test_result.details) else '✗ NO'}")
    
    # Severity breakdown
    g_severities = {}
    for detail in golden_result.details:
        sev = detail.severity.name
        g_severities[sev] = g_severities.get(sev, 0) + 1
    
    t_severities = {}
    for detail in test_result.details:
        sev = detail.severity.name
        t_severities[sev] = t_severities.get(sev, 0) + 1
    
    lines.append(f"\nSeverity Breakdown:")
    all_sevs = sorted(set(list(g_severities.keys()) + list(t_severities.keys())))
    for sev in all_sevs:
        g_count = g_severities.get(sev, 0)
        t_count = t_severities.get(sev, 0)
        match = '✓' if g_count == t_count else '✗'
        lines.append(f"  {sev:8s}: Golden={g_count:2d}, CodeGen={t_count:2d}  {match}")
    
    # Details comparison
    lines.append("\n" + "="*100)
    lines.append("DETAILS COMPARISON")
    lines.append("="*100)
    
    max_len = max(len(golden_result.details), len(test_result.details))
    for i in range(max_len):
        lines.append(f"\n--- Detail #{i+1} ---")
        
        if i < len(golden_result.details):
            g = golden_result.details[i]
            lines.append(f"  Golden:  [{g.severity.name}] {g.name}")
            lines.append(f"           Reason: {g.reason[:100]}...")
        else:
            lines.append(f"  Golden:  (no detail #{i+1})")
        
        if i < len(test_result.details):
            t = test_result.details[i]
            lines.append(f"  CodeGen: [{t.severity.name}] {t.name}")
            lines.append(f"           Reason: {t.reason[:100]}...")
        else:
            lines.append(f"  CodeGen: (no detail #{i+1})")
        
        # Check match
        if i < len(golden_result.details) and i < len(test_result.details):
            g = golden_result.details[i]
            t = test_result.details[i]
            match = (g.severity == t.severity and g.name == t.name and g.reason == t.reason)
            lines.append(f"  Match:   {'✓ YES' if match else '✗ NO'}")
    
    # Groups comparison
    lines.append("\n" + "="*100)
    lines.append("GROUPS COMPARISON")
    lines.append("="*100)
    
    lines.append(f"\nInfo Groups:")
    lines.append(f"  Golden:    {len(golden_result.info_groups or {})} groups")
    lines.append(f"  CodeGen:   {len(test_result.info_groups or {})} groups")
    
    lines.append(f"\nError Groups:")
    lines.append(f"  Golden:    {len(golden_result.error_groups or {})} groups")
    lines.append(f"  CodeGen:   {len(test_result.error_groups or {})} groups")
    
    lines.append(f"\nWarn Groups:")
    lines.append(f"  Golden:    {len(golden_result.warn_groups or {})} groups")
    lines.append(f"  CodeGen:   {len(test_result.warn_groups or {})} groups")
    
    # Overall verdict
    lines.append("\n" + "="*100)
    lines.append("VERDICT")
    lines.append("="*100)
    
    all_match = (
        golden_result.is_pass == test_result.is_pass and
        str(golden_result.value) == str(test_result.value) and
        len(golden_result.details) == len(test_result.details) and
        g_severities == t_severities
    )
    
    if all_match:
        lines.append("\n✓✓✓ PASS - Results are IDENTICAL ✓✓✓")
    else:
        lines.append("\n✗✗✗ FAIL - Results DIFFER ✗✗✗")
    
    lines.append("="*100)
    
    # Write to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines))
    
    return all_match

def main():
    print("GENERATING DETAILED OUTPUT COMPARISON")
    print("="*100)
    
    # Load checker modules
    restructure_dir = acl_root / "CHECKLIST" / "Tool" / "Agent" / "test" / "Restructure"
    golden_dir = acl_root / "Golden"
    output_dir = restructure_dir / "test_outputs"
    output_dir.mkdir(exist_ok=True)
    
    golden_path = golden_dir / "IMP-10-0-0-00.py"
    codegen_path = restructure_dir / "Check_10_0_0_00_aggressive.py"
    
    print(f"\nLoading checkers...")
    print(f"  Golden:     {golden_path}")
    print(f"  CodeGen:    {codegen_path}")
    
    golden_module = load_checker_module(golden_path, "golden_checker")
    codegen_module = load_checker_module(codegen_path, "codegen_aggressive_checker")
    
    golden_checker_class = golden_module.NetlistSpefVersionChecker
    codegen_checker_class = codegen_module.NetlistSpefVersionChecker
    
    # Test cases
    test_cases = [
        ("TC01_Type1", restructure_dir / "TC01_Type1.yaml"),
        ("TC02_Type2", restructure_dir / "TC02_Type2.yaml"),
        ("TC03_Type3", restructure_dir / "TC03_Type3.yaml"),
        ("TC04_Type4", restructure_dir / "TC04_Type4.yaml"),
    ]
    
    all_passed = True
    
    for test_name, config_path in test_cases:
        print(f"\n{'='*100}")
        print(f"Processing: {test_name}")
        print(f"{'='*100}")
        
        config = load_yaml_config(config_path)
        
        # Run Golden
        print(f"  Running Golden...")
        golden_result, golden_error = run_checker(golden_checker_class, config, golden_path)
        if golden_error:
            print(f"    ERROR: {golden_error}")
            continue
        
        # Save Golden output
        golden_output_file = output_dir / f"{test_name}_Golden.txt"
        with open(golden_output_file, 'w', encoding='utf-8') as f:
            f.write(format_result_details(golden_result))
        print(f"    Saved: {golden_output_file}")
        
        # Run CodeGen
        print(f"  Running CodeGen Aggressive...")
        codegen_result, codegen_error = run_checker(codegen_checker_class, config, codegen_path)
        if codegen_error:
            print(f"    ERROR: {codegen_error}")
            continue
        
        # Save CodeGen output
        codegen_output_file = output_dir / f"{test_name}_CodeGen.txt"
        with open(codegen_output_file, 'w', encoding='utf-8') as f:
            f.write(format_result_details(codegen_result))
        print(f"    Saved: {codegen_output_file}")
        
        # Generate comparison
        print(f"  Generating comparison...")
        comparison_file = output_dir / f"{test_name}_Comparison.txt"
        passed = compare_results_detailed(golden_result, codegen_result, comparison_file)
        print(f"    Saved: {comparison_file}")
        print(f"    Result: {'✓ PASS' if passed else '✗ FAIL'}")
        
        if not passed:
            all_passed = False
    
    # Summary
    print(f"\n{'='*100}")
    print("SUMMARY")
    print(f"{'='*100}")
    print(f"\nOutput files saved to: {output_dir}")
    print(f"\nGenerated files:")
    print(f"  - {test_name}_Golden.txt (Golden output)")
    print(f"  - {test_name}_CodeGen.txt (CodeGen output)")
    print(f"  - {test_name}_Comparison.txt (Side-by-side comparison)")
    
    if all_passed:
        print(f"\n✓✓✓ ALL TESTS PASSED - Results are IDENTICAL ✓✓✓")
    else:
        print(f"\n✗✗✗ SOME TESTS FAILED - Check comparison files ✗✗✗")
    
    print(f"{'='*100}")

if __name__ == '__main__':
    main()
