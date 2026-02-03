################################################################################
# Script Name: IMP-8-0-0-15.py
#
# Purpose:
#   Confirm clock tree VT requirements were met.
#
# Logic:
#   - Parse clock_cells_with_cell_type.txt to extract instance paths and cell types
#   - Parse IMP-8-0-0-14.rpt to extract clock tree hierarchies and cell instances
#   - Extract VT types (ULVT/LVT/SVT/HVT) from cell names using regex patterns
#   - Aggregate VT statistics per clock tree and across all cells
#   - Validate VT types against requirements (typically LVT/ULVT only allowed)
#   - Report violations where cells use incorrect VT types (SVT/HVT)
#   - Track cell functions (clock gates, buffers, inverters, flip-flops)
#   - Generate summary statistics with VT breakdown and percentages
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
class Check_8_0_0_15(InputFileParserMixin, OutputBuilderMixin, WaiverHandlerMixin, BaseChecker):
    """
    IMP-8-0-0-15: Confirm clock tree VT requirements were met.
    
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
    FOUND_DESC_TYPE1_4 = "Clock tree cells with compliant VT types found"
    MISSING_DESC_TYPE1_4 = "Clock tree cells with non-compliant VT types detected"
    FOUND_REASON_TYPE1_4 = "Clock tree cell uses compliant VT type (LVT/ULVT)"
    MISSING_REASON_TYPE1_4 = "Clock tree cell uses non-compliant VT type (SVT/HVT/UNKNOWN)"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_DESC_TYPE2_3 = "Clock tree cells matching VT requirements"
    MISSING_DESC_TYPE2_3 = "Clock tree cells violating VT requirements"
    FOUND_REASON_TYPE2_3 = "Cell VT type matches requirement and is validated"
    MISSING_REASON_TYPE2_3 = "Cell VT type does not satisfy requirement or is missing"
    
    # All Types (waiver description unified)
    WAIVED_DESC = "Waived clock tree VT violations"
    
    # Waiver parameters (Type 3/4 ONLY)
    WAIVED_BASE_REASON = "Clock tree VT violation waived per design approval"
    
    def __init__(self):
        """Initialize the checker."""
        super().__init__(
            check_module="8.0_PHYSICAL_IMPLEMENTATION_CHECK",
            item_id="IMP-8-0-0-15",
            item_desc="Confirm clock tree VT requirements were met."
        )
        # Custom member variables for parsed data
        self._parsed_items: List[Dict[str, Any]] = []
        self._vt_statistics: Dict[str, Dict[str, int]] = {}
        self._clock_trees: Dict[str, List[Dict[str, Any]]] = {}
    
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
        Parse input files to extract clock tree cell VT information.
        
        Parses:
        1. clock_cells_with_cell_type.txt - Cell instances with types
        2. IMP-8-0-0-14.rpt - Clock tree hierarchy report
        
        Returns:
            Dict with parsed data:
            - 'items': List[Dict] - All clock cells with VT info
            - 'metadata': Dict - Statistics and summary info
            - 'errors': List - Parsing errors
        """
        # 1. Validate input files (raises ConfigurationError if missing)
        valid_files, missing_files = self.validate_input_files()
        if not valid_files or len(valid_files) == 0:
            raise ConfigurationError("No valid input files found")
        
        # 2. Initialize data structures
        all_items = []
        vt_counts = {'ULVT': 0, 'LVT': 0, 'SVT': 0, 'RVT': 0, 'HVT': 0, 'UNKNOWN': 0}
        clock_trees = {}
        current_clock_tree = None
        errors = []
        
        # 3. Define VT extraction patterns
        vt_patterns = {
            'ULVT': re.compile(r'(ULVT)(?:\s|$)'),
            'LVT': re.compile(r'(?<!U)(LVT)(?:\s|$)'),
            'SVT': re.compile(r'(SVT)(?:\s|$)'),
            'RVT': re.compile(r'(RVT)(?:\s|$)'),
            'HVT': re.compile(r'(HVT)(?:\s|$)'),
        }
        
        # 4. Parse each input file
        for file_path in valid_files:
            file_name = Path(file_path).name
            
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line_num, line in enumerate(f, 1):
                        line = line.strip()
                        if not line:
                            continue
                        
                        # Parse clock_cells_with_cell_type.txt
                        if 'clock_cells_with_cell_type.txt' in file_name:
                            # Pattern: instance_path : CELL_TYPE
                            match = re.match(r'^([^:]+)\s*:\s*(\S+)\s*$', line)
                            if match:
                                instance_path = match.group(1).strip()
                                cell_type = match.group(2).strip()
                                
                                # Extract VT type from cell name
                                vt_type = self._extract_vt_type(cell_type, vt_patterns)
                                
                                # Determine cell function
                                cell_function = self._determine_cell_function(instance_path, cell_type)
                                
                                item = {
                                    'name': f"{instance_path} : {cell_type}",
                                    'instance_path': instance_path,
                                    'cell_type': cell_type,
                                    'vt_type': vt_type,
                                    'cell_function': cell_function,
                                    'line_number': line_num,
                                    'file_path': str(file_path),
                                    'clock_tree': 'global'  # Default to global
                                }
                                
                                all_items.append(item)
                                vt_counts[vt_type] += 1
                        
                        # Parse IMP-8-0-0-14.rpt
                        elif 'IMP-8-0-0-14.rpt' in file_name:
                            # Clock tree header
                            clock_tree_match = re.match(r'^(Generated )?[Cc]lock tree ([^:]+):', line)
                            if clock_tree_match:
                                current_clock_tree = clock_tree_match.group(2).strip()
                                if current_clock_tree not in clock_trees:
                                    clock_trees[current_clock_tree] = []
                                continue
                            
                            # Cell instance with VT type and level
                            cell_match = re.search(
                                r'\(L(\d+)\)\s+([^/\s]+)/([A-Z]+)\s*->\s*([A-Z]+)\s*\(([A-Z0-9]+BWP[^)]+PD(ULVT|LVT|RVT|SLVT|HVT))\)',
                                line
                            )
                            if cell_match and current_clock_tree:
                                level = cell_match.group(1)
                                instance_name = cell_match.group(2)
                                cell_type = cell_match.group(5)
                                vt_type = cell_match.group(6)
                                
                                # Normalize VT type (SLVT -> SVT)
                                if vt_type == 'SLVT':
                                    vt_type = 'SVT'
                                
                                cell_function = self._determine_cell_function(instance_name, cell_type)
                                
                                item = {
                                    'name': f"{current_clock_tree}: {instance_name} (L{level})",
                                    'instance_path': instance_name,
                                    'cell_type': cell_type,
                                    'vt_type': vt_type,
                                    'cell_function': cell_function,
                                    'level': int(level),
                                    'clock_tree': current_clock_tree,
                                    'line_number': line_num,
                                    'file_path': str(file_path)
                                }
                                
                                all_items.append(item)
                                clock_trees[current_clock_tree].append(item)
                                vt_counts[vt_type] += 1
                                continue
                            
                            # CTS-generated cell instance
                            cts_match = re.search(
                                r'\(L(\d+)\)\s+(CTS_[^/\s]+)/([A-Z]+)\s*->\s*([A-Z]+)\s*\(([A-Z0-9]+BWP[^)]+PD(ULVT|LVT|RVT|SLVT|HVT))\)',
                                line
                            )
                            if cts_match and current_clock_tree:
                                level = cts_match.group(1)
                                instance_name = cts_match.group(2)
                                cell_type = cts_match.group(5)
                                vt_type = cts_match.group(6)
                                
                                if vt_type == 'SLVT':
                                    vt_type = 'SVT'
                                
                                cell_function = 'cts_buffer_inverter'
                                
                                item = {
                                    'name': f"{current_clock_tree}: {instance_name} (L{level})",
                                    'instance_path': instance_name,
                                    'cell_type': cell_type,
                                    'vt_type': vt_type,
                                    'cell_function': cell_function,
                                    'level': int(level),
                                    'clock_tree': current_clock_tree,
                                    'line_number': line_num,
                                    'file_path': str(file_path)
                                }
                                
                                all_items.append(item)
                                clock_trees[current_clock_tree].append(item)
                                vt_counts[vt_type] += 1
                                continue
                            
                            # Flip-flop endpoint with VT type
                            ff_match = re.search(
                                r'\(L(\d+)\)\s+([^/\s]+)/CP\s*\(([A-Z0-9]+BWP[^)]+PD(ULVT|LVT|RVT|SLVT|HVT))\)',
                                line
                            )
                            if ff_match and current_clock_tree:
                                level = ff_match.group(1)
                                instance_name = ff_match.group(2)
                                cell_type = ff_match.group(3)
                                vt_type = ff_match.group(4)
                                
                                if vt_type == 'SLVT':
                                    vt_type = 'SVT'
                                
                                cell_function = 'flip_flop'
                                
                                item = {
                                    'name': f"{current_clock_tree}: {instance_name} (L{level})",
                                    'instance_path': instance_name,
                                    'cell_type': cell_type,
                                    'vt_type': vt_type,
                                    'cell_function': cell_function,
                                    'level': int(level),
                                    'clock_tree': current_clock_tree,
                                    'line_number': line_num,
                                    'file_path': str(file_path)
                                }
                                
                                all_items.append(item)
                                clock_trees[current_clock_tree].append(item)
                                vt_counts[vt_type] += 1
            
            except Exception as e:
                errors.append(f"Error parsing {file_path}: {str(e)}")
        
        # 5. Store frequently reused data on self
        self._parsed_items = all_items
        self._vt_statistics = vt_counts
        self._clock_trees = clock_trees
        
        # 6. Calculate metadata
        total_cells = len(all_items)
        metadata = {
            'total_cells': total_cells,
            'vt_counts': vt_counts,
            'vt_percentages': {
                vt: (count / total_cells * 100 if total_cells > 0 else 0)
                for vt, count in vt_counts.items()
            },
            'clock_tree_count': len(clock_trees),
            'clock_trees': list(clock_trees.keys())
        }
        
        return {
            'items': all_items,
            'metadata': metadata,
            'errors': errors
        }
    
    def _extract_vt_type(self, cell_name: str, vt_patterns: Dict[str, re.Pattern]) -> str:
        """
        Extract VT type from cell name using regex patterns.
        
        Args:
            cell_name: Cell type name
            vt_patterns: Dict of VT type to regex pattern
            
        Returns:
            VT type string (ULVT, LVT, SVT, RVT, HVT, or UNKNOWN)
        """
        # Check in priority order: ULVT > LVT > SVT > RVT > HVT
        for vt_type in ['ULVT', 'LVT', 'SVT', 'RVT', 'HVT']:
            if vt_patterns[vt_type].search(cell_name):
                return vt_type
        return 'UNKNOWN'
    
    def _determine_cell_function(self, instance_path: str, cell_type: str) -> str:
        """
        Determine cell function from instance path and cell type.
        
        Args:
            instance_path: Hierarchical instance path
            cell_type: Cell type name
            
        Returns:
            Cell function string
        """
        # Clock gate patterns
        if any(pattern in cell_type.upper() for pattern in ['CKLNQ', 'CLKG', 'CG_HIER', 'RC_CGIC']):
            return 'clock_gate'
        
        # CTS buffer/inverter patterns
        if 'CTS_' in instance_path or any(pattern in cell_type.upper() for pattern in ['DCCKND', 'DCCKBF']):
            return 'cts_buffer_inverter'
        
        # Flip-flop patterns
        if '/CP' in instance_path or 'DFR' in cell_type.upper() or 'DFF' in cell_type.upper():
            return 'flip_flop'
        
        return 'unknown'
    
    # =========================================================================
    # Type 1: Boolean Check
    # =========================================================================
    
    def _execute_type1(self) -> CheckResult:
        """
        Type 1: Boolean Check.
        
        Check if clock tree cells meet VT requirements (LVT/ULVT only).
        Does NOT use pattern_items for searching.
        
        Returns:
            CheckResult with is_pass based on check logic
        """
        # Parse input
        data = self._parse_input_files()
        items = data.get('items', [])
        metadata = data.get('metadata', {})
        
        # Separate compliant and non-compliant cells
        compliant_items = {}
        non_compliant_items = []
        
        for item in items:
            vt_type = item['vt_type']
            
            # Compliant VT types: LVT and ULVT
            if vt_type in ['LVT', 'ULVT']:
                compliant_items[item['name']] = {
                    'name': item['name'],
                    'line_number': item.get('line_number', 0),
                    'file_path': item.get('file_path', 'N/A')
                }
            else:
                # Non-compliant: SVT, RVT, HVT, UNKNOWN
                non_compliant_items.append(item['name'])
        
        # Use template helper for automatic output formatting
        return self.build_complete_output(
            found_items=compliant_items,
            missing_items=non_compliant_items,
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
        This is a status_check mode: only output items matching pattern_items.
        
        Returns:
            CheckResult with is_pass based on value comparison
        """
        # Parse input
        data = self._parse_input_files()
        all_items = {item['name']: item for item in data.get('items', [])}
        
        # Get requirements
        pattern_items = self.item_data.get('requirements', {}).get('pattern_items', [])
        
        # status_check mode: Check status of items matching pattern_items
        found_items = {}      # Matched AND VT compliant
        missing_items = {}    # Matched BUT VT non-compliant
        missing_patterns = []  # Pattern not matched at all
        
        for pattern in pattern_items:
            matched = False
            for item_name, item_data in all_items.items():
                # Check if pattern matches item name (case-insensitive)
                if pattern.lower() in item_name.lower():
                    matched = True
                    vt_type = item_data['vt_type']
                    
                    # Check if VT type is compliant (LVT/ULVT)
                    if vt_type in ['LVT', 'ULVT']:
                        found_items[item_name] = {
                            'name': item_name,
                            'line_number': item_data.get('line_number', 0),
                            'file_path': item_data.get('file_path', 'N/A')
                        }
                    else:
                        missing_items[item_name] = {
                            'name': item_name,
                            'line_number': item_data.get('line_number', 0),
                            'file_path': item_data.get('file_path', 'N/A')
                        }
                    break
            
            if not matched:
                missing_patterns.append(pattern)
        
        # Convert missing_items dict to list for build_complete_output
        missing_list = list(missing_items.keys()) if missing_items else missing_patterns
        
        # Use template helper (auto-handles waiver=0)
        return self.build_complete_output(
            found_items=found_items,
            missing_items=missing_list,
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
        
        Returns:
            CheckResult with FAIL for unwaived, INFO for waived items
        """
        # Parse input
        parsed_data = self._parse_input_files()
        all_items = {item['name']: item for item in parsed_data.get('items', [])}
        
        # Parse waiver configuration
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # Get requirements
        pattern_items = self.item_data.get('requirements', {}).get('pattern_items', [])
        
        # Find violations (non-compliant VT types)
        violations = []
        for pattern in pattern_items:
            for item_name, item_data in all_items.items():
                if pattern.lower() in item_name.lower():
                    vt_type = item_data['vt_type']
                    if vt_type not in ['LVT', 'ULVT']:
                        violations.append({
                            'name': item_name,
                            'line_number': item_data.get('line_number', 0),
                            'file_path': item_data.get('file_path', 'N/A')
                        })
        
        # Separate waived/unwaived using template helper
        waived_items = []
        missing_items = []
        
        for violation in violations:
            if self.match_waiver_entry(violation['name'], waive_dict):
                waived_items.append(violation['name'])
            else:
                missing_items.append(violation['name'])
        
        # Find unused waivers
        used_names = set(waived_items)
        unused_waivers = [name for name in waive_dict.keys() if name not in used_names]
        
        # Use template helper for automatic output formatting
        return self.build_complete_output(
            waived_items=waived_items,
            missing_items=missing_items,
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
        
        Returns:
            CheckResult with waiver logic applied
        """
        # Parse input
        data = self._parse_input_files()
        items = data.get('items', [])
        
        # Parse waiver configuration
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # Find non-compliant cells (violations)
        violations = []
        for item in items:
            vt_type = item['vt_type']
            if vt_type not in ['LVT', 'ULVT']:
                violations.append({
                    'name': item['name'],
                    'line_number': item.get('line_number', 0),
                    'file_path': item.get('file_path', 'N/A')
                })
        
        # Separate waived/unwaived
        waived_items = []
        missing_items = []
        
        for violation in violations:
            if self.match_waiver_entry(violation['name'], waive_dict):
                waived_items.append(violation['name'])
            else:
                missing_items.append(violation['name'])
        
        # Find unused waivers
        used_names = set(waived_items)
        unused_waivers = [name for name in waive_dict.keys() if name not in used_names]
        
        # Use template helper (auto-handles waiver=0)
        return self.build_complete_output(
            waived_items=waived_items,
            missing_items=missing_items,
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
    checker = Check_8_0_0_15()
    checker.init_checker(Path(__file__))
    result = checker.execute_check()
    checker.write_output(result)
    return 0 if result.is_pass else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())