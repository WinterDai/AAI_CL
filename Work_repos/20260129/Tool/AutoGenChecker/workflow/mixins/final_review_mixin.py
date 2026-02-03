"""
Final Review Mixin for IntelligentCheckerAgent.

This mixin provides Step 8 final review functionality,
allowing users to test, modify, and finalize the generated checker.

Combines functionality from:
- Interactive fix (Step 6)
- Output refinement (Step 7)
- Testing and finalization

Methods included:
- _final_review: Main entry point for final review workflow
- _run_test: Execute checker and display output
- _show_review_summary: Display current status
- _ai_modify_code: AI-powered code modification (bugs or logic)
- _ai_adjust_output: AI-powered output format adjustment
- _handle_finalization: Process backup files and mark complete
"""

from typing import Any
import re
import shutil
import os
from pathlib import Path


class FinalReviewMixin:
    """Mixin providing final review and testing capabilities for generated code."""
    
    # =========================================================================
    # Final Review Methods (Step 8)
    # =========================================================================
    
    def _final_review(
        self,
        code: str,
        config: dict[str, Any],
        file_analysis: dict[str, Any],
        readme: str,
        test_results: dict[str, Any] = None,
    ) -> str:
        """
        Step 8: Final Review - Test, modify, and finalize the checker.
        
        This step provides a unified interface for:
        - Running tests and viewing output
        - Fixing bugs or modifying logic
        - Adjusting output format/descriptions
        - Viewing full code
        - Resetting to skeleton
        - Finalizing and handling backups
        
        Args:
            code: Current checker implementation
            config: Configuration dictionary
            file_analysis: File analysis results
            readme: Generated README content
            test_results: Optional test results from Step 7
            
        Returns:
            Final code after user modifications
        """
        # Show current status
        self._show_review_summary(code, config, test_results)
        
        while True:
            print("\n" + "-"*80)
            print("Options:")
            print("  [T] Test Again - Re-run checker and show output")
            print("  [M] Modify Code - Fix bugs or change logic")
            print("  [O] Adjust Output - Change format/descriptions only")
            print("  [V] View Code - Show full checker implementation")
            print("  [R] Reset - Restore to skeleton template")
            print("  [F] Finalize - Mark complete & handle backups")
            print("  [Q] Quit - Save and exit (keep backups)")
            print("-"*80)
            
            try:
                user_choice = input("\nYour choice: ").strip().upper()
            except (EOFError, KeyboardInterrupt):
                print("\n💾 Saving and exiting...")
                self._save_code_to_file(code, config)
                return code
            
            if user_choice == 'T':
                # Go back to Step 7: Interactive Testing
                print("\n🧪 Returning to Step 7: Interactive Testing...")
                print("="*80)
                self._interactive_testing(config, readme, code)
                # After Step 7 returns, continue in Step 8 loop
                print("\n" + "="*80)
                print("🔍 Back to Step 8: Final Review")
                print("="*80)
                self._show_review_summary(code, config, test_results)
                
            elif user_choice == 'M':
                # Modify code (fix bugs or change logic)
                print("\n" + "="*60)
                print("🔧 Modify Code")
                print("="*60)
                print("\nDescribe the code changes you need:")
                print("\nExamples:")
                print("  • 'Fix the regex pattern on line 45 to handle spaces'")
                print("  • 'Change _parse_input_files to also extract clock names'")
                print("  • 'Add error handling for missing configuration keys'")
                print("  • 'The waive_dict iteration is wrong, fix it'")
                print("\n💡 Be specific about what needs to change")
                print("-"*60)
                
                try:
                    modification_request = input("\n🔧 Your modification: ").strip()
                except (EOFError, KeyboardInterrupt):
                    print("\n⏭️  Modification cancelled.")
                    continue
                
                if not modification_request:
                    print("⚠️  Empty request, please try again.")
                    continue
                
                print(f"\n🤖 AI is modifying code...")
                modified_code = self._ai_modify_code(
                    code=code,
                    modification_request=modification_request,
                    config=config,
                    file_analysis=file_analysis,
                    readme=readme,
                )
                
                # Show diff and confirm
                self._show_modification_summary(code, modified_code)
                
                try:
                    confirm = input("\nAccept changes? [Y/n]: ").strip().upper()
                except (EOFError, KeyboardInterrupt):
                    confirm = 'N'
                
                if confirm in ['', 'Y', 'YES']:
                    code = modified_code
                    self._save_code_to_file(code, config)
                    print("💾 Changes saved!")
                else:
                    print("❌ Changes discarded.")
                    
            elif user_choice == 'O':
                # Adjust output format only
                print("\n" + "="*60)
                print("🎨 Adjust Output Format")
                print("="*60)
                print("\nDescribe the output changes you want:")
                print("\nExamples:")
                print("  • 'Change INFO01 format from [view]: message to view | message'")
                print("  • 'Modify FOUND_DESC to say \"All checks passed\"'")
                print("  • 'Add line numbers to each ERROR01 output'")
                print("  • 'Format numbers with commas (1000 → 1,000)'")
                print("\n💡 Focus on display format, not parsing logic")
                print("-"*60)
                
                try:
                    output_request = input("\n🎨 Your output changes: ").strip()
                except (EOFError, KeyboardInterrupt):
                    print("\n⏭️  Adjustment cancelled.")
                    continue
                
                if not output_request:
                    print("⚠️  Empty request, please try again.")
                    continue
                
                print(f"\n🤖 AI is adjusting output format...")
                modified_code = self._ai_adjust_output(
                    code=code,
                    output_request=output_request,
                    config=config,
                    file_analysis=file_analysis,
                    readme=readme,
                )
                
                # Show diff and confirm
                print("\n✅ Output format adjusted!")
                self._show_modification_summary(code, modified_code)
                
                try:
                    confirm = input("\nAccept changes? [Y/n]: ").strip().upper()
                except (EOFError, KeyboardInterrupt):
                    confirm = 'N'
                
                if confirm in ['', 'Y', 'YES']:
                    code = modified_code
                    self._save_code_to_file(code, config)
                    print("💾 Changes saved!")
                else:
                    print("❌ Changes discarded.")
                    
            elif user_choice == 'V':
                # View full code
                print("\n" + "="*80)
                print("📄 Full Checker Implementation")
                print("="*80)
                print(code)
                print("="*80)
                
            elif user_choice == 'R':
                # Reset to template - with submenu
                print("\n🔄 Reset to Template")
                print("="*60)
                print("\nWhat would you like to reset?")
                print("  [1] Code only - Restore skeleton template")
                print("  [2] README only - Restore TODO template")
                print("  [3] Both - Reset code and README")
                print("  [C] Cancel")
                print("-"*60)
                
                try:
                    reset_choice = input("\nYour choice [1/2/3/C]: ").strip().upper()
                except (EOFError, KeyboardInterrupt):
                    print("\n❌ Reset cancelled.")
                    continue
                
                if reset_choice == 'C' or not reset_choice:
                    print("❌ Reset cancelled.")
                    continue
                
                # Determine what to reset
                reset_code = reset_choice in ['1', '3']
                reset_readme = reset_choice in ['2', '3']
                
                if not (reset_code or reset_readme):
                    print("❌ Invalid choice.")
                    continue
                
                # Get paths
                try:
                    from utils.paths import discover_project_paths
                except ImportError:
                    from AutoGenChecker.utils.paths import discover_project_paths
                
                paths = discover_project_paths()
                
                # Prepare file paths
                files_to_reset = []
                if reset_code:
                    code_file = paths.workspace_root / "Check_modules" / self.module / "scripts" / "checker" / f"{self.item_id}.py"
                    code_backup = code_file.parent / f"{self.item_id}.py.backup"
                    if code_backup.exists():
                        files_to_reset.append(("Code", code_file, code_backup))
                    else:
                        print("⚠️  No code backup found.")
                        
                if reset_readme:
                    readme_file = paths.workspace_root / "Check_modules" / self.module / "scripts" / "doc" / f"{self.item_id}_README.md"
                    readme_backup = readme_file.parent / f"{self.item_id}_README.md.backup"
                    if readme_backup.exists():
                        files_to_reset.append(("README", readme_file, readme_backup))
                    else:
                        print("⚠️  No README backup found.")
                
                if not files_to_reset:
                    print("❌ No backups found. Cannot restore templates.")
                    print("💡 Tip: Backups are created before AI implementation.")
                    continue
                
                # Show what will be reset
                print(f"\n⚠️  Will restore {len(files_to_reset)} file(s) to template:")
                for name, _, backup in files_to_reset:
                    print(f"   • {name}: {backup.name}")
                
                try:
                    confirm = input("\nContinue? [Y/N]: ").strip().upper()
                    if confirm != 'Y':
                        print("❌ Reset cancelled.")
                        continue
                    
                    # Perform restoration
                    for name, target_file, backup_file in files_to_reset:
                        with open(backup_file, 'r', encoding='utf-8') as f:
                            template_content = f.read()
                        
                        with open(target_file, 'w', encoding='utf-8') as f:
                            f.write(template_content)
                        
                        print(f"✅ {name} restored!")
                        
                        # Update in-memory content
                        if name == "Code":
                            code = template_content
                        elif name == "README":
                            readme = template_content
                    
                    print(f"\n✅ Reset complete! Restored {len(files_to_reset)} file(s).")
                    
                    proceed = input("\nContinue with template(s)? [Y/N]: ").strip().upper()
                    if proceed != 'Y':
                        print("💡 You can continue editing or make other changes.")
                        continue
                
                except Exception as e:
                    print(f"❌ Failed to reset: {e}")
                    continue
                
                # If user chose to proceed, exit to regenerate
                if reset_code:
                    return code
                
            elif user_choice == 'F':
                # Finalize and handle backups
                code = self._handle_finalization(code, config)
                return code
                
            elif user_choice == 'Q':
                # Quit without finalization
                print("\n💾 Saving and exiting...")
                self._save_code_to_file(code, config)
                print("💡 Backups preserved. Run --resume-from-step 8 to continue later.")
                return code
                
            else:
                print(f"⚠️  Invalid choice: {user_choice}")
    
    def _show_review_summary(self, code: str, config: dict[str, Any], test_results: dict[str, Any] = None) -> None:
        """Show current status summary."""
        print("\n" + "-"*80)
        print("📋 Current Status")
        print("-"*80)
        
        # Show test results if available
        if test_results:
            status = "✅ PASSED" if test_results.get('passed') else "❌ FAILED"
            print(f"Last Test: {status}")
            if test_results.get('output'):
                print(f"Exit Code: {test_results.get('exit_code', 'N/A')}")
        
        # Extract and show output descriptions
        desc_pattern = r'(FOUND_DESC|MISSING_DESC|WAIVED_DESC)\s*=\s*["\'](.+?)["\']'
        descriptions = re.findall(desc_pattern, code)
        
        if descriptions:
            print("\n🏷️  Output Descriptions:")
            for desc_name, desc_value in descriptions:
                print(f"  • {desc_name}: {desc_value}")
        
        # Show checker type
        if 'detect_checker_type()' in code:
            print("\n📊 Uses auto-detection for Type 1/2/3/4")
        
        print("-"*80)
    
    def _run_test(self, code: str, config: dict[str, Any]) -> dict[str, Any]:
        """
        Run the checker and capture output.
        
        Returns:
            dict with keys: passed, exit_code, output, errors
        """
        try:
            from utils.paths import discover_project_paths
        except ImportError:
            from AutoGenChecker.utils.paths import discover_project_paths
        
        paths = discover_project_paths()
        checker_file = paths.workspace_root / "Check_modules" / self.module / "scripts" / "checker" / f"{self.item_id}.py"
        
        # Run the checker
        import subprocess
        try:
            result = subprocess.run(
                ['python', str(checker_file)],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=str(checker_file.parent)
            )
            
            return {
                'passed': result.returncode == 0,
                'exit_code': result.returncode,
                'output': result.stdout,
                'errors': result.stderr,
            }
        except subprocess.TimeoutExpired:
            return {
                'passed': False,
                'exit_code': -1,
                'output': '',
                'errors': 'Test timeout (30s)',
            }
        except Exception as e:
            return {
                'passed': False,
                'exit_code': -1,
                'output': '',
                'errors': str(e),
            }
    
    def _show_test_results(self, test_results: dict[str, Any]) -> None:
        """Display test results."""
        print("\n" + "="*80)
        print("🧪 Test Results")
        print("="*80)
        
        if test_results['passed']:
            print("✅ Test PASSED")
        else:
            print("❌ Test FAILED")
        
        print(f"\nExit Code: {test_results['exit_code']}")
        
        if test_results['output']:
            print("\n📤 Output:")
            print("-"*80)
            print(test_results['output'])
            print("-"*80)
        
        if test_results['errors']:
            print("\n⚠️  Errors:")
            print("-"*80)
            print(test_results['errors'])
            print("-"*80)
    
    def _show_modification_summary(self, old_code: str, new_code: str) -> None:
        """Show summary of changes between old and new code."""
        old_lines = old_code.split('\n')
        new_lines = new_code.split('\n')
        
        # Count changed lines
        changed_lines = 0
        for i, (old, new) in enumerate(zip(old_lines, new_lines)):
            if old != new:
                changed_lines += 1
        
        print(f"\n📊 Changes: {changed_lines} lines modified")
        
        # Show first few changed lines
        print("\n🔍 Preview of changes:")
        shown = 0
        for i, (old, new) in enumerate(zip(old_lines, new_lines)):
            if old != new and shown < 5:
                print(f"  Line {i+1}:")
                print(f"    - {old[:70]}...")
                print(f"    + {new[:70]}...")
                shown += 1
        
        if changed_lines > 5:
            print(f"  ... and {changed_lines - 5} more changes")
    
    def _ai_modify_code(
        self,
        code: str,
        modification_request: str,
        config: dict[str, Any],
        file_analysis: dict[str, Any],
        readme: str,
    ) -> str:
        """
        AI modifies code based on user request (for bugs or logic changes).
        
        Uses smart retry with dynamic token allocation to avoid truncation.
        """
        # Calculate required tokens based on code size
        code_lines = code.count('\n') + 1
        max_tokens = self._calculate_required_tokens(code, is_modification=True)
        
        print(f"📊 Code modification setup:")
        print(f"    Current code: {code_lines} lines")
        print(f"    Allocated tokens: {max_tokens:,}")
        
        prompt = f"""You are fixing/modifying a Python checker implementation.

**User's Modification Request:**
{modification_request}

**Current Code:**
```python
{code}
```

**README Reference:**
{readme[:2000]}...

**Task:**
1. Understand the user's request
2. Make the necessary code changes
3. Ensure the code remains syntactically correct
4. Preserve the overall structure and template usage
5. Return ONLY the complete modified code (ALL {code_lines} lines or more)

**CRITICAL: Return the COMPLETE file - do NOT truncate!**

**Output Format:**
Return the complete modified Python code without any explanations or markdown.
"""
        
        try:
            from utils.models import LLMCallConfig
        except ImportError:
            from AutoGenChecker.utils.models import LLMCallConfig
        
        agent = self._get_llm_agent()
        
        # Smart retry with increasing tokens
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                if attempt > 0:
                    print(f"\n🔄 Retry attempt {attempt + 1}/{max_attempts} with {max_tokens:,} tokens...")
                
                llm_config = LLMCallConfig(
                    temperature=0.2,
                    max_tokens=max_tokens,
                )
                
                response = agent._llm_client.complete(prompt, config=llm_config)
                
                # Extract code from response
                import re
                code_match = re.search(r'```python\s*\n(.*?)\n```', response.text, re.DOTALL)
                if code_match:
                    extracted_code = code_match.group(1)
                else:
                    extracted_code = response.text
                
                # Clean up markers
                extracted_code = extracted_code.strip()
                if extracted_code.startswith('```python'):
                    extracted_code = extracted_code[len('```python'):].lstrip()
                if extracted_code.startswith('```'):
                    extracted_code = extracted_code[3:].lstrip()
                if extracted_code.endswith('```'):
                    extracted_code = extracted_code[:-3].rstrip()
                
                # Validate code completeness
                extracted_lines = extracted_code.count('\n') + 1
                
                # Check 1: Reasonable length
                if extracted_lines < code_lines * 0.5:
                    print(f"⚠️  Code truncated: {extracted_lines} lines vs expected {code_lines}+")
                    if attempt < max_attempts - 1:
                        max_tokens = int(max_tokens * 1.5)
                        print(f"    Increasing tokens to {max_tokens:,} and retrying...")
                        continue
                    else:
                        print("    Max retries reached, using original code")
                        return code
                
                # Check 2: Python syntax
                if not any(marker in extracted_code[:500] for marker in ['import ', 'from ', '#', 'class ', 'def ']):
                    print("⚠️  Extracted code doesn't look like Python")
                    if attempt < max_attempts - 1:
                        continue
                    else:
                        return code
                
                # Check 3: Minimum length
                if len(extracted_code) < 100:
                    print(f"⚠️  Code too short ({len(extracted_code)} chars)")
                    if attempt < max_attempts - 1:
                        continue
                    else:
                        return code
                
                # Success!
                print(f"✅ Code modified successfully ({extracted_lines} lines)")
                return extracted_code
                
            except Exception as e:
                print(f"❌ Attempt {attempt + 1} failed: {e}")
                if attempt < max_attempts - 1:
                    max_tokens = int(max_tokens * 1.5)
                    continue
                else:
                    return code
        
        # All attempts failed
        print("❌ All modification attempts failed, returning original code")
        return code
    
    def _ai_adjust_output(
        self,
        code: str,
        output_request: str,
        config: dict[str, Any],
        file_analysis: dict[str, Any],
        readme: str,
    ) -> str:
        """
        AI adjusts output format based on user request (display changes only).
        
        Uses smart retry with dynamic token allocation to avoid truncation.
        """
        # Calculate required tokens based on code size
        code_lines = code.count('\n') + 1
        max_tokens = self._calculate_required_tokens(code, is_modification=True)
        
        print(f"📊 Output adjustment setup:")
        print(f"    Current code: {code_lines} lines")
        print(f"    Allocated tokens: {max_tokens:,}")
        
        prompt = f"""You are adjusting the output format of a Python checker.

**User's Output Adjustment Request:**
{output_request}

**Current Code:**
```python
{code}
```

**Task:**
1. Focus ONLY on output formatting changes (descriptions, display format, etc.)
2. Do NOT change parsing logic or core functionality
3. Common changes: FOUND_DESC, MISSING_DESC, reason strings, DetailItem formatting
4. Ensure output is user-friendly and clear
5. Return ONLY the complete modified code (ALL {code_lines} lines or more)

**CRITICAL: Return the COMPLETE file - do NOT truncate!**

**Output Format:**
Return the complete modified Python code without any explanations or markdown.
"""
        
        try:
            from utils.models import LLMCallConfig
        except ImportError:
            from AutoGenChecker.utils.models import LLMCallConfig
        
        agent = self._get_llm_agent()
        
        # Smart retry with increasing tokens
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                if attempt > 0:
                    print(f"\n🔄 Retry attempt {attempt + 1}/{max_attempts} with {max_tokens:,} tokens...")
                
                llm_config = LLMCallConfig(
                    temperature=0.2,
                    max_tokens=max_tokens,
                )
                
                response = agent._llm_client.complete(prompt, config=llm_config)
                
                # Extract code from response
                import re
                code_match = re.search(r'```python\s*\n(.*?)\n```', response.text, re.DOTALL)
                if code_match:
                    extracted_code = code_match.group(1)
                else:
                    extracted_code = response.text
                
                # Clean up markers
                extracted_code = extracted_code.strip()
                if extracted_code.startswith('```python'):
                    extracted_code = extracted_code[len('```python'):].lstrip()
                if extracted_code.startswith('```'):
                    extracted_code = extracted_code[3:].lstrip()
                if extracted_code.endswith('```'):
                    extracted_code = extracted_code[:-3].rstrip()
                
                # Validate code completeness
                extracted_lines = extracted_code.count('\n') + 1
                
                # Check 1: Reasonable length
                if extracted_lines < code_lines * 0.5:
                    print(f"⚠️  Code truncated: {extracted_lines} lines vs expected {code_lines}+")
                    if attempt < max_attempts - 1:
                        max_tokens = int(max_tokens * 1.5)
                        print(f"    Increasing tokens to {max_tokens:,} and retrying...")
                        continue
                    else:
                        print("    Max retries reached, using original code")
                        return code
                
                # Check 2: Python syntax markers
                if not any(marker in extracted_code[:500] for marker in ['import ', 'from ', '#', 'class ', 'def ']):
                    print("⚠️  Extracted code doesn't look like Python")
                    if attempt < max_attempts - 1:
                        continue
                    else:
                        return code
                
                # Check 3: Minimum length
                if len(extracted_code) < 100:
                    print(f"⚠️  Code too short ({len(extracted_code)} chars)")
                    if attempt < max_attempts - 1:
                        continue
                    else:
                        return code
                
                # Success!
                print(f"✅ Output adjusted successfully ({extracted_lines} lines)")
                return extracted_code
                
            except Exception as e:
                print(f"❌ Attempt {attempt + 1} failed: {e}")
                if attempt < max_attempts - 1:
                    max_tokens = int(max_tokens * 1.5)
                    continue
                else:
                    return code
        
        # All attempts failed
        print("❌ All adjustment attempts failed, returning original code")
        return code
    
    def _handle_finalization(self, code: str, config: dict[str, Any]) -> str:
        """
        Handle finalization: mark complete and process backup files.
        
        Returns:
            Final code
        """
        print("\n✅ Finalize Checker")
        print("="*80)
        print("📝 Current code/README will be kept as final version.")
        
        try:
            from utils.paths import discover_project_paths
        except ImportError:
            from AutoGenChecker.utils.paths import discover_project_paths
        
        paths = discover_project_paths()
        
        # Show backup files
        code_backup = paths.workspace_root / "Check_modules" / self.module / "scripts" / "checker" / f"{self.item_id}.py.backup"
        readme_backup = paths.workspace_root / "Check_modules" / self.module / "scripts" / "doc" / f"{self.item_id}_README.md.backup"
        
        backup_count = 0
        print("\n📦 Backup files:")
        if code_backup.exists():
            print(f"  • {code_backup.name} (code skeleton)")
            backup_count += 1
        if readme_backup.exists():
            print(f"  • {readme_backup.name} (README template)")
            backup_count += 1
        
        if backup_count == 0:
            print("  (No backup files found)")
            print("\n🎉 Checker is ready for production use!")
            return code
        
        print("\n🔍 These backups contain initial TODO templates for reference.")
        print("\nChoose backup handling:")
        print("  [K] Keep backups (recommended - preserve TODO templates)")
        print("  [R] Remove backups (clean workspace)")
        print("  [C] Cancel finalization")
        
        while True:
            try:
                backup_choice = input("\nYour choice [K/R/C]: ").strip().upper()
            except (EOFError, KeyboardInterrupt):
                backup_choice = 'C'
            
            if backup_choice == 'C':
                print("❌ Finalization cancelled.")
                return code
            
            elif backup_choice == 'K':
                print("\n✅ Finalized! Backup files preserved.")
                print("💡 Backups contain initial TODO templates for future reference.")
                print("\n🎉 Checker is ready for production use!")
                return code
            
            elif backup_choice == 'R':
                confirm = input("\n⚠️  This will permanently delete TODO template backups. Continue? [Y/N]: ").strip().upper()
                if confirm != 'Y':
                    print("❌ Deletion cancelled. Backups preserved.")
                    continue
                
                deleted_count = 0
                
                # Delete code backup
                if code_backup.exists():
                    os.remove(code_backup)
                    print(f"  ✅ Deleted: {code_backup.name}")
                    deleted_count += 1
                
                # Delete README backup
                if readme_backup.exists():
                    os.remove(readme_backup)
                    print(f"  ✅ Deleted: {readme_backup.name}")
                    deleted_count += 1
                
                if deleted_count > 0:
                    print(f"\n🎉 Finalized! Deleted {deleted_count} backup file(s).")
                else:
                    print("\n💡 No backup files found to delete.")
                
                print("🎉 Checker is ready for production use!")
                return code
            
            else:
                print(f"⚠️  Invalid choice: {backup_choice}")
