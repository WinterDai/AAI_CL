################################################################################
# Script Name: MIG-IMP-8-1-1-01.py
#
# Purpose:
#   Confirm meet a resistance less than 0.5Ω(not exceed 0.8Ω) and a capacitance less than 350fF from pad opening to signal bump. (check the Note)
#
# Logic:
#   - Parse input files: MIG-IMP-8-1-1-01.rpt
#   - Extract net blocks containing Net name, RC corner, Total Cap, Total Res
#   - Validate each net against resistance limits (0.5Ω hard, 0.8Ω warning) and capacitance limit (350fF)
#   - Classify violations: FAIL (R≥0.5Ω or C≥350fF), WARNING (0.5Ω≤R<0.8Ω), PASS (R<0.5Ω and C<350fF)
#   - Apply waiver logic if configured (Type 3/4)
#   - Generate summary statistics and detailed violation reports
#
# Auto Type Detection:
#   Type 1: requirements.value=N/A, waivers.value=N/A/0 → Boolean check
#   Type 2: requirements.value>0, pattern_items exists, waivers.value=N/A/0 → Value comparison
#   Type 3: requirements.value>0, pattern_items exists, waivers.value>0 → Value with waiver logic
#   Type 4: requirements.value=N/A, waivers.value>0 → Boolean with waiver logic
#
# Output Behavior (Type 2/3 - Check README "Output Behavior" section!):
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
# Refactored: 2025-12-24 (Using checker_templates v1.1.0)
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
class Check_MIG_8_1_1_01(InputFileParserMixin, OutputBuilderMixin, WaiverHandlerMixin, BaseChecker):
    """
    MIG-IMP-8-1-1-01: Confirm meet a resistance less than 0.5Ω(not exceed 0.8Ω) and a capacitance less than 350fF from pad opening to signal bump. (check the Note)
    
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
    FOUND_DESC_TYPE1_4 = "Nets meeting RC limits found in report"
    MISSING_DESC_TYPE1_4 = "RC validation report not found or empty"
    FOUND_REASON_TYPE1_4 = "Net meets resistance (<0.5Ω) and capacitance (<350fF) limits"
    MISSING_REASON_TYPE1_4 = "RC validation report not found or contains no valid net data"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_DESC_TYPE2_3 = "Nets matching pattern and meeting RC limits"
    MISSING_DESC_TYPE2_3 = "Nets matching pattern but violating RC limits"
    FOUND_REASON_TYPE2_3 = "Net matches pattern and satisfies RC constraints (R<0.5Ω, C<350fF)"
    MISSING_REASON_TYPE2_3 = "Net matches pattern but violates RC limits (R≥0.5Ω or C≥350fF)"
    
    # All Types (waiver description unified)
    WAIVED_DESC = "RC violations waived per design approval"
    
    # Waiver parameters (Type 3/4 ONLY)
    WAIVED_BASE_REASON = "RC violation waived per design approval"
    
    # RC limit constants
    RESISTANCE_HARD_LIMIT = 0.5  # Ohms
    RESISTANCE_WARN_LIMIT = 0.8  # Ohms
    CAPACITANCE_LIMIT = 350.0    # fF
    
    def __init__(self):
        """Initialize the checker."""
        super().__init__(
            check_module="8.1_PHYSICAL_IMPLEMENTATION_CHECK",
            item_id="MIG-IMP-8-1-1-01",
            item_desc="Confirm meet a resistance less than 0.5Ω(not exceed 0.8Ω) and a capacitance less than 350fF from pad opening to signal bump. (check the Note)"
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
        except Exception as e:
            # Handle unexpected errors
            return create_check_result(
                is_pass=False,
                item_id=self.item_id,
                item_desc=self.item_desc,
                details=[DetailItem(
                    severity=Severity.FAIL,
                    message=f"Unexpected error during check execution: {str(e)}",
                    reason="Exception occurred during check execution"
                )]
            )
    
    # =========================================================================
    # Input Parsing (Common for All Types)
    # =========================================================================
    
    def _parse_input_files(self) -> Dict[str, Any]:
        """
        Parse input files to extract relevant data.
        
        Parses RC extraction reports with structure:
        - Net: <net_name>
        - RC Corner: <corner_name>
        - Total Cap = <value> ff
        - Total Res = <value> ohms
        
        Returns:
            Dict with parsed data:
            - 'items': List[Dict] - Net data with RC values and metadata
            - 'metadata': Dict - Summary statistics
            - 'errors': List - Parsing errors
        """
        # 1. Validate inputs - IMPORTANT: returns tuple (valid_files_list, missing_files_list)
        valid_files, missing_files = self.validate_input_files()
        
        # FIXED: KNOWN_ISSUE_LOGIC-001 - Explicitly check for empty list
        if missing_files:
            raise ConfigurationError(
                self.create_missing_files_error(missing_files)
            )
        
        if not valid_files or len(valid_files) == 0:
            raise ConfigurationError(
                create_check_result(
                    is_pass=False,
                    item_id=self.item_id,
                    item_desc=self.item_desc,
                    details=[DetailItem(
                        severity=Severity.FAIL,
                        message="No valid input files found",
                        reason="Input file validation failed"
                    )]
                )
            )
        
        # 2. Parse using patterns from file analysis
        all_items = []
        errors = []
        total_nets = 0
        pass_count = 0
        fail_count = 0
        warn_count = 0
        
        # Regex patterns for parsing
        pattern_net = re.compile(r'^Net:\s+([\w\[\]_]+)\s*$')
        pattern_corner = re.compile(r'^RC Corner:\s+(.+)\s*$')
        pattern_cap = re.compile(r'^Total Cap\s*=\s*([\d.]+)\s*ff\s*$', re.IGNORECASE)
        pattern_res = re.compile(r'^Total Res\s*=\s*([\d.]+)\s*ohms\s*$', re.IGNORECASE)
        
        for file_path in valid_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                    
                    # State machine for parsing net blocks
                    current_net = None
                    current_corner = None
                    current_cap = None
                    current_res = None
                    net_start_line = 0
                    
                    for line_num, line in enumerate(lines, 1):
                        line = line.strip()
                        
                        # Match net name
                        match_net = pattern_net.match(line)
                        if match_net:
                            # Save previous net if complete
                            if current_net and current_cap is not None and current_res is not None:
                                item = self._create_net_item(
                                    current_net, current_corner, current_cap, current_res,
                                    net_start_line, str(file_path)
                                )
                                all_items.append(item)
                                total_nets += 1
                                
                                # Update statistics
                                if item['status'] == 'PASS':
                                    pass_count += 1
                                elif item['status'] == 'FAIL':
                                    fail_count += 1
                                elif item['status'] == 'WARNING':
                                    warn_count += 1
                            
                            # Start new net
                            current_net = match_net.group(1)
                            current_corner = None
                            current_cap = None
                            current_res = None
                            net_start_line = line_num
                            continue
                        
                        # Match RC corner
                        match_corner = pattern_corner.match(line)
                        if match_corner:
                            current_corner = match_corner.group(1)
                            continue
                        
                        # Match capacitance
                        match_cap = pattern_cap.match(line)
                        if match_cap:
                            try:
                                current_cap = float(match_cap.group(1))
                            except ValueError:
                                errors.append(f"Invalid capacitance value at line {line_num}: {line}")
                            continue
                        
                        # Match resistance
                        match_res = pattern_res.match(line)
                        if match_res:
                            try:
                                current_res = float(match_res.group(1))
                            except ValueError:
                                errors.append(f"Invalid resistance value at line {line_num}: {line}")
                            continue
                    
                    # Save last net if complete
                    if current_net and current_cap is not None and current_res is not None:
                        item = self._create_net_item(
                            current_net, current_corner, current_cap, current_res,
                            net_start_line, str(file_path)
                        )
                        all_items.append(item)
                        total_nets += 1
                        
                        # Update statistics
                        if item['status'] == 'PASS':
                            pass_count += 1
                        elif item['status'] == 'FAIL':
                            fail_count += 1
                        elif item['status'] == 'WARNING':
                            warn_count += 1
            
            except Exception as e:
                errors.append(f"Error parsing file {file_path}: {str(e)}")
        
        # 3. Store frequently reused data on self
        self._parsed_items = all_items
        self._metadata = {
            'total_nets': total_nets,
            'pass_count': pass_count,
            'fail_count': fail_count,
            'warn_count': warn_count
        }
        
        # 4. Return aggregated dict
        return {
            'items': all_items,
            'metadata': self._metadata,
            'errors': errors
        }
    
    def _create_net_item(self, net_name: str, rc_corner: Optional[str], 
                        capacitance: float, resistance: float,
                        line_number: int, file_path: str) -> Dict[str, Any]:
        """
        Create a net item with RC validation status.
        
        Args:
            net_name: Net name
            rc_corner: RC corner name
            capacitance: Capacitance value in fF
            resistance: Resistance value in Ohms
            line_number: Source line number
            file_path: Source file path
            
        Returns:
            Dict with net data and validation status
        """
        # Determine status
        status = 'PASS'
        violation_type = []
        
        if resistance >= self.RESISTANCE_HARD_LIMIT:
            status = 'FAIL'
            violation_type.append(f'R={resistance:.6f}Ω≥{self.RESISTANCE_HARD_LIMIT}Ω')
        elif resistance >= self.RESISTANCE_WARN_LIMIT:
            if status != 'FAIL':
                status = 'WARNING'
            violation_type.append(f'R={resistance:.6f}Ω≥{self.RESISTANCE_WARN_LIMIT}Ω (warning)')
        
        if capacitance >= self.CAPACITANCE_LIMIT:
            status = 'FAIL'
            violation_type.append(f'C={capacitance:.6f}fF≥{self.CAPACITANCE_LIMIT}fF')
        
        # Create display name
        display_name = f"{net_name}"
        if rc_corner:
            display_name += f" @ {rc_corner}"
        
        return {
            'name': display_name,
            'net_name': net_name,
            'rc_corner': rc_corner or 'N/A',
            'capacitance': capacitance,
            'resistance': resistance,
            'status': status,
            'violation_type': ', '.join(violation_type) if violation_type else 'None',
            'line_number': line_number,
            'file_path': file_path
        }
    
    # =========================================================================
    # Type 1: Boolean Check
    # =========================================================================
    
    def _execute_type1(self) -> CheckResult:
        """
        Type 1: Boolean Check.
        
        Validates that RC extraction report exists and contains valid net data.
        PASS if report contains nets meeting RC limits.
        FAIL if report is missing, empty, or all nets violate limits.
        
        Returns:
            CheckResult with is_pass based on check logic
        """
        # Parse input
        data = self._parse_input_files()
        items = data.get('items', [])
        metadata = data.get('metadata', {})
        
        # Find passing nets
        passing_nets = [item for item in items if item['status'] == 'PASS']
        
        # Convert to dict with metadata for source file/line display
        found_items = {
            item['name']: {
                'name': item['name'],
                'line_number': item.get('line_number', 0),
                'file_path': item.get('file_path', 'N/A')
            }
            for item in passing_nets
        }
        
        missing_items = [] if found_items else ['RC validation report with passing nets']
        
        # Use template helper - Type 1: Use TYPE1_4 reason (emphasize "found/not found")
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
        
        status_check mode: Check status of nets matching pattern_items.
        Only nets matching pattern_items are evaluated and reported.
        
        found_items = patterns matched AND status correct (PASS)
        missing_items = patterns matched BUT status wrong (FAIL/WARNING)
        
        Returns:
            CheckResult with is_pass based on value comparison
        """
        # Parse input
        data = self._parse_input_files()
        all_items = data.get('items', [])
        
        # Get requirements
        pattern_items = self.item_data.get('requirements', {}).get('pattern_items', [])
        
        # status_check mode: Only output items matching pattern_items
        found_items = {}      # Matched AND status correct (PASS)
        missing_items = {}    # Matched BUT status wrong (FAIL/WARNING)
        missing_patterns = []  # Pattern not matched at all
        
        for pattern in pattern_items:
            matched = False
            for item in all_items:
                # Check if pattern matches net name (case-insensitive, support wildcards)
                if self._pattern_matches(pattern, item['net_name']):
                    matched = True
                    if item['status'] == 'PASS':
                        # Status correct
                        found_items[item['name']] = {
                            'name': item['name'],
                            'line_number': item.get('line_number', 0),
                            'file_path': item.get('file_path', 'N/A')
                        }
                    else:
                        # Status wrong (FAIL or WARNING)
                        missing_items[item['name']] = {
                            'name': item['name'],
                            'line_number': item.get('line_number', 0),
                            'file_path': item.get('file_path', 'N/A'),
                            'details': f"R={item['resistance']:.6f}Ω, C={item['capacitance']:.6f}fF - {item['violation_type']}"
                        }
            
            if not matched:
                missing_patterns.append(pattern)
        
        # Convert missing_items dict to list for build_complete_output
        missing_list = list(missing_items.keys()) if missing_items else missing_patterns
        
        # Use template helper (auto-handles waiver=0) - Type 2: Use TYPE2_3 reason
        return self.build_complete_output(
            found_items=found_items,
            missing_items=missing_list,
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
        all_items = parsed_data.get('items', [])
        
        # FIXED: KNOWN_ISSUE_API-016 - Use waivers.get() directly to preserve dict format
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # Get requirements
        pattern_items = self.item_data.get('requirements', {}).get('pattern_items', [])
        
        # status_check mode: Only output items matching pattern_items
        found_items = {}      # Matched AND status correct (PASS)
        violations = []       # Matched BUT status wrong (FAIL/WARNING)
        
        for pattern in pattern_items:
            for item in all_items:
                if self._pattern_matches(pattern, item['net_name']):
                    if item['status'] == 'PASS':
                        # Status correct
                        found_items[item['name']] = {
                            'name': item['name'],
                            'line_number': item.get('line_number', 0),
                            'file_path': item.get('file_path', 'N/A')
                        }
                    else:
                        # Status wrong - add to violations
                        violations.append({
                            'name': item['name'],
                            'net_name': item['net_name'],
                            'line_number': item.get('line_number', 0),
                            'file_path': item.get('file_path', 'N/A'),
                            'details': f"R={item['resistance']:.6f}Ω, C={item['capacitance']:.6f}fF - {item['violation_type']}"
                        })
        
        # Separate waived/unwaived using template helper
        waived_items = []
        unwaived_items = []
        
        for violation in violations:
            if self.match_waiver_entry(violation['net_name'], waive_dict):
                waived_items.append(violation['name'])
            else:
                unwaived_items.append(violation['name'])
        
        # FIXED: KNOWN_ISSUE_API-017 - waive_dict.keys() are item names (strings)
        # Find unused waivers
        used_names = set()
        for violation in violations:
            if self.match_waiver_entry(violation['net_name'], waive_dict):
                used_names.add(violation['net_name'])
        
        unused_waivers = [name for name in waive_dict.keys() if name not in used_names]
        
        # FIXED: KNOWN_ISSUE_API-021 - Use missing_items parameter instead of unwaived_items
        # Use template helper for automatic output formatting - Type 3: Use TYPE2_3 reason
        return self.build_complete_output(
            found_items=found_items,
            waived_items=waived_items,
            missing_items=unwaived_items,
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
        
        Use OutputBuilderMixin.build_complete_output() with has_waiver_value=True.
        
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
        
        # Find passing and failing nets
        passing_nets = [item for item in items if item['status'] == 'PASS']
        failing_nets = [item for item in items if item['status'] in ['FAIL', 'WARNING']]
        
        # Convert passing nets to dict with metadata
        found_items = {
            item['name']: {
                'name': item['name'],
                'line_number': item.get('line_number', 0),
                'file_path': item.get('file_path', 'N/A')
            }
            for item in passing_nets
        }
        
        # Separate waived/unwaived failing nets
        waived_items = []
        unwaived_items = []
        
        for item in failing_nets:
            if self.match_waiver_entry(item['net_name'], waive_dict):
                waived_items.append(item['name'])
            else:
                unwaived_items.append(item['name'])
        
        # FIXED: KNOWN_ISSUE_API-017 - waive_dict.keys() are item names (strings)
        # Find unused waivers
        used_names = set()
        for item in failing_nets:
            if self.match_waiver_entry(item['net_name'], waive_dict):
                used_names.add(item['net_name'])
        
        unused_waivers = [name for name in waive_dict.keys() if name not in used_names]
        
        # FIXED: KNOWN_ISSUE_API-021 - Use missing_items parameter instead of unwaived_items
        # Use template helper (auto-handles waiver=0) - Type 4: Use TYPE1_4 reason
        return self.build_complete_output(
            found_items=found_items,
            waived_items=waived_items,
            missing_items=unwaived_items,
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
    # Helper Methods (Optional - Add as needed)
    # =========================================================================
    
    def _pattern_matches(self, pattern: str, item: str) -> bool:
        """
        Check if item matches pattern (supports wildcards).
        
        Args:
            pattern: Pattern to match (supports * wildcard)
            item: Item to check
            
        Returns:
            True if item matches pattern
        """
        # Support wildcards
        if '*' in pattern:
            regex_pattern = pattern.replace('*', '.*')
            return bool(re.search(regex_pattern, item, re.IGNORECASE))
        # Exact match (case-insensitive)
        return pattern.lower() == item.lower()


# =========================================================================
# Entry Point
# =========================================================================

def main():
    """Main entry point."""
    checker = Check_MIG_8_1_1_01()
    checker.init_checker(Path(__file__))
    result = checker.execute_check()
    checker.write_output(result)
    return 0 if result.is_pass else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())