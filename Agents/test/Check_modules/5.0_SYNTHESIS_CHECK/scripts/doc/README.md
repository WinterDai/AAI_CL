# Checker Documentation Index

## 已重构 Checker 文档

所有文档位于：`Check_modules/5.0_SYNTHESIS_CHECK/scripts/doc/`

| Checker ID | 检查项 | 文档链接 | 支持类型 |
|------------|--------|----------|----------|
| IMP-5-0-0-00 | 库模型检查 | [IMP-5-0-0-00.md](IMP-5-0-0-00.md) | ✅ All Types |
| IMP-5-0-0-01 | LEF 数据检查 | [IMP-5-0-0-01.md](IMP-5-0-0-01.md) | ✅ All Types |
| IMP-5-0-0-02 | QRC 技术文件检查 | [IMP-5-0-0-02.md](IMP-5-0-0-02.md) | ✅ All Types |
| IMP-5-0-0-03 | 库 Corner 检查 | [IMP-5-0-0-03.md](IMP-5-0-0-03.md) | ✅ All Types |
| IMP-5-0-0-05 | 未解析引用检查 | [IMP-5-0-0-05.md](IMP-5-0-0-05.md) | ✅ All Types |
| IMP-5-0-0-06 | 空模块检查 | [IMP-5-0-0-06.md](IMP-5-0-0-06.md) | ✅ All Types |
| IMP-5-0-0-07 | SDC违规检查 | [IMP-5-0-0-07.md](IMP-5-0-0-07.md) | ✅ All Types |
| IMP-5-0-0-09 | Latch推断检查 | [IMP-5-0-0-09.md](IMP-5-0-0-09.md) | ✅ All Types |
| IMP-5-0-0-10 | 禁用单元检查 | [IMP-5-0-0-10.md](IMP-5-0-0-10.md) | ✅ All Types |

---

### [IMP-5-0-0-00: 库模型检查器](IMP-5-0-0-00.md)
**检查项：** 确认综合使用 lib 模型进行时序分析  
**输入文件：** `qor.rpt`  
**检查内容：** 提取并验证加载的库文件列表  
**常用类型：** Type 1（信息报告）

---

### [IMP-5-0-0-01: LEF 数据检查器](IMP-5-0-0-01.md)
**检查项：** 确认综合使用 LEF 数据进行 PLE 优化  
**输入文件：** `check.rpt`  
**检查内容：** 验证 `lib_lef_consistency_check_enable` 配置  
**常用类型：** Type 1（状态报告）或 Type 2（强制启用）

---

### [IMP-5-0-0-02: QRC 技术文件检查器](IMP-5-0-0-02.md)
**检查项：** 确认综合使用 QRC 技术文件进行 RC 数据提取  
**输入文件：** `qor.rpt`, `synthesis.log`  
**检查内容：** 解析 domain → rc_corner → qrc_tech 文件路径链  
**常用类型：** Type 4（布尔+豁免，允许特定 domain 不使用 QRC）  
**复杂度：** ⭐⭐⭐⭐⭐（最复杂的 checker）

---

### [IMP-5-0-0-03: 库 Corner 检查器](IMP-5-0-0-03.md)
**检查项：** 确认目标标准单元库 corner 正确  
**输入文件：** `qor.rpt`  
**检查内容：** 提取并验证库 corner（如 cworst_CCworst_T）  
**常用类型：** Type 2（严格验证）或 Type 3（允许多个 corner）

---

### [IMP-5-0-0-05: 未解析引用检查器](IMP-5-0-0-05.md)
**检查项：** 确认未解析引用为空或已正确豁免  
**输入文件：** `synthesis.log`  
**检查内容：** 从 Check Design Report 中提取未解析引用  
**常用类型：** Type 4（布尔+豁免，管理黑盒模块）  
**应用场景：** 第三方 IP、硬核宏、黑盒模块管理

---

### [IMP-5-0-0-06: 空模块检查器](IMP-5-0-0-06.md)
**检查项：** 确认空模块为空或已正确说明  
**输入文件：** `synthesis.log`  
**检查内容：** 从 Check Design Report 中提取空模块列表  
**常用类型：** Type 4（布尔+豁免）或 Type 2（严格零空模块）  
**应用场景：** 测试桩模块、遗留设计清理、质量门控

