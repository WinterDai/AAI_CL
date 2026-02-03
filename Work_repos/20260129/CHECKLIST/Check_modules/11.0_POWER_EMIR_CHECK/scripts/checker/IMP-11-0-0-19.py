################################################################################
# Script Name: IMP-11-0-0-19.py
#
# Purpose:
#   Confirm you are aware of and follow the customers' requirement about wake-up/rush-current if they have.(For non-PSO, please fill N/A)
#
# Logic:
#   - Parse Powerup.rpt to extract rush current, wake-up time, and switch activation metrics
#   - Extract summary metrics: max_rush_current (A), wake_up_time (s), total_switches, last_switch_time (s)
#   - Verify all power switches turned on successfully (switches_turned_on == total_switches)
#   - Extract first and last switch activation instances with timestamps
#   - Output metrics with bilingual reminder to confirm customer requirements
#   - Support waiver for incomplete activation or missing metrics
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
# Author: Chudong Yu
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
class Check_11_0_0_19(InputFileParserMixin, OutputBuilderMixin, WaiverHandlerMixin, BaseChecker):
    """
    IMP-11-0-0-19: Confirm you are aware of and follow the customers' requirement about wake-up/rush-current if they have.(For non-PSO, please fill N/A)
    
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
    FOUND_DESC_TYPE1_4 = "Powerup report complete with all required metrics found"
    MISSING_DESC_TYPE1_4 = "Powerup report incomplete or missing required metrics"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_DESC_TYPE2_3 = "All power switches activated successfully, metrics validated"
    MISSING_DESC_TYPE2_3 = "Power switch activation incomplete or metrics missing"
    
    # All Types (waiver description unified)
    WAIVED_DESC = "Powerup report issues waived per design team approval"
    
    # ⭐ REASON CONSTANTS - Split by Type semantics (API-025)
    # ALL Types pass found_reason/missing_reason, but use different constants
    
    # Type 1/4: Boolean checks - emphasize "found/not found" (existence)
    FOUND_REASON_TYPE1_4 = "Powerup report contains rush current, wake-up time, and complete switch activation data"
    MISSING_REASON_TYPE1_4 = "Required rush current or wake-up time data not found in powerup report"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_REASON_TYPE2_3 = "All power switches turned on successfully, rush current and wake-up time metrics validated"
    MISSING_REASON_TYPE2_3 = "Power switch activation failed (partial activation detected) or required metrics not satisfied"
    
    # Waiver-related (Type 3/4 only)
    WAIVED_BASE_REASON = "Powerup simulation metrics waived - customer requirements confirmed separately"
    UNUSED_WAIVER_REASON = "Waiver entry not matched - no corresponding powerup issue found in report"
    
    def __init__(self):
        """Initialize the checker."""
        super().__init__(
            check_module="11.0_POWER_EMIR_CHECK",
            item_id="IMP-11-0-0-19",
            item_desc="Confirm you are aware of and follow the customers' requirement about wake-up/rush-current if they have.(For non-PSO, please fill N/A)"
        )
        # Custom member variables for parsed data
        self._parsed_items: List[Dict[str, Any]] = []
        self._metadata: Dict[str, str] = {}
        self._rush_current: Optional[float] = None
        self._wake_up_time: Optional[float] = None
        self._switches_turned_on: Optional[int] = None
        self._total_switches: Optional[int] = None
        self._first_switch_instance: Optional[str] = None
        self._first_switch_time: Optional[float] = None
        self._last_switch_instance: Optional[str] = None
        self._last_switch_time: Optional[float] = None
    
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
        Parse Powerup.rpt to extract rush current, wake-up time, and switch activation metrics.
        
        Extracts:
        - Rush current (A)
        - Wake-up time (s)
        - Switch activation counts (turned_on/total)
        - First/last switch instances with timestamps
        - Simulation metadata (time, threshold voltage)
        
        Returns:
            Dict with parsed data:
            - 'items': List[Dict] - Validation items (metrics and activation status)
            - 'metadata': Dict - File metadata (simulation time, threshold)
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
        rush_current = None
        wake_up_time = None
        switches_turned_on = None
        total_switches = None
        first_switch_instance = None
        first_switch_time = None
        last_switch_instance = None
        last_switch_time = None
        simulation_time = None
        threshold_voltage = None
        
        # Initialize line number tracking
        rush_current_line = 0
        wake_up_time_line = 0
        switches_line = 0
        first_switch_line = 0
        last_switch_line = 0
        
        # 3. Parse each input file for powerup metrics
        for file_path in valid_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    in_detailed_section = False
                    for line_num, line in enumerate(f, 1):
                        # Pattern 1: Extract maximum rush current
                        match_rush = re.search(r'Measured maximum rush current\s*=\s*([0-9.eE+-]+)A', line)
                        if match_rush:
                            rush_current = float(match_rush.group(1))
                            rush_current_line = line_num
                        
                        # Pattern 2: Extract wake-up time
                        match_wakeup = re.search(r'Measured wake-up time for switched net\s*=\s*([0-9.eE+-]+)s', line)
                        if match_wakeup:
                            wake_up_time = float(match_wakeup.group(1))
                            wake_up_time_line = line_num
                        
                        # Pattern 3: Extract switch counts
                        match_switches = re.search(r'Number of power switches turned on in this simulation\s*=\s*(\d+)\s*\[of total\s*(\d+)\]', line)
                        if match_switches:
                            switches_turned_on = int(match_switches.group(1))
                            total_switches = int(match_switches.group(2))
                            switches_line = line_num
                        
                        # Pattern 4: Extract last switch information
                        match_last = re.search(r"Last power switch to turn-on in this simulation is '([^']+)' at time\s*([0-9.eE+-]+)s", line)
                        if match_last:
                            last_switch_instance = match_last.group(1)
                            last_switch_time = float(match_last.group(2))
                            last_switch_line = line_num
                        
                        # Pattern 6: Extract simulation metadata
                        match_sim_time = re.search(r'Simulation time\s*=\s*([0-9.eE+-]+)s', line)
                        if match_sim_time:
                            simulation_time = float(match_sim_time.group(1))
                        
                        match_threshold = re.search(r'Threshold \(Vt\)\s*=\s*([0-9.]+)V', line)
                        if match_threshold:
                            threshold_voltage = float(match_threshold.group(1))
                        
                        # Detect Detailed Report section
                        if 'Detailed Report' in line:
                            in_detailed_section = True
                            continue
                        
                        # Pattern 5: Extract first switch from Detailed Report section
                        # Format: ORDER  TURN-ON TIME  PEAK CURRENT  INSTANCES
                        # Example: 1  7.33883e-10  0.0134068  cdns_lp6_x48_ew_phy_top_SW_MODULE/PSW_18497:NSLEEPIN
                        if in_detailed_section and first_switch_instance is None:
                            # Skip header lines and lines with "ORDER" keyword
                            if 'ORDER' in line or 'TURN-ON' in line or line.strip() == '':
                                continue
                            # Try to match data line: ORDER(int) followed by time, current, instance
                            match_first = re.search(r'^\s*(\d+)\s+([0-9.eE+-]+)\s+[0-9.eE+-]+\s+(.+)$', line)
                            if match_first:
                                first_switch_instance = match_first.group(3).strip()
                                first_switch_time = float(match_first.group(2))
                                first_switch_line = line_num
            except Exception as e:
                errors.append(f"Error parsing {file_path}: {str(e)}")
        
        # Store parsed metrics
        self._rush_current = rush_current
        self._wake_up_time = wake_up_time
        self._switches_turned_on = switches_turned_on
        self._total_switches = total_switches
        self._first_switch_instance = first_switch_instance
        self._first_switch_time = first_switch_time
        self._last_switch_instance = last_switch_instance
        self._last_switch_time = last_switch_time
        
        # Build metadata
        if simulation_time is not None:
            metadata['simulation_time'] = f"{simulation_time}s"
        if threshold_voltage is not None:
            metadata['threshold_voltage'] = f"{threshold_voltage}V"
        
        # Store line numbers in metadata for use in Type 2 output
        metadata['rush_current_line'] = rush_current_line
        metadata['wake_up_time_line'] = wake_up_time_line
        metadata['switches_line'] = switches_line
        metadata['first_switch_line'] = first_switch_line
        metadata['last_switch_line'] = last_switch_line
        
        # Build items based on validation results
        # Check for missing metrics
        if rush_current is None:
            items.append({
                'name': 'MISSING_METRIC_RUSH_CURRENT',
                'line_number': 0,
                'file_path': str(valid_files[0]) if valid_files else 'N/A',
                'type': 'missing_metric',
                'detail': 'Rush current value not found in powerup report Summary section'
            })
        
        if wake_up_time is None:
            items.append({
                'name': 'MISSING_METRIC_WAKE_UP_TIME',
                'line_number': 0,
                'file_path': str(valid_files[0]) if valid_files else 'N/A',
                'type': 'missing_metric',
                'detail': 'Wake-up time value not found in powerup report Summary section'
            })
        
        # Check for incomplete switch activation
        if switches_turned_on is not None and total_switches is not None:
            if switches_turned_on < total_switches:
                items.append({
                    'name': 'INCOMPLETE_ACTIVATION',
                    'line_number': 0,
                    'file_path': str(valid_files[0]) if valid_files else 'N/A',
                    'type': 'activation_failure',
                    'detail': f"Only {switches_turned_on}/{total_switches} power switches turned on - {total_switches - switches_turned_on} switches failed to activate"
                })
        
        # If all metrics present and activation complete, create success items
        if (rush_current is not None and wake_up_time is not None and 
            switches_turned_on is not None and total_switches is not None and
            switches_turned_on == total_switches):
            
            # Create separate item for each metric with line number and file path
            # Use numeric prefixes to control output order (will be stripped in display)
            file_path = str(valid_files[0]) if valid_files else 'N/A'
            
            # Rush Current item (order: 1)
            items.append({
                'name': f'RUSH_CURRENT',
                'line_number': rush_current_line,
                'file_path': file_path,
                'type': 'success',
                'detail': f"1_Rush Current: {rush_current}A"
            })
            
            # Wake-up Time item (order: 2)
            items.append({
                'name': f'WAKE_UP_TIME',
                'line_number': wake_up_time_line,
                'file_path': file_path,
                'type': 'success',
                'detail': f"2_Wake-up Time: {wake_up_time}s"
            })
            
            # Switches item (order: 3)
            items.append({
                'name': f'SWITCHES',
                'line_number': switches_line,
                'file_path': file_path,
                'type': 'success',
                'detail': f"3_Switches: {switches_turned_on}/{total_switches}"
            })
            
            # First Switch item (order: 4)
            if first_switch_instance and first_switch_time is not None:
                items.append({
                    'name': f'FIRST_SWITCH',
                    'line_number': first_switch_line,
                    'file_path': file_path,
                    'type': 'success',
                    'detail': f"4_First Switch: {first_switch_instance} @ {first_switch_time}s"
                })
            
            # Last Switch item (order: 5)
            if last_switch_instance and last_switch_time is not None:
                items.append({
                    'name': f'LAST_SWITCH',
                    'line_number': last_switch_line,
                    'file_path': file_path,
                    'type': 'success',
                    'detail': f"5_Last Switch: {last_switch_instance} @ {last_switch_time}s"
                })
            
            # Add reminder as last INFO item (order: 9 to ensure it's last)
            items.append({
                'name': 'Z_USER_CONFIRMATION_REMINDER',
                'line_number': 0,
                'file_path': file_path,
                'type': 'success',
                'detail': '9_Please confirm your wake-up time and rush current followed customer requirements'
            })
        
        # 4. Store frequently reused data on self
        self._parsed_items = items
        self._metadata = metadata
        
        return {
            'items': items,
            'metadata': metadata,
            'errors': errors
        }
    # Helper Methods (Optional - Add as needed)
    

    # =========================================================================
    # Type 1: Boolean Check
    # =========================================================================

    def _execute_type1(self) -> CheckResult:
        """
        Type 1: Boolean check without waiver support.

        Validates powerup report completeness:
        - Summary section exists
        - All power switches activated successfully
        - Rush current and wake-up time metrics present
        - Extracts first and last switch activation details

        Returns:
            CheckResult with PASS if all validations succeed, FAIL otherwise
        """
        violations = self._type1_core_logic()

        # Build found_items from parsed data (metrics that passed validation)
        data = self._parse_input_files()
        items = data.get('items', [])

        found_items = {}
        missing_items = {}
        
        # Separate success items from violations, ensure reminder item is processed last
        reminder_item = None
        for item in items:
            if item.get('type') == 'success':
                # Check if this is the reminder item
                if item.get('name') == 'Z_USER_CONFIRMATION_REMINDER':
                    reminder_item = item
                    continue
                    
                # Use detail as the key (full display string) for found items
                detail_text = item.get('detail', '')
                found_items[detail_text] = {
                    'name': item['name'],
                    'line_number': item['line_number'],
                    'file_path': item['file_path'],
                    'detail': detail_text
                }
            else:
                # Use detail as reason for missing items
                detail_text = item.get('detail', '')
                missing_items[item['name']] = {
                    'name': item['name'],
                    'line_number': item['line_number'],
                    'file_path': item['file_path'],
                    'reason': detail_text
                }
        
        # Add reminder item last to ensure it appears last in output
        if reminder_item:
            detail_text = reminder_item.get('detail', '')
            found_items[detail_text] = {
                'name': reminder_item['name'],
                'line_number': reminder_item['line_number'],
                'file_path': reminder_item['file_path'],
                'detail': detail_text
            }

        # Use callable found_reason to provide different reasons for different items
        def get_found_reason(metadata):
            name = metadata.get('name', '')
            if name == 'Z_USER_CONFIRMATION_REMINDER':
                return ""  # No additional reason for reminder message
            return self.FOUND_REASON_TYPE1_4
        
        # Name extractor to remove numeric prefix used for sorting
        def extract_display_name(item_name, metadata):
            # Remove N_ prefix (e.g., "1_Rush Current" -> "Rush Current")
            if len(item_name) > 2 and item_name[0].isdigit() and item_name[1] == '_':
                return item_name[2:]
            return item_name

        return self.build_complete_output(
            found_items=found_items,
            missing_items=missing_items,
            found_desc=self.FOUND_DESC_TYPE1_4,
            missing_desc=self.MISSING_DESC_TYPE1_4,
            found_reason=get_found_reason,
            missing_reason=lambda m: m.get('reason', self.MISSING_REASON_TYPE1_4),
            name_extractor=extract_display_name
        )

    def _type1_core_logic(self) -> dict[str, dict]:
        """
        Core Type 1 boolean check logic (shared by Type 1 and Type 4).

        Validates powerup report:
        1. Summary section exists
        2. All power switches turned on successfully
        3. Rush current metric present
        4. Wake-up time metric present

        Returns:
            Dict of violations: {item_name: {'line_number': ..., 'file_path': ..., 'reason': ...}}
            Empty dict if all checks pass.
        """
        data = self._parse_input_files()
        items = data.get('items', [])
        
        violations = {}
        
        # Check for violations in parsed items
        for item in items:
            if item.get('type') != 'success':
                violations[item['name']] = {
                    'line_number': item['line_number'],
                    'file_path': item['file_path'],
                    'reason': item.get('detail', '')
                }

        return violations

    # =========================================================================
    # Type 4: Boolean Check with Waiver Logic
    # =========================================================================

    def _execute_type4(self) -> CheckResult:
        """
        Type 4: Boolean check with waiver support (reuses Type 1 core logic).

        Performs same validation as Type 1, but allows waivers for:
        - Incomplete switch activation
        - Missing rush current metric
        - Missing wake-up time metric

        Returns:
            CheckResult with PASS if all violations are waived, FAIL if unwaived violations exist
        """
        # Step 1: Get violations using Type 1's core logic
        violations = self._type1_core_logic()

        # Build found_items from parsed data (metrics that passed validation)
        data = self._parse_input_files()
        items = data.get('items', [])

        found_items = {}
        
        # Separate success items from violations, ensure reminder item is processed last
        reminder_item = None
        for item in items:
            if item.get('type') == 'success':
                # Check if this is the reminder item
                if item.get('name') == 'Z_USER_CONFIRMATION_REMINDER':
                    reminder_item = item
                    continue
                    
                # Use detail as the key (full display string) for found items
                detail_text = item.get('detail', '')
                found_items[detail_text] = {
                    'name': item['name'],
                    'line_number': item['line_number'],
                    'file_path': item['file_path'],
                    'detail': detail_text
                }
        
        # Add reminder item last to ensure it appears last in output
        if reminder_item:
            detail_text = reminder_item.get('detail', '')
            found_items[detail_text] = {
                'name': reminder_item['name'],
                'line_number': reminder_item['line_number'],
                'file_path': reminder_item['file_path'],
                'detail': detail_text
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

        # Name extractor to remove numeric prefix used for sorting
        def extract_display_name(item_name, metadata):
            # Remove N_ prefix (e.g., "1_Rush Current" -> "Rush Current")
            if len(item_name) > 2 and item_name[0].isdigit() and item_name[1] == '_':
                return item_name[2:]
            return item_name

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
            unused_waiver_reason=self.UNUSED_WAIVER_REASON,
            name_extractor=extract_display_name
        )

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _format_metrics_summary(self, metadata: dict) -> str:
        """
        Format powerup metrics into bilingual summary string.

        Args:
            metadata: Parsed metadata (not used, kept for compatibility)

        Returns:
            Formatted summary string with all metrics and bilingual reminder
        """
        # Use instance variables instead of metadata dict
        rush_current = self._rush_current
        wake_up_time = self._wake_up_time
        total_switches = self._total_switches if self._total_switches is not None else 0
        switches_turned_on = self._switches_turned_on if self._switches_turned_on is not None else 0
        first_switch = self._first_switch_instance
        first_switch_time = self._first_switch_time
        last_switch = self._last_switch_instance
        last_switch_time = self._last_switch_time

        # Format rush current and wake-up time
        rush_str = f"{rush_current}A" if rush_current is not None else 'N/A'
        wake_str = f"{wake_up_time}s" if wake_up_time is not None else 'N/A'

        # Format switch activation info
        switches_str = f"{switches_turned_on}/{total_switches}"
        first_str = f"{first_switch} @ {first_switch_time}s" if first_switch and first_switch_time is not None else 'N/A'
        last_str = f"{last_switch} @ {last_switch_time}s" if last_switch and last_switch_time is not None else 'N/A'

        # Build summary (without bilingual reminder - that's added separately)
        summary = (
            f"Rush Current: {rush_str} | "
            f"Wake-up Time: {wake_str} | "
            f"Switches: {switches_str} | "
            f"First Switch: {first_str} | "
            f"Last Switch: {last_str}"
        )

        return summary

    # =========================================================================
    # Type 2: Value Check
    # =========================================================================

    def _execute_type2(self) -> CheckResult:
        """Type 2: Pattern/value check without waiver support."""
        found_items, missing_items = self._type2_core_logic()

        # Name extractor to remove numeric prefix used for sorting
        def extract_display_name(item_name, metadata):
            # Remove N_ prefix (e.g., "1_Rush Current" -> "Rush Current")
            if len(item_name) > 2 and item_name[0].isdigit() and item_name[1] == '_':
                return item_name[2:]
            return item_name

        # FIXED: Pass dicts directly to build_complete_output
        return self.build_complete_output(
            found_items=found_items,
            missing_items=missing_items,
            found_desc=self.FOUND_DESC_TYPE2_3,
            missing_desc=self.MISSING_DESC_TYPE2_3,
            found_reason=self.FOUND_REASON_TYPE2_3,
            missing_reason=self.MISSING_REASON_TYPE2_3,
            name_extractor=extract_display_name
        )

    def _type2_core_logic(self) -> tuple[dict[str, dict], dict[str, dict]]:
        """
        Core Type 2 pattern matching logic (shared by Type 2 and Type 3).

        Returns:
            Tuple of (found_items, missing_items)
            - found_items: {metric_name: {'line_number': ..., 'file_path': ...}}
            - missing_items: {metric_name: {'line_number': ..., 'file_path': ..., 'reason': ...}}
        """
        data = self._parse_input_files()
        items = data.get('items', [])

        requirements = self.item_data.get('requirements', {})
        pattern_items = requirements.get('pattern_items', [])

        found_items = {}
        missing_items = {}

        # Extract metrics from instance variables (set by _parse_input_files)
        max_rush_current = self._rush_current
        wake_up_time = self._wake_up_time
        total_switches = self._total_switches if self._total_switches is not None else 0
        switches_turned_on = self._switches_turned_on if self._switches_turned_on is not None else 0
        first_switch_instance = self._first_switch_instance
        first_switch_time = self._first_switch_time
        last_switch_instance = self._last_switch_instance
        last_switch_time = self._last_switch_time

        # Get file path from valid files
        valid_files, _ = self.validate_input_files()
        file_path = str(valid_files[0]) if valid_files else 'N/A'
        
        # Get line numbers from metadata
        rush_line = data.get('metadata', {}).get('rush_current_line', 0)
        wakeup_line = data.get('metadata', {}).get('wake_up_time_line', 0)
        switches_line = data.get('metadata', {}).get('switches_line', 0)
        first_line = data.get('metadata', {}).get('first_switch_line', 0)
        last_line = data.get('metadata', {}).get('last_switch_line', 0)
        
        # Determine primary line number (prefer rush_current_line as primary metric)
        primary_line = rush_line if rush_line > 0 else (wakeup_line if wakeup_line > 0 else switches_line)

        # Build comprehensive metric display string with line numbers
        info_parts = []
        if max_rush_current is not None:
            line_info = f" (line {rush_line})" if rush_line > 0 else ""
            info_parts.append(f"Rush Current: {max_rush_current}A{line_info}")
        if wake_up_time is not None:
            line_info = f" (line {wakeup_line})" if wakeup_line > 0 else ""
            info_parts.append(f"Wake-up Time: {wake_up_time}s{line_info}")
        if total_switches > 0:
            line_info = f" (line {switches_line})" if switches_line > 0 else ""
            info_parts.append(f"Switches: {switches_turned_on}/{total_switches}{line_info}")
        if first_switch_instance and first_switch_time is not None:
            line_info = f" (line {first_line})" if first_line > 0 else ""
            info_parts.append(f"First Switch: {first_switch_instance} @ {first_switch_time}s{line_info}")
        if last_switch_instance and last_switch_time is not None:
            line_info = f" (line {last_line})" if last_line > 0 else ""
            info_parts.append(f"Last Switch: {last_switch_instance} @ {last_switch_time}s{line_info}")
        
        metric_display = ' | '.join(info_parts)
        
        # Separate reminder message
        reminder_message = '⚠️ Please confirm your wake-up time and rush current meet customer requirements (请确认你的wakeup time和rush current符合客户的要求)'

        # Check if all switches turned on successfully
        all_switches_on = (switches_turned_on == total_switches and total_switches > 0)

        # Match pattern_items against extracted metrics
        # Support two formats:
        # 1. Simplified: "Rush Current", "Wake-up Time" (README golden format)
        # 2. Detailed: "Rush Current: 0.427297A", "Wake-up Time: 1.11e-07s" (for specific value validation)
        patterns_matched = 0
        for pattern in pattern_items:
            matched = False

            # Normalize pattern - strip whitespace
            pattern_normalized = pattern.strip()
            
            # Check for Rush Current pattern (simplified or detailed format)
            if pattern_normalized == "Rush Current" or pattern_normalized.startswith("Rush Current:"):
                if max_rush_current is not None:
                    # If simplified format, just check existence
                    if pattern_normalized == "Rush Current":
                        patterns_matched += 1
                        matched = True
                    # If detailed format with value, validate exact match
                    else:
                        expected_value_str = pattern_normalized.replace("Rush Current:", "").strip().rstrip('A')
                        try:
                            expected_value = float(expected_value_str)
                            if abs(max_rush_current - expected_value) < 1e-9:
                                patterns_matched += 1
                                matched = True
                            else:
                                actual_str = f"{max_rush_current}A"
                                missing_items[pattern] = {
                                    'line_number': rush_line,
                                    'file_path': file_path,
                                    'reason': f'Expected rush current {expected_value_str}A, found {actual_str}'
                                }
                                matched = True
                        except ValueError:
                            missing_items[pattern] = {
                                'line_number': 0,
                                'file_path': file_path,
                                'reason': f'Invalid rush current value format in pattern: {pattern}'
                            }
                            matched = True
                else:
                    # Rush current not found in report
                    missing_items[pattern] = {
                        'line_number': 0,
                        'file_path': file_path,
                        'reason': 'Rush current value not found in powerup report'
                    }
                    matched = True

            # Check for Wake-up Time pattern (simplified or detailed format)
            elif pattern_normalized == "Wake-up Time" or pattern_normalized.startswith("Wake-up Time:"):
                if wake_up_time is not None:
                    # If simplified format, just check existence
                    if pattern_normalized == "Wake-up Time":
                        patterns_matched += 1
                        matched = True
                    # If detailed format with value, validate exact match
                    else:
                        expected_value_str = pattern_normalized.replace("Wake-up Time:", "").strip().rstrip('s')
                        try:
                            expected_value = float(expected_value_str)
                            if abs(wake_up_time - expected_value) < 1e-15:
                                patterns_matched += 1
                                matched = True
                            else:
                                actual_str = f"{wake_up_time}s"
                                missing_items[pattern] = {
                                    'line_number': wakeup_line,
                                    'file_path': file_path,
                                    'reason': f'Expected wake-up time {expected_value_str}s, found {actual_str}'
                                }
                                matched = True
                        except ValueError:
                            missing_items[pattern] = {
                                'line_number': 0,
                                'file_path': file_path,
                                'reason': f'Invalid wake-up time value format in pattern: {pattern}'
                            }
                            matched = True
                else:
                    # Wake-up time not found in report
                    missing_items[pattern] = {
                        'line_number': 0,
                        'file_path': file_path,
                        'reason': 'Wake-up time value not found in powerup report'
                    }
                    matched = True

            if not matched:
                missing_items[pattern] = {
                    'line_number': 0,
                    'file_path': file_path,
                    'reason': f'Pattern "{pattern}" not recognized or not found in powerup report'
                }

        # If all patterns matched and switches all turned on, add individual metrics to found_items
        if patterns_matched == len(pattern_items) and all_switches_on:
            # Add each metric as a separate found item with numeric prefix for ordering
            if max_rush_current is not None:
                found_items[f"1_Rush Current: {max_rush_current}A"] = {
                    'line_number': rush_line,
                    'file_path': file_path
                }
            
            if wake_up_time is not None:
                found_items[f"2_Wake-up Time: {wake_up_time}s"] = {
                    'line_number': wakeup_line,
                    'file_path': file_path
                }
            
            if total_switches > 0:
                found_items[f"3_Switches: {switches_turned_on}/{total_switches}"] = {
                    'line_number': switches_line,
                    'file_path': file_path
                }
            
            if first_switch_instance and first_switch_time is not None:
                found_items[f"4_First Switch: {first_switch_instance} @ {first_switch_time}s"] = {
                    'line_number': first_line,
                    'file_path': file_path
                }
            
            if last_switch_instance and last_switch_time is not None:
                found_items[f"5_Last Switch: {last_switch_instance} @ {last_switch_time}s"] = {
                    'line_number': last_line,
                    'file_path': file_path
                }
            
            # Add reminder as separate found item (order: 9 to ensure it's last)
            found_items['9_Please confirm your wake-up time and rush current followed customer requirements'] = {
                'line_number': 0,
                'file_path': file_path
            }

        # If switches didn't all turn on, add to missing_items
        if not all_switches_on:
            switch_error = f"Switch activation incomplete: {switches_turned_on}/{total_switches} switches turned on"
            missing_items[switch_error] = {
                'line_number': switches_line,
                'file_path': file_path,
                'reason': 'Not all power switches activated successfully'
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

        # Name extractor to remove numeric prefix used for sorting
        def extract_display_name(item_name, metadata):
            # Remove N_ prefix (e.g., "1_Rush Current" -> "Rush Current")
            if len(item_name) > 2 and item_name[0].isdigit() and item_name[1] == '_':
                return item_name[2:]
            return item_name

        # Step 5: Build output (FIXED: Pass dicts directly, not list(dict.values()))
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
            unused_waiver_reason=self.UNUSED_WAIVER_REASON,
            name_extractor=extract_display_name
        )

    def _matches_waiver(self, item: str, waive_patterns: List[str]) -> bool:
        """
        Check if item matches any waiver pattern.
        
        TODO: Optional - Implement waiver matching logic
        
        Args:
            item: Item to check
            waive_patterns: List of waiver patterns
            
        Returns:
            True if item matches any pattern
        """
        for pattern in waive_patterns:
            # Support wildcards
            if '*' in pattern:
                regex_pattern = pattern.replace('*', '.*')
                if re.search(regex_pattern, item, re.IGNORECASE):
                    return True
            # Exact match
            elif pattern.lower() == item.lower():
                return True
        return False


# =========================================================================
# Entry Point
# =========================================================================

def main():
    """Main entry point."""
    checker = Check_11_0_0_19()
    checker.init_checker(Path(__file__))
    result = checker.execute_check()
    checker.write_output(result)
    return 0 if result.is_pass else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())