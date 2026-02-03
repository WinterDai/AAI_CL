"""
AST Validator - Tool Skill for CodeGen Agent

Version: v1.0.0
Created: 2025-12-22

Validates Python code using AST parsing without execution.
Provides detailed error information for Evaluator-Optimizer feedback loop.
"""

import ast
import tokenize
import io
import re
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass, field


@dataclass
class SyntaxErrorInfo:
    """Detailed syntax error information."""
    line: int
    column: int
    message: str
    code_snippet: str = ""
    suggestion: str = ""
    
    def to_dict(self) -> dict:
        return {
            "line": self.line,
            "column": self.column,
            "message": self.message,
            "code_snippet": self.code_snippet,
            "suggestion": self.suggestion
        }


@dataclass
class ValidationResult:
    """Result of code validation."""
    is_valid: bool
    errors: List[SyntaxErrorInfo] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    ast_tree: Optional[ast.Module] = None
    
    # Analysis results
    classes_found: List[str] = field(default_factory=list)
    methods_found: List[str] = field(default_factory=list)
    imports_found: List[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            "is_valid": self.is_valid,
            "errors": [e.to_dict() for e in self.errors],
            "warnings": self.warnings,
            "classes_found": self.classes_found,
            "methods_found": self.methods_found,
            "imports_found": self.imports_found
        }
    
    def get_fix_suggestions(self) -> List[str]:
        """Get all fix suggestions from errors."""
        return [e.suggestion for e in self.errors if e.suggestion]


def validate_code(
    code: str,
    check_style: bool = True,
    required_methods: Optional[List[str]] = None
) -> ValidationResult:
    """
    Validate Python code using AST parsing.
    
    Args:
        code: Python code to validate
        check_style: Also check basic style issues
        required_methods: List of method names that must be present
        
    Returns:
        ValidationResult with errors, warnings, and analysis
    """
    result = ValidationResult(is_valid=True)
    
    # Step 1: Parse with AST
    try:
        tree = ast.parse(code)
        result.ast_tree = tree
    except SyntaxError as e:
        result.is_valid = False
        result.errors.append(_syntax_error_to_info(e, code))
        return result
    
    # Step 2: Analyze AST
    _analyze_ast(tree, result)
    
    # Step 3: Check required methods
    if required_methods:
        missing = set(required_methods) - set(result.methods_found)
        if missing:
            for method in missing:
                result.warnings.append(f"Missing required method: {method}")
    
    # Step 4: Basic style checks
    if check_style:
        style_warnings = _check_basic_style(code)
        result.warnings.extend(style_warnings)
    
    return result


def validate_method_code(
    code: str,
    expected_name: str
) -> ValidationResult:
    """
    Validate a single method definition.
    
    Wraps the code in a class if needed to validate method syntax.
    """
    # Check if it's a method (starts with def)
    if code.strip().startswith('def '):
        # Wrap in class for AST parsing
        wrapped = f"class _Wrapper:\n" + "\n".join(
            f"    {line}" for line in code.split('\n')
        )
        result = validate_code(wrapped, check_style=False)
        
        # Verify method name
        if result.is_valid and expected_name not in result.methods_found:
            result.warnings.append(
                f"Expected method '{expected_name}' but found: {result.methods_found}"
            )
        
        return result
    else:
        # Try parsing as-is
        return validate_code(code, check_style=False)


def validate_checker_code(code: str) -> ValidationResult:
    """
    Validate complete Checker code with framework-specific checks.
    
    Checks for:
    - Required methods (_parse_input_files, _execute_type1-4)
    - Proper class inheritance
    - Required imports
    """
    required_methods = [
        '_parse_input_files',
        '_execute_type1',
        '_execute_type2', 
        '_execute_type3',
        '_execute_type4',
        'execute_check'
    ]
    
    result = validate_code(
        code,
        check_style=True,
        required_methods=required_methods
    )
    
    # Check for required base classes
    if result.is_valid and result.ast_tree:
        for node in ast.walk(result.ast_tree):
            if isinstance(node, ast.ClassDef):
                bases = [_get_name(b) for b in node.bases]
                
                # Check for BaseChecker
                if 'BaseChecker' not in bases:
                    result.warnings.append(
                        f"Class {node.name} should inherit from BaseChecker"
                    )
                
                # Check for Mixins
                required_mixins = ['InputFileParserMixin', 'OutputBuilderMixin', 'WaiverHandlerMixin']
                for mixin in required_mixins:
                    if mixin not in bases:
                        result.warnings.append(
                            f"Class {node.name} missing mixin: {mixin}"
                        )
    
    return result


# ============================================================================
# Helper Functions
# ============================================================================

