################################################################################
# Script Name: IMP-2-0-0-06.py
#
# Purpose:
#   Confirm latest LVS rule deck(s) was used? List LVS rule deck name in Comments. eg: DFM_LVS_RC_PEGASUS_N3P_1p17M_1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2Yx2R_ALRDL.1.0a
#
# Logic:
#   - Parse LVS_pvl.log to extract LVS rule deck path from include statement
#   - Open rule deck file and extract COMMAND FILE DOCUMENT and VERSION
#   - For Type 1/4: Verify all three values (path, document, version) exist
#   - For Type 2/3: Compare current document/version against expected pattern_items
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
class Check_2_0_0_06(InputFileParserMixin, OutputBuilderMixin, WaiverHandlerMixin, BaseChecker):
    """
    IMP-2-0-0-06: Confirm latest LVS rule deck(s) was used? List LVS rule deck name in Comments. eg: DFM_LVS_RC_PEGASUS_N3P_1p17M_1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2Yx2R_ALRDL.1.0a
    
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
    FOUND_DESC_TYPE1_4 = "LVS rule deck information found and extracted successfully"
    MISSING_DESC_TYPE1_4 = "LVS rule deck information not found or incomplete"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_DESC_TYPE2_3 = "LVS rule deck version matched expected version"
    MISSING_DESC_TYPE2_3 = "LVS rule deck version does not match expected version"
    
    # All Types (waiver description unified)
    WAIVED_DESC = "LVS rule deck version mismatch waived"
    
    # ⭐ REASON CONSTANTS - Split by Type semantics (API-025)
    # ALL Types pass found_reason/missing_reason, but use different constants
    
    # Type 1/4: Boolean checks - emphasize "found/not found" (existence)
    FOUND_REASON_TYPE1_4 = "Rule deck path, document name, and version found in LVS log and rule deck file"
    MISSING_REASON_TYPE1_4 = "Rule deck path, document name, or version not found in LVS log or rule deck file"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_REASON_TYPE2_3 = "Rule deck document and version matched expected values and validated successfully"
    MISSING_REASON_TYPE2_3 = "Rule deck document or version does not match expected values - version mismatch detected"
    
    # Waiver-related (Type 3/4 only)
    WAIVED_BASE_REASON = "Rule deck version mismatch waived per project approval"
    UNUSED_WAIVER_REASON = "Waiver defined but no violation matched"
    
    def __init__(self):
        """Initialize the checker."""
        super().__init__(
            check_module="2.0_TECHFILE_AND_RULE_DECK_CHECK",
            item_id="IMP-2-0-0-06",
            item_desc="Confirm latest LVS rule deck(s) was used? List LVS rule deck name in Comments. eg: DFM_LVS_RC_PEGASUS_N3P_1p17M_1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2Yx2R_ALRDL.1.0a"
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
        Parse LVS_pvl.log to extract rule deck path, then parse rule deck file for document and version.
        
        Parsing Strategy:
        1. Read LVS_pvl.log line by line to find include statement with "*DFM_LVS*" pattern
        2. Extract absolute path and store in rule_path variable
        3. Open rule deck file at rule_path (already absolute, no path resolution needed)
        4. Parse rule deck file to extract current_doc from "COMMAND FILE DOCUMENT:" line
        5. Parse rule deck file to extract current_ver from "COMMAND FILE VERSION:" line
        6. Store all three values (rule_path, current_doc, current_ver) for validation
        
        Returns:
            Dict with parsed data:
            - 'items': List[Dict] - Rule deck information with metadata
            - 'metadata': Dict - File metadata (rule_path, current_doc, current_ver)
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
        
        # 3. Parse each input file for LVS rule deck information
        # Pattern 1: Extract LVS rule deck absolute path from include statement
        pattern_rule_path = r'include\s+"([^"]+DFM_LVS[^"]+)"'
        
        for file_path in valid_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line_num, line in enumerate(f, 1):
                        # Extract rule deck path from include statement
                        match = re.search(pattern_rule_path, line)
                        if match:
                            rule_deck_path = match.group(1)
                            # Normalize path separators (handle both Windows and Unix)
                            rule_deck_path = rule_deck_path.replace('\\', '/')
                            
                            # Parse rule deck file for document and version
                            rule_deck_file = Path(rule_deck_path)
                            if rule_deck_file.exists():
                                try:
                                    with open(rule_deck_file, 'r', encoding='utf-8', errors='ignore') as rd_f:
                                        for rd_line in rd_f:
                                            # Pattern 2: Extract document name
                                            doc_match = re.search(r'COMMAND FILE DOCUMENT:\s*(.+)', rd_line)
                                            if doc_match:
                                                current_doc = doc_match.group(1).strip()
                                            
                                            # Pattern 3: Extract version
                                            ver_match = re.search(r'COMMAND FILE VERSION:\s*(.+)', rd_line)
                                            if ver_match:
                                                current_ver = ver_match.group(1).strip()
                                except Exception as e:
                                    errors.append(f"Error parsing rule deck file {rule_deck_path}: {str(e)}")
                            else:
                                errors.append(f"Rule deck file not found at path: {rule_deck_path}")
                            
                            # Extract rule deck basename for display
                            rule_deck_basename = rule_deck_file.name
                            
                            # Create item with all extracted information
                            if rule_deck_path and current_doc and current_ver:
                                items.append({
                                    'name': f"{rule_deck_basename} ({current_doc}, {current_ver})",
                                    'line_number': line_num,
                                    'file_path': str(file_path),
                                    'type': 'rule_deck',
                                    'rule_deck_path': rule_deck_path,
                                    'rule_deck_basename': rule_deck_basename,
                                    'current_doc': current_doc,
                                    'current_ver': current_ver
                                })
            except Exception as e:
                errors.append(f"Error parsing {file_path}: {str(e)}")
        
        # 4. Store frequently reused data on self
        self._parsed_items = items
        self._rule_deck_path = rule_deck_path
        self._current_doc = current_doc
        self._current_ver = current_ver
        
        metadata = {
            'rule_deck_path': rule_deck_path,
            'current_doc': current_doc,
            'current_ver': current_ver
        }
        
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
        
        Verifies that LVS rule deck information (path, document, version) can be extracted.
        PASS if all three values are found and non-empty.
        FAIL if any required information is missing.
        """
        violations = self._type1_core_logic()
        
        # Build found_items from successfully extracted rule deck info
        found_items = {}
        data = self._parse_input_files()
        
        if not violations:
            # All required info found - create found_items entry
            items = data.get('items', [])
            if items:
                for item in items:
                    found_items[item['name']] = {
                        'name': item['name'],
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
    
    def _type1_core_logic(self) -> dict:
        """
        Core Type 1 boolean check logic (shared by Type 1 and Type 4).
        
        Extracts LVS rule deck path from LVS_pvl.log, then extracts document name
        and version from the rule deck file itself.
        
        Returns:
            Dict of violations: {item_name: {'line_number': ..., 'file_path': ..., 'reason': ...}}
            Empty dict if all checks pass (rule_path, current_doc, current_ver all found).
        """
        data = self._parse_input_files()
        errors = data.get('errors', [])
        metadata = data.get('metadata', {})
        
        violations = {}
        
        # Check for parsing errors
        if errors:
            for error in errors:
                violations[error] = {
                    'line_number': 0,
                    'file_path': 'N/A',
                    'reason': error
                }
            return violations
        
        # Extract required fields
        rule_path = metadata.get('rule_deck_path', '')
        current_doc = metadata.get('current_doc', '')
        current_ver = metadata.get('current_ver', '')
        
        # Check if all required information is present
        if not rule_path or not current_doc or not current_ver:
            missing_fields = []
            if not rule_path:
                missing_fields.append('rule deck path')
            if not current_doc:
                missing_fields.append('document name')
            if not current_ver:
                missing_fields.append('version')
            
            violations['LVS rule deck information incomplete'] = {
                'line_number': 0,
                'file_path': 'N/A',
                'reason': f"Missing: {', '.join(missing_fields)}"
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
            - found_items: {rule_deck_name: {'line_number': ..., 'file_path': ...}}
            - missing_items: {pattern_name: {'line_number': ..., 'file_path': ..., 'reason': ...}}
        """
        data = self._parse_input_files()
        items = data.get('items', [])
        
        requirements = self.item_data.get('requirements', {})
        pattern_items = requirements.get('pattern_items', [])
        
        found_items = {}
        missing_items = {}
        
        # Validate pattern_items configuration
        if len(pattern_items) < 2:
            missing_items['configuration_error'] = {
                'line_number': 0,
                'file_path': 'N/A',
                'reason': 'Configuration error: pattern_items must contain [expected_document, expected_version]'
            }
            return found_items, missing_items
        
        expected_document = pattern_items[0]
        expected_version = pattern_items[1]
        
        # Check each extracted rule deck
        for item in items:
            rule_deck_name = item.get('name', 'Unknown')
            current_document = item.get('current_doc', '')
            current_version = item.get('current_ver', '')
            line_number = item.get('line_number', 0)
            file_path = item.get('file_path', 'N/A')
            
            # Compare current values against expected pattern_items
            if current_document == expected_document and current_version == expected_version:
                # Both document and version match expected values
                found_items[rule_deck_name] = {
                    'line_number': line_number,
                    'file_path': file_path
                }
            else:
                # Document or version mismatch
                mismatch_details = []
                if current_document != expected_document:
                    mismatch_details.append(f'document mismatch (got "{current_document}", expected "{expected_document}")')
                if current_version != expected_version:
                    mismatch_details.append(f'version mismatch (got "{current_version}", expected "{expected_version}")')
                
                reason = f"Rule deck document or version does not match expected values - {', '.join(mismatch_details)}"
                
                missing_items[rule_deck_name] = {
                    'line_number': line_number,
                    'file_path': file_path,
                    'reason': reason
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
        
        # Process found_items_base (no waiver needed - already matching expected values)
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
        
        Same boolean check as Type 1 (verify rule deck info exists), plus waiver classification:
        - Match violations against waive_items
        - Unwaived violations → FAIL
        - Waived violations → INFO with [WAIVER] tag
        - Unused waivers → WARN with [WAIVER] tag
        PASS if all violations are waived.
        """
        # Step 1: Get violations using Type 1's core logic
        violations = self._type1_core_logic()
        
        # Build found_items from successfully extracted rule deck info
        found_items = {}
        data = self._parse_input_files()
        
        if not violations:
            # All required info found - create found_items entry
            items = data.get('items', [])
            if items:
                for item in items:
                    found_items[item['name']] = {
                        'name': item['name'],
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
# Entry Point
# =========================================================================

def main():
    """Main entry point."""
    checker = Check_2_0_0_06()
    checker.init_checker(Path(__file__))
    result = checker.execute_check()
    checker.write_output(result)
    return 0 if result.is_pass else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())