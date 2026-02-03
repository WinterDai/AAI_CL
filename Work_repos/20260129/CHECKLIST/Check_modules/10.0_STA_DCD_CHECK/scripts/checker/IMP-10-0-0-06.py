################################################################################
# Script Name: IMP-10-0-0-06.py
#
# Purpose:
#   Confirm the SI setting is correct.
#   Parse sta_post_syn.log to verify Signal Integrity (SI) configuration.
#
# Logic:
#   - Extract SI-related settings from Tempus log
#   - Check: Signoff Settings, delaycal_enable_si, CCS noise data, glitch analysis, CCS library
#   - Type 1: Boolean check (all 5 indicators must be found)
#   - Type 2/3: Pattern matching with optional waiver logic
#
# Auto Type Detection:
#   Type 1: requirements.value=N/A, waivers.value=N/A/0 → Boolean check
#   Type 2: requirements.value>0, pattern_items exists, waivers.value=N/A/0 → Value comparison
#   Type 3: requirements.value>0, pattern_items exists, waivers.value>0 → Value with waiver logic
#   Type 4: requirements.value=N/A, waivers.value>0 → Boolean with waiver logic
#
# Author: yyin
# Date: 2025-12-03
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


class SISettingChecker(BaseChecker):
    """
    Unified checker that auto-detects and handles all 4 checker types.
    
    Check Target: Confirm the SI setting is correct
    
    Type Detection Logic:
    - Type 1: requirements.value=N/A AND waivers.value=N/A/0
    - Type 2: requirements.value>0 AND pattern_items AND waivers.value=N/A/0
    - Type 3: requirements.value>0 AND pattern_items AND waivers.value>0
    - Type 4: requirements.value=N/A AND waivers.value>0
    
    Parsing Logic:
    - Extract 5 SI indicators from sta_post_syn.log:
      1. Signoff Settings: SI On
      2. delaycal_enable_si to 1
      3. timing_library_read_ccs_noise_data to 1
      4. glitch/report_noise commands
      5. Library Type: CCS libraries
    """
    
    # SI indicator keys
    SI_SIGNOFF_SETTINGS = "Signoff Settings: SI On"
    SI_DELAYCAL_ENABLE = "delaycal_enable_si to 1"
    SI_CCS_NOISE_DATA = "timing_library_read_ccs_noise_data to 1"
    SI_GLITCH_ANALYSIS = "report_noise"
    SI_CCS_LIBRARY = "CCS libraries"
    
    def __init__(self):
        super().__init__(
            check_module="10.0_STA_DCD_CHECK",
            item_id="IMP-10-0-0-06",
            item_desc="Confirm the SI setting is correct?"
        )
        self._si_indicators: Dict[str, Dict[str, Any]] = {}
        self._pattern_items: List[str] = []
        self._log_lines_override: Optional[List[str]] = None

    # =========================================================================
    # Helper Methods (Formatting & Mapping)
    # =========================================================================

    def _map_pattern_to_indicator(self, pattern: str) -> Optional[str]:
        """Map a pattern string to one of the SI indicator names."""
        pattern_lower = pattern.lower()
        mapping = [
            (self.SI_SIGNOFF_SETTINGS, ["signoff settings", "si on"]),
            (self.SI_DELAYCAL_ENABLE, ["delaycal_enable_si"]),
            (self.SI_CCS_NOISE_DATA, ["timing_library_read_ccs_noise_data"]),
            (self.SI_GLITCH_ANALYSIS, ["report_noise", "glitch results", "glitch" ]),
            (self.SI_CCS_LIBRARY, ["ccs libraries", "ccs lib"])
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
        if indicator_name == self.SI_SIGNOFF_SETTINGS:
            return "Signoff Settings: SI On"
        if indicator_name == self.SI_DELAYCAL_ENABLE:
            return "delaycal_enable_si"
        if indicator_name == self.SI_CCS_NOISE_DATA:
            return "timing_library_read_ccs_noise_data"
        if indicator_name == self.SI_GLITCH_ANALYSIS:
            return "report_noise"
        if indicator_name == self.SI_CCS_LIBRARY:
            return "CCS libraries"
        return indicator_name or "Unknown pattern"

    def _format_indicator_success_line(self, indicator_name: str) -> str:
        """Format the success line for a given indicator using parsed data."""
        data = self._si_indicators.get(indicator_name, {})

        if indicator_name == self.SI_SIGNOFF_SETTINGS:
            return "Signoff Settings: SI On"
        if indicator_name == self.SI_DELAYCAL_ENABLE:
            return "delaycal_enable_si: 1"
        if indicator_name == self.SI_CCS_NOISE_DATA:
            return "timing_library_read_ccs_noise_data: 1"
        if indicator_name == self.SI_GLITCH_ANALYSIS:
            value = str(data.get('value', '') or '')
            if 'not available' in value.lower():
                return "report_noise: Not available (parasitics issue)"
            match = re.search(r'out_file\s+(\S+\.rpt)', value)
            if match:
                return f"report_noise: Report generated ({match.group(1)})"
            if value:
                return f"report_noise: {value}"
            return "report_noise: Report generated"
        if indicator_name == self.SI_CCS_LIBRARY:
            libraries = data.get('libraries', []) or []
            lib_count = len(libraries)
            if lib_count:
                return f"CCS libraries: {lib_count} libraries found"
            return "CCS libraries: Not found"
        return indicator_name
    
    # =========================================================================
    # Input File Parsing
    # =========================================================================
    
    def _parse_sta_log(self) -> Dict[str, Dict[str, Any]]:
        """
        Parse sta_post_syn.log to extract SI settings.
        
        Searches for 5 key SI indicators:
        1. Signoff Settings: SI On (EWM-WFP)
        2. setting delaycal_enable_si to 1
        3. setting timing_library_read_ccs_noise_data to 1
        4. report_noise command execution
        5. CCS libraries mention
        
        Returns:
            Dict mapping indicator name to {found, line_number, file_path, value}
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
            self.SI_SIGNOFF_SETTINGS: {'found': False, 'line_number': 0, 'file_path': '', 'value': ''},
            self.SI_DELAYCAL_ENABLE: {'found': False, 'line_number': 0, 'file_path': '', 'value': ''},
            self.SI_CCS_NOISE_DATA: {'found': False, 'line_number': 0, 'file_path': '', 'value': ''},
            self.SI_GLITCH_ANALYSIS: {'found': False, 'line_number': 0, 'file_path': '', 'value': ''},
            self.SI_CCS_LIBRARY: {'found': False, 'line_number': 0, 'file_path': '', 'value': '', 'libraries': []}
        }
        
        # Track if we're in the libraries section
        in_libraries_section = False
        libraries_line_start = 0
        
        for file_path in valid_files:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            for line_num, line in enumerate(lines, 1):
                # 1. Signoff Settings: SI On
                if 'Signoff Settings:' in line and 'SI On' in line:
                    indicators[self.SI_SIGNOFF_SETTINGS] = {
                        'found': True,
                        'line_number': line_num,
                        'file_path': str(file_path),
                        'value': line.strip()
                    }
                
                # 2. delaycal_enable_si to 1
                if 'delaycal_enable_si' in line and 'to 1' in line:
                    indicators[self.SI_DELAYCAL_ENABLE] = {
                        'found': True,
                        'line_number': line_num,
                        'file_path': str(file_path),
                        'value': line.strip()
                    }
                
                # 3. timing_library_read_ccs_noise_data to 1
                if 'timing_library_read_ccs_noise_data' in line and 'to 1' in line:
                    indicators[self.SI_CCS_NOISE_DATA] = {
                        'found': True,
                        'line_number': line_num,
                        'file_path': str(file_path),
                        'value': line.strip()
                    }
                
                # 4. report_noise - capture glitch analysis status
                # Look for either success message (report file path) or failure message
                if 'Glitch results are not available' in line:
                    # Failure case: glitch analysis not available
                    indicators[self.SI_GLITCH_ANALYSIS] = {
                        'found': True,
                        'line_number': line_num,
                        'file_path': str(file_path),
                        'value': f"Report noise and glitch results are not available for reporting. {line.split('Glitch results are not available')[1].strip()}"
                    }
                elif 'report_noise' in line and 'out_file' in line and '.rpt' in line:
                    # Extract the report file path
                    import re
                    match = re.search(r'out_file\s+(\S+\.rpt)', line)
                    if match:
                        report_path = match.group(1)
                        indicators[self.SI_GLITCH_ANALYSIS] = {
                            'found': True,
                            'line_number': line_num,
                            'file_path': str(file_path),
                            'value': f"Report noise and report is {report_path}"
                        }
                
                # 5. CCS libraries - track section and collect library names
                if 'Found' in line and 'active setup/hold libraries:' in line:
                    in_libraries_section = True
                    libraries_line_start = line_num
                    continue
                
                if in_libraries_section:
                    # Check if we're still in the libraries section
                    stripped = line.strip()
                    if stripped and not stripped.startswith('Found') and not stripped.startswith('tcbn'):
                        # End of libraries section
                        in_libraries_section = False
                    elif stripped.endswith('_ccs'):
                        # This is a CCS library
                        indicators[self.SI_CCS_LIBRARY]['libraries'].append(stripped)
                        if not indicators[self.SI_CCS_LIBRARY]['found']:
                            indicators[self.SI_CCS_LIBRARY] = {
                                'found': True,
                                'line_number': libraries_line_start,
                                'file_path': str(file_path),
                                'value': f"Found {len(indicators[self.SI_CCS_LIBRARY]['libraries'])} CCS libraries",
                                'libraries': indicators[self.SI_CCS_LIBRARY]['libraries']
                            }
        
        return indicators
    
    def _check_pattern_in_log(self, pattern: str) -> Dict[str, Any]:
        """
        Check if a specific pattern exists in log files.
        
        For Type 2 checks, we need to distinguish between:
        1. Pattern found and matches exactly (found=True, mismatch=False)
        2. Related content found but value mismatches (found=False, mismatch=True)
        3. Nothing related found at all (found=False, mismatch=False)
        
        Args:
            pattern: Pattern string to search for
        
        Returns:
            Dict with {found, mismatch, line_number, file_path, value, actual_value}
        """
        if not self.item_data or 'input_files' not in self.item_data:
            return {'found': False, 'mismatch': False, 'line_number': 0, 'file_path': '', 'value': '', 'actual_value': ''}
        
        valid_files, _ = self.validate_input_files()
        indicator_name = self._map_pattern_to_indicator(pattern)
        
        for file_path in valid_files:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            for line_num, line in enumerate(lines, 1):
                # Exact substring match
                if pattern in line:
                    return {
                        'found': True,
                        'mismatch': False,
                        'line_number': line_num,
                        'file_path': str(file_path),
                        'value': line.strip(),
                        'actual_value': line.strip()
                    }
                
                # Check for mismatch cases based on indicator type
                if indicator_name == self.SI_SIGNOFF_SETTINGS:
                    # Look for "Signoff Settings:" with different SI state
                    if 'Signoff Settings:' in line and 'SI' in line and pattern not in line:
                        return {
                            'found': False,
                            'mismatch': True,
                            'line_number': line_num,
                            'file_path': str(file_path),
                            'value': '',
                            'actual_value': line.strip()
                        }
                elif indicator_name == self.SI_DELAYCAL_ENABLE:
                    # Look for delaycal_enable_si with different value
                    if 'delaycal_enable_si' in line and 'to' in line and pattern not in line:
                        return {
                            'found': False,
                            'mismatch': True,
                            'line_number': line_num,
                            'file_path': str(file_path),
                            'value': '',
                            'actual_value': line.strip()
                        }
                elif indicator_name == self.SI_CCS_NOISE_DATA:
                    # Look for timing_library_read_ccs_noise_data with different value
                    if 'timing_library_read_ccs_noise_data' in line and 'to' in line and pattern not in line:
                        return {
                            'found': False,
                            'mismatch': True,
                            'line_number': line_num,
                            'file_path': str(file_path),
                            'value': '',
                            'actual_value': line.strip()
                        }
        
        return {'found': False, 'mismatch': False, 'line_number': 0, 'file_path': '', 'value': '', 'actual_value': ''}
    
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
        
        # Parse SI settings
        self._si_indicators = self._parse_sta_log()
        
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
        - Check all 5 SI indicators
        - PASS: All indicators found
        - FAIL: Any indicator missing
        """
        waivers = self.get_waivers()
        waiver_value = waivers.get('value', 'N/A') if waivers else 'N/A'
        waive_items = waivers.get('waive_items', []) if waivers else []
        is_waiver_zero = (waiver_value == 0)
        
        details = []
        self._log_lines_override = None
        
        # Check all 5 indicators
        found_indicators = []
        missing_indicators = []
        
        for indicator_name, indicator_data in self._si_indicators.items():
            if indicator_data['found']:
                found_indicators.append(indicator_name)
                
                # Special handling for CCS libraries - show all libraries
                if indicator_name == self.SI_CCS_LIBRARY and 'libraries' in indicator_data and indicator_data['libraries']:
                    # Main entry showing count and all library names
                    lib_count = len(indicator_data['libraries'])
                    lib_list = ', '.join(indicator_data['libraries'])
                    details.append(DetailItem(
                        severity=Severity.INFO,
                        name=indicator_name,
                        line_number=indicator_data['line_number'],
                        file_path=indicator_data['file_path'],
                        reason=f"Found {lib_count} CCS libraries: {lib_list}"
                    ))
                else:
                    # Use formatted value if available, otherwise default message
                    reason = indicator_data.get('value', 'SI setting found')
                    details.append(DetailItem(
                        severity=Severity.INFO,
                        name=indicator_name,
                        line_number=indicator_data['line_number'],
                        file_path=indicator_data['file_path'],
                        reason=reason
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
                    reason=f"SI setting not found{reason_suffix}"
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
                'description': 'SI setting not found',
                'items': missing_indicators
            }

        # Prepare custom log lines for log output
        total_indicators = len(self._si_indicators)
        log_lines: List[str] = []

        if missing_indicators:
            # Determine severity/label depending on waiver mode
            miss_severity_label = "Info" if is_waiver_zero else "Fail"
            miss_tag = "INFO01" if is_waiver_zero else "ERROR01"
            miss_desc = "SI settings (forced PASS mode)" if is_waiver_zero else "SI setting not found"

            log_lines.append(f"IMP-10-0-0-06-{miss_tag}: {miss_desc}:")
            log_lines.append(f"  Severity: {miss_severity_label} Occurrence: {len(missing_indicators)}")
            for indicator_name in missing_indicators:
                log_lines.append(f"  - {self._get_indicator_label(indicator_name)}")

        if found_indicators:
            found_desc = (
                f"SI setting verified ({len(found_indicators)}/{total_indicators} indicators found)"
                if total_indicators else "SI settings detected"
            )
            log_lines.append(f"IMP-10-0-0-06-INFO01: {found_desc}:")
            log_lines.append(f"  Severity: Info Occurrence: {len(found_indicators)}")

            indicator_order = [
                self.SI_SIGNOFF_SETTINGS,
                self.SI_DELAYCAL_ENABLE,
                self.SI_CCS_NOISE_DATA,
                self.SI_GLITCH_ANALYSIS,
                self.SI_CCS_LIBRARY
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
        - FAIL: Any pattern_items not found
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
        mismatch_patterns = []
        self._log_lines_override = None
        
        # Check each pattern_items
        for pattern in self._pattern_items:
            result = self._check_pattern_in_log(pattern)
            
            if result['found']:
                found_patterns.append(pattern)
                # Keep the report concise by omitting the full log line in the reason.
                reason = "SI setting is correct"
                details.append(DetailItem(
                    severity=Severity.INFO,
                    name=pattern,
                    line_number=result['line_number'],
                    file_path=result['file_path'],
                    reason=reason
                ))
            elif result['mismatch']:
                # Found related content but value doesn't match
                mismatch_patterns.append(pattern)
                severity = Severity.INFO if is_waiver_zero else Severity.FAIL
                reason_suffix = "[WAIVED_AS_INFO]" if is_waiver_zero else ""
                indicator_name = self._map_pattern_to_indicator(pattern)
                indicator_label = self._get_indicator_label(indicator_name)
                actual_val = result.get('actual_value', '')
                base_reason = f"SI setting isn't correct: expected '{pattern}', found '{actual_val}'"
                details.append(DetailItem(
                    severity=severity,
                    name=pattern,
                    line_number=result['line_number'],
                    file_path=result['file_path'],
                    reason=f"{base_reason}{reason_suffix}"
                ))
            else:
                # Completely missing
                missing_patterns.append(pattern)
                severity = Severity.INFO if is_waiver_zero else Severity.FAIL
                reason_suffix = "[WAIVED_AS_INFO]" if is_waiver_zero else ""
                indicator_name = self._map_pattern_to_indicator(pattern)
                indicator_label = self._get_indicator_label(indicator_name)
                base_reason = f"SI setting isn't correct: expected '{indicator_label}'"
                details.append(DetailItem(
                    severity=severity,
                    name=pattern,
                    line_number=0,
                    file_path="N/A",
                    reason=f"{base_reason} not found{reason_suffix}"
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
        
        # Prepare custom log lines similar to Type 1
        total_patterns = len(self._pattern_items)
        error_groups = {}
        info_groups = {}
        log_lines: List[str] = []

        # Handle missing patterns (completely not found)
        if missing_patterns:
            miss_severity_label = "Info" if is_waiver_zero else "Fail"
            miss_tag = "INFO01" if is_waiver_zero else "ERROR01"
            miss_desc = "SI settings treated as correct via waiver" if is_waiver_zero else "SI setting isn't correct (missing required indicators)"

            log_lines.append(f"IMP-10-0-0-06-{miss_tag}: {miss_desc}:")
            log_lines.append(f"  Severity: {miss_severity_label} Occurrence: {len(missing_patterns)}")
            for pattern in missing_patterns:
                indicator_name = self._map_pattern_to_indicator(pattern)
                label = self._get_indicator_label(indicator_name) if indicator_name else pattern
                log_lines.append(f"  - {label} (SI setting isn't correct: missing)")

            if not is_waiver_zero:
                error_groups['ERROR01'] = {
                    "description": "SI setting isn't correct (missing required indicators)",
                    "items": [self._get_indicator_label(self._map_pattern_to_indicator(p)) or p for p in missing_patterns]
                }
        
        # Handle mismatch patterns (found but value doesn't match)
        if mismatch_patterns:
            mismatch_severity_label = "Info" if is_waiver_zero else "Fail"
            mismatch_tag = "INFO02" if is_waiver_zero else "ERROR02"
            mismatch_desc = "SI settings treated as correct via waiver" if is_waiver_zero else "SI setting isn't correct (value mismatch)"

            log_lines.append(f"IMP-10-0-0-06-{mismatch_tag}: {mismatch_desc}:")
            log_lines.append(f"  Severity: {mismatch_severity_label} Occurrence: {len(mismatch_patterns)}")
            for pattern in mismatch_patterns:
                indicator_name = self._map_pattern_to_indicator(pattern)
                label = self._get_indicator_label(indicator_name) if indicator_name else pattern
                log_lines.append(f"  - {label} (SI setting isn't correct: mismatch)")

            if not is_waiver_zero:
                error_groups['ERROR02'] = {
                    "description": "SI setting isn't correct (value mismatch)",
                    "items": [self._get_indicator_label(self._map_pattern_to_indicator(p)) or p for p in mismatch_patterns]
                }

        if found_patterns:
            if total_patterns and len(found_patterns) == total_patterns:
                found_desc = f"SI setting is correct ({len(found_patterns)}/{total_patterns} indicators found)"
            elif total_patterns:
                found_desc = f"SI setting partially correct ({len(found_patterns)}/{total_patterns} indicators found)"
            else:
                found_desc = "SI settings detected"
            log_lines.append(f"IMP-10-0-0-06-INFO01: {found_desc}:")
            log_lines.append(f"  Severity: Info Occurrence: {len(found_patterns)}")

            indicator_order = [
                self.SI_SIGNOFF_SETTINGS,
                self.SI_DELAYCAL_ENABLE,
                self.SI_CCS_NOISE_DATA,
                self.SI_GLITCH_ANALYSIS,
                self.SI_CCS_LIBRARY
            ]

            for indicator_name in indicator_order:
                pattern = self._find_pattern_for_indicator(indicator_name)
                if not pattern or pattern not in found_patterns:
                    continue
                log_lines.append(f"  - {self._format_indicator_success_line(indicator_name) }")

            info_groups['INFO01'] = {
                'description': found_desc,
                'items': [self._get_indicator_label(self._map_pattern_to_indicator(p)) or p for p in found_patterns]
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
        mismatch_unwaived = []
        mismatch_waived = []
        self._log_lines_override = None
        
        # Check each pattern_items
        for pattern in self._pattern_items:
            result = self._check_pattern_in_log(pattern)
            
            if result['found']:
                found_patterns.append(pattern)
                details.append(DetailItem(
                    severity=Severity.INFO,
                    name=pattern,
                    line_number=result['line_number'],
                    file_path=result['file_path'],
                    reason="SI setting is correct"
                ))
            elif result['mismatch']:
                # Found but value mismatch
                if pattern in waive_set:
                    mismatch_waived.append(pattern)
                    waiver_reason = waive_items_dict.get(pattern, '')
                    actual_val = result.get('actual_value', '')
                    base_reason = f"SI setting isn't correct: expected '{pattern}', found '{actual_val}'"
                    reason = f"{base_reason} {waiver_reason}[WAIVER]" if waiver_reason else f"{base_reason} [WAIVER]"
                    details.append(DetailItem(
                        severity=Severity.INFO,
                        name=pattern,
                        line_number=result['line_number'],
                        file_path=result['file_path'],
                        reason=reason
                    ))
                else:
                    mismatch_unwaived.append(pattern)
                    actual_val = result.get('actual_value', '')
                    details.append(DetailItem(
                        severity=Severity.FAIL,
                        name=pattern,
                        line_number=result['line_number'],
                        file_path=result['file_path'],
                        reason=f"SI setting isn't correct: expected '{pattern}', found '{actual_val}'"
                    ))
            else:
                # Completely missing
                if pattern in waive_set:
                    missing_waived.append(pattern)
                    waiver_reason = waive_items_dict.get(pattern, '')
                    indicator_name = self._map_pattern_to_indicator(pattern)
                    indicator_label = self._get_indicator_label(indicator_name)
                    base_reason = f"SI setting isn't correct: expected '{indicator_label}' not found"
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
                    indicator_name = self._map_pattern_to_indicator(pattern)
                    indicator_label = self._get_indicator_label(indicator_name)
                    details.append(DetailItem(
                        severity=Severity.FAIL,
                        name=pattern,
                        line_number=0,
                        file_path="N/A",
                        reason=f"SI setting isn't correct: expected '{indicator_label}' not found"
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
        
        is_pass = (len(missing_unwaived) == 0 and len(mismatch_unwaived) == 0)
        
        # Determine if this is a true PASS or waived PASS
        has_waived_errors = (len(missing_waived) > 0 or len(mismatch_waived) > 0)
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
                'description': "SI setting isn't correct (missing required indicators)",
                'items': [self._get_indicator_label(self._map_pattern_to_indicator(p)) or p for p in missing_unwaived]
            }
            log_lines.append("IMP-10-0-0-06-ERROR01: SI setting isn't correct (missing required indicators):")
            log_lines.append(f"  Severity: Fail Occurrence: {len(missing_unwaived)}")
            for pattern in missing_unwaived:
                indicator_name = self._map_pattern_to_indicator(pattern)
                label = self._get_indicator_label(indicator_name) if indicator_name else pattern
                log_lines.append(f"  - {label} (SI setting isn't correct: missing)")
        
        # Handle mismatch patterns (not waived)
        if mismatch_unwaived:
            error_groups['ERROR02'] = {
                'description': "SI setting isn't correct (value mismatch)",
                'items': [self._get_indicator_label(self._map_pattern_to_indicator(p)) or p for p in mismatch_unwaived]
            }
            log_lines.append("IMP-10-0-0-06-ERROR02: SI setting isn't correct (value mismatch):")
            log_lines.append(f"  Severity: Fail Occurrence: {len(mismatch_unwaived)}")
            for pattern in mismatch_unwaived:
                indicator_name = self._map_pattern_to_indicator(pattern)
                label = self._get_indicator_label(indicator_name) if indicator_name else pattern
                log_lines.append(f"  - {label} (SI setting isn't correct: mismatch)")
        
        # Handle unused waivers
        if unused_waivers:
            warn_groups['WARN01'] = {
                'description': 'Waiver not used',
                'items': unused_waivers
            }
            log_lines.append("IMP-10-0-0-06-WARN01: Waiver not used:")
            log_lines.append(f"  Severity: Warn Occurrence: {len(unused_waivers)}")
            for item in unused_waivers:
                log_lines.append(f"  - {item}")
        
        # Handle found patterns and waived patterns separately
        if found_patterns:
            if total_patterns and len(found_patterns) == total_patterns:
                found_desc = f"SI setting is correct ({len(found_patterns)}/{total_patterns} indicators found)"
            elif total_patterns:
                found_desc = f"SI setting is correct ({len(found_patterns)}/{total_patterns} indicators found)"
            else:
                found_desc = "SI settings verified"
            
            info_groups['INFO01'] = {
                'description': found_desc,
                'items': [self._get_indicator_label(self._map_pattern_to_indicator(p)) or p for p in found_patterns]
            }
            
            log_lines.append(f"IMP-10-0-0-06-INFO01: {found_desc}:")
            log_lines.append(f"  Severity: Info Occurrence: {len(found_patterns)}")
            
            indicator_order = [
                self.SI_SIGNOFF_SETTINGS,
                self.SI_DELAYCAL_ENABLE,
                self.SI_CCS_NOISE_DATA,
                self.SI_GLITCH_ANALYSIS,
                self.SI_CCS_LIBRARY
            ]
            
            for indicator_name in indicator_order:
                pattern = self._find_pattern_for_indicator(indicator_name)
                if not pattern or pattern not in found_patterns:
                    continue
                log_lines.append(f"  - {self._format_indicator_success_line(indicator_name)}")
        
        # Handle waived patterns separately (INFO02)
        waived_patterns = missing_waived + mismatch_waived
        if waived_patterns:
            waived_count = len(waived_patterns)
            waived_desc = f"SI setting verified via waiver ({waived_count} indicator{'s' if waived_count > 1 else ''} waived)"
            
            info_groups['INFO02'] = {
                'description': waived_desc,
                'items': [self._get_indicator_label(self._map_pattern_to_indicator(p)) or p for p in waived_patterns]
            }
            
            log_lines.append(f"IMP-10-0-0-06-INFO02: {waived_desc}:")
            log_lines.append(f"  Severity: Info Occurrence: {waived_count}")
            
            indicator_order = [
                self.SI_SIGNOFF_SETTINGS,
                self.SI_DELAYCAL_ENABLE,
                self.SI_CCS_NOISE_DATA,
                self.SI_GLITCH_ANALYSIS,
                self.SI_CCS_LIBRARY
            ]
            
            for indicator_name in indicator_order:
                pattern = self._find_pattern_for_indicator(indicator_name)
                if not pattern:
                    continue
                if pattern in missing_waived:
                    label = self._get_indicator_label(indicator_name)
                    log_lines.append(f"  - {label} [WAIVED: missing]")
                elif pattern in mismatch_waived:
                    label = self._get_indicator_label(indicator_name)
                    log_lines.append(f"  - {label} [WAIVED: mismatch]")
        
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
        
        # Check all 5 indicators
        found_indicators = []
        missing_indicators = []
        
        for indicator_name, indicator_data in self._si_indicators.items():
            if indicator_data['found']:
                found_indicators.append(indicator_name)
                details.append(DetailItem(
                    severity=Severity.INFO,
                    name=indicator_name,
                    line_number=indicator_data['line_number'],
                    file_path=indicator_data['file_path'],
                    reason="SI setting is correct"
                ))
            else:
                missing_indicators.append(indicator_name)
                details.append(DetailItem(
                    severity=Severity.FAIL,
                    name=indicator_name,
                    line_number=0,
                    file_path="N/A",
                    reason="SI setting isn't correct: indicator not found"
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
        total_indicators = len(self._si_indicators)
        error_groups = {}
        warn_groups = {}
        info_groups = {}
        log_lines: List[str] = []
        
        if missing_indicators:
            error_groups['ERROR01'] = {
                'description': "SI setting isn't correct (missing indicators)",
                'items': missing_indicators
            }
            log_lines.append("IMP-10-0-0-06-ERROR01: SI setting isn't correct (missing indicators):")
            log_lines.append(f"  Severity: Fail Occurrence: {len(missing_indicators)}")
            for indicator_name in missing_indicators:
                log_lines.append(f"  - {self._get_indicator_label(indicator_name)}")
        
        # Handle found indicators (INFO01)
        if found_indicators:
            if total_indicators and len(found_indicators) == total_indicators:
                info_desc = f"SI setting is correct ({len(found_indicators)}/{total_indicators} indicators found)"
            elif total_indicators:
                info_desc = f"SI setting is correct ({len(found_indicators)}/{total_indicators} indicators found)"
            else:
                info_desc = "SI setting verified"
            
            info_groups['INFO01'] = {
                'description': info_desc,
                'items': found_indicators
            }
            
            log_lines.append(f"IMP-10-0-0-06-INFO01: {info_desc}:")
            log_lines.append(f"  Severity: Info Occurrence: {len(found_indicators)}")
            
            indicator_order = [
                self.SI_SIGNOFF_SETTINGS,
                self.SI_DELAYCAL_ENABLE,
                self.SI_CCS_NOISE_DATA,
                self.SI_GLITCH_ANALYSIS,
                self.SI_CCS_LIBRARY
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
            
            log_lines.append(f"IMP-10-0-0-06-WARN01: {waiver_desc}:")
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
    checker = SISettingChecker()
    checker.run()
