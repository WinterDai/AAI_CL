################################################################################
# Script Name: IMP-7-0-0-02.py
#
# Purpose:
#   Confirm no ERROR message during read constraints.
#
# Logic:
#   - Parse input files: IMP-7-0-0-02.rpt
#   - Track constraint reading phase using state machine (reading vs post-constraint)
#   - Detect constraint file reading initiation with pattern "Reading timing constraints file"
#   - Identify successful constraint reading with "Constraints read successfully"
#   - Capture **ERROR: messages during constraint reading phase (Pattern 3)
#   - Capture parse-style error messages with severity="error" (Pattern 6)
#   - Ignore errors in post-constraint violation tables (these are summaries, not reading errors)
#   - Extract error code, message, file path, and line number for each error
#   - Monitor warnings for context but do not treat as failures
#   - Return PASS if no errors found during constraint reading, FAIL otherwise
#
# Auto Type Detection:
#   Type 1: requirements.value=N/A, pattern_items [] (empty), waivers.value=N/A/0 → Boolean Check
#   Type 2: requirements.value>0, pattern_items [...] (defined), waivers.value=N/A/0 → Value Check
#   Type 3: requirements.value>0, pattern_items [...] (defined), waivers.value>0 → Value Check with Waiver Logic
#   Type 4: requirements.value=N/A, pattern_items [] (empty), waivers.value>0 → Boolean Check with Waiver Logic
#   Note: requirements.value indicates number of patterns for config validation (doesn't affect PASS/FAIL)
#
# Waiver Tag Rules:
#   When waivers.value > 0 (Type 3/4):
#     - All waive_items related INFO/FAIL/WARN reason suffix: [WAIVER]
#   When waivers.value = 0 (Type 1/2):
#     - waive_items output as INFO with suffix: [WAIVED_INFO]
#     - FAIL/WARN converted to INFO with suffix: [WAIVED_AS_INFO]
#   All types support value = N/A
#
# Refactored: 2025-12-23 (Using checker_templates v1.1.0)
#
# Author: yyin
# Date: 2025-12-18
################################################################################

from pathlib import Path
import re
import sys
from typing import List, Dict, Tuple, Optional, Any


# Add common module to path
_SCRIPT_DIR = Path(__file__).resolve().parent
_CHECK_MODULES_DIR = _SCRIPT_DIR.parents[2]  # Go up to Check_modules/
_COMMON_DIR = _CHECK_MODULES_DIR / 'common'
if str(_COMMON_DIR) not in sys.path:
    sys.path.insert(0, str(_COMMON_DIR))

from base_checker import BaseChecker, CheckResult, ConfigurationError
from output_formatter import DetailItem, Severity, create_check_result

# MANDATORY: Import template mixins (checker_templates v1.1.0)
from checker_templates.waiver_handler_template import WaiverHandlerMixin
from checker_templates.output_builder_template import OutputBuilderMixin
from checker_templates.input_file_parser_template import InputFileParserMixin  # Optional but recommended


