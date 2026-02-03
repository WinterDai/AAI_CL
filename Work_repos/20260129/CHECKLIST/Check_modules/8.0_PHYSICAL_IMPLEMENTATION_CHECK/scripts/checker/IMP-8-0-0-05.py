################################################################################
# Script Name: IMP-8-0-0-05.py
#
# Purpose:
#   Confirm the power switches connection is correct . (for non-PSO, please fill N/A)
#
# Logic:
#   - Parse do_fv.log to extract LEC verification results for power switches
#   - Parse check_power_switch_connection.pass.rpt to extract database connectivity check results
#   - Verify both LEC and database checks passed (no errors/problems found)
#   - Support N/A for non-PSO designs (when no power switches present)
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
# Refactored: 2026-01-06 (Using checker_templates v1.1.0)
#
# Author: Chenwei Fan
# Date: 2026-01-06
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
class Check_8_0_0_05(InputFileParserMixin, OutputBuilderMixin, WaiverHandlerMixin, BaseChecker):
    """
    IMP-8-0-0-05: Confirm the power switches connection is correct . (for non-PSO, please fill N/A)
    
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
    FOUND_DESC_TYPE1_4 = "Power switch connection verification passed - both LEC and database checks succeeded"
    MISSING_DESC_TYPE1_4 = "Power switch connection verification failed - LEC or database check did not pass"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_DESC_TYPE2_3 = "Power switch connection patterns validated successfully"
    MISSING_DESC_TYPE2_3 = "Power switch connection patterns not satisfied"
    
    # All Types (waiver description unified)
    WAIVED_DESC = "Power switch connection issues waived per design approval"
    
    # ⭐ REASON CONSTANTS - Split by Type semantics (API-025)
    # ALL Types pass found_reason/missing_reason, but use different constants
    
    # Type 1/4: Boolean checks - emphasize "found/not found" (existence)
    FOUND_REASON_TYPE1_4 = "Power Switch Connection is CORRECT based on db check and LEC result."
    MISSING_REASON_TYPE1_4 = "Power Switch Connection is WRONG based on db check and LEC result."
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_REASON_TYPE2_3 = "Power switch connection requirements matched and validated"
    MISSING_REASON_TYPE2_3 = "Power switch connection requirements not satisfied or missing"
    
    # Waiver-related (Type 3/4 only)
    WAIVED_BASE_REASON = "Power switch connection issue waived - approved by design team for non-critical path"
    UNUSED_WAIVER_REASON = "Waiver defined but no violation matched"
    
    def __init__(self):
        """Initialize the checker."""
        super().__init__(
            check_module="8.0_PHYSICAL_IMPLEMENTATION_CHECK",
            item_id="IMP-8-0-0-05",
            item_desc="Confirm the power switches connection is correct . (for non-PSO, please fill N/A)"
        )
        # Custom member variables for parsed data
        self._parsed_items: List[Dict[str, Any]] = []
        self._metadata: Dict[str, str] = {}
        self._lec_passed: bool = False
        self._db_check_passed: bool = False
        self._is_pso_design: bool = False
        self._lec_errors: List[str] = []
        self._db_problems: List[str] = []
    
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
        Parse input files to extract power switch connection verification results.
        
        Parses two types of files:
        1. do_fv.log - Cadence Conformal LEC verification log for power switch checking
        2. check_power_switch_connection.pass.rpt - Database connectivity verification report
        
        Returns:
            Dict with parsed data:
            - 'items': List[Dict] - Verification results (LEC and DB check status)
            - 'metadata': Dict - File metadata (design name, tool info, timestamps)
            - 'errors': List - Parsing errors encountered
        """
        # 1. Validate input files (returns tuple: valid_files, missing_files)
        valid_files, missing_files = self.validate_input_files()
        
        # FIXED: Explicitly check for empty list
        if missing_files and len(missing_files) > 0:
            raise ConfigurationError(
                self.create_missing_files_error(missing_files)
            )
        
        # FIXED: Explicitly check for empty list
        if not valid_files or len(valid_files) == 0:
            raise ConfigurationError("No valid input files found")
        
        # 2. Initialize parsing structures
        items = []
        metadata = {}
        errors = []
        lec_passed = False
        db_check_passed = False
        is_pso_design = False
        lec_errors = []
        db_problems = []
        lec_line_number = 0
        lec_file_path = ''
        db_line_number = 0
        db_file_path = ''
        
        # 3. Parse each input file for power switch verification information
        for file_path in valid_files:
            try:
                file_name = Path(file_path).name.lower()
                
                # Parse LEC verification log (do_fv.log)
                if 'do_fv.log' in file_name:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        for line_num, line in enumerate(f, 1):
                            # Check for PSO/power switch indicators
                            if re.search(r'(?:PSO|power[_\s]switch|UPF|CPF|power[_\s]domain)', line, re.IGNORECASE):
                                is_pso_design = True
                            
                            # Check for LEC success indicator
                            if re.search(r'SUCCEEDED!', line):
                                lec_passed = True
                                lec_line_number = line_num
                                lec_file_path = str(file_path)
                                items.append({
                                    'name': 'LEC_VERIFICATION',
                                    'status': 'PASSED',
                                    'line_number': line_num,
                                    'file_path': str(file_path),
                                    'type': 'lec_check',
                                    'detail': 'LEC verification: SUCCEEDED!',
                                    'content': line.strip()
                                })
                            
                            # Extract LEC errors
                            error_match = re.search(r'//\s*(?:\*\*)?ERROR:\s*(?:\(([A-Z]+-[A-Z0-9]+)\))?\s*(.+)', line)
                            if error_match:
                                error_code = error_match.group(1) or 'UNKNOWN'
                                error_msg = error_match.group(2).strip()
                                lec_errors.append(f"{error_code}: {error_msg}")
                                items.append({
                                    'name': f'LEC_ERROR_{error_code}',
                                    'status': 'ERROR',
                                    'line_number': line_num,
                                    'file_path': str(file_path),
                                    'type': 'lec_error',
                                    'detail': f"{error_code}: {error_msg}",
                                    'content': line.strip()
                                })
                
                # Parse database connectivity report (check_power_switch_connection.pass.rpt)
                elif 'check_power_switch_connection' in file_name:
                    in_summary = False
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        for line_num, line in enumerate(f, 1):
                            # Extract design name
                            design_match = re.search(r'^#\s*Design:\s+(.+)\s*$', line)
                            if design_match:
                                metadata['design_name'] = design_match.group(1).strip()
                            
                            # Track summary section
                            if re.match(r'^Begin Summary\s*$', line):
                                in_summary = True
                                continue
                            elif re.match(r'^End Summary\s*$', line):
                                in_summary = False
                                continue
                            
                            # Check for pass status in summary
                            if in_summary:
                                if re.search(r'^\s*Found no problems or warnings\.\s*$', line):
                                    db_check_passed = True
                                    db_line_number = line_num
                                    db_file_path = str(file_path)
                                    items.append({
                                        'name': 'DB_CHECK',
                                        'status': 'PASSED',
                                        'line_number': line_num,
                                        'file_path': str(file_path),
                                        'type': 'db_check',
                                        'detail': 'Database check: Found no problems or warnings.',
                                        'content': line.strip()
                                    })
                                
                                # Extract problems/errors
                                problem_match = re.search(r'^\s*(?:ERROR|WARNING|Problem):\s*(.+)$', line)
                                if problem_match:
                                    problem_msg = problem_match.group(1).strip()
                                    db_problems.append(problem_msg)
                                    items.append({
                                        'name': 'DB_PROBLEM',
                                        'status': 'ERROR',
                                        'line_number': line_num,
                                        'file_path': str(file_path),
                                        'type': 'db_problem',
                                        'detail': problem_msg,
                                        'content': line.strip()
                                    })
                            
                            # Extract report timestamp
                            timestamp_match = re.search(r'^Verify Connectivity Report is created on (.+)$', line)
                            if timestamp_match:
                                metadata['report_timestamp'] = timestamp_match.group(1).strip()
            
            except Exception as e:
                errors.append(f"Error parsing {file_path}: {str(e)}")
        
        # 4. Store frequently reused data on self
        self._parsed_items = items
        self._metadata = metadata
        self._lec_passed = lec_passed
        self._db_check_passed = db_check_passed
        self._is_pso_design = is_pso_design
        self._lec_errors = lec_errors
        self._db_problems = db_problems
        
        return {
            'items': items,
            'metadata': metadata,
            'errors': errors,
            'lec_passed': lec_passed,
            'db_passed': db_check_passed,
            'lec_line_number': lec_line_number,
            'lec_file_path': lec_file_path,
            'db_line_number': db_line_number,
            'db_file_path': db_file_path
        }
    # Helper Methods (Optional - Add as needed)
    

    # =========================================================================
    # Type 1: Boolean Check

    def _execute_type1(self) -> CheckResult:
        """
        Type 1: Boolean check without waiver support.

        Performs dual verification:
        1. LEC verification: Searches for 'SUCCEEDED!' in do_fv.log
        2. Database check: Searches for 'Found no problems or warnings.' in connectivity report

        PASS if both patterns found, FAIL if either pattern missing.
        """
        violations = self._type1_core_logic()

        # Build found_items from successful checks
        data = self._parse_input_files()
        found_items = {}

        # Add LEC verification if passed
        if 'LEC verification' not in violations:
            found_items['LEC verification'] = {
                'name': 'LEC verification',
                'line_number': data.get('lec_line_number', 0),
                'file_path': data.get('lec_file_path', 'do_fv.log')
            }

        # Add database check if passed
        if 'Database check' not in violations:
            found_items['Database check'] = {
                'name': 'Database check',
                'line_number': data.get('db_line_number', 0),
                'file_path': data.get('db_file_path', 'check_power_switch_connection.pass.rpt')
            }

        missing_items = violations

        return self.build_complete_output(
            found_items=found_items,
            missing_items=missing_items,
            found_desc=self.FOUND_DESC_TYPE1_4,
            missing_desc=self.MISSING_DESC_TYPE1_4,
            found_reason=self.FOUND_REASON_TYPE1_4,
            missing_reason=self.MISSING_REASON_TYPE1_4
        )

    def _type1_core_logic(self) -> dict[str, dict]:
        """
        Core Type 1 boolean check logic (shared by Type 1 and Type 4).

        Performs dual verification:
        1. LEC verification: Pattern 'SUCCEEDED!' in do_fv.log
        2. Database check: Pattern 'Found no problems or warnings.' in connectivity report

        Returns:
            Dict of violations: {check_name: {'line_number': ..., 'file_path': ..., 'reason': ...}}
            Empty dict if all checks pass.
        """
        data = self._parse_input_files()
        violations = {}

        # Check 1: LEC verification (do_fv.log)
        lec_passed = data.get('lec_passed', False)
        if not lec_passed:
            violations['LEC verification'] = {
                'line_number': 0,
                'file_path': data.get('lec_file_path', 'do_fv.log'),
                'reason': "Pattern 'SUCCEEDED!' not found in do_fv.log"
            }

        # Check 2: Database connectivity check (check_power_switch_connection.pass.rpt)
        db_passed = data.get('db_passed', False)
        if not db_passed:
            violations['Database check'] = {
                'line_number': 0,
                'file_path': data.get('db_file_path', 'check_power_switch_connection.pass.rpt'),
                'reason': "Pattern 'Found no problems or warnings.' not found in connectivity report"
            }

        return violations

    # =========================================================================
    # Type 4: Boolean Check with Waiver Logic

    def _execute_type4(self) -> CheckResult:
        """
        Type 4: Boolean check with waiver support (reuses Type 1 core logic).

        Performs same dual verification as Type 1, but allows waiving violations:
        - LEC verification failures can be waived
        - Database check failures can be waived

        PASS if all violations are waived, FAIL if any unwaived violations exist.
        """
        violations = self._type1_core_logic()

        # Build found_items from successful checks
        data = self._parse_input_files()
        found_items = {}

        # Add LEC verification if passed
        if 'LEC verification' not in violations:
            found_items['LEC verification'] = {
                'name': 'LEC verification',
                'line_number': data.get('lec_line_number', 0),
                'file_path': data.get('lec_file_path', 'do_fv.log')
            }

        # Add database check if passed
        if 'Database check' not in violations:
            found_items['Database check'] = {
                'name': 'Database check',
                'line_number': data.get('db_line_number', 0),
                'file_path': data.get('db_file_path', 'check_power_switch_connection.pass.rpt')
            }

        # FIXED: Parse waiver configuration using correct API
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)

        # Split violations into waived and unwaived
        waived_items = {}
        missing_items = {}
        used_waivers = set()

        for viol_name, viol_data in violations.items():
            matched_waiver = self.match_waiver_entry(viol_name, waive_dict)
            if matched_waiver:
                waived_items[viol_name] = viol_data
                used_waivers.add(matched_waiver)
            else:
                missing_items[viol_name] = viol_data

        # Find unused waivers
        unused_waivers = [w for w in waive_dict.keys() if w not in used_waivers]

        # Build output
        return self.build_complete_output(
            found_items=found_items,
            missing_items=missing_items,
            waived_items=waived_items,
            unused_waivers=unused_waivers,
            waive_dict=waive_dict,
            found_desc=self.FOUND_DESC_TYPE1_4,
            missing_desc=self.MISSING_DESC_TYPE1_4,
            waived_desc=self.WAIVED_DESC,
            found_reason=self.FOUND_REASON_TYPE1_4,
            missing_reason=self.MISSING_REASON_TYPE1_4,
            waived_base_reason=self.WAIVED_BASE_REASON,
            unused_waiver_reason=self.UNUSED_WAIVER_REASON
        )

    # =========================================================================
    # Type 2: Value Check

    def _execute_type2(self) -> CheckResult:
        """Type 2: Pattern/value check without waiver support."""
        found_items, missing_items = self._type2_core_logic()

        # FIXED: Pass dict directly, not list(missing_items.values())
        return self.build_complete_output(
            found_items=found_items,
            missing_items=missing_items,
            found_desc=self.FOUND_DESC_TYPE2_3,
            missing_desc=self.MISSING_DESC_TYPE2_3,
            found_reason=self.FOUND_REASON_TYPE2_3,
            missing_reason=self.MISSING_REASON_TYPE2_3
        )

    def _type2_core_logic(self) -> tuple[dict[str, dict], dict[str, dict]]:
        """
        Core Type 2 pattern matching logic (shared by Type 2 and Type 3).

        Returns:
            Tuple of (found_items, missing_items)
            - found_items: {item_name: {'line_number': ..., 'file_path': ...}}
            - missing_items: {item_name: {'line_number': ..., 'file_path': ..., 'reason': ...}}
        """
        data = self._parse_input_files()
        items = data.get('items', [])

        requirements = self.item_data.get('requirements', {})
        pattern_items = requirements.get('pattern_items', [])

        found_items = {}
        missing_items = {}

        # Search for required patterns in parsed items
        # Pattern 1: "SUCCEEDED!" in do_fv.log (LEC verification)
        # Pattern 2: "Found no problems or warnings." in connectivity report
        for pattern in pattern_items:
            matched = False
            for item in items:
                item_content = item.get('content', '')
                # SUBSTRING MATCH: Search for pattern in item content
                if pattern.lower() in item_content.lower():
                    found_items[pattern] = {
                        'name': pattern,
                        'line_number': item.get('line_number', 0),
                        'file_path': item.get('file_path', 'N/A')
                    }
                    matched = True
                    break

            if not matched:
                missing_items[pattern] = {
                    'name': pattern,
                    'line_number': 0,
                    'file_path': 'N/A',
                    'reason': f'Pattern "{pattern}" not found in input files'
                }

        return found_items, missing_items

    # =========================================================================
    # Type 3: Value Check with Waiver Logic

    def _execute_type3(self) -> CheckResult:
        """Type 3: Pattern/value check with waiver support (reuses Type 2 core logic)."""
        # Step 1: Get found/missing items using Type 2's core logic
        found_items_base, violations = self._type2_core_logic()

        # FIXED: Parse waiver configuration using correct API
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)

        # Step 3: Split violations into waived and unwaived
        found_items = {}
        waived_items = {}
        missing_items = {}
        used_waivers = set()

        # Process found_items_base (no waiver needed - patterns found cleanly)
        for item_name, item_data in found_items_base.items():
            found_items[item_name] = item_data

        # Process violations with waiver matching
        for viol_name, viol_data in violations.items():
            matched_waiver = self.match_waiver_entry(viol_name, waive_dict)
            if matched_waiver:
                waived_items[viol_name] = viol_data
                used_waivers.add(matched_waiver)
            else:
                missing_items[viol_name] = viol_data

        # Step 4: Find unused waivers
        unused_waivers = [w for w in waive_dict.keys() if w not in used_waivers]

        # FIXED: Pass dict directly, not list(missing_items.values())
        return self.build_complete_output(
            found_items=found_items,
            missing_items=missing_items,
            waived_items=waived_items,
            unused_waivers=unused_waivers,
            waive_dict=waive_dict,
            found_desc=self.FOUND_DESC_TYPE2_3,
            missing_desc=self.MISSING_DESC_TYPE2_3,
            waived_desc=self.WAIVED_DESC,
            found_reason=self.FOUND_REASON_TYPE2_3,
            missing_reason=self.MISSING_REASON_TYPE2_3,
            waived_base_reason=self.WAIVED_BASE_REASON,
            unused_waiver_reason=self.UNUSED_WAIVER_REASON
        )
    def _matches_waiver(self, item: str, waive_patterns: List[str]) -> bool:
        """
        Check if item matches any waiver pattern.
        
        TODO: Optional - Implement waiver matching logic
        
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
    checker = Check_8_0_0_05()
    checker.init_checker(Path(__file__))
    result = checker.execute_check()
    checker.write_output(result)
    return 0 if result.is_pass else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())