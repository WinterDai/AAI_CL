"""Debug TC03 specifically"""
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

golden_result = golden.execute_check()

print("="*70)
print("GOLDEN CHECKER - TC03 Type3")
print("="*70)
print(f"is_pass: {golden_result.is_pass}")
print(f"value: {golden_result.value}")
print(f"details ({len(golden_result.details)} items):")
for i, detail in enumerate(golden_result.details):
    print(f"  [{i}] {detail.severity.name}: {detail.name}")
    print(f"      reason: {detail.reason}")

# CodeGen checker
codegen_path = Path(__file__).parent / "Check_10_0_0_00_aggressive.py"
CodeGenClass = load_checker(codegen_path)
codegen = CodeGenClass()
codegen.root = acl_root
codegen.item_data = config
codegen._initialized = True

module_dir = codegen.root / 'Check_modules' / codegen.check_module
codegen.log_path = logs / f'{codegen.item_id}.log'
codegen.rpt_path = reports / f'{codegen.item_id}.rpt'

codegen_result = codegen.execute_check()

print("\n" + "="*70)
print("CODEGEN AGGRESSIVE CHECKER - TC03 Type3")
print("="*70)
print(f"is_pass: {codegen_result.is_pass}")
print(f"value: {codegen_result.value}")
print(f"details ({len(codegen_result.details)} items):")
for i, detail in enumerate(codegen_result.details):
    print(f"  [{i}] {detail.severity.name}: {detail.name}")
    print(f"      reason: {detail.reason}")
