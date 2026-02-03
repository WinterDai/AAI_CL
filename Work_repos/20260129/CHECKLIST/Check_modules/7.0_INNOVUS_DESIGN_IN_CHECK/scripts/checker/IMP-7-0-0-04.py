################################################################################
# Script Name: IMP-7-0-0-04.py
#
# Purpose:
#   Confirm no issue for check_timing (all modes) in Innovus.
#
# Logic:
#   - Parse input files: IMP-7-0-0-04*.rpt (Innovus check_timing reports)
#   - Extract timing constraint warnings from three sections:
#     * TIMING CHECK SUMMARY: Aggregate warning counts by type
#     * TIMING CHECK DETAIL: Pin-level warnings with view context
#     * TIMING CHECK IDEAL CLOCKS: Clocks with ideal waveforms
#   - Use state machine to identify sections by detecting '---' delimiter lines
#   - Parse summary section for warning types and counts
#   - Parse detail section using 3-line grouping (pin, description, view)
#   - Aggregate warnings across all view-specific report files
#   - Classify as PASS (no warnings) or FAIL (warnings detected)
#   - Report both summary statistics and detailed pin-level violations
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
# Date: 2025-12-23
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
class Check_7_0_0_04(InputFileParserMixin, OutputBuilderMixin, WaiverHandlerMixin, BaseChecker):
    """
    IMP-7-0-0-04: Confirm no issue for check_timing (all modes) in Innovus.
    
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
    # ⭐ DESCRIPTION CONSTANTS - Split by Type semantics (API-026)
    # =========================================================================
    # DESC constants are split by Type for semantic clarity (same as REASON split)
    # Type 1/4 emphasize "found/not found", Type 2/3 emphasize "matched/satisfied"
    
    # Type 1/4: Boolean checks - emphasize "found/not found" (existence)
    FOUND_DESC_TYPE1_4 = "No timing constraint warnings found in check_timing reports"
    MISSING_DESC_TYPE1_4 = "Timing constraint warnings detected in check_timing reports"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_DESC_TYPE2_3 = "All required timing constraints validated successfully"
    MISSING_DESC_TYPE2_3 = "Required timing constraints not satisfied"
    
    # All Types (waiver description unified)
    WAIVED_DESC = "Timing constraint warnings waived per design approval"
    
    # ⭐ REASON CONSTANTS - Split by Type semantics (API-025)
    # ALL Types pass found_reason/missing_reason, but use different constants
    
    # Type 1/4: Boolean checks - emphasize "found/not found" (existence)
    FOUND_REASON_TYPE1_4 = "No timing constraint warnings found in check_timing analysis"
    MISSING_REASON_TYPE1_4 = "Timing constraint warning detected - may cause incorrect timing analysis"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_REASON_TYPE2_3 = "Required timing constraint pattern matched and validated"
    MISSING_REASON_TYPE2_3 = "Expected timing constraint pattern not satisfied or missing"
    
    # Waiver-related (Type 3/4 only)
    WAIVED_BASE_REASON = "Timing constraint warning waived per design approval"
    UNUSED_WAIVER_REASON = "Waiver defined but no violation matched"
    
    def __init__(self):
        """Initialize the checker."""
        super().__init__(
            check_module="7.0_INNOVUS_DESIGN_IN_CHECK",
            item_id="IMP-7-0-0-04",
            item_desc="Confirm no issue for check_timing (all modes) in Innovus."
        )
        # Custom member variables for parsed data
        self._parsed_items: List[Dict[str, Any]] = []
        self._metadata: Dict[str, str] = {}
        self._warning_summary: Dict[str, int] = {}
    
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
        Parse input files to extract timing constraint warnings.
        
        Parses Innovus check_timing reports containing:
        - TIMING CHECK SUMMARY: Warning counts by type
        - TIMING CHECK DETAIL: Pin-level warnings with view context
        - TIMING CHECK IDEAL CLOCKS: Clocks with ideal waveforms
        
        Returns:
            Dict with parsed data:
            - 'items': List[Dict] - Timing constraint warnings with metadata
            - 'metadata': Dict - Summary statistics
            - 'errors': List - Parsing errors
        """
        # 1. Validate input files - IMPORTANT: returns tuple (valid_files_list, missing_files_list)
        valid_files, missing_files = self.validate_input_files()
        
        # Fix LOGIC-001: Explicitly check for empty list
        if not valid_files or len(valid_files) == 0:
            raise ConfigurationError(
                self.create_missing_files_error(missing_files if missing_files else ["No input files found"])
            )
        
        if missing_files:
            raise ConfigurationError(
                self.create_missing_files_error(missing_files)
            )
        
        # 2. Parse using state machine for section-based parsing
        all_warnings = []
        warning_summary = {}
        errors = []
        
        # Patterns for parsing
        pattern_summary = re.compile(r'^\s*(\w+)\s+(.+?)\s+(\d+)\s*$')
        pattern_pin = re.compile(r'^\s*([^\s].+?)\s*$')
        pattern_description = re.compile(r'^\s+([A-Z][a-z].+?)\s*$')
        pattern_view = re.compile(r'^\s+(func_\S+|\S+_hold|\S+_setup)\s*$')
        pattern_ideal_clock = re.compile(r'^\s*(\S+)\s+(func_\S+|\S+_hold|\S+_setup)\s*$')
        pattern_section_delimiter = re.compile(r'^-{3,}')
        
        for file_path in valid_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                
                # State machine for section parsing
                state = 'INIT'
                section_name = ''
                detail_buffer = []  # Buffer for 3-line grouping in detail section
                
                for line_num, line in enumerate(lines, 1):
                    # Detect section delimiters
                    if pattern_section_delimiter.search(line):
                        # Next non-empty line is section header
                        continue
                    
                    # Detect section headers
                    if 'TIMING CHECK SUMMARY' in line:
                        state = 'IN_SUMMARY'
                        section_name = 'SUMMARY'
                        continue
                    elif 'TIMING CHECK DETAIL' in line:
                        state = 'IN_DETAIL'
                        section_name = 'DETAIL'
                        detail_buffer = []
                        continue
                    elif 'TIMING CHECK IDEAL CLOCKS' in line:
                        state = 'IN_IDEAL_CLOCKS'
                        section_name = 'IDEAL_CLOCKS'
                        continue
                    
                    # Parse based on current state
                    if state == 'IN_SUMMARY':
                        match = pattern_summary.search(line)
                        if match:
                            warning_type = match.group(1)
                            description = match.group(2).strip()
                            count = int(match.group(3))
                            
                            # Aggregate counts across files (for reference only)
                            if warning_type not in warning_summary:
                                warning_summary[warning_type] = 0
                            warning_summary[warning_type] += count
                            
                            # NOTE: Do NOT create warning entries from SUMMARY section
                            # Only use DETAIL and IDEAL_CLOCKS sections for actual violations
                            # SUMMARY is just aggregate statistics
                    
                    elif state == 'IN_DETAIL':
                        # 3-line grouping: pin, description, view
                        if line.strip() == '':
                            # Reset buffer on blank line
                            detail_buffer = []
                            continue
                        
                        detail_buffer.append((line_num, line))
                        
                        if len(detail_buffer) == 3:
                            # Extract pin, description, view
                            pin_line_num, pin_line = detail_buffer[0]
                            desc_line_num, desc_line = detail_buffer[1]
                            view_line_num, view_line = detail_buffer[2]
                            
                            match_pin = pattern_pin.search(pin_line)
                            match_desc = pattern_description.search(desc_line)
                            match_view = pattern_view.search(view_line)
                            
                            if match_pin and match_desc and match_view:
                                pin_name = match_pin.group(1).strip()
                                warning_desc = match_desc.group(1).strip()
                                view_name = match_view.group(1).strip()
                                
                                # Derive warning_type from description
                                warning_type = 'unknown'
                                if 'Clock not found' in warning_desc or 'clock is expected' in warning_desc:
                                    warning_type = 'clock_expected'
                                elif 'Unconstrained' in warning_desc:
                                    warning_type = 'uncons_endpoint'
                                elif 'No drive' in warning_desc:
                                    warning_type = 'no_drive'
                                
                                all_warnings.append({
                                    'name': f"{warning_desc} | Pin: {pin_name} | View: {view_name}",
                                    'pin': pin_name,
                                    'warning_type': warning_type,
                                    'description': warning_desc,
                                    'view': view_name,
                                    'line_number': pin_line_num,
                                    'file_path': str(file_path)
                                })
                            
                            # Reset buffer
                            detail_buffer = []
                    
                    elif state == 'IN_IDEAL_CLOCKS':
                        match = pattern_ideal_clock.search(line)
                        if match:
                            clock_name = match.group(1)
                            view_name = match.group(2)
                            
                            all_warnings.append({
                                'name': f"Ideal clock waveform | Clock: {clock_name} | View: {view_name}",
                                'clock': clock_name,
                                'warning_type': 'ideal_clock_waveform',
                                'view': view_name,
                                'description': 'Clock waveform is ideal',
                                'line_number': line_num,
                                'file_path': str(file_path)
                            })
            
            except Exception as e:
                errors.append(f"Error parsing {file_path}: {str(e)}")
        
        # 3. Store frequently reused data on self
        self._parsed_items = all_warnings
        self._warning_summary = warning_summary
        
        # 4. Return aggregated dict
        return {
            'items': all_warnings,
            'metadata': {
                'total_warnings': len(all_warnings),
                'warning_summary': warning_summary,
                'files_parsed': len(valid_files)
            },
            'errors': errors
        }
    
    # =========================================================================
    # Type 1: Boolean Check
    # =========================================================================
    
    def _execute_type1(self) -> CheckResult:
        """
        Type 1: Boolean Check.
        
        Check if any timing constraint warnings exist in check_timing reports.
        PASS if no warnings found, FAIL if warnings detected.
        
        Returns:
            CheckResult with is_pass based on check logic
        """
        # Parse input
        data = self._parse_input_files()
        items = data.get('items', [])
        
        # Group warnings by view and warning_type, then count occurrences
        # Output format: "{warning_type} ({count} occurrences) | View: {view}"
        violations_by_view_and_type = {}
        
        for item in items:
            # Determine view from item
            view = item.get('view', 'unknown')
            warning_type = item.get('warning_type', 'unknown')
            
            # Create key for grouping
            key = (view, warning_type)
            
            if key not in violations_by_view_and_type:
                violations_by_view_and_type[key] = {
                    'count': 0,
                    'first_line': item.get('line_number', 0),
                    'first_file': item.get('file_path', 'N/A')
                }
            violations_by_view_and_type[key]['count'] += 1
        
        # Build missing_items with formatted names
        missing_items = {}
        for (view, warning_type), info in violations_by_view_and_type.items():
            item_name = f"{warning_type} ({info['count']} occurrences) | View: {view}"
            missing_items[item_name] = {
                'name': item_name,
                'line_number': info['first_line'],
                'file_path': info['first_file']
            }
        
        # Build found_items (empty if there are violations)
        found_items = {}
        if not items:
            found_items['No timing constraint warnings'] = {
                'name': 'No timing constraint warnings',
                'line_number': 0,
                'file_path': 'All check_timing reports'
            }
        
        # Use template helper
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
        Pattern format: "warning_type|View: view_name" (substring match)
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
        
        # Group warnings by view and warning_type
        violations_by_view_and_type = {}
        
        for item in items:
            view = item.get('view', 'unknown')
            warning_type = item.get('warning_type', 'unknown')
            key = (view, warning_type)
            
            if key not in violations_by_view_and_type:
                violations_by_view_and_type[key] = {
                    'count': 0,
                    'first_line': item.get('line_number', 0),
                    'first_file': item.get('file_path', 'N/A')
                }
            violations_by_view_and_type[key]['count'] += 1
        
        # Match patterns against grouped violations
        # Pattern format: "warning_type|View: view_name" (substring match)
        found_items = {}
        missing_patterns = []
        
        for pattern in pattern_items:
            matched = False
            for (view, warning_type), info in violations_by_view_and_type.items():
                # Build searchable string: "warning_type | View: view"
                search_str = f"{warning_type} | View: {view}"
                
                # SUBSTRING MATCH (pattern_items are descriptive strings)
                if pattern.lower() in search_str.lower():
                    item_name = f"{warning_type} ({info['count']} occurrences) | View: {view}"
                    found_items[pattern] = {
                        'name': item_name,
                        'line_number': info['first_line'],
                        'file_path': info['first_file']
                    }
                    matched = True
                    break
            
            if not matched:
                missing_patterns.append(pattern)
        
        actual_count = len(found_items)
        
        # Use template helper
        return self.build_complete_output(
            found_items=found_items,
            missing_items=missing_patterns,
            found_desc=f"{self.FOUND_DESC_TYPE2_3} ({actual_count}/{expected_value} patterns found)",
            missing_desc=f"{self.MISSING_DESC_TYPE2_3} ({len(missing_patterns)} patterns not matched)",
            found_reason=self.FOUND_REASON_TYPE2_3,
            missing_reason=self.MISSING_REASON_TYPE2_3
        )
    
    # =========================================================================
    # Type 3: Value Check with Waiver Logic
    # =========================================================================
    
    def _execute_type3(self) -> CheckResult:
        """
        Type 3: Value check with waiver support.
        
        Check required patterns (pattern_items) with waiver logic:
        - Pattern format: "warning_type|View: view_name" (substring match)
        - Pattern satisfied if found AND waived (or not found)
        - PASS if ALL required patterns have waived violations
        
        Returns:
            CheckResult with FAIL for unwaived, INFO for waived items
        """
        # Parse input
        data = self._parse_input_files()
        items = data.get('items', [])
        
        # Get requirements and waivers
        requirements = self.item_data.get('requirements', {})
        pattern_items = requirements.get('pattern_items', [])
        
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # Group warnings by view and warning_type
        violations_by_view_and_type = {}
        
        for item in items:
            view = item.get('view', 'unknown')
            warning_type = item.get('warning_type', 'unknown')
            key = (view, warning_type)
            
            if key not in violations_by_view_and_type:
                violations_by_view_and_type[key] = {
                    'count': 0,
                    'first_line': item.get('line_number', 0),
                    'first_file': item.get('file_path', 'N/A')
                }
            violations_by_view_and_type[key]['count'] += 1
        
        # Track pattern satisfaction and waiver usage
        found_clean = {}  # Patterns with no violations
        found_waived = {}  # Patterns with waived violations
        missing_patterns = {}  # Patterns with unwaived violations
        other_waived = {}  # Waived items not matching patterns
        used_waiver_patterns = set()
        
        # Check each required pattern
        for pattern in pattern_items:
            pattern_satisfied = False
            pattern_has_violation = False
            
            # Check if pattern matches any grouped violation
            for (view, warning_type), info in violations_by_view_and_type.items():
                search_str = f"{warning_type} | View: {view}"
                
                # SUBSTRING MATCH
                if pattern.lower() in search_str.lower():
                    pattern_has_violation = True
                    item_name = f"{warning_type} ({info['count']} occurrences) | View: {view}"
                    item_data = {
                        'name': item_name,
                        'line_number': info['first_line'],
                        'file_path': info['first_file']
                    }
                    
                    # Check if waived
                    matched_waiver = None
                    for waiver_pattern in waive_dict.keys():
                        if self.match_waiver_entry(item_name, {waiver_pattern: waive_dict[waiver_pattern]}):
                            matched_waiver = waiver_pattern
                            used_waiver_patterns.add(waiver_pattern)
                            break
                    
                    if matched_waiver:
                        found_waived[item_name] = item_data
                        pattern_satisfied = True
                    else:
                        missing_patterns[item_name] = item_data
                    break  # Only match first occurrence of pattern
            
            # If pattern not found in violations, it's clean (satisfied)
            if not pattern_has_violation:
                item_name = f"{pattern} (0 occurrences) - clean"
                found_clean[item_name] = {
                    'name': item_name,
                    'line_number': 0,
                    'file_path': 'N/A'
                }
        
        # Track other waived violations (not matching any pattern)
        for (view, warning_type), info in violations_by_view_and_type.items():
            search_str = f"{warning_type} | View: {view}"
            is_pattern_violation = any(p.lower() in search_str.lower() for p in pattern_items)
            
            if not is_pattern_violation:
                item_name = f"{warning_type} ({info['count']} occurrences) | View: {view}"
                for waiver_pattern in waive_dict.keys():
                    if self.match_waiver_entry(item_name, {waiver_pattern: waive_dict[waiver_pattern]}):
                        used_waiver_patterns.add(waiver_pattern)
                        other_waived[item_name] = {
                            'name': item_name,
                            'line_number': info['first_line'],
                            'file_path': info['first_file']
                        }
                        break
        
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
        
        # Build output
        all_waived = {**found_waived, **other_waived}
        
        # Use template helper
        return self.build_complete_output(
            found_items=found_clean,
            waived_items=all_waived,
            missing_items=missing_patterns,
            waive_dict=waive_dict,
            unused_waivers=unused_waivers,
            found_desc=self.FOUND_DESC_TYPE2_3,
            missing_desc=self.MISSING_DESC_TYPE2_3,
            waived_desc=self.WAIVED_DESC,
            found_reason=self.FOUND_REASON_TYPE2_3,
            missing_reason=self.MISSING_REASON_TYPE2_3,
            waived_base_reason=self.WAIVED_BASE_REASON,
            unused_waiver_reason=self.UNUSED_WAIVER_REASON
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
        
        # Parse waiver configuration
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # Group warnings by view and warning_type, then count occurrences
        # Output format: "{warning_type} ({count} occurrences) | View: {view}"
        violations_by_view_and_type = {}
        
        for item in items:
            view = item.get('view', 'unknown')
            warning_type = item.get('warning_type', 'unknown')
            key = (view, warning_type)
            
            if key not in violations_by_view_and_type:
                violations_by_view_and_type[key] = {
                    'count': 0,
                    'first_line': item.get('line_number', 0),
                    'first_file': item.get('file_path', 'N/A')
                }
            violations_by_view_and_type[key]['count'] += 1
        
        # Build grouped items and separate waived/unwaived
        waived_items = {}
        unwaived_items = {}
        used_waiver_patterns = set()
        
        for (view, warning_type), info in violations_by_view_and_type.items():
            item_name = f"{warning_type} ({info['count']} occurrences) | View: {view}"
            item_data = {
                'name': item_name,
                'line_number': info['first_line'],
                'file_path': info['first_file']
            }
            
            # Check if waived
            matched_waiver = None
            for waiver_pattern in waive_dict.keys():
                if self.match_waiver_entry(item_name, {waiver_pattern: waive_dict[waiver_pattern]}):
                    matched_waiver = waiver_pattern
                    used_waiver_patterns.add(waiver_pattern)
                    break
            
            if matched_waiver:
                waived_items[item_name] = item_data
            else:
                unwaived_items[item_name] = item_data
        
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
        
        # Use template helper for automatic output formatting (waivers.value>0)
        return self.build_complete_output(
            found_items={},
            waived_items=waived_items,
            missing_items=unwaived_items,
            waive_dict=waive_dict,
            unused_waivers=unused_waivers,
            found_desc=self.FOUND_DESC_TYPE1_4,
            missing_desc=self.MISSING_DESC_TYPE1_4,
            waived_desc=self.WAIVED_DESC,
            found_reason=self.FOUND_REASON_TYPE1_4,
            missing_reason=self.MISSING_REASON_TYPE1_4,
            waived_base_reason=self.WAIVED_BASE_REASON,
            unused_waiver_reason=self.UNUSED_WAIVER_REASON
        )


# =========================================================================
# Entry Point
# =========================================================================

def main():
    """Main entry point."""
    checker = Check_7_0_0_04()
    checker.init_checker(Path(__file__))
    result = checker.execute_check()
    checker.write_output(result)
    return 0 if result.is_pass else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())