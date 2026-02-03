"""
Code Assembler - Postprocessor Skill for CodeGen Agent

Version: v2.0.0
Created: 2025-12-22
Updated: 2025-12-24

Assembles final Checker code by combining:
- Fixed Jinja2 templates (header, imports, init, entry point)
- LLM-generated code fragments (parse method, type executions, helpers)

v2.0 Changes:
- Support class_constants and instance_vars fragments
- Aligned with Golden code structure
- Fixed inheritance order in templates
"""

from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

try:
    from jinja2 import Environment, FileSystemLoader, Template
except ImportError:
    raise ImportError("jinja2 is required. Install with: pip install jinja2")

# Lazy import to avoid circular dependency
CodeGenContext = None

def _get_codegen_context():
    """Lazy import of CodeGenContext to avoid circular imports."""
    global CodeGenContext
    if CodeGenContext is None:
        from agents.code_generation.models import CodeGenContext as _CGC
        CodeGenContext = _CGC
    return CodeGenContext


# Template directory path
TEMPLATE_DIR = Path(__file__).parent / "templates"


def assemble_checker_code(
    codegen_context,  # Type: CodeGenContext (avoid import for circular dependency)
    code_fragments: Dict[str, str],
    author: str = "CodeGen Agent",
    version: str = "v1.0.0"
) -> str:
    """
    Assemble complete Checker Python code from templates and LLM fragments.
    
    v2.1: 支持 LLM 生成的语义化类名 (Golden Pattern)
    v2.0: 支持 class_constants 和 instance_vars 片段
    
    Args:
        codegen_context: Context containing item metadata
        code_fragments: Dict with keys:
            - class_name: LLM-generated semantic class name (optional, v2.1)
            - class_constants: Class-level constant definitions (optional, v2.0)
            - name_extractor_method: _build_name_extractor() method (optional, v2.1)
            - instance_vars: Additional __init__ instance variables (optional, v2.0)
            - parse_method: _parse_input_files() implementation
            - execute_type1-4: Type execution implementations
            - helper_methods: Additional helper methods (optional)
        author: Author name for header comment
        version: Version string for header comment
        
    Returns:
        Complete Python code as string
        
    Raises:
        ValueError: If required code fragments are missing
    """
    # Validate required fragments
    required_keys = ['parse_method', 'execute_type1', 'execute_type2', 
                     'execute_type3', 'execute_type4']
    missing = [k for k in required_keys if not code_fragments.get(k)]
    if missing:
        raise ValueError(f"Missing required code fragments: {missing}")
    
    # Setup Jinja2 environment
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True
    )
    
    # Load component templates
    header_template = env.get_template("header_comment.jinja2")
    imports_template = env.get_template("imports.jinja2")
    skeleton_template = env.get_template("checker_skeleton.py.jinja2")
    
    # v2.1: 使用 LLM 生成的语义化类名 (如果提供)
    class_name = code_fragments.get('class_name', '').strip()
    if not class_name or not class_name.replace('_', '').replace('-', '').isalnum():
        # 如果 LLM 没有提供有效类名，使用默认的
        class_name = codegen_context.class_name
    
    # v2.1: 合并 name_extractor_method 到 helper_methods
    helper_methods = code_fragments.get('helper_methods', '')
    name_extractor_method = code_fragments.get('name_extractor_method', '')
    if name_extractor_method:
        # 将 name_extractor_method 放在 helper_methods 前面
        helper_methods = name_extractor_method + '\n\n' + helper_methods if helper_methods else name_extractor_method
    
    # Prepare template context
    template_context = {
        # Metadata
        'item_id': codegen_context.item_id,
        'class_name': class_name,  # v2.1: 使用语义化类名
        'description': codegen_context.item_desc,
        'check_module': codegen_context.check_module,
        'author': author,
        'date': datetime.now().strftime("%Y-%m-%d"),
        'version': version,
        
        # Pre-rendered sections
        'header_comment': header_template.render(
            item_id=codegen_context.item_id,
            class_name=class_name,  # v2.1: 使用语义化类名
            description=codegen_context.item_desc,
            author=author,
            date=datetime.now().strftime("%Y-%m-%d"),
            version=version
        ),
        'imports_section': imports_template.render(),
        
        # v2.0: Class-level constants and instance vars
        'class_constants': code_fragments.get('class_constants', ''),
        'instance_vars': code_fragments.get('instance_vars', ''),
        
        # LLM-generated code fragments
        'parse_method': code_fragments['parse_method'],
        'execute_type1': code_fragments['execute_type1'],
        'execute_type2': code_fragments['execute_type2'],
        'execute_type3': code_fragments['execute_type3'],
        'execute_type4': code_fragments['execute_type4'],
        'helper_methods': helper_methods,  # v2.1: 包含 name_extractor_method
    }
    
    # Render final code
    return skeleton_template.render(**template_context)


