################################################################################
# Script Name: IMP-8-0-0-12.py
#
# Purpose:
#   Confirm no inputs are tied directly to the power rails (VDD/VSS) by using Tiehigh/Tielow cells(check the Note)
#
# Logic:
#   - Parse input files: IMP-8-0-0-12.rpt (Cadence Innovus verifyTieCell report)
#   - Extract tie cell violations with instance paths, pin names, and coordinates
#   - Parse violation section headers to categorize violation types
#   - Extract summary statistics (total violations, violations by type)
#   - Validate parsed violation count matches summary total
#   - Aggregate violations from all report files if multiple exist
#   - Determine PASS (no violations) or FAIL (violations found)
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
from checker_templates.input_file_parser_template import InputFileParserMixin  # Optional but recommended


# MANDATORY: Inherit mixins in correct order (InputFileParserMixin first if used)
class Check_8_0_0_12(InputFileParserMixin, OutputBuilderMixin, WaiverHandlerMixin, BaseChecker):
    """
    IMP-8-0-0-12: Confirm no inputs are tied directly to the power rails (VDD/VSS) by using Tiehigh/Tielow cells(check the Note)
    
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
    FOUND_DESC_TYPE1_4 = "No tie cell violations found in design"
    MISSING_DESC_TYPE1_4 = "Tie cell violations detected in design"
    FOUND_REASON_TYPE1_4 = "No tie cell violations found - all inputs use proper Tiehigh/Tielow cells"
    MISSING_REASON_TYPE1_4 = "Tie cell violations detected - inputs tied directly to power rails without proper Tiehigh/Tielow cells"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_DESC_TYPE2_3 = "All monitored instance pins have no tie cell violations"
    MISSING_DESC_TYPE2_3 = "Tie cell violations found for monitored instance pins"
    FOUND_REASON_TYPE2_3 = "All monitored instance pins validated - no tie cell violations matched"
    MISSING_REASON_TYPE2_3 = "Monitored instance pins have tie cell violations - inputs tied directly to power rails"
    
    # All Types (waiver description unified)
    WAIVED_DESC = "Tie cell violations waived per design approval"
    
    # Waiver parameters (Type 3/4 ONLY)
    WAIVED_BASE_REASON = "Tie cell violation waived - approved exception for specific design requirements"
    
    # Unused waivers (Type 3/4 ONLY)
    UNUSED_DESC = "Unused waiver entries - no matching violations found"
    UNUSED_WAIVER_REASON = "Waiver entry not matched - corresponding tie cell violation not found in report"
    
    def __init__(self):
        """Initialize the checker."""
        super().__init__(
            check_module="8.0_PHYSICAL_IMPLEMENTATION_CHECK",
            item_id="IMP-8-0-0-12",
            item_desc="Confirm no inputs are tied directly to the power rails (VDD/VSS) by using Tiehigh/Tielow cells(check the Note)"
        )
        # Custom member variables for parsed data
        self._parsed_items: List[Dict[str, Any]] = []
        self._metadata: Dict[str, str] = {}
        self._total_violations: int = 0
    
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
        Parse input files to extract tie cell violations.
        
        Parses Cadence Innovus verifyTieCell reports to extract:
        - Individual tie cell violations (instance, pin, coordinates)
        - Violation type categorization
        - Summary statistics
        - Design metadata
        
        Returns:
            Dict with parsed data:
            - 'items': List[Dict] - Violation items with metadata (line_number, file_path)
            - 'metadata': Dict - File metadata (design name, total violations)
            - 'errors': List - Any parsing errors encountered
        """
        # 1. Validate input files - returns tuple (valid_files_list, missing_files_list)
        valid_files, missing_files = self.validate_input_files()
        
        # FIXED: Explicitly check for empty list
        if missing_files and len(missing_files) > 0:
            raise ConfigurationError(
                self.create_missing_files_error(missing_files)
            )
        
        # FIXED: Explicitly check for empty list
        if not valid_files or len(valid_files) == 0:
            raise ConfigurationError(
                self.create_missing_files_error(["No input files configured"])
            )
        
        # 2. Initialize parsing structures
        items = []
        metadata = {}
        errors = []
        current_violation_type = "Unknown"
        total_violations = 0
        
        # Define patterns based on file analysis
        # Pattern 1: Individual tie cell violation
        violation_pattern = re.compile(
            r'Tie cell violation at \(([\d.]+),\s*([\d.]+)\)\s*\(([\d.]+),\s*([\d.]+)\)\s*for pin (\S+) of instance (.+)\.'
        )
        
        # Pattern 2: Summary violation count by type
        summary_count_pattern = re.compile(r'Number of (\w+)\s+viol\(s\):\s*(\d+)')
        
        # Pattern 3: Total violation count
        total_count_pattern = re.compile(r'(\d+)\s+total\s+(?:info|viol)\(s\)\s+created\.')
        
        # Pattern 4: Violation section header
        section_header_pattern = re.compile(r'^(\w+(?:\s+\w+)*)\s+Viol:')
        
        # Pattern 5: Design name from report header
        design_name_pattern = re.compile(r'#\s*Design:\s+(\S+)')
        
        # Pattern 6: No problems found indicator
        no_problems_pattern = re.compile(r'Found no problems or warnings\.')
        
        # 3. Parse each input file for tie cell violations
        for file_path in valid_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line_num, line in enumerate(f, 1):
                        # Extract design name
                        design_match = design_name_pattern.search(line)
                        if design_match:
                            metadata['design_name'] = design_match.group(1).strip()
                            continue
                        
                        # Check for clean report (no violations)
                        no_problems_match = no_problems_pattern.search(line)
                        if no_problems_match:
                            metadata['clean_report'] = True
                            continue
                        
                        # Detect violation section headers
                        section_match = section_header_pattern.match(line)
                        if section_match:
                            current_violation_type = section_match.group(1).strip()
                            continue
                        
                        # Extract individual violations
                        viol_match = violation_pattern.search(line)
                        if viol_match:
                            x1_coord, y1_coord, x2_coord, y2_coord, pin_name, instance_path = viol_match.groups()
                            
                            # Create violation item with full context
                            # Format: {instance_path}/{pin_name} | Location: ({x1}, {y1})
                            violation_name = f"{instance_path}/{pin_name} | Location: ({x1_coord}, {y1_coord})"
                            
                            items.append({
                                'name': violation_name,
                                'instance': instance_path,
                                'pin': pin_name,
                                'x1': x1_coord,
                                'y1': y1_coord,
                                'x2': x2_coord,
                                'y2': y2_coord,
                                'violation_type': current_violation_type,
                                'line_number': line_num,
                                'file_path': str(file_path)
                            })
                            continue
                        
                        # Extract summary counts
                        summary_match = summary_count_pattern.search(line)
                        if summary_match:
                            viol_type, count = summary_match.groups()
                            metadata[f'{viol_type}_violations'] = int(count)
                            continue
                        
                        # Extract total count
                        total_match = total_count_pattern.search(line)
                        if total_match:
                            total_violations = int(total_match.group(1))
                            metadata['total_violations'] = total_violations
                            continue
                            
            except Exception as e:
                errors.append(f"Error parsing {file_path}: {str(e)}")
        
        # Validate counts
        if total_violations > 0 and len(items) != total_violations:
            errors.append(
                f"Mismatch: Parsed {len(items)} violations but summary reports {total_violations}"
            )
        
        # 4. Store frequently reused data on self
        self._parsed_items = items
        self._metadata = metadata
        self._total_violations = total_violations
        
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
        Type 1: Boolean check without waiver support.

        Checks for tie cell violations (inputs tied directly to power rails).
        PASS if no violations found, FAIL if any violations exist.
        """
        violations = self._type1_core_logic()

        # Build found_items from clean designs (designs with no violations)
        data = self._parse_input_files()
        metadata = data.get('metadata', {})

        found_items = {}
        if not violations:
            # No violations - design is clean
            design_name = metadata.get('design_name', 'Design')
            found_items[design_name] = {
                'name': design_name,
                'line_number': 0,
                'file_path': metadata.get('file_path', 'N/A')
            }

        # FIXED: Pass violations dict directly (not list)
        return self.build_complete_output(
            found_items=found_items,
            missing_items=violations,
            found_desc=self.FOUND_DESC_TYPE1_4,
            missing_desc=self.MISSING_DESC_TYPE1_4,
            found_reason=self.FOUND_REASON_TYPE1_4,
            missing_reason=self.MISSING_REASON_TYPE1_4
        )

    def _type1_core_logic(self) -> dict[str, dict]:
        """
        Core Type 1 boolean check logic (shared by Type 1 and Type 4).

        Parses tie cell violation reports and extracts all violations.

        Returns:
            Dict of violations: {violation_name: {'line_number': ..., 'file_path': ..., 'reason': ...}}
            Empty dict if no violations found.
        """
        data = self._parse_input_files()
        items = data.get('items', [])
        metadata = data.get('metadata', {})
        errors = data.get('errors', [])

        violations = {}

        # Check for parsing errors
        if errors:
            error_msg = '; '.join(errors)
            violations['parsing_error'] = {
                'name': 'parsing_error',
                'line_number': 0,
                'file_path': metadata.get('file_path', 'N/A'),
                'reason': f"Report parsing failed: {error_msg}"
            }
            return violations

        # Extract violations from parsed items
        for item in items:
            violation_name = item.get('name', 'unknown_violation')
            instance_path = item.get('instance', 'unknown_instance')
            pin_name = item.get('pin', '')
            x1_coord = item.get('x1', '')
            y1_coord = item.get('y1', '')
            violation_type = item.get('violation_type', 'tie cell violation')

            # Build detailed reason
            reason_parts = [violation_type]
            if pin_name:
                reason_parts.append(f"Pin: {pin_name}")
            if x1_coord and y1_coord:
                reason_parts.append(f"Location: ({x1_coord}, {y1_coord})")

            violations[violation_name] = {
                'name': violation_name,
                'line_number': item.get('line_number', 0),
                'file_path': item.get('file_path', metadata.get('file_path', 'N/A')),
                'reason': ' | '.join(reason_parts)
            }

        return violations

    # =========================================================================
    # Type 4: Boolean Check with Waiver Logic
    # =========================================================================

    def _execute_type4(self) -> CheckResult:
        """
        Type 4: Boolean check with waiver support (reuses Type 1 core logic).

        Checks for tie cell violations with waiver matching:
        - Violations matching waive_items → waived (PASS)
        - Violations not matching waivers → unwaived (FAIL)
        - Unused waivers → WARNING
        """
        # Step 1: Get violations using Type 1's core logic
        violations = self._type1_core_logic()

        # Build found_items from clean designs
        data = self._parse_input_files()
        metadata = data.get('metadata', {})

        found_items = {}
        if not violations:
            # No violations - design is clean
            design_name = metadata.get('design_name', 'Design')
            found_items[design_name] = {
                'name': design_name,
                'line_number': 0,
                'file_path': metadata.get('file_path', 'N/A')
            }

        # Step 2: Parse waiver configuration
        # FIXED: Use waivers.get() instead of get_waive_items()
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
        # FIXED: Pass dicts directly (not lists)
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

        # FIXED: Pass dicts directly (not lists)
        return self.build_complete_output(
            found_items=found_items,
            missing_items=missing_items,
            found_desc=self.FOUND_DESC_TYPE2_3,
            missing_desc=self.MISSING_DESC_TYPE2_3,
            found_reason=self.FOUND_REASON_TYPE2_3,
            missing_reason=self.MISSING_REASON_TYPE2_3
        )

    def _type2_core_logic(self) -> tuple[dict[str, dict], dict[str, dict]]:
        """
        Core Type 2 pattern matching logic (shared by Type 2 and Type 3).

        Returns:
            Tuple of (found_items, missing_items)
            - found_items: {item_name: {'name': ..., 'line_number': ..., 'file_path': ...}}
            - missing_items: {item_name: {'name': ..., 'line_number': ..., 'file_path': ..., 'reason': ...}}
        """
        data = self._parse_input_files()
        items = data.get('items', [])

        requirements = self.item_data.get('requirements', {})
        pattern_items = requirements.get('pattern_items', [])

        found_items = {}
        missing_items = {}

        # Check each required pattern (instance pin) for tie cell violations
        for pattern in pattern_items:
            matched = False
            for item in items:
                # Build full instance pin identifier: {instance_path}/{pin_name}
                item_identifier = f"{item['instance']}/{item['pin']}"

                # EXACT MATCH: pattern_items are complete instance pin names
                if pattern.lower() == item_identifier.lower():
                    # Pattern found in violations - this is a FAIL case
                    # Store violation details for reporting
                    missing_items[pattern] = {
                        'name': pattern,
                        'line_number': item.get('line_number', 0),
                        'file_path': item.get('file_path', 'N/A'),
                        'reason': f"Tie cell violation at location ({item.get('x1', 'N/A')}, {item.get('y1', 'N/A')})"
                    }
                    matched = True
                    break

            if not matched:
                # Pattern not found in violations - this is a PASS case (no violation)
                found_items[pattern] = {
                    'name': pattern,
                    'line_number': 0,
                    'file_path': 'N/A'
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
        # FIXED: Use waivers.get() instead of get_waive_items()
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)

        # Step 3: Split violations into waived and unwaived
        found_items = {}
        waived_items = {}
        missing_items = {}
        used_waivers = set()

        # Process found_items_base (no waiver needed - clean items)
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
        # FIXED: Pass dicts directly (not lists)
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


def main():
    """Main entry point."""
    checker = Check_8_0_0_12()
    checker.init_checker(Path(__file__))
    result = checker.execute_check()
    checker.write_output(result)
    return 0 if result.is_pass else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())