# WebUI Developer Deployment Guide

## 开发者环境说明

### 工作环境结构

每个开发者会收到一个独立的 workspace 目录（通过 `pack_for_developer.py` 打包）：

```
<developer_name>_workspace_<timestamp>/
├── .git/                          # 独立的 git 仓库
├── CHECKLIST/
│   ├── Check_modules/
│   │   ├── common/               # 共享工具
│   │   ├── 10.0_STA_DCD_CHECK/  # 参考模块（完整实现）
│   │   └── <assigned_modules>/  # 分配给该开发者的模块
│   ├── Work/
│   │   ├── assignments/         # 只包含该开发者的任务分配
│   │   └── run.ps1              # 执行脚本
│   └── ...
├── Tool/
│   └── AutoGenChecker/
│       └── web_ui/              # ✅ WebUI 已包含在打包中
│           ├── frontend/
│           ├── backend/
│           └── start_all.ps1
└── ssg_aai_lego/                # Python 工具库

```

---

## 环境配置问题与解决方案

### ❌ 原有问题

1. **WORKSPACES_DIR 路径错误**
   - 当前硬编码：`C:\Users\yuyin\Desktop\CHECKLIST_V4\Tool\Mdispatcher\workspaces`
   - 开发者环境：workspace 就是当前目录，不存在 `Mdispatcher/workspaces/` 目录

2. **REASSIGN_EXCEL_PATH 不可访问**
   - 当前硬编码：yuyin 的 OneDrive 路径
   - 开发者无法访问 Admin 的 OneDrive

3. **Git 仓库路径假设**
   - 假设每个开发者有一个独立的 workspace 子目录
   - 实际：开发者的 workspace 根目录就是 git 仓库根目录

---

## ✅ 解决方案

### 方案 1：自动检测开发者环境（推荐）

修改 `dashboard.py` 的路径解析逻辑：

```python
def get_workspaces_dir():
    """
    智能检测工作目录：
    - 如果在 Admin 环境（Mdispatcher/workspaces 存在）→ 返回 workspaces 目录
    - 如果在 Developer 环境（当前目录是 workspace）→ 返回当前 workspace 根目录
    """
    # 1. 环境变量优先
    env_path = os.environ.get("WORKSPACES_DIR")
    if env_path and os.path.exists(env_path):
        return env_path
    
    # 2. 检测是否在 Admin 环境
    project_root = Path(__file__).resolve().parents[4]  # 到达 CHECKLIST_V4
    admin_workspaces = project_root / "Tool" / "Mdispatcher" / "workspaces"
    if admin_workspaces.exists():
        return str(admin_workspaces)
    
    # 3. 检测是否在 Developer 环境（workspace 根目录）
    # 从 web_ui/backend/api/dashboard.py 向上到 workspace 根目录
    # Tool/AutoGenChecker/web_ui/backend/api/dashboard.py -> ../../../../..
    workspace_root = Path(__file__).resolve().parents[5]
    
    # 验证是否是有效的 workspace（检查特征文件）
    if (workspace_root / "CHECKLIST").exists() and (workspace_root / ".git").exists():
        return str(workspace_root)
    
    # 4. Fallback（向后兼容）
    return r"C:\Users\yuyin\Desktop\CHECKLIST_V4\Tool\Mdispatcher\workspaces"


def get_excel_path():
    """
    智能检测 Excel 文件路径：
    - Admin 环境：OneDrive 路径
    - Developer 环境：Tool/AutoGenChecker/ 下的副本
    """
    # 1. 环境变量优先
    env_path = os.environ.get("REASSIGN_EXCEL_PATH")
    if env_path and os.path.exists(env_path):
        return env_path
    
    # 2. 检测 Developer 环境中的副本
    workspace_root = Path(__file__).resolve().parents[5]
    dev_excel = workspace_root / "Tool" / "AutoGenChecker" / "DR3_SSCET_BE_Check_List_v0.2_20260105.xlsx"
    if dev_excel.exists():
        return str(dev_excel)
    
    # 3. 检测 Admin 环境中的项目副本
    project_root = Path(__file__).resolve().parents[4]
    admin_excel = project_root / "Tool" / "AutoGenChecker" / "DR3_SSCET_BE_Check_List_v0.2_20260105.xlsx"
    if admin_excel.exists():
        return str(admin_excel)
    
    # 4. Fallback to OneDrive
    return r"C:\Users\yuyin\OneDrive - Cadence Design Systems Inc\2025\Checklist\RELEASE\DOC\DR3_SSCET_BE_Check_List_v0.2_20260105.xlsx"
```

