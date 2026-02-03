"""
Output Refinement Mixin for IntelligentCheckerAgent.

This mixin provides Step 7 output refinement functionality,
allowing users to interactively modify the generated code's output format.

Methods included:
- _output_refinement: Main entry point for output refinement workflow
- _show_implementation_summary: Display current code summary
- _show_modification_summary: Show diff between old and new code
- _ai_modify_output: AI-powered code modification based on user request
"""

from typing import Any
import re


class OutputRefinementMixin:
    """Mixin providing output refinement capabilities for generated code."""
    
    # =========================================================================
    # Output Refinement Methods (Step 7)
    # =========================================================================
    
    def _output_refinement(
        self,
        code: str,
        config: dict[str, Any],
        file_analysis: dict[str, Any],
        readme: str,
    ) -> str:
        """
        Step 7: Output Refinement - Allow user to modify output format/logic.
        
        This step is triggered ONLY when:
        - Code is executable (no syntax/runtime errors from Step 5)
        - Interactive mode is enabled
        - User wants to adjust output format, descriptions, or check logic
        
        Workflow:
        1. Show current implementation summary
        2. Ask if user wants to modify output
        3. If yes, guide user to provide specific modification request
        4. AI modifies code based on user's natural language description
        5. Save and return modified code
        """
        print("\n" + "="*80)
        print("✨ Step 7: Output Refinement (Optional)")
        print("="*80)
        print("\n✅ Code generation completed successfully!")
        print("   The checker is executable and ready for testing.")
        print("\n💡 You can now optionally refine the output before testing:")
        print("   - Modify INFO01/ERROR01 display format")
        print("   - Adjust output descriptions (FOUND_DESC, MISSING_DESC, etc.)")
        print("   - Change parsing logic or detection rules")
        print("   - Add/remove data fields in output")
        
        # Show current implementation summary
        self._show_implementation_summary(code, config)
        
        while True:
            print("\n" + "-"*80)
            print("Options:")
            print("  [C] Continue - Proceed to testing (keep current implementation)")
            print("  [M] Modify Output - Describe changes you want to make")
            print("  [V] View Code - Show full checker implementation")
            print("  [R] Reset - Restore original generated code")
            print("  [F] Finalize - Mark as complete and cleanup backups")
            print("  [Q] Quit - Save and exit (skip testing)")
            print("-"*80)
            
            try:
                user_choice = input("\nYour choice: ").strip().upper()
            except (EOFError, KeyboardInterrupt):
                print("\n⏭️  Skipping refinement, proceeding to next step...")
                return code
            
            if user_choice == 'C':
                print("\n✅ Continuing with current implementation...")
                return code
                
            elif user_choice == 'M':
                # Guide user to provide modification request
                print("\n" + "="*60)
                print("📝 Describe the changes you want to make")
                print("="*60)
                print("\nExamples of effective modification requests:")
                print("  • 'Change INFO01 format from [view]: message to view | message'")
                print("  • 'Add violation count to each ERROR01 line'")
                print("  • 'Modify FOUND_DESC to say \"All timing checks passed\"'")
                print("  • 'Extract path_group name from log and show it in output'")
                print("  • 'Only modify _execute_type2 method: add slack value to output'")
                print("\n💡 Tips:")
                print("  - Be specific about which output (INFO01/ERROR01/descriptions)")
                print("  - Provide examples if possible (current → desired format)")
                print("  - Specify method names if only targeting certain functions")
                print("-"*60)
                
                try:
                    modification_request = input("\n🔧 Your modification request: ").strip()
                except (EOFError, KeyboardInterrupt):
                    print("\n⏭️  Modification cancelled.")
                    continue
                
                if not modification_request:
                    print("⚠️  Empty request, please try again.")
                    continue
                
                # AI modifies code based on user request
                print(f"\n🤖 AI is modifying code based on your request...")
                print(f"   Request: {modification_request[:100]}{'...' if len(modification_request) > 100 else ''}")
                
                modified_code = self._ai_modify_output(
                    code=code,
                    modification_request=modification_request,
                    config=config,
                    file_analysis=file_analysis,
                    readme=readme,
                )
                
                # Show diff summary
                self._show_modification_summary(code, modified_code)
                
                # Ask for confirmation
                print("\n" + "-"*60)
                try:
                    confirm = input("Accept changes? [Y/n]: ").strip().upper()
                except (EOFError, KeyboardInterrupt):
                    confirm = 'N'
                
                if confirm in ['', 'Y', 'YES']:
                    code = modified_code
                    # Save modified code
                    self._save_code_to_file(code, config)
                    print("💾 Changes saved!")
                    print("\n💡 You can continue modifying or proceed to testing.")
                else:
                    print("❌ Changes discarded, keeping original code.")
                    
            elif user_choice == 'V':
                # Show full code
                print("\n" + "="*80)
                print("📄 Full Checker Implementation")
                print("="*80)
                print(code)
                print("="*80)
                
            elif user_choice == 'R':
                print("\n🔄 Reset to Original Code")
                print("="*80)
                
                # Get code file path
                try:
                    from utils.paths import discover_project_paths
                except ImportError:
                    from AutoGenChecker.utils.paths import discover_project_paths
                
                paths = discover_project_paths()
                code_file = paths.workspace_root / "Check_modules" / self.module / "scripts" / "checker" / f"{self.item_id}.py"
                backup_file = code_file.parent / f"{self.item_id}.py.backup"
                
                if not backup_file.exists():
                    print("❌ No backup found. Cannot restore skeleton template.")
                    print("💡 Tip: Backup contains initial skeleton created before AI implementation.")
                    continue
                
                # Confirm reset
                print("\n⚠️  Reset will:")
                print("  1. Restore skeleton template (initial code with TODO placeholders)")
                print("  2. Discard all AI-generated logic and manual edits")
                print("  3. Allow you to regenerate from scratch")
                confirm = input("\nContinue? [Y/N]: ").strip().upper()
                if confirm != 'Y':
                    print("❌ Reset cancelled.")
                    continue
                
                try:
                    # Restore from backup (skeleton template)
                    with open(backup_file, 'r', encoding='utf-8') as f:
                        skeleton_template = f.read()
                    
                    # Save to main file
                    with open(code_file, 'w', encoding='utf-8') as f:
                        f.write(skeleton_template)
                    
                    print(f"✅ Code reset to skeleton template!")
                    print(f"📄 Restored from: {backup_file}")
                    print("💡 You can now regenerate code from Step 4.")
                    
                    # Update code in memory (use skeleton template)
                    code = skeleton_template
                    
                    # Ask if ready to continue
                    proceed = input("\nProceed with original code? [Y/N]: ").strip().upper()
                    if proceed == 'Y':
                        return code
                    else:
                        print("💡 You can continue editing or make other changes.")
                        continue
                
                except Exception as e:
                    print(f"❌ Failed to reset: {e}")
                    continue
                
            elif user_choice == 'F':
                print("\n✅ Finalize Checker")
                print("="*80)
                print("📝 Current code/README will be kept as final version.")
                print("🔍 Backup files contain initial TODO templates for reference.")
                print()
                print("Choose backup handling:")
                print("  [K] Keep backups (recommended - preserve TODO templates)")
                print("  [R] Remove backups (clean workspace)")
                print("  [C] Cancel finalization")
                
                backup_choice = input("\nYour choice [K/R/C]: ").strip().upper()
                
                if backup_choice == 'C':
                    print("❌ Finalization cancelled.")
                    continue
                
                elif backup_choice == 'K':
                    print("\n✅ Finalized! Backup files preserved.")
                    print("💡 Backups contain initial TODO templates for future reference.")
                    print("📦 Backup files:")
                    
                    try:
                        from utils.paths import discover_project_paths
                    except ImportError:
                        from AutoGenChecker.utils.paths import discover_project_paths
                    
                    paths = discover_project_paths()
                    
                    # List backup files
                    code_backup = paths.workspace_root / "Check_modules" / self.module / "scripts" / "checker" / f"{self.item_id}.py.backup"
                    readme_backup = paths.workspace_root / "Check_modules" / self.module / "scripts" / "doc" / f"{self.item_id}_README.md.backup"
                    
                    if code_backup.exists():
                        print(f"  - {code_backup}")
                    if readme_backup.exists():
                        print(f"  - {readme_backup}")
                    
                    print("\n🎉 Checker is ready for production use!")
                    print("\nProceeding to testing...")
                    return code
                
                elif backup_choice == 'R':
                    confirm = input("\n⚠️  This will permanently delete TODO template backups. Continue? [Y/N]: ").strip().upper()
                    if confirm != 'Y':
                        print("❌ Deletion cancelled. Backups preserved.")
                        continue
                    
                    try:
                        from utils.paths import discover_project_paths
                    except ImportError:
                        from AutoGenChecker.utils.paths import discover_project_paths
                    
                    paths = discover_project_paths()
                    deleted_count = 0
                    
                    # Delete code backup
                    code_backup = paths.workspace_root / "Check_modules" / self.module / "scripts" / "checker" / f"{self.item_id}.py.backup"
                    if code_backup.exists():
                        import os
                        os.remove(code_backup)
                        print(f"  ✅ Deleted: {code_backup.name}")
                        deleted_count += 1
                    
                    # Delete README backup
                    readme_backup = paths.workspace_root / "Check_modules" / self.module / "scripts" / "doc" / f"{self.item_id}_README.md.backup"
                    if readme_backup.exists():
                        import os
                        os.remove(readme_backup)
                        print(f"  ✅ Deleted: {readme_backup.name}")
                        deleted_count += 1
                    
                    if deleted_count > 0:
                        print(f"\n🎉 Finalized! Deleted {deleted_count} backup file(s).")
                    else:
                        print("\n💡 No backup files found to delete.")
                    
                    print("💡 Checker is ready for production use.")
                    print("\nProceeding to testing...")
                    return code
                
                else:
                    print(f"⚠️  Invalid choice: {backup_choice}")
                    continue
                
            elif user_choice == 'Q':
                print("\n💾 Saving and exiting...")
                self._save_code_to_file(code, config)
                return code
                
            else:
                print(f"⚠️  Invalid choice: {user_choice}")
    
    def _show_implementation_summary(self, code: str, config: dict[str, Any]) -> None:
        """Show a brief summary of current implementation."""
        print("\n" + "-"*80)
        print("📋 Current Implementation Summary")
        print("-"*80)
        
        # Extract class constants (output descriptions)
        desc_pattern = r'(FOUND_DESC|MISSING_DESC|WAIVED_DESC|FOUND_REASON|MISSING_REASON|WAIVED_BASE_REASON)\s*=\s*["\'](.+?)["\']'
        descriptions = re.findall(desc_pattern, code)
        
        if descriptions:
            print("\n🏷️  Output Descriptions:")
            for name, value in descriptions:
                print(f"   {name:20s} = \"{value[:60]}{'...' if len(value) > 60 else ''}\"")
        
        # Extract method names
        methods = re.findall(r'def (_execute_type\d|_parse_files)\(', code)
        if methods:
            print(f"\n⚙️  Implemented Methods: {', '.join(set(methods))}")
        
        print("-"*80)
    
    def _show_modification_summary(self, old_code: str, new_code: str) -> None:
        """Show a brief summary of what changed."""
        # Simple line count diff
        old_lines = old_code.count('\n')
        new_lines = new_code.count('\n')
        diff = new_lines - old_lines
        
        print(f"   Lines changed: {abs(diff)} {'added' if diff > 0 else 'removed' if diff < 0 else 'modified'}")
        
        # Check if descriptions changed
        desc_pattern = r'(FOUND_DESC|MISSING_DESC|WAIVED_DESC|FOUND_REASON|MISSING_REASON|WAIVED_BASE_REASON)\s*=\s*["\'](.+?)["\']'
        old_descs = dict(re.findall(desc_pattern, old_code))
        new_descs = dict(re.findall(desc_pattern, new_code))
        
        changed_descs = []
        for key in set(old_descs.keys()) | set(new_descs.keys()):
            if old_descs.get(key) != new_descs.get(key):
                changed_descs.append(key)
        
        if changed_descs:
            print(f"   Modified descriptions: {', '.join(changed_descs)}")
    
    def _ai_modify_output(
        self,
        code: str,
        modification_request: str,
        config: dict[str, Any],
        file_analysis: dict[str, Any],
        readme: str,
    ) -> str:
        """
        Use AI to modify code based on user's natural language request.
        
        Uses smart retry with dynamic token allocation to avoid truncation.
        """
        # Calculate required tokens based on code size
        code_lines = code.count('\n') + 1
        max_tokens = self._calculate_required_tokens(code, is_modification=True)
        
        print(f"📊 Output modification setup:")
        print(f"    Current code: {code_lines} lines")
        print(f"    Allocated tokens: {max_tokens:,}")
        
        prompt = f"""Modify the checker code based on user's request.

====================================================================================
USER'S MODIFICATION REQUEST:
====================================================================================
{modification_request}

====================================================================================
CURRENT CODE:
====================================================================================
```python
{code}
```

====================================================================================
CONTEXT (for reference):
====================================================================================

README Output Descriptions:
{self._extract_readme_output_descriptions_for_code_gen(readme)}

File Analysis:
{file_analysis}

Config:
{config}

====================================================================================
MODIFICATION INSTRUCTIONS:
====================================================================================
1. Read the user's request VERY carefully
2. Make ONLY the changes requested - do NOT refactor unrelated code
3. Keep the same overall structure and logic
4. Maintain compliance with template requirements:
   - Keep all required methods (_parse_files, _execute_typeN)
   - Keep class constants (FOUND_DESC, etc.) if not explicitly changing them
   - Preserve error handling and edge case logic
5. If modifying output format:
   - Update both INFO01/ERROR01 formatting AND descriptions if needed
   - Ensure consistency across all Type implementations
6. If modifying parsing logic:
   - Update _parse_files() method
   - Ensure extracted data matches what _execute_typeN() expects
7. Return ONLY the complete modified Python code (ALL {code_lines} lines or more)

⚠️ CRITICAL:
- User request is about OUTPUT/LOGIC refinement, NOT about fixing errors
- Code is already executable, so maintain that stability
- Make surgical changes - don't rewrite large sections unnecessarily
- Return the COMPLETE file - do NOT truncate!

====================================================================================
OUTPUT:
====================================================================================
Return the complete modified Python code. Start with:
################################################################################"""

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
                extracted_code = self._extract_code_from_response(response.text)
                
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
