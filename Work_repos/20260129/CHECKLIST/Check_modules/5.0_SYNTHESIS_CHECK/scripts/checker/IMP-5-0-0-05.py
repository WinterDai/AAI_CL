################################################################################
# Script Name: IMP-5-0-0-05.py
#
# Purpose:
#   Confirm unresolved references in synthesis are either none or properly waived.
#   Parse synthesis log files to extract unresolved reference names.
#
# Logic:
#   - Extract unresolved references from "Check Design Report" section in logs
#   - Type 1: Report reference status (PASS if none found or some found)
#   - Type 2: Compare against expected count (pattern_items)
#   - Type 3/4: Support waiver logic for unresolved references
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


class UnresolvedRefsChecker(BaseChecker):
    """
    Unified checker that auto-detects and handles all 4 checker types.
    
    Check Target: Confirm unresolved references are none or properly waived
    
    Type Detection Logic:
    - Type 1: requirements.value=N/A AND waivers.value=N/A/0
    - Type 2: requirements.value>0 AND pattern_items AND waivers.value=N/A/0
    - Type 3: requirements.value>0 AND pattern_items AND waivers.value>0
    - Type 4: requirements.value=N/A AND waivers.value>0
    
    Parsing Logic:
    - Scan synthesis log files for "Check Design Report" section
    - Extract unresolved references from "hinst:" lines
    - Store reference name and line number
    - Type 1: Report reference status
    - Type 2: Compare count against expected (pattern_items[0])
    - Type 3/4: Support waiver logic for references
    """
    
    def __init__(self):
        super().__init__(
            check_module="5.0_SYNTHESIS_CHECK",
            item_id="IMP-5-0-0-05",
            item_desc="Confirm Unresolved References are none?"
        )
        self._ref_metadata: Dict[str, Dict[str, Any]] = {}
    
    # =========================================================================
    # Input File Parsing
    # =========================================================================
    
    def _parse_input_files(self) -> List[str]:
        """
        Parse synthesis log files to extract unresolved references.
        
        Format: Extract from "Check Design Report" section
        Example: "hinst: ref_name"
        
        Returns:
            List of unresolved reference names
        """
        if not self.item_data or 'input_files' not in self.item_data:
            return []
        
        # Validate input files using BaseChecker method
        valid_files, missing_files = self.validate_input_files()
        
        # Store missing files for error reporting
        if missing_files:
            self._ref_metadata['_missing_input_files'] = {
                'files': missing_files,
                'count': len(missing_files)
            }
            return []
        
        # Find log files
        log_paths = [f for f in valid_files if f.suffix.lower() == '.log']
        
        if not log_paths:
            return []
        
        # Extract unresolved references from all logs
        unresolved_refs = []
        has_check_design = False
        
        for log_path in log_paths:
            refs_dict, has_report = self._extract_unresolved_refs_from_log(log_path)
            
            if has_report:
                has_check_design = True
            
            # Add references to list and store metadata
            for ref_name, line_num in refs_dict.items():
                if ref_name not in self._ref_metadata:
                    unresolved_refs.append(ref_name)
                    self._ref_metadata[ref_name] = {
                        'line_number': line_num,
                        'file_path': str(log_path)
                    }
        
        # Store whether Check Design Report was found
        if not has_check_design:
            self._ref_metadata['_no_check_design'] = True
        
        return unresolved_refs
    
    def _extract_unresolved_refs_from_log(self, log_path: Path) -> Tuple[Dict[str, int], bool]:
        """
        Extract unresolved references from a synthesis log file.
        
        Args:
            log_path: Path to synthesis log file
        
        Returns:
            Tuple of (unresolved_refs_dict, has_check_design)
            - unresolved_refs_dict: Dict mapping reference name to line number
            - has_check_design: True if "Check Design Report" was found
        """
        lines = self.read_file(log_path)
        if not lines:
            return {}, False
        
        unresolved_refs: Dict[str, int] = {}
        has_check_design = False
        
        # Regex patterns
        check_design_pattern = re.compile(r'Check\s+Design\s+Report.*\(c\)', re.IGNORECASE)
        unresolved_section_pattern = re.compile(r'Unresolved\s+References.*Empty\s+Modules', re.IGNORECASE)
        no_unresolved_pattern = re.compile(r'No\s+unresolved\s+references\s+in\s+design', re.IGNORECASE)
        has_unresolved_pattern = re.compile(r"design\s+\S+\s+has\s+the\s+following\s+unresolved\s+references", re.IGNORECASE)
        total_unresolved_pattern = re.compile(r'Total\s+number\s+of\s+unresolved\s+references\s+in\s+design:\s*(\d+)', re.IGNORECASE)
        hinst_pattern = re.compile(r'hinst:\s*(\S+)', re.IGNORECASE)
        
        in_check_design = False
        in_unresolved_section = False
        current_design_has_unresolved = False
        
        for idx, line in enumerate(lines, start=1):
            # Detect Check Design Report
            if check_design_pattern.search(line):
                has_check_design = True
                in_check_design = True
                in_unresolved_section = False
                current_design_has_unresolved = False
                continue
            
            # Look for unresolved section
            if in_check_design and unresolved_section_pattern.search(line):
                in_unresolved_section = True
                continue
            
            # Check for no unresolved references
            if in_unresolved_section and no_unresolved_pattern.search(line):
                in_unresolved_section = False
                in_check_design = False
                continue
            
            # Check for design has unresolved references
            if in_unresolved_section and has_unresolved_pattern.search(line):
                current_design_has_unresolved = True
                continue
            
            # Extract unresolved reference names
            if in_unresolved_section and current_design_has_unresolved:
                # Check for total count (end of unresolved references list)
                if total_unresolved_pattern.search(line):
                    in_unresolved_section = False
                    in_check_design = False
                    current_design_has_unresolved = False
                    continue
                
                # Extract hinst: reference_name pattern
                hinst_match = hinst_pattern.search(line)
                if hinst_match:
                    ref_name = hinst_match.group(1).strip()
                    if ref_name and ref_name not in unresolved_refs:
                        unresolved_refs[ref_name] = idx
                    continue
            
            # Exit check design section if we hit a new major section
            if in_check_design and line.strip() and line.strip()[0].isupper() and '=' * 5 in line:
                in_check_design = False
                in_unresolved_section = False
        
        return unresolved_refs, has_check_design
    
    # =========================================================================
    # Main Execution
    # =========================================================================
    
    def execute_check(self) -> CheckResult:
        """
        Execute check with automatic type detection and handling.
        
        Returns:
            CheckResult
        """
        try:
            if self.root is None:
                raise RuntimeError("Checker not initialized. Call init_checker() first.")
            
            # Detect checker type (use BaseChecker method)
            checker_type = self.detect_checker_type()
            
            # Parse input files to extract unresolved references
            unresolved_refs = self._parse_input_files()
            
            # Execute based on type
            if checker_type == 1:
                return self._execute_type1(unresolved_refs)
            elif checker_type == 2:
                return self._execute_type2(unresolved_refs)
            elif checker_type == 3:
                return self._execute_type3(unresolved_refs)
            else:  # checker_type == 4
                return self._execute_type4(unresolved_refs)
        except ConfigurationError as e:
            return e.check_result
    
    # =========================================================================
    # Type 1: Boolean Check (No Waiver Logic)
    # =========================================================================
    
    def _execute_type1(self, unresolved_refs: List[str]) -> CheckResult:
        """
        Type 1: requirements.value=N/A, waivers.value=N/A/0
        
        Logic: 
        - Report unresolved reference status
        - PASS regardless of references found or not
        - All items shown as INFO
        """
        waivers = self.get_waivers()
        waiver_value = waivers.get('value', 'N/A') if waivers else 'N/A'
        waive_items = waivers.get('waive_items', []) if waivers else []
        
        # Check if waiver=0 (display mode)
        is_waiver_zero = (waiver_value == 0)
        
        # Check for missing input files first
        missing_info = self._ref_metadata.get('_missing_input_files')
        if missing_info:
            return self.create_missing_files_error(missing_info['files'])
        
        # Check for missing Check Design Report
        if self._ref_metadata.get('_no_check_design'):
            details = [DetailItem(
                severity=Severity.FAIL,
                name="Check Design Report not found",
                line_number=0,
                file_path="N/A",
                reason="No 'Check Design Report' found in synthesis logs"
            )]
            
            return create_check_result(
                value=0,
                is_pass=False,
                has_pattern_items=False,
                has_waiver_value=bool(waive_items),
                details=details,
                item_desc=self.item_desc,
                error_groups={
                    "ERROR01": {
                        "description": "Check Design Report missing",
                        "items": ["Check Design Report not found"]
                    }
                }
            )
        
        details = []
        
        # Case 1: No unresolved references found - PASS
        if not unresolved_refs:
            details.append(DetailItem(
                severity=Severity.INFO,
                name="",
                line_number=0,
                file_path="",
                reason="No unresolved references found in synthesis logs"
            ))
            
            # Add waive_items as INFO if configured
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
                for item in waive_items:
                    details.append(DetailItem(
                        severity=Severity.INFO,
                        name=str(item),
                        line_number=0,
                        file_path="N/A",
                        reason="Waiver item[WAIVED_INFO]"
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
                        "description": "Check result",
                        "items": []
                    }
                }
            )
        
        # Case 2: Unresolved references found - report as INFO
        for ref in unresolved_refs:
            metadata = self._ref_metadata.get(ref, {})
            details.append(DetailItem(
                severity=Severity.INFO,
                name=ref,
                line_number=metadata.get('line_number', ''),
                file_path=metadata.get('file_path', ''),
                reason="Unresolved reference detected"
            ))
        
        # Add waive_items as INFO
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
                "description": "Unresolved references detected",
                "items": unresolved_refs
            }
        }
        
        return create_check_result(
            value=len(unresolved_refs),
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
    
    def _execute_type2(self, unresolved_refs: List[str]) -> CheckResult:
        """
        Type 2: requirements.value>0, pattern_items exists, waivers.value=N/A/0
        
        Logic: 
        - Compare unresolved reference count against expected count
        - PASS if count matches expected (pattern_items[0])
        - FAIL if count doesn't match
        """
        requirements = self.get_requirements()
        pattern_items = requirements.get('pattern_items', []) if requirements else []
        expected_count = int(pattern_items[0]) if pattern_items else 0
        
        waivers = self.get_waivers()
        waiver_value = waivers.get('value', 'N/A') if waivers else 'N/A'
        waive_items = waivers.get('waive_items', []) if waivers else []
        
        # Check if waiver=0 (display mode)
        is_waiver_zero = (waiver_value == 0)
        
        # Check for missing input files first
        missing_info = self._ref_metadata.get('_missing_input_files')
        if missing_info:
            return self.create_missing_files_error(missing_info['files'])
        
        # Check for missing Check Design Report
        if self._ref_metadata.get('_no_check_design'):
            details = [DetailItem(
                severity=Severity.FAIL,
                name="Check Design Report not found",
                line_number=0,
                file_path="N/A",
                reason="No 'Check Design Report' found in synthesis logs"
            )]
            
            return create_check_result(
                value=0,
                is_pass=False,
                has_pattern_items=True,
                has_waiver_value=bool(waive_items),
                details=details,
                item_desc=self.item_desc,
                error_groups={
                    "ERROR01": {
                        "description": "Check Design Report missing",
                        "items": ["Check Design Report not found"]
                    }
                }
            )
        
        details = []
        actual_count = len(unresolved_refs)
        
        if is_waiver_zero:
            # waiver=0: Force PASS, show as INFO
            for ref in unresolved_refs:
                metadata = self._ref_metadata.get(ref, {})
                details.append(DetailItem(
                    severity=Severity.INFO,
                    name=ref,
                    line_number=metadata.get('line_number', ''),
                    file_path=metadata.get('file_path', ''),
                    reason=f"Unresolved reference count check waived (expected: {expected_count})[WAIVED_AS_INFO]"
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
        elif actual_count == expected_count:
            # Count matches - PASS
            if unresolved_refs:
                for ref in unresolved_refs:
                    metadata = self._ref_metadata.get(ref, {})
                    details.append(DetailItem(
                        severity=Severity.INFO,
                        name=ref,
                        line_number=metadata.get('line_number', ''),
                        file_path=metadata.get('file_path', ''),
                        reason="Unresolved reference count matches expected"
                    ))
            else:
                details.append(DetailItem(
                    severity=Severity.INFO,
                    name="",
                    line_number=0,
                    file_path="",
                    reason=f"No unresolved references found (expected: {expected_count})"
                ))
            is_pass = True
        else:
            # Count doesn't match - FAIL
            for ref in unresolved_refs:
                metadata = self._ref_metadata.get(ref, {})
                details.append(DetailItem(
                    severity=Severity.FAIL,
                    name=ref,
                    line_number=metadata.get('line_number', ''),
                    file_path=metadata.get('file_path', ''),
                    reason=f"Unresolved reference count {actual_count} doesn't match expected {expected_count}"
                ))
            
            if not unresolved_refs:
                details.append(DetailItem(
                    severity=Severity.FAIL,
                    name="",
                    line_number=0,
                    file_path="",
                    reason=f"No unresolved references found but expected {expected_count}"
                ))
            
            is_pass = False
        
        error_groups = None
        if not is_pass and not is_waiver_zero:
            error_groups = {
                "ERROR01": {
                    "description": f"Unresolved reference count mismatch (found: {actual_count}, expected: {expected_count})",
                    "items": unresolved_refs if unresolved_refs else ["No references found"]
                }
            }
        
        return create_check_result(
            value=actual_count,
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
    
    def _execute_type3(self, unresolved_refs: List[str]) -> CheckResult:
        """
        Type 3: requirements.value>0, pattern_items exists, waivers.value>0
        
        Logic: 
        - Compare unresolved reference count against expected
        - Support waiver for specific references
        - PASS if count matches or all extras are waived
        - FAIL if unwaived excess references
        """
        requirements = self.get_requirements()
        pattern_items = requirements.get('pattern_items', []) if requirements else []
        expected_count = int(pattern_items[0]) if pattern_items else 0
        
        waivers = self.get_waivers()
        waive_items_dict = self._get_waive_items_with_reasons()
        waive_items = list(waive_items_dict.keys())
        
        # Check for missing input files first
        missing_info = self._ref_metadata.get('_missing_input_files')
        if missing_info:
            return self.create_missing_files_error(missing_info['files'])
        
        # Check for missing Check Design Report
        if self._ref_metadata.get('_no_check_design'):
            details = [DetailItem(
                severity=Severity.FAIL,
                name="Check Design Report not found",
                line_number=0,
                file_path="N/A",
                reason="No 'Check Design Report' found in synthesis logs"
            )]
            
            return create_check_result(
                value=0,
                is_pass=False,
                has_pattern_items=True,
                has_waiver_value=True,
                details=details,
                item_desc=self.item_desc,
                error_groups={
                    "ERROR01": {
                        "description": "Check Design Report missing",
                        "items": ["Check Design Report not found"]
                    }
                }
            )
        
        details = []
        actual_count = len(unresolved_refs)
        
        # Separate waived and unwaived references
        waived_refs = [ref for ref in unresolved_refs if ref in waive_items]
        unwaived_refs = [ref for ref in unresolved_refs if ref not in waive_items]
        
        # Add unwaived references as FAIL
        for ref in unwaived_refs:
            metadata = self._ref_metadata.get(ref, {})
            details.append(DetailItem(
                severity=Severity.FAIL,
                name=ref,
                line_number=metadata.get('line_number', ''),
                file_path=metadata.get('file_path', ''),
                reason="Unresolved reference is NOT explained"
            ))
        
        # Add waived references as INFO
        for ref in waived_refs:
            metadata = self._ref_metadata.get(ref, {})
            waiver_reason = waive_items_dict.get(ref, '')
            reason = f"{waiver_reason}[WAIVER]" if waiver_reason else "Unresolved reference waived[WAIVER]"
            details.append(DetailItem(
                severity=Severity.INFO,
                name=ref,
                line_number=metadata.get('line_number', ''),
                file_path=metadata.get('file_path', ''),
                reason=reason
            ))
        
        # Check for unused waivers
        unused_waivers = [item for item in waive_items if item not in unresolved_refs]
        for item in unused_waivers:
            details.append(DetailItem(
                severity=Severity.WARN,
                name=item,
                line_number='',
                file_path='',
                reason="Waived item not found in check[WAIVER]"
            ))
        
        # Determine pass/fail
        is_pass = (len(unwaived_refs) == 0)
        
        # Create groups
        error_groups = None
        warn_groups = None
        info_groups = None
        
        if not is_pass:
            error_groups = {
                "ERROR01": {
                    "description": "Unresolved references not explained",
                    "items": unwaived_refs
                }
            }
        
        if unused_waivers:
            warn_groups = {
                "WARN01": {
                    "description": "Waived items not found in check",
                    "items": unused_waivers
                }
            }
        
        if waived_refs:
            info_groups = {
                "INFO01": {
                    "description": "Unresolved references waived",
                    "items": waived_refs
                }
            }
        
        return create_check_result(
            value=actual_count,
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
    
    def _execute_type4(self, unresolved_refs: List[str]) -> CheckResult:
        """
        Type 4: requirements.value=N/A, waivers.value>0
        
        Logic: 
        - Boolean check with waiver support
        - PASS if no unwaived references
        - FAIL if unwaived references exist
        """
        waivers = self.get_waivers()
        waive_items_dict = self._get_waive_items_with_reasons()
        waive_items = list(waive_items_dict.keys())
        
        # Check for missing input files first
        missing_info = self._ref_metadata.get('_missing_input_files')
        if missing_info:
            return self.create_missing_files_error(missing_info['files'])
        
        # Check for missing Check Design Report
        if self._ref_metadata.get('_no_check_design'):
            details = [DetailItem(
                severity=Severity.FAIL,
                name="Check Design Report not found",
                line_number=0,
                file_path="N/A",
                reason="No 'Check Design Report' found in synthesis logs"
            )]
            
            return create_check_result(
                value=0,
                is_pass=False,
                has_pattern_items=False,
                has_waiver_value=True,
                details=details,
                item_desc=self.item_desc,
                error_groups={
                    "ERROR01": {
                        "description": "Check Design Report missing",
                        "items": ["Check Design Report not found"]
                    }
                }
            )
        
        details = []
        
        # Separate waived and unwaived references
        waived_refs = [ref for ref in unresolved_refs if ref in waive_items]
        unwaived_refs = [ref for ref in unresolved_refs if ref not in waive_items]
        
        # Case 1: No unresolved references at all - PASS
        if not unresolved_refs:
            details.append(DetailItem(
                severity=Severity.INFO,
                name="",
                line_number=0,
                file_path="",
                reason="No unresolved references found in synthesis logs"
            ))
            
            info_groups = {
                "INFO01": {
                    "description": "Check result",
                    "items": []
                }
            }
        else:
            # Add unwaived references as FAIL
            for ref in unwaived_refs:
                metadata = self._ref_metadata.get(ref, {})
                details.append(DetailItem(
                    severity=Severity.FAIL,
                    name=ref,
                    line_number=metadata.get('line_number', ''),
                    file_path=metadata.get('file_path', ''),
                    reason="Unresolved reference is NOT explained"
                ))
            
            # Add waived references as INFO
            for ref in waived_refs:
                metadata = self._ref_metadata.get(ref, {})
                waiver_reason = waive_items_dict.get(ref, '')
                reason = f"{waiver_reason}[WAIVER]" if waiver_reason else "Unresolved reference waived[WAIVER]"
                details.append(DetailItem(
                    severity=Severity.INFO,
                    name=ref,
                    line_number=metadata.get('line_number', ''),
                    file_path=metadata.get('file_path', ''),
                    reason=reason
                ))
            
            info_groups = None
            if waived_refs:
                info_groups = {
                    "INFO01": {
                        "description": "Unresolved references waived",
                        "items": waived_refs
                    }
                }
        
        # Check for unused waivers
        unused_waivers = [item for item in waive_items if item not in unresolved_refs]
        for item in unused_waivers:
            details.append(DetailItem(
                severity=Severity.WARN,
                name=item,
                line_number='',
                file_path='',
                reason="Waived item not found in check[WAIVER]"
            ))
        
        # Determine pass/fail
        is_pass = (len(unwaived_refs) == 0)
        
        # Create groups
        error_groups = None
        warn_groups = None
        
        if not is_pass:
            error_groups = {
                "ERROR01": {
                    "description": "Unresolved references not explained",
                    "items": unwaived_refs
                }
            }
        
        if unused_waivers:
            warn_groups = {
                "WARN01": {
                    "description": "Waived items not found in check",
                    "items": unused_waivers
                }
            }
        
        return create_check_result(
            value="N/A",
            is_pass=is_pass,
            has_pattern_items=False,
            has_waiver_value=True,
            details=details,
            error_groups=error_groups,
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
    checker = UnresolvedRefsChecker()
    checker.run()


if __name__ == '__main__':
    main()
