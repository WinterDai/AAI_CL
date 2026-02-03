################################################################################
# Script Name: IMP-2-0-0-08.py
#
# Purpose:
#   Confirm latest BUMP rule deck(s) was used? List BUMP rule deck name in Comments. eg: PN3_CU_ROUND_BUMP_ON_PAD_17M_1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2Yx2R_003.10a
#
# Logic:
#   - Parse BUMP_pvl.log to extract rule deck include path
#   - Parse rule deck file to extract document name and version
#   - For Type 1/4: Verify all three values (path, doc, version) exist
#   - For Type 2/3: Compare current doc/version against expected pattern_items
#   - Support waiver for version mismatches (Type 3/4)
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
class Check_2_0_0_08(InputFileParserMixin, OutputBuilderMixin, WaiverHandlerMixin, BaseChecker):
    """
    IMP-2-0-0-08: Confirm latest BUMP rule deck(s) was used? List BUMP rule deck name in Comments. eg: PN3_CU_ROUND_BUMP_ON_PAD_17M_1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2Yx2R_003.10a
    
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
    FOUND_DESC_TYPE1_4 = "BUMP rule deck information found and extracted successfully"
    MISSING_DESC_TYPE1_4 = "BUMP rule deck information not found or incomplete"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_DESC_TYPE2_3 = "BUMP rule deck version matched expected specification"
    MISSING_DESC_TYPE2_3 = "BUMP rule deck version does not match expected specification"
    
    # All Types (waiver description unified)
    WAIVED_DESC = "BUMP rule deck version mismatch waived"
    
    # ⭐ REASON CONSTANTS - Split by Type semantics (API-025)
    # ALL Types pass found_reason/missing_reason, but use different constants
    
    # Type 1/4: Boolean checks - emphasize "found/not found" (existence)
    FOUND_REASON_TYPE1_4 = "Rule deck path, document name, and version successfully extracted from BUMP_pvl.log and rule deck file"
    MISSING_REASON_TYPE1_4 = "Failed to extract rule deck path, document name, or version from input files - verify BUMP_pvl.log contains valid include statement and rule deck file is accessible"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_REASON_TYPE2_3 = "Current rule deck document and version matched expected values - using approved BUMP rule deck"
    MISSING_REASON_TYPE2_3 = "Current rule deck document or version does not match expected values - incorrect BUMP rule deck version in use"
    
    # Waiver-related (Type 3/4 only)
    WAIVED_BASE_REASON = "BUMP rule deck version mismatch waived per project approval"
    UNUSED_WAIVER_REASON = "Waiver entry not matched - no corresponding rule deck version mismatch found"
    
    def __init__(self):
        """Initialize the checker."""
        super().__init__(
            check_module="2.0_TECHFILE_AND_RULE_DECK_CHECK",
            item_id="IMP-2-0-0-08",
            item_desc="Confirm latest BUMP rule deck(s) was used? List BUMP rule deck name in Comments. eg: PN3_CU_ROUND_BUMP_ON_PAD_17M_1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2Yx2R_003.10a"
        )
        # Custom member variables for parsed data
        self._parsed_items: List[Dict[str, Any]] = []
        self._metadata: Dict[str, str] = {}
        self._rule_deck_path: str = ""
        self._current_doc: str = ""
        self._current_ver: str = ""
    
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
        Parse input files to extract BUMP rule deck information.
        
        Parsing Strategy:
        1. Parse BUMP_pvl.log to extract rule deck include path
        2. Parse rule deck file to extract document name and version
        3. Store all three values: rule_path, current_doc, current_ver
        
        Returns:
            Dict with parsed data:
            - 'items': List[Dict] - Rule deck information (path, doc, version)
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
        rule_deck_path = ""
        current_doc = ""
        current_ver = ""
        
        # 3. Parse each input file for BUMP rule deck information
        for file_path in valid_files:
            try:
                # Step 1: Extract rule deck path from BUMP_pvl.log
                # Pattern 1: Extract BUMP rule deck path from include statement
                pattern_include = r'include\s+"([^"]+)"'
                
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line_num, line in enumerate(f, 1):
                        # Skip commented lines
                        if line.strip().startswith('#') or line.strip().startswith('//'):
                            continue
                        
                        # Match include statement
                        match = re.search(pattern_include, line)
                        if match:
                            rule_deck_path = match.group(1)
                            # Normalize path separators (handle both Windows and Linux)
                            rule_deck_path = rule_deck_path.replace('\\', '/')
                            break
                
                # Step 2: Parse rule deck file to extract document and version
                if rule_deck_path:
                    # Convert to Path object for file operations
                    rule_deck_file = Path(rule_deck_path)
                    
                    # Check if file exists
                    if rule_deck_file.exists():
                        # Pattern 2: Extract document name and version from rule deck header
                        pattern_doc_ver = r'DRC\s+COMMAND\s+FILE\s+DOCUMENT:\s*(\S+)\s+VER\s+(\S+)'
                        
                        with open(rule_deck_file, 'r', encoding='utf-8', errors='ignore') as rf:
                            for line_num, line in enumerate(rf, 1):
                                match = re.search(pattern_doc_ver, line)
                                if match:
                                    current_doc = match.group(1)
                                    current_ver = match.group(2)
                                    break
                    else:
                        errors.append(f"Rule deck file not found: {rule_deck_path}")
                
                # Create item if all three values extracted
                if rule_deck_path and current_doc and current_ver:
                    items.append({
                        'name': f"{rule_deck_path} ({current_doc}, {current_ver})",
                        'rule_path': rule_deck_path,
                        'current_doc': current_doc,
                        'current_ver': current_ver,
                        'line_number': 0,
                        'file_path': str(file_path),
                        'type': 'rule_deck_info'
                    })
                    # Store in metadata for easy access
                    metadata['rule_path'] = rule_deck_path
                    metadata['current_doc'] = current_doc
                    metadata['current_ver'] = current_ver
                elif rule_deck_path:
                    # Partial extraction - add error
                    errors.append(f"Failed to extract document/version from rule deck: {rule_deck_path}")
                else:
                    errors.append(f"No rule deck include statement found in {file_path}")
                    
            except Exception as e:
                errors.append(f"Error parsing {file_path}: {str(e)}")
        
        # 4. Store frequently reused data on self
        self._parsed_items = items
        self._metadata = metadata
        self._rule_deck_path = rule_deck_path
        self._current_doc = current_doc
        self._current_ver = current_ver
        
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
        
        Validates that BUMP rule deck information can be extracted:
        - Rule deck path from BUMP_pvl.log
        - Document name from rule deck file
        - Version from rule deck file
        
        PASS: All three values successfully extracted
        FAIL: Any value missing or extraction failed
        """
        violations = self._type1_core_logic()
        
        # Build found_items from successfully extracted rule deck info
        found_items = {}
        if not violations:
            # If no violations, rule deck info was successfully extracted
            data = self._parse_input_files()
            metadata = data.get('metadata', {})
            rule_path = metadata.get('rule_path', '')
            current_doc = metadata.get('current_doc', '')
            current_ver = metadata.get('current_ver', '')
            
            if rule_path and current_doc and current_ver:
                # Create a composite key for the successfully extracted rule deck
                rule_deck_name = f"{Path(rule_path).name}"
                found_items[rule_deck_name] = {
                    'name': rule_deck_name,
                    'line_number': 1,
                    'file_path': rule_path,
                    'document': current_doc,
                    'version': current_ver
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
    
    def _type1_core_logic(self) -> dict:
        """
        Core Type 1 boolean check logic (shared by Type 1 and Type 4).
        
        Validates extraction of BUMP rule deck information:
        1. Parse BUMP_pvl.log to get rule deck path
        2. Parse rule deck file to get document name and version
        3. Verify all three values exist and are non-empty
        
        Returns:
            Dict of violations: {item_name: {'line_number': ..., 'file_path': ..., 'reason': ...}}
            Empty dict if all checks pass (all values successfully extracted).
        """
        data = self._parse_input_files()
        errors = data.get('errors', [])
        metadata = data.get('metadata', {})
        
        violations = {}
        
        # Check if parsing encountered errors
        if errors:
            # Parsing failed - create violation entry
            input_files = self.get_input_files()
            default_file = input_files[0] if input_files else 'N/A'
            
            violations['BUMP rule deck information missing'] = {
                'line_number': 0,
                'file_path': default_file,
                'reason': self.MISSING_REASON_TYPE1_4
            }
            return violations
        
        # Extract the three required values
        rule_path = metadata.get('rule_path', '')
        current_doc = metadata.get('current_doc', '')
        current_ver = metadata.get('current_ver', '')
        
        # Check if any value is missing or empty
        if not rule_path or not current_doc or not current_ver:
            input_files = self.get_input_files()
            default_file = input_files[0] if input_files else 'N/A'
            
            violations['BUMP rule deck information missing'] = {
                'line_number': 0,
                'file_path': default_file,
                'reason': self.MISSING_REASON_TYPE1_4
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
    
    def _type2_core_logic(self) -> Tuple[Dict[str, Dict], Dict[str, Dict]]:
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
        
        # Validate pattern_items configuration
        if len(pattern_items) < 2:
            raise ConfigurationError(
                f"pattern_items must contain at least 2 items (document name and version), "
                f"found {len(pattern_items)}"
            )
        
        # Extract expected values from pattern_items
        expected_doc = pattern_items[0]  # Expected document name (e.g., "T-000-BP-DR-030-N1")
        expected_ver = pattern_items[1]  # Expected version (e.g., "1.0_1a")
        
        # Check if we found any rule deck information
        if not items:
            # No rule deck found at all
            missing_items['BUMP_rule_deck'] = {
                'line_number': 0,
                'file_path': 'N/A',
                'reason': f'No BUMP rule deck information found. Expected: ({expected_doc}, {expected_ver})'
            }
            return found_items, missing_items
        
        # Process the found rule deck (should be only one)
        for item in items:
            rule_deck_name = item.get('name', 'Unknown')
            current_doc = item.get('current_doc', '')
            current_ver = item.get('current_ver', '')
            line_number = item.get('line_number', 0)
            file_path = item.get('file_path', 'N/A')
            
            # Compare current values against expected values
            doc_match = (current_doc == expected_doc)
            ver_match = (current_ver == expected_ver)
            
            if doc_match and ver_match:
                # Both document and version match - PASS
                found_items[rule_deck_name] = {
                    'line_number': line_number,
                    'file_path': file_path
                }
            else:
                # Mismatch detected - FAIL
                mismatch_details = []
                if not doc_match:
                    mismatch_details.append(f"Document: expected '{expected_doc}', found '{current_doc}'")
                if not ver_match:
                    mismatch_details.append(f"Version: expected '{expected_ver}', found '{current_ver}'")
                
                missing_items[rule_deck_name] = {
                    'line_number': line_number,
                    'file_path': file_path,
                    'reason': f"Expected: ({expected_doc}, {expected_ver}), Found: ({current_doc}, {current_ver})"
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
    
    # =========================================================================
    # Type 4: Boolean Check with Waiver Logic
    # =========================================================================
    
    def _execute_type4(self) -> CheckResult:
        """
        Type 4: Boolean check with waiver support (reuses Type 1 core logic).
        
        Performs same validation as Type 1 but allows waiving extraction failures:
        - Reuses _type1_core_logic() to detect violations
        - Applies waiver matching to split violations into waived/unwaived
        - Waived violations → PASS (INFO with [WAIVER] tag)
        - Unwaived violations → FAIL
        - Unused waivers → WARN with [WAIVER] tag
        
        PASS: All violations are waived
        FAIL: Any unwaived violations exist
        """
        # Step 1: Get violations using Type 1's core logic
        violations = self._type1_core_logic()
        
        # Build found_items from successfully extracted rule deck info
        found_items = {}
        if not violations:
            # If no violations, rule deck info was successfully extracted
            data = self._parse_input_files()
            metadata = data.get('metadata', {})
            rule_path = metadata.get('rule_path', '')
            current_doc = metadata.get('current_doc', '')
            current_ver = metadata.get('current_ver', '')
            
            if rule_path and current_doc and current_ver:
                # Create a composite key for the successfully extracted rule deck
                rule_deck_name = f"{Path(rule_path).name}"
                found_items[rule_deck_name] = {
                    'name': rule_deck_name,
                    'line_number': 1,
                    'file_path': rule_path,
                    'document': current_doc,
                    'version': current_ver
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
# Entry Point
# =========================================================================

def main():
    """Main entry point."""
    checker = Check_2_0_0_08()
    checker.init_checker(Path(__file__))
    result = checker.execute_check()
    checker.write_output(result)
    return 0 if result.is_pass else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())