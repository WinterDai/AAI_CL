"""Unified CLI for AutoGenChecker workflow."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

# Add current directory to path for local imports
_current_dir = Path(__file__).parent
if str(_current_dir) not in sys.path:
    sys.path.insert(0, str(_current_dir))

from workflow import CheckerWorkflowOrchestrator


def main(argv: Sequence[str] | None = None) -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="AutoGenChecker - AI-assisted checker generation workflow",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # 🎯 Interactive Mode - Select all parameters with menu (Recommended!)
  python cli.py generate -i
  python cli.py generate --interactive-select
  
  # 🤖 AI Agent Mode - Complete implementation with self-check
  python cli.py generate --item-id IMP-10-0-0-11 --module 10.0_STA_DCD_CHECK --ai-agent
  
  # AI Agent with custom fix attempts and no interactive mode
  python cli.py generate --item-id IMP-10-0-0-11 --module 10.0_STA_DCD_CHECK --ai-agent --max-fix-attempts 5 --no-interactive-fix
  
  # 🔄 Resume from Step 6 (testing only - skip regeneration)
  python cli.py generate --item-id IMP-10-0-0-11 --module 10.0_STA_DCD_CHECK --ai-agent --resume-from-step 6
  
  # 🧠 Autonomous Agent - Self-thinking development
  python cli.py agent --run --max-tasks 5
  python cli.py agent --run --module 10.0_STA_DCD_CHECK
  python cli.py agent --discover  # Just discover pending tasks
  
  # Generate complete checker (README + Code + Test)
  python cli.py generate --item-id IMP-10-0-0-11 --module 10.0_STA_DCD_CHECK
  
  # Generate code only (skip README and test)
  python cli.py generate --item-id IMP-10-0-0-11 --module 10.0_STA_DCD_CHECK --code-only
  
  # Interactive mode (prompts at each step)
  python cli.py generate --item-id IMP-10-0-0-11 --module 10.0_STA_DCD_CHECK --interactive
  
  # Analyze files only (Step 2.5)
  python cli.py analyze --module 10.0_STA_DCD_CHECK --files reports/timing.rpt logs/sta.log
  
  # Generate without LLM (template only)
  python cli.py generate --item-id IMP-10-0-0-11 --module 10.0_STA_DCD_CHECK --no-llm
        """,
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # ===== Generate command =====
    generate_parser = subparsers.add_parser(
        "generate",
        help="Generate checker code (full workflow or code-only)",
    )
    generate_parser.add_argument(
        "-i", "--interactive-select",
        action="store_true",
        help="🎯 Interactive mode - select all parameters with menu (Recommended!)",
    )
    generate_parser.add_argument(
        "--item-id",
        required=False,  # Not required when using --interactive-select or --batch
        help="Checker item ID (e.g., IMP-10-0-0-11)",
    )
    generate_parser.add_argument(
        "--item-ids",
        nargs="+",
        help="Multiple checker item IDs for batch generation (e.g., IMP-16-0-0-01 IMP-16-0-0-02)",
    )
    generate_parser.add_argument(
        "--module",
        required=False,  # Not required when using --interactive-select
        help="Module name (e.g., 10.0_STA_DCD_CHECK)",
    )
    generate_parser.add_argument(
        "--desc",
        help="Optional description override",
    )
    generate_parser.add_argument(
        "--files",
        nargs="+",
        help="Optional input files override",
    )
    generate_parser.add_argument(
        "--ai-agent",
        action="store_true",
        help="🤖 Use Intelligent AI Agent for complete implementation (recommended)",
    )
    generate_parser.add_argument(
        "--max-fix-attempts",
        type=int,
        default=3,
        help="Max auto-fix attempts for self-check (default: 3)",
    )
    generate_parser.add_argument(
        "--no-interactive-fix",
        action="store_true",
        help="Disable interactive fix mode when auto-fix fails",
    )
    generate_parser.add_argument(
        "--code-only",
        action="store_true",
        help="Generate only code, skip README and test",
    )
    generate_parser.add_argument(
        "--readme-hints",
        default=None,
        help="直接提供README hints（跳过交互，用于脚本化）",
    )
    generate_parser.add_argument(
        "--full-test",
        action="store_true",
        help="生成并运行完整的6类测试（自动生成测试配置并执行）",
    )
    generate_parser.add_argument(
        "--save-baseline",
        action="store_true",
        help="将测试结果保存为baseline（用于regression测试）",
    )
    generate_parser.add_argument(
        "--regression",
        action="store_true",
        help="运行regression测试（对比当前结果与baseline）",
    )
    generate_parser.add_argument(
        "--interactive",
        action="store_true",
        help="Interactive mode with prompts",
    )
    generate_parser.add_argument(
        "--no-llm",
        action="store_true",
        help="Generate template without LLM (faster but less accurate)",
    )
    generate_parser.add_argument(
        "--llm-provider",
        default="openai",
        choices=["openai", "anthropic", "jedai"],
        help="LLM provider to use (jedai uses Cadence internal API with LDAP auth)",
    )
    generate_parser.add_argument(
        "--llm-model",
        help="Optional model override",
    )
    generate_parser.add_argument(
        "--output-dir",
        type=Path,
        help="Save artifacts to directory",
    )
    generate_parser.add_argument(
        "--resume-from-step",
        type=int,
        choices=[1, 2, 3, 4, 5, 6, 7, 8, 9],
        help="Resume from specific step (1-6: generation, 7: interactive testing, 8: final review, 9: package)",
    )
    generate_parser.add_argument(
        "--skip-testing",
        action="store_true",
        help="Skip interactive testing phase (Step 6+)",
    )
    
    # ===== Analyze command =====
    analyze_parser = subparsers.add_parser(
        "analyze",
        help="Analyze input files only (Step 2.5)",
    )
    analyze_parser.add_argument(
        "--module",
        required=True,
        help="Module name",
    )
    analyze_parser.add_argument(
        "--files",
        nargs="+",
        required=True,
        help="Input files to analyze",
    )
    
    # ===== Agent command (NEW) =====
    agent_parser = subparsers.add_parser(
        "agent",
        help="🧠 Autonomous agent mode - self-thinking development",
    )
    agent_parser.add_argument(
        "--run",
        action="store_true",
        help="Run autonomous development session",
    )
    agent_parser.add_argument(
        "--discover",
        action="store_true",
        help="Discover pending tasks only (no generation)",
    )
    agent_parser.add_argument(
        "--module",
        help="Focus on specific module (optional)",
    )
    agent_parser.add_argument(
        "--max-tasks",
        type=int,
        default=5,
        help="Maximum tasks to process per session (default: 5)",
    )
    agent_parser.add_argument(
        "--llm-provider",
        default="jedai",
        choices=["jedai", "openai", "anthropic"],
        help="LLM provider (default: jedai for internal use)",
    )
    agent_parser.add_argument(
        "--no-save",
        action="store_true",
        help="Don't auto-save generated outputs",
    )
    
    # Parse arguments
    args = parser.parse_args(argv)
    
    if not args.command:
        parser.print_help()
        return 0
    
    # Execute command
    if args.command == "generate":
        return _command_generate(args)
    elif args.command == "analyze":
        return _command_analyze(args)
    elif args.command == "agent":
        return _command_agent(args)
    
    return 0


