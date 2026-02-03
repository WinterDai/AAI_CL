# Developer Setup Guide

## WebUI 开发者环境配置指南

### 概述

WebUI 会在您的本地环境自动查找所需资源（workspace 目录和 Excel 文件）。系统使用以下优先级顺序：

1. **环境变量** - 最高优先级
2. **相对路径** - 从项目根目录自动查找
3. **默认路径** - 管理员路径（仅作为后备）

### 配置选项

#### 选项 1：使用环境变量（推荐用于自定义路径）

如果您的 workspace 和 Excel 文件在非标准位置，可以设置环境变量：

**PowerShell:**
```powershell
# 临时设置（当前会话）
$env:WORKSPACES_DIR = "D:\MyProjects\workspaces"
$env:REASSIGN_EXCEL_PATH = "D:\MyData\DR3_SSCET_BE_Check_List_v0.2_20260105.xlsx"

# 永久设置（用户级）
[System.Environment]::SetEnvironmentVariable("WORKSPACES_DIR", "D:\MyProjects\workspaces", "User")
[System.Environment]::SetEnvironmentVariable("REASSIGN_EXCEL_PATH", "D:\MyData\DR3_SSCET_BE_Check_List_v0.2_20260105.xlsx", "User")
```

**命令提示符 (CMD):**
```cmd
set WORKSPACES_DIR=D:\MyProjects\workspaces
set REASSIGN_EXCEL_PATH=D:\MyData\DR3_SSCET_BE_Check_List_v0.2_20260105.xlsx
```

#### 选项 2：使用标准项目结构（推荐用于团队协作）

如果您按照标准项目结构组织，无需任何配置：

```
CHECKLIST_V4/
  ├── Tool/
  │   ├── Mdispatcher/
  │   │   └── workspaces/        # workspace 目录
  │   └── AutoGenChecker/
  │       └── web_ui/
  ├── Project_config/
  │   └── collaterals/
  │       └── DR3_SSCET_BE_Check_List_v0.2_20260105.xlsx  # Excel 文件
```

系统会自动找到这些路径！

#### 选项 3：使用后备默认路径

如果以上都不适用，系统会使用管理员默认路径（可能需要访问权限）。

### 快速开始

1. **克隆项目到您的本地：**
   ```bash
   git clone <repository-url> CHECKLIST_V4
   cd CHECKLIST_V4
   ```

2. **获取 Excel 文件（联系管理员）：**
   - 将 `DR3_SSCET_BE_Check_List_v0.2_20260105.xlsx` 放到 `Project_config/collaterals/`

3. **确保 workspace 目录存在：**
   ```bash
   mkdir -p Tool/Mdispatcher/workspaces
   ```

4. **启动 WebUI：**
   ```bash
   cd Tool/AutoGenChecker/web_ui
   
   # 启动后端
   cd backend
   uvicorn app:app --reload --port 8000
   
   # 启动前端（新终端）
   cd ../frontend
   npm install
   npm run dev
   ```

5. **访问 WebUI：**
   ```
   http://localhost:5173
   ```

### 功能说明

#### Dashboard 视图

**开发者视图（默认）：**
- 显示您分配的任务统计
- 实时 git 提交记录
- 今日工作项
- 任务进度

**管理员视图：**
- 团队整体统计（模块数、任务数）
- 状态分布（已完成、进行中、未开始）
- 团队成员进度
- 开发者状态监控

切换视图：点击右上角 `[Developer ▼]` 选择开发者或点击 `[Admin]`

#### My Tasks 页面

显示分配给您的所有任务：
- 按模块分组
- 显示状态和截止日期
- 快速操作按钮（View Details, Mark Complete, Update Status）

#### 资源未找到时的行为

- **workspaces 目录不存在**：Dashboard 显示空状态，git 信息不可用
- **Excel 文件不存在**：My Tasks 页面显示提示信息，Dashboard 仅显示 git 数据

### 路径检测逻辑

系统使用以下函数自动检测路径：

```python
def get_workspaces_dir():
    # 1. 检查环境变量
    env_path = os.environ.get("WORKSPACES_DIR")
    if env_path and os.path.exists(env_path):
        return env_path
    
    # 2. 尝试相对路径（从项目根目录）
    project_root = Path(__file__).parent.parent.parent.parent.parent
    relative_path = project_root / "Tool" / "Mdispatcher" / "workspaces"
    if relative_path.exists():
        return str(relative_path)
    
    # 3. 后备默认路径
    return r"C:\Users\yuyin\Desktop\CHECKLIST_V4\Tool\Mdispatcher\workspaces"
```

### 常见问题

**Q: Dashboard 显示 "No data available"**
- 检查 Excel 文件是否存在
- 确认 Excel 文件路径正确
- 查看浏览器控制台错误信息

**Q: git 提交信息不显示**
- 确认 workspaces 目录存在
- 检查对应开发者的 workspace 是否已创建
- 确认 git 仓库已初始化

**Q: My Tasks 页面为空**
- 检查 Excel 文件中 Re-assign 表是否有您的任务
- 确认 Owner 列（F列）是否包含您的名字
- 刷新页面（点击 Dashboard 的 Refresh 按钮）

**Q: 如何切换到管理员视图？**
- 点击右上角 `[Admin]` 按钮
- 管理员视图显示所有团队成员的数据

### 技术支持

遇到问题请联系：
- 项目管理员：yuyin
- 提交 Issue：[GitHub Issues]

### 更新日志

**v1.0 (2026-01-14)**
- ✅ 动态路径检测
- ✅ Excel 集成
- ✅ git 提交监控
- ✅ 开发者/管理员双视图
- ✅ My Tasks 任务管理
