################################################################################
# Script Name: IMP-11-0-0-20.py
#
# Purpose:
#   Confirm wake-up time meet customer's requirement. (For non-PSO, please fill N/A)
#
# Logic:
#   - Parse Powerup.rpt to extract measured wake-up time from summary section
#   - Extract power switch activation statistics to validate simulation completeness
#   - Extract simulation metadata (time, threshold voltage, rush current)
#   - Verify measured wake-up time against customer requirement threshold
#   - Support waiver for wake-up time violations
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
class Check_11_0_0_20(InputFileParserMixin, OutputBuilderMixin, WaiverHandlerMixin, BaseChecker):
    """
    IMP-11-0-0-20: Confirm wake-up time meet customer's requirement. (For non-PSO, please fill N/A)
    
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
    FOUND_DESC_TYPE1_4 = "Wake-up time validation completed - all power switches activated"
    MISSING_DESC_TYPE1_4 = "Wake-up time validation failed - required data not found in report"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_DESC_TYPE2_3 = "Wake-up time meets customer requirement"
    MISSING_DESC_TYPE2_3 = "Wake-up time exceeds customer requirement"
    
    # All Types (waiver description unified)
    WAIVED_DESC = "Wake-up time requirement waived"
    
    # ⭐ REASON CONSTANTS - Split by Type semantics (API-025)
    # ALL Types pass found_reason/missing_reason, but use different constants
    
    # Type 1/4: Boolean checks - emphasize "found/not found" (existence)
    FOUND_REASON_TYPE1_4 = "All power switches turned on and wake-up time found in simulation report"
    MISSING_REASON_TYPE1_4 = "Wake-up time value not found in Powerup.rpt or power switches not fully activated"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_REASON_TYPE2_3 = "Measured wake-up time satisfied customer requirement threshold"
    MISSING_REASON_TYPE2_3 = "Measured wake-up time exceeds customer requirement threshold"
    
    # Waiver-related (Type 3/4 only)
    WAIVED_BASE_REASON = "Wake-up time violation waived per design team approval"
    UNUSED_WAIVER_REASON = "Waiver not matched - no corresponding wake-up time violation found"
    
    def __init__(self):
        """Initialize the checker."""
        super().__init__(
            check_module="11.0_POWER_EMIR_CHECK",
            item_id="IMP-11-0-0-20",
            item_desc="Confirm wake-up time meet customer's requirement. (For non-PSO, please fill N/A)"
        )
        # Custom member variables for parsed data
        self._parsed_items: List[Dict[str, Any]] = []
        self._metadata: Dict[str, str] = {}
        self._wake_up_time: Optional[float] = None
        self._switches_turned_on: Optional[int] = None
        self._total_switches: Optional[int] = None
        self._simulation_time: Optional[float] = None
        self._threshold_voltage: Optional[float] = None
        self._rush_current: Optional[float] = None
        self._last_switch_info: Dict[str, Any] = {}
    
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
        Parse Powerup.rpt to extract wake-up time and power switch statistics.
        
        Extracts:
        - Measured wake-up time from summary section
        - Power switch activation statistics (turned on vs total)
        - Simulation metadata (time, threshold voltage)
        - Maximum rush current
        - Last power switch turn-on information
        
        Returns:
            Dict with parsed data:
            - 'items': List[Dict] - Wake-up time measurement with metadata
            - 'metadata': Dict - Simulation metadata (time, threshold, rush current)
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
        wake_up_time = None
        wakeup_line_num = 0
        switches_turned_on = None
        total_switches = None
        simulation_time = None
        threshold_voltage = None
        rush_current = None
        last_switch_instance = None
        last_turn_on_time = None
        
        # Line number tracking for all metrics
        wakeup_line_num = 0
        switches_line_num = 0
        rush_current_line_num = 0
        
        # 3. Parse each input file for wake-up time information
        for file_path in valid_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    in_summary_section = False
                    
                    for line_num, line in enumerate(f, 1):
                        # Detect summary section
                        if 'Summary' in line and not in_summary_section:
                            in_summary_section = True
                            continue
                        
                        if 'Detailed Report' in line:
                            in_summary_section = False
                            continue
                        
                        # Only parse summary section
                        if not in_summary_section:
                            continue
                        
                        # Pattern 1: Extract measured wake-up time
                        match_wake_up = re.search(r'Measured wake-up time for switched net\s*=\s*([0-9.eE+-]+)s', line)
                        if match_wake_up:
                            wake_up_time = float(match_wake_up.group(1))
                            wakeup_line_num = line_num  # Save line number for metadata
                            items.append({
                                'name': f'wake_up_time_{wake_up_time}s',
                                'value': wake_up_time,
                                'line_number': line_num,
                                'file_path': str(file_path),
                                'type': 'wake_up_time'
                            })
                            continue
                        
                        # Pattern 2: Extract power switch activation statistics
                        match_switches = re.search(r'Number of power switches turned on in this simulation\s*=\s*(\d+)\s*\[of total\s*(\d+)\]', line)
                        if match_switches:
                            switches_turned_on = int(match_switches.group(1))
                            total_switches = int(match_switches.group(2))
                            switches_line_num = line_num  # Save line number
                            continue
                        
                        # Pattern 3: Extract simulation time
                        match_sim_time = re.search(r'Simulation time\s*=\s*([0-9.eE+-]+)s', line)
                        if match_sim_time:
                            simulation_time = float(match_sim_time.group(1))
                            continue
                        
                        # Pattern 3: Extract threshold voltage
                        match_threshold = re.search(r'Threshold \(Vt\)\s*=\s*([0-9.]+)V', line)
                        if match_threshold:
                            threshold_voltage = float(match_threshold.group(1))
                            continue
                        
                        # Pattern 4: Extract maximum rush current
                        match_rush = re.search(r'Measured maximum rush current\s*=\s*([0-9.eE+-]+)A', line)
                        if match_rush:
                            rush_current = float(match_rush.group(1))
                            rush_current_line_num = line_num  # Save line number
                            continue
                        
                        # Pattern 5: Extract last power switch turn-on information
                        match_last_switch = re.search(r"Last power switch to turn-on in this simulation is '([^']+)' at time ([0-9.eE+-]+)s", line)
                        if match_last_switch:
                            last_switch_instance = match_last_switch.group(1)
                            last_turn_on_time = float(match_last_switch.group(2))
                            continue
                
                # Validate critical data was found
                if wake_up_time is None:
                    errors.append(f"Wake-up time not found in {file_path}")
                
                if switches_turned_on is None or total_switches is None:
                    errors.append(f"Power switch statistics not found in {file_path}")
                elif switches_turned_on != total_switches:
                    errors.append(f"Not all power switches activated: {switches_turned_on}/{total_switches}")
                
                # Store metadata with all line numbers
                metadata = {
                    'simulation_time': simulation_time,
                    'threshold_voltage': threshold_voltage,
                    'rush_current': rush_current,
                    'switches_turned_on': switches_turned_on,
                    'total_switches': total_switches,
                    'last_switch_instance': last_switch_instance,
                    'last_turn_on_time': last_turn_on_time,
                    'wakeup_time': wake_up_time,
                    'wakeup_line_num': wakeup_line_num,
                    'switches_line_num': switches_line_num,
                    'rush_current_line_num': rush_current_line_num,
                    'file_path': str(file_path)
                }
                
            except Exception as e:
                errors.append(f"Error parsing {file_path}: {str(e)}")
        
        # 4. Store frequently reused data on self
        self._parsed_items = items
        self._metadata = metadata
        self._wake_up_time = wake_up_time
        self._switches_turned_on = switches_turned_on
        self._total_switches = total_switches
        self._simulation_time = simulation_time
        self._threshold_voltage = threshold_voltage
        self._rush_current = rush_current
        self._last_switch_info = {
            'instance': last_switch_instance,
            'turn_on_time': last_turn_on_time
        }
        
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

        Validates:
        1. Powerup.rpt file exists and is readable
        2. All power switches are activated (turned_on == total)
        3. Wake-up time value is present in the report

        Returns PASS if all validations succeed, FAIL otherwise.
        """
        violations = self._type1_core_logic()

        # Build found_items from successful validations
        data = self._parse_input_files()
        metadata = data.get('metadata', {})

        found_items = {}
        if not violations:
            # All checks passed - create separate found_items for each metric
            wakeup_time = metadata.get('wakeup_time', 'N/A')
            switches_on = metadata.get('switches_turned_on', 0)
            switches_total = metadata.get('total_switches', 0)
            rush_current = metadata.get('rush_current', 'N/A')
            file_path = metadata.get('file_path', 'N/A')
            
            # Line numbers for each metric
            wakeup_line = metadata.get('wakeup_line_num', 0)
            switches_line = metadata.get('switches_line_num', 0)
            rush_line = metadata.get('rush_current_line_num', 0)

            # Use numeric prefixes to control sort order (1_, 2_, 3_)
            found_items[f"1_Wake-up time: {wakeup_time}s"] = {
                'line_number': wakeup_line,
                'file_path': file_path
            }
            found_items[f"2_Power switches: {switches_on}/{switches_total} activated"] = {
                'line_number': switches_line,
                'file_path': file_path
            }
            found_items[f"3_Rush current: {rush_current}A"] = {
                'line_number': rush_line,
                'file_path': file_path
            }

        missing_items = violations
        
        # name_extractor: strip numeric prefix (1_, 2_, 3_) for clean display
        def name_extractor(item_name: str, metadata: dict) -> str:
            if item_name and len(item_name) > 2 and item_name[0].isdigit() and item_name[1] == '_':
                return item_name[2:]  # Remove "N_" prefix
            return item_name

        return self.build_complete_output(
            found_items=found_items,
            missing_items=missing_items,
            found_desc=self.FOUND_DESC_TYPE1_4,
            missing_desc=self.MISSING_DESC_TYPE1_4,
            found_reason=self.FOUND_REASON_TYPE1_4,
            missing_reason=self.MISSING_REASON_TYPE1_4,
            name_extractor=name_extractor
        )

    def _type1_core_logic(self) -> dict[str, dict]:
        """
        Core Type 1 boolean check logic (shared by Type 1 and Type 4).

        Performs validation checks:
        1. File parsing errors
        2. Power switch activation completeness
        3. Wake-up time measurement presence

        Returns:
            Dict of violations: {item_name: {'line_number': ..., 'file_path': ..., 'reason': ...}}
            Empty dict if all checks pass.
        """
        data = self._parse_input_files()
        errors = data.get('errors', [])
        metadata = data.get('metadata', {})

        violations = {}

        # Check 1: File parsing errors
        if errors:
            for idx, error in enumerate(errors):
                error_key = f"parse_error_{idx}"
                violations[error_key] = {
                    'line_number': 0,
                    'file_path': metadata.get('file_path', 'N/A'),
                    'reason': error
                }

        # Check 2: Power switch activation completeness
        switches_on = metadata.get('switches_turned_on', 0)
        switches_total = metadata.get('total_switches', 0)

        if switches_total > 0 and switches_on < switches_total:
            viol_key = f"incomplete_activation_{switches_on}_{switches_total}"
            violations[viol_key] = {
                'line_number': metadata.get('switches_line_number', 0),
                'file_path': metadata.get('file_path', 'N/A'),
                'reason': f"Power switch activation incomplete: {switches_on}/{switches_total} switches turned on"
            }

        # Check 3: Wake-up time measurement presence
        wakeup_time = metadata.get('wakeup_time', None)
        if wakeup_time is None or wakeup_time == 'N/A':
            viol_key = "missing_wakeup_time"
            violations[viol_key] = {
                'line_number': metadata.get('line_number', 0),
                'file_path': metadata.get('file_path', 'N/A'),
                'reason': "Wake-up time measurement missing from Summary section"
            }

        return violations

    # =========================================================================
    # Type 4: Boolean Check with Waiver Logic
    # =========================================================================

    def _execute_type4(self) -> CheckResult:
        """
        Type 4: Boolean check with waiver support (reuses Type 1 core logic).

        Performs same validations as Type 1, but allows violations to be waived:
        - Waived violations → INFO with [WAIVER] tag
        - Unwaived violations → ERROR (FAIL)
        - Unused waivers → WARN with [WAIVER] tag

        Returns PASS if all violations are waived.
        """
        # Step 1: Get violations using Type 1's core logic
        violations = self._type1_core_logic()

        # Build found_items from successful validations
        data = self._parse_input_files()
        metadata = data.get('metadata', {})

        found_items = {}
        if not violations:
            # All checks passed - create separate found_items for each metric
            wakeup_time = metadata.get('wakeup_time', 'N/A')
            switches_on = metadata.get('switches_turned_on', 0)
            switches_total = metadata.get('total_switches', 0)
            rush_current = metadata.get('rush_current', 'N/A')
            file_path = metadata.get('file_path', 'N/A')
            
            # Line numbers for each metric
            wakeup_line = metadata.get('wakeup_line_num', 0)
            switches_line = metadata.get('switches_line_num', 0)
            rush_line = metadata.get('rush_current_line_num', 0)

            # Use numeric prefixes to control sort order (1_, 2_, 3_)
            found_items[f"1_Wake-up time: {wakeup_time}s"] = {
                'line_number': wakeup_line,
                'file_path': file_path
            }
            found_items[f"2_Power switches: {switches_on}/{switches_total} activated"] = {
                'line_number': switches_line,
                'file_path': file_path
            }
            found_items[f"3_Rush current: {rush_current}A"] = {
                'line_number': rush_line,
                'file_path': file_path
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
        
        # name_extractor: strip numeric prefix (1_, 2_, 3_) for clean display
        def name_extractor(item_name: str, metadata: dict) -> str:
            if item_name and len(item_name) > 2 and item_name[0].isdigit() and item_name[1] == '_':
                return item_name[2:]  # Remove "N_" prefix
            return item_name

        # Step 5: Build output (FIXED: API-009)
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
            waived_base_reason="",
            unused_waiver_reason=self.UNUSED_WAIVER_REASON,
            name_extractor=name_extractor
        )

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

        # Extract measured wake-up time from parsed data
        measured_time = None
        measured_item = None

        for item in items:
            if item.get('type') == 'wake_up_time':
                measured_time = item.get('value')
                measured_item = item
                break

        if measured_time is None:
            # No wake-up time found in report
            missing_items['wake_up_time'] = {
                'line_number': 0,
                'file_path': 'N/A',
                'reason': 'Wake-up time not found in Powerup.rpt'
            }
            return found_items, missing_items

        # Compare measured time against customer requirement threshold
        if not pattern_items:
            missing_items['requirement_threshold'] = {
                'line_number': 0,
                'file_path': 'N/A',
                'reason': 'No customer requirement threshold defined in pattern_items'
            }
            return found_items, missing_items

        # Get customer requirement threshold (first pattern_item)
        requirement_threshold_str = pattern_items[0]
        try:
            requirement_threshold = float(requirement_threshold_str)
        except ValueError:
            missing_items['requirement_threshold'] = {
                'line_number': 0,
                'file_path': 'N/A',
                'reason': f'Invalid requirement threshold format: {requirement_threshold_str}'
            }
            return found_items, missing_items

        # Compare measured time vs requirement
        if measured_time <= requirement_threshold:
            # PASS: Wake-up time meets requirement
            item_name = f"Wake-up time: {measured_time:.2e}s (Requirement: {requirement_threshold:.2e}s)"
            found_items[item_name] = {
                'line_number': measured_item.get('line_number', 0),
                'file_path': measured_item.get('file_path', 'N/A')
            }
        else:
            # FAIL: Wake-up time exceeds requirement
            excess_time = measured_time - requirement_threshold
            item_name = f"Wake-up time: {measured_time:.2e}s exceeds requirement {requirement_threshold:.2e}s by {excess_time:.2e}s"
            missing_items[item_name] = {
                'line_number': measured_item.get('line_number', 0),
                'file_path': measured_item.get('file_path', 'N/A'),
                'reason': f'Measured wake-up time {measured_time:.2e}s exceeds customer requirement {requirement_threshold:.2e}s'
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
        
        # Extended waive_dict: maps both threshold and violation name to reason
        extended_waive_dict = waive_dict.copy()

        # Process found_items_base (no waiver needed - already passing)
        for item_name, item_data in found_items_base.items():
            found_items[item_name] = item_data

        # Process violations with waiver matching using threshold comparison
        for viol_name, viol_data in violations.items():
            # Extract measured wake-up time from violation name
            # Format: "Wake-up time: 1.5e-07s exceeds requirement ..."
            time_match = re.search(r'Wake-up time:\s*([0-9.eE+-]+)s', viol_name)
            if time_match:
                measured_time = float(time_match.group(1))
                
                # Check against all waiver thresholds
                matched_waiver = None
                for waiver_name, waiver_reason in waive_dict.items():
                    try:
                        waiver_threshold = float(waiver_name)
                        # Waive if measured_time <= waiver_threshold
                        if measured_time <= waiver_threshold:
                            matched_waiver = waiver_name
                            break
                    except ValueError:
                        # If waiver_name is not a valid number, skip
                        continue
                
                if matched_waiver:
                    # Add viol_name -> waiver_reason mapping to extended_waive_dict
                    waiver_reason = waive_dict.get(matched_waiver, '')
                    extended_waive_dict[viol_name] = waiver_reason
                    waived_items[viol_name] = viol_data
                    used_waivers.add(matched_waiver)
                else:
                    missing_items[viol_name] = viol_data
            else:
                # Cannot extract time, use default matching
                matched_waiver = self.match_waiver_entry(viol_name, waive_dict)
                if matched_waiver:
                    # Add viol_name -> waiver_reason mapping to extended_waive_dict
                    waiver_reason = waive_dict.get(matched_waiver, '')
                    extended_waive_dict[viol_name] = waiver_reason
                    waived_items[viol_name] = viol_data
                    used_waivers.add(matched_waiver)
                else:
                    missing_items[viol_name] = viol_data

        # Step 4: Find unused waivers
        unused_waivers = [w for w in waive_dict.keys() if w not in used_waivers]

        # Step 5: Build output (FIXED: API-009)
        return self.build_complete_output(
            found_items=found_items,
            missing_items=missing_items,
            waived_items=waived_items,
            unused_waivers=unused_waivers,
            waive_dict=extended_waive_dict,  # Use extended dict with viol_name mappings
            found_desc=self.FOUND_DESC_TYPE2_3,
            missing_desc=self.MISSING_DESC_TYPE2_3,
            waived_desc=self.WAIVED_DESC,
            found_reason=self.FOUND_REASON_TYPE2_3,
            missing_reason=self.MISSING_REASON_TYPE2_3,
            waived_base_reason="",
            unused_waiver_reason=self.UNUSED_WAIVER_REASON
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
    checker = Check_11_0_0_20()
    checker.init_checker(Path(__file__))
    result = checker.execute_check()
    checker.write_output(result)
    return 0 if result.is_pass else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())