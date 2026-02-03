################################################################################
# Script Name: IMP-6-0-0-03.py
#
# Purpose:
#   Confirm all user defined black boxes have port definitions declared (.lib or verilog stub file)
#   - Get black box list from requirements.pattern_items (golden value)
#   - Parse "// Parsing file .../xxx.lib ..." from LEC log
#   - Match each black box with .lib files (case-sensitive containment)
#   - Count missing port definitions (expected = 0)
#   - Create INFO group for each matched black box
#
#
# Logic:
#   - Parse LEC log to extract .lib file parsing commands
#   - Match library files with configured black box patterns
#   - Verify all expected black box libraries are defined
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


class BlackBoxPortDefinitionChecker(BaseChecker):
    """IMP-6-0-0-03: Confirm all user defined black boxes have port definitions declared?   (.lib or verilog stub file)"""
    
    def __init__(self):
        super().__init__(
            check_module="6.0_POST_SYNTHESIS_LEC_CHECK",
            item_id="IMP-6-0-0-03",
            item_desc="Confirm all user defined black boxes have port definitions declared?   (.lib or verilog stub file)"
        )
        self._lib_files: List[str] = []
        self._black_box_matches: Dict[str, List[str]] = {}  # black_box -> [lib files]
    
    def _parse_lib_files(self) -> List[str]:
        """Parse .lib files from LEC log: // Parsing file .../xxx.lib ..."""
        valid_files, missing_files = self.validate_input_files()
        
        lib_files = []
        
        for file_path in valid_files:
            lines = self.read_file(file_path)
            if not lines:
                continue
            
            for line in lines:
                # Match: // Parsing file /path/to/xxx.lib ...
                if '// Parsing file' in line and '.lib' in line:
                    match = re.search(r'// Parsing file\s+(.+\.lib)', line)
                    if match:
                        lib_path = match.group(1).strip()
                        lib_files.append(lib_path)
        
        return lib_files
    
    def _match_black_boxes_with_libs(self, black_boxes: List[str], lib_files: List[str]) -> Tuple[Dict[str, List[str]], List[str]]:
        """Match each black box with .lib files containing its name.
        
        Returns:
            (matches_dict, missing_list)
            matches_dict: {black_box: [lib_file1, lib_file2, ...]}
            missing_list: [black_box1, black_box2, ...] with no .lib match
        """
        matches = {}
        missing = []
        
        for bbox in black_boxes:
            matched_libs = []
            for lib_file in lib_files:
                # Case-sensitive containment check
                if bbox in lib_file:
                    matched_libs.append(lib_file)
            
            if matched_libs:
                matches[bbox] = matched_libs
            else:
                missing.append(bbox)
        
        return matches, missing
    
    def _get_waive_items_with_reasons(self) -> Dict[str, str]:
        """Get waiver items with their reasons."""
        waivers = self.get_waivers()
        if not waivers:
            return {}
        waive_items = waivers.get('waive_items', [])
        if waive_items and isinstance(waive_items[0], dict):
            return {item['name']: item.get('reason', '') for item in waive_items}
        return {item: '' for item in waive_items}
    
    def _execute_type1(self, missing_black_boxes: List[str]) -> CheckResult:
        """Type 1: Boolean check - informational review of black box matches."""
        details = []
        
        # Add INFO items for each black box with its matched .lib files
        for bbox, libs in self._black_box_matches.items():
            for lib in libs:
                details.append(DetailItem(
                    severity=Severity.INFO,
                    name=f"Black box '{bbox}' has port definition",
                    line_number=0,
                    file_path=lib,
                    reason=f"Found in .lib file"
                ))
        
        # Add info about missing ones if any
        if missing_black_boxes:
            for bbox in missing_black_boxes:
                details.append(DetailItem(
                    severity=Severity.INFO,
                    name=f"Black box '{bbox}' - no .lib match found",
                    line_number=0,
                    file_path="",
                    reason="No matching .lib file"
                ))
        
        if not details:
            details.append(DetailItem(
                severity=Severity.INFO,
                name="No black boxes defined in requirements",
                line_number=0,
                file_path="",
                reason=""
            ))
        
        return create_check_result(
            value=len(missing_black_boxes),
            is_pass=True,
            has_pattern_items=False,
            has_waiver_value=False,
            details=details,
            item_desc=self.item_desc,
            default_group_desc="Black box port definitions"
        )
    
    def _execute_type2(self, missing_black_boxes: List[str]) -> CheckResult:
        """Type 2: Value comparison - missing count vs expected (0)."""
        requirements = self.get_requirements()
        expected_value = requirements.get('value', 0)
        actual_value = len(missing_black_boxes)
        
        is_pass = (actual_value == expected_value)
        
        details = []
        
        # Add INFO for matched black boxes
        for bbox, libs in self._black_box_matches.items():
            for lib in libs:
                details.append(DetailItem(
                    severity=Severity.INFO,
                    name=f"'{bbox}' has port definition",
                    line_number=0,
                    file_path=lib,
                    reason=""
                ))
        
        # Add ERROR/WARN for missing ones
        if missing_black_boxes:
            for bbox in missing_black_boxes:
                details.append(DetailItem(
                    severity=Severity.FAIL if not is_pass else Severity.WARN,
                    name=f"'{bbox}' missing port definition",
                    line_number=0,
                    file_path="",
                    reason="No matching .lib file found"
                ))
        
        return create_check_result(
            value=actual_value,
            is_pass=is_pass,
            has_pattern_items=False,
            has_waiver_value=True,
            details=details,
            item_desc=self.item_desc,
            default_group_desc="Black box port definitions"
        )
    
    def _execute_type3(self, missing_black_boxes: List[str]) -> CheckResult:
        """Type 3: Value with waiver logic."""
        requirements = self.get_requirements()
        expected_value = requirements.get('value', 0)
        actual_value = len(missing_black_boxes)
        
        waivers = self.get_waivers()
        waiver_value = waivers.get('value', 'N/A') if waivers else 'N/A'
        waiver_items_dict = self._get_waive_items_with_reasons()
        
        # Check against expected or waiver
        if waiver_value != 'N/A':
            is_pass = (actual_value == waiver_value)
        else:
            is_pass = (actual_value == expected_value)
        
        details = []
        
        # INFO for matched black boxes
        for bbox, libs in self._black_box_matches.items():
            for lib in libs:
                details.append(DetailItem(
                    severity=Severity.INFO,
                    name=f"'{bbox}' has port definition",
                    line_number=0,
                    file_path=lib,
                    reason=""
                ))
        
        # Handle missing black boxes
        for bbox in missing_black_boxes:
            if bbox in waiver_items_dict:
                details.append(DetailItem(
                    severity=Severity.WAIVE,
                    name=f"'{bbox}' missing port definition",
                    line_number=0,
                    file_path="",
                    reason=waiver_items_dict[bbox]
                ))
            else:
                details.append(DetailItem(
                    severity=Severity.FAIL if not is_pass else Severity.WARN,
                    name=f"'{bbox}' missing port definition",
                    line_number=0,
                    file_path="",
                    reason="No matching .lib file found"
                ))
        
        return create_check_result(
            value=actual_value,
            is_pass=is_pass,
            has_pattern_items=False,
            has_waiver_value=True,
            details=details,
            item_desc=self.item_desc,
            default_group_desc="Black box port definitions"
        )
    
    def _execute_type4(self, missing_black_boxes: List[str]) -> CheckResult:
        """Type 4: Boolean with waiver logic."""
        waivers = self.get_waivers()
        waiver_value = waivers.get('value', 'N/A') if waivers else 'N/A'
        waiver_items_dict = self._get_waive_items_with_reasons()
        
        actual_value = len(missing_black_boxes)
        
        # Type 4: pass if waiver_value == 0 or all missing are waived
        if waiver_value == 0:
            is_pass = True
        else:
            # Pass if all missing items are waived
            unwaived_missing = [bbox for bbox in missing_black_boxes if bbox not in waiver_items_dict]
            is_pass = len(unwaived_missing) == 0
        
        details = []
        
        # INFO for matched black boxes
        for bbox, libs in self._black_box_matches.items():
            for lib in libs:
                details.append(DetailItem(
                    severity=Severity.INFO,
                    name=f"'{bbox}' has port definition",
                    line_number=0,
                    file_path=lib,
                    reason=""
                ))
        
        # Handle missing black boxes
        for bbox in missing_black_boxes:
            if bbox in waiver_items_dict:
                details.append(DetailItem(
                    severity=Severity.WAIVE,
                    name=f"'{bbox}' missing port definition",
                    line_number=0,
                    file_path="",
                    reason=waiver_items_dict[bbox]
                ))
            else:
                details.append(DetailItem(
                    severity=Severity.FAIL if not is_pass else Severity.WARN,
                    name=f"'{bbox}' missing port definition",
                    line_number=0,
                    file_path="",
                    reason="No matching .lib file found"
                ))
        
        return create_check_result(
            value=actual_value,
            is_pass=is_pass,
            has_pattern_items=False,
            has_waiver_value=False,
            details=details,
            item_desc=self.item_desc,
            default_group_desc="Black box port definitions"
        )
    
    def execute_check(self) -> CheckResult:
        """Execute black box port definition check.
        
        Logic:
        1. Get black box list from requirements.pattern_items (golden value)
        2. Parse "// Parsing file .../xxx.lib ..." from LEC log
        3. Match each black box with .lib files (case-sensitive containment)
        4. Count missing port definitions (expected = 0)
        5. Create INFO group for each matched black box
        6. Execute type-specific logic based on waiver configuration
        """
        if self.root is None:
            raise RuntimeError("Checker not initialized. Call init_checker() first.")
        
        try:
            # Step 1: Get black box list from requirements
            requirements = self.get_requirements()
            black_boxes = requirements.get('pattern_items', [])
            
            # Step 2: Parse .lib files from LEC log
            self._lib_files = self._parse_lib_files()
            
            # Step 3: Match black boxes with .lib files
            self._black_box_matches, missing_black_boxes = self._match_black_boxes_with_libs(
                black_boxes, self._lib_files
            )
            
            # Step 5-6: Execute type-specific logic
            check_type = self.detect_checker_type()
            
            if check_type == 1:
                return self._execute_type1(missing_black_boxes)
            elif check_type == 2:
                return self._execute_type2(missing_black_boxes)
            elif check_type == 3:
                return self._execute_type3(missing_black_boxes)
            else:  # type 4
                return self._execute_type4(missing_black_boxes)
        
        except ConfigurationError as e:
            return e.check_result


def main():
    """Main entry point for the checker."""
    checker = BlackBoxPortDefinitionChecker()
    checker.run()


if __name__ == '__main__':
    main()

