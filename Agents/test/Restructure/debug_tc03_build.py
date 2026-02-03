"""Check Golden's actual build_complete_output call for Type 3"""
import sys
from pathlib import Path
import importlib.util
import yaml

acl_root = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(acl_root / "Latest" / "CHECKLIST" / "Check_modules" / "common"))

def load_checker(file_path: Path):
    spec = importlib.util.spec_from_file_location("checker", file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.NetlistSpefVersionChecker

# Load config
config_file = Path(__file__).parent / "TC03_Type3.yaml"
with open(config_file, 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

# Golden checker
golden_path = acl_root / "Golden" / "IMP-10-0-0-00.py"
GoldenClass = load_checker(golden_path)
golden = GoldenClass()
golden.root = acl_root
golden.item_data = config
golden._initialized = True

module_dir = golden.root / 'Check_modules' / golden.check_module
logs = module_dir / 'logs'
reports = module_dir / 'reports'
logs.mkdir(parents=True, exist_ok=True)
reports.mkdir(parents=True, exist_ok=True)
golden.log_path = logs / f'{golden.item_id}.log'
golden.rpt_path = reports / f'{golden.item_id}.rpt'

# Intercept build_complete_output
original_build = golden.build_complete_output

def intercepted_build(**kwargs):
    print("="*70)
    print("build_complete_output called with:")
    print("="*70)
    for key, value in kwargs.items():
        if isinstance(value, dict):
            print(f"\n{key} ({len(value)} items):")
            for k, v in list(value.items())[:5]:  # Show first 5
                print(f"  {k}: {v}")
            if len(value) > 5:
                print(f"  ... and {len(value)-5} more")
        elif isinstance(value, list):
            print(f"\n{key} ({len(value)} items): {value}")
        else:
            print(f"\n{key}: {value}")
    
    result = original_build(**kwargs)
    
    print("\n" + "="*70)
    print(f"Result: is_pass={result.is_pass}, value={result.value}")
    print(f"Details ({len(result.details)} items):")
    for i, detail in enumerate(result.details):
        print(f"  [{i}] {detail.severity.name}: {detail.name}")
        print(f"      reason: {detail.reason}")
    print("="*70)
    
    return result

golden.build_complete_output = intercepted_build

# Execute Type 3
result = golden.execute_check()
