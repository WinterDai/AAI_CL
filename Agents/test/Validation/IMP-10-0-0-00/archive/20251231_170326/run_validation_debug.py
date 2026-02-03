# -*- coding: utf-8 -*-
"""
ValidationAgent Full Debug Script

Complete ValidationAgent debug script using:
- test/Check_modules/10.0_STA_DCD_CHECK/inputs/items/IMP-10-0-0-00.yaml
- Standardized output directory structure
- Complete README and path listing

Output to: test/Validation/{item_id}/
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime

# Setup paths
_SCRIPT_DIR = Path(__file__).resolve().parent
_AGENT_DIR = _SCRIPT_DIR.parents[2]  # test/Validation/IMP-10-0-0-00 -> Agent
if str(_AGENT_DIR) not in sys.path:
    sys.path.insert(0, str(_AGENT_DIR))

# Configuration
ITEM_ID = "IMP-10-0-0-00"
OUTPUT_ROOT = _SCRIPT_DIR.parent  # test/Validation/


def print_section(title: str):
    """Print section title"""
    print()
    print("=" * 70)
    print(f"  {title}")
    print("=" * 70)


async def run_validation_debug():
    """Run complete ValidationAgent debug"""
    print_section(f"ValidationAgent Full Debug: {ITEM_ID}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Output Dir: {OUTPUT_ROOT / ITEM_ID}")
    
    # ========================================================================
    # Step 1: Load test data
    # ========================================================================
    print_section("Step 1: Load Test Data")
    
    from agents.validation.test_loader import TestDataLoader, load_dev_item
    from agents.validation.output_manager import ValidationOutputManager
    
    # Initialize loader
    loader = TestDataLoader(agent_root=_AGENT_DIR, use_dev_data=True)
    
    # Check paths
    print(f"Agent Root: {loader.agent_root}")
    print(f"Check Modules Root: {loader.check_modules_root}")
    
    # Load item.yaml
    item_config = loader.load_item_config(ITEM_ID)
    if not item_config:
        print(f"[ERROR] item.yaml not found for {ITEM_ID}")
        return False
    
    print(f"[OK] Loaded item.yaml: {item_config.source_path}")
    print(f"   Description: {item_config.description}")
    print(f"   Requirements: value={item_config.requirements_value}")
    print(f"   Pattern Items: {item_config.pattern_items}")
    print(f"   Waivers: value={item_config.waivers_value}")
    
    # ========================================================================
    # Step 2: Initialize output manager
    # ========================================================================
    print_section("Step 2: Initialize Output Directory")
    
    output_mgr = ValidationOutputManager(OUTPUT_ROOT, ITEM_ID)
    output_mgr.initialize(archive_existing=True)
    
    paths = output_mgr.get_all_paths()
    print("Directory structure created:")
    for name, path in paths.items():
        print(f"  {name}: {path}")
    
    # Copy item.yaml
    item_yaml_path = Path(item_config.source_path)
    output_mgr.save_item_yaml(item_yaml_path)
    print(f"\n[OK] Copied item.yaml to input/")
    
    # ========================================================================
    # Step 3: Load CodeGen output (from Orchestrator test directory)
    # ========================================================================
    print_section("Step 3: Load CodeGenAgent Output")
    
    # Check multiple possible locations
    possible_paths = [
        _AGENT_DIR / "test" / "Ochestrator" / ITEM_ID / "generated_checker.py",
        _AGENT_DIR / "test" / "CodeGen" / ITEM_ID / f"Check_{ITEM_ID.replace('-', '_').replace('IMP_', '')}.py",
    ]
    
    generated_code = None
    item_spec = None
    source_path = None
    
    for path in possible_paths:
        if path.exists():
            source_path = path
            break
    
    if source_path:
        print(f"Found existing CodeGen output: {source_path}")
        with open(source_path, 'r', encoding='utf-8') as f:
            generated_code = f.read()
        print(f"[OK] Loaded checker code ({len(generated_code)} chars)")
        
        # Try to load item_spec
        spec_paths = [
            source_path.parent / "input_item_spec.json",
            source_path.parent / "codegen_debug.json",
        ]
        for spec_path in spec_paths:
            if spec_path.exists():
                with open(spec_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    item_spec = data.get("item_spec", data) if "item_spec" in data else data
                print(f"[OK] Loaded item_spec from {spec_path.name}")
                break
    else:
        print("No existing CodeGen output found, will build item_spec and call CodeGenAgent...")
        
        # Build item_spec (from item_config)
        item_spec = {
            "item_id": item_config.item_id,
            "description": item_config.description,
            "check_module": "IMP",
            "input_files": item_config.input_files,
            "requirements": {
                "value": item_config.requirements_value,
                "pattern_items": item_config.pattern_items,
            },
            "waivers": {
                "value": item_config.waivers_value,
                "waive_items": item_config.waive_items,
            },
        }
        
        # Run CodeGenerationAgent
        from agents.code_generation.agent import CodeGenerationAgent
        
        codegen_output_dir = _AGENT_DIR / "test" / "CodeGen" / ITEM_ID
        codegen_output_dir.mkdir(parents=True, exist_ok=True)
        
        codegen = CodeGenerationAgent(debug_mode=True)
        codegen_result = await codegen.process({
            "item_spec": item_spec,
            "output_dir": str(codegen_output_dir),
        })
        
        if codegen_result.status == "success" and codegen_result.result:
            generated_code = codegen_result.result
            print(f"[OK] CodeGen generated code ({len(generated_code)} chars)")
        else:
            print(f"[ERROR] CodeGen failed: {getattr(codegen_result, 'errors', 'Unknown error')}")
            return False
    
    # Save to output directory
    if generated_code:
        output_mgr.save_generated_code(generated_code)
        print("[OK] Saved generated_checker.py to input/")
    
    if item_spec:
        output_mgr.save_item_spec(item_spec)
        print("[OK] Saved item_spec.json to input/")
    
    # ========================================================================
    # Step 4: Run ValidationAgent
    # ========================================================================
    print_section("Step 4: Run ValidationAgent")
    
    from agents.validation.agent import ValidationAgent
    from agents.validation.models import ValidationInput
    
    # Prepare validation input
    validation_input = ValidationInput(
        generated_code=generated_code,
        item_spec=item_spec or item_config.to_dict(),
        log_samples=None,
    )
    
    # Create ValidationAgent
    validator = ValidationAgent(
        debug_mode=True,
        use_mock_llm=True,  # Use Mock LLM for quick testing
    )
    
    print("Starting validation...")
    start_time = datetime.now()
    
    result = await validator.process({
        "generated_code": generated_code,
        "item_spec": item_spec or item_config.to_dict(),
    })
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    print(f"[OK] Validation completed (duration: {duration:.2f}s)")
    print(f"   Status: {result.status}")
    
    # ========================================================================
    # Step 5: Save results and generate TestCase files
    # ========================================================================
    print_section("Step 5: Save Validation Results")
    
    # Extract data from result.artifacts
    artifacts = result.artifacts or {}
    
    # Save TestCase configs (now a list of dicts)
    test_cases = artifacts.get("test_cases", [])
    for tc in test_cases:
        if isinstance(tc, dict):
            tc_id = tc.get("id", "")
            tc_type = tc.get("type_id", 1)
            tc_direction = tc.get("direction", "positive")
            tc_config = tc.get("config_override", {})
            output_mgr.save_test_case(tc_id, tc_type, tc_direction, tc_config)
    
    print(f"[OK] Saved {len(test_cases)} TestCase configs")
    
    # Save execution results (from reviews)
    reviews = artifacts.get("reviews", [])
    for review in reviews:
        if isinstance(review, dict):
            tc_id = review.get("test_case_id", "")
            actual_output = review.get("actual_output", "N/A")
            expected_output = review.get("blind_expected", "N/A")
            verdict = review.get("verdict", "UNKNOWN")
            
            # Generate log and report
            log_content = f"""[{datetime.now().isoformat()}] TestCase: {tc_id}
