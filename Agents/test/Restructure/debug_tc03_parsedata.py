"""Debug TC03 to see parse_data return values"""
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

# Parse input files first
netlist_info, spef_info, errors = golden._parse_input_files()

print("="*70)
print("GOLDEN - _parse_input_files() output")
print("="*70)
print(f"\nnetlist_info:")
for k, v in netlist_info.items():
    print(f"  {k}: {v}")

print(f"\nspef_info:")
for k, v in spef_info.items():
    print(f"  {k}: {v}")

print(f"\nerrors: {errors}")

# Now call Type 3 logic manually to see parse_data output
print("\n" + "="*70)
print("GOLDEN - Type 3 parse_data() output")
print("="*70)

requirements = golden.get_requirements()
pattern_items = requirements.get('pattern_items', []) if requirements else []
print(f"\npattern_items: {pattern_items}")

all_content = []
if netlist_info.get('tool'):
    all_content.append(f"Tool: {netlist_info['tool']}")
if netlist_info.get('version'):
    all_content.append(f"Genus Synthesis Solution {netlist_info['version']}")
if netlist_info.get('full_timestamp'):
    all_content.append(f"Generated on: {netlist_info['full_timestamp']}")

if spef_info.get('program'):
    all_content.append(f"Program: {spef_info['program']}")
if spef_info.get('version'):
    all_content.append(f"VERSION {spef_info['version']}")
if spef_info.get('date'):
    all_content.append(f"DATE {spef_info['date']}")

print(f"\nall_content:")
for c in all_content:
    print(f"  - {c}")

found_items = {}
missing_items = {}
for pattern in pattern_items:
    found = False
    matched_content = None
    for content in all_content:
        if golden._match_pattern(content, [pattern]):
            found = True
            matched_content = content
            break
    
    if found:
        print(f"\n✓ Pattern '{pattern}' matched: {matched_content}")
        found_items[pattern] = {'matched': matched_content}
    else:
        print(f"\n✗ Pattern '{pattern}' NOT matched")
        missing_items[pattern] = {}

extra_items = {}
if spef_info.get('status') == 'Skipped':
    skip_reason = spef_info.get('skip_reason', 'SPEF reading was skipped')
    extra_items["SPEF Reading was skipped"] = {'reason': skip_reason}
    print(f"\n+ extra_item: 'SPEF Reading was skipped' (status={spef_info.get('status')})")

for error in errors:
    if "SPEF reading was skipped" not in error:
        extra_items[f"Error: {error}"] = {'reason': 'Unexpected error'}

print(f"\nfound_items ({len(found_items)}):")
for k, v in found_items.items():
    print(f"  {k}: {v}")

print(f"\nmissing_items ({len(missing_items)}):")
for k, v in missing_items.items():
    print(f"  {k}: {v}")

print(f"\nextra_items ({len(extra_items)}):")
for k, v in extra_items.items():
    print(f"  {k}: {v}")

# Now do CodeGen
print("\n" + "="*70)
print("CODEGEN - _parse_input_files() output")
print("="*70)

codegen_path = Path(__file__).parent / "Check_10_0_0_00_aggressive.py"
CodeGenClass = load_checker(codegen_path)
codegen = CodeGenClass()
codegen.root = acl_root
codegen.item_data = config
codegen._initialized = True
codegen.log_path = logs / f'{codegen.item_id}.log'
codegen.rpt_path = reports / f'{codegen.item_id}.rpt'

parsed_data = codegen._parse_input_files()
netlist_info_c = parsed_data.get('netlist_info', {})
spef_info_c = parsed_data.get('spef_info', {})
errors_c = parsed_data.get('errors', [])

print(f"\nnetlist_info:")
for k, v in netlist_info_c.items():
    print(f"  {k}: {v}")

print(f"\nspef_info:")
for k, v in spef_info_c.items():
    print(f"  {k}: {v}")

print(f"\nerrors: {errors_c}")
