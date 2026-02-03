"""
JSON Validator - Layer 2 Output Validator

v5.0 设计原则:
- 只验证 LLM 直接输出的字段 (不验证 Postprocessor 渲染的内容)
- 只验证影响 CodeGenAgent 的关键字段
- 避免与 Gate L0/L1 重复验证
- Retry 应该有效 (验证的问题必须是 LLM 能通过重试修复的)

版本: 2.1.0 (v5.0 aligned + type_execution_specs)
"""

from pathlib import Path
from typing import Tuple, List, Any


# ============================================================================
# 主函数
# ============================================================================

def validate_result(
    result: dict, 
    config_summary: Any  # duck typing, expects .detected_type attribute
) -> Tuple[str, List[str]]:
    """
    v5.0 Layer 2 验证: 只验证 LLM 直接输出且影响 CodeGen 的关键字段
    
    验证原则:
    ✓ check_logic 核心字段 (CodeGen 关键输入)
    ✓ A.5 class_constants (CodeGen 关键输入)
    ✓ A.5 logic_steps (CodeGen 关键输入)
    ✓ type_execution_specs (CodeGen 关键输入)
    ✓ TODO 残留 (仅在 LLM 直接输出字段中)
    
    不验证:
    ✗ type_examples (CodeGenAgent 忽略此字段)
    ✗ type_scenarios (用于 README 渲染，非 CodeGen 关键)
    ✗ generated_readme (Postprocessor 渲染，非 LLM 直接输出)
    ✗ 结构完整性 (Gate L0 负责)
    
    Args:
        result: LLM 输出
        config_summary: 配置摘要 (保留接口兼容性)
        
    Returns:
        (status, issues)
        status: "PASS" | "NEEDS_IMPROVEMENT" | "FAIL"
        issues: 具体问题列表
    """
    issues = []
    
    # 1. 检查 Check Logic 完整性 (CodeGen 关键)
    issues.extend(_check_logic_completeness(result))
    
    # 2. 检查 A.5 字段完整性 (CodeGen 关键)
    issues.extend(_check_a5_fields(result))
    
    # 3. 检查 type_execution_specs (CodeGen 关键)
    issues.extend(_check_type_execution_specs(result))
    
    # 4. 检查 TODO 残留 (仅在 LLM 直接输出字段中)
    issues.extend(_check_todo_residual(result))
    
    # 判断状态
    if not issues:
        return "PASS", []
    elif len(issues) <= 2:
        return "NEEDS_IMPROVEMENT", issues
    else:
        return "FAIL", issues


def _check_logic_completeness(result: dict) -> List[str]:
    """检查 Check Logic 完整性 (CodeGen 关键输入)"""
    issues = []
    
    check_logic = result.get("check_logic", {})
    
    if not check_logic.get("parsing_method"):
        issues.append("check_logic.parsing_method is empty")
    
    if not check_logic.get("pass_fail_logic"):
        issues.append("check_logic.pass_fail_logic is empty")
    
    return issues


def _check_a5_fields(result: dict) -> List[str]:
    """
    检查 A.5 扩展字段完整性 (CodeGen 关键输入)
    
    A.5 字段是 v4.9 新增的 CodeGen 关键输入:
    - class_constants: 8 个模板字符串
    - logic_steps: 3-5 个实现步骤
    """
    issues = []
    
    # 检查 class_constants (8 个必填)
    class_constants = result.get("class_constants", {})
    required_constants = [
        "found_desc", "missing_desc", "waived_desc",
        "found_reason", "missing_reason", "waived_base_reason",
        "extra_reason", "unused_waiver_reason"
    ]
    
    missing_constants = []
    for const in required_constants:
        if not class_constants.get(const):
            missing_constants.append(const)
    
    if missing_constants:
        if len(missing_constants) <= 3:
            issues.append(f"class_constants missing: {', '.join(missing_constants)}")
        else:
            issues.append(f"class_constants missing {len(missing_constants)}/8 fields")
    
    # 检查 logic_steps (3-5 个)
    logic_steps = result.get("logic_steps", [])
    if not logic_steps:
        issues.append("logic_steps is empty")
    elif len(logic_steps) < 3:
        issues.append(f"logic_steps should have 3-5 items, got {len(logic_steps)}")
    
    return issues


