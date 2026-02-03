################################################################################
# Script Name: IMP-6-0-0-01.py
#
# Purpose:
#   Review conformal log for any warnings and ensure they are expected.
#
#
# Logic:
#   - Parse Conformal log files for warnings
#   - Extract warning messages and locations
#   - Support waiver for reviewed warnings with explanations
# Author: yyin
# Date:   2025-11-06
# Updated: 2025-12-01 - Migrated to unified BaseChecker architecture
################################################################################

from pathlib import Path
import re
import sys
from typing import List, Dict, Any

# Add common module to path
_SCRIPT_DIR = Path(__file__).resolve().parent
_CHECK_MODULES_DIR = _SCRIPT_DIR.parents[2]
_COMMON_DIR = _CHECK_MODULES_DIR / 'common'
if str(_COMMON_DIR) not in sys.path:
    sys.path.insert(0, str(_COMMON_DIR))

from base_checker import BaseChecker, ConfigurationError
from output_formatter import DetailItem, Severity, CheckResult, create_check_result


class ConformalLogReviewChecker(BaseChecker):
    """IMP-6-0-0-01: Review conformal log for any warnings."""
    
    def __init__(self):
        super().__init__(
            check_module="6.0_POST_SYNTHESIS_LEC_CHECK",
            item_id="IMP-6-0-0-01",
            item_desc="Confirm conformal log file has been peer reviewed and all warnings have a waiver/explanation?"
        )
        self._metadata: Dict[str, Dict[str, Any]] = {}
    
    def _extract_warnings(self) -> List[str]:
        """Extract Warning messages from conformal log files."""
        valid_files, missing_files = self.validate_input_files()
        
        warnings = []
        
        for file_path in valid_files:
            lines = self.read_file(file_path)
            if not lines:
                continue
            
            for line_num, line in enumerate(lines, 1):
                if 'Warning' in line:
                    warning = line.strip()
                    # Remove leading // comment markers if present
                    if warning.startswith('//'):
                        warning = warning[2:].strip()
                    if warning not in warnings:
                        warnings.append(warning)
                        self._metadata[warning] = {
                            'line_number': line_num,
                            'file_path': str(file_path)
                        }
        
        return warnings
    
    def _get_waive_items_with_reasons(self) -> Dict[str, str]:
        """Get waiver items with their reasons."""
        waivers = self.get_waivers()
        if not waivers:
            return {}
        waive_items = waivers.get('waive_items', [])
        if waive_items and isinstance(waive_items[0], dict):
            return {item['name']: item.get('reason', '') for item in waive_items}
        return {item: '' for item in waive_items}
    
    def _execute_type1(self, warnings: List[str]) -> CheckResult:
        """Type 1: Boolean check - informational review."""
        waivers = self.get_waivers()
        waiver_value = waivers.get('value', 'N/A') if waivers else 'N/A'
        is_waiver_zero = (waiver_value == 0)
        
        details = []
        
        if not warnings:
            details.append(DetailItem(
                severity=Severity.INFO,
                name="No warnings found in conformal log",
                line_number=0,
                file_path="",
                reason="Clean log"
            ))
        else:
            for warning in warnings:
                metadata = self._metadata.get(warning, {})
                details.append(DetailItem(
                    severity=Severity.WARN,
                    name=warning,
                    line_number=metadata.get('line_number', ''),
                    file_path=metadata.get('file_path', ''),
                    reason="Review and confirm expected"
                ))
        
        return create_check_result(
            value=len(warnings),
            is_pass=True,
            has_pattern_items=False,
            has_waiver_value=False,
            details=details,
            item_desc=self.item_desc,
            default_group_desc="Warnings found in conformal log"
        )
    
    def _execute_type2(self, warnings: List[str]) -> CheckResult:
        """Type 2: Value comparison (not typically used for this check)."""
        return self._execute_type1(warnings)
    
    def _execute_type3(self, warnings: List[str]) -> CheckResult:
        """Type 3: Value with waiver logic (not typically used for this check)."""
        return self._execute_type1(warnings)
    
    def _execute_type4(self, warnings: List[str]) -> CheckResult:
        """Type 4: Boolean with waiver logic (not typically used for this check)."""
        return self._execute_type1(warnings)
    
    def execute_check(self) -> CheckResult:
        """Execute conformal log review check."""
        if self.root is None:
            raise RuntimeError("Checker not initialized. Call init_checker() first.")
        
        try:
            warnings = self._extract_warnings()
            checker_type = self.detect_checker_type()
            
            if checker_type == 1:
                return self._execute_type1(warnings)
            elif checker_type == 2:
                return self._execute_type2(warnings)
            elif checker_type == 3:
                return self._execute_type3(warnings)
            elif checker_type == 4:
                return self._execute_type4(warnings)
            else:
                return self._execute_type1(warnings)
        except ConfigurationError as e:
            return e.check_result


def main():
    """Main entry point for the checker."""
    checker = ConformalLogReviewChecker()
    checker.run()


if __name__ == '__main__':
    main()

