################################################################################
# Script Name: IMP-2-0-0-11.py
#
# Purpose:
#   List BEOL dummy rule deck name. eg: Dummy_BEOL_Pegasus_3nm_E_17M_1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2Yx2R_014.11_1a
#
# Logic:
#   - Parse BEOL_pvl.log to extract BEOL dummy rule deck name from include statements
#   - Extract rule deck filename from include path (e.g., Dummy_BEOL_Pegasus_5nm_014.13_1a.M16)
#   - For Type 1/4: Verify rule deck name exists in log file
#   - For Type 2/3: Compare extracted rule deck name against expected golden value
#   - Support waiver for rule deck name mismatches (Type 3/4)
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
class Check_2_0_0_11(InputFileParserMixin, OutputBuilderMixin, WaiverHandlerMixin, BaseChecker):
    """
    IMP-2-0-0-11: List BEOL dummy rule deck name. eg: Dummy_BEOL_Pegasus_3nm_E_17M_1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2Yx2R_014.11_1a
    
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
    FOUND_DESC_TYPE1_4 = "BEOL dummy rule deck name found in PVL log"
    MISSING_DESC_TYPE1_4 = "BEOL dummy rule deck name not found in PVL log"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_DESC_TYPE2_3 = "BEOL dummy rule deck name matched expected pattern"
    MISSING_DESC_TYPE2_3 = "BEOL dummy rule deck name does not match expected pattern"
    
    # All Types (waiver description unified)
    WAIVED_DESC = "BEOL dummy rule deck name mismatch waived"
    
    # ⭐ REASON CONSTANTS - Split by Type semantics (API-025)
    # ALL Types pass found_reason/missing_reason, but use different constants
    
    # Type 1/4: Boolean checks - emphasize "found/not found" (existence)
    FOUND_REASON_TYPE1_4 = "BEOL dummy rule deck name successfully extracted from include statement"
    MISSING_REASON_TYPE1_4 = "BEOL dummy rule deck name not found in include statements or log file is empty"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_REASON_TYPE2_3 = "BEOL dummy rule deck name matched and validated against expected golden value"
    MISSING_REASON_TYPE2_3 = "BEOL dummy rule deck name does not match expected golden value or pattern not satisfied"
    
    # Waiver-related (Type 3/4 only)
    WAIVED_BASE_REASON = "BEOL dummy rule deck name mismatch waived per design team approval"
    UNUSED_WAIVER_REASON = "Waiver not matched - no corresponding BEOL rule deck mismatch found"
    
    def __init__(self):
        """Initialize the checker."""
        super().__init__(
            check_module="2.0_TECHFILE_AND_RULE_DECK_CHECK",
            item_id="IMP-2-0-0-11",
            item_desc="List BEOL dummy rule deck name. eg: Dummy_BEOL_Pegasus_3nm_E_17M_1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2Yx2R_014.11_1a"
        )
        # Custom member variables for parsed data
        self._parsed_items: List[Dict[str, Any]] = []
        self._metadata: Dict[str, str] = {}
        self._beol_rule_deck_name: Optional[str] = None
    
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
        Parse BEOL_pvl.log to extract BEOL dummy rule deck name.
        
        Searches for include statements containing Dummy_BEOL_Pegasus pattern
        and extracts the rule deck filename.
        
        Returns:
            Dict with parsed data:
            - 'items': List[Dict] - BEOL rule deck name(s) found
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
        beol_rule_deck_name = None
        
        # 3. Parse each input file for BEOL dummy rule deck name
        # Pattern 1: Extract from include statement with full path
        pattern1 = r'include\s+"[^"]*/(Dummy_BEOL_Pegasus_[^"]+)"'
        # Pattern 2: Alternative pattern for rule deck name without path
        pattern2 = r'Dummy_BEOL_Pegasus_\S+'
        
        for file_path in valid_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line_num, line in enumerate(f, 1):
                        # Try pattern 1 first (include statement with path)
                        match1 = re.search(pattern1, line)
                        if match1:
                            beol_rule_deck_name = match1.group(1)
                            items.append({
                                'name': beol_rule_deck_name,
                                'line_number': line_num,
                                'file_path': str(file_path),
                                'line_content': line.strip(),
                                'type': 'beol_rule_deck'
                            })
                            # Take first match only
                            break
                        
                        # Try pattern 2 as fallback
                        match2 = re.search(pattern2, line)
                        if match2:
                            beol_rule_deck_name = match2.group(0)
                            items.append({
                                'name': beol_rule_deck_name,
                                'line_number': line_num,
                                'file_path': str(file_path),
                                'line_content': line.strip(),
                                'type': 'beol_rule_deck'
                            })
                            # Take first match only
                            break
                    
                    # If found in this file, stop processing other files
                    if beol_rule_deck_name:
                        break
                        
            except Exception as e:
                errors.append(f"Error parsing {file_path}: {str(e)}")
        
        # 4. Store frequently reused data on self
        self._parsed_items = items
        self._beol_rule_deck_name = beol_rule_deck_name
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

        Verifies that BEOL dummy rule deck name can be extracted from the PVL log file.
        - PASS: Rule deck name found in include statements
        - FAIL: Rule deck name not found or log file is empty
        """
        violations = self._type1_core_logic()

        # Build found_items from successfully extracted rule deck names
        data = self._parse_input_files()
        items = data.get('items', [])

        found_items = {}
        for item in items:
            item_name = item.get('name', 'unknown')
            found_items[item_name] = {
                'name': item_name,
                'line_number': item.get('line_number', 0),
                'file_path': item.get('file_path', 'N/A')
            }

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

        Extracts BEOL dummy rule deck name from include statements in BEOL_pvl.log.
        Returns violations if no rule deck name is found.

        Returns:
            Dict of violations: {item_name: {'line_number': ..., 'file_path': ..., 'reason': ...}}
            Empty dict if rule deck name is successfully extracted.
        """
        data = self._parse_input_files()
        items = data.get('items', [])
        errors = data.get('errors', [])
        metadata = data.get('metadata', {})

        violations = {}

        # Check for parsing errors first
        if errors:
            for error in errors:
                error_key = f"parse_error_{len(violations)}"
                violations[error_key] = {
                    'line_number': 0,
                    'file_path': metadata.get('log_file', 'N/A'),
                    'reason': error
                }

        # Check if any rule deck names were found
        if not items:
            violations['no_rule_deck_found'] = {
                'line_number': 0,
                'file_path': metadata.get('log_file', 'N/A'),
                'reason': 'BEOL dummy rule deck name not found in include statements or log file is empty'
            }

        return violations

    # =========================================================================
    # Type 4: Boolean Check with Waiver Logic
    # =========================================================================

    def _execute_type4(self) -> CheckResult:
        """
        Type 4: Boolean check with waiver support (reuses Type 1 core logic).

        Same boolean check as Type 1, but violations can be waived:
        - Clean items (rule deck found): PASS
        - Violations + waived: PASS
        - Violations + NOT waived: FAIL
        """
        # Step 1: Get violations using Type 1's core logic
        violations = self._type1_core_logic()

        # Build found_items from successfully extracted rule deck names
        data = self._parse_input_files()
        items = data.get('items', [])

        found_items = {}
        for item in items:
            item_name = item.get('name', 'unknown')
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

    def _type2_core_logic(self) -> tuple[dict[str, dict], dict[str, dict]]:
        """
        Core Type 2 pattern matching logic (shared by Type 2 and Type 3).

        Returns:
            Tuple of (found_items, missing_items)
            - found_items: {item_name: {'line_number': ..., 'file_path': ...}}
            - missing_items: {item_name: {'line_number': ..., 'file_path': ..., 'reason': ...}}
        """
        data = self._parse_input_files()
        items = data.get('items', [])

        requirements = self.item_data.get('requirements', {})
        pattern_items = requirements.get('pattern_items', [])

        found_items = {}
        missing_items = {}

        # Get expected golden BEOL rule deck name (first pattern item)
        if not pattern_items:
            missing_items['No pattern defined'] = {
                'line_number': 0,
                'file_path': 'N/A',
                'reason': 'No expected BEOL rule deck name defined in pattern_items'
            }
            return found_items, missing_items

        golden_beol = pattern_items[0]

        # Check if any BEOL rule deck was found in log file
        if not items:
            missing_items[golden_beol] = {
                'line_number': 0,
                'file_path': 'N/A',
                'reason': f'Expected BEOL rule deck "{golden_beol}" not found in log file'
            }
            return found_items, missing_items

        # Extract actual BEOL rule deck name from parsed items
        actual_beol = items[0]['name']
        actual_line = items[0].get('line_number', 0)
        actual_file = items[0].get('file_path', 'N/A')

        # Compare actual vs expected (exact match, case-sensitive for rule deck names)
        if actual_beol == golden_beol:
            # Match - add to found_items
            found_items[actual_beol] = {
                'line_number': actual_line,
                'file_path': actual_file
            }
        else:
            # Mismatch - add to missing_items with detailed reason
            missing_items[golden_beol] = {
                'line_number': actual_line,
                'file_path': actual_file,
                'reason': f'Expected "{golden_beol}" but found "{actual_beol}"'
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

        # Process found_items_base (no waiver needed - already matched golden)
        for item_name, item_data in found_items_base.items():
            found_items[item_name] = item_data

        # Process violations (mismatches) with waiver matching
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
    checker = Check_2_0_0_11()
    checker.init_checker(Path(__file__))
    result = checker.execute_check()
    checker.write_output(result)
    return 0 if result.is_pass else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())