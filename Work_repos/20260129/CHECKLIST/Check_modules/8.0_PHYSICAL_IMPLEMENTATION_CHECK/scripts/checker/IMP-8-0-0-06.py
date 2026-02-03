################################################################################
# Script Name: IMP-8-0-0-06.py
#
# Purpose:
#   Confirm the switch power pin is not in lef . (for non-PSO, please fill N/A)
#
# Logic:
#   - Parse Innovus log to extract PG pin layers from write_lef_abstract command
#   - Parse switch power layer report to extract design hierarchy, switch power net, and switch power layers
#   - For Type 1/4: Check if any LEF PG layer exists in switch power layers (overlap detection)
#   - For Type 2/3: Filter by design hierarchy (pattern_items), force PASS for sub-blocks
#   - PASS: No overlap between LEF PG layers and switch power layers
#   - FAIL: Overlap detected (switch power pins would be written to LEF)
#   - Support waiver for specific design hierarchies (Type 3/4)
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
# Refactored: 2026-01-06 (Using checker_templates v1.1.0)
#
# Author: Chenwei Fan
# Date: 2026-01-06
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
class Check_8_0_0_06(InputFileParserMixin, OutputBuilderMixin, WaiverHandlerMixin, BaseChecker):
    """
    IMP-8-0-0-06: Confirm the switch power pin is not in lef . (for non-PSO, please fill N/A)
    
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
    # ⭐ DESCRIPTION CONSTANTS - Split by Type semantics (API-026)
    # =========================================================================
    # DESC constants are split by Type for semantic clarity (same as REASON split)
    # Type 1/4 emphasize "found/not found", Type 2/3 emphasize "matched/satisfied"
    
    # Type 1/4: Boolean checks - emphasize "found/not found" (existence)
    FOUND_DESC_TYPE1_4 = "Power Switch Pin would not write out into LEF"
    MISSING_DESC_TYPE1_4 = "Power Switch Pin would write out into LEF"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_DESC_TYPE2_3 = "Power Switch Pin would not write out into LEF (TOP level) OR SUB-BLOCK level"
    MISSING_DESC_TYPE2_3 = "Power Switch Pin would write out into LEF (TOP level)"
    
    # All Types (waiver description unified)
    WAIVED_DESC = "Switch power pin in LEF waived for this design hierarchy"
    
    # ⭐ REASON CONSTANTS - Split by Type semantics (API-025)
    # ALL Types pass found_reason/missing_reason, but use different constants
    
    # Type 1/4: Boolean checks - emphasize "found/not found" (existence)
    FOUND_REASON_TYPE1_4 = "No overlap detected between LEF PG pin layers and switch power layers"
    MISSING_REASON_TYPE1_4 = "Overlap detected: LEF PG pin layers contain switch power layers"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_REASON_TYPE2_3 = "Design hierarchy matched and validated: No overlap between LEF PG pin layers and switch power layers, OR design is at sub-block level"
    MISSING_REASON_TYPE2_3 = "Design hierarchy matched but validation failed: LEF PG pin layers contain switch power layers"
    
    # Waiver-related (Type 3/4 only)
    WAIVED_BASE_REASON = "At this design hierarchy level, switch power pin in LEF can be accepted"
    UNUSED_WAIVER_REASON = "Waiver not matched - no corresponding design hierarchy found or design passed validation"
    
    def __init__(self):
        """Initialize the checker."""
        super().__init__(
            check_module="8.0_PHYSICAL_IMPLEMENTATION_CHECK",
            item_id="IMP-8-0-0-06",
            item_desc="Confirm the switch power pin is not in lef . (for non-PSO, please fill N/A)"
        )
        # Custom member variables for parsed data
        self._parsed_items: List[Dict[str, Any]] = []
        self._metadata: Dict[str, str] = {}
        self._lef_pg_layers: List[str] = []
        self._design_hier: str = ""
        self._switch_pg: str = ""
        self._switch_pg_layers: List[str] = []
    
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
        Parse input files to extract LEF PG layers and switch power information.
        
        Parses:
        1. Innovus log: Extract PG pin layers from write_lef_abstract command
        2. Switch power report: Extract design hierarchy, switch power net, and switch power layers
        
        Returns:
            Dict with parsed data:
            - 'items': List[Dict] - Parsed information (LEF PG, design hierarchy, switch power net/layers)
            - 'metadata': Dict - File metadata
            - 'errors': List - Parsing errors
        """
        # 1. Validate input files (returns tuple: valid_files, missing_files)
        valid_files, missing_files = self.validate_input_files()
        
        # FIXED: Explicitly check for empty list
        if missing_files and len(missing_files) > 0:
            raise ConfigurationError(
                self.create_missing_files_error(missing_files)
            )
        
        # FIXED: Explicitly check for empty list
        if not valid_files or len(valid_files) == 0:
            raise ConfigurationError("No valid input files found")
        
        # 2. Initialize parsing structures
        items = []
        metadata = {}
        errors = []
        lef_pg_layers = []
        design_hier = ""
        switch_pg = ""
        switch_pg_layers = []
        
        # 3. Parse each input file for switch power information
        for file_path in valid_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line_num, line in enumerate(f, 1):
                        # Pattern 1: Extract PG pin layers from write_lef_abstract command
                        # Example: "write_lef_abstract -extractBlockObs dbs/gddr36_ew_cdn_ghs_phy_top.OUTwoD.lef -noCutObs -specifyTopLayer 19 -stripePin -PGpinLayers 19"
                        match1 = re.search(r'write_lef_abstract.*OUTwoD\.lef.*-PGpinLayers\s+\{([^}]+)\}', line)
                        if match1:
                            lef_pg_str = match1.group(1).strip()
                            lef_pg_layers = lef_pg_str.split()
                            items.append({
                                'name': f"LEF_PG_Layers: {' '.join(lef_pg_layers)}",
                                'line_number': line_num,
                                'file_path': str(file_path),
                                'lef_pg': lef_pg_layers,
                                'type': 'lef_pg'
                            })
                            continue
                        
                        # Alternative pattern for PGpinLayers without braces
                        match1_alt = re.search(r'write_lef_abstract.*OUTwoD\.lef.*-PGpinLayers\s+(\S+)', line)
                        if match1_alt:
                            lef_pg_str = match1_alt.group(1).strip()
                            lef_pg_layers = lef_pg_str.split()
                            items.append({
                                'name': f"LEF_PG_Layers: {' '.join(lef_pg_layers)}",
                                'line_number': line_num,
                                'file_path': str(file_path),
                                'lef_pg': lef_pg_layers,
                                'type': 'lef_pg'
                            })
                            continue
                        
                        # Pattern 2: Extract design hierarchy
                        # Example: "Design Hierarchy: gddr36_ew_cdn_ghs_phy_top"
                        match2 = re.search(r'^Design Hierarchy:\s*(.+?)\s*$', line)
                        if match2:
                            design_hier = match2.group(1).strip()
                            items.append({
                                'name': f"Design_Hierarchy: {design_hier}",
                                'line_number': line_num,
                                'file_path': str(file_path),
                                'design_hier': design_hier,
                                'type': 'design_hierarchy'
                            })
                            continue
                        
                        # Pattern 3: Extract switch power net
                        # Example: "Switch Power: VDDG"
                        match3 = re.search(r'^Switch Power:\s*(.+?)\s*$', line)
                        if match3:
                            switch_pg = match3.group(1).strip()
                            items.append({
                                'name': f"Switch_Power_Net: {switch_pg}",
                                'line_number': line_num,
                                'file_path': str(file_path),
                                'switch_pg': switch_pg,
                                'type': 'switch_power_net'
                            })
                            continue
                        
                        # Pattern 4: Extract switch power layers (ignore comments after #)
                        # Example: "Switch Power Layer: 1 10 11 12 13 14 15 16 17 18 2 3 4 5 6 7 8 9  # Limit to 10KB"
                        match4 = re.search(r'^Switch Power Layer:\s*(.+?)(?:\s*#.*)?$', line)
                        if match4:
                            switch_pg_str = match4.group(1).strip()
                            switch_pg_layers = switch_pg_str.split()
                            items.append({
                                'name': f"Switch_Power_Layers: {' '.join(switch_pg_layers)}",
                                'line_number': line_num,
                                'file_path': str(file_path),
                                'switch_pg_layer': switch_pg_layers,
                                'type': 'switch_power_layers'
                            })
                            continue
            except Exception as e:
                errors.append(f"Error parsing {file_path}: {str(e)}")
        
        # 4. Store frequently reused data on self
        self._parsed_items = items
        self._lef_pg_layers = lef_pg_layers
        self._design_hier = design_hier
        self._switch_pg = switch_pg
        self._switch_pg_layers = switch_pg_layers
        
        return {
            'items': items,
            'metadata': metadata,
            'errors': errors,
            'lef_pg_layers': lef_pg_layers,
            'switch_power_data': self._build_switch_power_data(items)
        }
    
    def _build_switch_power_data(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Build consolidated switch power data from parsed items.
        
        Args:
            items: List of parsed items
            
        Returns:
            List of switch power data dictionaries
        """
        switch_power_data = []
        current_design = {}
        
        for item in items:
            item_type = item.get('type', '')
            
            if item_type == 'design_hierarchy':
                if current_design:
                    switch_power_data.append(current_design)
                current_design = {
                    'design_hier': item.get('design_hier', ''),
                    'line_number': item.get('line_number', 0),
                    'file_path': item.get('file_path', 'N/A'),
                    'switch_power_net': '',
                    'switch_layers': []
                }
            elif item_type == 'switch_power_net':
                if current_design:
                    current_design['switch_power_net'] = item.get('switch_pg', '')
            elif item_type == 'switch_power_layers':
                if current_design:
                    current_design['switch_layers'] = item.get('switch_pg_layer', [])
        
        if current_design:
            switch_power_data.append(current_design)
        
        return switch_power_data

    # =========================================================================
    # Type 1: Boolean Check
    # =========================================================================

    def _execute_type1(self) -> CheckResult:
        """
        Type 1: Boolean check without waiver support.

        Checks all designs for overlap between LEF PG pin layers and switch power layers.
        No design hierarchy filtering applied.

        Returns:
            CheckResult with found_items (no overlap) and missing_items (overlap detected)
        """
        violations = self._type1_core_logic()

        # Build found_items from designs with no overlap
        data = self._parse_input_files()
        all_designs = data.get('switch_power_data', [])

        found_items = {}
        for design in all_designs:
            design_hier = design.get('design_hier', 'Unknown')
            switch_power_net = design.get('switch_power_net', 'N/A')
            design_key = f"Design: {design_hier} | Switch Power: {switch_power_net}"
            
            if design_key not in violations:
                found_items[design_key] = {
                    'name': design_key,
                    'line_number': design.get('line_number', 0),
                    'file_path': design.get('file_path', 'N/A'),
                    'switch_power': switch_power_net,
                    'lef_pg_layers': data.get('lef_pg_layers', []),
                    'switch_layers': design.get('switch_layers', [])
                }

        return self.build_complete_output(
            found_items=found_items,
            missing_items=violations,
            found_desc=self.FOUND_DESC_TYPE1_4,
            missing_desc=self.MISSING_DESC_TYPE1_4,
            found_reason=self.FOUND_REASON_TYPE1_4,
            missing_reason=self.MISSING_REASON_TYPE1_4
        )

    def _type1_core_logic(self) -> Dict[str, Dict]:
        """
        Core Type 1 boolean check logic (shared by Type 1 and Type 4).

        Extracts LEF PG pin layers and switch power layers, then checks for overlap.

        Returns:
            Dict of violations: {design_name: {'line_number': ..., 'file_path': ..., 'reason': ...}}
            Empty dict if no overlap detected (all checks pass).
        """
        data = self._parse_input_files()

        # Handle parsing errors
        errors = data.get('errors', [])
        if errors:
            error_msg = '; '.join(errors)
            return {
                'parsing_error': {
                    'line_number': 0,
                    'file_path': 'N/A',
                    'reason': f"Failed to parse input files: {error_msg}"
                }
            }

        lef_pg_layers = data.get('lef_pg_layers', [])
        switch_power_data = data.get('switch_power_data', [])

        # If no LEF PG layers found, cannot perform check
        if not lef_pg_layers:
            return {
                'no_lef_pg_layers': {
                    'line_number': 0,
                    'file_path': 'N/A',
                    'reason': "No LEF PG pin layers found in Innovus log (write_lef_abstract command not found)"
                }
            }

        # If no switch power designs found, this is a PASS (no overlap possible)
        if not switch_power_data:
            return {}

        violations = {}

        # Check each design for overlap
        for design in switch_power_data:
            design_hier = design.get('design_hier', 'Unknown')
            switch_power_net = design.get('switch_power_net', 'N/A')
            switch_layers = design.get('switch_layers', [])

            # Find overlap between LEF PG layers and switch power layers
            overlap = sorted(set(lef_pg_layers) & set(switch_layers))

            if overlap:
                design_key = f"Design: {design_hier} | Switch Power: {switch_power_net}"
                violations[design_key] = {
                    'line_number': design.get('line_number', 0),
                    'file_path': design.get('file_path', 'N/A'),
                    'reason': f"Overlap detected: LEF PG pin layers contain switch power layers",
                    'switch_power': switch_power_net,
                    'lef_pg_layers': lef_pg_layers,
                    'switch_layers': switch_layers,
                    'overlap': overlap
                }

        return violations

    # =========================================================================
    # Type 4: Boolean Check with Waiver Logic
    # =========================================================================

    def _execute_type4(self) -> CheckResult:
        """
        Type 4: Boolean check with waiver support (reuses Type 1 core logic).

        Same as Type 1 but allows waiving specific design hierarchies.
        Violations can be waived by design hierarchy name.

        Returns:
            CheckResult with found_items, missing_items (unwaived), waived_items, and unused_waivers
        """
        # Step 1: Get violations using Type 1's core logic
        violations = self._type1_core_logic()

        # Build found_items from designs with no overlap
        data = self._parse_input_files()
        all_designs = data.get('switch_power_data', [])

        found_items = {}
        for design in all_designs:
            design_hier = design.get('design_hier', 'Unknown')
            switch_power_net = design.get('switch_power_net', 'N/A')
            design_key = f"Design: {design_hier} | Switch Power: {switch_power_net}"
            
            if design_key not in violations:
                found_items[design_key] = {
                    'name': design_key,
                    'line_number': design.get('line_number', 0),
                    'file_path': design.get('file_path', 'N/A'),
                    'switch_power': switch_power_net,
                    'lef_pg_layers': data.get('lef_pg_layers', []),
                    'switch_layers': design.get('switch_layers', [])
                }

        # Step 2: Parse waiver configuration (FIXED: Use waivers.get() instead of get_waive_items())
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)

        # Step 3: Split violations into waived and unwaived
        waived_items = {}
        missing_items = {}
        used_waivers = set()

        for viol_name, viol_data in violations.items():
            matched_waiver = self.match_waiver_entry(viol_name, waive_dict)
            if matched_waiver:
                waived_items[viol_name] = viol_data
                used_waivers.add(matched_waiver)
            else:
                missing_items[viol_name] = viol_data

        # Step 4: Find unused waivers
        unused_waivers = [w for w in waive_dict.keys() if w not in used_waivers]

        # Step 5: Build output (FIXED: Pass dict directly, not list)
        return self.build_complete_output(
            found_items=found_items,
            missing_items=missing_items,
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
    # Type 2: Value Check
    # =========================================================================

    def _execute_type2(self) -> CheckResult:
        """Type 2: Pattern/value check without waiver support."""
        found_items, missing_items = self._type2_core_logic()

        # FIXED: Pass dict directly for both found_items and missing_items
        return self.build_complete_output(
            found_items=found_items,
            missing_items=missing_items,
            found_desc=self.FOUND_DESC_TYPE2_3,
            missing_desc=self.MISSING_DESC_TYPE2_3,
            found_reason=self.FOUND_REASON_TYPE2_3,
            missing_reason=self.MISSING_REASON_TYPE2_3
        )

    def _type2_core_logic(self) -> Tuple[Dict[str, Dict], Dict[str, Dict]]:
        """
        Core Type 2 pattern matching logic (shared by Type 2 and Type 3).

        Returns:
            Tuple of (found_items, missing_items)
            - found_items: {design_name: {'line_number': ..., 'file_path': ..., 'details': ...}}
            - missing_items: {design_name: {'line_number': ..., 'file_path': ..., 'reason': ...}}
        """
        data = self._parse_input_files()
        lef_pg_layers = data.get('lef_pg_layers', [])
        switch_power_data = data.get('switch_power_data', [])

        requirements = self.item_data.get('requirements', {})
        pattern_items = requirements.get('pattern_items', [])

        found_items = {}
        missing_items = {}

        # Process each design in switch power data
        for design_entry in switch_power_data:
            design_hier = design_entry.get('design_hier', '')
            switch_power_net = design_entry.get('switch_power_net', '')
            switch_layers = design_entry.get('switch_layers', [])
            line_number = design_entry.get('line_number', 0)
            file_path = design_entry.get('file_path', 'N/A')

            # Check if design hierarchy matches pattern_items (EXACT MATCH)
            is_top_level = False
            for pattern in pattern_items:
                if pattern.lower() == design_hier.lower():
                    is_top_level = True
                    break

            # If not top-level (sub-block), force PASS
            design_key = f"Design: {design_hier} | Switch Power: {switch_power_net}"
            
            if not is_top_level:
                found_items[design_key] = {
                    'line_number': line_number,
                    'file_path': file_path,
                    'details': f"LEF PG Layers: {lef_pg_layers} | Switch Layers: {switch_layers} | Status: SUB-BLOCK level (check not applicable)"
                }
                continue

            # Top-level design: Check for overlap between LEF PG layers and switch power layers
            overlap = sorted(set(lef_pg_layers) & set(switch_layers))

            if overlap:
                # Overlap detected - FAIL
                missing_items[design_key] = {
                    'line_number': line_number,
                    'file_path': file_path,
                    'reason': f"LEF PG Layers: {lef_pg_layers} | Switch Layers: {switch_layers} | Overlap: {overlap} (TOP level)"
                }
            else:
                # No overlap - PASS
                found_items[design_key] = {
                    'line_number': line_number,
                    'file_path': file_path,
                    'details': f"LEF PG Layers: {lef_pg_layers} | Switch Layers: {switch_layers} | Status: No Overlap (TOP level)"
                }

        return found_items, missing_items

    # =========================================================================
    # Type 3: Value Check with Waiver Logic
    # =========================================================================

    def _execute_type3(self) -> CheckResult:
        """Type 3: Pattern/value check with waiver support (reuses Type 2 core logic)."""
        # Step 1: Get found/missing items using Type 2's core logic
        found_items_base, violations = self._type2_core_logic()

        # Step 2: Parse waiver configuration (FIXED: Use waivers.get() instead of get_waive_items())
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)

        # Step 3: Split violations into waived and unwaived
        found_items = {}
        waived_items = {}
        missing_items = {}
        used_waivers = set()

        # Process found_items_base (no waiver needed - already passing)
        for item_name, item_data in found_items_base.items():
            found_items[item_name] = item_data

        # Process violations with waiver matching
        for viol_name, viol_data in violations.items():
            matched_waiver = self.match_waiver_entry(viol_name, waive_dict)
            if matched_waiver:
                waived_items[viol_name] = viol_data
                used_waivers.add(matched_waiver)
            else:
                missing_items[viol_name] = viol_data

        # Step 4: Find unused waivers
        unused_waivers = [w for w in waive_dict.keys() if w not in used_waivers]

        # Step 5: Build output (FIXED: Pass dict directly, not list)
        return self.build_complete_output(
            found_items=found_items,
            missing_items=missing_items,
            waived_items=waived_items,
            unused_waivers=unused_waivers,
            waive_dict=waive_dict,
            found_desc=self.FOUND_DESC_TYPE2_3,
            missing_desc=self.MISSING_DESC_TYPE2_3,
            waived_desc=self.WAIVED_DESC,
            found_reason=self.FOUND_REASON_TYPE2_3,
            missing_reason=self.MISSING_REASON_TYPE2_3,
            waived_base_reason=self.WAIVED_BASE_REASON,
            unused_waiver_reason=self.UNUSED_WAIVER_REASON
        )


# =========================================================================
# Entry Point
# =========================================================================

def main():
    """Main entry point."""
    checker = Check_8_0_0_06()
    checker.init_checker(Path(__file__))
    result = checker.execute_check()
    checker.write_output(result)
    return 0 if result.is_pass else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())