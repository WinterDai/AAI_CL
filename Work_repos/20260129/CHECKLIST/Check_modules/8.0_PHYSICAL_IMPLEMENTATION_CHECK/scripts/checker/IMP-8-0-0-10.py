################################################################################
# Script Name: IMP-8-0-0-10.py
#
# Purpose:
#   Confirm you placed the discrete synchronizer flops close to each other (distance <= 10um) for process without dedicated 2/3 stage synchronizer library cell like TSMC. Make sure "no buffering on the Q->D path between sync flops" for the sync_regs falling under same hierarchy. Please fine tune clock tree for hold fixing. Please don't change the VT of synchronizer flops. (Check the Note. Fill N/A for library has 2/3 stages dedicated library cell)
#
# Logic:
#   - Parse input file: IMP-8-0-0-10.rpt containing synchronizer placement groups
#   - Extract group headers (Group0:, Group1:, etc.) to identify synchronizer instances
#   - Parse pin entries with hierarchical paths and physical coordinates (x, y in microns)
#   - Match Q->D pin pairs within each group (e.g., hic_dnt_sync_reg0/Q -> hic_dnt_sync_reg1/D)
#   - Calculate Euclidean distance between consecutive synchronizer stages: sqrt((x2-x1)^2 + (y2-y1)^2)
#   - Detect buffering violations by identifying non-register cells (hic_dnt_mux, hic_dnt_buf, hic_dnt_inv) in synchronizer paths
#   - Flag violations when distance > 10um OR buffer/mux/inverter detected between sync stages
#   - Report compliant groups as INFO, violations as FAIL with specific distance/buffer details
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
# Refactored: 2025-12-24 (Using checker_templates v1.1.0)
#
# Author: yyin
# Date: 2025-12-18
################################################################################

