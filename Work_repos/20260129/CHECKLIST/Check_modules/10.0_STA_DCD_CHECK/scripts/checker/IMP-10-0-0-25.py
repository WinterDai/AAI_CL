################################################################################
# Script Name: IMP-10-0-0-25.py
#
# Purpose:
#   Confirm check_timing report has no issue.
#
# Logic:
#   - Parse input files: check_timing_func.rpt, check_timing_scan.rpt
#   - Use state machine to track parsing sections (SUMMARY, DETAIL, IDEAL_CLOCKS)
#   - Extract warning counts from TIMING CHECK SUMMARY section
#   - Extract individual violations from TIMING CHECK DETAIL section (multi-line and single-line formats)
#   - Extract ideal clock violations from TIMING CHECK IDEAL CLOCKS section
#   - Aggregate warning counts and violations across all input files and timing views
#   - For each timing view, count total occurrences (total violations) per warning type
#   - PASS if total warning count = 0, FAIL if any warnings detected
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
class Check_10_0_0_25(InputFileParserMixin, OutputBuilderMixin, WaiverHandlerMixin, BaseChecker):
    """
    IMP-10-0-0-25: Confirm check_timing report has no issue.
    
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
    FOUND_DESC = "Check_timing verification passed - no constraint issues detected"
    MISSING_DESC = "Check_timing verification failed - constraint issues require resolution"
    WAIVED_DESC = "Waived check_timing violations"
    FOUND_REASON = "All timing views have no check_timing violations"
    MISSING_REASON = "Check_timing violations detected across timing views"
    WAIVED_BASE_REASON = "Check_timing violations waived per design team approval"
    
    def __init__(self):
        """Initialize the checker."""
        super().__init__(
            check_module="10.0_STA_DCD_CHECK",
            item_id="IMP-10-0-0-25",
            item_desc="Confirm check_timing report has no issue."
        )
        # Custom member variables for parsed data
        self._parsed_items: List[Dict[str, Any]] = []
        self._warning_summary: Dict[str, int] = {}
        self._violations_by_view: Dict[str, List[Dict[str, Any]]] = {}
    
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
        
        Parses PrimeTime/Tempus check_timing reports using state machine approach:
        - TIMING CHECK SUMMARY: Extract warning type counts
        - TIMING CHECK DETAIL: Extract individual violations (multi-line and single-line)
        - TIMING CHECK IDEAL CLOCKS: Extract ideal clock violations
        
        Returns:
            Dict with parsed data:
            - 'items': List[Dict] - All violations with metadata (line_number, file_path, view, warning_type)
            - 'clean_views': List[str] - Views with no violations
            - 'warning_summary': Dict[str, int] - Total counts per warning type
            - 'violations_by_view': Dict[str, List] - Violations grouped by view
            - 'metadata': Dict - File metadata
        """
        # 1. Validate input files - IMPORTANT: returns tuple (valid_files_list, missing_files_list)
        valid_files, missing_files = self.validate_input_files()
        if missing_files:
            raise ConfigurationError(
                self.create_missing_files_error(missing_files)
            )
        
        # 2. Initialize aggregation structures
        all_violations = []
        warning_summary = {}
        violations_by_view = {}
        all_views = set()
        
        # 3. Parse each file
        for file_path in valid_files:
            file_violations = self._parse_single_file(file_path)
            all_violations.extend(file_violations)
            
            # Aggregate by view
            for violation in file_violations:
                view = violation.get('view', 'unknown')
                all_views.add(view)
                if view not in violations_by_view:
                    violations_by_view[view] = []
                violations_by_view[view].append(violation)
                
                # Aggregate warning counts
                warning_type = violation.get('warning_type', 'unknown')
                warning_summary[warning_type] = warning_summary.get(warning_type, 0) + 1
        
        # 4. Identify clean views (views with no violations)
        clean_views = []
        for view in all_views:
            if view not in violations_by_view or len(violations_by_view[view]) == 0:
                clean_views.append(view)
        
        # 5. Store frequently reused data on self
        self._parsed_items = all_violations
        self._warning_summary = warning_summary
        self._violations_by_view = violations_by_view
        
        # 6. Return aggregated dict
        return {
            'items': all_violations,
            'clean_views': clean_views,
            'warning_summary': warning_summary,
            'violations_by_view': violations_by_view,
            'metadata': {
                'total_violations': len(all_violations),
                'total_views': len(all_views),
                'clean_views_count': len(clean_views)
            }
        }
    
    def _parse_single_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """
        Parse a single check_timing report file.
        
        Uses state machine to track parsing sections:
        - SUMMARY: Extract warning counts
        - DETAIL: Extract individual violations
        - IDEAL_CLOCKS: Extract ideal clock violations
        
        Args:
            file_path: Path to check_timing report file
            
        Returns:
            List of violation dictionaries with metadata
        """
        violations = []
        current_section = None
        line_buffer = []
        
        # Patterns
        pattern_section = re.compile(r'^\s*(TIMING CHECK SUMMARY|TIMING CHECK DETAIL|TIMING CHECK IDEAL CLOCKS)\s*$')
        pattern_delimiter = re.compile(r'^\s*-{3,}\s*$')
        pattern_summary = re.compile(r'^\s*(\S+)\s+(.+?)\s+(\d+)\s*$')
        pattern_single_line = re.compile(r'^\s*(\S+)\s+(No drive assertion|No input delay assertion.*?)\s+(func_\S+|scan_\S+)\s*$')
        pattern_ideal_clock = re.compile(r'^\s*([A-Z_0-9]+)\s+(func_\S+|scan_\S+)\s*$')
        
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line_num, line in enumerate(f, 1):
                # Check for section headers
                section_match = pattern_section.search(line)
                if section_match:
                    # Process buffered lines from previous section
                    if line_buffer and current_section == 'TIMING CHECK DETAIL':
                        violations.extend(self._process_detail_buffer(line_buffer, file_path))
                    line_buffer = []
                    current_section = section_match.group(1)
                    continue
                
                # Check for delimiter (section boundary)
                if pattern_delimiter.match(line):
                    if line_buffer and current_section == 'TIMING CHECK DETAIL':
                        violations.extend(self._process_detail_buffer(line_buffer, file_path))
                    line_buffer = []
                    continue
                
                # Parse based on current section
                if current_section == 'TIMING CHECK SUMMARY':
                    # Extract warning counts (not violations, just for info)
                    summary_match = pattern_summary.match(line)
                    if summary_match:
                        # Summary counts are aggregated separately, not as violations
                        pass
                
                elif current_section == 'TIMING CHECK DETAIL':
                    # Check for single-line format
                    single_match = pattern_single_line.match(line)
                    if single_match:
                        signal_name = single_match.group(1)
                        warning_desc = single_match.group(2)
                        view_name = single_match.group(3)
                        
                        violations.append({
                            'name': f"{signal_name} | {warning_desc} | View: {view_name}",
                            'signal': signal_name,
                            'warning_type': 'no_drive' if 'No drive' in warning_desc else 'no_input_delay',
                            'warning_description': warning_desc,
                            'view': view_name,
                            'line_number': line_num,
                            'file_path': str(file_path)
                        })
                    else:
                        # Multi-line format - buffer lines
                        stripped = line.strip()
                        if stripped:
                            line_buffer.append({
                                'line': line,
                                'line_number': line_num,
                                'stripped': stripped
                            })
                        else:
                            # Empty line - process buffer
                            if line_buffer:
                                violations.extend(self._process_detail_buffer(line_buffer, file_path))
                            line_buffer = []
                
                elif current_section == 'TIMING CHECK IDEAL CLOCKS':
                    # Extract ideal clock violations
                    ideal_match = pattern_ideal_clock.match(line)
                    if ideal_match:
                        clock_name = ideal_match.group(1)
                        view_name = ideal_match.group(2)
                        
                        violations.append({
                            'name': f"{clock_name} | Ideal clock waveform | View: {view_name}",
                            'signal': clock_name,
                            'warning_type': 'ideal_clock_waveform',
                            'warning_description': 'Clock waveform is ideal',
                            'view': view_name,
                            'line_number': line_num,
                            'file_path': str(file_path)
                        })
        
        # Process any remaining buffered lines
        if line_buffer and current_section == 'TIMING CHECK DETAIL':
            violations.extend(self._process_detail_buffer(line_buffer, file_path))
        
        return violations
    
    def _process_detail_buffer(self, line_buffer: List[Dict], file_path: Path) -> List[Dict[str, Any]]:
        """
        Process buffered lines from DETAIL section to extract multi-line violations.
        
        Multi-line format:
        Line 1: Pin/signal name (minimal indent)
        Line 2: Warning description (heavy indent ~37 spaces)
        Line 3: View name (heavy indent ~54 spaces)
        
        Args:
            line_buffer: List of buffered line dictionaries
            file_path: Source file path
            
        Returns:
            List of violation dictionaries
        """
        violations = []
        
        if len(line_buffer) >= 3:
            # Extract components
            pin_line = line_buffer[0]
            warning_line = line_buffer[1]
            view_line = line_buffer[2]
            
            # Check indentation to confirm multi-line format
            pin_indent = len(pin_line['line']) - len(pin_line['line'].lstrip())
            warning_indent = len(warning_line['line']) - len(warning_line['line'].lstrip())
            view_indent = len(view_line['line']) - len(view_line['line'].lstrip())
            
            # Multi-line format: pin has minimal indent, warning/view heavily indented
            if pin_indent < 10 and warning_indent > 30 and view_indent > 50:
                pin_name = pin_line['stripped']
                warning_desc = warning_line['stripped']
                view_name = view_line['stripped']
                
                # Determine warning type
                warning_type = 'unknown'
                if 'Clock not found' in warning_desc or 'clock is expected' in warning_desc:
                    warning_type = 'clock_expected'
                elif 'Unconstrained' in warning_desc:
                    warning_type = 'uncons_endpoint'
                
                violations.append({
                    'name': f"{pin_name} | {warning_desc} | View: {view_name}",
                    'signal': pin_name,
                    'warning_type': warning_type,
                    'warning_description': warning_desc,
                    'view': view_name,
                    'line_number': pin_line['line_number'],
                    'file_path': str(file_path)
                })
        
        return violations
    
    # =========================================================================
    # Type 1: Boolean Check
    # =========================================================================
    
    def _execute_type1(self) -> CheckResult:
        """
        Type 1: Boolean Check.
        
        Check if any check_timing violations exist.
        PASS if no violations, FAIL if any violations detected.
        
        Returns:
            CheckResult with is_pass based on violation count
        """
        # Parse input
        data = self._parse_input_files()
        violations = data.get('items', [])
        clean_views = data.get('clean_views', [])
        warning_summary = data.get('warning_summary', {})
        
        # Build found_items from clean views
        found_items = {}
        for view in clean_views:
            found_items[f"View: {view}"] = {
                'name': f"View: {view}",
                'line_number': 0,
                'file_path': 'N/A'
            }
        
        # Build missing_items from violations (group by view and warning type)
        # Format: "{warning_type} ({count} occurrences) | View: {view}" (per README)
        missing_items = {}
        violations_by_view = data.get('violations_by_view', {})
        
        for view, view_violations in violations_by_view.items():
            # Count occurrences per warning type in this view
            warning_counts = {}
            warning_first_violation = {}
            for violation in view_violations:
                warning_type = violation.get('warning_type', 'unknown')
                warning_counts[warning_type] = warning_counts.get(warning_type, 0) + 1
                if warning_type not in warning_first_violation:
                    warning_first_violation[warning_type] = violation
            
            # Create one entry per warning type per view
            for warning_type, count in warning_counts.items():
                # Include occurrence count in item name (per README format)
                item_name = f"{warning_type} ({count} occurrences) | View: {view}"
                first_violation = warning_first_violation[warning_type]
                missing_items[item_name] = {
                    'name': item_name,
                    'line_number': first_violation.get('line_number', 0),
                    'file_path': first_violation.get('file_path', 'N/A')
                }
        
        # Use template helper
        return self.build_complete_output(
            found_items=found_items,
            missing_items=missing_items,
            value=len(violations),
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
        PASS if all required patterns are found.
        
        Returns:
            CheckResult with is_pass based on pattern matching
        """
        # Parse input
        data = self._parse_input_files()
        violations = data.get('items', [])
        
        # Get requirements
        requirements = self.item_data.get('requirements', {})
        pattern_items = requirements.get('pattern_items', [])
        expected_value = requirements.get('value', 'N/A')
        
        # Match patterns against violations
        found_items = {}
        missing_patterns = []
        
        for pattern in pattern_items:
            matched = False
            for violation in violations:
                # Build searchable string from violation
                vio_str = f"{violation.get('warning_type', '')} | View: {violation.get('view', '')}"
                
                # SUBSTRING MATCH (pattern_items are descriptive strings)
                if pattern.lower() in vio_str.lower():
                    found_items[pattern] = {
                        'name': violation.get('name', pattern),
                        'line_number': violation.get('line_number', 0),
                        'file_path': violation.get('file_path', 'N/A')
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
            found_desc=f"{self.FOUND_DESC} ({actual_count}/{expected_value} patterns found)",
            missing_desc=f"{self.MISSING_DESC} ({len(missing_patterns)} patterns not matched)",
            found_reason=self.FOUND_REASON,
            missing_reason=self.MISSING_REASON
        )
    
    # =========================================================================
    # Type 3: Value Check with Waiver Logic
    # =========================================================================
    
    def _execute_type3(self) -> CheckResult:
        """
        Type 3: Value check with waiver support.
        
        Check required patterns (pattern_items) with waiver logic:
        - Pattern satisfied if clean OR waived
        - PASS if ALL required patterns are satisfied
        
        Returns:
            CheckResult with FAIL for unwaived, INFO for waived items
        """
        # Parse input
        data = self._parse_input_files()
        violations = data.get('items', [])
        clean_views = data.get('clean_views', [])
        
        # Get requirements and waivers
        requirements = self.item_data.get('requirements', {})
        pattern_items = requirements.get('pattern_items', [])
        
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # Track pattern satisfaction
        found_clean = {}
        found_waived = {}
        missing_patterns = {}
        other_waived = {}
        used_waiver_patterns = set()
        
        # Check each required pattern
        for pattern in pattern_items:
            pattern_satisfied = False
            
            # Check if pattern represents a clean view
            for view in clean_views:
                if pattern.lower() in view.lower():
                    item_name = f"View: {view} (clean)"
                    found_clean[item_name] = {
                        'name': item_name,
                        'line_number': 0,
                        'file_path': 'N/A'
                    }
                    pattern_satisfied = True
                    break
            
            # If not clean, check if pattern has waived violation
            if not pattern_satisfied:
                for violation in violations:
                    vio_str = f"{violation.get('warning_type', '')} | View: {violation.get('view', '')}"
                    
                    # SUBSTRING MATCH
                    if pattern.lower() in vio_str.lower():
                        vio_name = violation.get('name', vio_str)
                        vio_data = {
                            'name': vio_name,
                            'line_number': violation.get('line_number', 0),
                            'file_path': violation.get('file_path', 'N/A')
                        }
                        
                        # Check if waived
                        matched_waiver = None
                        for waiver_pattern in waive_dict.keys():
                            if self.match_waiver_entry(vio_name, {waiver_pattern: waive_dict[waiver_pattern]}):
                                matched_waiver = waiver_pattern
                                used_waiver_patterns.add(waiver_pattern)
                                break
                        
                        if matched_waiver:
                            found_waived[vio_name] = vio_data
                            pattern_satisfied = True
                        else:
                            missing_patterns[vio_name] = vio_data
                        break
        
        # Track other waived violations (not in pattern_items, for info only)
        for violation in violations:
            vio_str = f"{violation.get('warning_type', '')} | View: {violation.get('view', '')}"
            is_pattern_violation = any(pattern.lower() in vio_str.lower() for pattern in pattern_items)
            
            if not is_pattern_violation:
                vio_name = violation.get('name', vio_str)
                for waiver_pattern in waive_dict.keys():
                    if self.match_waiver_entry(vio_name, {waiver_pattern: waive_dict[waiver_pattern]}):
                        used_waiver_patterns.add(waiver_pattern)
                        other_waived[vio_name] = {
                            'name': vio_name,
                            'line_number': violation.get('line_number', 0),
                            'file_path': violation.get('file_path', 'N/A')
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
        
        return self.build_complete_output(
            found_items=found_clean,
            missing_items=missing_patterns,
            waived_items=all_waived,
            unused_waivers=unused_waivers,
            waive_dict=waive_dict,
            waived_tag="[WAIVER]",
            found_desc=f"{self.FOUND_DESC} ({len(found_clean)}/{len(pattern_items)} patterns satisfied)",
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
        
        Global check of all violations with waiver logic:
        - Clean views → found_items
        - Waived violations → waived_items
        - Unwaived violations → missing_items (FAIL)
        
        Returns:
            CheckResult with waiver logic applied
        """
        # Parse input
        data = self._parse_input_files()
        violations = data.get('items', [])
        clean_views = data.get('clean_views', [])
        violations_by_view = data.get('violations_by_view', {})
        
        # Parse waivers
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # Build found_items from clean views
        found_items = {}
        for view in clean_views:
            item_name = f"View: {view}"
            found_items[item_name] = {
                'name': item_name,
                'line_number': 0,
                'file_path': 'N/A'
            }
        
        # Apply waivers to violations (group by view and warning type)
        # Format: "{warning_type} ({count} occurrences) | View: {view}" (per README)
        waived_items = {}
        unwaived_items = {}
        used_waiver_patterns = set()
        
        for view, view_violations in violations_by_view.items():
            # Count occurrences per warning type in this view
            warning_counts = {}
            warning_first_violation = {}
            for violation in view_violations:
                warning_type = violation.get('warning_type', 'unknown')
                warning_counts[warning_type] = warning_counts.get(warning_type, 0) + 1
                if warning_type not in warning_first_violation:
                    warning_first_violation[warning_type] = violation
            
            # Create one entry per warning type per view
            for warning_type, count in warning_counts.items():
                # Include occurrence count in item name (per README format)
                item_name = f"{warning_type} ({count} occurrences) | View: {view}"
                first_violation = warning_first_violation[warning_type]
                vio_data = {
                    'name': item_name,
                    'line_number': first_violation.get('line_number', 0),
                    'file_path': first_violation.get('file_path', 'N/A')
                }
                
                # Check if this violation matches any waiver
                matched_waiver = None
                for waiver_pattern in waive_dict.keys():
                    if self.match_waiver_entry(item_name, {waiver_pattern: waive_dict[waiver_pattern]}):
                        matched_waiver = waiver_pattern
                        used_waiver_patterns.add(waiver_pattern)
                        break
                
                if matched_waiver:
                    waived_items[item_name] = vio_data
                else:
                    unwaived_items[item_name] = vio_data
        
        # Find unused waivers
        unused_waivers = {
            waiver_name: {
                'line_number': 0,
                'file_path': 'N/A',
                'reason': waive_dict[waiver_name]
            }
            for waiver_name in waive_dict.keys()
            if waiver_name not in used_waiver_patterns
        }
        
        # Build output
        return self.build_complete_output(
            found_items=found_items,
            missing_items=unwaived_items,
            waived_items=waived_items,
            unused_waivers=unused_waivers,
            waive_dict=waive_dict,
            value=len(violations),
            waived_tag="[WAIVER]",
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
    """Main entry point for standalone execution."""
    checker = Check_10_0_0_25()
    checker.init_checker(Path(__file__))
    result = checker.execute_check()
    checker.write_output(result)
    return 0 if result.is_pass else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())