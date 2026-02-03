"""
Enhanced Prompt Builder - Integrating Fillable Framework Templates

Design Principles:
1. Keep existing Jinja2 skeleton unchanged
2. Inject "fillable frameworks" into Prompt to provide concrete guidance to LLM
3. Support Critical Checklist validation

Usage:
    prompt = build_enhanced_prompt_with_fillable_templates(context, ...)
    
    # Prompt Structure:
    # 1. Grounding Data (log samples, data structure rules)
    # 2. Task Context
    # 3. Fillable Framework Templates \u2190 NEW!
    # 4. Critical Checklist \u2190 NEW!
    # 5. Output format
"""

from typing import Dict, Any, Optional
from .type_execution_templates import (
    get_type1_fillable_template,
    get_type2_fillable_template,
    get_type3_fillable_template,
    get_type4_fillable_template,
    get_layer2_boolean_logic_template,
    get_layer2_pattern_logic_template,
    get_layer1_parse_template,
    CRITICAL_CHECKLIST
)


def build_fillable_templates_section(
    item_spec: Dict[str, Any],
    architecture_guidance: Dict[str, Any]
) -> str:
    """
    Build fillable framework templates section
    
    Args:
        item_spec: Item specification
        architecture_guidance: Architecture guidance (includes three_layer_design, etc.)
    
    Returns:
        Formatted section with fillable templates
    """
    lines = [
        "=" * 80,
        "📝 CODE GENERATION TEMPLATES (Fillable Frameworks)",
        "=" * 80,
        "",
        "⚠️ CRITICAL: The following are **fillable frameworks** for methods you need to implement",
        "",
        "Framework Instructions:",
        "- FIXED: These sections MUST remain unchanged (API signatures, parameter passing)",
        "- TODO: These sections need to be filled based on business logic",
        "- ⚠️ CRITICAL: Marks key constraints that MUST be followed",
        "",
        "Please generate code strictly following the API signatures and parameters in the framework.",
        "Do NOT omit any parameters or calls from FIXED sections!",
        "",
    ]
    
    # Layer 1: Parsing
    if architecture_guidance.get('three_layer_design'):
        lines.extend([
            "=" * 70,
            "LAYER 1: Input File Parsing",
            "=" * 70,
            "",
            get_layer1_parse_template(),
            "",
        ])
    
    # Layer 2: Logic Modules
    if architecture_guidance.get('three_layer_design'):
        lines.extend([
            "=" * 70,
            "LAYER 2: Shared Logic Modules",
            "=" * 70,
            "",
            "## Boolean Check Logic (shared by Type1/4)",
            "",
            get_layer2_boolean_logic_template(),
            "",
            "## Pattern Check Logic (shared by Type2/3)",
            "",
            get_layer2_pattern_logic_template(),
            "",
        ])
    
    # Layer 3: Type Execution
    lines.extend([
        "=" * 70,
        "LAYER 3: Type Execution Methods",
        "=" * 70,
        "",
        "## Type 1: Boolean Check (no waiver)",
        "",
        get_type1_fillable_template(),
        "",
        "## Type 2: Value Check (no waiver)",
        "",
        get_type2_fillable_template(),
        "",
        "## Type 3: Value Check with Waiver (has waiver)",
        "",
        "⚠️ CRITICAL: Type3 is the MOST error-prone type!",
        "MUST include info_items parameter, even if it's an empty dict.",
        "",
        get_type3_fillable_template(),
        "",
        "## Type 4: Boolean Check with Waiver (has waiver)",
        "",
        get_type4_fillable_template(),
        "",
    ])
    
    lines.extend([
        "=" * 80,
        "",
    ])
    
    return "\n".join(lines)


def build_critical_checklist_section() -> str:
    """Build Critical Checklist section"""
    return f"""
{CRITICAL_CHECKLIST}

⚠️ Before submitting the generated code, please verify each item against the checklist above!
"""


