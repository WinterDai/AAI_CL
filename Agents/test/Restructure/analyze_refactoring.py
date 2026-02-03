"""
Deep analysis: Why refactoring didn't achieve expected code reduction.
Detailed line-by-line comparison of Type methods.
"""

import re
from pathlib import Path


def count_lines_in_method(content: str, method_name: str) -> int:
    """Count lines in a specific method"""
    pattern = rf'def {method_name}\(.*?\):'
    match = re.search(pattern, content)
    if not match:
        return 0
    
    start = match.start()
    # Find next method definition or class end
    next_method = re.search(r'\n    def ', content[start + len(match.group()):])
    if next_method:
        end = start + len(match.group()) + next_method.start()
    else:
        end = len(content)
    
    method_content = content[start:end]
    return len([line for line in method_content.splitlines() if line.strip()])


def analyze_type_methods(file_path: Path, label: str):
    """Analyze Type methods in a file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    type_methods = {
        '_execute_type1': count_lines_in_method(content, '_execute_type1'),
        '_execute_type2': count_lines_in_method(content, '_execute_type2'),
        '_execute_type3': count_lines_in_method(content, '_execute_type3'),
        '_execute_type4': count_lines_in_method(content, '_execute_type4'),
    }
    
    # Count helper methods (refactored only)
    helper_methods = {
        '_collect_version_content': count_lines_in_method(content, '_collect_version_content'),
        '_match_patterns_against_content': count_lines_in_method(content, '_match_patterns_against_content'),
        '_build_name_extractor': count_lines_in_method(content, '_build_name_extractor'),
    }
    
    total_type_lines = sum(type_methods.values())
    total_helper_lines = sum(helper_methods.values())
    total_lines = len(content.splitlines())
    
    return {
        'label': label,
        'total_lines': total_lines,
        'type_methods': type_methods,
        'total_type_lines': total_type_lines,
        'helper_methods': helper_methods,
        'total_helper_lines': total_helper_lines,
    }


def main():
    """Run deep analysis"""
    print("="*80)
    print("DEEP ANALYSIS: Why Refactoring Didn't Achieve Expected Reduction")
    print("="*80)
    
    golden_file = Path(r"c:\Users\wentao\AAI_local\AAI\Main_Work\ACL\Golden\IMP-10-0-0-00.py")
    refactored_file = Path(r"C:\Users\wentao\AAI_local\AAI\Main_Work\ACL\CHECKLIST\Tool\Agent\test\Restructure\Check_modules\10.0_STA_DCD_CHECK\scripts\checker\IMP-10-0-0-00.py")
    
    golden_data = analyze_type_methods(golden_file, "Golden")
    refactored_data = analyze_type_methods(refactored_file, "Refactored")
    
    # Report
    print(f"\n{'='*80}")
    print("FILE SIZE COMPARISON")
    print('='*80)
    print(f"Golden total lines: {golden_data['total_lines']}")
    print(f"Refactored total lines: {refactored_data['total_lines']}")
    print(f"Difference: {refactored_data['total_lines'] - golden_data['total_lines']:+d} lines")
    
    print(f"\n{'='*80}")
    print("TYPE METHODS COMPARISON")
    print('='*80)
    
    for method in ['_execute_type1', '_execute_type2', '_execute_type3', '_execute_type4']:
        golden_lines = golden_data['type_methods'][method]
        refactored_lines = refactored_data['type_methods'][method]
        diff = refactored_lines - golden_lines
        status = "SAME" if diff == 0 else f"{diff:+d}"
        print(f"{method:25} Golden: {golden_lines:3} lines | Refactored: {refactored_lines:3} lines | {status}")
    
    print(f"\nTotal Type methods:")
    print(f"  Golden: {golden_data['total_type_lines']} lines")
    print(f"  Refactored: {refactored_data['total_type_lines']} lines")
    print(f"  Difference: {refactored_data['total_type_lines'] - golden_data['total_type_lines']:+d} lines")
    
    print(f"\n{'='*80}")
    print("HELPER METHODS (Refactored Only)")
    print('='*80)
    
    for method, lines in refactored_data['helper_methods'].items():
        if lines > 0:
            print(f"{method:40} {lines:3} lines")
    
    print(f"\nTotal Helper methods: {refactored_data['total_helper_lines']} lines")
    
    # Analysis
    print(f"\n{'='*80}")
    print("ROOT CAUSE ANALYSIS")
    print('='*80)
    
    type_reduction = golden_data['total_type_lines'] - refactored_data['total_type_lines']
    helper_overhead = refactored_data['total_helper_lines']
    net_change = type_reduction - helper_overhead
    
    print(f"\n1. Code extracted from Type methods: {type_reduction} lines")
    print(f"2. Helper methods overhead: {helper_overhead} lines")
    print(f"3. Net code reduction: {net_change:+d} lines")
    
    print(f"\nEFFICIENCY ANALYSIS:")
    if helper_overhead > 0:
        reuse_factor = type_reduction / helper_overhead
        print(f"  Reuse factor: {reuse_factor:.2f}x")
        print(f"  (Each helper line saves {reuse_factor:.2f} lines of duplicated code)")
    
    # Expected vs Actual
    print(f"\n{'='*80}")
    print("EXPECTATION vs REALITY")
    print('='*80)
    print(f"\nExpected reduction (from discussion):")
    print(f"  - Collect content: ~20 lines * 2 uses = 40 lines saved")
    print(f"  - Match patterns: ~20 lines * 2 uses = 40 lines saved")
    print(f"  - Name extractor: ~10 lines * 2 uses = 20 lines saved")
    print(f"  - Total expected: ~100 lines saved")
    
    print(f"\nActual reduction:")
    print(f"  - Type methods reduction: {type_reduction} lines")
    print(f"  - Helper overhead: {helper_overhead} lines")
    print(f"  - Net reduction: {net_change:+d} lines")
    print(f"  - Gap: {100 - abs(net_change)} lines short of expectation")
    
    # Conclusion
    print(f"\n{'='*80}")
    print("CONCLUSION")
    print('='*80)
    
    if net_change < 0:
        print(f"\nREFACTORING FAILED: Code increased by {abs(net_change)} lines")
        print(f"\nReason: Helper method overhead ({helper_overhead} lines) exceeded")
        print(f"        the reduction in Type methods ({type_reduction} lines)")
        print(f"\nRoot Cause:")
        print(f"  - Helper methods are TOO SMALL to justify extraction")
        print(f"  - Not enough reuse (only 2 Type methods use each helper)")
        print(f"  - Docstrings and function definitions add overhead")
    else:
        print(f"\nREFACTORING SUCCEEDED: Code reduced by {net_change} lines")
        print(f"But falls short of {100 - net_change} lines vs expectation")


if __name__ == '__main__':
    main()
