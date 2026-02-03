################################################################################
# Script Name: IMP-15-0-0-03.py
#
# Purpose:
#   Confirm there is no issue about ESD PERC check if PERC check is needed.
#
# Logic:
#   - Parse input files: prec*.rep
#   - Extract CHECK status indicators (PASSED/FAILED) from verification results
#   - Count verified cells from "CELL NAME:" entries with placement counts
#   - Collect LVS filter configurations and any error/violation messages
#   - Determine overall PERC check status based on CHECK indicators
#   - Report PASS if "CHECK(s) PASSED" found and no "CHECK(s) FAILED"
#   - Report FAIL if "CHECK(s) FAILED" found or no CHECK status detected
#
# Auto Type Detection:
#   Type 1: requirements.value=N/A, pattern_items [] (empty), waivers.value=N/A/0 → Boolean Check
#   Type 2: requirements.value>0, pattern_items [...] (defined), waivers.value=N/A/0 → Value Check
#   Type 3: requirements.value>0, pattern_items [...] (defined), waivers.value>0 → Value Check with Waiver Logic
#   Type 4: requirements.value=N/A, pattern_items [] (empty), waivers.value>0 → Boolean Check with Waiver Logic
#   Note: requirements.value indicates number of patterns for config validation (doesn't affect PASS/FAIL)
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
from checker_templates.input_file_parser_template import InputFileParserMixin


