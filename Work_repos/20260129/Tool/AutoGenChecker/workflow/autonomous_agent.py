"""
Autonomous Checker Development Agent.

This is a self-thinking agent that can:
1. 🔍 Discover pending checker tasks in the project
2. 🧠 Plan and prioritize work autonomously
3. 💻 Generate checker code using AI
4. ✅ Self-validate generated code
5. 🔄 Iterate and fix issues automatically
6. 📊 Track progress and report status

Developer interaction: Review, approve, and deploy.
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
import traceback
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Setup import path
_parent_dir = Path(__file__).parent.parent
if str(_parent_dir) not in sys.path:
    sys.path.insert(0, str(_parent_dir))

try:
    from workflow.intelligent_agent import IntelligentCheckerAgent
    from workflow.models import CheckerArtifacts
    from llm_clients import create_llm_client, JedAIClient
    from utils.models import LLMCallConfig, LLMResponse
    from utils.paths import discover_project_paths
except ImportError:
    from AutoGenChecker.workflow.intelligent_agent import IntelligentCheckerAgent
    from AutoGenChecker.workflow.models import CheckerArtifacts
    from AutoGenChecker.llm_clients import create_llm_client, JedAIClient
    from AutoGenChecker.utils.models import LLMCallConfig, LLMResponse
    from AutoGenChecker.utils.paths import discover_project_paths


@dataclass
class CheckerTask:
    """Represents a single checker development task."""
    item_id: str
    module: str
    description: str
    priority: int = 5  # 1-10, higher is more important
    status: str = "pending"  # pending, in_progress, completed, failed, review
    input_files: List[str] = field(default_factory=list)
    config_path: Optional[str] = None
    generated_code: Optional[str] = None
    generated_readme: Optional[str] = None
    validation_result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = None


@dataclass
class AgentState:
    """Agent's internal state for tracking progress."""
    pending_tasks: List[CheckerTask] = field(default_factory=list)
    completed_tasks: List[CheckerTask] = field(default_factory=list)
    failed_tasks: List[CheckerTask] = field(default_factory=list)
    current_task: Optional[CheckerTask] = None
    session_start: str = field(default_factory=lambda: datetime.now().isoformat())
    total_checkers_generated: int = 0
    total_validation_passed: int = 0
    total_validation_failed: int = 0


