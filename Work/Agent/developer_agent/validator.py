"""
Developer Agent - Validator Implementation
Based on Agent_Development_Spec.md v1.1

Implements three-layer validation: AST + Runtime Sandbox + Consistency Check
Complies with Plan_v2.txt Gate 1/2/3 requirements.
"""
from typing import Dict, Any, List
import ast
import re
import fnmatch


def validate_10_2_compliance(code_str: str, yaml_str: str) -> Dict[str, Any]:
    """
    Three-layer validator: AST Static Check + Runtime Sandbox + Consistency Check
    
    Based on Plan_v2.txt Gate 1/2 requirements.
    
    Args:
        code_str: Combined Python code (Atom A + B + C)
        yaml_str: YAML configuration string
        
    Returns:
        {
            "valid": bool,
            "errors": List[str],
            "gate_results": {
                "gate1_signature": bool,
                "gate1_schema": bool,
                "gate1_type_safety": bool,
                "gate2_none_safety": bool,
                "gate2_alternatives": bool,
                "gate2_bad_regex": bool,
                "gate2_precedence": bool,
                "gate2_literal_alt": bool,
                "gate2_default_strategy": bool,
                "gate2_invalid_mode": bool,
                "consistency": bool
            }
        }
    """
    errors = []
    gate_results = {}

    # === Level 1: AST Static Safety Check (Plan_v2.txt L14, L405-427) ===
    try:
        tree = ast.parse(code_str)
        
        # Check for forbidden IO operations
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                if node.func.id in ['open', 'read', 'write', 'print', 'eval', 'exec']:
                    errors.append(f"CRITICAL [Gate1]: Forbidden IO function '{node.func.id}' detected.")
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                for alias in node.names:
                    if alias.name in ['os', 'sys', 'subprocess', 'pathlib']:
                        errors.append(f"CRITICAL [Gate1]: Forbidden import '{alias.name}' detected.")
        
        # Check function signatures
        func_names = {node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}
        
        required_funcs = ['extract_context', 'validate_logic', 'check_existence']
        gate_results["gate1_signature"] = all(name in func_names for name in required_funcs)
        if not gate_results["gate1_signature"]:
            missing = [f for f in required_funcs if f not in func_names]
            errors.append(f"FAIL [Gate1]: Missing required function(s): {missing}")
        
    except SyntaxError as e:
        return {"valid": False, "errors": [f"Syntax Error: {e}"], "gate_results": {}}

    # Stop early if critical errors found
    if any("CRITICAL" in e for e in errors):
        return {"valid": False, "errors": errors, "gate_results": gate_results}

    # === Level 2: Runtime Sandbox Tests (Plan_v2.txt L431-452) ===
    local_scope = {}
    try:
        # Strip import statements from code before exec (they're provided via globals)
        # This allows generated code to have imports for standalone use while still being testable
        code_lines = code_str.split('\n')
        clean_lines = []
        for line in code_lines:
            stripped = line.strip()
            # Skip import statements for re, fnmatch, typing (provided in globals)
            if stripped.startswith('import re') or stripped.startswith('import fnmatch'):
                continue
            if stripped.startswith('from typing import'):
                continue
            clean_lines.append(line)
        clean_code = '\n'.join(clean_lines)
        
        # Provide necessary modules and typing constructs in globals
        # Use a single namespace so recursive function calls work properly
        from typing import Dict, List, Optional, Any
        exec_namespace = {
            "re": re, 
            "fnmatch": fnmatch,
            "Dict": Dict,
            "List": List,
            "Optional": Optional,
            "Any": Any,
            "__builtins__": {"str": str, "int": int, "float": float, "bool": bool, 
                           "list": list, "dict": dict, "len": len, "range": range,
                           "isinstance": isinstance, "type": type, "set": set,
                           "True": True, "False": False, "None": None,
                           "enumerate": enumerate, "zip": zip, "map": map,
                           "min": min, "max": max, "sum": sum, "abs": abs,
                           "sorted": sorted, "reversed": reversed, "filter": filter}
        }
        # Use same dict for both globals and locals so recursive calls work
        exec(clean_code, exec_namespace, exec_namespace)
        local_scope = exec_namespace
        
        # Gate 1: Type Lock Test
        if 'extract_context' in local_scope:
            func = local_scope['extract_context']
            try:
                mock_result = func("Test line with value 123", "test.log")
                
                gate_results["gate1_schema"] = isinstance(mock_result, list)
                if mock_result and len(mock_result) > 0:
                    item = mock_result[0]
                    gate_results["gate1_type_safety"] = isinstance(item.get('value'), str)
                    if not gate_results.get("gate1_type_safety", True):
                        errors.append(f"FAIL [Gate1]: 'value' is {type(item.get('value'))}, MUST be str")
                    
                    required_keys = {'value', 'source_file', 'line_number', 'matched_content', 'parsed_fields'}
                    actual_keys = set(item.keys())
                    missing_keys = required_keys - actual_keys
                    if missing_keys:
                        errors.append(f"FAIL [Gate1]: Missing keys in ParsedItem: {missing_keys}")
                        gate_results["gate1_schema"] = False
                else:
                    # Empty result is acceptable
                    gate_results["gate1_type_safety"] = True
            except Exception as e:
                errors.append(f"FAIL [Gate1]: extract_context raised exception: {e}")
                gate_results["gate1_schema"] = False
                gate_results["gate1_type_safety"] = False
        
        # Gate 2: Atom B Test Vectors
        if 'validate_logic' in local_scope:
            func = local_scope['validate_logic']
            
            # Test 1: None-Safety (Plan_v2.txt L433)
            try:
                func("abc", "a", parsed_fields=None)
                gate_results["gate2_none_safety"] = True
            except Exception:
                gate_results["gate2_none_safety"] = False
                errors.append("FAIL [Gate2]: None-Safety test failed - function should handle parsed_fields=None")
            
            # Test 2: Empty Alternatives (Plan_v2.txt L436)
            try:
                res = func("abc", "|a||")
                gate_results["gate2_alternatives"] = (
                    res.get('is_match') == True and 
                    res.get('kind') == 'alternatives'
                )
                if not gate_results["gate2_alternatives"]:
                    errors.append(f"FAIL [Gate2]: Empty Alternatives test failed. Got: {res}")
            except Exception as e:
                gate_results["gate2_alternatives"] = False
                errors.append(f"FAIL [Gate2]: Empty Alternatives test raised exception: {e}")
            
            # Test 3: Bad Regex (Plan_v2.txt L439)
            try:
                res = func("abc", "regex:[", regex_mode="search")
                gate_results["gate2_bad_regex"] = (
                    res.get('is_match') == False and 
                    'invalid' in res.get('reason', '').lower()
                )
                if not gate_results["gate2_bad_regex"]:
                    errors.append(f"FAIL [Gate2]: Bad Regex handling test failed. Got: {res}")
            except Exception as e:
                gate_results["gate2_bad_regex"] = False
                errors.append(f"FAIL [Gate2]: Bad Regex test raised exception: {e}")
            
            # Test 4: Literal Alternatives (Plan_v2.txt L442-443)
            try:
                res_literal = func("regex:^a", "regex:^a|zzz")
                gate_results["gate2_literal_alt"] = res_literal.get('is_match') == True
                if not gate_results["gate2_literal_alt"]:
                    errors.append("FAIL [Gate2]: Literal Alternatives test failed - 'regex:^a' should match as literal in alternatives")
            except Exception as e:
                gate_results["gate2_literal_alt"] = False
                errors.append(f"FAIL [Gate2]: Literal Alternatives test raised exception: {e}")
            
            # Test 5: Wildcard Priority (Plan_v2.txt L447)
            try:
                res = func("abc", "a*c")
                gate_results["gate2_precedence"] = res.get('kind') == 'wildcard'
                if not gate_results["gate2_precedence"]:
                    errors.append(f"FAIL [Gate2]: Wildcard precedence test failed. Got kind: {res.get('kind')}")
            except Exception as e:
                gate_results["gate2_precedence"] = False
                errors.append(f"FAIL [Gate2]: Wildcard precedence test raised exception: {e}")
            
            # Test 6: Default Strategy Policy (Plan_v2.txt L449-450)
            try:
                res_contains = func("abc", "b", default_match="contains")
                res_exact = func("abc", "b", default_match="exact")
                gate_results["gate2_default_strategy"] = (
                    res_contains.get('is_match') == True and 
                    res_contains.get('kind') == 'contains' and
                    res_exact.get('is_match') == False and
                    res_exact.get('kind') == 'exact'
                )
                if not gate_results["gate2_default_strategy"]:
                    errors.append(f"FAIL [Gate2]: Default Strategy Policy test failed. contains={res_contains}, exact={res_exact}")
            except Exception as e:
                gate_results["gate2_default_strategy"] = False
                errors.append(f"FAIL [Gate2]: Default Strategy Policy test raised exception: {e}")
            
            # Test 7: regex_mode Invalid Value (Plan_v2.txt L452)
            try:
                res_bad_mode = func("abc", "regex:^a", regex_mode="INVALID_MODE")
                gate_results["gate2_invalid_mode"] = res_bad_mode.get('is_match') == True
                if not gate_results["gate2_invalid_mode"]:
                    errors.append("FAIL [Gate2]: Invalid regex_mode should default to search behavior")
            except Exception:
                gate_results["gate2_invalid_mode"] = False
                errors.append("FAIL [Gate2]: Invalid regex_mode raised exception instead of defaulting to search")
        
        # Gate 1: Atom C evidence field (Plan_v2.txt L157)
        if 'check_existence' in local_scope:
            func = local_scope['check_existence']
            try:
                evidence = [{'value': 'test'}]
                res = func(evidence)
                if res.get('evidence') != evidence:
                    errors.append("FAIL [Gate1]: Atom C failed to pass through 'evidence' list")
                    gate_results["gate1_evidence"] = False
                else:
                    gate_results["gate1_evidence"] = True
            except Exception as e:
                errors.append(f"FAIL [Gate1]: check_existence raised exception: {e}")
                gate_results["gate1_evidence"] = False

    except Exception as e:
        errors.append(f"Runtime Error: {str(e)}")

    # === Level 3: Dual Artifact Consistency Check ===
    if "regex:" in yaml_str:
        # YAML specifies regex, check if code handles regex
        code_lower = code_str.lower()
        if "re." not in code_str and "regex" not in code_lower:
            errors.append("Consistency Error: YAML specifies regex pattern, but code lacks regex handling")
            gate_results["consistency"] = False
        else:
            gate_results["consistency"] = True
    else:
        gate_results["consistency"] = True

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "gate_results": gate_results
    }


