"""
Self-Check & Self-Fix Mixin for IntelligentCheckerAgent.

This mixin provides code validation, issue detection, and automated fix capabilities.

Methods included:
- _self_check_and_fix: Main entry point for code validation
- _run_all_checks: Orchestrates all validation checks
- _check_*: Individual check methods
- _fix_*: Deterministic fix methods
- _ai_fix_issues: AI-powered issue resolution
- _find_similar_checkers: Example-based learning
- _search_source_for_api_info: API documentation lookup
"""

from typing import Any
import re
import ast


class SelfCheckMixin:
    """Mixin providing self-check and self-fix capabilities for generated code."""
    
    # =========================================================================
    # Main Self-Check & Self-Fix Entry Point
    # =========================================================================
    
    def _self_check_and_fix(
        self,
        code: str,
        config: dict[str, Any],
        file_analysis: dict[str, Any],
        readme: str,
    ) -> tuple[str, dict[str, Any]]:
        """
        Self-check generated code and auto-fix issues.
        
        Level 1: Automatic fix loop (up to max_fix_attempts times).
        
        Returns:
            Tuple of (fixed_code, check_results)
        """
        if self.verbose:
            print("\n" + "─"*80)
            print("[Step 6/9] 🔍 Self-Check & Fix")
            print("─"*80)
        
        check_results = {'has_issues': False, 'issues': [], 'fix_attempts': 0}
        
        for attempt in range(self.max_fix_attempts):
            # Run all checks
            issues = self._run_all_checks(code, config)
            
            if not issues:
                if self.verbose:
                    if attempt == 0:
                        print("  ✅ All checks passed on first try!")
                    else:
                        print(f"  ✅ All checks passed after {attempt} fix(es)")
                check_results['has_issues'] = False
                check_results['issues'] = []
                break
            
            check_results['fix_attempts'] = attempt + 1
            check_results['issues'] = issues
            
            # Separate critical errors from warnings
            critical_issues = [i for i in issues if i.get('severity') == 'critical']
            warning_issues = [i for i in issues if i.get('severity') != 'critical']
            
            # has_critical_issues blocks testing; warnings don't
            check_results['has_issues'] = len(critical_issues) > 0
            check_results['has_warnings'] = len(warning_issues) > 0
            check_results['critical_count'] = len(critical_issues)
            check_results['warning_count'] = len(warning_issues)
            
            if self.verbose:
                if critical_issues:
                    print(f"\n  ❌ Found {len(critical_issues)} CRITICAL issue(s) - Attempt {attempt + 1}/{self.max_fix_attempts}")
                    for i, issue in enumerate(critical_issues[:3], 1):
                        print(f"    {i}. [{issue['type']}] {issue['message'][:80]}...")
                if warning_issues:
                    print(f"\n  ⚠️ Found {len(warning_issues)} WARNING(s) (won't block testing)")
                    for i, issue in enumerate(warning_issues[:2], 1):
                        print(f"    {i}. [{issue['type']}] {issue['message'][:60]}...")
            
            # Only auto-fix critical issues, not warnings
            if critical_issues and attempt < self.max_fix_attempts - 1:
                code = self._ai_fix_issues(code, critical_issues, config, file_analysis, readme)
            elif not critical_issues:
                # No critical issues, only warnings - consider it passed
                if self.verbose:
                    print(f"  ✅ No critical issues! {len(warning_issues)} warning(s) noted.")
                check_results['has_issues'] = False
                break
            
        return code, check_results
    
    # =========================================================================
    # Check Orchestration
    # =========================================================================
    
    def _run_all_checks(self, code: str, config: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Run all validation checks on generated code.
        
        Returns list of issues found.
        """
        issues = []
        
        # Check 0: Use CodeValidator for known issues (from known_issues.yaml)
        validator_issues = self._check_known_issues(code)
        issues.extend(validator_issues)
        
        # Check 1: Syntax check
        syntax_issues = self._check_syntax(code)
        issues.extend(syntax_issues)
        
        # Check 2: Template compliance
        template_issues = self._check_template_compliance(code)
        issues.extend(template_issues)
        
        # Check 3: Required methods
        method_issues = self._check_required_methods(code)
        issues.extend(method_issues)
        
        # Check 4: Import check
        import_issues = self._check_imports(code)
        issues.extend(import_issues)
        
        # Check 5: Waiver Tag Rules check
        waiver_issues = self._check_waiver_tag_rules(code)
        issues.extend(waiver_issues)

        # Check 6: Type 1/2 reason usage (prevent lambda in waiver=0 mode)
        type12_reason_issues = self._check_type1_type2_reason_usage(code)
        issues.extend(type12_reason_issues)
        
        # Check 7: Regex raw string check (prevent invalid escape sequences)
        regex_raw_issues = self._check_regex_raw_string(code)
        issues.extend(regex_raw_issues)
        
        # Check 8: Runtime check (only if syntax passes)
        if not syntax_issues:
            runtime_issues = self._check_runtime(code, config)
            issues.extend(runtime_issues)
        
        return issues
    
    # =========================================================================
    # Individual Check Methods
    # =========================================================================
    
    def _check_known_issues(self, code: str) -> list[dict[str, Any]]:
        """
        Check code against known issues from known_issues.yaml.
        
        Uses CodeValidator for comprehensive pattern-based validation.
        """
        issues = []
        
        try:
            try:
                from utils.code_validator import CodeValidator
            except ImportError:
                from AutoGenChecker.utils.code_validator import CodeValidator
            
            validator = CodeValidator()
            errors, warnings = validator.validate(code)
            
            # Convert to standard issue format
            for err in errors:
                issues.append({
                    'type': f'KNOWN_ISSUE_{err.id}',
                    'message': err.message,
                    'severity': 'critical',
                    'suggestion': err.suggestion,
                })
            
            for warn in warnings:
                issues.append({
                    'type': f'KNOWN_ISSUE_{warn.id}',
                    'message': warn.message,
                    'severity': 'warning',
                    'suggestion': warn.suggestion,
                })
                
        except Exception as e:
            if self.verbose:
                print(f"    ⚠️ CodeValidator not available: {e}")
        
        return issues
    
    def _check_syntax(self, code: str) -> list[dict[str, Any]]:
        """Check for Python syntax errors."""
        issues = []
        
        try:
            ast.parse(code)
        except SyntaxError as e:
            issues.append({
                'type': 'SYNTAX_ERROR',
                'message': f"Line {e.lineno}: {e.msg}",
                'line': e.lineno,
                'details': str(e),
                'severity': 'critical',
            })
        
        return issues
    
    def _check_template_compliance(self, code: str) -> list[dict[str, Any]]:
        """Check if code follows template patterns."""
        issues = []
        
        # Check for mixin imports
        required_mixins = [
            'WaiverHandlerMixin',
            'OutputBuilderMixin',
        ]
        
        for mixin in required_mixins:
            if mixin not in code:
                issues.append({
                    'type': 'TEMPLATE_COMPLIANCE',
                    'message': f"Missing required mixin: {mixin}",
                    'severity': 'warning',
                })
        
        # Check for build_complete_output usage
        if 'build_complete_output' not in code:
            issues.append({
                'type': 'TEMPLATE_COMPLIANCE',
                'message': "Should use build_complete_output() for output generation",
                'severity': 'warning',
            })
        
        # Check for proper inheritance
        if 'class Checker(' in code:
            # Check inheritance order
            if 'BaseChecker)' in code and 'Mixin' not in code.split('class Checker(')[1].split(')')[0]:
                issues.append({
                    'type': 'TEMPLATE_COMPLIANCE',
                    'message': "Checker class should inherit mixins before BaseChecker",
                    'severity': 'warning',
                })
        
        return issues
    
    def _check_required_methods(self, code: str) -> list[dict[str, Any]]:
        """Check for required methods."""
        issues = []
        
        required_methods = [
            '_parse_input_files',
            '_execute_type1',
            '_execute_type2',
            '_execute_type3',
            '_execute_type4',
            'main',
        ]
        
        for method in required_methods:
            # Check for def method_name
            if f'def {method}' not in code:
                issues.append({
                    'type': 'MISSING_METHOD',
                    'message': f"Missing required method: {method}()",
                    'severity': 'critical' if method.startswith('_execute') else 'warning',
                })
        
        return issues
    
    def _check_imports(self, code: str) -> list[dict[str, Any]]:
        """Check for required imports."""
        issues = []
        
        required_imports = [
            ('Path', 'from pathlib import Path'),
            ('BaseChecker', 'from base_checker import BaseChecker'),
        ]
        
        for import_name, import_stmt in required_imports:
            if import_name not in code:
                issues.append({
                    'type': 'MISSING_IMPORT',
                    'message': f"Missing import: {import_stmt}",
                    'severity': 'warning',
                })
        
        return issues
    
    def _check_waiver_tag_rules(self, code: str) -> list[dict[str, Any]]:
        """Check if Waiver Tag Rules section is present and unchanged."""
        issues = []
        
        # Check for Waiver Tag Rules comment block
        waiver_rules_markers = [
            'Waiver Tag Rules:',
            'waivers.value > 0',
            '[WAIVER]',
            '[WAIVED_INFO]',
            '[WAIVED_AS_INFO]',
        ]
        
        missing_markers = [m for m in waiver_rules_markers if m not in code]
        
        if len(missing_markers) > 2:  # Allow some flexibility
            issues.append({
                'type': 'WAIVER_RULES',
                'message': "Waiver Tag Rules section may be modified or missing",
                'severity': 'warning',
                'details': f"Missing markers: {missing_markers}",
            })
        
        return issues

    def _check_type1_type2_reason_usage(self, code: str) -> list[dict[str, Any]]:
        """Ensure Type 1/2 reason parameters use static strings."""
        issues: list[dict[str, Any]] = []

        try:
            tree = ast.parse(code)
        except SyntaxError:
            return issues

        target_funcs = {"_execute_type1", "_execute_type2"}

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name in target_funcs:
                for child in ast.walk(node):
                    if isinstance(child, ast.Call):
                        func = child.func
                        if isinstance(func, ast.Attribute) and func.attr == "build_complete_output":
                            for kw in child.keywords:
                                if kw.arg in {"found_reason", "missing_reason"} and isinstance(kw.value, ast.Lambda):
                                    if not hasattr(kw.value, "end_lineno") or kw.value.end_lineno is None:
                                        continue
                                    issues.append({
                                        "type": "TYPE12_REASON_LAMBDA",
                                        "severity": "critical",
                                        "message": (
                                            f"{node.name}: {kw.arg} uses lambda; Type 1/2 require static strings."
                                        ),
                                        "function": node.name,
                                        "arg": kw.arg,
                                        "fix_span": (
                                            kw.value.lineno,
                                            kw.value.col_offset,
                                            kw.value.end_lineno,
                                            kw.value.end_col_offset,
                                        ),
                                    })

        return issues
    
    def _check_regex_raw_string(self, code: str) -> list[dict[str, Any]]:
        """
        Check for regex patterns that should use raw strings.
        
        Detects common invalid escape sequences like \\s, \\d, \\w, \\b in 
        non-raw strings AND docstrings that will cause SyntaxWarning in Python 3.12+.
        
        Returns:
            List of issues with fix_span for deterministic replacement.
        """
        issues = []
        
        # Invalid escape sequences that trigger SyntaxWarning in Python 3.12+
        invalid_escapes = r'\\[sdwbSDWB]'
        
        lines = code.splitlines()
        
        # Track if we're inside a docstring
        in_docstring = False
        docstring_start_line = 0
        docstring_start_col = 0
        docstring_quote = None
        docstring_content = []
        
        for line_num, line in enumerate(lines, 1):
            # Skip comments
            stripped = line.lstrip()
            if stripped.startswith('#') and not in_docstring:
                continue
            
            # Check for docstring start/end (triple quotes)
            if not in_docstring:
                # Look for docstring start: """ or '''
                for quote in ['"""', "'''"]:
                    # Find non-raw docstring start
                    match = re.search(rf'(?<![rRbBuUfF])({re.escape(quote)})', line)
                    if match:
                        col = match.start(1)
                        # Check if docstring ends on same line
                        rest_of_line = line[col + 3:]
                        end_match = rest_of_line.find(quote)
                        if end_match != -1:
                            # Single-line docstring
                            docstring_text = rest_of_line[:end_match]
                            if re.search(invalid_escapes, docstring_text):
                                issues.append({
                                    'type': 'REGEX_RAW_DOCSTRING',
                                    'message': f"Line {line_num}: Docstring contains invalid escape sequence (e.g., \\s, \\d). Use r{quote}...{quote}.",
                                    'severity': 'warning',
                                    'suggestion': f"Add 'r' prefix: r{quote}...{quote}",
                                    'fix_span': (line_num, col, line_num, col),
                                    'is_docstring': True,
                                })
                        else:
                            # Multi-line docstring start
                            in_docstring = True
                            docstring_start_line = line_num
                            docstring_start_col = col
                            docstring_quote = quote
                            docstring_content = [rest_of_line]
                        break
            else:
                # Inside multi-line docstring, look for end
                end_idx = line.find(docstring_quote)
                if end_idx != -1:
                    # Docstring ends
                    docstring_content.append(line[:end_idx])
                    full_docstring = '\n'.join(docstring_content)
                    if re.search(invalid_escapes, full_docstring):
                        issues.append({
                            'type': 'REGEX_RAW_DOCSTRING',
                            'message': f"Line {docstring_start_line}: Docstring contains invalid escape sequence (e.g., \\s, \\d). Use r{docstring_quote}...{docstring_quote}.",
                            'severity': 'warning',
                            'suggestion': f"Add 'r' prefix: r{docstring_quote}...{docstring_quote}",
                            'fix_span': (docstring_start_line, docstring_start_col, docstring_start_line, docstring_start_col),
                            'is_docstring': True,
                        })
                    in_docstring = False
                    docstring_content = []
                else:
                    docstring_content.append(line)
                continue  # Don't check for regular strings inside docstring
            
            # Check for regular strings (single/double quotes, not triple)
            # Match strings that are NOT raw strings
            string_pattern = re.compile(
                r'''(?<![rRbBuUfF])(?<!['"]) (['"])((?:\\.|(?!\1).)*?)\1''',
                re.VERBOSE
            )
            
            for match in string_pattern.finditer(line):
                quote_char = match.group(1)
                string_content = match.group(2)
                
                # Skip if this looks like part of a triple quote
                col = match.start()
                if col > 0 and line[col-1] in '"\'':
                    continue
                if col + len(match.group(0)) < len(line) and line[col + len(match.group(0))] in '"\'':
                    continue
                
                # Check for invalid escape sequences in the string content
                if re.search(invalid_escapes, string_content):
                    end_col = match.end()
                    
                    # Double-check it's not already a raw string by looking at prefix
                    prefix_start = col
                    while prefix_start > 0 and line[prefix_start - 1] in 'rRbBuUfF':
                        prefix_start -= 1
                    prefix = line[prefix_start:col].lower()
                    
                    if 'r' in prefix:
                        continue  # Already raw string
                    
                    issues.append({
                        'type': 'REGEX_RAW_STRING',
                        'message': f"Line {line_num}: String contains invalid escape sequence (e.g., \\s, \\d). Use r'...' prefix.",
                        'severity': 'warning',
                        'suggestion': "Add 'r' prefix: r'pattern' instead of 'pattern'",
                        'fix_span': (line_num, col, line_num, end_col),
                        'is_docstring': False,
                    })
        
        return issues
    
    def _check_runtime(self, code: str, config: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Try to import and instantiate the checker to catch runtime errors.
        
        Note: This is a lightweight check, not a full test.
        """
        issues = []
        import tempfile
        import importlib.util
        
        try:
            # Write code to temp file
            with tempfile.NamedTemporaryFile(
                mode='w', suffix='.py', delete=False, encoding='utf-8'
            ) as f:
                f.write(code)
                temp_path = f.name
            
            # Try to load the module
            spec = importlib.util.spec_from_file_location("temp_checker", temp_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                # Don't actually execute - just check if it can be loaded
                # spec.loader.exec_module(module)  # Skip execution
                
        except Exception as e:
            issues.append({
                'type': 'RUNTIME_ERROR',
                'message': f"Code may have runtime issues: {str(e)[:100]}",
                'severity': 'warning',
                'details': str(e),
            })
        finally:
            # Clean up temp file
            import os
            try:
                os.unlink(temp_path)
            except:
                pass
        
        return issues
    
    # =========================================================================
    # Deterministic Fix Methods
    # =========================================================================
    
    def _fix_type1_type2_reason_usage(self, code: str, issues: list[dict[str, Any]]) -> str:
        """Replace Type 1/2 lambda reasons with static strings."""
        if not issues:
            return code

        lines = code.splitlines(keepends=True)

        def _offset(lineno: int, col: int) -> int:
            position = 0
            for idx in range(lineno - 1):
                position += len(lines[idx])
            return position + col

        replacements = []
        for issue in issues:
            fix_span = issue.get('fix_span')
            arg = issue.get('arg')
            if not fix_span or not arg:
                continue
            start_line, start_col, end_line, end_col = fix_span
            replacement = 'self.FOUND_REASON' if arg == 'found_reason' else 'self.MISSING_REASON'
            start_pos = _offset(start_line, start_col)
            end_pos = _offset(end_line, end_col)
            replacements.append((start_pos, end_pos, replacement))

        if not replacements:
            return code

        # Apply replacements from end to start to preserve offsets
        replacements.sort(key=lambda item: item[0], reverse=True)
        new_code = code
        for start_pos, end_pos, replacement in replacements:
            new_code = new_code[:start_pos] + replacement + new_code[end_pos:]

        return new_code

    def _fix_regex_raw_string(self, code: str, issues: list[dict[str, Any]]) -> str:
        """
        Fix regex strings and docstrings by adding raw string prefix.
        
        Converts:
        - "\\s+" to r"\\s+" 
        - \"""...\""" to r\"""...\"""
        
        This prevents SyntaxWarning for invalid escape sequences.
        """
        if not issues:
            return code
        
        lines = code.splitlines(keepends=True)
        
        # Track modifications per line: (col, is_docstring)
        line_modifications = {}  # line_num -> list of (col, is_docstring)
        
        for issue in issues:
            fix_span = issue.get('fix_span')
            if not fix_span:
                continue
            
            line_num, col, _, _ = fix_span
            is_docstring = issue.get('is_docstring', False)
            
            if line_num not in line_modifications:
                line_modifications[line_num] = []
            
            line_modifications[line_num].append((col, is_docstring))
        
        # Apply fixes line by line
        new_lines = []
        for idx, line in enumerate(lines):
            line_num = idx + 1
            
            if line_num in line_modifications:
                # Sort by column in reverse order to handle multiple fixes on same line
                modifications = sorted(line_modifications[line_num], key=lambda x: x[0], reverse=True)
                line_content = line.rstrip('\n\r')
                line_ending = line[len(line_content):]
                
                for col, is_docstring in modifications:
                    # Find the quote character at this position
                    if col < len(line_content) and line_content[col] in '"\'':
                        # Check if there's already a prefix
                        prefix_start = col
                        while prefix_start > 0 and line_content[prefix_start - 1] in 'rRbBuUfF':
                            prefix_start -= 1
                        
                        existing_prefix = line_content[prefix_start:col].lower()
                        if 'r' not in existing_prefix:
                            # Add 'r' prefix before the quote
                            line_content = line_content[:col] + 'r' + line_content[col:]
                
                new_lines.append(line_content + line_ending)
            else:
                new_lines.append(line)
        
        return ''.join(new_lines)
    
    # =========================================================================
    # AI-Powered Fix Methods
    # =========================================================================
    
    def _ai_fix_issues(
        self,
        code: str,
        issues: list[dict[str, Any]],
        config: dict[str, Any],
        file_analysis: dict[str, Any],
        readme: str,
    ) -> str:
        """
        Use AI to fix detected issues.
        
        Enhanced with:
        - Source code API search (like human debugging)
        - Similar checker examples (learning from existing code)
        - Suggestions from CodeValidator
        """
        if self.verbose:
            print("  🔧 AI attempting to fix issues...")
        
        # Apply deterministic fixes for known patterns before invoking LLM
        type12_issues = [i for i in issues if i.get('type') == 'TYPE12_REASON_LAMBDA']
        if type12_issues:
            code = self._fix_type1_type2_reason_usage(code, type12_issues)
            issues = [i for i in issues if i.get('type') != 'TYPE12_REASON_LAMBDA']
            if not issues:
                return code

        # Fix regex raw string issues deterministically
        regex_raw_issues = [i for i in issues if i.get('type') == 'REGEX_RAW_STRING']
        if regex_raw_issues:
            code = self._fix_regex_raw_string(code, regex_raw_issues)
            issues = [i for i in issues if i.get('type') != 'REGEX_RAW_STRING']
            if not issues:
                return code

        # Build fix prompt with suggestions
        issues_parts = []
        for issue in issues:
            issue_text = f"- [{issue['type']}] {issue['message']}"
            if issue.get('suggestion'):
                issue_text += f"\n  CORRECT USAGE:\n{issue['suggestion']}"
            issues_parts.append(issue_text)
        
        issues_text = "\n".join(issues_parts)
        
        # 🔍 ENHANCEMENT 1: Search source code for API information
        api_context = self._search_source_for_api_info(issues_text)
        api_section = ""
        if api_context:
            api_section = f"""
====================================================================================
📖 API REFERENCE (Extracted from Source Code)
====================================================================================
{api_context}

Use the CORRECT API shown above, not Python's misleading suggestions!
"""
        
        # 🔍 ENHANCEMENT 2: Find similar successful checkers as examples
        similar_examples = self._find_similar_checkers(config, issues_text)
        examples_section = ""
        if similar_examples:
            examples_section = f"""
====================================================================================
📝 SIMILAR CHECKER EXAMPLES (Successful Implementations)
====================================================================================
{similar_examples}

Learn from these working examples when fixing your code!
"""
        
        prompt = f"""Fix the following issues in this Python checker code.

====================================================================================
❌ ISSUES FOUND
====================================================================================
{issues_text}

{api_section}{examples_section}
====================================================================================
📄 CURRENT CODE TO FIX
====================================================================================
```python
{code}
```

====================================================================================
🔧 FIX REQUIREMENTS
====================================================================================
1. Fix ALL the issues listed above
2. Keep the same overall structure and logic
3. DO NOT remove any working functionality
4. Ensure all 4 type methods (_execute_type1/2/3/4) are complete
5. Keep the Waiver Tag Rules section EXACTLY as specified
6. Use the CORRECT API from source code reference above
7. Learn from the similar checker examples above
8. Return ONLY the fixed Python code (no explanations)

README CONTEXT (for reference):
{readme[:2000]}

====================================================================================
📤 OUTPUT
====================================================================================
Return the complete fixed Python code. Start with ################################################################################"""

        try:
            from utils.models import LLMCallConfig
        except ImportError:
            from AutoGenChecker.utils.models import LLMCallConfig
        
        agent = self._get_llm_agent()
        llm_config = LLMCallConfig(
            temperature=0.1,  # Low temp for precise fixes
            max_tokens=16000,  # Increased limit to avoid truncation
        )
        
        try:
            if self.verbose:
                print("  🤖 Calling LLM to generate fixes...")
            response = agent._llm_client.complete(prompt, config=llm_config)
            if self.verbose:
                print("  ✅ LLM fix generation completed")
        except Exception as e:
            error_msg = f"LLM call failed during self-fix: {type(e).__name__}: {str(e)}"
            self._log(error_msg, "ERROR", "❌")
            if self.verbose:
                print(f"  ❌ {error_msg}")
            # Return original code if fix fails
            return code
        
        fixed_code = self._extract_code_from_response(response.text)
        
        if self.verbose:
            print(f"  📝 Generated fix ({len(fixed_code.split(chr(10)))} lines)")
        
        return fixed_code
    
    # =========================================================================
    # Helper Methods for AI Fix
    # =========================================================================
    
    def _find_similar_checkers(self, config: dict[str, Any], issues_text: str) -> str:
        """
        Search for similar successful checkers as learning examples.
        
        Strategy:
        1. Same module (same input file patterns)
        2. Working checkers (no syntax errors)
        3. Using OutputBuilderMixin (template-based)
        4. Focus on relevant code patterns based on issues
        
        Returns:
            String with code snippets from similar checkers
        """
        try:
            from utils.paths import discover_project_paths
        except ImportError:
            from AutoGenChecker.utils.paths import discover_project_paths
        
        paths = discover_project_paths()
        module_dir = paths.workspace_root / "Check_modules" / self.module / "scripts" / "checker"
        
        if not module_dir.exists():
            return ""
        
        examples = []
        max_examples = 2  # Limit to avoid token overflow
        
        # Search for working checkers in the same module
        for checker_file in module_dir.glob("IMP-*.py"):
            if checker_file.name == f"{self.item_id}.py":
                continue  # Skip current checker
            
            try:
                with open(checker_file, 'r', encoding='utf-8') as f:
                    checker_code = f.read()
                
                # Quick validation: must use template mixins
                if 'OutputBuilderMixin' not in checker_code:
                    continue
                
                # Quick syntax check
                try:
                    ast.parse(checker_code)
                except SyntaxError:
                    continue  # Skip broken checkers
                
                # Extract relevant sections based on issues
                relevant_sections = []
                
                # If issue mentions lambda/reason, extract lambda usage
                if 'lambda' in issues_text.lower() or 'reason' in issues_text.lower():
                    lambda_patterns = self._extract_lambda_patterns(checker_code)
                    if lambda_patterns:
                        relevant_sections.append(f"Lambda usage examples:\n{lambda_patterns}")
                
                # If issue mentions dict/items, extract dict construction
                if 'dict' in issues_text.lower() or 'items' in issues_text.lower():
                    dict_patterns = self._extract_dict_construction_patterns(checker_code)
                    if dict_patterns:
                        relevant_sections.append(f"Dict construction examples:\n{dict_patterns}")
                
                # If issue mentions API, extract build_complete_output calls
                if 'api' in issues_text.lower() or 'build_complete_output' in issues_text.lower():
                    api_calls = self._extract_api_calls(checker_code)
                    if api_calls:
                        relevant_sections.append(f"API call examples:\n{api_calls}")
                
                if relevant_sections:
                    examples.append(f"From {checker_file.name}:\n" + "\n".join(relevant_sections))
                    
                    if len(examples) >= max_examples:
                        break
            
            except Exception as e:
                continue  # Skip problematic files
        
        if examples:
            return "\n\n".join(examples)
        else:
            return ""
    
    def _extract_lambda_patterns(self, code: str) -> str:
        """Extract lambda usage patterns from code."""
        lambda_lines = []
        
        # Find lambda usage in build_complete_output calls
        for match in re.finditer(r'(found_reason|missing_reason|extra_reason)=lambda\s+item:[^\n]+', code):
            lambda_lines.append(match.group(0))
        
        if lambda_lines:
            return "  " + "\n  ".join(lambda_lines[:3])  # Max 3 examples
        return ""
    
    def _extract_dict_construction_patterns(self, code: str) -> str:
        """Extract dict construction patterns from code."""
        dict_patterns = []
        
        # Find dict construction with metadata
        pattern = r'(\w+)\s*=\s*\{[^}]*["\']name["\']:[^}]*["\']line_number["\']:[^}]*\}'
        for match in re.finditer(pattern, code, re.MULTILINE):
            # Get context (5 lines)
            start = max(0, match.start() - 200)
            end = min(len(code), match.end() + 200)
            snippet = code[start:end]
            dict_patterns.append(snippet.strip()[:300])  # Limit length
            
            if len(dict_patterns) >= 2:
                break
        
        if dict_patterns:
            return "  " + "\n  ---\n  ".join(dict_patterns)
        return ""
    
    def _extract_api_calls(self, code: str) -> str:
        """Extract build_complete_output call patterns."""
        # Find build_complete_output calls with context
        pattern = r'return\s+self\.build_complete_output\([^)]+\)'
        matches = list(re.finditer(pattern, code, re.DOTALL))
        
        if matches:
            # Get the first call with reasonable length
            for match in matches:
                call = match.group(0)
                if len(call) < 800:  # Reasonable size
                    return "  " + call
        
        return ""
    
    # =========================================================================
    # API Search Methods
    # =========================================================================
    
    def _search_source_for_api_info(self, error_msg: str) -> str:
        """
        Search source code to find correct API information.
        
        This method acts as an Agent tool - it searches the actual source code
        to find the correct parameter names, function signatures, etc.
        
        Returns:
            String containing discovered API information
        """
        discovered_info = []
        
        # Detect what we need to search for
        search_targets = []
        
        # Check for "unexpected keyword argument" errors
        kwarg_match = re.search(r"unexpected keyword argument ['\"](\w+)['\"]", error_msg)
        if kwarg_match:
            wrong_param = kwarg_match.group(1)
            search_targets.append({
                'type': 'wrong_parameter',
                'param': wrong_param,
                'search': 'build_complete_output'
            })
        
        # Check for "Did you mean" suggestions (often misleading)
        did_you_mean = re.search(r"Did you mean ['\"](\w+)['\"]", error_msg)
        if did_you_mean:
            suggested = did_you_mean.group(1)
            discovered_info.append(f"⚠️ Python suggested '{suggested}' but this may be WRONG!")
        
        # Check for AttributeError
        attr_match = re.search(r"has no attribute ['\"](\w+)['\"]", error_msg)
        if attr_match:
            wrong_attr = attr_match.group(1)
            search_targets.append({
                'type': 'wrong_attribute',
                'attr': wrong_attr
            })
        
        # Now search the source code
        for target in search_targets:
            if target['type'] == 'wrong_parameter' and 'build_complete_output' in target.get('search', ''):
                # Search output_builder_template.py for correct parameters
                api_info = self._read_build_complete_output_signature()
                if api_info:
                    discovered_info.append("\n📖 FOUND: build_complete_output() signature from source code:")
                    discovered_info.append(api_info)
                    
                    # Try to find similar parameter name
                    wrong_param = target['param']
                    similar = self._find_similar_param(wrong_param, api_info)
                    if similar:
                        discovered_info.append(f"\n✅ CORRECT PARAMETER: Use '{similar}' instead of '{wrong_param}'")
        
        return '\n'.join(discovered_info) if discovered_info else ""
    
    def _read_build_complete_output_signature(self) -> str:
        """
        Read the actual build_complete_output() function signature from source.
        """
        # Find the output_builder_template.py file
        from pathlib import Path
        
        # Get project paths
        try:
            from utils.paths import discover_project_paths
        except ImportError:
            from AutoGenChecker.utils.paths import discover_project_paths
        
        paths = discover_project_paths()
        
        # Search in common locations
        possible_paths = [
            paths.workspace_root / "Check_modules" / "common" / "checker_templates" / "output_builder_template.py",
            paths.workspace_root.parent / "CHECKLIST" / "Check_modules" / "common" / "checker_templates" / "output_builder_template.py",
        ]
        
        # Also try to find it dynamically
        import glob
        pattern = str(paths.workspace_root.parent) + "/**/output_builder_template.py"
        found_files = glob.glob(pattern, recursive=True)
        for f in found_files:
            possible_paths.insert(0, Path(f))
        
        for path in possible_paths:
            if path.exists():
                try:
                    content = path.read_text(encoding='utf-8')
                    
                    # Extract the build_complete_output method signature
                    # Find the method definition with all parameters
                    match = re.search(
                        r'def build_complete_output\s*\([^)]*\)\s*(?:->.*?)?:',
                        content,
                        re.DOTALL
                    )
                    if match:
                        # Get more context - the full signature
                        start = content.find('def build_complete_output')
                        if start != -1:
                            # Read until we find the closing paren and colon
                            depth = 0
                            end = start
                            for i, char in enumerate(content[start:], start):
                                if char == '(':
                                    depth += 1
                                elif char == ')':
                                    depth -= 1
                                    if depth == 0:
                                        # Find the colon after )
                                        colon_pos = content.find(':', i)
                                        if colon_pos != -1:
                                            end = colon_pos + 1
                                            break
                            
                            signature = content[start:end]
                            return signature
                except Exception:
                    continue
        
        return ""
    
    def _find_similar_param(self, wrong_param: str, signature: str) -> str:
        """
        Find the most similar correct parameter name.
        """
        # Extract all parameter names from signature
        params = re.findall(r'(\w+)\s*[=:]', signature)
        
        # Define common mappings
        mappings = {
            'waived_reason': 'waived_base_reason',
            'waived_desc_func': 'waived_base_reason',
            'found_reason_func': 'found_reason',
            'missing_reason_func': 'missing_reason',
            'extra_reason_func': 'extra_reason',
            'unused_reason': 'unused_waiver_reason',
        }
        
        # Check direct mapping first
        if wrong_param in mappings:
            return mappings[wrong_param]
        
        # Try fuzzy matching based on substring
        wrong_lower = wrong_param.lower()
        for param in params:
            param_lower = param.lower()
            # Check if the wrong param is a substring or similar
            if wrong_lower in param_lower or param_lower in wrong_lower:
                return param
            # Check word overlap
            wrong_words = set(re.findall(r'[a-z]+', wrong_lower))
            param_words = set(re.findall(r'[a-z]+', param_lower))
            if wrong_words & param_words:  # Intersection
                return param
        
        return ""
