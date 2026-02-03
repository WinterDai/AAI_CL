################################################################################
# Script Name: IMP-2-0-0-14.py
#
# Purpose:
#   List EM irxc rule deck name. eg: ICT_EM_v1d0p1a/cln3p_1p17m+ut-alrdl_1xa1xb1xc1xd1ya1yb4y2yy2yx2r_shdmim.ictem
#
# Logic:
#   - Parse Voltus log files to extract EM rule deck path using pattern "Info: Using EM Rules from : '<path>'"
#   - Extract version directory and filename from absolute path (last two path components)
#   - For Type 1/4: Verify EM rule deck information exists in log
#   - For Type 2/3: Validate extracted EM rule deck matches expected pattern_items (golden EM rule deck)
#   - Support waiver for EM rule deck version mismatches (Type 3/4)
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
class Check_2_0_0_14(InputFileParserMixin, OutputBuilderMixin, WaiverHandlerMixin, BaseChecker):
    """
    IMP-2-0-0-14: List EM irxc rule deck name. eg: ICT_EM_v1d0p1a/cln3p_1p17m+ut-alrdl_1xa1xb1xc1xd1ya1yb4y2yy2yx2r_shdmim.ictem
    
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
    FOUND_DESC_TYPE1_4 = "EM rule deck information found in Voltus log"
    MISSING_DESC_TYPE1_4 = "EM rule deck information not found in Voltus log"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_DESC_TYPE2_3 = "EM rule deck matched expected configuration"
    MISSING_DESC_TYPE2_3 = "EM rule deck does not match expected configuration"
    
    # All Types (waiver description unified)
    WAIVED_DESC = "EM rule deck mismatch waived"
    
    # ⭐ REASON CONSTANTS - Split by Type semantics (API-025)
    # ALL Types pass found_reason/missing_reason, but use different constants
    
    # Type 1/4: Boolean checks - emphasize "found/not found" (existence)
    FOUND_REASON_TYPE1_4 = "EM rule deck path successfully extracted from Voltus run log"
    MISSING_REASON_TYPE1_4 = "EM rule deck path not found in Voltus run log - check if EM analysis was enabled"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_REASON_TYPE2_3 = "EM rule deck identifier matched expected golden value and validated"
    MISSING_REASON_TYPE2_3 = "EM rule deck identifier does not match expected golden value or extraction failed"
    
    # Waiver-related (Type 3/4 only)
    WAIVED_BASE_REASON = "EM rule deck version difference waived per design team approval"
    UNUSED_WAIVER_REASON = "Waiver not matched - no corresponding EM rule deck mismatch found"
    
    def __init__(self):
        """Initialize the checker."""
        super().__init__(
            check_module="2.0_TECHFILE_AND_RULE_DECK_CHECK",
            item_id="IMP-2-0-0-14",
            item_desc="List EM irxc rule deck name. eg: ICT_EM_v1d0p1a/cln3p_1p17m+ut-alrdl_1xa1xb1xc1xd1ya1yb4y2yy2yx2r_shdmim.ictem"
        )
        # Custom member variables for parsed data
        self._parsed_items: List[Dict[str, Any]] = []
        self._metadata: Dict[str, str] = {}
        self._em_rule_deck: Optional[str] = None
    
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
        Parse Voltus log files to extract EM rule deck information.
        
        Extracts EM rule deck path from Voltus log using pattern:
        "Info: Using EM Rules from : '<path>'"
        
        Then extracts version directory and filename (last two path components):
        From: "/process/.../ictem_v1d2p1a/cln5_1p16m+ut-alrdl_1x1xb1xe1ya1yb6y2yy2r_shdmim.ictem"
        To: "ictem_v1d2p1a/cln5_1p16m+ut-alrdl_1x1xb1xe1ya1yb6y2yy2r_shdmim.ictem"
        
        Returns:
            Dict with parsed data:
            - 'items': List[Dict] - EM rule deck entries with metadata
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
        
        # Pattern 1: Extract EM rule deck path from Voltus log
        # Example: "Info: Using EM Rules from : '/process/tsmcN5/data/g/QRC/16M1X1Xb1Xe1Ya1Yb6Y2Yy2R_SHDMIM_UT/ictem_v1d2p1a/cln5_1p16m+ut-alrdl_1x1xb1xe1ya1yb6y2yy2r_shdmim.ictem'"
        em_path_pattern = re.compile(r"Info:\s+Using\s+EM\s+Rules\s+from\s+:\s+'([^']+)'")
        
        # Pattern 2: Extract version directory and filename (last two path components)
        # Example: From "/process/.../ictem_v1d2p1a/cln5_1p16m.ictem" -> "ictem_v1d2p1a/cln5_1p16m.ictem"
        em_rule_pattern = re.compile(r'/([^/]+/[^/]+\.ictem)$')
        
        # 3. Parse each input file for EM rule deck information
        for file_path in valid_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line_num, line in enumerate(f, 1):
                        # Search for EM rule deck path
                        match = em_path_pattern.search(line)
                        if match:
                            em_path = match.group(1)
                            
                            # Extract version/filename from absolute path
                            rule_match = em_rule_pattern.search(em_path)
                            if rule_match:
                                em_rule = rule_match.group(1)
                                
                                items.append({
                                    'name': em_rule,
                                    'line_number': line_num,
                                    'file_path': str(file_path),
                                    'type': 'em_rule_deck',
                                    'full_path': em_path
                                })
                                
                                # Store the EM rule deck for easy access
                                self._em_rule_deck = em_rule
                            else:
                                # Could not extract version/filename format
                                errors.append(f"Could not extract EM rule deck format from path: {em_path} at {file_path}:{line_num}")
            except Exception as e:
                errors.append(f"Error parsing {file_path}: {str(e)}")
        
        # 4. Store frequently reused data on self
        self._parsed_items = items
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
        """
        Type 1: Boolean check without waiver support.

        Verifies that EM rule deck information exists in Voltus log file.
        PASS if EM rule deck path is successfully extracted.
        FAIL if EM rule deck information is missing or cannot be parsed.
        """
        violations = self._type1_core_logic()

        # Build found_items from successfully extracted EM rule deck
        data = self._parse_input_files()
        items = data.get('items', [])

        found_items = {}
        if items:
            # EM rule deck successfully extracted
            for item in items:
                em_rule = item.get('name', '')
                found_items[em_rule] = {
                    'line_number': item.get('line_number', 0),
                    'file_path': item.get('file_path', 'N/A')
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

        Extracts EM rule deck information from Voltus log file and validates existence.

        Returns:
            Dict of violations: {item_name: {'line_number': ..., 'file_path': ..., 'reason': ...}}
            Empty dict if EM rule deck information is successfully extracted.
        """
        data = self._parse_input_files()
        items = data.get('items', [])
        errors = data.get('errors', [])

        violations = {}

        # Check for parsing errors
        if errors:
            for idx, error in enumerate(errors):
                violations[f"parse_error_{idx}"] = {
                    'line_number': 0,
                    'file_path': 'N/A',
                    'reason': error
                }

        # Check if EM rule deck information was found
        if not items:
            violations['em_rule_deck_missing'] = {
                'line_number': 0,
                'file_path': 'N/A',
                'reason': 'EM rule deck information not found in Voltus log file'
            }

        return violations

    # =========================================================================
    # Type 4: Boolean Check with Waiver Logic
    # =========================================================================

    def _execute_type4(self) -> CheckResult:
        """
        Type 4: Boolean check with waiver support (reuses Type 1 core logic).

        Same boolean check as Type 1, but supports waiving violations.
        Useful when EM rule deck information is missing but acceptable for certain scenarios
        (e.g., non-EM analysis runs, informational checks).
        """
        # Step 1: Get violations using Type 1's core logic
        violations = self._type1_core_logic()

        # Build found_items from successfully extracted EM rule deck
        data = self._parse_input_files()
        items = data.get('items', [])

        found_items = {}
        if items:
            # EM rule deck successfully extracted
            for item in items:
                em_rule = item.get('name', '')
                found_items[em_rule] = {
                    'line_number': item.get('line_number', 0),
                    'file_path': item.get('file_path', 'N/A')
                }

        # Step 2: Parse waiver configuration
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

    def _type2_core_logic(self) -> Tuple[Dict[str, Dict], Dict[str, Dict]]:
        """
        Core Type 2 pattern matching logic (shared by Type 2 and Type 3).

        Returns:
            Tuple of (found_items, missing_items)
            - found_items: {em_rule_deck: {'line_number': ..., 'file_path': ...}}
            - missing_items: {pattern: {'line_number': ..., 'file_path': ..., 'reason': ...}}
        """
        data = self._parse_input_files()
        items = data.get('items', [])

        requirements = self.item_data.get('requirements', {})
        pattern_items = requirements.get('pattern_items', [])

        found_items = {}
        missing_items = {}

        # Extract EM rule deck from parsed items
        if not items:
            # No EM rule deck found in input files
            for pattern in pattern_items:
                missing_items[pattern] = {
                    'line_number': 0,
                    'file_path': 'N/A',
                    'reason': f'EM rule deck not found in log files (expected: {pattern})'
                }
            return found_items, missing_items

        # Get the extracted EM rule deck (should be only one)
        extracted_em_rule = items[0].get('name', '')
        line_number = items[0].get('line_number', 0)
        file_path = items[0].get('file_path', 'N/A')

        # Check if extracted EM rule deck matches any pattern_items (EXACT MATCH)
        matched = False
        for pattern in pattern_items:
            if pattern.lower() == extracted_em_rule.lower():
                found_items[extracted_em_rule] = {
                    'line_number': line_number,
                    'file_path': file_path
                }
                matched = True
                break

        if not matched:
            # EM rule deck found but doesn't match expected patterns
            missing_items[extracted_em_rule] = {
                'line_number': line_number,
                'file_path': file_path,
                'reason': f'EM rule deck mismatch: Found={extracted_em_rule}, Expected one of: {", ".join(pattern_items)}'
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
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)

        # Step 3: Initialize result collections
        found_items = {}
        waived_items = {}
        missing_items = {}
        used_waivers = set()

        # Step 4: Process found_items_base (no waiver needed - these are clean matches)
        for item_name, item_data in found_items_base.items():
            found_items[item_name] = item_data

        # Step 5: Process violations with waiver matching
        for viol_name, viol_data in violations.items():
            matched_waiver = self.match_waiver_entry(viol_name, waive_dict)
            if matched_waiver:
                waived_items[viol_name] = viol_data
                used_waivers.add(matched_waiver)
            else:
                missing_items[viol_name] = viol_data

        # Step 6: Find unused waivers
        unused_waivers = [w for w in waive_dict.keys() if w not in used_waivers]

        # Step 7: Build output
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
    checker = Check_2_0_0_14()
    checker.init_checker(Path(__file__))
    result = checker.execute_check()
    checker.write_output(result)
    return 0 if result.is_pass else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())