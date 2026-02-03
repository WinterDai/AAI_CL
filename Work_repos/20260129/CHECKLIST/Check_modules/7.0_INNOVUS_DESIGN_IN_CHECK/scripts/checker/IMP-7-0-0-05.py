################################################################################
# Script Name: IMP-7-0-0-05.py
#
# Purpose:
#   Confirm no issue for check_design in Innovus.
#
# Logic:
#   - Parse input files: IMP-7-0-0-05.rpt (Innovus check_design report in Tcl dict format)
#   - Extract design check categories (netlist, power_intent, timing, place, opt) with violation counts
#   - Parse check blocks to extract check ID, severity (error/warning), count, message, and violation list
#   - Handle nested braces for multi-element violations (coordinates, tuples)
#   - Aggregate violations by category and severity for summary statistics
#   - Store individual violations grouped by check ID with full context
#   - Determine PASS/FAIL: PASS if no errors found, FAIL if any errors detected
#   - Handle edge cases: empty violations lists, multi-line entries, truncated reports, missing fields
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
from checker_templates.input_file_parser_template import InputFileParserMixin


# MANDATORY: Inherit mixins in correct order (InputFileParserMixin first if used)
class Check_7_0_0_05(InputFileParserMixin, OutputBuilderMixin, WaiverHandlerMixin, BaseChecker):
    """
    IMP-7-0-0-05: Confirm no issue for check_design in Innovus.
    
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
    FOUND_DESC_TYPE1_4 = "No design rule violations found in check_design report"
    MISSING_DESC_TYPE1_4 = "Design rule violations detected in check_design report"
    FOUND_REASON_TYPE1_4 = "No design rule violations found in check_design report"
    MISSING_REASON_TYPE1_4 = "Design rule violation detected in check_design report"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_DESC_TYPE2_3 = "All design check categories passed validation"
    MISSING_DESC_TYPE2_3 = "Design check categories failed validation"
    FOUND_REASON_TYPE2_3 = "Design check category passed validation"
    MISSING_REASON_TYPE2_3 = "Design check category failed validation"
    
    # All Types (waiver description unified)
    WAIVED_DESC = "Waived design rule violations"
    
    # Waiver parameters (Type 3/4 ONLY)
    WAIVED_BASE_REASON = "Design rule violation waived per design approval"
    
    def __init__(self):
        """Initialize the checker."""
        super().__init__(
            check_module="7.0_INNOVUS_DESIGN_IN_CHECK",
            item_id="IMP-7-0-0-05",
            item_desc="Confirm no issue for check_design in Innovus."
        )
        # Custom member variables for parsed data
        self._parsed_items: List[Dict[str, Any]] = []
        self._category_stats: Dict[str, Dict[str, int]] = {}
        self._violations_by_check: Dict[str, Dict[str, Any]] = {}
    
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
        
        Parses Innovus check_design report in Tcl dict format to extract:
        - Design check categories (netlist, power_intent, timing, place, opt)
        - Check blocks with ID, severity, count, message, and violation list
        - Handles nested braces for multi-element violations
        
        Returns:
            Dict with parsed data:
            - 'items': List[Dict] - Violations with metadata (line_number, file_path)
            - 'metadata': Dict - Category statistics and summary
            - 'errors': List - Any parsing errors encountered
        """
        # 1. Validate inputs - IMPORTANT: returns tuple (valid_files_list, missing_files_list)
        valid_files, missing_files = self.validate_input_files()
        
        # FIXED: KNOWN_ISSUE_LOGIC-001 - Explicitly check for empty list
        if not valid_files or len(valid_files) == 0:
            raise ConfigurationError("No valid input files found")
        
        if missing_files:
            raise ConfigurationError(
                self.create_missing_files_error(missing_files)
            )
        
        # 2. Parse using state machine for Tcl dict format
        all_violations = []
        category_stats = {}
        violations_by_check = {}
        errors = []
        
        for file_path in valid_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                    
                # State machine variables
                current_category = None
                current_check_id = None
                current_severity = None
                current_count = 0
                current_message = ""
                pending_message = ""  # Store message before dict set block
                in_dict_block = False  # Track if we're inside a dict block
                block_start_line = 0
                violations_list = []
                in_violations_block = False
                brace_depth = 0
                
                for line_num, line in enumerate(lines, 1):
                    line_stripped = line.strip()
                    
                    # Pattern 1: Design check category header
                    category_match = re.match(r'^#Design Check : (\w+) \((\d+)\)', line_stripped)
                    if category_match:
                        current_category = category_match.group(1)
                        total_count = int(category_match.group(2))
                        if current_category not in category_stats:
                            category_stats[current_category] = {'errors': 0, 'warnings': 0, 'total': total_count}
                        continue
                    
                    # Pattern 6: Message text (comes BEFORE dict set block)
                    message_match = re.match(r'^# Message: (.+)', line_stripped)
                    if message_match:
                        pending_message = message_match.group(1)
                        continue
                    
                    # Pattern 2: Check ID and category block start
                    check_block_match = re.match(r'^dict set design_checks (\w+) ([A-Z0-9-]+) \{', line_stripped)
                    if check_block_match:
                        # Start new check block
                        current_category = check_block_match.group(1)
                        current_check_id = check_block_match.group(2)
                        current_severity = None
                        current_count = 0
                        current_message = pending_message  # Use pending message
                        pending_message = ""  # Clear pending
                        violations_list = []
                        in_dict_block = True
                        in_violations_block = False
                        brace_depth = 1  # Start with 1 for the opening brace
                        block_start_line = line_num
                        continue
                    
                    # Pattern 3: Severity level (process BEFORE brace tracking)
                    if in_dict_block:
                        severity_match = re.match(r'^\s+severity\s+(error|warning)', line)  # Use original line, not stripped
                        if severity_match:
                            current_severity = severity_match.group(1)
                            # Don't continue, still need to track braces
                    
                    # Pattern 4: Violation count (process BEFORE brace tracking)
                    if in_dict_block:
                        count_match = re.match(r'^\s+count\s+(\d+)', line)  # Use original line, not stripped
                        if count_match:
                            current_count = int(count_match.group(1))
                            # Don't continue, still need to track braces
                    
                    # Violations block start
                    if in_dict_block and re.match(r'^\s+violations \{', line_stripped):
                        in_violations_block = True
                        # Don't continue, still need to track braces
                    
                    # Pattern 5: Violation list items (inside violations block)
                    if in_violations_block:
                        # Extract violation item
                        violation_match = re.match(r'^\s+\{(.+?)\}\s*$', line_stripped)
                        if violation_match:
                            violation_detail = violation_match.group(1)
                            violations_list.append(violation_detail)
                        
                        # Check if violations block ended
                        if line_stripped == '}':
                            in_violations_block = False
                        # Don't continue, still need to track braces
                    
                    # Track brace depth to detect end of dict block (do this LAST)
                    if in_dict_block:
                        open_braces = line_stripped.count('{')
                        close_braces = line_stripped.count('}')
                        brace_depth += open_braces - close_braces
                        
                        # Check if dict block ended
                        if brace_depth == 0:
                            # Save completed check block
                            if current_check_id and current_category:
                                self._save_check_block(
                                    current_category, current_check_id, current_severity,
                                    current_count, current_message, violations_list,
                                    violations_by_check, category_stats, all_violations,
                                    file_path, line_num
                                )
                            # Reset state
                            in_dict_block = False
                            current_check_id = None
                            continue
                
                # No need to save last check block - already saved when } is encountered
                    
            except Exception as e:
                errors.append(f"Error parsing {file_path}: {str(e)}")
        
        # 3. Store frequently reused data on self
        self._parsed_items = all_violations
        self._category_stats = category_stats
        self._violations_by_check = violations_by_check
        
        # 4. Return aggregated dict
        return {
            'items': all_violations,
            'metadata': {
                'category_stats': category_stats,
                'total_violations': len(all_violations),
                'total_errors': sum(stats['errors'] for stats in category_stats.values()),
                'total_warnings': sum(stats['warnings'] for stats in category_stats.values())
            },
            'errors': errors
        }
    
    def _save_check_block(
        self, category: str, check_id: str, severity: str,
        count: int, message: str, violations_list: List[str],
        violations_by_check: Dict, category_stats: Dict,
        all_violations: List, file_path: Path, line_num: int
    ):
        """
        Save parsed check block data.
        
        Args:
            category: Design check category (netlist, power_intent, etc.)
            check_id: Check ID (e.g., CHKNETLIST-1)
            severity: Severity level (error or warning)
            count: Violation count
            message: Descriptive message
            violations_list: List of violation details
            violations_by_check: Dict to store violations by check ID
            category_stats: Dict to store category statistics
            all_violations: List to append all violations
            file_path: Source file path
            line_num: Source line number
        """
        if not severity:
            severity = 'warning'  # Default if missing
        
        # Update category statistics
        if category in category_stats:
            if severity == 'error':
                category_stats[category]['errors'] += count
            else:
                category_stats[category]['warnings'] += count
        
        # Store violation by check ID
        check_key = f"{category}:{check_id}"
        violations_by_check[check_key] = {
            'category': category,
            'check_id': check_id,
            'severity': severity,
            'count': count,
            'message': message,
            'violations': violations_list
        }
        
        # Add to all violations list
        # Format: "[category]:[CHECK_ID] (severity: X, count: Y): message"
        formatted_name = f"{category}:{check_id} (severity: {severity}, count: {count}): {message}"
        all_violations.append({
            'name': formatted_name,
            'category': category,
            'check_id': check_id,
            'severity': severity,
            'count': count,
            'message': message,
            'line_number': line_num,
            'file_path': str(file_path)
        })
    
    # =========================================================================
    # Type 1: Boolean Check
    # =========================================================================
    
    def _execute_type1(self) -> CheckResult:
        """
        Type 1: Boolean Check.
        
        Check if any design rule violations (errors) exist in check_design report.
        PASS if no errors found, FAIL if any errors detected.
        Display all violations (errors + warnings) in output with grouped format.
        
        Returns:
            CheckResult with is_pass based on check logic
        """
        # Parse input
        data = self._parse_input_files()
        items = data.get('items', [])
        metadata = data.get('metadata', {})
        
        # Separate errors and warnings
        error_items = {}
        warning_items = {}
        
        for item in items:
            item_data = {
                'name': item['name'],
                'line_number': item.get('line_number', 0),
                'file_path': item.get('file_path', 'N/A')
            }
            
            if item['severity'] == 'error':
                error_items[item['name']] = item_data
            else:  # warning
                warning_items[item['name']] = item_data
        
        # PASS if no errors, FAIL if any errors
        # Display: Errors in ERROR01, Warnings in INFO01
        if error_items:
            # Has errors -> FAIL
            return self.build_complete_output(
                found_items=warning_items,  # Warnings as INFO
                missing_items=error_items,  # Errors as ERROR
                found_desc=self.FOUND_DESC_TYPE1_4,
                missing_desc=self.MISSING_DESC_TYPE1_4,
                found_reason=self.FOUND_REASON_TYPE1_4,
                missing_reason=self.MISSING_REASON_TYPE1_4
            )
        else:
            # No errors -> PASS
            return self.build_complete_output(
                found_items=warning_items,  # Warnings as INFO
                missing_items=[],  # No errors
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
        Pattern format: "category:CHECK_ID" or substring match.
        Only output items that match pattern_items.
        PASS if all required patterns are found.
        
        Returns:
            CheckResult with is_pass based on value comparison
        """
        # Parse input
        data = self._parse_input_files()
        items = data.get('items', [])
        
        # Get requirements
        requirements = self.item_data.get('requirements', {})
        pattern_items = requirements.get('pattern_items', [])
        expected_value = requirements.get('value', 'N/A')
        
        # Build all items dict with severity info
        all_items = {}
        for item in items:
            all_items[item['name']] = {
                'name': item['name'],
                'severity': item['severity'],
                'line_number': item.get('line_number', 0),
                'file_path': item.get('file_path', 'N/A')
            }
        
        # Match patterns against items - only output matched items
        found_items = {}  # Matched items (INFO)
        missing_items = {}  # Matched error items (ERROR)
        missing_patterns = []  # Patterns not matched
        
        for pattern in pattern_items:
            matched = False
            for item_name, item_data in all_items.items():
                # Substring match for pattern
                if pattern.lower() in item_name.lower():
                    output_data = {
                        'name': item_name,
                        'line_number': item_data['line_number'],
                        'file_path': item_data['file_path']
                    }
                    
                    # Separate by severity
                    if item_data['severity'] == 'error':
                        missing_items[item_name] = output_data
                    else:
                        found_items[item_name] = output_data
                    matched = True
                    break
            
            if not matched:
                missing_patterns.append(pattern)
        
        # Use template helper - only output pattern-matched items
        return self.build_complete_output(
            found_items=found_items,  # Matched warnings as INFO
            missing_items=missing_items if missing_items else missing_patterns,  # Matched errors as ERROR, or missing patterns
            found_desc=f"{self.FOUND_DESC_TYPE2_3} ({len(found_items) + len(missing_items)}/{expected_value} patterns found)",
            missing_desc=f"{self.MISSING_DESC_TYPE2_3} ({len(missing_items)} errors, {len(missing_patterns)} patterns not found)",
            found_reason=self.FOUND_REASON_TYPE2_3,
            missing_reason=self.MISSING_REASON_TYPE2_3
        )
    
    # =========================================================================
    # Type 3: Value Check with Waiver Logic
    # =========================================================================
    
    def _execute_type3(self) -> CheckResult:
        """
        Type 3: Value check with waiver support.
        
        Search pattern_items in input files, then apply waiver logic.
        Only output items that match pattern_items.
        Matched errors can be waived; unwaived errors -> FAIL.
        
        Returns:
            CheckResult with FAIL for unwaived errors, INFO for waived items
        """
        # Parse input
        parsed_data = self._parse_input_files()
        items = parsed_data.get('items', [])
        
        # Get requirements
        requirements = self.item_data.get('requirements', {})
        pattern_items = requirements.get('pattern_items', [])
        
        # FIXED: KNOWN_ISSUE_API-016 - Use waivers.get() directly to preserve dict format
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # Build all items dict with severity info
        all_items = {}
        for item in items:
            all_items[item['name']] = {
                'name': item['name'],
                'severity': item['severity'],
                'line_number': item.get('line_number', 0),
                'file_path': item.get('file_path', 'N/A')
            }
        
        # Match patterns against items - only process matched items
        found_items = {}  # Matched warnings (INFO)
        waived_items = {}  # Matched waived errors (INFO)
        unwaived_errors = {}  # Matched unwaived errors (ERROR)
        missing_patterns = []  # Patterns not matched
        used_waiver_patterns = set()
        
        for pattern in pattern_items:
            matched = False
            for item_name, item_data in all_items.items():
                # Substring match for pattern
                if pattern.lower() in item_name.lower():
                    output_data = {
                        'name': item_name,
                        'line_number': item_data['line_number'],
                        'file_path': item_data['file_path']
                    }
                    
                    if item_data['severity'] == 'error':
                        # Check if error is waived
                        matched_waiver = None
                        for waiver_pattern in waive_dict.keys():
                            if self.match_waiver_entry(item_name, {waiver_pattern: waive_dict[waiver_pattern]}):
                                matched_waiver = waiver_pattern
                                used_waiver_patterns.add(waiver_pattern)
                                break
                        
                        if matched_waiver:
                            waived_items[item_name] = output_data
                        else:
                            unwaived_errors[item_name] = output_data
                    else:  # warning
                        found_items[item_name] = output_data
                    
                    matched = True
                    break
            
            if not matched:
                missing_patterns.append(pattern)
        
        # Find unused waivers
        unused_waivers = {
            w: {
                'line_number': 0,
                'file_path': 'N/A',
                'reason': waive_dict[w]
            }
            for w in waive_dict.keys()
            if w not in used_waiver_patterns
        }
        
        # Build output: only pattern-matched items
        return self.build_complete_output(
            found_items=found_items,  # Matched warnings as INFO
            waived_items=waived_items,  # Waived matched errors as INFO
            missing_items=unwaived_errors if unwaived_errors else missing_patterns,  # Unwaived matched errors as ERROR
            waive_dict=waive_dict,
            unused_waivers=unused_waivers,
            found_desc=self.FOUND_DESC_TYPE2_3,
            missing_desc=self.MISSING_DESC_TYPE2_3,
            waived_desc=self.WAIVED_DESC,
            found_reason=self.FOUND_REASON_TYPE2_3,
            missing_reason=self.MISSING_REASON_TYPE2_3,
            waived_base_reason=self.WAIVED_BASE_REASON,
            unused_waiver_reason="Waiver not matched - no corresponding design rule violation found"
        )
    
    # =========================================================================
    # Type 4: Boolean Check with Waiver Logic
    # =========================================================================
    
    def _execute_type4(self) -> CheckResult:
        """
        Type 4: Boolean check with waiver support (Type 1 + waiver).
        
        Same boolean check as Type 1 (no pattern_items), plus waiver classification.
        Errors can be waived; PASS if all errors are waived.
        
        Returns:
            CheckResult with waiver logic applied
        """
        # Parse input
        data = self._parse_input_files()
        items = data.get('items', [])
        
        # FIXED: KNOWN_ISSUE_API-016 - Use waivers.get() directly to preserve dict format
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # Separate errors and warnings, then apply waiver logic
        waived_items = {}
        unwaived_errors = {}
        warning_items = {}
        used_waiver_patterns = set()
        
        for item in items:
            item_name = item['name']
            item_data = {
                'name': item_name,
                'line_number': item.get('line_number', 0),
                'file_path': item.get('file_path', 'N/A')
            }
            
            if item['severity'] == 'error':
                # Check if error is waived
                matched_waiver = None
                for waiver_pattern in waive_dict.keys():
                    if self.match_waiver_entry(item_name, {waiver_pattern: waive_dict[waiver_pattern]}):
                        matched_waiver = waiver_pattern
                        used_waiver_patterns.add(waiver_pattern)
                        break
                
                if matched_waiver:
                    waived_items[item_name] = item_data
                else:
                    unwaived_errors[item_name] = item_data
            else:  # warning
                warning_items[item_name] = item_data
        
        # Find unused waivers
        unused_waivers = {
            w: {
                'line_number': 0,
                'file_path': 'N/A',
                'reason': waive_dict[w]
            }
            for w in waive_dict.keys()
            if w not in used_waiver_patterns
        }
        
        # Build output: warnings as INFO, waived errors as INFO, unwaived errors as ERROR
        return self.build_complete_output(
            found_items=warning_items,  # Warnings as INFO
            waived_items=waived_items,  # Waived errors as INFO
            missing_items=unwaived_errors,  # Unwaived errors as ERROR
            waive_dict=waive_dict,
            unused_waivers=unused_waivers,
            found_desc=self.FOUND_DESC_TYPE1_4,
            missing_desc=self.MISSING_DESC_TYPE1_4,
            waived_desc=self.WAIVED_DESC,
            found_reason=self.FOUND_REASON_TYPE1_4,
            missing_reason=self.MISSING_REASON_TYPE1_4,
            waived_base_reason=self.WAIVED_BASE_REASON,
            unused_waiver_reason="Waiver not matched - no corresponding design rule violation found"
        )


# =========================================================================
# Entry Point
# =========================================================================

def main():
    """Main entry point."""
    checker = Check_7_0_0_05()
    checker.init_checker(Path(__file__))
    result = checker.execute_check()
    checker.write_output(result)
    return 0 if result.is_pass else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())