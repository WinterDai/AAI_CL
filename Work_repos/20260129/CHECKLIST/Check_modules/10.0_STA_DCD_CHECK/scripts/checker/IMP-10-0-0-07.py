################################################################################
# Script Name: IMP-10-0-0-07.py
#
# Purpose:
#   Confirm the OCV setting is correct (matches to latest foundry recommendation or addendum).
#   Parse sta_post_syn.log to verify On-Chip Variation (OCV/SOCV) configuration.
#
# Logic:
#   - Extract OCV-related settings from Tempus log
#   - Check: Analysis Mode, spatial derate settings, SOCV RC variation, wire derate, SOCV files
#   - Type 1: Boolean check (all 6 indicators must be found)
#   - Type 2/3: Pattern matching with optional waiver logic
#
# Auto Type Detection:
#   Type 1: requirements.value=N/A, waivers.value=N/A/0 → Boolean check
#   Type 2: requirements.value>0, pattern_items exists, waivers.value=N/A/0 → Value comparison
#   Type 3: requirements.value>0, pattern_items exists, waivers.value>0 → Value with waiver logic
#   Type 4: requirements.value=N/A, waivers.value>0 → Boolean with waiver logic
#
# Author: yyin
# Date: 2025-12-04
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
from output_formatter import DetailItem, Severity, ResultType, create_check_result


