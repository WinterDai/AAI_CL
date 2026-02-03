import sys
from pathlib import Path

# Simulate running from developer workspace
dev_workspace = Path(r"C:\Users\yuyin\Desktop\CHECKLIST_V4\Tool\Mdispatcher\workspaces\chenghao_yao_workspace_20260107_160649")
dashboard_path = dev_workspace / "Tool" / "AutoGenChecker" / "web_ui" / "backend" / "api"

sys.path.insert(0, str(dashboard_path))

# Mock __file__ for testing
import os
original_file = __file__
os.chdir(dashboard_path)

from dashboard import get_workspaces_dir, get_excel_path

print("=" * 80)
print("Developer Environment Path Detection Test (chenghao_yao)")
print("=" * 80)
workspaces_dir = get_workspaces_dir()
excel_path = get_excel_path()

print(f"WORKSPACES_DIR: {workspaces_dir}")
print(f"  -> Should be: {dev_workspace.parent}")
print(f"  -> Match: {Path(workspaces_dir) == dev_workspace.parent}")
print()
print(f"EXCEL_PATH: {excel_path}")
expected_excel = dev_workspace / "Tool" / "AutoGenChecker" / "DR3_SSCET_BE_Check_List_v0.2_20260105.xlsx"
print(f"  -> Should be: {expected_excel}")
print(f"  -> Match: {Path(excel_path) == expected_excel}")
print(f"  -> File exists: {Path(excel_path).exists()}")
print("=" * 80)