def determine_error_source(validation_errors: List[str]) -> str:
    """
    Analyze validation errors to determine which Atom caused the failure
    
    Args:
        validation_errors: List of error messages
        
    Returns:
        "atom_a" | "atom_b" | "atom_c" | "yaml" | "unknown"
    """
    error_text = " ".join(validation_errors).lower()
    
    # Atom A related keywords
    atom_a_keywords = [
        "extract_context", "parseditem", "atom a",
        "missing keys", "source_file", "line_number", 
        "matched_content", "type(item.get('value'))",
        "gate1_schema", "gate1_type_safety"
    ]
    
    # Atom B related keywords
    atom_b_keywords = [
        "validate_logic", "atom b", "kind", "precedence",
        "alternatives", "regex_mode", "wildcard", "gate2"
    ]
    
    # Atom C related keywords
    atom_c_keywords = [
        "check_existence", "atom c", "evidence"
    ]
    
    # YAML related keywords
    yaml_keywords = [
        "yaml", "consistency", "pattern_items", "waive_items"
    ]
    
    # Priority-based detection
    if any(kw in error_text for kw in atom_a_keywords):
        return "atom_a"
    elif any(kw in error_text for kw in atom_b_keywords):
        return "atom_b"
    elif any(kw in error_text for kw in atom_c_keywords):
        return "atom_c"
    elif any(kw in error_text for kw in yaml_keywords):
        return "yaml"
    else:
        return "unknown"