Item: {ITEM_ID}
Verdict: {verdict}
Confidence: {review.get("confidence", "N/A")}

Expected (Blind): {expected_output}
Actual Output: {actual_output}

Reasoning:
{review.get("reasoning", "(no reasoning)")}
"""
            log_path = output_mgr.save_execution_log(tc_id, log_content)
            
            report_content = f"""{actual_output}:{ITEM_ID}:{item_config.description}
TestCase: {tc_id}
Expected: {expected_output}
Actual: {actual_output}
Verdict: {verdict}
Confidence: {review.get("confidence", "N/A")}
"""
            report_path = output_mgr.save_execution_report(tc_id, report_content)
            
            # Record execution result
            output_mgr.record_execution_result(
                tc_id=tc_id,
                actual_output=actual_output,
                expected_output=expected_output,
                verdict=verdict,
                log_path=log_path,
                report_path=report_path,
            )
    
    print(f"[OK] Saved {len(reviews)} execution logs and reports")
    
    # Save validation result
    aggregated = artifacts.get("aggregated", {})
    validation_result = {
        "item_id": ITEM_ID,
        "status": result.status,
        "validation_status": artifacts.get("status", "UNKNOWN"),
        "timestamp": datetime.now().isoformat(),
        "duration_seconds": duration,
        "test_case_count": len(test_cases),
        "review_count": len(reviews),
        "statistics": {
            "total": aggregated.get("total_test_cases", 0),
            "correct": aggregated.get("correct_count", 0),
            "incorrect": aggregated.get("incorrect_count", 0),
            "uncertain": aggregated.get("uncertain_count", 0),
            "invalid": aggregated.get("invalid_count", 0),
        },
        "final_verdict": aggregated.get("final_verdict", "UNKNOWN"),
    }

    output_mgr.save_validation_result(validation_result)
    print("[OK] Saved validation_result.json")
    
    # Save validation report
    report_md = artifacts.get("report", "")
    if report_md:
        output_mgr.save_validation_report(report_md)
        print("[OK] Saved validation_report.md")
    
    # Save CodeGen feedback
    feedback = artifacts.get("feedback", {})
    if feedback:
        output_mgr.save_codegen_feedback(feedback)
        print("[OK] Saved feedback_to_codegen.json")
    
    # ========================================================================
    # Step 6: Execute checker.py and collect real outputs
    # ========================================================================
    print_section("Step 6: Execute checker.py (Collect Real Outputs)")
    
    try:
        from agents.validation.checker_executor import CheckerExecutor
        
        executor = CheckerExecutor(agent_root=_AGENT_DIR, use_test_env=True)
        print(f"[INFO] CheckerExecutor initialized")
        print(f"   Agent Root: {executor.agent_root}")
        print(f"   Test Env: {executor.use_test_env}")
        
        # Execute checker.py
        print(f"\n[RUN] Executing checker.py (item_id={ITEM_ID})...")
        exec_result = executor.execute_checker(generated_code, ITEM_ID)
        
        if exec_result.success:
            print(f"[OK] checker.py executed successfully (return_code={exec_result.return_code})")
            print(f"   is_pass: {exec_result.is_pass}")
            
            # Save real log
            if exec_result.log_content:
                log_path = output_mgr.save_checker_log(exec_result.log_content)
                print(f"[OK] Saved real log: {log_path}")
            
            # Save real report
            if exec_result.report_content:
                report_path = output_mgr.save_checker_report(exec_result.report_content)
                print(f"[OK] Saved real report: {report_path}")
            
            # Save real pkl
            if exec_result.check_result:
                pkl_path = output_mgr.save_checker_pkl(exec_result.check_result)
                print(f"[OK] Saved real pkl: {pkl_path}")
        else:
            print(f"[ERROR] checker.py execution failed (return_code={exec_result.return_code})")
            print(f"   stdout: {exec_result.stdout[:500] if exec_result.stdout else '(empty)'}")
            print(f"   stderr: {exec_result.stderr[:500] if exec_result.stderr else '(empty)'}")
            
            # Try to save available outputs even on failure
            if exec_result.log_content:
                log_path = output_mgr.save_checker_log(exec_result.log_content)
                print(f"[WARN] Saved log from failed run: {log_path}")
                
    except ImportError as e:
        print(f"[WARN] Cannot import CheckerExecutor: {e}")
        print("   Skipping checker.py execution step")
    except Exception as e:
        print(f"[ERROR] checker.py execution error: {e}")
        import traceback
        traceback.print_exc()
    
    # ========================================================================
    # Step 7: Generate complete README
    # ========================================================================
    print_section("Step 7: Generate README.md")
    
    readme_path = output_mgr.generate_readme()
    print(f"[OK] Generated: {readme_path}")
    
    # ========================================================================
    # Step 8: Final output
    # ========================================================================
    print_section("Debug Complete")
    
    print(f"Output directory: {output_mgr.item_dir}")
    print()
    print("Generated files:")
    
    # List all files
    def list_files(dir_path: Path, prefix: str = ""):
        for item in sorted(dir_path.iterdir()):
            if item.is_dir():
                print(f"{prefix}📁 {item.name}/")
                list_files(item, prefix + "  ")
            else:
                print(f"{prefix}📄 {item.name}")
    
    list_files(output_mgr.item_dir)
    
    print()
    print(f"View detailed report: {output_mgr.item_dir / 'README.md'}")
    
    return True


if __name__ == "__main__":
    success = asyncio.run(run_validation_debug())
    sys.exit(0 if success else 1)