def _command_generate(args: argparse.Namespace) -> int:
    """Execute generate command."""
    
    # Handle interactive mode
    if args.interactive_select:
        from utils.interactive_selector import interactive_mode
        
        print("\n" + "🎯"*40)
        print("Starting Interactive Selection Mode...")
        print("🎯"*40)
        
        # Run interactive selection
        selected = interactive_mode()
        
        # Update args with selected values
        args.llm_provider = selected['provider']
        args.llm_model = selected['model']
        args.module = selected['module']
        args.item_id = selected['item_id']
        args.resume_from_step = selected.get('resume_from_step')  # NEW: Get resume step
        
        # Force AI agent mode in interactive (this is the recommended way)
        args.ai_agent = True
        
        print("\n✅ Starting generation with selected parameters...\n")
    
    # Validate required parameters if not in interactive mode
    if not args.interactive_select:
        if not args.module:
            print("❌ Error: --module is required (or use -i for interactive mode)")
            return 1
        if not args.item_id and not args.item_ids:
            print("❌ Error: --item-id or --item-ids is required (or use -i for interactive mode)")
            return 1
    
    # Handle batch mode (--item-ids)
    if args.item_ids:
        return _run_batch_generate(args)
    
    # Auto-discover all items if no item specified
    if not args.item_id:
        discovered_items = _discover_module_items(args.module)
        if discovered_items:
            print(f"📦 Auto-discovered {len(discovered_items)} items in {args.module}")
            args.item_ids = discovered_items
            return _run_batch_generate(args)
        else:
            print(f"❌ Error: No items found in module {args.module}")
            print(f"   Use --item-id or --item-ids to specify items")
            return 1
    
    # Check for AI Agent mode (new intelligent workflow)
    if args.ai_agent:
        return _run_ai_agent_mode(args)
    
    if args.code_only:
        # Fast path: code only
        print(f"\n🚀 Generating code only for {args.item_id}...")
        
        code = CheckerWorkflowOrchestrator.generate_code_only(
            item_id=args.item_id,
            module=args.module,
            use_llm=not args.no_llm,
            llm_provider=args.llm_provider,
        )
        
        # Print or save code
        if args.output_dir:
            output_file = args.output_dir / f"{args.item_id}.py"
            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.write_text(code, encoding='utf-8')
            print(f"\n💾 Code saved to: {output_file}")
        else:
            print("\n" + "="*80)
            print("Generated Code:")
            print("="*80)
            print(code)
        
        return 0
    
    elif args.interactive:
        # Interactive mode
        artifacts = CheckerWorkflowOrchestrator.interactive_generation(
            item_id=args.item_id,
            module=args.module,
        )
    else:
        # Full workflow
        artifacts = CheckerWorkflowOrchestrator.generate_full_checker(
            item_id=args.item_id,
            module=args.module,
            item_desc=args.desc,
            input_files=args.files,
            use_llm=not args.no_llm,
            llm_provider=args.llm_provider,
            llm_model=args.llm_model,
            output_dir=args.output_dir,
        )
    
    # Print summary
    _print_generation_summary(artifacts, args)
    
    return 0