def validate_atom_a_only(code_str: str) -> Dict[str, Any]:
    """
    Validate only Atom A (extract_context)
    
    Args:
        code_str: Atom A code
        
    Returns:
        Validation result dictionary
    """
    errors = []
    gate_results = {}
    
    try:
        tree = ast.parse(code_str)
        
        # Check function exists
        func_names = {node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}
        gate_results["has_extract_context"] = 'extract_context' in func_names
        
        if not gate_results["has_extract_context"]:
            errors.append("FAIL: Missing extract_context function")
            return {"valid": False, "errors": errors, "gate_results": gate_results}
        
        # Execute and test
        local_scope = {}
        exec(code_str, {"re": re}, local_scope)
        
        func = local_scope['extract_context']
        result = func("Test line with value 123", "test.log")
        
        gate_results["returns_list"] = isinstance(result, list)
        
        if result and len(result) > 0:
            item = result[0]
            required_keys = {'value', 'source_file', 'line_number', 'matched_content', 'parsed_fields'}
            gate_results["has_required_keys"] = required_keys.issubset(set(item.keys()))
            gate_results["value_is_string"] = isinstance(item.get('value'), str)
            
            if not gate_results["has_required_keys"]:
                missing = required_keys - set(item.keys())
                errors.append(f"FAIL: Missing keys: {missing}")
            if not gate_results["value_is_string"]:
                errors.append(f"FAIL: 'value' must be str, got {type(item.get('value'))}")
        
    except SyntaxError as e:
        errors.append(f"Syntax Error: {e}")
    except Exception as e:
        errors.append(f"Runtime Error: {e}")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "gate_results": gate_results
    }