class AutonomousCheckerAgent:
    """
    Self-thinking agent for autonomous checker development.
    
    Capabilities:
    1. Task Discovery: Scan project for pending checker items
    2. Planning: Prioritize tasks based on complexity and dependencies
    3. Execution: Generate complete checker code using AI
    4. Validation: Run syntax checks and basic tests
    5. Iteration: Fix issues and retry if validation fails
    6. Reporting: Track and report progress
    
    Example:
        agent = AutonomousCheckerAgent(llm_provider="jedai")
        agent.run_autonomous_session(max_tasks=5)
    """
    
    def __init__(
        self,
        llm_provider: str = "jedai",
        workspace_root: Optional[Path] = None,
        verbose: bool = True,
        max_retries: int = 2,
        auto_save: bool = True,
    ):
        """
        Initialize the autonomous agent.
        
        Args:
            llm_provider: LLM provider (jedai, openai, anthropic)
            workspace_root: Project root directory
            verbose: Print detailed progress
            max_retries: Max retries for failed tasks
            auto_save: Automatically save generated code
        """
        self.llm_provider = llm_provider
        self.verbose = verbose
        self.max_retries = max_retries
        self.auto_save = auto_save
        
        # Discover project paths
        self.paths = discover_project_paths()
        self.workspace_root = workspace_root or self.paths.workspace_root
        
        # Initialize state
        self.state = AgentState()
        
        # State persistence file
        self.state_file = self.workspace_root / "Work" / "agent_state.json"
        
        if self.verbose:
            self._print_banner()
    
    def _print_banner(self):
        """Print agent initialization banner."""
        print("\n" + "="*80)
        print("🤖 AUTONOMOUS CHECKER DEVELOPMENT AGENT")
        print("="*80)
        print(f"  LLM Provider: {self.llm_provider}")
        print(f"  Workspace: {self.workspace_root}")
        print(f"  Auto-save: {self.auto_save}")
        print(f"  Max retries: {self.max_retries}")
        print("="*80 + "\n")
    
    # =========================================================================
    # PHASE 1: Task Discovery
    # =========================================================================
    
    def discover_pending_tasks(self) -> List[CheckerTask]:
        """
        Scan the project to discover all pending checker tasks.
        
        Looks for:
        - YAML config files in Check_modules/*/inputs/items/
        - Checker code with TODO markers
        - Items without implementation
        """
        if self.verbose:
            print("\n🔍 [Phase 1] Discovering pending tasks...")
        
        tasks = []
        check_modules_dir = self.workspace_root / "Check_modules"
        
        if not check_modules_dir.exists():
            print(f"  ⚠️  Check_modules directory not found: {check_modules_dir}")
            return tasks
        
        for module_dir in check_modules_dir.iterdir():
            if not module_dir.is_dir() or module_dir.name == "common":
                continue
            
            module_name = module_dir.name
            items_dir = module_dir / "inputs" / "items"
            checker_dir = module_dir / "scripts" / "checker"
            
            if not items_dir.exists():
                continue
            
            # Scan YAML configs
            for yaml_file in items_dir.glob("*.yaml"):
                item_id = yaml_file.stem
                checker_file = checker_dir / f"{item_id}.py" if checker_dir.exists() else None
                
                # Check if checker needs implementation
                needs_work = self._check_if_needs_implementation(
                    yaml_file, checker_file
                )
                
                if needs_work:
                    task = self._create_task_from_yaml(yaml_file, module_name)
                    if task:
                        tasks.append(task)
        
        # Sort by priority
        tasks.sort(key=lambda t: t.priority, reverse=True)
        
        if self.verbose:
            print(f"  ✅ Found {len(tasks)} pending tasks")
            for task in tasks[:5]:
                print(f"     - {task.item_id} ({task.module}) - Priority: {task.priority}")
            if len(tasks) > 5:
                print(f"     ... and {len(tasks) - 5} more")
        
        self.state.pending_tasks = tasks
        return tasks
    
    def _check_if_needs_implementation(
        self,
        yaml_file: Path,
        checker_file: Optional[Path],
    ) -> bool:
        """Check if a checker item needs implementation."""
        # No checker file = needs implementation
        if not checker_file or not checker_file.exists():
            return True
        
        # Check for TODO markers in existing code
        try:
            code = checker_file.read_text(encoding='utf-8')
            todo_patterns = [
                r'# TODO:',
                r'pass\s*#\s*TODO',
                r'raise NotImplementedError',
                r'def _parse_files\(self\).*?:\s*\n\s*pass',
            ]
            for pattern in todo_patterns:
                if re.search(pattern, code, re.IGNORECASE | re.DOTALL):
                    return True
        except Exception:
            pass
        
        return False
    
    def _create_task_from_yaml(
        self,
        yaml_file: Path,
        module_name: str,
    ) -> Optional[CheckerTask]:
        """Create a CheckerTask from a YAML config file."""
        try:
            import yaml as yaml_lib
        except ImportError:
            yaml_lib = None
        
        if not yaml_lib:
            return None
        
        try:
            with open(yaml_file, 'r', encoding='utf-8') as f:
                config = yaml_lib.safe_load(f) or {}
            
            # Calculate priority based on config
            priority = self._calculate_priority(config)
            
            return CheckerTask(
                item_id=yaml_file.stem,
                module=module_name,
                description=config.get('description', 'No description'),
                priority=priority,
                input_files=config.get('input_files', []),
                config_path=str(yaml_file),
            )
        except Exception as e:
            if self.verbose:
                print(f"  ⚠️  Error reading {yaml_file}: {e}")
            return None
    
    def _calculate_priority(self, config: Dict[str, Any]) -> int:
        """Calculate task priority based on config complexity."""
        priority = 5  # Default medium priority
        
        # Increase priority for simpler tasks (easier to implement first)
        input_files = config.get('input_files', [])
        if len(input_files) == 1:
            priority += 2  # Single file = easier
        elif len(input_files) == 0:
            priority -= 2  # No files = unclear requirements
        
        # Check requirements complexity
        req = config.get('requirements', {})
        if req.get('value') == 'N/A':
            priority += 1  # Boolean checks are simpler
        
        return min(10, max(1, priority))
    
    # =========================================================================
    # PHASE 2: Planning
    # =========================================================================
    
    def plan_work_session(
        self,
        max_tasks: int = 5,
        focus_module: Optional[str] = None,
    ) -> List[CheckerTask]:
        """
        Plan which tasks to work on in this session.
        
        Uses AI to analyze and prioritize tasks.
        """
        if self.verbose:
            print("\n🧠 [Phase 2] Planning work session...")
        
        tasks = self.state.pending_tasks
        
        # Filter by module if specified
        if focus_module:
            tasks = [t for t in tasks if focus_module in t.module]
        
        # Select top N tasks
        selected = tasks[:max_tasks]
        
        if self.verbose:
            print(f"  📋 Selected {len(selected)} tasks for this session:")
            for i, task in enumerate(selected, 1):
                print(f"     {i}. {task.item_id} - {task.description[:50]}...")
        
        return selected
    
    # =========================================================================
    # PHASE 3: Execution
    # =========================================================================
    
    def execute_task(self, task: CheckerTask) -> CheckerTask:
        """
        Execute a single checker development task.
        
        Uses IntelligentCheckerAgent for AI-powered generation.
        """
        if self.verbose:
            print(f"\n💻 [Phase 3] Executing task: {task.item_id}")
            print(f"   Module: {task.module}")
            print(f"   Description: {task.description}")
        
        task.status = "in_progress"
        self.state.current_task = task
        
        try:
            # Use intelligent agent for generation
            agent = IntelligentCheckerAgent(
                item_id=task.item_id,
                module=task.module,
                llm_provider=self.llm_provider,
                verbose=self.verbose,
            )
            
            artifacts = agent.generate_complete_checker()
            
            task.generated_code = artifacts.code
            task.generated_readme = artifacts.readme
            
            self.state.total_checkers_generated += 1
            
            if self.verbose:
                print(f"   ✅ Code generated: {len(artifacts.code)} chars")
                print(f"   ✅ README generated: {len(artifacts.readme)} chars")
            
        except Exception as e:
            task.status = "failed"
            task.error_message = str(e)
            if self.verbose:
                print(f"   ❌ Generation failed: {e}")
                traceback.print_exc()
            return task
        
        return task
    
    # =========================================================================
    # PHASE 4: Validation
    # =========================================================================
    
    def validate_task(self, task: CheckerTask) -> CheckerTask:
        """
        Validate generated checker code.
        
        Checks:
        - Syntax correctness
        - Required methods exist
        - No obvious errors
        """
        if self.verbose:
            print(f"\n✅ [Phase 4] Validating: {task.item_id}")
        
        if not task.generated_code:
            task.validation_result = {"passed": False, "error": "No code generated"}
            return task
        
        validation = {
            "passed": True,
            "syntax_check": None,
            "structure_check": None,
            "warnings": [],
        }
        
        # Syntax check
        try:
            compile(task.generated_code, f"{task.item_id}.py", "exec")
            validation["syntax_check"] = "PASS"
            if self.verbose:
                print(f"   ✅ Syntax check: PASS")
        except SyntaxError as e:
            validation["syntax_check"] = f"FAIL: {e}"
            validation["passed"] = False
            if self.verbose:
                print(f"   ❌ Syntax check: FAIL - {e}")
        
        # Structure check
        required_patterns = [
            r'class Checker\(BaseChecker\)',
            r'def execute_check\(self\)',
            r'def _parse_files\(self\)',
            r'from base_checker import',
        ]
        
        missing = []
        for pattern in required_patterns:
            if not re.search(pattern, task.generated_code):
                missing.append(pattern)
        
        if missing:
            validation["structure_check"] = f"FAIL: Missing {missing}"
            validation["passed"] = False
            if self.verbose:
                print(f"   ❌ Structure check: Missing required patterns")
        else:
            validation["structure_check"] = "PASS"
            if self.verbose:
                print(f"   ✅ Structure check: PASS")
        
        # Warnings
        if "TODO" in task.generated_code:
            validation["warnings"].append("Code contains TODO markers")
        if "pass" in task.generated_code and "# TODO" not in task.generated_code:
            validation["warnings"].append("Code may have empty pass statements")
        
        task.validation_result = validation
        
        if validation["passed"]:
            task.status = "review"
            self.state.total_validation_passed += 1
        else:
            task.status = "failed"
            self.state.total_validation_failed += 1
        
        return task
    
    # =========================================================================
    # PHASE 5: Iteration (Auto-fix)
    # =========================================================================
    
    def try_fix_task(self, task: CheckerTask) -> CheckerTask:
        """
        Attempt to fix a failed task using AI.
        
        Sends the error to AI and asks for correction.
        """
        if task.status != "failed" or not task.validation_result:
            return task
        
        if self.verbose:
            print(f"\n🔄 [Phase 5] Attempting to fix: {task.item_id}")
        
        error_info = json.dumps(task.validation_result, indent=2)
        
        prompt = f"""The following Python checker code has validation errors.
Please fix the code to resolve these issues.

Original Code:
```python
{task.generated_code}
```

Validation Errors:
{error_info}

Please provide the corrected Python code only, no explanations.
"""
        
        try:
            client = create_llm_client(self.llm_provider)
            config = LLMCallConfig(temperature=0.1, max_tokens=4000)
            response = client.complete(prompt, config=config)
            
            # Extract fixed code
            fixed_code = self._extract_code(response.text)
            if fixed_code:
                task.generated_code = fixed_code
                task.status = "pending"  # Re-validate
                if self.verbose:
                    print(f"   ✅ Fix applied, will re-validate")
            
        except Exception as e:
            if self.verbose:
                print(f"   ❌ Fix attempt failed: {e}")
        
        return task
    
    def _extract_code(self, text: str) -> Optional[str]:
        """Extract Python code from response."""
        match = re.search(r'```python\s*(.+?)\s*```', text, re.DOTALL)
        return match.group(1) if match else None
    
    # =========================================================================
    # PHASE 6: Save & Report
    # =========================================================================
    
    def save_task_output(self, task: CheckerTask) -> Path:
        """Save generated code and README to files."""
        output_dir = self.workspace_root / "Work" / "ai_generated" / task.module
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save code
        code_path = output_dir / f"{task.item_id}.py"
        if task.generated_code:
            code_path.write_text(task.generated_code, encoding='utf-8')
        
        # Save README
        readme_path = output_dir / f"{task.item_id}_README.md"
        if task.generated_readme:
            readme_path.write_text(task.generated_readme, encoding='utf-8')
        
        if self.verbose:
            print(f"   💾 Saved to: {output_dir}")
        
        return output_dir
    
    def generate_report(self) -> str:
        """Generate session report."""
        report = []
        report.append("\n" + "="*80)
        report.append("📊 AUTONOMOUS AGENT SESSION REPORT")
        report.append("="*80)
        report.append(f"Session Start: {self.state.session_start}")
        report.append(f"Session End: {datetime.now().isoformat()}")
        report.append("")
        report.append("📈 Statistics:")
        report.append(f"   Total checkers generated: {self.state.total_checkers_generated}")
        report.append(f"   Validation passed: {self.state.total_validation_passed}")
        report.append(f"   Validation failed: {self.state.total_validation_failed}")
        report.append("")
        
        if self.state.completed_tasks:
            report.append("✅ Completed Tasks (Ready for Review):")
            for task in self.state.completed_tasks:
                report.append(f"   - {task.item_id} ({task.module})")
        
        if self.state.failed_tasks:
            report.append("")
            report.append("❌ Failed Tasks:")
            for task in self.state.failed_tasks:
                report.append(f"   - {task.item_id}: {task.error_message}")
        
        report.append("")
        report.append("📋 Next Steps for Developer:")
        report.append("   1. Review generated code in Work/ai_generated/")
        report.append("   2. Test with actual input files")
        report.append("   3. Fine-tune parsing logic if needed")
        report.append("   4. Move approved checkers to Check_modules/")
        report.append("="*80 + "\n")
        
        return "\n".join(report)
    
    def save_state(self):
        """Save agent state to file for resumption."""
        state_dict = {
            "session_start": self.state.session_start,
            "total_checkers_generated": self.state.total_checkers_generated,
            "pending_tasks": [
                {"item_id": t.item_id, "module": t.module, "status": t.status}
                for t in self.state.pending_tasks
            ],
            "completed_tasks": [
                {"item_id": t.item_id, "module": t.module}
                for t in self.state.completed_tasks
            ],
        }
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.state_file.write_text(json.dumps(state_dict, indent=2), encoding='utf-8')
    
    # =========================================================================
    # Main Entry Point
    # =========================================================================
    
    def run_autonomous_session(
        self,
        max_tasks: int = 5,
        focus_module: Optional[str] = None,
    ) -> str:
        """
        Run a complete autonomous development session.
        
        The agent will:
        1. Discover pending tasks
        2. Plan work for the session
        3. Execute each task (generate code)
        4. Validate generated code
        5. Retry failed tasks
        6. Save outputs and generate report
        
        Args:
            max_tasks: Maximum tasks to process
            focus_module: Focus on specific module (optional)
        
        Returns:
            Session report string
        """
        print("\n" + "🚀"*40)
        print("   STARTING AUTONOMOUS DEVELOPMENT SESSION")
        print("🚀"*40 + "\n")
        
        # Phase 1: Discover
        self.discover_pending_tasks()
        
        if not self.state.pending_tasks:
            return "No pending tasks found. All checkers may be implemented!"
        
        # Phase 2: Plan
        work_queue = self.plan_work_session(max_tasks, focus_module)
        
        if not work_queue:
            return "No tasks selected for this session."
        
        # Process each task
        for i, task in enumerate(work_queue, 1):
            print(f"\n{'='*80}")
            print(f"📌 Task {i}/{len(work_queue)}: {task.item_id}")
            print("="*80)
            
            # Phase 3: Execute
            task = self.execute_task(task)
            
            if task.status == "failed":
                self.state.failed_tasks.append(task)
                continue
            
            # Phase 4: Validate
            task = self.validate_task(task)
            
            # Phase 5: Try fix if failed
            retries = 0
            while task.status == "failed" and retries < self.max_retries:
                retries += 1
                print(f"\n   🔄 Retry {retries}/{self.max_retries}...")
                task = self.try_fix_task(task)
                if task.status == "pending":
                    task = self.execute_task(task)
                    task = self.validate_task(task)
            
            # Phase 6: Save
            if task.status == "review" and self.auto_save:
                self.save_task_output(task)
                task.status = "completed"
                task.completed_at = datetime.now().isoformat()
                self.state.completed_tasks.append(task)
            elif task.status == "failed":
                self.state.failed_tasks.append(task)
        
        # Final report
        report = self.generate_report()
        print(report)
        
        # Save state
        self.save_state()
        
        return report
    
    def run_single_task(
        self,
        item_id: str,
        module: str,
    ) -> CheckerTask:
        """
        Run agent on a single specific task.
        
        Useful for targeted development.
        """
        task = CheckerTask(
            item_id=item_id,
            module=module,
            description="User-specified task",
        )
        
        task = self.execute_task(task)
        task = self.validate_task(task)
        
        if task.status == "failed" and self.max_retries > 0:
            task = self.try_fix_task(task)
            if task.status == "pending":
                task = self.execute_task(task)
                task = self.validate_task(task)
        
        if self.auto_save and task.generated_code:
            self.save_task_output(task)
        
        return task


