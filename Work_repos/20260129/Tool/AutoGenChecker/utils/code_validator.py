"""
Code Validator for AutoGenChecker

This module provides static analysis and validation for AI-generated checker code.
It validates code BEFORE saving to catch common mistakes early.

Features:
1. Syntax validation (ast.parse)
2. API usage validation (known_issues.yaml patterns)
3. Required metadata validation (line_number, file_path)
4. Import validation

Usage:
    from utils.code_validator import CodeValidator
    
    validator = CodeValidator()
    errors, warnings = validator.validate(code)
    
    if errors:
        # Code has critical issues - needs AI fix
        fixed_code = ai_fix_code(code, errors)
    elif warnings:
        # Code has warnings - may work but not optimal
        print("Warnings:", warnings)

Author: AI Assistant
Date: 2025-12-16
Version: 1.0.0
"""

import ast
import re
import yaml
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class ValidationIssue:
    """Represents a validation issue found in code."""
    id: str
    category: str
    severity: str  # ERROR or WARNING
    message: str
    line_number: Optional[int] = None
    suggestion: Optional[str] = None


class CodeValidator:
    """
    Validates AI-generated checker code for common mistakes.
    
    Loads known issues from config/known_issues.yaml and checks code
    against all patterns. Also performs syntax validation.
    """
    
    def __init__(self, known_issues_path: Optional[Path] = None):
        """
        Initialize validator with known issues.
        
        Args:
            known_issues_path: Path to known_issues.yaml. If None, uses default.
        """
        if known_issues_path is None:
            # Find config directory relative to this file
            self_path = Path(__file__).resolve()
            config_dir = self_path.parent.parent / 'config'
            known_issues_path = config_dir / 'known_issues.yaml'
        
        self.known_issues: List[Dict[str, Any]] = []
        self._load_known_issues(known_issues_path)
    
    def _load_known_issues(self, path: Path) -> None:
        """Load known issues from YAML file."""
        if path.exists():
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                    self.known_issues = data.get('known_issues', [])
            except Exception as e:
                print(f"Warning: Could not load known_issues.yaml: {e}")
                self.known_issues = []
        else:
            print(f"Warning: known_issues.yaml not found at {path}")
            self.known_issues = []
    
    def validate(self, code: str) -> Tuple[List[ValidationIssue], List[ValidationIssue]]:
        """
        Validate code and return errors and warnings.
        
        Args:
            code: Python code string to validate
        
        Returns:
            Tuple of (errors, warnings) - lists of ValidationIssue
        """
        errors: List[ValidationIssue] = []
        warnings: List[ValidationIssue] = []
        
        # 1. Syntax validation
        syntax_error = self._validate_syntax(code)
        if syntax_error:
            errors.append(syntax_error)
            # If syntax is broken, skip other checks
            return errors, warnings
        
        # 2. Check against known issues
        for issue in self.known_issues:
            found = self._check_pattern(code, issue)
            if found:
                validation_issue = ValidationIssue(
                    id=issue.get('id', 'UNKNOWN'),
                    category=issue.get('category', 'UNKNOWN'),
                    severity=issue.get('severity', 'WARNING'),
                    message=issue.get('explanation', 'Unknown issue'),
                    suggestion=issue.get('correct_usage', None)
                )
                
                if validation_issue.severity == 'ERROR':
                    errors.append(validation_issue)
                else:
                    warnings.append(validation_issue)
        
        # 3. Check for required metadata in parsed items
        metadata_issues = self._check_metadata_requirements(code)
        warnings.extend(metadata_issues)
        
        # 4. Check imports
        import_issues = self._check_imports(code)
        errors.extend([i for i in import_issues if i.severity == 'ERROR'])
        warnings.extend([i for i in import_issues if i.severity == 'WARNING'])
        
        return errors, warnings
    
    def _validate_syntax(self, code: str) -> Optional[ValidationIssue]:
        """Check Python syntax using ast.parse."""
        try:
            ast.parse(code)
            return None
        except SyntaxError as e:
            return ValidationIssue(
                id='SYNTAX-000',
                category='SYNTAX',
                severity='ERROR',
                message=f"Syntax error at line {e.lineno}: {e.msg}",
                line_number=e.lineno,
                suggestion=f"Fix syntax near: {e.text.strip() if e.text else 'unknown'}"
            )
    
    def _check_pattern(self, code: str, issue: Dict[str, Any]) -> bool:
        """Check if code matches a known issue pattern."""
        pattern = issue.get('pattern', '')
        if not pattern:
            return False
        
        try:
            return bool(re.search(pattern, code))
        except re.error:
            # Invalid regex, try literal match
            return pattern in code
    
    def _check_metadata_requirements(self, code: str) -> List[ValidationIssue]:
        """Check if parsed items include required metadata."""
        issues = []
        
        # Check if code has _parse_input_files but doesn't include line_number/file_path
        if '_parse_input_files' in code:
            # Strategy: Look for variable assignments followed by .append() calls
            # This handles multi-line dict definitions properly
            
            # Find all patterns like: var_name = {...} followed later by .append(var_name)
            # Use two-pass approach:
            # 1. Find all .append(variable_name) calls
            # 2. For each variable, find its dict definition and check for metadata
            
            append_calls = re.findall(r"\.append\s*\(\s*(\w+)\s*\)", code)
            
            # De-duplicate variable names
            checked_vars = set()
            
            for var_name in append_calls:
                # Skip if already checked
                if var_name in checked_vars:
                    continue
                checked_vars.add(var_name)
                
                # Look backwards to find dict assignment: var_name = {
                # Match from assignment to closing brace, allowing nested content
                dict_pattern = rf"{var_name}\s*=\s*\{{([^}}]+\}})*[^}}]*\}}"
                dict_match = re.search(dict_pattern, code, re.DOTALL)
                
                # Only check if variable is assigned a dict AND has 'name' field
                # (indicates it's a parsed item dict, not a simple value)
                if dict_match:
                    dict_content = dict_match.group(0)
                    # Check if it contains 'name' field (indicates it's a parsed item)
                    if "'name'" in dict_content or '"name"' in dict_content:
                        # Now check for required metadata
                        has_line_number = "'line_number'" in dict_content or '"line_number"' in dict_content
                        has_file_path = "'file_path'" in dict_content or '"file_path"' in dict_content
                        
                        if not has_line_number or not has_file_path:
                            issues.append(ValidationIssue(
                                id='META-001',
                                category='OUTPUT_FORMAT',
                                severity='WARNING',
                                message="Parsed item may be missing 'line_number' or 'file_path' metadata",
                                suggestion="Add 'line_number': line_num, 'file_path': str(file_path) to each item dict"
                            ))
                            break  # Only report once
                # If no dict definition found, skip (it's probably a simple value like a string)
            
            # Also check inline dict creation patterns: .append({...})
            inline_appends = re.findall(r"\.append\s*\(\s*\{[^}]+\}\s*\)", code)
            if inline_appends and not issues:
                for match in inline_appends:
                    # Check if it's a parsed item (has 'name' field)
                    if "'name'" in match or '"name"' in match:
                        has_line_number = "'line_number'" in match or '"line_number"' in match
                        has_file_path = "'file_path'" in match or '"file_path"' in match
                        
                        if not has_line_number or not has_file_path:
                            issues.append(ValidationIssue(
                                id='META-001',
                                category='OUTPUT_FORMAT',
                                severity='WARNING',
                                message="Parsed item may be missing 'line_number' or 'file_path' metadata",
                                suggestion="Add 'line_number': line_num, 'file_path': str(file_path) to each item"
                            ))
                            break  # Only report once
        
        return issues
    
    def _check_imports(self, code: str) -> List[ValidationIssue]:
        """Check for common import issues."""
        issues = []
        
        # Check if using template mixins but not importing correctly
        mixins = ['WaiverHandlerMixin', 'OutputBuilderMixin', 'InputFileParserMixin']
        for mixin in mixins:
            if mixin in code:
                # Check for correct import pattern
                correct_import = f"from checker_templates."
                if correct_import not in code and f"import {mixin}" in code:
                    issues.append(ValidationIssue(
                        id='IMPORT-002',
                        category='SYNTAX',
                        severity='WARNING',
                        message=f"{mixin} should be imported from checker_templates.xxx_template",
                        suggestion=f"from checker_templates.xxx_template import {mixin}"
                    ))
        
        return issues
    
    def get_fix_prompt(self, errors: List[ValidationIssue], warnings: List[ValidationIssue]) -> str:
        """
        Generate a prompt for AI to fix the issues.
        
        Args:
            errors: List of error issues
            warnings: List of warning issues
        
        Returns:
            Prompt string for AI to fix the code
        """
        prompt_parts = ["The generated code has the following issues that need to be fixed:\n"]
        
        if errors:
            prompt_parts.append("## CRITICAL ERRORS (must fix):\n")
            for i, err in enumerate(errors, 1):
                prompt_parts.append(f"{i}. [{err.id}] {err.message}")
                if err.suggestion:
                    prompt_parts.append(f"   Correct usage:\n{err.suggestion}")
                prompt_parts.append("")
        
        if warnings:
            prompt_parts.append("\n## WARNINGS (should fix):\n")
            for i, warn in enumerate(warnings, 1):
                prompt_parts.append(f"{i}. [{warn.id}] {warn.message}")
                if warn.suggestion:
                    prompt_parts.append(f"   Suggestion:\n{warn.suggestion}")
                prompt_parts.append("")
        
        prompt_parts.append("\nPlease fix ALL the above issues and return the corrected code.")
        
        return "\n".join(prompt_parts)
    
    def format_issues_summary(self, errors: List[ValidationIssue], warnings: List[ValidationIssue]) -> str:
        """Format issues for display to user."""
        lines = []
        
        if errors:
            lines.append(f"❌ {len(errors)} ERROR(s) found:")
            for err in errors:
                lines.append(f"   [{err.id}] {err.message[:80]}...")
        
        if warnings:
            lines.append(f"⚠️  {len(warnings)} WARNING(s) found:")
            for warn in warnings:
                lines.append(f"   [{warn.id}] {warn.message[:80]}...")
        
        if not errors and not warnings:
            lines.append("✅ No issues found!")
        
        return "\n".join(lines)


