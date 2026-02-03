#!/usr/bin/env python3
"""
Test runner for generated checker - Run all 4 Types and compare with Golden
"""
import sys
import json
from pathlib import Path

# Add paths
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root / "CHECKLIST" / "CHECKLIST"))
sys.path.insert(0, str(Path(__file__).parent / "test_output_no_golden"))

from generated_checker import NetlistSpefVersionChecker

def run_all_types():
    """Run all 4 types and collect results"""
    item_id = "IMP-10-0-0-00"
    item_desc = "Confirm the netlist/spef version is correct"
    log_file = Path(r"C:\Users\wentao\AAI_local\AAI\Main_Work\ACL\Golden\data\IMP-10-0-0-00\tempus_log\innovus.log")
    
    # Test configurations for each type
    configs = {
        "Type 1": {"requirements": {}, "waivers": {}},
        "Type 2": {"requirements": {"pattern_items": ["23.15-s099_1", "Nov 18 2025"]}, "waivers": {}},
        "Type 3": {"requirements": {"pattern_items": ["23.15-s099_1", "Nov 18 2025"]}, "waivers": {"waive_items": ["23.15-s099_1"]}},
        "Type 4": {"requirements": {}, "waivers": {"waive_items": ["SPEF File"]}},
    }
    
    results = {}
    
    for type_name, config in configs.items():
        type_num = int(type_name.split()[1])
        print(f"\n{'='*70}")
        print(f"Running {type_name}...")
        print(f"{'='*70}")
        
        try:
            # Create and initialize checker (Golden pattern)
            checker = NetlistSpefVersionChecker()
            checker.init_checker()  # Loads config from XML
            
            result = checker.execute_check()
            
            results[type_name] = {
                "status": result.status,
                "value": result.value,
                "details_count": len(result.details),
                "report": result.report
            }
            
            print(f"Status: {result.status}")
            print(f"Value: {result.value}")
            print(f"Details: {len(result.details)} items")
            print("\nReport:")
            print(result.report)
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()
            results[type_name] = {"error": str(e)}
    
    return results

def compare_with_golden():
    """Compare results with Golden version"""
    print(f"\n{'='*70}")
    print("Comparing with Golden version...")
    print(f"{'='*70}")
    
    golden_script = Path(__file__).parent / "Check_10_0_0_00_aggressive.py"
    if not golden_script.exists():
        print(f"⚠️ Golden script not found: {golden_script}")
        return
    
    print(f"Golden script: {golden_script}")
    print("\n[Manual Comparison Required]")
    print("Please run the Golden script separately and compare outputs manually.")

if __name__ == "__main__":
    print("="*70)
    print("CodeGen Output Test: Running All 4 Types")
    print("="*70)
    
    results = run_all_types()
    
    # Save results
    output_file = Path(__file__).parent / "test_output_no_golden" / "test_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\n✅ Results saved to: {output_file}")
    
    # Compare with Golden
    compare_with_golden()
    
    # Summary
    print(f"\n{'='*70}")
    print("Test Summary:")
    print(f"{'='*70}")
    for type_name, result in results.items():
        if "error" in result:
            print(f"  {type_name}: ❌ ERROR")
        else:
            print(f"  {type_name}: ✅ {result['status']}")