# =============================================================================
# CLI Entry Point
# =============================================================================

def main():
    """CLI entry point for autonomous agent."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Autonomous Checker Development Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run autonomous session (up to 5 tasks)
  python autonomous_agent.py --run
  
  # Focus on specific module
  python autonomous_agent.py --run --module 10.0_STA_DCD_CHECK
  
  # Process more tasks
  python autonomous_agent.py --run --max-tasks 10
  
  # Single task mode
  python autonomous_agent.py --single --item-id IMP-10-0-0-09 --module 10.0_STA_DCD_CHECK
  
  # Discover only (no generation)
  python autonomous_agent.py --discover
        """,
    )
    
    parser.add_argument("--run", action="store_true", help="Run autonomous session")
    parser.add_argument("--discover", action="store_true", help="Discover pending tasks only")
    parser.add_argument("--single", action="store_true", help="Single task mode")
    parser.add_argument("--item-id", help="Item ID for single task mode")
    parser.add_argument("--module", help="Module name (for filtering or single task)")
    parser.add_argument("--max-tasks", type=int, default=5, help="Max tasks per session")
    parser.add_argument(
        "--llm-provider",
        default="jedai",
        choices=["jedai", "openai", "anthropic"],
        help="LLM provider",
    )
    parser.add_argument("--no-save", action="store_true", help="Don't auto-save outputs")
    
    args = parser.parse_args()
    
    agent = AutonomousCheckerAgent(
        llm_provider=args.llm_provider,
        auto_save=not args.no_save,
    )
    
    if args.discover:
        tasks = agent.discover_pending_tasks()
        print(f"\nFound {len(tasks)} pending tasks.")
        
    elif args.single:
        if not args.item_id or not args.module:
            print("❌ --single requires --item-id and --module")
            return 1
        task = agent.run_single_task(args.item_id, args.module)
        print(f"\nTask status: {task.status}")
        
    elif args.run:
        agent.run_autonomous_session(
            max_tasks=args.max_tasks,
            focus_module=args.module,
        )
    else:
        parser.print_help()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
