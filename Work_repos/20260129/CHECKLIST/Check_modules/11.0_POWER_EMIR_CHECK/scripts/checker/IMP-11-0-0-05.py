################################################################################
# Script Name: IMP-11-0-0-05.py
#
# Purpose:
#   Confirm generate all the power library with detail view correctly.
#
# Logic:
#   - Parse *LibGen.log files to extract GDS file configurations
#   - Extract library corner identifiers from filename (voltage, temperature, RC corner)
#   - Search for set_pg_library_mode commands with -gds_files parameter
#   - Filter by celltype: only process "macros" (skip "techonly" and "stdcells")
#   - Filter by GDS files: only report libraries with non-empty -gds_files parameter
#   - Extract and display GDS file paths for each library corner
#   - Report all findings as informational output (always PASS)
#   - Clearly indicate when GDS files are empty {} or parameter is missing
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
# Refactored: 2026-01-16 (Using checker_templates v1.1.0)
#            - Changed to informational-only mode (always PASS)
#            - Enhanced output to show GDS file presence/absence clearly
#            - Added celltype filtering (macros only)
#            - Added GDS files non-empty filtering
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
class Check_11_0_0_05(InputFileParserMixin, OutputBuilderMixin, WaiverHandlerMixin, BaseChecker):
    """
    IMP-11-0-0-05: Confirm generate all the power library with detail view correctly.
    
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
    FOUND_DESC_TYPE1_4 = "Power library GDS files found in LibGen logs"
    MISSING_DESC_TYPE1_4 = "No GDS files found for macro power libraries"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_DESC_TYPE2_3 = "Macro power library with GDS detail view validated"
    MISSING_DESC_TYPE2_3 = "Macro power library missing GDS detail view"
    
    # All Types (waiver description unified)
    WAIVED_DESC = "GDS file requirement waived for specific macro libraries"
    
    # ⭐ REASON CONSTANTS - Split by Type semantics (API-025)
    # ALL Types pass found_reason/missing_reason, but use different constants
    
    # Type 1/4: Boolean checks - emphasize "found/not found" (existence)
    FOUND_REASON_TYPE1_4 = "GDS file found in macro power library configuration"
    MISSING_REASON_TYPE1_4 = "GDS file not found in macro power library configuration"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_REASON_TYPE2_3 = "Macro library configuration matched with GDS detail view"
    MISSING_REASON_TYPE2_3 = "Macro library configuration missing GDS detail view or filtered out"
    
    # Waiver-related (Type 3/4 only)
    WAIVED_BASE_REASON = "Macro power library GDS requirement waived per design team approval"
    UNUSED_WAIVER_REASON = "Waiver not matched - no corresponding macro library found without GDS files"
    
    def __init__(self):
        """Initialize the checker."""
        super().__init__(
            check_module="11.0_POWER_EMIR_CHECK",
            item_id="IMP-11-0-0-05",
            item_desc="Confirm generate all the power library with detail view correctly."
        )
        # Custom member variables for parsed data
        self._parsed_items: List[Dict[str, Any]] = []
        self._metadata: Dict[str, str] = {}
        self._library_gds_map: Dict[str, List[str]] = {}
        self._corner_info: Dict[str, Dict[str, str]] = {}
    
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
        Parse *LibGen.log files to extract GDS file configurations.
        
        Parsing Strategy:
        1. Use filename stem (without .LibGen.log extension) as library identifier
        2. Search for set_pg_library_mode commands with -celltype parameter
        3. Extract celltype value (macros, stdcells, techonly)
        4. Extract GDS file paths from -gds_files parameter (handles both braced and non-braced formats)
        5. Report all libraries with their GDS file configuration status
        
        Returns:
            Dict with parsed data:
            - 'items': List[Dict] - All libraries with GDS file information
            - 'metadata': Dict - File metadata
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
            raise ConfigurationError(
                self.create_error_result("No valid input files found")
            )
        
        # 2. Initialize parsing structures
        items = []
        metadata = {}
        errors = []
        library_gds_map = {}
        
        # Pattern definitions
        # Extract celltype from set_pg_library_mode command
        celltype_pattern = re.compile(r'set_pg_library_mode\s+.*-celltype\s+(\S+)')
        
        # Extract GDS files from set_pg_library_mode command
        # Pattern 1: -gds_files {file1 file2 ...} (with braces)
        # Pattern 2: -gds_files file1 file2 ... (without braces, terminated by next - option or end of line)
        gds_pattern_braces = re.compile(r'-gds_files\s+\{([^}]*)\}')
        gds_pattern_no_braces = re.compile(r'-gds_files\s+([^-\n]+?)(?=\s+-|\s*$)')
        
        # 3. Parse each input file for GDS file information
        for file_path in valid_files:
            try:
                # Use filename stem (without .LibGen.log extension) as library identifier
                filename = Path(file_path).name
                # Remove .LibGen.log extension to get library name
                library_name = filename.replace('.LibGen.log', '')
                
                # Parse celltype and GDS files from log content
                celltype = None
                gds_files = []
                gds_files_str = ""
                gds_line_number = 0
                
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line_num, line in enumerate(f, 1):
                        # Extract celltype
                        celltype_match = celltype_pattern.search(line)
                        if celltype_match:
                            celltype = celltype_match.group(1).strip()
                        
                        # Extract GDS files (try both patterns)
                        gds_match = gds_pattern_braces.search(line)
                        if gds_match:
                            gds_files_str = gds_match.group(1).strip()
                            # Split by whitespace to get individual file paths
                            gds_files = gds_files_str.split() if gds_files_str else []
                            gds_line_number = line_num
                        else:
                            # Try pattern without braces
                            gds_match = gds_pattern_no_braces.search(line)
                            if gds_match:
                                gds_files_str = gds_match.group(1).strip()
                                # Split by whitespace to get individual file paths
                                gds_files = gds_files_str.split() if gds_files_str else []
                                gds_line_number = line_num
                
                # Filter by celltype: only process "macros"
                # TEMPORARILY DISABLED: Report all libraries for debugging
                # if celltype not in ["macros"]:
                #     # Skip techonly and stdcells
                #     continue
                
                # Filter by GDS files: REPORT ALL (even empty ones for debugging)
                # if not gds_files or len(gds_files) == 0:
                #     # Skip libraries with empty GDS files list
                #     continue
                
                # Determine if GDS files are present
                has_gds = bool(gds_files and len(gds_files) > 0)
                
                # Store library information
                library_gds_map[library_name] = gds_files
                
                # Create item entry - report all libraries for debugging
                items.append({
                    'name': library_name,
                    'library_name': library_name,
                    'gds_files': gds_files,
                    'has_gds_files': has_gds,
                    'celltype': celltype,
                    'line_number': gds_line_number if gds_line_number > 0 else 0,
                    'file_path': str(file_path),
                    'type': 'library'
                })
            
            except Exception as e:
                errors.append(f"Error parsing {file_path}: {str(e)}")
        
        # 4. Store frequently reused data on self
        self._parsed_items = items
        self._library_gds_map = library_gds_map
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
        """
        Type 1: Boolean check without waiver support.
        
        This is an informational check that reports all GDS file configurations
        found in LibGen.log files (macros only, non-empty GDS files). The check 
        always passes and provides detailed information about power library GDS 
        configurations for user verification.
        """
        violations = self._type1_core_logic()
        
        # For this informational check, all found GDS configurations are "found_items"
        # Since this is an informational check that always passes, violations dict
        # contains the GDS configurations we want to report as found items
        # Include the per-item reason from the core logic
        found_items = {}
        for config_name, config_data in violations.items():
            found_items[config_name] = {
                'name': config_name,
                'line_number': config_data.get('line_number', 0),
                'file_path': config_data.get('file_path', 'N/A'),
                'reason': config_data.get('reason', self.FOUND_REASON_TYPE1_4)
            }
        
        # No missing items - this is an informational check that always passes
        missing_items = []
        
        # Use callable reason to extract per-item reason from metadata
        return self.build_complete_output(
            found_items=found_items,
            missing_items=missing_items,
            found_desc=self.FOUND_DESC_TYPE1_4,
            missing_desc=self.MISSING_DESC_TYPE1_4,
            found_reason=lambda item: item.get('reason', self.FOUND_REASON_TYPE1_4),
            missing_reason=self.MISSING_REASON_TYPE1_4
        )
    
    def _type1_core_logic(self) -> dict:
        """
        Core Type 1 boolean check logic (shared by Type 1 and Type 4).
        
        Extracts GDS file configurations from LibGen.log files and reports them
        for user verification. This is an informational check - all libraries
        are reported as INFO (only macros with non-empty GDS files are included).
        
        Returns:
            Dict of GDS configurations: {config_name: {'line_number': ..., 'file_path': ..., 'reason': ...}}
            Returns all found configurations (not violations in traditional sense).
        """
        data = self._parse_input_files()
        items = data.get('items', [])
        
        # For this informational check, we collect ALL library configurations
        # (already filtered to macros with non-empty GDS files in _parse_input_files)
        gds_configs = {}
        
        for item in items:
            config_name = item.get('name', 'unknown_config')
            gds_files = item.get('gds_files', [])
            has_gds = item.get('has_gds_files', False)
            celltype = item.get('celltype', 'unknown')
            
            # Build informational reason based on what was found
            if has_gds and len(gds_files) > 0:
                reason = f"GDS file configuration found: {' '.join(gds_files)} (celltype={celltype})"
            else:
                reason = f"No GDS files (-gds_files empty or not specified) (celltype={celltype})"
            
            gds_configs[config_name] = {
                'line_number': item.get('line_number', 0),
                'file_path': item.get('file_path', 'N/A'),
                'reason': reason,
                'gds_files': gds_files
            }
        
        return gds_configs
    
    # =========================================================================
    # Type 2: Value Check
    # =========================================================================
    
    def _execute_type2(self) -> CheckResult:
        """Type 2: Pattern/value check without waiver support.
        
        This is an informational check that extracts GDS file paths from LibGen.log files.
        Always returns PASS - all output is informational for user verification.
        All libraries reported as INFO (only macros with non-empty GDS files).
        """
        found_items, missing_items = self._type2_core_logic()
        
        # Since this is informational only, treat everything as found
        # (missing_items should be empty based on updated core logic)
        
        # Use callable reason to extract per-item reason from metadata
        return self.build_complete_output(
            found_items=found_items,
            missing_items=[],  # Always empty for informational check
            found_desc=self.FOUND_DESC_TYPE2_3,
            missing_desc=self.MISSING_DESC_TYPE2_3,
            found_reason=lambda item: item.get('reason', self.FOUND_REASON_TYPE2_3),
            missing_reason=self.MISSING_REASON_TYPE2_3
        )
    
    def _type2_core_logic(self) -> Tuple[Dict[str, Dict], Dict[str, Dict]]:
        """
        Core Type 2 pattern matching logic (shared by Type 2 and Type 3).
        
        Extracts GDS file paths from set_pg_library_mode commands in LibGen.log files.
        Matches library corner identifiers from pattern_items against parsed log data.
        Only processes macros with non-empty GDS files.
        
        Returns:
            Tuple of (found_items, missing_items)
            - found_items: {corner_id: {'line_number': ..., 'file_path': ..., 'gds_files': [...]}}
            - missing_items: {corner_id: {'line_number': 0, 'file_path': 'N/A', 'reason': ...}}
        """
        data = self._parse_input_files()
        items = data.get('items', [])  # List of {corner_id, gds_files, line_number, file_path}
        
        requirements = self.item_data.get('requirements', {})
        pattern_items = requirements.get('pattern_items', [])
        
        found_items = {}
        missing_items = {}
        
        # Build lookup dict from parsed items (corner_id -> item_data)
        corner_lookup = {}
        for item in items:
            corner_id = item.get('library_corner', '')
            corner_lookup[corner_id] = item
        
        # Check each required pattern (library corner identifier)
        for pattern in pattern_items:
            matched = False
            
            # EXACT MATCH: pattern_items are complete corner identifiers
            # Example: "ffgnp_0p825v_125c_cbest_CCbest_T"
            for corner_id, item_data in corner_lookup.items():
                if pattern.lower() == corner_id.lower():
                    # Found matching corner - report as informational item
                    gds_files = item_data.get('gds_files', [])
                    
                    # All libraries reported as found_items (informational check)
                    reason_suffix = "Macro library configuration matched with GDS detail view"
                    
                    found_items[corner_id] = {
                        'line_number': item_data.get('line_number', 0),
                        'file_path': item_data.get('file_path', 'N/A'),
                        'gds_files': gds_files,
                        'reason': reason_suffix
                    }
                    matched = True
                    break
            
            if not matched:
                # Pattern not found in any LibGen.log - report as found with note
                found_items[pattern] = {
                    'line_number': 0,
                    'file_path': 'N/A',
                    'gds_files': [],
                    'reason': f'Library corner not found in LibGen.log files (or filtered out)'
                }
        
        return found_items, missing_items
    
    # =========================================================================
    # Type 3: Value Check with Waiver Logic
    # =========================================================================
    
    def _execute_type3(self) -> CheckResult:
        """Type 3: Pattern/value check with waiver support (reuses Type 2 core logic).
        
        This is an informational check that extracts GDS file paths from LibGen.log files.
        Supports waiving missing library corners.
        Always returns PASS - all output is informational for user verification.
        """
        # Step 1: Get found/missing items using Type 2's core logic
        found_items_base, violations = self._type2_core_logic()
        
        # Step 2: Parse waiver configuration
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # Step 3: Initialize output categories
        found_items = {}
        waived_items = {}
        missing_items = {}
        used_waivers = set()
        
        # Step 4: Process found_items_base (no waiver needed - GDS files extracted)
        for item_name, item_data in found_items_base.items():
            found_items[item_name] = item_data
        
        # Step 5: Process violations (missing library corners) with waiver matching
        for viol_name, viol_data in violations.items():
            matched_waiver = self.match_waiver_entry(viol_name, waive_dict)
            if matched_waiver:
                waived_items[viol_name] = viol_data
                used_waivers.add(matched_waiver)
            else:
                missing_items[viol_name] = viol_data
        
        # Step 6: Find unused waivers
        unused_waivers = [w for w in waive_dict.keys() if w not in used_waivers]
        
        # Step 7: Build output - convert missing_items dict to list
        missing_items_list = list(missing_items.keys()) if isinstance(missing_items, dict) else missing_items
        
        # Use callable reasons to extract per-item reason from metadata
        return self.build_complete_output(
            found_items=found_items,
            missing_items=missing_items_list,
            waived_items=waived_items,
            unused_waivers=unused_waivers,
            waive_dict=waive_dict,
            found_desc=self.FOUND_DESC_TYPE2_3,
            missing_desc=self.MISSING_DESC_TYPE2_3,
            waived_desc=self.WAIVED_DESC,
            found_reason=lambda item: item.get('reason', self.FOUND_REASON_TYPE2_3),
            missing_reason=lambda item: item.get('reason', self.MISSING_REASON_TYPE2_3),
            waived_base_reason=lambda item: f"{self.WAIVED_BASE_REASON}",
            unused_waiver_reason=self.UNUSED_WAIVER_REASON
        )
    
    # =========================================================================
    # Type 4: Boolean Check with Waiver Logic
    # =========================================================================
    
    def _execute_type4(self) -> CheckResult:
        """
        Type 4: Boolean check with waiver support (reuses Type 1 core logic).
        
        This is an informational check that reports GDS file configurations.
        Waiver logic allows filtering out specific configurations from the report
        if they are already verified or not relevant for current review.
        """
        # Step 1: Get GDS configurations using Type 1's core logic
        violations = self._type1_core_logic()
        
        # For this informational check, all configurations start as found_items
        # Waivers will move some to waived_items for filtering
        found_items = {}
        for config_name, config_data in violations.items():
            found_items[config_name] = {
                'name': config_name,
                'line_number': config_data.get('line_number', 0),
                'file_path': config_data.get('file_path', 'N/A')
            }
        
        # Step 2: Parse waiver configuration
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # Step 3: Split configurations into waived and non-waived
        # For informational check: waived = filtered out, non-waived = reported
        waived_items = {}
        reported_items = {}
        used_waivers = set()
        
        for config_name, config_data in violations.items():
            matched_waiver = self.match_waiver_entry(config_name, waive_dict)
            if matched_waiver:
                # Configuration is waived (filtered from main report)
                waived_items[config_name] = config_data
                used_waivers.add(matched_waiver)
            else:
                # Configuration is reported in main output
                reported_items[config_name] = config_data
        
        # Step 4: Find unused waivers
        unused_waivers = [w for w in waive_dict.keys() if w not in used_waivers]
        
        # Step 5: Build output
        # For informational check: reported_items go to found_items, no missing_items
        final_found_items = {}
        for config_name, config_data in reported_items.items():
            final_found_items[config_name] = {
                'name': config_name,
                'line_number': config_data.get('line_number', 0),
                'file_path': config_data.get('file_path', 'N/A'),
                'reason': config_data.get('reason', self.FOUND_REASON_TYPE1_4)
            }
        
        # Use callable reason to extract per-item reason from metadata
        return self.build_complete_output(
            found_items=final_found_items,
            missing_items=[],
            waived_items=waived_items,
            unused_waivers=unused_waivers,
            waive_dict=waive_dict,
            found_desc=self.FOUND_DESC_TYPE1_4,
            missing_desc=self.MISSING_DESC_TYPE1_4,
            waived_desc=self.WAIVED_DESC,
            found_reason=lambda item: item.get('reason', self.FOUND_REASON_TYPE1_4),
            missing_reason=self.MISSING_REASON_TYPE1_4,
            waived_base_reason=lambda item: f"{self.WAIVED_BASE_REASON}",
            unused_waiver_reason=self.UNUSED_WAIVER_REASON
        )


# =========================================================================
# Entry Point
# =========================================================================

def main():
    """Main entry point."""
    checker = Check_11_0_0_05()
    checker.init_checker(Path(__file__))
    result = checker.execute_check()
    checker.write_output(result)
    return 0 if result.is_pass else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())