################################################################################
# Script Name: IMP-2-0-0-01.py
#
# Purpose:
#   List Innovus gdsout map name. eg: PRTF_Innovus_N3P_gdsout_17M_1Xa_h_1Xb_v_1Xc_h_1Xd_v_1Ya_h_1Yb_v_4Y_hvhv_2Yy2Yx2R_SHDMIM.10c.map
#
# Logic:
#   - Parse Innovus log file (do_innovusOUTwoD.logv) to extract GDS stream-out map file
#   - Search for streamOut command with -mapFile parameter containing PRTF*gdsout*.map
#   - Extract the map file path from the matched line
#   - For Type 1/4: Verify map file exists in log (boolean check)
#   - For Type 2/3: Compare extracted map file against golden configuration (pattern_items)
#   - Support waiver for map file mismatches (Type 3/4)
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
class Check_2_0_0_01(InputFileParserMixin, OutputBuilderMixin, WaiverHandlerMixin, BaseChecker):
    """
    IMP-2-0-0-01: List Innovus gdsout map name. eg: PRTF_Innovus_N3P_gdsout_17M_1Xa_h_1Xb_v_1Xc_h_1Xd_v_1Ya_h_1Yb_v_4Y_hvhv_2Yy2Yx2R_SHDMIM.10c.map
    
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
    FOUND_DESC_TYPE1_4 = "GDS stream-out map file found in Innovus log"
    MISSING_DESC_TYPE1_4 = "GDS stream-out map file not found in Innovus log"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_DESC_TYPE2_3 = "GDS stream-out map file matched expected configuration"
    MISSING_DESC_TYPE2_3 = "GDS stream-out map file does not match expected configuration"
    
    # All Types (waiver description unified)
    WAIVED_DESC = "GDS map file mismatch waived per design team approval"
    
    # ⭐ REASON CONSTANTS - Split by Type semantics (API-025)
    # ALL Types pass found_reason/missing_reason, but use different constants
    
    # Type 1/4: Boolean checks - emphasize "found/not found" (existence)
    FOUND_REASON_TYPE1_4 = "GDS map file path successfully extracted from streamOut command"
    MISSING_REASON_TYPE1_4 = "No streamOut command with PRTF gdsout map file found in log"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_REASON_TYPE2_3 = "GDS map file path matched golden configuration and validated"
    MISSING_REASON_TYPE2_3 = "GDS map file path does not match golden configuration - expected different map file"
    
    # Waiver-related (Type 3/4 only)
    WAIVED_BASE_REASON = "GDS map file mismatch waived - alternative map file approved for this design"
    UNUSED_WAIVER_REASON = "Waiver not matched - specified map file not found in streamOut command"
    
    def __init__(self):
        """Initialize the checker."""
        super().__init__(
            check_module="2.0_TECHFILE_AND_RULE_DECK_CHECK",
            item_id="IMP-2-0-0-01",
            item_desc="List Innovus gdsout map name. eg: PRTF_Innovus_N3P_gdsout_17M_1Xa_h_1Xb_v_1Xc_h_1Xd_v_1Ya_h_1Yb_v_4Y_hvhv_2Yy2Yx2R_SHDMIM.10c.map"
        )
        # Custom member variables for parsed data
        self._parsed_items: List[Dict[str, Any]] = []
        self._metadata: Dict[str, str] = {}
        self._gds_map_files: List[str] = []
    
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
        Parse Innovus log file to extract GDS stream-out map file information.
        
        Searches for streamOut command with -mapFile parameter containing PRTF*gdsout*.map pattern.
        Extracts the full map file path from the command line.
        
        Returns:
            Dict with parsed data:
            - 'items': List[Dict] - GDS map file entries with metadata
            - 'metadata': Dict - File metadata (tool version, date, etc.)
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
        gds_map_files = []
        
        # Pattern to extract GDS map file from streamOut command
        # Matches: streamOut ... -mapFile <path_to_PRTF*gdsout*.map> ...
        streamout_pattern = re.compile(
            r'streamOut\s+.*?-mapFile\s+([^\s]+PRTF[^\s]*gdsout[^\s]*\.map)',
            re.IGNORECASE
        )
        
        # Alternative pattern for any PRTF*gdsout*.map reference
        fallback_pattern = re.compile(
            r'([^\s/]+PRTF[^\s/]*gdsout[^\s/]*\.map)',
            re.IGNORECASE
        )
        
        # 3. Parse each input file for GDS map file information
        for file_path in valid_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line_num, line in enumerate(f, 1):
                        # Primary pattern: streamOut command with -mapFile
                        match = streamout_pattern.search(line)
                        if match:
                            map_file_path = match.group(1)
                            # Extract basename only (filename without directory)
                            map_file_name = Path(map_file_path).name
                            
                            # Avoid duplicates
                            if map_file_name not in gds_map_files:
                                gds_map_files.append(map_file_name)
                                items.append({
                                    'name': map_file_name,
                                    'full_path': map_file_path,
                                    'line_number': line_num,
                                    'file_path': str(file_path),
                                    'type': 'gdsout_map'
                                })
                        else:
                            # Fallback pattern: any PRTF*gdsout*.map reference
                            fallback_match = fallback_pattern.search(line)
                            if fallback_match:
                                map_file_name = fallback_match.group(1)
                                
                                # Avoid duplicates
                                if map_file_name not in gds_map_files:
                                    gds_map_files.append(map_file_name)
                                    items.append({
                                        'name': map_file_name,
                                        'full_path': map_file_name,
                                        'line_number': line_num,
                                        'file_path': str(file_path),
                                        'type': 'gdsout_map_fallback'
                                    })
            except Exception as e:
                errors.append(f"Error parsing {file_path}: {str(e)}")
        
        # 4. Store frequently reused data on self
        self._parsed_items = items
        self._gds_map_files = gds_map_files
        self._metadata = metadata
        
        return {
            'items': items,
            'metadata': metadata,
            'errors': errors
        }
    
    # =========================================================================
    # Type 1: Boolean Check
    # =========================================================================
    
    def _execute_type1(self) -> CheckResult:
        """Type 1: Boolean check without waiver support."""
        violations = self._type1_core_logic()
        
        # Build found_items from clean items (map files that were successfully extracted)
        data = self._parse_input_files()
        found_items = {}
        
        # If we found a valid map file, it goes to found_items
        if not violations and data.get('items'):
            for item in data['items']:
                item_name = item.get('name', 'GDS map file')
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
        """
        Core Type 1 boolean check logic (shared by Type 1 and Type 4).
        
        Returns:
            Dict of violations: {item_name: {'line_number': ..., 'file_path': ..., 'reason': ...}}
            Empty dict if all checks pass.
        """
        data = self._parse_input_files()
        items = data.get('items', [])
        errors = data.get('errors', [])
        
        violations = {}
        
        # Check for parsing errors first
        if errors:
            for error in errors:
                violations['GDS map file not found'] = {
                    'line_number': 0,
                    'file_path': 'N/A',
                    'reason': 'No streamOut command with PRTF gdsout map file found in log'
                }
            return violations
        
        # Check if no map file was found
        if not items:
            violations['GDS map file not found'] = {
                'line_number': 0,
                'file_path': 'N/A',
                'reason': 'No streamOut command with PRTF gdsout map file found in log'
            }
            return violations
        
        # If we reach here, map file was successfully extracted (no violations)
        return violations
    
    # =========================================================================
    # Type 4: Boolean Check with Waiver Logic
    # =========================================================================
    
    def _execute_type4(self) -> CheckResult:
        """Type 4: Boolean check with waiver support (reuses Type 1 core logic)."""
        # Step 1: Get violations using Type 1's core logic
        violations = self._type1_core_logic()
        
        # Build found_items from clean items (map files that were successfully extracted)
        data = self._parse_input_files()
        found_items = {}
        
        # If we found a valid map file, it goes to found_items
        if not violations and data.get('items'):
            for item in data['items']:
                item_name = item.get('name', 'GDS map file')
                found_items[item_name] = {
                    'name': item_name,
                    'line_number': item.get('line_number', 0),
                    'file_path': item.get('file_path', 'N/A')
                }
        
        # Step 2: Parse waiver configuration (FIXED: Use waivers.get() directly)
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
        
        # Step 5: Build output (FIXED: Pass dict directly, not list)
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
    
    def _type2_core_logic(self) -> Tuple[Dict[str, dict], Dict[str, dict]]:
        """
        Core Type 2 pattern matching logic (shared by Type 2 and Type 3).
        
        Returns:
            Tuple of (found_items, missing_items)
            - found_items: {map_file_path: {'line_number': ..., 'file_path': ...}}
            - missing_items: {pattern: {'line_number': 0, 'file_path': 'N/A', 'reason': ...}}
        """
        data = self._parse_input_files()
        items = data.get('items', [])
        
        requirements = self.item_data.get('requirements', {})
        pattern_items = requirements.get('pattern_items', [])
        
        found_items = {}
        missing_items = {}
        
        # Extract all GDS map file paths found in log
        for item in items:
            map_file_path = item.get('name', '')
            found_items[map_file_path] = {
                'line_number': item.get('line_number', 0),
                'file_path': item.get('file_path', 'N/A')
            }
        
        # Check if golden pattern_items are found
        for pattern in pattern_items:
            matched = False
            for item in items:
                map_file_path = item.get('name', '')
                # EXACT MATCH: pattern_items contain full absolute paths
                if pattern == map_file_path:
                    matched = True
                    break
            
            if not matched:
                missing_items[pattern] = {
                    'line_number': 0,
                    'file_path': 'N/A',
                    'reason': f'Golden map file path not found in streamOut command'
                }
        
        return found_items, missing_items
    
    # =========================================================================
    # Type 3: Value Check with Waiver Logic
    # =========================================================================
    
    def _execute_type3(self) -> CheckResult:
        """Type 3: Pattern/value check with waiver support (reuses Type 2 core logic)."""
        # Step 1: Get found/missing items using Type 2's core logic
        found_items_base, violations = self._type2_core_logic()
        
        # Step 2: Parse waiver configuration (FIXED: Use waivers.get() directly)
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # Step 3: Split items into found (matching golden), waived, and missing
        found_items = {}
        waived_items = {}
        missing_items = {}
        used_waivers = set()
        
        # Process found_items_base (items matching golden pattern_items)
        requirements = self.item_data.get('requirements', {})
        pattern_items = requirements.get('pattern_items', [])
        
        for item_name, item_data in found_items_base.items():
            # Check if this item matches golden pattern_items
            if item_name in pattern_items:
                found_items[item_name] = item_data
            else:
                # Item found but doesn't match golden - check if waived
                matched_waiver = self.match_waiver_entry(item_name, waive_dict)
                if matched_waiver:
                    waived_items[item_name] = item_data
                    used_waivers.add(matched_waiver)
                else:
                    missing_items[item_name] = item_data
        
        # Process violations (golden patterns not found)
        for viol_name, viol_data in violations.items():
            matched_waiver = self.match_waiver_entry(viol_name, waive_dict)
            if matched_waiver:
                waived_items[viol_name] = viol_data
                used_waivers.add(matched_waiver)
            else:
                missing_items[viol_name] = viol_data
        
        # Step 4: Find unused waivers
        unused_waivers = [w for w in waive_dict.keys() if w not in used_waivers]
        
        # Step 5: Build output (FIXED: Pass dict directly, not list)
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
    # Helper Methods (Optional - Add as needed)
    # =========================================================================
    
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
    checker = Check_2_0_0_01()
    checker.init_checker(Path(__file__))
    result = checker.execute_check()
    checker.write_output(result)
    return 0 if result.is_pass else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())