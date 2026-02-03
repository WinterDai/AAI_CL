################################################################################
# Script Name: IMP-8-0-0-02.py
#
# Purpose:
#   Confirm all ports status are Fixed.
#
# Logic:
#   - Parse input files: IMP-8-0-0-02.rpt
#   - Extract port names and placement status using regex patterns
#   - Handle standard ports, bus notation ports, and spacing variations
#   - Classify ports as fixed or unfixed based on status field
#   - Track total ports, fixed ports, and unfixed ports with line numbers
#   - Generate summary statistics (INFO01) and unfixed port list (ERROR01)
#   - PASS if all ports have status='fixed', FAIL if any unfixed ports exist
#
# Auto Type Detection:
#   Type 1: requirements.value=N/A, pattern_items [] (empty), waivers.value=N/A/0 → Boolean Check
#   Type 2: requirements.value>0, pattern_items [...] (defined), waivers.value=N/A/0 → Value Check
#   Type 3: requirements.value>0, pattern_items [...] (defined), waivers.value>0 → Value Check with Waiver Logic
#   Type 4: requirements.value=N/A, pattern_items [] (empty), waivers.value>0 → Boolean Check with Waiver Logic
#   Note: requirements.value indicates number of patterns for config validation (doesn't affect PASS/FAIL)
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
# Refactored: 2025-12-18 (Using checker_templates v1.1.0)
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
from checker_templates.input_file_parser_template import InputFileParserMixin  # Optional but recommended


