################################################################################
# Script Name: IMP-2-0-0-00.py
#
# Purpose:
#   List Innovus Tech Lef name. eg:N16_Encounter_11M_2Xa1Xd3Xe2Y2R_UTRDL_9T_PODE_1.2a.tlef
#
# Logic:
#   - Parse Innovus log file to extract technology LEF filename from "Loading LEF file" statements
#   - Extract tech LEF path using pattern: r'\[.*?\]\s+Loading LEF file\s+([^\s]+\.tlef)'
#   - For Type 1/4: Verify tech LEF file was successfully loaded (existence check)
#   - For Type 2/3: Compare extracted tech LEF against golden reference from pattern_items
#   - Support waiver for tech LEF filename mismatches (Type 3/4)
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
class Check_2_0_0_00(InputFileParserMixin, OutputBuilderMixin, WaiverHandlerMixin, BaseChecker):
    """
    IMP-2-0-0-00: List Innovus Tech Lef name. eg:N16_Encounter_11M_2Xa1Xd3Xe2Y2R_UTRDL_9T_PODE_1.2a.tlef
    
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
    FOUND_DESC_TYPE1_4 = "Technology LEF file found in Innovus log"
    MISSING_DESC_TYPE1_4 = "Technology LEF file not found in Innovus log"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_DESC_TYPE2_3 = "Technology LEF filename matched expected pattern"
    MISSING_DESC_TYPE2_3 = "Technology LEF filename does not match expected pattern"
    
    # All Types (waiver description unified)
    WAIVED_DESC = "Technology LEF mismatch waived"
    
    # ⭐ REASON CONSTANTS - Split by Type semantics (API-025)
    # ALL Types pass found_reason/missing_reason, but use different constants
    
    # Type 1/4: Boolean checks - emphasize "found/not found" (existence)
    FOUND_REASON_TYPE1_4 = "Technology LEF file successfully loaded in Innovus session"
    MISSING_REASON_TYPE1_4 = "No technology LEF file loading detected in Innovus log - check restoreDesign command"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_REASON_TYPE2_3 = "Technology LEF filename matched and validated against golden reference"
    MISSING_REASON_TYPE2_3 = "Technology LEF filename does not match golden reference - verify correct tech file is used"
    
    # Waiver-related (Type 3/4 only)
    WAIVED_BASE_REASON = "Technology LEF filename mismatch waived per design team approval"
    UNUSED_WAIVER_REASON = "Waiver entry not matched - no corresponding tech LEF mismatch found in log"
    
    def __init__(self):
        """Initialize the checker."""
        super().__init__(
            check_module="2.0_TECHFILE_AND_RULE_DECK_CHECK",
            item_id="IMP-2-0-0-00",
            item_desc="List Innovus Tech Lef name. eg:N16_Encounter_11M_2Xa1Xd3Xe2Y2R_UTRDL_9T_PODE_1.2a.tlef"
        )
        # Custom member variables for parsed data
        self._parsed_items: List[Dict[str, Any]] = []
        self._metadata: Dict[str, str] = {}
        self._tech_lef_path: Optional[str] = None
    
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
        Parse Innovus log files to extract technology LEF filename.
        
        Searches for "Loading LEF file" statements and extracts the .tlef file path.
        Pattern: r'\[.*?\]\s+Loading LEF file\s+([^\s]+\.tlef)'
        
        Returns:
            Dict with parsed data:
            - 'items': List[Dict] - Technology LEF files found (with metadata)
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
        tech_lef_path = None
        
        # Pattern to extract tech lef path from Loading LEF file statement
        loading_pattern = re.compile(r'\[.*?\]\s+Loading LEF file\s+([^\s]+\.tlef)', re.IGNORECASE)
        
        # 3. Parse each input file for technology LEF information
        for file_path in valid_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line_num, line in enumerate(f, 1):
                        # Search for Loading LEF file statement
                        match = loading_pattern.search(line)
                        if match:
                            tech_lef_full_path = match.group(1)
                            # Extract just the filename from the path
                            tech_lef_filename = Path(tech_lef_full_path).name
                            
                            # Store the tech LEF information
                            tech_lef_path = tech_lef_filename
                            items.append({
                                'name': tech_lef_filename,
                                'line_number': line_num,
                                'file_path': str(file_path),
                                'full_path': tech_lef_full_path,
                                'type': 'tech_lef'
                            })
                            # Typically only one tech LEF is loaded, break after first match
                            break
            except Exception as e:
                errors.append(f"Error parsing {file_path}: {str(e)}")
        
        # 4. Store frequently reused data on self
        self._parsed_items = items
        self._tech_lef_path = tech_lef_path
        
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
        
        Verifies that a technology LEF file is loaded in Innovus session.
        PASS if tech LEF file is found in log, FAIL if not found.
        """
        violations = self._type1_core_logic()
        
        # Build found_items from successfully loaded tech LEF files
        data = self._parse_input_files()
        items = data.get('items', [])
        
        # ⚠️ CRITICAL: found_items MUST be dict[str, dict], NOT list!
        found_items = {}
        for item in items:
            tlef_name = item.get('name', '')
            found_items[tlef_name] = {
                'name': tlef_name,
                'line_number': item.get('line_number', 0),
                'file_path': item.get('file_path', 'N/A')
            }
        
        # FIXED: Convert violations dict to missing_items dict (not list)
        missing_items = violations
        
        return self.build_complete_output(
            found_items=found_items,
            missing_items=missing_items,
            found_desc=self.FOUND_DESC_TYPE1_4,
            missing_desc=self.MISSING_DESC_TYPE1_4,
            found_reason=self.FOUND_REASON_TYPE1_4,
            missing_reason=self.MISSING_REASON_TYPE1_4
        )
    
    def _type1_core_logic(self) -> dict[str, dict]:
        """
        Core Type 1 boolean check logic (shared by Type 1 and Type 4).
        
        Checks if technology LEF file is loaded in Innovus log.
        
        Returns:
            Dict of violations: {item_name: {'line_number': ..., 'file_path': ..., 'reason': ...}}
            Empty dict if tech LEF file is found (check passes).
        """
        data = self._parse_input_files()
        items = data.get('items', [])
        errors = data.get('errors', [])
        
        violations = {}
        
        # Check for parsing errors first
        if errors:
            violations['parsing_error'] = {
                'line_number': 0,
                'file_path': 'N/A',
                'reason': f"Failed to parse input files: {'; '.join(errors)}"
            }
            return violations
        
        # Type 1 boolean check: Verify tech LEF file is loaded
        if not items:
            # No tech LEF file found in log - this is a violation
            violations['No tech LEF file found'] = {
                'line_number': 0,
                'file_path': data.get('metadata', {}).get('default_file', 'N/A'),
                'reason': 'No technology LEF file loading detected in Innovus log - check restoreDesign command'
            }
        
        return violations
    
    # =========================================================================
    # Type 2: Value Check
    # =========================================================================
    
    def _execute_type2(self) -> CheckResult:
        """Type 2: Pattern/value check without waiver support."""
        found_items, missing_items = self._type2_core_logic()
        
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
            - found_items: {tech_lef_filename: {'line_number': ..., 'file_path': ...}}
            - missing_items: {pattern: {'line_number': ..., 'file_path': ..., 'reason': ...}}
        """
        data = self._parse_input_files()
        items = data.get('items', [])
        
        requirements = self.item_data.get('requirements', {})
        pattern_items = requirements.get('pattern_items', [])
        
        found_items = {}
        missing_items = {}
        
        # Extract tech LEF filename from items (parsed from log)
        # items contain: [{'name': 'tech_lef_filename.tlef', 'line_number': N, 'file_path': 'log.logv'}]
        tech_lef_found = None
        tech_lef_data = None
        
        if items:
            # Get the first (and should be only) tech LEF entry
            tech_lef_found = items[0]['name']
            tech_lef_data = {
                'line_number': items[0].get('line_number', 0),
                'file_path': items[0].get('file_path', 'N/A')
            }
        
        # Check each pattern against found tech LEF
        for pattern in pattern_items:
            if tech_lef_found:
                # Extract just the filename from pattern (in case it contains path)
                pattern_filename = Path(pattern).name if '/' in pattern or '\\' in pattern else pattern
                
                # EXACT MATCH: Compare tech LEF filename against golden reference
                # Pattern is the complete filename to match
                if pattern_filename.lower() == tech_lef_found.lower():
                    found_items[tech_lef_found] = tech_lef_data
                else:
                    # Tech LEF found but doesn't match golden reference
                    missing_items[pattern] = {
                        'line_number': tech_lef_data['line_number'],
                        'file_path': tech_lef_data['file_path'],
                        'reason': f'Technology LEF filename does not match golden reference - verify correct tech file is used. Expect ({pattern})'
                    }
            else:
                # No tech LEF found in log
                missing_items[pattern] = {
                    'line_number': 0,
                    'file_path': 'N/A',
                    'reason': f'Technology LEF file not found in Innovus log - check if tech LEF was loaded. Expect ({pattern})'
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
        
        # Process found_items_base (tech LEF matched golden reference - no waiver needed)
        for item_name, item_data in found_items_base.items():
            found_items[item_name] = item_data
        
        # Process violations (tech LEF mismatch) with waiver matching
        for viol_name, viol_data in violations.items():
            # viol_name is the pattern (golden reference filename)
            # Need to check if the actual tech LEF filename is waived
            # Extract actual tech LEF from viol_data or re-parse
            data = self._parse_input_files()
            items = data.get('items', [])
            actual_tech_lef = items[0]['name'] if items else viol_name
            
            # Match waiver against actual tech LEF filename (not pattern)
            matched_waiver = self.match_waiver_entry(actual_tech_lef, waive_dict)
            if matched_waiver:
                waived_items[actual_tech_lef] = {
                    'line_number': viol_data.get('line_number', 0),
                    'file_path': viol_data.get('file_path', 'N/A')
                }
                used_waivers.add(matched_waiver)
            else:
                missing_items[viol_name] = viol_data
        
        # Step 4: Find unused waivers
        unused_waivers = [w for w in waive_dict.keys() if w not in used_waivers]
        
        # Step 5: Build output
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
    # Type 4: Boolean Check with Waiver Logic
    # =========================================================================
    
    def _execute_type4(self) -> CheckResult:
        """
        Type 4: Boolean check with waiver support (reuses Type 1 core logic).
        
        Same boolean check as Type 1, but violations can be waived.
        PASS if tech LEF file is found OR violation is waived.
        """
        # Step 1: Get violations using Type 1's core logic
        violations = self._type1_core_logic()
        
        # Build found_items from successfully loaded tech LEF files
        data = self._parse_input_files()
        items = data.get('items', [])
        
        # ⚠️ CRITICAL: found_items MUST be dict[str, dict], NOT list!
        found_items = {}
        for item in items:
            tlef_name = item.get('name', '')
            found_items[tlef_name] = {
                'name': tlef_name,
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
    # Helper Methods (Optional - Add as needed)
    # =========================================================================
    
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
    checker = Check_2_0_0_00()
    checker.init_checker(Path(__file__))
    result = checker.execute_check()
    checker.write_output(result)
    return 0 if result.is_pass else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())