################################################################################
# Script Name: IMP-2-0-0-05.py
#
# Purpose:
#   Confirm ANT rule deck was not modified? If it was, explain in comments field.
#
# Logic:
#   - Parse ANT_pvl.log to extract local ANT rule deck path from include statement
#   - Extract golden rule deck path from pattern_items[0] (baseline reference)
#   - For Type 1/4: Check if local_rule path exists and is valid
#   - For Type 2/3: Compare local_rule vs golden_rule using difflib after preprocessing
#   - Preprocessing: Remove '//' prefix from lines starting with '//#' (uncomment debug lines)
#   - Generate diff file (res_temp) if differences found
#   - Support waiver for approved modifications (Type 3/4)
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
import difflib
import shutil
from typing import List, Dict, Tuple, Optional, Any
from datetime import datetime


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
class Check_2_0_0_05(InputFileParserMixin, OutputBuilderMixin, WaiverHandlerMixin, BaseChecker):
    """
    IMP-2-0-0-05: Confirm ANT rule deck was not modified? If it was, explain in comments field.
    
    Checking Types:
    - Type 1: requirements=N/A, pattern_items [], waivers=N/A/0 → Boolean Check
    - Type 2: requirements>0, pattern_items [...], waivers=N/A/0 → Value Check
    - Type 3: requirements>0, pattern_items [...], waivers>0 → Value Check with Waiver Logic
    - Type 4: requirements=N/A, pattern_items [], waivers=N/A/0 → Boolean Check with Waiver Logic
    
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
    FOUND_DESC_TYPE1_4 = "ANT rule deck path found in log file"
    MISSING_DESC_TYPE1_4 = "ANT rule deck path not found in log file"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_DESC_TYPE2_3 = "ANT rule deck matches golden reference (unmodified)"
    MISSING_DESC_TYPE2_3 = "ANT rule deck modified - differences detected"
    
    # All Types (waiver description unified)
    WAIVED_DESC = "ANT rule deck modification waived"
    
    # ⭐ REASON CONSTANTS - Split by Type semantics (API-025)
    # ALL Types pass found_reason/missing_reason, but use different constants
    
    # Type 1/4: Boolean checks - emphasize "found/not found" (existence)
    FOUND_REASON_TYPE1_4 = "Rule deck path successfully extracted from ANT_pvl.log"
    MISSING_REASON_TYPE1_4 = "No include statement found in ANT_pvl.log or rule deck path is empty"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_REASON_TYPE2_3 = "Rule deck content matches golden reference - no modifications detected"
    MISSING_REASON_TYPE2_3 = "Rule deck content differs from golden reference - see diff file for details"
    
    # Waiver-related (Type 3/4 only)
    WAIVED_BASE_REASON = "Rule deck modification approved and waived per project requirements"
    UNUSED_WAIVER_REASON = "Waiver entry not matched - specified rule deck not found or not modified"
    
    def __init__(self):
        """Initialize the checker."""
        super().__init__(
            check_module="2.0_TECHFILE_AND_RULE_DECK_CHECK",
            item_id="IMP-2-0-0-05",
            item_desc="Confirm ANT rule deck was not modified? If it was, explain in comments field."
        )
        # Custom member variables for parsed data
        self._local_rule: Optional[str] = None
        self._golden_rule: Optional[str] = None
        self._diff_file: Optional[str] = None
        self._metadata: Dict[str, str] = {}
    
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
        Parse ANT_pvl.log to extract local ANT rule deck path.
        
        Extracts the absolute path to the ANT rule deck from include statement:
        Pattern: include "C:\path\to\ANT_rule_deck.encrypt"
        
        Returns:
            Dict with parsed data:
            - 'items': List[Dict] - Contains local_rule path info
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
        local_rule_path = None
        
        # 3. Parse each input file for ANT rule deck include statement
        # Pattern: include "C:\Users\chenweif\...\PLN5LO_16M_1X1Xb1Xe1Ya1Yb6Y2Yy2R_014_ANT.13_1a.encrypt"
        pattern = re.compile(r'include\s+"([^"]+)"')
        
        for file_path in valid_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line_num, line in enumerate(f, 1):
                        match = pattern.search(line)
                        if match:
                            local_rule_path = match.group(1)
                            items.append({
                                'name': Path(local_rule_path).name,
                                'path': local_rule_path,
                                'line_number': line_num,
                                'file_path': str(file_path),
                                'type': 'local_rule'
                            })
                            # Only take first match
                            break
            except Exception as e:
                errors.append(f"Error parsing {file_path}: {str(e)}")
        
        # 4. Store frequently reused data on self
        self._local_rule = local_rule_path
        self._metadata = metadata
        
        return {
            'items': items,
            'metadata': metadata,
            'errors': errors
        }
    
    # =========================================================================
    # Type 1: Boolean Check
    # =========================================================================
    
    def _execute_type1(self) -> CheckResult:
        """Type 1: Boolean check without waiver support.
        
        Checks if ANT rule deck path was successfully extracted from ANT_pvl.log.
        PASS: Rule deck path found and valid
        FAIL: No include statement found or rule deck path is empty
        """
        violations = self._type1_core_logic()
        
        # Build found_items from successfully extracted rule deck paths
        found_items = {}
        data = self._parse_input_files()
        local_rule = self._local_rule
        
        if local_rule and not violations:
            # Successfully extracted rule deck path
            rule_deck_name = Path(local_rule).name
            found_items[rule_deck_name] = {
                'name': rule_deck_name,
                'line_number': data.get('items', [{}])[0].get('line_number', 1),
                'file_path': local_rule
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
        
        Validates that ANT rule deck path was successfully extracted from ANT_pvl.log.
        
        Returns:
            Dict of violations: {item_name: {'line_number': ..., 'file_path': ..., 'reason': ...}}
            Empty dict if all checks pass.
        """
        data = self._parse_input_files()
        errors = data.get('errors', [])
        local_rule = self._local_rule
        
        violations = {}
        
        # Check for parsing errors
        if errors:
            for error in errors:
                violations['parsing_error'] = {
                    'line_number': 0,
                    'file_path': 'N/A',
                    'reason': error
                }
            return violations
        
        # Check if local_rule path was extracted
        if not local_rule:
            input_files = self.get_input_files()
            ant_log = input_files[0] if input_files else 'ANT_pvl.log'
            violations['ANT_pvl.log'] = {
                'line_number': 0,
                'file_path': ant_log,
                'reason': 'No include statement found in ANT_pvl.log or rule deck path is empty'
            }
        
        return violations
    
    # =========================================================================
    # Type 4: Boolean Check with Waiver Logic
    # =========================================================================
    
    def _execute_type4(self) -> CheckResult:
        """Type 4: Boolean check with waiver support (reuses Type 1 core logic).
        
        Same as Type 1 but allows waiving violations for approved rule deck modifications.
        Violations can be waived if rule deck modifications are documented and approved.
        """
        violations = self._type1_core_logic()
        
        # Build found_items from successfully extracted rule deck paths
        found_items = {}
        data = self._parse_input_files()
        local_rule = self._local_rule
        
        if local_rule and not violations:
            # Successfully extracted rule deck path
            rule_deck_name = Path(local_rule).name
            found_items[rule_deck_name] = {
                'name': rule_deck_name,
                'line_number': data.get('items', [{}])[0].get('line_number', 1),
                'file_path': local_rule
            }
        
        # FIXED: Use waivers.get() instead of get_waive_items() (API-016)
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
        """Type 2: Rule deck comparison check without waiver support."""
        found_items, missing_items = self._type2_core_logic()
        
        # Construct diff file path if differences found
        missing_reason = self.MISSING_REASON_TYPE2_3
        if missing_items:
            res_temp_path = self.rpt_path.parent / f"{self.item_id}_diff.txt"
            missing_reason = f"{self.MISSING_REASON_TYPE2_3} - see diff file: {res_temp_path}"
        
        return self.build_complete_output(
            found_items=found_items,
            missing_items=missing_items,
            found_desc=self.FOUND_DESC_TYPE2_3,
            missing_desc=self.MISSING_DESC_TYPE2_3,
            found_reason=self.FOUND_REASON_TYPE2_3,
            missing_reason=missing_reason
        )
    
    def _type2_core_logic(self) -> Tuple[Dict[str, dict], Dict[str, dict]]:
        """
        Core Type 2 rule deck comparison logic (shared by Type 2 and Type 3).
        
        Returns:
            Tuple of (found_items, missing_items)
            - found_items: {rule_deck_name: {'line_number': ..., 'file_path': ...}}
            - missing_items: {diff_file_name: {'line_number': ..., 'file_path': ..., 'reason': ...}}
        """
        data = self._parse_input_files()
        items = data.get('items', [])
        
        requirements = self.item_data.get('requirements', {})
        pattern_items = requirements.get('pattern_items', [])
        
        found_items = {}
        missing_items = {}
        
        if not pattern_items:
            return found_items, missing_items
        
        # Extract golden rule deck path from pattern_items[0]
        golden_rule_path = Path(pattern_items[0])
        
        # Extract local rule deck path from parsed items
        local_rule_path = None
        local_rule_line = 0
        local_rule_file = 'N/A'
        
        for item in items:
            if 'path' in item:
                local_rule_path = Path(item['path'])
                local_rule_line = item.get('line_number', 0)
                local_rule_file = item.get('file_path', 'N/A')
                break
        
        if not local_rule_path:
            missing_items['rule_deck_not_found'] = {
                'line_number': 0,
                'file_path': 'N/A',
                'reason': 'Local ANT rule deck path not found in log file'
            }
            return found_items, missing_items
        
        # Check if local rule deck file exists
        if not local_rule_path.exists():
            missing_items['rule_deck_missing'] = {
                'line_number': local_rule_line,
                'file_path': str(local_rule_file),
                'reason': f'Local rule deck file does not exist: {local_rule_path}'
            }
            return found_items, missing_items
        
        # Check if golden rule deck file exists
        if not golden_rule_path.exists():
            missing_items['golden_deck_missing'] = {
                'line_number': 0,
                'file_path': 'N/A',
                'reason': f'Golden rule deck file does not exist: {golden_rule_path}'
            }
            return found_items, missing_items
        
        # Preprocess and compare rule deck files
        try:
            # Read and preprocess local rule deck
            with open(local_rule_path, 'r', encoding='utf-8', errors='ignore') as f:
                local_lines = f.readlines()
            
            # Read and preprocess golden rule deck
            with open(golden_rule_path, 'r', encoding='utf-8', errors='ignore') as f:
                golden_lines = f.readlines()
            
            # Preprocessing: Remove '//' prefix from lines starting with '//#'
            def preprocess_lines(lines):
                processed = []
                for line in lines:
                    stripped = line.lstrip()
                    if stripped.startswith('//#'):
                        # Uncomment debug lines: remove '//' prefix
                        processed.append(stripped[2:])
                    else:
                        processed.append(line)
                return processed
            
            local_processed = preprocess_lines(local_lines)
            golden_processed = preprocess_lines(golden_lines)
            
            # Generate diff using difflib
            diff = list(difflib.unified_diff(
                golden_processed,
                local_processed,
                fromfile=str(golden_rule_path),
                tofile=str(local_rule_path),
                lineterm=''
            ))
            
            if diff:
                # Differences found - generate diff file
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                diff_filename = f"{self.item_id}_diff_{timestamp}.txt"
                diff_path = self.rpt_path.parent / diff_filename
                
                with open(diff_path, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(diff))
                
                missing_items[diff_filename] = {
                    'line_number': 0,
                    'file_path': str(diff_path),
                    'reason': 'Rule deck content differs from golden reference'
                }
            else:
                # No differences - rule deck matches golden reference
                found_items[local_rule_path.name] = {
                    'line_number': local_rule_line,
                    'file_path': str(local_rule_file)
                }
        
        except Exception as e:
            missing_items['comparison_error'] = {
                'line_number': 0,
                'file_path': 'N/A',
                'reason': f'Error comparing rule decks: {str(e)}'
            }
        
        return found_items, missing_items
    
    # =========================================================================
    # Type 3: Value Check with Waiver Logic
    # =========================================================================
    
    def _execute_type3(self) -> CheckResult:
        """Type 3: Rule deck comparison check with waiver support (reuses Type 2 core logic)."""
        # Step 1: Get found/missing items using Type 2's core logic
        found_items_base, violations = self._type2_core_logic()
        
        # Step 2: Parse waiver configuration
        # FIXED: Use waivers.get() instead of get_waive_items() (API-016)
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # Step 3: Split violations into waived and unwaived
        found_items = {}
        waived_items = {}
        missing_items = {}
        used_waivers = set()
        
        # Process found_items_base (no waiver needed - clean matches)
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
        
        # Step 5: Construct diff file path if differences found
        missing_reason = self.MISSING_REASON_TYPE2_3
        if missing_items:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            res_temp_path = self.rpt_path.parent / f"{self.item_id}_diff_{timestamp}.txt"
            missing_reason = f"{self.MISSING_REASON_TYPE2_3} - see diff file: {res_temp_path}"
        
        # Step 6: Build output
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
            missing_reason=missing_reason,
            waived_base_reason=self.WAIVED_BASE_REASON,
            unused_waiver_reason=self.UNUSED_WAIVER_REASON
        )


# =========================================================================
# Entry Point
# =========================================================================

def main():
    """Main entry point."""
    checker = Check_2_0_0_05()
    checker.init_checker(Path(__file__))
    result = checker.execute_check()
    checker.write_output(result)
    return 0 if result.is_pass else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())