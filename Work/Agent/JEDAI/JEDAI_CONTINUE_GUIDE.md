# JEDAI + Continue 集成使用指南

## ✅ 部署完成

JEDAI已成功部署到VSCode Continue扩展！

---

## 📋 已配置的模型

| 模型名称 | 用途 | 特点 |
|---------|------|------|
| **gemini-2.5-pro** | 通用任务 | 🌟 推荐，性能强大 |
| **gemini-2.5-flash** | 快速响应 | ⚡ 速度快 |
| **claude-sonnet-4** | 代码编写 | 💻 代码能力强 |
| **claude-3-7-sonnet** | 最新Claude | 🆕 最新版本 |
| **deepseek-r1** | 复杂推理 | 🧠 推理能力强 |
| **llama-3.3** | 开源选择 | 🆓 开源模型 |
| **gpt-5.2** | Azure GPT | 🔷 微软生态 |

---

## 🚀 快速开始

### 1. 重启VSCode
```
方法1: 完全关闭VSCode后重新打开
方法2: Ctrl+Shift+P → "Developer: Reload Window"
```

### 2. 打开Continue面板
```
方法1: Ctrl+Shift+P → "Continue: Open"
方法2: 点击VSCode左侧Continue图标
方法3: 快捷键 Ctrl+L
```

### 3. 选择模型
- 点击Continue面板顶部的模型选择器
- 推荐选择：**gemini-2.5-pro** 或 **claude-sonnet-4**

### 4. 开始使用

**基础对话：**
```
你好，请介绍一下你自己
```

**代码生成：**
```
用Python写一个快速排序函数
```

**代码编辑：**
```
1. 选中代码
2. 按 Ctrl+Shift+L
3. 描述需要的修改
```

**Agent模式（工具调用）：**
```
帮我分析当前项目结构
查找所有Python文件中的TODO
```

---

## 🔑 Token管理

### 当前Token信息
- **有效期**: 10小时
- **生成时间**: 2026-01-16 17:56:05
- **过期时间**: 2026-01-17 03:56:05

### Token过期后更新
```bash
# 1. 获取新Token
python get_jedai_token.py

# 2. 自动部署到Continue
python deploy_continue.py

# 3. 重启VSCode
```

---

## 🛠️ Tool Calling功能

所有配置的模型都支持Tool Calling，可以：
- ✅ 调用Continue内置工具（文件读写、搜索等）
- ✅ 执行终端命令
- ✅ 代码分析和修改
- ✅ 与MCP服务器交互（如已配置）

---

## 📝 配置文件位置

### Windows
```
C:\Users\wentao\.continue\config.yaml
```

### 备份位置
```
工作区: c:\Users\wentao\Desktop\AAI\Main_work\ACL\JEDAI\continue_config_jedai.yaml
```

---

## 🔧 常用命令

```bash
# 获取新Token
python get_jedai_token.py

# 部署配置到Continue
python deploy_continue.py

# 测试JEDAI连接
python jedai_cli.py gemini "Hello"

# 列出所有可用模型
python jedai_cli.py --list
```

---

## ⚡ 使用技巧

### 1. 选择合适的模型
- **复杂代码任务**: claude-sonnet-4
- **快速响应**: gemini-2.5-flash
- **通用任务**: gemini-2.5-pro
- **推理问题**: deepseek-r1

### 2. 使用快捷键
- `Ctrl+L`: 打开Continue聊天
- `Ctrl+Shift+L`: 编辑选中代码
- `Ctrl+I`: 内联编辑

### 3. Context提供
Continue会自动包含：
- 当前打开的文件
- 终端输出
- Git差异
- 错误信息

---

## ❌ 故障排查

### Token失效
**症状**: 401 Unauthorized错误
**解决**: 运行 `python get_jedai_token.py` 获取新Token

### 模型无响应
**症状**: 长时间无响应
**解决**: 
1. 检查网络连接到 sjf-dsgdspr-084.cadence.com:5668
2. 尝试切换其他模型
3. 查看VSCode输出面板的Continue日志

### 配置未生效
**症状**: 看不到JEDAI模型
**解决**:
1. 确认配置文件已更新：`cat ~/.continue/config.yaml`
2. 重启VSCode
3. 重新运行 `python deploy_continue.py`

---

## 📊 API端点信息

- **JEDAI服务器**: http://sjf-dsgdspr-084.cadence.com:5668
- **Chat端点**: /api/copilot/v1/llm/chat/completions
- **认证端点**: /api/v1/security/login

---

## 📚 更多资源

- **JEDAI CLI工具**: `jedai_cli.py`
- **Python集成**: `jedai_langchain.py`
- **代理服务器**: `jedai_proxy.py`
- **MCP服务器**: `jedai_mcp_server.py`

---

## 💡 示例对话

### 代码审查
```
请审查这段代码的性能问题：
[粘贴代码]
```

### 重构建议
```
选中代码后：
"将这个函数重构为更简洁的形式"
```

### 文档生成
```
"为这个函数生成详细的文档字符串"
```

### Bug修复
```
"这段代码有个错误：[错误信息]
请帮我修复"
```

---

## 🎯 下一步

1. ✅ 重启VSCode
2. ✅ 打开Continue面板
3. ✅ 选择模型并开始对话
4. ✅ 尝试Tool Calling功能

**祝使用愉快！** 🚀
