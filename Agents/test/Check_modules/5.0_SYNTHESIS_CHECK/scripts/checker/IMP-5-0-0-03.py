################################################################################
# Script Name: IMP-5-0-0-03.py
#
# Purpose:
#   Confirm target standard cell library corners are correct.
#   Parse qor.rpt to extract library corner and validate against expected value.
#
# Logic:
#   - Extract library corner from "Library domain:" line in qor.rpt
#   - Extract corner pattern (tcond_XXX_T format)
#   - Type 1: Report corner usage (PASS if found or not found)
#   - Type 2: Compare against expected corner value
#   - Type 3/4: Support waiver logic for corner mismatches
#
# Auto Type Detection:
#   Type 1: requirements.value=N/A, waivers.value=N/A/0 → Boolean check
#   Type 2: requirements.value>0, pattern_items exists, waivers.value=N/A/0 → Value comparison
#   Type 3: requirements.value>0, pattern_items exists, waivers.value>0 → Value with waiver logic
#   Type 4: requirements.value=N/A, waivers.value>0 → Boolean with waiver logic
#
# Author: yuyin
# Date: 2025-11-26
################################################################################

from pathlib import Path
import re
import sys
from typing import List, Tuple, Dict, Any, Optional

# Add common module to path
_SCRIPT_DIR = Path(__file__).resolve().parent
_CHECK_MODULES_DIR = _SCRIPT_DIR.parents[2]  # Go up to Check_modules/
_COMMON_DIR = _CHECK_MODULES_DIR / 'common'
if str(_COMMON_DIR) not in sys.path:
    sys.path.insert(0, str(_COMMON_DIR))

from base_checker import BaseChecker, CheckResult, ConfigurationError
from output_formatter import DetailItem, Severity, create_check_result


