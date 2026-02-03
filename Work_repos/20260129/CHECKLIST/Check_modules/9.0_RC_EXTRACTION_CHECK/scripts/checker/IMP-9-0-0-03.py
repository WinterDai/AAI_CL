################################################################################
# Script Name: IMP-9-0-0-03.py
#
# Purpose:
#   Confirm no ERROR message in the QRC log files.
#
# Logic:
#   - Parse input files: do_qrc*.log
#   - Scan each line for ERROR messages using regex pattern: ^ERROR\s*\(([A-Z]+-\d+)\)\s*:\s*(.+)$
#   - Extract ERROR details: error code, message text, line number, file path
#   - Count total INFO, WARNING, and ERROR messages for summary statistics
#   - Group errors by error code and track occurrence counts
#   - Determine PASS/FAIL: PASS if no ERRORs found, FAIL if any ERRORs exist
#   - Build output: INFO01 shows summary statistics, ERROR01 lists ERROR details
#
# Auto Type Detection:
#   Type 1: requirements.value=N/A, waivers.value=N/A/0 → Boolean check
#   Type 2: requirements.value>0, pattern_items exists, waivers.value=N/A/0 → Value comparison
#   Type 3: requirements.value>0, pattern_items exists, waivers.value>0 → Value with waiver logic
#   Type 4: requirements.value=N/A, waivers.value>0 → Boolean with waiver logic
#
# Output Behavior (Type 2/3 - Check README "Output Behavior" section!):
#   existence_check: pattern_items = items that SHOULD EXIST in input files
#     - found_items = patterns found in file
#     - missing_items = patterns NOT found in file
#   status_check: pattern_items = items to CHECK STATUS (only output matched items)
#     - found_items = patterns matched AND status correct
#     - missing_items = patterns matched BUT status wrong
#
# Waiver Tag Rules:
#   When waivers.value > 0 (Type 3/4):
#     - All waive_items related INFO/FAIL/WARN reason suffix: [WAIVER]
#   When waivers.value = 0 (Type 1/2):
#     - waive_items output as INFO with suffix: [WAIVED_INFO]
#     - FAIL/WARN converted to INFO with suffix: [WAIVED_AS_INFO]
#   All types support value = N/A
#
# Refactored: 2025-12-25 (Using checker_templates v1.1.0)
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
class Check_9_0_0_03(InputFileParserMixin, OutputBuilderMixin, WaiverHandlerMixin, BaseChecker):
    """
    IMP-9-0-0-03: Confirm no ERROR message in the QRC log files.
    
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
    FOUND_DESC_TYPE1_4 = "QRC extraction completed with no ERROR messages found"
    MISSING_DESC_TYPE1_4 = "ERROR messages found in QRC extraction logs"
    FOUND_REASON_TYPE1_4 = "No ERROR messages found in QRC extraction logs"
    MISSING_REASON_TYPE1_4 = "ERROR messages found in QRC extraction logs - extraction failed"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_DESC_TYPE2_3 = "QRC extraction log validated - no ERROR messages detected"
    MISSING_DESC_TYPE2_3 = "QRC extraction validation failed - ERROR messages detected"
    FOUND_REASON_TYPE2_3 = "QRC extraction log validated successfully - no ERROR patterns matched"
    MISSING_REASON_TYPE2_3 = "QRC extraction validation failed - ERROR patterns detected in logs"
    
    # All Types (waiver description unified)
    WAIVED_DESC = "QRC extraction ERROR messages waived"
    
    # Waiver parameters (Type 3/4 ONLY)
    WAIVED_BASE_REASON = "QRC extraction ERROR waived per design team approval"
    
    def __init__(self):
        """Initialize the checker."""
        super().__init__(
            check_module="9.0_RC_EXTRACTION_CHECK",
            item_id="IMP-9-0-0-03",
            item_desc="Confirm no ERROR message in the QRC log files."
        )
        # Custom member variables for parsed data
        self._parsed_items: List[Dict[str, Any]] = []
        self._error_summary: Dict[str, int] = {}
        self._message_counts: Dict[str, int] = {'INFO': 0, 'WARNING': 0, 'ERROR': 0}
    
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
        Parse input files to extract relevant data.
        
        Parse QRC log files to extract ERROR, WARNING, and INFO messages.
        Uses regex patterns to identify message types and extract details.
        
        Returns:
            Dict with parsed data:
            - 'items': List[Dict] - ERROR messages with metadata (line_number, file_path)
            - 'metadata': Dict - Summary statistics (message counts, error summary)
            - 'errors': List - Any parsing errors encountered
        """
        # 1. Validate inputs - IMPORTANT: returns tuple (valid_files_list, missing_files_list)
        valid_files, missing_files = self.validate_input_files()
        
        # FIXED: KNOWN_ISSUE_LOGIC-001 - Explicitly check for empty list
        if not valid_files or len(valid_files) == 0:
            raise ConfigurationError(
                self.create_missing_files_error(missing_files if missing_files else ["No input files found"])
            )
        
        if missing_files:
            raise ConfigurationError(
                self.create_missing_files_error(missing_files)
            )
        
        # 2. Parse using patterns from file analysis
        all_error_items = []
        error_summary = {}
        message_counts = {'INFO': 0, 'WARNING': 0, 'ERROR': 0}
        
        # Define regex patterns for QRC log messages
        error_pattern = re.compile(r'^ERROR\s*\(([A-Z]+-\d+)\)\s*:\s*(.+)$')
        warning_pattern = re.compile(r'^WARNING\s*\(([A-Z]+-\d+)\)\s*:\s*(.+)$')
        info_pattern = re.compile(r'^INFO\s*\(([A-Z]+-\d+)\)\s*:\s*(.+)$')
        
        for file_path in valid_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line_num, line in enumerate(f, 1):
                        line = line.strip()
                        
                        # Check for ERROR messages
                        error_match = error_pattern.match(line)
                        if error_match:
                            error_code = error_match.group(1)
                            error_msg = error_match.group(2)
                            
                            # Create error item with required metadata
                            error_item = {
                                'name': f"{error_code}: {error_msg}",
                                'error_code': error_code,
                                'message': error_msg,
                                'line_number': line_num,
                                'file_path': str(file_path)
                            }
                            all_error_items.append(error_item)
                            
                            # Update error summary
                            if error_code not in error_summary:
                                error_summary[error_code] = {
                                    'count': 0,
                                    'first_occurrence': error_item
                                }
                            error_summary[error_code]['count'] += 1
                            
                            message_counts['ERROR'] += 1
                            continue
                        
                        # Check for WARNING messages
                        warning_match = warning_pattern.match(line)
                        if warning_match:
                            message_counts['WARNING'] += 1
                            continue
                        
                        # Check for INFO messages
                        info_match = info_pattern.match(line)
                        if info_match:
                            message_counts['INFO'] += 1
                            continue
                            
            except Exception as e:
                # Log parsing error but continue with other files
                self.logger.warning(f"Error parsing file {file_path}: {str(e)}")
        
        # 3. Store frequently reused data on self
        self._parsed_items = all_error_items
        self._error_summary = error_summary
        self._message_counts = message_counts
        
        # 4. Return aggregated dict with items containing line_number and file_path
        return {
            'items': all_error_items,
            'metadata': {
                'total_errors': len(all_error_items),
                'error_summary': error_summary,
                'message_counts': message_counts
            },
            'errors': []
        }
    
    # =========================================================================
    # Type 1: Boolean Check
    # =========================================================================
    
    def _execute_type1(self) -> CheckResult:
        """
        Type 1: Boolean Check.
        
        Check if any ERROR messages exist in QRC log files.
        PASS if no ERRORs found, FAIL if any ERRORs exist.
        
        Returns:
            CheckResult with is_pass based on check logic
        """
        # Parse input
        data = self._parse_input_files()
        items = data.get('items', [])
        metadata = data.get('metadata', {})
        message_counts = metadata.get('message_counts', {})
        
        # Convert error items to dict with metadata for source file/line display
        if items:
            # Found ERROR messages - FAIL case
            # FIXED: KNOWN_ISSUE_API-009 - Pass dict format {name: metadata}, not list
            missing_items = {}
            for item in items:
                missing_items[item['name']] = {
                    'line_number': item.get('line_number', 0),
                    'file_path': item.get('file_path', 'N/A')
                }
            
            # Use template helper - Type 1: Use TYPE1_4 reason (emphasize "found/not found")
            return self.build_complete_output(
                found_items={},
                missing_items=missing_items,
                found_desc=self.FOUND_DESC_TYPE1_4,
                missing_desc=self.MISSING_DESC_TYPE1_4,
                found_reason=self.FOUND_REASON_TYPE1_4,
                missing_reason=self.MISSING_REASON_TYPE1_4
            )
        else:
            # No ERROR messages - PASS case
            # Create summary info item
            summary_name = f"QRC extraction summary: {message_counts.get('INFO', 0)} INFO, {message_counts.get('WARNING', 0)} WARNING, {message_counts.get('ERROR', 0)} ERROR messages"
            found_items = {
                summary_name: {
                    'line_number': 0,
                    'file_path': 'Summary'
                }
            }
            
            return self.build_complete_output(
                found_items=found_items,
                missing_items={},
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
        This is a status_check mode - check if ERROR messages exist.
        
        Returns:
            CheckResult with is_pass based on value comparison
        """
        # Parse input
        data = self._parse_input_files()
        items = data.get('items', [])
        metadata = data.get('metadata', {})
        message_counts = metadata.get('message_counts', {})
        
        # Get requirements
        pattern_items = self.item_data.get('requirements', {}).get('pattern_items', [])
        
        # FIXED: KNOWN_ISSUE_API-009 - Convert error items to dict with metadata
        missing_items = {}
        for item in items:
            missing_items[item['name']] = {
                'line_number': item.get('line_number', 0),
                'file_path': item.get('file_path', 'N/A')
            }
        
        if items:
            # Found ERROR messages - FAIL case
            return self.build_complete_output(
                found_items={},
                missing_items=missing_items,
                found_desc=self.FOUND_DESC_TYPE2_3,
                missing_desc=self.MISSING_DESC_TYPE2_3,
                found_reason=self.FOUND_REASON_TYPE2_3,
                missing_reason=self.MISSING_REASON_TYPE2_3
            )
        else:
            # No ERROR messages - PASS case
            summary_name = f"QRC extraction summary: {message_counts.get('INFO', 0)} INFO, {message_counts.get('WARNING', 0)} WARNING, {message_counts.get('ERROR', 0)} ERROR messages"
            found_items = {
                summary_name: {
                    'line_number': 0,
                    'file_path': 'Summary'
                }
            }
            
            return self.build_complete_output(
                found_items=found_items,
                missing_items={},
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
        ERROR messages can be waived based on error code or message pattern.
        
        Returns:
            CheckResult with FAIL for unwaived, INFO for waived items
        """
        # Parse input
        parsed_data = self._parse_input_files()
        items = parsed_data.get('items', [])
        metadata = parsed_data.get('metadata', {})
        message_counts = metadata.get('message_counts', {})
        
        # FIXED: KNOWN_ISSUE_API-016 - Use waivers.get() directly to preserve dict format
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # FIXED: KNOWN_ISSUE_API-009 - Build dict format {name: metadata}
        # Separate waived/unwaived ERROR messages
        waived_items = {}
        unwaived_items = {}
        
        for error_item in items:
            error_name = error_item['name']
            error_code = error_item.get('error_code', '')
            
            item_metadata = {
                'line_number': error_item.get('line_number', 0),
                'file_path': error_item.get('file_path', 'N/A')
            }
            
            # Check if this error matches any waiver pattern
            # Match by error code or full error name
            # FIXED: KNOWN_ISSUE_API-017 - Use waive_dict.keys() for item names
            if self.match_waiver_entry(error_code, waive_dict) or \
               self.match_waiver_entry(error_name, waive_dict):
                waived_items[error_name] = item_metadata
            else:
                unwaived_items[error_name] = item_metadata
        
        # FIXED: KNOWN_ISSUE_API-017 - Use waive_dict.keys() to get item names
        # Find unused waivers
        used_names = set()
        for error_item in items:
            error_code = error_item.get('error_code', '')
            error_name = error_item['name']
            if self.match_waiver_entry(error_code, waive_dict):
                used_names.add(error_code)
            if self.match_waiver_entry(error_name, waive_dict):
                used_names.add(error_name)
        
        unused_waivers = [name for name in waive_dict.keys() if name not in used_names]
        
        # FIXED: KNOWN_ISSUE_API-021 - Use missing_items parameter, not unwaived_items
        # Use template helper for automatic output formatting
        return self.build_complete_output(
            missing_items=unwaived_items,
            waived_items=waived_items,
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
        message_counts = metadata.get('message_counts', {})
        
        # FIXED: KNOWN_ISSUE_API-016 - Use waivers.get() directly to preserve dict format
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # FIXED: KNOWN_ISSUE_API-009 - Build dict format {name: metadata}
        # Separate waived/unwaived ERROR messages
        waived_items = {}
        unwaived_items = {}
        
        for error_item in items:
            error_name = error_item['name']
            error_code = error_item.get('error_code', '')
            
            item_metadata = {
                'line_number': error_item.get('line_number', 0),
                'file_path': error_item.get('file_path', 'N/A')
            }
            
            # Check if this error matches any waiver pattern
            # FIXED: KNOWN_ISSUE_API-017 - Use waive_dict.keys() for item names
            if self.match_waiver_entry(error_code, waive_dict) or \
               self.match_waiver_entry(error_name, waive_dict):
                waived_items[error_name] = item_metadata
            else:
                unwaived_items[error_name] = item_metadata
        
        # FIXED: KNOWN_ISSUE_API-017 - Use waive_dict.keys() to get item names
        # Find unused waivers
        used_names = set()
        for error_item in items:
            error_code = error_item.get('error_code', '')
            error_name = error_item['name']
            if self.match_waiver_entry(error_code, waive_dict):
                used_names.add(error_code)
            if self.match_waiver_entry(error_name, waive_dict):
                used_names.add(error_name)
        
        unused_waivers = [name for name in waive_dict.keys() if name not in used_names]
        
        # Create found_items for summary (if no unwaived errors)
        found_items = {}
        if not unwaived_items:
            summary_name = f"QRC extraction summary: {message_counts.get('INFO', 0)} INFO, {message_counts.get('WARNING', 0)} WARNING, {message_counts.get('ERROR', 0)} ERROR messages"
            found_items = {
                summary_name: {
                    'line_number': 0,
                    'file_path': 'Summary'
                }
            }
        
        # FIXED: KNOWN_ISSUE_API-021 - Use missing_items parameter, not unwaived_items
        # Use template helper (auto-handles waiver=0)
        return self.build_complete_output(
            found_items=found_items,
            missing_items=unwaived_items,
            waived_items=waived_items,
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
    checker = Check_9_0_0_03()
    checker.init_checker(Path(__file__))
    result = checker.execute_check()
    checker.write_output(result)
    return 0 if result.is_pass else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())