def _command_analyze(args: argparse.Namespace) -> int:
    """Execute analyze command."""
    
    analysis_results = CheckerWorkflowOrchestrator.analyze_files_only(
        module=args.module,
        input_files=args.files,
    )
    
    return 0


def _print_generation_summary(artifacts, args):
    """Print generation summary."""
    print("\n" + "="*80)
    print("✅ Generation Complete!")
    print("="*80)
    
    if artifacts.code:
        lines_of_code = len(artifacts.code.split('\n'))
        print(f"\n📝 Generated Code: {lines_of_code} lines")
    
    if artifacts.readme:
        print(f"📚 Generated README")
    
    if artifacts.file_analysis:
        print(f"📊 Analyzed {len(artifacts.file_analysis)} file(s)")
    
    print(f"\n⏱️  Time taken: {artifacts.time_taken_seconds:.1f} seconds")
    
    if artifacts.manual_refinement_needed:
        print(f"\n⚠️  Manual refinement needed:")
        for item in artifacts.manual_refinement_needed:
            print(f"  📝 {item}")
        print(f"\n💡 Estimated manual work: 10-30 minutes")
    
    # Next steps
    print(f"\n📋 Next Steps:")
    print(f"  1. Review generated code in Check_modules/{args.module}/scripts/checker/")
    print(f"  2. Complete any TODO sections")
    print(f"  3. Test with: python Check_modules/{args.module}/scripts/checker/{args.item_id}.py")
    print(f"  4. Run regression test: python common/regression_testing/create_all_snapshots.py")
    
    print("\n" + "="*80 + "\n")


