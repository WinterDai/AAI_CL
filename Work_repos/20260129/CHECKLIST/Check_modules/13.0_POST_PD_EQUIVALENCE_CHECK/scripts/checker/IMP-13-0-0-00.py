################################################################################
# Script Name: IMP-13-0-0-00.py
#
# Purpose:
#   Confirm conformal constraints have been peer reviewed and approved.
#
#
# Logic:
#   - Parse LEC log for add_pin_constraints commands
#   - Extract and list all constraint definitions
#   - Verify constraints have been peer reviewed
# Author: yyin
# Date:   2025-11-06
# Updated: 2025-12-01 - Migrated to unified BaseChecker architecture
################################################################################

from pathlib import Path
import re
import sys
from typing import List, Dict, Any, Tuple

# Add common module to path
_SCRIPT_DIR = Path(__file__).resolve().parent
_CHECK_MODULES_DIR = _SCRIPT_DIR.parents[2]
_COMMON_DIR = _CHECK_MODULES_DIR / 'common'
if str(_COMMON_DIR) not in sys.path:
    sys.path.insert(0, str(_COMMON_DIR))

from base_checker import BaseChecker, ConfigurationError
from output_formatter import DetailItem, Severity, CheckResult, create_check_result


class ConformalConstraintsReviewChecker(BaseChecker):
    """IMP-13-0-0-00: Confirm conformal constraints have been peer reviewed and approved."""
    
    def __init__(self):
        super().__init__(
            check_module="13.0_POST_PD_EQUIVALENCE_CHECK",
            item_id="IMP-13-0-0-00",
            item_desc="Confirm conformal constraints have been peer reviewed and approved?"
        )
        # Store constraint metadata
        self._metadata: Dict[str, Dict[str, Any]] = {}
    
    def _extract_add_pin_constraints(self) -> List[str]:
        """Extract add_pin_constraints from input files."""
        valid_files, missing_files = self.validate_input_files()
        
        constraints = []
        
        for file_path in valid_files:
            lines = self.read_file(file_path)
            if not lines:
                continue
            
            for line_num, line in enumerate(lines, 1):
                if 'add_pin_constraints' in line:
                    constraint = line.strip()
                    # Remove '//' prefix if present
                    if constraint.startswith('//'):
                        constraint = constraint[2:].strip()
                    if constraint not in constraints:
                        constraints.append(constraint)
                        self._metadata[constraint] = {
                            'line_number': line_num,
                            'file_path': str(file_path)
                        }
        
        return constraints
    
    def _get_waive_items_with_reasons(self) -> Dict[str, str]:
        """Get waiver items with their reasons."""
        waivers = self.get_waivers()
        if not waivers:
            return {}
        waive_items = waivers.get('waive_items', [])
        if waive_items and isinstance(waive_items[0], dict):
            return {item['name']: item.get('reason', '') for item in waive_items}
        return {item: '' for item in waive_items}
    
    def _execute_type1(self, constraints: List[str]) -> CheckResult:
        """Type 1: Boolean check - informational review."""
        waivers = self.get_waivers()
        waiver_value = waivers.get('value', 'N/A') if waivers else 'N/A'
        is_waiver_zero = (waiver_value == 0)
        
        details = []
        
        if not constraints:
            details.append(DetailItem(
                severity=Severity.INFO,
                name="No add_pin_constraints found",
                line_number=0,
                file_path="",
                reason="No constraints to review"
            ))
        else:
            for constraint in constraints:
                metadata = self._metadata.get(constraint, {})
                details.append(DetailItem(
                    severity=Severity.WARN,
                    name=constraint,
                    line_number=metadata.get('line_number', ''),
                    file_path=metadata.get('file_path', ''),
                    reason="Need to be peer reviewed"
                ))
        
        return create_check_result(
            value=len(constraints),
            is_pass=True,
            has_pattern_items=False,
            has_waiver_value=False,
            details=details,
            item_desc=self.item_desc,
            default_group_desc="Conformal constraints requiring peer review"
        )
    
    def _execute_type2(self, constraints: List[str]) -> CheckResult:
        """Type 2: Value comparison (not typically used for this check)."""
        return self._execute_type1(constraints)
    
    def _execute_type3(self, constraints: List[str]) -> CheckResult:
        """Type 3: Value with waiver logic (not typically used for this check)."""
        return self._execute_type1(constraints)
    
    def _execute_type4(self, constraints: List[str]) -> CheckResult:
        """Type 4: Boolean with waiver logic (not typically used for this check)."""
        return self._execute_type1(constraints)
    
    def execute_check(self) -> CheckResult:
        """Execute conformal constraints review check."""
        if self.root is None:
            raise RuntimeError("Checker not initialized. Call init_checker() first.")
        
        try:
            constraints = self._extract_add_pin_constraints()
            checker_type = self.detect_checker_type()
            
            if checker_type == 1:
                return self._execute_type1(constraints)
            elif checker_type == 2:
                return self._execute_type2(constraints)
            elif checker_type == 3:
                return self._execute_type3(constraints)
            elif checker_type == 4:
                return self._execute_type4(constraints)
            else:
                return self._execute_type1(constraints)
        except ConfigurationError as e:
            return e.check_result


def main():
    """Main entry point for the checker."""
    checker = ConformalConstraintsReviewChecker()
    checker.run()


if __name__ == '__main__':
    main()
