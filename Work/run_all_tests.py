"""
Run all unit tests for L0-L6
"""

import sys
import subprocess
from pathlib import Path

def run_layer_tests(layer_name, test_file):
    """Run tests for a single layer"""
    layer_dir = Path(__file__).parent / layer_name
    test_path = layer_dir / test_file
    
    if not test_path.exists():
        print(f"⚠️  {layer_name}: Test file not found")
        return False
    
    print(f"\n{'='*80}")
    print(f"Running {layer_name} tests...")
    print('='*80)
    
    try:
        result = subprocess.run(
            [sys.executable, str(test_path)],
            cwd=str(layer_dir),
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            print(f"✅ {layer_name} tests PASSED")
            return True
        else:
            print(f"❌ {layer_name} tests FAILED")
            print(result.stdout)
            print(result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏱️  {layer_name} tests TIMEOUT")
        return False
    except Exception as e:
        print(f"❌ {layer_name} tests ERROR: {e}")
        return False


def main():
    print("\n" + "="*80)
    print("UNIT TEST SUITE: L0-L6 Layers")
    print("="*80)
    
    layers = [
        ('L0_Config', 'test_l0.py'),
        ('L1_IO', 'test_l1.py'),
        ('L2_Parsing', 'test_l2.py'),
        ('L3_Check', 'test_l3.py'),
        ('L4_Waiver', 'test_l4.py'),
        ('L5_Output', 'test_l5.py'),
        ('L6_Report', 'test_l6.py')
    ]
    
    results = []
    for layer_name, test_file in layers:
        passed = run_layer_tests(layer_name, test_file)
        results.append((layer_name, passed))
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    
    for layer_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{layer_name:20s} {status}")
    
    print(f"\nTotal: {passed_count}/{total_count} layers passed")
    
    if passed_count == total_count:
        print("\n✅ ALL UNIT TESTS PASSED\n")
        return 0
    else:
        print("\n❌ SOME TESTS FAILED\n")
        return 1


if __name__ == '__main__':
    sys.exit(main())
