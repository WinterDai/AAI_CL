"""
ItemSpec Builder Postprocessor

Postprocessor: 无条件执行，数据组装
职责: 从所有 preprocessor 输出和 LLM 结果构建 ItemSpec dict

版本: 1.0.0

注意: 返回 dict 而非 ItemSpec 实例，由 agent.py 负责转换为 ItemSpec
"""

from pathlib import Path
from typing import Optional, Any, Dict, List
from dataclasses import dataclass, field


# ============================================================================
# 本地数据类 (与 models.py 保持兼容)
# ============================================================================

@dataclass
class CheckLogic:
    """检查逻辑"""
    parsing_method: str
    regex_patterns: List[str] = field(default_factory=list)
    pass_fail_logic: str = ""


@dataclass
class TypeExample:
    """Type 示例"""
    type_id: str
    yaml_config: str = ""
    behavior: str = ""
    output: str = ""
    use_case: str = ""


@dataclass
class ParseLogicSpec:
    """解析逻辑规格"""
    file_type: str = "log"
    parsing_strategy: str = "line-by-line"
    key_patterns: List[str] = field(default_factory=list)
    extraction_fields: List[str] = field(default_factory=list)
    aggregation_method: str = "concat"
    error_handling: str = "skip"


@dataclass
class TypeExecutionSpec:
    """Type 执行规格"""
    type_id: int
    description: str
    pass_condition: str
    fail_condition: str
    needs_pattern_search: bool = False
    needs_waiver_logic: bool = False
    output_format: str = "INFO01/ERROR01"


# ============================================================================
# 主函数
# ============================================================================

def build(
    config_summary: Any,  # duck typing
    file_analysis: Any,   # duck typing
    llm_result: dict,
    readme_content: str,
    module: str = ""
) -> Dict[str, Any]:
    """
    构建 ItemSpec，供下游 Agent 使用
    
    Postprocessor 职责 (数据组装):
    ✓ 合并所有 preprocessor 输出
    ✓ 整合 LLM 结果
    ✓ 构建完整 ItemSpec
    
    不做:
    ✗ 数据变换
    ✗ 逻辑决策
    ✗ 内容验证
    
    Args:
        config_summary: 来自 config_loader
        file_analysis: 来自 file_reader
        llm_result: 来自 LLM Phase
        readme_content: 来自 readme_renderer
        module: 模块名称
        
    Returns:
        ItemSpec: 完整的规格，供 CodeGenAgent 和 ValidationAgent 使用
    """
    # 提取 check_logic
    check_logic_dict = llm_result.get("check_logic", {})
    check_logic = CheckLogic(
        parsing_method=check_logic_dict.get("parsing_method", ""),
        regex_patterns=check_logic_dict.get("regex_patterns", []),
        pass_fail_logic=check_logic_dict.get("pass_fail_logic", "")
    )
    
    # 提取 type_examples
    type_examples_dict = llm_result.get("type_examples", {})
    type_examples = {}
    for type_id, example in type_examples_dict.items():
        type_examples[type_id] = TypeExample(
            type_id=type_id,
            yaml_config=example.get("yaml", ""),
            behavior=example.get("behavior", ""),
            output=example.get("output", ""),
            use_case=example.get("use_case", "")
        )
    
    # 推断 module (如果未提供)
    if not module:
        # 从 item_id 推断: IMP-5-0-0-00 -> 5.0_SYNTHESIS_CHECK
        parts = config_summary.item_id.split('-')
        if len(parts) >= 2:
            module = f"{parts[1]}.0_CHECK"
    
    # 构建 ItemSpec dict (由 agent.py 转换为 ItemSpec 实例)
    return {
        # 基础信息
        "item_id": config_summary.item_id,
        "module": module,
        "description": config_summary.description,
        "detected_type": config_summary.detected_type,
        
        # 配置信息
        "requirements": config_summary.requirements,
        "pattern_items": config_summary.pattern_items,
        "waivers": config_summary.waivers,
        
        # 文件信息
        "input_files": config_summary.input_files,
        "file_analysis": file_analysis,
        
        # LLM 生成结果
        "check_logic": check_logic,
        "type_examples": type_examples,
        "generated_readme": readme_content,
        
        # 代码生成规格 (可选，从 LLM 结果提取)
        "parse_logic": _extract_parse_logic(llm_result, file_analysis),
        "type_execution_specs": _extract_type_specs(config_summary.detected_type),
        
        # 输出格式
        "output_info01_format": llm_result.get("output_info01_format", ""),
        "output_error01_format": llm_result.get("output_error01_format", "")
    }


