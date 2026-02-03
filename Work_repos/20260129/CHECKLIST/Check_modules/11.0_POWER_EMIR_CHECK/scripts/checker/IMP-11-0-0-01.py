################################################################################
# Script Name: IMP-11-0-0-01.py
#
# Purpose:
#   Confirm the design has no power open/short and all instances are physically connected.
#
# Logic:
#   - Parse lvs.rep.cls file to extract LVS run result status
#   - Extract overall run result (MATCH/MISMATCH) from header section
#   - Verify LVS result matches expected status (MATCH)
#   - PASS if LVS result is MATCH (no power/connectivity issues)
#   - FAIL if LVS result is MISMATCH or missing (power opens/shorts exist)
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
# Author: Jing Li
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
class Check_11_0_0_01(InputFileParserMixin, OutputBuilderMixin, WaiverHandlerMixin, BaseChecker):
    """
    IMP-11-0-0-01: Confirm the design has no power open/short and all instances are physically connected.
    
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
    FOUND_DESC_TYPE1_4 = "LVS comparison passed - no power connectivity issues found"
    MISSING_DESC_TYPE1_4 = "Power connectivity issues found in LVS report"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_DESC_TYPE2_3 = "LVS comparison matched - all power connectivity requirements satisfied"
    MISSING_DESC_TYPE2_3 = "LVS comparison failed - power connectivity requirements not satisfied"
    
    # All Types (waiver description unified)
    WAIVED_DESC = "Waived power connectivity violations"
    
    # ⭐ REASON CONSTANTS - Split by Type semantics (API-025)
    # ALL Types pass found_reason/missing_reason, but use different constants
    
    # Type 1/4: Boolean checks - emphasize "found/not found" (existence)
    FOUND_REASON_TYPE1_4 = "LVS Run Result: MATCH | No power open/short detected | All instances physically connected"
    MISSING_REASON_TYPE1_4 = "LVS Run Result: MISMATCH | Power open/short detected or instances unconnected"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_REASON_TYPE2_3 = "LVS comparison matched successfully | Power connectivity validated | All instances properly connected"
    MISSING_REASON_TYPE2_3 = "LVS comparison failed | Power connectivity requirements not satisfied"
    
    # Waiver-related (Type 3/4 only)
    WAIVED_BASE_REASON = "Power connectivity violation waived per design review"
    UNUSED_WAIVER_REASON = "Waiver not matched - no corresponding power connectivity violation found in LVS report"
    
    def __init__(self):
        """Initialize the checker."""
        super().__init__(
            check_module="11.0_POWER_EMIR_CHECK",
            item_id="IMP-11-0-0-01",
            item_desc="Confirm the design has no power open/short and all instances are physically connected."
        )
        # Custom member variables for parsed data
        self._parsed_items: List[Dict[str, Any]] = []
        self._metadata: Dict[str, str] = {}
        self._lvs_run_result: Optional[str] = None
        self._cell_statistics: Dict[str, int] = {}
    
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
        Parse LVS report file to extract run result status.
        
        Parses lvs.rep.cls file to extract:
        - Overall LVS run result (MATCH/MISMATCH)
        - Cell match statistics (matched, mismatched, expanded)
        - File metadata (top cell, run date, etc.)
        
        Returns:
            Dict with parsed data:
            - 'items': List[Dict] - LVS run result items with status
            - 'metadata': Dict - File metadata (top_cell, run_date, etc.)
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
        lvs_run_result = None
        cell_statistics = {}
        
        # 3. Parse each input file for LVS run result information
        # Pattern 1: Extract overall LVS run result (MATCH/MISMATCH)
        run_result_pattern = re.compile(r'^#####\s+Run Result\s*:\s*(\w+)\s*$')
        # Pattern 2: Extract top cell name
        top_cell_pattern = re.compile(r'^#####\s+Top Cell\s*:\s*(.+?)\s*<vs>\s*(.+?)\s*$')
        # Pattern 3: Extract cell match statistics
        statistics_pattern = re.compile(r'^(Cells matched|Cells which mismatch|Cells expanded|Cells not run)\s*\|\s*([\d,]+)\s*$')
        
        for file_path in valid_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line_num, line in enumerate(f, 1):
                        # Extract LVS run result
                        match = run_result_pattern.search(line)
                        if match:
                            lvs_run_result = match.group(1).strip()
                            items.append({
                                'name': 'Overall_Run_Result',
                                'line_number': line_num,
                                'file_path': str(file_path),
                                'type': 'lvs_run_result',
                                'status': lvs_run_result
                            })
                            metadata['run_result'] = lvs_run_result
                            metadata['result_line'] = line_num
                        
                        # Extract top cell
                        match = top_cell_pattern.search(line)
                        if match:
                            layout_top = match.group(1).strip()
                            schematic_top = match.group(2).strip()
                            metadata['layout_top_cell'] = layout_top
                            metadata['schematic_top_cell'] = schematic_top
                        
                        # Extract cell statistics
                        match = statistics_pattern.search(line)
                        if match:
                            stat_type = match.group(1).strip()
                            count_str = match.group(2).replace(',', '')
                            cell_statistics[stat_type] = int(count_str)
            except Exception as e:
                errors.append(f"Error parsing {file_path}: {str(e)}")
        
        # 4. Store frequently reused data on self
        self._parsed_items = items
        self._metadata = metadata
        self._lvs_run_result = lvs_run_result
        self._cell_statistics = cell_statistics
        
        return {
            'items': items,
            'metadata': metadata,
            'errors': errors
        }
    
    # =========================================================================
    # Type 1: Boolean Check
    # =========================================================================
    
    def _execute_type1(self) -> CheckResult:
        """
        Type 1: Boolean check without waiver support.
        
        Verifies LVS run result is MATCH (no power opens/shorts or connectivity issues).
        PASS if LVS result is MATCH, FAIL if MISMATCH or missing.
        """
        violations = self._type1_core_logic()
        
        # Build found_items from clean LVS results (MATCH status)
        data = self._parse_input_files()
        lvs_result = data.get('metadata', {}).get('run_result', '')
        
        found_items = {}
        if lvs_result == 'MATCH':
            # LVS passed - add as found item
            valid_files, _ = self.validate_input_files()
            found_items['Overall_Run_Result'] = {
                'name': 'Overall_Run_Result',
                'line_number': data.get('metadata', {}).get('result_line', 0),
                'file_path': str(valid_files[0]) if valid_files else 'N/A'
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
    
    def _type1_core_logic(self) -> dict:
        """
        Core Type 1 boolean check logic (shared by Type 1 and Type 4).
        
        Parses lvs.rep.cls file and checks if LVS result is MATCH.
        
        Returns:
            Dict of violations: {item_name: {'line_number': ..., 'file_path': ..., 'reason': ...}}
            Empty dict if LVS result is MATCH (all checks pass).
        """
        data = self._parse_input_files()
        
        # Check for parsing errors
        errors = data.get('errors', [])
        if errors:
            # File parsing failed - treat as violation
            return {
                'Overall_Run_Result': {
                    'line_number': 0,
                    'file_path': 'N/A',
                    'reason': f"LVS file parsing failed: {'; '.join(errors)}"
                }
            }
        
        # Extract LVS result from metadata
        metadata = data.get('metadata', {})
        lvs_result = metadata.get('run_result', '')
        line_number = metadata.get('result_line', 0)
        valid_files, _ = self.validate_input_files()
        file_path = str(valid_files[0]) if valid_files else 'N/A'
        
        violations = {}
        
        # Check if LVS result is MATCH
        if lvs_result != 'MATCH':
            # LVS failed or result missing - this is a violation
            violations['Overall_Run_Result'] = {
                'line_number': line_number,
                'file_path': file_path,
                'reason': self.MISSING_REASON_TYPE1_4
            }
        
        return violations
    
    # =========================================================================
    # Type 2: Value Check
    # =========================================================================
    
    def _execute_type2(self) -> CheckResult:
        """Type 2: Pattern/value check without waiver support."""
        found_items, missing_items = self._type2_core_logic()
        
        return self.build_complete_output(
            found_items=found_items,
            missing_items=missing_items,
            found_desc=self.FOUND_DESC_TYPE2_3,
            missing_desc=self.MISSING_DESC_TYPE2_3,
            found_reason=self.FOUND_REASON_TYPE2_3,
            missing_reason=self.MISSING_REASON_TYPE2_3
        )
    
    def _type2_core_logic(self) -> Tuple[Dict[str, Dict], Dict[str, Dict]]:
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
        
        # Check for expected LVS result status (EXACT MATCH)
        for pattern in pattern_items:
            matched = False
            for item in items:
                item_status = item.get('status', '')
                # EXACT MATCH: pattern_items contains expected status value (e.g., "MATCH")
                if pattern.upper() == item_status.upper():
                    found_items[item.get('name', pattern)] = {
                        'line_number': item.get('line_number', 0),
                        'file_path': item.get('file_path', 'N/A')
                    }
                    matched = True
                    break
            
            if not matched:
                missing_items[pattern] = {
                    'line_number': 0,
                    'file_path': 'N/A',
                    'reason': f'LVS run result pattern "{pattern}" not found'
                }
        
        return found_items, missing_items
    
    # =========================================================================
    # Type 3: Value Check with Waiver Logic
    # =========================================================================
    
    def _execute_type3(self) -> CheckResult:
        """Type 3: Pattern/value check with waiver support (reuses Type 2 core logic)."""
        found_items_base, violations = self._type2_core_logic()
        
        # FIXED: Use waivers.get('waive_items', []) instead of get_waive_items()
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        found_items = {}
        waived_items = {}
        missing_items = {}
        used_waivers = set()
        
        # Process found_items_base (no waiver needed)
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
        
        unused_waivers = [w for w in waive_dict.keys() if w not in used_waivers]
        
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
    
    # =========================================================================
    # Type 4: Boolean Check with Waiver Logic
    # =========================================================================
    
    def _execute_type4(self) -> CheckResult:
        """
        Type 4: Boolean check with waiver support (reuses Type 1 core logic).
        
        Same LVS MATCH check as Type 1, but violations can be waived.
        PASS if LVS result is MATCH OR violation is waived.
        """
        violations = self._type1_core_logic()
        
        # Build found_items from clean LVS results (MATCH status)
        data = self._parse_input_files()
        lvs_result = data.get('metadata', {}).get('run_result', '')
        
        found_items = {}
        if lvs_result == 'MATCH':
            # LVS passed - add as found item
            valid_files, _ = self.validate_input_files()
            found_items['Overall_Run_Result'] = {
                'name': 'Overall_Run_Result',
                'line_number': data.get('metadata', {}).get('result_line', 0),
                'file_path': str(valid_files[0]) if valid_files else 'N/A'
            }
        
        # FIXED: Use waivers.get('waive_items', []) instead of get_waive_items()
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
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
        
        unused_waivers = [w for w in waive_dict.keys() if w not in used_waivers]
        
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
# Entry Point
# =========================================================================

def main():
    """Main entry point."""
    checker = Check_11_0_0_01()
    checker.init_checker(Path(__file__))
    result = checker.execute_check()
    checker.write_output(result)
    return 0 if result.is_pass else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())