def _discover_module_items(module: str) -> list:
    """
    Discover all item IDs in a module by scanning inputs/items/*.yaml
    """
    items_dir = Path(f"../CHECKLIST/Check_modules/{module}/inputs/items")
    
    if not items_dir.exists():
        # Try test_inputs
        items_dir = Path(f"../CHECKLIST/Check_modules/{module}/test_inputs/items")
    
    if not items_dir.exists():
        return []
    
    items = []
    for yaml_file in sorted(items_dir.glob("*.yaml")):
        item_id = yaml_file.stem  # e.g., IMP-16-0-0-01
        items.append(item_id)
    
    return items


def _run_batch_generate(args: argparse.Namespace) -> int:
    """
    Run batch generation for multiple checkers.
    """
    item_ids = args.item_ids
    total = len(item_ids)
    
    print(f"\n{'='*60}")
    print(f"🚀 Batch Generation: {total} checkers")
    print(f"{'='*60}")
    print(f"Module: {args.module}")
    print(f"Items: {', '.join(item_ids)}")
    print(f"{'='*60}\n")
    
    results = {"success": [], "failed": []}
    
    for i, item_id in enumerate(item_ids, 1):
        print(f"\n{'='*60}")
        print(f"[{i}/{total}] Processing {item_id}")
        print(f"{'='*60}")
        
        # Create a copy of args with single item_id
        args.item_id = item_id
        
        try:
            if args.ai_agent:
                result = _run_ai_agent_mode(args)
            else:
                # Non-AI agent mode
                artifacts = CheckerWorkflowOrchestrator.generate_full_checker(
                    item_id=item_id,
                    module=args.module,
                    item_desc=args.desc,
                    input_files=args.files,
                    use_llm=not args.no_llm,
                    llm_provider=args.llm_provider,
                    llm_model=args.llm_model,
                    output_dir=args.output_dir,
                )
                result = 0
            
            if result == 0:
                results["success"].append(item_id)
                print(f"\n✅ {item_id} completed successfully")
            else:
                results["failed"].append(item_id)
                print(f"\n❌ {item_id} failed with code {result}")
                
        except Exception as e:
            results["failed"].append(item_id)
            print(f"\n❌ {item_id} failed with error: {e}")
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"📊 Batch Generation Summary")
    print(f"{'='*60}")
    print(f"✅ Success: {len(results['success'])}/{total}")
    if results["success"]:
        print(f"   {', '.join(results['success'])}")
    print(f"❌ Failed:  {len(results['failed'])}/{total}")
    if results["failed"]:
        print(f"   {', '.join(results['failed'])}")
    print(f"{'='*60}\n")
    
    return 0 if not results["failed"] else 1


