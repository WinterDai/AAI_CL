################################################################################
# Script Name: IMP-6-0-0-02.py
#
# Purpose:
#   Ensure there are no black box in design.
#
#
# Logic:
#   - Parse black_box.rpt to extract black box instances
#   - List all black box modules found
#   - Report count and details of black boxes
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


class BlackBoxChecker(BaseChecker):
    """IMP-6-0-0-02: Confirm all listed black boxes are intended?"""
    
    def __init__(self):
        super().__init__(
            check_module="6.0_POST_SYNTHESIS_LEC_CHECK",
            item_id="IMP-6-0-0-02",
            item_desc="Confirm all listed black boxes are intended?"
        )
        self._metadata: Dict[str, Dict[str, Any]] = {}
    
    def _parse_input_files(self) -> List[str]:
        """Parse black box report files."""
        valid_files, missing_files = self.validate_input_files()
        
        black_boxes = []
        
        for file_path in valid_files:
            lines = self.read_file(file_path)
            if not lines:
                continue
            
            for line_num, line in enumerate(lines, 1):
                line_stripped = line.strip()
                # Skip header lines and empty lines
                if not line_stripped or line_stripped.startswith('---') or 'Module' in line_stripped:
                    continue
                
                # Parse black box entries (format: module_name)
                if line_stripped:
                    black_box = line_stripped
                    if black_box not in black_boxes:
                        black_boxes.append(black_box)
                        self._metadata[black_box] = {
                            'line_number': line_num,
                            'file_path': str(file_path)
                        }
        
        return black_boxes
    
    def _get_waive_items_with_reasons(self) -> Dict[str, str]:
        """Get waiver items with their reasons."""
        waivers = self.get_waivers()
        if not waivers:
            return {}
        waive_items = waivers.get('waive_items', [])
        if waive_items and isinstance(waive_items[0], dict):
            return {item['name']: item.get('reason', '') for item in waive_items}
        return {item: '' for item in waive_items}
    
    def _execute_type1(self, black_boxes: List[str]) -> CheckResult:
        """Type 1: Boolean check - any black box is FAIL."""
        waivers = self.get_waivers()
        waiver_value = waivers.get('value', 'N/A') if waivers else 'N/A'
        is_waiver_zero = (waiver_value == 0)
        
        details = []
        is_pass = (len(black_boxes) == 0)
        
        if not black_boxes:
            details.append(DetailItem(
                severity=Severity.INFO,
                name="No black boxes found",
                line_number=0,
                file_path="",
                reason="Design is complete"
            ))
        else:
            severity = Severity.INFO if is_waiver_zero else Severity.FAIL
            reason_suffix = "[WAIVED_AS_INFO]" if is_waiver_zero else ""
            for black_box in black_boxes:
                metadata = self._metadata.get(black_box, {})
                details.append(DetailItem(
                    severity=severity,
                    name=black_box,
                    line_number=metadata.get('line_number', ''),
                    file_path=metadata.get('file_path', ''),
                    reason=f"Black box found{reason_suffix}"
                ))
            if is_waiver_zero:
                is_pass = True
        
        # Add waive_items when waiver=0
        if is_waiver_zero and waivers:
            waive_items = waivers.get('waive_items', [])
            for item in waive_items:
                details.append(DetailItem(
                    severity=Severity.INFO,
                    name=item,
                    line_number=0,
                    file_path="N/A",
                    reason="Waiver item[WAIVED_INFO]"
                ))
        
        return create_check_result(
            value=len(black_boxes),
            is_pass=is_pass,
            has_pattern_items=False,
            has_waiver_value=False,
            details=details,
            item_desc=self.item_desc,
            default_group_desc="Black box modules in design"
        )
    
    def _execute_type2(self, black_boxes: List[str]) -> CheckResult:
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
        
        actual_value = len(black_boxes)
        is_pass = (actual_value <= req_value)
        details = []
        
        if not black_boxes:
            details.append(DetailItem(
                severity=Severity.INFO,
                name="No black boxes found",
                line_number=0,
                file_path="",
                reason="Design is complete"
            ))
        else:
            if is_waiver_zero:
                severity = Severity.INFO
                reason_suffix = "[WAIVED_AS_INFO]"
                is_pass = True
            else:
                severity = Severity.FAIL if actual_value > req_value else Severity.INFO
                reason_suffix = ""
            
            for black_box in black_boxes:
                metadata = self._metadata.get(black_box, {})
                details.append(DetailItem(
                    severity=severity,
                    name=black_box,
                    line_number=metadata.get('line_number', ''),
                    file_path=metadata.get('file_path', ''),
                    reason=f"Black box found (requirement: ≤{req_value}){reason_suffix}"
                ))
        
        # Add waive_items when waiver=0
        if is_waiver_zero and waivers:
            waive_items = waivers.get('waive_items', [])
            for item in waive_items:
                details.append(DetailItem(
                    severity=Severity.INFO,
                    name=item,
                    line_number=0,
                    file_path="N/A",
                    reason="Waiver item[WAIVED_INFO]"
                ))
        
        return create_check_result(
            value=actual_value,
            is_pass=is_pass,
            has_pattern_items=False,
            has_waiver_value=False,
            details=details,
            item_desc=self.item_desc,
            default_group_desc=f"Black boxes in design (found: {actual_value}, requirement: â‰¤{req_value})"
        )
    
    def _execute_type3(self, black_boxes: List[str]) -> CheckResult:
        """Type 3: Value comparison with waiver logic."""
        requirements = self.get_requirements()
        req_value = requirements.get('value', 0) if requirements else 0
        try:
            req_value = int(req_value)
        except:
            req_value = 0
        
        waive_items_dict = self._get_waive_items_with_reasons()
        actual_value = len(black_boxes)
        
        details = []
        waived_count = 0
        
        if not black_boxes:
            details.append(DetailItem(
                severity=Severity.INFO,
                name="No black boxes found",
                line_number=0,
                file_path="",
                reason="Design is complete"
            ))
        else:
            for black_box in black_boxes:
                metadata = self._metadata.get(black_box, {})
                if black_box in waive_items_dict:
                    waived_count += 1
                    waive_reason = waive_items_dict[black_box]
                    details.append(DetailItem(
                        severity=Severity.INFO,
                        name=black_box,
                        line_number=metadata.get('line_number', ''),
                        file_path=metadata.get('file_path', ''),
                        reason=f"Waived: {waive_reason}" if waive_reason else "Waived"
                    ))
                else:
                    details.append(DetailItem(
                        severity=Severity.FAIL if (actual_value - waived_count) > req_value else Severity.INFO,
                        name=black_box,
                        line_number=metadata.get('line_number', ''),
                        file_path=metadata.get('file_path', ''),
                        reason=f"Black box found (requirement: â‰¤{req_value})"
                    ))
        
        effective_value = actual_value - waived_count
        is_pass = (effective_value <= req_value)
        
        return create_check_result(
            value=effective_value,
            is_pass=is_pass,
            has_pattern_items=False,
            has_waiver_value=True,
            details=details,
            item_desc=self.item_desc,
            default_group_desc=f"Black boxes (found: {actual_value}, waived: {waived_count}, effective: {effective_value}, requirement: â‰¤{req_value})"
        )
    
    def _execute_type4(self, black_boxes: List[str]) -> CheckResult:
        """Type 4: Boolean check with waiver logic."""
        waive_items_dict = self._get_waive_items_with_reasons()
        
        details = []
        all_waived = True
        
        if not black_boxes:
            details.append(DetailItem(
                severity=Severity.INFO,
                name="No black boxes found",
                line_number=0,
                file_path="",
                reason="Design is complete"
            ))
            all_waived = True
        else:
            for black_box in black_boxes:
                metadata = self._metadata.get(black_box, {})
                if black_box in waive_items_dict:
                    waive_reason = waive_items_dict[black_box]
                    details.append(DetailItem(
                        severity=Severity.INFO,
                        name=black_box,
                        line_number=metadata.get('line_number', ''),
                        file_path=metadata.get('file_path', ''),
                        reason=f"Waived: {waive_reason}" if waive_reason else "Waived"
                    ))
                else:
                    all_waived = False
                    details.append(DetailItem(
                        severity=Severity.FAIL,
                        name=black_box,
                        line_number=metadata.get('line_number', ''),
                        file_path=metadata.get('file_path', ''),
                        reason="Black box found (not waived)"
                    ))
        
        is_pass = all_waived
        
        return create_check_result(
            value=len([bb for bb in black_boxes if bb not in waive_items_dict]),
            is_pass=is_pass,
            has_pattern_items=False,
            has_waiver_value=True,
            details=details,
            item_desc=self.item_desc,
            default_group_desc="Black boxes with waiver check"
        )
    
    def execute_check(self) -> CheckResult:
        """Execute black box check."""
        if self.root is None:
            raise RuntimeError("Checker not initialized. Call init_checker() first.")
        
        try:
            black_boxes = self._parse_input_files()
            checker_type = self.detect_checker_type()
            
            if checker_type == 1:
                return self._execute_type1(black_boxes)
            elif checker_type == 2:
                return self._execute_type2(black_boxes)
            elif checker_type == 3:
                return self._execute_type3(black_boxes)
            elif checker_type == 4:
                return self._execute_type4(black_boxes)
            else:
                return self._execute_type2(black_boxes)
        except ConfigurationError as e:
            return e.check_result


def main():
    """Main entry point for the checker."""
    checker = BlackBoxChecker()
    checker.run()


if __name__ == '__main__':
    main()