def get_common_mistakes_prompt() -> str:
    """
    Get a formatted string of common mistakes for inclusion in prompts.
    
    This is used by the prompt builder to prevent issues before they happen.
    """
    validator = CodeValidator()
    
    lines = [
        "====================================================================================",
        "⚠️ COMMON MISTAKES TO AVOID (CRITICAL!)",
        "====================================================================================",
        ""
    ]
    
    for issue in validator.known_issues:
        if issue.get('severity') == 'ERROR':
            lines.append(f"❌ [{issue.get('id')}] {issue.get('category')}")
            lines.append(f"   WRONG:")
            for line in issue.get('wrong_usage', '').strip().split('\n'):
                lines.append(f"      {line}")
            lines.append(f"   CORRECT:")
            for line in issue.get('correct_usage', '').strip().split('\n'):
                lines.append(f"      {line}")
            lines.append("")
    
    return "\n".join(lines)


# Convenience function for quick validation
def validate_checker_code(code: str) -> Tuple[bool, str]:
    """
    Quick validation of checker code.
    
    Args:
        code: Python code to validate
    
    Returns:
        Tuple of (is_valid, message)
        is_valid: True if no errors (warnings OK)
        message: Summary of issues or success message
    """
    validator = CodeValidator()
    errors, warnings = validator.validate(code)
    
    is_valid = len(errors) == 0
    message = validator.format_issues_summary(errors, warnings)
    
    return is_valid, message


if __name__ == '__main__':
    # Test the validator
    test_code = '''
    def _parse_input_files(self):
        valid_files = self.validate_input_files()  # Wrong!
        for f in valid_files:
            pass
        return self.build_complete_output(item_desc="test")
    '''
    
    is_valid, message = validate_checker_code(test_code)
    print(f"Valid: {is_valid}")
    print(message)
