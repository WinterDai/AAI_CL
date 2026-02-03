################################################################################
# Script Name: IMP-10-0-0-13.py
#
# Purpose:
#   Confirm the max_capacitance check result is clean.
#
# Logic:
#   - Parse input files: maxcap_1.rpt, maxcap_2.rpt
#   - Validate report type is max_capacitance using header pattern
#   - Extract violations using state machine (SEARCHING_HEADER → IN_TABLE → PENDING_VALUES)
#   - Handle single-line violations (pin, required, actual, slack, view on one line)
#   - Handle multi-line violations (hierarchical pin names wrapping to next line)
#   - Aggregate violations across all input files
#   - Track unique timing views and violation counts
#   - Apply waiver logic to separate waived/unwaived violations
#   - Report clean result if no unwaived violations exist
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
class Check_10_0_0_13(InputFileParserMixin, OutputBuilderMixin, WaiverHandlerMixin, BaseChecker):
    """
    IMP-10-0-0-13: Confirm the max_capacitance check result is clean.
    
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
    FOUND_DESC = "Clean max_capacitance checks"
    MISSING_DESC = "Max_capacitance violations detected"
    WAIVED_DESC = "Waived max_capacitance violations"
    FOUND_REASON = "No max_capacitance violations detected"
    MISSING_REASON = "Max_capacitance violation found"
    WAIVED_BASE_REASON = "Max_capacitance violation waived per design approval"
    
    def __init__(self):
        """Initialize the checker."""
        super().__init__(
            check_module="10.0_STA_DCD_CHECK",
            item_id="IMP-10-0-0-13",
            item_desc="Confirm the max_capacitance check result is clean."
        )
        # Custom member variables for parsed data
        self._parsed_items: List[Dict[str, Any]] = []
        self._metadata: Dict[str, Any] = {}
    
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
        Parse input files to extract max_capacitance violations.
        
        Uses state machine approach to handle:
        - Single-line violations (all fields on one line)
        - Multi-line violations (hierarchical pin names wrapping)
        
        Returns:
            Dict with parsed data:
            - 'items': List[Dict] - Violations with metadata (line_number, file_path)
            - 'metadata': Dict - Summary statistics (total_violations, unique_views)
            - 'errors': List - Any parsing errors encountered
        """
        # 1. Validate inputs - IMPORTANT: returns tuple (valid_files_list, missing_files_list)
        valid_files, missing_files = self.validate_input_files()
        if missing_files:
            raise ConfigurationError(
                self.create_missing_files_error(missing_files)
            )
        
        # 2. Define parsing patterns
        pattern_check_type = re.compile(r'^Check type\s*:\s*(\S+)')
        pattern_violation_single = re.compile(r'^\s*(\S+)\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(-?\d+\.\d+)\s+(\S+)\s*$')
        pattern_pin_name = re.compile(r'^\s*(\S+/\S+)\s*$')
        pattern_continuation = re.compile(r'^\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(-?\d+\.\d+)\s+(\S+)\s*$')
        pattern_separator = re.compile(r'^\s*-{10,}\s*$')
        pattern_header = re.compile(r'^\s*Pin Name\s+Required\s+Actual\s+Slack\s+View\s*$')
        
        # 3. Parse all files
        all_violations = []
        unique_views = set()
        errors = []
        
        for file_path in valid_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    # State machine states
                    state = 'SEARCHING_HEADER'
                    pending_pin_name = None
                    pending_line_num = None
                    
                    for line_num, line in enumerate(f, 1):
                        # State: SEARCHING_HEADER
                        if state == 'SEARCHING_HEADER':
                            match = pattern_check_type.search(line)
                            if match:
                                check_type = match.group(1)
                                if check_type == 'max_capacitance':
                                    state = 'IN_TABLE'
                        
                        # State: IN_TABLE
                        elif state == 'IN_TABLE':
                            # Check for table header
                            if pattern_header.search(line):
                                continue
                            
                            # Check for separator (end of table)
                            if pattern_separator.search(line):
                                continue
                            
                            # Try single-line violation pattern first
                            match = pattern_violation_single.search(line)
                            if match:
                                pin_name = match.group(1)
                                required_cap = match.group(2)
                                actual_cap = match.group(3)
                                slack = match.group(4)
                                view_name = match.group(5)
                                
                                # Only report violations (negative slack)
                                if float(slack) < 0:
                                    violation_name = f"Pin '{pin_name}': Required={required_cap}, Actual={actual_cap}, Slack={slack} (View: {view_name})"
                                    all_violations.append({
                                        'name': violation_name,
                                        'pin_name': pin_name,
                                        'required_cap': required_cap,
                                        'actual_cap': actual_cap,
                                        'slack': slack,
                                        'view_name': view_name,
                                        'line_number': line_num,
                                        'file_path': str(file_path)
                                    })
                                    unique_views.add(view_name)
                                continue
                            
                            # Try multi-line pattern (pin name only)
                            match = pattern_pin_name.search(line)
                            if match:
                                pending_pin_name = match.group(1)
                                pending_line_num = line_num
                                state = 'PENDING_VALUES'
                                continue
                        
                        # State: PENDING_VALUES
                        elif state == 'PENDING_VALUES':
                            # Try continuation pattern
                            match = pattern_continuation.search(line)
                            if match:
                                required_cap = match.group(1)
                                actual_cap = match.group(2)
                                slack = match.group(3)
                                view_name = match.group(4)
                                
                                # Only report violations (negative slack)
                                if float(slack) < 0:
                                    violation_name = f"Pin '{pending_pin_name}': Required={required_cap}, Actual={actual_cap}, Slack={slack} (View: {view_name})"
                                    all_violations.append({
                                        'name': violation_name,
                                        'pin_name': pending_pin_name,
                                        'required_cap': required_cap,
                                        'actual_cap': actual_cap,
                                        'slack': slack,
                                        'view_name': view_name,
                                        'line_number': pending_line_num,
                                        'file_path': str(file_path)
                                    })
                                    unique_views.add(view_name)
                                
                                # Reset state
                                pending_pin_name = None
                                pending_line_num = None
                                state = 'IN_TABLE'
                            else:
                                # No continuation found, reset state
                                pending_pin_name = None
                                pending_line_num = None
                                state = 'IN_TABLE'
            
            except Exception as e:
                errors.append(f"Error parsing {file_path}: {str(e)}")
        
        # 4. Store frequently reused data on self
        self._parsed_items = all_violations
        self._metadata = {
            'total_violations': len(all_violations),
            'unique_views': len(unique_views),
            'views': list(unique_views)
        }
        
        # 5. Return aggregated dict with items containing line_number and file_path
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
        metadata = data.get('metadata', {})
        
        # Convert violations to dict with metadata for source file/line display
        # Output format: "Fail: <name>. In line <N>, <filepath>: <reason>"
        violation_items = {}
        for violation in violations:
            vio_name = violation['name']
            violation_items[vio_name] = {
                'name': vio_name,
                'line_number': violation.get('line_number', 0),
                'file_path': violation.get('file_path', 'N/A')
            }
        
        # For Type 1: violations are missing_items (semantic failures)
        # Clean result if no violations
        found_items = {} if violation_items else {'No violations': {'name': 'No violations', 'line_number': 0, 'file_path': 'N/A'}}
        missing_items = violation_items
        
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
        
        # Get requirements
        requirements = self.item_data.get('requirements', {})
        pattern_items = requirements.get('pattern_items', [])
        expected_value = requirements.get('value', 'N/A')
        
        # Match violations against pattern_items using SUBSTRING MATCH
        # (Based on README: pattern_items contain descriptive strings to search)
        found_items = {}
        missing_patterns = []
        
        for pattern in pattern_items:
            matched = False
            for violation in violations:
                # Build searchable string from violation
                vio_str = violation['name']
                
                # SUBSTRING MATCH - pattern_items are descriptive strings
                if pattern.lower() in vio_str.lower():
                    found_items[violation['name']] = {
                        'name': violation['name'],
                        'line_number': violation.get('line_number', 0),
                        'file_path': violation.get('file_path', 'N/A')
                    }
                    matched = True
                    break
            
            if not matched:
                missing_patterns.append(pattern)
        
        actual_count = len(found_items)
        
        # Use template helper (auto-handles waiver=0)
        return self.build_complete_output(
            found_items=found_items,
            missing_items=missing_patterns,
            found_desc=f"{self.FOUND_DESC} ({actual_count}/{expected_value})",
            missing_desc=f"{self.MISSING_DESC} ({len(missing_patterns)} patterns not matched)",
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
        data = self._parse_input_files()
        violations = data.get('items', [])
        
        # Get requirements and waivers
        requirements = self.item_data.get('requirements', {})
        pattern_items = requirements.get('pattern_items', [])
        
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # Track pattern satisfaction
        found_items = {}      # Patterns with no violations (clean)
        found_waived = {}     # Patterns with waived violations
        missing_patterns = {} # Patterns with unwaived violations
        other_waived = {}     # Waived violations NOT in pattern_items (for info)
        used_waiver_patterns = set()
        
        # Check each required pattern
        for pattern in pattern_items:
            pattern_has_violation = False
            
            # Check if pattern has violations
            for violation in violations:
                vio_str = violation['name']
                
                # SUBSTRING MATCH
                if pattern.lower() in vio_str.lower():
                    pattern_has_violation = True
                    vio_name = violation['name']
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
                    else:
                        missing_patterns[vio_name] = vio_data
                    break
            
            # If pattern has no violations, it's clean
            if not pattern_has_violation:
                found_items[pattern] = {
                    'name': pattern,
                    'line_number': 0,
                    'file_path': 'N/A'
                }
        
        # Track other waived violations (not in pattern_items, for info only)
        for violation in violations:
            vio_str = violation['name']
            is_pattern_violation = any(pattern.lower() in vio_str.lower() for pattern in pattern_items)
            
            if not is_pattern_violation:
                vio_name = violation['name']
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
            found_items=found_items,
            missing_items=missing_patterns,
            waived_items=all_waived,
            unused_waivers=unused_waivers,
            waive_dict=waive_dict,
            waived_tag="[WAIVER]",
            
            found_desc=f"{self.FOUND_DESC} ({len(found_items)}/{len(pattern_items)} patterns)",
            missing_desc=self.MISSING_DESC,
            waived_desc=self.WAIVED_DESC,
            
            found_reason=lambda item: self.FOUND_REASON,
            missing_reason=lambda item: self.MISSING_REASON,
            waived_base_reason=self.WAIVED_BASE_REASON,
            unused_waiver_reason="Waiver defined but no violation matched"
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
        
        # Build found_items (clean - no violations if violations list is empty)
        found_items = {}
        if not violations:
            found_items['No violations'] = {
                'name': 'No violations',
                'line_number': 0,
                'file_path': 'N/A'
            }
        
        # Apply waivers to violations
        waived_items = {}
        unwaived_items = {}
        used_waiver_patterns = set()
        
        for violation in violations:
            vio_name = violation['name']
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
            waived_tag="[WAIVER]",
            
            found_desc=self.FOUND_DESC,
            missing_desc=self.MISSING_DESC,
            waived_desc=self.WAIVED_DESC,
            
            found_reason=self.FOUND_REASON,
            missing_reason=self.MISSING_REASON,
            waived_base_reason=self.WAIVED_BASE_REASON,
            unused_waiver_reason="Waiver defined but no violation matched"
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
    checker = Check_10_0_0_13()
    checker.init_checker(Path(__file__))
    result = checker.execute_check()
    checker.write_output(result)
    return 0 if result.is_pass else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())