def integrate_into_existing_prompt(
    existing_prompt_parts: Dict[str, str],
    item_spec: Dict[str, Any],
    architecture_guidance: Dict[str, Any]
) -> str:
    """
    Integrate into existing Prompt build process
    
    Existing Prompt Structure:
    1. Grounding Data (golden_reference, log_samples, data_structure_rules)
    2. Semantic Intent
    3. Context Agent Data
    4. Task Context
    5. Type Specifications
    6. Output Format
    
    New Additions:
    - Insert Fillable Templates after Task Context
    - Insert Critical Checklist before Output Format
    
    Args:
        existing_prompt_parts: Dict with keys like 'grounding', 'task_context', etc.
        item_spec: Item specification
        architecture_guidance: Architecture guidance
    
    Returns:
        Complete prompt string
    """
    sections = []
    
    # 1. Grounding Data (existing)
    if existing_prompt_parts.get('grounding'):
        sections.append(existing_prompt_parts['grounding'])
    
    # 2. Semantic Intent (existing)
    if existing_prompt_parts.get('semantic_intent'):
        sections.append(existing_prompt_parts['semantic_intent'])
    
    # 3. Context Agent Data (existing)
    if existing_prompt_parts.get('context_agent'):
        sections.append(existing_prompt_parts['context_agent'])
    
    # 4. Task Context (existing)
    if existing_prompt_parts.get('task_context'):
        sections.append(existing_prompt_parts['task_context'])
    
    # 5. Type Specifications (existing)
    if existing_prompt_parts.get('type_specs'):
        sections.append(existing_prompt_parts['type_specs'])
    
    # === NEW: Fillable Templates ===
    sections.append(build_fillable_templates_section(item_spec, architecture_guidance))
    
    # === NEW: Critical Checklist ===
    sections.append(build_critical_checklist_section())
    
    # 6. Output Format (existing)
    if existing_prompt_parts.get('output_format'):
        sections.append(existing_prompt_parts['output_format'])
    
    return "\n\n".join(sections)


# ============================================================================
# Usage Example - Integration into existing prompts.py
# ============================================================================

def example_integration():
    """
    Example: How to integrate into existing build_user_prompt()
    """
    code_snippet = '''
# agents/code_generation/prompts.py

from agents.common.skills.postprocessors.code_assembler.templates.fillable_skeletons import (
    build_fillable_templates_section,
    build_critical_checklist_section
)

def build_user_prompt(
    codegen_context: CodeGenContext,
    feedback: Optional[ValidationFeedback] = None,
    log_samples: Optional[Dict[str, str]] = None,
    reference_snippets: Optional[Dict[str, str]] = None,
    golden_reference: Optional[str] = None,
) -> str:
    """Build User Prompt v6.1 - Integrate fillable frameworks"""
    sections = []
    
    # === Existing sections ===
    sections.append(_build_grounding_section(golden_reference, log_samples, reference_snippets, ...))
    sections.append(_build_semantic_intent_section(codegen_context))
    sections.append(_build_context_agent_section(codegen_context))
    sections.append(_build_task_context_section(codegen_context))
    sections.append(_build_type_specs_section(codegen_context))
    
    # === NEW: Fillable Framework Templates ===
    item_spec = {
        'item_id': codegen_context.item_id,
        'requirements': codegen_context.requirements,
        ...
    }
    architecture_guidance = codegen_context.metadata.get('architecture_guidance', {})
    sections.append(build_fillable_templates_section(item_spec, architecture_guidance))
    
    # === NEW: Critical Checklist ===
    sections.append(build_critical_checklist_section())
    
    # === Existing sections ===
    sections.append(_build_output_format_section())
    
    return "\\n\\n".join(sections)
    '''
    return code_snippet


if __name__ == '__main__':
    # Demonstration
    print("=" * 80)
    print("Enhanced Prompt Builder - Fillable Framework Template Integration")
    print("=" * 80)
    print()
    print(example_integration())
