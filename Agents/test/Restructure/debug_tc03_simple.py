"""Simple direct comparison of Golden vs CodeGen TC03 outputs"""
import sys
from pathlib import Path
import importlib.util
import yaml

acl_root = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(acl_root / "Latest" / "CHECKLIST" / "Check_modules" / "common"))
sys.path.insert(0, str(acl_root / "CHECKLIST" / "Tool" / "Agent" / "test" / "Restructure" / "Check_modules" / "common"))

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

result_g = golden.execute_check()

# CodeGen checker
codegen_path = Path(__file__).parent / "Check_10_0_0_00_aggressive.py"
CodeGenClass = load_checker(codegen_path)
codegen = CodeGenClass()
codegen.root = acl_root
codegen.item_data = config
codegen._initialized = True
codegen.log_path = logs / f'{codegen.item_id}.log'
codegen.rpt_path = reports / f'{codegen.item_id}.rpt'

result_c = codegen.execute_check()

# Compare detail by detail
print("="*70)
print("GOLDEN DETAILS:")
print("="*70)
for i, d in enumerate(result_g.details):
    print(f"\n[{i}] {d.severity.name}: {d.name}")
    print(f"    file: {d.file_path}")
    print(f"    line: {d.line_number}")
    print(f"    reason: {d.reason}")

print("\n" + "="*70)
print("CODEGEN DETAILS:")
print("="*70)
for i, d in enumerate(result_c.details):
    print(f"\n[{i}] {d.severity.name}: {d.name}")
    print(f"    file: {d.file_path}")
    print(f"    line: {d.line_number}")
    print(f"    reason: {d.reason}")

print("\n" + "="*70)
print("ANALYSIS:")
print("="*70)
print(f"Golden has {len(result_g.details)} details")
print(f"CodeGen has {len(result_c.details)} details")

# Find which detail is in Golden but not in CodeGen
golden_names = [d.name for d in result_g.details]
codegen_names = [d.name for d in result_c.details]

print(f"\nGolden names: {golden_names}")
print(f"CodeGen names: {codegen_names}")

missing_in_codegen = [n for n in golden_names if n not in codegen_names]
extra_in_codegen = [n for n in codegen_names if n not in golden_names]

if missing_in_codegen:
    print(f"\n❌ Missing in CodeGen: {missing_in_codegen}")
if extra_in_codegen:
    print(f"\n⚠️ Extra in CodeGen: {extra_in_codegen}")
