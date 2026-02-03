"""
Interactive Fix Mixin for IntelligentCheckerAgent.

This mixin provides Level 2 interactive fix capabilities when
automatic fixes fail after max_fix_attempts.

Methods included:
- _interactive_fix: Main entry point for interactive fix mode
- _ai_fix_with_hint: AI-powered fix with user-provided hints
"""

from typing import Any


class InteractiveFixMixin:
    """Mixin providing interactive fix capabilities for code with issues."""
    
    # =========================================================================
    # Interactive Fix Methods
    # =========================================================================
    
    def _interactive_fix(
        self,
        code: str,
        config: dict[str, Any],
        file_analysis: dict[str, Any],
        readme: str,
        check_results: dict[str, Any],
    ) -> str:
        """
        Level 2: Interactive fix with user participation.
        
        Called when auto-fix fails after max_fix_attempts.
        """
        print("\n" + "="*80)
        print("⚠️  AI Auto-Fix Failed - Interactive Mode")
        print("="*80)
        print(f"\nAttempted {check_results['fix_attempts']} automatic fix(es)")
        print(f"Remaining issues: {len(check_results['issues'])}")
        print("\nIssue Details:")
        for i, issue in enumerate(check_results['issues'], 1):
            print(f"  {i}. [{issue['type']}] {issue['message']}")
            if 'details' in issue:
                print(f"     Details: {issue['details'][:100]}...")
        
        while True:
            print("\n" + "-"*60)
            print("Options:")
            print("  [1] Let AI continue trying with additional hints")
            print("  [2] Save current version and fix manually later")
            print("  [3] Abort generation")
            print("  Or type a hint/instruction for the AI")
            print("-"*60)
            
            try:
                user_input = input("\nYour choice or hint: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n⚠️ Input cancelled, saving current version...")
                return code
            
            if user_input == '1':
                # Continue with generic prompt
                code = self._ai_fix_with_hint(
                    code, check_results['issues'], config, file_analysis, readme,
                    hint="Please carefully review and fix all issues. Pay special attention to the error messages."
                )
                # Re-check
                new_issues = self._run_all_checks(code, config)
                if not new_issues:
                    print("\n✅ All issues fixed!")
                    return code
                check_results['issues'] = new_issues
                print(f"\n⚠️ Still have {len(new_issues)} issue(s)")
                
            elif user_input == '2':
                print("\n📁 Saving current version...")
                return code
                
            elif user_input == '3':
                print("\n❌ Generation aborted.")
                raise KeyboardInterrupt("User aborted generation")
                
            else:
                # User provided a hint
                code = self._ai_fix_with_hint(
                    code, check_results['issues'], config, file_analysis, readme,
                    hint=user_input
                )
                # Re-check
                new_issues = self._run_all_checks(code, config)
                if not new_issues:
                    print("\n✅ All issues fixed!")
                    return code
                check_results['issues'] = new_issues
                print(f"\n⚠️ Still have {len(new_issues)} issue(s)")
        
        return code
    
    def _ai_fix_with_hint(
        self,
        code: str,
        issues: list[dict[str, Any]],
        config: dict[str, Any],
        file_analysis: dict[str, Any],
        readme: str,
        hint: str,
    ) -> str:
        """Fix code with user-provided hint."""
        print(f"\n🔍 Step 1: Analyzing your hint...")
        print(f"   Hint: '{hint}'")
        
        issues_text = "\n".join([
            f"- [{issue['type']}] {issue['message']}"
            for issue in issues
        ])
        
        print(f"\n📝 Step 2: Building fix instructions...")
        if issues:
            print(f"   - {len(issues)} issue(s) to address")
        print(f"   - User guidance: {hint[:60]}..." if len(hint) > 60 else f"   - User guidance: {hint}")
        
        prompt = f"""Fix the following issues in this Python checker code.

ISSUES FOUND:
{issues_text}

USER HINT:
{hint}

CURRENT CODE:
```python
{code}
```

REQUIREMENTS:
1. Fix ALL the issues listed above
2. Follow the user's hint carefully
3. Keep the same overall structure and logic
4. Return ONLY the fixed Python code (no explanations)

OUTPUT:
Return the complete fixed Python code. Start with ################################################################################"""

        try:
            from utils.models import LLMCallConfig
        except ImportError:
            from AutoGenChecker.utils.models import LLMCallConfig
        
        agent = self._get_llm_agent()
        llm_config = LLMCallConfig(
            temperature=0.1,
            max_tokens=16000,  # Increased limit to avoid truncation
        )
        
        print(f"\n🤖 Step 3: Calling AI to fix code...")
        print(f"   Model: {self.llm_provider}/{self.llm_model or 'default'}")
        print(f"   (This may take 30-60 seconds for complex fixes)")
        
        response = agent._llm_client.complete(prompt, config=llm_config)
        
        print(f"\n✅ Step 4: Extracting fixed code...")
        fixed_code = self._extract_code_from_response(response.text)
        print(f"   Generated: {len(fixed_code.split(chr(10)))} lines of code")
        
        return fixed_code
