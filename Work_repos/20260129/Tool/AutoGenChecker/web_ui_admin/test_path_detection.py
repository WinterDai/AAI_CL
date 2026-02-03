import sys
sys.path.insert(0, r'C:\Users\yuyin\Desktop\CHECKLIST_V4\Tool\AutoGenChecker\web_ui\backend\api')

from dashboard import get_workspaces_dir, get_excel_path

print("=" * 80)
print("Admin Environment Path Detection Test")
print("=" * 80)
print(f"WORKSPACES_DIR: {get_workspaces_dir()}")
print(f"EXCEL_PATH: {get_excel_path()}")
print("=" * 80)