def _run_ai_agent_mode(args: argparse.Namespace) -> int:
    """
    Run Intelligent AI Agent for complete checker implementation.
    
    This is the recommended mode for developers:
    - AI analyzes actual input files
    - AI generates comprehensive README
    - AI implements complete code (all 4 types + parsing logic)
    - Developer only reviews and fine-tunes
    """
    if args.no_llm:
        print("❌ ERROR: --ai-agent requires LLM (cannot use with --no-llm)")
        return 1
    
    # [Phase 1] Handle hints: CLI parameter has highest priority
    user_hints = None
    resume_step = getattr(args, 'resume_from_step', None)
    
    # Only process hints if not resuming past step 3
    if not resume_step or resume_step <= 3:
        if hasattr(args, 'readme_hints') and args.readme_hints:
            # Direct hints provided via CLI parameter (highest priority)
            user_hints = args.readme_hints
            print(f"📝 Using CLI provided hints: {user_hints[:50]}...")
        # Otherwise, hints will be collected by agent at Step 3
    else:
        # Resuming from step 4+, skip hints
        print(f"ℹ️  Resuming from step {resume_step}, skipping hints phase")
    
    # Import intelligent agent
    try:
        from workflow.intelligent_agent import IntelligentCheckerAgent
    except ImportError:
        from AutoGenChecker.workflow.intelligent_agent import IntelligentCheckerAgent
    
    # Create agent with self-check/fix options
    agent = IntelligentCheckerAgent(
        item_id=args.item_id,
        module=args.module,
        llm_provider=args.llm_provider,
        llm_model=args.llm_model,
        verbose=True,
        max_fix_attempts=args.max_fix_attempts,
        interactive=not args.no_interactive_fix,
        skip_testing=getattr(args, 'skip_testing', False),
        resume_from_step=getattr(args, 'resume_from_step', None),
        user_hints=user_hints,  # Pass CLI hints (or None, agent will collect at Step 3)
    )
    
    # Generate complete checker
    try:
        artifacts = agent.generate_complete_checker()
    except Exception as e:
        print(f"\n❌ AI Agent failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    # Save artifacts to standard locations (not temp directory)
    try:
        from utils.paths import discover_project_paths
    except ImportError:
        from AutoGenChecker.utils.paths import discover_project_paths
    
    paths = discover_project_paths()
    module_dir = paths.workspace_root / "Check_modules" / args.module
    
    # Standard paths
    checker_path = module_dir / "scripts" / "checker" / f"{args.item_id}.py"
    readme_path = module_dir / "scripts" / "doc" / f"{args.item_id}_README.md"
    
    # Ensure directories exist
    checker_path.parent.mkdir(parents=True, exist_ok=True)
    readme_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save README to standard location
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(artifacts.readme)
    print(f"\n💾 README updated: {readme_path}")
    
    # Save code to standard location
    with open(checker_path, 'w', encoding='utf-8') as f:
        f.write(artifacts.code)
    print(f"💾 Checker updated: {checker_path}")
    
    # Optionally save to custom output_dir if specified
    if args.output_dir:
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        import shutil
        shutil.copy(readme_path, output_dir / f"{args.item_id}_README.md")
        shutil.copy(checker_path, output_dir / f"{args.item_id}.py")
        
        # Save analysis
        import json
        analysis_path = output_dir / f"{args.item_id}_file_analysis.json"
        with open(analysis_path, 'w', encoding='utf-8') as f:
            json.dump(artifacts.file_analysis, f, indent=2)
        print(f"💾 Backup saved to: {output_dir}")
    
    # Brief file saved confirmation (acceptance report already printed in agent)
    print(f"\n📁 Files saved successfully. See Acceptance Report above for details.\n")
    
    # [Phase 2-3] Run full test suite if requested
    if hasattr(args, 'full_test') and args.full_test:
        print("\n" + "="*80)
        print("🧪 Running Full Test Suite (6 test types)")
        print("="*80)
        
        try:
            from workflow.test_generator import generate_test_configs
            from workflow.test_runner import run_tests
            from workflow.result_merger import merge_and_report
        except ImportError:
            from AutoGenChecker.workflow.test_generator import generate_test_configs
            from AutoGenChecker.workflow.test_runner import run_tests
            from AutoGenChecker.workflow.result_merger import merge_and_report
        
        # Step 1: Generate test configs
        print("\n📋 Step 1: Generating test configurations...")
        test_configs = generate_test_configs(args.item_id, args.module)
        
        # Step 2: Run all tests
        print(f"\n🧪 Step 2: Running {len(test_configs)} tests...")
        test_results = run_tests(args.item_id, args.module)
        
        # Step 3: Merge results and generate report
        print("\n📊 Step 3: Generating test report...")
        # Find the latest results directory
        test_results_base = paths.workspace_root / "Work" / "test_results" / args.item_id
        latest_results_dir = sorted(test_results_base.glob("*"))[-1]
        
        reports = merge_and_report(latest_results_dir)
        
        print(f"\n✅ Test suite completed!")
        print(f"📄 Report: {reports['markdown'].relative_to(paths.workspace_root)}")
        
        # [Phase 4] Save as baseline if requested
        if hasattr(args, 'save_baseline') and args.save_baseline:
            print("\n💾 Saving test results as baseline...")
            try:
                from workflow.baseline_manager import save_baseline
            except ImportError:
                from AutoGenChecker.workflow.baseline_manager import save_baseline
            
            baseline_path = save_baseline(args.item_id, latest_results_dir)
            print(f"✅ Baseline saved: {baseline_path.relative_to(paths.workspace_root)}")
        
        # [Phase 5] Run regression test if requested
        if hasattr(args, 'regression') and args.regression:
            print("\n🔍 Running regression test...")
            try:
                from workflow.regression_diff import run_regression_test
                from workflow.regression_reporter import generate_regression_report
            except ImportError:
                from AutoGenChecker.workflow.regression_diff import run_regression_test
                from AutoGenChecker.workflow.regression_reporter import generate_regression_report
            
            diff_results = run_regression_test(args.item_id, latest_results_dir)
            regression_report_path = generate_regression_report(args.item_id, diff_results)
            
            print(f"✅ Regression report: {regression_report_path.relative_to(paths.workspace_root)}")
    
    return 0


def _command_agent(args: argparse.Namespace) -> int:
    """Execute autonomous agent command."""
    
    print("\n" + "="*80)
    print("🧠 AUTONOMOUS CHECKER DEVELOPMENT AGENT")
    print("="*80)
    print("The agent will autonomously:")
    print("  1. 🔍 Discover pending checker tasks in the project")
    print("  2. 🧠 Plan and prioritize work")
    print("  3. 💻 Generate complete checker code using AI")
    print("  4. ✅ Validate generated code (syntax + structure)")
    print("  5. 🔄 Auto-fix and retry if validation fails")
    print("  6. 💾 Save outputs for developer review")
    print("="*80 + "\n")
    
    # Import autonomous agent
    try:
        from workflow.autonomous_agent import AutonomousCheckerAgent
    except ImportError:
        from AutoGenChecker.workflow.autonomous_agent import AutonomousCheckerAgent
    
    # Create agent
    agent = AutonomousCheckerAgent(
        llm_provider=args.llm_provider,
        auto_save=not args.no_save,
        verbose=True,
    )
    
    if args.discover:
        # Discovery mode only
        tasks = agent.discover_pending_tasks()
        print(f"\n📋 Found {len(tasks)} pending checker tasks.")
        if tasks:
            print("\nTop 10 pending tasks by priority:")
            for i, task in enumerate(tasks[:10], 1):
                print(f"  {i}. [{task.priority}] {task.item_id} ({task.module})")
                print(f"      {task.description[:60]}...")
        return 0
    
    elif args.run:
        # Full autonomous run
        try:
            report = agent.run_autonomous_session(
                max_tasks=args.max_tasks,
                focus_module=args.module,
            )
            return 0
        except KeyboardInterrupt:
            print("\n\n⚠️  Session interrupted by user.")
            print("Partial progress has been saved.")
            return 1
        except Exception as e:
            print(f"\n❌ Agent session failed: {e}")
            import traceback
            traceback.print_exc()
            return 1
    
    else:
        print("❌ Please specify --run or --discover")
        print("   Example: python cli.py agent --run")
        print("   Example: python cli.py agent --discover")
        return 1


if __name__ == "__main__":
    sys.exit(main())
