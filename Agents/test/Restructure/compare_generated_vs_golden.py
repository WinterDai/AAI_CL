#!/usr/bin/env python3
"""
Compare Generated vs Golden checker outputs
"""
import sys
import shutil
from pathlib import Path

# Setup paths
script_dir = Path(__file__).parent
project_root = script_dir.parents[4]
common_dir = project_root / 'CHECKLIST' / 'CHECKLIST' / 'Check_modules' / 'common'
sys.path.insert(0, str(common_dir))

# Output directories
output_dir = script_dir / "comparison_outputs"
generated_dir = output_dir / "generated"
golden_dir = output_dir / "golden"

# Create output directories
generated_dir.mkdir(parents=True, exist_ok=True)
golden_dir.mkdir(parents=True, exist_ok=True)

def run_generated():
    """Run generated checker and copy outputs"""
    print("="*70)
    print("Running Generated Checker...")
    print("="*70)
    
    sys.path.insert(0, str(script_dir / "test_output_no_golden"))
    from generated_checker import NetlistSpefVersionChecker as GeneratedChecker
    
    checker = GeneratedChecker()
    checker.init_checker()
    result = checker.execute_check()
    checker.write_output(result)
    
    # Copy outputs
    latest_dir = project_root / "Latest" / "CHECKLIST" / "Check_modules" / "10.0_STA_DCD_CHECK"
    log_file = latest_dir / "logs" / "IMP-10-0-0-00.log"
    rpt_file = latest_dir / "reports" / "IMP-10-0-0-00.rpt"
    
    if log_file.exists():
        shutil.copy2(log_file, generated_dir / "IMP-10-0-0-00.log")
    if rpt_file.exists():
        shutil.copy2(rpt_file, generated_dir / "IMP-10-0-0-00.rpt")
    
    print(f"✅ Generated outputs saved to: {generated_dir}")
    return result

def run_golden():
    """Run Golden checker and copy outputs"""
    print("\n" + "="*70)
    print("Running Golden Checker...")
    print("="*70)
    
    # Remove generated import to avoid conflict
    if 'generated_checker' in sys.modules:
        del sys.modules['generated_checker']
    
    # Load Golden script with fix
    golden_script = script_dir / 'Check_10_0_0_00_aggressive.py'
    code = open(golden_script, encoding='utf-8').read()
    code = code.replace(
        "    checker = init_checker()\n    checker.execute_check()\n    checker.write_output()",
        "    checker = init_checker()\n    result = checker.execute_check()\n    checker.write_output(result)"
    )
    
    # Provide __file__ in exec context
    golden_globals = {'__file__': str(golden_script), '__name__': '__main__'}
    exec(code, golden_globals)
    
    # Golden has already run via exec
    # Copy outputs
    latest_dir = project_root / "Latest" / "CHECKLIST" / "Check_modules" / "10.0_STA_DCD_CHECK"
    log_file = latest_dir / "logs" / "IMP-10-0-0-00.log"
    rpt_file = latest_dir / "reports" / "IMP-10-0-0-00.rpt"
    
    if log_file.exists():
        shutil.copy2(log_file, golden_dir / "IMP-10-0-0-00.log")
    if rpt_file.exists():
        shutil.copy2(rpt_file, golden_dir / "IMP-10-0-0-00.rpt")
    
    print(f"✅ Golden outputs saved to: {golden_dir}")

def compare_outputs():
    """Compare generated vs golden outputs"""
    print("\n" + "="*70)
    print("Comparison Results")
    print("="*70)
    
    for filename in ["IMP-10-0-0-00.log", "IMP-10-0-0-00.rpt"]:
        gen_file = generated_dir / filename
        gold_file = golden_dir / filename
        
        if not gen_file.exists():
            print(f"❌ Generated {filename} not found")
            continue
        if not gold_file.exists():
            print(f"❌ Golden {filename} not found")
            continue
        
        gen_content = gen_file.read_text(encoding='utf-8')
        gold_content = gold_file.read_text(encoding='utf-8')
        
        if gen_content == gold_content:
            print(f"✅ {filename}: IDENTICAL")
        else:
            print(f"⚠️  {filename}: DIFFERENT")
            print(f"   Generated: {len(gen_content)} chars")
            print(f"   Golden: {len(gold_content)} chars")
            
            # Show first difference
            for i, (gc, gc2) in enumerate(zip(gen_content, gold_content)):
                if gc != gc2:
                    context_start = max(0, i-50)
                    context_end = min(len(gen_content), i+50)
                    print(f"\n   First difference at position {i}:")
                    print(f"   Generated: ...{gen_content[context_start:context_end]}...")
                    print(f"   Golden:    ...{gold_content[context_start:context_end]}...")
                    break

if __name__ == "__main__":
    try:
        result = run_generated()
        run_golden()
        compare_outputs()
        
        print("\n" + "="*70)
        print("Comparison Complete!")
        print(f"Outputs saved in: {output_dir}")
        print("="*70)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
