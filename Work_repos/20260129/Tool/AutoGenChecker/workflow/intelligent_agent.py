"""
Intelligent Agent for Complete Checker Development.

This agent can:
1. Parse YAML config → Extract input_files
2. Analyze actual input files using AI
3. Generate comprehensive README following DEVELOPER_TASK_PROMPTS.md
4. Implement complete checker logic (all 4 types)
5. Fill in parsing logic based on file analysis

Developer only needs to review and fine-tune the AI-generated code.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any, Optional
from datetime import datetime
import logging

# Setup import path
_parent_dir = Path(__file__).parent.parent
if str(_parent_dir) not in sys.path:
    sys.path.insert(0, str(_parent_dir))

try:
    from workflow.pipeline import CheckerGenerationPipeline
    from workflow.models import WorkflowConfig, CheckerArtifacts
    from utils.models import CheckerAgentRequest
    from workflow.mixins import (
        LoggingMixin, FileAnalysisMixin, ReadmeGenerationMixin, 
        CodeGenerationMixin, SelfCheckMixin, FinalReviewMixin,
        TestingMixin
    )
except ImportError:
    from AutoGenChecker.workflow.pipeline import CheckerGenerationPipeline
    from AutoGenChecker.workflow.models import WorkflowConfig, CheckerArtifacts
    from AutoGenChecker.utils.models import CheckerAgentRequest


class IntelligentCheckerAgent(LoggingMixin, FileAnalysisMixin, ReadmeGenerationMixin, CodeGenerationMixin, SelfCheckMixin, FinalReviewMixin, TestingMixin):
    """
    AI-powered agent that generates production-ready checker code.
    
    New 9-Step Workflow:
    Step 1: Load Config
    Step 2: File Analysis
    Step 3: README Generation
    Step 4: README Review [K/E/R]
    Step 5: Code Generation
    Step 6: Self-Check & Fix
    Step 7: Code Testing
    Step 8: Final Review [T/M/O/V/R/F/Q]
    Step 9: Package & Report
    4. AI implements complete code:
       - _parse_files() with real parsing logic
       - All 4 type implementations (_execute_type1/2/3/4)
       - Proper error handling and edge cases
    5. Self-check & Self-fix (automatic validation and correction)
    6. Interactive fix (if auto-fix fails, allow user intervention)
    
    Developer's job: Review, test, and fine-tune (not implement from scratch)
    """
    
    # Default settings for self-check/fix
    DEFAULT_MAX_FIX_ATTEMPTS = 3
    DEFAULT_INTERACTIVE = True
    
    def __init__(
        self,
        item_id: str,
        module: str,
        llm_provider: str = "openai",
        llm_model: str | None = None,
        verbose: bool = True,
        max_fix_attempts: int = DEFAULT_MAX_FIX_ATTEMPTS,
        interactive: bool = DEFAULT_INTERACTIVE,
        skip_testing: bool = False,
        resume_from_step: int | None = None,
        user_hints: str | None = None,  # [Phase 1] Add hints parameter
    ):
        self.item_id = item_id
        self.module = module
        self.llm_provider = llm_provider
        self.llm_model = llm_model
        self.verbose = verbose
        self.max_fix_attempts = max_fix_attempts
        self.interactive = interactive
        self.skip_testing = skip_testing
        self.resume_from_step = resume_from_step
        self.user_hints = user_hints  # [Phase 1] Store hints
        
        # Create LLM agent once and reuse it (to avoid re-authentication)
        self._llm_agent = None
        
        # Cache for resume functionality
        self._cached_config = None
        self._cached_file_analysis = None
        self._cached_readme = None
        self._cached_code = None
        
        # Setup logging and Rich console
        self._setup_logging()
        self._setup_rich_console()
    
    def _load_cached_data(self) -> None:
        """Load cached data from previous run for resume functionality."""
        try:
            from utils.paths import discover_project_paths
        except ImportError:
            from AutoGenChecker.utils.paths import discover_project_paths
        
        paths = discover_project_paths()
        
        # Load README if available
        readme_path = paths.workspace_root / "Check_modules" / self.module / "scripts" / "doc" / f"{self.item_id}_README.md"
        if readme_path.exists():
            import os
            file_mtime = os.path.getmtime(readme_path)
            from datetime import datetime
            mod_time_str = datetime.fromtimestamp(file_mtime).strftime('%Y-%m-%d %H:%M:%S')
            
            with open(readme_path, 'r', encoding='utf-8') as f:
                self._cached_readme = f.read()
            
            print(f"📂 Loaded README from {readme_path}")
            print(f"   Last modified: {mod_time_str} ({len(self._cached_readme)} bytes)")
            if self.verbose:
                print(f"   Preview: {self._cached_readme[:200]}...")
        
        # Load code if available
        code_path = paths.workspace_root / "Check_modules" / self.module / "scripts" / "checker" / f"{self.item_id}.py"
        if code_path.exists():
            import os
            file_mtime = os.path.getmtime(code_path)
            from datetime import datetime
            mod_time_str = datetime.fromtimestamp(file_mtime).strftime('%Y-%m-%d %H:%M:%S')
            
            with open(code_path, 'r', encoding='utf-8') as f:
                self._cached_code = f.read()
            
            print(f"📂 Loaded code from {code_path}")
            print(f"   Last modified: {mod_time_str} ({len(self._cached_code)} bytes)")
            if self.verbose:
                print(f"   Preview: {self._cached_code[:200]}...")
        
        # Load config
        config_path = paths.workspace_root / "Check_modules" / self.module / "inputs" / "items" / f"{self.item_id}.yaml"
        if config_path.exists():
            import yaml
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
            self._cached_config = {
                'item_id': self.item_id,
                'module': self.module,
                'description': config_data.get('description', 'TBD'),
                'input_files': config_data.get('input_files', []),
                'requirements': config_data.get('requirements', {}),
                'waivers': config_data.get('waivers', {}),
                'config_file': str(config_path),
            }
            if self.verbose:
                print(f"📂 Loaded cached config from {config_path}")
    
    def _get_llm_agent(self):
        """Get or create LLM agent (cached to avoid re-authentication)."""
        if self._llm_agent is None:
            try:
                from llm_checker_agent import build_agent_from_provider
            except ImportError:
                from AutoGenChecker.llm_checker_agent import build_agent_from_provider
            
            self._llm_agent = build_agent_from_provider(
                self.llm_provider,
                model=self.llm_model,
            )
        
        return self._llm_agent
    
    def _collect_user_hints_for_readme(self) -> str:
        """
        Collect user hints for README generation at Step 3.
        
        This is called after file analysis (Step 2), so user has seen
        the analysis results and can provide more accurate hints.
        """
        try:
            from workflow.user_interaction import prompt_user_for_hints, load_latest_hints
        except ImportError:
            from AutoGenChecker.workflow.user_interaction import prompt_user_for_hints, load_latest_hints
        
        # First try to load from hints.txt (returns dict with latest/history/count)
        hints_data = load_latest_hints(self.module, self.item_id)
        
        # Always use prompt_user_for_hints - it will handle both cases:
        # - If hints_data exists: show latest + history option
        # - If no hints_data: prompt for new input
        return prompt_user_for_hints(self.item_id, self.module)
    
    def generate_complete_checker(self) -> CheckerArtifacts:
        """
        Generate a complete, production-ready checker with AI assistance.
        
        New 9-Step Workflow:
        Step 1: Load Config
        Step 2: File Analysis
        Step 3: README Generation
        Step 4: README Review [K/E/R]
        Step 5: Code Generation
        Step 6: Self-Check & Fix
        Step 7: Interactive Testing
        Step 8: Final Review [T/M/O/V/R/F/Q]
        Step 9: Package & Report
        
        Resume Logic:
        - resume_from_step <= 6: Executes steps, generates/modifies files
        - resume_from_step = 7: Interactive testing (Type 1/2/3/4)
        - resume_from_step = 8: Directly to final review
        - resume_from_step >= 9: Skips to reporting
        
        Returns:
            CheckerArtifacts with:
            - readme: Comprehensive README with 4 type examples
            - code: Complete implementation with real parsing logic
            - file_analysis: Detailed file format analysis
        """
        # Simple header without Rich panel
        print("\n" + "─"*80)
        print("🤖 AI Agent: 9-Step Checker Development")
        print("─"*80)
        print(f"Item:          {self.item_id}")
        print(f"Module:        {self.module}")
        print(f"LLM:           {self.llm_provider}/{self.llm_model or 'default'}")
        print(f"Interactive:   {'Enabled' if self.interactive else 'Disabled'}")
        if self.resume_from_step:
            print(f"Resume:        Step {self.resume_from_step}")
        print(f"Log:           {self.log_file.name}")
        print("─"*80)
        
        # Load cached data only when needed based on resume step
        # - Step 3+ needs README (if resuming from step 3/4/5...)
        # - Step 5+ needs code (if resuming from step 5/6/7...)
        # - Step 2 should NOT load cached data (we're regenerating it)
        if self.resume_from_step and self.resume_from_step > 2:
            self._load_cached_data()
        
        # Step 1: Load config and extract input_files
        if not self.resume_from_step or self.resume_from_step <= 1:
            config = self._load_and_analyze_config()
            self._cached_config = config
        else:
            config = self._cached_config
        
        # Step 2: AI analyzes actual input files
        if not self.resume_from_step or self.resume_from_step <= 2:
            file_analysis = self._ai_analyze_input_files(config)
            self._cached_file_analysis = file_analysis
        else:
            file_analysis = self._cached_file_analysis
        
        # Step 3: AI generates comprehensive README (MANDATORY - never skip)
        readme_generated_this_run = False
        if not self.resume_from_step or self.resume_from_step <= 3:
            # Collect hints at Step 3 (after file analysis, before README generation)
            if not self.user_hints:
                self.user_hints = self._collect_user_hints_for_readme()
            
            readme = self._ai_generate_readme(config, file_analysis)
            self._cached_readme = readme
            readme_generated_this_run = True
        else:
            # Resume from Step 4+: Must have cached README from previous run
            if not self._cached_readme:
                raise RuntimeError(
                    f"Cannot resume from Step {self.resume_from_step}: README not found. "
                    "README generation is mandatory (Step 3). Please run Steps 1-3 first."
                )
            readme = self._cached_readme
        
        # Step 4: User review & edit README (interactive mode)
        # Show review UI if: (1) interactive enabled AND (2) README was just generated OR resume from step 4
        if self.interactive and (readme_generated_this_run or self.resume_from_step == 4):
            reviewed_readme = self._user_review_readme(readme, config)
            # Check if user chose to regenerate (None return from reset)
            if reviewed_readme is None:
                self._log("User requested README regeneration after reset", "INFO", "🔄")
                readme = self._ai_generate_readme(config, file_analysis)
                self._cached_readme = readme
            else:
                readme = reviewed_readme
                self._cached_readme = readme  # Update cache with user's edits
        
        # Step 5: AI implements complete code
        if not self.resume_from_step or self.resume_from_step <= 5:
            code = self._ai_implement_complete_code(config, file_analysis, readme)
            self._cached_code = code
            # Save code immediately after generation (Step 5)
            self._save_code_to_file(code, config)
        else:
            code = self._cached_code
        
        # Step 6: Self-check & Self-fix loop
        if not self.resume_from_step or self.resume_from_step <= 6:
            code, check_results = self._self_check_and_fix(
                code, config, file_analysis, readme
            )
            self._cached_code = code
            # Save updated code after self-fix (Step 6)
            self._save_code_to_file(code, config)
        else:
            # Skip self-check if resuming from step 7+
            check_results = {'has_issues': False, 'issues': [], 'fix_attempts': 0}
        
        # Step 7: Interactive Testing (comprehensive test suite)
        if not self.skip_testing and self.interactive:
            if not self.resume_from_step or self.resume_from_step <= 7:
                if not check_results.get('has_issues'):
                    print("\n" + "─"*80)
                    print("[Step 7/9] 🧪 Interactive Testing")
                    print("─"*80)
                    self._interactive_testing(config, readme, code)
                else:
                    print("\n⚠️  Skipping Step 7 (Interactive Testing) due to code issues from Step 6")
                    print("   Will proceed to Step 8 (Final Review) for manual fixes")
        
        # Step 8: Final Review (unified interactive review)
        # Execute if: (a) no critical issues OR (b) resuming from Step 8+
        if self.interactive and (not check_results.get('has_issues') or self.resume_from_step and self.resume_from_step >= 8):
            if not self.resume_from_step or self.resume_from_step <= 8:
                print("\n" + "─"*80)
                print("[Step 8/9] 🔍 Final Review")
                print("─"*80)
                code = self._final_review(code, config, file_analysis, readme, None)
        
        # Step 9: Package results
        artifacts = CheckerArtifacts(
            config=config,
            readme=readme,
            code=code,
            file_analysis=file_analysis,
            workflow_steps_completed=[
                "step1_config_load",
                "step2_file_analysis",
                "step3_readme_generation",
                "step4_readme_review",
                "step5_code_generation",
                "step6_self_check_fix",
                "step7_interactive_testing",
                "step8_final_review",
                "step9_package",
            ],
        )
        
        self._print_acceptance_report(artifacts, check_results)
        
        # Final summary with Rich
        self._print_final_summary(artifacts, check_results)
        
        return artifacts
    
    def _load_and_analyze_config(self) -> dict[str, Any]:
        """Load YAML config and extract metadata."""
        if self.verbose:
            print("\n" + "─"*80)
            print("[Step 1/9] 📄 Loading Configuration")
            print("─"*80)
        
        try:
            from utils.paths import discover_project_paths
        except ImportError:
            from AutoGenChecker.utils.paths import discover_project_paths
        
        paths = discover_project_paths()
        config_file = (
            paths.workspace_root / 
            "Check_modules" / 
            self.module / 
            "inputs" / 
            "items" / 
            f"{self.item_id}.yaml"
        )
        
        if not config_file.exists():
            raise FileNotFoundError(f"Config not found: {config_file}")
        
        try:
            import yaml
        except ImportError:
            yaml = None
        
        if yaml:
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
        else:
            config_data = {}
        
        # Extract key fields
        config = {
            'item_id': self.item_id,
            'module': self.module,
            'description': config_data.get('description', 'TBD'),
            'input_files': config_data.get('input_files', []),
            'requirements': config_data.get('requirements', {}),
            'waivers': config_data.get('waivers', {}),
            'config_file': str(config_file),
        }
        
        if self.verbose:
            print(f"  ✅ Loaded: {config_file.name}")
            print(f"  Description: {config['description']}")
            print(f"  Input files: {len(config['input_files'])}")
        
        return config

    # =========================================================================
    # Acceptance Report
    # =========================================================================
    
    def _print_acceptance_report(
        self,
        artifacts: 'CheckerArtifacts',
        check_results: dict[str, Any],
    ) -> None:
        """Print final acceptance report for developer review."""
        print("\n" + "="*80)
        print("📋 ACCEPTANCE REPORT")
        print("="*80)
        
        # File locations
        print("\n📁 Generated Files:")
        print(f"   README: Work/ai_generated/{self.item_id}_README.md")
        print(f"   Code:   Check_modules/{self.module}/scripts/checker/{self.item_id}.py")
        
        # Check results summary
        print("\n🔍 Automatic Check Results:")
        critical_count = check_results.get('critical_count', 0)
        warning_count = check_results.get('warning_count', 0)
        
        if not check_results.get('has_issues') and not check_results.get('has_warnings'):
            print("   ✅ All checks passed")
        elif not check_results.get('has_issues') and check_results.get('has_warnings'):
            print(f"   ✅ No critical issues ({warning_count} warning(s) noted)")
            for issue in check_results.get('issues', [])[:3]:
                if issue.get('severity') != 'critical':
                    print(f"   ⚠️ [{issue['type']}] {issue['message'][:50]}...")
        else:
            print(f"   ❌ {critical_count} CRITICAL issue(s), {warning_count} warning(s)")
            for issue in check_results.get('issues', [])[:5]:
                severity_icon = "❌" if issue.get('severity') == 'critical' else "⚠️"
                print(f"   {severity_icon} [{issue['type']}] {issue['message'][:60]}")
        
        if check_results.get('fix_attempts', 0) > 0:
            print(f"   🔧 Auto-fix attempts: {check_results['fix_attempts']}")
        
        # Stats
        print("\n📊 Statistics:")
        print(f"   README: {len(artifacts.readme)} characters")
        print(f"   Code:   {len(artifacts.code.split(chr(10)))} lines")
        
        # Manual check suggestions
        print("\n👤 Suggested Manual Checks:")
        print("   □ Output Descriptions match the check logic")
        print("   □ Parsing patterns cover all edge cases")
        print("   □ Type 1/2/3/4 behaviors are correct")
        print("   □ Waiver matching logic is accurate")
        print("   □ Error messages are helpful")
        
        # Test commands
        print("\n🧪 Test Commands:")
        print(f"   # Run Type 1 test")
        print(f"   python {self.item_id}.py")
        print(f"   ")
        print(f"   # Create snapshots for regression testing")
        print(f"   python common/regression_testing/create_all_snapshots.py \\")
        print(f"       --modules {self.module} --checkers {self.item_id} --force")
    
    # =========================================================================
    # Step 10: Interactive Testing
    # =========================================================================
    
    def _prompt_for_code_modification(
        self,
        code: str,
        config: dict[str, Any],
        readme: str,
    ) -> str:
        """
        Prompt user to describe code changes and apply AI modification.
        
        Returns:
            Modified code (or original if cancelled/failed)
        """
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
            return code
        
        if not modification_request:
            print("⚠️  Empty request, skipped.")
            return code
        
        print(f"\n🤖 AI is modifying code...")
        
        # Get file_analysis
        try:
            from utils.paths import discover_project_paths
        except ImportError:
            from AutoGenChecker.utils.paths import discover_project_paths
        
        paths = discover_project_paths()
        
        # Load file_analysis from state file
        state_file = paths.workspace_root / "Check_modules" / self.module / "scripts" / "doc" / f"{self.item_id}_state.json"
        file_analysis = {}
        if state_file.exists():
            import json
            with open(state_file, 'r', encoding='utf-8') as f:
                state = json.load(f)
                file_analysis = state.get('file_analysis', {})
        
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
            self._save_code_to_file(modified_code, config)
            print("💾 Changes saved!")
            return modified_code
        else:
            print("❌ Changes discarded.")
            return code
    
    def _interactive_testing(
        self,
        config: dict[str, Any],
        readme: str,
        code: str,
    ) -> None:
        """
        Interactive testing workflow - test all 4 types with real input files.
        
        User decides if output matches expectations.
        """
        # Loop to allow multiple test selections
        while True:
            #print("\n" + "="*80)
            #print("[Step 6] 🧪 Interactive Testing (Optional)")
            #print("="*80)
            print("\nTest your generated checker with different Type configurations:")
            print("  [1] Type 1 (requirements.value=N/A, waivers.value=N/A): Boolean check, no waivers")
            print("  [2] Type 1 (requirements.value=N/A, waivers.value=0): Boolean check with waiver=0")
            print("  [3] Type 2 (requirements.value>0, waivers.value=N/A): Value check, no waivers")
            print("  [4] Type 2 (requirements.value>0, waivers.value=0): Value check with waiver=0")
            print("  [5] Type 3: Value check with waivers")
            print("  [6] Type 4: Boolean check with waivers")
            print("  [A] Run All Types")
            print("  [I] Integration Test (run.ps1 with real YAML)")
            print("  [B] Save Baseline (save current outputs for regression)")
            print("  [R] Regression Test (compare with saved baseline)")
            print("  [Q] Quit testing")
            print("-"*80)
            
            try:
                choice = input("Your choice: ").strip().upper()
            except (EOFError, KeyboardInterrupt):
                print("\n⏭️  Exiting interactive testing...")
                return
            
            if choice in ['Q', 'QUIT', 'EXIT', '']:
                print("⏭️  Exiting interactive testing.")
                return
            
            # Handle Baseline operations
            if choice == 'B':
                self._save_baseline(config)
                continue
            
            if choice == 'R':
                self._run_regression_test(config)
                continue
            
            # Handle Integration Test
            if choice == 'I':
                self._run_integration_test(config, code)
                continue
            
            # Map choices to test configs
            test_map = {
                '1': ('type1_na', 'Type 1 (requirements.value=N/A, waivers.value=N/A)'),
                '2': ('type1_0', 'Type 1 (requirements.value=N/A, waivers.value=0)'),
                '3': ('type2_na', 'Type 2 (requirements.value>0, waivers.value=N/A)'),
                '4': ('type2_0', 'Type 2 (requirements.value>0, waivers.value=0)'),
                '5': ('type3', 'Type 3'),
                '6': ('type4', 'Type 4'),
            }
            
            if choice == 'A':
                # Run all tests in batch mode (no confirmation for each)
                print("\n🚀 Running all 6 test types...")
                test_results = []
                
                # Create unified test report file in test_outputs directory
                try:
                    from utils.paths import discover_project_paths
                except ImportError:
                    from AutoGenChecker.utils.paths import discover_project_paths
                
                paths = discover_project_paths()
                test_output_dir = paths.workspace_root / "Check_modules" / self.module / "test_outputs"
                test_output_dir.mkdir(parents=True, exist_ok=True)
                
                test_report_file = test_output_dir / f"{self.item_id}_test.rpt"
                test_log_file = test_output_dir / f"{self.item_id}_test.log"
                
                # Run all tests and collect outputs
                with open(test_report_file, 'w', encoding='utf-8') as rpt_f, \
                     open(test_log_file, 'w', encoding='utf-8') as log_f:
                    
                    rpt_f.write(f"Test Report: {self.item_id}\n")
                    rpt_f.write("="*80 + "\n\n")
                    
                    log_f.write(f"Test Log: {self.item_id}\n")
                    log_f.write("="*80 + "\n\n")
                    
                    for idx, (test_id, test_name) in enumerate(test_map.values(), 1):
                        result = self._run_single_test(test_id, test_name, config, readme, code, batch_mode=True)
                        
                        # Write to log file (checker log output)
                        log_f.write(f"[Test {idx}/6] {test_name}\n")
                        log_f.write("-"*80 + "\n")
                        log_f.write(f"Test ID: {test_id}\n")
                        log_f.write(f"Status: {result.get('status', 'UNKNOWN')}\n\n")
                        
                        if result.get('log'):
                            log_f.write("Checker Log Output:\n")
                            log_f.write(result['log'])
                        else:
                            log_f.write("(No log output)\n")
                        
                        # Include stderr if present
                        if result.get('stderr'):
                            log_f.write("\n\nSTDERR:\n")
                            log_f.write(result['stderr'])
                        
                        log_f.write("\n" + "="*80 + "\n\n")
                        
                        # Write to report file (checker report output)
                        rpt_f.write(f"[Test {idx}/6] {test_name}\n")
                        rpt_f.write("-"*80 + "\n")
                        rpt_f.write(f"Test ID: {test_id}\n")
                        rpt_f.write(f"Status: {result.get('status', 'UNKNOWN')}\n\n")
                        
                        if result.get('report'):
                            rpt_f.write("Checker Report Output:\n")
                            rpt_f.write(result['report'])
                        else:
                            rpt_f.write("(No report output)\n")
                        
                        rpt_f.write("\n" + "="*80 + "\n\n")
                        
                        test_results.append({
                            'id': test_id,
                            'name': test_name,
                            'status': result.get('status', 'UNKNOWN'),
                            'output_file': str(test_report_file)
                        })
                
                print(f"\n💾 Test report saved: {test_report_file.relative_to(paths.workspace_root)}")
                print(f"💾 Test log saved: {test_log_file.relative_to(paths.workspace_root)}")
                
                # Display summary table
                self._display_test_summary(test_results)
                
                # Ask user if all test results match expectations
                print("\n" + "="*80)
                print("❓ Do ALL test results match your expectations?")
                print("  [Y] Yes - All outputs are correct")
                print("  [N] No - Some tests need fixing")
                print("  [S] Skip judgment")
                print("-"*80)
                
                try:
                    judgment = input("Your judgment: ").strip().upper()
                except (EOFError, KeyboardInterrupt):
                    print("\n⏭️  Judgment skipped.")
                    judgment = 'S'
                
                if judgment == 'Y':
                    print("✅ All tests PASSED - Outputs match expectations!")
                elif judgment == 'N':
                    # Directly enter Modify Code mode
                    code = self._prompt_for_code_modification(code, config, readme)
                else:
                    print("⏭️  Judgment skipped.")
                
                # Ask if user wants to continue with interactive testing
                print("\n" + "-"*80)
                try:
                    continue_choice = input("Continue testing? [Y/n]: ").strip().upper()
                except (EOFError, KeyboardInterrupt):
                    continue_choice = 'N'
                
                if continue_choice not in ['', 'Y', 'YES']:
                    print("⏭️  Exiting interactive testing.")
                    return
                
            elif choice in test_map:
                test_id, test_name = test_map[choice]
                result = self._run_single_test(test_id, test_name, config, readme, code)
                
                # If user judged the test as needing fixes, offer to modify code
                if result.get('status') == 'FAIL':
                    code = self._prompt_for_code_modification(code, config, readme)
                # Loop continues - user can test another type
            else:
                print(f"❌ Invalid choice: {choice}")
    
    def _save_baseline(self, config: dict[str, Any]) -> None:
        """
        Save current test outputs as baseline for regression testing.
        
        Baseline includes:
        - All 6 type test outputs
        - Checker code snapshot
        - README snapshot
        - 6 test YAML configs
        """
        print("\n" + "="*60)
        print("💾 Saving Baseline")
        print("="*60)
        
        try:
            from utils.paths import discover_project_paths
        except ImportError:
            from AutoGenChecker.utils.paths import discover_project_paths
        
        import json
        import shutil
        import yaml
        from datetime import datetime
        
        paths = discover_project_paths()
        
        # Baseline directory
        baseline_dir = paths.workspace_root / "Check_modules" / self.module / "baselines" / self.item_id
        baseline_dir.mkdir(parents=True, exist_ok=True)
        
        # Test configs directory (in baseline)
        test_configs_dir = baseline_dir / "test_configs"
        test_configs_dir.mkdir(parents=True, exist_ok=True)
        
        # Timestamp for this baseline
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 1. Copy current checker code
        checker_src = paths.workspace_root / "Check_modules" / self.module / "scripts" / "checker" / f"{self.item_id}.py"
        if checker_src.exists():
            shutil.copy(checker_src, baseline_dir / f"{self.item_id}.py")
            print(f"  ✅ Checker code saved")
        else:
            print(f"  ⚠️ Checker code not found: {checker_src}")
            return
        
        # 2. Load and copy current README
        readme_src = paths.workspace_root / "Check_modules" / self.module / "scripts" / "doc" / f"{self.item_id}_README.md"
        readme_content = ""
        if readme_src.exists():
            shutil.copy(readme_src, baseline_dir / f"{self.item_id}_README.md")
            readme_content = readme_src.read_text(encoding='utf-8')
            print(f"  ✅ README saved")
        else:
            print(f"  ⚠️ README not found, using empty")
        
        # 3. Generate and save all 6 test configs
        test_types = ['type1_na', 'type1_0', 'type2_na', 'type2_0', 'type3', 'type4']
        test_configs = {}
        
        # Test configs will be saved to test_inputs/items/ for actual execution
        test_inputs_dir = paths.workspace_root / "Check_modules" / self.module / "test_inputs" / "items"
        test_inputs_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"\n  Generating 6 test configurations...")
        for test_id in test_types:
            test_config = self._generate_test_config(test_id, config, readme_content)
            if test_config:
                test_configs[test_id] = test_config
                
                # Save YAML file to test_inputs/items/ (for checker execution)
                yaml_file = test_inputs_dir / f"{self.item_id}_test_{test_id}.yaml"
                with open(yaml_file, 'w', encoding='utf-8') as f:
                    yaml.dump({self.item_id: test_config}, f, default_flow_style=False, allow_unicode=True)
                
                # Also save to baseline for reference
                baseline_yaml = test_configs_dir / f"{self.item_id}_test_{test_id}.yaml"
                with open(baseline_yaml, 'w', encoding='utf-8') as f:
                    yaml.dump({self.item_id: test_config}, f, default_flow_style=False, allow_unicode=True)
                
                print(f"    ✅ {test_id}.yaml saved")
            else:
                print(f"    ⚠️ {test_id}: failed to generate config")
        
        # 4. Run all tests and capture outputs
        test_outputs = {}
        
        print(f"\n  Running all 6 tests to capture outputs...")
        for test_id in test_types:
            if test_id not in test_configs:
                continue
            # Use YAML from test_inputs/items/ for execution
            yaml_file = test_inputs_dir / f"{self.item_id}_test_{test_id}.yaml"
            output = self._run_checker_with_config(yaml_file, paths)
            if output and not output.startswith("Error:"):
                test_outputs[test_id] = output
                # Show brief result
                if "PASS" in output:
                    print(f"    ✅ {test_id}: PASS")
                elif "FAIL" in output:
                    print(f"    ❌ {test_id}: FAIL")
                else:
                    print(f"    📝 {test_id}: captured ({len(output)} chars)")
            else:
                print(f"    ⚠️ {test_id}: {output[:100] if output else 'no output'}")
        
        # 5. Save baseline JSON
        baseline_data = {
            "item_id": self.item_id,
            "module": self.module,
            "timestamp": timestamp,
            "test_configs": test_configs,
            "test_outputs": test_outputs
        }
        
        baseline_file = baseline_dir / "baseline.json"
        with open(baseline_file, 'w', encoding='utf-8') as f:
            json.dump(baseline_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Baseline saved to: {baseline_dir.relative_to(paths.workspace_root)}")
        print(f"   Test configs: {len(test_configs)}/6")
        print(f"   Test outputs: {len(test_outputs)}/6")
    
    def _run_checker_with_config(self, yaml_file: Path, paths) -> str:
        """Run checker with specific YAML config and capture output from log file."""
        import subprocess
        import os
        
        checker_script = paths.workspace_root / "Check_modules" / self.module / "scripts" / "checker" / f"{self.item_id}.py"
        
        if not checker_script.exists():
            return f"Error: Checker not found at {checker_script}"
        
        if not yaml_file.exists():
            return f"Error: Config file not found at {yaml_file}"
        
        # Log file location (where checker writes output)
        log_file = paths.workspace_root / "Check_modules" / self.module / "logs" / f"{self.item_id}.log"
        
        # Clear log file before running
        if log_file.exists():
            log_file.unlink()
        
        # Build environment with TEST_CONFIG
        env = os.environ.copy()
        env['CHECKLIST_ROOT'] = str(paths.workspace_root.parent)
        env['TEST_CONFIG'] = str(yaml_file)  # This is the key - checker reads config from this env var
        
        try:
            # Run checker without arguments - it will read TEST_CONFIG env var
            result = subprocess.run(
                ['python', str(checker_script)],
                cwd=str(paths.workspace_root / "Check_modules" / self.module),
                capture_output=True,
                text=True,
                timeout=60,
                env=env
            )
            
            # Read output from log file (checker writes to log, not stdout)
            if log_file.exists():
                output = log_file.read_text(encoding='utf-8')
                return output
            else:
                # Fallback to stdout/stderr if no log file
                output = result.stdout
                if result.stderr:
                    output += "\n[STDERR]\n" + result.stderr
                return output if output else f"No output (exit code: {result.returncode})"
        except subprocess.TimeoutExpired:
            return "Error: Timeout (60s exceeded)"
        except Exception as e:
            return f"Error: {e}"
    
    def _run_regression_test(self, config: dict[str, Any]) -> None:
        """
        Run regression test - compare current outputs with saved baseline.
        """
        print("\n" + "="*60)
        print("🔍 Regression Test")
        print("="*60)
        
        try:
            from utils.paths import discover_project_paths
        except ImportError:
            from AutoGenChecker.utils.paths import discover_project_paths
        
        import json
        
        paths = discover_project_paths()
        
        # Load baseline
        baseline_dir = paths.workspace_root / "Check_modules" / self.module / "baselines" / self.item_id
        baseline_file = baseline_dir / "baseline.json"
        
        if not baseline_file.exists():
            print(f"❌ No baseline found!")
            print(f"   Please save baseline first with [B] option")
            return
        
        with open(baseline_file, 'r', encoding='utf-8') as f:
            baseline = json.load(f)
        
        print(f"📅 Baseline from: {baseline.get('timestamp', 'unknown')}")
        
        # Use saved test configs from baseline
        test_types = ['type1_na', 'type1_0', 'type2_na', 'type2_0', 'type3', 'type4']
        test_configs_dir = baseline_dir / "test_configs"
        
        results = {"pass": 0, "fail": 0, "skip": 0}
        
        print(f"\n  Comparing outputs...")
        for test_id in test_types:
            baseline_output = baseline.get('test_outputs', {}).get(test_id)
            
            # Run current test using saved config
            yaml_file = test_configs_dir / f"{self.item_id}_test_{test_id}.yaml"
            current_output = self._run_checker_with_config(yaml_file, paths)
            
            if not baseline_output:
                print(f"    ⏭️ {test_id}: no baseline (skipped)")
                results["skip"] += 1
            elif not current_output:
                print(f"    ❌ {test_id}: no current output (FAIL)")
                results["fail"] += 1
            elif self._compare_outputs(baseline_output, current_output):
                print(f"    ✅ {test_id}: PASS")
                results["pass"] += 1
            else:
                print(f"    ❌ {test_id}: DIFF (FAIL)")
                results["fail"] += 1
                # Show diff summary
                self._show_output_diff(test_id, baseline_output, current_output)
        
        # Summary
        print(f"\n" + "-"*60)
        print(f"📊 Regression Results:")
        print(f"   ✅ Pass: {results['pass']}")
        print(f"   ❌ Fail: {results['fail']}")
        print(f"   ⏭️ Skip: {results['skip']}")
        
        if results['fail'] == 0:
            print(f"\n🎉 All regression tests passed!")
        else:
            print(f"\n⚠️ {results['fail']} test(s) have different outputs")
    
    def _compare_outputs(self, baseline: str, current: str) -> bool:
        """Compare two outputs, ignoring timestamps and whitespace differences."""
        import re
        
        def normalize(s):
            # Remove timestamps
            s = re.sub(r'\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}', '[TIMESTAMP]', s)
            # Normalize whitespace
            s = re.sub(r'\s+', ' ', s).strip()
            return s
        
        return normalize(baseline) == normalize(current)
    
    def _show_output_diff(self, test_id: str, baseline: str, current: str) -> None:
        """Show a brief diff between baseline and current output."""
        baseline_lines = baseline.strip().split('\n')
        current_lines = current.strip().split('\n')
        
        # Show first difference
        for i, (b, c) in enumerate(zip(baseline_lines, current_lines)):
            if b != c:
                print(f"      First diff at line {i+1}:")
                print(f"        Baseline: {b[:60]}...")
                print(f"        Current:  {c[:60]}...")
                break
    
    def _run_integration_test(self, config: dict[str, Any], code: str) -> None:
        """
        Run integration test using run.ps1 to verify:
        1. YAML format is correct
        2. Checker can be loaded by run.ps1
        3. End-to-end execution works
        """
        print("\n" + "="*60)
        print("🔗 Integration Test (run.ps1)")
        print("="*60)
        
        try:
            from utils.paths import discover_project_paths
        except ImportError:
            from AutoGenChecker.utils.paths import discover_project_paths
        
        paths = discover_project_paths()
        
        # Step 1: Validate YAML format
        print("\n[1/4] 📝 Validating YAML format...")
        yaml_file = paths.workspace_root / "Check_modules" / self.module / "inputs" / "items" / f"{self.item_id}.yaml"
        
        if not yaml_file.exists():
            print(f"❌ YAML file not found: {yaml_file}")
            return
        
        try:
            import yaml
            with open(yaml_file, 'r', encoding='utf-8') as f:
                yaml_content = yaml.safe_load(f)
            
            # Check required fields
            required_fields = ['description', 'input_files']
            missing_fields = [f for f in required_fields if f not in yaml_content]
            
            if missing_fields:
                print(f"⚠️  Missing required fields: {', '.join(missing_fields)}")
            else:
                print(f"✅ YAML format valid")
                print(f"   Description: {yaml_content.get('description', 'N/A')[:60]}...")
                print(f"   Input files: {len(yaml_content.get('input_files', []))}")
        except Exception as e:
            print(f"❌ YAML parsing error: {e}")
            return
        
        # Step 2: Save checker code
        print("\n[2/4] 💾 Saving checker code...")
        checker_file = paths.workspace_root / "Check_modules" / self.module / "scripts" / "checker" / f"{self.item_id}.py"
        checker_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(checker_file, 'w', encoding='utf-8') as f:
            f.write(code)
        print(f"✅ Checker saved: {checker_file}")
        
        # Step 3: Run via run.ps1
        print("\n[3/4] 🚀 Running via run.ps1...")
        print(f"   Command: ./run.ps1 -root CHECKLIST -stage Initial -check_module {self.module} -check_item {self.item_id}")
        
        work_dir = paths.workspace_root.parent / "Work"
        if not work_dir.exists():
            print(f"⚠️  Work directory not found: {work_dir}")
            print(f"   Creating Work directory...")
            work_dir.mkdir(parents=True, exist_ok=True)
        
        import subprocess
        import sys
        
        try:
            # Construct run.ps1 command
            run_script = paths.workspace_root / "Work" / "run.ps1"
            
            if not run_script.exists():
                print(f"⚠️  run.ps1 not found: {run_script}")
                print(f"   Tip: Make sure run.ps1 exists in CHECKLIST/Work/")
                return
            
            cmd = [
                "powershell.exe",
                "-ExecutionPolicy", "Bypass",
                "-File", str(run_script),
                "-root", "CHECKLIST",
                "-stage", "Initial",
                "-check_module", self.module,
                "-check_item", self.item_id
            ]
            
            print(f"\n   Executing command...")
            result = subprocess.run(
                cmd,
                cwd=str(work_dir),
                capture_output=True,
                text=True,
                timeout=60
            )
            
            # Step 4: Display results
            print("\n[4/4] 📊 Integration Test Results")
            print("="*60)
            
            if result.returncode == 0:
                print("✅ run.ps1 execution: SUCCESS")
            else:
                print(f"❌ run.ps1 execution: FAILED (exit code {result.returncode})")
            
            # Show output
            if result.stdout:
                print("\n📤 STDOUT:")
                print("-"*60)
                # Show last 30 lines to keep it concise
                stdout_lines = result.stdout.strip().split('\n')
                if len(stdout_lines) > 30:
                    print("   ... (showing last 30 lines)")
                    for line in stdout_lines[-30:]:
                        print(f"   {line}")
                else:
                    for line in stdout_lines:
                        print(f"   {line}")
            
            if result.stderr:
                print("\n⚠️  STDERR:")
                print("-"*60)
                for line in result.stderr.strip().split('\n'):
                    print(f"   {line}")
            
            print("="*60)
            
            # Parse results
            if "PASS:" in result.stdout:
                print("✅ Checker result: PASS")
            elif "FAIL:" in result.stdout:
                print("❌ Checker result: FAIL")
            else:
                print("⚠️  Checker result: No PASS/FAIL found in output")
            
            # Check for generated files in Check_modules directory
            print("\n📁 Checking generated files...")
            print("-"*60)
            
            module_dir = paths.workspace_root / "Check_modules" / self.module
            
            # 1. Check report file
            report_file = module_dir / "reports" / f"{self.item_id}.rpt"
            if report_file.exists():
                print(f"✅ Report generated: Check_modules/{self.module}/reports/{self.item_id}.rpt")
                # Show report size and first few lines
                report_size = report_file.stat().st_size
                print(f"   Size: {report_size} bytes")
                with open(report_file, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()[:5]
                    if lines:
                        print(f"   Preview (first 5 lines):")
                        for line in lines:
                            print(f"     {line.rstrip()}")
            else:
                print(f"⚠️  Report not found: {report_file}")
            
            # 2. Check log file
            log_file = module_dir / "logs" / f"{self.item_id}.log"
            if log_file.exists():
                print(f"\n✅ Log generated: Check_modules/{self.module}/logs/{self.item_id}.log")
                log_size = log_file.stat().st_size
                print(f"   Size: {log_size} bytes")
            else:
                print(f"\n⚠️  Log not found: {log_file}")
            
            # 3. Check outputs YAML (module-level, not item-level)
            outputs_yaml = module_dir / "outputs" / f"{self.module}.yaml"
            if outputs_yaml.exists():
                print(f"\n✅ YAML generated: Check_modules/{self.module}/outputs/{self.module}.yaml")
                try:
                    import yaml
                    with open(outputs_yaml, 'r', encoding='utf-8') as f:
                        output_data = yaml.safe_load(f)
                    
                    # Validate YAML structure
                    if output_data:
                        print(f"   Format: Valid YAML")
                        # Check module-level fields
                        if 'module' in output_data:
                            print(f"   module: {output_data['module']}")
                        if 'stage' in output_data:
                            print(f"   stage: {output_data['stage']}")
                        if 'generated_at' in output_data:
                            print(f"   generated_at: {output_data['generated_at']}")
                        
                        # Check if current item exists in check_items
                        if 'check_items' in output_data and self.item_id in output_data['check_items']:
                            item_result = output_data['check_items'][self.item_id]
                            print(f"   {self.item_id}:")
                            print(f"     - executed: {item_result.get('executed', 'N/A')}")
                            print(f"     - status: {item_result.get('status', 'N/A')}")
                            if 'failures' in item_result:
                                print(f"     - failures: {len(item_result['failures'])} item(s)")
                            if 'warnings' in item_result:
                                print(f"     - warnings: {len(item_result['warnings'])} item(s)")
                            if 'infos' in item_result:
                                print(f"     - infos: {len(item_result['infos'])} item(s)")
                        else:
                            print(f"   ⚠️  Item {self.item_id} not found in check_items")
                        
                        # Show total items
                        if 'check_items' in output_data:
                            total_items = len(output_data['check_items'])
                            print(f"   Total check items: {total_items}")
                    else:
                        print(f"   ⚠️  Empty YAML file")
                except Exception as e:
                    print(f"   ⚠️  YAML parsing error: {e}")
            else:
                print(f"\n⚠️  Output YAML not found: {outputs_yaml}")
            
            print("-"*60)
            
            print("\n💡 Integration test completed!")
            print("   This validates that:")
            print("   • YAML format is correct")
            print("   • Checker can be loaded by run.ps1")
            print("   • End-to-end execution works")
            print("   • All output files (report/log/yaml) are generated correctly")
            
        except subprocess.TimeoutExpired:
            print("\n❌ Test timed out after 60 seconds")
        except Exception as e:
            print(f"\n❌ Integration test failed: {e}")
            import traceback
            traceback.print_exc()
    
    def _run_single_test(
        self,
        test_id: str,
        test_name: str,
        config: dict[str, Any],
        readme: str,
        code: str,
        batch_mode: bool = False,
    ) -> dict[str, Any]:
        """
        Run a single test case with user confirmation (unless batch_mode=True).
        
        Returns:
            dict with 'status' (PASS/FAIL/ERROR/SKIPPED) and 'output_file' path
        """
        print("\n" + "-"*80)
        print(f"🧪 Testing: {test_name}")
        print("-"*80)
        
        # Import yaml module (needed for both batch and interactive mode)
        import yaml
        
        # Generate test YAML config
        test_config = self._generate_test_config(test_id, config, readme)
        
        if not test_config:
            print(f"⚠️  Could not generate test config for {test_name}")
            return {'status': 'ERROR', 'output_file': None}
        
        # Display test configuration
        if not batch_mode:
            print("\n📝 Test Configuration:")
            print("```yaml")
            print(yaml.dump({self.item_id: test_config}, default_flow_style=False, allow_unicode=True))
            print("```")
        
        # Save test config to temporary file
        try:
            from utils.paths import discover_project_paths
        except ImportError:
            from AutoGenChecker.utils.paths import discover_project_paths
        
        paths = discover_project_paths()
        test_config_dir = paths.workspace_root / "Check_modules" / self.module / "test_inputs" / "items"
        test_config_dir.mkdir(parents=True, exist_ok=True)
        
        test_config_file = test_config_dir / f"{self.item_id}_test_{test_id}.yaml"
        with open(test_config_file, 'w', encoding='utf-8') as f:
            yaml.dump(test_config, f, default_flow_style=False, allow_unicode=True)
        
        if not batch_mode:
            print(f"\n💾 Test config saved: {test_config_file}")
        
        # Ask if user wants to run the test (skip in batch mode)
        if not batch_mode:
            try:
                run_choice = input("\n▶️  Run this test? [Y/n]: ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                print("\n⏭️  Skipped.")
                return {'status': 'SKIPPED', 'log': '', 'report': '', 'stderr': ''}
            
            if run_choice not in ['', 'y', 'yes']:
                print("⏭️  Test skipped.")
                return {'status': 'SKIPPED', 'log': '', 'report': '', 'stderr': ''}
        
        # Execute the test
        return self._execute_test(test_config_file, test_name, code, batch_mode)
    
    def _execute_test(
        self,
        test_config_file: Path,
        test_name: str,
        code: str,
        batch_mode: bool = False,
    ) -> dict[str, Any]:
        """
        Execute the checker with test config and capture output.
        
        Returns:
            dict with 'status', 'output', 'stderr', 'output_file' path
        """
        if not batch_mode:
            print(f"\n🚀 Running checker with {test_name} config...")
        
        # Save code to temporary location
        try:
            from utils.paths import discover_project_paths
        except ImportError:
            from AutoGenChecker.utils.paths import discover_project_paths
        
        paths = discover_project_paths()
        checker_file = paths.workspace_root / "Check_modules" / self.module / "scripts" / "checker" / f"{self.item_id}.py"
        
        # Save code (no backup - we modify skeleton incrementally)
        with open(checker_file, 'w', encoding='utf-8') as f:
            f.write(code)
        
        # Determine test ID from config file name
        test_id = test_config_file.stem.replace(f"{self.item_id}_test_", "")
        
        # Run the checker with test config
        import subprocess
        import sys
        
        try:
            # Set environment variable to use test config
            import os
            env = os.environ.copy()
            
            # Set CHECKLIST_ROOT if not already set
            if 'CHECKLIST_ROOT' not in env:
                env['CHECKLIST_ROOT'] = str(paths.workspace_root)
            
            # Temporarily replace the original YAML with test YAML
            original_yaml = paths.workspace_root / "Check_modules" / self.module / "inputs" / "items" / f"{self.item_id}.yaml"
            original_yaml_backup = None
            
            if original_yaml.exists():
                import shutil
                original_yaml_backup = original_yaml.with_suffix('.yaml.backup')
                shutil.copy(original_yaml, original_yaml_backup)
            
            # Copy test config to the expected location
            import shutil
            shutil.copy(test_config_file, original_yaml)
            
            # Run checker
            result = subprocess.run(
                [sys.executable, str(checker_file)],
                cwd=paths.workspace_root,
                capture_output=True,
                text=True,
                timeout=30,
                env=env
            )
            
            # Restore original YAML
            if original_yaml_backup and original_yaml_backup.exists():
                shutil.move(original_yaml_backup, original_yaml)
            
            # Read checker output from generated log/report files
            # Checker writes to Check_modules/{module}/logs/{item_id}.log and reports/{item_id}.rpt
            log_file = paths.workspace_root / "Check_modules" / self.module / "logs" / f"{self.item_id}.log"
            report_file = paths.workspace_root / "Check_modules" / self.module / "reports" / f"{self.item_id}.rpt"
            
            # Read both log and report
            checker_log = ""
            checker_report = ""
            
            if log_file.exists():
                checker_log = log_file.read_text(encoding='utf-8')
            
            if report_file.exists():
                checker_report = report_file.read_text(encoding='utf-8')
            
            # In batch/test mode, move logs/reports to test_outputs and clean up
            if batch_mode:
                test_output_dir = paths.workspace_root / "Check_modules" / self.module / "test_outputs"
                test_output_dir.mkdir(parents=True, exist_ok=True)
                
                # Move log/report to test_outputs with test ID prefix
                if log_file.exists():
                    test_log_dest = test_output_dir / f"{self.item_id}_{test_id}.log"
                    shutil.move(str(log_file), str(test_log_dest))
                
                if report_file.exists():
                    test_report_dest = test_output_dir / f"{self.item_id}_{test_id}.rpt"
                    shutil.move(str(report_file), str(test_report_dest))
            
            # Use log for status parsing (log contains PASS/FAIL)
            # Fallback to stdout if no files generated
            status_source = checker_log if checker_log else (checker_report if checker_report else result.stdout)
            
            # Parse check result from output
            status = 'UNKNOWN'
            if result.returncode != 0:
                status = 'ERROR'
            elif "PASS:" in status_source:
                status = 'PASS'
            elif "FAIL:" in status_source:
                status = 'FAIL'
            
            # Display output (only if not batch mode)
            if not batch_mode:
                print("\n" + "="*80)
                print("📊 Test Output:")
                print("="*80)
                print(checker_log if checker_log else status_source)
                if result.stderr:
                    print("\n⚠️  Stderr:")
                    print(result.stderr)
                print("="*80)
                
                # Parse check result from output
                check_status = None
                if "PASS:" in status_source:
                    check_status = "✅ PASS"
                elif "FAIL:" in status_source:
                    check_status = "❌ FAIL"
                
                # Display execution status
                if result.returncode == 0:
                    if check_status:
                        print(f"✅ Execution: SUCCESS | Check Result: {check_status}")
                    else:
                        print(f"✅ Execution: SUCCESS | Check Result: ⚠️ No PASS/FAIL in output")
                else:
                    if check_status:
                        print(f"❌ Execution: FAILED (exit code {result.returncode}) | Check Result: {check_status}")
                    else:
                        print(f"❌ Execution: FAILED (exit code {result.returncode}) | Check Result: ⚠️ Exception/Error")
                print("="*80)
                
                # Ask user if output matches expectation (only in interactive mode)
                print("\n❓ Does the output match your expectations?")
                print("  [Y] Yes - Output is correct")
                print("  [N] No - Needs fixing")
                print("  [S] Skip judgment")
                
                try:
                    judgment = input("Your judgment: ").strip().upper()
                except (EOFError, KeyboardInterrupt):
                    print("\n⏭️  Judgment skipped.")
                    return {'status': status, 'output': result.stdout, 'stderr': result.stderr}
                
                if judgment == 'Y':
                    print("✅ Test PASSED - Output matches expectations!")
                    return {'status': 'PASS', 'log': checker_log, 'report': checker_report, 'stderr': result.stderr}
                elif judgment == 'N':
                    print("⚠️  Test needs fixing.")
                    return {'status': 'FAIL', 'log': checker_log, 'report': checker_report, 'stderr': result.stderr}
                else:
                    print("⏭️  Judgment skipped.")
                    return {'status': status, 'log': checker_log, 'report': checker_report, 'stderr': result.stderr}
            
            # In batch mode, return status with log and report
            return {'status': status, 'log': checker_log, 'report': checker_report, 'stderr': result.stderr}
        
        except subprocess.TimeoutExpired:
            error_msg = "Test timed out after 30 seconds"
            if not batch_mode:
                print(f"\n❌ {error_msg}")
            return {'status': 'ERROR', 'log': error_msg, 'report': '', 'stderr': ''}
        except Exception as e:
            error_msg = f"Test failed: {e}"
            if not batch_mode:
                print(f"\n❌ {error_msg}")
            return {'status': 'ERROR', 'log': error_msg, 'report': '', 'stderr': str(e)}
    
    def _display_test_summary(self, test_results: list[dict]) -> None:
        """Display summary table of all test results."""
        print("\n┌─ Test Results Summary ────────────────────────────────────────────────────┐")
        
        # Count results
        pass_count = sum(1 for r in test_results if r['status'] == 'PASS')
        fail_count = sum(1 for r in test_results if r['status'] == 'FAIL')
        error_count = sum(1 for r in test_results if r['status'] == 'ERROR')
        
        # Print table header
        print(f"│ {'Test Type':<42} │ {'Status':<10} │ {'Output':<15} │")
        print("├────────────────────────────────────────────┼────────────┼─────────────────┤")
        
        # Print each result
        for result in test_results:
            status_symbol = {
                'PASS': '✅ PASS',
                'FAIL': '❌ FAIL',
                'ERROR': '⚠️ ERROR',
                'UNKNOWN': '❓ UNKNWN'
            }.get(result['status'], '❓ UNKNWN')
            
            # Truncate output filename
            if result['output_file']:
                output_short = Path(result['output_file']).name[:13] + ".." if len(Path(result['output_file']).name) > 15 else Path(result['output_file']).name
            else:
                output_short = 'N/A'
            
            test_name = result['name'][:40] + ".." if len(result['name']) > 42 else result['name']
            print(f"│ {test_name:<42} │ {status_symbol:<10} │ {output_short:<15} │")
        
        print("└────────────────────────────────────────────┴────────────┴─────────────────┘")
        print(f"\n📊 Summary: {len(test_results)} Total | ✅ {pass_count} Pass | ❌ {fail_count} Fail | ⚠️ {error_count} Error")
        
        # Show output files location
        if test_results and test_results[0]['output_file']:
            import os
            output_dir = os.path.dirname(test_results[0]['output_file'])
            print(f"📁 Output directory: {output_dir}")
    
    
    def _quick_validate_code(self, code: str) -> dict:
        """
        Quick validation without running the code.
        
        Checks:
        1. Python syntax errors
        2. Known issues from known_issues.yaml
        3. Missing imports
        
        Returns:
            Dict with validation results
        """
        result = {
            'has_errors': False,
            'syntax_errors': [],
            'known_issues': [],
            'can_auto_fix': False
        }
        
        # Check 1: Syntax errors
        try:
            compile(code, '<string>', 'exec')
        except SyntaxError as e:
            result['has_errors'] = True
            result['syntax_errors'].append({
                'line': e.lineno,
                'message': e.msg,
                'text': e.text
            })
        
        # Check 2: Known issues
        try:
            try:
                from utils.code_validator import CodeValidator
            except ImportError:
                from AutoGenChecker.utils.code_validator import CodeValidator
            validator = CodeValidator()
            issues = validator.validate_code(code)
            
            if issues:
                result['has_errors'] = True
                result['known_issues'] = issues
                # Check if any issues have auto-fix suggestions
                result['can_auto_fix'] = any(
                    'correct_usage' in issue for issue in issues
                )
        except Exception:
            pass  # Validator not available
        
        return result
    
    def _offer_fix_options(
        self,
        test_name: str,
        code: str,
        test_config_file: Path,
        test_output: str,
        test_stderr: str,
        exit_code: int,
        validation_result: dict = None,
    ) -> str:
        """
        Offer options to fix failing test.
        
        Enhanced "mixed method" approach with 3 fix modes:
        1. Quick Fix - AI single-shot with enhanced context (README + API + errors)
        2. Deep Fix - Agentic AI with tool-calling (search, read, verify)
        3. Manual Hint - User provides repair direction
        
        Args:
            validation_result: Results from _quick_validate_code()
        
        Returns:
            Fixed code (may be same as input if not fixed)
        """
        # ==========================================================================
        # STEP 1: Display diagnostic information
        # ==========================================================================
        print("\n" + "="*70)
        print("🔍 DIAGNOSTIC ANALYSIS")
        print("="*70)
        
        # Display validation results
        if validation_result and validation_result['has_errors']:
            print("\n⚠️  Code Issues Detected:")
            
            if validation_result['syntax_errors']:
                print(f"\n  📛 Syntax Errors: {len(validation_result['syntax_errors'])}")
                for err in validation_result['syntax_errors'][:3]:
                    print(f"     Line {err['line']}: {err['message']}")
            
            if validation_result['known_issues']:
                print(f"\n  📋 Known Pattern Issues: {len(validation_result['known_issues'])}")
                for issue in validation_result['known_issues'][:3]:
                    print(f"     [{issue['id']}] {issue.get('explanation', 'Issue detected')[:50]}...")
            
            if validation_result['can_auto_fix']:
                print("\n  ✅ Auto-fixable issues found")
        else:
            print("\n✅ Code syntax is valid")
            print("   Issue may be logic-related or API usage error")
        
        # Show error summary
        if test_stderr:
            print(f"\n📛 Error Summary:")
            # Extract key error info
            error_lines = test_stderr.strip().split('\n')
            for line in error_lines[-5:]:  # Show last 5 lines
                if line.strip():
                    print(f"   {line[:80]}")
        
        # ==========================================================================
        # STEP 2: Show fix options with clear descriptions
        # ==========================================================================
        print("\n" + "="*70)
        print("🔧 FIX OPTIONS")
        print("="*70)
        
        # ==========================================================================
        # Build options menu - "mixed method" approach
        # ==========================================================================
        options = []
        option_num = 1
        
        # Option: Auto-fix (only if known issues found)
        has_auto_fix = validation_result and validation_result.get('can_auto_fix', False)
        if has_auto_fix:
            options.append(('auto_fix', option_num))
            print(f"  [{option_num}] ⚡ Auto-fix - Apply known fixes (regex-based, instant)")
            print(f"      → Fixes: {len(validation_result.get('known_issues', []))} known pattern issue(s)")
            option_num += 1
        
        # Option: Quick Fix (enhanced single-shot)
        options.append(('quick_fix', option_num))
        print(f"\n  [{option_num}] 🚀 Quick Fix - AI single-shot with enhanced context")
        print(f"      → Injects: README output specs + API signatures + full error")
        print(f"      → Best for: Parameter errors, API usage mistakes, simple logic bugs")
        option_num += 1
        
        # Option: Deep Fix (agentic)
        options.append(('deep_fix', option_num))
        print(f"\n  [{option_num}] 🤖 Deep Fix - Agentic AI with tool-calling")
        print(f"      → Can: Search codebase, read files, verify fixes, iterate")
        print(f"      → Best for: Complex logic errors, missing context, unknown APIs")
        option_num += 1
        
        # Option: Manual Hint
        options.append(('hint_fix', option_num))
        print(f"\n  [{option_num}] 💡 Manual Hint - Provide repair direction to AI")
        print(f"      → You tell AI: what's wrong and how to fix it")
        print(f"      → Best for: When you know the issue but need AI to implement")
        option_num += 1
        
        # Option: Rerun
        options.append(('rerun', option_num))
        print(f"\n  [{option_num}] 🔄 Rerun - Re-execute test with same code")
        option_num += 1
        
        # Option: Skip
        options.append(('skip', option_num))
        print(f"  [{option_num}] ⏭️  Skip - Continue without fixing")
        
        print("\n" + "-"*70)
        
        try:
            fix_choice = input("Your choice: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n⏭️  Skipped.")
            return code
        
        # ==========================================================================
        # STEP 3: Handle user choice based on options list
        # ==========================================================================
        # Find selected action from options list
        selected_action = None
        try:
            choice_num = int(fix_choice)
            for action, num in options:
                if num == choice_num:
                    selected_action = action
                    break
        except ValueError:
            pass
        
        if not selected_action:
            print("⏭️  Invalid choice, skipping fix.")
            return code
        
        # ----------------------------------------------------------------------
        # Action: Auto-fix known issues
        # ----------------------------------------------------------------------
        if selected_action == 'auto_fix':
            print("\n⚡ Applying auto-fixes...")
            fixed_code = self._auto_fix_known_issues(code, validation_result)
            
            if fixed_code != code:
                print("✅ Auto-fix applied")
                print("\nFixed issues:")
                for issue in validation_result.get('known_issues', [])[:5]:
                    print(f"  • [{issue['id']}] {issue['category']}")
                
                try:
                    rerun = input("\n▶️  Rerun test with fixed code? [Y/n]: ").strip().lower()
                except (EOFError, KeyboardInterrupt):
                    return fixed_code
                
                if rerun in ['', 'y', 'yes']:
                    self._execute_test(test_config_file, test_name, fixed_code)
            else:
                print("⚠️  Auto-fix could not be applied")
            
            return fixed_code
        
        # ----------------------------------------------------------------------
        # Action: Quick Fix (enhanced single-shot AI)
        # ----------------------------------------------------------------------
        elif selected_action == 'quick_fix':
            print("\n🚀 Quick Fix: AI analyzing with enhanced context...")
            print("   → Loading README output descriptions...")
            print("   → Loading API signatures...")
            print("   → Analyzing full error trace...")
            
            fixed_code = self._ai_fix_test_failure(
                code=code,
                test_name=test_name,
                test_output=test_output,
                test_stderr=test_stderr,
                exit_code=exit_code,
                validation_issues=validation_result.get('known_issues', []) if validation_result else [],
                enhanced_context=True  # NEW: Enable enhanced context injection
            )
            
            if fixed_code != code:
                print("✅ Code fixed by AI")
                try:
                    rerun = input("\n▶️  Rerun test with fixed code? [Y/n]: ").strip().lower()
                except (EOFError, KeyboardInterrupt):
                    return fixed_code
                
                if rerun in ['', 'y', 'yes']:
                    self._execute_test(test_config_file, test_name, fixed_code)
            else:
                print("⚠️  AI could not fix the code automatically")
                print("   💡 Try Deep Fix for more thorough analysis")
            
            return fixed_code
        
        # ----------------------------------------------------------------------
        # Action: Deep Fix (Agentic AI with tools)
        # ----------------------------------------------------------------------
        elif selected_action == 'deep_fix':
            print("\n🤖 Deep Fix: Starting Agentic AI with tools...")
            print("   The AI can now:")
            print("   → Search codebase for function definitions")
            print("   → Read files to understand API signatures")
            print("   → Execute tests to verify fixes")
            print("   → Iterate until successful (max 5 attempts)")
            
            fixed_code = self._agentic_fix(
                code=code,
                test_name=test_name,
                test_config_file=test_config_file,
                error_message=f"{test_output}\n{test_stderr}",
            )
            
            return fixed_code
        
        # ----------------------------------------------------------------------
        # Action: Manual Hint
        # ----------------------------------------------------------------------
        elif selected_action == 'hint_fix':
            print("\n💡 Manual Hint Mode")
            print("   Tell the AI what's wrong and how to fix it.")
            print("   Examples:")
            print("   - 'Use waived_base_reason instead of waived_reason'")
            print("   - 'The parsing regex is wrong, path has extra slashes'")
            print("   - 'Need to handle empty violations list'")
            print()
            try:
                hint = input("Your hint: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n⏭️  Skipped.")
                return code
            
            if hint:
                print("\n🔧 AI fixing code with your hint...")
                fixed_code = self._ai_fix_test_failure(
                    code=code,
                    test_name=test_name,
                    test_output=test_output,
                    test_stderr=test_stderr,
                    exit_code=exit_code,
                    user_hint=hint
                )
                
                if fixed_code != code:
                    print("✅ Code fixed by AI")
                    try:
                        rerun = input("\n▶️  Rerun test with fixed code? [Y/n]: ").strip().lower()
                    except (EOFError, KeyboardInterrupt):
                        return fixed_code
                    
                    if rerun in ['', 'y', 'yes']:
                        self._execute_test(test_config_file, test_name, fixed_code)
                else:
                    print("⚠️  AI could not fix the code")
                
                return fixed_code
            else:
                print("   No hint provided, skipping.")
                return code
        
        # ----------------------------------------------------------------------
        # Action: Rerun test
        # ----------------------------------------------------------------------
        elif selected_action == 'rerun':
            print("\n🔄 Re-running test with same code...")
            self._execute_test(test_config_file, test_name, code)
            return code
        
        # ----------------------------------------------------------------------
        # Action: Skip
        # ----------------------------------------------------------------------
        elif selected_action == 'skip':
            print("⏭️  Skipping fix.")
            return code
        
        return code
    
    def _agentic_fix(
        self,
        code: str,
        test_name: str,
        test_config_file: Path,
        error_message: str,
    ) -> str:
        """
        Use Agentic Fixer to fix code with tool-calling capability.
        
        The AI agent can:
        - Search codebase for function definitions
        - Read files to understand API signatures
        - Execute tests to verify fixes
        - Iterate until successful or max attempts reached
        
        Returns:
            Fixed code (or original if fix failed)
        """
        try:
            from workflow.agentic_fixer import AgenticFixer
            from utils.paths import discover_project_paths
        except ImportError:
            from AutoGenChecker.workflow.agentic_fixer import AgenticFixer
            from AutoGenChecker.utils.paths import discover_project_paths
        
        # Get project paths
        paths = discover_project_paths()
        work_dir = paths.workspace_root.parent  # Parent of CHECKLIST folder
        
        # Get checker path
        checker_path = paths.workspace_root / "Check_modules" / self.module / "scripts" / "checker" / f"{self.item_id}.py"
        
        # Build test command
        test_command = f"python \"{test_config_file}\" --test {test_name}"
        
        # Create agentic fixer
        agent = self._get_llm_agent()
        fixer = AgenticFixer(
            work_dir=work_dir,
            llm_client=agent._llm_client,
            max_iterations=5,
            verbose=True
        )
        
        # Run agentic fix
        fixed_code, success, explanation = fixer.fix_code(
            code=code,
            error_message=error_message,
            test_command=test_command,
            test_config_path=test_config_file,
            checker_path=checker_path,
        )
        
        if success:
            print(f"\n✅ Agentic Fix succeeded!")
            print(f"   Explanation: {explanation}")
        else:
            print(f"\n⚠️  Agentic Fix did not fully succeed: {explanation}")
            print("   You may need to manually review and fix the code.")
        
        return fixed_code
    
    def _auto_fix_known_issues(self, code: str, validation_result: dict) -> str:
        """
        Apply automatic fixes for known issues.
        
        Uses regex replacements from known_issues.yaml.
        
        Returns:
            Fixed code
        """
        fixed_code = code
        
        for issue in validation_result.get('known_issues', []):
            if 'correct_usage' not in issue:
                continue
            
            # Simple pattern-based replacement
            # This is a basic implementation - could be enhanced
            pattern = issue.get('pattern', '')
            wrong = issue.get('wrong_usage', '')
            correct = issue.get('correct_usage', '')
            
            if pattern and correct:
                import re
                try:
                    # Try to replace the pattern
                    fixed_code = re.sub(pattern, correct, fixed_code)
                except Exception:
                    pass  # Pattern replacement failed
        
        return fixed_code
    

    # Additional self-check helper methods moved to SelfCheckMixin

    def _extract_readme_output_descriptions_for_code_gen(self, readme: str) -> str:
        """
        Extract and format Output Descriptions from README for code generation prompt.
        
        Returns a formatted string with EXACT descriptions to use in code.
        
        Args:
            readme: Full README content
            
        Returns:
            Formatted string with extracted descriptions or fallback instructions
        """
        import re
        
        # Try to find Output Descriptions section
        start_markers = [
            r'## Output Descriptions',
            r'## Output descriptions',
            r'### Output Descriptions',
        ]
        
        start_pos = -1
        for marker in start_markers:
            match = re.search(marker, readme, re.IGNORECASE)
            if match:
                start_pos = match.start()
                break
        
        if start_pos == -1:
            return """⚠️ Output Descriptions section not found in README!
