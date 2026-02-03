################################################################################
# Script Name: IMP-2-0-0-04.py
#
# Purpose:
#   Confirm latest Antenna rule deck(s) was used? List DRC rule deck name in Comments. eg: PLN3ELO_17M_1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2Yx2R_014_ANT.11_2a.encrypt PLN3ELO_17M_1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2Yx2R_014_SHDMIM_ANT.11_2a.encrypt
#
# Logic:
#   - Parse ANT_pvl.log to extract rule deck include statements (absolute paths)
#   - Open each rule deck file and extract document name and version from DRC COMMAND FILE DOCUMENT header
#   - For Type 1/4: Verify rule deck path, document, and version can be extracted
#   - For Type 2/3: Compare extracted document/version against expected pattern_items values
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
class Check_2_0_0_04(InputFileParserMixin, OutputBuilderMixin, WaiverHandlerMixin, BaseChecker):
    """
    IMP-2-0-0-04: Confirm latest Antenna rule deck(s) was used? List DRC rule deck name in Comments. eg: PLN3ELO_17M_1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2Yx2R_014_ANT.11_2a.encrypt PLN3ELO_17M_1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2Yx2R_014_SHDMIM_ANT.11_2a.encrypt
    
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
    FOUND_DESC_TYPE1_4 = "Antenna rule deck information found in ANT log"
    MISSING_DESC_TYPE1_4 = "Antenna rule deck information not found or incomplete in ANT log"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_DESC_TYPE2_3 = "Antenna rule deck version matched expected version"
    MISSING_DESC_TYPE2_3 = "Antenna rule deck version does not match expected version"
    
    # All Types (waiver description unified)
    WAIVED_DESC = "Antenna rule deck version mismatch waived"
    
    # ⭐ REASON CONSTANTS - Split by Type semantics (API-025)
    # ALL Types pass found_reason/missing_reason, but use different constants
    
    # Type 1/4: Boolean checks - emphasize "found/not found" (existence)
    FOUND_REASON_TYPE1_4 = "Rule deck path, document name, and version successfully extracted from ANT log"
    MISSING_REASON_TYPE1_4 = "Rule deck path, document name, or version not found in ANT log or rule deck file"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_REASON_TYPE2_3 = "Rule deck document and version matched expected values and validated"
    MISSING_REASON_TYPE2_3 = "Rule deck document or version does not match expected pattern - version mismatch detected"
    
    # Waiver-related (Type 3/4 only)
    WAIVED_BASE_REASON = "Rule deck version mismatch waived per project approval"
    UNUSED_WAIVER_REASON = "Waiver defined but no violation matched"
    
    def __init__(self):
        """Initialize the checker."""
        super().__init__(
            check_module="2.0_TECHFILE_AND_RULE_DECK_CHECK",
            item_id="IMP-2-0-0-04",
            item_desc="Confirm latest Antenna rule deck(s) was used? List DRC rule deck name in Comments. eg: PLN3ELO_17M_1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2Yx2R_014_ANT.11_2a.encrypt PLN3ELO_17M_1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2Yx2R_014_SHDMIM_ANT.11_2a.encrypt"
        )
        # Custom member variables for parsed data
        self._parsed_items: List[Dict[str, Any]] = []
        self._metadata: Dict[str, str] = {}
        self._rule_deck_info: List[Dict[str, str]] = []
    
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
        Parse ANT_pvl.log to extract rule deck information.
        
        Parsing Strategy:
        1. Extract rule deck include paths from ANT_pvl.log
        2. For each rule deck file, extract document name and version
        3. Return list of rule deck info with path, document, and version
        
        Returns:
            Dict with parsed data:
            - 'items': List[Dict] - Rule deck information (path, document, version)
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
        rule_deck_paths = []
        
        # 3. Parse each input file for rule deck include statements
        pattern_include = re.compile(r'include\s+"([^"]+)"')
        pattern_document = re.compile(r'DRC\s+COMMAND\s+FILE\s+DOCUMENT:\s*(\S+)\s+VER\s+(\S+)')
        
        for file_path in valid_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line_num, line in enumerate(f, 1):
                        # Extract rule deck include paths
                        match = pattern_include.search(line)
                        if match:
                            rule_path = match.group(1)
                            rule_deck_paths.append({
                                'path': rule_path,
                                'line_number': line_num,
                                'log_file': str(file_path)
                            })
            except Exception as e:
                errors.append(f"Error parsing {file_path}: {str(e)}")
        
        # Parse each rule deck file for document and version
        for rule_deck_info in rule_deck_paths:
            rule_path = rule_deck_info['path']
            try:
                # Handle both Windows and Unix paths
                rule_deck_file = Path(rule_path)
                
                if not rule_deck_file.exists():
                    errors.append(f"Rule deck file not found: {rule_path}")
                    continue
                
                current_doc = None
                current_ver = None
                
                with open(rule_deck_file, 'r', encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        match = pattern_document.search(line)
                        if match:
                            current_doc = match.group(1)
                            current_ver = match.group(2)
                            break
                
                if current_doc and current_ver:
                    # Extract filename from path
                    rule_filename = rule_deck_file.name
                    
                    items.append({
                        'name': f"{rule_filename} ({current_doc}, {current_ver})",
                        'rule_path': rule_path,
                        'rule_filename': rule_filename,
                        'current_doc': current_doc,
                        'current_ver': current_ver,
                        'line_number': rule_deck_info['line_number'],
                        'file_path': rule_deck_info['log_file']
                    })
                else:
                    errors.append(f"Document or version not found in rule deck: {rule_path}")
            except Exception as e:
                errors.append(f"Error parsing rule deck {rule_path}: {str(e)}")
        
        # 4. Store frequently reused data on self
        self._parsed_items = items
        self._rule_deck_info = items
        
        return {
            'items': items,
            'metadata': metadata,
            'errors': errors
        }
    
    # =========================================================================
    # Type 1: Boolean Check
    # =========================================================================
    
    def _execute_type1(self) -> CheckResult:
        """Type 1: Boolean check without waiver support."""
        violations = self._type1_core_logic()
        
        # Build found_items from successfully extracted rule decks
        data = self._parse_input_files()
        items = data.get('items', [])
        
        # Convert items to dict with metadata for found_items
        found_items = {
            item['name']: {
                'name': item['name'],
                'line_number': item.get('line_number', 0),
                'file_path': item.get('file_path', 'N/A')
            }
            for item in items
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
        
        Returns:
            Dict of violations: {item_name: {'line_number': ..., 'file_path': ..., 'reason': ...}}
            Empty dict if all checks pass.
        """
        data = self._parse_input_files()
        
        # Check for parsing errors
        if data.get('errors'):
            error_msg = data['errors'][0]
            return {
                'ANT_pvl.log': {
                    'line_number': 0,
                    'file_path': 'N/A',
                    'reason': error_msg
                }
            }
        
        # Check if rule deck info was successfully extracted
        items = data.get('items', [])
        if not items:
            return {
                'ANT_pvl.log': {
                    'line_number': 0,
                    'file_path': 'N/A',
                    'reason': 'Rule deck path, document name, or version not found in ANT log or rule deck file'
                }
            }
        
        # All checks passed
        return {}
    
    # =========================================================================
    # Type 4: Boolean Check with Waiver Logic
    # =========================================================================
    
    def _execute_type4(self) -> CheckResult:
        """Type 4: Boolean check with waiver support (reuses Type 1 core logic)."""
        violations = self._type1_core_logic()
        
        # Build found_items from successfully extracted rule decks
        data = self._parse_input_files()
        items = data.get('items', [])
        
        # Convert items to dict with metadata for found_items
        found_items = {
            item['name']: {
                'name': item['name'],
                'line_number': item.get('line_number', 0),
                'file_path': item.get('file_path', 'N/A')
            }
            for item in items
        }
        
        # FIXED: Use waivers.get() instead of get_waive_items()
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
    
    def _type2_core_logic(self) -> Tuple[Dict[str, Dict], Dict[str, Dict]]:
        """
        Core Type 2 pattern matching logic (shared by Type 2 and Type 3).
        
        Returns:
            Tuple of (found_items, missing_items)
            - found_items: {rule_deck_filename: {'line_number': ..., 'file_path': ...}}
            - missing_items: {rule_deck_filename: {'line_number': ..., 'file_path': ..., 'reason': ...}}
        """
        data = self._parse_input_files()
        items = data.get('items', [])
        
        requirements = self.item_data.get('requirements', {})
        pattern_items = requirements.get('pattern_items', [])
        
        # pattern_items[0] = Expected document identifier (e.g., "T-N05-CL-DR-014-N1")
        # pattern_items[1] = Expected version identifier (e.g., "014.13_1a")
        expected_doc = pattern_items[0] if len(pattern_items) > 0 else None
        expected_ver = pattern_items[1] if len(pattern_items) > 1 else None
        
        found_items = {}
        missing_items = {}
        
        # Process each rule deck file found in ANT_pvl.log
        for item in items:
            rule_deck_filename = item['name']
            current_doc = item.get('current_doc', 'N/A')
            current_ver = item.get('current_ver', 'N/A')
            line_number = item.get('line_number', 0)
            file_path = item.get('file_path', 'N/A')
            
            # Compare extracted document and version against expected pattern_items
            doc_match = (current_doc == expected_doc) if expected_doc else True
            ver_match = (current_ver == expected_ver) if expected_ver else True
            
            if doc_match and ver_match:
                # Document and version match expected values
                found_items[rule_deck_filename] = {
                    'name': rule_deck_filename,
                    'line_number': line_number,
                    'file_path': file_path,
                    'document': current_doc,
                    'version': current_ver
                }
            else:
                # Document or version mismatch
                mismatch_reason = []
                if not doc_match:
                    mismatch_reason.append('document mismatch')
                if not ver_match:
                    mismatch_reason.append('version mismatch')
                
                missing_items[rule_deck_filename] = {
                    'name': rule_deck_filename,
                    'line_number': line_number,
                    'file_path': file_path,
                    'document': current_doc,
                    'version': current_ver,
                    'reason': f"Rule deck {' and '.join(mismatch_reason)} detected"
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
# Entry Point
# =========================================================================

def main():
    """Main entry point."""
    checker = Check_2_0_0_04()
    checker.init_checker(Path(__file__))
    result = checker.execute_check()
    checker.write_output(result)
    return 0 if result.is_pass else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())