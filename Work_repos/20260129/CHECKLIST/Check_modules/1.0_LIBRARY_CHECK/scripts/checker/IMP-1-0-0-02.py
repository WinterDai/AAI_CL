################################################################################
# Script Name: IMP-1-0-0-02.py
#
# Purpose:
#   List any forbidden cells (special request from foundry or customers).
#   This is an informational checker that displays configured forbidden cell patterns.
#
#
# Logic:
#   - Extract forbidden cell list from configuration
#   - Check if any forbidden cells are specified
#   - Document special requests from foundry or customers
# Author: yyin
# Date:   2025-11-05
# Updated: 2025-12-01 - Migrated to unified BaseChecker architecture
################################################################################

from pathlib import Path
import sys
from typing import List

# Add common module to path
_SCRIPT_DIR = Path(__file__).resolve().parent
_CHECK_MODULES_DIR = _SCRIPT_DIR.parents[2]  # scripts/checker/ -> scripts/ -> 1.0_LIBRARY_CHECK/
_COMMON_DIR = _CHECK_MODULES_DIR / 'common'
if str(_COMMON_DIR) not in sys.path:
    sys.path.insert(0, str(_COMMON_DIR))

from base_checker import BaseChecker
from output_formatter import DetailItem, Severity, CheckResult, create_check_result


class ForbiddenCellChecker(BaseChecker):
    """IMP-1-0-0-02: List any forbidden cells."""
    
    def __init__(self):
        super().__init__(
            check_module="1.0_LIBRARY_CHECK",
            item_id="IMP-1-0-0-02",
            item_desc="List any forbidden cells (special request from foundry or customers)."
        )
    
    def execute_check(self) -> CheckResult:
        """
        Execute forbidden cell listing check.
        
        This checker doesn't parse input files - it just displays pattern_items
        from the configuration as the list of forbidden cells.
        """
        if self.root is None:
            raise RuntimeError("Checker not initialized. Call init_checker() first.")
        
        # Get pattern_items (forbidden cell patterns)
        requirements = self.get_requirements()
        pattern_items = requirements.get('pattern_items', []) if requirements else []
        
        details = []
        
        if not pattern_items:
            # No forbidden cells configured - show WARN
            details.append(DetailItem(
                severity=Severity.WARN,
                name="",
                line_number=0,
                file_path="N/A",
                reason="Golden value expected but not provided"
            ))
            
            details.append(DetailItem(
                severity=Severity.INFO,
                name="",
                line_number=0,
                file_path="N/A",
                reason="No forbidden cells found in current DATA_INTERFACE.yaml"
            ))
            
            return create_check_result(
                value=0,
                is_pass=True,
                has_pattern_items=False,
                has_waiver_value=False,
                details=details,
                item_desc=self.item_desc
            )
        
        # List forbidden cells as INFO
        for cell_pattern in pattern_items:
            details.append(DetailItem(
                severity=Severity.INFO,
                name=cell_pattern,
                line_number='',
                file_path='',
                reason="Forbidden cell type"
            ))
        
        return create_check_result(
            value=len(pattern_items),
            is_pass=True,
            has_pattern_items=True,
            has_waiver_value=False,
            details=details,
            item_desc=self.item_desc,
            info_groups={
                "INFO01": {
                    "description": "Forbidden Cell Types",
                    "items": pattern_items
                }
            }
        )


def main():
    """Main entry point for the checker."""
    checker = ForbiddenCellChecker()
    checker.run()


if __name__ == '__main__':
    main()
