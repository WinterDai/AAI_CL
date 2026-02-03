################################################################################
# Script Name: IMP-15-0-0-00.py
#
# Purpose:
#   Confirm whether ESD PERC check is needed.
#
# Logic:
#   - Parse input files: IMP-7-0-0-00.rpt
#   - Extract design type information from the report
#   - Check if design type matches phy_top or tv_chip patterns
#   - Validate that design type is identified (phy_top or tv_chip)
#   - Determine if ESD PERC check is required based on design type
#   - Return PASS if design is phy_top OR tv_chip (ESD PERC check needed)
#   - Return FAIL if design is neither phy_top nor tv_chip (ESD PERC check not needed)
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
from checker_templates.input_file_parser_template import InputFileParserMixin


# MANDATORY: Inherit mixins in correct order (InputFileParserMixin first if used)
class Check_15_0_0_00(InputFileParserMixin, OutputBuilderMixin, WaiverHandlerMixin, BaseChecker):
    """
    IMP-15-0-0-00: Confirm whether ESD PERC check is needed.
    
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
    FOUND_DESC_TYPE1_4 = "Design type identified as requiring ESD PERC check"
    MISSING_DESC_TYPE1_4 = "Design type does not require ESD PERC check"
    FOUND_REASON_TYPE1_4 = "Design type is phy_top or tv_chip - ESD PERC check is needed"
    MISSING_REASON_TYPE1_4 = "Design type is neither phy_top nor tv_chip - ESD PERC check is not needed"
    
    # Type 2/3: Pattern checks - COPY EXACT VALUES FROM README!
    FOUND_DESC_TYPE2_3 = "Design types matched and require ESD PERC check"
    MISSING_DESC_TYPE2_3 = "Design types matched but do not require ESD PERC check"
    FOUND_REASON_TYPE2_3 = "Design type matched pattern and requires ESD PERC verification"
    MISSING_REASON_TYPE2_3 = "Design type matched pattern but does not satisfy ESD PERC requirements"
    
    # All Types (waiver description) - COPY EXACT VALUES FROM README!
    WAIVED_DESC = "Design types waived from ESD PERC check requirement"
    
    # Waiver parameters (Type 3/4 ONLY) - COPY EXACT VALUES FROM README!
    WAIVED_BASE_REASON = "Design type waived from ESD PERC check requirement"
    
    def __init__(self):
        """Initialize the checker."""
        super().__init__(
            check_module="15.0_ESD_PERC_CHECK",
            item_id="IMP-15-0-0-00",
            item_desc="Confirm whether ESD PERC check is needed."
        )
        # Custom member variables for parsed data
        self._parsed_items: List[Dict[str, Any]] = []
        self._design_type: Optional[str] = None
    
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
        Parse input files to extract design type information.
        
        Parses IMP-7-0-0-00.rpt to identify design type and determine if
        ESD PERC check is needed based on phy_top or tv_chip patterns.
        
        Returns:
            Dict with parsed data:
            - 'items': List[Dict] - Design type items found (with metadata)
            - 'metadata': Dict - File metadata
            - 'design_type': str - Identified design type
            - 'errors': List - Any parsing errors encountered
        """
        # 1. Validate input files - IMPORTANT: returns tuple (valid_files_list, missing_files_list)
        valid_files, missing_files = self.validate_input_files()
        if missing_files:
            raise ConfigurationError(
                self.create_missing_files_error(missing_files)
            )
        
        # FIXED: KNOWN_ISSUE_LOGIC-001 - Explicitly check for empty list
        if not valid_files or len(valid_files) == 0:
            raise ConfigurationError("No valid input files found")
        
        # 2. Parse using patterns from file analysis
        items = []
        design_type = None
        errors = []
        
        # Define patterns for design type identification
        patterns = {
            'phy_top_pattern1': r'design_type\s*:\s*\S*phy_top',
            'tv_chip_pattern': r'design_type\s*:\s*tv_chip',
            'alternative_pattern': r'(phy_top|tv_chip)'
        }
        
        for file_path in valid_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line_num, line in enumerate(f, 1):
                        # Check for phy_top pattern
                        match_phy_top = re.search(patterns['phy_top_pattern1'], line, re.IGNORECASE)
                        if match_phy_top:
                            design_type = 'phy_top'
                            items.append({
                                'name': 'phy_top',
                                'line_number': line_num,
                                'file_path': str(file_path),
                                'line_content': line.strip(),
                                'design_type': 'phy_top'
                            })
                            continue
                        
                        # Check for tv_chip pattern
                        match_tv_chip = re.search(patterns['tv_chip_pattern'], line, re.IGNORECASE)
                        if match_tv_chip:
                            design_type = 'tv_chip'
                            items.append({
                                'name': 'tv_chip',
                                'line_number': line_num,
                                'file_path': str(file_path),
                                'line_content': line.strip(),
                                'design_type': 'tv_chip'
                            })
                            continue
                        
                        # Check for alternative pattern
                        match_alt = re.search(patterns['alternative_pattern'], line, re.IGNORECASE)
                        if match_alt and not design_type:
                            matched_type = match_alt.group(1).lower()
                            design_type = matched_type
                            items.append({
                                'name': matched_type,
                                'line_number': line_num,
                                'file_path': str(file_path),
                                'line_content': line.strip(),
                                'design_type': matched_type
                            })
            except Exception as e:
                errors.append(f"Error parsing {file_path}: {str(e)}")
        
        # 3. Store frequently reused data on self
        self._parsed_items = items
        self._design_type = design_type
        
        return {
            'items': items,
            'metadata': {
                'total': len(items),
                'design_type': design_type
            },
            'design_type': design_type,
            'errors': errors
        }
    
    # =========================================================================
    # Type 1: Boolean Check
    # =========================================================================
    
    def _execute_type1(self) -> CheckResult:
        """
        Type 1: Boolean Check.
        
        Check if design type is phy_top or tv_chip (ESD PERC check needed).
        PASS if design is phy_top OR tv_chip.
        FAIL if design is neither phy_top nor tv_chip.
        
        Returns:
            CheckResult with is_pass based on check logic
        """
        # Parse input
        data = self._parse_input_files()
        items = data.get('items', [])
        design_type = data.get('design_type')
        
        # Check if design type requires ESD PERC check
        requires_esd_perc = design_type in ['phy_top', 'tv_chip']
        
        # Convert list to dict with metadata for source file/line display
        found_items = {}
        missing_items = []
        
        if requires_esd_perc and items:
            # Design type found and requires ESD PERC check
            for item in items:
                found_items[item['name']] = {
                    'name': item['name'],
                    'line_number': item.get('line_number', 0),
                    'file_path': item.get('file_path', 'N/A')
                }
        else:
            # Design type does not require ESD PERC check or not found
            if design_type:
                missing_items.append(f"Design type '{design_type}' does not require ESD PERC check")
            else:
                missing_items.append("No design type identified - ESD PERC check requirement unknown")
        
        # FIXED: API-002 - Use found_desc and missing_desc instead of item_desc
        return self.build_complete_output(
            found_items=found_items,
            missing_items=missing_items,
            found_desc=self.FOUND_DESC_TYPE1_4,
            missing_desc=self.MISSING_DESC_TYPE1_4
        )
    
    # =========================================================================
    # Type 2: Value Check
    # =========================================================================
    
    def _execute_type2(self) -> CheckResult:
        """
        Type 2: Value Check.
        
        Search pattern_items in input files (status_check mode).
        found_items = patterns matched AND require ESD PERC check.
        missing_items = patterns matched BUT do not require ESD PERC check.
        
        Returns:
            CheckResult with is_pass based on value comparison
        """
        # Parse input
        data = self._parse_input_files()
        all_items = {item['name']: item for item in data.get('items', [])}
        design_type = data.get('design_type')
        
        # Get requirements
        pattern_items = self.item_data.get('requirements', {}).get('pattern_items', [])
        
        # status_check mode: Check status of items matching pattern_items
        found_items = {}      # Matched AND status correct (requires ESD PERC)
        missing_items = []    # Matched BUT status wrong (does not require ESD PERC)
        missing_patterns = []  # Pattern not matched at all
        
        for pattern in pattern_items:
            matched = False
            for item_name, item_data in all_items.items():
                if pattern.lower() in item_name.lower():
                    # Check if design type requires ESD PERC check
                    if item_data.get('design_type') in ['phy_top', 'tv_chip']:
                        # Status correct - requires ESD PERC
                        found_items[item_name] = {
                            'name': item_name,
                            'line_number': item_data.get('line_number', 0),
                            'file_path': item_data.get('file_path', 'N/A')
                        }
                    else:
                        # Status wrong - does not require ESD PERC
                        missing_items.append(item_name)
                    matched = True
                    break
            if not matched:
                missing_patterns.append(pattern)
        
        # If no patterns matched, add to missing_items
        if missing_patterns:
            missing_items.extend(missing_patterns)
        
        # FIXED: API-002 - Use found_desc and missing_desc instead of item_desc
        return self.build_complete_output(
            found_items=found_items,
            missing_items=missing_items,
            found_desc=self.FOUND_DESC_TYPE2_3,
            missing_desc=self.MISSING_DESC_TYPE2_3
        )
    
    # =========================================================================
    # Type 3: Value Check with Waiver Logic
    # =========================================================================
    
    def _execute_type3(self) -> CheckResult:
        """
        Type 3: Value check with waiver support.
        
        Same pattern search logic as Type 2 (status_check mode), plus waiver classification.
        
        Returns:
            CheckResult with FAIL for unwaived, INFO for waived items
        """
        # Parse input
        parsed_data = self._parse_input_files()
        all_items = {item['name']: item for item in parsed_data.get('items', [])}
        
        # FIXED: KNOWN_ISSUE_API-016 - Use waivers.get() directly to preserve dict format
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # Get requirements
        pattern_items = self.item_data.get('requirements', {}).get('pattern_items', [])
        
        # status_check mode: Check status of items matching pattern_items
        found_items = {}      # Matched AND status correct (requires ESD PERC, not waived)
        waived_items = {}     # Matched AND status correct but waived
        missing_items = []    # Matched BUT status wrong (does not require ESD PERC)
        
        for pattern in pattern_items:
            for item_name, item_data in all_items.items():
                if pattern.lower() in item_name.lower():
                    # Check if design type requires ESD PERC check
                    if item_data.get('design_type') in ['phy_top', 'tv_chip']:
                        # Status correct - requires ESD PERC
                        item_dict = {
                            'name': item_name,
                            'line_number': item_data.get('line_number', 0),
                            'file_path': item_data.get('file_path', 'N/A')
                        }
                        
                        # Check if waived
                        if self.match_waiver_entry(item_name, waive_dict):
                            waived_items[item_name] = item_dict
                        else:
                            found_items[item_name] = item_dict
                    else:
                        # Status wrong - does not require ESD PERC
                        missing_items.append(item_name)
                    break
        
        # Find unused waivers
        used_names = set(waived_items.keys())
        used_names.update(found_items.keys())
        unused_waivers = [name for name in waive_dict.keys() if name not in used_names]
        
        # FIXED: API-002 - Use found_desc and missing_desc instead of item_desc
        return self.build_complete_output(
            found_items=found_items,
            waived_items=waived_items,
            missing_items=missing_items,
            waive_dict=waive_dict,
            unused_waivers=unused_waivers,
            found_desc=self.FOUND_DESC_TYPE2_3,
            missing_desc=self.MISSING_DESC_TYPE2_3
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
        design_type = data.get('design_type')
        
        # FIXED: KNOWN_ISSUE_API-016 - Use waivers.get() directly to preserve dict format
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # Check if design type requires ESD PERC check
        requires_esd_perc = design_type in ['phy_top', 'tv_chip']
        
        # Separate waived/unwaived items
        found_items = {}
        waived_items = {}
        missing_items = []
        
        if requires_esd_perc and items:
            # Design type found and requires ESD PERC check
            for item in items:
                item_dict = {
                    'name': item['name'],
                    'line_number': item.get('line_number', 0),
                    'file_path': item.get('file_path', 'N/A')
                }
                
                # Check if waived
                if self.match_waiver_entry(item['name'], waive_dict):
                    waived_items[item['name']] = item_dict
                else:
                    found_items[item['name']] = item_dict
        else:
            # Design type does not require ESD PERC check or not found
            if design_type:
                missing_items.append(f"Design type '{design_type}' does not require ESD PERC check")
            else:
                missing_items.append("No design type identified - ESD PERC check requirement unknown")
        
        # Find unused waivers
        used_names = set(waived_items.keys())
        used_names.update(found_items.keys())
        unused_waivers = [name for name in waive_dict.keys() if name not in used_names]
        
        # FIXED: API-002 - Use found_desc and missing_desc instead of item_desc
        return self.build_complete_output(
            found_items=found_items,
            waived_items=waived_items,
            missing_items=missing_items,
            waive_dict=waive_dict,
            unused_waivers=unused_waivers,
            found_desc=self.FOUND_DESC_TYPE1_4,
            missing_desc=self.MISSING_DESC_TYPE1_4
        )


# =========================================================================
# Entry Point
# =========================================================================

def main():
    """Main entry point."""
    checker = Check_15_0_0_00()
    checker.init_checker(Path(__file__))
    result = checker.execute_check()
    checker.write_output(result)
    return 0 if result.is_pass else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())