def assemble_with_defaults(
    codegen_context,  # Type: CodeGenContext (avoid import for circular dependency)
    code_fragments: Dict[str, str]
) -> str:
    """
    Assemble code with TODO placeholders for missing fragments.
    
    Use this when LLM output is incomplete but you still want
    to generate a skeleton file.
    """
    # Fill missing fragments with TODOs
    default_fragments = {
        'parse_method': _default_parse_method(),
        'execute_type1': _default_execute_type(1),
        'execute_type2': _default_execute_type(2),
        'execute_type3': _default_execute_type(3),
        'execute_type4': _default_execute_type(4),
        'helper_methods': '',
    }
    
    merged = {**default_fragments, **{k: v for k, v in code_fragments.items() if v}}
    
    return assemble_checker_code(codegen_context, merged)


def _default_parse_method() -> str:
    """Generate default _parse_input_files() with TODO."""
    return '''def _parse_input_files(self) -> Dict[str, Any]:
    """
    Parse input files and extract relevant data.
    
    Returns:
        Dict with keys: 'items', 'metadata', 'errors'
    """
    # TODO: Implement parsing logic based on input file patterns
    items = []
    metadata = {}
    errors = []
    
    valid_files = self.validate_input_files()
    if not valid_files:
        errors.append("No valid input files found")
        return {'items': items, 'metadata': metadata, 'errors': errors}
    
    # TODO: Parse each file
    for file_path in valid_files:
        lines = self.read_file(file_path)
        # TODO: Extract items using regex patterns
        pass
    
    metadata['files_parsed'] = len(valid_files)
    metadata['total_items'] = len(items)
    
    return {'items': items, 'metadata': metadata, 'errors': errors}'''


def _default_execute_type(type_num: int) -> str:
    """Generate default _execute_typeN() with TODO."""
    type_desc = {
        1: "Boolean Check - existence check only",
        2: "Value Check - pattern matching required",
        3: "Value Check with Waiver logic",
        4: "Boolean Check with Waiver logic"
    }
    
    return f'''def _execute_type{type_num}(self) -> CheckResult:
    """
    Type {type_num}: {type_desc.get(type_num, 'Unknown')}
    
    Returns:
        CheckResult with pass/fail status
    """
    # TODO: Implement Type {type_num} execution logic
    return CheckResult(
        is_pass=False,
        reason="Type {type_num} not implemented",
        details={{}}
    )'''


# ============================================================================
# Fragment Extraction Utilities
# ============================================================================

def extract_method_body(code: str, method_name: str) -> Optional[str]:
    """
    Extract a method body from code string.
    
    Useful for extracting individual methods from LLM output.
    """
    import re
    
    # Pattern to match method definition and body
    pattern = rf'(def {method_name}\(self.*?\):.*?)(?=\n    def |\nclass |\nif __name__|$)'
    match = re.search(pattern, code, re.DOTALL)
    
    if match:
        return match.group(1).strip()
    return None


def merge_fragments(existing: Dict[str, str], new: Dict[str, str]) -> Dict[str, str]:
    """
    Merge new fragments with existing, preferring new non-empty values.
    """
    result = existing.copy()
    for key, value in new.items():
        if value and value.strip():
            result[key] = value
    return result


if __name__ == "__main__":
    # Test with mock data
    from agents.code_generation.models import CodeGenContext, TypeExecutionSpec
    
    context = CodeGenContext(
        item_id="IMP-5-0-0-05",
        class_name="Check_5_0_0_05",
        description="Test checker for demonstration",
        regex_patterns=[r'error:\s+(.+)'],
        input_file_patterns=["*.log"],
        type_specs=[
            TypeExecutionSpec(
                type_id=1,
                description="Boolean Check",
                pass_condition="No errors found",
                fail_condition="Errors found"
            )
        ],
        pattern_items=[],
        waive_items=[],
        requirements_value=None,
        waivers_value=None,
        semantic_hints={},
        raw_item_spec={}
    )
    
    fragments = {
        'parse_method': _default_parse_method(),
        'execute_type1': _default_execute_type(1),
        'execute_type2': _default_execute_type(2),
        'execute_type3': _default_execute_type(3),
        'execute_type4': _default_execute_type(4),
    }
    
    code = assemble_checker_code(context, fragments)
    print(code)
