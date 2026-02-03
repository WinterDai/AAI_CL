## 概述
<!-- 简要描述这个PR实现了什么功能或修复了什么问题 -->
实现模块: [例如: 7.0_INNOVUS_DESIGN_IN_CHECK]

## 实现的Checkers
<!-- 列出所有已实现的Checker ID及其描述 -->
- [ ] IMP-X-X-X-XX: Description 1
- [ ] IMP-X-X-X-XX: Description 2

## 测试结果
<!-- 描述本地测试的情况 -->
- [ ] 已使用 IP_project_folder 中的样例数据测试
- [ ] 所有Checkers均生成了预期的JSON和Report输出
- [ ] 异常处理测试通过（如文件缺失、格式错误等）

## 变更类型
- [ ] 新功能 (New Feature)
- [ ] 缺陷修复 (Bug Fix)
- [ ] 文档更新 (Documentation)
- [ ] 代码重构 (Refactoring)

## Checklist
<!-- 提交前请确认以下每一项 -->
- [ ] 代码符合 Header Comment 标准 (包含 ID, Author, Date, Logic)
- [ ] 所有Checker类均继承自 `BaseChecker`
- [ ] 使用 `OutputFormatter` 进行结果输出
- [ ] 没有硬编码路径，所有路径均来自配置或参数
- [ ] 代码经过格式化，无明显风格问题
- [ ] 逻辑注释清晰，关键步骤有说明

## 备注
<!-- 任何需要Reviewer特别注意的地方，如特殊的Waiver逻辑或依赖项 -->
