"""
Testing Mixin for IntelligentCheckerAgent.

This mixin provides testing and test-related fix capabilities.

Methods included:
- _ai_fix_test_failure: AI-powered fix based on test failure
- _generate_test_config: Generate test configuration for specific types
- _extract_patterns_from_readme: Extract pattern items from README
- _extract_waivers_from_readme: Extract waiver items from README
- _extract_waive_items_from_readme_variant: Extract waive items for variant types
"""

from typing import Any
import re


class TestingMixin:
    """Mixin providing testing and test fix capabilities for generated code."""
    
    # =========================================================================
    # Test Fix Methods
    # =========================================================================
    
    def _ai_fix_test_failure(
        self,
        code: str,
        test_name: str,
        test_output: str,
        test_stderr: str,
        exit_code: int,
        user_hint: str = "",
        validation_issues: list = None,
        enhanced_context: bool = False,
    ) -> str:
        """
        Use AI to fix code based on test failure.
        
        Enhanced with Agent-style search capability:
        - If error mentions "unexpected keyword argument", search source code
        - Provide discovered API info to AI for accurate fixes
        
        Args:
            enhanced_context: If True, inject additional context from README Output 
                             Descriptions section for better fix quality (Quick Fix mode)
        """
        # ==========================================================================
        # AGENT SEARCH PHASE: Search source code for API information
        # ==========================================================================
        error_text = f"{test_output}\n{test_stderr}"
        
        agent_discovered_info = ""
        if "unexpected keyword argument" in error_text or "has no attribute" in error_text:
            print("   🔍 Searching source code for correct API information...")
            agent_discovered_info = self._search_source_for_api_info(error_text)
            if agent_discovered_info:
                print("   ✅ Found relevant API information from source code")
        
        # ==========================================================================
        # ENHANCED CONTEXT: Load README Output Descriptions if in Quick Fix mode
        # ==========================================================================
        readme_output_section = ""
        if enhanced_context:
            readme_output_section = self._extract_readme_output_descriptions()
            if readme_output_section:
                print("   ✅ Loaded README Output Descriptions")
        
        # ==========================================================================
        # Get API reference for build_complete_output
        # ==========================================================================
        try:
            from prompt_templates.api_v2_reference import TEMPLATE_V2_INSTRUCTIONS
        except ImportError:
            from AutoGenChecker.prompt_templates.api_v2_reference import TEMPLATE_V2_INSTRUCTIONS
        
        # Extract API signature section
        api_section = ""
        if "## 4. OUTPUT BUILDING" in TEMPLATE_V2_INSTRUCTIONS:
            start = TEMPLATE_V2_INSTRUCTIONS.find("## 4. OUTPUT BUILDING")
            end = TEMPLATE_V2_INSTRUCTIONS.find("## 5.", start)
            if end > start:
                api_section = TEMPLATE_V2_INSTRUCTIONS[start:end]
        
        # Build validation issues section
        validation_section = ""
        if validation_issues:
            validation_section = "\n\n====================================================================================\n"
            validation_section += "⚠️ PRE-VALIDATION DETECTED ISSUES:\n"
            validation_section += "====================================================================================\n"
            for issue in validation_issues[:5]:  # Show first 5
                validation_section += f"\n[{issue['id']}] {issue['category']}: {issue.get('severity', 'ERROR')}\n"
                validation_section += f"  Problem: {issue.get('explanation', 'Issue detected')}\n"
                if 'correct_usage' in issue:
                    validation_section += f"  Fix: Use correct pattern from known_issues.yaml\n"
        
        # ==========================================================================
        # Build Agent-discovered section
        # ==========================================================================
        agent_section = ""
        if agent_discovered_info:
            agent_section = "\n\n====================================================================================\n"
            agent_section += "🔍 AGENT DISCOVERED (from searching actual source code):\n"
            agent_section += "====================================================================================\n"
            agent_section += agent_discovered_info
            agent_section += "\n\n⚠️ TRUST THE AGENT DISCOVERY ABOVE! It comes from actual source code.\n"
        
        # Build fix prompt
        hint_section = f"\n\nUser Hint: {user_hint}" if user_hint else ""
        
        # ==========================================================================
        # Build README output descriptions section for enhanced context
        # ==========================================================================
        readme_section = ""
        if readme_output_section:
            readme_section = f"""
====================================================================================
📋 README OUTPUT DESCRIPTIONS (Use these exact strings in your code!):
====================================================================================
{readme_output_section}
"""
        
        prompt = f"""You are fixing a Python checker that failed during testing.

Test Name: {test_name}
Exit Code: {exit_code}

Test Output (stdout):
{test_output[:2000] if test_output else "(empty)"}

Error Messages (stderr):
{test_stderr[:3000] if test_stderr else "(empty)"}
{agent_section}
{validation_section}
{readme_section}
{hint_section}

Current Code:
```python
{code}
```

====================================================================================
⚠️ API REFERENCE (for build_complete_output errors):
====================================================================================
{api_section}

Task: Fix the code to resolve the test failure.

====================================================================================
⚠️ COMMON PARAMETER NAME MISTAKES (CHECK THIS FIRST!):
====================================================================================

If error says "unexpected keyword argument", use this mapping:

❌ WRONG PARAMETER          →  ✅ CORRECT PARAMETER
-----------------------------------------------------------------
waived_reason               →  waived_base_reason
waived_desc_func            →  waived_base_reason (use lambda)
found_reason_func           →  found_reason (use lambda)
missing_reason_func         →  missing_reason (use lambda)
extra_reason_func           →  extra_reason (use lambda)
item_desc                   →  (remove - doesn't exist)

Example fix:
```python
# ❌ WRONG:
waived_reason=lambda item: f"..."

# ✅ CORRECT:
waived_base_reason=lambda item: f"..."
```

⚠️ DO NOT follow Python's suggestion "Did you mean 'waived_desc'?" - that's wrong!
   waived_desc is for GROUP description (static string)
   waived_base_reason is for ITEM reason (can use lambda)

====================================================================================

⚠️ NON-EXISTENT METHODS (DO NOT USE!):
====================================================================================
❌ self.log()        - BaseChecker has NO log() method! Remove these calls.
❌ self.logger       - BaseChecker has NO logger attribute!
❌ self.debug()      - BaseChecker has NO debug() method!

If you need debugging, use print() temporarily or just remove the log statements.
The framework handles result reporting automatically through build_complete_output().

====================================================================================

Other common issues:
1. Type errors (list vs Path, str vs dict)
2. Missing imports
3. Logic errors in parsing or checking

⚠️ CRITICAL: ALWAYS check the parameter mapping table above FIRST!

Return ONLY the fixed Python code, no explanations."""

        try:
            from utils.models import LLMCallConfig
        except ImportError:
            from AutoGenChecker.utils.models import LLMCallConfig
        
        agent = self._get_llm_agent()
        llm_config = LLMCallConfig(
            temperature=0.2,
            max_tokens=16000,  # Increased limit to avoid truncation
        )
        
        try:
            response = agent._llm_client.complete(prompt, config=llm_config)
            fixed_code = response.text.strip()
            
            # Extract code from markdown if wrapped
            if '```python' in fixed_code:
                match = re.search(r'```python\n(.*?)\n```', fixed_code, re.DOTALL)
                if match:
                    fixed_code = match.group(1)
            elif '```' in fixed_code:
                match = re.search(r'```\n(.*?)\n```', fixed_code, re.DOTALL)
                if match:
                    fixed_code = match.group(1)
            
            return fixed_code
        except Exception as e:
            print(f"⚠️  AI fix failed: {e}")
            return code
    
    # =========================================================================
    # Test Configuration Methods
    # =========================================================================
    
    def _generate_test_config(
        self,
        test_id: str,
        config: dict[str, Any],
        readme: str,
    ) -> dict[str, Any]:
        """
        Generate test configuration for specific type.
        
        Extracts patterns from README Type examples.
        """
        description = config.get('description', 'TBD')
        input_files = config.get('input_files', [])
        
        if test_id == 'type1_na':
            # Type 1: value=N/A, waivers=N/A
            return {
                'description': description,
                'requirements': {
                    'value': 'N/A',
                    'pattern_items': []
                },
                'input_files': input_files,
                'waivers': {
                    'value': 'N/A',
                    'waive_items': []
                }
            }
        
        elif test_id == 'type1_0':
            # Type 1 with waivers=0: Extract from README Type 1 Variant section
            waive_items_str = self._extract_waive_items_from_readme_variant(readme, 'Type 1 Variant')
            return {
                'description': description,
                'requirements': {
                    'value': 'N/A',  # Type 1 MUST have requirements.value=N/A
                    'pattern_items': []
                },
                'input_files': input_files,
                'waivers': {
                    'value': 0,  # waivers=0 means "forced PASS mode"
                    'waive_items': waive_items_str or [
                        'Violations are acceptable for this check'  # Fallback
                    ]
                }
            }
        
        elif test_id == 'type2_na':
            # Type 2: Extract pattern_items from README Type 2 section
            patterns = self._extract_patterns_from_readme(readme, 'Type 2')
            value = len(patterns) if patterns else 2
            return {
                'description': description,
                'requirements': {
                    'value': value,
                    'pattern_items': patterns or ["pattern1", "pattern2"]
                },
                'input_files': input_files,
                'waivers': {
                    'value': 'N/A',
                    'waive_items': []
                }
            }
        
        elif test_id == 'type2_0':
            # Type 2 with waivers=0: Extract from README Type 2 Variant section
            patterns = self._extract_patterns_from_readme(readme, 'Type 2')
            waive_items_str = self._extract_waive_items_from_readme_variant(readme, 'Type 2 Variant')
            value = len(patterns) if patterns else 2
            return {
                'description': description,
                'requirements': {
                    'value': value,
                    'pattern_items': patterns or ["pattern1", "pattern2"]
                },
                'input_files': input_files,
                'waivers': {
                    'value': 0,  # waivers=0 means "forced PASS mode"
                    'waive_items': waive_items_str or [
                        'Violations are acceptable for this check'
                    ]
                }
            }
        
        elif test_id == 'type3':
            # Type 3: Extract from README Type 3 section
            patterns = self._extract_patterns_from_readme(readme, 'Type 3')
            waivers = self._extract_waivers_from_readme(readme, 'Type 3')
            value = len(patterns) if patterns else 1
            return {
                'description': description,
                'requirements': {
                    'value': value,
                    'pattern_items': patterns or ["pattern1"]
                },
                'input_files': input_files,
                'waivers': {
                    'value': len(waivers) if waivers else 2,
                    'waive_items': waivers or [
                        {'name': 'item1', 'reason': 'Test waiver 1'},
                        {'name': 'item2', 'reason': 'Test waiver 2'}
                    ]
                }
            }
        
        elif test_id == 'type4':
            # Type 4: Boolean with waivers
            waivers = self._extract_waivers_from_readme(readme, 'Type 4')
            return {
                'description': description,
                'requirements': {
                    'value': 'N/A',
                    'pattern_items': []
                },
                'input_files': input_files,
                'waivers': {
                    'value': len(waivers) if waivers else 1,
                    'waive_items': waivers or [
                        {'name': 'item1', 'reason': 'Test waiver'}
                    ]
                }
            }
        
        return {}
    
    # =========================================================================
    # README Extraction Helpers
    # =========================================================================
    
    def _extract_patterns_from_readme(self, readme: str, type_section: str) -> list[str]:
        """Extract pattern_items from README Type section."""
        # Find Type section
        pattern = rf'## {type_section}:.*?```yaml.*?pattern_items:(.*?)input_files:'
        match = re.search(pattern, readme, re.DOTALL)
        
        if match:
            patterns_text = match.group(1)
            # Extract list items
            pattern_lines = re.findall(r'- "(.*?)"', patterns_text)
            return pattern_lines[:3]  # Limit to 3 patterns
        
        return []
    
    def _extract_waivers_from_readme(self, readme: str, type_section: str) -> list[dict]:
        """Extract waive_items from README Type section (Type 3/4).
        
        Supports multiple key names: name, error_code, cell_name, instance_name, etc.
        The first non-reason key found will be used as 'name' in the output dict.
        """
        # Find Type section waive_items
        pattern = rf'## {type_section}:.*?waive_items:(.*?)```'
        match = re.search(pattern, readme, re.DOTALL)
        
        if match:
            waivers_text = match.group(1)
            # Extract waiver entries - support multiple key names
            waiver_entries = []
            
            # Common key names used in waive_items
            # Priority: error_code > name > cell_name > instance_name > pattern
            name_key_patterns = [
                (r'error_code:\s*"(.*?)"', 'error_code'),
                (r'name:\s*"(.*?)"', 'name'),
                (r'cell_name:\s*"(.*?)"', 'cell_name'),
                (r'instance_name:\s*"(.*?)"', 'instance_name'),
                (r'pattern:\s*"(.*?)"', 'pattern'),
            ]
            
            # Try each key pattern to find matches
            name_matches = []
            used_key = 'name'
            for key_pattern, key_name in name_key_patterns:
                matches = re.findall(key_pattern, waivers_text)
                if matches:
                    name_matches = matches
                    used_key = key_name
                    break
            
            reason_matches = re.findall(r'reason:\s*"(.*?)"', waivers_text)
            
            # Build entries using the detected key name
            for i, name in enumerate(name_matches):
                reason = reason_matches[i] if i < len(reason_matches) else ''
                waiver_entries.append({used_key: name, 'reason': reason})
            
            return waiver_entries[:3]  # Limit to 3 waivers
        
        return []
    
    def _extract_waive_items_from_readme_variant(self, readme: str, variant_section: str) -> list[str]:
        """Extract waive_items string list from README Type Variant section (Type 1/2 with waiver=0)."""
        # Find Type Variant section waive_items (simple string list, not dict)
        # Pattern: ### Type X Variant... waive_items: ... - "explanation text"
        pattern = rf'### {variant_section}.*?waive_items:\s*#[^\n]*\n\s*-\s*"([^"]+)"'
        match = re.search(pattern, readme, re.DOTALL)
        
        if match:
            waive_text = match.group(1)
            # Return single explanation string as list
            return [waive_text]
        
        return []