---

### [IMP-5-0-0-07: SDC 违规检查器](IMP-5-0-0-07.md)
**检查项：** 确认没有 SDC 违规或错误（max cap、max transition 等）  
**输入文件：** `synthesis.log` (优先 `*_generic.log`)  
**检查内容：** 解析 read_sdc 命令结果，提取失败的约束命令  
**常用类型：** Type 4（布尔+豁免）或 Type 2（严格零违规）  
**应用场景：** 约束质量检查、测试模式约束豁免、生产流程门控

---

### [IMP-5-0-0-09: Latch 推断检查器](IMP-5-0-0-09.md)
**检查项：** 确认综合推断的 latch 已正确文档化  
**输入文件：** `latch.rpt`  
**检查内容：** 提取 latch 单元名称，验证是否在文档化列表中  
**常用类型：** Type 2（严格验证）或 Type 4（布尔+豁免）  
**应用场景：** 防止意外 latch、时钟门控验证、同步设计质量检查

---

### [IMP-5-0-0-10: 禁用单元检查器](IMP-5-0-0-10.md)
**检查项：** 确认综合网表中未实例化禁用单元  
**输入文件：** `gates.rpt`  
**检查内容：** 验证单元名称是否匹配禁用模式（支持正则）  
**常用类型：** Type 3（值比较+豁免）或 Type 4（布尔+豁免）  
**特殊性：** 配置来自两个文件（IMP-1-0-0-02 + IMP-5-0-0-10）

---

## 文档使用指南

### 快速查找

**按检查对象分类：**
- **库文件相关：** IMP-5-0-0-00（库模型），IMP-5-0-0-01（LEF），IMP-5-0-0-03（Corner）
- **RC 提取相关：** IMP-5-0-0-02（QRC 技术文件）
- **网表质量相关：** IMP-5-0-0-05（未解析引用），IMP-5-0-0-06（空模块），IMP-5-0-0-09（Latch 推断），IMP-5-0-0-10（禁用单元）
- **约束质量相关：** IMP-5-0-0-07（SDC 违规）

**按复杂度分类：**
- **简单：** IMP-5-0-0-00, IMP-5-0-0-01, IMP-5-0-0-03, IMP-5-0-0-09
- **中等：** IMP-5-0-0-05, IMP-5-0-0-06, IMP-5-0-0-07, IMP-5-0-0-10
- **复杂：** IMP-5-0-0-02（多文件关联解析）

**按常用 Type 分类：**
- **Type 1（信息报告）：** IMP-5-0-0-00, IMP-5-0-0-01
- **Type 2（严格验证）：** IMP-5-0-0-03, IMP-5-0-0-06（生产流程），IMP-5-0-0-07（生产流程），IMP-5-0-0-09
- **Type 3（值+豁免）：** IMP-5-0-0-09, IMP-5-0-0-10
- **Type 4（布尔+豁免）：** IMP-5-0-0-02, IMP-5-0-0-05, IMP-5-0-0-06, IMP-5-0-0-07, IMP-5-0-0-09

---

## 文档结构

每个 checker 文档包含以下章节：

1. **概述**
   - 检查项描述
   - 检查类型
   - 输入文件

2. **检查逻辑**
   - 输入文件解析方法
   - 违例定义
   - 特殊处理逻辑

3. **自动类型检测**
   - Type 1/2/3/4 检测规则

4. **Type 1-4 详细说明**
   - 每种类型的配置示例
   - 检查行为
   - 输出示例（PASS/FAIL/WAIVED 场景）

5. **配置错误处理**
   - 缺失文件处理
   - 异常情况说明

6. **输出文件说明**
   - Log 文件格式
   - Report 文件格式

7. **使用建议**
   - 不同场景的推荐配置

8. **常见问题**
   - FAQ 和故障排查

9. **维护建议**
   - 最佳实践
   - 注意事项

---

## 相关文档

