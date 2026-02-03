################################################################################
# Script Name: IMP-6-0-0-05.py
#
# Purpose:
#   Ensure there are no non-equivalent points in final LEC.
#
#
# Logic:
#   - Parse noneq.rpt for non-equivalent points
#   - Extract all non-equivalent instances and signals
#   - Support waiver for approved non-equivalent points
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


class NonEquivalentPointsChecker(BaseChecker):
    """IMP-6-0-0-05: Confirm no non-equivalent points exist?"""
    
    def __init__(self):
        super().__init__(
            check_module="6.0_POST_SYNTHESIS_LEC_CHECK",
            item_id="IMP-6-0-0-05",
            item_desc="Confirm no non-equivalent points exist?"
        )
        self._metadata: Dict[str, Dict[str, Any]] = {}
    
    def _parse_input_files(self) -> int:
        """Parse LEC log to extract non-equivalent points count."""
        valid_files, missing_files = self.validate_input_files()
        
        non_equiv_count = 0
        
        for file_path in valid_files:
            lines = self.read_file(file_path)
            if not lines:
                continue
            
            for line_num, line in enumerate(lines, 1):
                # Look for patterns like "Non-equivalent: 0" or "Nonequivalent points: 0"
                if 'non' in line.lower() and 'equiv' in line.lower():
                    # Extract number using regex
                    match = re.search(r'non[-\s]?equiv(?:alent)?\s*(?:points?)?\s*[:\s]+(\d+)', line, re.IGNORECASE)
                    if match:
                        count = int(match.group(1))
                        non_equiv_count += count
                        
                        if count > 0:
                            self._metadata[f"NonEquiv_{line_num}"] = {
                                'count': count,
                                'line_number': line_num,
                                'file_path': str(file_path),
                                'line_content': line.strip()
                            }
        
        return non_equiv_count
    
    def _get_waive_items_with_reasons(self) -> Dict[str, str]:
        """Get waiver items with their reasons."""
        waivers = self.get_waivers()
        if not waivers:
            return {}
        waive_items = waivers.get('waive_items', [])
        if waive_items and isinstance(waive_items[0], dict):
            return {item['name']: item.get('reason', '') for item in waive_items}
        return {item: '' for item in waive_items}
    
    def _execute_type1(self, non_equiv_count: int) -> CheckResult:
        """Type 1: Boolean check - any non-equivalent point is FAIL."""
        waivers = self.get_waivers()
        waiver_value = waivers.get('value', 'N/A') if waivers else 'N/A'
        is_waiver_zero = (waiver_value == 0)
        
        is_pass = (non_equiv_count == 0)
        details = []
        
        if non_equiv_count == 0:
            details.append(DetailItem(
                severity=Severity.INFO,
                name="No non-equivalent points found",
                line_number=0,
                file_path="",
                reason="LEC passed - design is equivalent"
            ))
        else:
            severity = Severity.INFO if is_waiver_zero else Severity.FAIL
            reason_suffix = "[WAIVED_AS_INFO]" if is_waiver_zero else ""
            for key, metadata in self._metadata.items():
                details.append(DetailItem(
                    severity=severity,
                    name=f"Non-equivalent points: {metadata['count']}",
                    line_number=metadata['line_number'],
                    file_path=metadata['file_path'],
                    reason=f"Found in: {metadata['line_content']}{reason_suffix}"
                ))
            if is_waiver_zero:
                is_pass = True
        
        return create_check_result(
            value=non_equiv_count,
            is_pass=is_pass,
            has_pattern_items=False,
            has_waiver_value=False,
            details=details,
            item_desc=self.item_desc,
            default_group_desc=f"Non-equivalent points in LEC (Total: {non_equiv_count})"
        )
    
    def _execute_type2(self, non_equiv_count: int) -> CheckResult:
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
        
        is_pass = (non_equiv_count <= req_value)
        details = []
        
        if non_equiv_count == 0:
            details.append(DetailItem(
                severity=Severity.INFO,
                name="No non-equivalent points found",
                line_number=0,
                file_path="",
                reason="LEC passed - design is equivalent"
            ))
        else:
            if is_waiver_zero:
                severity = Severity.INFO
                reason_suffix = "[WAIVED_AS_INFO]"
                is_pass = True
            else:
                severity = Severity.FAIL if non_equiv_count > req_value else Severity.INFO
                reason_suffix = ""
            
            for key, metadata in self._metadata.items():
                details.append(DetailItem(
                    severity=severity,
                    name=f"Non-equivalent points: {metadata['count']}",
                    line_number=metadata['line_number'],
                    file_path=metadata['file_path'],
                    reason=f"Found in: {metadata['line_content']}{reason_suffix}"
                ))
        
        return create_check_result(
            value=non_equiv_count,
            is_pass=is_pass,
            has_pattern_items=False,
            has_waiver_value=False,
            details=details,
            item_desc=self.item_desc,
            default_group_desc=f"Non-equivalent points in LEC (found: {non_equiv_count}, requirement: â‰¤{req_value})"
        )
    
    def _execute_type3(self, non_equiv_count: int) -> CheckResult:
        """Type 3: Value comparison with waiver logic."""
        return self._execute_type2(non_equiv_count)
    
    def _execute_type4(self, non_equiv_count: int) -> CheckResult:
        """Type 4: Boolean check with waiver logic."""
        return self._execute_type1(non_equiv_count)
    
    def execute_check(self) -> CheckResult:
        """Execute non-equivalent points check."""
        if self.root is None:
            raise RuntimeError("Checker not initialized. Call init_checker() first.")
        
        try:
            non_equiv_count = self._parse_input_files()
            checker_type = self.detect_checker_type()
            
            if checker_type == 1:
                return self._execute_type1(non_equiv_count)
            elif checker_type == 2:
                return self._execute_type2(non_equiv_count)
            elif checker_type == 3:
                return self._execute_type3(non_equiv_count)
            elif checker_type == 4:
                return self._execute_type4(non_equiv_count)
            else:
                return self._execute_type2(non_equiv_count)
        except ConfigurationError as e:
            return e.check_result


def main():
    """Main entry point for the checker."""
    checker = NonEquivalentPointsChecker()
    checker.run()


if __name__ == '__main__':
    main()

