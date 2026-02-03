"""Test dashboard API directly"""
import sys
sys.path.insert(0, r"C:\Users\yuyin\Desktop\CHECKLIST_V4\Tool\AutoGenChecker")

from api.dashboard import get_git_info
import subprocess
import re

workspace_path = r"C:\Users\yuyin\Desktop\CHECKLIST_V4\Tool\Mdispatcher\workspaces\chenghao_yao_workspace_20260107_160649"

# Simulate remote branches dict
remote_branches = {
    "assignment/chenghao_yao_20260107": "6e6ecfa5"
}

print("Testing get_git_info...")
result = get_git_info(workspace_path, "chenghao_yao", remote_branches)

print(f"\nResults:")
print(f"  Assignment Branch: {result['assignment_branch']}")
print(f"  Last Commit Time: {result['last_commit_time']}")
print(f"  Last Commit Message: {result['last_commit_message']}")
print(f"  Modified Items Count: {result['modified_files_count']}")
print(f"  Modified Items: {result.get('modified_items', [])}")

# Verify the logic manually
print("\n\nManual verification:")
diff_result = subprocess.run(
    ["git", "diff", "--name-only", "origin/master", f"origin/{result['assignment_branch']}"],
    cwd=workspace_path,
    capture_output=True,
    text=True,
    timeout=10
)

if diff_result.returncode == 0:
    files = diff_result.stdout.strip().split("\n")
    check_modules_files = [f for f in files if "CHECKLIST/Check_modules/" in f]
    
    # Extract item IDs
    item_ids = set()
    for file_path in check_modules_files:
        match = re.search(r'(IMP-\d+-\d+-\d+-\d+|STA-\d+-\d+-\d+-\d+|MIG-\w+-\d+-\d+-\d+-\d+)', file_path)
        if match:
            item_ids.add(match.group(1))
    
    print(f"  Total files changed: {len(files)}")
    print(f"  Check_modules files: {len(check_modules_files)}")
    print(f"  Unique item IDs: {sorted(item_ids)}")
    print(f"  Item count: {len(item_ids)}")
