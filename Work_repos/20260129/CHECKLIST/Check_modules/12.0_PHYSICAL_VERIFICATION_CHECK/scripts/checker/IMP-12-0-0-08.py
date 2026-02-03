################################################################################
# Script Name: IMP-12-0-0-08.py
#
# Purpose:
#   Confirm the MIM_ANT rule deck setting is correct. (For MIG,please check with AMS team about the MIM cell type (MIM or SHDMIM) because the MIM_ANT rule will be different).
#
# Logic:
#   - Parse sourceme file to extract configuration variables (setenv/set commands)
#   - Parse PVL log file to extract configuration variables (VARIABLE = value format)
#   - PVL log values take precedence over sourceme values (overwrite registry)
#   - Validate pattern_items (YAML dictionaries) against registry
#   - Compare registry values against expected values (case-insensitive for enabled/disabled)
#   - Classify items: found_items (correct values), missing_items (incorrect/not found)
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
class Check_12_0_0_08(InputFileParserMixin, OutputBuilderMixin, WaiverHandlerMixin, BaseChecker):
    """
    IMP-12-0-0-08: Confirm the MIM_ANT rule deck setting is correct. (For MIG,please check with AMS team about the MIM cell type (MIM or SHDMIM) because the MIM_ANT rule will be different).
    
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
    FOUND_DESC_TYPE1_4 = "MIM antenna rule deck configuration found and validated"
    MISSING_DESC_TYPE1_4 = "MIM antenna rule deck configuration not found in setup files"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_DESC_TYPE2_3 = "MIM antenna rule deck setting matched expected configuration (1/1)"
    MISSING_DESC_TYPE2_3 = "MIM antenna rule deck setting does not match expected configuration (0/1 satisfied)"
    
    # All Types (waiver description unified)
    WAIVED_DESC = "Waived MIM antenna rule deck configuration mismatches"
    
    # ⭐ REASON CONSTANTS - Split by Type semantics (API-025)
    # ALL Types pass found_reason/missing_reason, but use different constants
    
    # Type 1/4: Boolean checks - emphasize "found/not found" (existence)
    FOUND_REASON_TYPE1_4 = "MIM antenna configuration variables found in PVL log and sourceme files"
    MISSING_REASON_TYPE1_4 = "Required MIM antenna configuration variables not found in PVL log or sourceme files"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_REASON_TYPE2_3 = "MIM antenna rule deck setting matched and validated against expected configuration"
    MISSING_REASON_TYPE2_3 = "MIM antenna rule deck setting not satisfied - expected 'disabled' state for FHDMIM variable"
    
    # Waiver-related (Type 3/4 only)
    WAIVED_BASE_REASON = "MIM antenna rule deck configuration mismatch waived per design team approval"
    UNUSED_WAIVER_REASON = "Waiver entry not matched - no corresponding MIM antenna configuration mismatch found"
    
    def __init__(self):
        """Initialize the checker."""
        super().__init__(
            check_module="12.0_PHYSICAL_VERIFICATION_CHECK",
            item_id="IMP-12-0-0-08",
            item_desc="Confirm the MIM_ANT rule deck setting is correct. (For MIG,please check with AMS team about the MIM cell type (MIM or SHDMIM) because the MIM_ANT rule will be different)."
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
        Parse input files to extract MIM antenna configuration variables.
        
        Parses two file types:
        1. Sourceme file (do_cmd_3star_ANT_MIM_sourceme): setenv/set commands
        2. PVL log file (do_pvs_ANT_MIM_pvl.log): VARIABLE = value format
        
        PVL log values take precedence over sourceme values (always overwrite).
        
        Returns:
            Dict with parsed data:
            - 'items': List[Dict] - Configuration variables with values
            - 'metadata': Dict - File metadata
            - 'errors': List - Parsing errors
            - 'registry': Dict - Variable registry with metadata
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
        config_registry = {}
        
        # Patterns for parsing (matching IMP-12-0-0-07 format)
        pattern_variable = re.compile(r'^variable\s+(\w+)\s*=\s*"?([^";]+)"?;?')
        pattern_warning = re.compile(r'^\[WARN\]:\s*(.+?)\s+at line\s+(\d+)\s+in file\s+(.+?)\s+is\s+(.+)')
        pattern_include = re.compile(r'^include\s+"([^"]+)"')
        pattern_define = re.compile(r'^\s*(//)?(#DEFINE)\s+(\w+)\s*(?://(.*))?')
        pattern_layout_system = re.compile(r'^LAYOUT\s+SYSTEM\s+(\w+)')
        pattern_layout_primary = re.compile(r'^LAYOUT\s+PRIMARY\s+(\S+)')
        
        # 3. Parse each input file for ANT_MIM rule deck configuration
        # Step 3a: Parse sourceme file first (lower priority)
        sourceme_files = [f for f in valid_files if 'sourceme' in str(f)]
        for file_path in sourceme_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line_num, line in enumerate(f, 1):
                        # Parse #DEFINE switches
                        match_define = pattern_define.match(line)
                        if match_define:
                            comment_prefix = match_define.group(1)
                            define_name = match_define.group(3)
                            enabled = (comment_prefix is None)
                            value = 'enabled' if enabled else 'disabled'
                            
                            config_registry[define_name] = {
                                'value': value,
                                'source': 'sourceme',
                                'enabled': enabled,
                                'line_number': line_num,
                                'file_path': str(file_path)
                            }
                        
                        # Parse LAYOUT SYSTEM (metadata only)
                        match_system = pattern_layout_system.match(line)
                        if match_system:
                            metadata['layout_system'] = match_system.group(1)
                        
                        # Parse LAYOUT PRIMARY (metadata only)
                        match_primary = pattern_layout_primary.match(line)
                        if match_primary:
                            metadata['primary_cell'] = match_primary.group(1)
            except Exception as e:
                errors.append(f"Error parsing {file_path}: {str(e)}")
        
        # Step 3b: Parse PVL log file (higher priority - ALWAYS overwrites)
        pvl_files = [f for f in valid_files if 'pvl.log' in str(f)]
        for file_path in pvl_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line_num, line in enumerate(f, 1):
                        # Parse variable definitions (ALWAYS overwrite registry)
                        match_var = pattern_variable.match(line)
                        if match_var:
                            var_name = match_var.group(1)
                            var_value = match_var.group(2).strip()
                            enabled = (var_value.lower() != 'disabled')
                            
                            # CRITICAL: ALWAYS overwrite (remove "if not in registry" check)
                            config_registry[var_name] = {
                                'value': var_value.lower(),
                                'source': 'pvl',
                                'enabled': enabled,
                                'line_number': line_num,
                                'file_path': str(file_path)
                            }
                        
                        # Parse warnings (informational only)
                        match_warn = pattern_warning.match(line)
                        if match_warn:
                            setting_name = match_warn.group(1)
                            warn_line = match_warn.group(2)
                            warn_file = match_warn.group(3)
                            warn_reason = match_warn.group(4)
                            # Log but don't affect registry
                            metadata.setdefault('warnings', []).append({
                                'setting': setting_name,
                                'line': warn_line,
                                'file': warn_file,
                                'reason': warn_reason
                            })
                        
                        # Parse include statements (metadata)
                        match_include = pattern_include.match(line)
                        if match_include:
                            metadata['rule_deck_path'] = match_include.group(1)
            except Exception as e:
                errors.append(f"Error parsing {file_path}: {str(e)}")
        
        # Convert registry to items list
        for setting_name, setting_data in config_registry.items():
            items.append({
                'name': setting_name,
                'value': setting_data['value'],
                'source': setting_data['source'],
                'enabled': setting_data['enabled'],
                'line_number': setting_data['line_number'],
                'file_path': setting_data['file_path']
            })
        
        # 4. Store frequently reused data on self
        self._parsed_items = items
        self._config_registry = config_registry
        self._metadata = metadata
        
        # Store config_registry in metadata for access by type methods
        metadata['config_registry'] = config_registry
        
        return {
            'items': items,
            'metadata': metadata,
            'errors': errors,
            'registry': config_registry
        }
    
    # =========================================================================
    # Type 1: Boolean Check
    # =========================================================================
    
    def _execute_type1(self) -> CheckResult:
        """
        Type 1: Boolean check without waiver support.
        
        Validates MIM_ANT rule deck configuration by checking:
        1. Required configuration variables exist in PVL log or sourceme files
        2. Variable values match expected settings (case-insensitive for enabled/disabled)
        
        Returns PASS if all required variables are found with correct values.
        Returns FAIL if any required variables are missing or have incorrect values.
        """
        violations = self._type1_core_logic()
        
        # Build found_items from clean configurations (variables with correct values)
        data = self._parse_input_files()
        registry = data.get('registry', {})
        
        found_items = {}
        for var_name, var_data in registry.items():
            # Only include variables that are NOT in violations
            if var_name not in violations:
                found_items[var_name] = {
                    'name': var_name,
                    'line_number': var_data.get('line_number', 0),
                    'file_path': var_data.get('file_path', 'N/A')
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
        
        Validates MIM_ANT rule deck configuration variables against expected values.
        
        Logic:
        1. Parse sourceme and PVL log files to extract configuration variables
        2. Build registry with PVL log values taking precedence over sourceme values
        3. Validate pattern_items (YAML dictionaries) against registry
        4. Compare registry values against expected values (case-insensitive for enabled/disabled)
        5. Classify violations: missing variables or incorrect values
        
        Returns:
            Dict of violations: {var_name: {'line_number': ..., 'file_path': ..., 'reason': ...}}
            Empty dict if all checks pass.
        """
        data = self._parse_input_files()
        registry = data.get('registry', {})
        errors = data.get('errors', [])
        
        violations = {}
        
        # Check for parsing errors
        if errors:
            for error in errors:
                violations[f"ParseError_{len(violations)}"] = {
                    'line_number': 0,
                    'file_path': 'N/A',
                    'reason': error
                }
        
        # Get pattern_items from requirements
        requirements = self.get_requirements()
        pattern_items = requirements.get('pattern_items', [])
        
        # If no pattern_items defined, check if registry is empty (no config found)
        if not pattern_items:
            if not registry:
                violations['MIM_ANT_CONFIG'] = {
                    'line_number': 0,
                    'file_path': 'N/A',
                    'reason': 'Required MIM antenna configuration variables not found in PVL log or sourceme files'
                }
            return violations
        
        # Validate each pattern_item against registry
        for pattern in pattern_items:
            if not isinstance(pattern, dict):
                violations[f"InvalidPattern_{len(violations)}"] = {
                    'line_number': 0,
                    'file_path': 'N/A',
                    'reason': f'Invalid pattern_item format: {pattern} (expected dictionary)'
                }
                continue
            
            var_name = pattern.get('name', '')
            expected_value = pattern.get('value', '')
            
            if not var_name:
                violations[f"MissingName_{len(violations)}"] = {
                    'line_number': 0,
                    'file_path': 'N/A',
                    'reason': f'Pattern item missing "name" field: {pattern}'
                }
                continue
            
            # Check if variable exists in registry
            if var_name not in registry:
                violations[var_name] = {
                    'line_number': 0,
                    'file_path': 'N/A',
                    'reason': f'Required configuration variable "{var_name}" not found in PVL log or sourceme files'
                }
                continue
            
            # Get actual value from registry
            actual_value = registry[var_name].get('value', '')
            
            # Compare values (case-insensitive for enabled/disabled keywords)
            if self._normalize_config_value(actual_value) != self._normalize_config_value(expected_value):
                violations[var_name] = {
                    'line_number': registry[var_name].get('line_number', 0),
                    'file_path': registry[var_name].get('file_path', 'N/A'),
                    'reason': f'Configuration mismatch: expected "{expected_value}", found "{actual_value}"'
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
            - found_items: {setting_name: {'line_number': ..., 'file_path': ...}}
            - missing_items: {setting_name: {'line_number': ..., 'file_path': ..., 'reason': ...}}
        """
        data = self._parse_input_files()
        config_registry = data.get('config_registry', {})
        
        requirements = self.item_data.get('requirements', {})
        pattern_items = requirements.get('pattern_items', [])
        
        found_items = {}
        missing_items = {}
        
        # Validate each required setting against expected value
        for pattern_dict in pattern_items:
            # Extract setting name and expected value from dictionary
            if not isinstance(pattern_dict, dict):
                continue
            
            for setting_name, expected_value in pattern_dict.items():
                if setting_name in config_registry:
                    setting_data = config_registry[setting_name]
                    actual_value = setting_data.get('value', '')
                    
                    # Case-insensitive comparison of actual vs expected value
                    if actual_value.lower() == str(expected_value).lower():
                        # Setting matches expected value
                        found_items[setting_name] = {
                            'line_number': setting_data.get('line_number', 0),
                            'file_path': setting_data.get('file_path', 'N/A')
                        }
                    else:
                        # Setting exists but has wrong value
                        missing_items[setting_name] = {
                            'line_number': setting_data.get('line_number', 0),
                            'file_path': setting_data.get('file_path', 'N/A'),
                            'reason': f'Setting state does not match expected value or setting is missing from configuration (expected: {expected_value}, actual: {actual_value})'
                        }
                else:
                    # Setting not found in configuration
                    missing_items[setting_name] = {
                        'line_number': 0,
                        'file_path': 'N/A',
                        'reason': f'Setting state does not match expected value or setting is missing from configuration (expected: {expected_value}, not found in files)'
                    }
        
        return found_items, missing_items
    
    def _compare_values(self, actual: str, expected: str) -> bool:
        """
        Compare actual value against expected value.
        Case-insensitive comparison for enabled/disabled states.
        
        Args:
            actual: Actual value from configuration
            expected: Expected value from pattern_items
            
        Returns:
            True if values match, False otherwise
        """
        # Normalize values for comparison
        actual_normalized = str(actual).strip().lower()
        expected_normalized = str(expected).strip().lower()
        
        return actual_normalized == expected_normalized
    
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
        
        # Process found_items_base (no waiver needed - these are correct values)
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
        
        Same validation as Type 1, but with waiver support:
        - Violations matching waive_items → waived_items (PASS)
        - Violations not matching waivers → missing_items (FAIL)
        - Unused waivers → unused_waivers (WARN)
        
        Returns PASS if all violations are waived.
        Returns FAIL if any unwaived violations exist.
        """
        violations = self._type1_core_logic()
        
        # Build found_items from clean configurations
        data = self._parse_input_files()
        registry = data.get('registry', {})
        
        found_items = {}
        for var_name, var_data in registry.items():
            # Only include variables that are NOT in violations
            if var_name not in violations:
                found_items[var_name] = {
                    'name': var_name,
                    'line_number': var_data.get('line_number', 0),
                    'file_path': var_data.get('file_path', 'N/A')
                }
        
        # Parse waiver configuration (FIXED: Use waivers.get() instead of get_waive_items())
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # Split violations into waived and unwaived
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
        
        # Find unused waivers
        unused_waivers = [w for w in waive_dict.keys() if w not in used_waivers]
        
        # FIXED: Pass dict directly, not list(dict.values())
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
    # Helper Methods
    # =========================================================================
    
    def _normalize_config_value(self, value: str) -> str:
        """
        Normalize configuration values for case-insensitive comparison.
        
        Converts enabled/disabled keywords to lowercase for comparison.
        Preserves other values as-is.
        
        Args:
            value: Configuration value to normalize
            
        Returns:
            Normalized value (lowercase for enabled/disabled, original otherwise)
        """
        if not isinstance(value, str):
            return str(value)
        
        value_lower = value.lower().strip()
        
        # Normalize enabled/disabled keywords
        if value_lower in ['enabled', 'disabled', 'enable', 'disable', 'true', 'false', 'yes', 'no']:
            return value_lower
        
        # Return original value for other cases (preserve case for paths, numbers, etc.)
        return value.strip()


# =========================================================================
# Entry Point
# =========================================================================

def main():
    """Main entry point."""
    checker = Check_12_0_0_08()
    checker.init_checker(Path(__file__))
    result = checker.execute_check()
    checker.write_output(result)
    return 0 if result.is_pass else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())