################################################################################
# Script Name: IMP-8-0-0-23.py
#
# Purpose:
#   confirm no unplaced cells in design.
#
# Logic:
#   - Parse input files: IMP-8-0-0-23_case0.rpt
#   - Check for special "0x0" marker indicating no unplaced cells (PASS condition)
#   - Extract hierarchical cell instance paths from report lines
#   - Split whitespace-separated tokens to handle multiple cells per line
#   - Validate cell paths contain '/' separator (hierarchical format)
#   - Deduplicate cell instances across multiple file mentions
#   - Count total unplaced cells across all input files
#   - For Type 1/4: PASS if "0x0" found or no cells extracted, FAIL otherwise
#   - For Type 2/3: Match cells against pattern_items, classify by placement status
#   - For Type 3/4: Apply waiver logic to separate waived/unwaived violations
#   - Handle edge cases: empty files, malformed paths, duplicate cells
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
# Refactored: 2025-12-24 (Using checker_templates v1.1.0)
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
class Check_8_0_0_23(InputFileParserMixin, OutputBuilderMixin, WaiverHandlerMixin, BaseChecker):
    """
    IMP-8-0-0-23: confirm no unplaced cells in design.
    
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
    FOUND_DESC_TYPE1_4 = "No unplaced cells found in design"
    MISSING_DESC_TYPE1_4 = "Unplaced cells detected in design"
    FOUND_REASON_TYPE1_4 = "0x0 indicator found - no unplaced cells detected in design"
    MISSING_REASON_TYPE1_4 = "Unplaced cell instance detected - placement incomplete"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_DESC_TYPE2_3 = "All cells successfully placed - 0x0 indicator matched"
    MISSING_DESC_TYPE2_3 = "Placement incomplete - unplaced cells found in design"
    FOUND_REASON_TYPE2_3 = "Placement status validated - 0x0 indicator matched, all cells placed successfully"
    MISSING_REASON_TYPE2_3 = "Cell placement status not satisfied - instance remains unplaced"
    
    # All Types (waiver description unified)
    WAIVED_DESC = "Waived unplaced cells (approved exceptions)"
    
    # Waiver parameters (Type 3/4 ONLY)
    WAIVED_BASE_REASON = "Unplaced cell waived per design team approval"
    UNUSED_WAIVER_REASON = "Waiver not matched - no corresponding unplaced cell found in report"
    
    def __init__(self):
        """Initialize the checker."""
        super().__init__(
            check_module="8.0_PHYSICAL_IMPLEMENTATION_CHECK",
            item_id="IMP-8-0-0-23",
            item_desc="confirm no unplaced cells in design."
        )
        # Custom member variables for parsed data
        self._parsed_items: List[Dict[str, Any]] = []
        self._placement_stats: Dict[str, int] = {}
        self._unplaced_cells: Dict[str, Dict[str, Any]] = {}
    
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
                details=[],
                summary=f"Checker execution failed: {str(e)}"
            )
    
    # =========================================================================
    # Input Parsing (Common for All Types)
    # =========================================================================
    
    def _parse_input_files(self) -> Dict[str, Any]:
        """
        Parse input files to extract placement status information.
        
        Parses placement report to identify:
        - Special "0x0" indicator (no unplaced cells)
        - Unplaced cell instances with hierarchical paths
        - Placement statistics if available
        
        Returns:
            Dict with parsed data:
            - 'items': List[Dict] - All parsed items (cells, statistics, errors)
            - 'unplaced_cells': Dict[str, Dict] - Unplaced cells with metadata
            - 'placement_stats': Dict[str, int] - Placement statistics
            - 'metadata': Dict - File metadata
            - 'errors': List - Parsing errors
        """
        # 1. Validate input files - IMPORTANT: returns tuple (valid_files_list, missing_files_list)
        valid_files, missing_files = self.validate_input_files()
        
        # Fix LOGIC-001: Explicitly check for empty list
        if missing_files:
            raise ConfigurationError(
                self.create_missing_files_error(missing_files)
            )
        if not valid_files or len(valid_files) == 0:
            raise ConfigurationError("No valid input files found")
        
        # 2. Initialize data structures
        all_items = []
        unplaced_cells = {}  # Dict to deduplicate by cell name
        placement_stats = {
            'total_cells': 0,
            'placed_cells': 0,
            'unplaced_cells': 0
        }
        errors = []
        placement_complete = False
        
        # 3. Define patterns for parsing
        # Pattern 1: Hierarchical instance path (slash-separated)
        hierarchical_path_pattern = re.compile(r'([^\s/]+(?:/[^\s/]+)+)')
        # Pattern 2: Special value "0x0" indicating no unplaced cells
        zero_indicator_pattern = re.compile(r'^\s*0x0\s*$')
        # Pattern 3: Whitespace-separated token splitter
        token_pattern = re.compile(r'\S+')
        
        # 4. Parse each file
        for file_path in valid_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    
                    # Check for empty file
                    if not content.strip():
                        # Empty file = no unplaced cells (PASS condition)
                        placement_stats['unplaced_cells'] = 0
                        placement_complete = True
                        all_items.append({
                            'name': 'Empty Report',
                            'line_number': 1,
                            'file_path': str(file_path),
                            'type': 'statistics',
                            'stats': {'unplaced_cells': 0},
                            'formatted': 'Placement Summary: Empty report (no unplaced cells)'
                        })
                        continue
                    
                    # Special format: "0x0" means 0 unplaced cells (shorthand notation)
                    if zero_indicator_pattern.match(content.strip()):
                        placement_stats['unplaced_cells'] = 0
                        placement_complete = True
                        all_items.append({
                            'name': '0x0',
                            'line_number': 1,
                            'file_path': str(file_path),
                            'type': 'statistics',
                            'stats': {'unplaced_cells': 0},
                            'formatted': 'Placement Summary: Unplaced cells: 0 (all cells placed)'
                        })
                        continue
                    
                    # Parse line by line to extract unplaced cell instances
                    lines = content.split('\n')
                    for line_num, line in enumerate(lines, 1):
                        line_stripped = line.strip()
                        if not line_stripped:
                            continue
                        
                        # Extract all whitespace-separated tokens
                        tokens = token_pattern.findall(line_stripped)
                        
                        for token in tokens:
                            # Validate token as hierarchical path (contains '/' separator)
                            if hierarchical_path_pattern.match(token):
                                # Extract cell name (leaf instance)
                                cell_name = token
                                
                                # Deduplicate by cell name
                                if cell_name not in unplaced_cells:
                                    unplaced_cells[cell_name] = {
                                        'name': cell_name,
                                        'line_number': line_num,
                                        'file_path': str(file_path),
                                        'type': 'unplaced_cell',
                                        'status': 'UNPLACED'
                                    }
                                    all_items.append(unplaced_cells[cell_name])
                    
                    # Update placement statistics based on unplaced cells found
                    if unplaced_cells:
                        placement_stats['unplaced_cells'] = len(unplaced_cells)
            
            except Exception as e:
                errors.append(f"Error parsing {file_path}: {str(e)}")
        
        # 5. Store frequently reused data on self
        self._parsed_items = all_items
        self._unplaced_cells = unplaced_cells
        self._placement_stats = placement_stats
        
        # 6. Return aggregated dict
        return {
            'items': all_items,
            'unplaced_cells': unplaced_cells,
            'placement_stats': placement_stats,
            'placement_complete': placement_complete,
            'metadata': {
                'total_items': len(all_items),
                'unplaced_count': len(unplaced_cells)
            },
            'errors': errors
        }
    
    # =========================================================================
    # Type 1: Boolean Check
    # =========================================================================
    
    def _execute_type1(self) -> CheckResult:
        """
        Type 1: Boolean Check.
        
        Check if any unplaced cells exist in the design.
        PASS if no unplaced cells found, FAIL otherwise.
        
        Returns:
            CheckResult with is_pass based on check logic
        """
        # Parse input
        data = self._parse_input_files()
        unplaced_cells = data.get('unplaced_cells', {})
        placement_stats = data.get('placement_stats', {})
        placement_complete = data.get('placement_complete', False)
        errors = data.get('errors', [])
        
        # Check for parsing errors
        if errors:
            missing_items = [f"Report parsing error: {err}" for err in errors]
            return self.build_complete_output(
                found_items={},
                missing_items=missing_items,
                found_desc=self.FOUND_DESC_TYPE1_4,
                missing_desc=self.MISSING_DESC_TYPE1_4,
                found_reason=self.FOUND_REASON_TYPE1_4,
                missing_reason=self.MISSING_REASON_TYPE1_4
            )
        
        # Determine pass/fail based on unplaced cells
        unplaced_count = placement_stats.get('unplaced_cells', 0)
        
        # PASS conditions:
        # 1. Explicit: unplaced_count = 0 in statistics
        # 2. Implicit: no unplaced cells found AND placement complete
        if unplaced_count == 0 and len(unplaced_cells) == 0:
            # All cells placed successfully
            found_items = {
                'All Cells Placed': {
                    'name': 'All Cells Placed',
                    'line_number': 0,
                    'file_path': 'N/A',
                    'total_cells': placement_stats.get('total_cells', 0),
                    'placed_cells': placement_stats.get('placed_cells', 0),
                    'unplaced_cells': 0
                }
            }
            missing_items = []
        elif len(unplaced_cells) == 0 and placement_complete:
            # Implicit pass: no unplaced cells mentioned and placement complete
            found_items = {
                'Placement Complete': {
                    'name': 'Placement Complete',
                    'line_number': 0,
                    'file_path': 'N/A',
                    'status': 'COMPLETE'
                }
            }
            missing_items = []
        else:
            # FAIL: unplaced cells detected
            found_items = {}
            missing_items = []
            
            # Add unplaced cells to missing_items
            for cell_name, cell_data in unplaced_cells.items():
                missing_items.append(cell_name)
            
            # If no specific cells but count > 0, add generic message
            if not missing_items and unplaced_count > 0:
                missing_items.append(f"{unplaced_count} unplaced cells detected")
        
        # Use template helper (Type 1: emphasize "found/not found")
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
        
        Check placement status of specific cells listed in pattern_items.
        This is a status_check mode: only output cells that match pattern_items.
        
        Returns:
            CheckResult with is_pass based on value comparison
        """
        # Parse input
        data = self._parse_input_files()
        all_items = data.get('items', [])
        unplaced_cells = data.get('unplaced_cells', {})
        
        # Get requirements
        pattern_items = self.item_data.get('requirements', {}).get('pattern_items', [])
        
        # status_check mode: Check status of items matching pattern_items
        found_items = {}      # Matched AND status correct (PLACED)
        missing_items = {}    # Matched BUT status wrong (UNPLACED)
        
        # Special case: pattern_items contains "0x0" (clean status indicator)
        if '0x0' in pattern_items:
            # Check if report shows "0x0" (no unplaced cells)
            has_0x0 = any(item.get('name') == '0x0' for item in all_items)
            
            if has_0x0 and len(unplaced_cells) == 0:
                # Report shows "0x0" - all cells placed
                found_items = {
                    '0x0': {
                        'name': '0x0',
                        'line_number': next((item.get('line_number', 0) for item in all_items if item.get('name') == '0x0'), 0),
                        'file_path': next((item.get('file_path', 'N/A') for item in all_items if item.get('name') == '0x0'), 'N/A')
                    }
                }
            else:
                # Report does NOT show "0x0" - unplaced cells exist
                for cell_name, cell_data in unplaced_cells.items():
                    missing_items[cell_name] = {
                        'name': cell_name,
                        'line_number': cell_data.get('line_number', 0),
                        'file_path': cell_data.get('file_path', 'N/A'),
                        'status': 'UNPLACED',
                        'cell_type': cell_data.get('cell_type', 'Unknown')
                    }
        else:
            # Normal pattern matching for specific cells
            for pattern in pattern_items:
                matched = False
                
                # Check if pattern matches any unplaced cell
                for cell_name, cell_data in unplaced_cells.items():
                    if pattern.lower() in cell_name.lower() or re.search(pattern, cell_name, re.IGNORECASE):
                        # Pattern matched, but cell is UNPLACED (status wrong)
                        missing_items[cell_name] = {
                            'name': cell_name,
                            'line_number': cell_data.get('line_number', 0),
                            'file_path': cell_data.get('file_path', 'N/A'),
                            'status': 'UNPLACED',
                            'cell_type': cell_data.get('cell_type', 'Unknown')
                        }
                        matched = True
                
                # Check in all items for placed cells
                if not matched:
                    for item in all_items:
                        item_name = item.get('name', '')
                        if pattern.lower() in item_name.lower() or re.search(pattern, item_name, re.IGNORECASE):
                            # Check if this is a cell with PLACED status
                            if item.get('type') == 'cell' and item.get('status') == 'PLACED':
                                found_items[item_name] = {
                                    'name': item_name,
                                    'line_number': item.get('line_number', 0),
                                    'file_path': item.get('file_path', 'N/A'),
                                    'status': 'PLACED'
                                }
                                matched = True
                                break
        
        # Use template helper (Type 2: emphasize "matched/satisfied")
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
        
        Check placement status with waiver classification.
        Unplaced cells can be waived if they match waiver patterns.
        
        Returns:
            CheckResult with FAIL for unwaived, INFO for waived items
        """
        # Parse input
        parsed_data = self._parse_input_files()
        unplaced_cells = parsed_data.get('unplaced_cells', {})
        
        # Fix API-016: Use waivers.get() directly to preserve dict format
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # Separate waived/unwaived using template helper
        waived_items = {}
        unwaived_items = {}
        
        for cell_name, cell_data in unplaced_cells.items():
            if self.match_waiver_entry(cell_name, waive_dict):
                waived_items[cell_name] = {
                    'name': cell_name,
                    'line_number': cell_data.get('line_number', 0),
                    'file_path': cell_data.get('file_path', 'N/A'),
                    'cell_type': cell_data.get('cell_type', 'Unknown')
                }
            else:
                unwaived_items[cell_name] = {
                    'name': cell_name,
                    'line_number': cell_data.get('line_number', 0),
                    'file_path': cell_data.get('file_path', 'N/A'),
                    'cell_type': cell_data.get('cell_type', 'Unknown')
                }
        
        # Fix API-017: waive_dict.keys() are item names (strings)
        used_names = set(waived_items.keys())
        unused_waivers = [name for name in waive_dict.keys() if name not in used_names]
        
        # Fix API-021: Use missing_items parameter instead of unwaived_items
        return self.build_complete_output(
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
        
        Check if unplaced cells exist, with waiver classification.
        
        Returns:
            CheckResult with waiver logic applied
        """
        # Parse input
        data = self._parse_input_files()
        unplaced_cells = data.get('unplaced_cells', {})
        placement_stats = data.get('placement_stats', {})
        errors = data.get('errors', [])
        
        # Fix API-016: Use waivers.get() directly to preserve dict format
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # Check for parsing errors
        if errors:
            missing_items = {}
            for err in errors:
                missing_items[f"Error: {err}"] = {
                    'name': f"Error: {err}",
                    'line_number': 0,
                    'file_path': 'N/A'
                }
            
            return self.build_complete_output(
                found_items={},
                missing_items=missing_items,
                waive_dict=waive_dict,
                has_waiver_value=True,
                found_desc=self.FOUND_DESC_TYPE1_4,
                missing_desc=self.MISSING_DESC_TYPE1_4,
                waived_desc=self.WAIVED_DESC,
                found_reason=self.FOUND_REASON_TYPE1_4,
                missing_reason=self.MISSING_REASON_TYPE1_4,
                waived_base_reason=self.WAIVED_BASE_REASON
            )
        
        # Separate waived/unwaived unplaced cells
        waived_items = {}
        unwaived_items = {}
        
        for cell_name, cell_data in unplaced_cells.items():
            if self.match_waiver_entry(cell_name, waive_dict):
                waived_items[cell_name] = {
                    'name': cell_name,
                    'line_number': cell_data.get('line_number', 0),
                    'file_path': cell_data.get('file_path', 'N/A'),
                    'cell_type': cell_data.get('cell_type', 'Unknown')
                }
            else:
                unwaived_items[cell_name] = {
                    'name': cell_name,
                    'line_number': cell_data.get('line_number', 0),
                    'file_path': cell_data.get('file_path', 'N/A'),
                    'cell_type': cell_data.get('cell_type', 'Unknown')
                }
        
        # Fix API-017: waive_dict.keys() are item names (strings)
        used_names = set(waived_items.keys())
        unused_waivers = [name for name in waive_dict.keys() if name not in used_names]
        
        # If no unwaived items, create found_items
        found_items = {}
        if not unwaived_items:
            found_items = {
                'All Cells Placed': {
                    'name': 'All Cells Placed (or waived)',
                    'line_number': 0,
                    'file_path': 'N/A',
                    'total_cells': placement_stats.get('total_cells', 0),
                    'placed_cells': placement_stats.get('placed_cells', 0),
                    'unplaced_cells': len(waived_items)
                }
            }
        
        # Fix API-021: Use missing_items parameter instead of unwaived_items
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
    checker = Check_8_0_0_23()
    checker.init_checker(Path(__file__))
    result = checker.execute_check()
    checker.write_output(result)
    return 0 if result.is_pass else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())