################################################################################
# Script Name: IMP-2-0-0-12.py
#
# Purpose:
#   List COD dummy rule deck name (fill N/A if no COD). eg: PLN16FFP_FINcut_AutoGen.11b.encrypt
#
# Logic:
#   - Parse COD_pvl.log to extract COD rule deck filename from include statement
#   - Extract basename from absolute path to get filename only
#   - Verify extracted filename matches expected golden value (if pattern_items provided)
#   - Support waiver for COD rule deck mismatches
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
import os
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
class Check_2_0_0_12(InputFileParserMixin, OutputBuilderMixin, WaiverHandlerMixin, BaseChecker):
    """
    IMP-2-0-0-12: List COD dummy rule deck name (fill N/A if no COD). eg: PLN16FFP_FINcut_AutoGen.11b.encrypt
    
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
    FOUND_DESC_TYPE1_4 = "COD rule deck found in PVL log file"
    MISSING_DESC_TYPE1_4 = "COD rule deck not found in PVL log file"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_DESC_TYPE2_3 = "COD rule deck matched expected configuration"
    MISSING_DESC_TYPE2_3 = "COD rule deck does not match expected configuration"
    
    # All Types (waiver description unified)
    WAIVED_DESC = "COD rule deck check waived"
    
    # ⭐ REASON CONSTANTS - Split by Type semantics (API-025)
    # ALL Types pass found_reason/missing_reason, but use different constants
    
    # Type 1/4: Boolean checks - emphasize "found/not found" (existence)
    FOUND_REASON_TYPE1_4 = "COD rule deck include statement found and extracted successfully"
    MISSING_REASON_TYPE1_4 = "No COD rule deck include statement found in log file"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_REASON_TYPE2_3 = "COD rule deck filename matched expected golden value"
    MISSING_REASON_TYPE2_3 = "COD rule deck filename does not match expected golden value"
    
    # Waiver-related (Type 3/4 only)
    WAIVED_BASE_REASON = "COD rule deck mismatch waived per design team approval"
    UNUSED_WAIVER_REASON = "Waiver not matched - no corresponding COD rule deck mismatch found"
    
    def __init__(self):
        """Initialize the checker."""
        super().__init__(
            check_module="2.0_TECHFILE_AND_RULE_DECK_CHECK",
            item_id="IMP-2-0-0-12",
            item_desc="List COD dummy rule deck name (fill N/A if no COD). eg: PLN16FFP_FINcut_AutoGen.11b.encrypt"
        )
        # Custom member variables for parsed data
        self._parsed_items: List[Dict[str, Any]] = []
        self._metadata: Dict[str, str] = {}
        self._cod_rule_deck: Optional[str] = None
    
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
        Parse COD_pvl.log to extract COD rule deck filename from include statement.
        
        Searches for include statements containing .COD extension, extracts the full path,
        and returns the basename only (e.g., PLN12FFC_FINcut_AutoGen.09_1a.COD).
        
        Returns:
            Dict with parsed data:
            - 'items': List[Dict] - COD rule deck information (single item or empty)
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
        cod_rule_deck = None
        
        # 3. Parse each input file for COD rule deck include statement
        for file_path in valid_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line_num, line in enumerate(f, 1):
                        # Pattern 1: Primary include pattern with quotes
                        match = re.search(r'^include\s+"(.+\.COD)"', line, re.IGNORECASE)
                        if match:
                            full_path = match.group(1)
                            cod_filename = os.path.basename(full_path)
                            cod_rule_deck = cod_filename
                            items.append({
                                'name': cod_filename,
                                'line_number': line_num,
                                'file_path': str(file_path),
                                'type': 'cod_rule_deck',
                                'full_path': full_path
                            })
                            break  # Stop after finding first COD deck
                        
                        # Pattern 2: Alternative include pattern with flexible quotes
                        match = re.search(r'^include\s+[\'"]?([^\'"]+\.COD)[\'"]?', line, re.IGNORECASE)
                        if match:
                            full_path = match.group(1)
                            cod_filename = os.path.basename(full_path)
                            cod_rule_deck = cod_filename
                            items.append({
                                'name': cod_filename,
                                'line_number': line_num,
                                'file_path': str(file_path),
                                'type': 'cod_rule_deck',
                                'full_path': full_path
                            })
                            break  # Stop after finding first COD deck
                
                # If found in this file, stop processing other files
                if cod_rule_deck:
                    break
                    
            except Exception as e:
                errors.append(f"Error parsing {file_path}: {str(e)}")
        
        # 4. Store frequently reused data on self
        self._parsed_items = items
        self._cod_rule_deck = cod_rule_deck
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

        Extracts COD rule deck filename from COD_pvl.log include statement.
        - If include statement found and filename extracted → PASS (found_items)
        - If no include statement found → PASS with "N/A" (acceptable per requirements.value=N/A)

        Returns:
            CheckResult with found_items containing extracted COD deck name or "N/A"
        """
        violations = self._type1_core_logic()

        # Build found_items from parsed data
        data = self._parse_input_files()
        items = data.get('items', [])

        # ⚠️ CRITICAL: found_items MUST be dict[str, dict], NOT list!
        found_items = {}
        for item in items:
            item_name = item.get('name', 'N/A')
            found_items[item_name] = {
                'line_number': item.get('line_number', 0),
                'file_path': item.get('file_path', 'N/A')
            }

        # If no items found, add "N/A" as acceptable result
        if not found_items:
            found_items['N/A'] = {
                'line_number': 0,
                'file_path': 'N/A'
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

        Extracts COD rule deck filename from include statement in COD_pvl.log.
        This is a pure extraction check - no violations expected in normal operation.

        Returns:
            Dict of violations: {item_name: {'line_number': ..., 'file_path': ..., 'reason': ...}}
            Empty dict if extraction successful (normal case for this check)
        """
        data = self._parse_input_files()
        errors = data.get('errors', [])

        violations = {}

        # Check for parsing errors (e.g., file not found, malformed content)
        if errors:
            for error in errors:
                error_key = f"parsing_error_{len(violations)}"
                violations[error_key] = {
                    'line_number': 0,
                    'file_path': error.get('file_path', 'N/A'),
                    'reason': error.get('message', 'Unknown parsing error')
                }

        # Note: For this check, successful extraction means no violations
        # The extracted COD deck name goes to found_items in _execute_type1()
        # Violations would only occur if there were parsing errors or file access issues

        return violations

    # =========================================================================
    # Type 4: Boolean Check with Waiver Logic
    # =========================================================================

    def _execute_type4(self) -> CheckResult:
        """
        Type 4: Boolean check with waiver support (reuses Type 1 core logic).

        Same extraction logic as Type 1, but supports waiving specific COD deck names
        if they are flagged as violations (e.g., non-standard or deprecated decks).

        Flow:
        1. Extract COD deck name using Type 1 core logic
        2. Parse waiver configuration
        3. Classify violations into waived vs unwaived
        4. Track unused waivers

        Returns:
            CheckResult with waiver classification
        """
        violations = self._type1_core_logic()

        # Build found_items from parsed data
        data = self._parse_input_files()
        items = data.get('items', [])

        # ⚠️ CRITICAL: found_items MUST be dict[str, dict], NOT list!
        found_items = {}
        for item in items:
            item_name = item.get('name', 'N/A')
            found_items[item_name] = {
                'line_number': item.get('line_number', 0),
                'file_path': item.get('file_path', 'N/A')
            }

        # If no items found, add "N/A" as acceptable result
        if not found_items:
            found_items['N/A'] = {
                'line_number': 0,
                'file_path': 'N/A'
            }

        # FIXED: Use waivers.get() instead of get_waive_items() per API-016
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
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

        unused_waivers = [w for w in waive_dict.keys() if w not in used_waivers]

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

        # Extract actual COD rule deck filename from parsed items
        actual_cod_filename = None
        actual_file_path = 'N/A'
        actual_line_number = 0

        if items:
            # items should contain the extracted COD filename from include statement
            for item in items:
                if 'name' in item:
                    actual_cod_filename = item['name']
                    actual_file_path = item.get('file_path', 'N/A')
                    actual_line_number = item.get('line_number', 0)
                    break

        # Check if we have pattern_items to validate against
        if not pattern_items:
            # No golden value to compare - just report what we found
            if actual_cod_filename:
                found_items[actual_cod_filename] = {
                    'line_number': actual_line_number,
                    'file_path': actual_file_path
                }
            else:
                missing_items['COD rule deck'] = {
                    'line_number': 0,
                    'file_path': 'N/A',
                    'reason': 'No COD rule deck filename found in log file'
                }
        else:
            # Validate against expected golden value (exact match)
            expected_filename = pattern_items[0]  # Should have exactly 1 pattern

            if actual_cod_filename:
                # Compare actual vs expected (exact match, case-insensitive)
                if actual_cod_filename.lower() == expected_filename.lower():
                    # Match - add to found_items
                    found_items[actual_cod_filename] = {
                        'line_number': actual_line_number,
                        'file_path': actual_file_path
                    }
                else:
                    # Mismatch - add to missing_items
                    mismatch_name = f"Expected: {expected_filename}, Found: {actual_cod_filename}"
                    missing_items[mismatch_name] = {
                        'line_number': actual_line_number,
                        'file_path': actual_file_path,
                        'reason': f'COD rule deck filename mismatch (expected: {expected_filename}, found: {actual_cod_filename})'
                    }
            else:
                # No COD filename found
                missing_items[expected_filename] = {
                    'line_number': 0,
                    'file_path': 'N/A',
                    'reason': f'Expected COD rule deck "{expected_filename}" not found in log file'
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
        # FIXED: Use waivers.get() instead of get_waive_items() per API-016
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
    checker = Check_2_0_0_12()
    checker.init_checker(Path(__file__))
    result = checker.execute_check()
    checker.write_output(result)
    return 0 if result.is_pass else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())