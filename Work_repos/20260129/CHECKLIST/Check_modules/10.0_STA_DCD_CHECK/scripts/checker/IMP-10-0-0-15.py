################################################################################
# Script Name: IMP-10-0-0-15.py
#
# Purpose:
#   Confirm the double_clock check result is clean.
#
# Logic:
#   - Parse input files: double_clock_*.rpt
#   - Extract view names and timestamps from report headers
#   - Detect column headers marking violation section boundaries
#   - Parse violation entries (instance/pin, transition type, reverse swing/slope)
#   - Aggregate violations across all files and views
#   - Classify results: clean report (headers only) = PASS, violations found = FAIL
#   - Apply waiver logic if configured (match violations against waiver patterns)
#
# Auto Type Detection:
#   Type 1: requirements.value=N/A, waivers.value=N/A/0 → Boolean check
#   Type 2: requirements.value>0, pattern_items exists, waivers.value=N/A/0 → Value comparison
#   Type 3: requirements.value>0, pattern_items exists, waivers.value>0 → Value with waiver logic
#   Type 4: requirements.value=N/A, waivers.value>0 → Boolean with waiver logic
#
# Waiver Tag Rules:
#   When waivers.value > 0 (Type 3/4):
#     - All waive_items related INFO/FAIL/WARN reason suffix: [WAIVER]
#   When waivers.value = 0 (Type 1/2):
#     - waive_items output as INFO with suffix: [WAIVED_INFO]
#     - FAIL/WARN converted to INFO with suffix: [WAIVED_AS_INFO]
#   All types support value = N/A
#
# Refactored: 2025-12-19 (Using checker_templates v1.1.0)
#
# Author: yyin
# Date: 2025-12-19
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
class Check_10_0_0_15(InputFileParserMixin, OutputBuilderMixin, WaiverHandlerMixin, BaseChecker):
    """
    IMP-10-0-0-15: Confirm the double_clock check result is clean.
    
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
    # UNIFIED DESCRIPTIONS - MUST be identical across ALL Type 1/2/3/4
    # =========================================================================
    FOUND_DESC = "Clean timing views with no double clocking violations"
    MISSING_DESC = "Double clocking violations detected"
    WAIVED_DESC = "Waived double clocking violations"
    FOUND_REASON = "All timing views are clean - no double clocking violations detected"
    MISSING_REASON = "Double clocking violation detected in timing view"
    WAIVED_BASE_REASON = "Double clocking violation waived per design team approval"
    UNUSED_WAIVER_REASON = "Waiver not matched to any violations in current reports"
    
    def __init__(self):
        """Initialize the checker."""
        super().__init__(
            check_module="10.0_STA_DCD_CHECK",
            item_id="IMP-10-0-0-15",
            item_desc="Confirm the double_clock check result is clean."
        )
        # Custom member variables for parsed data
        self._parsed_violations: List[Dict[str, Any]] = []
        self._parsed_views: List[Dict[str, Any]] = []
        self._metadata: Dict[str, str] = {}
    
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
        except Exception as e:
            # Handle unexpected errors
            error_msg = f"Unexpected error during check execution: {str(e)}"
            return create_check_result(
                is_pass=False,
                item_id=self.item_id,
                item_desc=self.item_desc,
                details=[DetailItem(
                    severity=Severity.FAIL,
                    name=error_msg,
                    line_number=0,
                    file_path="",
                    reason=error_msg
                )]
            )
    
    # =========================================================================
    # Input Parsing (Common for All Types)
    # =========================================================================
    
    def _parse_input_files(self) -> Dict[str, Any]:
        """
        Parse input files to extract double clocking violations.
        
        Uses InputFileParserMixin helper methods:
        - validate_input_files() - Returns (valid_files, missing_files) tuple
        - read_file() - Safe file reading with error handling
        
        Returns:
            Dict with parsed data:
            - 'violations': List[Dict] - Violation items with metadata (line_number, file_path)
            - 'views': List[Dict] - View information
            - 'metadata': Dict - File metadata
            - 'errors': List - Any parsing errors encountered
        """
        # 1. Validate input files - IMPORTANT: returns tuple (valid_files_list, missing_files_list)
        valid_files, missing_files = self.validate_input_files()
        
        # FIXED: Explicitly check for empty list
        if missing_files:
            raise ConfigurationError(
                self.create_missing_files_error(missing_files)
            )
        
        if not valid_files or len(valid_files) == 0:
            error_msg = "No valid input files found"
            raise ConfigurationError(
                create_check_result(
                    is_pass=False,
                    item_id=self.item_id,
                    item_desc=self.item_desc,
                    details=[DetailItem(
                        severity=Severity.FAIL,
                        name=error_msg,
                        line_number=0,
                        file_path="",
                        reason=error_msg
                    )]
                )
            )
        
        # 2. Parse using patterns from file analysis
        all_violations = []
        all_views = []
        parsing_errors = []
        
        # Define parsing patterns
        patterns = {
            'view_header': re.compile(r'Double Clocking Report For View:\s+([\w\d_]+)'),
            'timestamp': re.compile(r'Generated:\s+(.+?)\s*$'),
            'column_header': re.compile(r'^Instance Pin\s+Transition Type\s+Reverse Swing\s+Reverse Slope'),
            'violation': re.compile(r'^([\w\d_/]+)\s+(\w+)\s+([\d.]+(?:e[+-]?\d+)?)\s+([\d.]+(?:e[+-]?\d+)?)'),
            'section_delimiter': re.compile(r'^\*{50,}')
        }
        
        # State machine for parsing
        for file_path in valid_files:
            try:
                current_view = None
                current_timestamp = None
                in_violation_section = False
                
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line_num, line in enumerate(f, 1):
                        line = line.rstrip()
                        
                        # Check for view header
                        view_match = patterns['view_header'].search(line)
                        if view_match:
                            current_view = view_match.group(1)
                            in_violation_section = False
                            continue
                        
                        # Check for timestamp
                        timestamp_match = patterns['timestamp'].search(line)
                        if timestamp_match:
                            current_timestamp = timestamp_match.group(1)
                            continue
                        
                        # Check for column header (marks start of violation section)
                        if patterns['column_header'].search(line):
                            in_violation_section = True
                            # Record view info
                            if current_view:
                                all_views.append({
                                    'name': current_view,
                                    'timestamp': current_timestamp,
                                    'line_number': line_num,
                                    'file_path': str(file_path)
                                })
                            continue
                        
                        # Check for section delimiter (marks end of violation section)
                        # Only reset view if we're already in violation section
                        # This prevents the header delimiter from resetting the view
                        if patterns['section_delimiter'].search(line):
                            if in_violation_section:
                                # End of violation section - reset state
                                in_violation_section = False
                                current_view = None
                                current_timestamp = None
                            # Else: This is a header delimiter, don't reset view
                            continue
                        
                        # Parse violation entries
                        if in_violation_section and line.strip():
                            violation_match = patterns['violation'].search(line)
                            if violation_match:
                                instance_pin = violation_match.group(1)
                                transition_type = violation_match.group(2)
                                reverse_swing = violation_match.group(3)
                                reverse_slope = violation_match.group(4)
                                
                                # Create violation item with REQUIRED metadata
                                violation_name = f"{current_view}: {instance_pin} ({transition_type})"
                                all_violations.append({
                                    'name': violation_name,
                                    'view': current_view or 'unknown',
                                    'instance_pin': instance_pin,
                                    'transition_type': transition_type,
                                    'reverse_swing': reverse_swing,
                                    'reverse_slope': reverse_slope,
                                    'line_number': line_num,  # REQUIRED for report output!
                                    'file_path': str(file_path)  # REQUIRED for report output!
                                })
            
            except Exception as e:
                parsing_errors.append(f"Error parsing {file_path}: {str(e)}")
        
        # 3. Store frequently reused data on self
        self._parsed_violations = all_violations
        self._parsed_views = all_views
        self._metadata = {
            'total_violations': len(all_violations),
            'total_views': len(all_views),
            'files_parsed': len(valid_files)
        }
        
        # 4. Return aggregated dict
        return {
            'violations': all_violations,
            'views': all_views,
            'metadata': self._metadata,
            'errors': parsing_errors
        }
    
    # =========================================================================
    # Type 1: Boolean Check
    # =========================================================================
    
    def _execute_type1(self) -> CheckResult:
        """
        Type 1: Boolean Check.
        
        Custom boolean validation - check if any double clocking violations exist.
        Does NOT use pattern_items for searching.
        
        Use OutputBuilderMixin.build_complete_output() for automatic formatting.
        
        Returns:
            CheckResult with is_pass based on check logic
        """
        # Parse input
        data = self._parse_input_files()
        violations = data.get('violations', [])
        views = data.get('views', [])
        errors = data.get('errors', [])
        
        # Handle parsing errors
        if errors:
            return create_check_result(
                is_pass=False,
                item_id=self.item_id,
                item_desc=self.item_desc,
                details=[DetailItem(
                    severity=Severity.ERROR,
                    reason=f"Parsing errors encountered: {'; '.join(errors)}"
                )]
            )
        
        # FIXED: Convert violations to dict with metadata for source file/line display
        # Output format: "Fail: <name>. In line <N>, <filepath>: <reason>"
        violation_items = {
            v['name']: {
                'name': v['name'],
                'line_number': v.get('line_number', 0),
                'file_path': v.get('file_path', 'N/A')
            }
            for v in violations
        }
        
        # Convert views to dict for INFO display
        view_items = {
            v['name']: {
                'name': v['name'],
                'line_number': v.get('line_number', 0),
                'file_path': v.get('file_path', 'N/A')
            }
            for v in views
        }
        
        # FIXED: Pass dict directly, not list(dict.values())
        # Use template helper
        # If violations exist, they are "missing_items" (failures)
        # If no violations, views are "found_items" (clean reports)
        if violation_items:
            return self.build_complete_output(
                found_items={},
                missing_items=violation_items,
                found_desc=self.FOUND_DESC,
                missing_desc=self.MISSING_DESC,
                found_reason=self.FOUND_REASON,
                missing_reason=self.MISSING_REASON
            )
        else:
            return self.build_complete_output(
                found_items=view_items,
                missing_items={},
                found_desc=self.FOUND_DESC,
                missing_desc=self.MISSING_DESC,
                found_reason=self.FOUND_REASON,
                missing_reason=self.MISSING_REASON
            )
    
    # =========================================================================
    # Type 2: Value Check
    # =========================================================================
    
    def _execute_type2(self) -> CheckResult:
        """
        Type 2: Value Check.
        
        Search pattern_items in input files.
        found_items = patterns found; missing_items = patterns not found.
        PASS/FAIL depends on check purpose (violation check vs requirement check).
        
        Template auto-handles waiver=0 conversions.
        
        Returns:
            CheckResult with is_pass based on value comparison
        """
        # Parse input
        data = self._parse_input_files()
        violations = data.get('violations', [])
        views = data.get('views', [])
        errors = data.get('errors', [])
        
        # Handle parsing errors
        if errors:
            error_msg = f"Parsing errors encountered: {'; '.join(errors)}"
            return create_check_result(
                is_pass=False,
                item_id=self.item_id,
                item_desc=self.item_desc,
                details=[DetailItem(
                    severity=Severity.FAIL,
                    name=error_msg,
                    line_number=0,
                    file_path="",
                    reason=error_msg
                )]
            )
        
        # Get requirements
        pattern_items = self.item_data.get('requirements', {}).get('pattern_items', [])
        
        # FIXED: Convert violations to dict with metadata
        violation_items = {
            v['name']: {
                'name': v['name'],
                'line_number': v.get('line_number', 0),
                'file_path': v.get('file_path', 'N/A')
            }
            for v in violations
        }
        
        # Convert views to dict
        view_items = {
            v['name']: {
                'name': v['name'],
                'line_number': v.get('line_number', 0),
                'file_path': v.get('file_path', 'N/A')
            }
            for v in views
        }
        
        # FIXED: Pass dict directly, not list
        # For double_clock check, violations are "extra_items" (unexpected)
        # Clean views are "found_items" (expected)
        if violation_items:
            return self.build_complete_output(
                found_items=view_items,
                extra_items=violation_items,
                found_desc=self.FOUND_DESC,
                extra_desc=self.MISSING_DESC,
                found_reason=self.FOUND_REASON,
                missing_reason=self.MISSING_REASON
            )
        else:
            return self.build_complete_output(
                found_items=view_items,
                extra_items={},
                found_desc=self.FOUND_DESC,
                extra_desc=self.MISSING_DESC,
                found_reason=self.FOUND_REASON,
                missing_reason=self.MISSING_REASON
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
        violations = parsed_data.get('violations', [])
        views = parsed_data.get('views', [])
        errors = parsed_data.get('errors', [])
        
        # Handle parsing errors
        if errors:
            error_msg = f"Parsing errors encountered: {'; '.join(errors)}"
            return create_check_result(
                is_pass=False,
                item_id=self.item_id,
                item_desc=self.item_desc,
                details=[DetailItem(
                    severity=Severity.FAIL,
                    name=error_msg,
                    line_number=0,
                    file_path="",
                    reason=error_msg
                )]
            )
        
        # Parse waiver configuration using template helper
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # Separate waived/unwaived using template helper
        waived_items = {}
        unwaived_items = {}
        used_waiver_patterns = set()
        
        for violation in violations:
            violation_name = violation['name']
            violation_metadata = {
                'name': violation_name,
                'line_number': violation.get('line_number', 0),
                'file_path': violation.get('file_path', 'N/A')
            }
            
            # match_waiver_entry returns the matching waiver key or None
            matched_waiver = self.match_waiver_entry(violation_name, waive_dict)
            if matched_waiver:
                waived_items[violation_name] = violation_metadata
                used_waiver_patterns.add(matched_waiver)
            else:
                unwaived_items[violation_name] = violation_metadata
        
        # Find unused waivers - waive_dict is {pattern: reason}
        # Format should match IMP-10-0-0-14: only line_number, file_path, reason
        unused_waivers = {
            pattern: {
                'line_number': 0,
                'file_path': 'waiver_config',
                'reason': waive_dict[pattern]
            }
            for pattern in waive_dict.keys()
            if pattern not in used_waiver_patterns
        }
        
        # Convert views to dict for INFO display
        view_items = {
            v['name']: {
                'name': v['name'],
                'line_number': v.get('line_number', 0),
                'file_path': v.get('file_path', 'N/A')
            }
            for v in views
        }
        
        # FIXED: Pass dict directly, not list
        # Use template helper for automatic output formatting
        return self.build_complete_output(
            found_items=view_items,
            waived_items=waived_items,
            missing_items=unwaived_items,
            unused_waivers=unused_waivers,
            waive_dict=waive_dict,
            found_desc=self.FOUND_DESC,
            missing_desc=self.MISSING_DESC,
            waived_desc=self.WAIVED_DESC,
            found_reason=self.FOUND_REASON,
            missing_reason=self.MISSING_REASON,
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
        violations = data.get('violations', [])
        views = data.get('views', [])
        errors = data.get('errors', [])
        
        # Handle parsing errors
        if errors:
            error_msg = f"Parsing errors encountered: {'; '.join(errors)}"
            return create_check_result(
                is_pass=False,
                item_id=self.item_id,
                item_desc=self.item_desc,
                details=[DetailItem(
                    severity=Severity.FAIL,
                    name=error_msg,
                    line_number=0,
                    file_path="",
                    reason=error_msg
                )]
            )
        
        # Parse waiver configuration
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # Separate waived/unwaived violations
        waived_items = {}
        unwaived_items = {}
        used_waiver_patterns = set()
        
        for violation in violations:
            violation_name = violation['name']
            violation_metadata = {
                'name': violation_name,
                'line_number': violation.get('line_number', 0),
                'file_path': violation.get('file_path', 'N/A')
            }
            
            # match_waiver_entry returns the matching waiver key or None
            matched_waiver = self.match_waiver_entry(violation_name, waive_dict)
            if matched_waiver:
                waived_items[violation_name] = violation_metadata
                used_waiver_patterns.add(matched_waiver)
            else:
                unwaived_items[violation_name] = violation_metadata
        
        # Find unused waivers - waive_dict is {pattern: reason}
        # Format should match IMP-10-0-0-14: only line_number, file_path, reason
        unused_waivers = {
            pattern: {
                'line_number': 0,
                'file_path': 'waiver_config',
                'reason': waive_dict[pattern]
            }
            for pattern in waive_dict.keys()
            if pattern not in used_waiver_patterns
        }
        
        # Convert views to dict
        view_items = {
            v['name']: {
                'name': v['name'],
                'line_number': v.get('line_number', 0),
                'file_path': v.get('file_path', 'N/A')
            }
            for v in views
        }
        
        # FIXED: Pass dict directly, not list
        # Use template helper (auto-handles waiver=0)
        return self.build_complete_output(
            found_items=view_items,
            waived_items=waived_items,
            missing_items=unwaived_items,
            unused_waivers=unused_waivers,
            waive_dict=waive_dict,
            has_waiver_value=True,
            found_desc=self.FOUND_DESC,
            missing_desc=self.MISSING_DESC,
            waived_desc=self.WAIVED_DESC,
            found_reason=self.FOUND_REASON,
            missing_reason=self.MISSING_REASON,
            waived_base_reason=self.WAIVED_BASE_REASON
        )


# =========================================================================
# Entry Point
# =========================================================================

def main():
    """Main entry point."""
    checker = Check_10_0_0_15()
    checker.init_checker(Path(__file__))
    result = checker.execute_check()
    checker.write_output(result)
    return 0 if result.is_pass else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())