################################################################################
# Script Name: IMP-12-0-0-06.py
#
# Purpose:
#   Confirm the MIM related check setting is correct. (Fill N/A if no MIMCAP inserted or no MIM related layers)
#
# Logic:
#   - Parse do_cmd_3star_DRC_sourceme to extract intended MIM switch configuration (enabled/disabled)
#   - Parse do_pvs_DRC_pvl.log to extract actual MIM switch configuration from PVL parsing
#   - PVL log configuration takes precedence over sourceme (represents actual tool behavior)
#   - Validate final configuration against pattern_items (expected switch states)
#   - Support status_check mode: only report switches in pattern_items, compare actual vs expected state
#   - Return N/A if no MIM switches found in either file
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
class Check_12_0_0_06(InputFileParserMixin, OutputBuilderMixin, WaiverHandlerMixin, BaseChecker):
    """
    IMP-12-0-0-06: Confirm the MIM related check setting is correct. (Fill N/A if no MIMCAP inserted or no MIM related layers)
    
    Checking Types:
    - Type 1: requirements=N/A, pattern_items [], waivers=N/A/0 → Boolean Check
    - Type 2: requirements>0, pattern_items [...], waivers=N/A/0 → Value Check
    - Type 3: requirements>0, pattern_items [...], waivers>0 → Value Check with Waiver Logic
    - Type 4: requirements=N/A, pattern_items [], waivers=N/A/0 → Boolean Check with Waiver Logic
    
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
    FOUND_DESC_TYPE1_4 = "MIM configuration switches found in DRC rule deck"
    MISSING_DESC_TYPE1_4 = "Required MIM configuration switches not found in DRC setup"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_DESC_TYPE2_3 = "MIM switch configuration matched expected settings"
    MISSING_DESC_TYPE2_3 = "MIM switch configuration mismatch detected"
    
    # All Types (waiver description unified)
    WAIVED_DESC = "Waived MIM configuration mismatches"
    
    # ⭐ REASON CONSTANTS - Split by Type semantics (API-025)
    # ALL Types pass found_reason/missing_reason, but use different constants
    
    # Type 1/4: Boolean checks - emphasize "found/not found" (existence)
    FOUND_REASON_TYPE1_4 = "MIM-related #DEFINE switches found in PVL parsing log and sourceme configuration"
    MISSING_REASON_TYPE1_4 = "Required MIM switches not found in PVL log or sourceme file"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_REASON_TYPE2_3 = "MIM switch state matched expected configuration (actual state matches requirement)"
    MISSING_REASON_TYPE2_3 = "MIM switch state does not match expected configuration"
    # Note: Actual expected/actual values are included in the reason field of missing_items
    
    # Waiver-related (Type 3/4 only)
    WAIVED_BASE_REASON = "MIM switch configuration mismatch waived per design team approval"
    UNUSED_WAIVER_REASON = "Waiver entry not matched - no corresponding MIM switch mismatch found in actual configuration"
    
    def __init__(self):
        """Initialize the checker."""
        super().__init__(
            check_module="12.0_PHYSICAL_VERIFICATION_CHECK",
            item_id="IMP-12-0-0-06",
            item_desc="Confirm the MIM related check setting is correct. (Fill N/A if no MIMCAP inserted or no MIM related layers)"
        )
        # Custom member variables for parsed data
        self._parsed_items: List[Dict[str, Any]] = []
        self._metadata: Dict[str, str] = {}
        self._switch_registry: Dict[str, str] = {}  # {switch_name: 'enabled'/'disabled'}
        self._rule_file_path: str = ""
    
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
        Parse input files to extract MIM switch configuration.
        
        Parsing Strategy:
        1. Parse do_cmd_3star_DRC_sourceme for intended MIM switch configuration (low priority)
        2. Parse do_pvs_DRC_pvl.log for actual MIM switch configuration (high priority - overwrites)
        3. Build final switch registry with actual configuration
        4. Return N/A if no MIM switches found in either file
        
        Returns:
            Dict with parsed data:
            - 'items': List[Dict] - MIM switches with state and metadata
            - 'metadata': Dict - File metadata (rule_file_path)
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
        switch_registry = {}  # {switch_name: 'enabled'/'disabled'}
        rule_file_path = ""
        
        # Patterns for MIM switch detection
        # Pattern 1: Enabled MIM switches in sourceme (uncommented #DEFINE)
        sourceme_enabled_pattern = r'^\s*#DEFINE\s+((?:SHD|FHD)MIM[A-Z0-9_]*|CoWoS_S|KOZ_High_subst_layer)\s*(?://.*)?$'
        # Pattern 2: Disabled MIM switches in sourceme (commented out)
        sourceme_disabled_pattern = r'^\s*(?://|#)\s*#?DEFINE\s+((?:SHD|FHD)MIM[A-Z0-9_]*|CoWoS_S|KOZ_High_subst_layer)\s*(?://.*)?$'
        # Pattern 3: Active MIM switches in PVL log (actual config - takes precedence)
        pvl_enabled_pattern = r'^#DEFINE\s+(.*MIM.*|SHDMIM.*|.*MIMCAP.*|CoWoS_S|KOZ_High_subst_layer)\s*$'
        # Pattern 4: Rule file path header in PVL log
        pvl_header_pattern = r'^Parsing Rule File\s+(.+\.pvl)\s+\.\.\.'
        
        # 3. Parse each input file for MIM switch information
        for file_path in valid_files:
            try:
                file_name = file_path.name
                
                # Step 1: Parse sourceme file (low priority)
                # FIXED: Support both DRC and ANT_MIM sourceme files
                if 'sourceme' in file_name and ('do_cmd_3star_DRC_sourceme' in file_name or 'do_cmd_3star_ANT_MIM_sourceme' in file_name):
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        for line_num, line in enumerate(f, 1):
                            # Check for enabled switches
                            match_enabled = re.search(sourceme_enabled_pattern, line)
                            if match_enabled:
                                switch_name = match_enabled.group(1).upper()
                                switch_registry[switch_name] = 'enabled'
                                continue
                            
                            # Check for disabled switches (only if not already found as enabled)
                            match_disabled = re.search(sourceme_disabled_pattern, line)
                            if match_disabled:
                                switch_name = match_disabled.group(1).upper()
                                # Only add if not already in registry (avoid overwriting enabled with disabled)
                                if switch_name not in switch_registry:
                                    switch_registry[switch_name] = 'disabled'
                
                # Step 2: Parse PVL log (high priority - overwrites sourceme)
                # FIXED: Support both DRC and ANT_MIM PVL logs
                elif 'pvl.log' in file_name and ('do_pvs_DRC_pvl.log' in file_name or 'do_pvs_ANT_MIM_pvl.log' in file_name):
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        for line_num, line in enumerate(f, 1):
                            # Extract rule file path from header
                            header_match = re.search(pvl_header_pattern, line)
                            if header_match:
                                rule_file_path = header_match.group(1)
                                continue
                            
                            # Extract enabled MIM switches (overwrites sourceme entries)
                            switch_match = re.search(pvl_enabled_pattern, line)
                            if switch_match:
                                switch_name = switch_match.group(1).upper()
                                # PVL log always overwrites sourceme (actual behavior)
                                switch_registry[switch_name] = 'enabled'
            
            except Exception as e:
                errors.append(f"Error parsing {file_path}: {str(e)}")
        
        # Build items list from final switch registry
        for switch_name, state in switch_registry.items():
            items.append({
                'name': switch_name,
                'state': state,
                'line_number': 0,  # Line number not critical for this check
                'file_path': rule_file_path if rule_file_path else 'N/A',
                'type': 'mim_switch'
            })
        
        # Store metadata
        metadata['rule_file_path'] = rule_file_path
        
        # 4. Store frequently reused data on self
        self._parsed_items = items
        self._switch_registry = switch_registry
        self._rule_file_path = rule_file_path
        
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
        
        Validates MIM-related switch configuration by:
        1. Parsing PVL log and sourceme files for MIM switch definitions
        2. Checking if any MIM switches are found and properly configured
        3. Returns PASS if MIM switches exist, FAIL if missing or invalid
        
        Returns:
            CheckResult with found_items (configured switches) and missing_items (violations)
        """
        violations = self._type1_core_logic()
        
        # Build found_items from configured switches (passing objects)
        data = self._parse_input_files()
        configured_switches = data.get('items', [])
        
        found_items = {}
        for switch in configured_switches:
            switch_name = switch.get('name', '')
            if switch_name and switch_name not in violations:
                found_items[switch_name] = {
                    'name': switch_name,
                    'line_number': switch.get('line_number', 0),
                    'file_path': switch.get('file_path', 'N/A')
                }
        
        # Convert violations dict to dict format for missing_items
        missing_items = {}
        for viol_name, viol_data in violations.items():
            missing_items[viol_name] = viol_data
        
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
        
        Validates MIM switch configuration by:
        1. Parsing PVL log for actual switch states (takes precedence)
        2. Parsing sourceme for intended switch states (fallback)
        3. Checking if any MIM switches are found
        4. Validating configuration consistency
        
        Returns:
            Dict of violations: {switch_name: {'line_number': ..., 'file_path': ..., 'reason': ...}}
            Empty dict if all checks pass (MIM switches found and valid)
        """
        data = self._parse_input_files()
        items = data.get('items', [])
        metadata = data.get('metadata', {})
        errors = data.get('errors', [])
        
        violations = {}
        
        # Check for parsing errors
        if errors:
            for error in errors:
                violations[f"parsing_error_{len(violations)}"] = {
                    'line_number': 0,
                    'file_path': 'N/A',
                    'reason': error
                }
            return violations
        
        # Check if no MIM switches found at all
        if not items:
            violations['MIM_configuration'] = {
                'line_number': 0,
                'file_path': metadata.get('pvl_log_file', 'do_pvs_DRC_pvl.log'),
                'reason': 'Required MIM switches not found in PVL log or sourceme file'
            }
            return violations
        
        # Validate each switch configuration
        for switch in items:
            switch_name = switch.get('name', '')
            switch_state = switch.get('state', '')
            source = switch.get('source', '')
            
            # Check for invalid switch state
            if switch_state not in ['enabled', 'disabled']:
                violations[switch_name] = {
                    'line_number': switch.get('line_number', 0),
                    'file_path': switch.get('file_path', 'N/A'),
                    'reason': f'Invalid MIM switch state: {switch_state} (expected: enabled/disabled)'
                }
                continue
            
            # Check for missing source information
            if not source:
                violations[switch_name] = {
                    'line_number': switch.get('line_number', 0),
                    'file_path': switch.get('file_path', 'N/A'),
                    'reason': 'MIM switch found but source file information missing'
                }
                continue
        
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
            - found_items: {switch_name: {'line_number': ..., 'file_path': ..., 'actual_state': ...}}
            - missing_items: {switch_name: {'line_number': ..., 'file_path': ..., 'reason': ..., 'expected_state': ..., 'actual_state': ...}}
        """
        data = self._parse_input_files()
        items = data.get('items', [])
        
        requirements = self.item_data.get('requirements', {})
        pattern_items = requirements.get('pattern_items', [])
        
        found_items = {}
        missing_items = {}
        
        # Pattern items are dictionaries: {'switch_name': 'expected_state'}
        for pattern_dict in pattern_items:
            for switch_name, expected_state in pattern_dict.items():
                expected_state_lower = expected_state.lower()
                matched = False
                
                # Search for this switch in parsed items
                for item in items:
                    item_name = item.get('name', '')
                    
                    # EXACT MATCH (case-insensitive) - switch names are concrete identifiers
                    if switch_name.lower() == item_name.lower():
                        actual_state = item.get('state', '').lower()
                        
                        # Check if state matches expected
                        if actual_state == expected_state_lower:
                            # State matches - add to found_items
                            found_items[switch_name] = {
                                'line_number': item.get('line_number', 0),
                                'file_path': item.get('file_path', 'N/A'),
                                'actual_state': actual_state,
                                'expected_state': expected_state_lower
                            }
                            matched = True
                        else:
                            # State mismatch - add to missing_items
                            missing_items[switch_name] = {
                                'line_number': item.get('line_number', 0),
                                'file_path': item.get('file_path', 'N/A'),
                                'reason': f'MIM switch state does not match expected configuration (expected: {expected_state_lower}, actual: {actual_state})',
                                'expected_state': expected_state_lower,
                                'actual_state': actual_state
                            }
                            matched = True
                        break
                
                if not matched:
                    # Switch not found in any file
                    missing_items[switch_name] = {
                        'line_number': 0,
                        'file_path': 'N/A',
                        'reason': f'MIM switch "{switch_name}" not found in configuration files',
                        'expected_state': expected_state_lower,
                        'actual_state': 'not_found'
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
        
        # Process found_items_base (no waiver needed - already correct)
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
        
        # Step 5: Build output
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
        
        Performs same validation as Type 1, but adds waiver processing:
        1. Reuses _type1_core_logic() to get violations
        2. Matches violations against waive_items by switch name
        3. Splits violations into waived (PASS) and unwaived (FAIL)
        4. Tracks unused waivers for reporting
        
        Returns:
            CheckResult with found_items, waived_items, missing_items, and unused_waivers
        """
        # Step 1: Get violations using Type 1's core logic
        violations = self._type1_core_logic()
        
        # Build found_items from configured switches (passing objects)
        data = self._parse_input_files()
        configured_switches = data.get('items', [])
        
        found_items = {}
        for switch in configured_switches:
            switch_name = switch.get('name', '')
            if switch_name and switch_name not in violations:
                found_items[switch_name] = {
                    'name': switch_name,
                    'line_number': switch.get('line_number', 0),
                    'file_path': switch.get('file_path', 'N/A')
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
        
        # Step 5: Build output
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
    checker = Check_12_0_0_06()
    checker.init_checker(Path(__file__))
    result = checker.execute_check()
    checker.write_output(result)
    return 0 if result.is_pass else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())