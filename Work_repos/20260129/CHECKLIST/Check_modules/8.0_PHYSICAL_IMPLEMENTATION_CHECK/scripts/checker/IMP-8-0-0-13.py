################################################################################
# Script Name: IMP-8-0-0-13.py
#
# Purpose:
#   Confirm proper clock tree buffer/inverter types are used. Provide a list in comment field.
#
# Logic:
#   - Parse input files: IMP-8-0-0-13.rpt
#   - Read CTS library specification file line-by-line
#   - Tokenize each line by whitespace to extract individual cell names
#   - Apply regex patterns to identify and categorize cells:
#     * Clock buffers (DCCKND*) with drive strength extraction
#     * Clock inverters (CKND2D*) with drive strength extraction
#     * Clock gates (CKL*QD*) preserving wildcards
#     * Clock logic cells (CKAN2D*, CKMUX2D*, etc.) with logic type extraction
#   - Group cells by category (buffer/inverter/gate/logic) and drive strength
#   - Aggregate results if multiple files provided, removing duplicates
#   - Validate for empty files or non-standard cell types
#   - Generate comprehensive inventory with category labels and drive strength indicators
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
class Check_8_0_0_13(InputFileParserMixin, OutputBuilderMixin, WaiverHandlerMixin, BaseChecker):
    """
    IMP-8-0-0-13: Confirm proper clock tree buffer/inverter types are used. Provide a list in comment field.
    
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
    FOUND_DESC_TYPE1_4 = "Clock tree buffer/inverter cell types found in CTS library specification"
    MISSING_DESC_TYPE1_4 = "CTS library specification not found or empty"
    FOUND_REASON_TYPE1_4 = "Clock tree cell types found and categorized in CTS library specification"
    MISSING_REASON_TYPE1_4 = "CTS library specification file not found or contains no valid cell definitions"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_DESC_TYPE2_3 = "Required clock tree cell types matched in CTS library"
    MISSING_DESC_TYPE2_3 = "Expected clock tree cell types not found in CTS library"
    FOUND_REASON_TYPE2_3 = "Required clock tree cell type matched and validated in CTS library specification"
    MISSING_REASON_TYPE2_3 = "Expected clock tree cell type not found in CTS library specification"
    
    # All Types (waiver description unified)
    WAIVED_DESC = "Waived clock tree cell type violations"
    
    # Waiver parameters (Type 3/4 ONLY)
    WAIVED_BASE_REASON = "Clock tree cell type violation waived per design approval"
    
    def __init__(self):
        """Initialize the checker."""
        super().__init__(
            check_module="8.0_PHYSICAL_IMPLEMENTATION_CHECK",
            item_id="IMP-8-0-0-13",
            item_desc="Confirm proper clock tree buffer/inverter types are used. Provide a list in comment field."
        )
        # Custom member variables for parsed data
        self._parsed_items: List[Dict[str, Any]] = []
        self._cell_categories: Dict[str, List[Dict[str, Any]]] = {
            'buffers': [],
            'inverters': [],
            'clock_gates': [],
            'logic_cells': []
        }
    
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
        Parse input files to extract CTS cell library specifications.
        
        Parses the CTS library specification file to extract:
        - Clock buffers (DCCKND*) with drive strength
        - Clock inverters (CKND2D*) with drive strength
        - Clock gates (CKL*QD*) with wildcards preserved
        - Clock logic cells (CKAN2D*, CKMUX2D*, etc.) with logic type
        
        Returns:
            Dict with parsed data:
            - 'items': List[Dict] - All CTS cells with metadata (line_number, file_path, category, drive_strength)
            - 'metadata': Dict - Aggregated statistics (total cells, cells by category)
            - 'errors': List - Any parsing errors encountered
        """
        # 1. Validate input files - IMPORTANT: returns tuple (valid_files_list, missing_files_list)
        valid_files, missing_files = self.validate_input_files()
        
        # FIXED: KNOWN_ISSUE_LOGIC-001 - Explicitly check for empty list
        if not valid_files or len(valid_files) == 0:
            raise ConfigurationError("No valid input files found")
        
        # 2. Define regex patterns for CTS cell types
        patterns = {
            'buffer': re.compile(r'(DCCKND(\d+)BWP\d+H\d+P\d+PD[UL]LVT)'),
            'inverter': re.compile(r'(CKND2D(\d+)BWP\d+H\d+P\d+PD[UL]LVT)'),
            'clock_gate': re.compile(r'(CKL\*QD(\d+)\*H\d+\*[UL]LVT)'),
            'logic_and': re.compile(r'(CKAN2D(\d+)BWP\d+H\d+P\d+PD[UL]LVT)'),
            'logic_mux': re.compile(r'(CKMUX2D(\d+)BWP\d+H\d+P\d+PD[UL]LVT)'),
            'logic_xor': re.compile(r'(CKXOR2D(\d+)BWP\d+H\d+P\d+PD[UL]LVT)'),
            'logic_or': re.compile(r'(CKOR2D(\d+)BWP\d+H\d+P\d+PD[UL]LVT)'),
            'logic_nor': re.compile(r'(CKNR2D(\d+)BWP\d+H\d+P\d+PD[UL]LVT)')
        }
        
        # 3. Parse files
        all_items = []
        seen_cells = set()  # For duplicate removal across files
        errors = []
        
        for file_path in valid_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line_num, line in enumerate(f, 1):
                        # Skip empty lines
                        if not line.strip():
                            continue
                        
                        # Tokenize line by whitespace
                        tokens = line.split()
                        
                        for token in tokens:
                            # Skip if already seen (duplicate removal)
                            if token in seen_cells:
                                continue
                            
                            # Try to match against each pattern
                            matched = False
                            
                            # Check buffer pattern
                            match = patterns['buffer'].search(token)
                            if match:
                                cell_name = match.group(1)
                                drive_strength = match.group(2)
                                all_items.append({
                                    'name': cell_name,
                                    'category': 'buffer',
                                    'drive_strength': drive_strength,
                                    'line_number': line_num,
                                    'file_path': str(file_path)
                                })
                                seen_cells.add(token)
                                matched = True
                                continue
                            
                            # Check inverter pattern
                            match = patterns['inverter'].search(token)
                            if match:
                                cell_name = match.group(1)
                                drive_strength = match.group(2)
                                all_items.append({
                                    'name': cell_name,
                                    'category': 'inverter',
                                    'drive_strength': drive_strength,
                                    'line_number': line_num,
                                    'file_path': str(file_path)
                                })
                                seen_cells.add(token)
                                matched = True
                                continue
                            
                            # Check clock gate pattern (with wildcards)
                            match = patterns['clock_gate'].search(token)
                            if match:
                                cell_name = match.group(1)
                                drive_strength = match.group(2)
                                all_items.append({
                                    'name': cell_name,
                                    'category': 'clock_gate',
                                    'drive_strength': drive_strength,
                                    'line_number': line_num,
                                    'file_path': str(file_path)
                                })
                                seen_cells.add(token)
                                matched = True
                                continue
                            
                            # Check logic cell patterns
                            for logic_type, pattern in [
                                ('logic_and', patterns['logic_and']),
                                ('logic_mux', patterns['logic_mux']),
                                ('logic_xor', patterns['logic_xor']),
                                ('logic_or', patterns['logic_or']),
                                ('logic_nor', patterns['logic_nor'])
                            ]:
                                match = pattern.search(token)
                                if match:
                                    cell_name = match.group(1)
                                    drive_strength = match.group(2)
                                    all_items.append({
                                        'name': cell_name,
                                        'category': logic_type,
                                        'drive_strength': drive_strength,
                                        'line_number': line_num,
                                        'file_path': str(file_path)
                                    })
                                    seen_cells.add(token)
                                    matched = True
                                    break
                            
            except Exception as e:
                errors.append(f"Error parsing {file_path}: {str(e)}")
        
        # 4. Categorize cells for metadata
        categorized = {
            'buffers': [item for item in all_items if item['category'] == 'buffer'],
            'inverters': [item for item in all_items if item['category'] == 'inverter'],
            'clock_gates': [item for item in all_items if item['category'] == 'clock_gate'],
            'logic_cells': [item for item in all_items if item['category'].startswith('logic_')]
        }
        
        # 5. Store on self
        self._parsed_items = all_items
        self._cell_categories = categorized
        
        # 6. Return aggregated dict
        return {
            'items': all_items,
            'metadata': {
                'total': len(all_items),
                'buffers': len(categorized['buffers']),
                'inverters': len(categorized['inverters']),
                'clock_gates': len(categorized['clock_gates']),
                'logic_cells': len(categorized['logic_cells'])
            },
            'errors': errors
        }
    
    # =========================================================================
    # Type 1: Boolean Check
    # =========================================================================
    
    def _execute_type1(self) -> CheckResult:
        """
        Type 1: Boolean Check.
        
        Validates that CTS library specification file exists and contains valid cell definitions.
        Provides comprehensive inventory of all clock tree cell types found.
        
        Returns:
            CheckResult with is_pass based on whether valid CTS cells were found
        """
        # Parse input
        data = self._parse_input_files()
        items = data.get('items', [])
        metadata = data.get('metadata', {})
        
        # Convert list to dict with metadata for source file/line display
        found_items = {
            f"{item['name']} (Category: {item['category']}, Drive: D{item['drive_strength']})": {
                'name': f"{item['name']} (Category: {item['category']}, Drive: D{item['drive_strength']})",
                'line_number': item.get('line_number', 0),
                'file_path': item.get('file_path', 'N/A')
            }
            for item in items
        } if items else {}
        
        missing_items = [] if found_items else ['CTS library specification with valid cell definitions']
        
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
        
        Searches for required clock tree cell types (pattern_items) in CTS library specification.
        Uses existence_check mode: pattern_items are cells that SHOULD EXIST in the library.
        
        Returns:
            CheckResult with is_pass based on whether all required cells were found
        """
        # Parse input
        data = self._parse_input_files()
        items = data.get('items', [])
        
        # Get requirements
        pattern_items = self.item_data.get('requirements', {}).get('pattern_items', [])
        
        # Build lookup dict for parsed items
        parsed_cells = {item['name'].lower(): item for item in items}
        
        # existence_check mode: Check if pattern_items exist in parsed cells
        found_items = {}
        missing_items = []
        
        for pattern in pattern_items:
            pattern_lower = pattern.lower()
            matched = False
            
            # Try exact match first
            if pattern_lower in parsed_cells:
                item = parsed_cells[pattern_lower]
                found_items[item['name']] = {
                    'name': item['name'],
                    'line_number': item.get('line_number', 0),
                    'file_path': item.get('file_path', 'N/A')
                }
                matched = True
            else:
                # Try wildcard/partial match
                for cell_name, item in parsed_cells.items():
                    if pattern_lower in cell_name or self._wildcard_match(pattern_lower, cell_name):
                        found_items[item['name']] = {
                            'name': item['name'],
                            'line_number': item.get('line_number', 0),
                            'file_path': item.get('file_path', 'N/A')
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
        Type 3: Value check with waiver support.
        
        Same pattern search logic as Type 2, plus waiver classification.
        Searches for required clock tree cell types and allows waiving missing cells.
        
        Returns:
            CheckResult with FAIL for unwaived missing cells, INFO for waived items
        """
        # Parse input
        parsed_data = self._parse_input_files()
        items = parsed_data.get('items', [])
        
        # FIXED: KNOWN_ISSUE_API-016 - Use waivers.get() directly to preserve dict format
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # Get requirements
        pattern_items = self.item_data.get('requirements', {}).get('pattern_items', [])
        
        # Build lookup dict for parsed items
        parsed_cells = {item['name'].lower(): item for item in items}
        
        # Find missing cells (violations)
        violations = []
        found_items = {}
        
        for pattern in pattern_items:
            pattern_lower = pattern.lower()
            matched = False
            
            # Try exact match first
            if pattern_lower in parsed_cells:
                item = parsed_cells[pattern_lower]
                found_items[item['name']] = {
                    'name': item['name'],
                    'line_number': item.get('line_number', 0),
                    'file_path': item.get('file_path', 'N/A')
                }
                matched = True
            else:
                # Try wildcard/partial match
                for cell_name, item in parsed_cells.items():
                    if pattern_lower in cell_name or self._wildcard_match(pattern_lower, cell_name):
                        found_items[item['name']] = {
                            'name': item['name'],
                            'line_number': item.get('line_number', 0),
                            'file_path': item.get('file_path', 'N/A')
                        }
                        matched = True
                        break
            
            if not matched:
                violations.append(pattern)
        
        # Separate waived/unwaived using template helper
        waived_items = []
        unwaived_items = []
        
        for violation in violations:
            if self.match_waiver_entry(violation, waive_dict):
                waived_items.append(violation)
            else:
                unwaived_items.append(violation)
        
        # FIXED: KNOWN_ISSUE_API-017 - Use waive_dict.keys() to get item names
        used_names = set(waived_items)
        unused_waivers = [name for name in waive_dict.keys() if name not in used_names]
        
        # FIXED: KNOWN_ISSUE_API-021 - Use missing_items parameter instead of unwaived_items
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
        
        Validates CTS library specification exists with waiver support for missing/invalid cells.
        
        Returns:
            CheckResult with waiver logic applied
        """
        # Parse input
        data = self._parse_input_files()
        items = data.get('items', [])
        
        # FIXED: KNOWN_ISSUE_API-016 - Use waivers.get() directly to preserve dict format
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # Convert list to dict with metadata
        found_items = {
            f"{item['name']} (Category: {item['category']}, Drive: D{item['drive_strength']})": {
                'name': f"{item['name']} (Category: {item['category']}, Drive: D{item['drive_strength']})",
                'line_number': item.get('line_number', 0),
                'file_path': item.get('file_path', 'N/A')
            }
            for item in items
        } if items else {}
        
        # Check if library is missing/empty (violation)
        violations = [] if found_items else ['CTS library specification with valid cell definitions']
        
        # Separate waived/unwaived
        waived_items = []
        unwaived_items = []
        
        for violation in violations:
            if self.match_waiver_entry(violation, waive_dict):
                waived_items.append(violation)
            else:
                unwaived_items.append(violation)
        
        # FIXED: KNOWN_ISSUE_API-017 - Use waive_dict.keys() to get item names
        used_names = set(waived_items)
        unused_waivers = [name for name in waive_dict.keys() if name not in used_names]
        
        # FIXED: KNOWN_ISSUE_API-021 - Use missing_items parameter instead of unwaived_items
        # Type 4: Use TYPE1_4 reason (emphasize "found/not found") - API-026
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
    # Helper Methods
    # =========================================================================
    
    def _wildcard_match(self, pattern: str, text: str) -> bool:
        """
        Check if text matches pattern with wildcard support.
        
        Args:
            pattern: Pattern with * wildcards
            text: Text to match against
            
        Returns:
            True if text matches pattern
        """
        if '*' not in pattern:
            return pattern == text
        
        # Convert wildcard pattern to regex
        regex_pattern = pattern.replace('*', '.*')
        return bool(re.match(f'^{regex_pattern}$', text, re.IGNORECASE))


# =========================================================================
# Entry Point
# =========================================================================

def main():
    """Main entry point."""
    checker = Check_8_0_0_13()
    checker.init_checker(Path(__file__))
    result = checker.execute_check()
    checker.write_output(result)
    return 0 if result.is_pass else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())