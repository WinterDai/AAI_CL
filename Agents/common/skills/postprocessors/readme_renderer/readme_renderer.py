"""
README Renderer Postprocessor

Postprocessor: 无条件执行，确定性渲染
职责: 使用 Jinja2 模板渲染 README，不含业务逻辑

版本: 1.0.0
"""

from pathlib import Path
from typing import Optional, Any, Dict

try:
    from jinja2 import Environment, FileSystemLoader, select_autoescape
    HAS_JINJA2 = True
except ImportError:
    HAS_JINJA2 = False


# ============================================================================
# 常量
# ============================================================================

# 模板目录
TEMPLATE_DIR = Path(__file__).parent / "templates"

# Type 描述映射
TYPE_DESCRIPTIONS = {
    1: "Boolean Check (存在性检查)",
    2: "Value Check (值匹配检查)",
    3: "Value Check + Waiver (值匹配检查 + 豁免)",
    4: "Boolean Check + Waiver (存在性检查 + 豁免)"
}


# ============================================================================
# 主函数
# ============================================================================

def render_readme(
    llm_result: dict,
    config_summary: Any,  # duck typing, expects .item_id, .description, etc.
    template_name: str = "checker_readme.jinja2"
) -> str:
    """
    使用 Jinja2 模板渲染 README
    
    Postprocessor 职责 (确定性渲染):
    ✓ 加载固定 Jinja2 模板
    ✓ 填充 LLM 生成的内容
    ✓ 返回完整 README
    
    不做:
    ✗ 任何逻辑判断
    ✗ 内容生成
    
    Args:
        llm_result: LLM 输出的结构化 JSON
        config_summary: 配置摘要
        template_name: Jinja2 模板名称
        
    Returns:
        str: 渲染后的 README 内容
    """
    if not HAS_JINJA2:
        return _fallback_render(llm_result, config_summary)
    
    # 创建 Jinja2 环境
    env = Environment(
        loader=FileSystemLoader(TEMPLATE_DIR),
        autoescape=select_autoescape(['html', 'xml']),
        trim_blocks=True,
        lstrip_blocks=True
    )
    
    # 加载模板
    try:
        template = env.get_template(template_name)
    except Exception as e:
        return _fallback_render(llm_result, config_summary)
    
    # 准备模板变量
    context = _prepare_context(llm_result, config_summary)
    
    # 渲染模板
    return template.render(**context)


def _prepare_context(llm_result: dict, config_summary: Any) -> dict:
    """准备模板渲染上下文"""
    # v5.0: detected_type 不再由 Tool 预判，使用默认值 1
    detected_type = getattr(config_summary, 'detected_type', 1)
    
    return {
        # 基础信息
        "item_id": config_summary.item_id,
        "description": config_summary.description,
        "detected_type": detected_type,
        "type_description": TYPE_DESCRIPTIONS.get(detected_type, "Unknown"),
        "file_count": config_summary.file_count,
        "aggregation_needed": config_summary.aggregation_needed,
        
        # LLM 生成的内容
        "check_logic": llm_result.get("check_logic", {}),
        "type_examples": llm_result.get("type_examples", {}),
        "category": llm_result.get("category", "Checker"),
        "testing_commands": llm_result.get("testing_commands", ""),
        "output_info01_format": llm_result.get("output_info01_format", ""),
        "output_error01_format": llm_result.get("output_error01_format", ""),
        
        # 路径信息
        "module_path": f"Check_modules/{config_summary.item_id.split('-')[1]}.0_*"
    }


def _fallback_render(llm_result: dict, config_summary: Any) -> str:
    """
    Jinja2 不可用时的降级渲染
    """
    check_logic = llm_result.get("check_logic", {})
    type_examples = llm_result.get("type_examples", {})
    
    lines = [
        f"# {config_summary.item_id}: {config_summary.description}",
        "",
        "## Overview",
        "",
        f"**Check Type**: Type {config_summary.detected_type} - {TYPE_DESCRIPTIONS.get(config_summary.detected_type, 'Unknown')}",
        f"**Files**: {config_summary.file_count} input file(s)",
        "",
        "## Check Logic",
        "",
        "### Parsing Method",
        "",
        check_logic.get("parsing_method", "N/A"),
        "",
        "### Pass/Fail Criteria",
        "",
        check_logic.get("pass_fail_logic", "N/A"),
        "",
        "## Type Configuration Examples",
        ""
    ]
    
    for type_id, example in type_examples.items():
        lines.extend([
            f"### {type_id.replace('type', 'Type ')}",
            "",
            "**YAML Configuration:**",
            "```yaml",
            example.get("yaml", ""),
            "```",
            "",
            f"**Behavior:** {example.get('behavior', '')}",
            "",
            "**Expected Output:**",
            "```",
            example.get("output", ""),
            "```",
            ""
        ])
    
    return "\n".join(lines)


def save_readme(readme_path: str, content: str) -> dict:
    """
    保存 README 文件
    
    Args:
        readme_path: README 文件路径
        content: README 内容
        
    Returns:
        dict: {"saved": bool, "path": str, "size": int}
    """
    path = Path(readme_path)
    
    # 确保目录存在
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return {
        "saved": True,
        "path": str(path),
        "size": len(content)
    }


if __name__ == "__main__":
    # 测试
    from agents.context.models import ConfigSummary, FileInfo
    
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
    
    readme = render_readme(llm_result, config)
    print(readme)
