################################################################################
# Script Name: IMP-5-0-0-11.py
#
# Purpose:
#   Confirm synthesis log has been peer reviewed and all warnings are 
#   understood and annotated with explanation.
#   Supports 4 checking types based on requirements and waivers configuration.
#
# Refactoring to BaseChecker:
#   - Migrated from BooleanChecker to unified BaseChecker
#   - Added support for all 4 checking types (Type 1/2/3/4)
#   - Automatic type detection based on requirements.value and waivers.value
#   - Centralized input validation with create_missing_files_error()
#
# Usage:
#   python IMP-5-0-0-11.py [type]
#   type: Optional override (1/2/3/4), default is auto-detect
#
#
# Logic:
#   - Parse synthesis logs for all warning messages
#   - Extract and categorize warnings by severity
#   - Verify peer review and annotation of warnings
# Author: yyin
# Date:   2025-11-03
# Updated: 2025-11-26 - Migrated to BaseChecker (All 4 Types)
################################################################################

import sys
import re
from pathlib import Path
from typing import List, Dict, Tuple

# Add common modules to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'common'))

from base_checker import BaseChecker, ConfigurationError
from output_formatter import CheckResult, Severity, DetailItem, create_check_result


class SynthesisLogReviewChecker(BaseChecker):
    """
    IMP-5-0-0-11: Confirm synthesis log has been peer reviewed?
    
    Parses synthesis log files and checks review status from configuration.
    
    Checking Types:
    - Type 1: requirements=N/A, waivers=N/A/0 → Always PASS (shows review status)
    - Type 2: requirements>0, waivers=N/A/0 → Not typically used for this checker
    - Type 3: requirements>0, waivers>0 → Not typically used for this checker
    - Type 4: requirements=N/A, waivers>0 → Not typically used for this checker
    
    Note: This checker typically uses Type 1 (informational only).
    """
    
    def __init__(self):
        """Initialize the synthesis log review checker."""
        super().__init__(
            check_module="5.0_SYNTHESIS_CHECK",
            item_id="IMP-5-0-0-11",
            item_desc="Confirm synthesis log has been peer reviewed and all warnings are understood and annotated with an explanation?"
        )
    
    # =========================================================================
    # Main Check Execution
    # =========================================================================
    
    def execute_check(self) -> CheckResult:
        """
        Execute check with automatic type detection and delegation.
        
        Returns:
            CheckResult based on detected checker type
        """
        try:
            if self.root is None:
                raise RuntimeError("Checker not initialized. Call init_checker() first.")
            
            # Detect checker type (use BaseChecker method)
            checker_type = self.detect_checker_type()
            
            # Execute based on type
            if checker_type == 1:
                return self._execute_type1()
            elif checker_type == 2:
                return self._execute_type2()
            elif checker_type == 3:
                return self._execute_type3()
            else:  # checker_type == 4
                return self._execute_type4()
        except ConfigurationError as e:
            return e.check_result
    
    # =========================================================================
    # Helper Methods
    # =========================================================================
    
    def _get_reviewed_flag(self) -> bool:
        """
        Check if synthesis logs have been reviewed.
        
        Reads 'reviewed_synthesis_logs' from requirements in item_data.
        Returns True if any entry equals 'yes' (case-insensitive).
        """
        if not self.item_data or 'requirements' not in self.item_data:
            return False
        
        requirements = self.item_data.get('requirements', {})
        reviewed_list = requirements.get('reviewed_synthesis_logs', [])
        
        if not isinstance(reviewed_list, list):
            return False
        
        # Check if any value is 'yes' (case-insensitive)
        for value in reviewed_list:
            if isinstance(value, str) and value.strip().lower() == 'yes':
                return True
        
        return False
    
    def _get_log_summary(self, log_path: Path) -> Tuple[int, int, str, int]:
        """
        Get log summary including first warning details.
        
        Returns:
            Tuple of (warning_count, error_count, first_warning_text, first_warning_line)
        """
        warning_count = 0
        error_count = 0
        first_warning = None
        first_warning_line = 0
        
        try:
            lines = self.read_file(log_path)
            if not lines:
                return 0, 0, None, 0
            
            for line_num, line in enumerate(lines, start=1):
                line_lower = line.lower()
                
                # Count and capture first warning
                if 'warning' in line_lower or 'warn:' in line_lower:
                    warning_count += 1
                    if first_warning is None:
                        # Extract warning content after "Warning:" or "Warn:"
                        first_warning = self._extract_warning_content(line.strip())
                        if len(first_warning) > 150:
                            first_warning = first_warning[:150] + "..."
                        first_warning_line = line_num
                
                # Count errors (but not "0 errors")
                if 'error' in line_lower and '0 error' not in line_lower:
                    error_count += 1
        except Exception:
            pass
        
        return warning_count, error_count, first_warning, first_warning_line
    
    def _extract_warning_content(self, line: str) -> str:
        """
        Extract warning content after "Warning:" or "Warn:".
        
        Args:
            line: Original log line
            
        Returns:
            Extracted warning content
        """
        # Try to match "Warning:" or "Warn:" (case-insensitive)
        match = re.search(r'warning\s*:\s*(.+)', line, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        
        match = re.search(r'warn\s*:\s*(.+)', line, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        
        # If no match, return original line
        return line
    
    # =========================================================================
    # Type 1: Informational Check (requirements=N/A, waivers=N/A/0)
    # =========================================================================
    
    def _execute_type1(self) -> CheckResult:
        """
        Type 1: Informational check only, always PASS.
        Shows review status and warning/error counts.
        
        Returns:
            CheckResult with is_pass=True, INFO/WARN messages about review status
        """
        # Validate input files
        valid_files, missing_files = self.validate_input_files()
        
        # Handle missing input files
        if missing_files:
            return self.create_missing_files_error(missing_files)
        
        # Check review status
        is_reviewed = self._get_reviewed_flag()
        
        # Get log files
        log_files = [f for f in valid_files if f.suffix.lower() == '.log']
        
        # Build details
        details = []
        
        if not log_files:
            # No log files found
            details.append(DetailItem(
                severity=Severity.INFO,
                name="",
                line_number=0,
                file_path="",
                reason="No synthesis log files found for review"
            ))
        else:
            # Build details based on review status
            for log_file in log_files:
                warn_count, err_count, first_warning, first_warning_line = self._get_log_summary(log_file)
                
                if is_reviewed:
                    # Reviewed - show INFO with details
                    if first_warning:
                        detail_content = f"{first_warning} ({warn_count-1} remaining warnings and {err_count} errors)"
                    else:
                        detail_content = ""
                    
                    details.append(DetailItem(
                        severity=Severity.INFO,
                        name=detail_content,
                        line_number=first_warning_line if first_warning else 0,
                        file_path=str(log_file.resolve()) if first_warning else "",
                        reason=f"{log_file.name} has been reviewed ({warn_count} warnings, {err_count} errors)"
                    ))
                else:
                    # Not reviewed - show WARN with details
                    if first_warning:
                        detail_content = f"{first_warning} ({warn_count-1} remaining warnings and {err_count} errors)"
                    else:
                        detail_content = ""
                    
                    details.append(DetailItem(
                        severity=Severity.WARN,
                        name=detail_content,
                        line_number=first_warning_line if first_warning else 0,
                        file_path=str(log_file.resolve()) if first_warning else "",
                        reason=f"{log_file.name} needs to be reviewed"
                    ))
        
        # Build groups
        warn_items = [d for d in details if d.severity == Severity.WARN]
        info_items = [d for d in details if d.severity == Severity.INFO]
        
        warn_groups = None
        info_groups = None
        
        if warn_items:
            warn_groups = {
                "WARN01": {
                    "description": "Synthesis logs need to be reviewed",
                    "items": []
                }
            }
        
        if info_items:
            info_groups = {
                "INFO01": {
                    "description": "Check result",
                    "items": []
                }
            }
        
        # Always PASS for Type 1
        return create_check_result(
            value="N/A",
            is_pass=True,
            has_pattern_items=False,
            has_waiver_value=False,
            details=details,
            warn_groups=warn_groups,
            info_groups=info_groups,
            item_desc=self.item_desc
        )
    
    # =========================================================================
    # Type 2/3/4: Placeholder implementations (not typically used)
    # =========================================================================
    
    def _execute_type2(self) -> CheckResult:
        """
        Type 2: Not typically used for log review checker.
        Delegates to Type 1 behavior.
        """
        return self._execute_type1()
    
    def _execute_type3(self) -> CheckResult:
        """
        Type 3: Not typically used for log review checker.
        Delegates to Type 1 behavior.
        """
        return self._execute_type1()
    
    def _execute_type4(self) -> CheckResult:
        """
        Type 4: Not typically used for log review checker.
        Delegates to Type 1 behavior.
        """
        return self._execute_type1()


# =============================================================================
# Entry Point
# =============================================================================

if __name__ == '__main__':
    checker = SynthesisLogReviewChecker()
    checker.run()