def _syntax_error_to_info(error: SyntaxError, code: str) -> SyntaxErrorInfo:
    """Convert Python SyntaxError to SyntaxErrorInfo."""
    lines = code.split('\n')
    
    # Get code snippet around error
    snippet = ""
    if error.lineno and 0 < error.lineno <= len(lines):
        start = max(0, error.lineno - 2)
        end = min(len(lines), error.lineno + 1)
        snippet_lines = []
        for i in range(start, end):
            prefix = ">>> " if i == error.lineno - 1 else "    "
            snippet_lines.append(f"{prefix}{i+1}: {lines[i]}")
        snippet = "\n".join(snippet_lines)
    
    # Generate suggestion
    suggestion = _suggest_fix(error, lines)
    
    return SyntaxErrorInfo(
        line=error.lineno or 0,
        column=error.offset or 0,
        message=str(error.msg),
        code_snippet=snippet,
        suggestion=suggestion
    )


def _suggest_fix(error: SyntaxError, lines: List[str]) -> str:
    """Suggest a fix based on common syntax errors."""
    msg = str(error.msg).lower() if error.msg else ""
    
    if "unexpected eof" in msg:
        return "Check for unclosed parentheses, brackets, or strings"
    elif "invalid syntax" in msg:
        if error.lineno and error.lineno > 0:
            line = lines[error.lineno - 1] if error.lineno <= len(lines) else ""
            if ':' not in line and (line.strip().startswith('def ') or 
                                    line.strip().startswith('class ') or
                                    line.strip().startswith('if ') or
                                    line.strip().startswith('for ')):
                return "Missing colon ':' at end of statement"
        return "Check for typos, missing operators, or incorrect indentation"
    elif "unterminated string" in msg:
        return "Check for unclosed quotes (single ', double \", or triple ''')"
    elif "expected ':'" in msg:
        return "Add colon ':' at the end of the statement"
    elif "indentation" in msg:
        return "Fix indentation - use consistent 4 spaces per level"
    
    return ""


def _analyze_ast(tree: ast.Module, result: ValidationResult) -> None:
    """Analyze AST to extract classes, methods, and imports."""
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            result.classes_found.append(node.name)
        elif isinstance(node, ast.FunctionDef):
            result.methods_found.append(node.name)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                result.imports_found.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for alias in node.names:
                result.imports_found.append(f"{module}.{alias.name}")


def _get_name(node: ast.expr) -> str:
    """Get name from AST node (Name or Attribute)."""
    if isinstance(node, ast.Name):
        return node.id
    elif isinstance(node, ast.Attribute):
        return node.attr
    return ""


def _check_basic_style(code: str) -> List[str]:
    """Check basic style issues."""
    warnings = []
    lines = code.split('\n')
    
    for i, line in enumerate(lines, 1):
        # Check line length
        if len(line) > 120:
            warnings.append(f"Line {i}: Line too long ({len(line)} > 120 chars)")
        
        # Check trailing whitespace
        if line.rstrip() != line and line.strip():
            warnings.append(f"Line {i}: Trailing whitespace")
        
        # Check tabs vs spaces
        if '\t' in line:
            warnings.append(f"Line {i}: Tab character found (use spaces)")
    
    # Check for missing docstrings on classes and methods
    try:
        tree = ast.parse(code)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                if not ast.get_docstring(node):
                    warnings.append(f"Missing docstring for {node.name}")
    except SyntaxError:
        pass  # Already reported in main validation
    
    return warnings


# ============================================================================
# Quick Validation Functions
# ============================================================================

def is_valid_python(code: str) -> bool:
    """Quick check if code is valid Python syntax."""
    try:
        ast.parse(code)
        return True
    except SyntaxError:
        return False


def get_syntax_errors(code: str) -> List[SyntaxErrorInfo]:
    """Get only syntax errors from code."""
    result = validate_code(code, check_style=False)
    return result.errors


def count_methods(code: str) -> int:
    """Count number of method/function definitions in code."""
    result = validate_code(code, check_style=False)
    return len(result.methods_found)


if __name__ == "__main__":
    # Test with various code samples
    
    # Valid code
    valid_code = '''
def _parse_input_files(self) -> Dict[str, Any]:
    """Parse input files."""
    return {'items': [], 'metadata': {}, 'errors': []}
'''
    
    # Invalid code (missing colon)
    invalid_code = '''
def _parse_input_files(self)
    return {'items': []}
'''
    
    print("=== Valid Code ===")
    result = validate_method_code(valid_code, "_parse_input_files")
    print(f"Is valid: {result.is_valid}")
    print(f"Methods found: {result.methods_found}")
    
    print("\n=== Invalid Code ===")
    result = validate_method_code(invalid_code, "_parse_input_files")
    print(f"Is valid: {result.is_valid}")
    for error in result.errors:
        print(f"Error at line {error.line}: {error.message}")
        print(f"Suggestion: {error.suggestion}")