def _extract_parse_logic(llm_result: dict, file_analysis: Any) -> Optional[ParseLogicSpec]:
    """从 LLM 结果提取解析逻辑规格"""
    check_logic = llm_result.get("check_logic", {})
    
    if not check_logic:
        return None
    
    return ParseLogicSpec(
        file_type=file_analysis.detected_format,
        parsing_strategy=_infer_parsing_strategy(check_logic.get("parsing_method", "")),
        key_patterns=check_logic.get("regex_patterns", []),
        extraction_fields=[],
        aggregation_method="concat" if file_analysis.files_analyzed > 1 else "single",
        error_handling="skip"
    )


def _infer_parsing_strategy(parsing_method: str) -> str:
    """从解析方法描述推断策略"""
    method_lower = parsing_method.lower()
    
    if "line" in method_lower:
        return "line-by-line"
    elif "section" in method_lower:
        return "section-based"
    elif "regex" in method_lower:
        return "regex-match"
    elif "json" in method_lower:
        return "json-parse"
    else:
        return "line-by-line"


def _extract_type_specs(detected_type: int) -> list[TypeExecutionSpec]:
    """生成 Type 执行规格"""
    
    # Type 1: Boolean Check
    type1 = TypeExecutionSpec(
        type_id=1,
        description="Boolean Check - 存在性检查",
        pass_condition="文件存在且内容符合预期",
        fail_condition="文件不存在或内容不符合预期",
        needs_pattern_search=False,
        needs_waiver_logic=False,
        output_format="INFO01/ERROR01"
    )
    
    # Type 2: Value Check
    type2 = TypeExecutionSpec(
        type_id=2,
        description="Value Check - 值匹配检查",
        pass_condition="找到的值数量 >= requirements.value",
        fail_condition="找到的值数量 < requirements.value",
        needs_pattern_search=True,
        needs_waiver_logic=False,
        output_format="INFO01/ERROR01"
    )
    
    # Type 3: Value Check + Waiver
    type3 = TypeExecutionSpec(
        type_id=3,
        description="Value Check + Waiver - 值匹配检查 + 豁免",
        pass_condition="找到的值数量 >= requirements.value (考虑 waiver)",
        fail_condition="找到的值数量 < requirements.value (未被 waiver)",
        needs_pattern_search=True,
        needs_waiver_logic=True,
        output_format="INFO01/ERROR01 with [WAIVER] tag"
    )
    
    # Type 4: Boolean Check + Waiver
    type4 = TypeExecutionSpec(
        type_id=4,
        description="Boolean Check + Waiver - 存在性检查 + 豁免",
        pass_condition="检查通过或已被 waiver",
        fail_condition="检查失败且未被 waiver",
        needs_pattern_search=False,
        needs_waiver_logic=True,
        output_format="INFO01/ERROR01 with [WAIVER] tag"
    )
    
    return [type1, type2, type3, type4]


if __name__ == "__main__":
    # 测试
    from agents.context.models import ConfigSummary, FileInfo, FileAnalysis, PatternMatch
    
    config = ConfigSummary(
        item_id="IMP-5-0-0-00",
        description="Test checker",
        input_files=[FileInfo(path="/test/file.log", exists=True, size=100)],
        file_count=1,
        aggregation_needed=False,
        requirements={"value": "N/A"},
        pattern_items=[],
        waivers={"value": "N/A"},
        detected_type=1
    )
    
    file_analysis = FileAnalysis(
        files_analyzed=1,
        total_lines_sampled=100,
        detected_format="log",
        common_patterns=[],
        section_headers=[],
        sample_lines=[]
    )
    
    llm_result = {
        "check_logic": {
            "parsing_method": "Line-by-line parsing",
            "regex_patterns": [],
            "pass_fail_logic": "PASS if file exists"
        },
        "type_examples": {
            "type1": {
                "yaml": "requirements:\n  value: N/A",
                "behavior": "Boolean check",
                "output": "PASS"
            }
        }
    }
    
    item_spec = build(config, file_analysis, llm_result, "# README content")
    print(f"Item ID: {item_spec.item_id}")
    print(f"Type: {item_spec.detected_type}")
    print(f"Has README: {len(item_spec.generated_readme) > 0}")