class LibCornerChecker(BaseChecker):
    """
    Unified checker that auto-detects and handles all 4 checker types.
    
    Check Target: Confirm target standard cell library corners are correct
    
    Type Detection Logic:
    - Type 1: requirements.value=N/A AND waivers.value=N/A/0
    - Type 2: requirements.value>0 AND pattern_items AND waivers.value=N/A/0
    - Type 3: requirements.value>0 AND pattern_items AND waivers.value>0
    - Type 4: requirements.value=N/A AND waivers.value>0
    
    Parsing Logic:
    - Extract library corner from qor.rpt "Library domain:" line
    - Extract corner pattern in format tcond_XXX_T
    - Store corner name and line number
    - Type 1: Report corner usage
    - Type 2: Compare against expected corner (pattern_items[0])
    - Type 3/4: Support waiver logic for mismatches
    """
    
    def __init__(self):
        super().__init__(
            check_module="5.0_SYNTHESIS_CHECK",
            item_id="IMP-5-0-0-03",
            item_desc="Confirm target standard cell library corners are correct?"
        )
        self._corner_metadata: Dict[str, Dict[str, Any]] = {}
        self._expected_corner: Optional[str] = None
    
    # =========================================================================
    # Input File Parsing
    # =========================================================================
    
    def _parse_input_files(self) -> List[str]:
        """
        Parse qor.rpt to extract library corner.
        
        Format: Extract from "Library domain:" line
        Example: "Library domain: tcond_cworst_CCworst_T"
        
        Returns:
            List containing the extracted corner (empty if not found)
        """
        if not self.item_data or 'input_files' not in self.item_data:
            return []
        
        # Validate input files using BaseChecker method
        valid_files, missing_files = self.validate_input_files()
        
        # Store missing files for error reporting
        if missing_files:
            self._corner_metadata['_missing_input_files'] = {
                'files': missing_files,
                'count': len(missing_files)
            }
            # Return empty list - will be handled in execute methods
            return []
        
        # Find qor.rpt
        qor_path = None
        for f in valid_files:
            if f.name.lower() == 'qor.rpt':
                qor_path = f
                break
        
        if not qor_path:
            return []
        
        # Extract corner from qor.rpt
        corner = self._extract_corner_from_qor(qor_path)
        
        if corner:
            return [corner]
        
        return []
    
    def _extract_corner_from_qor(self, qor_path: Path) -> Optional[str]:
        """
        Extract library corner from QoR report.
        
        Args:
            qor_path: Path to qor.rpt file
        
        Returns:
            Corner string if found, None otherwise
        """
        lines = self.read_file(qor_path)
        if not lines:
            return None
        
        for line_num, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith('Library domain:'):
                domain_full_str = stripped.split(':', 1)[1].strip()
                
                # Try to extract tcond_XXX pattern
                m = re.search(r'tcond_(.*?_T)', domain_full_str)
                if m:
                    corner = m.group(1)
                else:
                    # Use raw domain string if no tcond pattern found
                    corner = domain_full_str
                
                # Store metadata
                self._corner_metadata[corner] = {
                    'line_number': line_num,
                    'file_path': str(qor_path),
                    'full_domain': domain_full_str
                }
                
                return corner
        
        return None
    
    def _corner_matches_expected(self, corner: str, expected: str) -> bool:
        """
        Check if corner matches expected value.
        
        Args:
            corner: Actual corner extracted from qor.rpt
            expected: Expected corner from pattern_items
        
        Returns:
            True if matches, False otherwise
        """
        # Direct match
        if corner == expected:
            return True
        
        # Case-insensitive match
        if corner.lower() == expected.lower():
            return True
        
        # Check if expected is substring of corner
        if expected.lower() in corner.lower():
            return True
        
        return False
    
    # =========================================================================
    # Main Execution
    # =========================================================================
    
    def execute_check(self) -> CheckResult:
        """
        Execute check with automatic type detection and handling.
        
        Returns:
            CheckResult
        """
        if self.root is None:
            raise RuntimeError("Checker not initialized. Call init_checker() first.")
        
        try:
            # Get expected corner from pattern_items
            requirements = self.get_requirements()
            pattern_items = requirements.get('pattern_items', []) if requirements else []
            self._expected_corner = pattern_items[0] if pattern_items else None
            
            # Detect checker type (use BaseChecker method)
            checker_type = self.detect_checker_type()
            
            # Parse input files to extract corner
            corners = self._parse_input_files()
            actual_corner = corners[0] if corners else None
            
            # Determine if corner matches expected (for Type 2/3)
            corner_matches = False
            if actual_corner and self._expected_corner:
                corner_matches = self._corner_matches_expected(actual_corner, self._expected_corner)
            
            # Execute based on type
            if checker_type == 1:
                return self._execute_type1(actual_corner)
            elif checker_type == 2:
                return self._execute_type2(actual_corner, corner_matches)
            elif checker_type == 3:
                return self._execute_type3(actual_corner, corner_matches)
            else:  # checker_type == 4
                return self._execute_type4(actual_corner, corner_matches)
        
        except ConfigurationError as e:
            # Return the CheckResult from the exception
            return e.check_result
    
    # =========================================================================
    # Type 1: Boolean Check (No Waiver Logic)
    # =========================================================================
    
    def _execute_type1(self, actual_corner: Optional[str]) -> CheckResult:
        """
        Type 1: requirements.value=N/A, waivers.value=N/A/0
        
        Logic: 
        - Report library corner usage
        - PASS regardless of corner found or not
        - All items shown as INFO
        """
        waivers = self.get_waivers()
        waiver_value = waivers.get('value', 'N/A') if waivers else 'N/A'
        waive_items = waivers.get('waive_items', []) if waivers else []
        
        # Check if waiver=0 (display mode)
        is_waiver_zero = (waiver_value == 0)
        
        # Check for missing input files first
        missing_info = self._corner_metadata.get('_missing_input_files')
        if missing_info:
            return self.create_missing_files_error(missing_info['files'])
        
        details = []
        
        # Case 1: No corner found
        if not actual_corner:
            details.append(DetailItem(
                severity=Severity.INFO,
                name="No library corner detected",
                line_number=0,
                file_path="N/A",
                reason="Library corner information not found in qor.rpt"
            ))
            
            return create_check_result(
                value=0,
                is_pass=True,
                has_pattern_items=False,
                has_waiver_value=bool(waive_items),
                details=details,
                item_desc=self.item_desc,
                info_groups={
                    "INFO01": {
                        "description": "Library corner not detected in QoR",
                        "items": ["No library corner detected"]
                    }
                }
            )
        
        # Case 2: Corner found - report as INFO
        metadata = self._corner_metadata.get(actual_corner, {})
        details.append(DetailItem(
            severity=Severity.INFO,
            name=actual_corner,
            line_number=metadata.get('line_number', ''),
            file_path=metadata.get('file_path', ''),
            reason="Library corner is being used"
        ))
        
        # Add waive_items as INFO (display only)
        if waive_items and not is_waiver_zero:
            for item in waive_items:
                details.append(DetailItem(
                    severity=Severity.INFO,
                    name=str(item),
                    line_number=0,
                    file_path="N/A",
                    reason="Waiver"
                ))
        
        if is_waiver_zero:
            # waiver=0: Force PASS, add waive_items
            for item in waive_items:
                details.append(DetailItem(
                    severity=Severity.INFO,
                    name=str(item),
                    line_number=0,
                    file_path="N/A",
                    reason="Waiver item[WAIVED_INFO]"
                ))
        
        # Create info groups
        info_groups = {
            "INFO01": {
                "description": "Library corner detected in synthesis",
                "items": [actual_corner]
            }
        }
        
        return create_check_result(
            value=1,
            is_pass=True,
            has_pattern_items=False,
            has_waiver_value=bool(waive_items),
            details=details,
            info_groups=info_groups,
            item_desc=self.item_desc
        )
    
    # =========================================================================
    # Type 2: Numeric Comparison (No Waiver Logic)
    # =========================================================================
    
    def _execute_type2(self, actual_corner: Optional[str], corner_matches: bool) -> CheckResult:
        """
        Type 2: requirements.value>0, pattern_items exists, waivers.value=N/A/0
        
        Logic: 
        - Compare actual corner against expected corner
        - PASS if matches, FAIL if doesn't match
        - Report error if corner not found but expected
        """
        waivers = self.get_waivers()
        waiver_value = waivers.get('value', 'N/A') if waivers else 'N/A'
        waive_items = waivers.get('waive_items', []) if waivers else []
        
        # Check if waiver=0 (display mode)
        is_waiver_zero = (waiver_value == 0)
        
        # Check for missing input files first
        missing_info = self._corner_metadata.get('_missing_input_files')
        if missing_info:
            return self.create_missing_files_error(missing_info['files'])
        
        details = []
        
        # Case 1: No corner found but expected value configured
        if not actual_corner:
            if self._expected_corner:
                details.append(DetailItem(
                    severity=Severity.FAIL,
                    name="Missing corner information",
                    line_number=0,
                    file_path="N/A",
                    reason=f"Information related to library corner is missing in logs and reports, expected {self._expected_corner}"
                ))
                
                return create_check_result(
                    value=0,
                    is_pass=False,
                    has_pattern_items=True,
                    has_waiver_value=bool(waive_items),
                    details=details,
                    item_desc=self.item_desc,
                    error_groups={
                        "ERROR01": {
                            "description": "Library corner information missing",
                            "items": ["Missing corner information"]
                        }
                    }
                )
            else:
                # No expected value configured - PASS
                return create_check_result(
                    value=0,
                    is_pass=True,
                    has_pattern_items=False,
                    has_waiver_value=bool(waive_items),
                    details=[],
                    item_desc=self.item_desc
                )
        
        # Case 2: No expected value configured but corner found
        if not self._expected_corner:
            metadata = self._corner_metadata.get(actual_corner, {})
            details.append(DetailItem(
                severity=Severity.WARN,
                name="Golden value expected but not provided",
                line_number=0,
                file_path="",
                reason=""
            ))
            details.append(DetailItem(
                severity=Severity.INFO,
                name=actual_corner,
                line_number=metadata.get('line_number', ''),
                file_path=metadata.get('file_path', ''),
                reason="Library corner used and golden value expected but not provided"
            ))
            
            return create_check_result(
                value=0,
                is_pass=True,
                has_pattern_items=False,
                has_waiver_value=bool(waive_items),
                details=details,
                item_desc=self.item_desc
            )
        
        # Case 3: Both actual and expected exist - compare
        metadata = self._corner_metadata.get(actual_corner, {})
        
        if is_waiver_zero:
            # waiver=0: Force PASS, show as INFO
            details.append(DetailItem(
                severity=Severity.INFO,
                name=actual_corner,
                line_number=metadata.get('line_number', ''),
                file_path=metadata.get('file_path', ''),
                reason=f"Corner check waived (expected: {self._expected_corner})[WAIVED_AS_INFO]"
            ))
            
            for item in waive_items:
                details.append(DetailItem(
                    severity=Severity.INFO,
                    name=str(item),
                    line_number=0,
                    file_path="N/A",
                    reason="Waiver item[WAIVED_INFO]"
                ))
            
            is_pass = True
        elif corner_matches:
            # Corner matches - PASS
            details.append(DetailItem(
                severity=Severity.INFO,
                name=actual_corner,
                line_number=metadata.get('line_number', ''),
                file_path=metadata.get('file_path', ''),
                reason="Library corner matches expected"
            ))
            is_pass = True
        else:
            # Corner doesn't match - FAIL
            details.append(DetailItem(
                severity=Severity.FAIL,
                name=actual_corner,
                line_number=metadata.get('line_number', ''),
                file_path=metadata.get('file_path', ''),
                reason=f"Target standard cell library corners aren't correct and expected {self._expected_corner}"
            ))
            is_pass = False
        
        error_groups = None
        if not is_pass and not is_waiver_zero:
            error_groups = {
                "ERROR01": {
                    "description": "Library corner doesn't match expected value",
                    "items": [actual_corner]
                }
            }
        
        return create_check_result(
            value=1 if actual_corner else 0,
            is_pass=is_pass,
            has_pattern_items=True,
            has_waiver_value=bool(waive_items),
            details=details,
            error_groups=error_groups,
            item_desc=self.item_desc
        )
    
    # =========================================================================
    # Type 3: Numeric Comparison WITH Waiver Logic
    # =========================================================================
    
    def _execute_type3(self, actual_corner: Optional[str], corner_matches: bool) -> CheckResult:
        """
        Type 3: requirements.value>0, pattern_items exists, waivers.value>0
        
        Logic: 
        - Compare actual corner against expected corner
        - Support waiver for corner mismatches
        - PASS if matches or waived
        - FAIL if unwaived mismatch
        """
        waivers = self.get_waivers()
        waive_items_dict = self._get_waive_items_with_reasons()
        waive_items = list(waive_items_dict.keys())
        
        # Check for missing input files first
        missing_info = self._corner_metadata.get('_missing_input_files')
        if missing_info:
            return self.create_missing_files_error(missing_info['files'])
        
        details = []
        
        # Case 1: No corner found but expected
        if not actual_corner:
            if self._expected_corner:
                details.append(DetailItem(
                    severity=Severity.FAIL,
                    name="Missing corner information",
                    line_number=0,
                    file_path="N/A",
                    reason=f"Information related to library corner is missing, expected {self._expected_corner}"
                ))
                
                return create_check_result(
                    value=0,
                    is_pass=False,
                    has_pattern_items=True,
                    has_waiver_value=True,
                    details=details,
                    item_desc=self.item_desc,
                    error_groups={
                        "ERROR01": {
                            "description": "Library corner information missing",
                            "items": ["Missing corner information"]
                        }
                    }
                )
        
        # Case 2: Corner found - check if matches or waived
        metadata = self._corner_metadata.get(actual_corner, {})
        is_waived = actual_corner in waive_items
        
        if corner_matches:
            # Matches - PASS with INFO
            details.append(DetailItem(
                severity=Severity.INFO,
                name=actual_corner,
                line_number=metadata.get('line_number', ''),
                file_path=metadata.get('file_path', ''),
                reason="Library corner matches expected"
            ))
            is_pass = True
        elif is_waived:
            # Doesn't match but waived - PASS with INFO
            waiver_reason = waive_items_dict.get(actual_corner, '')
            reason = f"{waiver_reason}[WAIVER]" if waiver_reason else "Corner mismatch waived[WAIVER]"
            details.append(DetailItem(
                severity=Severity.INFO,
                name=actual_corner,
                line_number=metadata.get('line_number', ''),
                file_path=metadata.get('file_path', ''),
                reason=reason
            ))
            is_pass = True
        else:
            # Doesn't match and not waived - FAIL
            details.append(DetailItem(
                severity=Severity.FAIL,
                name=actual_corner,
                line_number=metadata.get('line_number', ''),
                file_path=metadata.get('file_path', ''),
                reason=f"Target standard cell library corners aren't correct and expected {self._expected_corner}"
            ))
            is_pass = False
        
        # Check for unused waivers
        unused_waivers = [item for item in waive_items if item != actual_corner]
        for item in unused_waivers:
            details.append(DetailItem(
                severity=Severity.WARN,
                name=item,
                line_number='',
                file_path='',
                reason="Waived item not found in check[WAIVER]"
            ))
        
        # Create groups
        error_groups = None
        warn_groups = None
        info_groups = None
        
        if not is_pass:
            error_groups = {
                "ERROR01": {
                    "description": "Unwaived library corner mismatch",
                    "items": [actual_corner]
                }
            }
        
        if unused_waivers:
            warn_groups = {
                "WARN01": {
                    "description": "Unused waivers",
                    "items": unused_waivers
                }
            }
        
        if is_waived or corner_matches:
            info_groups = {
                "INFO01": {
                    "description": "Library corner status",
                    "items": [actual_corner]
                }
            }
        
        return create_check_result(
            value=1 if actual_corner else 0,
            is_pass=is_pass,
            has_pattern_items=True,
            has_waiver_value=True,
            details=details,
            error_groups=error_groups,
            warn_groups=warn_groups,
            info_groups=info_groups,
            item_desc=self.item_desc
        )
    
    # =========================================================================
    # Type 4: Boolean Check WITH Waiver Logic
    # =========================================================================
    
    def _execute_type4(self, actual_corner: Optional[str], corner_matches: bool) -> CheckResult:
        """
        Type 4: requirements.value=N/A, waivers.value>0
        
        Logic: 
        - Boolean check with waiver support
        - Report corner status with waiver classification
        """
        waivers = self.get_waivers()
        waive_items_dict = self._get_waive_items_with_reasons()
        waive_items = list(waive_items_dict.keys())
        
        # Check for missing input files first
        missing_info = self._corner_metadata.get('_missing_input_files')
        if missing_info:
            return self.create_missing_files_error(missing_info['files'])
        
        details = []
        
        # No violations for Type 4 - just report status
        if actual_corner:
            metadata = self._corner_metadata.get(actual_corner, {})
            is_waived = actual_corner in waive_items
            
            if is_waived:
                waiver_reason = waive_items_dict.get(actual_corner, '')
                reason = f"{waiver_reason}[WAIVER]" if waiver_reason else "Waived[WAIVER]"
                severity = Severity.INFO
            else:
                reason = "Library corner is being used"
                severity = Severity.INFO
            
            details.append(DetailItem(
                severity=severity,
                name=actual_corner,
                line_number=metadata.get('line_number', ''),
                file_path=metadata.get('file_path', ''),
                reason=reason
            ))
        
        # Check for unused waivers
        unused_waivers = [item for item in waive_items if item != actual_corner]
        for item in unused_waivers:
            details.append(DetailItem(
                severity=Severity.WARN,
                name=item,
                line_number='',
                file_path='',
                reason="Waived item not found in check[WAIVER]"
            ))
        
        warn_groups = None
        info_groups = None
        
        if unused_waivers:
            warn_groups = {
                "WARN01": {
                    "description": "Unused waivers",
                    "items": unused_waivers
                }
            }
        
        if actual_corner:
            info_groups = {
                "INFO01": {
                    "description": "Library corner detected",
                    "items": [actual_corner]
                }
            }
        
        return create_check_result(
            value="N/A",
            is_pass=True,
            has_pattern_items=False,
            has_waiver_value=True,
            details=details,
            warn_groups=warn_groups,
            info_groups=info_groups,
            item_desc=self.item_desc
        )
    
    # =========================================================================
    # Helper Methods
    # =========================================================================
    
    def _get_waive_items_with_reasons(self) -> Dict[str, str]:
        """
        Get waive items with their reasons.
        
        Supports both formats:
        - List of dicts: [{"name": "item", "reason": "why"}]
        - List of strings: ["item ; # reason", "item, # reason"]
        
        Returns:
            Dict mapping waive_item to reason string
        """
        waivers = self.get_waivers()
        if not waivers:
            return {}
        
        waive_items = waivers.get('waive_items', [])
        
        # If waive_items is a list of dicts with 'name' and 'reason'
        if waive_items and isinstance(waive_items[0], dict):
            return {item['name']: item.get('reason', '') for item in waive_items}
        
        # If waive_items is a simple list of strings
        result = {}
        for item in waive_items:
            item_str = str(item).strip()
            # Support both comma and semicolon separators
            if ';' in item_str:
                parts = item_str.split(';', 1)
                name = parts[0].strip()
                reason = parts[1].strip() if len(parts) > 1 else ""
                if reason.startswith('#'):
                    reason = reason[1:].strip()
                result[name] = reason
            elif ',' in item_str:
                parts = item_str.split(',', 1)
                name = parts[0].strip()
                reason = parts[1].strip() if len(parts) > 1 else ""
                if reason.startswith('#'):
                    reason = reason[1:].strip()
                result[name] = reason
            else:
                result[item_str] = ""
        
        return result


def main():
    """Main entry point for the checker."""
    checker = LibCornerChecker()
    checker.run()


if __name__ == '__main__':
    main()
