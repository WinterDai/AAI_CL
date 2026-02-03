################################################################################
# Script Name: IMP-8-0-0-04.py
#
# Purpose:
#   Confirm buffers are attached for all ports and are set as fixed.
#
# Logic:
#   - Parse input files: IMP-8-0-0-04.rpt
#   - Extract port entries with regex patterns for single/multiple buffer connections
#   - Parse port name (handle bus notation with braces), direction, connected cell names, placement statuses
#   - For each port, verify buffer existence (cell_name not empty) and placement status (all cells must be "fixed")
#   - Handle multiple buffers for bidi ports by splitting space-separated cell names and statuses
#   - Classify results: PASS if buffer exists AND all buffers fixed, FAIL if missing buffer OR any buffer not fixed
#   - Generate summary statistics: total ports, ports with buffers, ports with fixed buffers, breakdown by direction
#
# Auto Type Detection:
#   Type 1: requirements.value=N/A, waivers.value=N/A/0 → Boolean check
#   Type 2: requirements.value>0, pattern_items exists, waivers.value=N/A/0 → Value comparison
#   Type 3: requirements.value>0, pattern_items exists, waivers.value>0 → Value with waiver logic
#   Type 4: requirements.value=N/A, waivers.value>0 → Boolean with waiver logic
#
# Output Behavior (Type 2/3 - Check README "Output Behavior" section!):
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
# Author: chyao
# Date: 2026-01-14
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
class Check_8_0_0_04(InputFileParserMixin, OutputBuilderMixin, WaiverHandlerMixin, BaseChecker):
    """
    IMP-8-0-0-04: Confirm buffers are attached for all ports and are set as fixed.
    
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
    FOUND_DESC_TYPE1_4 = "All ports have approved buffers attached and fixed"
    MISSING_DESC_TYPE1_4 = "Ports with missing or unfixed buffers found"
    FOUND_REASON_TYPE1_4 = "All ports have approved buffer types (INV/BUF/CKND/CKBD/CKBMVPMZ/CKNMVPMZ/DCCK) attached and placement status is fixed"
    MISSING_REASON_TYPE1_4 = "Port buffer validation failed - missing approved buffer or unfixed placement"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_DESC_TYPE2_3 = "Port buffer requirements satisfied"
    MISSING_DESC_TYPE2_3 = "Port buffer requirements not satisfied"
    FOUND_REASON_TYPE2_3 = "Port has approved buffer attached and placement status is fixed"
    MISSING_REASON_TYPE2_3 = "Port drive not buffered with approved cell type or buffer placement not fixed"
    
    # All Types (waiver description unified)
    WAIVED_DESC = "Waived port buffer violations"
    
    # Waiver parameters (Type 3/4 ONLY) - FIXED: API-020 - waived_base_reason must be static string
    WAIVED_BASE_REASON = "Port buffer requirement waived per design approval"
    UNUSED_WAIVER_REASON = "Waiver entry not matched - no corresponding port buffer violation found"
    
    def __init__(self):
        """Initialize the checker."""
        super().__init__(
            check_module="8.0_PHYSICAL_IMPLEMENTATION_CHECK",
            item_id="IMP-8-0-0-04",
            item_desc="Confirm buffers are attached for all ports and are set as fixed."
        )
        # Custom member variables for parsed data
        self._parsed_items: List[Dict[str, Any]] = []
        self._port_stats: Dict[str, int] = {}
    
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
        Parse input files to extract port buffer connectivity information.
        
        Parses custom VLSI port-buffer connectivity report format.
        Each line describes a port's connectivity to buffer/IO cells with placement status.
        
        Returns:
            Dict with parsed data:
            - 'items': List[Dict] - Port entries with buffer status (with line_number, file_path)
            - 'metadata': Dict - Statistics (total ports, with buffers, fixed buffers, by direction)
            - 'errors': List - Any parsing errors encountered
        """
        # 1. Validate input files - returns tuple (valid_files_list, missing_files_list)
        valid_files, missing_files = self.validate_input_files()
        
        # FIXED: LOGIC-001 - Explicitly check for empty list
        if missing_files and len(missing_files) > 0:
            raise ConfigurationError(
                self.create_missing_files_error(missing_files)
            )
        if not valid_files or len(valid_files) == 0:
            raise ConfigurationError("No valid input files found")
        
        # 2. Initialize parsing structures
        items = []
        metadata = {}
        errors = []
        
        # Statistics tracking
        total_ports = 0
        ports_with_buffers = 0
        ports_with_fixed_buffers = 0
        direction_stats = {'input': 0, 'output': 0, 'bidi': 0}
        
        # Regex patterns for parsing
        # Pattern for port entries (handles both single and multiple buffers)
        port_pattern = re.compile(
            r'Port:\s*\{?([^;}]+)\}?;\s*'
            r'Direction:\s*(\w+);.*?'
            r'Port_connected_cell_name:\s*([^;]+);.*?'
            r'Port_connected_cell_pStatus:\s*([^;]+);'
        )
        
        # Valid buffer type prefix pattern
        buffer_prefix_pattern = re.compile(r'^(INV|BUF|CKND|CKBD|CKBMVPMZ|CKNMVPMZ|DCCK)')
        
        # 3. Parse each input file for port buffer connectivity information
        for file_path in valid_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line_num, line in enumerate(f, 1):
                        line = line.strip()
                        if not line or line.startswith('#'):
                            continue
                        
                        match = port_pattern.search(line)
                        if match:
                            port_name = match.group(1).strip()
                            direction = match.group(2).strip().lower()
                            cell_names_str = match.group(3).strip()
                            cell_statuses_str = match.group(4).strip()
                            
                            total_ports += 1
                            if direction in direction_stats:
                                direction_stats[direction] += 1
                            
                            # Skip bidirectional ports (use IO cells, not buffers)
                            if direction == 'bidi':
                                continue
                            
                            # Skip float ports (0x0 connection - special ports that don't require buffer cells)
                            if cell_names_str == '0x0':
                                continue
                            
                            # Parse cell names and statuses
                            cell_names = cell_names_str.split() if cell_names_str else []
                            cell_statuses = cell_statuses_str.split() if cell_statuses_str else []
                            
                            # Check for missing connection (empty cell names)
                            if not cell_names:
                                violation_type = 'missing_buffer'
                                violation_details = f"Port: {port_name}; Port_connected_cell_name: (empty); Port_connected_cell_pStatus: (empty);"
                                items.append({
                                    'name': port_name,
                                    'direction': direction,
                                    'has_buffer': False,
                                    'all_fixed': False,
                                    'cell_names': [],
                                    'cell_statuses': [],
                                    'violation_type': violation_type,
                                    'violation_details': violation_details,
                                    'line_number': line_num,
                                    'file_path': str(file_path)
                                })
                                continue
                            
                            # Validate buffer types
                            invalid_buffers = []
                            for cell_name in cell_names:
                                if not buffer_prefix_pattern.match(cell_name):
                                    invalid_buffers.append(cell_name)
                            
                            if invalid_buffers:
                                violation_type = 'invalid_buffer'
                                cell_names_display = ' '.join(cell_names) if cell_names else '(empty)'
                                cell_statuses_display = ' '.join(cell_statuses) if cell_statuses else '(empty)'
                                violation_details = f"Port: {port_name}; Port_connected_cell_name: {cell_names_display}; Port_connected_cell_pStatus: {cell_statuses_display};"
                                items.append({
                                    'name': port_name,
                                    'direction': direction,
                                    'has_buffer': False,
                                    'all_fixed': False,
                                    'cell_names': cell_names,
                                    'cell_statuses': cell_statuses,
                                    'violation_type': violation_type,
                                    'violation_details': violation_details,
                                    'line_number': line_num,
                                    'file_path': str(file_path)
                                })
                                continue
                            
                            # Valid buffer types - check placement status
                            ports_with_buffers += 1
                            all_fixed = all(status.lower() == 'fixed' for status in cell_statuses)
                            
                            if all_fixed:
                                ports_with_fixed_buffers += 1
                                # Port passes - has valid buffer and all fixed
                                items.append({
                                    'name': port_name,
                                    'direction': direction,
                                    'has_buffer': True,
                                    'all_fixed': True,
                                    'cell_names': cell_names,
                                    'cell_statuses': cell_statuses,
                                    'violation_type': None,
                                    'violation_details': None,
                                    'line_number': line_num,
                                    'file_path': str(file_path)
                                })
                            else:
                                # Buffer not fixed
                                violation_type = 'unfixed_buffer'
                                cell_names_display = ' '.join(cell_names) if cell_names else '(empty)'
                                cell_statuses_display = ' '.join(cell_statuses) if cell_statuses else '(empty)'
                                violation_details = f"Port: {port_name}; Port_connected_cell_name: {cell_names_display}; Port_connected_cell_pStatus: {cell_statuses_display};"
                                items.append({
                                    'name': port_name,
                                    'direction': direction,
                                    'has_buffer': True,
                                    'all_fixed': False,
                                    'cell_names': cell_names,
                                    'cell_statuses': cell_statuses,
                                    'violation_type': violation_type,
                                    'violation_details': violation_details,
                                    'line_number': line_num,
                                    'file_path': str(file_path)
                                })
            
            except Exception as e:
                errors.append(f"Error parsing {file_path}: {str(e)}")
        
        # 4. Store frequently reused data on self
        self._parsed_items = items
        self._port_stats = {
            'total_ports': total_ports,
            'ports_with_buffers': ports_with_buffers,
            'ports_with_fixed_buffers': ports_with_fixed_buffers,
            'direction_stats': direction_stats
        }
        
        return {
            'items': items,
            'metadata': self._port_stats,
            'errors': errors
        }
    
    # =========================================================================
    # Type 1: Boolean Check
    # =========================================================================
    
    def _execute_type1(self) -> CheckResult:
        """
        Type 1: Boolean Check.
        
        Check if all ports have buffers attached and are fixed.
        Does NOT use pattern_items for searching.
        
        Returns:
            CheckResult with is_pass based on check logic
        """
        # Parse input
        data = self._parse_input_files()
        items = data.get('items', [])
        
        # Only collect violations with detailed reasons
        missing_items = {}  # Ports with violations
        
        for item in items:
            port_name = item['name']
            
            if not (item['has_buffer'] and item['all_fixed']):
                # Port fails - collect with detailed violation reason
                violation_details = item.get('violation_details', 'Port drive not buffered or buffer not fixed')
                # Use violation_details as BOTH key and name for consistent display in log and rpt
                missing_items[violation_details] = {
                    'name': violation_details,  # Complete format for display
                    'line_number': item.get('line_number', 0),
                    'file_path': item.get('file_path', 'N/A'),
                    'reason': violation_details
                }
        
        # Type 1: Only output violations with detailed failure reasons
        return self.build_complete_output(
            found_items={},  # Don't output passing ports
            missing_items=missing_items,
            found_desc=self.FOUND_DESC_TYPE1_4,
            missing_desc=self.MISSING_DESC_TYPE1_4,
            found_reason=self.FOUND_REASON_TYPE1_4,
            missing_reason=lambda meta: meta.get('reason', self.MISSING_REASON_TYPE1_4)
        )
    
    # =========================================================================
    # Type 2: Value Check
    # =========================================================================
    
    def _execute_type2(self) -> CheckResult:
        """
        Type 2: Value Check.
        
        Search pattern_items in input files (status_check mode).
        found_items = patterns matched AND status correct (buffer exists and fixed).
        missing_items = patterns matched BUT status wrong (missing buffer or not fixed).
        
        Returns:
            CheckResult with is_pass based on value comparison
        """
        # Parse input
        data = self._parse_input_files()
        all_items = {item['name']: item for item in data.get('items', [])}
        
        # Get requirements
        pattern_items = self.item_data.get('requirements', {}).get('pattern_items', [])
        
        # status_check mode: Only collect violations with detailed reasons
        missing_items = {}    # Matched BUT status wrong
        
        for pattern in pattern_items:
            matched = False
            for port_name, item_data in all_items.items():
                # Check if pattern matches port name (case-insensitive, support wildcards)
                if self._matches_pattern(port_name, pattern):
                    matched = True
                    
                    if not (item_data['has_buffer'] and item_data['all_fixed']):
                        # Status wrong - collect with detailed violation reason
                        violation_details = item_data.get('violation_details', 'Port drive not buffered or buffer not fixed')
                        # Use violation_details as BOTH key and name for consistent display in log and rpt
                        missing_items[violation_details] = {
                            'name': violation_details,  # Complete format for display
                            'line_number': item_data.get('line_number', 0),
                            'file_path': item_data.get('file_path', 'N/A'),
                            'reason': violation_details
                        }
            
            if not matched:
                # Pattern not found in parsed items
                missing_items[pattern] = {
                    'name': pattern,
                    'line_number': 0,
                    'file_path': 'N/A'
                }
        
        # Type 2: Only output violations with detailed failure reasons
        return self.build_complete_output(
            found_items={},  # Don't output passing ports
            missing_items=missing_items,
            found_desc=self.FOUND_DESC_TYPE2_3,
            missing_desc=self.MISSING_DESC_TYPE2_3,
            found_reason=self.FOUND_REASON_TYPE2_3,
            missing_reason=lambda meta: meta.get('reason', self.MISSING_REASON_TYPE2_3)
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
        all_items = {item['name']: item for item in parsed_data.get('items', [])}
        
        # FIXED: API-008/016 - Use waivers.get() directly to preserve dict format
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # Get requirements
        pattern_items = self.item_data.get('requirements', {}).get('pattern_items', [])
        
        # Find violations (ports matching pattern but with buffer issues)
        violations = {}
        
        for pattern in pattern_items:
            for port_name, item_data in all_items.items():
                if self._matches_pattern(port_name, pattern):
                    if not (item_data['has_buffer'] and item_data['all_fixed']):
                        # Violation - collect with detailed reason
                        violation_details = item_data.get('violation_details', 'Port drive not buffered or buffer not fixed')
                        # Use violation_details as BOTH key and name for consistent display in log and rpt
                        violations[violation_details] = {
                            'name': violation_details,  # Complete format for display
                            'line_number': item_data.get('line_number', 0),
                            'file_path': item_data.get('file_path', 'N/A'),
                            'reason': violation_details
                        }
        
        # Separate waived/unwaived using template helper
        waived_items = {}
        unwaived_items = {}
        used_waivers = set()
        
        for viol_name, viol_data in violations.items():
            matched_waiver = self.match_waiver_entry(viol_name, waive_dict)
            if matched_waiver:
                waived_items[viol_name] = viol_data
                used_waivers.add(matched_waiver)
            else:
                unwaived_items[viol_name] = viol_data
        
        # Find unused waivers
        unused_waivers = [w for w in waive_dict.keys() if w not in used_waivers]
        
        # FIXED: API-009/021 - Pass dict directly, use missing_items parameter
        # Type 3: Only output violations and waivers with detailed reasons
        return self.build_complete_output(
            found_items={},  # Don't output passing ports
            waived_items=waived_items,
            missing_items=unwaived_items,
            waive_dict=waive_dict,
            unused_waivers=unused_waivers,
            found_desc=self.FOUND_DESC_TYPE2_3,
            missing_desc=self.MISSING_DESC_TYPE2_3,
            waived_desc=self.WAIVED_DESC,
            found_reason=self.FOUND_REASON_TYPE2_3,
            missing_reason=lambda meta: meta.get('reason', self.MISSING_REASON_TYPE2_3),
            waived_base_reason=self.WAIVED_BASE_REASON,
            unused_waiver_reason=self.UNUSED_WAIVER_REASON
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
        items = data.get('items', [])
        
        # FIXED: API-008/016 - Use waivers.get() directly to preserve dict format
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # Only collect violations with detailed reasons
        violations = {}   # Ports with violations
        
        for item in items:
            port_name = item['name']
            
            if not (item['has_buffer'] and item['all_fixed']):
                # Port fails - collect with detailed violation reason
                violation_details = item.get('violation_details', 'Port drive not buffered or buffer not fixed')
                # Use violation_details as BOTH key and name for consistent display in log and rpt
                violations[violation_details] = {
                    'name': violation_details,  # Complete format for display
                    'line_number': item.get('line_number', 0),
                    'file_path': item.get('file_path', 'N/A'),
                    'reason': violation_details
                }
        
        # Separate waived/unwaived
        waived_items = {}
        unwaived_items = {}
        used_waivers = set()
        
        for viol_name, viol_data in violations.items():
            matched_waiver = self.match_waiver_entry(viol_name, waive_dict)
            if matched_waiver:
                waived_items[viol_name] = viol_data
                used_waivers.add(matched_waiver)
            else:
                unwaived_items[viol_name] = viol_data
        
        # Find unused waivers
        unused_waivers = [w for w in waive_dict.keys() if w not in used_waivers]
        
        # FIXED: API-009/021 - Pass dict directly, use missing_items parameter
        # Type 4: Only output violations and waivers with detailed reasons
        return self.build_complete_output(
            found_items={},  # Don't output passing ports
            waived_items=waived_items,
            missing_items=unwaived_items,
            waive_dict=waive_dict,
            unused_waivers=unused_waivers,
            found_desc=self.FOUND_DESC_TYPE1_4,
            missing_desc=self.MISSING_DESC_TYPE1_4,
            waived_desc=self.WAIVED_DESC,
            found_reason=self.FOUND_REASON_TYPE1_4,
            missing_reason=lambda meta: meta.get('reason', self.MISSING_REASON_TYPE1_4),
            waived_base_reason=self.WAIVED_BASE_REASON,
            unused_waiver_reason=self.UNUSED_WAIVER_REASON
        )
    
    # =========================================================================
    # Helper Methods
    # =========================================================================
    
    def _matches_pattern(self, item: str, pattern: str) -> bool:
        """
        Check if item matches pattern (supports wildcards).
        
        Args:
            item: Item to check
            pattern: Pattern to match (supports * wildcards)
            
        Returns:
            True if item matches pattern
        """
        # Support wildcards
        if '*' in pattern:
            regex_pattern = pattern.replace('*', '.*')
            return bool(re.search(regex_pattern, item, re.IGNORECASE))
        # Exact match (case-insensitive)
        return pattern.lower() == item.lower()


# =========================================================================
# Entry Point
# =========================================================================

def main():
    """Main entry point."""
    checker = Check_8_0_0_04()
    checker.init_checker(Path(__file__))
    result = checker.execute_check()
    checker.write_output(result)
    return 0 if result.is_pass else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())