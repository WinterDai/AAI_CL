################################################################################
# Script Name: IMP-8-0-0-01.py
#
# Purpose:
#   Confirm all ports are assigned on metal track.
#
# Logic:
#   - Parse input files: IMP-8-0-0-01_case*.rpt (Cadence Innovus checkPinAssignment reports)
#   - Extract header metadata (design name, tool version) from report header
#   - Locate "Start Checking pins" section marker to confirm report section
#   - Parse each **ERROR line to extract pin violation details (pin name, partition, net, status, coordinates, layer, violation type)
#   - Store violations with line_number and file_path for traceability
#   - Classify violations by type: NOT ON ROUTING TRACK (critical), OVERLAPPED WITH ROUTE BLOCKAGE (acceptable), Unplaced Pins (critical)
#   - Aggregate statistics: total violations, violations by type, violations by layer
#   - For Type 2/3: Match violations against pattern_items (status_check mode)
#   - For Type 3/4: Apply waiver logic to classify violations as waived/unwaived
#   - Generate output with source file/line tracing for each violation
#
# Auto Type Detection:
#   Type 1: requirements.value=N/A, waivers.value=N/A/0 → Boolean check
#   Type 2: requirements.value>0, pattern_items exists, waivers.value=N/A/0 → Value comparison
#   Type 3: requirements.value>0, pattern_items exists, waivers.value>0 → Value with waiver logic
#   Type 4: requirements.value=N/A, waivers.value>0 → Boolean with waiver logic
#
# Output Behavior (Type 2/3 - Check README "Output Behavior" section!):
#   status_check: pattern_items = items to CHECK STATUS (only output matched items)
#     - found_items = patterns matched AND status correct (on track)
#     - missing_items = patterns matched BUT status wrong (off track/unplaced)
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
# Author: chyao
# Date: 2026-01-09
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
class Check_8_0_0_01(InputFileParserMixin, OutputBuilderMixin, WaiverHandlerMixin, BaseChecker):
    """
    IMP-8-0-0-01: Confirm all ports are assigned on metal track.
    
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
    # Type 1/4: Boolean checks - COPY EXACT VALUES FROM README!
    FOUND_DESC_TYPE1_4 = "All ports found on metal routing tracks"
    MISSING_DESC_TYPE1_4 = "Ports not found on metal routing tracks"
    FOUND_REASON_TYPE1_4 = "All ports found on metal routing tracks with no placement violations"
    MISSING_REASON_TYPE1_4 = "Ports not found on metal routing tracks - placement verification failed"
    
    # Type 2/3: Pattern checks - COPY EXACT VALUES FROM README!
    FOUND_DESC_TYPE2_3 = "All ports correctly placed on metal routing tracks"
    MISSING_DESC_TYPE2_3 = "Port placement violations detected"
    FOUND_REASON_TYPE2_3 = "Port placement validated: all ports matched routing track requirements"
    MISSING_REASON_TYPE2_3 = "Port placement requirements not satisfied - routing track violations detected"
    
    # All Types (waiver description) - COPY EXACT VALUES FROM README!
    WAIVED_DESC = "Waived port placement violations"
    
    # Waiver parameters (Type 3/4 ONLY) - COPY EXACT VALUES FROM README!
    WAIVED_BASE_REASON = "Port placement violation waived per design review"
    
    def __init__(self):
        """Initialize the checker."""
        super().__init__(
            check_module="8.0_PHYSICAL_IMPLEMENTATION_CHECK",
            item_id="IMP-8-0-0-01",
            item_desc="Confirm all ports are assigned on metal track."
        )
        # Custom member variables for parsed data
        self._parsed_items: List[Dict[str, Any]] = []
        self._metadata: Dict[str, Any] = {}
    
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
        Parse input files to extract pin placement violations.
        
        Parses Cadence Innovus checkPinAssignment report to extract:
        - Pin violations (NOT ON ROUTING TRACK, OVERLAPPED WITH ROUTE BLOCKAGE)
        - Pin metadata (name, partition, net, status, coordinates, layer)
        - Design metadata (design name, tool version)
        
        Returns:
            Dict with parsed data:
            - 'items': List[Dict] - Pin violations with metadata (line_number, file_path)
            - 'metadata': Dict - Design metadata (design_name, tool_version, total_violations)
            - 'errors': List - Any parsing errors encountered
        """
        # 1. Validate input files - IMPORTANT: returns tuple (valid_files_list, missing_files_list)
        valid_files, missing_files = self.validate_input_files()
        if not valid_files or len(valid_files) == 0:
            raise ConfigurationError("No valid input files found")
        
        # 2. Parse using patterns from file analysis
        all_items = []
        metadata = {
            'design_name': '',
            'tool_version': '',
            'total_violations': 0,
            'violations_by_type': {},
            'violations_by_layer': {}
        }
        errors = []
        
        # Regex patterns for parsing
        # Pattern 1: Main error line with pin violation details
        pattern_error = re.compile(
            r'\*\*ERROR:\s*\(([A-Z]+-\d+)\):\s+'
            r'Pin\s+\[([^\]]+)\]\s+of\s+partition\s+\[([^\]]+)\]\s+'
            r'connected\s+to\s+net\s+\[([^\]]+)\]\s+is\s+\[([A-Z]+)\]\s+'
            r'at\s+location\s+\(\s*([\d.]+),\s*([\d.]+)\)\s+'
            r'on\s+layer\s+(\w+)\s+is\s+(.+?)\.'
        )
        
        # Pattern 2: Design name from header
        pattern_design = re.compile(r'Start Checking pins of top cell:\s+\[([^\]]+)\]')
        
        # Pattern 3: Tool version
        pattern_tool = re.compile(r'#\s+Generated by:\s+(.+)')
        
        # Pattern 4: Unplaced pins section start
        pattern_unplaced_section = re.compile(r'^Unplaced Pins:\s*$')
        
        # Pattern 5: Individual unplaced pin names
        pattern_unplaced_pin = re.compile(r'^\s+-\s+([\w\[\]]+)\s*$')
        
        for file_path in valid_files:
            try:
                in_unplaced_section = False
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line_num, line in enumerate(f, 1):
                        # Extract design name
                        match_design = pattern_design.search(line)
                        if match_design:
                            metadata['design_name'] = match_design.group(1)
                        
                        # Extract tool version
                        match_tool = pattern_tool.search(line)
                        if match_tool:
                            metadata['tool_version'] = match_tool.group(1).strip()
                        
                        # Check for unplaced pins section start
                        if pattern_unplaced_section.search(line):
                            in_unplaced_section = True
                            continue
                        
                        # Extract individual unplaced pin names
                        if in_unplaced_section:
                            match_unplaced = pattern_unplaced_pin.search(line)
                            if match_unplaced:
                                pin_name = match_unplaced.group(1)
                                item_name = f"{pin_name}"
                                
                                all_items.append({
                                    'name': item_name,
                                    'pin_name': pin_name,
                                    'partition': 'N/A',
                                    'net': 'N/A',
                                    'status': 'UNPLACED',
                                    'x_coord': 'N/A',
                                    'y_coord': 'N/A',
                                    'layer': 'N/A',
                                    'violation_type': 'UNPLACED',
                                    'error_code': 'N/A',
                                    'line_number': line_num,
                                    'file_path': str(file_path)
                                })
                                
                                # Update statistics
                                metadata['violations_by_type']['UNPLACED'] = \
                                    metadata['violations_by_type'].get('UNPLACED', 0) + 1
                            elif line.strip() == '':
                                # Blank line ends unplaced section
                                in_unplaced_section = False
                        
                        # Extract pin violation details (ERROR lines)
                        match_error = pattern_error.search(line)
                        if match_error:
                            error_code = match_error.group(1)
                            pin_name = match_error.group(2)
                            partition = match_error.group(3)
                            net = match_error.group(4)
                            status = match_error.group(5)
                            x_coord = match_error.group(6)
                            y_coord = match_error.group(7)
                            layer = match_error.group(8)
                            violation_type = match_error.group(9).strip()
                            
                            # Create item name for display
                            item_name = f"{pin_name}"
                            
                            item = {
                                'name': item_name,
                                'pin_name': pin_name,
                                'partition': partition,
                                'net': net,
                                'status': status,
                                'x_coord': x_coord,
                                'y_coord': y_coord,
                                'layer': layer,
                                'violation_type': violation_type,
                                'error_code': error_code,
                                'line_number': line_num,
                                'file_path': str(file_path)
                            }
                            
                            all_items.append(item)
                            
                            # Update statistics
                            metadata['violations_by_type'][violation_type] = \
                                metadata['violations_by_type'].get(violation_type, 0) + 1
                            metadata['violations_by_layer'][layer] = \
                                metadata['violations_by_layer'].get(layer, 0) + 1
            
            except Exception as e:
                errors.append(f"Error parsing {file_path}: {str(e)}")
        
        # Update total violations count
        metadata['total_violations'] = len(all_items)
        
        # 3. Store frequently reused data on self
        self._parsed_items = all_items
        self._metadata = metadata
        
        # 4. Return aggregated dict with items containing line_number and file_path
        return {
            'items': all_items,
            'metadata': metadata,
            'errors': errors
        }
    
    # =========================================================================
    # Type 1: Boolean Check
    # =========================================================================
    
    def _execute_type1(self) -> CheckResult:
        """
        Type 1: Boolean Check.
        
        Check if any pin placement violations exist in the design.
        PASS: No violations found (all ports on metal tracks)
        FAIL: Violations detected
        
        Returns:
            CheckResult with is_pass based on check logic
        """
        # Parse input
        data = self._parse_input_files()
        items = data.get('items', [])
        
        # Filter out acceptable violations (OVERLAPPED WITH ROUTE BLOCKAGE)
        critical_violations = [
            item for item in items 
            if item['violation_type'] != 'OVERLAPPED WITH ROUTE BLOCKAGE'
        ]
        
        # Convert list to dict with metadata for source file/line display
        # Output format: "Info: <name>. In line <N>, <filepath>: <reason>"
        found_items = {}
        missing_items = []
        
        if critical_violations:
            # Critical violations found - FAIL
            for item in critical_violations:
                item_name = item['name']
                missing_items.append(item_name)
        else:
            # No critical violations - PASS
            found_items = {
                'All ports verified': {
                    'name': 'All ports verified',
                    'line_number': 0,
                    'file_path': 'N/A'
                }
            }
        
        # Use template helper
        # Type 1: Use TYPE1_4 reason (emphasize "found/not found") - API-025
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
        
        status_check mode: Check placement status of specific ports listed in pattern_items.
        Only output items that match pattern_items.
        
        found_items = patterns matched AND status correct (on track)
        missing_items = patterns matched BUT status wrong (off track/unplaced)
        
        Returns:
            CheckResult with is_pass based on value comparison
        """
        # Parse input
        data = self._parse_input_files()
        all_violations = {item['pin_name']: item for item in data.get('items', [])}
        
        # Get requirements
        pattern_items = self.item_data.get('requirements', {}).get('pattern_items', [])
        
        # status_check mode: Check status of items matching pattern_items
        found_items = {}      # Matched AND status correct (no violation)
        missing_items = []    # Matched BUT status wrong (has violation)
        
        for pattern in pattern_items:
            matched = False
            
            # Check if pattern matches any violation
            for pin_name, violation_data in all_violations.items():
                if pattern.lower() in pin_name.lower() or pattern == pin_name:
                    # Pattern matched - this pin has a violation (status wrong)
                    # Filter out acceptable violations
                    if violation_data['violation_type'] != 'OVERLAPPED WITH ROUTE BLOCKAGE':
                        item_name = violation_data['name']
                        missing_items.append(item_name)
                        matched = True
                        break
            
            # If pattern not found in violations, it means the pin is correctly placed
            if not matched:
                found_items[pattern] = {
                    'name': pattern,
                    'line_number': 0,
                    'file_path': 'N/A'
                }
        
        # Use template helper (auto-handles waiver=0)
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
        
        Same status_check logic as Type 2, plus waiver classification.
        
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
        all_violations = {item['pin_name']: item for item in parsed_data.get('items', [])}
        
        # Parse waiver configuration using template helper
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # Get requirements
        pattern_items = self.item_data.get('requirements', {}).get('pattern_items', [])
        
        # status_check mode with waiver logic
        found_items = {}      # Matched AND status correct (no violation)
        waived_items = {}     # Matched, status wrong, but waived
        unwaived_items = []   # Matched, status wrong, not waived
        
        for pattern in pattern_items:
            matched = False
            
            # Check if pattern matches any violation
            for pin_name, violation_data in all_violations.items():
                if pattern.lower() in pin_name.lower() or pattern == pin_name:
                    # Pattern matched - this pin has a violation
                    # Filter out acceptable violations
                    if violation_data['violation_type'] != 'OVERLAPPED WITH ROUTE BLOCKAGE':
                        matched = True
                        
                        # Check if violation is waived
                        if self.match_waiver_entry(pin_name, waive_dict):
                            waived_items[pin_name] = {
                                'name': violation_data['name'],
                                'line_number': violation_data.get('line_number', 0),
                                'file_path': violation_data.get('file_path', 'N/A'),
                                'reason': f"{violation_data['violation_type']}"
                            }
                        else:
                            unwaived_items.append(violation_data['name'])
                        break
            
            # If pattern not found in violations, it means the pin is correctly placed
            if not matched:
                found_items[pattern] = {
                    'name': pattern,
                    'line_number': 0,
                    'file_path': 'N/A'
                }
        
        # Find unused waivers
        used_names = set(waived_items.keys())
        unused_waivers = [name for name in waive_dict.keys() if name not in used_names]
        
        # Use template helper for automatic output formatting
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
        
        Use OutputBuilderMixin.build_complete_output() with has_waiver_value=True.
        
        Returns:
            CheckResult with waiver logic applied
        """
        # Parse input
        data = self._parse_input_files()
        items = data.get('items', [])
        
        # Filter out acceptable violations (OVERLAPPED WITH ROUTE BLOCKAGE)
        critical_violations = [
            item for item in items 
            if item['violation_type'] != 'OVERLAPPED WITH ROUTE BLOCKAGE'
        ]
        
        # Parse waiver configuration
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # Classify violations into waived/unwaived
        found_items = {}
        waived_items = {}
        unwaived_items = []
        
        if critical_violations:
            # Violations found - classify by waiver status
            for item in critical_violations:
                pin_name = item['pin_name']
                item_name = item['name']
                
                # Check if violation is waived
                if self.match_waiver_entry(pin_name, waive_dict):
                    waived_items[pin_name] = {
                        'name': item_name,
                        'line_number': item.get('line_number', 0),
                        'file_path': item.get('file_path', 'N/A'),
                        'reason': f"{item['violation_type']}"
                    }
                else:
                    unwaived_items.append(item_name)
        else:
            # No violations - PASS
            found_items = {
                'All ports verified': {
                    'name': 'All ports verified',
                    'line_number': 0,
                    'file_path': 'N/A'
                }
            }
        
        # Find unused waivers
        used_names = set(waived_items.keys())
        unused_waivers = [name for name in waive_dict.keys() if name not in used_names]
        
        # Use template helper (auto-handles waiver=0)
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
    checker = Check_8_0_0_01()
    checker.init_checker(Path(__file__))
    result = checker.execute_check()
    checker.write_output(result)
    return 0 if result.is_pass else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())