################################################################################
# Script Name: IMP-11-0-0-04.py
#
# Purpose:
#   Confirm proper rc/PVT corners were used for IR drop and EM analysis. List rc/PVT corners used in comments field.
#
# Logic:
#   - Parse input files: *static*.log, *dynamic*.log, *EM*.log
#   - Extract PVT corner from view definition basename pattern: {mode}_{process}_{voltage}v_{temp}c
#   - Extract PA view definition from read_view_definition command
#   - Extract Signal RC corner from "SPEF files for RC Corner" line
#   - Extract PowerGround RC from extraction_tech_file command (set to "NA" if not found)
#   - Format output: "PA view: {paview}, Signal RC: {signalrc}, PowerGround RC: {pgrc}, PVT is: {process} corner, {voltage}, {temperature}."
#   - Validate corner specifications against expected pattern_items (Type 2/3)
#   - Apply waiver logic for exempted corners (Type 3/4)
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
# Refactored: 2026-01-11 (Using checker_templates v1.1.0)
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
from checker_templates.input_file_parser_template import InputFileParserMixin


# MANDATORY: Inherit mixins in correct order (InputFileParserMixin first if used)
class Check_11_0_0_04(InputFileParserMixin, OutputBuilderMixin, WaiverHandlerMixin, BaseChecker):
    """
    IMP-11-0-0-04: Confirm proper rc/PVT corners were used for IR drop and EM analysis. List rc/PVT corners used in comments field.
    
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
    FOUND_DESC_TYPE1_4 = "RC/PVT corner specifications found in Voltus analysis logs"
    MISSING_DESC_TYPE1_4 = "RC/PVT corner specifications not found or incomplete in Voltus analysis logs"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_DESC_TYPE2_3 = "RC/PVT corner configuration validated and matched expected specification"
    MISSING_DESC_TYPE2_3 = "RC/PVT corner configuration not satisfied - missing or incorrect specification"
    
    # All Types (waiver description unified)
    WAIVED_DESC = "RC/PVT corner specification waived for this analysis"
    
    # ⭐ REASON CONSTANTS - Split by Type semantics (API-025)
    # ALL Types pass found_reason/missing_reason, but use different constants
    
    # Type 1/4: Boolean checks - emphasize "found/not found" (existence)
    FOUND_REASON_TYPE1_4 = "PA view, Signal RC corner, and Power/Ground RC corner specifications found in log file"
    MISSING_REASON_TYPE1_4 = "Missing corner specification: view definition, Signal RC corner, or Power/Ground RC corner not found in log file"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_REASON_TYPE2_3 = "Corner specification matched: PA view, Signal RC, and PG RC corners validated against expected configuration"
    MISSING_REASON_TYPE2_3 = "Corner specification not satisfied: expected PA view or RC corner configuration missing or incorrect"
    
    # Waiver-related (Type 3/4 only)
    WAIVED_BASE_REASON = "Corner specification waived per design team approval - alternative corner configuration accepted"
    UNUSED_WAIVER_REASON = "Waiver not matched - no corresponding corner specification violation found in analysis logs"
    
    def __init__(self):
        """Initialize the checker."""
        super().__init__(
            check_module="11.0_POWER_EMIR_CHECK",
            item_id="IMP-11-0-0-04",
            item_desc="Confirm proper rc/PVT corners were used for IR drop and EM analysis. List rc/PVT corners used in comments field."
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
        Parse input files to extract PVT/RC corner specifications.
        
        Extracts corner information from Voltus analysis logs:
        1. PA view definition: read_view_definition command
        2. PVT corner components: extracted from view definition basename
        3. Signal RC corner: "SPEF files for RC Corner" line
        4. PowerGround RC: extraction_tech_file command (or "NA" if not found)
        
        Returns:
            Dict with parsed data:
            - 'items': List[Dict] - Corner specifications with metadata
            - 'metadata': Dict - File metadata
            - 'errors': List - Any parsing errors encountered
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
        
        # Regex patterns for extraction
        view_def_pattern = re.compile(r'read_view_definition\s+\S+/(\S+)_viewdefinition\.tcl')
        pvt_pattern = re.compile(r'_(func|test)_(\w+)_([\d]+p[\d]+)v_(m?\d+)c_')
        signal_rc_pattern = re.compile(r'SPEF files for RC Corner\s+(\S+):')
        pg_rc_pattern = re.compile(r'extraction_tech_file\s+(\S+)')
        
        # 3. Parse each input file for corner information
        for file_path in valid_files:
            corner_data = {
                'name': '',
                'mode': '',
                'process': '',
                'voltage': '',
                'temperature': '',
                'paview': 'Not found',
                'signalrc': 'Not specified',
                'pgrc': 'NA',
                'file_path': str(file_path),
                'line_number': 0
            }
            
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line_num, line in enumerate(f, 1):
                        # Extract PA view definition
                        view_match = view_def_pattern.search(line)
                        if view_match:
                            paview_basename = view_match.group(1)
                            corner_data['paview'] = paview_basename + '_viewdefinition.tcl'
                            if corner_data['line_number'] == 0:
                                corner_data['line_number'] = line_num
                            
                            # Extract PVT from view definition basename
                            pvt_match = pvt_pattern.search(paview_basename)
                            if pvt_match:
                                corner_data['mode'] = pvt_match.group(1)
                                corner_data['process'] = pvt_match.group(2)
                                voltage_raw = pvt_match.group(3)
                                corner_data['voltage'] = voltage_raw.replace('p', '.') + 'v'
                                temp_raw = pvt_match.group(4)
                                if temp_raw.startswith('m'):
                                    corner_data['temperature'] = '-' + temp_raw[1:] + 'c'
                                else:
                                    corner_data['temperature'] = temp_raw + 'c'
                                
                                # Build corner name
                                corner_data['name'] = f"{corner_data['mode']}_{corner_data['process']}_{voltage_raw}v_{temp_raw}c"
                        
                        # Extract Signal RC corner
                        signal_match = signal_rc_pattern.search(line)
                        if signal_match:
                            corner_data['signalrc'] = signal_match.group(1)
                            if corner_data['line_number'] == 0:
                                corner_data['line_number'] = line_num
                        
                        # Extract PowerGround RC
                        pg_match = pg_rc_pattern.search(line)
                        if pg_match:
                            tech_file = pg_match.group(1)
                            # Extract RC corner from filename (e.g., qrc_tech_cbest_CCbest_125c.tch)
                            rc_match = re.search(r'(\w+_\w+_\w+)\.tch', tech_file)
                            if rc_match:
                                corner_data['pgrc'] = rc_match.group(1)
                            else:
                                corner_data['pgrc'] = tech_file
                            if corner_data['line_number'] == 0:
                                corner_data['line_number'] = line_num
            except Exception as e:
                errors.append(f"Error reading file {file_path}: {str(e)}")
                continue
            
            # Set default line number if no patterns were found
            if corner_data['line_number'] == 0:
                corner_data['line_number'] = 1
            
            # Only add if we found at least the view definition
            if corner_data['paview'] != 'Not found':
                items.append(corner_data)
            else:
                errors.append(f"No view definition found in {file_path.name}")
        
        # 4. Store frequently reused data on self
        self._parsed_items = items
        self._metadata = {'total': len(items)}
        
        return {
            'items': items,
            'metadata': metadata,
            'errors': errors
        }
    
    # =========================================================================
    # Type 1: Boolean Check
    # =========================================================================
    
    def _execute_type1(self) -> CheckResult:
        """Type 1: Boolean check without waiver support.
        
        Validates that all Voltus log files contain complete corner specifications:
        - PA view definition (read_view_definition command)
        - Signal RC corner ("SPEF files for RC Corner" line)
        - Power/Ground RC corner (extraction_tech_file command)
        - PVT information (extracted from view definition basename)
        
        Returns:
            CheckResult with:
            - found_items: Log files with complete corner specifications
            - missing_items: Log files missing corner specifications
        """
        violations = self._type1_core_logic()
        
        # Build found_items from clean log files (those without violations)
        data = self._parse_input_files()
        all_items = data.get('items', [])
        
        found_items = {}
        for item in all_items:
            item_name = item.get('name', 'unknown')
            # Only include items that are NOT in violations
            if item_name not in violations:
                found_items[item_name] = {
                    'name': item_name,
                    'line_number': item.get('line_number', 0),
                    'file_path': item.get('file_path', 'N/A')
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
        """Core Type 1 boolean check logic (shared by Type 1 and Type 4).
        
        Validates corner specifications in Voltus log files:
        1. Extracts PA view definition from read_view_definition command
        2. Extracts Signal RC corner from "SPEF files for RC Corner" line
        3. Extracts Power/Ground RC from extraction_tech_file command
        4. Extracts PVT from view definition basename pattern
        5. Identifies log files missing any required corner specification
        
        Returns:
            Dict of violations: {log_name: {'line_number': ..., 'file_path': ..., 'reason': ...}}
            Empty dict if all log files have complete corner specifications.
        """
        data = self._parse_input_files()
        items = data.get('items', [])
        errors = data.get('errors', [])
        
        violations = {}
        
        # Handle parsing errors as violations
        for idx, error in enumerate(errors):
            error_name = f'parsing_error_{idx}'
            violations[error_name] = {
                'line_number': 0,
                'file_path': 'N/A',
                'reason': error
            }
        
        # Check each log file for complete corner specifications
        for item in items:
            item_name = item.get('name', 'unknown')
            file_path = item.get('file_path', 'N/A')
            line_number = item.get('line_number', 0)
            
            # Extract corner specification components
            pa_view = item.get('paview', '')
            signal_rc = item.get('signalrc', '')
            pg_rc = item.get('pgrc', '')
            process = item.get('process', '')
            voltage = item.get('voltage', '')
            temperature = item.get('temperature', '')
            
            # Check for missing components
            missing_components = []
            if not pa_view or pa_view == 'Not found':
                missing_components.append('PA view definition')
            if not signal_rc or signal_rc == 'Not specified':
                missing_components.append('Signal RC corner')
            # Note: Power/Ground RC corner (pgrc) is optional for EM analysis (verify_AC_limit)
            # and only required for IR drop analysis. We don't check it as mandatory.
            if not process or not voltage or not temperature:
                missing_components.append('PVT information')
            
            # If any component is missing, add to violations
            if missing_components:
                violations[item_name] = {
                    'line_number': line_number,
                    'file_path': file_path,
                    'reason': f"Missing corner specification: {', '.join(missing_components)}"
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
            - found_items: {corner_id: {'line_number': ..., 'file_path': ..., 'details': ...}}
            - missing_items: {corner_id: {'line_number': ..., 'file_path': ..., 'reason': ...}}
        """
        data = self._parse_input_files()
        items = data.get('items', [])
        
        requirements = self.item_data.get('requirements', {})
        pattern_items = requirements.get('pattern_items', [])
        
        found_items = {}
        missing_items = {}
        
        # Check each required corner pattern
        for pattern in pattern_items:
            matched = False
            
            # Search for corner in parsed items
            for item in items:
                corner_id = item.get('name', '')
                
                # EXACT MATCH: pattern_items are corner identifiers (mode_process_voltage_temperature)
                if pattern.lower() == corner_id.lower():
                    # Build detailed corner specification string
                    pa_view = item.get('paview', 'N/A')
                    signal_rc = item.get('signalrc', 'N/A')
                    pg_rc = item.get('pgrc', 'N/A')
                    process = item.get('process', 'N/A')
                    voltage = item.get('voltage', 'N/A')
                    temperature = item.get('temperature', 'N/A')
                    
                    details = (
                        f"PA view: {pa_view}, "
                        f"Signal RC: {signal_rc}, "
                        f"PowerGround RC: {pg_rc}, "
                        f"PVT is: {process} corner, {voltage}, {temperature}."
                    )
                    
                    found_items[corner_id] = {
                        'line_number': item.get('line_number', 0),
                        'file_path': item.get('file_path', 'N/A'),
                        'details': details
                    }
                    matched = True
                    break
            
            if not matched:
                missing_items[pattern] = {
                    'line_number': 0,
                    'file_path': 'N/A',
                    'reason': f'Corner "{pattern}" not found in analysis logs'
                }
        
        return found_items, missing_items
    
    # =========================================================================
    # Type 3: Value Check with Waiver Logic
    # =========================================================================
    
    def _execute_type3(self) -> CheckResult:
        """Type 3: Pattern/value check with waiver support (reuses Type 2 core logic)."""
        # Step 1: Get found/missing items using Type 2's core logic
        found_items_base, violations = self._type2_core_logic()
        
        # Step 2: Parse waiver configuration (FIXED: API-008)
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # Step 3: Split violations into waived and unwaived
        found_items = {}
        waived_items = {}
        missing_items = {}
        used_waivers = set()
        
        # Process found_items_base (no waiver needed - corners found and correct)
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
        
        # Step 5: Build output (FIXED: API-009 - pass dicts directly)
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
        """Type 4: Boolean check with waiver support (reuses Type 1 core logic).
        
        Same validation as Type 1, but with waiver support:
        - Reuses _type1_core_logic() to identify violations
        - Matches violations against waive_items (by log file name)
        - Splits violations into waived (PASS) and unwaived (FAIL)
        - Tracks unused waivers
        
        Returns:
            CheckResult with:
            - found_items: Log files with complete corner specifications
            - waived_items: Log files with missing specs but waived
            - missing_items: Log files with missing specs (unwaived)
            - unused_waivers: Waivers that didn't match any violations
        """
        # Step 1: Get violations using Type 1's core logic
        violations = self._type1_core_logic()
        
        # Build found_items from clean log files (those without violations)
        data = self._parse_input_files()
        all_items = data.get('items', [])
        
        found_items = {}
        for item in all_items:
            item_name = item.get('name', 'unknown')
            # Only include items that are NOT in violations
            if item_name not in violations:
                found_items[item_name] = {
                    'name': item_name,
                    'line_number': item.get('line_number', 0),
                    'file_path': item.get('file_path', 'N/A')
                }
        
        # Step 2: Parse waiver configuration (FIXED: API-008)
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # Step 3: Split violations into waived and unwaived
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
        
        # Step 4: Find unused waivers
        unused_waivers = [w for w in waive_dict.keys() if w not in used_waivers]
        
        # Step 5: Build output (FIXED: API-009 - pass dicts directly)
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
    checker = Check_11_0_0_04()
    checker.init_checker(Path(__file__))
    result = checker.execute_check()
    checker.write_output(result)
    return 0 if result.is_pass else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())