################################################################################
# Script Name: IMP-13-0-0-04.py
#
# Purpose:
#   Ensure there are no aborted points in final LEC.
#
#
# Logic:
#   - Parse LEC log for flatten model settings
#   - Verify set flatten model commands exist
#   - Check flatten model configuration completeness
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


class AbortedPointsChecker(BaseChecker):
    """IMP-13-0-0-04: Confirm no aborted compare points exist in log files or reports?"""
    
    def __init__(self):
        super().__init__(
            check_module="13.0_POST_PD_EQUIVALENCE_CHECK",
            item_id="IMP-13-0-0-04",
            item_desc="Confirm no aborted compare points exist in log files or reports?"
        )
        self._metadata: Dict[str, Dict[str, Any]] = {}
    
    def _parse_input_files(self) -> int:
        """Parse LEC log to extract aborted points count."""
        valid_files, missing_files = self.validate_input_files()
        
        aborted_count = 0
        
        for file_path in valid_files:
            lines = self.read_file(file_path)
            if not lines:
                continue
            
            for line_num, line in enumerate(lines, 1):
                # Look for patterns like "Aborted: 0" or "Aborted points: 0"
                if 'aborted' in line.lower():
                    # Extract number using regex
                    match = re.search(r'aborted\s*(?:points?)?\s*[:\s]+(\d+)', line, re.IGNORECASE)
                    if match:
                        count = int(match.group(1))
                        aborted_count += count
                        
                        if count > 0:
                            self._metadata[f"Aborted_{line_num}"] = {
                                'count': count,
                                'line_number': line_num,
                                'file_path': str(file_path),
                                'line_content': line.strip()
                            }
        
        return aborted_count
    
    def _get_waive_items_with_reasons(self) -> Dict[str, str]:
        """Get waiver items with their reasons."""
        waivers = self.get_waivers()
        if not waivers:
            return {}
        waive_items = waivers.get('waive_items', [])
        if waive_items and isinstance(waive_items[0], dict):
            return {item['name']: item.get('reason', '') for item in waive_items}
        return {item: '' for item in waive_items}
    
    def _execute_type1(self, aborted_count: int) -> CheckResult:
        """Type 1: Boolean check - any aborted point is FAIL."""
        waivers = self.get_waivers()
        waiver_value = waivers.get('value', 'N/A') if waivers else 'N/A'
        waive_items = waivers.get('waive_items', []) if waivers else []
        is_waiver_zero = (waiver_value == 0)
        
        is_pass = (aborted_count == 0)
        details = []
        
        if aborted_count == 0:
            details.append(DetailItem(
                severity=Severity.INFO,
                name="No aborted points found",
                line_number=0,
                file_path="",
                reason="LEC completed successfully"
            ))
        else:
            severity = Severity.INFO if is_waiver_zero else Severity.FAIL
            reason_suffix = "[WAIVED_AS_INFO]" if is_waiver_zero else ""
            for key, metadata in self._metadata.items():
                details.append(DetailItem(
                    severity=severity,
                    name=f"Aborted points: {metadata['count']}",
                    line_number=metadata['line_number'],
                    file_path=metadata['file_path'],
                    reason=f"Found in: {metadata['line_content']}{reason_suffix}"
                ))
            if is_waiver_zero:
                is_pass = True
        
        # Add waive_items when waiver=0
        if is_waiver_zero and waive_items:
            for item in waive_items:
                details.append(DetailItem(
                    severity=Severity.INFO,
                    name=item,
                    line_number=0,
                    file_path="N/A",
                    reason="Waiver item[WAIVED_INFO]"
                ))
        
        return create_check_result(
            value=aborted_count,
            is_pass=is_pass,
            has_pattern_items=False,
            has_waiver_value=False,
            details=details,
            item_desc=self.item_desc,
            default_group_desc=f"Aborted points in LEC (Total: {aborted_count})"
        )
    
    def _execute_type2(self, aborted_count: int) -> CheckResult:
        """Type 2: Value comparison against requirements.value."""
        requirements = self.get_requirements()
        req_value = requirements.get('value', 0) if requirements else 0
        try:
            req_value = int(req_value)
        except:
            req_value = 0
        
        waivers = self.get_waivers()
        waiver_value = waivers.get('value', 'N/A') if waivers else 'N/A'
        is_waiver_zero = (waiver_value == 0)
        
        is_pass = (aborted_count <= req_value)
        details = []
        
        if aborted_count == 0:
            details.append(DetailItem(
                severity=Severity.INFO,
                name="No aborted points found",
                line_number=0,
                file_path="",
                reason="LEC completed successfully"
            ))
        else:
            if is_waiver_zero:
                severity = Severity.INFO
                reason_suffix = "[WAIVED_AS_INFO]"
                is_pass = True
            else:
                severity = Severity.FAIL if aborted_count > req_value else Severity.INFO
                reason_suffix = ""
            
            for key, metadata in self._metadata.items():
                details.append(DetailItem(
                    severity=severity,
                    name=f"Aborted points: {metadata['count']}",
                    line_number=metadata['line_number'],
                    file_path=metadata['file_path'],
                    reason=f"Found in: {metadata['line_content']}{reason_suffix}"
                ))
        
        return create_check_result(
            value=aborted_count,
            is_pass=is_pass,
            has_pattern_items=False,
            has_waiver_value=False,
            details=details,
            item_desc=self.item_desc,
            default_group_desc=f"Aborted points in LEC (found: {aborted_count}, requirement: ≤{req_value})"
        )
    
    def _execute_type3(self, aborted_count: int) -> CheckResult:
        """Type 3: Value comparison with waiver logic (not typically used for count-based checks)."""
        return self._execute_type2(aborted_count)
    
    def _execute_type4(self, aborted_count: int) -> CheckResult:
        """Type 4: Boolean check with waiver logic (not typically used for count-based checks)."""
        return self._execute_type1(aborted_count)
    
    def execute_check(self) -> CheckResult:
        """Execute aborted points check."""
        if self.root is None:
            raise RuntimeError("Checker not initialized. Call init_checker() first.")
        
        try:
            aborted_count = self._parse_input_files()
            checker_type = self.detect_checker_type()
            
            if checker_type == 1:
                return self._execute_type1(aborted_count)
            elif checker_type == 2:
                return self._execute_type2(aborted_count)
            elif checker_type == 3:
                return self._execute_type3(aborted_count)
            elif checker_type == 4:
                return self._execute_type4(aborted_count)
            else:
                return self._execute_type2(aborted_count)
        except ConfigurationError as e:
            return e.check_result


def main():
    """Main entry point for the checker."""
    checker = AbortedPointsChecker()
    checker.run()


if __name__ == '__main__':
    main()