def _check_type_execution_specs(result: dict) -> List[str]:
    """
    检查 type_execution_specs 完整性 (CodeGen 关键输入)
    
    type_execution_specs 是 CodeGenAgent 的主要输入，定义了 4 种 Type 的执行规格。
    """
    issues = []
    
    specs = result.get("type_execution_specs", [])
    
    # 检查数量
    if not specs:
        issues.append("type_execution_specs is empty (need 4 specs)")
        return issues
    
    if len(specs) < 4:
        issues.append(f"type_execution_specs has {len(specs)} specs (need 4)")
    
    # 检查每个 spec 的关键字段
    required_fields = ["type_id", "description", "pass_condition", "fail_condition"]
    for i, spec in enumerate(specs[:4]):  # 只检查前 4 个
        if not isinstance(spec, dict):
            issues.append(f"type_execution_specs[{i}] is not a dict")
            continue
        
        missing = [f for f in required_fields if not spec.get(f)]
        if missing:
            issues.append(f"type_execution_specs[{i}] missing: {', '.join(missing)}")
            break  # 只报告一次详细问题
    
    return issues


def _check_todo_residual(result: dict) -> List[str]:
    """
    检查 TODO 残留 (仅在 LLM 直接输出字段中)
    
    v5.0 变更:
    - 不检查 generated_readme (Postprocessor 渲染，非 LLM 直接输出)
    - 只检查 check_logic, class_constants 等 LLM 直接生成的字段
    """
    issues = []
    placeholders = ["TODO", "TBD", "FIXME", "[填写", "[待"]
    
    # 检查 check_logic 字段
    check_logic = result.get("check_logic", {})
    for key, value in check_logic.items():
        if isinstance(value, str) and any(p in value for p in placeholders):
            issues.append(f"check_logic.{key} contains placeholder")
    
    # 检查 class_constants 字段
    class_constants = result.get("class_constants", {})
    for key, value in class_constants.items():
        if isinstance(value, str) and any(p in value for p in placeholders):
            issues.append(f"class_constants.{key} contains placeholder")
    
    # 检查 logic_steps
    logic_steps = result.get("logic_steps", [])
    for i, step in enumerate(logic_steps):
        if isinstance(step, str) and any(p in step for p in placeholders):
            issues.append(f"logic_steps[{i}] contains placeholder")
            break  # 只报告一次
    
    return issues


def format_feedback(issues: List[str]) -> str:
    """
    格式化反馈信息，用于重试
    
    Args:
        issues: 问题列表
        
    Returns:
        str: 格式化的反馈字符串
    """
    if not issues:
        return ""
    
    lines = ["Previous attempt had the following issues:"]
    for i, issue in enumerate(issues, 1):
        lines.append(f"  {i}. {issue}")
    lines.append("")
    lines.append("Please fix these issues in your response.")
    
    return "\n".join(lines)


if __name__ == "__main__":
    # 测试
    from agents.context.models import ConfigSummary, FileInfo
    
    config = ConfigSummary(
        item_id="IMP-5-0-0-00",
        description="Test",
        input_files=[],
        file_count=0,
        aggregation_needed=False,
        requirements={},
        pattern_items=[],
        waivers={},
        detected_type=1
    )
    
    # 测试不完整的结果
    incomplete_result = {
        "check_logic": {
            "parsing_method": "TODO: fill this"
        },
        "type_examples": {
            "type1": {"yaml": "test", "behavior": "test"}
            # missing type2, type3, type4
        }
    }
    
    status, issues = validate_result(incomplete_result, config)
    print(f"Status: {status}")
    print(f"Issues: {issues}")
    print()
    print(format_feedback(issues))
