################################################################################
# Script Name: IMP-11-0-0-02.py
#
# Purpose:
#   Confirm EMIR signoff criteria follows addendum or SOW, otherwise follow internal spec (design rule with IP specific margin)
#
# Logic:
#   - Parse input files to extract EMIR signoff criteria values (EM_TEMPERATURE, EM_LIFETIME, STATIC_IR_TARGET, DYNAMIC_IR_TARGET)
#   - Extract EMIR parameter values from configuration files using pattern matching
#   - Verify extracted values match required pattern_items specifications
#   - Support waiver for specific EMIR criteria deviations
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
class Check_11_0_0_02(InputFileParserMixin, OutputBuilderMixin, WaiverHandlerMixin, BaseChecker):
    """
    IMP-11-0-0-02: Confirm EMIR signoff criteria follows addendum or SOW, otherwise follow internal spec (design rule with IP specific margin)
    
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
    FOUND_DESC_TYPE1_4 = "EMIR signoff criteria found in configuration"
    MISSING_DESC_TYPE1_4 = "Required EMIR signoff criteria not found in configuration"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_DESC_TYPE2_3 = "EMIR signoff criteria matched required specifications"
    MISSING_DESC_TYPE2_3 = "EMIR signoff criteria not satisfied or missing from configuration"
    
    # All Types (waiver description unified)
    WAIVED_DESC = "Waived EMIR signoff criteria deviations"
    
    # ⭐ REASON CONSTANTS - Split by Type semantics (API-025)
    # ALL Types pass found_reason/missing_reason, but use different constants
    
    # Type 1/4: Boolean checks - emphasize "found/not found" (existence)
    FOUND_REASON_TYPE1_4 = "All required EMIR signoff criteria found in design configuration"
    MISSING_REASON_TYPE1_4 = "Required EMIR signoff criteria not found in design configuration files"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_REASON_TYPE2_3 = "All EMIR signoff criteria matched and validated against requirements (EM_TEMPERATURE=105°C, EM_LIFETIME=87600hrs, STATIC_IR=3%, DYNAMIC_IR=15%)"
    MISSING_REASON_TYPE2_3 = "EMIR signoff criteria not satisfied - missing or incorrect values for required parameters"
    
    # Waiver-related (Type 3/4 only)
    WAIVED_BASE_REASON = "EMIR signoff criteria deviation waived per project-specific requirements"
    UNUSED_WAIVER_REASON = "Waiver entry not matched - no corresponding EMIR criteria deviation found in configuration"
    
    def __init__(self):
        """Initialize the checker."""
        super().__init__(
            check_module="11.0_POWER_EMIR_CHECK",
            item_id="IMP-11-0-0-02",
            item_desc="Confirm EMIR signoff criteria follows addendum or SOW, otherwise follow internal spec (design rule with IP specific margin)"
        )
        # Custom member variables for parsed data
        self._parsed_items: List[Dict[str, Any]] = []
        self._metadata: Dict[str, str] = {}
        self._emir_criteria: Dict[str, str] = {}
    
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
        Parse input files to extract EMIR signoff criteria values.
        
        Extracts EMIR parameters from configuration files:
        - EM_TEMPERATURE: Electromigration temperature (e.g., 105°C)
        - EM_LIFETIME: Electromigration lifetime (e.g., 87600 hours = 10 years)
        - STATIC_IR_TARGET: Static IR drop target percentage (e.g., 3%)
        - DYNAMIC_IR_TARGET: Dynamic IR drop target percentage (e.g., 15%)
        
        Returns:
            Dict with parsed data:
            - 'items': List[Dict] - EMIR criteria found with values
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
        emir_criteria = {}
        
        # Define EMIR criteria patterns
        patterns = {
            'EM_TEMPERATURE': r'EM[_\s]*TEMPERATURE[:\s]*(\d+)',
            'EM_LIFETIME': r'EM[_\s]*LIFETIME[:\s]*(\d+)',
            'STATIC_IR_TARGET': r'STATIC[_\s]*IR[_\s]*TARGET[:\s]*(\d+)%?',
            'DYNAMIC_IR_TARGET': r'DYNAMIC[_\s]*IR[_\s]*TARGET[:\s]*(\d+)%?'
        }
        
        # 3. Parse each input file for EMIR signoff criteria
        for file_path in valid_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line_num, line in enumerate(f, 1):
                        # Check each EMIR criteria pattern
                        for criteria_name, pattern in patterns.items():
                            match = re.search(pattern, line, re.IGNORECASE)
                            if match:
                                value = match.group(1)
                                # Store criteria with value
                                criteria_key = f"{criteria_name}={value}"
                                
                                # Avoid duplicates
                                if criteria_key not in emir_criteria:
                                    emir_criteria[criteria_key] = {
                                        'name': criteria_key,
                                        'criteria_type': criteria_name,
                                        'value': value,
                                        'line_number': line_num,
                                        'file_path': str(file_path),
                                        'line_content': line.strip()
                                    }
                                    items.append(emir_criteria[criteria_key])
            except Exception as e:
                errors.append(f"Error parsing {file_path}: {str(e)}")
        
        # 4. Store frequently reused data on self
        self._parsed_items = items
        self._emir_criteria = emir_criteria
        
        return {
            'items': items,
            'metadata': metadata,
            'errors': errors,
            'clean_criteria': emir_criteria
        }
    
    # =========================================================================
    # Type 1: Boolean Check
    # =========================================================================
    
    def _execute_type1(self) -> CheckResult:
        """Type 1: Boolean check without waiver support."""
        violations = self._type1_core_logic()
        
        # ⚠️ CRITICAL: found_items MUST be dict[str, dict], NOT list!
        # Build dict from clean EMIR criteria (those that pass validation)
        data = self._parse_input_files()
        clean_criteria = data.get('clean_criteria', {})
        
        found_items = {}
        for criterion_name, criterion_data in clean_criteria.items():
            found_items[criterion_name] = {
                'name': criterion_name,
                'line_number': criterion_data.get('line_number', 0),
                'file_path': criterion_data.get('file_path', 'N/A')
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
        
        Validates EMIR signoff criteria against required specifications:
        - EM_TEMPERATURE: Must be present and valid
        - EM_LIFETIME: Must be present and valid
        - STATIC_IR_TARGET: Must be present and valid
        - DYNAMIC_IR_TARGET: Must be present and valid
        
        Returns:
            Dict of violations: {criterion_name: {'line_number': ..., 'file_path': ..., 'reason': ...}}
            Empty dict if all checks pass.
        """
        data = self._parse_input_files()
        items = data.get('items', [])
        errors = data.get('errors', [])
        
        violations = {}
        
        # Check for parsing errors first
        if errors:
            for error in errors:
                error_key = f"PARSE_ERROR_{len(violations)}"
                violations[error_key] = {
                    'line_number': 0,
                    'file_path': 'N/A',
                    'reason': error
                }
        
        # Required EMIR signoff criteria
        required_criteria = {
            'EM_TEMPERATURE': 'EMIR temperature specification',
            'EM_LIFETIME': 'EMIR lifetime specification',
            'STATIC_IR_TARGET': 'Static IR drop target',
            'DYNAMIC_IR_TARGET': 'Dynamic IR drop target'
        }
        
        # Track found criteria
        found_criteria = set()
        
        # Validate each parsed item
        for item in items:
            criterion_name = item.get('name', '')
            criterion_value = item.get('value', '')
            
            if criterion_name in required_criteria:
                found_criteria.add(criterion_name)
                
                # Validate criterion has a value
                if not criterion_value or criterion_value.strip() == '':
                    violations[criterion_name] = {
                        'line_number': item.get('line_number', 0),
                        'file_path': item.get('file_path', 'N/A'),
                        'reason': f'{required_criteria[criterion_name]} is missing value'
                    }
        
        # Check for missing required criteria
        missing_criteria = set(required_criteria.keys()) - found_criteria
        for criterion_name in missing_criteria:
            violations[criterion_name] = {
                'line_number': 0,
                'file_path': 'N/A',
                'reason': f'{required_criteria[criterion_name]} not found in configuration files'
            }
        
        return violations
    
    # =========================================================================
    # Type 2: Value Check
    # =========================================================================
    
    def _execute_type2(self) -> CheckResult:
        """Type 2: Pattern/value check without waiver support."""
        found_items, missing_items = self._type2_core_logic()
        
        # ⚠️ _type2_core_logic() returns dict[str, dict] for both found_items and missing_items
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
            - found_items: {item_name: {'line_number': ..., 'file_path': ...}}
            - missing_items: {item_name: {'line_number': ..., 'file_path': ..., 'reason': ...}}
        """
        data = self._parse_input_files()
        items = data.get('items', [])
        
        requirements = self.item_data.get('requirements', {})
        pattern_items = requirements.get('pattern_items', [])
        
        found_items = {}
        missing_items = {}
        
        # Check each required EMIR signoff criteria pattern
        for pattern in pattern_items:
            matched = False
            
            # Search for pattern in parsed EMIR configuration items
            for item in items:
                item_name = item.get('name', '')
                
                # EXACT MATCH: EMIR criteria are exact parameter=value pairs
                # Example: "EM_TEMPERATURE=105" must match exactly
                if pattern.lower() == item_name.lower():
                    found_items[pattern] = {
                        'line_number': item.get('line_number', 0),
                        'file_path': item.get('file_path', 'N/A')
                    }
                    matched = True
                    break
            
            if not matched:
                missing_items[pattern] = {
                    'line_number': 0,
                    'file_path': 'N/A',
                    'reason': f'EMIR signoff criteria "{pattern}" not found or value mismatch'
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
        
        # Process found_items_base (criteria that matched - no waiver needed)
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
        
        # Step 5: Build output (FIXED: API-009 - pass dict directly, not list)
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
        """Type 4: Boolean check with waiver support (reuses Type 1 core logic)."""
        violations = self._type1_core_logic()
        
        # ⚠️ CRITICAL: found_items MUST be dict[str, dict], NOT list!
        data = self._parse_input_files()
        clean_criteria = data.get('clean_criteria', {})
        
        found_items = {}
        for criterion_name, criterion_data in clean_criteria.items():
            found_items[criterion_name] = {
                'name': criterion_name,
                'line_number': criterion_data.get('line_number', 0),
                'file_path': criterion_data.get('file_path', 'N/A')
            }
        
        # FIXED: API-008 - Use waivers.get() instead of get_waive_items()
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
        
        # FIXED: API-009 - Pass dict directly, not list(dict.keys())
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
    checker = Check_11_0_0_02()
    checker.init_checker(Path(__file__))
    result = checker.execute_check()
    checker.write_output(result)
    return 0 if result.is_pass else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())