from pathlib import Path
import re
import sys
import math
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
class Check_8_0_0_10(InputFileParserMixin, OutputBuilderMixin, WaiverHandlerMixin, BaseChecker):
    """
    IMP-8-0-0-10: Confirm you placed the discrete synchronizer flops close to each other (distance <= 10um) for process without dedicated 2/3 stage synchronizer library cell like TSMC. Make sure "no buffering on the Q->D path between sync flops" for the sync_regs falling under same hierarchy. Please fine tune clock tree for hold fixing. Please don't change the VT of synchronizer flops. (Check the Note. Fill N/A for library has 2/3 stages dedicated library cell)
    
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
    FOUND_DESC_TYPE1_4 = "Synchronizer groups with compliant placement (distance ≤ 10um, no buffering)"
    MISSING_DESC_TYPE1_4 = "Synchronizer groups with placement violations"
    FOUND_REASON_TYPE1_4 = "Synchronizer placement verified: distance within 10um threshold and no buffering on Q->D path"
    MISSING_REASON_TYPE1_4 = "Synchronizer placement violation detected: distance exceeds 10um or buffering present on Q->D path"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_DESC_TYPE2_3 = "Synchronizer groups matching placement requirements"
    MISSING_DESC_TYPE2_3 = "Synchronizer groups not satisfying placement constraints"
    FOUND_REASON_TYPE2_3 = "Synchronizer placement requirements satisfied: distance and buffering constraints met"
    MISSING_REASON_TYPE2_3 = "Synchronizer placement requirements not satisfied: constraint violations detected"
    
    # All Types (waiver description unified)
    WAIVED_DESC = "Waived synchronizer placement violations"
    
    # Waiver parameters (Type 3/4 ONLY)
    WAIVED_BASE_REASON = "Synchronizer placement violation waived per design approval"
    
    # Distance threshold in microns
    DISTANCE_THRESHOLD = 10.0
    
    def __init__(self):
        """Initialize the checker."""
        super().__init__(
            check_module="8.0_PHYSICAL_IMPLEMENTATION_CHECK",
            item_id="IMP-8-0-0-10",
            item_desc="Confirm you placed the discrete synchronizer flops close to each other (distance <= 10um) for process without dedicated 2/3 stage synchronizer library cell like TSMC. Make sure no buffering on the Q->D path between sync flops for the sync_regs falling under same hierarchy. Please fine tune clock tree for hold fixing. Please don't change the VT of synchronizer flops. (Check the Note. Fill N/A for library has 2/3 stages dedicated library cell)"
        )
        # Custom member variables for parsed data
        self._parsed_groups: List[Dict[str, Any]] = []
        self._compliant_groups: Dict[str, Dict] = {}
        self._violation_groups: Dict[str, Dict] = {}
    
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
        Parse input files to extract synchronizer placement data.
        
        Parses synchronizer placement reports organized by groups. Each group contains
        pin entries with hierarchical paths and physical coordinates (x, y) in microns.
        
        Returns:
            Dict with parsed data:
            - 'groups': List[Dict] - Synchronizer groups with placement analysis
            - 'compliant': Dict - Groups meeting placement requirements
            - 'violations': Dict - Groups with distance or buffering violations
            - 'metadata': Dict - Summary statistics
        """
        # 1. Validate inputs - IMPORTANT: returns tuple (valid_files_list, missing_files_list)
        valid_files, missing_files = self.validate_input_files()
        
        # FIXED: KNOWN_ISSUE_LOGIC-001 - Explicitly check for empty list
        if not valid_files or len(valid_files) == 0:
            raise ConfigurationError("No valid input files found")
        
        # 2. Parse synchronizer groups
        all_groups = []
        
        for file_path in valid_files:
            groups = self._parse_synchronizer_groups(file_path)
            all_groups.extend(groups)
        
        # 3. Analyze placement for each group
        # Build output format per README: "[hierarchy_path] Group N: Stage regX->regY distance=X.XXum (compliant)"
        compliant_groups = {}
        violation_groups = {}
        
        for group in all_groups:
            group_name = group['name']
            hierarchy_path = group.get('hierarchy_path', '')
            violations = group.get('violations', [])
            compliant_stages = group.get('compliant_stages', [])
            
            # Build display prefix: "[hierarchy_path] Group N"
            group_num = group_name.replace('Group', '')
            display_prefix = f"{hierarchy_path} {group_name}" if hierarchy_path else group_name
            
            if violations:
                # Has violations - format per README ERROR01
                # Format: "[hierarchy_path] Group N: VIOLATION - Distance=X.XXum (>10um threshold) | Stage: regX->regY"
                for violation in violations:
                    display_name = f"{display_prefix}: VIOLATION - {violation}"
                    violation_groups[display_name] = {
                        'name': display_name,
                        'line_number': group.get('line_number', 0),
                        'file_path': group.get('file_path', 'N/A'),
                        'violations': violation,
                        'group_name': group_name,
                        'hierarchy_path': hierarchy_path
                    }
            
            # Add compliant stages - format per README INFO01
            # Format: "[hierarchy_path] Group N: Stage regX->regY distance=X.XXum (compliant)"
            for stage_info in compliant_stages:
                display_name = f"{display_prefix}: {stage_info}"
                compliant_groups[display_name] = {
                    'name': display_name,
                    'line_number': group.get('line_number', 0),
                    'file_path': group.get('file_path', 'N/A'),
                    'max_distance': group.get('max_distance', 0.0),
                    'group_name': group_name,
                    'hierarchy_path': hierarchy_path
                }
        
        # 4. Store on self
        self._parsed_groups = all_groups
        self._compliant_groups = compliant_groups
        self._violation_groups = violation_groups
        
        # 5. Return aggregated dict
        return {
            'groups': all_groups,
            'compliant': compliant_groups,
            'violations': violation_groups,
            'metadata': {
                'total_groups': len(all_groups),
                'compliant_count': len(compliant_groups),
                'violation_count': len(violation_groups)
            }
        }
    
    def _parse_synchronizer_groups(self, file_path: Path) -> List[Dict[str, Any]]:
        """
        Parse synchronizer groups from placement report file.
        
        Args:
            file_path: Path to placement report file
            
        Returns:
            List of group dictionaries with placement analysis
        """
        groups = []
        current_group = None
        current_group_pins = []
        current_group_line = 0
        
        # Regex patterns
        pattern_group = re.compile(r'^Group(\d+):')
        pattern_pin = re.compile(r'PinName:\s+([^;]+)\s*;\s*cellPT:\s*\{([\d.]+)\s+([\d.]+)\}')
        pattern_sync_reg = re.compile(r'/(hic_dnt_sync_reg\d+)/([DQ])\s*;')
        pattern_buffer = re.compile(r'/(hic_dnt_(?:mux|buf|inv)[^/]*)/[A-Z]')
        
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line_num, line in enumerate(f, 1):
                # Check for group header
                group_match = pattern_group.match(line)
                if group_match:
                    # Process previous group if exists
                    if current_group is not None:
                        group_data = self._analyze_group_placement(
                            current_group, current_group_pins, current_group_line, str(file_path)
                        )
                        groups.append(group_data)
                    
                    # Start new group
                    current_group = f"Group{group_match.group(1)}"
                    current_group_pins = []
                    current_group_line = line_num
                    continue
                
                # Parse pin entries within current group
                if current_group is not None:
                    pin_match = pattern_pin.search(line)
                    if pin_match:
                        pin_path = pin_match.group(1)
                        x_coord = float(pin_match.group(2))
                        y_coord = float(pin_match.group(3))
                        
                        # Extract register and pin type if sync register
                        sync_match = pattern_sync_reg.search(line)
                        if sync_match:
                            reg_name = sync_match.group(1)
                            pin_type = sync_match.group(2)
                            
                            current_group_pins.append({
                                'pin_path': pin_path,
                                'reg_name': reg_name,
                                'pin_type': pin_type,
                                'x': x_coord,
                                'y': y_coord,
                                'line_number': line_num
                            })
                        
                        # Check for buffer/mux/inverter
                        buffer_match = pattern_buffer.search(line)
                        if buffer_match:
                            current_group_pins.append({
                                'pin_path': pin_path,
                                'is_buffer': True,
                                'buffer_cell': buffer_match.group(1),
                                'x': x_coord,
                                'y': y_coord,
                                'line_number': line_num
                            })
            
            # Process last group
            if current_group is not None:
                group_data = self._analyze_group_placement(
                    current_group, current_group_pins, current_group_line, str(file_path)
                )
                groups.append(group_data)
        
        return groups
    
    def _analyze_group_placement(self, group_name: str, pins: List[Dict], 
                                 line_number: int, file_path: str) -> Dict[str, Any]:
        """
        Analyze placement of synchronizer group.
        
        Args:
            group_name: Name of the group (e.g., "Group0")
            pins: List of pin dictionaries with coordinates
            line_number: Line number where group starts
            file_path: Source file path
            
        Returns:
            Dictionary with group analysis results
        """
        violations = []
        compliant_stages = []
        max_distance = 0.0
        hierarchy_path = ""
        
        # Separate sync registers and buffers
        sync_pins = [p for p in pins if not p.get('is_buffer', False)]
        buffer_pins = [p for p in pins if p.get('is_buffer', False)]
        
        # Extract hierarchy path from first sync pin
        if sync_pins:
            pin_path = sync_pins[0].get('pin_path', '')
            # Remove the register/pin part to get hierarchy
            # e.g., "inst_data_path_top/.../inst_hic_dff_out/hic_dnt_sync_reg0/Q" -> "inst_data_path_top/.../inst_hic_dff_out"
            parts = pin_path.strip().split('/')
            if len(parts) >= 2:
                # Find the last hic_dnt_sync_reg part and remove it
                for i in range(len(parts) - 1, -1, -1):
                    if 'hic_dnt_sync_reg' in parts[i]:
                        hierarchy_path = '/'.join(parts[:i])
                        break
                if not hierarchy_path:
                    hierarchy_path = '/'.join(parts[:-1])
        
        # Check for buffering violation
        if buffer_pins:
            for bp in buffer_pins:
                buffer_cell = bp['buffer_cell']
                # Format: "[hierarchy_path] Group N: VIOLATION - Buffering detected: cell_name on Q->D path"
                violations.append(f"Buffering detected: {buffer_cell} on Q->D path")
        
        # Group pins by register name
        reg_pins = {}
        for pin in sync_pins:
            reg_name = pin.get('reg_name')
            if reg_name:
                if reg_name not in reg_pins:
                    reg_pins[reg_name] = {}
                reg_pins[reg_name][pin['pin_type']] = pin
        
        # Extract register numbers and sort
        reg_numbers = []
        for reg_name in reg_pins.keys():
            match = re.search(r'sync_reg(\d+)', reg_name)
            if match:
                reg_numbers.append((int(match.group(1)), reg_name))
        reg_numbers.sort()
        
        # Check consecutive Q->D pairs
        for i in range(len(reg_numbers) - 1):
            curr_num, curr_reg = reg_numbers[i]
            next_num, next_reg = reg_numbers[i + 1]
            
            # Get Q pin of current register and D pin of next register
            q_pin = reg_pins.get(curr_reg, {}).get('Q')
            d_pin = reg_pins.get(next_reg, {}).get('D')
            
            if q_pin and d_pin:
                # Calculate Euclidean distance
                distance = math.sqrt(
                    (d_pin['x'] - q_pin['x'])**2 + 
                    (d_pin['y'] - q_pin['y'])**2
                )
                max_distance = max(max_distance, distance)
                
                # Stage info: reg0->reg1
                stage_info = f"Stage reg{curr_num}->reg{next_num}"
                
                # Check distance threshold
                if distance > self.DISTANCE_THRESHOLD:
                    # Format: "VIOLATION - Distance=X.XXum (>10um threshold) | Stage: regX->regY"
                    violations.append(f"Distance={distance:.2f}um (>{self.DISTANCE_THRESHOLD}um threshold) | {stage_info}")
                else:
                    # Format: "Stage regX->regY distance=X.XXum (compliant)"
                    compliant_stages.append(f"{stage_info} distance={distance:.2f}um (compliant)")
        
        return {
            'name': group_name,
            'hierarchy_path': hierarchy_path,
            'line_number': line_number,
            'file_path': file_path,
            'violations': violations,
            'compliant_stages': compliant_stages,
            'max_distance': max_distance,
            'pin_count': len(sync_pins),
            'buffer_count': len(buffer_pins)
        }
    
    # =========================================================================
    # Type 1: Boolean Check
    # =========================================================================
    
    def _execute_type1(self) -> CheckResult:
        """
        Type 1: Boolean Check.
        
        Custom boolean validation - check all synchronizer groups.
        Does NOT use pattern_items for searching.
        Output format per README: "[hierarchy_path] Group N: Stage regX->regY distance=X.XXum (compliant)"
        
        Use OutputBuilderMixin.build_complete_output() for automatic formatting.
        
        Returns:
            CheckResult with is_pass based on check logic
        """
        # Parse input - _parse_input_files already formats output per README
        data = self._parse_input_files()
        compliant = data.get('compliant', {})
        violations = data.get('violations', {})
        
        # Use template helper for automatic output formatting
        # Type 1: Use TYPE1_4 reason (emphasize "found/not found") - API-025
        return self.build_complete_output(
            found_items=compliant,
            missing_items=violations,
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
        Type 2: Value Check (status_check mode).
        
        Search pattern_items in synchronizer groups.
        This is a status_check mode - only output matched items.
        - found_items = patterns matched AND placement compliant (distance ≤10um, no buffering)
        - missing_items = patterns matched BUT has violations (distance >10um or buffering)
        
        Template auto-handles waiver=0 conversions.
        
        Returns:
            CheckResult with is_pass based on value comparison
        """
        # Parse input
        data = self._parse_input_files()
        compliant = data.get('compliant', {})
        violations = data.get('violations', {})
        
        # Get requirements
        pattern_items = self.item_data.get('requirements', {}).get('pattern_items', [])
        
        # status_check mode: Match patterns and check their status
        found_items = {}  # Patterns matched AND compliant
        missing_items = {}  # Patterns matched BUT has violations
        
        for pattern in pattern_items:
            matched = False
            
            # Check in compliant groups first
            for group_name, group_data in compliant.items():
                if pattern.lower() in group_name.lower():
                    # Pattern matched AND compliant → found_items
                    max_dist = group_data.get('max_distance', 0.0)
                    display_name = f"{group_name}: distance={max_dist:.2f}um (compliant)"
                    found_items[display_name] = {
                        'name': display_name,
                        'line_number': group_data.get('line_number', 0),
                        'file_path': group_data.get('file_path', 'N/A')
                    }
                    matched = True
                    break
            
            # Check in violation groups
            if not matched:
                for group_name, group_data in violations.items():
                    if pattern.lower() in group_name.lower():
                        # Pattern matched BUT has violations → missing_items
                        violation_details = group_data.get('violations', 'Violation detected')
                        display_name = f"{group_name}: VIOLATION - {violation_details}"
                        missing_items[display_name] = {
                            'name': display_name,
                            'line_number': group_data.get('line_number', 0),
                            'file_path': group_data.get('file_path', 'N/A')
                        }
                        matched = True
                        break
            
            # Pattern not found in any group - report as missing
            if not matched:
                missing_items[f"{pattern} (not found in report)"] = {
                    'name': f"{pattern} (not found in report)",
                    'line_number': 0,
                    'file_path': 'N/A'
                }
        
        # Use template helper (auto-handles waiver=0)
        # Type 2: Use TYPE2_3 reason (emphasize "matched/satisfied") - API-026
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
        compliant = parsed_data.get('compliant', {})
        violations = parsed_data.get('violations', {})
        
        # Get requirements
        pattern_items = self.item_data.get('requirements', {}).get('pattern_items', [])
        
        # FIXED: KNOWN_ISSUE_API-016 - Use waivers.get() directly to preserve dict format
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # status_check mode: Match patterns and check their status
        found_items = {}  # Patterns matched AND compliant
        waived_items = {}  # Patterns matched, has violations, BUT waived
        unwaived_items = {}  # Patterns matched, has violations, NOT waived
        used_waiver_patterns = set()
        
        for pattern in pattern_items:
            matched = False
            
            # Check in compliant groups first
            for group_name, group_data in compliant.items():
                if pattern.lower() in group_name.lower():
                    # Pattern matched AND compliant → found_items
                    max_dist = group_data.get('max_distance', 0.0)
                    display_name = f"{group_name}: distance={max_dist:.2f}um (compliant)"
                    found_items[display_name] = {
                        'name': display_name,
                        'line_number': group_data.get('line_number', 0),
                        'file_path': group_data.get('file_path', 'N/A')
                    }
                    matched = True
                    break
            
            # Check in violation groups
            if not matched:
                for group_name, group_data in violations.items():
                    if pattern.lower() in group_name.lower():
                        # Pattern matched BUT has violations
                        violation_details = group_data.get('violations', 'Violation detected')
                        display_name = f"{group_name}: VIOLATION - {violation_details}"
                        item_data = {
                            'name': display_name,
                            'line_number': group_data.get('line_number', 0),
                            'file_path': group_data.get('file_path', 'N/A')
                        }
                        
                        # Check if waived
                        matched_waiver = None
                        for waiver_pattern in waive_dict.keys():
                            if self.match_waiver_entry(group_name, {waiver_pattern: waive_dict[waiver_pattern]}):
                                matched_waiver = waiver_pattern
                                used_waiver_patterns.add(waiver_pattern)
                                break
                        
                        if matched_waiver:
                            waived_items[display_name] = item_data
                        else:
                            unwaived_items[display_name] = item_data
                        
                        matched = True
                        break
            
            # Pattern not found - report as missing (unwaived)
            if not matched:
                unwaived_items[f"{pattern} (not found in report)"] = {
                    'name': f"{pattern} (not found in report)",
                    'line_number': 0,
                    'file_path': 'N/A'
                }
        
        # Find unused waivers
        unused_waivers = {
            w: {
                'line_number': 0,
                'file_path': 'waiver_config',
                'reason': waive_dict[w]
            }
            for w in waive_dict.keys()
            if w not in used_waiver_patterns
        }
        
        # Type 3: Use TYPE2_3 reason (emphasize "matched/satisfied") - API-026
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
        Outputs all compliant groups as found_items, and handles violations with waiver logic.
        
        Use OutputBuilderMixin.build_complete_output() with has_waiver_value=True.
        
        Returns:
            CheckResult with waiver logic applied
        """
        # Parse input
        data = self._parse_input_files()
        compliant = data.get('compliant', {})
        violations = data.get('violations', {})
        
        # FIXED: KNOWN_ISSUE_API-016 - Use waivers.get() directly to preserve dict format
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # Build found_items from compliant groups
        found_items = {}
        for group_name, group_data in compliant.items():
            max_dist = group_data.get('max_distance', 0.0)
            display_name = f"{group_name}: distance={max_dist:.2f}um (compliant)"
            found_items[display_name] = {
                'name': display_name,
                'line_number': group_data.get('line_number', 0),
                'file_path': group_data.get('file_path', 'N/A')
            }
        
        # Separate waived/unwaived violations
        waived_items = {}
        unwaived_items = {}
        used_waiver_patterns = set()
        
        for group_name, group_data in violations.items():
            violation_details = group_data.get('violations', 'Violation detected')
            display_name = f"{group_name}: VIOLATION - {violation_details}"
            item_data = {
                'name': display_name,
                'line_number': group_data.get('line_number', 0),
                'file_path': group_data.get('file_path', 'N/A')
            }
            
            # Check if waived
            matched_waiver = None
            for waiver_pattern in waive_dict.keys():
                if self.match_waiver_entry(group_name, {waiver_pattern: waive_dict[waiver_pattern]}):
                    matched_waiver = waiver_pattern
                    used_waiver_patterns.add(waiver_pattern)
                    break
            
            if matched_waiver:
                waived_items[display_name] = item_data
            else:
                unwaived_items[display_name] = item_data
        
        # Find unused waivers
        unused_waivers = {
            w: {
                'line_number': 0,
                'file_path': 'waiver_config',
                'reason': waive_dict[w]
            }
            for w in waive_dict.keys()
            if w not in used_waiver_patterns
        }
        
        # Type 4: Use TYPE1_4 desc+reason + waiver params - API-026
        return self.build_complete_output(
            found_items=found_items,
            waived_items=waived_items,
            missing_items=unwaived_items,
            waive_dict=waive_dict,
            unused_waivers=unused_waivers,
            has_waiver_value=True,
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
    checker = Check_8_0_0_10()
    checker.init_checker(Path(__file__))
    result = checker.execute_check()
    checker.write_output(result)
    return 0 if result.is_pass else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())