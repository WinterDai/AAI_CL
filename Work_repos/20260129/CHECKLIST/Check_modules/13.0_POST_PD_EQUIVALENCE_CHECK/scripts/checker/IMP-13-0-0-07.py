################################################################################
# Script Name: IMP-13-0-0-07.py
#
# Purpose:
#   Verify final LEC result is PASS.
#
#
# Logic:
#   - Parse LEC log to search for library pin verification command
#   - Verify "set flatten model -library_pin_verification" exists
#   - Report if command is missing or incorrect
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


class LECFlattenModelChecker(BaseChecker):
    """IMP-13-0-0-07: Confirm "set flatten model -library_pin_verification" in LEC flow."""
    
    def __init__(self):
        super().__init__(
            check_module="13.0_POST_PD_EQUIVALENCE_CHECK",
            item_id="IMP-13-0-0-07",
            item_desc="Confirm \"set flatten model -library_pin_verification\" in LEC flow."
        )
        self._metadata: Dict[str, Dict[str, Any]] = {}
        self._target_string = "set flatten model -library_pin_verification"
    
    def _search_target_string(self) -> bool:
        """Search for the target string in input files."""
        valid_files, missing_files = self.validate_input_files()
        
        found = False
        
        # Store checked files for error message
        self._metadata["checked_files"] = [str(f) for f in valid_files]
        
        for file_path in valid_files:
            lines = self.read_file(file_path)
            if not lines:
                continue
            
            for line_num, line in enumerate(lines, 1):
                if self._target_string in line:
                    found = True
                    self._metadata["found"] = {
                        'line_number': line_num,
                        'file_path': str(file_path),
                        'line_content': line.strip()
                    }
                    # If found, we can stop searching (unless we want to find all occurrences, 
                    # but requirement says "If found -> PASS")
                    return True
        
        return False
    
    def _get_waive_items_with_reasons(self) -> Dict[str, str]:
        """Get waiver items with their reasons."""
        waivers = self.get_waivers()
        if not waivers:
            return {}
        waive_items = waivers.get('waive_items', [])
        if waive_items and isinstance(waive_items[0], dict):
            return {item['name']: item.get('reason', '') for item in waive_items}
        return {item: '' for item in waive_items}
    
    def _execute_type1(self, found: bool) -> CheckResult:
        """Type 1: Boolean check - found is PASS, not found is FAIL."""
        details = []
        
        if found:
            metadata = self._metadata.get("found", {})
            details.append(DetailItem(
                severity=Severity.INFO,
                name=f"Found '{self._target_string}'",
                line_number=metadata.get('line_number', 0),
                file_path=metadata.get('file_path', ''),
                reason="Target string found in log"
            ))
        else:
            checked_files = self._metadata.get("checked_files", [])
            file_info = checked_files[0] if checked_files else "no input files"
            details.append(DetailItem(
                severity=Severity.FAIL,
                name=f"Missing '{self._target_string}'",
                line_number=0,
                file_path="",
                reason=f"'{self._target_string}' isn't found in {file_info}"
            ))
        
        return create_check_result(
            value="Found" if found else "Missing",
            is_pass=found,
            has_pattern_items=False,
            has_waiver_value=False,
            details=details,
            item_desc=self.item_desc,
            default_group_desc="LEC Flatten Model Check"
        )
    
    def _execute_type2(self, found: bool) -> CheckResult:
        """Type 2: Value comparison (not typically used for this check)."""
        return self._execute_type1(found)
    
    def _execute_type3(self, found: bool) -> CheckResult:
        """Type 3: Value with waiver logic (not typically used for this check)."""
        return self._execute_type1(found)
    
    def _execute_type4(self, found: bool) -> CheckResult:
        """Type 4: Boolean with waiver logic."""
        waivers = self.get_waivers()
        waiver_value = waivers.get('value', 'N/A') if waivers else 'N/A'
        
        # If found, it's a pass regardless of waiver
        if found:
            return self._execute_type1(found)
            
        # If not found, check if waived
        # For type 4, waiver_value=0 usually means waive all errors
        is_waived = (waiver_value == 0)
        
        details = []
        if is_waived:
            details.append(DetailItem(
                severity=Severity.WAIVE,
                name=f"Missing '{self._target_string}'",
                line_number=0,
                file_path="",
                reason="Waived by waiver value 0"
            ))
        else:
            checked_files = self._metadata.get("checked_files", [])
            file_info = checked_files[0] if checked_files else "no input files"
            details.append(DetailItem(
                severity=Severity.FAIL,
                name=f"Missing '{self._target_string}'",
                line_number=0,
                file_path="",
                reason=f"'{self._target_string}' isn't found in {file_info}"
            ))
            
        return create_check_result(
            value="Missing",
            is_pass=is_waived,
            has_pattern_items=False,
            has_waiver_value=True,
            details=details,
            item_desc=self.item_desc,
            default_group_desc="LEC Flatten Model Check"
        )
    
    def execute_check(self) -> CheckResult:
        """Execute LEC flatten model check."""
        if self.root is None:
            raise RuntimeError("Checker not initialized. Call init_checker() first.")
        
        try:
            found = self._search_target_string()
            
            check_type = self.detect_checker_type()
            
            if check_type == 1:
                return self._execute_type1(found)
            elif check_type == 2:
                return self._execute_type2(found)
            elif check_type == 3:
                return self._execute_type3(found)
            else:  # type 4
                return self._execute_type4(found)
        
        except ConfigurationError as e:
            return e.check_result


def main():
    """Main entry point for the checker."""
    checker = LECFlattenModelChecker()
    checker.run()


if __name__ == '__main__':
    main()
