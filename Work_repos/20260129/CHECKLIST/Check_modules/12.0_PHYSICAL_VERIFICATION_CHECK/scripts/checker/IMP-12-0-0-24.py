################################################################################
# Script Name: IMP-12-0-0-24.py
#
# Purpose:
#   Confirm add the chipBoundary layer to check boundary DRC for test chip.
#
# Logic:
#   - Parse DRC report files (Calibre/Pegasus format) to extract layer statistics
#   - Search for Chip_Boundary layer in layer statistics section
#   - Extract geometry count for Chip_Boundary layer
#   - Verify geometry count equals 1 (valid chip boundary definition)
#   - Support both Calibre and Pegasus DRC report formats
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
# Author: Jingyu Wang
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
class Check_12_0_0_24(InputFileParserMixin, OutputBuilderMixin, WaiverHandlerMixin, BaseChecker):
    """
    IMP-12-0-0-24: Confirm add the chipBoundary layer to check boundary DRC for test chip.
    
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
    FOUND_DESC_TYPE1_4 = "Chip_Boundary layer found in DRC report with correct geometry count"
    MISSING_DESC_TYPE1_4 = "Chip_Boundary layer not found in DRC report or incorrect geometry count"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_DESC_TYPE2_3 = "Chip_Boundary layer matched in DRC report (1/1)"
    MISSING_DESC_TYPE2_3 = "Expected Chip_Boundary layer not satisfied (0/1 missing)"
    
    # All Types (waiver description unified)
    WAIVED_DESC = "Chip_Boundary layer requirement waived"
    
    # ⭐ REASON CONSTANTS - Split by Type semantics (API-025)
    # ALL Types pass found_reason/missing_reason, but use different constants
    
    # Type 1/4: Boolean checks - emphasize "found/not found" (existence)
    FOUND_REASON_TYPE1_4 = "Chip_Boundary layer found with geometry count = 1 in DRC report"
    MISSING_REASON_TYPE1_4 = "Chip_Boundary layer validation failed (see details for actual geometry count)"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_REASON_TYPE2_3 = "Required Chip_Boundary layer matched and validated with geometry count = 1"
    MISSING_REASON_TYPE2_3 = "Expected Chip_Boundary layer not satisfied or missing from DRC report"
    
    # Waiver-related (Type 3/4 only)
    WAIVED_BASE_REASON = "Chip_Boundary layer check waived per design team approval"
    UNUSED_WAIVER_REASON = "Waiver not matched - Chip_Boundary layer found or no corresponding violation"
    
    def __init__(self):
        """Initialize the checker."""
        super().__init__(
            check_module="12.0_PHYSICAL_VERIFICATION_CHECK",
            item_id="IMP-12-0-0-24",
            item_desc="Confirm add the chipBoundary layer to check boundary DRC for test chip."
        )
        # Custom member variables for parsed data
        self._parsed_items: List[Dict[str, Any]] = []
        self._metadata: Dict[str, str] = {}
        self._chip_boundary_found: bool = False
        self._geometry_count: int = 0
        self._report_type: str = "Unknown"
    
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
        Parse DRC report files to extract Chip_Boundary layer information.
        
        Supports both Calibre and Pegasus DRC report formats.
        Searches for Chip_Boundary layer in layer statistics section and
        extracts geometry count.
        
        Returns:
            Dict with parsed data:
            - 'items': List[Dict] - Chip_Boundary layer findings with metadata
            - 'metadata': Dict - Report metadata (tool type, design name)
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
        chip_boundary_found = False
        geometry_count = 0
        report_type = "Unknown"
        
        # Patterns for Chip_Boundary layer detection
        # Calibre format: "LAYER Chip_Boundary ............. TOTAL Original Geometry Count = 1"
        pattern_calibre = re.compile(r'^\s*LAYER\s+Chip_Boundary\s+\.+\s+TOTAL\s+Original\s+Geometry\s+Count\s+=\s+(\d+)', re.IGNORECASE)
        
        # Pegasus format: "LAYER Chip_Boundary ........................ Total Original Geometry:          1"
        pattern_pegasus = re.compile(r'^\s*LAYER\s+Chip_Boundary\s+\.+\s+Total\s+Original\s+Geometry:\s+(\d+)', re.IGNORECASE)
        
        # Report type detection patterns
        calibre_marker = re.compile(r'CALIBRE::DRC', re.IGNORECASE)
        pegasus_marker = re.compile(r'Pegasus\s+VERSION', re.IGNORECASE)
        
        # 3. Parse each input file for Chip_Boundary layer information
        for file_path in valid_files:
            try:
                current_report_type = "Unknown"
                file_has_chip_boundary = False
                
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line_num, line in enumerate(f, 1):
                        # Detect report type
                        if calibre_marker.search(line):
                            current_report_type = "Calibre"
                        elif pegasus_marker.search(line):
                            current_report_type = "Pegasus"
                        
                        # Try Calibre format
                        match_calibre = pattern_calibre.search(line)
                        if match_calibre:
                            file_has_chip_boundary = True
                            chip_boundary_found = True
                            geometry_count = int(match_calibre.group(1))
                            report_type = current_report_type if current_report_type != "Unknown" else "Calibre"
                            file_basename = file_path.stem  # Use file basename for uniqueness
                            
                            items.append({
                                'name': f'Chip_Boundary_{file_basename}',  # Use file basename to support multiple reports
                                'line_number': line_num,
                                'file_path': str(file_path),
                                'type': 'layer',
                                'geometry_count': geometry_count,
                                'report_type': report_type,
                                'file_basename': file_basename,
                                'line_content': line.strip()
                            })
                            break  # Found in this file, move to next file
                        
                        # Try Pegasus format
                        match_pegasus = pattern_pegasus.search(line)
                        if match_pegasus:
                            file_has_chip_boundary = True
                            chip_boundary_found = True
                            geometry_count = int(match_pegasus.group(1))
                            report_type = current_report_type if current_report_type != "Unknown" else "Pegasus"
                            file_basename = file_path.stem  # Use file basename for uniqueness
                            
                            items.append({
                                'name': f'Chip_Boundary_{file_basename}',  # Use file basename to support multiple reports
                                'line_number': line_num,
                                'file_path': str(file_path),
                                'type': 'layer',
                                'geometry_count': geometry_count,
                                'report_type': report_type,
                                'file_basename': file_basename,
                                'line_content': line.strip()
                            })
                            break  # Found in this file, move to next file
                
                # Track files that don't have Chip_Boundary layer
                if not file_has_chip_boundary:
                    errors.append(f"Chip_Boundary layer not found in {file_path.name}")
                    
            except Exception as e:
                errors.append(f"Error parsing {file_path}: {str(e)}")
        
        # 4. Store frequently reused data on self
        self._parsed_items = items
        self._chip_boundary_found = chip_boundary_found
        self._geometry_count = geometry_count
        self._report_type = report_type
        self._metadata = metadata
        
        return {
            'items': items,
            'metadata': metadata,
            'errors': errors
        }
    # Helper Methods (Optional - Add as needed)
    

    # =========================================================================
    # Type 1: Boolean Check
    # =========================================================================

    def _execute_type1(self) -> CheckResult:
        """Type 1: Boolean check without waiver support."""
        violations = self._type1_core_logic()

        # Build found_items from clean items (reports with valid Chip_Boundary layer)
        data = self._parse_input_files()
        found_items = {}

        # If no violations, all parsed reports are clean
        if not violations:
            for item in data.get('items', []):
                item_name = item.get('name', 'Unknown')
                found_items[item_name] = {
                    'name': item_name,
                    'line_number': item.get('line_number', 0),
                    'file_path': item.get('file_path', 'N/A')
                }

        # FIXED: Pass dict directly, not list(violations.values())
        return self.build_complete_output(
            found_items=found_items,
            missing_items=violations,
            found_desc=self.FOUND_DESC_TYPE1_4,
            missing_desc=self.MISSING_DESC_TYPE1_4,
            found_reason=self.FOUND_REASON_TYPE1_4,
            missing_reason=lambda m: m.get('reason', self.MISSING_REASON_TYPE1_4)  # Use specific reason from metadata
        )

    def _type1_core_logic(self) -> dict[str, dict]:
        """
        Core Type 1 boolean check logic (shared by Type 1 and Type 4).

        Validates Chip_Boundary layer in DRC reports:
        - Searches for Chip_Boundary layer in layer statistics
        - Verifies geometry count equals 1
        - Supports both Calibre and Pegasus DRC report formats

        Returns:
            Dict of violations: {item_name: {'line_number': ..., 'file_path': ..., 'reason': ...}}
            Empty dict if all checks pass.
        """
        data = self._parse_input_files()
        items = data.get('items', [])
        errors = data.get('errors', [])

        violations = {}

        # Check for parsing errors
        if errors:
            for idx, error in enumerate(errors):
                error_key = f"Parse_Error_{idx+1}"
                violations[error_key] = {
                    'line_number': 0,
                    'file_path': 'N/A',
                    'reason': error
                }

        # If no items found and no parsing errors, it's a violation
        if not items and not errors:
            violations['Chip_Boundary'] = {
                'line_number': 0,
                'file_path': 'N/A',
                'reason': 'Chip_Boundary layer not found in any DRC report (Calibre/Pegasus)'
            }

        # Check each parsed item for Chip_Boundary layer validation
        for item in items:
            layer_name = item.get('name', '')  # Format: Chip_Boundary_<file_basename>
            geometry_count = item.get('geometry_count', 0)
            file_path = item.get('file_path', 'N/A')
            line_number = item.get('line_number', 0)
            file_basename = item.get('file_basename', 'Unknown')

            # Validate geometry count = 1 for each report
            if geometry_count != 1:
                # Use layer_name as key (includes file basename for uniqueness)
                violations[layer_name] = {
                    'line_number': line_number,
                    'file_path': file_path,
                    'reason': f'Chip_Boundary = {geometry_count} at line {line_number} in {file_basename}'
                }

        return violations

    # =========================================================================
    # Type 4: Boolean Check with Waiver Logic
    # =========================================================================

    def _execute_type4(self) -> CheckResult:
        """Type 4: Boolean check with waiver support (reuses Type 1 core logic)."""
        # Step 1: Get violations using Type 1's core logic
        violations = self._type1_core_logic()

        # Build found_items from clean items (reports with valid Chip_Boundary layer)
        data = self._parse_input_files()
        found_items = {}

        # If no violations, all parsed reports are clean
        if not violations:
            for item in data.get('items', []):
                item_name = item.get('name', 'Unknown')
                found_items[item_name] = {
                    'name': item_name,
                    'line_number': item.get('line_number', 0),
                    'file_path': item.get('file_path', 'N/A')
                }

        # Step 2: Parse waiver configuration
        # FIXED: Use waivers.get('waive_items', []) instead of get_waive_items()
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

        # Step 5: Build output
        # FIXED: Pass dict directly for missing_items and waived_items
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
            missing_reason=lambda m: m.get('reason', self.MISSING_REASON_TYPE1_4),  # Use specific reason
            waived_base_reason=self.WAIVED_BASE_REASON,
            unused_waiver_reason=self.UNUSED_WAIVER_REASON
        )

    # =========================================================================
    # Type 2: Value Check
    # =========================================================================

    def _execute_type2(self) -> CheckResult:
        """Type 2: Pattern/value check without waiver support."""
        found_items, missing_items = self._type2_core_logic()

        # FIXED: Pass dict directly for missing_items
        return self.build_complete_output(
            found_items=found_items,
            missing_items=missing_items,
            found_desc=self.FOUND_DESC_TYPE2_3,
            missing_desc=self.MISSING_DESC_TYPE2_3,
            found_reason=self.FOUND_REASON_TYPE2_3,
            missing_reason=lambda m: m.get('reason', self.MISSING_REASON_TYPE2_3)  # Use specific reason
        )

    def _type2_core_logic(self) -> tuple[dict[str, dict], dict[str, dict]]:
        """
        Core Type 2 pattern matching logic (shared by Type 2 and Type 3).

        Returns:
            Tuple of (found_items, missing_items)
            - found_items: {layer_name: {'line_number': ..., 'file_path': ..., 'geometry_count': ...}}
            - missing_items: {layer_name: {'line_number': ..., 'file_path': ..., 'reason': ...}}
        """
        data = self._parse_input_files()
        items = data.get('items', [])

        requirements = self.item_data.get('requirements', {})
        pattern_items = requirements.get('pattern_items', [])

        found_items = {}
        missing_items = {}

        # Search for Chip_Boundary layer in DRC report items
        # Note: Each item now has unique name like Chip_Boundary_Calibre, Chip_Boundary_Pegasus
        for pattern in pattern_items:
            # Check each parsed item (one per report file)
            for item in items:
                layer_name = item.get('name', '')  # e.g., Chip_Boundary_Calibre
                geometry_count = item.get('geometry_count', 0)
                report_type = item.get('report_type', 'Unknown')

                # PATTERN MATCH: Check if pattern is in layer_name (e.g., "Chip_Boundary" in "Chip_Boundary_Calibre")
                if pattern.lower() in layer_name.lower():
                    # Validate geometry count = 1 (valid chip boundary definition)
                    if geometry_count == 1:
                        found_items[layer_name] = {
                            'line_number': item.get('line_number', 0),
                            'file_path': item.get('file_path', 'N/A'),
                            'geometry_count': geometry_count,
                            'report_type': report_type
                        }
                    else:
                        # Layer found but geometry count incorrect
                        line_content = item.get('line_content', '')
                        missing_items[layer_name] = {
                            'line_number': item.get('line_number', 0),
                            'file_path': item.get('file_path', 'N/A'),
                            'reason': f'{pattern} geometry count = {geometry_count} (expected: 1) in {report_type} report. Line: {line_content[:80]}'
                        }

        # If pattern_items is empty (Type 1), check all items
        if not pattern_items and items:
            for item in items:
                layer_name = item.get('name', '')
                geometry_count = item.get('geometry_count', 0)
                report_type = item.get('report_type', 'Unknown')
                
                if geometry_count == 1:
                    found_items[layer_name] = {
                        'line_number': item.get('line_number', 0),
                        'file_path': item.get('file_path', 'N/A'),
                        'geometry_count': geometry_count,
                        'report_type': report_type
                    }
                else:
                    line_content = item.get('line_content', '')
                    missing_items[layer_name] = {
                        'line_number': item.get('line_number', 0),
                        'file_path': item.get('file_path', 'N/A'),
                        'reason': f'Chip_Boundary geometry count = {geometry_count} (expected: 1) in {report_type} report. Line: {line_content[:80]}'
                    }

        return found_items, missing_items

    # =========================================================================
    # Type 3: Value Check with Waiver Logic
    # =========================================================================

    def _execute_type3(self) -> CheckResult:
        """Type 3: Pattern/value check with waiver support (reuses Type 2 core logic)."""
        # Step 1: Get found/missing items using Type 2's core logic
        found_items_base, violations = self._type2_core_logic()

        # Step 2: Parse waiver configuration
        # FIXED: Use waivers.get('waive_items', []) instead of get_waive_items()
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)

        # Step 3: Split violations into waived and unwaived
        found_items = {}
        waived_items = {}
        missing_items = {}
        used_waivers = set()

        # Process found_items_base (no waiver needed - already valid)
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

        # Step 5: Build output
        # FIXED: Pass dict directly for missing_items and waived_items
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
            missing_reason=lambda m: m.get('reason', self.MISSING_REASON_TYPE2_3),  # Use specific reason
            waived_base_reason=self.WAIVED_BASE_REASON,
            unused_waiver_reason=self.UNUSED_WAIVER_REASON
        )
    
    def _matches_waiver(self, item: str, waive_patterns: List[str]) -> bool:
        """
        Check if item matches any waiver pattern.
        
        TODO: Optional - Implement waiver matching logic
        
        Args:
            item: Item to check
            waive_patterns: List of waiver patterns
            
        Returns:
            True if item matches any pattern
        """
        for pattern in waive_patterns:
            # Support wildcards
            if '*' in pattern:
                regex_pattern = pattern.replace('*', '.*')
                if re.search(regex_pattern, item, re.IGNORECASE):
                    return True
            # Exact match
            elif pattern.lower() == item.lower():
                return True
        return False


# =========================================================================
# Entry Point
# =========================================================================

def main():
    """Main entry point."""
    checker = Check_12_0_0_24()
    checker.init_checker(Path(__file__))
    result = checker.execute_check()
    checker.write_output(result)
    return 0 if result.is_pass else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())