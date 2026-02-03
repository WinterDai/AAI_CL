"""
Fillable Skeletons - Fillable Framework Template System

Provides concrete code frameworks to LLM to ensure generated code meets architectural constraints.

Core Files:
- type_execution_templates.py: Fillable frameworks for Type1-4 + Layer1-2
- prompt_builder.py: Builder for integrating into prompts

Design Philosophy:
AutoGenChecker's "fillable" approach + Your Jinja2 skeleton = Optimal solution
- Jinja2 handles 90% fixed framework (execute_check, etc.)
- Fillable templates provide concrete guidance for 10% business logic (API signatures, TODO markers)
- Critical Checklist ensures key constraints are not missed
"""

from .type_execution_templates import (
    get_type1_fillable_template,
    get_type2_fillable_template,
    get_type3_fillable_template,
    get_type4_fillable_template,
    get_layer1_parse_template,
    get_layer2_boolean_logic_template,
    get_layer2_pattern_logic_template,
    CRITICAL_CHECKLIST,
)

from .prompt_builder import (
    build_fillable_templates_section,
    build_critical_checklist_section,
    integrate_into_existing_prompt,
)

__all__ = [
    # Template getters
    'get_type1_fillable_template',
    'get_type2_fillable_template',
    'get_type3_fillable_template',
    'get_type4_fillable_template',
    'get_layer1_parse_template',
    'get_layer2_boolean_logic_template',
    'get_layer2_pattern_logic_template',
    'CRITICAL_CHECKLIST',
    
    # Prompt builders
    'build_fillable_templates_section',
    'build_critical_checklist_section',
    'integrate_into_existing_prompt',
]
