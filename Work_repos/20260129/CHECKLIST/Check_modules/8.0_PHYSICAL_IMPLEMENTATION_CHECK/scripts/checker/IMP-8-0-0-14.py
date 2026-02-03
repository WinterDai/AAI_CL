################################################################################
# Script Name: IMP-8-0-0-14.py
#
# Purpose:
#   Confirm no VT mixing on clock tree for all modes. For some instances has clock attribute but used as data, please list that into Waiver list.
#
# Logic:
#   - Parse clock_cells_with_cell_type.txt to extract instance-to-cell mappings with VT types
#   - Parse IMP-8-0-0-14.rpt to extract clock tree structures and identify generator inputs
#   - Extract VT type from cell names using regex pattern (LVT/ULVT/SVT/HVT/RVT)
#   - Group cells by clock tree and calculate VT distribution per tree
#   - Identify dominant VT type (most common) for each clock tree
#   - Detect VT mixing violations: cells with VT different from dominant VT
#   - Classify violations as waivable (generator inputs, generated clocks) or non-waivable
#   - Match violations against waiver list using instance path patterns
#   - Report unwaived VT mixing violations as FAIL, waived items as INFO
#
# Auto Type Detection:
#   Type 1: requirements.value=N/A, pattern_items [] (empty), waivers.value=N/A/0 → Boolean Check
#   Type 2: requirements.value>0, pattern_items [...] (defined), waivers.value=N/A/0 → Value Check
#   Type 3: requirements.value>0, pattern_items [...] (defined), waivers.value>0 → Value Check with Waiver Logic
#   Type 4: requirements.value=N/A, pattern_items [] (empty), waivers.value>0 → Boolean Check with Waiver Logic
#   Note: requirements.value indicates number of patterns for config validation (doesn't affect PASS/FAIL)
#
# Output Behavior (Type 3 - status_check mode):
#   pattern_items = clock trees to CHECK VT CONSISTENCY (only output matched trees)
#     - found_items = clock trees with consistent VT (no mixing)
#     - missing_items = clock trees with VT mixing violations
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
from collections import defaultdict, Counter


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
class Check_8_0_0_14(InputFileParserMixin, OutputBuilderMixin, WaiverHandlerMixin, BaseChecker):
    """
    IMP-8-0-0-14: Confirm no VT mixing on clock tree for all modes. For some instances has clock attribute but used as data, please list that into Waiver list.
    
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
    FOUND_DESC_TYPE1_4 = "Clock trees with consistent VT types found"
    MISSING_DESC_TYPE1_4 = "Clock trees with VT mixing not found"
    FOUND_REASON_TYPE1_4 = "Clock tree has consistent VT type across all cells"
    MISSING_REASON_TYPE1_4 = "Clock tree VT consistency check not performed"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_DESC_TYPE2_3 = "Clock trees with consistent VT types (no mixing detected)"
    MISSING_DESC_TYPE2_3 = "Clock trees with VT mixing violations"
    FOUND_REASON_TYPE2_3 = "All cells in clock tree use consistent VT type"
    MISSING_REASON_TYPE2_3 = "VT mixing detected - multiple VT types found in clock tree"
    
    # All Types (waiver description unified)
    WAIVED_DESC = "VT mixing violations waived (clock-attributed cells used as data)"
    
    # Waiver parameters (Type 3/4 ONLY)
    WAIVED_BASE_REASON = "Clock-attributed cell used in data path (generator input or clock divider)"
    
    def __init__(self):
        """Initialize the checker."""
        super().__init__(
            check_module="8.0_PHYSICAL_IMPLEMENTATION_CHECK",
            item_id="IMP-8-0-0-14",
            item_desc="Confirm no VT mixing on clock tree for all modes. For some instances has clock attribute but used as data, please list that into Waiver list."
        )
        # Custom member variables for parsed data
        self._parsed_items: List[Dict[str, Any]] = []
        self._clock_tree_data: Dict[str, Dict[str, Any]] = {}
        self._instance_to_cell: Dict[str, Tuple[str, str]] = {}
        self._waiver_candidates: Dict[str, Dict[str, Any]] = {}
    
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
            return create_check_result(
                is_pass=False,
                item_id=self.item_id,
                item_desc=self.item_desc,
                details=[DetailItem(
                    severity=Severity.FAIL,
                    message=f"Unexpected error during check execution: {str(e)}",
                    reason=f"Exception: {type(e).__name__}"
                )]
            )
    
    # =========================================================================
    # Input Parsing (Common for All Types)
    # =========================================================================
    
    def _parse_input_files(self) -> Dict[str, Any]:
        """
        Parse input files to extract clock tree VT information.
        
        Parses two input files:
        1. clock_cells_with_cell_type.txt - Instance to cell mapping
        2. IMP-8-0-0-14.rpt - Clock tree structure with VT types
        
        Returns:
            Dict with parsed data:
            - 'items': List[Dict] - VT mixing violations with metadata
            - 'metadata': Dict - Summary statistics
            - 'errors': List - Parsing errors
        """
        # 1. Validate input files (raises ConfigurationError if missing)
        valid_files, missing_files = self.validate_input_files()
        if missing_files:
            raise ConfigurationError(
                self.create_missing_files_error(missing_files)
            )
        
        # 2. Initialize data structures
        instance_to_cell: Dict[str, Tuple[str, str, int, str]] = {}  # instance: (cell, vt, line, file)
        clock_tree_data: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            'cells': [],
            'vt_distribution': Counter(),
            'waiver_candidates': [],
            'source_file': '',
            'source_line': 0
        })
        waiver_candidates: Dict[str, Dict[str, Any]] = {}
        errors = []
        
        # 3. Parse each input file
        for file_path in valid_files:
            file_name = Path(file_path).name
            
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    if 'clock_cells_with_cell_type.txt' in file_name:
                        self._parse_clock_cells_file(f, file_path, instance_to_cell, errors)
                    elif 'IMP-8-0-0-14.rpt' in file_name:
                        self._parse_clock_tree_report(f, file_path, clock_tree_data, waiver_candidates, errors)
            except Exception as e:
                errors.append(f"Error parsing {file_path}: {str(e)}")
        
        # 4. Merge data from both files and detect violations
        violations = self._detect_vt_mixing_violations(
            instance_to_cell, clock_tree_data, waiver_candidates
        )
        
        # 5. Store frequently reused data on self
        self._parsed_items = violations
        self._clock_tree_data = dict(clock_tree_data)
        self._instance_to_cell = instance_to_cell
        self._waiver_candidates = waiver_candidates
        
        # 6. Return aggregated dict
        return {
            'items': violations,
            'metadata': {
                'total_clock_trees': len(clock_tree_data),
                'total_cells': len(instance_to_cell),
                'total_violations': len(violations),
                'total_waiver_candidates': len(waiver_candidates)
            },
            'errors': errors
        }
    
    def _parse_clock_cells_file(
        self,
        file_handle,
        file_path: Path,
        instance_to_cell: Dict[str, Tuple[str, str, int, str]],
        errors: List[str]
    ) -> None:
        """
        Parse clock_cells_with_cell_type.txt file.
        
        Format: instance_path : cell_name
        Example: cdn_hs_phy/inst/.../RC_CGIC_INST : CKLNQD4BWP300H8P64PDULVT
        """
        pattern_instance_cell = re.compile(r'^([^:]+)\s*:\s*(\S+)$')
        pattern_vt_type = re.compile(r'(LVT|ULVT|SVT|HVT|RVT|SLVT)(?:\s|$)', re.IGNORECASE)
        
        for line_num, line in enumerate(file_handle, 1):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            match = pattern_instance_cell.search(line)
            if match:
                instance_path = match.group(1).strip()
                cell_name = match.group(2).strip()
                
                # Extract VT type from cell name
                vt_match = pattern_vt_type.search(cell_name)
                if vt_match:
                    vt_type = vt_match.group(1).upper()
                    instance_to_cell[instance_path] = (cell_name, vt_type, line_num, str(file_path))
                else:
                    errors.append(f"Line {line_num}: Cannot extract VT type from cell '{cell_name}'")
    
    def _parse_clock_tree_report(
        self,
        file_handle,
        file_path: Path,
        clock_tree_data: Dict[str, Dict[str, Any]],
        waiver_candidates: Dict[str, Dict[str, Any]],
        errors: List[str]
    ) -> None:
        """
        Parse IMP-8-0-0-14.rpt file.
        
        Extracts clock tree structures, VT types, and waiver candidates.
        """
        pattern_clock_tree = re.compile(r'^(Generated )?[Cc]lock tree ([^:]+):', re.IGNORECASE)
        pattern_cell_in_tree = re.compile(r'\(([A-Z0-9]+BWP[0-9]+[A-Z0-9]+PD(?:UL)?(LVT|SVT|SLVT|ULVT|HVT|RVT))\)', re.IGNORECASE)
        pattern_generator_input = re.compile(r'\(generator input\)', re.IGNORECASE)
        pattern_generated_clock = re.compile(r'\(generated clock tree ([^)]+)\)', re.IGNORECASE)
        pattern_instance_path = re.compile(r'\(L\d+\)\s+([^/\s]+(?:/[^/\s]+)*)/([A-Z]+)\s+\(([A-Z0-9]+)\)', re.IGNORECASE)
        pattern_vt_type = re.compile(r'(LVT|ULVT|SVT|HVT|RVT|SLVT)(?:\s|$|\))', re.IGNORECASE)
        
        current_clock_tree = None
        
        for line_num, line in enumerate(file_handle, 1):
            # Check for clock tree header
            tree_match = pattern_clock_tree.search(line)
            if tree_match:
                current_clock_tree = tree_match.group(2).strip()
                if current_clock_tree not in clock_tree_data:
                    clock_tree_data[current_clock_tree]['source_file'] = str(file_path)
                    clock_tree_data[current_clock_tree]['source_line'] = line_num
                continue
            
            if not current_clock_tree:
                continue
            
            # Check for cells with VT types
            cell_match = pattern_cell_in_tree.search(line)
            if cell_match:
                cell_name = cell_match.group(1)
                vt_type = cell_match.group(2).upper()
                
                # Extract instance path if available
                instance_match = pattern_instance_path.search(line)
                instance_path = instance_match.group(1) if instance_match else None
                
                clock_tree_data[current_clock_tree]['cells'].append({
                    'cell_name': cell_name,
                    'vt_type': vt_type,
                    'instance_path': instance_path,
                    'line_number': line_num,
                    'file_path': str(file_path)
                })
                clock_tree_data[current_clock_tree]['vt_distribution'][vt_type] += 1
                
                # Check for waiver candidates
                if pattern_generator_input.search(line) or pattern_generated_clock.search(line):
                    if instance_path:
                        waiver_candidates[instance_path] = {
                            'cell_name': cell_name,
                            'vt_type': vt_type,
                            'clock_tree': current_clock_tree,
                            'reason': 'generator input' if pattern_generator_input.search(line) else 'generated clock',
                            'line_number': line_num,
                            'file_path': str(file_path)
                        }
    
    def _detect_vt_mixing_violations(
        self,
        instance_to_cell: Dict[str, Tuple[str, str, int, str]],
        clock_tree_data: Dict[str, Dict[str, Any]],
        waiver_candidates: Dict[str, Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Detect VT mixing violations in clock trees.
        
        Returns:
            List of violation dictionaries with metadata
        """
        violations = []
        
        for clock_tree, tree_data in clock_tree_data.items():
            vt_distribution = tree_data['vt_distribution']
            
            # Skip if no cells or only one VT type
            if len(vt_distribution) <= 1:
                continue
            
            # Identify dominant VT (most common)
            dominant_vt = vt_distribution.most_common(1)[0][0]
            
            # Find cells with non-dominant VT
            for cell_info in tree_data['cells']:
                if cell_info['vt_type'] != dominant_vt:
                    instance_path = cell_info.get('instance_path', 'unknown')
                    
                    # Check if this is a waiver candidate
                    is_waiver_candidate = instance_path in waiver_candidates
                    
                    violation_name = f"{clock_tree}: {instance_path}"
                    violations.append({
                        'name': violation_name,
                        'clock_tree': clock_tree,
                        'instance_path': instance_path,
                        'cell_name': cell_info['cell_name'],
                        'vt_type': cell_info['vt_type'],
                        'dominant_vt': dominant_vt,
                        'vt_distribution': dict(vt_distribution),
                        'is_waiver_candidate': is_waiver_candidate,
                        'line_number': cell_info.get('line_number', 0),
                        'file_path': cell_info.get('file_path', 'N/A')
                    })
        
        return violations
    
    # =========================================================================
    # Type 1: Boolean Check
    # =========================================================================
    
    def _execute_type1(self) -> CheckResult:
        """
        Type 1: Boolean Check.
        
        Check if any VT mixing violations exist in clock trees.
        
        Returns:
            CheckResult with is_pass based on check logic
        """
        # Parse input
        data = self._parse_input_files()
        violations = data.get('items', [])
        
        # Convert violations to dict format with metadata
        found_items = {}
        if not violations:
            # No violations found - PASS
            found_items = {
                'No VT mixing detected': {
                    'name': 'No VT mixing detected',
                    'line_number': 0,
                    'file_path': 'N/A'
                }
            }
            missing_items = []
        else:
            # Violations found - FAIL
            found_items = {}
            missing_items = ['VT mixing violations detected']
        
        # Use template helper for automatic output formatting
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
        
        Check VT consistency for clock trees specified in pattern_items.
        Uses status_check mode: only output matched clock trees.
        
        Returns:
            CheckResult with is_pass based on value comparison
        """
        # Parse input
        data = self._parse_input_files()
        violations = data.get('items', [])
        
        # Get pattern_items (clock trees to check)
        pattern_items = self.item_data.get('requirements', {}).get('pattern_items', [])
        
        # Group violations by clock tree
        violations_by_tree = defaultdict(list)
        for violation in violations:
            violations_by_tree[violation['clock_tree']].append(violation)
        
        # status_check mode: Check status of matched clock trees
        found_items = {}      # Matched AND no VT mixing
        missing_items = []    # Matched BUT has VT mixing
        
        for pattern in pattern_items:
            matched = False
            for clock_tree in self._clock_tree_data.keys():
                if pattern.lower() in clock_tree.lower() or pattern == clock_tree:
                    matched = True
                    tree_violations = violations_by_tree.get(clock_tree, [])
                    
                    if not tree_violations:
                        # No VT mixing - PASS
                        tree_data = self._clock_tree_data[clock_tree]
                        vt_dist = tree_data['vt_distribution']
                        vt_summary = ', '.join([f"{vt}={count}" for vt, count in vt_dist.items()])
                        
                        found_items[clock_tree] = {
                            'name': clock_tree,
                            'vt_summary': vt_summary,
                            'line_number': tree_data.get('source_line', 0),
                            'file_path': tree_data.get('source_file', 'N/A')
                        }
                    else:
                        # VT mixing detected - FAIL
                        first_violation = tree_violations[0]
                        vt_dist = first_violation['vt_distribution']
                        vt_summary = ', '.join([f"{vt}={count}" for vt, count in vt_dist.items()])
                        
                        missing_items.append(clock_tree)
                    break
        
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
        
        Check VT consistency with waiver classification for data path usage.
        
        Returns:
            CheckResult with FAIL for unwaived, INFO for waived items
        """
        # Parse input
        parsed_data = self._parse_input_files()
        violations = parsed_data.get('items', [])
        
        # Parse waiver configuration using template helper (API-016 FIX)
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # Get pattern_items (clock trees to check)
        pattern_items = self.item_data.get('requirements', {}).get('pattern_items', [])
        
        # Group violations by clock tree
        violations_by_tree = defaultdict(list)
        for violation in violations:
            violations_by_tree[violation['clock_tree']].append(violation)
        
        # Separate waived/unwaived violations
        waived_items = []
        unwaived_items = []
        found_items = {}  # Clock trees with no violations
        
        for pattern in pattern_items:
            for clock_tree in self._clock_tree_data.keys():
                if pattern.lower() in clock_tree.lower() or pattern == clock_tree:
                    tree_violations = violations_by_tree.get(clock_tree, [])
                    
                    if not tree_violations:
                        # No VT mixing - add to found_items
                        tree_data = self._clock_tree_data[clock_tree]
                        vt_dist = tree_data['vt_distribution']
                        vt_summary = ', '.join([f"{vt}={count}" for vt, count in vt_dist.items()])
                        
                        found_items[clock_tree] = {
                            'name': clock_tree,
                            'vt_summary': vt_summary,
                            'line_number': tree_data.get('source_line', 0),
                            'file_path': tree_data.get('source_file', 'N/A')
                        }
                    else:
                        # Check each violation for waiver match
                        for violation in tree_violations:
                            violation_key = violation['instance_path']
                            
                            if self.match_waiver_entry(violation_key, waive_dict):
                                waived_items.append(violation['instance_path'])
                            else:
                                unwaived_items.append(violation['instance_path'])
                    break
        
        # Find unused waivers
        used_names = set(waived_items)
        
        unused_waivers = []
        for waiver_key, waiver_info in waive_dict.items():
            if waiver_info['name'] not in used_names:
                unused_waivers.append(waiver_info['name'])
        
        # Use template helper for automatic output formatting (API-021 FIX)
        return self.build_complete_output(
            found_items=found_items,
            waived_items=waived_items,
            missing_items=unwaived_items,  # API-021 FIX: Use missing_items instead of unwaived_items
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
        
        Check if VT mixing exists with waiver classification.
        
        Returns:
            CheckResult with waiver logic applied
        """
        # Parse input
        data = self._parse_input_files()
        violations = data.get('items', [])
        
        # Parse waiver configuration (API-016 FIX)
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # Separate waived/unwaived violations
        waived_items = []
        unwaived_items = []
        
        for violation in violations:
            violation_key = violation['instance_path']
            
            if self.match_waiver_entry(violation_key, waive_dict):
                waived_items.append(violation['instance_path'])
            else:
                unwaived_items.append(violation['instance_path'])
        
        # Find unused waivers
        used_names = set(waived_items)
        
        unused_waivers = []
        for waiver_key, waiver_info in waive_dict.items():
            if waiver_info['name'] not in used_names:
                unused_waivers.append(waiver_info['name'])
        
        # Prepare found_items (clean clock trees)
        found_items = {}
        if not unwaived_items and not waived_items:
            found_items = {
                'No VT mixing detected': {
                    'name': 'No VT mixing detected',
                    'line_number': 0,
                    'file_path': 'N/A'
                }
            }
        
        # Use template helper (API-021 FIX)
        return self.build_complete_output(
            found_items=found_items,
            waived_items=waived_items,
            missing_items=unwaived_items,  # API-021 FIX: Use missing_items instead of unwaived_items
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
    checker = Check_8_0_0_14()
    checker.init_checker(Path(__file__))
    result = checker.execute_check()
    checker.write_output(result)
    return 0 if result.is_pass else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())