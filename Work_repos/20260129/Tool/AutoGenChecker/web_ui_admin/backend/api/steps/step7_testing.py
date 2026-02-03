"""
Step 7: Interactive Testing API.

Test checker with all 6 Type configurations (matching CLI workflow).
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import traceback
from pathlib import Path

router = APIRouter()


# Test type definitions matching CLI's 6 test types
# Names match CLI format: Type N (requirements.value=X, waivers.value=Y)
TEST_TYPES = {
    'type1_na': {
        'name': 'Type 1 (requirements.value=N/A, waivers.value=N/A)',
        'desc': 'Boolean check, no waivers',
        'requirements_value': 'N/A',
        'waivers_value': 'N/A'
    },
    'type1_0': {
        'name': 'Type 1 (requirements.value=N/A, waivers.value=0)',
        'desc': 'Boolean check with waiver=0',
        'requirements_value': 'N/A',
        'waivers_value': '0'
    },
    'type2_na': {
        'name': 'Type 2 (requirements.value>0, waivers.value=N/A)',
        'desc': 'Value check, no waivers',
        'requirements_value': '>0',
        'waivers_value': 'N/A'
    },
    'type2_0': {
        'name': 'Type 2 (requirements.value>0, waivers.value=0)',
        'desc': 'Value check with waiver=0',
        'requirements_value': '>0',
        'waivers_value': '0'
    },
    'type3': {
        'name': 'Type 3 (requirements.value>0, waivers.value>0)',
        'desc': 'Value check with waivers',
        'requirements_value': '>0',
        'waivers_value': '>0'
    },
    'type4': {
        'name': 'Type 4 (requirements.value=N/A, waivers.value>0)',
        'desc': 'Boolean check with waivers',
        'requirements_value': 'N/A',
        'waivers_value': '>0'
    }
}


class TestRequest(BaseModel):
    """Request model for testing"""
    module: str
    item_id: str
    code: str
    config: dict
    readme: str = ""
    test_type: str  # 'type1_na', 'type1_0', 'type2_na', 'type2_0', 'type3', 'type4'


class TestResponse(BaseModel):
    """Response model for testing"""
    status: str
    test_passed: bool = False
    check_result: str = "UNKNOWN"  # PASS/FAIL/ERROR/UNKNOWN
    output: Optional[str] = None
    log_output: Optional[str] = None
    report_output: Optional[str] = None
    stderr: Optional[str] = None
    error: Optional[str] = None
    execution_time: Optional[float] = None
    test_config: Optional[dict] = None


class AllTestsRequest(BaseModel):
    """Request model for running all tests"""
    module: str
    item_id: str
    code: str
    config: dict
    readme: str = ""


class AllTestsResponse(BaseModel):
    """Response model for all tests"""
    status: str
    results: Dict[str, Any] = {}
    summary: Dict[str, int] = {}
    test_log: List[str] = []
    report_file: Optional[str] = None
    log_file: Optional[str] = None


@router.get("/test-types")
async def get_test_types():
    """Get all available test types"""
    return {"test_types": TEST_TYPES}


@router.post("/run-test", response_model=TestResponse)
async def run_test(request: TestRequest):
    """
    Run interactive test for specific type.
    
    Tests (6 types matching CLI):
    - type1_na: Boolean check (N/A requirements, N/A waivers)
    - type1_0: Boolean check (N/A requirements, 0 waivers)  
    - type2_na: Value check (requirements>0, N/A waivers)
    - type2_0: Value check (requirements>0, 0 waivers)
    - type3: Value check with waivers (requirements>0, waivers>0)
    - type4: Boolean check with waivers (N/A requirements, waivers>0)
    
    Returns:
        TestResponse with test results
    """
    try:
        from workflow.intelligent_agent import IntelligentCheckerAgent
        import time
        import subprocess
        import sys
        import shutil
        import yaml
        
        try:
            from utils.paths import discover_project_paths
        except ImportError:
            from AutoGenChecker.utils.paths import discover_project_paths
        
        paths = discover_project_paths()
        
        # Create agent
        agent = IntelligentCheckerAgent(
            item_id=request.item_id,
            module=request.module,
            verbose=False,
            interactive=False
        )
        
        start_time = time.time()
        
        # Debug: Log the incoming config
        print(f"[DEBUG] Step 7 run_test called for {request.test_type}")
        print(f"[DEBUG] request.config keys: {request.config.keys() if request.config else 'None'}")
        print(f"[DEBUG] request.config.input_files: {request.config.get('input_files', 'NOT FOUND')}")
        
        # Generate test config
        test_config = agent._generate_test_config(
            test_id=request.test_type,
            config=request.config,
            readme=request.readme
        )
        
        print(f"[DEBUG] Generated test_config: {test_config}")
        
        if not test_config:
            return TestResponse(
                status="error",
                test_passed=False,
                check_result="ERROR",
                error=f"Could not generate test config for {request.test_type}"
            )
        
        # Save test config to temporary file (flat format matching original YAML)
        test_config_dir = paths.workspace_root / "Check_modules" / request.module / "test_inputs" / "items"
        test_config_dir.mkdir(parents=True, exist_ok=True)
        
        test_config_file = test_config_dir / f"{request.item_id}_test_{request.test_type}.yaml"
        
        # Convert input_files paths back to ${CHECKLIST_ROOT} format for portability
        portable_input_files = []
        workspace_root_str = str(paths.workspace_root).replace('\\', '/')
        for input_file in test_config.get('input_files', []):
            input_file_str = str(input_file).replace('\\', '/')
            # Replace absolute path with ${CHECKLIST_ROOT} variable
            if workspace_root_str in input_file_str:
                portable_path = input_file_str.replace(workspace_root_str, '${CHECKLIST_ROOT}')
                portable_input_files.append(portable_path)
            elif input_file_str.startswith('${CHECKLIST_ROOT}'):
                # Already in portable format
                portable_input_files.append(input_file_str)
            else:
                # Relative path - prepend ${CHECKLIST_ROOT}
                portable_input_files.append(f'${{CHECKLIST_ROOT}}/{input_file_str.lstrip("/")}')
        
        # Update test_config with portable paths
        test_config['input_files'] = portable_input_files
        
        # Save as flat format (no item_id/module at root, just the config fields)
        # This matches the format in README examples
        with open(test_config_file, 'w', encoding='utf-8') as f:
            yaml.dump(test_config, f, default_flow_style=False, allow_unicode=True)
        
        # Save code to checker location
        checker_file = paths.workspace_root / "Check_modules" / request.module / "scripts" / "checker" / f"{request.item_id}.py"
        checker_file.parent.mkdir(parents=True, exist_ok=True)
        with open(checker_file, 'w', encoding='utf-8') as f:
            f.write(request.code)
        
        # Backup and replace original YAML
        original_yaml = paths.workspace_root / "Check_modules" / request.module / "inputs" / "items" / f"{request.item_id}.yaml"
        original_yaml_backup = None
        
        if original_yaml.exists():
            original_yaml_backup = original_yaml.with_suffix('.yaml.backup')
            shutil.copy(original_yaml, original_yaml_backup)
        
        original_yaml.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(test_config_file, original_yaml)
        
        # Run checker
        import os
        env = os.environ.copy()
        if 'CHECKLIST_ROOT' not in env:
            env['CHECKLIST_ROOT'] = str(paths.workspace_root)
        
        try:
            result = subprocess.run(
                [sys.executable, str(checker_file)],
                cwd=paths.workspace_root,
                capture_output=True,
                text=True,
                timeout=60,
                env=env
            )
        finally:
            # Restore original YAML
            if original_yaml_backup and original_yaml_backup.exists():
                shutil.move(original_yaml_backup, original_yaml)
        
        execution_time = time.time() - start_time
        
        # Read checker output files
        log_file = paths.workspace_root / "Check_modules" / request.module / "logs" / f"{request.item_id}.log"
        report_file = paths.workspace_root / "Check_modules" / request.module / "reports" / f"{request.item_id}.rpt"
        
        checker_log = ""
        checker_report = ""
        
        if log_file.exists():
            checker_log = log_file.read_text(encoding='utf-8')
        
        if report_file.exists():
            checker_report = report_file.read_text(encoding='utf-8')
        
        # Move outputs to test_outputs directory
        test_output_dir = paths.workspace_root / "Check_modules" / request.module / "test_outputs"
        test_output_dir.mkdir(parents=True, exist_ok=True)
        
        if log_file.exists():
            test_log_dest = test_output_dir / f"{request.item_id}_{request.test_type}.log"
            shutil.move(str(log_file), str(test_log_dest))
        
        if report_file.exists():
            test_report_dest = test_output_dir / f"{request.item_id}_{request.test_type}.rpt"
            shutil.move(str(report_file), str(test_report_dest))
        
        # Determine check result
        status_source = checker_log if checker_log else (checker_report if checker_report else result.stdout)
        
        check_result = 'UNKNOWN'
        test_passed = False
        
        if result.returncode != 0:
            check_result = 'ERROR'
        elif "PASS:" in status_source:
            check_result = 'PASS'
            test_passed = True
        elif "FAIL:" in status_source:
            check_result = 'FAIL'
        
        return TestResponse(
            status="success",
            test_passed=test_passed,
            check_result=check_result,
            output=result.stdout,
            log_output=checker_log,
            report_output=checker_report,
            stderr=result.stderr if result.stderr else None,
            execution_time=execution_time,
            test_config=test_config
        )
        
    except Exception as e:
        error_msg = f"Test execution failed: {str(e)}"
        print(f"[ERROR] {error_msg}")
        traceback.print_exc()
        
        return TestResponse(
            status="error",
            test_passed=False,
            check_result="ERROR",
            error=error_msg
        )


@router.post("/run-all-tests", response_model=AllTestsResponse)
async def run_all_tests(request: AllTestsRequest):
    """
    Run all 6 type tests (matching CLI's "Run All Types" option).
    
    Returns:
        AllTestsResponse with all results and summary
    """
    try:
        results = {}
        
        # Test log format matching CLI output
        test_log = []
        
        passed = 0
        failed = 0
        errors = 0
        
        for idx, (test_type, test_info) in enumerate(TEST_TYPES.items(), 1):
            test_req = TestRequest(
                module=request.module,
                item_id=request.item_id,
                code=request.code,
                config=request.config,
                readme=request.readme,
                test_type=test_type
            )
            
            result = await run_test(test_req)
            results[test_type] = result.model_dump()
            
            # Update stats
            exec_time = result.execution_time or 0
            if result.check_result == 'PASS':
                passed += 1
            elif result.check_result == 'FAIL':
                failed += 1
            else:
                errors += 1
        
        # Generate log file content (matching CLI format)
        try:
            from utils.paths import discover_project_paths
        except ImportError:
            from AutoGenChecker.utils.paths import discover_project_paths
        
        paths = discover_project_paths()
        test_output_dir = paths.workspace_root / "Check_modules" / request.module / "test_outputs"
        test_output_dir.mkdir(parents=True, exist_ok=True)
        
        test_report_file = test_output_dir / f"{request.item_id}_test.rpt"
        test_log_file = test_output_dir / f"{request.item_id}_test.log"
        
        # Write test log file (CLI format with actual checker outputs)
        with open(test_log_file, 'w', encoding='utf-8') as log_f:
            log_f.write(f"Test Log: {request.item_id}\n")
            log_f.write("=" * 80 + "\n\n")
            
            for idx, (test_type, result_dict) in enumerate(results.items(), 1):
                test_info = TEST_TYPES[test_type]
                log_f.write(f"[Test {idx}/6] {test_info['name']}\n")
                log_f.write("-" * 80 + "\n")
                log_f.write(f"Test ID: {test_type}\n")
                log_f.write(f"Status: {result_dict.get('check_result', 'UNKNOWN')}\n\n")
                
                if result_dict.get('log_output'):
                    log_f.write("Checker Log Output:\n")
                    log_f.write(result_dict['log_output'])
                else:
                    log_f.write("(No log output)\n")
                
                # Include stderr if present
                if result_dict.get('stderr'):
                    log_f.write("\n\nSTDERR:\n")
                    log_f.write(result_dict['stderr'])
                
                log_f.write("\n" + "=" * 80 + "\n\n")
        
        # Write test report file (CLI format with actual checker reports)
        with open(test_report_file, 'w', encoding='utf-8') as rpt_f:
            rpt_f.write(f"Test Report: {request.item_id}\n")
            rpt_f.write("=" * 80 + "\n\n")
            
            for idx, (test_type, result_dict) in enumerate(results.items(), 1):
                test_info = TEST_TYPES[test_type]
                rpt_f.write(f"[Test {idx}/6] {test_info['name']}\n")
                rpt_f.write("-" * 80 + "\n")
                rpt_f.write(f"Test ID: {test_type}\n")
                rpt_f.write(f"Status: {result_dict.get('check_result', 'UNKNOWN')}\n\n")
                
                if result_dict.get('report_output'):
                    rpt_f.write("Checker Report Output:\n")
                    rpt_f.write(result_dict['report_output'])
                else:
                    rpt_f.write("(No report output)\n")
                
                rpt_f.write("\n" + "=" * 80 + "\n\n")
        
        # Generate display log for frontend (summary format)
        display_log = [
            "─" * 60,
            "[Step 7/9] 🧪 Interactive Testing",
            "─" * 60,
            "",
            "🚀 Running all 6 test types...",
            ""
        ]
        
        for idx, (test_type, result_dict) in enumerate(results.items(), 1):
            test_info = TEST_TYPES[test_type]
            exec_time = result_dict.get('execution_time', 0) or 0
            check_result = result_dict.get('check_result', 'UNKNOWN')
            
            if check_result == 'PASS':
                display_log.append(f"[Test {idx}/6] {test_info['name']}")
                display_log.append(f"    ✅ PASS ({exec_time:.2f}s)")
            elif check_result == 'FAIL':
                display_log.append(f"[Test {idx}/6] {test_info['name']}")
                display_log.append(f"    ❌ FAIL ({exec_time:.2f}s)")
            else:
                display_log.append(f"[Test {idx}/6] {test_info['name']}")
                display_log.append(f"    ⚠️ ERROR: {result_dict.get('error', 'Unknown error')}")
            
            display_log.append("")
        
        # Summary
        display_log.append("─" * 60)
        display_log.append("📊 Test Summary:")
        display_log.append(f"    Total:  6")
        display_log.append(f"    Passed: {passed} ✅")
        display_log.append(f"    Failed: {failed} ❌")
        display_log.append(f"    Errors: {errors} ⚠️")
        display_log.append("─" * 60)
        
        if failed == 0 and errors == 0:
            display_log.append("✅ All tests passed!")
        else:
            display_log.append(f"⚠️ {failed + errors} test(s) need attention")
        
        return AllTestsResponse(
            status="success",
            results=results,
            summary={
                'total': 6,
                'passed': passed,
                'failed': failed,
                'errors': errors
            },
            test_log=display_log,
            report_file=str(test_report_file.relative_to(paths.workspace_root)),
            log_file=str(test_log_file.relative_to(paths.workspace_root))
        )
        
    except Exception as e:
        error_msg = f"All tests failed: {str(e)}"
        print(f"[ERROR] {error_msg}")
        traceback.print_exc()
        
        return AllTestsResponse(
            status="error",
            test_log=[f"❌ Error: {error_msg}"]
        )


class IntegrationTestRequest(BaseModel):
    """Request model for integration test"""
    module: str
    item_id: str
    code: str


class IntegrationTestResponse(BaseModel):
    """Response model for integration test"""
    status: str
    steps: List[Dict[str, Any]] = []
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    return_code: Optional[int] = None
    checker_result: Optional[str] = None
    generated_files: Dict[str, Any] = {}
    error: Optional[str] = None


@router.post("/integration-test", response_model=IntegrationTestResponse)
async def run_integration_test(request: IntegrationTestRequest):
    """
    Run integration test using run.ps1 (Windows) or run.csh (Linux).
    
    Validates:
    1. YAML format is correct
    2. Checker can be loaded by run script
    3. End-to-end execution works
    4. All output files (report/log/yaml) are generated correctly
    
    Returns:
        IntegrationTestResponse with step-by-step results
    """
    try:
        import subprocess
        import sys
        import platform
        import yaml
        import os
        
        try:
            from utils.paths import discover_project_paths
        except ImportError:
            from AutoGenChecker.utils.paths import discover_project_paths
        
        paths = discover_project_paths()
        steps = []
        
        # Step 1: Validate YAML format
        step1 = {"name": "Validating YAML format", "status": "running"}
        yaml_file = paths.workspace_root / "Check_modules" / request.module / "inputs" / "items" / f"{request.item_id}.yaml"
        
        if not yaml_file.exists():
            step1["status"] = "error"
            step1["message"] = f"YAML file not found: {yaml_file}"
            steps.append(step1)
            return IntegrationTestResponse(
                status="error",
                steps=steps,
                error=f"YAML file not found: {yaml_file}"
            )
        
        try:
            with open(yaml_file, 'r', encoding='utf-8') as f:
                yaml_content = yaml.safe_load(f)
            
            required_fields = ['description', 'input_files']
            missing_fields = [f for f in required_fields if f not in yaml_content]
            
            if missing_fields:
                step1["status"] = "warning"
                step1["message"] = f"Missing fields: {', '.join(missing_fields)}"
            else:
                step1["status"] = "success"
                step1["message"] = f"YAML valid - {len(yaml_content.get('input_files', []))} input files"
            steps.append(step1)
        except Exception as e:
            step1["status"] = "error"
            step1["message"] = f"YAML parsing error: {e}"
            steps.append(step1)
            return IntegrationTestResponse(
                status="error",
                steps=steps,
                error=str(e)
            )
        
        # Step 2: Save checker code
        step2 = {"name": "Saving checker code", "status": "running"}
        checker_file = paths.workspace_root / "Check_modules" / request.module / "scripts" / "checker" / f"{request.item_id}.py"
        checker_file.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(checker_file, 'w', encoding='utf-8') as f:
                f.write(request.code)
            step2["status"] = "success"
            step2["message"] = f"Saved to {checker_file.name}"
            steps.append(step2)
        except Exception as e:
            step2["status"] = "error"
            step2["message"] = str(e)
            steps.append(step2)
            return IntegrationTestResponse(
                status="error",
                steps=steps,
                error=str(e)
            )
        
        # Step 3: Run via run.ps1/run.csh
        step3 = {"name": "Running integration test", "status": "running"}
        work_dir = paths.workspace_root / "Work"
        
        if not work_dir.exists():
            work_dir.mkdir(parents=True, exist_ok=True)
        
        is_windows = platform.system() == 'Windows'
        
        # Root path should be ".." (parent of Work dir, which is CHECKLIST)
        root_path = ".."
        
        try:
            if is_windows:
                run_script = paths.workspace_root / "Work" / "run.ps1"
                
                if not run_script.exists():
                    step3["status"] = "error"
                    step3["message"] = f"run.ps1 not found in Work directory"
                    steps.append(step3)
                    return IntegrationTestResponse(
                        status="error",
                        steps=steps,
                        error="run.ps1 not found"
                    )
                
                cmd = [
                    "powershell.exe",
                    "-ExecutionPolicy", "Bypass",
                    "-File", str(run_script),
                    "-root", root_path,
                    "-stage", "Initial",
                    "-check_module", request.module,
                    "-check_item", request.item_id
                ]
            else:
                run_script = paths.workspace_root / "Work" / "run.csh"
                
                if not run_script.exists():
                    step3["status"] = "error"
                    step3["message"] = f"run.csh not found in Work directory"
                    steps.append(step3)
                    return IntegrationTestResponse(
                        status="error",
                        steps=steps,
                        error="run.csh not found"
                    )
                
                os.chmod(run_script, 0o755)
                cmd = [
                    "/bin/csh", "-f", str(run_script),
                    "-root", root_path,
                    "-stage", "Initial",
                    "-check_module", request.module,
                    "-check_item", request.item_id
                ]
            
            result = subprocess.run(
                cmd,
                cwd=str(work_dir),
                capture_output=True,
                text=True,
                timeout=60
            )
            
            step3["status"] = "success" if result.returncode == 0 else "error"
            step3["message"] = f"Exit code: {result.returncode}"
            step3["return_code"] = result.returncode
            steps.append(step3)
            
        except subprocess.TimeoutExpired:
            step3["status"] = "error"
            step3["message"] = "Timeout after 60 seconds"
            steps.append(step3)
            return IntegrationTestResponse(
                status="error",
                steps=steps,
                error="Test timed out"
            )
        except Exception as e:
            step3["status"] = "error"
            step3["message"] = str(e)
            steps.append(step3)
            return IntegrationTestResponse(
                status="error",
                steps=steps,
                error=str(e)
            )
        
        # Step 4: Check generated files
        step4 = {"name": "Checking generated files", "status": "running"}
        module_dir = paths.workspace_root / "Check_modules" / request.module
        generated_files = {}
        
        # Check report file
        report_file = module_dir / "reports" / f"{request.item_id}.rpt"
        if report_file.exists():
            generated_files["report"] = {
                "path": str(report_file.relative_to(paths.workspace_root)),
                "size": report_file.stat().st_size,
                "exists": True
            }
        else:
            generated_files["report"] = {"exists": False}
        
        # Check log file
        log_file = module_dir / "logs" / f"{request.item_id}.log"
        if log_file.exists():
            generated_files["log"] = {
                "path": str(log_file.relative_to(paths.workspace_root)),
                "size": log_file.stat().st_size,
                "exists": True
            }
        else:
            generated_files["log"] = {"exists": False}
        
        # Check outputs YAML
        outputs_yaml = module_dir / "outputs" / f"{request.module}.yaml"
        if outputs_yaml.exists():
            try:
                with open(outputs_yaml, 'r', encoding='utf-8') as f:
                    output_data = yaml.safe_load(f)
                
                generated_files["yaml"] = {
                    "path": str(outputs_yaml.relative_to(paths.workspace_root)),
                    "exists": True,
                    "valid": True
                }
                
                # Check if item exists in check_items
                if output_data and 'check_items' in output_data and request.item_id in output_data['check_items']:
                    item_result = output_data['check_items'][request.item_id]
                    generated_files["yaml"]["item_result"] = {
                        "executed": item_result.get('executed'),
                        "status": item_result.get('status')
                    }
            except Exception as e:
                generated_files["yaml"] = {
                    "exists": True,
                    "valid": False,
                    "error": str(e)
                }
        else:
            generated_files["yaml"] = {"exists": False}
        
        files_ok = all(f.get("exists", False) for f in generated_files.values())
        step4["status"] = "success" if files_ok else "warning"
        step4["message"] = f"{sum(1 for f in generated_files.values() if f.get('exists'))}/3 files generated"
        steps.append(step4)
        
        # Parse checker result
        checker_result = None
        if "PASS:" in result.stdout:
            checker_result = "PASS"
        elif "FAIL:" in result.stdout:
            checker_result = "FAIL"
        else:
            checker_result = "UNKNOWN"
        
        return IntegrationTestResponse(
            status="success" if result.returncode == 0 else "error",
            steps=steps,
            stdout=result.stdout,
            stderr=result.stderr if result.stderr else None,
            return_code=result.returncode,
            checker_result=checker_result,
            generated_files=generated_files
        )
        
    except Exception as e:
        error_msg = f"Integration test failed: {str(e)}"
        print(f"[ERROR] {error_msg}")
        traceback.print_exc()
        
        return IntegrationTestResponse(
            status="error",
            error=error_msg
        )


@router.post("/save-baseline")
async def save_baseline(request: AllTestsRequest):
    """
    Save current test outputs as baseline for regression testing.
    """
    try:
        from workflow.intelligent_agent import IntelligentCheckerAgent
        
        agent = IntelligentCheckerAgent(
            item_id=request.item_id,
            module=request.module,
            verbose=False,
            interactive=False
        )
        
        # Run all tests first
        all_results = await run_all_tests(request)
        
        # Then save as baseline
        agent._save_baseline(request.config)
        
        return {
            "status": "success",
            "message": f"Baseline saved for {request.item_id}",
            "test_results": all_results.summary
        }
        
    except Exception as e:
        error_msg = f"Save baseline failed: {str(e)}"
        print(f"[ERROR] {error_msg}")
        traceback.print_exc()
        
        return {
            "status": "error",
            "error": error_msg
        }


@router.get("/read-file")
async def read_generated_file(path: str):
    """
    Read content of a generated file (report, log, yaml).
    
    Args:
        path: Relative path to the file (relative to workspace root)
    """
    try:
        try:
            from utils.paths import discover_project_paths
        except ImportError:
            from AutoGenChecker.utils.paths import discover_project_paths
        
        paths = discover_project_paths()
        
        # Construct full path
        full_path = paths.workspace_root / path
        
        # Security check - ensure file is within workspace
        try:
            full_path.resolve().relative_to(paths.workspace_root.resolve())
        except ValueError:
            return {
                "status": "error",
                "error": "Access denied: path outside workspace"
            }
        
        # Check file exists
        if not full_path.exists():
            return {
                "status": "error",
                "error": f"File not found: {path}"
            }
        
        # Read file content
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return {
            "status": "success",
            "path": path,
            "content": content,
            "size": len(content)
        }
        
    except Exception as e:
        error_msg = f"Read file failed: {str(e)}"
        print(f"[ERROR] {error_msg}")
        traceback.print_exc()
        
        return {
            "status": "error",
            "error": error_msg
        }


@router.post("/regression-test")
async def regression_test(request: AllTestsRequest):
    """
    Run regression test comparing with saved baseline.
    """
    try:
        from workflow.intelligent_agent import IntelligentCheckerAgent
        
        agent = IntelligentCheckerAgent(
            item_id=request.item_id,
            module=request.module,
            verbose=False,
            interactive=False
        )
        
        # Run regression test
        agent._run_regression_test(request.config)
        
        return {
            "status": "success",
            "message": f"Regression test completed for {request.item_id}"
        }
        
    except Exception as e:
        error_msg = f"Regression test failed: {str(e)}"
        print(f"[ERROR] {error_msg}")
        traceback.print_exc()
        
        return {
            "status": "error",
            "error": error_msg
        }
