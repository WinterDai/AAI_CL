"""
ItemSpec Parser - Preprocessor Skill for CodeGen Agent

Version: v1.1.0
Created: 2025-12-22
Updated: 2025-12-23

Parses ItemSpec JSON (from ContextAgent) and extracts information needed for code generation.
Transforms the ItemSpec structure into a CodeGenContext.

IMPORTANT: Uses CodeGenContext from agents.code_generation.models
"""

import json
import re
from pathlib import Path
from typing import Optional, Dict, Any, List

# Import from code_generation models
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))
from agents.code_generation.models import CodeGenContext, TypeExecutionSpec


def parse_item_spec(
    item_spec_path: str,
    item_id: Optional[str] = None
) -> CodeGenContext:
    """
    Parse ItemSpec JSON and create CodeGenContext for code generation.
    
    Args:
        item_spec_path: Path to item_spec.json file
        item_id: Optional item ID (extracted from JSON if not provided)
        
    Returns:
        CodeGenContext populated with all necessary information
        
    Raises:
        FileNotFoundError: If item_spec.json not found
        ValueError: If JSON is malformed
    """
    path = Path(item_spec_path)
    
    if not path.exists():
        raise FileNotFoundError(f"ItemSpec not found: {path}")
    
    # Load JSON
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Extract item_id from JSON or path
    if not item_id:
        item_id = data.get("item_id", _extract_item_id_from_path(path))
    
    # Parse main fields (ContextAgent output structure)
    description = data.get("description", "")
    module = data.get("module", "")
    detected_type = data.get("detected_type", 1)
    
    # Extract check_logic
    check_logic = data.get("check_logic", {})
    regex_patterns = check_logic.get("regex_patterns", [])
    parsing_method = check_logic.get("parsing_method", "")
    pass_fail_logic = check_logic.get("pass_fail_logic", "")
    
    # Extract parse_logic
    parse_logic = data.get("parse_logic", {})
    extraction_fields = parse_logic.get("extraction_fields", [])
    file_type = parse_logic.get("file_type", "log")
    
    # Extract requirements and waivers
    requirements = data.get("requirements", {})
    waivers = data.get("waivers", {})
    
    # Extract type_execution_specs and convert to TypeExecutionSpec objects
    type_execution_specs_raw = data.get("type_execution_specs", [])
    type_specs = _parse_type_specs(type_execution_specs_raw)
    
    # Build class name
    class_name = _item_id_to_class_name(item_id)
    
    # Build context
    return CodeGenContext(
        item_id=item_id,
        class_name=class_name,
        check_module=module,
        item_desc=description,
        detected_type=detected_type,
        regex_patterns=regex_patterns,
        parsing_method=parsing_method,
        pass_fail_logic=pass_fail_logic,
        type_specs=type_specs,
        extraction_fields=extraction_fields,
        file_type=file_type,
        requirements=requirements,
        waivers=waivers,
    )


def _extract_item_id_from_path(path: Path) -> str:
    """
    Extract item ID from file path.
    
    Expects path like: .../IMP-5-0-0-05/item_spec.json
    Returns: IMP-5-0-0-05
    """
    # Try parent directory name
    parent_name = path.parent.name
    if re.match(r'IMP-\d+-\d+-\d+-\d+', parent_name):
        return parent_name
    
    # Try grandparent
    grandparent_name = path.parent.parent.name
    if re.match(r'IMP-\d+-\d+-\d+-\d+', grandparent_name):
        return grandparent_name
    
    # Default
    return "UNKNOWN"


def _item_id_to_class_name(item_id: str) -> str:
    """
    Convert item ID to Python class name.
    
    IMP-5-0-0-05 → Check_5_0_0_05
    """
    if item_id.startswith("IMP-"):
        item_id = item_id[4:]
    return f"Check_{item_id.replace('-', '_')}"


def _normalize_type_id(raw_type_id) -> int:
    """将 type_id 规范化为 int (1,2,3,4)"""
    if isinstance(raw_type_id, int):
        return raw_type_id
    if isinstance(raw_type_id, str):
        cleaned = raw_type_id.lower().replace("type", "").replace(" ", "").strip()
        try:
            return int(cleaned)
        except ValueError:
            return 1
    return 1


def _parse_type_specs(type_specs_raw: List[Dict[str, Any]]) -> List[TypeExecutionSpec]:
    """
    Parse raw type_execution_specs from ItemSpec into TypeExecutionSpec objects.
    """
    type_specs = []
    
    for spec in type_specs_raw:
        type_specs.append(TypeExecutionSpec(
            type_id=_normalize_type_id(spec.get("type_id", 0)),
            description=spec.get("description", ""),
            pass_condition=spec.get("pass_condition", ""),
            fail_condition=spec.get("fail_condition", ""),
            needs_pattern_search=spec.get("needs_pattern_search", False),
            needs_waiver_logic=spec.get("needs_waiver_logic", False),
            output_format=spec.get("output_format", ""),
        ))
    
    # Ensure we have all 4 types (fill with defaults if missing)
    existing_type_ids = {s.type_id for s in type_specs}
    for type_id in [1, 2, 3, 4]:
        if type_id not in existing_type_ids:
            type_specs.append(TypeExecutionSpec(
                type_id=type_id,
                description=f"Type {type_id} (not defined in ItemSpec)",
                pass_condition="Not specified",
                fail_condition="Not specified",
            ))
    
    # Sort by type_id
    type_specs.sort(key=lambda s: s.type_id)
    
    return type_specs


# ============================================================================
# Convenience Functions
# ============================================================================

def load_and_parse(item_dir: str) -> CodeGenContext:
    """
    Convenience function to load and parse ItemSpec from directory.
    
    Args:
        item_dir: Directory containing item_spec.json
        
    Returns:
        CodeGenContext
    """
    path = Path(item_dir) / "item_spec.json"
    return parse_item_spec(str(path))


def validate_item_spec(data: Dict[str, Any]) -> List[str]:
    """
    Validate ItemSpec structure.
    
    Returns:
        List of validation errors (empty if valid)
    """
    errors = []
    
    required_fields = ["item_id", "description"]
    for field in required_fields:
        if field not in data:
            errors.append(f"Missing required field: {field}")
    
    return errors


if __name__ == "__main__":
    # Test with sample path
    import sys
    if len(sys.argv) > 1:
        context = parse_item_spec(sys.argv[1])
        print(f"Item ID: {context.item_id}")
        print(f"Class Name: {context.class_name}")
        print(f"Description: {context.item_desc[:100]}...")
        print(f"Regex Patterns: {len(context.regex_patterns)}")
        print(f"Type Specs: {[s.type_id for s in context.type_specs]}")
        print("\n--- Prompt Text ---")
        print(context.to_prompt_text())
    else:
        print("Usage: python itemspec_parser.py <path_to_item_spec.json>")
