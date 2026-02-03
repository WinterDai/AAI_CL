# Path structure analysis
from pathlib import Path

dashboard_path = Path(r"C:\Users\yuyin\Desktop\CHECKLIST_V4\Tool\AutoGenChecker\web_ui\backend\api\dashboard.py")

print("Path hierarchy from dashboard.py:")
print(f"[0] dashboard.py: {dashboard_path}")
print(f"[1] api/: {dashboard_path.parent}")
print(f"[2] backend/: {dashboard_path.parents[1]}")
print(f"[3] web_ui/: {dashboard_path.parents[2]}")
print(f"[4] AutoGenChecker/: {dashboard_path.parents[3]}")
print(f"[5] Tool/: {dashboard_path.parents[4]}")
print(f"[6] CHECKLIST_V4/: {dashboard_path.parents[5]}")

print("\n" + "=" * 80)
print("Developer workspace structure:")
dev_path = Path(r"C:\Users\yuyin\Desktop\CHECKLIST_V4\Tool\Mdispatcher\workspaces\chenghao_yao_workspace_20260107_160649\Tool\AutoGenChecker\web_ui\backend\api\dashboard.py")
print(f"[0] dashboard.py: {dev_path}")
print(f"[5] Tool/: {dev_path.parents[4]}")
print(f"[6] <workspace_root>: {dev_path.parents[5]}")
print(f"[7] workspaces/: {dev_path.parents[6]}")
