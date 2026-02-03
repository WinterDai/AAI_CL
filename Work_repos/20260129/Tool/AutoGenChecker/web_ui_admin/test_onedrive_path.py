import os
import sys
from pathlib import Path

sys.path.insert(0, r'C:\Users\yuyin\Desktop\CHECKLIST_V4\Tool\AutoGenChecker\web_ui\backend\api')

print("=" * 80)
print("OneDrive 环境变量检测")
print("=" * 80)

# 检查 OneDrive 环境变量
onedrive = os.environ.get("OneDrive")
onedrive_commercial = os.environ.get("OneDriveCommercial")

print(f"OneDrive: {onedrive}")
print(f"OneDriveCommercial: {onedrive_commercial}")
print()

# 测试路径构建
if onedrive_commercial:
    test_path = Path(onedrive_commercial) / "2025" / "Checklist" / "RELEASE" / "DOC" / "DR3_SSCET_BE_Check_List_v0.2_20260105.xlsx"
    print(f"构建的路径: {test_path}")
    print(f"文件是否存在: {test_path.exists()}")
elif onedrive:
    # 尝试构建商业版路径
    onedrive_parent = Path(onedrive).parent
    commercial = onedrive_parent / "OneDrive - Cadence Design Systems Inc"
    print(f"尝试商业版路径: {commercial}")
    print(f"目录是否存在: {commercial.exists()}")
    
    if commercial.exists():
        test_path = commercial / "2025" / "Checklist" / "RELEASE" / "DOC" / "DR3_SSCET_BE_Check_List_v0.2_20260105.xlsx"
        print(f"构建的路径: {test_path}")
        print(f"文件是否存在: {test_path.exists()}")

print()
print("=" * 80)
print("实际 get_excel_path() 返回值")
print("=" * 80)

from dashboard import get_excel_path
excel_path = get_excel_path()
print(f"Excel 路径: {excel_path}")
print(f"文件存在: {Path(excel_path).exists()}")