def validate_atom_b_only(code_str: str) -> Dict[str, Any]:
    """
    Validate only Atom B (validate_logic)
    
    Args:
        code_str: Atom B code
        
    Returns:
        Validation result dictionary
    """
    errors = []
    gate_results = {}
    
    try:
        tree = ast.parse(code_str)
        
        # Check function exists
        func_names = {node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}
        gate_results["has_validate_logic"] = 'validate_logic' in func_names
        
        if not gate_results["has_validate_logic"]:
            errors.append("FAIL: Missing validate_logic function")
            return {"valid": False, "errors": errors, "gate_results": gate_results}
        
        # Execute and run Gate 2 tests
        local_scope = {}
        exec(code_str, {"re": re, "fnmatch": fnmatch}, local_scope)
        
        func = local_scope['validate_logic']
        
        # Run all Gate 2 tests
        test_results = _run_gate2_tests(func)
        gate_results.update(test_results["gate_results"])
        errors.extend(test_results["errors"])
        
    except SyntaxError as e:
        errors.append(f"Syntax Error: {e}")
    except Exception as e:
        errors.append(f"Runtime Error: {e}")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "gate_results": gate_results
    }


def _run_gate2_tests(func) -> Dict[str, Any]:
    """Run all Gate 2 tests on validate_logic function"""
    errors = []
    gate_results = {}
    
    # Test 1: None-Safety
    try:
        func("abc", "a", parsed_fields=None)
        gate_results["none_safety"] = True
    except Exception:
        gate_results["none_safety"] = False
        errors.append("FAIL: None-Safety test failed")
    
    # Test 2: Empty Alternatives
    try:
        res = func("abc", "|a||")
        gate_results["alternatives"] = res.get('is_match') == True and res.get('kind') == 'alternatives'
        if not gate_results["alternatives"]:
            errors.append(f"FAIL: Empty Alternatives test failed. Got: {res}")
    except Exception as e:
        gate_results["alternatives"] = False
        errors.append(f"FAIL: Alternatives test exception: {e}")
    
    # Test 3: Bad Regex
    try:
        res = func("abc", "regex:[", regex_mode="search")
        gate_results["bad_regex"] = res.get('is_match') == False and 'invalid' in res.get('reason', '').lower()
        if not gate_results["bad_regex"]:
            errors.append(f"FAIL: Bad Regex test failed. Got: {res}")
    except Exception as e:
        gate_results["bad_regex"] = False
        errors.append(f"FAIL: Bad Regex test exception: {e}")
    
    # Test 4: Literal Alternatives
    try:
        res = func("regex:^a", "regex:^a|zzz")
        gate_results["literal_alt"] = res.get('is_match') == True
        if not gate_results["literal_alt"]:
            errors.append("FAIL: Literal Alternatives test failed")
    except Exception as e:
        gate_results["literal_alt"] = False
        errors.append(f"FAIL: Literal Alternatives exception: {e}")
    
    # Test 5: Wildcard Priority
    try:
        res = func("abc", "a*c")
        gate_results["wildcard_priority"] = res.get('kind') == 'wildcard'
        if not gate_results["wildcard_priority"]:
            errors.append(f"FAIL: Wildcard priority test failed. Got kind: {res.get('kind')}")
    except Exception as e:
        gate_results["wildcard_priority"] = False
        errors.append(f"FAIL: Wildcard test exception: {e}")
    
    # Test 6: Default Strategy
    try:
        res_contains = func("abc", "b", default_match="contains")
        res_exact = func("abc", "b", default_match="exact")
        gate_results["default_strategy"] = (
            res_contains.get('is_match') == True and 
            res_contains.get('kind') == 'contains' and
            res_exact.get('is_match') == False and
            res_exact.get('kind') == 'exact'
        )
        if not gate_results["default_strategy"]:
            errors.append(f"FAIL: Default Strategy test failed")
    except Exception as e:
        gate_results["default_strategy"] = False
        errors.append(f"FAIL: Default Strategy exception: {e}")
    
    # Test 7: Invalid regex_mode
    try:
        res = func("abc", "regex:^a", regex_mode="INVALID_MODE")
        gate_results["invalid_mode"] = res.get('is_match') == True
        if not gate_results["invalid_mode"]:
            errors.append("FAIL: Invalid regex_mode should default to search")
    except Exception:
        gate_results["invalid_mode"] = False
        errors.append("FAIL: Invalid regex_mode raised exception")
    
    return {"errors": errors, "gate_results": gate_results}
