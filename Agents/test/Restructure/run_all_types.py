"""
运行Check_10_0_0_00_aggressive.py生成4种Type的reports
"""
import sys
from pathlib import Path
import yaml

# Add common module path
test_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(test_dir / 'Check_modules' / 'common'))

# Import aggressive checker
import importlib.util
spec = importlib.util.spec_from_file_location("aggressive_checker", test_dir / 'Check_10_0_0_00_aggressive.py')
aggressive_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(aggressive_module)
AggressiveChecker = aggressive_module.NetlistSpefVersionChecker


def load_yaml_config(yaml_path):
    """Load YAML configuration file."""
    with open(yaml_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def run_type(config_file, type_name, type_suffix):
    """Run checker with specified config and save report."""
    print(f"\n{'='*70}")
    print(f"Running Type: {type_name}")
    print(f"Config: {config_file}")
    print(f"{'='*70}")
    
    # Load configuration
    config = load_yaml_config(config_file)
    
    print(f"DEBUG: Config loaded:")
    print(f"  requirements.value: {config.get('requirements', {}).get('value')}")
    print(f"  pattern_items: {config.get('requirements', {}).get('pattern_items')}")
    print(f"  waivers.value: {config.get('waivers', {}).get('value')}")
    print(f"  waive_items: {config.get('waivers', {}).get('waive_items')}")
    
    # Create checker and set configuration
    checker = AggressiveChecker()
    
    # Initialize checker paths (this will load default item_data)
    checker.init_checker(Path(__file__))
    
    # IMPORTANT: Set custom config AFTER init_checker to override default
    checker.item_data = config
    
    # Clear cache to ensure fresh execution for each type
    cache_file = checker.cache_dir / f"{checker.item_id}.pkl"
    if cache_file.exists():
        cache_file.unlink()
    
    # Update report path to include type suffix
    original_rpt = checker.rpt_path
    custom_rpt = original_rpt.parent / f"{original_rpt.stem}_{type_suffix}.rpt"
    checker.rpt_path = custom_rpt
    
    # Also update log path for consistency
    original_log = checker.log_path
    custom_log = original_log.parent / f"{original_log.stem}_{type_suffix}.log"
    checker.log_path = custom_log
    
    print(f"DEBUG: Updated paths:")
    print(f"  rpt_path: {checker.rpt_path}")
    print(f"  log_path: {checker.log_path}")
    
    # Execute check
    try:
        # Debug: Check what type is detected
        check_type = checker.detect_checker_type()
        print(f"DEBUG: Detected check type: {check_type}")
        
        result = checker.execute_check()
        
        # Write output to log and report files
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


def main():
    """Run all 4 types."""
    test_configs = [
        ('TC01_Type1.yaml', 'Type 1: Boolean Check (no waiver)', 'Type1'),
        ('TC02_Type2.yaml', 'Type 2: Value Check (no waiver)', 'Type2'),
        ('TC03_Type3.yaml', 'Type 3: Value Check with Waiver', 'Type3'),
        ('TC04_Type4.yaml', 'Type 4: Boolean Check with Waiver', 'Type4'),
    ]
    
    results = []
    for config_file, type_name, type_suffix in test_configs:
        config_path = test_dir / config_file
        success = run_type(config_path, type_name, type_suffix)
        results.append((type_name, success))
    
    # Summary
    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")
    for type_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {type_name}")
    
    passed = sum(1 for _, s in results if s)
    print(f"\nOverall: {passed}/{len(results)} types completed successfully")


if __name__ == "__main__":
    main()
