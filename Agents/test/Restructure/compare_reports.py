"""
对比Golden (Check_10_0_0_00_aggressive) vs CodeGen (Check_10_0_0_00_generated) 报告
"""
from pathlib import Path


def compare_reports():
    """Compare Golden and CodeGen reports for all 4 types."""
    test_dir = Path(__file__).resolve().parent
    golden_dir = test_dir / 'Check_modules' / 'IMP' / 'reports'
    codegen_dir = test_dir / 'Check_modules' / '10.0_STA_DCD_CHECK' / 'reports'
    
    types = ['Type1', 'Type2', 'Type3', 'Type4']
    
    print(f"{'='*80}")
    print("Golden vs CodeGen Report Comparison")
    print(f"{'='*80}\n")
    
    for type_name in types:
        golden_file = golden_dir / f'IMP-10-0-0-00_{type_name}.rpt'
        codegen_file = codegen_dir / f'IMP-10-0-0-00_CodeGen_{type_name}.rpt'
        
        print(f"\n{'='*80}")
        print(f"{type_name}")
        print(f"{'='*80}")
        
        if not golden_file.exists():
            print(f"❌ Golden file not found: {golden_file}")
            continue
            
        if not codegen_file.exists():
            print(f"❌ CodeGen file not found: {codegen_file}")
            continue
        
        golden_content = golden_file.read_text(encoding='utf-8')
        codegen_content = codegen_file.read_text(encoding='utf-8')
        
        # Extract key info
        golden_result = "PASS" if golden_content.startswith("PASS") else "FAIL"
        codegen_result = "PASS" if codegen_content.startswith("PASS") else "FAIL"
        
        # Compare
        if golden_result == codegen_result:
            print(f"✅ Result: {golden_result} (Both match)")
        else:
            print(f"❌ Result: Golden={golden_result}, CodeGen={codegen_result}")
        
        # Show first 15 lines of each
        print(f"\n--- Golden (first 15 lines) ---")
        print('\n'.join(golden_content.split('\n')[:15]))
        
        print(f"\n--- CodeGen (first 15 lines) ---")
        print('\n'.join(codegen_content.split('\n')[:15]))
        
        # Show differences
        if golden_content == codegen_content:
            print(f"\n✅ Content identical")
        else:
            print(f"\n⚠️ Content differs (see details above)")


if __name__ == '__main__':
    compare_reports()
