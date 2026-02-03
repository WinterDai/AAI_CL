################################################################################
# Script Name: IMP-2-0-0-10.py
#
# Purpose:
#   List FEOL dummy rule deck name. eg: Dummy_FEOL_Pegasus_3nm_E_17M_1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2Yx2R_014.11_1a
#
# Logic:
#   - Parse FEOL_pvl.log to extract FEOL rule deck filename from include statements
#   - Extract filename from both Windows (backslash) and Unix (forward slash) paths
#   - Verify extracted filename matches expected pattern: Dummy_FEOL_Pegasus_*
#   - For Type 1/4: Check if FEOL rule deck name was successfully extracted
#   - For Type 2/3: Validate extracted name against golden value from pattern_items
#   - Support waiver for mismatched FEOL rule deck names
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
class Check_2_0_0_10(InputFileParserMixin, OutputBuilderMixin, WaiverHandlerMixin, BaseChecker):
    """
    IMP-2-0-0-10: List FEOL dummy rule deck name. eg: Dummy_FEOL_Pegasus_3nm_E_17M_1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2Yx2R_014.11_1a
    
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
    FOUND_DESC_TYPE1_4 = "FEOL dummy rule deck name found in PVL log"
    MISSING_DESC_TYPE1_4 = "FEOL dummy rule deck name not found in PVL log"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_DESC_TYPE2_3 = "FEOL dummy rule deck name matched expected value"
    MISSING_DESC_TYPE2_3 = "FEOL dummy rule deck name does not match expected value"
    
    # All Types (waiver description unified)
    WAIVED_DESC = "FEOL dummy rule deck name mismatch waived"
    
    # ⭐ REASON CONSTANTS - Split by Type semantics (API-025)
    # ALL Types pass found_reason/missing_reason, but use different constants
    
    # Type 1/4: Boolean checks - emphasize "found/not found" (existence)
    FOUND_REASON_TYPE1_4 = "FEOL dummy rule deck name successfully extracted from include statement"
    MISSING_REASON_TYPE1_4 = "FEOL dummy rule deck include statement not found or could not be parsed from log file"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_REASON_TYPE2_3 = "FEOL dummy rule deck name matched and validated against expected golden value"
    MISSING_REASON_TYPE2_3 = "FEOL dummy rule deck name does not match expected golden value or pattern not satisfied"
    
    # Waiver-related (Type 3/4 only)
    WAIVED_BASE_REASON = "FEOL dummy rule deck name mismatch waived per design team approval"
    UNUSED_WAIVER_REASON = "Waiver entry not matched - no corresponding FEOL rule deck mismatch found"
    
    def __init__(self):
        """Initialize the checker."""
        super().__init__(
            check_module="2.0_TECHFILE_AND_RULE_DECK_CHECK",
            item_id="IMP-2-0-0-10",
            item_desc="List FEOL dummy rule deck name. eg: Dummy_FEOL_Pegasus_3nm_E_17M_1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2Yx2R_014.11_1a"
        )
        # Custom member variables for parsed data
        self._parsed_items: List[Dict[str, Any]] = []
        self._metadata: Dict[str, str] = {}
        self._feol_rule: Optional[str] = None
    
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
        Parse input files to extract FEOL dummy rule deck name from include statements.
        
        Scans FEOL_pvl.log for include statements containing FEOL rule deck filenames.
        Supports both Windows (backslash) and Unix (forward slash) path separators.
        
        Patterns:
        - Windows: include "C:\\path\\to\\Dummy_FEOL_Pegasus_5nm_014.13_1a.FEOL"
        - Unix: include "/path/to/Dummy_FEOL_Pegasus_3nm_E_17M_1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2Yx2R_014.11_1a.FEOL"
        
        Returns:
            Dict with parsed data:
            - 'items': List[Dict] - Extracted FEOL rule deck filenames
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
        feol_rule = None
        
        # 3. Parse each input file for FEOL rule deck information
        # Pattern 1: Extract FEOL rule deck filename from include statement (Windows path)
        pattern1 = re.compile(r'include\s+"[^"]*\\([^\\]+\.FEOL)"', re.IGNORECASE)
        # Pattern 2: Extract FEOL rule deck filename from include statement (Unix path)
        pattern2 = re.compile(r'include\s+"[^"]*/([^/]+\.FEOL)"', re.IGNORECASE)
        # Pattern 3: Alternative pattern using case-insensitive matching for "Dummy_FEOL"
        pattern3 = re.compile(r'include\s+".*?([Dd]ummy_FEOL_[^"\\]+\.FEOL)"', re.IGNORECASE)
        
        for file_path in valid_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line_num, line in enumerate(f, 1):
                        # Skip commented lines
                        stripped_line = line.strip()
                        if stripped_line.startswith('#') or stripped_line.startswith('//'):
                            continue
                        
                        # Try all patterns to extract FEOL rule deck filename
                        match = pattern1.search(line) or pattern2.search(line) or pattern3.search(line)
                        
                        if match:
                            feol_filename = match.group(1)
                            
                            # Validate extracted name matches expected pattern
                            if 'Dummy_FEOL' in feol_filename or 'dummy_FEOL' in feol_filename.lower():
                                if feol_filename.endswith('.FEOL'):
                                    feol_rule = feol_filename
                                    items.append({
                                        'name': feol_filename,
                                        'line_number': line_num,
                                        'file_path': str(file_path),
                                        'type': 'feol_rule_deck'
                                    })
                                    # Stop after finding the first match
                                    break
            except Exception as e:
                errors.append(f"Error parsing {file_path}: {str(e)}")
        
        # 4. Store frequently reused data on self
        self._parsed_items = items
        self._feol_rule = feol_rule
        
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

        Verifies that FEOL dummy rule deck name can be successfully extracted
        FAIL if include statement is missing or cannot be parsed.
        """
        violations = self._type1_core_logic()

        # Build found_items from successfully extracted FEOL rule deck names
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

        # FIXED: Pass dict directly, not list
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

        Extracts FEOL dummy rule deck name from PVL log file and validates
        that the include statement was found and successfully parsed.

        Returns:
            Dict of violations: {item_name: {'line_number': ..., 'file_path': ..., 'reason': ...}}
            Empty dict if FEOL rule deck name successfully extracted.
        """
        data = self._parse_input_files()
        items = data.get('items', [])
        errors = data.get('errors', [])
        metadata = data.get('metadata', {})

        violations = {}

        # Check if parsing encountered errors
        if errors:
            for error in errors:
                error_key = f"parsing_error_{len(violations)}"
                violations[error_key] = {
                    'line_number': 0,
                    'file_path': metadata.get('log_file', 'N/A'),
                    'reason': error
                }

        # Check if no FEOL rule deck name was extracted
        if not items:
            violations['feol_rule_deck_missing'] = {
                'line_number': 0,
                'file_path': metadata.get('log_file', 'N/A'),
                'reason': 'FEOL rule deck include statement not found in log file'
            }

        return violations

    # =========================================================================
    # Type 4: Boolean Check with Waiver Logic
    # =========================================================================

    def _execute_type4(self) -> CheckResult:
        """
        Type 4: Boolean check with waiver support (reuses Type 1 core logic).

        Same boolean check as Type 1 (verify FEOL rule deck name extraction),
        but adds waiver classification:
        - Violations can be waived (e.g., missing include statement acceptable)
        - Unwaived violations → FAIL
        - Waived violations → INFO with [WAIVER] tag
        - Unused waivers → WARN with [WAIVER] tag

        PASS if all violations are waived.
        """
        # Step 1: Get violations using Type 1's core logic
        violations = self._type1_core_logic()

        # Build found_items from successfully extracted FEOL rule deck names
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
        # FIXED: Pass dict directly, not list
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

        # FIXED: Pass dict directly, not list
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

        # Extract FEOL rule deck name from parsed items
        # items contain extracted filenames from include statements
        for item in items:
            item_name = item.get('name', '')
            # Report the extracted FEOL rule deck name
            found_items[item_name] = {
                'line_number': item.get('line_number', 0),
                'file_path': item.get('file_path', 'N/A')
            }

        # Validate against expected pattern (golden value)
        # pattern_items contains the expected FEOL rule deck filename
        if pattern_items:
            expected_name = pattern_items[0]  # Golden value

            # Check if expected name was found
            matched = False
            for item_name in found_items.keys():
                # EXACT MATCH (case-insensitive) - complete filename comparison
                if expected_name.lower() == item_name.lower():
                    matched = True
                    break

            if not matched:
                # Expected pattern not found - report as missing
                if found_items:
                    # We found a different FEOL rule deck name
                    actual_name = list(found_items.keys())[0]
                    missing_items[expected_name] = {
                        'line_number': 0,
                        'file_path': 'N/A',
                        'reason': f'Expected: {expected_name}, Found: {actual_name}'
                    }
                else:
                    # No FEOL rule deck name found at all
                    missing_items[expected_name] = {
                        'line_number': 0,
                        'file_path': 'N/A',
                        'reason': f'FEOL rule deck name not found in input file'
                    }
        else:
            # No pattern_items defined - cannot validate
            if not found_items:
                missing_items['FEOL_rule_deck'] = {
                    'line_number': 0,
                    'file_path': 'N/A',
                    'reason': 'FEOL rule deck name not found in input file'
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

        # Process found_items_base (no waiver needed - these are clean matches)
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
        # FIXED: Pass dict directly, not list
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
    checker = Check_2_0_0_10()
    checker.init_checker(Path(__file__))
    result = checker.execute_check()
    checker.write_output(result)
    return 0 if result.is_pass else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())