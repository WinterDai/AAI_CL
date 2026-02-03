################################################################################
# Script Name: IMP-10-0-0-17.py
#
# Purpose:
#   Confirm the min-pulse check result is clean.
#
# Logic:
#   - Parse input files: *min_pulse_width_hold.rpt
#   - Validate input files exist using validate_input_files()
#   - Use state machine to parse violation reports line-by-line
#   - Extract violation details: path number, status (VIOLATED/MET), slack, pin name
#   - Collect context for each violation: view name, clock name, final slack
#   - Aggregate violations across all files and timing views
#   - Apply waiver logic if configured (match violations against waiver patterns)
#   - Report PASS if violation_count == 0, FAIL if violations exist
#   - Handle edge cases: empty files, missing view fields, multiple files per view
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
# Date: 2025-12-17
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
class Check_10_0_0_17(InputFileParserMixin, OutputBuilderMixin, WaiverHandlerMixin, BaseChecker):
    """
    IMP-10-0-0-17: Confirm the min-pulse check result is clean.
    
    Checking Types:
    - Type 1: requirements=N/A, waivers=N/A/0 → Informational/Boolean check
    - Type 2: requirements>0, waivers=N/A/0 → Value check without waivers
    - Type 3: requirements>0, waivers>0 → Value check with waiver logic
    - Type 4: requirements=N/A, waivers=>0 → Boolean check with waiver logic
    
    Template Library v1.1.0:
    - Uses InputFileParserMixin for parsing (parse_log_with_patterns, normalize_command)
    - Uses WaiverHandlerMixin for waiver processing (parse_waive_items(waive_items_raw), match_waiver_entry(item, waive_dict))
    - Uses OutputBuilderMixin for result construction (build_complete_output(...))
    """
    
    # =========================================================================
    # UNIFIED DESCRIPTIONS - MUST be identical across ALL Type 1/2/3/4
    # =========================================================================
    FOUND_DESC = "Min pulse width verification clean"
    MISSING_DESC = "Min pulse width verification failed - clock pulses too narrow"
    WAIVED_DESC = "Waived min pulse width violations"
    UNUSED_DESC = "Unused min pulse width waiver entries"
    FOUND_REASON = "All min pulse width checks passed across all timing views"
    MISSING_REASON = "Min pulse width violations detected"
    WAIVED_BASE_REASON = "Min pulse width violation waived per design team approval"
    UNUSED_WAIVER_REASON = "Waiver not matched - no corresponding pulse width violation found"
    
    def __init__(self):
        """Initialize the checker."""
        super().__init__(
            check_module="10.0_STA_DCD_CHECK",
            item_id="IMP-10-0-0-17",
            item_desc="Confirm the min-pulse check result is clean."
        )
        # Custom member variables for parsed data
        self._parsed_violations: List[Dict[str, Any]] = []
        self._total_paths_checked: int = 0
        self._violation_count: int = 0
    
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
        Parse input files to extract min pulse width violations.
        
        Uses state machine to parse violation reports:
        - SEARCHING: Looking for "Path N:" headers
        - IN_VIOLATION: Collecting violation details (view, clock, slack)
        - COMPLETE_VIOLATION: Violation fully parsed, ready for next
        
        Returns:
            Dict with parsed data:
            - 'items': List[Dict] - Violations with metadata (line_number, file_path)
            - 'metadata': Dict - Summary statistics
            - 'errors': List - Parsing errors
        """
        # 1. Validate input files - IMPORTANT: returns tuple (valid_files_list, missing_files_list)
        valid_files, missing_files = self.validate_input_files()
        
        # Fix KNOWN_ISSUE_LOGIC-001: Explicitly check for empty list
        if missing_files:
            raise ConfigurationError(
                self.create_missing_files_error(missing_files)
            )
        
        if not valid_files or len(valid_files) == 0:
            raise ConfigurationError("No valid input files found")
        
        # 2. Parse using state machine
        all_violations = []
        total_paths = 0
        errors = []
        
        # Patterns from file analysis
        path_pattern = re.compile(
            r'Path\s+(\d+):\s+(VIOLATED|MET)\s+\(([+-]?\d+\.\d+)\s+ns\)\s+PulseWidth\s+Check\s+with\s+Pin\s+([\w/]+)'
        )
        view_pattern = re.compile(r'View:\s+([\w_]+)')
        clock_pattern = re.compile(r'Clock:\s+\([RF]\)\s+([\w_]+)')
        slack_pattern = re.compile(r'Slack:=\s+([+-]?\d+\.\d+)')
        
        for file_path in valid_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    # State machine variables
                    state = 'SEARCHING'
                    current_violation = None
                    current_line_num = 0
                    
                    for line_num, line in enumerate(f, 1):
                        current_line_num = line_num
                        
                        # State: SEARCHING - looking for Path headers
                        if state == 'SEARCHING':
                            match = path_pattern.search(line)
                            if match:
                                path_num = match.group(1)
                                status = match.group(2)
                                slack = match.group(3)
                                pin_name = match.group(4)
                                
                                total_paths += 1
                                
                                # Only track VIOLATED paths
                                if status == 'VIOLATED':
                                    current_violation = {
                                        'path_number': path_num,
                                        'status': status,
                                        'slack': slack,
                                        'pin_name': pin_name,
                                        'line_number': line_num,
                                        'file_path': str(file_path),
                                        'view': 'unknown_view',
                                        'clock': 'unknown_clock'
                                    }
                                    state = 'IN_VIOLATION'
                        
                        # State: IN_VIOLATION - collecting details
                        elif state == 'IN_VIOLATION':
                            # Extract view
                            view_match = view_pattern.search(line)
                            if view_match:
                                current_violation['view'] = view_match.group(1)
                            
                            # Extract clock
                            clock_match = clock_pattern.search(line)
                            if clock_match:
                                current_violation['clock'] = clock_match.group(1)
                            
                            # Extract final slack (confirmation)
                            slack_match = slack_pattern.search(line)
                            if slack_match:
                                current_violation['slack_confirmed'] = slack_match.group(1)
                                # Violation complete
                                all_violations.append(current_violation)
                                current_violation = None
                                state = 'SEARCHING'
                            
                            # Check for next path (incomplete violation)
                            if path_pattern.search(line):
                                if current_violation:
                                    # Save incomplete violation
                                    all_violations.append(current_violation)
                                # Process new path
                                match = path_pattern.search(line)
                                path_num = match.group(1)
                                status = match.group(2)
                                slack = match.group(3)
                                pin_name = match.group(4)
                                
                                total_paths += 1
                                
                                if status == 'VIOLATED':
                                    current_violation = {
                                        'path_number': path_num,
                                        'status': status,
                                        'slack': slack,
                                        'pin_name': pin_name,
                                        'line_number': line_num,
                                        'file_path': str(file_path),
                                        'view': 'unknown_view',
                                        'clock': 'unknown_clock'
                                    }
                                    state = 'IN_VIOLATION'
                                else:
                                    state = 'SEARCHING'
                    
                    # Handle incomplete violation at end of file
                    if current_violation:
                        all_violations.append(current_violation)
                        
            except Exception as e:
                errors.append(f"Error parsing {file_path}: {str(e)}")
        
        # 3. Store frequently reused data on self
        self._parsed_violations = all_violations
        self._total_paths_checked = total_paths
        self._violation_count = len(all_violations)
        
        # 4. Return aggregated dict with items containing line_number and file_path
        return {
            'items': all_violations,
            'metadata': {
                'total_paths': total_paths,
                'violation_count': len(all_violations),
                'files_processed': len(valid_files)
            },
            'errors': errors
        }
    
    # =========================================================================
    # Type 1: Informational/Boolean Check
    # =========================================================================
    
    def _execute_type1(self) -> CheckResult:
        """
        Type 1: Informational or Boolean check (no waivers).
        
        Use OutputBuilderMixin.build_complete_output() for automatic formatting.
        
        Returns:
            CheckResult with is_pass based on check logic
        """
        # Parse input
        data = self._parse_input_files()
        violations = data.get('items', [])
        metadata = data.get('metadata', {})
        
        # Check logic: PASS if no violations, FAIL if violations exist
        if not violations or len(violations) == 0:
            # PASS case - no violations found
            found_items = {
                f"Checked {metadata.get('total_paths', 0)} pulse width paths": {
                    'name': f"Checked {metadata.get('total_paths', 0)} pulse width paths",
                    'line_number': 0,
                    'file_path': 'Summary'
                }
            }
            missing_items = []
        else:
            # FAIL case - violations detected
            found_items = {}
            missing_items = []
            
            for v in violations:
                violation_name = f"[{v['pin_name']}] Pulse width violation: {v['slack']}ns (clock: {v['clock']}, view: {v['view']})"
                missing_items.append(violation_name)
        
        # Use template helper
        return self.build_complete_output(
            found_items=found_items,
            missing_items=missing_items,
            found_desc=self.FOUND_DESC,
            missing_desc=self.MISSING_DESC,
            found_reason=self.FOUND_REASON,
            missing_reason=self.MISSING_REASON
        )
    
    # =========================================================================
    # Type 2: Value comparison
    # =========================================================================
    
    def _execute_type2(self) -> CheckResult:
        """
        Type 2: Value comparison check (no waivers).
        
        Template auto-handles waiver=0 conversions.
        
        Returns:
            CheckResult with is_pass based on value comparison
        """
        # Parse input
        data = self._parse_input_files()
        violations = data.get('items', [])
        metadata = data.get('metadata', {})
        
        # Get requirements
        pattern_items = self.item_data.get('requirements', {}).get('pattern_items', [])
        
        # Check logic: Compare actual violations vs expected (should be 0)
        if not violations or len(violations) == 0:
            # PASS case
            found_items = {
                f"Checked {metadata.get('total_paths', 0)} pulse width paths": {
                    'name': f"Checked {metadata.get('total_paths', 0)} pulse width paths",
                    'line_number': 0,
                    'file_path': 'Summary'
                }
            }
            extra_items = {}
        else:
            # FAIL case - violations are "extra" (unexpected)
            found_items = {}
            extra_items = {}
            
            for v in violations:
                violation_name = f"[{v['pin_name']}] Pulse width violation: {v['slack']}ns (clock: {v['clock']}, view: {v['view']})"
                extra_items[violation_name] = {
                    'name': violation_name,
                    'line_number': v.get('line_number', 0),
                    'file_path': v.get('file_path', 'N/A')
                }
        
        # Use template helper (auto-handles waiver=0)
        return self.build_complete_output(
            found_items=found_items,
            extra_items=extra_items,
            found_desc=self.FOUND_DESC,
            missing_desc=self.MISSING_DESC,
            found_reason=self.FOUND_REASON,
            missing_reason=self.MISSING_REASON
        )
    
    # =========================================================================
    # Type 3: Value Check with Waiver Logic
    # =========================================================================
    
    def _execute_type3(self) -> CheckResult:
        """
        Type 3: Value comparison with waiver support.
        
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
        violations = parsed_data.get('items', [])
        metadata = parsed_data.get('metadata', {})
        
        # Fix KNOWN_ISSUE_API-016: Use waivers.get() directly to preserve dict format
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # Separate waived/unwaived using template helper
        waived_items = []
        unwaived_items = {}
        
        for v in violations:
            # Create violation identifier for waiver matching
            violation_name = f"[{v['pin_name']}] Pulse width violation: {v['slack']}ns (clock: {v['clock']}, view: {v['view']})"
            
            # Try to match against waivers
            if self.match_waiver_entry(violation_name, waive_dict):
                waived_items.append(violation_name)
            else:
                unwaived_items[violation_name] = {
                    'name': violation_name,
                    'line_number': v.get('line_number', 0),
                    'file_path': v.get('file_path', 'N/A')
                }
        
        # Find unused waivers
        used_names = set(waived_items)
        unused_waivers = []
        for waiver_key, waiver_info in waive_dict.items():
            if waiver_info['name'] not in used_names:
                unused_waivers.append(waiver_info['name'])
        
        # Build found_items for clean paths (if no violations)
        found_items = {}
        if not violations or len(violations) == 0:
            found_items = {
                f"Checked {metadata.get('total_paths', 0)} pulse width paths": {
                    'name': f"Checked {metadata.get('total_paths', 0)} pulse width paths",
                    'line_number': 0,
                    'file_path': 'Summary'
                }
            }
        
        # Use template helper for automatic output formatting
        return self.build_complete_output(
            found_items=found_items,
            waived_items=waived_items,
            unwaived_items=unwaived_items,
            waive_dict=waive_dict,
            unused_waivers=unused_waivers,
            found_desc=self.FOUND_DESC,
            missing_desc=self.MISSING_DESC,
            waived_desc=self.WAIVED_DESC,
            unused_desc=self.UNUSED_DESC,
            found_reason=self.FOUND_REASON,
            missing_reason=self.MISSING_REASON,
            waived_base_reason=self.WAIVED_BASE_REASON,
            unused_waiver_reason=self.UNUSED_WAIVER_REASON
        )
    
    # =========================================================================
    # Type 4: Boolean Check with Waiver Logic
    # =========================================================================
    
    def _execute_type4(self) -> CheckResult:
        """
        Type 4: Boolean check with waiver support.
        
        Use OutputBuilderMixin.build_complete_output() with has_waiver_value=True.
        
        Returns:
            CheckResult with waiver logic applied
        """
        # Parse input
        data = self._parse_input_files()
        violations = data.get('items', [])
        metadata = data.get('metadata', {})
        
        # Fix KNOWN_ISSUE_API-016: Use waivers.get() directly to preserve dict format
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # Separate waived/unwaived
        waived_items = []
        unwaived_items = {}
        
        for v in violations:
            violation_name = f"[{v['pin_name']}] Pulse width violation: {v['slack']}ns (clock: {v['clock']}, view: {v['view']})"
            
            if self.match_waiver_entry(violation_name, waive_dict):
                waived_items.append(violation_name)
            else:
                unwaived_items[violation_name] = {
                    'name': violation_name,
                    'line_number': v.get('line_number', 0),
                    'file_path': v.get('file_path', 'N/A')
                }
        
        # Find unused waivers
        used_names = set(waived_items)
        unused_waivers = []
        for waiver_key, waiver_info in waive_dict.items():
            if waiver_info['name'] not in used_names:
                unused_waivers.append(waiver_info['name'])
        
        # Build found_items for clean paths
        found_items = {}
        if not violations or len(violations) == 0:
            found_items = {
                f"Checked {metadata.get('total_paths', 0)} pulse width paths": {
                    'name': f"Checked {metadata.get('total_paths', 0)} pulse width paths",
                    'line_number': 0,
                    'file_path': 'Summary'
                }
            }
        
        # Use template helper (auto-handles waiver=0)
        return self.build_complete_output(
            found_items=found_items,
            waived_items=waived_items,
            unwaived_items=unwaived_items,
            waive_dict=waive_dict,
            unused_waivers=unused_waivers,
            has_waiver_value=True,
            found_desc=self.FOUND_DESC,
            missing_desc=self.MISSING_DESC,
            waived_desc=self.WAIVED_DESC,
            unused_desc=self.UNUSED_DESC,
            found_reason=self.FOUND_REASON,
            missing_reason=self.MISSING_REASON,
            waived_base_reason=self.WAIVED_BASE_REASON,
            unused_waiver_reason=self.UNUSED_WAIVER_REASON
        )
    
    # =========================================================================
    # Helper Methods (Optional - Add as needed)
    # =========================================================================
    
    def _matches_waiver(self, item: str, waive_patterns: List[str]) -> bool:
        """
        Check if item matches any waiver pattern.
        
        Args:
            item: Item to check
            waive_patterns: List of waiver patterns
            
        Returns:
            True if item matches any pattern
        """
        for pattern in waive_patterns:
            # Support wildcards
            if '*' in pattern:
                regex_pattern = pattern.replace('*', '.*')
                if re.search(regex_pattern, item, re.IGNORECASE):
                    return True
            # Exact match
            elif pattern.lower() == item.lower():
                return True
        return False


# =========================================================================
# Entry Point
# =========================================================================

def main():
    """Main entry point."""
    checker = Check_10_0_0_17()
    checker.init_checker(Path(__file__))
    result = checker.execute_check()
    checker.write_output(result)
    return 0 if result.is_pass else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())