# MANDATORY: Inherit mixins in correct order (InputFileParserMixin first if used)
class Check_15_0_0_03(InputFileParserMixin, OutputBuilderMixin, WaiverHandlerMixin, BaseChecker):
    """
    IMP-15-0-0-03: Confirm there is no issue about ESD PERC check if PERC check is needed.
    
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
    FOUND_DESC_TYPE1_4 = "PERC check passed with no failures detected"
    MISSING_DESC_TYPE1_4 = "PERC check failed or no CHECK status found"
    FOUND_REASON_TYPE1_4 = "PERC verification completed successfully"
    MISSING_REASON_TYPE1_4 = "PERC verification failed or incomplete"
    
    # Type 2/3: Pattern checks - COPY EXACT VALUES FROM README!
    FOUND_DESC_TYPE2_3 = "PERC check passed for specified files"
    MISSING_DESC_TYPE2_3 = "PERC check failed for specified files"
    FOUND_REASON_TYPE2_3 = "PERC verification passed"
    MISSING_REASON_TYPE2_3 = "PERC verification failed"
    
    # All Types (waiver description) - COPY EXACT VALUES FROM README!
    WAIVED_DESC = "PERC check failures waived"
    
    # Waiver parameters (Type 3/4 ONLY) - COPY EXACT VALUES FROM README!
    WAIVED_BASE_REASON = "PERC check failure waived"
    
    def __init__(self):
        """Initialize the checker."""
        super().__init__(
            check_module="15.0_ESD_PERC_CHECK",
            item_id="IMP-15-0-0-03",
            item_desc="Confirm there is no issue about ESD PERC check if PERC check is needed."
        )
        # Custom member variables for parsed data
        self._parsed_items: List[Dict[str, Any]] = []
        self._check_status: Dict[str, Any] = {}
    
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
        
        Parse PERC report files (prec*.rep) to extract:
        1. Overall CHECK status (PASSED/FAILED) from verification results section
        2. Cell verification details (cell names and placement counts)
        3. LVS filter configurations
        4. Any error or violation messages
        
        Returns:
            Dict with parsed data:
            - 'items': List[Dict] - PERC check results per file with metadata
            - 'metadata': Dict - Aggregated statistics
            - 'errors': List - Any parsing errors encountered
        """
        # 1. Validate input files - IMPORTANT: returns tuple (valid_files_list, missing_files_list)
        valid_files, missing_files = self.validate_input_files()
        
        # FIXED: LOGIC-001 - Explicitly check for empty list
        if not valid_files or len(valid_files) == 0:
            raise ConfigurationError(
                self.create_missing_files_error(missing_files) if missing_files 
                else "No valid input files found"
            )
        
        # 2. Parse using patterns from file analysis
        all_items = []
        total_cells = 0
        total_passed = 0
        total_failed = 0
        errors = []
        
        # Define patterns for PERC report parsing
        pattern_check_passed = re.compile(r'#\s+CHECK\(s\)\s+PASSED\s+#')
        pattern_check_failed = re.compile(r'#\s+CHECK\(s\)\s+FAILED\s+#')
        pattern_cell_name = re.compile(r'CELL NAME:\s+(\S+)\s+\((\d+)\s+placements?\)')
        pattern_lvs_filter = re.compile(r'LVS FILTER\s+(\S+)\s+(OPEN|SHORT|\S+)')
        pattern_error = re.compile(r'(ERROR|VIOLATION|FAIL):\s*(.+)', re.IGNORECASE)
        
        for file_path in valid_files:
            file_passed = False
            file_failed = False
            file_cells = []
            file_errors = []
            file_cell_count = 0
            
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line_num, line in enumerate(f, 1):
                        # Check for PASSED status
                        if pattern_check_passed.search(line):
                            file_passed = True
                            total_passed += 1
                        
                        # Check for FAILED status
                        if pattern_check_failed.search(line):
                            file_failed = True
                            total_failed += 1
                        
                        # Extract cell names and counts
                        cell_match = pattern_cell_name.search(line)
                        if cell_match:
                            cell_name = cell_match.group(1)
                            cell_count = int(cell_match.group(2))
                            file_cells.append({
                                'name': cell_name,
                                'count': cell_count,
                                'line_number': line_num,
                                'file_path': str(file_path)
                            })
                            file_cell_count += cell_count
                            total_cells += cell_count
                        
                        # Extract error/violation messages
                        error_match = pattern_error.search(line)
                        if error_match:
                            error_type = error_match.group(1)
                            error_msg = error_match.group(2).strip()
                            file_errors.append({
                                'type': error_type,
                                'message': error_msg,
                                'line_number': line_num,
                                'file_path': str(file_path)
                            })
                
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
                    'cells': file_cells,
                    'errors': file_errors,
                    'line_number': 1  # Report file level at line 1
                }
                all_items.append(item)
                
            except Exception as e:
                errors.append(f"Error parsing {file_path}: {str(e)}")
        
        # 3. Store frequently reused data on self
        self._parsed_items = all_items
        self._check_status = {
            'total_passed': total_passed,
            'total_failed': total_failed,
            'total_cells': total_cells
        }
        
        # 4. Return aggregated dict with items containing line_number and file_path
        return {
            'items': all_items,
            'metadata': {
                'total_files': len(all_items),
                'total_passed': total_passed,
                'total_failed': total_failed,
                'total_cells': total_cells
            },
            'errors': errors
        }
    
    # =========================================================================
    # Type 1: Boolean Check
    # =========================================================================
    
    def _execute_type1(self) -> CheckResult:
        """
        Type 1: Boolean Check.
        
        Check if PERC verification passed overall (at least one PASSED, no FAILED).
        Does NOT use pattern_items for searching.
        
        Returns:
            CheckResult with is_pass based on check logic
        """
        # Parse input
        data = self._parse_input_files()
        items = data.get('items', [])
        metadata = data.get('metadata', {})
        
        # Check overall status
        has_passed = any(item['passed'] for item in items)
        has_failed = any(item['failed'] for item in items)
        has_check_status = has_passed or has_failed
        
        # Build found_items and missing_items
        found_items = {}
        missing_items = []
        
        if has_passed and not has_failed:
            # PASS case: Build found_items with file details
            for item in items:
                if item['passed']:
                    found_items[item['name']] = {
                        'name': item['name'],
                        'line_number': item.get('line_number', 1),
                        'file_path': item.get('file_path', 'N/A'),
                        'cell_count': item.get('cell_count', 0)
                    }
        else:
            # FAIL case: Build missing_items
            if has_failed:
                for item in items:
                    if item['failed']:
                        missing_items.append(f"{item['name']} (CHECK FAILED)")
            elif not has_check_status:
                missing_items.append("No CHECK status found in PERC reports")
            else:
                missing_items.append("PERC check did not pass")
        
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
        
        Search pattern_items in input files (status_check mode).
        found_items = patterns matched AND status correct (PASSED).
        missing_items = patterns matched BUT status wrong (FAILED/UNKNOWN).
        
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
        
        # status_check mode: Check status of items matching pattern_items
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
        
        # status_check mode: Check status of items matching pattern_items
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
                        # Status wrong (FAILED or UNKNOWN) - check waiver
                        if self.match_waiver_entry(item_name, waive_dict):
                            waived_items[item_name] = {
                                'name': item_name,
                                'line_number': item_data.get('line_number', 1),
                                'file_path': item_data.get('file_path', 'N/A'),
                                'status': item_data['status']
                            }
                        else:
                            unwaived_items.append(f"{item_name} (status: {item_data['status']})")
                    break
            
            if not matched:
                missing_patterns.append(pattern)
        
        # Combine unwaived items and missing patterns
        all_unwaived = unwaived_items + missing_patterns
        
        # Find unused waivers
        used_names = set(waived_items.keys())
        unused_waivers = [name for name in waive_dict.keys() if name not in used_names]
        
        # Use template helper for automatic output formatting
        # Type 3: Use TYPE2_3 desc+reason + waiver params - API-026
        return self.build_complete_output(
            found_items=found_items,
            waived_items=waived_items,
            missing_items=all_unwaived,
            unused_waivers=unused_waivers,
            waive_dict=waive_dict,
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
        
        Returns:
            CheckResult with waiver logic applied
        """
        # Parse input
        data = self._parse_input_files()
        items = data.get('items', [])
        
        # FIXED: API-016 - Use waivers.get() directly to preserve dict format
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # Check overall status
        has_passed = any(item['passed'] for item in items)
        has_failed = any(item['failed'] for item in items)
        
        # Build found_items, waived_items, and missing_items
        found_items = {}
        waived_items = {}
        missing_items = []
        
        if has_passed and not has_failed:
            # PASS case: Build found_items with file details
            for item in items:
                if item['passed']:
                    found_items[item['name']] = {
                        'name': item['name'],
                        'line_number': item.get('line_number', 1),
                        'file_path': item.get('file_path', 'N/A'),
                        'cell_count': item.get('cell_count', 0)
                    }
        else:
            # FAIL case: Separate waived and unwaived failures
            for item in items:
                if item['failed']:
                    if self.match_waiver_entry(item['name'], waive_dict):
                        waived_items[item['name']] = {
                            'name': item['name'],
                            'line_number': item.get('line_number', 1),
                            'file_path': item.get('file_path', 'N/A'),
                            'status': item['status']
                        }
                    else:
                        missing_items.append(f"{item['name']} (CHECK FAILED)")
            
            # Add general failure if no specific failures found
            if not has_failed and not has_passed:
                missing_items.append("No CHECK status found in PERC reports")
        
        # Find unused waivers
        used_names = set(waived_items.keys())
        unused_waivers = [name for name in waive_dict.keys() if name not in used_names]
        
        # Use template helper (auto-handles waiver=0)
        # Type 4: Use TYPE1_4 desc+reason + waiver params - API-026
        return self.build_complete_output(
            found_items=found_items,
            waived_items=waived_items,
            missing_items=missing_items,
            unused_waivers=unused_waivers,
            waive_dict=waive_dict,
            found_desc=self.FOUND_DESC_TYPE1_4,
            missing_desc=self.MISSING_DESC_TYPE1_4,
            waived_desc=self.WAIVED_DESC,
            found_reason=self.FOUND_REASON_TYPE1_4,
            missing_reason=self.MISSING_REASON_TYPE1_4,
            waived_base_reason=self.WAIVED_BASE_REASON
        )
    
    # =========================================================================
    # Helper Methods
    # =========================================================================
    
    def _matches_pattern(self, pattern: str, item: str) -> bool:
        """
        Check if item matches pattern (supports wildcards).
        
        Args:
            pattern: Pattern to match (may contain wildcards)
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
    checker = Check_15_0_0_03()
    checker.init_checker(Path(__file__))
    result = checker.execute_check()
    checker.write_output(result)
    return 0 if result.is_pass else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())