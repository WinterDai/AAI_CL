################################################################################
# Script Name: IMP-2-0-0-15.py
#
# Purpose:
#   List QRC techfile name. eg: 17M1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2Yx2R_SHDMIM_UT/fs_v1d0p1a
#
# Logic:
#   - Parse extraction log to locate process_technology option line
#   - Extract QRC techfile path from technology_name parameter
#   - Extract metal_stack/corner_variant from full QRC path
#   - For Type 1/4: Verify QRC path exists and is valid
#   - For Type 2/3: Compare extracted QRC tech against golden reference in pattern_items
#   - Support waiver for techfile version mismatches (Type 3/4)
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
class Check_2_0_0_15(InputFileParserMixin, OutputBuilderMixin, WaiverHandlerMixin, BaseChecker):
    """
    IMP-2-0-0-15: List QRC techfile name. eg: 17M1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2Yx2R_SHDMIM_UT/fs_v1d0p1a
    
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
    FOUND_DESC_TYPE1_4 = "QRC techfile reference found in extraction log"
    MISSING_DESC_TYPE1_4 = "QRC techfile reference not found in extraction log"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_DESC_TYPE2_3 = "QRC techfile version matched expected configuration"
    MISSING_DESC_TYPE2_3 = "QRC techfile version mismatch detected"
    
    # All Types (waiver description unified)
    WAIVED_DESC = "QRC techfile version mismatch waived"
    
    # ⭐ REASON CONSTANTS - Split by Type semantics (API-025)
    # ALL Types pass found_reason/missing_reason, but use different constants
    
    # Type 1/4: Boolean checks - emphasize "found/not found" (existence)
    FOUND_REASON_TYPE1_4 = "QRC technology file path successfully extracted from process_technology option"
    MISSING_REASON_TYPE1_4 = "QRC technology file path not found in process_technology option or extraction log"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_REASON_TYPE2_3 = "QRC techfile version matched and validated against golden reference"
    MISSING_REASON_TYPE2_3 = "QRC techfile version does not match expected golden reference"
    
    # Waiver-related (Type 3/4 only)
    WAIVED_BASE_REASON = "QRC techfile version mismatch waived per design team approval"
    UNUSED_WAIVER_REASON = "Waiver entry not matched - no corresponding techfile mismatch found"
    
    def __init__(self):
        """Initialize the checker."""
        super().__init__(
            check_module="2.0_TECHFILE_AND_RULE_DECK_CHECK",
            item_id="IMP-2-0-0-15",
            item_desc="List QRC techfile name. eg: 17M1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2Yx2R_SHDMIM_UT/fs_v1d0p1a"
        )
        # Custom member variables for parsed data
        self._parsed_items: List[Dict[str, Any]] = []
        self._metadata: Dict[str, str] = {}
        self._qrc_tech: Optional[str] = None
    
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
        Parse extraction log to extract QRC techfile information.
        
        Searches for process_technology option line and extracts:
        - Full QRC path from -technology_name parameter
        - Metal stack and corner variant (e.g., 16M1X1Xb1Xe1Ya1Yb6Y2Yy2R_SHDMIM_UT/fs_v1d2p4a)
        
        Returns:
            Dict with parsed data:
            - 'items': List[Dict] - QRC techfile entries with metadata
            - 'qrc_tech': str - Extracted QRC techfile version
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
        qrc_tech = None
        
        # 3. Parse each input file for QRC techfile information
        # Pattern 1: Locate process_technology option line
        pattern1 = r'.*Option\s+process_technology\s+-technology_name\s*='
        # Pattern 2: Extract metal_stack/corner_variant from full path
        pattern3 = r'/QRC/([^/]+/[^/]+)/'
        
        for file_path in valid_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                    
                    for line_num, line in enumerate(lines, 1):
                        # Look for process_technology option line
                        if re.search(pattern1, line):
                            # Extract QRC path from this line or next lines
                            # The path typically follows the = sign
                            match = re.search(pattern3, line)
                            if match:
                                qrc_tech = match.group(1)
                                items.append({
                                    'name': qrc_tech,
                                    'line_number': line_num,
                                    'file_path': str(file_path),
                                    'type': 'qrc_techfile'
                                })
                                metadata = {
                                    'line_number': line_num,
                                    'file_path': str(file_path)
                                }
                                break
                            else:
                                # Check next few lines for the path
                                for next_line_offset in range(1, 5):
                                    if line_num + next_line_offset <= len(lines):
                                        next_line = lines[line_num + next_line_offset - 1]
                                        match = re.search(pattern3, next_line)
                                        if match:
                                            qrc_tech = match.group(1)
                                            items.append({
                                                'name': qrc_tech,
                                                'line_number': line_num + next_line_offset,
                                                'file_path': str(file_path),
                                                'type': 'qrc_techfile'
                                            })
                                            metadata = {
                                                'line_number': line_num + next_line_offset,
                                                'file_path': str(file_path)
                                            }
                                            break
                                if qrc_tech:
                                    break
                    
                    if qrc_tech:
                        break
                        
            except Exception as e:
                errors.append(f"Error parsing {file_path}: {str(e)}")
        
        # 4. Store frequently reused data on self
        self._parsed_items = items
        self._qrc_tech = qrc_tech
        self._metadata = metadata
        
        return {
            'items': items,
            'qrc_tech': qrc_tech,
            'metadata': metadata,
            'errors': errors
        }
    
    # =========================================================================
    # Type 1: Boolean Check
    # =========================================================================
    
    def _execute_type1(self) -> CheckResult:
        """
        Type 1: Boolean check without waiver support.
        
        Verifies that QRC techfile path can be extracted from the extraction log.
        PASS if qrc_tech is found and valid.
        FAIL if qrc_tech cannot be extracted or is empty.
        """
        violations = self._type1_core_logic()
        
        # Build found_items from successfully extracted QRC techfile
        data = self._parse_input_files()
        qrc_tech = data.get('qrc_tech', '')
        metadata = data.get('metadata', {})
        
        found_items = {}
        if qrc_tech:
            found_items[qrc_tech] = {
                'line_number': metadata.get('line_number', 0),
                'file_path': metadata.get('file_path', 'N/A')
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
    
    def _type1_core_logic(self) -> Dict[str, Dict]:
        """
        Core Type 1 boolean check logic (shared by Type 1 and Type 4).
        
        Extracts QRC techfile path from extraction log and validates it exists.
        
        Returns:
            Dict of violations: {item_name: {'line_number': ..., 'file_path': ..., 'reason': ...}}
            Empty dict if QRC techfile is successfully extracted.
        """
        data = self._parse_input_files()
        qrc_tech = data.get('qrc_tech', '')
        errors = data.get('errors', [])
        metadata = data.get('metadata', {})
        
        violations = {}
        
        # Check for parsing errors
        if errors:
            for error in errors:
                violations[error] = {
                    'line_number': 0,
                    'file_path': metadata.get('file_path', 'N/A'),
                    'reason': 'QRC techfile extraction failed'
                }
            return violations
        
        # Check if QRC techfile was extracted
        if not qrc_tech:
            violations['QRC techfile reference not found'] = {
                'line_number': 0,
                'file_path': metadata.get('file_path', 'N/A'),
                'reason': 'QRC technology file path not found in process_technology option or extraction log'
            }
        
        return violations
    
    # =========================================================================
    # Type 4: Boolean Check with Waiver Logic
    # =========================================================================
    
    def _execute_type4(self) -> CheckResult:
        """
        Type 4: Boolean check with waiver support (reuses Type 1 core logic).
        
        Same boolean check as Type 1, but violations can be waived.
        PASS if QRC techfile is found OR all violations are waived.
        FAIL if unwaived violations exist.
        """
        # Step 1: Get violations using Type 1's core logic
        violations = self._type1_core_logic()
        
        # Build found_items from successfully extracted QRC techfile
        data = self._parse_input_files()
        qrc_tech = data.get('qrc_tech', '')
        metadata = data.get('metadata', {})
        
        found_items = {}
        if qrc_tech:
            found_items[qrc_tech] = {
                'line_number': metadata.get('line_number', 0),
                'file_path': metadata.get('file_path', 'N/A')
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
            - found_items: {qrc_tech: {'line_number': ..., 'file_path': ...}}
            - missing_items: {pattern: {'line_number': ..., 'file_path': ..., 'reason': ...}}
        """
        data = self._parse_input_files()
        items = data.get('items', [])
        qrc_tech = data.get('qrc_tech', '')
        metadata = data.get('metadata', {})
        
        requirements = self.item_data.get('requirements', {})
        pattern_items = requirements.get('pattern_items', [])
        
        found_items = {}
        missing_items = {}
        
        # Extract QRC techfile version from parsed items
        if not items:
            # No QRC techfile found in log
            for pattern in pattern_items:
                missing_items[pattern] = {
                    'line_number': 0,
                    'file_path': 'N/A',
                    'reason': f'QRC techfile not found in extraction log (expected: {pattern})'
                }
            return found_items, missing_items
        
        # Type 2: Compare extracted QRC tech against golden reference in pattern_items
        # pattern_items should contain exactly one golden QRC techfile version
        if not pattern_items:
            # No golden reference defined - report extracted QRC as found
            found_items[qrc_tech] = {
                'line_number': metadata.get('line_number', 0),
                'file_path': metadata.get('file_path', 'N/A')
            }
        else:
            golden_qrc = pattern_items[0]
            
            # EXACT MATCH: QRC techfile version must match exactly
            if qrc_tech.lower() == golden_qrc.lower():
                # Match - QRC techfile version is correct
                found_items[qrc_tech] = {
                    'line_number': metadata.get('line_number', 0),
                    'file_path': metadata.get('file_path', 'N/A')
                }
            else:
                # Mismatch - QRC techfile version does not match golden reference
                missing_items[qrc_tech] = {
                    'line_number': metadata.get('line_number', 0),
                    'file_path': metadata.get('file_path', 'N/A'),
                    'reason': f'Found: {qrc_tech} | Expected: {golden_qrc}'
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
        
        # Process found_items_base (no waiver needed - already matched golden reference)
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
    checker = Check_2_0_0_15()
    checker.init_checker(Path(__file__))
    result = checker.execute_check()
    checker.write_output(result)
    return 0 if result.is_pass else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())