class OCVSettingChecker(BaseChecker):
    """
    Unified checker that auto-detects and handles all 4 checker types.
    
    Check Target: Confirm the OCV setting is correct
    
    Type Detection Logic:
    - Type 1: requirements.value=N/A AND waivers.value=N/A/0
    - Type 2: requirements.value>0 AND pattern_items AND waivers.value=N/A/0
    - Type 3: requirements.value>0 AND pattern_items AND waivers.value>0
    - Type 4: requirements.value=N/A AND waivers.value>0
    
    Parsing Logic:
    - Extract 6 OCV indicators from sta_post_syn.log:
      1. Analysis Mode: MMMC OCV (SOCV)
      2. timing_enable_spatial_derate_mode to 1
      3. timing_spatial_derate_distance_mode to chip_size
      4. SOCV RC Variation Factors (table or command)
      5. Wire Derate SOCV Factors
      6. SOCV Files
    """
    
    # OCV indicator keys
    OCV_ANALYSIS_MODE = "Analysis Mode: MMMC OCV"
    OCV_SPATIAL_DERATE_ENABLE = "timing_enable_spatial_derate_mode to 1"
    OCV_SPATIAL_DERATE_DISTANCE = "timing_spatial_derate_distance_mode to chip_size"
    OCV_SOCV_RC_VARIATION = "SOCV RC Variation Factors"
    OCV_WIRE_DERATE = "Wire Derate SOCV Factors"
    OCV_SOCV_FILES = "SOCV Files"
    
    def __init__(self):
        super().__init__(
            check_module="10.0_STA_DCD_CHECK",
            item_id="IMP-10-0-0-07",
            item_desc="Confirm the OCV setting is correct?"
        )
        self._ocv_indicators: Dict[str, Dict[str, Any]] = {}
        self._pattern_items: List[str] = []
        self._log_lines_override: Optional[List[str]] = None

    # =========================================================================
    # Helper Methods (Formatting & Mapping)
    # =========================================================================

    def _map_pattern_to_indicator(self, pattern: str) -> Optional[str]:
        """Map a pattern string to one of the OCV indicator names."""
        pattern_lower = pattern.lower()
        mapping = [
            (self.OCV_ANALYSIS_MODE, ["analysis mode", "mmmc ocv", "socv"]),
            (self.OCV_SPATIAL_DERATE_ENABLE, ["spatial_derate_mode", "enable_spatial"]),
            (self.OCV_SPATIAL_DERATE_DISTANCE, ["spatial_derate_distance", "chip_size"]),
            (self.OCV_SOCV_RC_VARIATION, ["socv rc variation", "set_socv_rc_variation_factor", "rc variation factors"]),
            (self.OCV_WIRE_DERATE, ["wire derate", "socv factors"]),
            (self.OCV_SOCV_FILES, ["socv files", "ocv files"])
        ]

        for indicator_name, tokens in mapping:
            if any(token in pattern_lower for token in tokens):
                return indicator_name
        return None

    def _find_pattern_for_indicator(self, indicator_name: str) -> Optional[str]:
        """Return the first pattern string corresponding to the given indicator."""
        for pattern in self._pattern_items:
            if self._map_pattern_to_indicator(pattern) == indicator_name:
                return pattern
        return None

    def _get_indicator_label(self, indicator_name: Optional[str]) -> str:
        """Return a concise label for the indicator used in log output."""
        if indicator_name == self.OCV_ANALYSIS_MODE:
            return "Analysis Mode: MMMC OCV"
        if indicator_name == self.OCV_SPATIAL_DERATE_ENABLE:
            return "timing_enable_spatial_derate_mode"
        if indicator_name == self.OCV_SPATIAL_DERATE_DISTANCE:
            return "timing_spatial_derate_distance_mode"
        if indicator_name == self.OCV_SOCV_RC_VARIATION:
            return "SOCV RC Variation"
        if indicator_name == self.OCV_WIRE_DERATE:
            return "Wire derate"
        if indicator_name == self.OCV_SOCV_FILES:
            return "SOCV files"
        return indicator_name or "Unknown pattern"

    def _format_indicator_success_line(self, indicator_name: str) -> str:
        """Format the success line for a given indicator using parsed data."""
        data = self._ocv_indicators.get(indicator_name, {})

        if indicator_name == self.OCV_ANALYSIS_MODE:
            return "Analysis Mode: MMMC OCV (SOCV)"
        
        if indicator_name == self.OCV_SPATIAL_DERATE_ENABLE:
            return "timing_enable_spatial_derate_mode: 1"
        
        if indicator_name == self.OCV_SPATIAL_DERATE_DISTANCE:
            mode = data.get('mode', 'chip_size')
            return f"timing_spatial_derate_distance_mode: {mode}"
        
        if indicator_name == self.OCV_SOCV_RC_VARIATION:
            early = data.get('early', 'N/A')
            late = data.get('late', 'N/A')
            source = data.get('source', 'unknown')
            if source == 'table':
                return f"SOCV RC Variation: Early {early}, Late {late}"
            else:
                return f"SOCV RC Variation: {early} (command only)"
        
        if indicator_name == self.OCV_WIRE_DERATE:
            enabled = data.get('enabled', False)
            if enabled:
                return "Wire derate: SOCV factors enabled"
            return "Wire derate: No SOCV factors"
        
        if indicator_name == self.OCV_SOCV_FILES:
            file_count = data.get('file_count', 0)
            is_spatial = data.get('is_spatial_ocv', False)
            if is_spatial:
                return f"SOCV files: Spatial-OCV ({file_count} files)"
            return f"SOCV files: Standard SOCV ({file_count} files)"
        
        return indicator_name
    
    # =========================================================================
    # Input File Parsing
    # =========================================================================
    
    def _parse_sta_log(self) -> Dict[str, Dict[str, Any]]:
        """
        Parse sta_post_syn.log to extract OCV settings.
        
        Searches for 6 key OCV indicators:
        1. Analysis Mode: MMMC OCV (SOCV)
        2. timing_enable_spatial_derate_mode to 1
        3. timing_spatial_derate_distance_mode to chip_size
        4. SOCV RC Variation Factors (table preferred, else command)
        5. Wire Derate SOCV Factors
        6. SOCV Files
        
        Returns:
            Dict mapping indicator name to {found, line_number, file_path, value, ...}
        """
        if not self.item_data or 'input_files' not in self.item_data:
            raise ConfigurationError("No input_files specified in configuration")
        
        # Validate input files using BaseChecker method
        valid_files, missing_files = self.validate_input_files()
        
        # Raise ConfigurationError if files are missing
        if missing_files:
            missing_list = '\n'.join(f"  - {f}" for f in missing_files)
            raise ConfigurationError(
                f"Input file(s) not found:\n{missing_list}"
            )
        
        # Initialize indicators
        indicators = {
            self.OCV_ANALYSIS_MODE: {'found': False, 'line_number': 0, 'file_path': '', 'value': ''},
            self.OCV_SPATIAL_DERATE_ENABLE: {'found': False, 'line_number': 0, 'file_path': '', 'value': ''},
            self.OCV_SPATIAL_DERATE_DISTANCE: {'found': False, 'line_number': 0, 'file_path': '', 'value': '', 'mode': ''},
            self.OCV_SOCV_RC_VARIATION: {'found': False, 'line_number': 0, 'file_path': '', 'value': '', 'early': '', 'late': '', 'source': ''},
            self.OCV_WIRE_DERATE: {'found': False, 'line_number': 0, 'file_path': '', 'value': '', 'enabled': False},
            self.OCV_SOCV_FILES: {'found': False, 'line_number': 0, 'file_path': '', 'value': '', 'file_count': 0, 'is_spatial_ocv': False, 'files': []}
        }
        
        # Parsing state flags
        in_socv_table = False
        in_wire_table = False
        in_ocv_files_table = False
        in_socv_files_list = False
        wire_table_line_count = 0
        ocv_table_line_count = 0
        
        for file_path in valid_files:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            for line_num, line in enumerate(lines, 1):
                # 1. Analysis Mode: MMMC OCV
                if 'Analysis Mode:' in line and 'MMMC OCV' in line:
                    indicators[self.OCV_ANALYSIS_MODE] = {
                        'found': True,
                        'line_number': line_num,
                        'file_path': str(file_path),
                        'value': line.strip()
                    }
                
                # 2. timing_enable_spatial_derate_mode
                if 'timing_enable_spatial_derate_mode' in line and 'to' in line:
                    indicators[self.OCV_SPATIAL_DERATE_ENABLE] = {
                        'found': True,
                        'line_number': line_num,
                        'file_path': str(file_path),
                        'value': line.strip()
                    }
                
                # 3. timing_spatial_derate_distance_mode
                if 'timing_spatial_derate_distance_mode' in line and 'to' in line:
                    # Extract the mode value (e.g., chip_size)
                    match = re.search(r'to\s+(\w+)', line)
                    mode = match.group(1) if match else 'unknown'
                    indicators[self.OCV_SPATIAL_DERATE_DISTANCE] = {
                        'found': True,
                        'line_number': line_num,
                        'file_path': str(file_path),
                        'value': line.strip(),
                        'mode': mode
                    }
                
                # 4. SOCV RC Variation Factors - Table (priority)
                if 'SOCV RC Variation Factors' in line:
                    in_socv_table = True
                    if not indicators[self.OCV_SOCV_RC_VARIATION]['found']:
                        indicators[self.OCV_SOCV_RC_VARIATION]['line_number'] = line_num
                        indicators[self.OCV_SOCV_RC_VARIATION]['file_path'] = str(file_path)
                    continue
                
                if in_socv_table:
                    # Parse table data row (skip separators and headers)
                    if '|' in line and 'Analysis View' not in line and '---' not in line and '+' not in line:
                        parts = [p.strip() for p in line.split('|')]
                        # Expected format: | view_name | early_value | late_value |
                        if len(parts) >= 4 and parts[1] and parts[2] and parts[3]:
                            try:
                                early_val = parts[2]
                                late_val = parts[3]
                                indicators[self.OCV_SOCV_RC_VARIATION] = {
                                    'found': True,
                                    'line_number': indicators[self.OCV_SOCV_RC_VARIATION].get('line_number', line_num),
                                    'file_path': str(file_path),
                                    'value': f"Early {early_val}, Late {late_val}",
                                    'early': early_val,
                                    'late': late_val,
                                    'source': 'table'
                                }
                                in_socv_table = False  # Found data, stop parsing table
                            except:
                                pass
                    elif line.strip() == '' or '###' in line:
                        in_socv_table = False
                
                # 4. SOCV RC Variation - Command (fallback if no table found)
                if not indicators[self.OCV_SOCV_RC_VARIATION]['found'] and 'set_socv_rc_variation_factor' in line:
                    # Extract factor value
                    match = re.search(r'set_socv_rc_variation_factor\s+([\d.]+)', line)
                    if match:
                        factor = match.group(1)
                        indicators[self.OCV_SOCV_RC_VARIATION] = {
                            'found': True,
                            'line_number': line_num,
                            'file_path': str(file_path),
                            'value': factor,
                            'early': factor,
                            'late': factor,
                            'source': 'command'
                        }
                
                # 5. Wire Derate SOCV Factors
                if '### WIRE DERATE ###' in line:
                    in_wire_table = True
                    wire_table_line_count = 0
                    if not indicators[self.OCV_WIRE_DERATE]['found']:
                        indicators[self.OCV_WIRE_DERATE]['line_number'] = line_num
                        indicators[self.OCV_WIRE_DERATE]['file_path'] = str(file_path)
                    continue
                
                if in_wire_table:
                    wire_table_line_count += 1
                    # Look for X in SOCV Factors column (typically in 4th or 5th line of table)
                    if 'X' in line and wire_table_line_count > 2:
                        # Check if X is in the SOCV Factors column
                        if '|' in line:
                            parts = [p.strip() for p in line.split('|')]
                            # Format: | User Derate | SOCV Factors |
                            if len(parts) >= 3 and 'X' in parts[2]:
                                indicators[self.OCV_WIRE_DERATE] = {
                                    'found': True,
                                    'line_number': indicators[self.OCV_WIRE_DERATE].get('line_number', line_num),
                                    'file_path': str(file_path),
                                    'value': 'SOCV factors enabled',
                                    'enabled': True
                                }
                                in_wire_table = False
                    elif line.strip() == '' or '###' in line:
                        # End of table without finding X
                        if not indicators[self.OCV_WIRE_DERATE]['found']:
                            indicators[self.OCV_WIRE_DERATE] = {
                                'found': True,
                                'line_number': indicators[self.OCV_WIRE_DERATE].get('line_number', line_num),
                                'file_path': str(file_path),
                                'value': 'No SOCV factors',
                                'enabled': False
                            }
                        in_wire_table = False
                
                # 6. SOCV Files
                if '### OCV FILES ###' in line:
                    in_ocv_files_table = True
                    ocv_table_line_count = 0
                    if not indicators[self.OCV_SOCV_FILES]['found']:
                        indicators[self.OCV_SOCV_FILES]['line_number'] = line_num
                        indicators[self.OCV_SOCV_FILES]['file_path'] = str(file_path)
                    continue
                
                if in_ocv_files_table:
                    ocv_table_line_count += 1
                    # Check for Spatial-OCV marker
                    if 'Spatial-OCV' in line and 'X' in line:
                        if '|' in line:
                            parts = [p.strip() for p in line.split('|')]
                            # Format: | AOCV | Spatial-OCV |
                            if len(parts) >= 3 and 'X' in parts[2]:
                                indicators[self.OCV_SOCV_FILES]['is_spatial_ocv'] = True
                    
                    if 'SOCV Files:' in line:
                        in_ocv_files_table = False
                        in_socv_files_list = True
                        continue
                
                # Count SOCV files - look for .socv file entries
                if in_socv_files_list:
                    # Check if line contains .socv file path
                    if '.socv' in line:
                        file_entry = line.strip()
                        # Remove leading dash if present
                        if file_entry.startswith('-'):
                            file_entry = file_entry[1:].strip()
                        if file_entry:
                            indicators[self.OCV_SOCV_FILES]['files'].append(file_entry)
                    elif line.strip() == '' or (line.strip() and not line.strip().startswith('-') and '.socv' not in line):
                        # End of file list - finalize the indicator
                        if indicators[self.OCV_SOCV_FILES]['files']:
                            file_count = len(indicators[self.OCV_SOCV_FILES]['files'])
                            is_spatial = indicators[self.OCV_SOCV_FILES].get('is_spatial_ocv', False)
                            indicators[self.OCV_SOCV_FILES] = {
                                'found': True,
                                'line_number': indicators[self.OCV_SOCV_FILES].get('line_number', line_num),
                                'file_path': str(file_path),
                                'value': f"{'Spatial-OCV' if is_spatial else 'Standard SOCV'} ({file_count} files)",
                                'file_count': file_count,
                                'is_spatial_ocv': is_spatial,
                                'files': indicators[self.OCV_SOCV_FILES]['files']
                            }
                        in_socv_files_list = False
            
            # Handle case where SOCV files list extends to end of file
            if in_socv_files_list and indicators[self.OCV_SOCV_FILES]['files']:
                file_count = len(indicators[self.OCV_SOCV_FILES]['files'])
                is_spatial = indicators[self.OCV_SOCV_FILES].get('is_spatial_ocv', False)
                indicators[self.OCV_SOCV_FILES] = {
                    'found': True,
                    'line_number': indicators[self.OCV_SOCV_FILES].get('line_number', 0),
                    'file_path': str(file_path),
                    'value': f"{'Spatial-OCV' if is_spatial else 'Standard SOCV'} ({file_count} files)",
                    'file_count': file_count,
                    'is_spatial_ocv': is_spatial,
                    'files': indicators[self.OCV_SOCV_FILES]['files']
                }
        
        return indicators
    
    def _check_pattern_in_log(self, pattern: str) -> Dict[str, Any]:
        """
        Check if a specific pattern exists in log files (case-insensitive partial match for Type 2/3).
        
        For Type 2 checks, simply search for the pattern string (case-insensitive).
        Also handles common variations like "to" vs "=" in patterns.
        Special handling for semantic patterns like "SOCV Files Used".
        
        Args:
            pattern: Pattern string to search for
        
        Returns:
            Dict with {found, line_number, file_path, value}
        """
        if not self.item_data or 'input_files' not in self.item_data:
            return {'found': False, 'line_number': 0, 'file_path': '', 'value': ''}
        
        valid_files, _ = self.validate_input_files()
        
        # Special handling for "SOCV Files Used" - check if SOCV files are actually listed
        if 'socv files used' in pattern.lower():
            return self._check_socv_files_used(valid_files)
        
        # Normalize pattern for flexible matching
        pattern_lower = pattern.lower()
        # Create alternative patterns for common variations
        pattern_variations = [pattern_lower]
        if ' = ' in pattern_lower:
            pattern_variations.append(pattern_lower.replace(' = ', ' to '))
        if ' to ' in pattern_lower:
            pattern_variations.append(pattern_lower.replace(' to ', ' = '))
        
        for file_path in valid_files:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            for line_num, line in enumerate(lines, 1):
                line_lower = line.lower()
                # Check if any pattern variation matches
                for pattern_var in pattern_variations:
                    if pattern_var in line_lower:
                        return {
                            'found': True,
                            'line_number': line_num,
                            'file_path': str(file_path),
                            'value': line.strip()
                        }
        
        return {'found': False, 'line_number': 0, 'file_path': '', 'value': ''}
    
    def _check_socv_files_used(self, valid_files: List[Path]) -> Dict[str, Any]:
        """
        Check if SOCV files are actually used (listed in the log).
        
        Returns:
            Dict with {found, line_number, file_path, value}
        """
        for file_path in valid_files:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            in_socv_files_section = False
            socv_files_line_num = 0
            socv_file_count = 0
            
            for line_num, line in enumerate(lines, 1):
                # Look for "SOCV Files:" header
                if 'socv files:' in line.lower():
                    in_socv_files_section = True
                    socv_files_line_num = line_num
                    continue
                
                # Count .socv files
                if in_socv_files_section:
                    if '.socv' in line.lower():
                        socv_file_count += 1
                    elif line.strip() == '' or (line.strip() and not line.strip().startswith('-') and '.socv' not in line.lower()):
                        # End of SOCV files section
                        break
            
            # If we found SOCV files, return success
            if socv_file_count > 0:
                return {
                    'found': True,
                    'line_number': socv_files_line_num,
                    'file_path': str(file_path),
                    'value': f'SOCV Files Used ({socv_file_count} files)'
                }
        
        return {'found': False, 'line_number': 0, 'file_path': '', 'value': ''}
    
    # =========================================================================
    # Main Execution
    # =========================================================================
    
    def execute_check(self) -> CheckResult:
        """
        Execute check with automatic type detection and handling.
        
        Returns:
            CheckResult
        """
        if self.root is None:
            raise RuntimeError("Checker not initialized. Call init_checker() first.")
        
        # Get pattern items
        requirements = self.get_requirements()
        self._pattern_items = requirements.get('pattern_items', []) if requirements else []
        
        # Detect checker type (use BaseChecker method)
        checker_type = self.detect_checker_type()
        
        # Parse OCV settings
        self._ocv_indicators = self._parse_sta_log()
        
        # Execute based on type
        if checker_type == 1:
            return self._execute_type1()
        elif checker_type == 2:
            return self._execute_type2()
        elif checker_type == 3:
            return self._execute_type3()
        else:  # checker_type == 4
            return self._execute_type4()
    
    # =========================================================================
    # Type 1: Boolean Check (No Waiver Logic)
    # =========================================================================
    
    def _execute_type1(self) -> CheckResult:
        """
        Type 1: requirements.value=N/A, waivers.value=N/A/0
        
        Logic: 
        - Check all 6 OCV indicators
        - PASS: All indicators found
        - FAIL: Any indicator missing
        """
        waivers = self.get_waivers()
        waiver_value = waivers.get('value', 'N/A') if waivers else 'N/A'
        waive_items = waivers.get('waive_items', []) if waivers else []
        is_waiver_zero = (waiver_value == 0)
        
        details = []
        self._log_lines_override = None
        
        # Check all 6 indicators
        found_indicators = []
        missing_indicators = []
        
        for indicator_name, indicator_data in self._ocv_indicators.items():
            if indicator_data['found']:
                found_indicators.append(indicator_name)
                details.append(DetailItem(
                    severity=Severity.INFO,
                    name=indicator_name,
                    line_number=indicator_data['line_number'],
                    file_path=indicator_data['file_path'],
                    reason="OCV setting found"
                ))
            else:
                missing_indicators.append(indicator_name)
                severity = Severity.INFO if is_waiver_zero else Severity.FAIL
                reason_suffix = "[WAIVED_AS_INFO]" if is_waiver_zero else ""
                details.append(DetailItem(
                    severity=severity,
                    name=indicator_name,
                    line_number=0,
                    file_path="N/A",
                    reason=f"OCV setting not found{reason_suffix}"
                ))
        
        # Add waive_items
        if is_waiver_zero and waive_items:
            for item in waive_items:
                details.append(DetailItem(
                    severity=Severity.INFO,
                    name=item,
                    line_number=0,
                    file_path="N/A",
                    reason="Waiver item[WAIVED_INFO]"
                ))
        
        # Determine PASS/FAIL
        if is_waiver_zero:
            is_pass = True
        else:
            is_pass = (len(missing_indicators) == 0)
        
        # Create groups for report generation
        error_groups = {}
        if missing_indicators and not is_waiver_zero:
            error_groups['ERROR01'] = {
                'description': 'OCV setting not found',
                'items': missing_indicators
            }

        # Prepare custom log lines for log output
        total_indicators = len(self._ocv_indicators)
        log_lines: List[str] = []

        if missing_indicators:
            # Determine severity/label depending on waiver mode
            miss_severity_label = "Info" if is_waiver_zero else "Fail"
            miss_tag = "INFO01" if is_waiver_zero else "ERROR01"
            miss_desc = "OCV settings (forced PASS mode)" if is_waiver_zero else "OCV setting not found"

            log_lines.append(f"IMP-10-0-0-07-{miss_tag}: {miss_desc}:")
            log_lines.append(f"  Severity: {miss_severity_label} Occurrence: {len(missing_indicators)}")
            for indicator_name in missing_indicators:
                log_lines.append(f"  - {self._get_indicator_label(indicator_name)}")

        if found_indicators:
            found_desc = (
                f"OCV setting verified ({len(found_indicators)}/{total_indicators} indicators found)"
                if total_indicators else "OCV settings detected"
            )
            log_lines.append(f"IMP-10-0-0-07-INFO01: {found_desc}:")
            log_lines.append(f"  Severity: Info Occurrence: {len(found_indicators)}")

            indicator_order = [
                self.OCV_ANALYSIS_MODE,
                self.OCV_SPATIAL_DERATE_ENABLE,
                self.OCV_SPATIAL_DERATE_DISTANCE,
                self.OCV_SOCV_RC_VARIATION,
                self.OCV_WIRE_DERATE,
                self.OCV_SOCV_FILES
            ]

            for indicator_name in indicator_order:
                if indicator_name not in found_indicators:
                    continue
                log_lines.append(f"  - {self._format_indicator_success_line(indicator_name)}")

        if log_lines:
            self._log_lines_override = log_lines

        result = create_check_result(
            value=len(found_indicators),
            is_pass=is_pass,
            has_pattern_items=False,
            has_waiver_value=bool(waive_items),
            details=details,
            error_groups=error_groups if error_groups else None,
            info_groups=None,
            info_message=None,
            item_desc=self.item_desc
        )

        return result
    
    def write_output(self, result: CheckResult):
        """Customize log formatting while keeping standard report output."""
        if self.formatter is None or self.log_path is None or self.rpt_path is None:
            raise RuntimeError("Checker not initialized. Call init_checker() first.")

        # Always write the report using the standard formatter
        self.formatter.write_report(result, self.rpt_path, mode='w')

        # Custom log formatting when override lines are available
        if self._log_lines_override:
            self.log_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Check if this is a waived pass
            is_waived_pass = hasattr(result, '_is_waived_pass') and result._is_waived_pass
            
            if result.is_pass and is_waived_pass:
                status = "PASS(Waive)"
            else:
                status = "PASS" if result.is_pass else "FAIL"
            
            with self.log_path.open('w', encoding='utf-8') as log_file:
                log_file.write(f'{status}:{self.item_id}:{self.item_desc}\n')
                log_output = '\n'.join(str(line) for line in self._log_lines_override)
                log_file.write(log_output + '\n')
        else:
            self.formatter.write_log(result, self.log_path, mode='w')

        # Cache result using the shared cache manager (mirrors BaseChecker.write_output)
        from result_cache_manager import configure_global_cache

        cache = configure_global_cache(
            cache_dir=self.cache_dir,
            max_memory_size=200,
            enable_file_cache=True
        )
        cache.set(self.item_id, result)

        BaseChecker._result_cache[self.item_id] = result

        # Reset summary to avoid leaking into subsequent runs
        self._log_lines_override = None
    
    # =========================================================================
    # Type 2: Value Comparison (No Waiver Logic)
    # =========================================================================

    def _execute_type2(self) -> CheckResult:
        """
        Type 2: requirements.value>0, pattern_items exists, waivers.value=N/A/0
        
        Logic: 
        - Check each pattern_items in log
        - PASS: All pattern_items found
        - FAIL: Any pattern_items not found (distinguish Missing vs Mismatch)
        """
        requirements = self.get_requirements()
        expected_value = requirements.get('value', 0) if requirements else 0
        try:
            expected_value = int(expected_value)
        except:
            expected_value = 0
        
        waivers = self.get_waivers()
        waiver_value = waivers.get('value', 'N/A') if waivers else 'N/A'
        waive_items = waivers.get('waive_items', []) if waivers else []
        is_waiver_zero = (waiver_value == 0)
        
        details = []
        found_patterns = []
        missing_patterns = []
        self._log_lines_override = None
        
        # Check each pattern_items - simple substring search
        for pattern in self._pattern_items:
            result = self._check_pattern_in_log(pattern)
            
            if result['found']:
                found_patterns.append(pattern)
                details.append(DetailItem(
                    severity=Severity.INFO,
                    name=pattern,
                    line_number=result['line_number'],
                    file_path=result['file_path'],
                    reason="OCV setting is correct"
                ))
            else:
                # Pattern not found
                missing_patterns.append(pattern)
                severity = Severity.INFO if is_waiver_zero else Severity.FAIL
                reason_suffix = "[WAIVED_AS_INFO]" if is_waiver_zero else ""
                details.append(DetailItem(
                    severity=severity,
                    name=pattern,
                    line_number=0,
                    file_path="N/A",
                    reason=f"OCV setting isn't correct: pattern '{pattern}' not found{reason_suffix}"
                ))
        
        # Add waive_items
        if is_waiver_zero and waive_items:
            for item in waive_items:
                details.append(DetailItem(
                    severity=Severity.INFO,
                    name=item,
                    line_number=0,
                    file_path="N/A",
                    reason="Waiver item[WAIVED_INFO]"
                ))
        
        # Determine PASS/FAIL
        if is_waiver_zero:
            is_pass = True
        else:
            is_pass = (len(found_patterns) == expected_value)
        
        # Prepare custom log lines
        total_patterns = len(self._pattern_items)
        error_groups = {}
        info_groups = {}
        log_lines: List[str] = []

        # Handle missing patterns (not waived)
        if missing_patterns and not is_waiver_zero:
            error_groups['ERROR01'] = {
                "description": "OCV setting isn't correct (pattern not found)",
                "items": missing_patterns
            }
            log_lines.append("IMP-10-0-0-07-ERROR01: OCV setting isn't correct (pattern not found):")
            log_lines.append(f"  Severity: Fail Occurrence: {len(missing_patterns)}")
            for pattern in missing_patterns:
                log_lines.append(f"  - {pattern}")
        
        # Handle missing patterns (waived as INFO)
        if missing_patterns and is_waiver_zero:
            log_lines.append("IMP-10-0-0-07-INFO02: OCV settings treated as correct via waiver:")
            log_lines.append(f"  Severity: Info Occurrence: {len(missing_patterns)}")
            for pattern in missing_patterns:
                log_lines.append(f"  - {pattern} (missing but waived)")

        if found_patterns:
            if total_patterns and len(found_patterns) == total_patterns:
                found_desc = f"OCV setting is correct ({len(found_patterns)}/{total_patterns} patterns found)"
            elif total_patterns:
                found_desc = f"OCV setting partially correct ({len(found_patterns)}/{total_patterns} patterns found)"
            else:
                found_desc = "OCV settings detected"
            log_lines.append(f"IMP-10-0-0-07-INFO01: {found_desc}:")
            log_lines.append(f"  Severity: Info Occurrence: {len(found_patterns)}")

            # For Type 2, simply list the patterns that were found
            for pattern in found_patterns:
                log_lines.append(f"  - {pattern}")

            info_groups['INFO01'] = {
                'description': found_desc,
                'items': found_patterns
            }

        if log_lines:
            self._log_lines_override = log_lines

        return create_check_result(
            value=len(found_patterns),
            is_pass=is_pass,
            has_pattern_items=True,
            has_waiver_value=bool(waive_items),
            details=details,
            error_groups=error_groups if error_groups else None,
            info_groups=info_groups if info_groups else None,
            item_desc=self.item_desc
        )
    
    # =========================================================================
    # Type 3: Value Comparison WITH Waiver Logic
    # =========================================================================
    
    def _execute_type3(self) -> CheckResult:
        """
        Type 3: requirements.value>0, pattern_items exists, waivers.value>0
        
        Logic: 
        - Check each pattern_items in log
        - Separate into: found, missing+waived, missing+unwaived, unused waivers
        """
        waivers = self.get_waivers()
        waive_items_dict = self._get_waive_items_with_reasons()
        waive_items = list(waive_items_dict.keys())
        waive_set = set(waive_items)
        
        details = []
        found_patterns = []
        missing_unwaived = []
        missing_waived = []
        self._log_lines_override = None
        
        # Check each pattern_items - simple substring search
        for pattern in self._pattern_items:
            result = self._check_pattern_in_log(pattern)
            
            if result['found']:
                found_patterns.append(pattern)
                details.append(DetailItem(
                    severity=Severity.INFO,
                    name=pattern,
                    line_number=result['line_number'],
                    file_path=result['file_path'],
                    reason="OCV setting is correct"
                ))
            else:
                # Pattern not found
                if pattern in waive_set:
                    missing_waived.append(pattern)
                    waiver_reason = waive_items_dict.get(pattern, '')
                    base_reason = f"OCV setting isn't correct: pattern '{pattern}' not found"
                    reason = f"{base_reason} {waiver_reason}[WAIVER]" if waiver_reason else f"{base_reason} [WAIVER]"
                    details.append(DetailItem(
                        severity=Severity.INFO,
                        name=pattern,
                        line_number=0,
                        file_path="N/A",
                        reason=reason
                    ))
                else:
                    missing_unwaived.append(pattern)
                    details.append(DetailItem(
                        severity=Severity.FAIL,
                        name=pattern,
                        line_number=0,
                        file_path="N/A",
                        reason=f"OCV setting isn't correct: pattern '{pattern}' not found"
                    ))
        
        # Find unused waivers
        checked_patterns_set = set(self._pattern_items)
        unused_waivers = [item for item in waive_items if item not in checked_patterns_set]
        
        for item in unused_waivers:
            details.append(DetailItem(
                severity=Severity.WARN,
                name=item,
                line_number=0,
                file_path="N/A",
                reason="Waived item not found in check[WAIVER]"
            ))
        
        is_pass = (len(missing_unwaived) == 0)
        
        # Determine if this is a true PASS or waived PASS
        has_waived_errors = (len(missing_waived) > 0)
        is_waived_pass = is_pass and has_waived_errors
        
        # Create explicit error groups
        total_patterns = len(self._pattern_items)
        error_groups = {}
        warn_groups = {}
        info_groups = {}
        log_lines: List[str] = []
        
        # Handle missing patterns (not waived)
        if missing_unwaived:
            error_groups['ERROR01'] = {
                'description': "OCV setting isn't correct (pattern not found)",
                'items': missing_unwaived
            }
            log_lines.append("IMP-10-0-0-07-ERROR01: OCV setting isn't correct (pattern not found):")
            log_lines.append(f"  Severity: Fail Occurrence: {len(missing_unwaived)}")
            for pattern in missing_unwaived:
                log_lines.append(f"  - {pattern}")
        
        # Handle unused waivers
        if unused_waivers:
            warn_groups['WARN01'] = {
                'description': 'Waiver not used',
                'items': unused_waivers
            }
            log_lines.append("IMP-10-0-0-07-WARN01: Waiver not used:")
            log_lines.append(f"  Severity: Warn Occurrence: {len(unused_waivers)}")
            for item in unused_waivers:
                log_lines.append(f"  - {item}")
        
        # Handle found patterns separately (INFO01)
        if found_patterns:
            if total_patterns and len(found_patterns) == total_patterns:
                found_desc = f"OCV setting is correct ({len(found_patterns)}/{total_patterns} patterns found)"
            elif total_patterns:
                found_desc = f"OCV setting is correct ({len(found_patterns)}/{total_patterns} patterns found)"
            else:
                found_desc = "OCV settings verified"
            
            info_groups['INFO01'] = {
                'description': found_desc,
                'items': found_patterns
            }
            
            log_lines.append(f"IMP-10-0-0-07-INFO01: {found_desc}:")
            log_lines.append(f"  Severity: Info Occurrence: {len(found_patterns)}")
            
            # For Type 3, simply list the patterns that were found
            for pattern in found_patterns:
                log_lines.append(f"  - {pattern}")
        
        # Handle waived patterns separately (INFO02)
        waived_patterns = missing_waived
        if waived_patterns:
            waived_count = len(waived_patterns)
            waived_desc = f"OCV setting verified via waiver ({waived_count} pattern{'s' if waived_count > 1 else ''} waived)"
            
            info_groups['INFO02'] = {
                'description': waived_desc,
                'items': waived_patterns
            }
            
            log_lines.append(f"IMP-10-0-0-07-INFO02: {waived_desc}:")
            log_lines.append(f"  Severity: Info Occurrence: {waived_count}")
            
            # For Type 3, list waived patterns
            for pattern in missing_waived:
                log_lines.append(f"  - {pattern} [WAIVED: missing]")
        
        if log_lines:
            self._log_lines_override = log_lines
        
        # Store waived pass flag for status line customization
        result = create_check_result(
            value=len(found_patterns),
            is_pass=is_pass,
            has_pattern_items=True,
            has_waiver_value=True,
            details=details,
            error_groups=error_groups if error_groups else None,
            warn_groups=warn_groups if warn_groups else None,
            info_groups=info_groups if info_groups else None,
            item_desc=self.item_desc
        )
        
        # Mark if this is a waived pass for custom status line
        if is_waived_pass:
            result._is_waived_pass = True
        
        return result
    
    # =========================================================================
    # Type 4: Boolean WITH Waiver Logic
    # =========================================================================
    
    def _execute_type4(self) -> CheckResult:
        """
        Type 4: requirements.value=N/A, waivers.value>0
        
        Logic: Boolean check + Waiver separation (INFO only)
        """
        waivers = self.get_waivers()
        waive_items_dict = self._get_waive_items_with_reasons()
        waive_items = list(waive_items_dict.keys())
        
        details = []
        self._log_lines_override = None
        
        # Check all 6 indicators
        found_indicators = []
        missing_indicators = []
        
        for indicator_name, indicator_data in self._ocv_indicators.items():
            if indicator_data['found']:
                found_indicators.append(indicator_name)
                details.append(DetailItem(
                    severity=Severity.INFO,
                    name=indicator_name,
                    line_number=indicator_data['line_number'],
                    file_path=indicator_data['file_path'],
                    reason="OCV setting found"
                ))
            else:
                missing_indicators.append(indicator_name)
                details.append(DetailItem(
                    severity=Severity.FAIL,
                    name=indicator_name,
                    line_number=0,
                    file_path="N/A",
                    reason="OCV setting isn't correct: indicator not found"
                ))
        
        # Add waive_items - mark as WARN since they're unused in Type 4
        if waive_items:
            for item in waive_items:
                waiver_reason = waive_items_dict.get(item, '')
                reason = f"{waiver_reason}[WAIVER]" if waiver_reason else "Waiver item (unused)[WAIVER]"
                details.append(DetailItem(
                    severity=Severity.WARN,
                    name=item,
                    line_number=0,
                    file_path="N/A",
                    reason=reason
                ))
        
        is_pass = (len(missing_indicators) == 0)
        
        # Determine if waiver notes exist (even if all passed)
        has_waiver_notes = len(waive_items) > 0
        
        # Create info groups
        total_indicators = len(self._ocv_indicators)
        error_groups = {}
        warn_groups = {}
        info_groups = {}
        log_lines: List[str] = []
        
        if missing_indicators:
            error_groups['ERROR01'] = {
                'description': "OCV setting isn't correct (missing indicators)",
                'items': missing_indicators
            }
            log_lines.append("IMP-10-0-0-07-ERROR01: OCV setting isn't correct (missing indicators):")
            log_lines.append(f"  Severity: Fail Occurrence: {len(missing_indicators)}")
            for indicator_name in missing_indicators:
                log_lines.append(f"  - {self._get_indicator_label(indicator_name)}")
        
        # Handle found indicators (INFO01)
        if found_indicators:
            if total_indicators and len(found_indicators) == total_indicators:
                info_desc = f"OCV setting is correct ({len(found_indicators)}/{total_indicators} indicators found)"
            elif total_indicators:
                info_desc = f"OCV setting is correct ({len(found_indicators)}/{total_indicators} indicators found)"
            else:
                info_desc = "OCV setting verified"
            
            info_groups['INFO01'] = {
                'description': info_desc,
                'items': found_indicators
            }
            
            log_lines.append(f"IMP-10-0-0-07-INFO01: {info_desc}:")
            log_lines.append(f"  Severity: Info Occurrence: {len(found_indicators)}")
            
            indicator_order = [
                self.OCV_ANALYSIS_MODE,
                self.OCV_SPATIAL_DERATE_ENABLE,
                self.OCV_SPATIAL_DERATE_DISTANCE,
                self.OCV_SOCV_RC_VARIATION,
                self.OCV_WIRE_DERATE,
                self.OCV_SOCV_FILES
            ]
            
            for indicator_name in indicator_order:
                if indicator_name not in found_indicators:
                    continue
                log_lines.append(f"  - {self._format_indicator_success_line(indicator_name)}")
        
        # Handle waiver notes separately (WARN01) - unused waivers
        if waive_items:
            waiver_count = len(waive_items)
            waiver_desc = f"Waiver not used ({waiver_count} item{'s' if waiver_count > 1 else ''})"
            
            warn_groups['WARN01'] = {
                'description': waiver_desc,
                'items': waive_items
            }
            
            log_lines.append(f"IMP-10-0-0-07-WARN01: {waiver_desc}:")
            log_lines.append(f"  Severity: Warn Occurrence: {waiver_count}")
            for item in waive_items:
                waiver_reason = waive_items_dict.get(item, '')
                if waiver_reason:
                    log_lines.append(f"  - {item}: {waiver_reason}")
                else:
                    log_lines.append(f"  - {item}")
        
        if log_lines:
            self._log_lines_override = log_lines
        
        result = create_check_result(
            value=len(found_indicators),
            is_pass=is_pass,
            has_pattern_items=False,
            has_waiver_value=True,
            details=details,
            error_groups=error_groups if error_groups else None,
            warn_groups=warn_groups if warn_groups else None,
            info_groups=info_groups if info_groups else None,
            item_desc=self.item_desc
        )
        
        # Mark if this pass includes waiver notes for custom status line
        if is_pass and has_waiver_notes:
            result._is_waived_pass = True
        
        return result
    
    # =========================================================================
    # Helper Methods
    # =========================================================================
    
    def _get_waive_items_with_reasons(self) -> Dict[str, str]:
        """
        Get waive_items with their reasons.
        
        Returns:
            Dict mapping waive_item to reason string
        """
        waivers = self.get_waivers()
        if not waivers:
            return {}
        
        waive_items = waivers.get('waive_items', [])
        
        # If waive_items is a list of dicts with 'name' and 'reason'
        if waive_items and isinstance(waive_items[0], dict):
            return {item['name']: item.get('reason', '') for item in waive_items}
        
        # If waive_items is a simple list
        return {item: '' for item in waive_items}


################################################################################
# Main Entry Point
################################################################################

if __name__ == '__main__':
    checker = OCVSettingChecker()
    checker.run()
