"""
Test Runner for Comprehensive Checker Testing.

Runs generated test configurations and captures results.
Supports:
- Single test execution
- Full test suite (all 6 types)
- Result capture (status, output, errors)
- Progress tracking

Storage: Work/test_results/{item_id}/{timestamp}/
"""

from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import subprocess
import json
import yaml


class TestResult:
    """Single test execution result."""
    
    def __init__(
        self,
        test_type: str,
        status: str,
        output: str,
        errors: Optional[str] = None,
        execution_time: float = 0.0,
    ):
        self.test_type = test_type
        self.status = status
        self.output = output
        self.errors = errors
        self.execution_time = execution_time
        self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "test_type": self.test_type,
            "status": self.status,
            "output": self.output,
            "errors": self.errors,
            "execution_time": self.execution_time,
            "timestamp": self.timestamp,
        }


class TestRunner:
    """Execute tests and capture results."""
    
    def __init__(self, item_id: str, module: str, verbose: bool = True):
        """
        Initialize test runner.
        
        Args:
            item_id: Checker ID
            module: Module name
            verbose: Print detailed output
        """
        self.item_id = item_id
        self.module = module
        self.verbose = verbose
        
        # Setup paths
        try:
            from utils.paths import discover_project_paths
        except ImportError:
            from AutoGenChecker.utils.paths import discover_project_paths
        
        paths = discover_project_paths()
        self.workspace_root = paths.workspace_root
        
        # Checker script path
        self.checker_script = (
            self.workspace_root /
            "Check_modules" /
            module /
            "scripts" /
            "checker" /
            f"{item_id}.py"
        )
        
        # Test config directory
        self.test_config_dir = (
            self.workspace_root / "Work" / "test_configs" / item_id
        )
        
        # Test results directory (timestamped)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.test_results_dir = (
            self.workspace_root / "Work" / "test_results" / item_id / timestamp
        )
        self.test_results_dir.mkdir(parents=True, exist_ok=True)
    
    def run_all_tests(self) -> Dict[str, TestResult]:
        """
        Run all 6 test types.
        
        Returns:
            Dict mapping test type to TestResult
        """
        if not self.checker_script.exists():
            raise FileNotFoundError(f"Checker script not found: {self.checker_script}")
        
        if not self.test_config_dir.exists():
            raise FileNotFoundError(
                f"Test configs not found: {self.test_config_dir}\n"
                "Run test_generator.py first"
            )
        
        # Load manifest to get test types
        manifest_file = self.test_config_dir / "manifest.json"
        if not manifest_file.exists():
            raise FileNotFoundError(f"Manifest not found: {manifest_file}")
        
        with open(manifest_file, 'r', encoding='utf-8') as f:
            manifest = json.load(f)
        
        test_types = list(manifest["test_types"].keys())
        
        print(f"\n🧪 Running {len(test_types)} tests for {self.item_id}...")
        
        results = {}
        for test_type in test_types:
            result = self.run_single_test(test_type)
            results[test_type] = result
            
            # Print result
            status_icon = "✅" if "PASS" in result.status else "❌" if "ERROR" in result.status else "⚠️"
            print(f"  {status_icon} {test_type}: {result.status} ({result.execution_time:.2f}s)")
        
        # Save consolidated results
        self._save_results(results)
        
        return results
    
    def run_single_test(self, test_type: str) -> TestResult:
        """
        Run a single test configuration.
        
        Args:
            test_type: Test type (e.g., "type1_na", "type2")
        
        Returns:
            TestResult object
        """
        config_file = self.test_config_dir / f"{test_type}.yaml"
        if not config_file.exists():
            return TestResult(
                test_type=test_type,
                status="SKIP",
                output="",
                errors=f"Config file not found: {config_file}",
            )
        
        # Build command
        # Use python executable to run checker with config
        import sys
        python_exe = sys.executable
        
        cmd = [
            python_exe,
            str(self.checker_script),
            str(config_file),
        ]
        
        # Execute checker
        import time
        start_time = time.time()
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,  # 60 second timeout
                cwd=str(self.workspace_root),
            )
            
            execution_time = time.time() - start_time
            
            # Parse status from output
            status = self._parse_status_from_output(result.stdout)
            
            # Save individual test output
            self._save_test_output(test_type, result.stdout, result.stderr)
            
            return TestResult(
                test_type=test_type,
                status=status,
                output=result.stdout,
                errors=result.stderr if result.stderr else None,
                execution_time=execution_time,
            )
        
        except subprocess.TimeoutExpired:
            execution_time = time.time() - start_time
            return TestResult(
                test_type=test_type,
                status="TIMEOUT",
                output="",
                errors="Test execution exceeded 60 second timeout",
                execution_time=execution_time,
            )
        
        except Exception as e:
            execution_time = time.time() - start_time
            return TestResult(
                test_type=test_type,
                status="EXCEPTION",
                output="",
                errors=str(e),
                execution_time=execution_time,
            )
    
    def _parse_status_from_output(self, output: str) -> str:
        """
        Extract status from checker output.
        
        Looks for patterns like:
        - "Status: PASS"
        - "Status: ERROR"
        - "Status: ERROR (1 waived)"
        """
        import re
        
        # Try to find "Status: XXX" pattern
        match = re.search(r'Status:\s+(\w+(?:\s+\(.*?\))?)', output, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        
        # Fallback: look for PASS/ERROR keywords
        if "PASS" in output.upper():
            return "PASS"
        elif "ERROR" in output.upper():
            return "ERROR"
        elif "SKIP" in output.upper():
            return "SKIP"
        
        return "UNKNOWN"
    
    def _save_test_output(self, test_type: str, stdout: str, stderr: str) -> None:
        """Save individual test output to file."""
        output_file = self.test_results_dir / f"{test_type}_output.txt"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"Test Type: {test_type}\n")
            f.write(f"Timestamp: {datetime.now().isoformat()}\n")
            f.write(f"\n{'='*80}\n")
            f.write(f"STDOUT:\n")
            f.write(f"{'='*80}\n")
            f.write(stdout)
            
            if stderr:
                f.write(f"\n{'='*80}\n")
                f.write(f"STDERR:\n")
                f.write(f"{'='*80}\n")
                f.write(stderr)
    
    def _save_results(self, results: Dict[str, TestResult]) -> None:
        """Save consolidated test results."""
        results_json = {
            "item_id": self.item_id,
            "module": self.module,
            "timestamp": datetime.now().isoformat(),
            "checker_script": str(self.checker_script.relative_to(self.workspace_root)),
            "test_results": {
                test_type: result.to_dict()
                for test_type, result in results.items()
            },
            "summary": self._generate_summary(results),
        }
        
        # Save JSON
        results_file = self.test_results_dir / "test_results.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results_json, f, indent=2)
        
        if self.verbose:
            print(f"\n📄 Results saved to: {results_file.relative_to(self.workspace_root)}")
    
    def _generate_summary(self, results: Dict[str, TestResult]) -> Dict[str, Any]:
        """Generate test summary statistics."""
        total = len(results)
        passed = sum(1 for r in results.values() if "PASS" in r.status)
        failed = sum(1 for r in results.values() if "ERROR" in r.status)
        skipped = sum(1 for r in results.values() if r.status in ["SKIP", "TIMEOUT", "EXCEPTION"])
        
        total_time = sum(r.execution_time for r in results.values())
        
        return {
            "total_tests": total,
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "pass_rate": f"{passed / total * 100:.1f}%" if total > 0 else "0%",
            "total_execution_time": f"{total_time:.2f}s",
        }


