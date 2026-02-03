"""
item_spec 门禁检查器 (Gate)
=============================
在线主链路：L0 结构检查 + L1 执行检查

门禁策略:
- L0: JSON/Schema/必填字段/类型/枚举 → 不通过直接 FAIL
- L1: Regex 编译 + 性能护栏 + 基础功能验证 → 不通过触发修复

使用方式:
    from agents.common.skills.evaluators.item_spec_gate import ItemSpecGate
    
    gate = ItemSpecGate()
    result = gate.check(item_spec_dict)
    if result.passed:
        print("Gate PASSED")
    else:
        print(f"Gate FAILED: {result.failures}")
"""

import json
import re
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Optional


class GateLevel(Enum):
    """门禁级别"""
    L0_STRUCTURE = "L0_STRUCTURE"  # 结构正确性
    L1_EXECUTABLE = "L1_EXECUTABLE"  # 可执行正确性


class FailureCode(Enum):
    """失败代码"""
    # L0 错误
    JSON_INVALID = "JSON_INVALID"
    FIELD_MISSING = "FIELD_MISSING"
    FIELD_TYPE_ERROR = "FIELD_TYPE_ERROR"
    ENUM_INVALID = "ENUM_INVALID"
    EMPTY_REQUIRED = "EMPTY_REQUIRED"
    
    # L1 错误
    REGEX_COMPILE_ERROR = "REGEX_COMPILE_ERROR"
    REGEX_TIMEOUT_RISK = "REGEX_TIMEOUT_RISK"
    LOGIC_INCONSISTENT = "LOGIC_INCONSISTENT"


@dataclass
class GateFailure:
    """门禁失败记录"""
    level: GateLevel
    code: FailureCode
    field_path: str
    message: str
    value: Any = None
    suggestion: str = ""


@dataclass
class GateResult:
    """门禁检查结果"""
    passed: bool
    level_passed: dict = field(default_factory=dict)  # {L0: True, L1: False}
    failures: list = field(default_factory=list)  # List[GateFailure]
    warnings: list = field(default_factory=list)
    check_duration_ms: float = 0
    
    def to_dict(self) -> dict:
        return {
            "passed": self.passed,
            "level_passed": {k.value: v for k, v in self.level_passed.items()},
            "failures": [
                {
                    "level": f.level.value,
                    "code": f.code.value,
                    "field_path": f.field_path,
                    "message": f.message,
                    "value": str(f.value)[:200] if f.value else None,
                    "suggestion": f.suggestion
                }
                for f in self.failures
            ],
            "warnings": self.warnings,
            "check_duration_ms": self.check_duration_ms
        }


