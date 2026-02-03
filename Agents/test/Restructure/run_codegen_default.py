"""
运行Check_10_0_0_00_generated.py使用默认YAML配置（Type 2 with waiver=0）
"""
import sys
from pathlib import Path

# Add common module path
test_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(test_dir / 'Check_modules' / 'common'))

# Import CodeGen checker
import importlib.util
spec = importlib.util.spec_from_file_location("codegen_checker", test_dir / 'Check_10_0_0_00_generated.py')
codegen_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(codegen_module)
CodeGenChecker = codegen_module.NetlistSpefVersionChecker


def main():
    """Run checker with default YAML configuration."""
    print("="*70)
    print("Running CodeGen with Default YAML Config")
    print("="*70)
    
    # Create checker
    checker = CodeGenChecker()
    
    # Initialize with default config (will load from inputs/items/IMP-10-0-0-00.yaml)
    checker.init_checker(Path(__file__))
    
    # Clear cache
    cache_file = checker.cache_dir / f"{checker.item_id}.pkl"
    if cache_file.exists():
        cache_file.unlink()
        print(f"Cache cleared: {cache_file}")
    
    # Check what type is detected
    check_type = checker.detect_checker_type()
    print(f"Detected check type: {check_type}")
    print(f"Config:")
    print(f"  requirements.value: {checker.item_data.get('requirements', {}).get('value')}")
    print(f"  pattern_items: {checker.item_data.get('requirements', {}).get('pattern_items')}")
    print(f"  waivers.value: {checker.item_data.get('waivers', {}).get('value')}")
    print(f"  waive_items: {checker.item_data.get('waivers', {}).get('waive_items')}")
    
    # Execute check
    try:
        result = checker.execute_check()
        
        # Write output
        checker.write_output(result)
        
        print(f"\nResult Summary:")
        print(f"  is_pass: {result.is_pass}")
        print(f"  value: {result.value}")
        print(f"  details count: {len(result.details)}")
        
        # Print details
        print(f"\nDetails:")
        for i, detail in enumerate(result.details, 1):
            print(f"  {i}. [{detail.severity.name}] {detail.name}")
            print(f"     Reason: {detail.reason}")
            if detail.line_number > 0:
                print(f"     Location: {detail.file_path}:{detail.line_number}")
        
        print(f"\n[OK] Report saved to: {checker.rpt_path}")
        return True
        
    except Exception as e:
        print(f"\n[ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
