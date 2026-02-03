"""
Regression Diff Engine for Smart Comparison.

Compares current test results with baseline:
- Smart diff ignoring timestamps/line numbers
- Focuses on status, item counts, error messages
- Detects regressions (PASS→FAIL) and improvements (FAIL→PASS)
- Generates structured diff data for reporting

Output: Diff data structure for regression_reporter.py
"""

from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import json
import re
from datetime import datetime


class RegressionDiff:
    """Smart comparison engine for test results."""
    
    # Fields to ignore in comparison
    IGNORE_FIELDS = [
        "timestamp",
        "execution_time",
        "baseline_created",
        "source_results",
        "checksums",
    ]
    
    # Status severity ranking (for regression detection)
    STATUS_SEVERITY = {
        "PASS": 0,
        "SKIP": 1,
        "TIMEOUT": 2,
        "ERROR": 3,
        "EXCEPTION": 4,
        "FAIL": 5,
    }
    
    def __init__(self, item_id: str, current_results_dir: Path):
        """
        Initialize regression diff engine.
        
        Args:
            item_id: Checker ID
            current_results_dir: Directory with current test results
        """
        self.item_id = item_id
        self.current_results_dir = current_results_dir
        
        # Load current results
        current_results_file = current_results_dir / "test_results.json"
        if not current_results_file.exists():
            raise FileNotFoundError(f"Current results not found: {current_results_file}")
        
        with open(current_results_file, 'r', encoding='utf-8') as f:
            self.current_results = json.load(f)
        
        # Load baseline
        try:
            from workflow.baseline_manager import load_baseline
        except ImportError:
            from AutoGenChecker.workflow.baseline_manager import load_baseline
        
        self.baseline = load_baseline(item_id)
        if not self.baseline:
            raise ValueError(f"No baseline found for {item_id}. Run with --save-baseline first.")
    
    def compare(self) -> Dict[str, Any]:
        """
        Perform smart comparison between current and baseline.
        
        Returns:
            Diff data structure with:
            - overall_status: REGRESSION, IMPROVEMENT, UNCHANGED
            - regressions: List of test_type with PASS→FAIL
            - improvements: List of test_type with FAIL→PASS
            - status_changes: Detailed status change data
            - output_diffs: Smart output comparison (ignoring timestamps)
        """
        baseline_results = self.baseline["test_results"]["test_results"]
        current_results = self.current_results["test_results"]
        
        # Compare test statuses
        status_changes = self._compare_statuses(baseline_results, current_results)
        
        # Detect regressions and improvements
        regressions = []
        improvements = []
        unchanged = []
        
        for test_type, change_data in status_changes.items():
            old_status = change_data["old_status"]
            new_status = change_data["new_status"]
            
            if old_status == new_status:
                unchanged.append(test_type)
            elif self._is_regression(old_status, new_status):
                regressions.append({
                    "test_type": test_type,
                    "old_status": old_status,
                    "new_status": new_status,
                    "severity": self._compute_regression_severity(old_status, new_status),
                })
            elif self._is_improvement(old_status, new_status):
                improvements.append({
                    "test_type": test_type,
                    "old_status": old_status,
                    "new_status": new_status,
                })
        
        # Compare outputs (smart diff ignoring timestamps)
        output_diffs = self._compare_outputs(baseline_results, current_results)
        
        # Determine overall status
        if regressions:
            overall_status = "REGRESSION"
        elif improvements:
            overall_status = "IMPROVEMENT"
        else:
            overall_status = "UNCHANGED"
        
        return {
            "item_id": self.item_id,
            "comparison_time": datetime.now().isoformat(),
            "baseline_info": {
                "created": self.baseline["baseline_created"],
                "description": self.baseline["description"],
                "pass_rate": self.baseline["summary"]["pass_rate"],
            },
            "current_info": {
                "pass_rate": self.current_results["summary"]["pass_rate"],
                "total_tests": self.current_results["summary"]["total_tests"],
            },
            "overall_status": overall_status,
            "regressions": regressions,
            "improvements": improvements,
            "unchanged": unchanged,
            "status_changes": status_changes,
            "output_diffs": output_diffs,
        }
    
    def _compare_statuses(
        self,
        baseline_results: Dict[str, Any],
        current_results: Dict[str, Any],
    ) -> Dict[str, Dict[str, str]]:
        """
        Compare test statuses between baseline and current.
        
        Returns:
            Dict mapping test_type to {old_status, new_status, changed}
        """
        status_changes = {}
        
        for test_type in baseline_results.keys():
            old_status = baseline_results[test_type]["status"]
            new_status = current_results.get(test_type, {}).get("status", "MISSING")
            
            status_changes[test_type] = {
                "old_status": old_status,
                "new_status": new_status,
                "changed": old_status != new_status,
            }
        
        return status_changes
    
    def _is_regression(self, old_status: str, new_status: str) -> bool:
        """
        Check if status change is a regression.
        
        Regression = severity increased (e.g., PASS→ERROR)
        """
        old_severity = self.STATUS_SEVERITY.get(old_status, 999)
        new_severity = self.STATUS_SEVERITY.get(new_status, 999)
        
        return new_severity > old_severity
    
    def _is_improvement(self, old_status: str, new_status: str) -> bool:
        """
        Check if status change is an improvement.
        
        Improvement = severity decreased (e.g., ERROR→PASS)
        """
        old_severity = self.STATUS_SEVERITY.get(old_status, 999)
        new_severity = self.STATUS_SEVERITY.get(new_status, 999)
        
        return new_severity < old_severity
    
    def _compute_regression_severity(self, old_status: str, new_status: str) -> str:
        """Compute regression severity level."""
        if old_status == "PASS" and new_status in ["ERROR", "FAIL", "EXCEPTION"]:
            return "CRITICAL"  # Working test now broken
        elif new_status in ["ERROR", "EXCEPTION"]:
            return "HIGH"  # Any new errors
        elif new_status == "TIMEOUT":
            return "MEDIUM"  # Performance regression
        else:
            return "LOW"
    
    def _compare_outputs(
        self,
        baseline_results: Dict[str, Any],
        current_results: Dict[str, Any],
    ) -> Dict[str, Dict[str, Any]]:
        """
        Smart comparison of test outputs.
        
        Ignores:
        - Timestamps
        - Line numbers in error messages
        - Execution time variations
        
        Focuses on:
        - Status changes
        - Error message content
        - Item count changes
        """
        output_diffs = {}
        
        for test_type in baseline_results.keys():
            baseline_output = baseline_results[test_type].get("output", "")
            current_output = current_results.get(test_type, {}).get("output", "")
            
            # Normalize outputs (remove timestamps, normalize line numbers)
            baseline_normalized = self._normalize_output(baseline_output)
            current_normalized = self._normalize_output(current_output)
            
            # Check if outputs differ
            if baseline_normalized != current_normalized:
                # Extract meaningful differences
                diff_data = self._extract_output_diff(
                    baseline_output, current_output, test_type
                )
                output_diffs[test_type] = diff_data
        
        return output_diffs
    
    def _normalize_output(self, output: str) -> str:
        """
        Normalize output for comparison.
        
        Removes timestamps, line numbers, execution times.
        """
        # Remove timestamps (various formats)
        output = re.sub(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[.\d]*', '[TIMESTAMP]', output)
        output = re.sub(r'\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2}', '[TIMESTAMP]', output)
        
        # Remove execution times
        output = re.sub(r'\d+\.\d+s', '[TIME]', output)
        output = re.sub(r'\d+\s*seconds?', '[TIME]', output)
        
        # Remove line numbers in error messages
        output = re.sub(r'line \d+', 'line [N]', output, flags=re.IGNORECASE)
        output = re.sub(r':\d+:', ':[N]:', output)
        
        # Remove memory addresses
        output = re.sub(r'0x[0-9a-fA-F]+', '[ADDR]', output)
        
        return output
    
    def _extract_output_diff(
        self,
        baseline_output: str,
        current_output: str,
        test_type: str,
    ) -> Dict[str, Any]:
        """
        Extract meaningful differences from outputs.
        
        Returns structured diff data.
        """
        # Extract item counts if present
        baseline_counts = self._extract_item_counts(baseline_output)
        current_counts = self._extract_item_counts(current_output)
        
        return {
            "has_diff": True,
            "baseline_counts": baseline_counts,
            "current_counts": current_counts,
            "count_changed": baseline_counts != current_counts,
            "baseline_preview": baseline_output[:200],
            "current_preview": current_output[:200],
        }
    
    def _extract_item_counts(self, output: str) -> Dict[str, int]:
        """Extract item counts from output (e.g., INFO01: 3 items)."""
        counts = {}
        
        # Pattern: INFO01, ERROR01, etc.
        for match in re.finditer(r'(INFO\d+|ERROR\d+|WARNING\d+):\s*(\d+)', output):
            label = match.group(1)
            count = int(match.group(2))
            counts[label] = count
        
        return counts


def run_regression_test(item_id: str, current_results_dir: Path) -> Dict[str, Any]:
    """
    Convenience function to run regression test.
    
    Args:
        item_id: Checker ID
        current_results_dir: Directory with current test results
    
    Returns:
        Regression diff data
    """
    diff_engine = RegressionDiff(item_id, current_results_dir)
    return diff_engine.compare()


if __name__ == "__main__":
    # Regression diff CLI
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python regression_diff.py <item_id> <current_results_dir>")
        print("Example: python regression_diff.py IMP-9-0-0-07 Work/test_results/IMP-9-0-0-07/20250126_143052")
        sys.exit(1)
    
    item_id = sys.argv[1]
    current_results_dir = Path(sys.argv[2])
    
    print(f"\nRegression Diff")
    print(f"Item: {item_id}")
    print(f"Current Results: {current_results_dir}")
    
    try:
        diff_data = run_regression_test(item_id, current_results_dir)
        
        print(f"\n📊 Regression Analysis:")
        print(f"  Overall Status: {diff_data['overall_status']}")
        print(f"  Regressions: {len(diff_data['regressions'])}")
        print(f"  Improvements: {len(diff_data['improvements'])}")
        print(f"  Unchanged: {len(diff_data['unchanged'])}")
        
        if diff_data['regressions']:
            print(f"\n❌ Regressions Detected:")
            for reg in diff_data['regressions']:
                print(f"  - {reg['test_type']}: {reg['old_status']} → {reg['new_status']} ({reg['severity']})")
        
        print(f"\n✅ Regression test completed")
        
    except Exception as e:
        print(f"\n❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