# MANDATORY: Inherit mixins in correct order (InputFileParserMixin first if used)
class Check_8_0_0_02(InputFileParserMixin, OutputBuilderMixin, WaiverHandlerMixin, BaseChecker):
    """
    IMP-8-0-0-02: Confirm all ports status are Fixed.
    
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
    FOUND_DESC_TYPE1_4 = "All ports have fixed placement status"
    MISSING_DESC_TYPE1_4 = "Ports with unfixed placement status found"
    FOUND_REASON_TYPE1_4 = "All ports found with fixed placement status"
    MISSING_REASON_TYPE1_4 = "Port placement status not fixed (placed or unplaced)"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_DESC_TYPE2_3 = "All ports have fixed placement status (pattern matched)"
    MISSING_DESC_TYPE2_3 = "Port placement status pattern not satisfied (placed/unplaced found)"
    FOUND_REASON_TYPE2_3 = "Port placement status matched expected pattern (fixed)"
    MISSING_REASON_TYPE2_3 = "Port placement status pattern not satisfied (expected: fixed, found: placed/unplaced)"
    
    # All Types (waiver description unified)
    WAIVED_DESC = "Waived ports with unfixed placement status"
    
    # Waiver parameters (Type 3/4 ONLY)
    WAIVED_BASE_REASON = "Port placement status waived per design team approval"
    UNUSED_WAIVER_REASON = "Waiver not matched - no corresponding port with unfixed status found"
    
    def __init__(self):
        """Initialize the checker."""
        super().__init__(
            check_module="8.0_PHYSICAL_IMPLEMENTATION_CHECK",
            item_id="IMP-8-0-0-02",
            item_desc="Confirm all ports status are Fixed."
        )
        # Custom member variables for parsed data
        self._parsed_items: List[Dict[str, Any]] = []
        self._total_ports: int = 0
        self._fixed_ports: int = 0
        self._unfixed_ports: List[Dict[str, Any]] = []
    
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
        Parse input files to extract port status information.
        
        Parses IMP-8-0-0-02.rpt to extract port names and placement status.
        Handles multiple port name formats:
        - Standard: "Port: pad_mem_dqs_p ; Pstatus: fixed"
        - Bus notation: "Port: {pad_mem_data[7]} ; Pstatus: fixed"
        - Spacing variations: "Port: clk4x ; Pstatus: fixed"
        
        Returns:
            Dict with parsed data:
            - 'items': List[Dict] - All parsed ports with metadata
            - 'metadata': Dict - Summary statistics
            - 'errors': List - Any parsing errors encountered
            - 'total_ports': int - Total number of ports found
            - 'fixed_ports': int - Number of fixed ports
            - 'unfixed_ports': List[Dict] - Ports with non-fixed status
        """
        # 1. Validate input files - IMPORTANT: returns tuple (valid_files_list, missing_files_list)
        valid_files, missing_files = self.validate_input_files()
        
        # Check for missing files
        if missing_files:
            raise ConfigurationError(
                self.create_missing_files_error(missing_files)
            )
        if not valid_files or len(valid_files) == 0:
            raise ConfigurationError("No valid input files found")
        
        # 2. Initialize counters and storage
        all_items = []
        total_ports = 0
        fixed_ports = 0
        unfixed_ports = []
        errors = []
        
        # 3. Define regex patterns for port status extraction
        # Pattern 1: Standard port status line
        pattern1 = re.compile(r'^Port:\s*([^;{]+?)\s*;\s*Pstatus:\s*(\w+)\s*$')
        # Pattern 2: Port with bus notation (braces)
        pattern2 = re.compile(r'^Port:\s*\{([^}]+)\}\s*;\s*Pstatus:\s*(\w+)\s*$')
        # Pattern 3: Generic fallback for spacing variations
        pattern3 = re.compile(r'Port:\s*(.+?)\s*;\s*Pstatus:\s*(\S+)')
        
        # 4. Parse each file
        for file_path in valid_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line_num, line in enumerate(f, 1):
                        line = line.strip()
                        if not line or line.startswith('#'):
                            continue
                        
                        # Try patterns in order of specificity
                        match = pattern2.search(line)  # Try bus notation first
                        if not match:
                            match = pattern1.search(line)  # Try standard format
                        if not match:
                            match = pattern3.search(line)  # Try generic fallback
                        
                        if match:
                            port_name = match.group(1).strip()
                            status = match.group(2).strip().lower()
                            
                            # Create item with metadata
                            item = {
                                'name': port_name,
                                'status': status,
                                'line_number': line_num,
                                'file_path': str(file_path),
                                'line_content': line
                            }
                            
                            all_items.append(item)
                            total_ports += 1
                            
                            # Classify by status
                            if status == 'fixed':
                                fixed_ports += 1
                            else:
                                # Any non-fixed status (unfixed, placed, unplaced)
                                unfixed_ports.append(item)
                                
            except Exception as e:
                errors.append(f"Error parsing {file_path}: {str(e)}")
        
        # 5. Store on self for reuse
        self._parsed_items = all_items
        self._total_ports = total_ports
        self._fixed_ports = fixed_ports
        self._unfixed_ports = unfixed_ports
        
        # 6. Return aggregated dict
        return {
            'items': all_items,
            'metadata': {
                'total_ports': total_ports,
                'fixed_ports': fixed_ports,
                'unfixed_count': len(unfixed_ports)
            },
            'errors': errors,
            'total_ports': total_ports,
            'fixed_ports': fixed_ports,
            'unfixed_ports': unfixed_ports
        }
    
    # =========================================================================
    # Type 1: Boolean Check
    # =========================================================================
    
    def _execute_type1(self) -> CheckResult:
        """
        Type 1: Boolean Check.
        
        Checks if all ports have fixed placement status.
        PASS: All ports are fixed (unfixed_ports list is empty)
        FAIL: One or more ports have non-fixed status
        
        Returns:
            CheckResult with is_pass based on check logic
        """
        # Parse input
        data = self._parse_input_files()
        unfixed_ports = data.get('unfixed_ports', [])
        total_ports = data.get('total_ports', 0)
        fixed_ports = data.get('fixed_ports', 0)
        
        # Build found_items (fixed ports) with metadata
        found_items = {}
        for item in self._parsed_items:
            if item['status'] == 'fixed':
                found_items[item['name']] = {
                    'name': item['name'],
                    'line_number': item['line_number'],
                    'file_path': item['file_path']
                }
        
        # Build missing_items (unfixed ports) with metadata
        missing_items = {}
        for item in unfixed_ports:
            key = f"{item['name']} (status: {item['status']})"
            missing_items[key] = {
                'name': key,
                'line_number': item['line_number'],
                'file_path': item['file_path']
            }
        
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
        
        Search pattern_items in input files.
        Only output items that match pattern_items.
        PASS if all matched items have fixed status.
        
        Returns:
            CheckResult with is_pass based on value comparison
        """
        # Parse input
        data = self._parse_input_files()
        
        # Get requirements
        requirements = self.item_data.get('requirements', {})
        pattern_items = requirements.get('pattern_items', [])
        expected_value = requirements.get('value', 'N/A')
        
        # Build all items dict for pattern matching
        all_items = {}
        for item in self._parsed_items:
            all_items[item['name']] = {
                'name': item['name'],
                'status': item['status'],
                'line_number': item['line_number'],
                'file_path': item['file_path']
            }
        
        # Match patterns against items - only output matched items
        found_items = {}  # Matched items with fixed status (INFO)
        missing_items = {}  # Matched items with unfixed status (ERROR)
        missing_patterns = []  # Patterns not matched
        
        for pattern in pattern_items:
            matched = False
            for item_name, item_data in all_items.items():
                # Substring match for pattern
                if pattern.lower() in item_name.lower():
                    output_data = {
                        'name': item_name,
                        'line_number': item_data['line_number'],
                        'file_path': item_data['file_path']
                    }
                    
                    # Separate by status
                    if item_data['status'] == 'fixed':
                        found_items[item_name] = output_data
                    else:
                        key = f"{item_name} (status: {item_data['status']})"
                        missing_items[key] = {
                            'name': key,
                            'line_number': item_data['line_number'],
                            'file_path': item_data['file_path']
                        }
                    matched = True
                    break
            
            if not matched:
                missing_patterns.append(pattern)
        
        # Use template helper - only output pattern-matched items
        return self.build_complete_output(
            found_items=found_items,  # Matched fixed ports as INFO
            missing_items=missing_items if missing_items else missing_patterns,  # Matched unfixed ports as ERROR, or missing patterns
            found_desc=f"{self.FOUND_DESC_TYPE2_3} ({len(found_items) + len(missing_items)}/{expected_value} patterns found)",
            missing_desc=f"{self.MISSING_DESC_TYPE2_3} ({len(missing_items)} unfixed, {len(missing_patterns)} patterns not found)",
            found_reason=self.FOUND_REASON_TYPE2_3,
            missing_reason=self.MISSING_REASON_TYPE2_3
        )
    
    # =========================================================================
    # Type 3: Value Check with Waiver Logic
    # =========================================================================
    
    def _execute_type3(self) -> CheckResult:
        """
        Type 3: Value check with waiver support.
        
        Search pattern_items in input files, then apply waiver logic.
        Only output items that match pattern_items.
        Matched unfixed ports can be waived; unwaived unfixed -> FAIL.
        
        Returns:
            CheckResult with FAIL for unwaived errors, INFO for waived items
        """
        # Parse input
        parsed_data = self._parse_input_files()
        
        # Get requirements
        requirements = self.item_data.get('requirements', {})
        pattern_items = requirements.get('pattern_items', [])
        
        # Get waivers
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # Build all items dict for pattern matching
        all_items = {}
        for item in self._parsed_items:
            all_items[item['name']] = {
                'name': item['name'],
                'status': item['status'],
                'line_number': item['line_number'],
                'file_path': item['file_path']
            }
        
        # Match patterns against items - only process matched items
        found_items = {}  # Matched fixed ports (INFO)
        waived_items = {}  # Matched waived unfixed ports (INFO)
        unwaived_errors = {}  # Matched unwaived unfixed ports (ERROR)
        missing_patterns = []  # Patterns not matched
        used_waiver_patterns = set()
        
        for pattern in pattern_items:
            matched = False
            for item_name, item_data in all_items.items():
                # Substring match for pattern
                if pattern.lower() in item_name.lower():
                    output_data = {
                        'name': item_name,
                        'line_number': item_data['line_number'],
                        'file_path': item_data['file_path']
                    }
                    
                    if item_data['status'] == 'fixed':
                        found_items[item_name] = output_data
                    else:
                        # Check if unfixed port is waived
                        matched_waiver = None
                        for waiver_pattern in waive_dict.keys():
                            if self.match_waiver_entry(item_name, {waiver_pattern: waive_dict[waiver_pattern]}):
                                matched_waiver = waiver_pattern
                                used_waiver_patterns.add(waiver_pattern)
                                break
                        
                        key = f"{item_name} (status: {item_data['status']})"
                        if matched_waiver:
                            waived_items[key] = {
                                'name': key,
                                'line_number': item_data['line_number'],
                                'file_path': item_data['file_path']
                            }
                        else:
                            unwaived_errors[key] = {
                                'name': key,
                                'line_number': item_data['line_number'],
                                'file_path': item_data['file_path']
                            }
                    
                    matched = True
                    break
            
            if not matched:
                missing_patterns.append(pattern)
        
        # Find unused waivers
        unused_waivers = {
            w: {
                'name': w,
                'line_number': 0,
                'file_path': 'waiver_config'
            }
            for w in waive_dict.keys()
            if w not in used_waiver_patterns
        }
        
        # Build output: only pattern-matched items
        return self.build_complete_output(
            found_items=found_items,  # Matched fixed ports as INFO
            waived_items=waived_items,  # Waived matched unfixed ports as INFO
            missing_items=unwaived_errors if unwaived_errors else missing_patterns,  # Unwaived matched unfixed as ERROR
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
        
        Same boolean check as Type 1 (no pattern_items), plus waiver classification.
        
        Returns:
            CheckResult with waiver logic applied
        """
        # Parse input
        data = self._parse_input_files()
        unfixed_ports = data.get('unfixed_ports', [])
        
        # Get waivers
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # Build found_items (fixed ports)
        found_items = {}
        for item in self._parsed_items:
            if item['status'] == 'fixed':
                found_items[item['name']] = {
                    'name': item['name'],
                    'line_number': item['line_number'],
                    'file_path': item['file_path']
                }
        
        # Separate waived/unwaived unfixed ports
        waived_items = {}
        unwaived_items = {}
        used_waiver_names = set()
        
        for item in unfixed_ports:
            port_name = item['name']
            key = f"{port_name} (status: {item['status']})"
            
            # Check if port matches any waiver pattern
            matched_waiver = None
            for waiver_name in waive_dict.keys():
                if self.match_waiver_entry(port_name, {waiver_name: waive_dict[waiver_name]}):
                    matched_waiver = waiver_name
                    used_waiver_names.add(waiver_name)
                    break
            
            if matched_waiver:
                waived_items[key] = {
                    'name': key,
                    'line_number': item['line_number'],
                    'file_path': item['file_path']
                }
            else:
                unwaived_items[key] = {
                    'name': key,
                    'line_number': item['line_number'],
                    'file_path': item['file_path']
                }
        
        # Find unused waivers
        unused_waivers = {}
        for waiver_name in waive_dict.keys():
            if waiver_name not in used_waiver_names:
                unused_waivers[waiver_name] = {
                    'name': waiver_name,
                    'line_number': 0,
                    'file_path': 'waiver_config'
                }
        
        return self.build_complete_output(
            found_items=found_items,
            missing_items=unwaived_items,
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
    checker = Check_8_0_0_02()
    checker.init_checker(Path(__file__))
    result = checker.execute_check()
    checker.write_output(result)
    return 0 if result.is_pass else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())