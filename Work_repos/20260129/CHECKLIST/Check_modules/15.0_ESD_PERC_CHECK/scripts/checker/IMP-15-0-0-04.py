################################################################################
# Script Name: IMP-15-0-0-04.py
#
# Purpose:
#   Confirm there is no issue about CNOD check if CNOD check is needed.
#
# Logic:
#   - Parse input files: cnod_perc.rep
#   - Search for "CHECK(s) PASS" pattern in the report
#   - Extract CNOD violation entries with cell names and distances
#   - Parse summary statistics (total cells, violation counts, percentages)
#   - Validate that CNOD check passed (CHECK(s) PASS found)
#   - Report FAIL if CHECK(s) PASS pattern not found
#   - Handle edge cases: empty files, missing summary sections
#
# Auto Type Detection:
#   Type 1: requirements.value=N/A, waivers.value=N/A/0 → Boolean check
#   Type 2: requirements.value>0, pattern_items exists, waivers.value=N/A/0 → Value comparison
#   Type 3: requirements.value>0, pattern_items exists, waivers.value>0 → Value with waiver logic
#   Type 4: requirements.value=N/A, waivers.value>0 → Boolean with waiver logic
#
# Output Behavior (Type 2/3 - Check README "Output Behavior" section!):
#   existence_check: pattern_items = items that SHOULD EXIST in input files
#     - found_items = patterns found in file
#     - missing_items = patterns NOT found in file
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
# Refactored: 2025-12-26 (Using checker_templates v1.1.0)
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
class Check_15_0_0_04(InputFileParserMixin, OutputBuilderMixin, WaiverHandlerMixin, BaseChecker):
    """
    IMP-15-0-0-04: Confirm there is no issue about CNOD check if CNOD check is needed.
    
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
    # DESCRIPTION & REASON CONSTANTS - COPY FROM README Output Descriptions!
    # =========================================================================
    # Type 1/4: Boolean checks - COPY EXACT VALUES FROM README!
    FOUND_DESC_TYPE1_4 = "CNOD check passed with no failures detected"
    MISSING_DESC_TYPE1_4 = "CNOD check failed or CHECK(s) PASSED not found"
    FOUND_REASON_TYPE1_4 = "CNOD verification completed successfully"
    MISSING_REASON_TYPE1_4 = "CNOD verification failed or incomplete"
    
    # Type 2/3: Pattern checks - COPY EXACT VALUES FROM README!
    FOUND_DESC_TYPE2_3 = "CNOD check passed for specified files"
    MISSING_DESC_TYPE2_3 = "CNOD check failed for specified files"
    FOUND_REASON_TYPE2_3 = "CNOD verification passed"
    MISSING_REASON_TYPE2_3 = "CNOD verification failed"
    
    # All Types (waiver description) - COPY EXACT VALUES FROM README!
    WAIVED_DESC = "CNOD check failures waived"
    
    # Waiver parameters (Type 3/4 ONLY) - COPY EXACT VALUES FROM README!
    WAIVED_BASE_REASON = "CNOD check failure waived"
    
    def __init__(self):
        """Initialize the checker."""
        super().__init__(
            check_module="15.0_ESD_PERC_CHECK",
            item_id="IMP-15-0-0-04",
            item_desc="Confirm there is no issue about CNOD check if CNOD check is needed."
        )
        # Custom member variables for parsed data
        self._parsed_items: List[Dict[str, Any]] = []
        self._check_passed: bool = False
        self._summary_stats: Dict[str, Any] = {}
    
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
        
        Parses CNOD percentage report to extract:
        - CHECK(s) PASSED/FAILED status per file
        - CNOD violation entries (cell names, distances, locations)
        - Summary statistics (total cells, violation counts, percentages)
        
        Returns:
            Dict with parsed data:
            - 'items': List[Dict] - File status results with metadata (line_number, file_path, status)
            - 'metadata': Dict - Summary statistics and check status
            - 'errors': List - Any parsing errors encountered
            - 'check_passed': bool - Whether all files passed (PASSED found and no FAILED)
        """
        # 1. Validate input files (raises ConfigurationError if missing)
        valid_files, missing_files = self.validate_input_files()
        if not valid_files or len(valid_files) == 0:
            raise ConfigurationError(
                self.create_missing_files_error(missing_files)
            )
        
        # 2. Initialize parsing results
        all_items = []  # Store file status results
        violations = []  # Store CNOD violations
        total_passed = 0
        total_failed = 0
        metadata = {
            'total_cells': 0,
            'violation_count': 0,
            'percentage': 0.0,
            'status': 'UNKNOWN'
        }
        errors = []
        overall_check_passed = False
        overall_check_failed = False
        
        # 3. Define patterns for parsing
        patterns = {
            # Pattern 1: Pass/Fail status indicator - CHECK(s) PASSED
            'pass_status': r'#\s+CHECK\(s\)\s+PASSED\s+#',
            'fail_status': r'#\s+CHECK\(s\)\s+FAILED\s+#',
            
            # Pattern 2: CNOD violation entry with cell name and distance
            'violation': r'(?:CNOD\s+)?(?:Violation|ERROR|Warning)\s*:?\s*Cell\s+([\w\/]+)\s+.*?distance\s*[:=]?\s*([\d.]+)\s*(um|nm)?',
            
            # Pattern 3: Summary statistics - total cells checked
            'total_cells': r'Total\s+(?:cells?|instances?)\s*(?:checked|analyzed)?\s*[:=]?\s*(\d+)',
            
            # Pattern 4: Violation count summary
            'violation_count': r'(?:Total\s+)?(?:CNOD\s+)?(?:Violations?|Errors?)\s*[:=]?\s*(\d+)',
            
            # Pattern 5: Cell location coordinates
            'location': r'(?:Location|Coordinate|Position)\s*[:=]?\s*\(?\s*([\d.]+)\s*,\s*([\d.]+)\s*\)?',
            
            # Pattern 6: Percentage calculation
            'percentage': r'Percentage\s*:\s*([\d.]+)%'
        }
        
        # 4. Parse each file
        for file_path in valid_files:
            file_passed = False
            file_failed = False
            file_violations = []
            file_cell_count = 0
            
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line_num, line in enumerate(f, 1):
                        # Check for PASSED status
                        if re.search(patterns['pass_status'], line):
                            file_passed = True
                            overall_check_passed = True
                            total_passed += 1
                        
                        # Check for FAILED status
                        if re.search(patterns['fail_status'], line):
                            file_failed = True
                            overall_check_failed = True
                            total_failed += 1
                        
                        # Extract CNOD violations
                        violation_match = re.search(patterns['violation'], line, re.IGNORECASE)
                        if violation_match:
                            cell_name = violation_match.group(1)
                            distance = violation_match.group(2)
                            unit = violation_match.group(3) if violation_match.lastindex >= 3 else 'um'
                            
                            violation_entry = {
                                'name': f"Cell {cell_name} - distance {distance}{unit}",
                                'cell_name': cell_name,
                                'distance': distance,
                                'unit': unit,
                                'line_number': line_num,
                                'file_path': str(file_path)
                            }
                            violations.append(violation_entry)
                            file_violations.append(violation_entry)
                        
                        # Extract total cells
                        total_match = re.search(patterns['total_cells'], line, re.IGNORECASE)
                        if total_match:
                            file_cell_count = int(total_match.group(1))
                            metadata['total_cells'] += file_cell_count
                        
                        # Extract violation count
                        count_match = re.search(patterns['violation_count'], line, re.IGNORECASE)
                        if count_match:
                            metadata['violation_count'] += int(count_match.group(1))
                        
                        # Extract percentage
                        pct_match = re.search(patterns['percentage'], line, re.IGNORECASE)
                        if pct_match:
                            metadata['percentage'] = float(pct_match.group(1))
                
                # Determine file status
                file_status = 'UNKNOWN'
                if file_passed and not file_failed:
                    file_status = 'PASSED'
                elif file_failed:
                    file_status = 'FAILED'
                
                # Create item for this file
                item = {
                    'name': file_path.name,
                    'file_path': str(file_path),
                    'status': file_status,
                    'passed': file_passed,
                    'failed': file_failed,
                    'cell_count': file_cell_count,
                    'violations': file_violations,
                    'line_number': 1  # Report file level at line 1
                }
                all_items.append(item)
                        
            except Exception as e:
                errors.append(f"Error parsing {file_path}: {str(e)}")
        
        # 5. Store frequently reused data on self
        self._parsed_items = all_items
        self._check_passed = overall_check_passed and not overall_check_failed  # Only pass if PASSED found and no FAILED
        self._summary_stats = metadata
        
        return {
            'items': all_items,
            'metadata': {
                'total_files': len(all_items),
                'total_passed': total_passed,
                'total_failed': total_failed,
                'total_cells': metadata['total_cells'],
                'violation_count': metadata['violation_count']
            },
            'errors': errors,
            'check_passed': overall_check_passed and not overall_check_failed  # Only pass if PASSED found and no FAILED
        }
    
    # =========================================================================
    # Type 1: Boolean Check
    # =========================================================================
    
    def _execute_type1(self) -> CheckResult:
        """
        Type 1: Boolean Check.
        
        Custom boolean validation - checks if CHECK(s) PASS pattern exists in report.
        Does NOT use pattern_items for searching.
        
        Use OutputBuilderMixin.build_complete_output() for automatic formatting.
        
        Returns:
            CheckResult with is_pass based on check logic
        """
        # Parse input
        data = self._parse_input_files()
        check_passed = data.get('check_passed', False)
        items = data.get('items', [])
        valid_files, _ = self.validate_input_files()
        
        # Build found_items and missing_items
        found_items = {}
        missing_items = []
        
        if check_passed:
            # PASS case: Build found_items with file details
            for file_path in valid_files:
                found_items[file_path.name] = {
                    'name': file_path.name,
                    'line_number': 1,
                    'file_path': str(file_path)
                }
        else:
            # FAIL case: Build missing_items with actual file names
            for file_path in valid_files:
                missing_items.append(f"{file_path.name} (CNOD check failed or incomplete)")
        
        # Use template helper for automatic output formatting
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
        
        Search pattern_items (file names) in input files (status_check mode).
        found_items = files matched AND status correct (PASSED).
        missing_items = files matched BUT status wrong (FAILED/UNKNOWN).
        
        Template auto-handles waiver=0 conversions.
        
        Returns:
            CheckResult with is_pass based on value comparison
        """
        # Parse input
        data = self._parse_input_files()
        items = data.get('items', [])
        
        # Get requirements
        pattern_items = self.item_data.get('requirements', {}).get('pattern_items', [])
        
        # Build lookup dict for all parsed items
        all_items = {item['name']: item for item in items}
        
        # status_check mode: Check status of files matching pattern_items
        found_items = {}      # Matched AND status correct (PASSED)
        missing_items = []    # Matched BUT status wrong (FAILED/UNKNOWN)
        missing_patterns = [] # Pattern not matched at all
        
        for pattern in pattern_items:
            matched = False
            for item_name, item_data in all_items.items():
                # Match pattern (support wildcards)
                if self._matches_pattern(pattern, item_name):
                    matched = True
                    if item_data['status'] == 'PASSED':
                        # Status correct
                        found_items[item_name] = {
                            'name': item_name,
                            'line_number': item_data.get('line_number', 1),
                            'file_path': item_data.get('file_path', 'N/A'),
                            'cell_count': item_data.get('cell_count', 0)
                        }
                    else:
                        # Status wrong (FAILED or UNKNOWN)
                        missing_items.append(f"{item_name} (status: {item_data['status']})")
                    break
            
            if not matched:
                missing_patterns.append(pattern)
        
        # Combine missing items and patterns
        all_missing = missing_items + missing_patterns
        
        # Use template helper (auto-handles waiver=0)
        # Type 2: Use TYPE2_3 desc+reason (emphasize "matched/satisfied") - API-026
        return self.build_complete_output(
            found_items=found_items,
            missing_items=all_missing,
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
        
        Same pattern search logic as Type 2 (status_check mode), plus waiver classification.
        
        Returns:
            CheckResult with FAIL for unwaived, INFO for waived items
        """
        # Parse input
        parsed_data = self._parse_input_files()
        items = parsed_data.get('items', [])
        
        # FIXED: API-016 - Use waivers.get() directly to preserve dict format
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # Get requirements
        pattern_items = self.item_data.get('requirements', {}).get('pattern_items', [])
        
        # Build lookup dict for all parsed items
        all_items = {item['name']: item for item in items}
        
        # status_check mode: Check status of files matching pattern_items
        found_items = {}      # Matched AND status correct (PASSED)
        waived_items = {}     # Matched BUT status wrong AND waived
        unwaived_items = []   # Matched BUT status wrong AND not waived
        missing_patterns = [] # Pattern not matched at all
        
        for pattern in pattern_items:
            matched = False
            for item_name, item_data in all_items.items():
                # Match pattern (support wildcards)
                if self._matches_pattern(pattern, item_name):
                    matched = True
                    if item_data['status'] == 'PASSED':
                        # Status correct
                        found_items[item_name] = {
                            'name': item_name,
                            'line_number': item_data.get('line_number', 1),
                            'file_path': item_data.get('file_path', 'N/A'),
                            'cell_count': item_data.get('cell_count', 0)
                        }
                    else:
                        # Status wrong - check if waived
                        status_desc = f"{item_name} (status: {item_data['status']})"
                        if self.match_waiver_entry(item_name, waive_dict):
                            waived_items[item_name] = {
                                'name': item_name,
                                'line_number': item_data.get('line_number', 1),
                                'file_path': item_data.get('file_path', 'N/A'),
                                'cell_count': item_data.get('cell_count', 0)
                            }
                        else:
                            unwaived_items.append(status_desc)
                    break
            
            if not matched:
                missing_patterns.append(pattern)
        
        # Combine unwaived items and missing patterns
        all_missing = unwaived_items + missing_patterns
        
        # Find unused waivers
        used_names = set(waived_items.keys())
        unused_waivers = [name for name in waive_dict.keys() if name not in used_names]
        
        # Use template helper for automatic output formatting
        # Type 3: Use TYPE2_3 desc+reason + waiver params - API-026
        return self.build_complete_output(
            found_items=found_items,
            missing_items=all_missing,
            waived_items=waived_items,
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
        check_passed = data.get('check_passed', False)
        
        # Parse waiver configuration
        # FIXED: Use waivers.get() directly to preserve dict format
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # Boolean check logic: CHECK(s) PASS found or not
        if check_passed:
            found_items = {
                'CHECK(s) PASS': {
                    'name': 'CHECK(s) PASS',
                    'line_number': 0,
                    'file_path': 'cnod_perc.rep'
                }
            }
            waived_items = {}
            missing_items = {}
        else:
            # Check if failure is waived
            failure_name = 'CHECK(s) PASS not found'
            if self.match_waiver_entry(failure_name, waive_dict):
                waived_items = {
                    failure_name: {
                        'name': failure_name,
                        'line_number': 0,
                        'file_path': 'cnod_perc.rep'
                    }
                }
                found_items = {}
                missing_items = {}
            else:
                found_items = {}
                waived_items = {}
                missing_items = {
                    failure_name: {
                        'name': failure_name,
                        'line_number': 0,
                        'file_path': 'cnod_perc.rep'
                    }
                }
        
        # Find unused waivers
        used_names = set(waived_items.keys())
        unused_waivers = [name for name in waive_dict.keys() if name not in used_names]
        
        # Use template helper (auto-handles waiver=0)
        # Type 4: Use TYPE1_4 desc+reason + waiver params - API-026
        return self.build_complete_output(
            found_items=found_items,
            missing_items=missing_items,
            waived_items=waived_items,
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
    
    def _matches_pattern(self, pattern: str, item_name: str) -> bool:
        """
        Check if item_name matches pattern (supports wildcards).
        
        Args:
            pattern: Pattern to match (may contain *)
            item_name: Item name to check
            
        Returns:
            True if item_name matches pattern
        """
        if '*' in pattern:
            regex_pattern = pattern.replace('*', '.*')
            return bool(re.search(regex_pattern, item_name, re.IGNORECASE))
        return pattern.lower() == item_name.lower()
    
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
    checker = Check_15_0_0_04()
    checker.init_checker(Path(__file__))
    result = checker.execute_check()
    checker.write_output(result)
    return 0 if result.is_pass else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())