class ItemSpecGate:
    """item_spec 门禁检查器"""
    
    # item_spec JSON Schema 定义
    REQUIRED_FIELDS = {
        "item_id": str,
        "module": str,
        "description": str,
        # "detected_type": int,  # v4.0: 移至运行时判定，不再是必需字段
        "check_logic": dict,
    }
    
    OPTIONAL_FIELDS = {
        "requirements": dict,
        "pattern_items": list,
        "waivers": dict,
        "input_files": list,
        "file_analysis": dict,
        "type_examples": dict,
        "generated_readme": str,
        "parse_logic": (dict, type(None)),
        "type_execution_specs": list,
        "output_info01_format": str,
        "output_error01_format": str,
        "test_scenarios": list,
    }
    
    CHECK_LOGIC_REQUIRED = {
        "parsing_method": str,
        "regex_patterns": list,
        "pass_fail_logic": str,
    }
    
    VALID_DETECTED_TYPES = {1, 2, 3, 4}
    
    # Regex 性能护栏参数
    REGEX_TIMEOUT_MS = 100  # 单个 regex 测试超时
    REGEX_TEST_STRING_LEN = 10000  # 用于测试的字符串长度
    
    # 灾难性回溯检测模式 (需要精确匹配真正危险的嵌套量词)
    # 注意: 这些模式检测的是 regex 语法本身，不是普通文本
    CATASTROPHIC_PATTERNS = [
        r'\([^)]*\+[^)]*\)\+',      # (a+)+ 类型: 量词+后跟+
        r'\([^)]*\*[^)]*\)\*',      # (a*)* 类型: 量词*后跟*
        r'\([^)]*\*[^)]*\)\+',      # (a*)+ 类型: 量词*后跟+
        r'\([^)]*\+[^)]*\)\*',      # (a+)* 类型: 量词+后跟*
        r'\(\?:[^)]*\+[^)]*\)\+',   # (?:a+)+ 非捕获组版本
        r'\(\?:[^)]*\*[^)]*\)\*',   # (?:a*)* 非捕获组版本
        r'\.[\*\+]\.\*',            # .*.*  连续贪婪通配
        r'\.\+\.\+',                # .+.+  连续贪婪通配
    ]
    
    def __init__(self, strict_mode: bool = False):
        """
        Args:
            strict_mode: 严格模式下 warning 也会导致失败
        """
        self.strict_mode = strict_mode
    
    def check(self, item_spec: dict | str | Path) -> GateResult:
        """
        执行门禁检查
        
        Args:
            item_spec: item_spec 字典、JSON 字符串或文件路径
            
        Returns:
            GateResult: 检查结果
        """
        start_time = time.perf_counter()
        failures = []
        warnings = []
        level_passed = {GateLevel.L0_STRUCTURE: True, GateLevel.L1_EXECUTABLE: True}
        
        # 1. 解析输入
        spec_dict, parse_error = self._parse_input(item_spec)
        if parse_error:
            failures.append(parse_error)
            level_passed[GateLevel.L0_STRUCTURE] = False
            return GateResult(
                passed=False,
                level_passed=level_passed,
                failures=failures,
                check_duration_ms=(time.perf_counter() - start_time) * 1000
            )
        
        # 2. L0 结构检查
        l0_failures = self._check_l0_structure(spec_dict)
        failures.extend(l0_failures)
        if l0_failures:
            level_passed[GateLevel.L0_STRUCTURE] = False
        
        # 3. L1 可执行检查（仅在 L0 通过时）
        if level_passed[GateLevel.L0_STRUCTURE]:
            l1_failures, l1_warnings = self._check_l1_executable(spec_dict)
            failures.extend(l1_failures)
            warnings.extend(l1_warnings)
            if l1_failures:
                level_passed[GateLevel.L1_EXECUTABLE] = False
        
        # 4. 计算最终结果
        passed = all(level_passed.values())
        if self.strict_mode and warnings:
            passed = False
        
        return GateResult(
            passed=passed,
            level_passed=level_passed,
            failures=failures,
            warnings=warnings,
            check_duration_ms=(time.perf_counter() - start_time) * 1000
        )
    
    def _parse_input(self, item_spec) -> tuple[dict | None, GateFailure | None]:
        """解析输入为字典"""
        if isinstance(item_spec, dict):
            return item_spec, None
        
        if isinstance(item_spec, (str, Path)):
            path = Path(item_spec)
            if path.exists() and path.suffix == '.json':
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        return json.load(f), None
                except json.JSONDecodeError as e:
                    return None, GateFailure(
                        level=GateLevel.L0_STRUCTURE,
                        code=FailureCode.JSON_INVALID,
                        field_path="<root>",
                        message=f"JSON 解析失败: {e}",
                        suggestion="检查 JSON 格式，确保括号、引号匹配"
                    )
                except Exception as e:
                    return None, GateFailure(
                        level=GateLevel.L0_STRUCTURE,
                        code=FailureCode.JSON_INVALID,
                        field_path="<file>",
                        message=f"文件读取失败: {e}",
                        suggestion="检查文件路径和权限"
                    )
            elif isinstance(item_spec, str):
                try:
                    return json.loads(item_spec), None
                except json.JSONDecodeError as e:
                    return None, GateFailure(
                        level=GateLevel.L0_STRUCTURE,
                        code=FailureCode.JSON_INVALID,
                        field_path="<root>",
                        message=f"JSON 字符串解析失败: {e}",
                        suggestion="检查 JSON 格式"
                    )
        
        return None, GateFailure(
            level=GateLevel.L0_STRUCTURE,
            code=FailureCode.JSON_INVALID,
            field_path="<input>",
            message=f"不支持的输入类型: {type(item_spec)}",
            suggestion="请传入 dict、JSON 字符串或 .json 文件路径"
        )
    
    def _check_l0_structure(self, spec: dict) -> list[GateFailure]:
        """L0: 结构正确性检查"""
        failures = []
        
        # 1. 检查必填字段
        for field_name, expected_type in self.REQUIRED_FIELDS.items():
            if field_name not in spec:
                failures.append(GateFailure(
                    level=GateLevel.L0_STRUCTURE,
                    code=FailureCode.FIELD_MISSING,
                    field_path=field_name,
                    message=f"必填字段缺失: {field_name}",
                    suggestion=f"添加 '{field_name}' 字段，类型应为 {expected_type.__name__}"
                ))
            elif not isinstance(spec[field_name], expected_type):
                failures.append(GateFailure(
                    level=GateLevel.L0_STRUCTURE,
                    code=FailureCode.FIELD_TYPE_ERROR,
                    field_path=field_name,
                    message=f"字段类型错误: {field_name}，期望 {expected_type.__name__}，实际 {type(spec[field_name]).__name__}",
                    value=spec[field_name],
                    suggestion=f"将 '{field_name}' 的值转换为 {expected_type.__name__} 类型"
                ))
        
        # 2. 检查 detected_type 枚举值
        if "detected_type" in spec and isinstance(spec["detected_type"], int):
            if spec["detected_type"] not in self.VALID_DETECTED_TYPES:
                failures.append(GateFailure(
                    level=GateLevel.L0_STRUCTURE,
                    code=FailureCode.ENUM_INVALID,
                    field_path="detected_type",
                    message=f"detected_type 值无效: {spec['detected_type']}，有效值为 {self.VALID_DETECTED_TYPES}",
                    value=spec["detected_type"],
                    suggestion="将 detected_type 设置为 1、2、3 或 4"
                ))
        
        # 3. 检查 check_logic 内部字段
        if "check_logic" in spec and isinstance(spec["check_logic"], dict):
            check_logic = spec["check_logic"]
            for field_name, expected_type in self.CHECK_LOGIC_REQUIRED.items():
                if field_name not in check_logic:
                    failures.append(GateFailure(
                        level=GateLevel.L0_STRUCTURE,
                        code=FailureCode.FIELD_MISSING,
                        field_path=f"check_logic.{field_name}",
                        message=f"check_logic 缺失必填字段: {field_name}",
                        suggestion=f"在 check_logic 中添加 '{field_name}'"
                    ))
                elif not isinstance(check_logic[field_name], expected_type):
                    failures.append(GateFailure(
                        level=GateLevel.L0_STRUCTURE,
                        code=FailureCode.FIELD_TYPE_ERROR,
                        field_path=f"check_logic.{field_name}",
                        message=f"check_logic.{field_name} 类型错误",
                        value=check_logic[field_name],
                        suggestion=f"将类型修正为 {expected_type.__name__}"
                    ))
            
            # 4. 检查 regex_patterns 非空
            if "regex_patterns" in check_logic:
                patterns = check_logic["regex_patterns"]
                if isinstance(patterns, list) and len(patterns) == 0:
                    failures.append(GateFailure(
                        level=GateLevel.L0_STRUCTURE,
                        code=FailureCode.EMPTY_REQUIRED,
                        field_path="check_logic.regex_patterns",
                        message="regex_patterns 不能为空列表",
                        suggestion="至少添加一个正则表达式"
                    ))
        
        # 5. 检查 item_id 格式
        if "item_id" in spec and isinstance(spec["item_id"], str):
            item_id = spec["item_id"]
            if not re.match(r'^[A-Z]+-\d+-\d+-\d+-\d+$', item_id):
                failures.append(GateFailure(
                    level=GateLevel.L0_STRUCTURE,
                    code=FailureCode.ENUM_INVALID,
                    field_path="item_id",
                    message=f"item_id 格式不符合规范: {item_id}",
                    value=item_id,
                    suggestion="item_id 应为 'XXX-N-N-N-NN' 格式，如 'IMP-5-0-0-05'"
                ))
        
        return failures
    
    def _check_l1_executable(self, spec: dict) -> tuple[list[GateFailure], list[str]]:
        """L1: 可执行正确性检查"""
        failures = []
        warnings = []
        
        check_logic = spec.get("check_logic", {})
        patterns = check_logic.get("regex_patterns", [])
        
        # 1. 检查每个 regex 是否能编译
        for i, pattern in enumerate(patterns):
            if not isinstance(pattern, str):
                failures.append(GateFailure(
                    level=GateLevel.L1_EXECUTABLE,
                    code=FailureCode.REGEX_COMPILE_ERROR,
                    field_path=f"check_logic.regex_patterns[{i}]",
                    message=f"regex 不是字符串类型: {type(pattern).__name__}",
                    value=pattern,
                    suggestion="将 regex 转换为字符串"
                ))
                continue
            
            try:
                compiled = re.compile(pattern)
            except re.error as e:
                failures.append(GateFailure(
                    level=GateLevel.L1_EXECUTABLE,
                    code=FailureCode.REGEX_COMPILE_ERROR,
                    field_path=f"check_logic.regex_patterns[{i}]",
                    message=f"regex 编译失败: {e}",
                    value=pattern,
                    suggestion=f"修正正则表达式语法错误"
                ))
                continue
            
            # 2. 检查灾难性回溯风险
            catastrophic_risk = self._check_catastrophic_backtracking(pattern)
            if catastrophic_risk:
                warnings.append(
                    f"regex_patterns[{i}] 可能存在灾难性回溯风险: {catastrophic_risk}"
                )
            
            # 3. 性能测试（超时护栏）
            timeout_failure = self._test_regex_performance(pattern, i)
            if timeout_failure:
                failures.append(timeout_failure)
        
        # 4. 检查逻辑一致性
        logic_failures = self._check_logic_consistency(spec)
        failures.extend(logic_failures)
        
        return failures, warnings
    
    def _check_catastrophic_backtracking(self, pattern: str) -> str | None:
        """检测可能导致灾难性回溯的模式"""
        for risky_pattern in self.CATASTROPHIC_PATTERNS:
            if re.search(risky_pattern, pattern):
                return f"匹配到危险模式: {risky_pattern}"
        return None
    
    def _test_regex_performance(self, pattern: str, index: int) -> GateFailure | None:
        """测试 regex 性能"""
        # 生成测试字符串（可能触发回溯的边界情况）
        test_strings = [
            "a" * self.REGEX_TEST_STRING_LEN,
            " " * self.REGEX_TEST_STRING_LEN,
            "aaa bbb ccc " * (self.REGEX_TEST_STRING_LEN // 12),
            "ERROR: " + "x" * (self.REGEX_TEST_STRING_LEN - 7),
        ]
        
        try:
            compiled = re.compile(pattern, re.IGNORECASE)
        except re.error:
            return None  # 编译错误已在前面处理
        
        for test_str in test_strings:
            start = time.perf_counter()
            try:
                compiled.search(test_str)
            except Exception:
                pass
            elapsed_ms = (time.perf_counter() - start) * 1000
            
            if elapsed_ms > self.REGEX_TIMEOUT_MS:
                return GateFailure(
                    level=GateLevel.L1_EXECUTABLE,
                    code=FailureCode.REGEX_TIMEOUT_RISK,
                    field_path=f"check_logic.regex_patterns[{index}]",
                    message=f"regex 执行时间过长: {elapsed_ms:.1f}ms (阈值 {self.REGEX_TIMEOUT_MS}ms)",
                    value=pattern,
                    suggestion="简化正则表达式，避免嵌套量词或开放式通配"
                )
        
        return None
    
    def _check_logic_consistency(self, spec: dict) -> list[GateFailure]:
        """检查逻辑一致性"""
        failures = []
        
        detected_type = spec.get("detected_type")
        check_logic = spec.get("check_logic", {})
        requirements = spec.get("requirements", {})
        waivers = spec.get("waivers", {})
        
        # Type 3/4 应该有 waiver 配置示例
        if detected_type in (3, 4):
            type_examples = spec.get("type_examples", {})
            type_key = f"type{detected_type}"
            if type_key in type_examples:
                example = type_examples[type_key]
                yaml_str = example.get("yaml", "")
                if "waive_items" not in yaml_str and "waiver" not in yaml_str.lower():
                    failures.append(GateFailure(
                        level=GateLevel.L1_EXECUTABLE,
                        code=FailureCode.LOGIC_INCONSISTENT,
                        field_path=f"type_examples.{type_key}.yaml",
                        message=f"Type {detected_type} 需要 waiver 配置，但示例中未包含",
                        suggestion=f"在 type{detected_type} 示例中添加 waive_items 配置"
                    ))
        
        # pass_fail_logic 应该与 detected_type 匹配
        pass_fail_logic = check_logic.get("pass_fail_logic", "").lower()
        if detected_type == 1 and "waiver" in pass_fail_logic:
            # Type 1 是纯 boolean，不应该有 waiver 逻辑
            pass  # 这是允许的，因为描述可能说明 Type 3/4 的行为
        
        return failures


# 便捷函数
def check_item_spec(item_spec: dict | str | Path, strict: bool = False) -> GateResult:
    """
    便捷函数：检查 item_spec 是否通过门禁
    
    Args:
        item_spec: item_spec 字典、JSON 字符串或文件路径
        strict: 是否启用严格模式
        
    Returns:
        GateResult: 检查结果
    """
    gate = ItemSpecGate(strict_mode=strict)
    return gate.check(item_spec)


if __name__ == "__main__":
    # 示例用法
    import sys
    
    if len(sys.argv) > 1:
        path = sys.argv[1]
        result = check_item_spec(path)
        print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
    else:
        print("Usage: python item_spec_gate.py <path_to_item_spec.json>")
