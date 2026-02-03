################################################################################
# Script Name: IMP-10-0-0-12.py
#
# Purpose:
#   Confirm the max_transition check result is clean.
#
# Logic:
#   - Parse input files: maxtran_1.rpt, maxtran_2.rpt
#   - Validate report headers contain "Check type : max_transition"
#   - Extract violation entries using state machine parser (single-line and multi-line formats)
#   - Parse pin name, required limit, actual transition, slack, and timing view
#   - Filter violations where slack < 0 (negative slack indicates violation)
#   - Aggregate violations across all input files
#   - Apply waiver logic to match violations against waive_items patterns
#   - Report clean (pass) if all violations are waived or no violations exist
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
# Refactored: 2025-12-17 (Using checker_templates v1.1.0)
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
class Check_10_0_0_12(InputFileParserMixin, OutputBuilderMixin, WaiverHandlerMixin, BaseChecker):
    """
    IMP-10-0-0-12: Confirm the max_transition check result is clean.
    
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
    FOUND_DESC = "Clean max_transition checks (no violations)"
    MISSING_DESC = "Max_transition violations detected"
    WAIVED_DESC = "Waived max_transition violations"
    EXTRA_DESC = "Unexpected max_transition violations"
    FOUND_REASON = "Pin meets max_transition requirements"
    MISSING_REASON = "Max_transition violation detected"
    WAIVED_BASE_REASON = "Max_transition violation waived per design approval"
    EXTRA_REASON = "Unexpected max_transition violation"
    UNUSED_WAIVER_REASON = "Waiver defined but no violation matched"
    
    def __init__(self):
        """Initialize the checker."""
        super().__init__(
            check_module="10.0_STA_DCD_CHECK",
            item_id="IMP-10-0-0-12",
            item_desc="Confirm the max_transition check result is clean."
        )
        # Custom member variables for parsed data
        self._parsed_items: List[Dict[str, Any]] = []
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
    
    # =========================================================================
    # Input Parsing (Common for All Types)
    # =========================================================================
    
    def _parse_input_files(self) -> Dict[str, Any]:
        """
        Parse input files to extract max_transition violations.
        
        Parsing Logic:
        1. Validate input files exist and contain max_transition check header
        2. Use state machine to parse violation entries (single-line and multi-line)
        3. Extract: pin_name, required_limit, actual_value, slack, timing_view
        4. Filter violations where slack < 0
        5. Store line_number and file_path for each violation
        
        Returns:
            Dict with parsed data:
            - 'items': List[Dict] - Violations with metadata (line_number, file_path)
            - 'metadata': Dict - File metadata (total violations, files processed)
            - 'errors': List - Any parsing errors encountered
        """
        # 1. Validate input files - IMPORTANT: returns tuple (valid_files_list, missing_files_list)
        valid_files, missing_files = self.validate_input_files()
        if missing_files:
            raise ConfigurationError(
                self.create_missing_files_error(missing_files)
            )
        
        # FIXED: Explicitly check for empty list
        if not valid_files or len(valid_files) == 0:
            raise ConfigurationError("No valid input files found")
        
        # 2. Parse using state machine for max_transition reports
        all_violations = []
        errors = []
        
        # Patterns for parsing
        pattern_header = re.compile(r'^Check type\s*:\s*max_transition', re.IGNORECASE)
        pattern_table_header = re.compile(r'^\s*Pin Name\s+Required\s+Actual\s+Slack\s+View\s*$')
        pattern_single_line = re.compile(r'^\s*(\S+)\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(-?\d+\.\d+)\s+(\S+)\s*$')
        pattern_pin_name = re.compile(r'^\s*([a-zA-Z0-9_/]+)\s*$')
        pattern_continuation = re.compile(r'^\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(-?\d+\.\d+)\s+(\S+)\s*$')
        
        for file_path in valid_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                
                # State machine states
                state = 'INIT'
                pending_pin_name = None
                pending_line_num = 0
                header_found = False
                
                for line_num, line in enumerate(lines, 1):
                    # State: INIT - looking for check type header
                    if state == 'INIT':
                        if pattern_header.search(line):
                            state = 'HEADER'
                            header_found = True
                    
                    # State: HEADER - looking for table header
                    elif state == 'HEADER':
                        if pattern_table_header.search(line):
                            state = 'DATA'
                    
                    # State: DATA - parsing violation entries
                    elif state == 'DATA':
                        # Try single-line format first
                        match_single = pattern_single_line.match(line)
                        if match_single:
                            pin_name = match_single.group(1)
                            required = float(match_single.group(2))
                            actual = float(match_single.group(3))
                            slack = float(match_single.group(4))
                            view = match_single.group(5)
                            
                            # Only record violations (slack < 0)
                            if slack < 0:
                                all_violations.append({
                                    'name': pin_name,
                                    'pin_name': pin_name,
                                    'required': required,
                                    'actual': actual,
                                    'slack': slack,
                                    'view': view,
                                    'line_number': line_num,
                                    'file_path': str(file_path)
                                })
                            
                            pending_pin_name = None
                            continue
                        
                        # Try multi-line format - pin name line
                        match_pin = pattern_pin_name.match(line)
                        if match_pin and pending_pin_name is None:
                            pending_pin_name = match_pin.group(1)
                            pending_line_num = line_num
                            continue
                        
                        # Try multi-line format - continuation line
                        match_cont = pattern_continuation.match(line)
                        if match_cont and pending_pin_name is not None:
                            required = float(match_cont.group(1))
                            actual = float(match_cont.group(2))
                            slack = float(match_cont.group(3))
                            view = match_cont.group(4)
                            
                            # Only record violations (slack < 0)
                            if slack < 0:
                                all_violations.append({
                                    'name': pending_pin_name,
                                    'pin_name': pending_pin_name,
                                    'required': required,
                                    'actual': actual,
                                    'slack': slack,
                                    'view': view,
                                    'line_number': pending_line_num,
                                    'file_path': str(file_path)
                                })
                            
                            pending_pin_name = None
                            continue
                
                # Validate header was found
                if not header_found:
                    errors.append(f"File {file_path} does not contain 'Check type : max_transition' header")
            
            except Exception as e:
                errors.append(f"Error parsing {file_path}: {str(e)}")
        
        # 3. Store frequently reused data on self
        self._parsed_items = all_violations
        self._metadata = {
            'total_violations': len(all_violations),
            'files_processed': len(valid_files)
        }
        
        # 4. Return aggregated dict with items containing line_number and file_path
        return {
            'items': all_violations,
            'metadata': self._metadata,
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
        errors = data.get('errors', [])
        
        # Check for parsing errors
        if errors:
            error_items = {
                f"Parse error {i+1}": {
                    'name': err,
                    'line_number': 0,
                    'file_path': 'N/A'
                }
                for i, err in enumerate(errors)
            }
            return self.build_complete_output(
                missing_items=error_items,
                missing_desc="Parsing errors encountered",
                missing_reason="Failed to parse input file"
            )
        
        # Type 1: Check if violations exist
        if violations:
            # Convert violations to dict with metadata for source file/line display
            violation_items = {
                f"{v['pin_name']} (view: {v['view']}, slack: {v['slack']:.4f}ns)": {
                    'name': f"{v['pin_name']} (view: {v['view']}, slack: {v['slack']:.4f}ns)",
                    'line_number': v.get('line_number', 0),
                    'file_path': v.get('file_path', 'N/A')
                }
                for v in violations
            }
            
            # Use template helper - violations are missing_items (semantic failures)
            return self.build_complete_output(
                missing_items=violation_items,
                found_desc=self.FOUND_DESC,
                missing_desc=self.MISSING_DESC,
                found_reason=self.FOUND_REASON,
                missing_reason=self.MISSING_REASON
            )
        else:
            # No violations - clean result
            clean_item = {
                'All pins clean': {
                    'name': 'All pins clean',
                    'line_number': 0,
                    'file_path': 'N/A'
                }
            }
            
            return self.build_complete_output(
                found_items=clean_item,
                found_desc=self.FOUND_DESC,
                missing_desc=self.MISSING_DESC,
                found_reason=lambda item: self.FOUND_REASON,
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
        
        # Get requirements
        requirements = self.item_data.get('requirements', {})
        pattern_items = requirements.get('pattern_items', [])
        expected_value = requirements.get('value', 'N/A')
        
        # Match each pattern against violations (pattern matching logic)
        found_items = {}
        missing_patterns = []
        
        for pattern in pattern_items:
            matched = False
            for violation in violations:
                # Build violation string for pattern matching
                vio_str = f"{violation['pin_name']} (view: {violation['view']}, slack: {violation['slack']:.4f}ns)"
                
                # Pattern matching: check if pattern is substring of violation
                if pattern.lower() in vio_str.lower():
                    found_items[vio_str] = {
                        'name': vio_str,
                        'line_number': violation.get('line_number', 0),
                        'file_path': violation.get('file_path', 'N/A')
                    }
                    matched = True
                    break
            
            if not matched:
                missing_patterns.append(pattern)
        
        # Compare count vs value
        actual_count = len(found_items)
        
        if expected_value != 'N/A':
            try:
                expected_count = int(expected_value)
                if actual_count != expected_count:
                    # FAIL: Count mismatch
                    missing_items = {
                        f"Missing pattern {i+1}: {pattern}": {
                            'name': pattern,
                            'line_number': 0,
                            'file_path': 'N/A'
                        }
                        for i, pattern in enumerate(missing_patterns)
                    }
                    
                    return self.build_complete_output(
                        found_items=found_items,
                        missing_items=missing_items,
                        found_desc=f"{self.FOUND_DESC} - Found {actual_count}/{expected_count} required patterns",
                        missing_desc=f"{self.MISSING_DESC} - Missing {len(missing_patterns)} required patterns",
                        found_reason=self.FOUND_REASON,
                        missing_reason="Pattern not found - no violation for this corner"
                    )
            except ValueError:
                pass
        
        # PASS: All patterns found or value is N/A
        return self.build_complete_output(
            found_items=found_items,
            found_desc=f"{self.FOUND_DESC} - All {len(pattern_items)} patterns found",
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
        
        # Get requirements
        requirements = self.item_data.get('requirements', {})
        pattern_items = requirements.get('pattern_items', [])
        
        # Parse waiver configuration using template helper
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # Track pattern satisfaction
        found_clean = {}      # Patterns satisfied by no violations (clean)
        found_waived = {}     # Patterns satisfied by waived violations
        missing_patterns = {} # Patterns with unwaived violations
        used_waiver_patterns = set()
        
        # Check each required pattern
        for pattern in pattern_items:
            pattern_has_violation = False
            pattern_violation_waived = False
            
            # Check if pattern matches any violation
            for violation in violations:
                vio_str = f"{violation['pin_name']} (view: {violation['view']}, slack: {violation['slack']:.4f}ns)"
                
                # Pattern matching: check if pattern is substring
                if pattern.lower() in vio_str.lower():
                    pattern_has_violation = True
                    vio_data = {
                        'name': vio_str,
                        'line_number': violation.get('line_number', 0),
                        'file_path': violation.get('file_path', 'N/A')
                    }
                    
                    # Check if waived
                    matched_waiver = None
                    for waiver_pattern in waive_dict.keys():
                        if self.match_waiver_entry(vio_str, {waiver_pattern: waive_dict[waiver_pattern]}):
                            matched_waiver = waiver_pattern
                            used_waiver_patterns.add(waiver_pattern)
                            break
                    
                    if matched_waiver:
                        found_waived[vio_str] = vio_data
                        pattern_violation_waived = True
                    else:
                        missing_patterns[vio_str] = vio_data
                    break
            
            # If pattern has no violation, it's clean
            if not pattern_has_violation:
                clean_name = f"Pattern clean: {pattern}"
                found_clean[clean_name] = {
                    'name': clean_name,
                    'line_number': 0,
                    'file_path': 'N/A'
                }
        
        # Find unused waivers
        unused_waivers = {
            w: {
                'name': w,
                'line_number': 0,
                'file_path': 'N/A',
                'reason': waive_dict[w]
            }
            for w in waive_dict.keys()
            if w not in used_waiver_patterns
        }
        
        # Use template helper for automatic output formatting
        return self.build_complete_output(
            found_items=found_clean,
            missing_items=missing_patterns,
            waived_items=found_waived,
            unused_waivers=unused_waivers,
            waive_dict=waive_dict,
            waived_tag="[WAIVER]",
            found_desc=f"{self.FOUND_DESC} - Required patterns satisfied: {len(found_clean)}/{len(pattern_items)}",
            missing_desc=f"{self.MISSING_DESC} - Required patterns with unwaived violations",
            waived_desc=self.WAIVED_DESC,
            found_reason=lambda item: "Pattern satisfied (clean)",
            missing_reason=lambda item: "Pattern violation (unwaived)",
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
        
        # Parse waiver configuration
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # Apply waivers to violations
        waived_items = {}
        unwaived_items = {}
        used_waiver_patterns = set()
        
        for violation in violations:
            vio_name = f"{violation['pin_name']} (view: {violation['view']}, slack: {violation['slack']:.4f}ns)"
            vio_data = {
                'name': vio_name,
                'line_number': violation.get('line_number', 0),
                'file_path': violation.get('file_path', 'N/A')
            }
            
            # Check if this violation matches any waiver
            matched_waiver = None
            for waiver_pattern in waive_dict.keys():
                if self.match_waiver_entry(vio_name, {waiver_pattern: waive_dict[waiver_pattern]}):
                    matched_waiver = waiver_pattern
                    used_waiver_patterns.add(waiver_pattern)
                    break
            
            if matched_waiver:
                waived_items[vio_name] = vio_data
            else:
                unwaived_items[vio_name] = vio_data
        
        # Build found_items (clean - no violations if no unwaived violations)
        found_items = {}
        if not unwaived_items:
            found_items = {
                'All violations waived or clean': {
                    'name': 'All violations waived or clean',
                    'line_number': 0,
                    'file_path': 'N/A'
                }
            }
        
        # Find unused waivers
        unused_waivers = {
            waiver_name: {
                'name': waiver_name,
                'line_number': 0,
                'file_path': 'N/A',
                'reason': waive_dict[waiver_name]
            }
            for waiver_name in waive_dict.keys()
            if waiver_name not in used_waiver_patterns
        }
        
        # Use template helper (auto-handles waiver=0)
        return self.build_complete_output(
            found_items=found_items,
            missing_items=unwaived_items,
            waived_items=waived_items,
            unused_waivers=unused_waivers,
            waive_dict=waive_dict,
            waived_tag="[WAIVER]",
            found_desc=self.FOUND_DESC,
            missing_desc=self.MISSING_DESC,
            waived_desc=self.WAIVED_DESC,
            found_reason=lambda item: self.FOUND_REASON,
            missing_reason=lambda item: self.MISSING_REASON,
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
    checker = Check_10_0_0_12()
    checker.init_checker(Path(__file__))
    result = checker.execute_check()
    checker.write_output(result)
    return 0 if result.is_pass else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())