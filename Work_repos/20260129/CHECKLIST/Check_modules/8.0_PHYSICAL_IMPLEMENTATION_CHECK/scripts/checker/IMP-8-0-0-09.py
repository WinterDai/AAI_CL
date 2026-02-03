################################################################################
# Script Name: IMP-8-0-0-09.py
#
# Purpose:
#   Confirm we take care of the dynamic power optimization in the whole innovs flow(Check the Note)
#
# Logic:
#   - Parse get_default_switching_activity to extract switching activity parameters (seq_activity, input_activity, etc.)
#   - Parse getNanoRouteMode to extract power-driven routing settings (route_global_with_power_driven, route_global_exp_power_driven_effort)
#   - Parse getDesignMode to extract design-level power optimization settings (powerEffort, propagateActivity)
#   - Parse getOptMode to extract optimization power effort settings (opt_power_effort, opt_leakage_to_dynamic_ratio)
#   - Validate that critical power optimization parameters are defined and enabled across all flow stages
#   - Aggregate all power optimization settings and verify comprehensive dynamic power optimization coverage
#   - Report missing or disabled power optimization settings as violations
#
# Auto Type Detection:
#   Type 1: requirements.value=N/A, pattern_items [] (empty), waivers.value=N/A/0 → Boolean Check
#   Type 2: requirements.value>0, pattern_items [...] (defined), waivers.value=N/A/0 → Value Check
#   Type 3: requirements.value>0, pattern_items [...] (defined), waivers.value>0 → Value Check with Waiver Logic
#   Type 4: requirements.value=N/A, pattern_items [] (empty), waivers.value>0 → Boolean Check with Waiver Logic
#   Note: requirements.value indicates number of patterns for config validation (doesn't affect PASS/FAIL)
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
# Refactored: 2025-12-24 (Using checker_templates v1.1.0)
#
# Author: chyao
# Date: 2026-01-21
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
class Check_8_0_0_09(InputFileParserMixin, OutputBuilderMixin, WaiverHandlerMixin, BaseChecker):
    """
    IMP-8-0-0-09: Confirm we take care of the dynamic power optimization in the whole innovs flow(Check the Note)
    
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
    # DESCRIPTION & REASON CONSTANTS - Split by Type semantics (API-026)
    # =========================================================================
    # Type 1/4: Boolean checks - emphasize "found/not found" (existence)
    FOUND_DESC_TYPE1_4 = "All power optimization settings found and correctly configured"
    MISSING_DESC_TYPE1_4 = "Required power optimization settings not found or incorrectly configured"
    FOUND_REASON_TYPE1_4 = "All power optimization settings found and correctly configured in all four configuration files"
    MISSING_REASON_TYPE1_4 = "Required power optimization settings not found or incorrectly configured in configuration files"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_DESC_TYPE2_3 = "All required power optimization parameters matched expected configuration (7/7)"
    MISSING_DESC_TYPE2_3 = "Required power optimization parameters not satisfied (5/7 correct, 2 missing/incorrect)"
    FOUND_REASON_TYPE2_3 = "All required power optimization parameters matched and validated: switching activity configured, power-driven routing enabled, design power effort set to high, optimizer power settings correct"
    MISSING_REASON_TYPE2_3 = "Required power optimization parameters not satisfied: some parameters missing, have empty values, or incorrect configuration"
    
    # All Types (waiver description unified)
    WAIVED_DESC = "Power optimization configuration issues waived"
    
    # Waiver parameters (Type 3/4 ONLY)
    WAIVED_BASE_REASON = "Power optimization configuration deviation waived per design team approval"
    UNUSED_WAIVER_REASON = "Waiver not matched - no corresponding power optimization configuration issue found"
    
    def __init__(self):
        """Initialize the checker."""
        super().__init__(
            check_module="8.0_PHYSICAL_IMPLEMENTATION_CHECK",
            item_id="IMP-8-0-0-09",
            item_desc="Confirm we take care of the dynamic power optimization in the whole innovs flow(Check the Note)"
        )
        # Custom member variables for parsed data
        self._parsed_items: List[Dict[str, Any]] = []
        self._switching_activity_params: Dict[str, Any] = {}
        self._nanoroute_params: Dict[str, Any] = {}
        self._design_mode_params: Dict[str, Any] = {}
        self._opt_mode_params: Dict[str, Any] = {}
    
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
        except Exception as e:
            # Handle unexpected errors
            return create_check_result(
                is_pass=False,
                reason=f"Checker execution failed: {str(e)}",
                details=[],
                summary={}
            )
    
    # =========================================================================
    # Input Parsing (Common for All Types)
    # =========================================================================
    
    def _parse_input_files(self) -> Dict[str, Any]:
        """
        Parse input files to extract power optimization configuration information.
        
        Parses four configuration files:
        1. get_default_switching_activity - switching activity parameters for dynamic power analysis
        2. getNanoRouteMode - power-driven routing settings
        3. getDesignMode - design-level power optimization settings
        4. getOptMode - optimization power effort and leakage-to-dynamic ratio settings
        
        Returns:
            Dict with parsed data:
            - 'items': List[Dict] - All power optimization settings with name, value, status, source file
            - 'metadata': Dict - Aggregated metadata from all files (counts per file type)
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
                self.create_missing_files_error(["No input files configured"])
            )
        
        # 2. Initialize parsing structures
        items = []
        metadata = {}
        errors = []
        switching_activity_params = {}
        nanoroute_params = {}
        design_mode_params = {}
        opt_mode_params = {}
        
        # 3. Parse each input file for power optimization information
        for file_path in valid_files:
            file_name = Path(file_path).name
            
            try:
                if file_name == 'get_default_switching_activity':
                    file_items = self._parse_switching_activity_file(file_path, switching_activity_params, errors)
                    items.extend(file_items)
                elif file_name == 'getNanoRouteMode':
                    file_items = self._parse_nanoroute_mode_file(file_path, nanoroute_params, errors)
                    items.extend(file_items)
                elif file_name == 'getDesignMode':
                    file_items = self._parse_design_mode_file(file_path, design_mode_params, errors)
                    items.extend(file_items)
                elif file_name == 'getOptMode':
                    file_items = self._parse_opt_mode_file(file_path, opt_mode_params, errors)
                    items.extend(file_items)
            except Exception as e:
                errors.append(f"Error parsing {file_name}: {str(e)}")
        
        # 4. Store frequently reused data on self
        self._parsed_items = items
        self._switching_activity_params = switching_activity_params
        self._nanoroute_params = nanoroute_params
        self._design_mode_params = design_mode_params
        self._opt_mode_params = opt_mode_params
        
        metadata = {
            'total_settings': len(items),
            'switching_activity_count': len(switching_activity_params),
            'nanoroute_count': len(nanoroute_params),
            'design_mode_count': len(design_mode_params),
            'opt_mode_count': len(opt_mode_params)
        }
        
        return {
            'items': items,
            'metadata': metadata,
            'errors': errors,
            'switching_activity': switching_activity_params,
            'nanoroute_mode': nanoroute_params,
            'design_mode': design_mode_params,
            'opt_mode': opt_mode_params
        }
    # Helper Methods (Optional - Add as needed)
    

    # =========================================================================
    # Type 1: Boolean Check

    def _execute_type1(self) -> CheckResult:
        """
        Type 1: Boolean check without waiver support.

        Validates that all critical power optimization parameters are correctly
        configured across all four configuration files (get_default_switching_activity,
        getNanoRouteMode, getDesignMode, getOptMode).

        Returns:
            CheckResult with found_items (correctly configured parameters) and
            missing_items (violations - missing or incorrectly configured parameters).
        """
        violations = self._type1_core_logic()

        # Build found_items from correctly configured parameters
        data = self._parse_input_files()
        all_params = data.get('items', [])

        # Extract base parameter names from violations keys for filtering
        # Violation keys are like "getDesignMode -powerEffort low (expected: high)"
        # We need to match against base name "getDesignMode -powerEffort"
        violation_base_names = set()
        for viol_key in violations.keys():
            # Extract base name by removing value and "(expected: ...)" suffix
            base_name = viol_key.split()[0] + ' ' + viol_key.split()[1] if len(viol_key.split()) >= 2 else viol_key
            violation_base_names.add(base_name)

        found_items = {}
        for param in all_params:
            param_name = param.get('name', '')
            param_value = param.get('value', '')
            # Only include parameters that are NOT in violations (match by base name)
            if param_name not in violation_base_names:
                # Format: getDesignMode -powerEffort high
                display_name = f"{param_name} {param_value}" if param_value else param_name
                found_items[display_name] = {
                    'name': display_name,
                    'line_number': param.get('line_number', 0),
                    'file_path': param.get('file_path', 'N/A')
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

    def _type1_core_logic(self) -> dict[str, dict]:
        """
        Core Type 1 boolean check logic (shared by Type 1 and Type 4).

        Validates all critical power optimization parameters across four configuration files:
        1. get_default_switching_activity: input_activity, clip_activity_to_domain_freq
        2. getNanoRouteMode: route_global_with_power_driven, route_global_exp_power_driven_effort
        3. getDesignMode: powerEffort, propagateActivity
        4. getOptMode: opt_leakage_to_dynamic_ratio, opt_route_type_for_power, opt_power_effort

        Returns:
            Dict of violations: {param_name: {'line_number': ..., 'file_path': ..., 'reason': ...}}
            Empty dict if all checks pass.
        """
        data = self._parse_input_files()
        items = data.get('items', [])
        errors = data.get('errors', [])

        violations = {}

        # If parsing errors occurred, report them as violations
        if errors:
            for error in errors:
                violations[f"Parse Error: {error}"] = {
                    'line_number': 0,
                    'file_path': 'N/A',
                    'reason': f"Failed to parse configuration file: {error}"
                }

        # Define expected parameter configurations
        expected_params = {
            'get_default_switching_activity -input_activity': {
                'expected_value': '0.15',
                'check_type': 'numeric',
                'description': 'Input activity parameter'
            },
            'get_default_switching_activity -clip_activity_to_domain_freq': {
                'expected_value': 'true',
                'check_type': 'boolean',
                'description': 'Clip activity to domain frequency'
            },
            'getNanoRouteMode -route_global_with_power_driven': {
                'expected_value': 'true',
                'check_type': 'boolean',
                'description': 'Power-driven routing'
            },
            'getNanoRouteMode -route_global_exp_power_driven_effort': {
                'expected_value': 'medium',
                'check_type': 'enum',
                'valid_values': ['low', 'medium', 'high'],
                'description': 'Power-driven routing effort'
            },
            'getDesignMode -powerEffort': {
                'expected_value': 'high',
                'check_type': 'enum',
                'valid_values': ['none', 'low', 'medium', 'high'],
                'description': 'Design power effort'
            },
            'getDesignMode -propagateActivity': {
                'expected_value': 'true',
                'check_type': 'boolean',
                'description': 'Activity propagation'
            },
            'getOptMode -opt_leakage_to_dynamic_ratio': {
                'expected_value': '0.2',
                'check_type': 'numeric',
                'description': 'Leakage to dynamic ratio'
            },
            'getOptMode -opt_route_type_for_power': {
                'expected_value': 'true',
                'check_type': 'boolean',
                'description': 'Route type for power optimization'
            },
            'getOptMode -opt_power_effort': {
                'expected_value': 'high',
                'check_type': 'enum',
                'valid_values': ['none', 'low', 'medium', 'high'],
                'description': 'Optimization power effort'
            }
        }

        # Build a lookup dict from parsed items
        found_params = {}
        for item in items:
            param_name = item.get('name', '')
            found_params[param_name] = item

        # Check each expected parameter
        for param_key, param_config in expected_params.items():
            expected_value = param_config['expected_value']
            
            if param_key not in found_params:
                # Parameter not found in any file
                # Format: getDesignMode -powerEffort NOT_FOUND (expected: high)
                display_name = f"{param_key} NOT_FOUND (expected: {expected_value})"
                violations[display_name] = {
                    'name': display_name,
                    'line_number': 0,
                    'file_path': 'N/A',
                    'reason': f"{param_config['description']} not found in configuration files"
                }
            else:
                # Parameter found, validate its value
                param_item = found_params[param_key]
                actual_value = param_item.get('value', '').strip()
                check_type = param_config['check_type']

                # Check if value is empty or undefined
                if not actual_value or actual_value == '{ }' or actual_value == '{}':
                    # Format: getDesignMode -powerEffort {} (expected: high)
                    display_name = f"{param_key} {{}} (expected: {expected_value})"
                    violations[display_name] = {
                        'name': display_name,
                        'line_number': param_item.get('line_number', 0),
                        'file_path': param_item.get('file_path', 'N/A'),
                        'reason': f"{param_config['description']} value not defined (expected: {expected_value})"
                    }
                    continue

                # Validate based on check type
                is_valid = False

                if check_type == 'boolean':
                    # Boolean check: must match expected value (case-insensitive)
                    is_valid = actual_value.lower() == expected_value.lower()
                    if not is_valid:
                        # Format: getDesignMode -powerEffort false (expected: true)
                        display_name = f"{param_key} {actual_value} (expected: {expected_value})"
                        violations[display_name] = {
                            'name': display_name,
                            'line_number': param_item.get('line_number', 0),
                            'file_path': param_item.get('file_path', 'N/A'),
                            'reason': f"{param_config['description']} set to '{actual_value}' (expected: {expected_value})"
                        }

                elif check_type == 'numeric':
                    # Numeric check: must match expected value
                    try:
                        actual_float = float(actual_value)
                        expected_float = float(expected_value)
                        is_valid = abs(actual_float - expected_float) < 0.001
                        if not is_valid:
                            # Format: getOptMode -opt_leakage_to_dynamic_ratio 0.5 (expected: 0.2)
                            display_name = f"{param_key} {actual_value} (expected: {expected_value})"
                            violations[display_name] = {
                                'name': display_name,
                                'line_number': param_item.get('line_number', 0),
                                'file_path': param_item.get('file_path', 'N/A'),
                                'reason': f"{param_config['description']} set to '{actual_value}' (expected: {expected_value})"
                            }
                    except ValueError:
                        display_name = f"{param_key} {actual_value} (invalid)"
                        violations[display_name] = {
                            'name': display_name,
                            'line_number': param_item.get('line_number', 0),
                            'file_path': param_item.get('file_path', 'N/A'),
                            'reason': f"{param_config['description']} has invalid numeric value '{actual_value}' (expected: {expected_value})"
                        }

                elif check_type == 'enum':
                    # Enum check: must be in valid values and match expected
                    valid_values = param_config.get('valid_values', [])
                    if actual_value.lower() not in [v.lower() for v in valid_values]:
                        display_name = f"{param_key} {actual_value} (invalid)"
                        violations[display_name] = {
                            'name': display_name,
                            'line_number': param_item.get('line_number', 0),
                            'file_path': param_item.get('file_path', 'N/A'),
                            'reason': f"{param_config['description']} has invalid value '{actual_value}' (valid: {', '.join(valid_values)})"
                        }
                    elif actual_value.lower() != expected_value.lower():
                        # Format: getDesignMode -powerEffort low (expected: high)
                        display_name = f"{param_key} {actual_value} (expected: {expected_value})"
                        violations[display_name] = {
                            'name': display_name,
                            'line_number': param_item.get('line_number', 0),
                            'file_path': param_item.get('file_path', 'N/A'),
                            'reason': f"{param_config['description']} set to '{actual_value}' (expected: {expected_value})"
                        }

        return violations

    # =========================================================================
    # Type 4: Boolean Check with Waiver Logic

    def _execute_type4(self) -> CheckResult:
        """
        Type 4: Boolean check with waiver support (reuses Type 1 core logic).

        Performs the same validation as Type 1, but allows violations to be waived.
        Violations are classified as:
        - Waived: Matched against waive_items (shown as INFO with [WAIVER] tag)
        - Unwaived: Not matched (shown as ERROR, causes FAIL)

        Returns:
            CheckResult with found_items (correct configs), missing_items (unwaived violations),
            waived_items (waived violations), and unused_waivers.
        """
        violations = self._type1_core_logic()

        # Build found_items from correctly configured parameters
        data = self._parse_input_files()
        all_params = data.get('items', [])

        # Extract base parameter names from violations keys for filtering
        violation_base_names = set()
        for viol_key in violations.keys():
            base_name = viol_key.split()[0] + ' ' + viol_key.split()[1] if len(viol_key.split()) >= 2 else viol_key
            violation_base_names.add(base_name)

        found_items = {}
        for param in all_params:
            param_name = param.get('name', '')
            param_value = param.get('value', '')
            # Only include parameters that are NOT in violations (match by base name)
            if param_name not in violation_base_names:
                # Format: getDesignMode -powerEffort high
                display_name = f"{param_name} {param_value}" if param_value else param_name
                found_items[display_name] = {
                    'name': display_name,
                    'line_number': param.get('line_number', 0),
                    'file_path': param.get('file_path', 'N/A')
                }

        # FIXED: Use waivers.get() instead of get_waive_items()
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
    # Type 2: Value Check

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

    def _type2_core_logic(self) -> tuple[dict[str, dict], dict[str, dict]]:
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

        # Parse pattern_items to extract parameter name and expected value
        # Format: "command -parameter expected_value"
        # Example: "get_default_switching_activity -input_activity 0.15"
        for pattern in pattern_items:
            parts = pattern.split()
            if len(parts) < 3:
                # Invalid pattern format
                missing_items[pattern] = {
                    'line_number': 0,
                    'file_path': 'N/A',
                    'reason': f'Invalid pattern format: {pattern}'
                }
                continue

            command = parts[0]
            parameter = parts[1]
            expected_value = ' '.join(parts[2:])  # Handle multi-word values

            matched = False
            for item in items:
                item_name = item.get('name', '')
                item_value = item.get('value', '')

                # Match by checking if pattern is in item name
                if command.lower() in item_name.lower() and parameter.lower() in item_name.lower():
                    # Check if value matches expected value
                    # Handle special cases: empty values "{ }", boolean values, numeric values
                    item_value_clean = str(item_value).strip()
                    expected_value_clean = str(expected_value).strip()

                    # Check for empty value patterns
                    is_empty = item_value_clean in ['{}', '{ }', '', 'none', 'None']

                    # Case-insensitive comparison for string values
                    value_matches = (item_value_clean.lower() == expected_value_clean.lower())

                    if value_matches and not is_empty:
                        # Value matches and is not empty - found
                        # Format: getDesignMode -powerEffort high
                        display_name = f"{command} {parameter} {item_value_clean}"
                        found_items[display_name] = {
                            'name': display_name,
                            'line_number': item.get('line_number', 0),
                            'file_path': item.get('file_path', 'N/A')
                        }
                        matched = True
                    else:
                        # Value doesn't match or is empty - missing with reason
                        # Format with actual value: getDesignMode -powerEffort low (expected: high)
                        if is_empty:
                            reason = f'Parameter value not defined (found: {item_value_clean}, expected: {expected_value_clean})'
                            display_name = f"{command} {parameter} {{}} (expected: {expected_value_clean})"
                        else:
                            reason = f'Parameter value mismatch (found: {item_value_clean}, expected: {expected_value_clean})'
                            display_name = f"{command} {parameter} {item_value_clean} (expected: {expected_value_clean})"

                        missing_items[display_name] = {
                            'name': display_name,
                            'line_number': item.get('line_number', 0),
                            'file_path': item.get('file_path', 'N/A'),
                            'reason': reason
                        }
                        matched = True
                    break

            if not matched:
                # Parameter not found in any file
                # Format: getDesignMode -powerEffort NOT_FOUND (expected: high)
                display_name = f"{command} {parameter} NOT_FOUND (expected: {expected_value})"
                missing_items[display_name] = {
                    'name': display_name,
                    'line_number': 0,
                    'file_path': 'N/A',
                    'reason': f'Parameter "{parameter}" not found in command "{command}"'
                }

        return found_items, missing_items

    # =========================================================================
    # Type 3: Value Check with Waiver Logic

    def _execute_type3(self) -> CheckResult:
        """Type 3: Pattern/value check with waiver support (reuses Type 2 core logic)."""
        # Step 1: Get found/missing items using Type 2's core logic
        found_items_base, violations = self._type2_core_logic()

        # Step 2: Parse waiver configuration
        # FIXED: Use waivers.get() instead of get_waive_items()
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
    def _parse_switching_activity_file(self, file_path: Path, params_dict: Dict, errors: List) -> List[Dict[str, Any]]:
        """
        Parse get_default_switching_activity file.
        
        Extracts switching activity parameters for dynamic power analysis.
        Pattern 1: -parameter_name {numeric_value}
        Pattern 2: -parameter_name { } (empty/undefined)
        
        Args:
            file_path: Path to get_default_switching_activity file
            params_dict: Dictionary to store extracted parameters
            errors: List to append parsing errors
            
        Returns:
            List of parsed parameter items with metadata
        """
        items = []
        
        # Pattern 1: Parameter with value in braces
        pattern_with_value = re.compile(r'^-([a-zA-Z_]+)\s+\{\s*([^}]*)\s*\}')
        
        # Critical parameters that must be defined
        critical_params = ['seq_activity', 'input_activity', 'clip_activity_to_domain_freq']
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    
                    # Try pattern with value
                    match = pattern_with_value.search(line)
                    if match:
                        param_name = match.group(1)
                        param_value = match.group(2).strip()
                        
                        # Check if value is empty
                        if not param_value:
                            item = {
                                'name': f"get_default_switching_activity -{param_name}",
                                'command': 'get_default_switching_activity',
                                'parameter': f'-{param_name}',
                                'value': '{}',
                                'status': 'undefined',
                                'is_critical': param_name in critical_params,
                                'line_number': line_num,
                                'file_path': str(file_path),
                                'file_type': 'get_default_switching_activity',
                                'category': 'switching_activity',
                                'source': 'get_default_switching_activity'
                            }
                            items.append(item)
                            params_dict[param_name] = {'value': None, 'line_number': line_num}
                        else:
                            item = {
                                'name': f"get_default_switching_activity -{param_name}",
                                'command': 'get_default_switching_activity',
                                'parameter': f'-{param_name}',
                                'value': param_value,
                                'status': 'defined',
                                'is_critical': param_name in critical_params,
                                'line_number': line_num,
                                'file_path': str(file_path),
                                'file_type': 'get_default_switching_activity',
                                'category': 'switching_activity',
                                'source': 'get_default_switching_activity'
                            }
                            items.append(item)
                            params_dict[param_name] = {'value': param_value, 'line_number': line_num}
        except Exception as e:
            errors.append(f"Error reading get_default_switching_activity: {str(e)}")
        
        return items
    
    def _parse_nanoroute_mode_file(self, file_path: Path, params_dict: Dict, errors: List) -> List[Dict[str, Any]]:
        """
        Parse getNanoRouteMode file.
        
        Extracts power-driven routing settings.
        Pattern: -setting_name value # metadata
        
        Args:
            file_path: Path to getNanoRouteMode file
            params_dict: Dictionary to store extracted parameters
            errors: List to append parsing errors
            
        Returns:
            List of parsed parameter items with metadata
        """
        items = []
        
        # Pattern: Parameter line with value (comment is optional)
        # Supports: "-param_name value # comment" OR "-param_name value"
        pattern_setting = re.compile(r'^-([\w_]+)\s+(\S+)(?:\s*#.*)?$')
        pattern_metadata = re.compile(r'#\s*enums=\{([^}]+)\},\s*default=(\S+),\s*(user setting|default)')
        
        # Critical power-related parameters
        power_params = [
            'route_global_with_power_driven',
            'route_global_exp_power_driven_effort'
        ]
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line_num, line in enumerate(f, 1):
                    line_stripped = line.strip()
                    if not line_stripped or line_stripped.startswith('#'):
                        continue
                    
                    # Extract setting name and value
                    match = pattern_setting.search(line_stripped)
                    if match:
                        param_name = match.group(1)
                        current_value = match.group(2).strip()
                        
                        # Only track power-related parameters
                        if param_name in power_params:
                            # Extract metadata if present
                            meta_match = pattern_metadata.search(line)
                            status = 'user setting'
                            if meta_match:
                                status = meta_match.group(3)
                            
                            item = {
                                'name': f"getNanoRouteMode -{param_name}",
                                'command': 'getNanoRouteMode',
                                'parameter': f'-{param_name}',
                                'value': current_value,
                                'status': status,
                                'line_number': line_num,
                                'file_path': str(file_path),
                                'file_type': 'getNanoRouteMode',
                                'category': 'nanoroute',
                                'source': 'getNanoRouteMode'
                            }
                            items.append(item)
                            params_dict[param_name] = {'value': current_value, 'line_number': line_num}
        except Exception as e:
            errors.append(f"Error reading getNanoRouteMode: {str(e)}")
        
        return items
    
    def _parse_design_mode_file(self, file_path: Path, params_dict: Dict, errors: List) -> List[Dict[str, Any]]:
        """
        Parse getDesignMode file.
        
        Extracts design-level power optimization settings.
        Pattern: -parameter value # metadata
        
        Args:
            file_path: Path to getDesignMode file
            params_dict: Dictionary to store extracted parameters
            errors: List to append parsing errors
            
        Returns:
            List of parsed parameter items with metadata
        """
        items = []
        
        # Pattern 5: Parameter with value and metadata comment
        pattern_setting = re.compile(r'^-([\w]+)\s+([^#]+?)\s*#\s*(.+)$')
        pattern_metadata = re.compile(r'#.*?(user setting|default)')
        
        # Critical power-related parameters
        power_params = ['powerEffort', 'propagateActivity']
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line_num, line in enumerate(f, 1):
                    line_stripped = line.strip()
                    if not line_stripped or line_stripped.startswith('#'):
                        continue
                    
                    # Extract setting name and value
                    match = pattern_setting.search(line_stripped)
                    if match:
                        param_name = match.group(1)
                        current_value = match.group(2).strip()
                        
                        # Only track power-related parameters
                        if param_name in power_params:
                            # Extract metadata if present
                            meta_match = pattern_metadata.search(line)
                            status = 'user setting'
                            if meta_match:
                                status = meta_match.group(1)
                            
                            item = {
                                'name': f"getDesignMode -{param_name}",
                                'command': 'getDesignMode',
                                'parameter': f'-{param_name}',
                                'value': current_value,
                                'status': status,
                                'line_number': line_num,
                                'file_path': str(file_path),
                                'file_type': 'getDesignMode',
                                'category': 'design_mode',
                                'source': 'getDesignMode'
                            }
                            items.append(item)
                            params_dict[param_name] = {'value': current_value, 'line_number': line_num}
        except Exception as e:
            errors.append(f"Error reading getDesignMode: {str(e)}")
        
        return items
    
    def _parse_opt_mode_file(self, file_path: Path, params_dict: Dict, errors: List) -> List[Dict[str, Any]]:
        """
        Parse getOptMode file.
        
        Extracts optimizer power effort and leakage-to-dynamic ratio settings.
        Pattern: -parameter value # metadata
        
        Args:
            file_path: Path to getOptMode file
            params_dict: Dictionary to store extracted parameters
            errors: List to append parsing errors
            
        Returns:
            List of parsed parameter items with metadata
        """
        items = []
        
        # Pattern 7: Parameter name and value extraction
        pattern_setting = re.compile(r'^-([a-zA-Z_]+(?:_[a-zA-Z_]+)*)\s+([^#\s]+(?:\s+[^#\s]+)*?)\s*(?:#|$)')
        pattern_metadata = re.compile(r'#.*?(user setting|default)')
        
        # Critical power-related parameters
        power_params = ['opt_power_effort', 'opt_leakage_to_dynamic_ratio', 'opt_route_type_for_power']
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line_num, line in enumerate(f, 1):
                    line_stripped = line.strip()
                    if not line_stripped or line_stripped.startswith('#'):
                        continue
                    
                    # Extract setting name and value
                    match = pattern_setting.search(line_stripped)
                    if match:
                        param_name = match.group(1)
                        current_value = match.group(2).strip()
                        
                        # Only track power-related parameters
                        if param_name in power_params:
                            # Extract metadata if present
                            meta_match = pattern_metadata.search(line)
                            status = 'user setting'
                            if meta_match:
                                status = meta_match.group(1)
                            
                            item = {
                                'name': f"getOptMode -{param_name}",
                                'command': 'getOptMode',
                                'parameter': f'-{param_name}',
                                'value': current_value,
                                'status': status,
                                'line_number': line_num,
                                'file_path': str(file_path),
                                'file_type': 'getOptMode',
                                'category': 'opt_mode',
                                'source': 'getOptMode'
                            }
                            items.append(item)
                            params_dict[param_name] = {'value': current_value, 'line_number': line_num}
        except Exception as e:
            errors.append(f"Error reading getOptMode: {str(e)}")
        
        return items


# =========================================================================
# Entry Point
# =========================================================================

def main():
    """Main entry point."""
    checker = Check_8_0_0_09()
    checker.init_checker(Path(__file__))
    result = checker.execute_check()
    checker.write_output(result)
    return 0 if result.is_pass else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())