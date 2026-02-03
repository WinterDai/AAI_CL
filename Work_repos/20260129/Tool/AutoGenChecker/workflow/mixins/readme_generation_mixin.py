"""
README Generation Mixin for IntelligentCheckerAgent.

This mixin handles all README generation and modification functionality:
- AI-powered README generation (Step 3)
- User review and interactive editing
- Backup and restore operations
- AI-assisted README modifications
"""

from typing import Any, TYPE_CHECKING
from pathlib import Path

if TYPE_CHECKING:
    from rich.console import Console


class ReadmeGenerationMixin:
    """Mixin providing README generation and editing capabilities."""
    
    def _ai_generate_readme(
        self,
        config: dict[str, Any],
        file_analysis: dict[str, Any],
    ) -> str:
        """
        AI generates comprehensive README following Step 2 template.
        
        README includes:
        - Overview (category, input files, functional description)
        - Check Logic (input parsing, detection logic)
        - 4 Type Examples (Type 1/2/3/4 with YAML configs)
        - Testing section
        """
        # Note: Step 3 header is now printed in prompt_user_for_hints()
        # so we don't duplicate it here
        
        # IMPORTANT: Backup existing TODO template BEFORE AI generation
        self._backup_readme_template(config)
        self._log("TODO template backed up", "DEBUG")
        
        # Build prompt for README generation
        self._log("\n🔨 Generating README with AI...", "DEBUG")
        self._log("   Building prompt for LLM...", "DEBUG")
        prompt = self._build_readme_generation_prompt(config, file_analysis)
        
        # Call LLM (use cached agent)
        try:
            from utils.models import LLMCallConfig
        except ImportError:
            from AutoGenChecker.utils.models import LLMCallConfig
        
        agent = self._get_llm_agent()
        llm_config = LLMCallConfig(
            temperature=0.3,  # Medium temp for creativity
            max_tokens=16000,  # Increased to handle long descriptions (avoid truncation)
        )
        
        self._log("Calling LLM to generate README...", "INFO", "🤖")
        response = agent._llm_client.complete(prompt, config=llm_config)
        
        readme_content = response.text
        
        self._log(f"Generated {len(readme_content)} characters", "INFO", "✅")
        
        # IMPORTANT: Save README to file immediately (Step 3 requirement)
        self._save_readme_to_file(readme_content, config)
        
        return readme_content
    
    def _backup_readme_template(self, config: dict[str, Any]) -> None:
        """
        Backup existing README template BEFORE AI generation.
        
        This preserves the TODO template so users can Reset to clean state.
        Backup is only created once (first generation).
        """
        try:
            from utils.paths import discover_project_paths
        except ImportError:
            from AutoGenChecker.utils.paths import discover_project_paths
        
        paths = discover_project_paths()
        readme_file = (
            paths.workspace_root / 
            "Check_modules" / 
            self.module / 
            "scripts" / 
            "doc" / 
            f"{self.item_id}_README.md"
        )
        backup_file = readme_file.parent / f"{self.item_id}_README.md.backup"
        
        # Only backup if: (1) backup doesn't exist AND (2) source file exists
        if not backup_file.exists() and readme_file.exists():
            try:
                with open(readme_file, 'r', encoding='utf-8') as f:
                    template_content = f.read()
                
                with open(backup_file, 'w', encoding='utf-8') as f:
                    f.write(template_content)
                
                if self.verbose:
                    print(f"  📦 Backed up TODO template: {backup_file.name}")
            except Exception as e:
                if self.verbose:
                    print(f"  ⚠️  Failed to backup template: {e}")
    
    def _backup_code_template(self, config: dict[str, Any]) -> None:
        """
        Backup existing skeleton code BEFORE AI fills it.
        
        This preserves the initial TODO skeleton for Reset functionality.
        Reset will restore this backup, allowing fresh regeneration.
        
        Args:
            config: Checker configuration
        """
        try:
            from utils.paths import discover_project_paths
        except ImportError:
            from AutoGenChecker.utils.paths import discover_project_paths
        
        paths = discover_project_paths()
        checker_file = (
            paths.workspace_root / 
            "Check_modules" / 
            self.module / 
            "scripts" / 
            "checker" / 
            f"{self.item_id}.py"
        )
        backup_file = checker_file.parent / f"{self.item_id}.py.backup"
        
        # Only backup if:
        # 1. Backup doesn't exist yet (preserve initial TODO skeleton)
        # 2. Source file exists
        if not backup_file.exists() and checker_file.exists():
            try:
                with open(checker_file, 'r', encoding='utf-8') as f:
                    skeleton_content = f.read()
                
                with open(backup_file, 'w', encoding='utf-8') as f:
                    f.write(skeleton_content)
                
                if self.verbose:
                    print(f"  📦 Backed up skeleton template: {backup_file.name}")
            except Exception as e:
                if self.verbose:
                    print(f"  ⚠️  Failed to backup skeleton: {e}")
    
    def _save_readme_to_file(self, readme_content: str, config: dict[str, Any]) -> None:
        """
        Save README to the expected location.
        
        This ensures README is persisted after Step 3, enabling resume from Step 4+.
        """
        try:
            from utils.paths import discover_project_paths
        except ImportError:
            from AutoGenChecker.utils.paths import discover_project_paths
        
        paths = discover_project_paths()
        readme_file = (
            paths.workspace_root / 
            "Check_modules" / 
            self.module / 
            "scripts" / 
            "doc" / 
            f"{self.item_id}_README.md"
        )
        
        # Create directory if not exists
        readme_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Write README (backup was already created before AI generation)
        with open(readme_file, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        
        if self.verbose:
            print(f"  💾 README saved to {readme_file}")
    
    def _user_review_readme(self, readme: str, config: dict[str, Any]) -> str:
        """
        Allow user to review and edit README before code generation.
        
        This interactive step happens after Step 3 (README generation) and before
        Step 4 (code implementation), giving users a chance to:
        - Review Output Descriptions
        - Adjust check logic descriptions
        - Modify pattern_items/waive_items examples
        - Add clarifications or notes
        
        Args:
            readme: Generated README content
            config: Checker configuration
            
        Returns:
            README content (possibly modified by user)
        """
        try:
            from utils.paths import discover_project_paths
        except ImportError:
            from AutoGenChecker.utils.paths import discover_project_paths
        
        paths = discover_project_paths()
        readme_file = (
            paths.workspace_root / 
            "Check_modules" / 
            self.module / 
            "scripts" / 
            "doc" / 
            f"{self.item_id}_README.md"
        )
        
        print("\n" + "─" * 80)
        print("[Step 4/9] 📋 README Review & Edit")
        print("─" * 80)
        print(f"\nGenerated README saved to:")
        print(f"  {readme_file}")
        print("\nChoose action:")
        print("  [K]eep    - Accept current README and proceed")
        print("  [A]I-edit - AI-assisted modification (describe changes)")
        print("  [E]dit    - Edit README manually in text editor")
        print("  [R]eset   - Restore initial TODO template")
        print("  [Q]uit    - Save and exit (resume later)")
        print("─" * 80)
        
        # Store original for reset option
        original_readme = readme
        
        while True:
            choice = input("\nYour choice [K/A/E/R/Q]: ").strip().upper()
            
            if choice == 'K':
                print("✓ README accepted")
                return readme
            
            elif choice == 'A':
                print("\n🤖 AI-Assisted README Edit")
                print("=" * 78)
                print("Describe what you want to change in the README.")
                print("Examples:")
                print("  - Change found_desc to 'Clean max transition checks'")
                print("  - Add more waive_items examples for Type 3")
                print("  - Fix the pattern_items to use actual view names")
                print("  - Update the INFO01 format description")
                print("\nEnter your modification request (or 'cancel' to return):")
                print("-" * 78)
                
                user_prompt = input("> ").strip()
                
                if user_prompt.lower() == 'cancel':
                    print("❌ Cancelled AI edit.")
                    continue
                
                if not user_prompt:
                    print("❌ Empty prompt. Please describe what to change.")
                    continue
                
                try:
                    print("\n🔄 AI is modifying README based on your request...")
                    modified_readme = self._ai_modify_readme(
                        readme, 
                        user_prompt, 
                        config, 
                        readme_file
                    )
                    
                    # Save modified README
                    with open(readme_file, 'w', encoding='utf-8') as f:
                        f.write(modified_readme)
                    
                    print(f"✅ README updated and saved to {readme_file}")
                    
                    # Show diff summary
                    old_lines = readme.count('\n')
                    new_lines = modified_readme.count('\n')
                    print(f"📊 Changes: {old_lines} → {new_lines} lines")
                    
                    # Save user's modification request as hints
                    try:
                        from workflow.user_interaction import save_hints_to_txt
                        if save_hints_to_txt(config['module'], config['item_id'], user_prompt):
                            print(f"💾 Hints saved to Work/phase-1-dev/{config['module']}/hints.txt")
                    except Exception as e:
                        print(f"⚠️  Warning: Failed to save hints: {e}")
                    
                    # Ask if satisfied
                    proceed = input("\n✅ Accept changes and continue? [Y/N/R (retry with new prompt)]: ").strip().upper()
                    
                    if proceed == 'Y':
                        return modified_readme
                    elif proceed == 'R':
                        # Update readme for next iteration
                        readme = modified_readme
                        print("🔄 Ready for another AI edit. What else to change?")
                        continue
                    else:
                        print("💡 Changes saved. You can continue editing or quit.")
                        # Update readme for next iteration
                        readme = modified_readme
                        continue
                
                except Exception as e:
                    print(f"❌ AI modification failed: {e}")
                    print("💡 Try a different prompt or use manual edit mode [E]")
                    continue
            
            elif choice == 'E':
                print(f"📝 Opening README in editor...")
                
                # Open in default editor
                import subprocess
                import platform
                
                system = platform.system()
                try:
                    if system == 'Windows':
                        subprocess.run(['notepad.exe', str(readme_file)], check=True)
                    elif system == 'Darwin':  # macOS
                        subprocess.run(['open', '-e', str(readme_file)], check=True)
                    else:  # Linux
                        # Try common editors
                        for editor in ['gedit', 'kate', 'nano', 'vim']:
                            try:
                                subprocess.run([editor, str(readme_file)], check=True)
                                break
                            except FileNotFoundError:
                                continue
                    
                    print("\n⏳ Waiting for you to save and close the editor...")
                    input("Press ENTER when you've finished editing the README: ")
                    
                    # Reload the edited README
                    with open(readme_file, 'r', encoding='utf-8') as f:
                        edited_readme = f.read()
                    
                    print("✅ README reloaded with your changes!")
                    
                    # Ask if ready to continue
                    proceed = input("\nProceed to code generation? [Y/N]: ").strip().upper()
                    if proceed == 'Y':
                        return edited_readme
                    elif proceed == 'N':
                        print("💡 You can continue editing or quit to resume later.")
                        continue
                    else:
                        print("Invalid choice. Returning to menu...")
                        continue
                
                except Exception as e:
                    print(f"❌ Failed to open editor: {e}")
                    print("💡 Please edit the README manually:")
                    print(f"   {readme_file}")
                    print("\nThen run:")
                    print(f"   python cli.py generate --item-id {self.item_id} \\")
                    print(f"       --module {self.module} --ai-agent --resume-from-step 4")
                    return readme
            
            elif choice == 'R':
                print("\n🔄 Reset to Initial State")
                print("=" * 78)
                
                # Check if backup exists
                backup_file = readme_file.parent / f"{self.item_id}_README.md.backup"
                if not backup_file.exists():
                    print("❌ No backup found. Cannot restore TODO template.")
                    print("💡 Tip: Backup contains initial TODO template created before AI generation.")
                    continue
                
                # Confirm reset
                print("\n⚠️  Reset will:")
                print("  1. Restore TODO template (initial skeleton with placeholders)")
                print("  2. Discard all AI-generated content and manual edits")
                print("  3. Allow you to regenerate from scratch")
                confirm = input("\nContinue? [Y/N]: ").strip().upper()
                if confirm != 'Y':
                    print("❌ Reset cancelled.")
                    continue
                
                try:
                    # Restore from backup (TODO template)
                    with open(backup_file, 'r', encoding='utf-8') as f:
                        todo_template = f.read()
                    
                    # Save to main file
                    with open(readme_file, 'w', encoding='utf-8') as f:
                        f.write(todo_template)
                    
                    print(f"✅ README reset to TODO template!")
                    print(f"📄 Restored from: {backup_file}")
                    
                    # Ask if user wants to regenerate immediately
                    regenerate = input("\n🔄 Regenerate README from Step 3 now? [Y/N]: ").strip().upper()
                    if regenerate == 'Y':
                        print("\n🚀 Starting README regeneration...")
                        # Trigger regeneration by returning None (will be handled by caller)
                        return None  # Signal to regenerate
                    else:
                        print("\n💡 README remains as TODO template.")
                        print("   You can:")
                        print("   - [E] Edit manually")
                        print("   - [Q] Quit and resume later with --resume-from-step 3")
                        continue
                
                except Exception as e:
                    print(f"❌ Failed to reset: {e}")
                    continue
            
            elif choice == 'Q':
                print("\n💾 Progress saved. README is ready for your review.")
                print("\nTo resume after editing README:")
                print(f"  python cli.py generate --item-id {self.item_id} \\")
                print(f"      --module {self.module} --ai-agent --resume-from-step 4")
                print("\nExiting...")
                import sys
                sys.exit(0)
            
            else:
                print("❌ Invalid choice. Please enter C, A, E, R, or Q.")
    
    def _ai_modify_readme(
        self,
        current_readme: str,
        user_prompt: str,
        config: dict[str, Any],
        readme_file: Path,
    ) -> str:
        """
        Use AI to modify README based on user's natural language request.
        
        Args:
            current_readme: Current README content
            user_prompt: User's modification request
            config: Checker configuration
            readme_file: Path to README file
            
        Returns:
            Modified README content
        """
        # Build AI prompt for modification
        modification_prompt = f"""You are modifying a checker README based on user request.

====================================================================================
USER REQUEST:
====================================================================================
{user_prompt}

====================================================================================
CURRENT README:
====================================================================================
{current_readme}

====================================================================================
MODIFICATION INSTRUCTIONS:
====================================================================================
1. Read the user's request carefully
2. Locate the relevant sections in the README
3. Make ONLY the requested changes
4. Keep the overall structure and format intact
5. DO NOT change sections unrelated to the request
6. Preserve all markdown formatting
7. Return the COMPLETE modified README (not just the changed parts)

⚠️ CRITICAL RULES:
- If user asks to change descriptions: Update the "## Output Descriptions" section
- If user asks about patterns: Update pattern_items in Type 2/3 configurations
- If user asks about waivers: Update waive_items in Type 3/4 configurations
- If user asks about examples: Update the Sample Output sections
- Keep the exact same heading structure (##, ###, etc.)
- DO NOT wrap output in ```markdown``` - return raw markdown

====================================================================================
OUTPUT REQUIREMENTS:
====================================================================================
Return the COMPLETE modified README with:
- Same structure as original
- Only the requested changes applied
- All other content preserved
- Valid markdown formatting
"""

        # Call LLM
        try:
            from utils.models import LLMCallConfig
        except ImportError:
            from AutoGenChecker.utils.models import LLMCallConfig
        
        agent = self._get_llm_agent()
        llm_config = LLMCallConfig(
            temperature=0.3,  # Low temp for accurate editing
            max_tokens=20000,  # Increased to handle long READMEs
        )
        
        response = agent._llm_client.complete(modification_prompt, config=llm_config)
        
        # Extract modified README
        modified_readme = response.text.strip()
        
        # Remove markdown code block if present
        if modified_readme.startswith('```markdown'):
            modified_readme = modified_readme[len('```markdown'):].strip()
        if modified_readme.startswith('```'):
            modified_readme = modified_readme[3:].strip()
        if modified_readme.endswith('```'):
            modified_readme = modified_readme[:-3].strip()
        
        return modified_readme
    
    def _save_code_to_file(self, code: str, config: dict[str, Any]) -> None:
        """
        Save generated/fixed code to the checker file.
        
        This ensures code is persisted after Step 4 and Step 5, enabling resume from Step 6+.
        Note: Backup is created BEFORE AI generation (in _backup_code_template), not here.
        """
        try:
            from utils.paths import discover_project_paths
        except ImportError:
            from AutoGenChecker.utils.paths import discover_project_paths
        
        paths = discover_project_paths()
        checker_file = (
            paths.workspace_root / 
            "Check_modules" / 
            self.module / 
            "scripts" / 
            "checker" / 
            f"{self.item_id}.py"
        )
        
        # Create directory if not exists
        checker_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Clean up code markers that may have been added by LLM
        cleaned_code = code.strip()
        # Remove leading ```python marker
        if cleaned_code.startswith('```python'):
            lines = cleaned_code.split('\n')
            cleaned_code = '\n'.join(lines[1:])  # Skip first line
        # Remove trailing ``` marker
        if cleaned_code.endswith('```'):
            cleaned_code = cleaned_code[:-3].strip()
        
        # Write code
        with open(checker_file, 'w', encoding='utf-8') as f:
            f.write(cleaned_code)
        
        if self.verbose:
            print(f"  💾 Code saved to {checker_file}")
    
    def _build_readme_generation_prompt(
        self,
        config: dict[str, Any],
        file_analysis: dict[str, Any],
    ) -> str:
        """
        Build prompt for README generation following Step 2 template.
        
        Based on DEVELOPER_TASK_PROMPTS.md v1.1.0 Step 2 Phase 2.
        Uses a standard template structure with TODO placeholders that AI fills in.
        """
        item_id = config['item_id']
        module = config.get('module', self.module)
        description = config.get('description', 'TBD')
        input_files = config.get('input_files', [])
        input_files_str = ', '.join(input_files) if input_files else 'TBD'
        
        # [Phase 1] Add user hints if available
        user_hints_section = ""
        if hasattr(self, 'user_hints') and self.user_hints:
            user_hints_section = f"""
====================================================================================
USER PROVIDED HINTS (CRITICAL - Follow these requirements!):
====================================================================================
{self.user_hints}

IMPORTANT: These hints contain domain-specific knowledge that the AI must incorporate:
- Use the specific terminology mentioned
- Follow the suggested patterns and examples
- Respect the check purpose and edge cases described
- Prioritize hints over generic assumptions
====================================================================================
"""
        
        # Standard README template with TODO placeholders for AI to fill
        # IMPORTANT: This template MUST match work_dispatcher's README_TEMPLATE for consistency
        readme_template = f'''# {item_id}: {description}

## Overview

**Check ID:** {item_id}  
**Description:** {description}  
**Category:** TODO - Add category  
**Input Files:** TODO - List input files

TODO: Add functional description of the checker

---

## Check Logic

### Input Parsing
TODO: Describe how to parse input files

**Key Patterns:**
```python
# Pattern 1: [Description]
pattern1 = r'TODO: Add actual regex pattern'
# Example: "TODO: Add example line from file"
```

### Detection Logic
TODO: Describe check logic step by step

---

## Output Behavior (CRITICAL - Determines Type 2/3 Logic!)

**Check Mode:** `existence_check` | `status_check`

Choose ONE mode based on what pattern_items represents:

### Mode 1: `existence_check` - 存在性检查
**Use when:** pattern_items are items that SHOULD EXIST in input files

```
pattern_items: ["item_A", "item_B", "item_C"]
Input file contains: item_A, item_B

Result:
  found_items:   item_A, item_B    ← Pattern found in file
  missing_items: item_C            ← Pattern NOT found in file

PASS: All pattern_items found in file
FAIL: Some pattern_items not found in file
```

### Mode 2: `status_check` - 状态检查  
**Use when:** pattern_items are items to CHECK STATUS, only output matched items

```
pattern_items: ["port_A", "port_B"]
Input file contains: port_A(fixed), port_B(unfixed), port_C(unfixed)

Result:
  found_items:   port_A            ← Pattern matched AND status correct
  missing_items: port_B            ← Pattern matched BUT status wrong
  (port_C not output - not in pattern_items)

PASS: All matched items have correct status
FAIL: Some matched items have wrong status (or pattern not matched)
```

**Selected Mode for this checker:** TODO: Choose `existence_check` or `status_check`

**Rationale:** TODO: Explain why this mode is appropriate

---

## Output Descriptions (CRITICAL - Code Generator Uses These!)

This section defines the output strings used by `build_complete_output()` in the checker code.
**Fill in these values based on the check logic above.**

```python
# ⚠️ CRITICAL: Description & Reason parameter usage by Type (API-026)
# Both DESC and REASON constants are split by Type for semantic clarity:
#   Type 1/4 (Boolean): Use DESC_TYPE1_4 & REASON_TYPE1_4 (emphasize "found/not found")
#   Type 2/3 (Pattern): Use DESC_TYPE2_3 & REASON_TYPE2_3 (emphasize "matched/satisfied")

# Item description for this checker
item_desc = "{description}"

# PASS case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_desc_type1_4 = "TODO: Type 1/4 - e.g., 'Tool version found in configuration'"
# Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
found_desc_type2_3 = "TODO: Type 2/3 - e.g., 'Required pattern matched (2/2)'"

# PASS reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_reason_type1_4 = "TODO: Type 1/4 - e.g., 'Tool version found in configuration'"
# Type 2/3: Pattern checks - emphasize pattern matching terms (matched|satisfied|validated|compliant|fulfilled)
found_reason_type2_3 = "TODO: Type 2/3 - e.g., 'Required pattern matched and validated'"

# FAIL case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_desc_type1_4 = "TODO: Type 1/4 - e.g., 'Required item not found in setup file'"
# Type 2/3: Pattern checks - emphasize pattern mismatch
missing_desc_type2_3 = "TODO: Type 2/3 - e.g., 'Expected pattern not satisfied (1/2 missing)'"

# FAIL reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_reason_type1_4 = "TODO: Type 1/4 - e.g., 'Required item not found in setup file'"
# Type 2/3: Pattern checks - emphasize pattern mismatch terms (not satisfied|missing|failed)
missing_reason_type2_3 = "TODO: Type 2/3 - e.g., 'Expected pattern not satisfied or missing'"

# WAIVED case descriptions (ALL Types need these)
# Type 1/2 use in waiver=0 mode for waive_items comments
# Type 3/4 use for actual waived violations
waived_desc = "TODO: e.g., 'Waived timing violations'"

# WAIVED reasons (Type 3/4 ONLY - actual waiver logic)
waived_base_reason = "TODO: Type 3/4 - e.g., 'Timing violation waived per design team approval'"

# UNUSED waivers (Type 3/4 ONLY)
unused_desc = "TODO: e.g., 'Unused waiver entries'"
unused_waiver_reason = "TODO: e.g., 'Waiver not matched - no corresponding violation found'"
```

### INFO01/ERROR01 Display Format

```
INFO01 (Clean/Pass items):
  Format: TODO: e.g., "[view_name]: all path groups clean"
  Example: TODO: e.g., "func_rcss_0p675v_125c: setup=0.123ns, hold=0.045ns"

ERROR01 (Violation/Fail items):
  Format: TODO: e.g., "[VIOLATION_TYPE]: [details]"
  Example: TODO: e.g., "TIMING VIOLATION: View=func_rcss, Slack=-0.012ns"
```

---

## Type 1: Boolean Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
{item_id}:
  description: "{description}"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - TODO: Add input file path
  waivers:
    value: N/A
    waive_items: []
```

**Check Behavior:**
Type 1 performs custom boolean checks (file exists? config valid?).
PASS/FAIL based on checker's own validation logic.

**Sample Output (PASS):**
```
Status: PASS
Reason: [found_reason from Output Descriptions]
INFO01:
  - [item in INFO01 format]
```

**Sample Output (FAIL):**
```
Status: FAIL
Reason: [missing_reason from Output Descriptions]
ERROR01:
  - [item in ERROR01 format]
```

### Type 1 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
{item_id}:
  description: "{description}"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - TODO: Add input file path
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: This check is informational only because [reason]"
      - "Note: Violations are expected in [scenario] and do not require fixes"
```

**CRITICAL Behavior (waivers.value=0):**
- NOTE: Type 1 has NO waiver logic. waive=0 is forced PASS mode only
- IMPORTANT: waive_items uses PLAIN STRINGS (NOT name/reason dict like Type 3/4!)
- waive_items serves as COMMENT ONLY (no matching/filtering logic)
- waive_items content printed as INFO with [WAIVED_INFO] tag
- ALL violations force converted: FAIL→PASS, displayed as INFO with [WAIVED_AS_INFO] tag
- Check ALWAYS returns PASS (violations shown as INFO for tracking)
- Used when: Check is informational only, violations expected/acceptable

**Sample Output (PASS with violations):**
```
Status: PASS  # Always PASS when waivers.value=0
Reason: All violations waived as informational
INFO01 ([WAIVED_INFO] - waive_items as comment):
  - "TODO: Explain why violations are acceptable for this check"
INFO02 ([WAIVED_AS_INFO] - violations converted to PASS, shown as INFO):
  - [violation_item] [WAIVED_AS_INFO]
```

---

## Type 2: Value Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
{item_id}:
  description: "{description}"
  requirements:
    value: 0
    pattern_items:
      - "TODO: pattern1"  # ⚠️ MUST match description semantic level!
      - "TODO: pattern2"  # If description="List version" → Use "22.11-s119" (NOT "innovus/22.11-s119")
  input_files:
    - TODO: Add input file path
  waivers:
    value: N/A
    waive_items: []
```

🛑 CRITICAL RULE for pattern_items:
- If description contains "version": Use VERSION IDENTIFIERS ONLY (e.g., "22.11-s119_1")
  ❌ DO NOT use paths: "innovus/221/22.11-s119_1"
  ❌ DO NOT use filenames: "libtech.lef"
- If description contains "filename"/"name": Use COMPLETE FILENAMES (e.g., "design.v")
- If description contains "status": Use STATUS VALUES (e.g., "Loaded", "Skipped")

**Check Behavior:**
Type 2 searches pattern_items in input files.
PASS/FAIL depends on check purpose:
- Violation Check: PASS if found_items empty (no violations)
- Requirement Check: PASS if missing_items empty (all requirements met)

**Sample Output (PASS):**
```
Status: PASS
Reason: [found_reason]
INFO01:
  - [items matching pattern_items]
```

### Type 2 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
{item_id}:
  description: "{description}"
  requirements:
    value: 0
    pattern_items:
      - "TODO: pattern1"
      - "TODO: pattern2"
  input_files:
    - TODO: Add input file path
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: This check is informational only because [reason]"
      - "Note: Pattern mismatches are expected in [scenario] and do not require fixes"
```

**CRITICAL Behavior (waivers.value=0):**
- NOTE: Type 2 has NO waiver logic. waive=0 is forced PASS mode only
- IMPORTANT: waive_items uses PLAIN STRINGS (NOT name/reason dict like Type 3/4!)
- waive_items serves as COMMENT ONLY (no matching/filtering logic)
- waive_items content printed as INFO with [WAIVED_INFO] tag
- ALL errors/mismatches force converted: ERROR→PASS, displayed as INFO with [WAIVED_AS_INFO] tag
- Check ALWAYS returns PASS (errors shown as INFO for tracking)
- Used when: Pattern check is informational, mismatches expected

**Sample Output (PASS with mismatches):**
```
Status: PASS  # Always PASS when waivers.value=0
Reason: All mismatches waived as informational
INFO01 ([WAIVED_INFO] - waive_items as comment):
  - "TODO: Explain why mismatches are acceptable"
INFO02 ([WAIVED_AS_INFO] - errors converted to PASS, shown as INFO):
  - [mismatch_item] [WAIVED_AS_INFO]
```

---

## Type 3: Value Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
{item_id}:
  description: "{description}"
  requirements:
    value: 0
    pattern_items:
      - "TODO: pattern1"  # ⚠️ MUST match description semantic level!
  input_files:
    - TODO: Add input file path
  waivers:
    value: 2
    waive_items:
      - name: "TODO: item_to_waive_1"  # ⚠️ MUST match pattern_items semantic level!
        reason: "TODO: waiver reason 1"
      - name: "TODO: item_to_waive_2"
        reason: "TODO: waiver reason 2"
```

🛑 CRITICAL RULE for pattern_items AND waive_items.name:
- BOTH must be at SAME semantic level as description!
- If description contains "version": 
  ✅ pattern_items: ["22.11-s119_1", "23.10-s200"] (version identifiers)
  ✅ waive_items.name: "22.11-s119_1" (same level as pattern_items)
  ❌ DO NOT mix: pattern_items="innovus/22.11-s119" (path) with waive_items.name="22.11-s119" (version)
- If description contains "filename":
  ✅ pattern_items: ["design.v", "top.v"] (filenames)
  ✅ waive_items.name: "design.v" (same level as pattern_items)

**Check Behavior:**
Type 3 = Type 2 + waiver support.
Same pattern search logic as Type 2, plus waiver classification:
- Match found_items against waive_items
- Unwaived items → ERROR (need fix)
- Waived items → INFO with [WAIVER] tag (approved)
- Unused waivers → WARN with [WAIVER] tag
PASS if all found_items (violations) are waived.

**Sample Output (with waived items):**
```
Status: PASS
Reason: All violations waived
INFO01 (Waived):
  - [waived_item] [WAIVER]
WARN01 (Unused Waivers):
  - [unused_waiver]: [unused_waiver_reason]
```

---

## Type 4: Boolean Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
{item_id}:
  description: "{description}"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - TODO: Add input file path
  waivers:
    value: 2
    waive_items:
      - name: "TODO: item_to_waive_1"
        reason: "TODO: waiver reason 1"
      - name: "TODO: item_to_waive_2"
        reason: "TODO: waiver reason 2"
```

⚠️ CRITICAL: Type 4 waive_items MUST be IDENTICAL to Type 3 waive_items!
- After generating Type 3 configuration, COPY the EXACT waive_items to Type 4
- Use the SAME name values from Type 3
- Use the SAME reason text from Type 3
- This ensures consistency since Type 3 and Type 4 use identical waiver logic

**Check Behavior:**
Type 4 = Type 1 + waiver support.
Same boolean check as Type 1 (no pattern_items), plus waiver classification:
- Match violations against waive_items
- Unwaived violations → ERROR
- Waived violations → INFO with [WAIVER] tag
- Unused waivers → WARN with [WAIVER] tag
PASS if all violations are waived.

**Sample Output:**
```
Status: PASS
Reason: All items waived
INFO01 (Waived):
  - [waived_item] [WAIVER]
```

---

## Testing

### Test Commands

```powershell
# Create test snapshots for all types
python common/regression_testing/create_all_snapshots.py --modules {module} --checkers {item_id} --force

# Run individual tests
python {item_id}.py
```

---

## Notes

TODO: Add notes, limitations, known issues, etc.
'''

        # Build the prompt for AI
        prompt = f"""You are filling in a README template. DO NOT change the structure.

{user_hints_section}
====================================================================================
⚠️ CRITICAL: STRICT TEMPLATE COMPLIANCE REQUIRED
====================================================================================

You MUST:
1. Keep the EXACT markdown structure - same headings, same order, same format
2. Replace ONLY the "TODO:" text with actual content
3. DO NOT add new sections or remove existing sections
4. DO NOT change heading names or hierarchy
5. The "## Output Descriptions" section is MANDATORY - fill in ALL the python code strings!

====================================================================================
FILE ANALYSIS RESULTS (use this to fill TODOs):
====================================================================================
{file_analysis}

====================================================================================
CONFIG:
====================================================================================
{config}

====================================================================================
README TEMPLATE TO FILL (keep EXACT structure):
====================================================================================
{readme_template}

====================================================================================
OUTPUT REQUIREMENTS:
====================================================================================
Return the README with:
- Same structure as template (all ## headings preserved)
- All "TODO:" replaced with actual content
- "## Output Descriptions" section with filled python strings
- Real patterns and examples from file analysis
- ⚠️ CRITICAL: For Type 2/3, requirements.value MUST equal len(pattern_items)
  Example: If 2 patterns, use value: 2; if 3 patterns, use value: 3
- DO NOT wrap in ```markdown``` code block, just return raw markdown

====================================================================================
⚠️ STEP 0: Semantic Alignment Analysis (DO THIS FIRST!)
====================================================================================

Before defining pattern_items and waive_items, perform semantic alignment analysis:

**Step 1: Analyze Check Purpose from Description**
Read the checker description carefully to determine the PRIMARY check goal and semantic level:

**SEMANTIC LEVEL GUIDE - Common Description Patterns:**

1. **"List [X] version" / "Confirm [X] version is correct"**
   - Semantic: Extract VERSION IDENTIFIERS, not full paths or filenames
   - Example patterns: "22.11-s119_1", "v3.2", "231/23.11.000"
   - Check Logic: Extract version numbers from tool paths or filenames
   - ✅ Pattern: `"22.11-s119_1"` (version only)
   - ❌ Pattern: `"innovus/221/22.11-s119_1"` (full path - too broad)

2. **"List [X] name" / "List [X] filename"**  
   - Semantic: Extract COMPLETE FILENAMES with extensions
   - Example patterns: "design.v", "CORE65GPSVT_v3.2.lib", "PLN3ELO_17M_014.11_2a.encrypt"
   - Check Logic: Extract full filename (may include version within name)
   - ✅ Pattern: `"CORE65GPSVT_v3.2.lib"` (complete filename)
   - ❌ Pattern: `"v3.2"` (version only - too narrow)

3. **"Confirm [X] was [not] modified" / "Check modification status"**
   - Semantic: Extract STATUS VALUES as strings
   - Example patterns: "MODIFIED", "UNMODIFIED", "YES", "NO"
   - Check Logic: Compare against baseline or check modification flags
   - ✅ Pattern: `"UNMODIFIED"`, `"MODIFIED"`
   - ❌ Pattern: Boolean true/false (wrong type)

4. **"Confirm no [X] exist" / "Check for [X]"**
   - Semantic: Extract COUNTS or existence status
   - Example patterns: "0", "5", "NONE", "FOUND"
   - Check Logic: Count occurrences or report existence
   - ✅ Pattern: `"0"`, `"NONE"` (count or status)
   - ❌ Pattern: Boolean (if count needed)

5. **"Confirm [X] is correct" / "Verify [X]"**
   - ⚠️ AMBIGUOUS! Determine from context:
   - If examples show values → Extract those VALUES
   - If checking against spec → Extract STATUS ("PASS"/"FAIL")
   - If no clear spec → Use Type 1 (Boolean)
   
6. **"List [X]" without qualifiers**
   - ⚠️ AMBIGUOUS! Check examples in description:
   - If example shows filenames → Extract FILENAMES
   - If example shows values → Extract VALUES
   - If example shows counts → Extract COUNTS

7. **Mixed semantics in one description**
   - Example: "Confirm version is correct. List name in comment."
   - Solution: Choose PRIMARY semantic (usually the first one)
   - Or use Check Logic to extract both dimensions

**Step 2: Match Pattern Items to Actual Parsing Output**
⚠️ CRITICAL: Description is FIXED - you MUST adjust Check Logic and pattern_items to match it!

Based on the patterns in "Check Logic" section, answer:
- What does the description REQUIRE the checker to extract?
- Does the current Check Logic extract the right granularity?
- If NOT, adjust the Check Logic to extract what description promises!
- Pattern items MUST match the extraction granularity that description requires!

Examples:
- Description says "version" → Adjust Check Logic to extract version numbers → pattern_items = version strings
- Description says "files" → Adjust Check Logic to extract filenames → pattern_items = file identifiers  
- Description says "status" → Adjust Check Logic to extract status text → pattern_items = status values
- Description says mixed → Check Logic extracts multiple dimensions → pattern_items reflect each dimension

**Step 3: Semantic Consistency Validation**

❌ WRONG Example 1 - Description says "version" but pattern_items are filenames:
```yaml
description: "Confirm QRC version is correct"
pattern_items:
  - "quantus_tool.exe"    # ❌ This is a filename, not a version!
  - "output.spef"         # ❌ This is a filename, not a version!
```

✅ CORRECT Example 1 - Aligned semantics:
```yaml
description: "Confirm QRC version is correct"
pattern_items:
  - "22.1.1-s233"         # ✅ This is a version number!
  - "22.1.2-s240"         # ✅ This is a version number!
```

❌ WRONG Example 2 - Mismatch between description and actual parsing:
```yaml
description: "Confirm netlist version is correct"  # FIXED - Cannot change!
Check Logic: "Extract netlist filename from read_netlist command"
# ❌ Logic extracts FILENAME but description requires VERSION check!
pattern_items: ["design_v1.2.3.v"]  # ❌ Ambiguous - is this version or filename?
```

✅ CORRECT Example 2 - Adjust Check Logic to match FIXED description:
```yaml
description: "Confirm netlist version is correct"  # FIXED - Cannot change!
Check Logic: "Extract version identifier from netlist path (e.g., extract date/tag from path structure)"
# ✅ Example: From "C:\\project\\2024_Q4\\design.v" extract "2024_Q4"
# ✅ Example: From "design_v1.2.3.v" extract "v1.2.3"
pattern_items:
  - "2024_Q4"             # ✅ Version identifier extracted from path!
  - "v1.2.3"              # ✅ Version tag extracted from filename!
```

Alternative - If NO version info exists in files:
```yaml
description: "Confirm netlist version is correct"  # FIXED - Cannot change!
Check Logic: "Verify netlist file exists and extract design name as version identifier"
# ✅ Use design name as version proxy when explicit version unavailable
pattern_items:
  - "phy_cmn_phase_align_digtop"  # ✅ Design name as version identifier
```

⚠️ RULE: NEVER change description! Always adjust Check Logic and pattern_items to fulfill what description requires!

**Step 4: Multi-Dimensional Checks**
If checker validates multiple dimensions, pattern_items should reflect ALL dimensions:

Example - Mixed version + configuration check:
```yaml
description: "Confirm tool version and SPEF configuration"
Check Logic:
  - Pattern 1: Extract QRC version from header
  - Pattern 2: Extract SPEF loading status
pattern_items:
  - "22.1.1-s233"         # Dimension 1: Version
  - "SPEF: Skipped"       # Dimension 2: Configuration
# ✅ Each pattern_item corresponds to one check dimension!
```

**Step 5: Validation Checklist (Before finalizing pattern_items)**
Before writing Type 2/3 configurations, verify:
□ Does Check Logic extract what the FIXED description requires?
□ Do pattern_items match what Check Logic regex patterns actually extract?
□ Does the semantic level (version/file/status/config) align with FIXED description?
□ Would pattern_items make sense if you read them without context?
□ Can checker code easily compare parsed values against these pattern_items?
□ Are waive_items using the SAME format/granularity as pattern_items?

If ANY checkbox is unchecked:
- ❌ DO NOT change description (it's FIXED!)
- ✅ Adjust Check Logic to extract what description requires
- ✅ Adjust pattern_items to match the corrected extraction logic

====================================================================================
📚 REAL-WORLD EXAMPLES: How to Interpret Common Descriptions
====================================================================================

**Example A: "List Innovus implementation tool version (eg. innovus/221/22.11-s119_1)"**
```yaml
❌ WRONG Interpretation - Taking example literally:
  pattern_items:
    - "innovus/221/22.11-s119_1"  # Full path - too broad!
    
✅ CORRECT Interpretation - Extract VERSION from path:
  Check Logic: "Parse tool path and extract version identifier"
  pattern_items:
    - "22.11-s119_1"      # Version identifier only
    - "22.10-s100_2"      # Another version
  # Rational: Description says "version", example shows WHERE to find it
```

**Example B: "Confirm latest DRC rule deck(s) was used? List DRC rule deck name in Comments."**
```yaml
❌ WRONG - Focus on "Confirm latest":
  Type: Type 1 (Boolean check if latest)
  
✅ CORRECT - Focus on "List name":
  Type: Type 2 (Value check - extract names)
  Check Logic: "Extract DRC rule deck filenames from reports"
  pattern_items:
    - "PLN3ELO_17M_014.11_2a.encrypt"
    - "PLN3ELO_17M_054_PATCH.11_2a.encrypt"
  # Rational: "List name" is primary action, "latest" is validation context
```

**Example C: "Confirm DRC rule deck was not modified? If it was, explain in comments."**
```yaml
❌ WRONG - Treating as boolean:
  Type: Type 1 (Boolean: true if not modified)
  
✅ CORRECT - Extract modification status as value:
  Type: Type 2 (Value check - report status)
  Check Logic: "Check modification status against baseline"
  pattern_items:
    - "UNMODIFIED"        # Status value 1
    - "MODIFIED"          # Status value 2
  # Rational: Need to distinguish between states, not just yes/no
```

**Example D: "Confirm max routing layer is correct. Provide max routing layer value in comment."**
```yaml
❌ WRONG - Split into boolean + value:
  Type: Type 1 for "is correct", separate comment for value
  
✅ CORRECT - Extract the value directly:
  Type: Type 2 (Value check - extract layer)
  Check Logic: "Extract maximum routing layer value from design"
  pattern_items:
    - "M7"                # Layer identifier
    - "M11"               # Another layer
  # Rational: "Provide value" is the real check, "is correct" is validation
```

**Example E: "List the VT ratio (without physical cells): EG: TSMCN7/N6:SVT(50%)/LVT(40%)/ULVT(10%)"**
```yaml
❌ WRONG - Taking example format literally:
  pattern_items:
    - "TSMCN7/N6:SVT(50%)/LVT(40%)/ULVT(10%)"  # Too rigid!
    
✅ CORRECT - Break down structure:
  Type: Type 2 (Value check - extract ratio components)
  Check Logic: "Calculate VT distribution excluding physical cells"
  pattern_items:
    - "SVT(50%)"          # Component 1
    - "LVT(40%)"          # Component 2
    - "ULVT(10%)"         # Component 3
  # Rational: Checker validates each VT type percentage, not whole string
```

**Example F: "Confirm the netlist/constraint version is correct. For MIG program, list FEI release package name."**
```yaml
❌ WRONG - Mixed boolean + conditional list:
  Type: Type 1 for version check, ignore MIG part
  
✅ CORRECT - Extract both dimensions:
  Type: Type 2 (Value check - extract identifiers)
  Check Logic: 
    - "Extract netlist/constraint version identifiers"
    - "For MIG: Extract FEI release package name"
  pattern_items:
    - "netlist_v2024Q4"   # Netlist version
    - "constraints_v1.5"  # Constraint version
    - "FEI_R3.2"          # FEI package (for MIG)
  # Rational: Both are identification checks, use Type 2 for both
```

**Example G: "Confirm proper clock tree buffer/inverter types are used. Provide a list in comment."**
```yaml
❌ WRONG - Boolean "proper types used":
  Type: Type 1 (Boolean check)
  
✅ CORRECT - List the actual types:
  Type: Type 2 (Value check - extract cell types)
  Check Logic: "Extract clock tree buffer and inverter cell names"
  pattern_items:
    - "CKBD4BWP"          # Buffer type
    - "CKINVD2BWP"        # Inverter type
    - "CKBD8BWP"          # Another buffer
  # Rational: "Provide a list" indicates value extraction, not boolean
```

====================================================================================
⚠️ STEP 1: SEMANTIC VALIDATION - Match Description to pattern_items!
====================================================================================

🛑 MANDATORY PRE-CHECK: Before configuring pattern_items, VALIDATE semantic alignment:

**Description Keyword Analysis:**
1. ✅ If description contains "version" / "版本":
   - pattern_items = VERSION IDENTIFIERS ONLY (e.g., "22.11-s119_1", "v3.2")
   - ❌ DO NOT use file paths (e.g., "innovus/221/22.11-s119_1")
   - ❌ DO NOT use filenames (e.g., "libtech.lef")
   - Example: "List Innovus version" → pattern_items: ["22.11-s119_1", "23.10-s200"]

2. ✅ If description contains "filename" / "name" / "file list" / "文件名":
   - pattern_items = COMPLETE FILENAMES (e.g., "design.v", "timing.sdc")
   - ✅ Include extension if present (e.g., ".v", ".lef", ".db")
   - Example: "List design files" → pattern_items: ["top.v", "sub_module.v"]

3. ✅ If description contains "status" / "state" / "loaded":
   - pattern_items = STATUS VALUES (e.g., "Loaded", "MODIFIED", "Skipped")
   - Example: "Check SPEF status" → pattern_items: ["Loaded", "Skipped"]

4. ✅ If description contains "count" / "number of" / "数量":
   - pattern_items = NUMERIC VALUES or descriptions (e.g., "5", "10 files")
   - Example: "Count design files" → pattern_items: ["5", "10"]

🔍 VALIDATION RULE:
- Read description keyword → Determine semantic level (version/filename/status/count)
- Extract values at MATCHING semantic level from file analysis
- REJECT values that don't match the semantic level

🚫 COMMON MISTAKE - Version vs Filename Confusion:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Description: "List Innovus tool version (e.g., innovus/221/22.11-s119_1)"

❌ WRONG - Using path from example:
pattern_items:
  - "innovus/221/22.11-s119_1"      # ❌ This is a PATH, not a version!
  - "C:\\tools\\innovus\\22.11-s119_1"  # ❌ This is a full path!
  - "innovus.exe"                    # ❌ This is a FILENAME, not a version!

✅ CORRECT - Extract VERSION identifier only:
pattern_items:
  - "22.11-s119_1"                   # ✅ Version identifier
  - "23.10-s200"                     # ✅ Another version
  - "22.1.1-s233"                    # ✅ Version format
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️ Key Insight: Example "innovus/221/22.11-s119_1" shows WHERE to find version,
                NOT what to extract! Extract only the VERSION part: "22.11-s119_1"

====================================================================================
⚠️ STEP 2: Type Configuration MUST Use REAL Examples from File Analysis!
====================================================================================

For ALL Type configurations, you MUST use REAL examples:

1. **pattern_items** (Type 2/3): Golden Values for Matching (NOT Display Format!)
   
   ⚠️ CRITICAL CONCEPT: pattern_items are "golden values" (expected configurations/versions)
   - These are simplified identifiers used for matching logic
   - NOT the complete output format strings from "Display Format" section
   - Extract 2-3 representative golden values from file analysis AT THE CORRECT SEMANTIC LEVEL
   
   **Golden Value Examples:**
   - Version numbers: "22.1.1-s233", "21.1.0-s100"
   - Status indicators: "SPEF: Skipped", "SPEF: Loaded"
   - File identifiers: "design_name.v.gz", "timing.rpt"
   - View/corner names: "func_rcss_0p675v_125c", "test_ffss_0p825v_m40c"
   
   ❌ WRONG (generic placeholders):
   ```yaml
   pattern_items:
     - "TODO: Add pattern"
   ```
   
   ❌ WRONG (using full Display Format):
   ```yaml
   pattern_items:
     - "INFO01: Netlist: /path/to/design.v.gz | SPEF: Skipped (reason)"
     # Problem: This is output format, NOT golden value!
   ```
   
   ✅ CORRECT (simplified golden values from file analysis):
   ```yaml
   pattern_items:
     - "22.1.1-s233"        # Version number
     - "22.1.2-s240"        # Another version
     - "SPEF: Skipped"      # Status indicator
     - "design_top.v.gz"    # File identifier
   ```

2. **waive_items**: REQUIRED for ALL Types with waivers configuration!

   ⚠️ IMPORTANT: waive_items examples are needed for:
   - Type 1 with waivers.value=0 → triggers [WAIVED_AS_INFO] behavior
   - Type 2 with waivers.value=0 → triggers [WAIVED_AS_INFO] behavior  
   - Type 3 with waivers.value>0 → normal waiver with [WAIVER] tag
   - Type 4 with waivers.value>0 → normal waiver with [WAIVER] tag
   
   ❌ WRONG (generic):
   ```yaml
   waive_items:
     - name: "TODO: exception_item"
       reason: "TODO: waiver reason"
   ```
   
   ✅ CORRECT for Type 1/2 (waivers.value=0):
   ```yaml
   waivers:
     value: 0  # Items will be converted to INFO with [WAIVED_AS_INFO]
     waive_items:
       - name: "View 'func_rcss_0p675v_125c_pcss_cmax_pcff3_setup' path_group 'default' setup: WNS=-0.2318ns (40 violations)"
         reason: "Known issue - will be fixed in next release"
   ```
   
   ✅ CORRECT for Type 3/4 (waivers.value>0):
   ```yaml
   waivers:
     value: 2  # Use 2 examples for consistency (same as template)
     waive_items:
       - name: "func_rcss_0p675v_125c_pcss_cmax_pcff3_setup"
         reason: "Waived per design review - non-critical debug path"
       - name: "func_rcff_0p825v_125c_pcff_cmin_pcss3_hold"
         reason: "Waived - timing margin acceptable for this corner"
   ```

   ⚠️ CRITICAL CONSISTENCY REQUIREMENT - waive_items.name MUST Match pattern_items Format!
   
   **Rule 1: Format Consistency**
   - Type 3 waive_items.name MUST use SAME format as Type 2 pattern_items
   - Type 4 waive_items.name MUST use SAME format as checker's violation identifiers
   - DO NOT use full Display Format ("INFO01: xxx") in waive_items.name
   - DO NOT use complete output strings in waive_items.name
   
   **Rule 2: Golden Value Matching**
   - pattern_items are "golden values" (expected configurations/versions)
   - waive_items.name should be "golden values" that match pattern_items
   - Example: If pattern_items = ["version_1.2.3"], then waive_items.name = "version_1.2.3"
   - Example: If pattern_items = ["SPEF: Skipped"], then waive_items.name = "SPEF: Skipped"
   
   **Rule 3: Complete Consistency Between Type 3 and Type 4**
   Type 3 and Type 4 MUST use IDENTICAL waiver examples!
   - SAME number of waive_items (use value: 2 for both)
   - SAME waive_items.name values (use identical names in both Type 3 and Type 4)
   - SAME waive_items.reason text (use identical reasons in both types)
   - Type 3 and Type 4 waiver logic is IDENTICAL - examples must be IDENTICAL!
   
   ⚠️ CRITICAL: Copy Type 3 waive_items to Type 4 EXACTLY:
   - Generate Type 3 waive_items based on pattern_items (2 examples)
   - Use THE EXACT SAME waive_items for Type 4 configuration
   - This ensures consistency and makes it clear that waiver logic is identical
   - Both types should show the same waiver examples in their configurations
   
   Example of CORRECT consistency:
   ```yaml
   # Type 3 configuration
   waivers:
     value: 2
     waive_items:
       - name: "22.11-s119_1"
         reason: "Waived - legacy version approved for this design"
       - name: "SPEF: Skipped"
         reason: "Waived - SPEF not required for post-synthesis check"
   
   # Type 4 configuration - MUST USE IDENTICAL waive_items!
   waivers:
     value: 2
     waive_items:
       - name: "22.11-s119_1"                              # ✅ SAME as Type 3
         reason: "Waived - legacy version approved for this design"  # ✅ SAME as Type 3
       - name: "SPEF: Skipped"                             # ✅ SAME as Type 3
         reason: "Waived - SPEF not required for post-synthesis check"  # ✅ SAME as Type 3
   ```
   
   ❌ WRONG EXAMPLES (Type 3/4 - Multiple Format Violations):
   
   **Wrong Example 1: Using full Display Format (NEVER do this!)**
   ```yaml
   # ❌ WRONG - Using complete output format string
   waive_items:
     - name: "Netlist: /path/to/design.v.gz | SPEF: Skipped (we are writing post-synthesis SDF files)"
       reason: "Waived"
   # Problem: This is the Display Format, NOT the golden value!
   # Should use simplified format matching pattern_items
   ```
   
   **Wrong Example 2: Format mismatch with pattern_items**
   ```yaml
   # Type 2 pattern_items:
   pattern_items:
     - "22.1.1-s233"  # Simplified golden value
   
   # ❌ WRONG Type 3 waive_items - format mismatch!
   waive_items:
     - name: "Version: 22.1.1-s233 found in SPEF header"  # TOO DETAILED!
       reason: "Waived"
   
   # ✅ CORRECT - SAME format as pattern_items
   waive_items:
     - name: "22.1.1-s233"  # Matches pattern_items format
       reason: "Waived - legacy version approved"
   ```
   
   **Wrong Example 3: Using generic error messages**
   ```yaml
   # ❌ WRONG - Generic error messages
   waive_items:
     - name: "ERROR: Tool version not found in setup file"
     - name: "ERROR: Timing violation found"
     - name: "ERROR: Required file missing"
     - name: "ERROR: File path not configured"
   ```
   
   ✅ CORRECT EXAMPLES (Type 3/4 using actual data items):
   ```yaml
   # ✅ CORRECT - Tool version check with ACTUAL versions
   waive_items:
     - name: "quantus/202/20.20.000"  # Actual version string from file
       reason: "Waived - older version approved for this design"
     - name: "innovus/231/23.10-s092_1"  # Another actual version
       reason: "Waived - intermediate version used for debug"
   
   # ✅ CORRECT - STA timing check with ACTUAL violations
   waive_items:
     - name: "View 'func_setup' path_group 'default': WNS=-0.2318ns"
       reason: "Waived - non-critical debug path per design review"
     - name: "View 'func_hold' path_group 'clk_grp': WNS=-0.1234ns"
       reason: "Waived - timing margin acceptable for this corner"
   
   # ✅ CORRECT - File check with ACTUAL file paths
   waive_items:
     - name: "/proj/ip/config/timing.sdc"
       reason: "Waived - using alternative constraint file per team agreement"
     - name: "/proj/ip/data/power.db"
       reason: "Waived - legacy design uses different power format"
   ```
   
   🎯 KEY PRINCIPLE: waiver "name" = ACTUAL DATA ITEM from input files
   - Tool version check → use actual version strings (e.g., "ssv/231/23.12-s092_1")
   - Timing check → use actual violation strings (e.g., "WNS=-0.2318ns")
   - File check → use actual file paths (e.g., "/path/to/file.sdc")
   - Pattern check → use actual pattern values (e.g., "METAL5", "VDD_CORE")
   - NOT error descriptions like "ERROR: version not found"

3. **Sample Output**: Use REAL data from file analysis
   - Show actual item names that would appear in INFO01/ERROR01
   - Match the format defined in "## Output Descriptions"
   - For waivers.value=0: Show [WAIVED_AS_INFO] tag
   - For waivers.value>0: Show [WAIVER] tag

This makes the README a useful reference for developers testing ALL Type configurations!"""

        return prompt
