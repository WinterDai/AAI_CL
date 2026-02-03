################################################################################
# Script Name: IMP-15-0-0-02.py
#
# Purpose:
#   Confirm the PERC voltage setting is correct.(check the Note)
#
# Logic:
#   - Parse setup_vars.tcl to identify TT corner DDRIO libraries
#   - Extract library file paths containing both "tt" and "ddrio" patterns
#   - Read voltage_map entries from identified TT corner library files
#   - Parse voltage.txt to extract VARIABLE declarations with voltage values
#   - Compare voltage_map values from libraries against voltage.txt specifications
#   - Report mismatches as voltage setting errors
#
# Auto Type Detection:
#   Type 1: requirements.value=N/A, waivers.value=N/A/0 → Boolean check
#   Type 2: requirements.value>0, pattern_items exists, waivers.value=N/A/0 → Value comparison
#   Type 3: requirements.value>0, pattern_items exists, waivers.value>0 → Value with waiver logic
#   Type 4: requirements.value=N/A, waivers.value>0 → Boolean with waiver logic
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
# Refactored: 2025-12-26 (Using checker_templates v1.1.0)
#
# Author: yyin
# Date: 2025-12-18
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
class Check_15_0_0_02(InputFileParserMixin, OutputBuilderMixin, WaiverHandlerMixin, BaseChecker):
    """
    IMP-15-0-0-02: Confirm the PERC voltage setting is correct.(check the Note)
    
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
    # DESCRIPTION & REASON CONSTANTS - COPY FROM README Output Descriptions!
    # =========================================================================
    # Type 1/4: Boolean checks
    FOUND_DESC_TYPE1_4 = "All TT corner DDRIO library voltage_map entries found and validated against voltage.txt"
    MISSING_DESC_TYPE1_4 = "TT corner DDRIO library voltage mismatches found between voltage_map and voltage.txt"
    FOUND_REASON_TYPE1_4 = "All voltage_map entries from TT corner DDRIO libraries found to match voltage.txt specifications"
    MISSING_REASON_TYPE1_4 = "Voltage mismatches found in TT corner: voltage_map entries from DDRIO libraries do not match voltage.txt specifications"
    
    # Type 2/3: Pattern checks
    FOUND_DESC_TYPE2_3 = "All TT corner DDRIO library voltage_map entries matched voltage.txt specifications and validated"
    MISSING_DESC_TYPE2_3 = "TT corner DDRIO library voltage settings not satisfied - mismatches detected between voltage_map and voltage.txt"
    FOUND_REASON_TYPE2_3 = "All voltage_map entries from TT corner DDRIO libraries matched voltage.txt specifications and validated successfully"
    MISSING_REASON_TYPE2_3 = "TT corner voltage specifications not satisfied: voltage_map mismatches or missing/extra voltage definitions detected in DDRIO libraries"
    
    # All Types (waiver description)
    WAIVED_DESC = "TT corner DDRIO voltage violations waived per design approval"
    
    # Waiver parameters (Type 3/4 ONLY)
    WAIVED_BASE_REASON = "TT corner DDRIO voltage mismatch waived - approved exception per design team review"
    
    def __init__(self):
        """Initialize the checker."""
        super().__init__(
            check_module="15.0_ESD_PERC_CHECK",
            item_id="IMP-15-0-0-02",
            item_desc="Confirm the PERC voltage setting is correct.(check the Note)"
        )
        # Custom member variables for parsed data
        self._tt_ddrio_libs: List[Dict[str, Any]] = []
        self._voltage_spec: Dict[str, float] = {}
        self._voltage_map: Dict[str, Dict[str, float]] = {}
    
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
        Parse input files to extract relevant data.
        
        Parses:
        1. setup_vars.tcl - Identifies TT corner DDRIO libraries
        2. TT corner library files - Extracts voltage_map entries
        3. voltage.txt - Extracts voltage specifications
        
        Returns:
            Dict with parsed data:
            - 'items': List[Dict] - Voltage mismatches with metadata
            - 'metadata': Dict - Parsing statistics
            - 'errors': List - Parsing errors
        """
        # 1. Validate input files - IMPORTANT: returns tuple (valid_files_list, missing_files_list)
        valid_files, missing_files = self.validate_input_files()
        if missing_files:
            raise ConfigurationError(
                self.create_missing_files_error(missing_files)
            )
        
        # 2. Separate files by type
        setup_vars_files = [f for f in valid_files if 'setup_vars.tcl' in str(f)]
        voltage_txt_files = [f for f in valid_files if 'voltage.txt' in str(f)]
        
        if not setup_vars_files:
            raise ConfigurationError("setup_vars.tcl not found in input files")
        if not voltage_txt_files:
            raise ConfigurationError("voltage.txt not found in input files")
        
        # 3. Parse setup_vars.tcl to find TT corner DDRIO libraries
        self._parse_setup_vars(setup_vars_files[0])
        
        # 4. Parse voltage.txt to get voltage specifications
        self._parse_voltage_txt(voltage_txt_files[0])
        
        # 5. Extract voltage_map from TT corner library files
        self._extract_voltage_maps()
        
        # 6. Compare voltage_map against voltage.txt specifications
        mismatches = self._compare_voltages()
        
        # 7. Store frequently reused data on self
        self._parsed_items = mismatches
        
        return {
            'items': mismatches,
            'metadata': {
                'total_tt_libs': len(self._tt_ddrio_libs),
                'total_voltage_domains': len(self._voltage_spec),
                'total_mismatches': len(mismatches)
            },
            'errors': []
        }
    
    def _parse_setup_vars(self, file_path: Path) -> None:
        """
        Parse setup_vars.tcl to identify TT corner DDRIO libraries.
        
        Args:
            file_path: Path to setup_vars.tcl
        """
        lib_macro_pattern = re.compile(r'set\s+LIB_MACRO\(([^,]+),([^)]+)\)\s+"([^"]+)"')
        
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line_num, line in enumerate(f, 1):
                match = lib_macro_pattern.search(line)
                if match:
                    corner_name = match.group(1)
                    lib_type = match.group(2)
                    lib_path = match.group(3)
                    
                    # Check if this is a TT corner DDRIO library
                    # Must contain both "tt" and "ddrio" in the library path
                    lib_path_lower = lib_path.lower()
                    if 'tt' in lib_path_lower and 'ddrio' in lib_path_lower:
                        self._tt_ddrio_libs.append({
                            'corner_name': corner_name,
                            'lib_type': lib_type,
                            'lib_path': lib_path,
                            'line_number': line_num,
                            'file_path': str(file_path)
                        })
    
    def _parse_voltage_txt(self, file_path: Path) -> None:
        """
        Parse voltage.txt to extract voltage specifications.
        
        Args:
            file_path: Path to voltage.txt
        """
        variable_pattern = re.compile(r'^VARIABLE\s+"([^"]+)"\s+([0-9.]+)')
        
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                match = variable_pattern.search(line)
                if match:
                    var_name = match.group(1)
                    voltage = float(match.group(2))
                    self._voltage_spec[var_name] = voltage
    
    def _extract_voltage_maps(self) -> None:
        """
        Extract voltage_map entries from TT corner library files.
        """
        voltage_map_pattern = re.compile(r'voltage_map\s*\(\s*"?([^"]+)"?\s*,\s*([0-9.]+)\s*\)')
        
        for lib_info in self._tt_ddrio_libs:
            lib_path = Path(lib_info['lib_path'])
            
            # Skip if library file doesn't exist
            if not lib_path.exists():
                continue
            
            voltage_map = {}
            try:
                with open(lib_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        match = voltage_map_pattern.search(line)
                        if match:
                            domain_name = match.group(1)
                            voltage = float(match.group(2))
                            voltage_map[domain_name] = voltage
            except Exception:
                # Skip files that can't be read
                continue
            
            if voltage_map:
                self._voltage_map[lib_info['corner_name']] = voltage_map
    
    def _compare_voltages(self) -> List[Dict[str, Any]]:
        """
        Compare voltage_map values against voltage.txt specifications.
        
        Returns:
            List of voltage mismatches with metadata
        """
        mismatches = []
        
        for corner_name, voltage_map in self._voltage_map.items():
            # Find the library info for this corner
            lib_info = next((lib for lib in self._tt_ddrio_libs 
                           if lib['corner_name'] == corner_name), None)
            
            if not lib_info:
                continue
            
            for domain_name, actual_voltage in voltage_map.items():
                # Check if this domain exists in voltage.txt
                if domain_name in self._voltage_spec:
                    expected_voltage = self._voltage_spec[domain_name]
                    
                    # Compare voltages (allow small floating point tolerance)
                    if abs(actual_voltage - expected_voltage) > 0.001:
                        mismatch_name = f"{corner_name}:{domain_name}"
                        mismatches.append({
                            'name': mismatch_name,
                            'corner_name': corner_name,
                            'domain_name': domain_name,
                            'expected_voltage': expected_voltage,
                            'actual_voltage': actual_voltage,
                            'lib_path': lib_info['lib_path'],
                            'line_number': lib_info['line_number'],
                            'file_path': lib_info['file_path']
                        })
        
        return mismatches
    
    # =========================================================================
    # Type 1: Boolean Check
    # =========================================================================
    
    def _execute_type1(self) -> CheckResult:
        """
        Type 1: Boolean Check.
        
        Checks if TT corner DDRIO libraries have correct PERC voltage settings.
        
        Returns:
            CheckResult with is_pass based on check logic
        """
        # Parse input
        data = self._parse_input_files()
        mismatches = data.get('items', [])
        
        # Build found_items (all correct voltage_map entries)
        found_items = {}
        for corner_name, voltage_map in self._voltage_map.items():
            lib_info = next((lib for lib in self._tt_ddrio_libs 
                           if lib['corner_name'] == corner_name), None)
            if not lib_info:
                continue
            
            lib_filename = Path(lib_info['lib_path']).name
            
            for domain_name, actual_voltage in voltage_map.items():
                if domain_name in self._voltage_spec:
                    expected_voltage = self._voltage_spec[domain_name]
                    if abs(actual_voltage - expected_voltage) <= 0.001:
                        # Format: [lib_filename] voltage_map([domain])=[voltage]v - MATCHES voltage.txt
                        item_name = f"{lib_filename} voltage_map({domain_name})={actual_voltage}v - MATCHES voltage.txt"
                        found_items[item_name] = {
                            'name': item_name,
                            'line_number': lib_info.get('line_number', 0),
                            'file_path': lib_info.get('file_path', 'N/A')
                        }
        
        # Build missing_items (voltage mismatches)
        missing_items = {}
        for mismatch in mismatches:
            lib_filename = Path(mismatch['lib_path']).name
            domain_name = mismatch['domain_name']
            lib_voltage = mismatch['actual_voltage']
            spec_voltage = mismatch['expected_voltage']
            
            # Format: [lib_filename] voltage_map([domain]): VOLTAGE MISMATCH - lib=[lib_voltage]v spec=[spec_voltage]v
            item_name = f"{lib_filename} voltage_map({domain_name}): VOLTAGE MISMATCH - lib={lib_voltage}v spec={spec_voltage}v"
            missing_items[item_name] = {
                'name': item_name,
                'line_number': mismatch.get('line_number', 0),
                'file_path': mismatch.get('file_path', 'N/A'),
                'reason': f"Voltage mismatch in {lib_filename}: voltage_map({domain_name}) has {lib_voltage}v but voltage.txt specifies {spec_voltage}v"
            }
        
        # Use template helper - FIXED: Pass dict directly, not list
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
        
        Compares voltage_map values against voltage.txt specifications.
        Uses status_check mode: pattern_items are voltage domains to check status.
        
        Returns:
            CheckResult with is_pass based on value comparison
        """
        # Parse input
        data = self._parse_input_files()
        mismatches = data.get('items', [])
        
        # Get pattern_items (voltage domains to check)
        pattern_items = self.item_data.get('requirements', {}).get('pattern_items', [])
        
        # Build found_items (voltage domains with correct values)
        found_items = {}
        for corner_name, voltage_map in self._voltage_map.items():
            lib_info = next((lib for lib in self._tt_ddrio_libs 
                           if lib['corner_name'] == corner_name), None)
            
            if not lib_info:
                continue
            
            lib_filename = Path(lib_info['lib_path']).name
            
            for domain_name, actual_voltage in voltage_map.items():
                # Check if this domain is in pattern_items (if specified)
                if pattern_items and domain_name not in pattern_items:
                    continue
                
                # Check if voltage matches specification
                if domain_name in self._voltage_spec:
                    expected_voltage = self._voltage_spec[domain_name]
                    if abs(actual_voltage - expected_voltage) <= 0.001:
                        # Format: [lib_filename] voltage_map([domain])=[voltage]v - MATCHES voltage.txt
                        item_name = f"{lib_filename} voltage_map({domain_name})={actual_voltage}v - MATCHES voltage.txt"
                        found_items[item_name] = {
                            'name': item_name,
                            'line_number': lib_info.get('line_number', 0),
                            'file_path': lib_info.get('file_path', 'N/A')
                        }
        
        # Build missing_items (voltage domains with incorrect values)
        missing_items = {}
        for mismatch in mismatches:
            # Check if this domain is in pattern_items (if specified)
            if pattern_items and mismatch['domain_name'] not in pattern_items:
                continue
            
            lib_filename = Path(mismatch['lib_path']).name
            domain_name = mismatch['domain_name']
            lib_voltage = mismatch['actual_voltage']
            spec_voltage = mismatch['expected_voltage']
            
            # Format: [lib_filename] voltage_map([domain]): VOLTAGE MISMATCH - lib=[lib_voltage]v spec=[spec_voltage]v
            item_name = f"{lib_filename} voltage_map({domain_name}): VOLTAGE MISMATCH - lib={lib_voltage}v spec={spec_voltage}v"
            missing_items[item_name] = {
                'name': item_name,
                'line_number': mismatch.get('line_number', 0),
                'file_path': mismatch.get('file_path', 'N/A'),
                'reason': f"Voltage mismatch in {lib_filename}: voltage_map({domain_name}) has {lib_voltage}v but voltage.txt specifies {spec_voltage}v"
            }
        
        # Use template helper - FIXED: Pass dict directly, not list
        return self.build_complete_output(
            found_items=found_items,
            missing_items=missing_items,
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
        
        Returns:
            CheckResult with FAIL for unwaived, INFO for waived items
        """
        # Parse input
        parsed_data = self._parse_input_files()
        mismatches = parsed_data.get('items', [])
        
        # FIXED: Use waivers.get() directly to preserve dict format
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # Get pattern_items (voltage domains to check)
        pattern_items = self.item_data.get('requirements', {}).get('pattern_items', [])
        
        # Build found_items (voltage domains with correct values)
        found_items = {}
        for corner_name, voltage_map in self._voltage_map.items():
            lib_info = next((lib for lib in self._tt_ddrio_libs 
                           if lib['corner_name'] == corner_name), None)
            
            if not lib_info:
                continue
            
            lib_filename = Path(lib_info['lib_path']).name
            
            for domain_name, actual_voltage in voltage_map.items():
                # Check if this domain is in pattern_items (if specified)
                if pattern_items and domain_name not in pattern_items:
                    continue
                
                # Check if voltage matches specification
                if domain_name in self._voltage_spec:
                    expected_voltage = self._voltage_spec[domain_name]
                    if abs(actual_voltage - expected_voltage) <= 0.001:
                        # Format: [lib_filename] voltage_map([domain])=[voltage]v - MATCHES voltage.txt
                        item_name = f"{lib_filename} voltage_map({domain_name})={actual_voltage}v - MATCHES voltage.txt"
                        found_items[item_name] = {
                            'name': item_name,
                            'line_number': lib_info.get('line_number', 0),
                            'file_path': lib_info.get('file_path', 'N/A')
                        }
        
        # Separate waived/unwaived mismatches using template helper
        waived_items = {}
        unwaived_items = {}
        
        for mismatch in mismatches:
            # Check if this domain is in pattern_items (if specified)
            if pattern_items and mismatch['domain_name'] not in pattern_items:
                continue
            
            lib_filename = Path(mismatch['lib_path']).name
            domain_name = mismatch['domain_name']
            lib_voltage = mismatch['actual_voltage']
            spec_voltage = mismatch['expected_voltage']
            
            # Format: [lib_filename] voltage_map([domain]): VOLTAGE MISMATCH - lib=[lib_voltage]v spec=[spec_voltage]v
            item_name = f"{lib_filename} voltage_map({domain_name}): VOLTAGE MISMATCH - lib={lib_voltage}v spec={spec_voltage}v"
            
            if self.match_waiver_entry(item_name, waive_dict):
                waived_items[item_name] = {
                    'name': item_name,
                    'line_number': mismatch.get('line_number', 0),
                    'file_path': mismatch.get('file_path', 'N/A'),
                    'reason': f"Voltage mismatch in {lib_filename}: voltage_map({domain_name}) has {lib_voltage}v but voltage.txt specifies {spec_voltage}v"
                }
            else:
                unwaived_items[item_name] = {
                    'name': item_name,
                    'line_number': mismatch.get('line_number', 0),
                    'file_path': mismatch.get('file_path', 'N/A'),
                    'reason': f"Voltage mismatch in {lib_filename}: voltage_map({domain_name}) has {lib_voltage}v but voltage.txt specifies {spec_voltage}v"
                }
        
        # Find unused waivers
        used_names = set(waived_items.keys())
        unused_waivers = [name for name in waive_dict.keys() if name not in used_names]
        
        # Use template helper for automatic output formatting - FIXED: Pass dict directly
        return self.build_complete_output(
            found_items=found_items,
            waived_items=waived_items,
            missing_items=unwaived_items,
            waive_dict=waive_dict,
            unused_waivers=unused_waivers,
            found_desc=self.FOUND_DESC_TYPE2_3,
            missing_desc=self.MISSING_DESC_TYPE2_3,
            waived_desc=self.WAIVED_DESC,
            found_reason=self.FOUND_REASON_TYPE2_3,
            missing_reason=self.MISSING_REASON_TYPE2_3,
            waived_base_reason=self.WAIVED_BASE_REASON
        )
    
    # =========================================================================
    # Type 4: Boolean Check with Waiver Logic
    # =========================================================================
    
    def _execute_type4(self) -> CheckResult:
        """
        Type 4: Boolean check with waiver support (Type 1 + waiver).
        
        Same boolean check as Type 1 (no pattern_items), plus waiver classification.
        
        Returns:
            CheckResult with waiver logic applied
        """
        # Parse input
        data = self._parse_input_files()
        mismatches = data.get('items', [])
        
        # FIXED: Use waivers.get() directly to preserve dict format
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # Separate waived/unwaived mismatches
        waived_items = {}
        unwaived_items = {}
        
        for mismatch in mismatches:
            lib_filename = Path(mismatch['lib_path']).name
            domain_name = mismatch['domain_name']
            lib_voltage = mismatch['actual_voltage']
            spec_voltage = mismatch['expected_voltage']
            
            # Format: [lib_filename] voltage_map([domain]): VOLTAGE MISMATCH - lib=[lib_voltage]v spec=[spec_voltage]v
            item_name = f"{lib_filename} voltage_map({domain_name}): VOLTAGE MISMATCH - lib={lib_voltage}v spec={spec_voltage}v"
            
            if self.match_waiver_entry(item_name, waive_dict):
                waived_items[item_name] = {
                    'name': item_name,
                    'line_number': mismatch.get('line_number', 0),
                    'file_path': mismatch.get('file_path', 'N/A'),
                    'reason': f"Voltage mismatch in {lib_filename}: voltage_map({domain_name}) has {lib_voltage}v but voltage.txt specifies {spec_voltage}v"
                }
            else:
                unwaived_items[item_name] = {
                    'name': item_name,
                    'line_number': mismatch.get('line_number', 0),
                    'file_path': mismatch.get('file_path', 'N/A'),
                    'reason': f"Voltage mismatch in {lib_filename}: voltage_map({domain_name}) has {lib_voltage}v but voltage.txt specifies {spec_voltage}v"
                }
        
        # Build found_items (all correct voltage_map entries)
        found_items = {}
        for corner_name, voltage_map in self._voltage_map.items():
            lib_info = next((lib for lib in self._tt_ddrio_libs 
                           if lib['corner_name'] == corner_name), None)
            if not lib_info:
                continue
            
            lib_filename = Path(lib_info['lib_path']).name
            
            for domain_name, actual_voltage in voltage_map.items():
                if domain_name in self._voltage_spec:
                    expected_voltage = self._voltage_spec[domain_name]
                    if abs(actual_voltage - expected_voltage) <= 0.001:
                        # Format: [lib_filename] voltage_map([domain])=[voltage]v - MATCHES voltage.txt
                        item_name = f"{lib_filename} voltage_map({domain_name})={actual_voltage}v - MATCHES voltage.txt"
                        found_items[item_name] = {
                            'name': item_name,
                            'line_number': lib_info.get('line_number', 0),
                            'file_path': lib_info.get('file_path', 'N/A')
                        }
        
        # Find unused waivers
        used_names = set(waived_items.keys())
        unused_waivers = [name for name in waive_dict.keys() if name not in used_names]
        
        # Use template helper - FIXED: Pass dict directly
        return self.build_complete_output(
            found_items=found_items,
            waived_items=waived_items,
            missing_items=unwaived_items,
            waive_dict=waive_dict,
            unused_waivers=unused_waivers,
            found_desc=self.FOUND_DESC_TYPE1_4,
            missing_desc=self.MISSING_DESC_TYPE1_4,
            waived_desc=self.WAIVED_DESC,
            found_reason=self.FOUND_REASON_TYPE1_4,
            missing_reason=self.MISSING_REASON_TYPE1_4,
            waived_base_reason=self.WAIVED_BASE_REASON
        )


# =========================================================================
# Entry Point
# =========================================================================

def main():
    """Main entry point."""
    checker = Check_15_0_0_02()
    checker.init_checker(Path(__file__))
    result = checker.execute_check()
    checker.write_output(result)
    return 0 if result.is_pass else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())