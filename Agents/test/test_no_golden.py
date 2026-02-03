# -*- coding: utf-8 -*-
"""
测试 NO GOLDEN 模式是否正常工作
"""

import sys
import os
import asyncio
from pathlib import Path

# Setup path
script_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(script_dir))

from agents.code_generation.prompts import build_user_prompt
from agents.code_generation.models import CodeGenContext

def test_no_golden_prompt():
    """测试 build_user_prompt 在无 Golden 时的行为"""
    
    # 创建最小化的 context (使用正确的字段名)
    context = CodeGenContext(
        item_id="IMP-10-0-0-00",
        class_name="NetlistSpefVersionChecker",
        check_module="Implementation",
        item_desc="Confirm the netlist/spef version is correct.",
        default_type=1,
        requirements={"pattern_items": []},
    )
    context.architecture_guidance = {
        "architecture_type": "three_layer",
        "complexity_level": "medium",
    }
    context.semantic_intent = {
        "check_target": "Netlist/SPEF version",
        "data_flow": "STA log -> file paths -> version info"
    }
    
    # 创建 snippets (来自 Skill Library)
    snippets = {
        "type1": """def _execute_type1(self, parsed_data):
    return self.execute_boolean_check(parse_data_func=lambda: ..., has_waiver=False)""",
        "type3": """def _execute_type3(self, parsed_data):
    # 注意: 需要构建 info_items
    info_items = {...}
    return self.execute_value_check(parse_data_func=..., has_waiver=True, info_items=info_items)""",
    }
    
    # 测试1: golden_reference=None
    prompt = build_user_prompt(
        codegen_context=context,  # 正确的参数名
        feedback=None,
        log_samples=None,
        reference_snippets=snippets,
        golden_reference=None  # NO GOLDEN!
    )
    
    # 验证 prompt 中不包含 Golden 相关内容
    has_golden_section = "Golden 代码片段" in prompt
    has_snippets_section = "代码参考片段" in prompt
    has_data_structure_rules = "数据结构规范" in prompt
    
    print("=" * 60)
    print("NO GOLDEN 模式测试结果:")
    print("=" * 60)
    print(f"✓ 无 Golden 代码片段 section: {not has_golden_section}")
    print(f"✓ 有 代码参考片段 section: {has_snippets_section}")
    print(f"✓ 有 数据结构规范 section: {has_data_structure_rules}")
    print()
    
    # 显示 prompt 的前1000字符
    print("Prompt 前1000字符预览:")
    print("-" * 60)
    print(prompt[:1000])
    print("...")
    print("-" * 60)
    
    # 验证 type3 snippet 是否包含 info_items
    has_info_items = "info_items" in prompt
    print(f"\n✓ type3 snippet 包含 info_items: {has_info_items}")
    
    return not has_golden_section and has_snippets_section and has_data_structure_rules

if __name__ == "__main__":
    success = test_no_golden_prompt()
    if success:
        print("\n✅ 所有测试通过!")
    else:
        print("\n❌ 部分测试失败!")
    sys.exit(0 if success else 1)
