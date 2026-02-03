################################################################################
# Script Name: IMP-12-0-0-25.py
#
# Purpose:
#   Confirm the BUMP DRC rule deck setting is correct.
#
# Logic:
#   - Parse input files to extract switch states (#DEFINE enabled/disabled) and variable values
#   - Extract switch definitions using patterns for enabled (#DEFINE) and disabled (//#DEFINE) states
#   - Extract variable definitions using patterns for Pegasus (lowercase 'variable') and Calibre (uppercase 'VARIABLE') formats
#   - Verify switch states and variable values against requirements from YAML configuration
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
class Check_12_0_0_25(InputFileParserMixin, OutputBuilderMixin, WaiverHandlerMixin, BaseChecker):
    """
    IMP-12-0-0-25: Confirm the BUMP DRC rule deck setting is correct.
    
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
    FOUND_DESC_TYPE1_4 = "BUMP DRC rule deck configuration found and validated"
    MISSING_DESC_TYPE1_4 = "BUMP DRC rule deck configuration not found or incomplete"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_DESC_TYPE2_3 = "All BUMP DRC rule deck settings matched requirements (15/15)"
    MISSING_DESC_TYPE2_3 = "BUMP DRC rule deck settings mismatch detected (configuration errors found)"
    
    # All Types (waiver description unified)
    WAIVED_DESC = "BUMP DRC rule deck configuration mismatches waived"
    
    # ⭐ REASON CONSTANTS - Split by Type semantics (API-025)
    # ALL Types pass found_reason/missing_reason, but use different constants
    
    # Type 1/4: Boolean checks - emphasize "found/not found" (existence)
    FOUND_REASON_TYPE1_4 = "BUMP DRC rule deck configuration found with all required settings"
    MISSING_REASON_TYPE1_4 = "Required BUMP DRC rule deck configuration not found in input files"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_REASON_TYPE2_3 = "All switch states and variable values matched and validated against requirements"
    MISSING_REASON_TYPE2_3 = "One or more switch states or variable values not satisfied or mismatched with requirements"
    
    # Waiver-related (Type 3/4 only)
    WAIVED_BASE_REASON = "BUMP DRC rule deck configuration mismatch waived per design team approval"
    UNUSED_WAIVER_REASON = "Waiver not matched - no corresponding configuration mismatch found in rule deck files"
    
    def __init__(self):
        """Initialize the checker."""
        super().__init__(
            check_module="12.0_PHYSICAL_VERIFICATION_CHECK",
            item_id="IMP-12-0-0-25",
            item_desc="Confirm the BUMP DRC rule deck setting is correct."
        )
        # Custom member variables for parsed data
        self._parsed_items: List[Dict[str, Any]] = []
        self._metadata: Dict[str, str] = {}
        self._switch_states: Dict[str, Dict[str, Any]] = {}
        self._variable_values: Dict[str, Dict[str, Any]] = {}
    
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
        Parse input files to extract BUMP DRC rule deck switch states and variable values.
        
        Extracts:
        - Switch states: #DEFINE (enabled) or //#DEFINE (disabled)
        - Variable values: variable/VARIABLE keyword followed by name and value
        
        Returns:
            Dict with parsed data:
            - 'items': List[Dict] - All detected switches and variables with metadata
            - 'switches': Dict - Switch states by name
            - 'variables': Dict - Variable values by name
            - 'clean_items': Dict - Items matching requirements
            - 'metadata': Dict - File metadata
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
        switch_states = {}
        variable_values = {}
        
        # Define patterns for switch and variable detection
        pattern_enabled = re.compile(r'^\s*#DEFINE\s+(\w+)')
        pattern_disabled = re.compile(r'^\s*//\s*#DEFINE\s+(\w+)')
        pattern_variable_pegasus = re.compile(r'^\s*variable\s+(\w+)\s+(.+)')
        pattern_variable_calibre = re.compile(r'^\s*VARIABLE\s+(\w+)\s+(.+)')
        
        # 3. Parse each input file for switch states and variable values
        for file_path in valid_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line_num, line in enumerate(f, 1):
                        # Check for disabled switch (must check before enabled to avoid false positives)
                        match_disabled = pattern_disabled.search(line)
                        if match_disabled:
                            switch_name = match_disabled.group(1)
                            switch_states[switch_name] = {
                                'name': switch_name,
                                'state': 'disabled',
                                'line_number': line_num,
                                'file_path': str(file_path),
                                'type': 'switch'
                            }
                            items.append(switch_states[switch_name])
                            continue
                        
                        # Check for enabled switch
                        match_enabled = pattern_enabled.search(line)
                        if match_enabled:
                            switch_name = match_enabled.group(1)
                            switch_states[switch_name] = {
                                'name': switch_name,
                                'state': 'enabled',
                                'line_number': line_num,
                                'file_path': str(file_path),
                                'type': 'switch'
                            }
                            items.append(switch_states[switch_name])
                            continue
                        
                        # Check for Pegasus variable (lowercase)
                        match_var_pegasus = pattern_variable_pegasus.search(line)
                        if match_var_pegasus:
                            var_name = match_var_pegasus.group(1)
                            var_value = match_var_pegasus.group(2).strip()
                            # Clean value: remove comments (//) and special chars (;)
                            if '//' in var_value:
                                var_value = var_value.split('//')[0].strip()
                            var_value = var_value.rstrip(';').strip()
                            variable_values[var_name] = {
                                'name': var_name,
                                'value': var_value,
                                'line_number': line_num,
                                'file_path': str(file_path),
                                'type': 'variable'
                            }
                            items.append(variable_values[var_name])
                            continue
                        
                        # Check for Calibre variable (uppercase)
                        match_var_calibre = pattern_variable_calibre.search(line)
                        if match_var_calibre:
                            var_name = match_var_calibre.group(1)
                            var_value = match_var_calibre.group(2).strip()
                            # Clean value: remove comments (//) and special chars (;)
                            if '//' in var_value:
                                var_value = var_value.split('//')[0].strip()
                            var_value = var_value.rstrip(';').strip()
                            variable_values[var_name] = {
                                'name': var_name,
                                'value': var_value,
                                'line_number': line_num,
                                'file_path': str(file_path),
                                'type': 'variable'
                            }
                            items.append(variable_values[var_name])
                            continue
                            
            except Exception as e:
                errors.append(f"Error parsing {file_path}: {str(e)}")
        
        # 4. Store frequently reused data on self
        self._parsed_items = items
        self._switch_states = switch_states
        self._variable_values = variable_values
        
        # 5. Build clean_items (items matching requirements)
        clean_items = {}
        requirements = self.item_data.get('requirements', {})
        pattern_items = requirements.get('pattern_items', [])
        
        for pattern_dict in pattern_items:
            # Skip non-dict items (防止字符串等非字典类型报错)
            if not isinstance(pattern_dict, dict):
                continue
            for config_name, expected_value in pattern_dict.items():
                # Check if it's a switch
                if isinstance(expected_value, str) and expected_value.lower() in ['enabled', 'disabled']:
                    if config_name in switch_states:
                        switch_data = switch_states[config_name]
                        if switch_data['state'] == expected_value:
                            clean_items[config_name] = switch_data
                else:
                    # Variable
                    if config_name in variable_values:
                        var_data = variable_values[config_name]
                        try:
                            if float(var_data['value']) == float(expected_value):
                                clean_items[config_name] = var_data
                        except (ValueError, TypeError):
                            pass
        
        return {
            'items': items,
            'switches': switch_states,
            'variables': variable_values,
            'clean_items': clean_items,
            'metadata': metadata,
            'errors': errors
        }
    
    # =========================================================================
    # Type 1: Boolean Check
    # =========================================================================
    
    def _execute_type1(self) -> CheckResult:
        """
        Type 1: Boolean check without waiver support.

        Validates BUMP DRC rule deck configuration by checking:
        - Switch states (enabled/disabled) match requirements
        - Variable values match requirements

        Returns PASS if all configuration items are correct, FAIL otherwise.
        """
        violations = self._type1_core_logic()

        # Build found_items from clean configuration items
        data = self._parse_input_files()
        clean_items = data.get('clean_items', {})

        # ⚠️ CRITICAL: found_items MUST be dict[str, dict], NOT list!
        found_items = {}
        for item_name, item_data in clean_items.items():
            found_items[item_name] = {
                'name': item_name,
                'line_number': item_data.get('line_number', 0),
                'file_path': item_data.get('file_path', 'N/A')
            }

        # ⚠️ CRITICAL: missing_items for build_complete_output expects dict[str, dict], NOT list!
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

        Validates BUMP DRC rule deck configuration against requirements:
        - Checks switch states (enabled/disabled)
        - Checks variable values

        Returns:
            Dict of violations: {item_name: {'line_number': ..., 'file_path': ..., 'reason': ...}}
            Empty dict if all checks pass.
        """
        data = self._parse_input_files()
        switches = data.get('switches', {})
        variables = data.get('variables', {})
        errors = data.get('errors', [])

        violations = {}

        # If parsing errors occurred, treat as violations
        if errors:
            for error in errors:
                violations[f"parse_error_{len(violations)}"] = {
                    'line_number': 0,
                    'file_path': 'N/A',
                    'reason': error
                }

        # Get requirements
        requirements = self.item_data.get('requirements', {})
        pattern_items = requirements.get('pattern_items', [])

        # Check each pattern item
        for pattern_dict in pattern_items:
            for config_name, expected_value in pattern_dict.items():
                # Check if it's a switch (expected_value is "enabled" or "disabled")
                if isinstance(expected_value, str) and expected_value.lower() in ['enabled', 'disabled']:
                    # Switch validation
                    if config_name in switches:
                        switch_data = switches[config_name]
                        actual_state = switch_data['state']

                        if actual_state != expected_value:
                            # Switch state mismatch
                            violations[config_name] = {
                                'line_number': switch_data.get('line_number', 0),
                                'file_path': switch_data.get('file_path', 'N/A'),
                                'reason': f"detect switch {config_name} {actual_state} (mismatch requirement: {expected_value})"
                            }
                    else:
                        # Switch not found
                        violations[config_name] = {
                            'line_number': 0,
                            'file_path': 'N/A',
                            'reason': f"switch {config_name} not found (requirement: {expected_value})"
                        }

                else:
                    # Variable validation (expected_value is numeric)
                    if config_name in variables:
                        var_data = variables[config_name]
                        actual_value = var_data['value']

                        # Compare numeric values (handle both int and float)
                        try:
                            if float(actual_value) != float(expected_value):
                                # Variable value mismatch
                                violations[config_name] = {
                                    'line_number': var_data.get('line_number', 0),
                                    'file_path': var_data.get('file_path', 'N/A'),
                                    'reason': f"detect variable {config_name} {actual_value} (mismatch requirement: {expected_value})"
                                }
                        except (ValueError, TypeError):
                            violations[config_name] = {
                                'line_number': var_data.get('line_number', 0),
                                'file_path': var_data.get('file_path', 'N/A'),
                                'reason': f"detect variable {config_name} {actual_value} (invalid numeric value, requirement: {expected_value})"
                            }
                    else:
                        # Variable not found
                        violations[config_name] = {
                            'line_number': 0,
                            'file_path': 'N/A',
                            'reason': f"variable {config_name} not found (requirement: {expected_value})"
                        }

        return violations

    # =========================================================================
    # Type 4: Boolean Check with Waiver Logic
    # =========================================================================

    def _execute_type4(self) -> CheckResult:
        """
        Type 4: Boolean check with waiver support (reuses Type 1 core logic).

        Performs same validation as Type 1, but supports waivers:
        - Violations matching waive_items → waived (PASS)
        - Violations not matching waivers → missing_items (FAIL)
        - Unused waivers → WARN

        Returns PASS if all violations are waived.
        """
        # Step 1: Get violations using Type 1's core logic
        violations = self._type1_core_logic()

        # Build found_items from clean configuration items
        data = self._parse_input_files()
        clean_items = data.get('clean_items', {})

        # ⚠️ CRITICAL: found_items MUST be dict[str, dict], NOT list!
        found_items = {}
        for item_name, item_data in clean_items.items():
            found_items[item_name] = {
                'name': item_name,
                'line_number': item_data.get('line_number', 0),
                'file_path': item_data.get('file_path', 'N/A')
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

        # Step 5: Build output (FIXED: API-009 - pass dict directly)
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

        # ⚠️ FIXED: API-009 - pass dict directly, NOT list(missing_items.values())
        # Use lambda to extract custom reason from item metadata
        return self.build_complete_output(
            found_items=found_items,
            missing_items=missing_items,
            found_desc=self.FOUND_DESC_TYPE2_3,
            missing_desc=self.MISSING_DESC_TYPE2_3,
            found_reason=lambda m: m.get('reason', self.FOUND_REASON_TYPE2_3),
            missing_reason=lambda m: m.get('reason', self.MISSING_REASON_TYPE2_3)
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
        switches = data.get('switches', {})
        variables = data.get('variables', {})

        requirements = self.item_data.get('requirements', {})
        pattern_items = requirements.get('pattern_items', [])

        found_items = {}
        missing_items = {}

        # Process each pattern item (dict with switch/variable name as key, expected value as value)
        for pattern_dict in pattern_items:
            # Skip non-dict items (防止字符串等非字典类型报错)
            if not isinstance(pattern_dict, dict):
                continue
            for config_name, expected_value in pattern_dict.items():
                # Check if it's a switch (expected_value is "enabled" or "disabled")
                if isinstance(expected_value, str) and expected_value.lower() in ['enabled', 'disabled']:
                    # Switch validation
                    if config_name in switches:
                        switch_data = switches[config_name]
                        actual_state = switch_data['state']

                        if actual_state == expected_value:
                            # Switch state matches requirement
                            file_path = switch_data.get('file_path', 'N/A')
                            file_name = Path(file_path).name if file_path != 'N/A' else 'N/A'
                            found_items[config_name] = {
                                'line_number': switch_data.get('line_number', 0),
                                'file_path': file_path,
                                'reason': f"detect switch {config_name} {actual_state} (match requirement: {expected_value}) at line {switch_data.get('line_number', 0)} of file {file_name}"
                            }
                        else:
                            # Switch state mismatch
                            file_path = switch_data.get('file_path', 'N/A')
                            file_name = Path(file_path).name if file_path != 'N/A' else 'N/A'
                            missing_items[config_name] = {
                                'line_number': switch_data.get('line_number', 0),
                                'file_path': file_path,
                                'reason': f"detect switch {config_name} {actual_state} (mismatch requirement: {expected_value}) at line {switch_data.get('line_number', 0)} of file {file_name}"
                            }
                    else:
                        # Switch not found
                        missing_items[config_name] = {
                            'line_number': 0,
                            'file_path': 'N/A',
                            'reason': f"switch {config_name} not found in any input files (requirement: {expected_value})"
                        }

                else:
                    # Variable validation (expected_value is numeric)
                    if config_name in variables:
                        var_data = variables[config_name]
                        actual_value = var_data['value']

                        # Compare numeric values (handle both int and float)
                        try:
                            if float(actual_value) == float(expected_value):
                                # Variable value matches requirement
                                file_path = var_data.get('file_path', 'N/A')
                                file_name = Path(file_path).name if file_path != 'N/A' else 'N/A'
                                found_items[config_name] = {
                                    'line_number': var_data.get('line_number', 0),
                                    'file_path': file_path,
                                    'reason': f"detect variable {config_name} {actual_value} (match requirement: {expected_value}) at line {var_data.get('line_number', 0)} of file {file_name}"
                                }
                            else:
                                # Variable value mismatch
                                file_path = var_data.get('file_path', 'N/A')
                                file_name = Path(file_path).name if file_path != 'N/A' else 'N/A'
                                missing_items[config_name] = {
                                    'line_number': var_data.get('line_number', 0),
                                    'file_path': file_path,
                                    'reason': f"detect variable {config_name} {actual_value} (mismatch requirement: {expected_value}) at line {var_data.get('line_number', 0)} of file {file_name}"
                                }
                        except (ValueError, TypeError):
                            file_path = var_data.get('file_path', 'N/A')
                            file_name = Path(file_path).name if file_path != 'N/A' else 'N/A'
                            missing_items[config_name] = {
                                'line_number': var_data.get('line_number', 0),
                                'file_path': file_path,
                                'reason': f"detect variable {config_name} {actual_value} (invalid numeric value, requirement: {expected_value}) at line {var_data.get('line_number', 0)} of file {file_name}"
                            }
                    else:
                        # Variable not found
                        missing_items[config_name] = {
                            'line_number': 0,
                            'file_path': 'N/A',
                            'reason': f"variable {config_name} not found in any input files (requirement: {expected_value})"
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

        # Process found_items_base (no waiver needed - these are clean matches)
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

        # Step 5: Build output (FIXED: API-009 - pass dict directly)
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
# Entry Point
# =========================================================================

def main():
    """Main entry point."""
    checker = Check_12_0_0_25()
    checker.init_checker(Path(__file__))
    result = checker.execute_check()
    checker.write_output(result)
    return 0 if result.is_pass else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())