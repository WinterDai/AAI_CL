################################################################################
# Script Name: IMP-15-0-0-01.py
#
# Purpose:
#   Confirm whether CNOD check is needed. For example, we need to check CNOD for TSMCN5 process.
#
# Logic:
#   - Parse input files: setup_vars.tcl
#   - Extract DESIGN_PROCESS variable from TCL configuration file
#   - Identify process technology node (tsmc3, tsmcn5, tsmcn4, tsmcn3, etc.)
#   - Determine CNOD check requirement based on process node
#   - CNOD checks are required for: tsmcn5, tsmcn4, tsmcn3
#   - Report process technology and CNOD requirement status
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
from checker_templates.input_file_parser_template import InputFileParserMixin  # Optional but recommended


# MANDATORY: Inherit mixins in correct order (InputFileParserMixin first if used)
class Check_15_0_0_01(InputFileParserMixin, OutputBuilderMixin, WaiverHandlerMixin, BaseChecker):
    """
    IMP-15-0-0-01: Confirm whether CNOD check is needed. For example, we need to check CNOD for TSMCN5 process.
    
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
    FOUND_DESC_TYPE1_4 = "Process technology identified and CNOD requirement determined"
    MISSING_DESC_TYPE1_4 = "DESIGN_PROCESS variable not found in setup configuration"
    FOUND_REASON_TYPE1_4 = "DESIGN_PROCESS variable found in setup configuration"
    MISSING_REASON_TYPE1_4 = "Required DESIGN_PROCESS variable not found in setup_vars.tcl"
    
    # Type 2/3: Pattern checks - COPY EXACT VALUES FROM README!
    FOUND_DESC_TYPE2_3 = "DESIGN_PROCESS variable matched and validated"
    MISSING_DESC_TYPE2_3 = "DESIGN_PROCESS pattern not satisfied in setup file"
    FOUND_REASON_TYPE2_3 = "DESIGN_PROCESS pattern matched and CNOD requirement validated"
    MISSING_REASON_TYPE2_3 = "DESIGN_PROCESS pattern not satisfied or missing from configuration"
    
    # All Types (waiver description) - COPY EXACT VALUES FROM README!
    WAIVED_DESC = "Process technology check waived"
    
    # Waiver parameters (Type 3/4 ONLY) - COPY EXACT VALUES FROM README!
    WAIVED_BASE_REASON = "CNOD check requirement waived per design team approval"
    
    def __init__(self):
        """Initialize the checker."""
        super().__init__(
            check_module="15.0_ESD_PERC_CHECK",
            item_id="IMP-15-0-0-01",
            item_desc="Confirm whether CNOD check is needed. For example, we need to check CNOD for TSMCN5 process."
        )
        # Custom member variables for parsed data
        self._parsed_items: List[Dict[str, Any]] = []
        self._process_node: Optional[str] = None
        self._cnod_required: bool = False
    
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
        
        Parses setup_vars.tcl to extract DESIGN_PROCESS and other MISC variables.
        
        Returns:
            Dict with parsed data:
            - 'items': List[Dict] - Main items to check (with metadata: line_number, file_path)
            - 'metadata': Dict - File metadata (process_node, cnod_required)
            - 'errors': List - Any parsing errors encountered
        """
        # 1. Validate input files (raises ConfigurationError if missing)
        valid_files, missing_files = self.validate_input_files()
        
        # Fix LOGIC-001: Explicitly check for empty list
        if not valid_files or len(valid_files) == 0:
            raise ConfigurationError(
                self.create_missing_files_error(missing_files if missing_files else ["No input files configured"])
            )
        
        if missing_files:
            raise ConfigurationError(
                self.create_missing_files_error(missing_files)
            )
        
        # 2. Parse TCL configuration file
        items = []
        metadata = {}
        errors = []
        process_node = None
        cnod_required = False
        
        # CNOD-required process nodes (tsmc3 and tsmcn3 are equivalent)
        CNOD_PROCESSES = ['tsmcn5', 'tsmcn4', 'tsmcn3', 'tsmc3', 'tsmc5', 'tsmc4']
        
        # Pattern for extracting MISC variables
        # Pattern 1: Extract DESIGN_PROCESS specifically
        design_process_pattern = re.compile(r'^set\s+MISC\(DESIGN_PROCESS\)\s+(\w+)', re.IGNORECASE)
        # Pattern 2: Generic MISC variable extraction
        misc_pattern = re.compile(r'^set\s+MISC\(([^)]+)\)\s+(.+)$', re.IGNORECASE)
        
        for file_path in valid_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line_num, line in enumerate(f, 1):
                        # Skip comments and empty lines
                        stripped_line = line.strip()
                        if not stripped_line or stripped_line.startswith('#'):
                            continue
                        
                        # Try to match DESIGN_PROCESS pattern first
                        match = design_process_pattern.search(line)
                        if match:
                            process_node = match.group(1).strip()
                            cnod_required = process_node.lower() in CNOD_PROCESSES
                            
                            items.append({
                                'name': 'DESIGN_PROCESS',
                                'value': process_node,
                                'line_number': line_num,
                                'file_path': str(file_path),
                                'line_content': stripped_line
                            })
                            continue
                        
                        # Try generic MISC pattern
                        match = misc_pattern.search(line)
                        if match:
                            var_name = match.group(1).strip()
                            var_value = match.group(2).strip()
                            
                            items.append({
                                'name': var_name,
                                'value': var_value,
                                'line_number': line_num,
                                'file_path': str(file_path),
                                'line_content': stripped_line
                            })
            except Exception as e:
                errors.append(f"Error parsing {file_path}: {str(e)}")
        
        # 3. Store frequently reused data on self
        self._parsed_items = items
        self._process_node = process_node
        self._cnod_required = cnod_required
        
        # 4. Build metadata
        metadata = {
            'process_node': process_node,
            'cnod_required': cnod_required,
            'total_variables': len(items)
        }
        
        return {
            'items': items,
            'metadata': metadata,
            'errors': errors
        }
    
    # =========================================================================
    # Type 1: Boolean Check
    # =========================================================================
    
    def _execute_type1(self) -> CheckResult:
        """
        Type 1: Boolean Check.
        
        Custom boolean validation (file exists? config valid?).
        Does NOT use pattern_items for searching.
        
        Use OutputBuilderMixin.build_complete_output() for automatic formatting.
        
        Returns:
            CheckResult with is_pass based on check logic
        """
        # Parse input
        data = self._parse_input_files()
        items = data.get('items', [])
        metadata = data.get('metadata', {})
        
        # Check if DESIGN_PROCESS was found
        process_node = metadata.get('process_node')
        cnod_required = metadata.get('cnod_required', False)
        
        if process_node:
            # Found DESIGN_PROCESS - determine CNOD status
            cnod_status_text = "needed" if cnod_required else "not needed"
            
            # For report: short name, reason uses template format
            # For log: simple format without explanation
            short_name = f"Process: {process_node}"
            log_display = f"Process: {process_node} | CNOD Check Required: {'Yes' if cnod_required else 'No'}"
            reason_text = f"Process technology found: {process_node}. CNOD check is {cnod_status_text}."
            
            found_items = {
                'DESIGN_PROCESS': {
                    'name': short_name,  # Short name for report
                    'line_number': next((item['line_number'] for item in items if item['name'] == 'DESIGN_PROCESS'), 0),
                    'file_path': next((item['file_path'] for item in items if item['name'] == 'DESIGN_PROCESS'), 'N/A'),
                    'process_node': process_node,
                    'cnod_status': cnod_status_text,
                    'reason': reason_text,  # Template format for report reason
                    'log_display': log_display  # Simple format for log output
                }
            }
            missing_items = []
        else:
            found_items = {}
            missing_items = ['DESIGN_PROCESS']

        # Output must match README format:
        # INFO01: "Process: tsmc3 | CNOD Check Required: No | Reason: ..."
        return self.build_complete_output(
            found_items=found_items,
            missing_items=missing_items,
            found_desc=self.FOUND_DESC_TYPE1_4,
            missing_desc=self.MISSING_DESC_TYPE1_4,
            found_reason=self.FOUND_REASON_TYPE1_4,  # Use constant for report
            missing_reason=self.MISSING_REASON_TYPE1_4,
            name_extractor=lambda item_name, metadata: metadata.get('log_display', metadata.get('name', item_name))
        )
    
    # =========================================================================
    # Type 2: Value Check
    # =========================================================================
    
    def _execute_type2(self) -> CheckResult:
        """
        Type 2: Value Check.
        
        Search pattern_items in input files.
        found_items = patterns found; missing_items = patterns not found.
        PASS/FAIL depends on check purpose (violation check vs requirement check).
        
        Template auto-handles waiver=0 conversions.
        
        Returns:
            CheckResult with is_pass based on value comparison
        """
        # Parse input
        data = self._parse_input_files()
        items = data.get('items', [])
        
        # Get requirements
        pattern_items = self.item_data.get('requirements', {}).get('pattern_items', [])
        
        # Build lookup dict for parsed items
        parsed_dict = {item['name']: item for item in items}
        
        # existence_check mode: Check if pattern_items exist in input files
        found_items = {}
        missing_items = []
        
        for pattern in pattern_items:
            if pattern in parsed_dict:
                item = parsed_dict[pattern]
                found_items[pattern] = {
                    'name': pattern,
                    'line_number': item.get('line_number', 0),
                    'file_path': item.get('file_path', 'N/A'),
                    'variable_name': pattern,
                    'variable_value': item.get('value', 'N/A')
                }
            else:
                missing_items.append(pattern)
        
        # Use template helper (auto-handles waiver=0)
        # Type 2: Use TYPE2_3 reason (emphasize "matched/satisfied") - API-025
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
        items = parsed_data.get('items', [])
        
        # Fix API-016: Use waivers.get() directly to preserve dict format
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # Get requirements
        pattern_items = self.item_data.get('requirements', {}).get('pattern_items', [])
        
        # Build lookup dict for parsed items
        parsed_dict = {item['name']: item for item in items}
        
        # existence_check mode: Check if pattern_items exist in input files
        # Separate waived/unwaived using template helper
        found_items = {}
        waived_items = {}
        missing_items = []
        
        for pattern in pattern_items:
            if pattern in parsed_dict:
                item = parsed_dict[pattern]
                item_dict = {
                    'name': pattern,
                    'line_number': item.get('line_number', 0),
                    'file_path': item.get('file_path', 'N/A'),
                    'variable_name': pattern,
                    'variable_value': item.get('value', 'N/A')
                }
                
                # Check if waived
                if self.match_waiver_entry(pattern, waive_dict):
                    waived_items[pattern] = item_dict
                else:
                    found_items[pattern] = item_dict
            else:
                # Pattern not found - check if missing is waived
                if self.match_waiver_entry(pattern, waive_dict):
                    waived_items[pattern] = {
                        'name': pattern,
                        'line_number': 0,
                        'file_path': 'N/A',
                        'variable_name': pattern,
                        'variable_value': 'NOT FOUND'
                    }
                else:
                    missing_items.append(pattern)
        
        # Find unused waivers
        used_names = set(waived_items.keys())
        unused_waivers = [name for name in waive_dict.keys() if name not in used_names]
        
        # Use template helper for automatic output formatting
        # Type 3: Use TYPE2_3 reason (emphasize "matched/satisfied") - API-025
        return self.build_complete_output(
            found_items=found_items,
            waived_items=waived_items,
            missing_items=missing_items,
            waive_dict=waive_dict,
            unused_waivers=unused_waivers,
            found_desc=self.FOUND_DESC_TYPE2_3,
            missing_desc=self.MISSING_DESC_TYPE2_3,
            waived_desc=self.WAIVED_DESC,
            found_reason=self.FOUND_REASON_TYPE1_4,  # Use constant for report
            missing_reason=self.MISSING_REASON_TYPE1_4,
            waived_base_reason=self.WAIVED_BASE_REASON,
            name_extractor=lambda item_name, metadata: metadata.get('log_display', metadata.get('name', item_name))
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
        metadata = data.get('metadata', {})
        
        # Fix API-016: Use waivers.get() directly to preserve dict format
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # Check if DESIGN_PROCESS was found
        process_node = metadata.get('process_node')
        cnod_required = metadata.get('cnod_required', False)
        
        found_items = {}
        waived_items = {}
        missing_items = []
        
        if process_node:
            cnod_status_text = "needed" if cnod_required else "not needed"
            
            # For report: short name, reason uses template format
            # For log: simple format without explanation
            short_name = f"Process: {process_node}"
            log_display = f"Process: {process_node} | CNOD Check Required: {'Yes' if cnod_required else 'No'}"
            reason_text = f"Process technology found: {process_node}. CNOD check is {cnod_status_text}."
            
            item_dict = {
                'name': short_name,  # Short name for report
                'line_number': next((item['line_number'] for item in items if item['name'] == 'DESIGN_PROCESS'), 0),
                'file_path': next((item['file_path'] for item in items if item['name'] == 'DESIGN_PROCESS'), 'N/A'),
                'process_node': process_node,
                'cnod_status': cnod_status_text,
                'reason': reason_text,  # Template format for report reason
                'log_display': log_display  # Simple format for log output
            }
            
            # Check if waived
            if self.match_waiver_entry('DESIGN_PROCESS', waive_dict):
                waived_items['DESIGN_PROCESS'] = item_dict
            else:
                found_items['DESIGN_PROCESS'] = item_dict
        else:
            # DESIGN_PROCESS not found - check if waived
            if self.match_waiver_entry('DESIGN_PROCESS', waive_dict):
                waived_items['DESIGN_PROCESS'] = {
                    'name': 'DESIGN_PROCESS',
                    'line_number': 0,
                    'file_path': 'N/A',
                    'process_node': 'NOT FOUND',
                    'cnod_status': 'UNKNOWN',
                    'reason': 'DESIGN_PROCESS variable not found in setup_vars.tcl'
                }
            else:
                missing_items.append('DESIGN_PROCESS')

        # Find unused waivers
        used_names = set(waived_items.keys())
        unused_waivers = [name for name in waive_dict.keys() if name not in used_names]

        return self.build_complete_output(
            found_items=found_items,
            waived_items=waived_items,
            missing_items=missing_items,
            waive_dict=waive_dict,
            unused_waivers=unused_waivers,
            found_desc=self.FOUND_DESC_TYPE1_4,
            missing_desc=self.MISSING_DESC_TYPE1_4,
            waived_desc=self.WAIVED_DESC,
            found_reason=self.FOUND_REASON_TYPE1_4,  # Use constant for report
            missing_reason=self.MISSING_REASON_TYPE1_4,
            waived_base_reason=self.WAIVED_BASE_REASON,
            name_extractor=lambda item_name, metadata: metadata.get('log_display', metadata.get('name', item_name))
        )


# =========================================================================
# Entry Point
# =========================================================================

def main():
    """Main entry point."""
    checker = Check_15_0_0_01()
    checker.init_checker(Path(__file__))
    result = checker.execute_check()
    checker.write_output(result)
    return 0 if result.is_pass else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())