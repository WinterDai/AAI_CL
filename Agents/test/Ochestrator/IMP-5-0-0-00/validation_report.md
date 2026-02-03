# Validation Report: IMP-5-0-0-00

## 概要
- 总测试数: 8
- 有效测试: 8
- CORRECT: 5
- INCORRECT: 3
- UNCERTAIN: 0
- TESTCASE_INVALID: 0

## 整体判定
**FAIL** - 3 个测试失败

## 测试详情
### TC_01
- 盲推预期: PASS
- 实际输出: FAIL
- 判定: **INCORRECT**
- 置信度: HIGH
- 推理: Type 1 positive: 根据配置推理预期为 PASS
- 问题: 预期 PASS，实际 FAIL
- 建议: 检查对应 Type 的执行逻辑

### TC_02
- 盲推预期: FAIL
- 实际输出: FAIL
- 判定: **CORRECT**
- 置信度: HIGH
- 推理: Type 1 negative: 根据配置推理预期为 FAIL

### TC_03
- 盲推预期: PASS
- 实际输出: FAIL
- 判定: **INCORRECT**
- 置信度: HIGH
- 推理: Type 2 positive: 根据配置推理预期为 PASS
- 问题: 预期 PASS，实际 FAIL
- 建议: 检查对应 Type 的执行逻辑

### TC_04
- 盲推预期: FAIL
- 实际输出: FAIL
- 判定: **CORRECT**
- 置信度: HIGH
- 推理: Type 2 negative: 根据配置推理预期为 FAIL

### TC_05
- 盲推预期: WAIVER
- 实际输出: FAIL
- 判定: **INCORRECT**
- 置信度: HIGH
- 推理: Type 3 positive: 根据配置推理预期为 WAIVER
- 问题: 预期 WAIVER，实际 FAIL
- 建议: 检查对应 Type 的执行逻辑

### TC_06
- 盲推预期: FAIL
- 实际输出: FAIL
- 判定: **CORRECT**
- 置信度: HIGH
- 推理: Type 3 negative: 根据配置推理预期为 FAIL

### TC_07
- 盲推预期: FAIL
- 实际输出: FAIL
- 判定: **CORRECT**
- 置信度: HIGH
- 推理: Type 4 positive: 根据配置推理预期为 FAIL

### TC_08
- 盲推预期: FAIL
- 实际输出: FAIL
- 判定: **CORRECT**
- 置信度: HIGH
- 推理: Type 4 negative: 根据配置推理预期为 FAIL

## 发现的问题
- 检查 INCORRECT 测试用例的对应场景