def run_tests(item_id: str, module: str, test_type: Optional[str] = None) -> Dict[str, TestResult]:
    """
    Convenience function to run tests.
    
    Args:
        item_id: Checker ID
        module: Module name
        test_type: Optional specific test type to run (if None, run all)
    
    Returns:
        Dict mapping test type to TestResult
    """
    runner = TestRunner(item_id, module)
    
    if test_type:
        result = runner.run_single_test(test_type)
        return {test_type: result}
    else:
        return runner.run_all_tests()


if __name__ == "__main__":
    # Test runner CLI
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python test_runner.py <item_id> <module> [test_type]")
        print("Example: python test_runner.py IMP-9-0-0-07 9.0_RC_EXTRACTION_CHECK")
        print("         python test_runner.py IMP-9-0-0-07 9.0_RC_EXTRACTION_CHECK type1_na")
        sys.exit(1)
    
    item_id = sys.argv[1]
    module = sys.argv[2]
    test_type = sys.argv[3] if len(sys.argv) > 3 else None
    
    print(f"\nTest Runner")
    print(f"Item: {item_id}")
    print(f"Module: {module}")
    if test_type:
        print(f"Test Type: {test_type}")
    
    try:
        results = run_tests(item_id, module, test_type)
        
        # Print summary
        print(f"\n📊 Test Summary:")
        if test_type:
            result = results[test_type]
            print(f"  Status: {result.status}")
            print(f"  Time: {result.execution_time:.2f}s")
        else:
            passed = sum(1 for r in results.values() if "PASS" in r.status)
            total = len(results)
            print(f"  Passed: {passed}/{total}")
            print(f"  Pass Rate: {passed / total * 100:.1f}%")
        
        print(f"\n✅ Tests completed successfully")
        
    except Exception as e:
        print(f"\n❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