Use generic descriptions:
- FOUND_DESC = "Items found and verified"
- MISSING_DESC = "Required items not found"  
- FOUND_REASON = "Item meets requirements"
- MISSING_REASON = "Item does not meet requirements"
"""
        
        # Find section end
        section_end_match = re.search(r'\n## ', readme[start_pos + 5:])
        if section_end_match:
            end_pos = start_pos + 5 + section_end_match.start()
        else:
            end_pos = len(readme)
        
        output_section = readme[start_pos:end_pos].strip()
        
        # Extract the Python code block with descriptions
        code_match = re.search(r'```python\n(.*?)\n```', output_section, re.DOTALL)
        if code_match:
            code_content = code_match.group(1)
            
            # Extract key description lines
            extracted_lines = []
            for line in code_content.split('\n'):
                # Match both simple format (found_desc =) and typed format (found_desc_type1_4 =)
                if any(keyword in line.lower() for keyword in [
                    'found_desc', 'missing_desc', 'waived_desc', 'unused_desc',
                    'found_reason', 'missing_reason', 'waived_base_reason', 'waived_reason',
                    'unused_waiver_reason', 'item_desc'
                ]) and '=' in line and not line.strip().startswith('#'):
                    extracted_lines.append(line.strip())
            
            # Extract item format specifications (INFO01/ERROR01/WARN01 format)
            format_section = []
            in_format_section = False
            for line in output_section.split('\n'):
                if 'INFO01/ERROR01/WARN01 Display Format' in line or 'Display Format' in line:
                    in_format_section = True
                elif in_format_section:
                    if line.strip().startswith('##'):  # Next section
                        break
                    if 'Format:' in line or 'Example:' in line or 'occurrences' in line:
                        format_section.append(line.strip())
            
            result = """⚠️⚠️⚠️ CRITICAL: COPY THESE EXACT STRINGS TO CLASS CONSTANTS! ⚠️⚠️⚠️