### 通用文档
- **[QUICK_REFERENCE.md](../../../../doc/QUICK_REFERENCE.md)** - 快速参考卡片
- **[checker_type_configuration_guide.md](../../../../doc/checker_type_configuration_guide.md)** - 完整配置指南
- **[refactoring_summary_2025-11-26.md](../../../../doc/refactoring_summary_2025-11-26.md)** - 重构总结

### 代码文件
- **BaseChecker:** `common/base_checker.py`
- **OutputFormatter:** `common/output_formatter.py`
- **Checker 脚本:** `Check_modules/5.0_SYNTHESIS_CHECK/scripts/checker/IMP-5-0-0-*.py`

---

## 使用示例

### 场景 1：首次配置某个 checker
1. 打开对应的 checker 文档（如 `IMP-5-0-0-05.md`）
2. 阅读"检查逻辑"章节，理解 checker 的工作原理
3. 根据项目需求选择合适的 Type（参考"使用建议"章节）
4. 复制对应 Type 的配置示例到 YAML 文件
5. 根据实际情况修改配置参数

### 场景 2：理解 checker 输出
1. 查看 log 或 report 文件中的错误
2. 打开对应 checker 文档
3. 查找相关 Type 的"输出示例"章节
4. 对照示例理解输出含义

### 场景 3：添加豁免
1. 打开 checker 文档（如 `IMP-5-0-0-10.md`）
2. 查看 Type 3 或 Type 4 的配置示例
3. 参考"豁免最佳实践"章节
4. 添加 waive_items，包含清晰的 reason

### 场景 4：故障排查
1. 遇到错误时，打开对应 checker 文档
2. 查看"常见问题"章节
3. 如果问题不在列表中，检查"配置错误处理"章节
4. 参考"检查逻辑"章节，理解 checker 的解析流程

---

## 文档维护

### 更新频率
- **Checker 逻辑变更时：** 立即更新对应文档
- **新增 Type 支持时：** 添加新的 Type 示例
- **用户反馈时：** 补充常见问题和故障排查

### 贡献指南
1. 保持文档结构一致（使用现有模板）
2. 提供真实的配置示例和输出
3. 包含多种场景（PASS/FAIL/WAIVED）
4. 添加清晰的表格和图示
5. 更新文档索引（本文件）

---

## 最新更新

### 2025-11-27: 统一配置验证机制
**提交哈希：** `f48e381`

#### 核心改进
- **新增 ConfigurationError 异常类**
  - 在 `base_checker.py` 中实现统一的配置错误处理机制
  - 当 `input_files` 为空或缺失时自动抛出异常，携带完整的 CheckResult
  
- **增强 validate_input_files() 方法**
  - 添加 `raise_on_empty` 参数（默认 True）
  - 自动检测并报告配置错误
  - 向后兼容旧代码（设置 `raise_on_empty=False`）

- **更新所有 Checker (IMP-5-0-0-00 到 IMP-5-0-0-19)**
  - 在 `execute_check()` 中添加 try-except 捕获 ConfigurationError
  - 移除冗余的 input_files 验证代码
  - 统一错误处理流程：配置错误 → 文件缺失 → 正常检查

- **data_interface.py 升级到 v1.2**
  - 支持 Linux/Windows 跨平台路径转换
  - 自动检测操作系统并应用正确的路径分隔符
  - 智能识别 CHECKLIST 根目录路径

#### 技术优势
- ✅ 代码复用性提高：配置验证逻辑集中在 base_checker
- ✅ 错误信息一致：所有 checker 使用相同的 CONFIG_ERROR 格式
- ✅ 维护性提升：新 checker 自动继承配置验证功能
- ✅ 跨平台支持：同一套代码可在 Windows 和 Linux 环境运行

#### 影响的文件
- `Check_modules/common/base_checker.py` (+45行)
- `Check_modules/5.0_SYNTHESIS_CHECK/scripts/checker/*.py` (19个文件)
- `Project_config/scripts/data_interface.py` (v1.2)

---

**索引版本：** 1.1  
**最后更新：** 2025-11-27  
**维护者：** yuyin
