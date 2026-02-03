################################################################################
# Script Name: IMP-9-0-0-04.py
#
# Purpose:
#   Confirm no physically open nets in QRC imcomplete net report.
#
# Logic:
#   - Parse input files: *.incompletenets
#   - Extract net names from "NET: <net_name>" lines
#   - Extract connection status from "- <reason>" lines following each NET declaration
#   - Classify nets: single-pin connected to physical wire (acceptable) vs physically open (error)
#   - Aggregate results across all corner reports
#   - Report physically open nets as errors, provide statistics on acceptable single-pin nets
#   - Apply waiver logic if configured (Type 3/4)
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
# Refactored: 2025-12-25 (Using checker_templates v1.1.0)
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
class Check_9_0_0_04(InputFileParserMixin, OutputBuilderMixin, WaiverHandlerMixin, BaseChecker):
    """
    IMP-9-0-0-04: Confirm no physically open nets in QRC imcomplete net report.
    
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
    FOUND_DESC_TYPE1_4 = "Acceptable single-pin nets connected to physical wire"
    MISSING_DESC_TYPE1_4 = "Physically open nets detected"
    FOUND_REASON_TYPE1_4 = "Single-pin net connected to physical wire (acceptable)"
    MISSING_REASON_TYPE1_4 = "Physically open net detected - routing failure or connectivity issue"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_DESC_TYPE2_3 = "Expected incomplete nets matched and validated"
    MISSING_DESC_TYPE2_3 = "Expected incomplete nets not satisfied or missing"
    FOUND_REASON_TYPE2_3 = "Expected incomplete net pattern matched and validated"
    MISSING_REASON_TYPE2_3 = "Expected incomplete net pattern not satisfied or missing"
    
    # All Types (waiver description unified)
    WAIVED_DESC = "Waived physically open nets"
    
    # Waiver parameters (Type 3/4 ONLY)
    WAIVED_BASE_REASON = "Physically open net waived per design approval"
    UNUSED_WAIVER_REASON = "Waiver pattern not matched to any physically open net"
    
    def __init__(self):
        """Initialize the checker."""
        super().__init__(
            check_module="9.0_RC_EXTRACTION_CHECK",
            item_id="IMP-9-0-0-04",
            item_desc="Confirm no physically open nets in QRC imcomplete net report."
        )
        # Custom member variables for parsed data
        self._parsed_items: List[Dict[str, Any]] = []
        self._acceptable_nets: List[Dict[str, Any]] = []
        self._open_nets: List[Dict[str, Any]] = []
    
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
        except Exception as e:
            # Handle unexpected errors
            return create_check_result(
                is_pass=False,
                item_id=self.item_id,
                item_desc=self.item_desc,
                details=[DetailItem(
                    name="Error",
                    severity=Severity.FAIL,
                    reason=f"Unexpected error during check execution: {str(e)}",
                    line_number=0,
                    file_path="N/A"
                )]
            )
    
    # =========================================================================
    # Input Parsing (Common for All Types)
    # =========================================================================
    
    def _parse_input_files(self) -> Dict[str, Any]:
        """
        Parse input files to extract relevant data.
        
        Parses QRC incomplete nets reports with state-machine approach:
        1. Track net names from "NET: <net_name>" lines
        2. Track connection status from "- <reason>" lines
        3. Classify nets: acceptable (single-pin physical wire) vs open (error)
        4. Aggregate across all corner reports
        
        Returns:
            Dict with parsed data:
            - 'items': List[Dict] - All incomplete nets with metadata
            - 'acceptable_nets': List[Dict] - Single-pin nets (acceptable)
            - 'open_nets': List[Dict] - Physically open nets (errors)
            - 'metadata': Dict - Statistics
            - 'errors': List - Parsing errors
        """
        # 1. Validate inputs - IMPORTANT: returns tuple (valid_files_list, missing_files_list)
        valid_files, missing_files = self.validate_input_files()
        
        # FIXED: KNOWN_ISSUE_LOGIC-001 - Explicitly check for empty list
        if not valid_files or len(valid_files) == 0:
            raise ConfigurationError("No valid input files found")
        
        if missing_files:
            raise ConfigurationError(
                self.create_missing_files_error(missing_files)
            )
        
        # 2. Parse using patterns from file analysis
        all_items = []
        acceptable_nets = []
        open_nets = []
        errors = []
        
        # Patterns
        pattern_net = re.compile(r'^NET:\s+(.+)$')
        pattern_acceptable = re.compile(r'^-\s+only one pin\s*:\s*(\w+)\s+is connected to a physical wire\s*$')
        pattern_reason = re.compile(r'^-\s+(.+)$')
        
        for file_path in valid_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    current_net = None
                    current_net_line = 0
                    
                    for line_num, line in enumerate(f, 1):
                        line = line.rstrip()
                        
                        # Check for NET declaration
                        net_match = pattern_net.match(line)
                        if net_match:
                            current_net = net_match.group(1).strip()
                            current_net_line = line_num
                            continue
                        
                        # Check for reason line (must follow NET declaration)
                        reason_match = pattern_reason.match(line)
                        if reason_match and current_net:
                            reason = reason_match.group(1).strip()
                            
                            # Check if acceptable (single-pin physical wire)
                            acceptable_match = pattern_acceptable.match(line)
                            
                            net_item = {
                                'name': current_net,
                                'reason': reason,
                                'line_number': current_net_line,
                                'file_path': str(file_path),
                                'is_acceptable': acceptable_match is not None
                            }
                            
                            all_items.append(net_item)
                            
                            if acceptable_match:
                                acceptable_nets.append(net_item)
                            else:
                                open_nets.append(net_item)
                            
                            # Reset state for next net
                            current_net = None
                            current_net_line = 0
                    
                    # Check for incomplete parsing (NET without reason)
                    if current_net:
                        errors.append(f"Incomplete net entry at line {current_net_line} in {file_path}: {current_net}")
            
            except Exception as e:
                errors.append(f"Error parsing {file_path}: {str(e)}")
        
        # 3. Store on self for reuse
        self._parsed_items = all_items
        self._acceptable_nets = acceptable_nets
        self._open_nets = open_nets
        
        # 4. Return aggregated dict with items containing line_number and file_path
        return {
            'items': all_items,
            'acceptable_nets': acceptable_nets,
            'open_nets': open_nets,
            'metadata': {
                'total': len(all_items),
                'acceptable': len(acceptable_nets),
                'open': len(open_nets)
            },
            'errors': errors
        }
    
    # =========================================================================
    # Type 1: Boolean Check
    # =========================================================================
    
    def _execute_type1(self) -> CheckResult:
        """
        Type 1: Boolean Check.
        
        Check if physically open nets exist in the design.
        - found_items: Acceptable single-pin nets (INFO)
        - missing_items: Physically open nets (FAIL)
        
        Returns:
            CheckResult with is_pass based on check logic
        """
        # Parse input
        data = self._parse_input_files()
        acceptable_nets = data.get('acceptable_nets', [])
        open_nets = data.get('open_nets', [])
        
        # Convert to dict with metadata for source file/line display
        found_items = {
            f"{net['name']}": {
                'name': net['name'],
                'line_number': net.get('line_number', 0),
                'file_path': net.get('file_path', 'N/A')
            }
            for net in acceptable_nets
        }
        
        missing_items = [net['name'] for net in open_nets]
        
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
        
        Search pattern_items in input files (existence_check mode).
        - found_items: Pattern nets found in file
        - missing_items: Pattern nets NOT found in file
        
        Returns:
            CheckResult with is_pass based on value comparison
        """
        # Parse input
        data = self._parse_input_files()
        all_items = {item['name']: item for item in data.get('items', [])}
        
        # Get requirements
        pattern_items = self.item_data.get('requirements', {}).get('pattern_items', [])
        
        # existence_check mode: Check if pattern_items exist in input files
        found_items = {}
        missing_items = []
        
        for pattern in pattern_items:
            matched = False
            for item_name, item_data in all_items.items():
                # Support wildcard matching
                if '*' in pattern:
                    regex_pattern = pattern.replace('*', '.*')
                    if re.search(regex_pattern, item_name, re.IGNORECASE):
                        found_items[item_name] = {
                            'name': item_name,
                            'line_number': item_data.get('line_number', 0),
                            'file_path': item_data.get('file_path', 'N/A')
                        }
                        matched = True
                        break
                # Exact match
                elif pattern.lower() == item_name.lower():
                    found_items[item_name] = {
                        'name': item_name,
                        'line_number': item_data.get('line_number', 0),
                        'file_path': item_data.get('file_path', 'N/A')
                    }
                    matched = True
                    break
            
            if not matched:
                missing_items.append(pattern)
        
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
        Type 3: Value check with waiver support (Type 2 + waiver).
        
        Same pattern search logic as Type 2, plus waiver classification.
        - found_items: Pattern nets found in file (not waived)
        - waived_items: Pattern nets found AND waived
        - missing_items: Pattern nets NOT found in file
        
        Returns:
            CheckResult with FAIL for unwaived found items or missing items
        """
        # Parse input (same as Type 2)
        data = self._parse_input_files()
        all_items = {item['name']: item for item in data.get('items', [])}
        
        # Get requirements
        pattern_items = self.item_data.get('requirements', {}).get('pattern_items', [])
        
        # FIXED: KNOWN_ISSUE_API-016 - Use waivers.get() directly to preserve dict format
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # existence_check mode with waiver: Check if pattern_items exist in input files
        found_items = {}      # Found and NOT waived
        waived_items = {}     # FIXED: Use dict format {name: metadata}
        missing_items = []    # Not found
        
        for pattern in pattern_items:
            matched = False
            matched_item = None
            
            for item_name, item_data in all_items.items():
                # Support wildcard matching
                if '*' in pattern:
                    regex_pattern = pattern.replace('*', '.*')
                    if re.search(regex_pattern, item_name, re.IGNORECASE):
                        matched = True
                        matched_item = (item_name, item_data)
                        break
                # Exact match
                elif pattern.lower() == item_name.lower():
                    matched = True
                    matched_item = (item_name, item_data)
                    break
            
            if matched and matched_item:
                item_name, item_data = matched_item
                # Check if waived
                if self.match_waiver_entry(item_name, waive_dict) or self.match_waiver_entry(pattern, waive_dict):
                    waived_items[item_name] = {
                        'line_number': item_data.get('line_number', 0),
                        'file_path': item_data.get('file_path', 'N/A')
                    }
                else:
                    found_items[item_name] = {
                        'name': item_name,
                        'line_number': item_data.get('line_number', 0),
                        'file_path': item_data.get('file_path', 'N/A')
                    }
            else:
                missing_items.append(pattern)
        
        # FIXED: KNOWN_ISSUE_API-017 - Find unused waivers
        used_names = set(waived_items.keys())
        used_names.update(found_items.keys())
        unused_waivers = [name for name in waive_dict.keys() if name not in used_names]
        
        # Use template helper for automatic output formatting
        # Type 3: Use TYPE2_3 reason (emphasize "matched/satisfied") - API-026
        return self.build_complete_output(
            found_items=found_items,
            waived_items=waived_items,
            missing_items=missing_items,
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
        - found_items: Acceptable single-pin nets (INFO)
        - waived_items: Physically open nets that are waived
        - missing_items: Physically open nets that are NOT waived (FAIL)
        
        Returns:
            CheckResult with waiver logic applied
        """
        # Parse input
        data = self._parse_input_files()
        acceptable_nets = data.get('acceptable_nets', [])
        open_nets = data.get('open_nets', [])
        
        # Convert acceptable_nets to found_items
        found_items = {
            f"{net['name']}": {
                'name': net['name'],
                'line_number': net.get('line_number', 0),
                'file_path': net.get('file_path', 'N/A')
            }
            for net in acceptable_nets
        }
        
        # FIXED: KNOWN_ISSUE_API-016 - Use waivers.get() directly to preserve dict format
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # Separate waived/unwaived
        waived_items = {}  # FIXED: Use dict format {name: metadata}
        missing_items = []  # FIXED: KNOWN_ISSUE_API-021 - Use missing_items instead of unwaived_items
        
        for net in open_nets:
            net_name = net['name']
            if self.match_waiver_entry(net_name, waive_dict):
                waived_items[net_name] = {
                    'line_number': net.get('line_number', 0),
                    'file_path': net.get('file_path', 'N/A'),
                    'reason': net.get('reason', '')
                }
            else:
                missing_items.append(net_name)
        
        # FIXED: KNOWN_ISSUE_API-017 - waive_dict.keys() contains item names (strings)
        # waived_items is now a dict, so use .keys() to get used names
        used_names = set(waived_items.keys())
        unused_waivers = [name for name in waive_dict.keys() if name not in used_names]
        
        # FIXED: KNOWN_ISSUE_API-021 - Use missing_items parameter
        # Use template helper (auto-handles waiver=0)
        # Type 4: Use TYPE1_4 reason (emphasize "found/not found") - API-026
        return self.build_complete_output(
            found_items=found_items,
            waived_items=waived_items,
            missing_items=missing_items,
            waive_dict=waive_dict,
            unused_waivers=unused_waivers,
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
    checker = Check_9_0_0_04()
    checker.init_checker(Path(__file__))
    result = checker.execute_check()
    checker.write_output(result)
    return 0 if result.is_pass else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())