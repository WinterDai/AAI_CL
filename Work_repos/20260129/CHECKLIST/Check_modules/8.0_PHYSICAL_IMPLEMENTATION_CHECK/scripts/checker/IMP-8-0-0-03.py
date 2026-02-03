################################################################################
# Script Name: IMP-8-0-0-03.py
#
# Purpose:
#   Confirm routing blockages are created around the block edges.
#
# Logic:
#   - Parse input file: IMP-8-0-0-03.rpt
#   - Extract die box coordinates (llx, lly, urx, ury) from "Block die boxes" line
#   - Extract all routing blockage definitions with layer and box coordinates
#   - Classify each blockage by edge proximity (left/right/top/bottom) using tolerance ±0.5
#   - Group blockages by metal layer and count per edge
#   - Validate that all four edges (left, right, top, bottom) have blockage coverage
#   - Report PASS if all edges covered, FAIL if any edge missing blockages
#
# Auto Type Detection:
#   Type 1: requirements.value=N/A, pattern_items [] (empty), waivers.value=N/A/0 → Boolean Check
#   Type 2: requirements.value>0, pattern_items [...] (defined), waivers.value=N/A/0 → Value Check
#   Type 3: requirements.value>0, pattern_items [...] (defined), waivers.value>0 → Value Check with Waiver Logic
#   Type 4: requirements.value=N/A, pattern_items [] (empty), waivers.value>0 → Boolean Check with Waiver Logic
#   Note: requirements.value indicates number of patterns for config validation (doesn't affect PASS/FAIL)
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
class Check_8_0_0_03(InputFileParserMixin, OutputBuilderMixin, WaiverHandlerMixin, BaseChecker):
    """
    IMP-8-0-0-03: Confirm routing blockages are created around the block edges.
    
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
    FOUND_DESC_TYPE1_4 = "All edge routing blockages found and properly aligned to die boundaries"
    MISSING_DESC_TYPE1_4 = "Missing edge blockages or blockages not aligned to die edges"
    FOUND_REASON_TYPE1_4 = "Edge routing blockages found and validated on all four edges"
    MISSING_REASON_TYPE1_4 = "Required edge blockages not found or misaligned"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_DESC_TYPE2_3 = "Required edge blockage patterns matched on all layers"
    MISSING_DESC_TYPE2_3 = "Expected edge blockage patterns not satisfied"
    FOUND_REASON_TYPE2_3 = "Required edge blockage patterns matched and validated"
    MISSING_REASON_TYPE2_3 = "Expected edge blockage patterns not satisfied or missing"
    
    # All Types (waiver description unified)
    WAIVED_DESC = "Waived edge blockage violations"
    
    # Waiver parameters (Type 3/4 ONLY)
    WAIVED_BASE_REASON = "Edge blockage violation waived per design approval"
    
    def __init__(self):
        """Initialize the checker."""
        super().__init__(
            check_module="8.0_PHYSICAL_IMPLEMENTATION_CHECK",
            item_id="IMP-8-0-0-03",
            item_desc="Confirm routing blockages are created around the block edges."
        )
        # Custom member variables for parsed data
        self._die_box: Optional[Dict[str, float]] = None
        self._blockages: List[Dict[str, Any]] = []
        self._edge_coverage: Dict[str, List[str]] = {
            'left': [],
            'right': [],
            'top': [],
            'bottom': []
        }
        self._tolerance = 0.5  # Edge detection tolerance
    
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
                    reason=f"Unexpected error during check execution: {str(e)}"
                )]
            )
    
    # =========================================================================
    # Input Parsing (Common for All Types)
    # =========================================================================
    
    def _parse_input_files(self) -> Dict[str, Any]:
        """
        Parse input files to extract die box and routing blockages.
        
        Returns:
            Dict with parsed data:
            - 'items': List[Dict] - Edge coverage summary items
            - 'metadata': Dict - Die box and blockage statistics
            - 'errors': List - Any parsing errors encountered
            - 'die_box': Dict - Die boundary coordinates
            - 'blockages': List[Dict] - All routing blockages
            - 'edge_coverage': Dict - Blockages per edge
        """
        # 1. Validate input files - IMPORTANT: returns tuple (valid_files_list, missing_files_list)
        valid_files, missing_files = self.validate_input_files()
        
        # FIXED: KNOWN_ISSUE_LOGIC-001 - Explicitly check for empty list
        if missing_files:
            raise ConfigurationError(
                self.create_missing_files_error(missing_files)
            )
        if not valid_files or len(valid_files) == 0:
            raise ConfigurationError(
                create_check_result(
                    is_pass=False,
                    item_id=self.item_id,
                    item_desc=self.item_desc,
                    details=[DetailItem(
                        severity=Severity.FAIL,
                        reason="No valid input files found"
                    )]
                )
            )
        
        # 2. Parse die box and blockages
        die_box = None
        blockages = []
        errors = []
        
        # Patterns for parsing
        die_box_pattern = re.compile(r'Block die boxes:\s*\{\{([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\}\}')
        blockage_pattern = re.compile(r'Routing Blockage:\s*Layer\s+(M\d+);\s*Box\s*\{\{([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\}\}')
        
        for file_path in valid_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line_num, line in enumerate(f, 1):
                        # Extract die box
                        if die_box is None:
                            die_match = die_box_pattern.search(line)
                            if die_match:
                                die_box = {
                                    'llx': float(die_match.group(1)),
                                    'lly': float(die_match.group(2)),
                                    'urx': float(die_match.group(3)),
                                    'ury': float(die_match.group(4)),
                                    'line_number': line_num,
                                    'file_path': str(file_path)
                                }
                        
                        # Extract routing blockages
                        blockage_match = blockage_pattern.search(line)
                        if blockage_match:
                            blockages.append({
                                'layer': blockage_match.group(1),
                                'llx': float(blockage_match.group(2)),
                                'lly': float(blockage_match.group(3)),
                                'urx': float(blockage_match.group(4)),
                                'ury': float(blockage_match.group(5)),
                                'line_number': line_num,
                                'file_path': str(file_path)
                            })
            except Exception as e:
                errors.append(f"Error parsing {file_path}: {str(e)}")
        
        # 3. Validate die box was found
        if die_box is None:
            errors.append("Die box definition not found in report")
            raise ConfigurationError(
                create_check_result(
                    is_pass=False,
                    item_id=self.item_id,
                    item_desc=self.item_desc,
                    details=[DetailItem(
                        severity=Severity.FAIL,
                        reason="Die box definition not found in report"
                    )]
                )
            )
        
        # 4. Classify blockages by edge
        edge_coverage = {
            'left': [],
            'right': [],
            'top': [],
            'bottom': []
        }
        
        for blockage in blockages:
            # Check left edge (llx near die.llx)
            if abs(blockage['llx'] - die_box['llx']) <= self._tolerance:
                edge_coverage['left'].append(f"{blockage['layer']} (line {blockage['line_number']})")
            
            # Check right edge (urx near die.urx)
            if abs(blockage['urx'] - die_box['urx']) <= self._tolerance:
                edge_coverage['right'].append(f"{blockage['layer']} (line {blockage['line_number']})")
            
            # Check bottom edge (lly near die.lly)
            if abs(blockage['lly'] - die_box['lly']) <= self._tolerance:
                edge_coverage['bottom'].append(f"{blockage['layer']} (line {blockage['line_number']})")
            
            # Check top edge (ury near die.ury)
            if abs(blockage['ury'] - die_box['ury']) <= self._tolerance:
                edge_coverage['top'].append(f"{blockage['layer']} (line {blockage['line_number']})")
        
        # 5. Store on self for reuse
        self._die_box = die_box
        self._blockages = blockages
        self._edge_coverage = edge_coverage
        
        # 6. Create summary items for output
        items = []
        for edge, layers in edge_coverage.items():
            if layers:
                items.append({
                    'name': f"{edge.capitalize()} edge: {len(layers)} blockages",
                    'line_number': die_box['line_number'],
                    'file_path': die_box['file_path'],
                    'edge': edge,
                    'count': len(layers),
                    'layers': layers
                })
        
        return {
            'items': items,
            'metadata': {
                'total_blockages': len(blockages),
                'die_box': die_box,
                'edges_covered': len([e for e in edge_coverage.values() if e])
            },
            'errors': errors,
            'die_box': die_box,
            'blockages': blockages,
            'edge_coverage': edge_coverage
        }
    
    # =========================================================================
    # Type 1: Boolean Check
    # =========================================================================
    
    def _execute_type1(self) -> CheckResult:
        """
        Type 1: Boolean Check.
        
        Validates that all four edges have routing blockage coverage.
        
        Returns:
            CheckResult with is_pass based on edge coverage
        """
        # Parse input
        data = self._parse_input_files()
        edge_coverage = data.get('edge_coverage', {})
        die_box = data.get('die_box', {})
        
        # Check if all edges have blockages
        found_items = {}
        missing_items = []
        
        for edge in ['left', 'right', 'top', 'bottom']:
            if edge_coverage.get(edge):
                found_items[f"{edge.capitalize()} edge"] = {
                    'name': f"{edge.capitalize()} edge: {len(edge_coverage[edge])} blockages",
                    'line_number': die_box.get('line_number', 0),
                    'file_path': die_box.get('file_path', 'N/A')
                }
            else:
                missing_items.append(f"{edge.capitalize()} edge")
        
        # Use template helper - Type 1: Use TYPE1_4 reason (emphasize "found/not found") - API-025
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
        
        Compares actual edge blockages against required pattern_items.
        
        Returns:
            CheckResult with is_pass based on pattern matching
        """
        # Parse input
        data = self._parse_input_files()
        edge_coverage = data.get('edge_coverage', {})
        die_box = data.get('die_box', {})
        
        # Get requirements
        pattern_items = self.item_data.get('requirements', {}).get('pattern_items', [])
        
        # Build found items with metadata
        found_items = {}
        for edge in ['left', 'right', 'top', 'bottom']:
            if edge_coverage.get(edge):
                found_items[f"{edge.capitalize()} edge"] = {
                    'name': f"{edge.capitalize()} edge: {len(edge_coverage[edge])} blockages",
                    'line_number': die_box.get('line_number', 0),
                    'file_path': die_box.get('file_path', 'N/A')
                }
        
        # Check for missing edges (not in pattern_items or no coverage)
        missing_items = []
        for edge in ['left', 'right', 'top', 'bottom']:
            if not edge_coverage.get(edge):
                missing_items.append(f"{edge.capitalize()} edge")
        
        # Use template helper - Type 2: Use TYPE2_3 reason (emphasize "matched/satisfied") - API-025
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
        
        Validates edge blockages with waiver classification.
        
        Returns:
            CheckResult with FAIL for unwaived, INFO for waived items
        """
        # Parse input
        parsed_data = self._parse_input_files()
        edge_coverage = parsed_data.get('edge_coverage', {})
        die_box = parsed_data.get('die_box', {})
        
        # FIXED: KNOWN_ISSUE_API-016 - Use waivers.get() directly to preserve dict format
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # Find violations (missing edges)
        violations = []
        for edge in ['left', 'right', 'top', 'bottom']:
            if not edge_coverage.get(edge):
                violations.append({
                    'name': f"{edge.capitalize()} edge",
                    'line_number': die_box.get('line_number', 0),
                    'file_path': die_box.get('file_path', 'N/A')
                })
        
        # Separate waived/unwaived using template helper
        waived_items = []
        unwaived_items = []
        
        for violation in violations:
            if self.match_waiver_entry(violation['name'], waive_dict):
                waived_items.append(violation)
            else:
                unwaived_items.append(violation)
        
        # Build found items (edges with coverage)
        found_items = {}
        for edge in ['left', 'right', 'top', 'bottom']:
            if edge_coverage.get(edge):
                found_items[f"{edge.capitalize()} edge"] = {
                    'name': f"{edge.capitalize()} edge: {len(edge_coverage[edge])} blockages",
                    'line_number': die_box.get('line_number', 0),
                    'file_path': die_box.get('file_path', 'N/A')
                }
        
        # FIXED: KNOWN_ISSUE_API-017 - waive_dict.keys() are item names (strings)
        used_names = set(w['name'] for w in waived_items)
        unused_waivers = [name for name in waive_dict.keys() if name not in used_names]
        
        # FIXED: KNOWN_ISSUE_API-021 - Use missing_items parameter instead of unwaived_items
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
        
        Validates edge blockages with waiver classification.
        
        Returns:
            CheckResult with waiver logic applied
        """
        # Parse input
        data = self._parse_input_files()
        edge_coverage = data.get('edge_coverage', {})
        die_box = data.get('die_box', {})
        
        # FIXED: KNOWN_ISSUE_API-016 - Use waivers.get() directly to preserve dict format
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # Find violations (missing edges)
        violations = []
        for edge in ['left', 'right', 'top', 'bottom']:
            if not edge_coverage.get(edge):
                violations.append({
                    'name': f"{edge.capitalize()} edge",
                    'line_number': die_box.get('line_number', 0),
                    'file_path': die_box.get('file_path', 'N/A')
                })
        
        # Separate waived/unwaived
        waived_items = []
        unwaived_items = []
        
        for violation in violations:
            if self.match_waiver_entry(violation['name'], waive_dict):
                waived_items.append(violation)
            else:
                unwaived_items.append(violation)
        
        # Build found items (edges with coverage)
        found_items = {}
        for edge in ['left', 'right', 'top', 'bottom']:
            if edge_coverage.get(edge):
                found_items[f"{edge.capitalize()} edge"] = {
                    'name': f"{edge.capitalize()} edge: {len(edge_coverage[edge])} blockages",
                    'line_number': die_box.get('line_number', 0),
                    'file_path': die_box.get('file_path', 'N/A')
                }
        
        # FIXED: KNOWN_ISSUE_API-017 - waive_dict.keys() are item names (strings)
        used_names = set(w['name'] for w in waived_items)
        unused_waivers = [name for name in waive_dict.keys() if name not in used_names]
        
        # FIXED: KNOWN_ISSUE_API-021 - Use missing_items parameter instead of unwaived_items
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
    checker = Check_8_0_0_03()
    checker.init_checker(Path(__file__))
    result = checker.execute_check()
    checker.write_output(result)
    return 0 if result.is_pass else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())