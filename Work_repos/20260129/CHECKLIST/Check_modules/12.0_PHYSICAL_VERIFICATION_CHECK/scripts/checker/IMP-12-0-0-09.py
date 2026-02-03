################################################################################
# Script Name: IMP-12-0-0-09.py
#
# Purpose:
#   Confirm the LVS rule deck setting is correct.
#
# Logic:
#   - Parse PVL log file to extract #DEFINE statements (actual configuration)
#   - Parse sourceme file to extract #define statements (intended configuration)
#   - PVL log settings ALWAYS override sourceme settings (higher priority)
#   - Extract POWER_NAME and GROUND_NAME lists from sourceme
#   - Compare actual configuration against expected pattern_items
#   - Verify each flag's state (enabled/disabled) matches expected value
#   - Support waiver for configuration mismatches
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
# Author: Jingyu Wang
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
class Check_12_0_0_09(InputFileParserMixin, OutputBuilderMixin, WaiverHandlerMixin, BaseChecker):
    """
    IMP-12-0-0-09: Confirm the LVS rule deck setting is correct.
    
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
    FOUND_DESC_TYPE1_4 = "LVS rule deck configuration validated successfully"
    MISSING_DESC_TYPE1_4 = "LVS rule deck configuration validation failed"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_DESC_TYPE2_3 = "LVS rule deck setting matched expected configuration"
    MISSING_DESC_TYPE2_3 = "LVS rule deck setting does not match expected configuration"
    
    # All Types (waiver description unified)
    WAIVED_DESC = "LVS rule deck setting mismatch waived"
    
    # ⭐ REASON CONSTANTS - Split by Type semantics (API-025)
    # ALL Types pass found_reason/missing_reason, but use different constants
    
    # Type 1/4: Boolean checks - emphasize "found/not found" (existence)
    FOUND_REASON_TYPE1_4 = "All LVS configuration flags found with correct states in rule deck files"
    MISSING_REASON_TYPE1_4 = "Required LVS configuration flag not found or has incorrect state in rule deck files"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_REASON_TYPE2_3 = "LVS configuration flag matched expected state (enabled/disabled as required)"
    MISSING_REASON_TYPE2_3 = "LVS configuration flag state mismatch - expected: {expected}, actual: {actual}"
    
    # Waiver-related (Type 3/4 only)
    WAIVED_BASE_REASON = "LVS configuration mismatch waived per design team approval"
    UNUSED_WAIVER_REASON = "Waiver defined but no violation matched"
    
    def __init__(self):
        """Initialize the checker."""
        super().__init__(
            check_module="12.0_PHYSICAL_VERIFICATION_CHECK",
            item_id="IMP-12-0-0-09",
            item_desc="Confirm the LVS rule deck setting is correct."
        )
        # Custom member variables for parsed data
        self._parsed_items: List[Dict[str, Any]] = []
        self._metadata: Dict[str, str] = {}
        self._config_registry: Dict[str, str] = {}
    
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
        Parse input files to extract LVS rule deck configuration settings.
        
        Parses two file types:
        1. PVL log file (.pvl) - Contains actual configuration (#DEFINE statements)
        2. Sourceme file - Contains intended configuration (#define statements)
        
        PVL log settings ALWAYS override sourceme settings (higher priority).
        
        Returns:
            Dict with parsed data:
            - 'items': List[Dict] - Configuration flags with expected vs actual state
            - 'metadata': Dict - File metadata (design name, tool version, etc.)
            - 'errors': List - Parsing errors
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
        config_registry = {}  # Stores flag_name -> state (enabled/disabled)
        
        # Separate files by type
        pvl_files = []
        sourceme_files = []
        
        for file_path in valid_files:
            file_name = file_path.name.lower()
            if '.pvl' in file_name or 'do_pvs_lvs' in file_name:
                pvl_files.append(file_path)
            elif 'sourceme' in file_name or 'do_cmd' in file_name:
                sourceme_files.append(file_path)
        
        # 3. Parse sourceme files first (lower priority)
        for file_path in sourceme_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line_num, line in enumerate(f, 1):
                        # Pattern 2: Enabled #define statements
                        match = re.match(r'^\s*#define\s+(\w+)\s*(?://.*)?$', line)
                        if match:
                            flag_name = match.group(1)
                            config_registry[flag_name] = 'enabled'
                            continue
                        
                        # Pattern 3: Commented out #define (disabled)
                        match = re.match(r'^\s*//\s*#define\s+(\w+)\s*(?://.*)?$', line)
                        if match:
                            flag_name = match.group(1)
                            config_registry[flag_name] = 'disabled'
                            continue
                        
                        # Pattern 4: VARIABLE declarations (Calibre LVS format)
                        # Format: VARIABLE VAR_NAME "value1" "value2" ...
                        match = re.match(r'^\s*VARIABLE\s+(\w+)\s+(.+?)(?:\s*//.*)?$', line, re.IGNORECASE)
                        if match:
                            var_name = match.group(1)
                            var_values_str = match.group(2)
                            # Extract values (strip quotes from each value)
                            var_values = [v.strip('"') for v in var_values_str.split()]
                            # Store as sorted comma-separated string for comparison
                            config_registry[var_name] = ','.join(sorted(var_values))
                            continue
                        
                        # Extract metadata: LAYOUT PRIMARY
                        match = re.match(r'^\s*LAYOUT\s+PRIMARY\s+(.+?)\s*$', line)
                        if match:
                            metadata['design_name'] = match.group(1)
                            continue
                        
                        # Extract metadata: SOURCE PATH
                        match = re.match(r'^\s*SOURCE\s+PATH\s+(.+?)\s*$', line)
                        if match:
                            metadata['netlist_path'] = match.group(1)
                            continue
            except Exception as e:
                errors.append(f"Error parsing sourceme {file_path}: {str(e)}")
        
        # 4. Parse PVL log files (higher priority - ALWAYS overwrites)
        for file_path in pvl_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line_num, line in enumerate(f, 1):
                        # Pattern 1: #DEFINE statements in PVL (uppercase)
                        match = re.match(r'^\s*#DEFINE\s+(\w+)', line)
                        if match:
                            flag_name = match.group(1)
                            # CRITICAL: ALWAYS overwrite registry (no "if not in registry" check!)
                            config_registry[flag_name] = 'enabled'
                            continue
                        
                        # Pattern 2: variable declarations in PVL (Pegasus format)
                        # Format: variable VAR_NAME = "value";
                        match = re.match(r'^\s*variable\s+(\w+)\s*=\s*"?([^"]+)"?;?', line, re.IGNORECASE)
                        if match:
                            var_name = match.group(1)
                            var_value = match.group(2).strip()
                            # CRITICAL: ALWAYS overwrite registry (PVL has higher priority)
                            config_registry[var_name] = var_value
                            continue
                        
                        # Extract metadata: SCHEMATIC_PRIMARY
                        match = re.match(r'^\s*SCHEMATIC_PRIMARY\s+"([^"]+)"\s*;', line)
                        if match:
                            metadata['schematic_primary'] = match.group(1)
                            continue
                        
                        # Extract metadata: Tool version
                        match = re.search(r'PEGASUS_PVL_LIBRARY\s+=\s+.+/(\d+\.\d+\.\d+-\w+)/', line)
                        if match:
                            metadata['tool_version'] = match.group(1)
                            continue
            except Exception as e:
                errors.append(f"Error parsing PVL log {file_path}: {str(e)}")
        
        # 5. Compare actual vs expected configuration (from pattern_items)
        pattern_items = self.item_data.get('requirements', {}).get('pattern_items', [])
        
        for pattern_dict in pattern_items:
            # Parse dictionary: {'KEY': 'value'} or {'KEY': ['list', 'of', 'values']}
            if not isinstance(pattern_dict, dict):
                errors.append(f"Invalid pattern_item format: {pattern_dict}")
                continue
            
            key_name = list(pattern_dict.keys())[0]
            expected_state = pattern_dict[key_name]
            
            # Get actual state from registry
            actual_state = config_registry.get(key_name, 'not_found')
            
            # Handle list-type expected values (e.g., POWER_NAME, GROUND_NAME)
            if isinstance(expected_state, list):
                # Convert list to sorted comma-separated string for comparison
                expected_state_str = ','.join(sorted(expected_state))
            else:
                expected_state_str = str(expected_state)
            
            # Convert actual state to string
            actual_state_str = str(actual_state)
            
            # Case-insensitive comparison
            if actual_state_str.lower() == expected_state_str.lower():
                items.append({
                    'name': key_name,
                    'expected': expected_state_str,
                    'actual': actual_state_str,
                    'status': 'MATCH',
                    'line_number': 0,
                    'file_path': 'N/A'
                })
            else:
                items.append({
                    'name': key_name,
                    'expected': expected_state_str,
                    'actual': actual_state_str,
                    'status': 'MISMATCH',
                    'line_number': 0,
                    'file_path': 'N/A'
                })
        
        # 6. Store frequently reused data on self
        self._parsed_items = items
        self._config_registry = config_registry
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
        
        Validates LVS rule deck configuration by:
        1. Parsing PVL log and sourceme files for #DEFINE/#define statements
        2. Extracting POWER_NAME and GROUND_NAME lists
        3. Checking configuration flags against expected states
        4. Reporting violations as missing_items (FAIL)
        """
        violations = self._type1_core_logic()
        
        # Build found_items from clean configuration flags
        data = self._parse_input_files()
        all_flags = data.get('items', [])
        
        # ⚠️ CRITICAL: found_items MUST be dict[str, dict], NOT list!
        found_items = {}
        for flag in all_flags:
            flag_name = flag.get('name', '')
            if flag_name not in violations:
                # This flag is clean (correct state)
                found_items[flag_name] = {
                    'name': flag_name,
                    'line_number': flag.get('line_number', 0),
                    'file_path': flag.get('file_path', 'N/A')
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
        
        Validates LVS rule deck configuration by:
        1. Parsing PVL log file for #DEFINE statements (highest priority)
        2. Parsing sourceme file for #define statements (fallback)
        3. Extracting POWER_NAME and GROUND_NAME lists from sourceme
        4. Checking each configuration flag's state (enabled/disabled)
        5. Comparing against expected configuration
        
        Returns:
            Dict of violations: {flag_name: {'line_number': ..., 'file_path': ..., 'reason': ...}}
            Empty dict if all checks pass.
        """
        data = self._parse_input_files()
        items = data.get('items', [])
        
        violations = {}
        
        for item in items:
            if item['status'] == 'MISMATCH':
                violations[item['name']] = {
                    'line_number': item.get('line_number', 0),
                    'file_path': item.get('file_path', 'N/A'),
                    'reason': f"Expected {item['expected']}, got {item['actual']}"
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
            - found_items: {flag_name: {'line_number': ..., 'file_path': ...}}
            - missing_items: {flag_name: {'line_number': ..., 'file_path': ..., 'reason': ...}}
        """
        data = self._parse_input_files()
        items = data.get('items', [])
        
        found_items = {}
        missing_items = {}
        
        for item in items:
            flag_name = item.get('name', '')
            if item['status'] == 'MATCH':
                found_items[flag_name] = {
                    'name': flag_name,
                    'line_number': item.get('line_number', 0),
                    'file_path': item.get('file_path', 'N/A')
                }
            else:  # MISMATCH
                missing_items[flag_name] = {
                    'name': flag_name,
                    'line_number': item.get('line_number', 0),
                    'file_path': item.get('file_path', 'N/A'),
                    'reason': f"Expected {item['expected']}, got {item['actual']}"
                }
        
        return found_items, missing_items
    
    # =========================================================================
    # Type 3: Value Check with Waiver Logic
    # =========================================================================
    
    def _execute_type3(self) -> CheckResult:
        """Type 3: Pattern/value check with waiver support (reuses Type 2 core logic)."""
        # Step 1: Get found/missing items using Type 2's core logic
        found_items_base, violations = self._type2_core_logic()
        
        # Step 2: Parse waiver configuration (FIXED: Use waivers.get() instead of get_waive_items())
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # Step 3: Split violations into waived and unwaived
        found_items = {}
        waived_items = {}
        missing_items = {}
        used_waivers = set()
        
        # Process found_items_base (no waiver needed - these matched expected values)
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
        
        # Step 5: Build output (FIXED: Pass dict directly, not list(dict.values()))
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
        
        Same validation as Type 1, but with waiver classification:
        - Clean flags → found_items (PASS)
        - Waived violations → waived_items (PASS with [WAIVER] tag)
        - Unwaived violations → missing_items (FAIL)
        - Unused waivers → WARN with [WAIVER] tag
        
        PASS if all violations are waived.
        """
        # Step 1: Get violations using Type 1's core logic
        violations = self._type1_core_logic()
        
        # Build found_items from clean configuration flags
        data = self._parse_input_files()
        all_flags = data.get('items', [])
        
        # ⚠️ CRITICAL: found_items MUST be dict[str, dict], NOT list!
        found_items = {}
        for flag in all_flags:
            flag_name = flag.get('name', '')
            if flag_name not in violations:
                # This flag is clean (correct state)
                found_items[flag_name] = {
                    'name': flag_name,
                    'line_number': flag.get('line_number', 0),
                    'file_path': flag.get('file_path', 'N/A')
                }
        
        # Step 2: Parse waiver configuration (FIXED: Use waivers.get() instead of get_waive_items())
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
        
        # Step 5: Build output (FIXED: Pass dict directly, not list(dict.values()))
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
    checker = Check_12_0_0_09()
    checker.init_checker(Path(__file__))
    result = checker.execute_check()
    checker.write_output(result)
    return 0 if result.is_pass else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())