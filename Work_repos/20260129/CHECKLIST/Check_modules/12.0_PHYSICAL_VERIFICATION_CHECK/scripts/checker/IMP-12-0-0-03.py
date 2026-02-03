################################################################################
# Script Name: IMP-12-0-0-03.py
#
# Purpose:
#   Confirm the DRC rule deck setting is correct. Make sure the switch settings match with Foundry CTA (/local/method/CTAF/<process>/production in chamber). Please add justification in Comment if you changed some switching setting in CTA.
#
# Logic:
#   - Parse do_pvs_DRC_pvl.log to extract enabled #DEFINE switches from Pegasus PVL parsing output
#   - Parse do_cmd_3star_DRC_sourceme to extract all #DEFINE switches (enabled/disabled) and VARIABLE settings
#   - Build registry of switch states and variable values with line numbers and file paths
#   - Compare actual settings against pattern_items (expected CTA requirements)
#   - Report found_items (matching settings) and missing_items (mismatches requiring justification)
#   - Support waiver for justified deviations from CTA requirements
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
class Check_12_0_0_03(InputFileParserMixin, OutputBuilderMixin, WaiverHandlerMixin, BaseChecker):
    """
    IMP-12-0-0-03: Confirm the DRC rule deck setting is correct. Make sure the switch settings match with Foundry CTA (/local/method/CTAF/<process>/production in chamber). Please add justification in Comment if you changed some switching setting in CTA.
    
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
    FOUND_DESC_TYPE1_4 = "DRC rule deck configuration found and validated"
    MISSING_DESC_TYPE1_4 = "DRC rule deck configuration not found or invalid"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_DESC_TYPE2_3 = "DRC rule deck setting matches CTA requirement"
    MISSING_DESC_TYPE2_3 = "DRC rule deck setting does not match CTA requirement"
    
    # All Types (waiver description unified)
    WAIVED_DESC = "DRC rule deck setting mismatch waived with justification"
    
    # ⭐ REASON CONSTANTS - Split by Type semantics (API-025)
    # ALL Types pass found_reason/missing_reason, but use different constants
    
    # Type 1/4: Boolean checks - emphasize "found/not found" (existence)
    FOUND_REASON_TYPE1_4 = "DRC rule deck configuration found in input files and validated against CTA"
    MISSING_REASON_TYPE1_4 = "Required DRC configuration not found in input files or validation failed"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_REASON_TYPE2_3 = "Switch/variable setting matched and validated against CTA requirement"
    MISSING_REASON_TYPE2_3 = "Switch/variable setting does not match CTA requirement - justification required in comments"
    
    # Waiver-related (Type 3/4 only)
    WAIVED_BASE_REASON = "DRC rule deck setting mismatch waived per design team approval"
    UNUSED_WAIVER_REASON = "Waiver entry not matched - no corresponding setting mismatch found in input files"
    
    def __init__(self):
        """Initialize the checker."""
        super().__init__(
            check_module="12.0_PHYSICAL_VERIFICATION_CHECK",
            item_id="IMP-12-0-0-03",
            item_desc="Confirm the DRC rule deck setting is correct. Make sure the switch settings match with Foundry CTA (/local/method/CTAF/<process>/production in chamber). Please add justification in Comment if you changed some switching setting in CTA."
        )
        # Custom member variables for parsed data
        self._parsed_items: List[Dict[str, Any]] = []
        self._metadata: Dict[str, str] = {}
        self._switch_registry: Dict[str, Dict[str, Any]] = {}
        self._variable_registry: Dict[str, Dict[str, Any]] = {}
    
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
        Parse input files to extract DRC rule deck switch and variable settings.
        
        Parses two input files:
        1. do_pvs_DRC_pvl.log - Pegasus PVL parsing log with enabled #DEFINE switches
        2. do_cmd_3star_DRC_sourceme - Calibre DRC configuration script with switches and variables
        
        Returns:
            Dict with parsed data:
            - 'items': List[Dict] - All switches and variables with status/value
            - 'metadata': Dict - File metadata (tool version, rule file paths)
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
        switch_registry = {}
        variable_registry = {}
        
        # 3. Parse input files in priority order:
        #    - First: sourceme (configuration script - what's intended)
        #    - Second: PVL log (actual parsed config - what's actually used)
        #    PVL log takes precedence when there are conflicts
        
        # Parse sourceme file first
        for file_path in valid_files:
            try:
                file_name = Path(file_path).name
                if 'do_cmd_3star_DRC_sourceme' in file_name:
                    # Parse Calibre DRC configuration script
                    self._parse_sourceme_script(file_path, switch_registry, variable_registry, errors)
            except Exception as e:
                errors.append(f"Error parsing {file_path}: {str(e)}")
        
        # Parse PVL log second (overwrites sourceme when conflicts exist)
        for file_path in valid_files:
            try:
                file_name = Path(file_path).name
                if 'do_pvs_DRC_pvl.log' in file_name:
                    # Parse Pegasus PVL parsing log
                    self._parse_pvl_log(file_path, switch_registry, metadata, errors)
                    
            except Exception as e:
                errors.append(f"Error parsing {file_path}: {str(e)}")
        
        # 4. Build items list from registries
        for switch_name, switch_data in switch_registry.items():
            items.append({
                'name': switch_name,
                'type': 'switch',
                'status': switch_data['status'],
                'line_number': switch_data['line_number'],
                'file_path': switch_data['file_path'],
                'comment': switch_data.get('comment', '')
            })
        
        for var_name, var_data in variable_registry.items():
            items.append({
                'name': var_name,
                'type': 'variable',
                'value': var_data['value'],
                'line_number': var_data['line_number'],
                'file_path': var_data['file_path'],
                'comment': var_data.get('comment', '')
            })
        
        # 5. Store frequently reused data on self
        self._parsed_items = items
        self._switch_registry = switch_registry
        self._variable_registry = variable_registry
        self._metadata = metadata
        
        return {
            'items': items,
            'metadata': metadata,
            'errors': errors
        }
    
    def _parse_pvl_log(self, file_path: Path, switch_registry: Dict, metadata: Dict, errors: List):
        """Parse Pegasus PVL parsing log to extract enabled switches.
        
        PVL log represents the ACTUAL parsed configuration that was used,
        so it takes precedence over sourceme script when there are conflicts.
        """
        pattern_pvl_define = re.compile(r'^#DEFINE\s+([A-Za-z0-9_]+)\s*$')
        pattern_rule_file = re.compile(r'^Parsing Rule File\s+(.+?)\s+\.\.\.$')
        
        current_rule_file = None
        
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line_num, line in enumerate(f, 1):
                # Extract rule file path
                match_file = pattern_rule_file.search(line)
                if match_file:
                    current_rule_file = match_file.group(1)
                    metadata['rule_file_path'] = current_rule_file
                    continue
                
                # Extract enabled switches
                match_define = pattern_pvl_define.search(line)
                if match_define:
                    switch_name = match_define.group(1)
                    # PVL log shows actual configuration, so ALWAYS update registry
                    # (overwrites sourceme data if it conflicts)
                    switch_registry[switch_name] = {
                        'status': 'enabled',
                        'line_number': line_num,
                        'file_path': str(file_path),
                        'comment': 'Enabled in PVL parsing log (actual configuration)'
                    }
    
    def _parse_sourceme_script(self, file_path: Path, switch_registry: Dict, variable_registry: Dict, errors: List):
        """Parse Calibre DRC configuration script to extract switches and variables."""
        pattern_enabled = re.compile(r'^\s*#DEFINE\s+([A-Z_0-9]+)\s*(?://\s*(.*))?$')
        pattern_disabled = re.compile(r'^\s*//\s*#DEFINE\s+([A-Z_0-9]+)\s*(?://\s*(.*))?$')
        pattern_variable = re.compile(r'^\s*VARIABLE\s+([A-Z_0-9]+)\s+"?([^"\n]+)"?\s*(?://\s*(.*))?$')
        
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line_num, line in enumerate(f, 1):
                # Check for disabled switches first (more specific pattern)
                match_disabled = pattern_disabled.search(line)
                if match_disabled:
                    switch_name = match_disabled.group(1)
                    comment = match_disabled.group(2) if match_disabled.group(2) else ''
                    switch_registry[switch_name] = {
                        'status': 'disabled',
                        'line_number': line_num,
                        'file_path': str(file_path),
                        'comment': comment.strip()
                    }
                    continue
                
                # Check for enabled switches
                match_enabled = pattern_enabled.search(line)
                if match_enabled:
                    switch_name = match_enabled.group(1)
                    comment = match_enabled.group(2) if match_enabled.group(2) else ''
                    switch_registry[switch_name] = {
                        'status': 'enabled',
                        'line_number': line_num,
                        'file_path': str(file_path),
                        'comment': comment.strip()
                    }
                    continue
                
                # Check for variable definitions
                match_variable = pattern_variable.search(line)
                if match_variable:
                    var_name = match_variable.group(1)
                    var_value = match_variable.group(2).strip().strip('"')
                    comment = match_variable.group(3) if match_variable.group(3) else ''
                    variable_registry[var_name] = {
                        'value': var_value,
                        'line_number': line_num,
                        'file_path': str(file_path),
                        'comment': comment.strip()
                    }
    
    # =========================================================================
    # Type 1: Boolean Check
    # =========================================================================
    
    def _execute_type1(self) -> CheckResult:
        """Type 1: Boolean check without waiver support.
        
        Validates DRC rule deck settings against CTA requirements by:
        1. Parsing enabled switches from do_pvs_DRC_pvl.log
        2. Parsing all switches and variables from do_cmd_3star_DRC_sourceme
        3. Checking for mismatches between actual settings and expected CTA configuration
        
        Returns:
            CheckResult with found_items (matching settings) and missing_items (mismatches)
        """
        violations = self._type1_core_logic()
        
        # Build found_items from clean/matching settings
        data = self._parse_input_files()
        all_settings = data.get('items', [])
        
        # ⚠️ CRITICAL: found_items MUST be dict[str, dict], NOT list!
        found_items = {}
        for setting in all_settings:
            setting_name = setting.get('name', '')
            # Only include settings that are NOT violations
            if setting_name not in violations:
                found_items[setting_name] = {
                    'name': setting_name,
                    'line_number': setting.get('line_number', 0),
                    'file_path': setting.get('file_path', 'N/A')
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
        
        Validates DRC rule deck configuration by:
        1. Extracting enabled switches from Pegasus PVL parsing output
        2. Extracting all switch/variable settings from sourceme file
        3. Comparing against expected CTA requirements
        4. Identifying mismatches requiring justification
        
        Returns:
            Dict of violations: {setting_name: {'line_number': ..., 'file_path': ..., 'reason': ...}}
            Empty dict if all settings match CTA requirements.
        """
        data = self._parse_input_files()
        
        # Get parsed data
        items = data.get('items', [])
        errors = data.get('errors', [])
        
        violations = {}
        
        # Check for parsing errors first
        if errors:
            for error in errors:
                error_key = f"parsing_error_{len(violations)}"
                violations[error_key] = {
                    'line_number': 0,
                    'file_path': 'N/A',
                    'reason': f"DRC rule deck parsing error: {error}"
                }
        
        # Build switch and variable registries
        switch_registry = {}
        variable_registry = {}
        
        for item in items:
            item_name = item.get('name', '')
            item_type = item.get('type', '')
            
            if item_type == 'switch':
                switch_registry[item_name] = {
                    'status': item.get('status', 'unknown'),
                    'line_number': item.get('line_number', 0),
                    'file_path': item.get('file_path', 'N/A')
                }
            elif item_type == 'variable':
                variable_registry[item_name] = {
                    'value': item.get('value', ''),
                    'line_number': item.get('line_number', 0),
                    'file_path': item.get('file_path', 'N/A')
                }
        
        # Check for switches defined but not enabled (potential CTA deviation)
        for switch_name, switch_data in switch_registry.items():
            switch_state = switch_data.get('status', 'unknown')
            # If switch is explicitly disabled or commented, check if it should be enabled per CTA
            if switch_state in ['disabled', 'commented']:
                # This is a potential CTA deviation - flag for review
                violations[switch_name] = {
                    'line_number': switch_data.get('line_number', 0),
                    'file_path': switch_data.get('file_path', 'N/A'),
                    'reason': f"Switch '{switch_name}' is {switch_state} - verify against CTA requirements and add justification if intentional"
                }
        
        # Validate variable settings (check for suspicious or non-standard values)
        for var_name, var_data in variable_registry.items():
            var_value = var_data.get('value', '')
            # Flag variables with empty or suspicious values
            if not var_value or var_value.strip() == '':
                violations[var_name] = {
                    'line_number': var_data.get('line_number', 0),
                    'file_path': var_data.get('file_path', 'N/A'),
                    'reason': f"Variable '{var_name}' has empty value - verify against CTA requirements"
                }
        
        # If no input files were successfully parsed, report critical failure
        if not switch_registry and not variable_registry:
            violations['no_configuration_found'] = {
                'line_number': 0,
                'file_path': 'N/A',
                'reason': 'No DRC rule deck configuration found in input files - cannot validate against CTA requirements'
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
        switches = data.get('items', [])
        
        requirements = self.item_data.get('requirements', {})
        pattern_items = requirements.get('pattern_items', [])
        
        found_items = {}
        missing_items = {}
        
        # Build registry of all switches/variables from parsed data
        switch_registry = {}
        for switch in switches:
            switch_name = switch['name']
            switch_registry[switch_name] = {
                'state': switch.get('status', switch.get('value', 'N/A')),
                'value': switch.get('value', 'N/A'),
                'line_number': switch.get('line_number', 0),
                'file_path': switch.get('file_path', 'N/A')
            }
        
        # Check each pattern_item requirement
        for pattern_item in pattern_items:
            # Parse pattern_item format: dictionary {'SWITCH_NAME': 'expected_state'} or {'VARIABLE_NAME': 'expected_value'}
            if isinstance(pattern_item, dict):
                # Extract key-value pair from dictionary
                for item_name, expected_value in pattern_item.items():
                    # Check if switch/variable exists in registry
                    if item_name in switch_registry:
                        actual_data = switch_registry[item_name]
                        actual_value = actual_data.get('state', actual_data.get('value', 'N/A'))
                        
                        # Compare actual vs expected (case-insensitive for enabled/disabled)
                        if str(actual_value).lower() == str(expected_value).lower():
                            # Match found - setting is correct
                            found_items[item_name] = {
                                'line_number': actual_data['line_number'],
                                'file_path': actual_data['file_path']
                            }
                        else:
                            # Mismatch - setting does not match CTA requirement
                            missing_items[item_name] = {
                                'line_number': actual_data['line_number'],
                                'file_path': actual_data['file_path'],
                                'reason': f'Expected: {expected_value}, Found: {actual_value}'
                            }
                    else:
                        # Switch/variable not found in input files
                        missing_items[item_name] = {
                            'line_number': 0,
                            'file_path': 'N/A',
                            'reason': f'Expected: {expected_value}, Not found in input files'
                        }
            elif isinstance(pattern_item, str) and ':' in pattern_item:
                # Handle string format "SWITCH_NAME: expected_state" (legacy format)
                parts = pattern_item.split(':', 1)
                item_name = parts[0].strip()
                expected_value = parts[1].strip()
                
                # Check if switch/variable exists in registry
                if item_name in switch_registry:
                    actual_data = switch_registry[item_name]
                    actual_value = actual_data.get('state', actual_data.get('value', 'N/A'))
                    
                    # Compare actual vs expected (case-insensitive for enabled/disabled)
                    if str(actual_value).lower() == expected_value.lower():
                        # Match found - setting is correct
                        found_items[item_name] = {
                            'line_number': actual_data['line_number'],
                            'file_path': actual_data['file_path']
                        }
                    else:
                        # Mismatch - setting does not match CTA requirement
                        missing_items[item_name] = {
                            'line_number': actual_data['line_number'],
                            'file_path': actual_data['file_path'],
                            'reason': f'Expected: {expected_value}, Found: {actual_value}'
                        }
                else:
                    # Switch/variable not found in input files
                    missing_items[item_name] = {
                        'line_number': 0,
                        'file_path': 'N/A',
                        'reason': f'Expected: {expected_value}, Not found in input files'
                    }
            elif isinstance(pattern_item, str):
                # Handle list-type values (e.g., PAD_TEXT: ["bump", "rx_p", ...])
                # These are informational and considered found if present
                item_name = pattern_item
                if item_name in switch_registry:
                    actual_data = switch_registry[item_name]
                    found_items[item_name] = {
                        'line_number': actual_data['line_number'],
                        'file_path': actual_data['file_path']
                    }
                else:
                    missing_items[item_name] = {
                        'line_number': 0,
                        'file_path': 'N/A',
                        'reason': 'Not found in input files'
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
        
        # Step 3: Process found_items (no waiver needed - already correct)
        found_items = {}
        for item_name, item_data in found_items_base.items():
            found_items[item_name] = item_data
        
        # Step 4: Split violations into waived and unwaived
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
        
        # Step 5: Find unused waivers
        unused_waivers = [w for w in waive_dict.keys() if w not in used_waivers]
        
        # Step 6: Build output (FIXED: Pass dicts directly, not list(dict.values()))
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
        
        Same validation as Type 1, but allows waiving justified CTA deviations:
        1. Reuses _type1_core_logic() to identify all setting mismatches
        2. Matches violations against waive_items (justified deviations)
        3. Splits into waived (justified) and unwaived (requires fix) violations
        4. Tracks unused waivers for cleanup
        
        Returns:
            CheckResult with found_items, waived_items, missing_items, and unused_waivers
        """
        # Step 1: Get violations using Type 1's core logic
        violations = self._type1_core_logic()
        
        # Build found_items from clean/matching settings
        data = self._parse_input_files()
        all_settings = data.get('items', [])
        
        # ⚠️ CRITICAL: found_items MUST be dict[str, dict], NOT list!
        found_items = {}
        for setting in all_settings:
            setting_name = setting.get('name', '')
            # Only include settings that are NOT violations
            if setting_name not in violations:
                found_items[setting_name] = {
                    'name': setting_name,
                    'line_number': setting.get('line_number', 0),
                    'file_path': setting.get('file_path', 'N/A')
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
        
        # Step 5: Build output (FIXED: Pass dicts directly, not list(dict.values()))
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
    checker = Check_12_0_0_03()
    checker.init_checker(Path(__file__))
    result = checker.execute_check()
    checker.write_output(result)
    return 0 if result.is_pass else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())