### 方案 2：环境配置文件

在 `web_ui/backend/` 添加 `.env` 文件支持：

```env
# Admin Environment
ENVIRONMENT=admin
WORKSPACES_DIR=C:\Users\yuyin\Desktop\CHECKLIST_V4\Tool\Mdispatcher\workspaces
REASSIGN_EXCEL_PATH=C:\Users\yuyin\OneDrive\...\DR3_SSCET_BE_Check_List_v0.2_20260105.xlsx

# Developer Environment
ENVIRONMENT=developer
WORKSPACE_ROOT=.
REASSIGN_EXCEL_PATH=../../Tool/AutoGenChecker/DR3_SSCET_BE_Check_List_v0.2_20260105.xlsx
```

---

## 修改清单

### 1. `dashboard.py` - 路径解析逻辑

**需要修改的函数：**
- `get_workspaces_dir()` - 自动检测 Admin/Developer 环境
- `get_excel_path()` - 查找 Excel 副本
- `get_git_info()` - 适配单仓库模式（Developer 环境下当前目录就是仓库）

### 2. `pack_for_developer.py` - 添加 Excel 复制

确保打包时将 Excel 文件复制到开发者 workspace：

```python
# 在 pack_for_developer() 函数中添加
print("   -> Copying Excel assignment file...")
excel_src = tool_root / "AutoGenChecker" / "DR3_SSCET_BE_Check_List_v0.2_20260105.xlsx"
if excel_src.exists():
    excel_dest = staging_dir / "Tool" / "AutoGenChecker" / "DR3_SSCET_BE_Check_List_v0.2_20260105.xlsx"
    shutil.copy(excel_src, excel_dest)
```

### 3. Developer 说明文档

在 `README_DEV.md` 添加 WebUI 使用说明：

```markdown
## WebUI 使用指南

### 启动 WebUI

cd Tool/AutoGenChecker/web_ui
.\start_all.ps1

### 访问地址
- Frontend: http://localhost:5173
- Backend API: http://localhost:8001

### 功能说明
- **Dashboard**: 查看你的任务进度和 commit 历史
- **My Tasks**: 查看分配给你的所有检查项
- **Dispatch**: 查看任务分配情况
- **Collection**: 收集信息辅助工具
```

---

## 测试计划

### Admin 环境测试（yuyin）
```powershell
cd C:\Users\yuyin\Desktop\CHECKLIST_V4\Tool\AutoGenChecker\web_ui
.\start_all.ps1

# 验证：
# ✅ Dashboard 显示所有开发者
# ✅ Team Progress 显示完整统计
# ✅ 可以切换查看每个开发者的状态
# ✅ Excel 数据从 OneDrive 读取
```

### Developer 环境测试（模拟）
```powershell
cd C:\Users\yuyin\Desktop\CHECKLIST_V4\Tool\Mdispatcher\workspaces\chenghao_yao_workspace_20260107_160649\Tool\AutoGenChecker\web_ui
.\start_all.ps1

# 验证：
# ✅ Dashboard 只显示当前开发者（chenghao_yao）的信息
# ✅ My Tasks 显示分配给该开发者的任务
# ✅ Git 信息正确（从当前仓库读取）
# ✅ Excel 数据从 Tool/AutoGenChecker/ 下的副本读取
```

---

## 部署步骤

### Step 1: 修改 dashboard.py 路径逻辑
### Step 2: 修改 pack_for_developer.py 添加 Excel 复制
### Step 3: 更新 README_DEV.md 添加 WebUI 说明
### Step 4: 测试 Admin 环境
### Step 5: 测试 Developer 环境（用已有 workspace）
### Step 6: 重新打包并分发给开发者

---

## 常见问题

**Q: 开发者的 Excel 文件会过期吗？**
A: 是的。建议定期重新打包或让开发者手动更新 Excel 副本。也可以考虑使用共享网络路径。

**Q: 开发者可以看到其他人的任务吗？**
A: 可以，但只能看到自己的详细 commit 历史。这是为了团队透明度。

**Q: 开发者的 WebUI 会自动 git fetch 吗？**
A: 会，但只 fetch 当前仓库（不会像 Admin 一样 fetch 所有 workspaces）。

**Q: 如何处理 Excel 文件更新？**
A: 
- Admin: 直接修改 OneDrive 文件，WebUI 自动读取
- Developer: 需要从 Admin 获取新的 Excel 文件副本