You MUST define these as class constants and use EXACTLY these values:

```python
class Check_X_X_X_XX(...):
    # COPY THESE EXACT STRINGS FROM README - DO NOT PARAPHRASE!
"""
            result += "\n".join(f"    {line}" for line in extracted_lines)
            result += "\n```\n"
            
            if format_section:
                result += "\n\n⚠️ CRITICAL: Item Name Format (MUST include occurrence count!):\n" + "\n".join(format_section[:10])
            
            result += """\n\n⚠️⚠️⚠️ STRICT RULES:
1. DO NOT MODIFY, PARAPHRASE, or "IMPROVE" these strings!
2. Copy-paste EXACTLY as shown above
3. Use the EXACT variable names (found_desc_type1_4, found_reason_type2_3, etc.)
4. If README has TYPE1_4 and TYPE2_3 variants, define BOTH sets of constants
5. Agent will be penalized for any deviation from README descriptions!
"""
            
            if extracted_lines:
                return result
        
        # Fallback: return first 1000 chars of section
        return output_section[:1000] + "\n\n⚠️ EXTRACT the exact description strings from above and use them!"
    
    def _extract_output_behavior(self, readme: str) -> str:
        """
        Extract the '## Output Behavior' section from README for Type 2/3 logic.
        
        Returns:
            String with check mode (existence_check or status_check) and rationale
        """
        import re
        
        # Find Output Behavior section
        match = re.search(r'## Output Behavior.*?(?=\n## |\Z)', readme, re.DOTALL | re.IGNORECASE)
        if not match:
            return "⚠️ Output Behavior section not found - default to existence_check mode"
        
        section = match.group(0)
        
        # Extract selected mode
        mode_match = re.search(r'Selected Mode.*?:\s*`?(existence_check|status_check)`?', section, re.IGNORECASE)
        if mode_match:
            mode = mode_match.group(1).lower()
            # Return MORE context - include the full section up to 2000 chars to include examples
            return f"⚠️ OUTPUT BEHAVIOR MODE: {mode}\n\n{section[:2000]}"
        
        return f"⚠️ Output Behavior section found but mode not specified:\n{section[:1000]}"
    
    def _extract_output_format(self, readme: str) -> str:
        """
        Extract the '## Output Descriptions' section's Display Format subsection.
        
        This contains the specific output format for INFO01/ERROR01 items.
        
        Returns:
            String with display format specifications
        """
        import re
        
        # Find "Display Format" or "INFO01/ERROR01 Display Format" section
        match = re.search(
            r'### (INFO01/ERROR01 )?Display Format.*?(?=\n### |\n## |\Z)',
            readme,
            re.DOTALL | re.IGNORECASE
        )
        
        if match:
            return f"⚠️ OUTPUT DISPLAY FORMAT (CRITICAL - Use these exact formats!):\n\n{match.group(0)[:1500]}"
        
        return ""
    
    def _extract_readme_output_descriptions(self) -> str:
        """
        Extract the '## Output Descriptions' section from the README file.
        
        This section contains crucial information about:
        - found_reason: Why violations are found
        - missing_reason: Why expected items are missing
        - waived_base_reason: Why items are waived
        - Other description strings for build_complete_output()
        
        Returns:
            String containing the Output Descriptions section, or empty string if not found
        """
        try:
            from utils.paths import discover_project_paths
        except ImportError:
            from AutoGenChecker.utils.paths import discover_project_paths
        
        try:
            # Get README path
            paths = discover_project_paths()
            readme_path = paths.workspace_root / "Check_modules" / self.module / "scripts" / "doc" / f"{self.item_id}_README.md"
            
            if not readme_path.exists():
                return ""
            
            readme_content = readme_path.read_text(encoding='utf-8')
            
            # Extract Output Descriptions section
            import re
            
            # Find the section start
            start_markers = [
                r'## Output Descriptions',
                r'## Output descriptions',
                r'### Output Descriptions',
            ]
            
            start_pos = -1
            for marker in start_markers:
                match = re.search(marker, readme_content, re.IGNORECASE)
                if match:
                    start_pos = match.start()
                    break
            
            if start_pos == -1:
                return ""
            
            # Find the section end (next ## heading or end of file)
            section_end_match = re.search(r'\n## ', readme_content[start_pos + 5:])
            if section_end_match:
                end_pos = start_pos + 5 + section_end_match.start()
            else:
                end_pos = len(readme_content)
            
            output_section = readme_content[start_pos:end_pos].strip()
            
            # Limit size to avoid token overflow
            if len(output_section) > 2000:
                output_section = output_section[:2000] + "\n... (truncated)"
            
            return output_section
            
        except Exception as e:
            return f"(Could not load README Output Descriptions: {e})"