# MANDATORY: Inherit mixins in correct order (InputFileParserMixin first if used)
class Check_7_0_0_02(InputFileParserMixin, OutputBuilderMixin, WaiverHandlerMixin, BaseChecker):
    """
    IMP-7-0-0-02: Confirm no ERROR message during read constraints.
    
    Checking Types:
    - Type 1: requirements=N/A, pattern_items [], waivers=N/A/0 → Boolean Check
    - Type 2: requirements>0, pattern_items [...], waivers=N/A/0 → Value Check
    - Type 3: requirements>0, pattern_items [...], waivers>0 → Value Check with Waiver Logic
    - Type 4: requirements=N/A, pattern_items [], waivers>0 → Boolean Check with Waiver Logic
    
    Template Library v1.1.0:
    - Uses InputFileParserMixin for parsing (parse_log_with_patterns, normalize_command)
    - Uses WaiverHandlerMixin for waiver processing (parse_waive_items(waive_items_raw), match_waiver_entry(item, waive_dict))
    - Uses OutputBuilderMixin for result construction (build_complete_output(...))
    """
    
    # =========================================================================
    # DESCRIPTION & REASON CONSTANTS - Split by Type semantics (API-026)
    # =========================================================================
    # Type 1/4: Boolean checks - emphasize "found/not found" (existence)
    FOUND_DESC_TYPE1_4 = "Constraint files successfully read without errors"
    MISSING_DESC_TYPE1_4 = "ERROR messages found during constraint reading"
    FOUND_REASON_TYPE1_4 = "Constraint file read successfully without errors"
    MISSING_REASON_TYPE1_4 = "ERROR message detected during constraint reading phase"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_DESC_TYPE2_3 = "Expected constraint reading patterns matched"
    MISSING_DESC_TYPE2_3 = "Required constraint reading patterns not satisfied"
    FOUND_REASON_TYPE2_3 = "Constraint reading pattern matched and validated"
    MISSING_REASON_TYPE2_3 = "Expected constraint reading pattern not satisfied"
    
    # All Types (waiver description unified)
    WAIVED_DESC = "Waived constraint reading errors"
    
    # Waiver parameters (Type 3/4 ONLY)
    WAIVED_BASE_REASON = "Constraint reading error waived per design approval"
    
    def __init__(self):
        """Initialize the checker."""
        super().__init__(
            check_module="7.0_INNOVUS_DESIGN_IN_CHECK",
            item_id="IMP-7-0-0-02",
            item_desc="Confirm no ERROR message during read constraints."
        )
        # Custom member variables for parsed data
        self._parsed_items: List[Dict[str, Any]] = []
        self._constraint_files: List[str] = []
        self._in_reading_phase: bool = False
    
    # =========================================================================
    # Main Check Execution
    # =========================================================================
    
    def execute_check(self) -> CheckResult:
        """
        Execute check with automatic type detection and delegation.
        
        Returns:
            CheckResult based on detected checker type
        """
        try:
            if self.root is None:
                raise RuntimeError("Checker not initialized. Call init_checker() first.")
            
            # Detect checker type (use BaseChecker method)
            checker_type = self.detect_checker_type()
            
            # Execute based on type
            if checker_type == 1:
                return self._execute_type1()
            elif checker_type == 2:
                return self._execute_type2()
            elif checker_type == 3:
                return self._execute_type3()
            else:  # checker_type == 4
                return self._execute_type4()
        except ConfigurationError as e:
            return e.check_result
    
    # =========================================================================
    # Input Parsing (Common for All Types)
    # =========================================================================
    
    def _parse_input_files(self) -> Dict[str, Any]:
        """
        Parse input files to extract constraint reading errors.
        
        Uses state machine to track constraint reading phase:
        1. Detect constraint file reading initiation
        2. Track reading phase vs post-constraint phase
        3. Capture ERROR messages during reading phase only
        4. Ignore post-constraint violation summaries
        
        Returns:
            Dict with parsed data:
            - 'items': List[Dict] - ERROR messages found during constraint reading
            - 'metadata': Dict - Constraint files read, total errors
            - 'errors': List - Any parsing errors encountered
        """
        # 1. Validate input files - IMPORTANT: returns tuple (valid_files_list, missing_files_list)
        valid_files, missing_files = self.validate_input_files()
        
        # FIXED: LOGIC-001 - Explicitly check for empty list
        if not valid_files or len(valid_files) == 0:
            raise ConfigurationError(
                self.create_missing_files_error(missing_files if missing_files else ["No input files configured"])
            )
        
        if missing_files:
            raise ConfigurationError(
                self.create_missing_files_error(missing_files)
            )
        
        # 2. Define patterns for constraint reading detection
        patterns = {
            # Pattern 1: Constraint file reading initiation
            'reading_start': r"Reading timing constraints file '([^']+)'",
            
            # Pattern 2: Successful constraint reading confirmation
            'reading_success': r"INFO\s*\(CTE\):\s*Constraints read successfully",
            
            # Pattern 3: ERROR messages during constraint reading
            'error_standard': r"\*\*ERROR:\s*\(([A-Z]+-\d+)\):\s*(.+?)(?:\(File\s+([^,]+),\s*Line\s+(\d+)\))?",
            
            # Pattern 4: WARNING messages (context only)
            'warning': r"\*\*WARN:\s*\(([A-Z]+-\d+)\):\s*(.+?)(?:\(File\s+([^,]+),\s*Line\s+(\d+)\))?",
            
            # Pattern 5: Message summary line
            'summary': r"\*\*\*\s*Message Summary:\s*(\d+)\s*warning\(s\),\s*(\d+)\s*error\(s\)",
            
            # Pattern 6: Table format ERROR messages
            # Extracts: | ERROR_CODE | error | COUNT | description |
            # Output format: ERROR_CODE: description (no | symbols)
            'error_parse': r"([A-Z]+-\d+)\s*\|\s*error\s*\|\s*\d+\s+(.+)"
        }
        
        # 3. Parse files with state tracking
        all_errors = []
        constraint_files = []
        in_reading_phase = False
        
        for file_path in valid_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line_num, line in enumerate(f, 1):
                        # Track constraint reading phase
                        if match := re.search(patterns['reading_start'], line):
                            constraint_file = match.group(1)
                            constraint_files.append(constraint_file)
                            in_reading_phase = True
                            continue
                        
                        # Exit reading phase on success
                        if re.search(patterns['reading_success'], line):
                            in_reading_phase = False
                            continue
                        
                        # Capture ERROR messages during reading phase only
                        if in_reading_phase:
                            # Standard ERROR format
                            if match := re.search(patterns['error_standard'], line):
                                error_code = match.group(1)
                                error_msg = match.group(2).strip()
                                error_file = match.group(3) if match.group(3) else 'N/A'
                                error_line = match.group(4) if match.group(4) else 'N/A'
                                
                                all_errors.append({
                                    'name': f"{error_code}: {error_msg}",
                                    'error_code': error_code,
                                    'message': error_msg,
                                    'error_file': error_file,
                                    'error_line': error_line,
                                    'line_number': line_num,
                                    'file_path': str(file_path)
                                })
                            
                            # Parse-style ERROR format
                            elif match := re.search(patterns['error_parse'], line):
                                error_code = match.group(1)
                                error_msg = match.group(2).strip().strip('|').strip()
                                
                                all_errors.append({
                                    'name': f"{error_code}: {error_msg}",
                                    'error_code': error_code,
                                    'message': error_msg,
                                    'error_file': 'N/A',
                                    'error_line': 'N/A',
                                    'line_number': line_num,
                                    'file_path': str(file_path)
                                })
            
            except Exception as e:
                # Log parsing error but continue
                self.logger.warning(f"Error parsing {file_path}: {str(e)}")
        
        # 4. Store frequently reused data on self
        self._parsed_items = all_errors
        self._constraint_files = constraint_files
        
        # 5. Return aggregated dict with items containing line_number and file_path
        return {
            'items': all_errors,
            'metadata': {
                'total_errors': len(all_errors),
                'constraint_files': constraint_files,
                'total_constraint_files': len(constraint_files)
            },
            'errors': []
        }
    
    # =========================================================================
    # Type 1: Boolean Check
    # =========================================================================
    
    def _execute_type1(self) -> CheckResult:
        """
        Type 1: Boolean Check.
        
        Check if any ERROR messages exist during constraint reading.
        PASS if no errors found, FAIL if errors exist.
        
        Returns:
            CheckResult with is_pass based on check logic
        """
        # Parse input
        data = self._parse_input_files()
        items = data.get('items', [])
        metadata = data.get('metadata', {})
        
        # Convert error list to dict with metadata for source file/line display
        # Output format: "Fail: <name>. In line <N>, <filepath>: <reason>"
        if items:
            # Errors found - FAIL
            missing_items_dict = {
                item['name']: {
                    'name': item['name'],
                    'line_number': item.get('line_number', 0),
                    'file_path': item.get('file_path', 'N/A'),
                    'error_code': item.get('error_code', 'N/A'),
                    'message': item.get('message', ''),
                    'error_file': item.get('error_file', 'N/A'),
                    'error_line': item.get('error_line', 'N/A')
                }
                for item in items
            }
            found_items_dict = {}
        else:
            # No errors - PASS
            # Show constraint files that were successfully read
            constraint_files = metadata.get('constraint_files', [])
            found_items_dict = {
                f"Constraint file: {cf}": {
                    'name': f"Constraint file: {cf}",
                    'line_number': 0,
                    'file_path': 'N/A'
                }
                for cf in constraint_files
            } if constraint_files else {
                'No constraint reading errors': {
                    'name': 'No constraint reading errors',
                    'line_number': 0,
                    'file_path': 'N/A'
                }
            }
            missing_items_dict = {}
        
        # Use template helper
        # Type 1: Use TYPE1_4 reason (emphasize "found/not found") - API-025
        return self.build_complete_output(
            found_items=found_items_dict,
            missing_items=missing_items_dict,
            found_desc=self.FOUND_DESC_TYPE1_4,
            missing_desc=self.MISSING_DESC_TYPE1_4,
            found_reason=self.FOUND_REASON_TYPE1_4,
            missing_reason=self.MISSING_REASON_TYPE1_4
        )
    
    # =========================================================================
    # Type 2: Value Check
    # =========================================================================
    
    def _execute_type2(self) -> CheckResult:
        """
        Type 2: Value Check.
        
        Search pattern_items in input files.
        found_items = patterns found; missing_items = patterns not found.
        
        Returns:
            CheckResult with is_pass based on value comparison
        """
        # Parse input
        data = self._parse_input_files()
        items = data.get('items', [])
        
        # Get requirements
        pattern_items = self.item_data.get('requirements', {}).get('pattern_items', [])
        
        # Build error_code lookup for matching (only compare error codes)
        error_code_map = {item['error_code']: item for item in items}
        
        # Find which patterns were found vs missing
        found_items_dict = {}
        missing_items_dict = {}
        
        for pattern in pattern_items:
            if pattern in error_code_map:
                # Pattern (error code) found in errors
                matching_item = error_code_map[pattern]
                found_items_dict[matching_item['name']] = {
                    'name': matching_item['name'],
                    'line_number': matching_item.get('line_number', 0),
                    'file_path': matching_item.get('file_path', 'N/A')
                }
            else:
                # Pattern not found
                missing_items_dict[pattern] = {
                    'name': pattern,
                    'line_number': 0,
                    'file_path': 'N/A'
                }
        
        # Find extra items not in pattern_items (error codes not in config)
        matched_codes = set(pattern_items)
        extra_items_dict = {
            item['name']: {
                'name': item['name'],
                'line_number': item.get('line_number', 0),
                'file_path': item.get('file_path', 'N/A')
            }
            for item in items if item['error_code'] not in matched_codes
        }
        
        # Use template helper (auto-handles waiver=0)
        # Type 2: Use TYPE2_3 reason (emphasize "matched/satisfied") - API-026
        return self.build_complete_output(
            found_items=found_items_dict,
            missing_items=missing_items_dict,
            extra_items=extra_items_dict,
            found_desc=self.FOUND_DESC_TYPE2_3,
            missing_desc=self.MISSING_DESC_TYPE2_3,
            found_reason=self.FOUND_REASON_TYPE2_3,
            missing_reason=self.MISSING_REASON_TYPE2_3
        )
    
    # =========================================================================
    # Type 3: Value Check with Waiver Logic
    # =========================================================================
    
    def _execute_type3(self) -> CheckResult:
        """
        Type 3: Value check with waiver support.
        
        Same pattern search logic as Type 2, plus waiver classification.
        
        Returns:
            CheckResult with FAIL for unwaived, INFO for waived items
        """
        # Parse input
        parsed_data = self._parse_input_files()
        items = parsed_data.get('items', [])
        
        # FIXED: API-016 - Use waivers.get() directly to preserve dict format
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # Get requirements
        pattern_items = self.item_data.get('requirements', {}).get('pattern_items', [])
        
        # Find violations (errors that match pattern_items by error_code)
        violations = [item for item in items if item['error_code'] in pattern_items]
        
        # Separate waived/unwaived using template helper (match by error_code)
        waived_items_dict = {}
        unwaived_items_dict = {}
        
        for violation in violations:
            violation_name = violation['name']
            violation_code = violation['error_code']
            # Match waiver by error_code instead of full name
            if self.match_waiver_entry(violation_code, waive_dict):
                waived_items_dict[violation_name] = {
                    'name': violation_name,
                    'line_number': violation.get('line_number', 0),
                    'file_path': violation.get('file_path', 'N/A')
                }
            else:
                unwaived_items_dict[violation_name] = {
                    'name': violation_name,
                    'line_number': violation.get('line_number', 0),
                    'file_path': violation.get('file_path', 'N/A')
                }
        
        # Find patterns that were satisfied (not found in errors by error_code)
        found_codes = {item['error_code'] for item in items}
        found_items_dict = {
            pattern: {
                'name': pattern,
                'line_number': 0,
                'file_path': 'N/A'
            }
            for pattern in pattern_items if pattern not in found_codes
        }
        
        # FIXED: API-017 - waive_dict.keys() contains item names (strings)
        # Find unused waivers
        used_names = set(waived_items_dict.keys())
        unused_waivers = [name for name in waive_dict.keys() if name not in used_names]
        
        # FIXED: API-021 - Use missing_items parameter instead of unwaived_items
        # Use template helper for automatic output formatting
        # Type 3: Use TYPE2_3 reason (emphasize "matched/satisfied") - API-026
        return self.build_complete_output(
            found_items=found_items_dict,
            waived_items=waived_items_dict,
            missing_items=unwaived_items_dict,
            waive_dict=waive_dict,
            unused_waivers=unused_waivers,
            found_desc=self.FOUND_DESC_TYPE2_3,
            missing_desc=self.MISSING_DESC_TYPE2_3,
            waived_desc=self.WAIVED_DESC,
            found_reason=self.FOUND_REASON_TYPE2_3,
            missing_reason=self.MISSING_REASON_TYPE2_3,
            waived_base_reason=self.WAIVED_BASE_REASON
        )
    
    # =========================================================================
    # Type 4: Boolean Check with Waiver Logic
    # =========================================================================
    
    def _execute_type4(self) -> CheckResult:
        """
        Type 4: Boolean check with waiver support (Type 1 + waiver).
        
        Same boolean check as Type 1 (no pattern_items), plus waiver classification.
        
        Returns:
            CheckResult with waiver logic applied
        """
        # Parse input
        data = self._parse_input_files()
        items = data.get('items', [])
        metadata = data.get('metadata', {})
        
        # FIXED: API-016 - Use waivers.get() directly to preserve dict format
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # Separate waived/unwaived errors (match by error_code)
        waived_items_dict = {}
        unwaived_items_dict = {}
        
        for item in items:
            item_name = item['name']
            item_code = item['error_code']
            # Match waiver by error_code instead of full name
            if self.match_waiver_entry(item_code, waive_dict):
                waived_items_dict[item_name] = {
                    'name': item_name,
                    'line_number': item.get('line_number', 0),
                    'file_path': item.get('file_path', 'N/A')
                }
            else:
                unwaived_items_dict[item_name] = {
                    'name': item_name,
                    'line_number': item.get('line_number', 0),
                    'file_path': item.get('file_path', 'N/A')
                }
        
        # If no errors, show constraint files that were successfully read
        if not items:
            constraint_files = metadata.get('constraint_files', [])
            found_items_dict = {
                f"Constraint file: {cf}": {
                    'name': f"Constraint file: {cf}",
                    'line_number': 0,
                    'file_path': 'N/A'
                }
                for cf in constraint_files
            } if constraint_files else {
                'No constraint reading errors': {
                    'name': 'No constraint reading errors',
                    'line_number': 0,
                    'file_path': 'N/A'
                }
            }
        else:
            found_items_dict = {}
        
        # FIXED: API-017 - waive_dict.keys() contains item names (strings)
        # Find unused waivers
        used_names = set(waived_items_dict.keys())
        unused_waivers = [name for name in waive_dict.keys() if name not in used_names]
        
        # FIXED: API-021 - Use missing_items parameter instead of unwaived_items
        # Use template helper (auto-handles waiver=0)
        # Type 4: Use TYPE1_4 reason (emphasize "found/not found") - API-026
        return self.build_complete_output(
            found_items=found_items_dict,
            waived_items=waived_items_dict,
            missing_items=unwaived_items_dict,
            waive_dict=waive_dict,
            unused_waivers=unused_waivers,
            found_desc=self.FOUND_DESC_TYPE1_4,
            missing_desc=self.MISSING_DESC_TYPE1_4,
            waived_desc=self.WAIVED_DESC,
            found_reason=self.FOUND_REASON_TYPE1_4,
            missing_reason=self.MISSING_REASON_TYPE1_4,
            waived_base_reason=self.WAIVED_BASE_REASON
        )


# =========================================================================
# Entry Point
# =========================================================================

def main():
    """Main entry point."""
    checker = Check_7_0_0_02()
    checker.init_checker(Path(__file__))
    result = checker.execute_check()
    checker.write_output(result)
    return 0 if result.is_pass else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())