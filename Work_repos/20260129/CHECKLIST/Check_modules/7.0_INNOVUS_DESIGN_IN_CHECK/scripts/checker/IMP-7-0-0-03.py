################################################################################
# Script Name: IMP-7-0-0-03.py
#
# Purpose:
#   Confirm all Warning messages during read constraints can be waived.
#
# Logic:
#   - Parse input files: IMP-7-0-0-02.rpt
#   - Extract constraint file reading context and track active constraint modes
#   - Detect WARNING messages in both standard format (**WARN:) and table format (| ID | Severity | Count |)
#   - Parse warning codes, descriptions, source files, and line numbers from both formats
#   - For table format, extract warning code and description while removing | delimiters
#   - Classify warnings as waived or unwaived based on waiver configuration
#   - Report unwaived warnings as failures and waived warnings as informational
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
# Refactored: 2025-12-18 (Using checker_templates v1.1.0)
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
class Check_7_0_0_03(InputFileParserMixin, OutputBuilderMixin, WaiverHandlerMixin, BaseChecker):
    """
    IMP-7-0-0-03: Confirm all Warning messages during read constraints can be waived.
    
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
    FOUND_DESC_TYPE1_4 = "Constraint reading completed without warnings"
    MISSING_DESC_TYPE1_4 = "WARNING messages found during constraint reading"
    FOUND_REASON_TYPE1_4 = "No WARNING messages detected during constraint file reading"
    MISSING_REASON_TYPE1_4 = "WARNING message found during constraint reading - requires waiver or resolution"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_DESC_TYPE2_3 = "Expected WARNING patterns matched in constraint log"
    MISSING_DESC_TYPE2_3 = "Required WARNING patterns not satisfied"
    FOUND_REASON_TYPE2_3 = "WARNING pattern matched and validated against requirements"
    MISSING_REASON_TYPE2_3 = "Expected WARNING pattern not satisfied or missing from log"
    
    # All Types (waiver description unified)
    WAIVED_DESC = "Waived WARNING messages during constraint reading"
    
    # Waiver parameters (Type 3/4 ONLY)
    WAIVED_BASE_REASON = "WARNING message waived per design approval"
    
    def __init__(self):
        """Initialize the checker."""
        super().__init__(
            check_module="7.0_INNOVUS_DESIGN_IN_CHECK",
            item_id="IMP-7-0-0-03",
            item_desc="Confirm all Warning messages during read constraints can be waived."
        )
        # Custom member variables for parsed data
        self._parsed_warnings: List[Dict[str, Any]] = []
        self._constraint_files: List[str] = []
        self._in_constraint_reading: bool = False
    
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
        Parse input files to extract WARNING messages during constraint reading.
        
        Parses IMP-7-0-0-02.rpt to extract:
        1. Constraint file reading context
        2. Standard format WARNING messages (**WARN:)
        3. Table format WARNING messages (| ID | Severity | Count |)
        
        Returns:
            Dict with parsed data:
            - 'items': List[Dict] - WARNING messages with metadata (line_number, file_path)
            - 'metadata': Dict - File metadata (constraint_files, total_warnings)
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
        
        # 2. Parse using patterns from file analysis
        # Use dict to deduplicate by warning code (same code only appears once)
        warnings_dict = {}  # key: warning_code, value: warning dict
        constraint_files = []
        errors = []
        
        # Pattern definitions
        # Pattern 1: Constraint file reading initiation
        pattern_file_reading = re.compile(r"Reading timing constraints file '([^']+)'")
        
        # Pattern 2: Successful constraint reading confirmation
        pattern_success = re.compile(r"INFO\s*\(CTE\):\s*Constraints read successfully")
        
        # Pattern 3: WARNING messages during constraint reading (standard log format)
        # Use greedy .+ to capture full message including quotes, then optional File/Line capture
        pattern_standard_warn = re.compile(
            r"\*\*WARN:\s*\(([A-Z]+-\d+)\):\s+(.+?)(?:\s+\(File\s+([^,]+),\s*Line\s+(\d+)\))?\s*$"
        )
        
        # Pattern 4: Message summary line
        pattern_summary = re.compile(r"\*\*\*\s*Message Summary:\s*(\d+)\s*warning\(s\),\s*(\d+)\s*error\(s\)")
        
        # Pattern 5: Table format - | ID | Severity | Count | Description |
        # Only match severity='warning', not 'error'
        # Note: End pipe | is optional as some lines may be truncated
        pattern_table_warn = re.compile(
            r'^\|\s*([A-Z]+-\d+)\s*\|\s*(warning)\s*\|\s*(\d+)\s*\|\s*(.+?)(?:\s*\|)?$'
        )
        
        for file_path in valid_files:
            in_constraint_reading = False
            in_table_mode = False
            current_table_warning = None
            
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line_num, line in enumerate(f, 1):
                        line = line.rstrip()
                        
                        # Track constraint file reading context
                        if match := pattern_file_reading.search(line):
                            constraint_file = match.group(1)
                            constraint_files.append(constraint_file)
                            in_constraint_reading = True
                            continue
                        
                        # Track successful constraint reading
                        if pattern_success.search(line):
                            in_constraint_reading = False
                            continue
                        
                        # Detect table mode start (header line with | ID | Severity |)
                        # Note: Severity and Count may have variable spacing
                        if '| ID' in line and 'Severity' in line and 'Count' in line and 'Description' in line:
                            in_table_mode = True
                            continue
                        
                        # Detect table mode end (empty line or non-table/non-separator line)
                        # Keep table mode active for separator lines (starting with -)
                        if in_table_mode:
                            if not line.strip():
                                # Empty line ends table mode
                                in_table_mode = False
                                current_table_warning = None
                                continue
                            elif not line.strip().startswith('|') and not line.strip().startswith('-'):
                                # Non-table, non-separator line ends table mode
                                in_table_mode = False
                                current_table_warning = None
                                continue
                        
                        # Parse table format warnings
                        if in_table_mode:
                            if match := pattern_table_warn.match(line):
                                warning_code = match.group(1)
                                severity = match.group(2)
                                count = match.group(3)
                                description = match.group(4).strip()
                                
                                # Only capture warnings (severity='warning'), skip errors
                                if severity == 'warning':
                                    # Deduplicate: only keep first occurrence of each warning code
                                    if warning_code not in warnings_dict:
                                        # Format: WARNING_CODE: description (no | symbols)
                                        warning_name = f"{warning_code}: {description}"
                                        
                                        warnings_dict[warning_code] = {
                                            'name': warning_name,
                                            'code': warning_code,
                                            'description': description,
                                            'count': count,
                                            'line_number': line_num,
                                            'file_path': str(file_path),
                                            'format': 'table'
                                        }
                            continue
                        
                        # Parse standard format warnings during constraint reading
                        if in_constraint_reading:
                            if match := pattern_standard_warn.search(line):
                                warning_code = match.group(1)
                                message_text = match.group(2).strip()
                                source_file = match.group(3) if match.group(3) else 'N/A'
                                source_line = match.group(4) if match.group(4) else '0'
                                
                                # Deduplicate: only keep first occurrence of each warning code
                                if warning_code not in warnings_dict:
                                    # Format: WARNING_CODE: message
                                    warning_name = f"{warning_code}: {message_text}"
                                    
                                    warnings_dict[warning_code] = {
                                        'name': warning_name,
                                        'code': warning_code,
                                        'message': message_text,
                                        'source_file': source_file,
                                        'source_line': source_line,
                                        'line_number': line_num,
                                        'file_path': str(file_path),
                                        'format': 'standard'
                                    }
            
            except Exception as e:
                errors.append(f"Error parsing {file_path}: {str(e)}")
        
        # Convert dict back to list for compatibility
        all_warnings = list(warnings_dict.values())
        
        # 3. Store frequently reused data on self
        self._parsed_warnings = all_warnings
        self._constraint_files = constraint_files
        
        # 4. Return aggregated dict with items containing line_number and file_path
        return {
            'items': all_warnings,
            'metadata': {
                'total_warnings': len(all_warnings),
                'constraint_files': constraint_files
            },
            'errors': errors
        }
    
    # =========================================================================
    # Type 1: Boolean Check
    # =========================================================================
    
    def _execute_type1(self) -> CheckResult:
        """
        Type 1: Boolean Check.
        
        Check if any WARNING messages exist during constraint reading.
        PASS if no warnings found, FAIL if warnings exist.
        
        Returns:
            CheckResult with is_pass based on check logic
        """
        # Parse input
        data = self._parse_input_files()
        warnings = data.get('items', [])
        
        # Convert list to dict with metadata for source file/line display
        # Output format: "Info/Fail: <name>. In line <N>, <filepath>: <reason>"
        if warnings:
            # Warnings found - FAIL case
            missing_items = {
                warning['name']: {
                    'name': warning['name'],
                    'line_number': warning.get('line_number', 0),
                    'file_path': warning.get('file_path', 'N/A')
                }
                for warning in warnings
            }
            found_items = {}
        else:
            # No warnings - PASS case
            found_items = {
                'No warnings': {
                    'name': 'No warnings found during constraint reading',
                    'line_number': 0,
                    'file_path': 'N/A'
                }
            }
            missing_items = {}
        
        # Use template helper
        # Type 1: Use TYPE1_4 reason (emphasize "found/not found") - API-025
        return self.build_complete_output(
            found_items=found_items,
            missing_items=missing_items,
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
        warnings = data.get('items', [])
        
        # Get requirements
        pattern_items = self.item_data.get('requirements', {}).get('pattern_items', [])
        
        # Extract warning codes from parsed warnings
        found_codes = {w['code'] for w in warnings}
        
        # Compare against expected patterns
        found_items = {}
        missing_items = {}
        
        for pattern in pattern_items:
            # Find matching warnings
            matching_warnings = [w for w in warnings if w['code'] == pattern]
            
            if matching_warnings:
                # Pattern found
                for warning in matching_warnings:
                    found_items[warning['name']] = {
                        'name': warning['name'],
                        'line_number': warning.get('line_number', 0),
                        'file_path': warning.get('file_path', 'N/A')
                    }
            else:
                # Pattern not found
                missing_items[pattern] = {
                    'name': pattern,
                    'line_number': 0,
                    'file_path': 'N/A'
                }
        
        # Find extra warnings not in pattern_items
        extra_items = {}
        for warning in warnings:
            if warning['code'] not in pattern_items:
                extra_items[warning['name']] = {
                    'name': warning['name'],
                    'line_number': warning.get('line_number', 0),
                    'file_path': warning.get('file_path', 'N/A')
                }
        
        # Use template helper (auto-handles waiver=0)
        # Type 2: Use TYPE2_3 reason (emphasize "matched/satisfied") - API-026
        return self.build_complete_output(
            found_items=found_items,
            missing_items=missing_items,
            extra_items=extra_items,
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
        
        Uses WaiverHandlerMixin for waiver processing:
        - parse_waive_items(waive_items_raw): Parse waiver configuration
        - match_waiver_entry(item, waive_dict): Match item against waivers
        
        Uses OutputBuilderMixin for result construction:
        - build_complete_output(...): Assemble final CheckResult with auto-formatting
        
        Returns:
            CheckResult with FAIL for unwaived, INFO for waived items
        """
        # Parse input
        parsed_data = self._parse_input_files()
        warnings = parsed_data.get('items', [])
        
        # FIXED: API-016 - Use waivers.get() directly to preserve dict format
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # Get requirements
        pattern_items = self.item_data.get('requirements', {}).get('pattern_items', [])
        
        # Find violations (warnings matching pattern_items)
        violations = []
        for pattern in pattern_items:
            matching_warnings = [w for w in warnings if w['code'] == pattern]
            violations.extend(matching_warnings)
        
        # Separate waived/unwaived using template helper
        waived_items = {}
        missing_items = {}
        
        for warning in violations:
            # Try matching by warning code
            if self.match_waiver_entry(warning['code'], waive_dict):
                waived_items[warning['name']] = {
                    'name': warning['name'],
                    'line_number': warning.get('line_number', 0),
                    'file_path': warning.get('file_path', 'N/A')
                }
            else:
                missing_items[warning['name']] = {
                    'name': warning['name'],
                    'line_number': warning.get('line_number', 0),
                    'file_path': warning.get('file_path', 'N/A')
                }
        
        # FIXED: API-017 - waive_dict.keys() are item names (strings)
        used_codes = {w['code'] for w in violations if self.match_waiver_entry(w['code'], waive_dict)}
        unused_waivers = [
            {'name': name}
            for name in waive_dict.keys()
            if name not in used_codes
        ]
        
        # FIXED: API-021 - Use missing_items parameter instead of unwaived_items
        # Type 3: Use TYPE2_3 reason (emphasize "matched/satisfied") - API-026
        return self.build_complete_output(
            waived_items=waived_items,
            missing_items=missing_items,
            waive_dict=waive_dict,
            unused_waivers=unused_waivers,
            waived_desc=self.WAIVED_DESC,
            missing_desc=self.MISSING_DESC_TYPE2_3,
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
        
        Use OutputBuilderMixin.build_complete_output() with has_waiver_value=True.
        
        Returns:
            CheckResult with waiver logic applied
        """
        # Parse input
        data = self._parse_input_files()
        warnings = data.get('items', [])
        
        # FIXED: API-016 - Use waivers.get() directly to preserve dict format
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # Separate waived/unwaived warnings
        waived_items = {}
        missing_items = {}
        
        for warning in warnings:
            # Try matching by warning code
            if self.match_waiver_entry(warning['code'], waive_dict):
                waived_items[warning['name']] = {
                    'name': warning['name'],
                    'line_number': warning.get('line_number', 0),
                    'file_path': warning.get('file_path', 'N/A')
                }
            else:
                missing_items[warning['name']] = {
                    'name': warning['name'],
                    'line_number': warning.get('line_number', 0),
                    'file_path': warning.get('file_path', 'N/A')
                }
        
        # FIXED: API-017 - waive_dict.keys() are item names (strings)
        used_codes = {w['code'] for w in warnings if self.match_waiver_entry(w['code'], waive_dict)}
        unused_waivers = [
            {'name': name}
            for name in waive_dict.keys()
            if name not in used_codes
        ]
        
        # FIXED: API-021 - Use missing_items parameter instead of unwaived_items
        # Type 4: Use TYPE1_4 reason (emphasize "found/not found") - API-026
        return self.build_complete_output(
            waived_items=waived_items,
            missing_items=missing_items,
            waive_dict=waive_dict,
            unused_waivers=unused_waivers,
            waived_desc=self.WAIVED_DESC,
            missing_desc=self.MISSING_DESC_TYPE1_4,
            found_reason=self.FOUND_REASON_TYPE1_4,
            missing_reason=self.MISSING_REASON_TYPE1_4,
            waived_base_reason=self.WAIVED_BASE_REASON
        )


# =========================================================================
# Entry Point
# =========================================================================

def main():
    """Main entry point."""
    checker = Check_7_0_0_03()
    checker.init_checker(Path(__file__))
    result = checker.execute_check()
    checker.write_output(result)
    return 0 if result.is_pass else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())