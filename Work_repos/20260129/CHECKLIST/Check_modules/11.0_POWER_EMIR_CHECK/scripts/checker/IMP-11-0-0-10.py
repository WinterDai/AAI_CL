################################################################################
# Script Name: IMP-11-0-0-10.py
#
# Purpose:
#   Confirm static power analysis results matches the requirement.
#
# Logic:
#   - Parse VDD_VSS_div.iv to extract NOMINAL_VOLTAGE and first instance DIV value
#   - Calculate Static_IR_Drop percentage: ((NOMINAL_VOLTAGE - PWR_IV) / NOMINAL_VOLTAGE) * 100%
#   - Parse results_VDD to extract maximum current density (J/JMAX) from "Results for rj" section
#   - Parse results_VSS to extract maximum current density (J/JMAX) from "Results for rj" section
#   - Compare Static_IR_Drop against 3% threshold and Power_EM against 1.0 threshold
#   - Report PASS if all metrics within limits, FAIL if any metric exceeds threshold
#   - Support waiver logic for Type 3/4 to exempt specific metric violations
#
# Auto Type Detection:
#   Type 1: requirements.value=N/A, waivers.value=N/A/0 → Boolean check (data extraction only)
#   Type 2: requirements.value>0, pattern_items exists, waivers.value=N/A/0 → Value comparison
#   Type 3: requirements.value>0, pattern_items exists, waivers.value>0 → Value with waiver logic
#   Type 4: requirements.value=N/A, waivers.value>0 → Boolean with waiver logic
#
# Output Behavior (Type 2/3 - Check README "Output Behavior" section!):
#   status_check: pattern_items = metric thresholds to CHECK STATUS (only output matched metrics)
#     - found_items = metrics matched AND value within threshold
#     - missing_items = metrics matched BUT value exceeds threshold
#
# Waiver Tag Rules:
#   When waivers.value > 0 (Type 3/4):
#     - All waive_items related INFO/FAIL/WARN reason suffix: [WAIVER]
#   When waivers.value = 0 (Type 1/2):
#     - waive_items output as INFO with suffix: [WAIVED_INFO]
#     - FAIL/WARN converted to INFO with suffix: [WAIVED_AS_INFO]
#   All types support value = N/A
#
# Refactored: 2026-01-08 (Using checker_templates v1.1.0)
#
# Author: Zhihan Zhen
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
class Check_11_0_0_10(InputFileParserMixin, OutputBuilderMixin, WaiverHandlerMixin, BaseChecker):
    """
    IMP-11-0-0-10: Confirm static power analysis results matches the requirement.
    
    Checking Types:
    - Type 1: requirements=N/A, pattern_items [], waivers=N/A/0 → Boolean Check (data extraction only)
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
    FOUND_DESC_TYPE1_4 = "All power analysis data successfully extracted"
    MISSING_DESC_TYPE1_4 = "Power analysis data extraction failed"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_DESC_TYPE2_3 = "All power analysis metrics meet requirements (3/3 passed)"
    MISSING_DESC_TYPE2_3 = "Power analysis metrics exceed requirements (violations detected)"
    
    # All Types (waiver description unified)
    WAIVED_DESC = "Waived power analysis violations"
    
    # ⭐ REASON CONSTANTS - Split by Type semantics (API-025)
    # ALL Types pass found_reason/missing_reason, but use different constants
    
    # Type 1/4: Boolean checks - emphasize "found/not found" (existence)
    FOUND_REASON_TYPE1_4 = "Static IR Drop and Power EM data extracted successfully"
    MISSING_REASON_TYPE1_4 = "Required power analysis data not found in input files"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_REASON_TYPE2_3 = "All power metrics matched requirements and validated successfully"
    MISSING_REASON_TYPE2_3 = "Power metric exceeds threshold requirement"
    
    # Waiver-related (Type 3/4 only)
    WAIVED_BASE_REASON = "Power analysis violation waived per design team approval"
    UNUSED_WAIVER_REASON = "Waiver not matched - no corresponding power violation found"
    
    def __init__(self):
        """Initialize the checker."""
        super().__init__(
            check_module="11.0_POWER_EMIR_CHECK",
            item_id="IMP-11-0-0-10",
            item_desc="Confirm static power analysis results matches the requirement."
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
        Parse input files to extract power analysis metrics.
        
        Parses three input files:
        1. VDD_VSS_div.iv - Extract NOMINAL_VOLTAGE and first instance PWR_IV for Static_IR_Drop calculation
        2. results_VDD - Extract maximum current density (J/JMAX) from "Results for rj" section
        3. results_VSS - Extract maximum current density (J/JMAX) from "Results for rj" section
        
        Returns:
            Dict with parsed data:
            - 'items': List[Dict] - Power metrics with values and metadata
            - 'metadata': Dict - File metadata (nominal voltage, file paths)
            - 'errors': List - Any parsing errors encountered
        """
        # 1. Validate input files (raises ConfigurationError if missing)
        valid_files, missing_files = self.validate_input_files()
        if missing_files:
            raise ConfigurationError(
                self.create_missing_files_error(missing_files)
            )
        
        items = []
        metadata = {}
        errors = []
        
        # Separate files by type
        vdd_vss_div_file = None
        results_files = []  # Store all result files
        
        for file_path in valid_files:
            file_name = file_path.name
            if 'VDD_VSS_div.iv' in file_name:
                vdd_vss_div_file = file_path
            elif 'result' in file_name.lower():
                results_files.append(file_path)
        
        # Parse VDD_VSS_div.iv for Static_IR_Drop
        if vdd_vss_div_file:
            try:
                nominal_voltage = None
                first_instance_pwr_iv = None
                in_data_section = False
                
                with open(vdd_vss_div_file, 'r', encoding='utf-8', errors='ignore') as f:
                    for line_num, line in enumerate(f, 1):
                        # Extract NOMINAL_VOLTAGE
                        if not nominal_voltage:
                            match = re.match(r'^NOMINAL_VOLTAGE\s+([\d.]+)', line)
                            if match:
                                nominal_voltage = float(match.group(1))
                                metadata['nominal_voltage'] = nominal_voltage
                                metadata['nominal_voltage_line'] = line_num
                                metadata['nominal_voltage_file'] = str(vdd_vss_div_file)
                                continue
                        
                        # Detect BEGIN section
                        if re.match(r'^BEGIN\s*$', line):
                            in_data_section = True
                            continue
                        
                        # Extract first instance PWR_IV after BEGIN
                        if in_data_section and first_instance_pwr_iv is None:
                            match = re.match(r'^-\s+(\S+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s*$', line)
                            if match:
                                # Group 2 is PWR_IV (second numeric field)
                                first_instance_pwr_iv = float(match.group(2))
                                
                                # Calculate Static_IR_Drop percentage
                                if nominal_voltage and nominal_voltage > 0:
                                    static_ir_drop_percent = ((nominal_voltage - first_instance_pwr_iv) / nominal_voltage) * 100
                                    
                                    items.append({
                                        'name': 'Static_IR_Drop',
                                        'value': static_ir_drop_percent,
                                        'unit': '%',
                                        'threshold': 3.0,
                                        'line_number': line_num,
                                        'file_path': str(vdd_vss_div_file),
                                        'raw_data': {
                                            'nominal_voltage': nominal_voltage,
                                            'pwr_iv': first_instance_pwr_iv,
                                            'instance_name': match.group(1)
                                        }
                                    })
                                break
                
                # Check if required data was found
                if nominal_voltage is None:
                    errors.append({
                        'file': str(vdd_vss_div_file),
                        'error': 'NOMINAL_VOLTAGE header not found',
                        'line_number': 0,
                        'file_path': str(vdd_vss_div_file)
                    })
                if first_instance_pwr_iv is None:
                    errors.append({
                        'file': str(vdd_vss_div_file),
                        'error': 'No instance data found after BEGIN marker',
                        'line_number': 0,
                        'file_path': str(vdd_vss_div_file)
                    })
            except Exception as e:
                errors.append({
                    'file': str(vdd_vss_div_file),
                    'error': f'Failed to parse VDD_VSS_div.iv: {str(e)}',
                    'line_number': 0,
                    'file_path': str(vdd_vss_div_file)
                })
        
        # Parse all result files for Power_EM
        for result_file in results_files:
            try:
                in_rj_section = False
                power_em_found = False
                
                with open(result_file, 'r', encoding='utf-8', errors='ignore') as f:
                    for line_num, line in enumerate(f, 1):
                        # Detect rj section
                        if re.match(r'^Results for rj', line):
                            in_rj_section = True
                            continue
                        
                        # Extract maximum current density
                        if in_rj_section:
                            match = re.search(r'Minimum, Average, Maximum Current Density \(J/JMAX\):\s*([\d.eE+-]+),\s*([\d.eE+-]+),\s*([\d.eE+-]+)', line)
                            if match:
                                max_current_density = float(match.group(3))
                                
                                # Determine power domain name from filename
                                file_name = result_file.name
                                if 'VDD' in file_name:
                                    power_domain = 'VDD'
                                elif 'VSS' in file_name:
                                    power_domain = 'VSS'
                                else:
                                    # Extract domain from filename pattern
                                    domain_match = re.search(r'results?[_-]?(\w+)', file_name, re.IGNORECASE)
                                    power_domain = domain_match.group(1) if domain_match else 'UNKNOWN'
                                
                                items.append({
                                    'name': f'{power_domain}_Power_EM',
                                    'value': max_current_density,
                                    'unit': '',
                                    'threshold': 1.0,
                                    'line_number': line_num,
                                    'file_path': str(result_file),
                                    'raw_data': {
                                        'min': float(match.group(1)),
                                        'avg': float(match.group(2)),
                                        'max': max_current_density,
                                        'power_domain': power_domain
                                    }
                                })
                                power_em_found = True
                                break
                
                # Check if rj section was found
                if not power_em_found:
                    errors.append({
                        'file': str(result_file),
                        'error': 'Results for rj section not found or no current density data',
                        'line_number': 0,
                        'file_path': str(result_file)
                    })
            except Exception as e:
                errors.append({
                    'file': str(result_file),
                    'error': f'Failed to parse result file: {str(e)}',
                    'line_number': 0,
                    'file_path': str(result_file)
                })
        
        # Store frequently reused data on self
        self._parsed_items = items
        self._metadata = metadata
        
        return {
            'items': items,
            'metadata': metadata,
            'errors': errors
        }
    
    # =========================================================================
    # Type 1: Boolean Check (Data Extraction Only)
    # =========================================================================
    
    def _execute_type1(self) -> CheckResult:
        """
        Type 1: Boolean Check (Data Extraction Only).
        
        Validates that all required power analysis data is present and parseable.
        Does NOT compare against target thresholds - only checks if data can be extracted.
        
        Returns:
            CheckResult with is_pass based on data extraction success
        """
        # Parse input
        data = self._parse_input_files()
        items = data.get('items', [])
        errors = data.get('errors', [])
        
        # Convert items to dict with metadata for source file/line display
        found_items = {}
        
        for item in items:
            # Type 1: Only check if data was extracted, don't compare with threshold
            # Display extracted value without comparison
            if 'Power_EM' in item['name']:
                display_name = f"{item['name']}: {item['value']:.4f}"
            else:
                display_name = f"{item['name']}: {item['value']:.2f}{item['unit']}"
            
            found_items[display_name] = {
                'name': display_name,
                'line_number': item.get('line_number', 0),
                'file_path': item.get('file_path', 'N/A')
            }
        
        # Convert errors to missing items
        missing_items = []
        if errors:
            for error in errors:
                missing_items.append(error['error'])
        
        # Use template helper (auto-handles waiver=0)
        # Type 1: Use TYPE1_4 reason (emphasize "found/not found")
        return self.build_complete_output(
            found_items=found_items,
            missing_items=missing_items,
            found_desc=self.FOUND_DESC_TYPE1_4,
            missing_desc=self.MISSING_DESC_TYPE1_4,
            found_reason=self.FOUND_REASON_TYPE1_4,
            missing_reason=self.MISSING_REASON_TYPE1_4
        )
    
    # =========================================================================
    # Type 2: Value Check
    # =========================================================================
    
    def _execute_type2(self) -> CheckResult:
        """
        Type 2: Value Check.
        
        Validates power metrics against threshold requirements.
        Uses status_check mode: only outputs metrics matching pattern_items.
        
        Returns:
            CheckResult with is_pass based on value comparison
        """
        # Parse input
        data = self._parse_input_files()
        items = data.get('items', [])
        errors = data.get('errors', [])
        
        # Get pattern_items (metric thresholds to check)
        pattern_items = self.item_data.get('requirements', {}).get('pattern_items', [])
        
        # Build dict of all parsed metrics
        all_metrics = {item['name']: item for item in items}
        
        # status_check mode: Check metrics matching pattern_items
        found_items = {}      # Metrics within threshold
        missing_items = {}    # Metrics exceeding threshold
        missing_patterns = [] # Patterns not found in parsed data
        
        for pattern in pattern_items:
            # Extract metric name from pattern (e.g., "Static_IR_Drop < 3%" -> "Static_IR_Drop")
            # Pattern can be "Static_IR_Drop" or "VDD_Power_EM" or "VSS_Power_EM"
            metric_name = pattern.strip()
            
            # Check if metric exists in parsed data
            matched = False
            for item_name, item_data in all_metrics.items():
                if metric_name in item_name:
                    matched = True
                    # Check if value within threshold
                    if item_data['value'] < item_data['threshold']:
                        # Status correct - within threshold
                        # For Type 2: Print actual value in display name
                        if item_name == 'Static_IR_Drop':
                            display_name = f"{item_name}: {item_data['value']:.2f}{item_data['unit']} < target ({item_data['threshold']}{item_data['unit']})"
                        else:
                            # For Power_EM metrics, show actual value
                            display_name = f"{item_name}: {item_data['value']:.4f} < target ({item_data['threshold']})"
                        
                        found_items[display_name] = {
                            'name': display_name,
                            'line_number': item_data.get('line_number', 0),
                            'file_path': item_data.get('file_path', 'N/A')
                        }
                    else:
                        # Status wrong - exceeds threshold
                        # For Type 2: Print actual value in display name
                        if item_name == 'Static_IR_Drop':
                            display_name = f"{item_name}: {item_data['value']:.2f}{item_data['unit']} >= target ({item_data['threshold']}{item_data['unit']})"
                        else:
                            # For Power_EM metrics, show actual value
                            display_name = f"{item_name}: {item_data['value']:.4f} >= target ({item_data['threshold']})"
                        
                        missing_items[display_name] = {
                            'name': display_name,
                            'line_number': item_data.get('line_number', 0),
                            'file_path': item_data.get('file_path', 'N/A')
                        }
                    break
            
            if not matched:
                missing_patterns.append(pattern)
        
        # Handle parsing errors as missing items
        if errors:
            for error in errors:
                error_name = f"{error['file']}: {error['error']}"
                missing_items[error_name] = {
                    'name': error_name,
                    'line_number': error.get('line_number', 0),
                    'file_path': error.get('file_path', 'N/A')
                }
        
        # Convert missing_items dict to list of names for build_complete_output
        missing_list = list(missing_items.keys()) if missing_items else missing_patterns
        
        # Use template helper (auto-handles waiver=0)
        # Type 2: Use TYPE2_3 desc+reason (emphasize "matched/satisfied")
        return self.build_complete_output(
            found_items=found_items,
            missing_items=missing_list,
            found_desc=self.FOUND_DESC_TYPE2_3,
            missing_desc=self.MISSING_DESC_TYPE2_3,
            found_reason=self.FOUND_REASON_TYPE2_3,
            missing_reason=self.MISSING_REASON_TYPE2_3
        )
    
    # =========================================================================
    # Type 3: Value Check with Waiver Logic
    # =========================================================================
    
    def _execute_type3(self) -> CheckResult:
        """
        Type 3: Value check with waiver support.
        
        Same pattern search logic as Type 2, plus waiver classification.
        
        Uses WaiverHandlerMixin for waiver processing:
        - parse_waive_items(waive_items_raw): Parse waiver configuration
        - match_waiver_entry(item, waive_dict): Match item against waivers
        
        Uses OutputBuilderMixin for result construction:
        - build_complete_output(...): Assemble final CheckResult with auto-formatting
        
        Returns:
            CheckResult with FAIL for unwaived, INFO for waived items
        """
        # Parse input
        parsed_data = self._parse_input_files()
        items = parsed_data.get('items', [])
        errors = parsed_data.get('errors', [])
        
        # CORRECT! Use waivers.get() directly to preserve dict format
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # Get pattern_items (metric thresholds to check)
        pattern_items = self.item_data.get('requirements', {}).get('pattern_items', [])
        
        # Build dict of all parsed metrics
        all_metrics = {item['name']: item for item in items}
        
        # status_check mode: Check metrics matching pattern_items
        found_items = {}      # Metrics within threshold (not waived)
        violations = {}       # Metrics exceeding threshold (to be classified)
        missing_patterns = [] # Patterns not found in parsed data
        
        for pattern in pattern_items:
            # Extract metric name from pattern
            metric_name = pattern.strip()
            
            # Check if metric exists in parsed data
            matched = False
            for item_name, item_data in all_metrics.items():
                if metric_name in item_name:
                    matched = True
                    # Check if value within threshold
                    if item_data['value'] < item_data['threshold']:
                        # Status correct - within threshold
                        if item_name == 'Static_IR_Drop':
                            display_name = f"{item_name}: {item_data['value']:.2f}{item_data['unit']} < target ({item_data['threshold']}{item_data['unit']})"
                        else:
                            display_name = f"{item_name}: {item_data['value']:.4f} < target ({item_data['threshold']})"
                        
                        found_items[display_name] = {
                            'name': display_name,
                            'line_number': item_data.get('line_number', 0),
                            'file_path': item_data.get('file_path', 'N/A')
                        }
                    else:
                        # Status wrong - exceeds threshold (violation)
                        if item_name == 'Static_IR_Drop':
                            display_name = f"{item_name}: {item_data['value']:.2f}{item_data['unit']} >= target ({item_data['threshold']}{item_data['unit']})"
                        else:
                            display_name = f"{item_name}: {item_data['value']:.4f} >= target ({item_data['threshold']})"
                        
                        violations[display_name] = {
                            'name': display_name,
                            'line_number': item_data.get('line_number', 0),
                            'file_path': item_data.get('file_path', 'N/A')
                        }
                    break
            
            if not matched:
                missing_patterns.append(pattern)
        
        # Handle parsing errors as violations
        if errors:
            for error in errors:
                error_name = f"{error['file']}: {error['error']}"
                violations[error_name] = {
                    'name': error_name,
                    'line_number': error.get('line_number', 0),
                    'file_path': error.get('file_path', 'N/A')
                }
        
        # Separate waived/unwaived violations using template helper
        waived_items = {}
        unwaived_items = {}
        
        for violation_name, violation_data in violations.items():
            # Extract base metric name for waiver matching
            base_name = violation_name.split(':')[0].strip()
            
            if self.match_waiver_entry(base_name, waive_dict):
                waived_items[violation_name] = violation_data
            else:
                unwaived_items[violation_name] = violation_data
        
        # Find unused waivers by checking if waiver names were used
        used_names = set()
        for violation_name in waived_items.keys():
            base_name = violation_name.split(':')[0].strip()
            used_names.add(base_name)
        
        unused_waivers = [name for name in waive_dict.keys() if name not in used_names]
        
        # Convert unwaived_items to list for missing_items parameter
        missing_list = list(unwaived_items.keys()) if unwaived_items else missing_patterns
        
        # Use template helper for automatic output formatting (waivers.value>0)
        # Type 3: Use TYPE2_3 desc+reason (emphasize "matched/satisfied")
        return self.build_complete_output(
            found_items=found_items,
            waived_items=waived_items,
            missing_items=missing_list,
            waive_dict=waive_dict,
            unused_waivers=unused_waivers,
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
        Type 4: Boolean check with waiver support (Type 1 + waiver).
        
        Same boolean check as Type 1 (data extraction only), plus waiver classification.
        Does NOT compare against target thresholds - only checks if data can be extracted.
        
        Use OutputBuilderMixin.build_complete_output() with has_waiver_value=True.
        
        Returns:
            CheckResult with waiver logic applied
        """
        # Parse input
        data = self._parse_input_files()
        items = data.get('items', [])
        errors = data.get('errors', [])
        
        # CORRECT! Use waivers.get() directly to preserve dict format
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # Convert items to dict with metadata
        found_items = {}
        
        for item in items:
            # Type 4: Only check if data was extracted, don't compare with threshold
            # Display extracted value without comparison
            if 'Power_EM' in item['name']:
                display_name = f"{item['name']}: {item['value']:.4f}"
            else:
                display_name = f"{item['name']}: {item['value']:.2f}{item['unit']}"
            
            found_items[display_name] = {
                'name': display_name,
                'line_number': item.get('line_number', 0),
                'file_path': item.get('file_path', 'N/A')
            }
        
        # Convert errors to violations dict
        violations = {}
        if errors:
            for error in errors:
                error_name = error['error']
                violations[error_name] = {
                    'name': error_name,
                    'line_number': error.get('line_number', 0),
                    'file_path': error.get('file_path', 'N/A')
                }
        
        # Separate waived/unwaived violations
        waived_items = {}
        unwaived_items = {}
        
        for violation_name, violation_data in violations.items():
            # Extract base metric name for waiver matching
            base_name = violation_name.split(':')[0].strip()
            
            if self.match_waiver_entry(base_name, waive_dict):
                waived_items[violation_name] = violation_data
            else:
                unwaived_items[violation_name] = violation_data
        
        # Find unused waivers
        used_names = set()
        for violation_name in waived_items.keys():
            base_name = violation_name.split(':')[0].strip()
            used_names.add(base_name)
        
        unused_waivers = [name for name in waive_dict.keys() if name not in used_names]
        
        # Convert unwaived_items to list for missing_items parameter
        missing_list = list(unwaived_items.keys())
        
        # Use template helper for automatic output formatting (waivers.value>0)
        # Type 4: Use TYPE1_4 reason (emphasize "found/not found")
        return self.build_complete_output(
            found_items=found_items,
            waived_items=waived_items,
            missing_items=missing_list,
            waive_dict=waive_dict,
            unused_waivers=unused_waivers,
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
    checker = Check_11_0_0_10()
    checker.init_checker(Path(__file__))
    result = checker.execute_check()
    checker.write_output(result)
    return 0 if result.is_pass else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())