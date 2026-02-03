################################################################################
# Script Name: IMP-2-0-0-07.py
#
# Purpose:
#   Confirm LVS rule deck was not modified? If it was, explain in comments field.
#
# Logic:
#   - Parse LVS_pvl.log to extract LVS rule deck absolute path from include statement
#   - Extract local rule deck path from log file (already absolute path)
#   - For Type 2/3: Compare local rule deck against golden baseline from pattern_items
#   - Create temporary files with uncommented lines (remove // prefix from //#)
#   - Use difflib to compare processed files and generate diff report
#   - PASS if no differences detected, FAIL if modifications found
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
import tempfile
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
class Check_2_0_0_07(InputFileParserMixin, OutputBuilderMixin, WaiverHandlerMixin, BaseChecker):
    """
    IMP-2-0-0-07: Confirm LVS rule deck was not modified? If it was, explain in comments field.
    
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
    FOUND_DESC_TYPE1_4 = "LVS rule deck path found in log file"
    MISSING_DESC_TYPE1_4 = "LVS rule deck path not found in log file"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_DESC_TYPE2_3 = "LVS rule deck matches golden baseline (no modifications detected)"
    MISSING_DESC_TYPE2_3 = "LVS rule deck modified - differences detected from golden baseline"
    
    # All Types (waiver description unified)
    WAIVED_DESC = "LVS rule deck modifications waived"
    
    # ⭐ REASON CONSTANTS - Split by Type semantics (API-025)
    # ALL Types pass found_reason/missing_reason, but use different constants
    
    # Type 1/4: Boolean checks - emphasize "found/not found" (existence)
    FOUND_REASON_TYPE1_4 = "LVS rule deck path successfully extracted from LVS_pvl.log"
    MISSING_REASON_TYPE1_4 = "LVS rule deck include statement not found in LVS_pvl.log"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_REASON_TYPE2_3 = "LVS rule deck content matched golden baseline - no modifications detected"
    MISSING_REASON_TYPE2_3 = "LVS rule deck content differs from golden baseline - see diff report for details"
    
    # Waiver-related (Type 3/4 only)
    WAIVED_BASE_REASON = "LVS rule deck modification waived per design team approval"
    UNUSED_WAIVER_REASON = "Waiver not matched - no corresponding rule deck modification found"
    
    def __init__(self):
        """Initialize the checker."""
        super().__init__(
            check_module="2.0_TECHFILE_AND_RULE_DECK_CHECK",
            item_id="IMP-2-0-0-07",
            item_desc="Confirm LVS rule deck was not modified? If it was, explain in comments field."
        )
        # Custom member variables for parsed data
        self._local_rule: Optional[str] = None
        self._golden_rule: Optional[str] = None
        self._diff_report_path: Optional[str] = None
    
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
        Parse LVS_pvl.log to extract LVS rule deck absolute path.
        
        Searches for include statement pattern: include "absolute_path"
        Extracts the path between double quotes as local_rule.
        
        Returns:
            Dict with parsed data:
            - 'items': List[Dict] - Local rule deck path information
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
        local_rule = None
        
        # 3. Parse each input file for LVS rule deck include statement
        # Pattern: include "absolute_path"
        include_pattern = re.compile(r'^include\s+"([^"]+)"')
        
        for file_path in valid_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line_num, line in enumerate(f, 1):
                        match = include_pattern.search(line)
                        if match:
                            local_rule = match.group(1)
                            items.append({
                                'name': local_rule,
                                'line_number': line_num,
                                'file_path': str(file_path),
                                'type': 'lvs_rule_deck'
                            })
                            # Only need first match
                            break
            except Exception as e:
                errors.append(f"Error parsing {file_path}: {str(e)}")
        
        # 4. Store frequently reused data on self
        self._local_rule = local_rule
        
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

        Validates that LVS rule deck path can be extracted from log file.
        PASS if include statement with rule deck path is found.
        FAIL if include statement is missing or path is empty.
        """
        violations = self._type1_core_logic()

        # Build found_items from successfully extracted rule deck path
        found_items = {}
        data = self._parse_input_files()

        if not violations and data.get('items'):
            # Rule deck path successfully extracted
            item = data['items'][0]
            found_items[item['name']] = {
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

        Extracts LVS rule deck path from log file and validates extraction.

        Returns:
            Dict of violations: {item_name: {'line_number': ..., 'file_path': ..., 'reason': ...}}
            Empty dict if rule deck path successfully extracted.
        """
        data = self._parse_input_files()
        errors = data.get('errors', [])
        items = data.get('items', [])

        violations = {}

        # Check for parsing errors
        if errors:
            for idx, error in enumerate(errors):
                violations[f'parsing_error_{idx}'] = {
                    'line_number': 0,
                    'file_path': 'N/A',
                    'reason': error
                }

        # Check if rule deck path was extracted
        if not items and not errors:
            violations['rule_deck_extraction_failed'] = {
                'line_number': 0,
                'file_path': 'N/A',
                'reason': 'LVS rule deck path extraction failed - no include statement found in log file'
            }

        return violations

    # =========================================================================
    # Type 4: Boolean Check with Waiver Logic
    # =========================================================================

    def _execute_type4(self) -> CheckResult:
        """
        Type 4: Boolean check with waiver support (reuses Type 1 core logic).

        Same as Type 1 but allows waiving extraction failures.
        Useful when rule deck path extraction is informational or when
        specific extraction failures are acceptable.
        """
        violations = self._type1_core_logic()

        # Build found_items from successfully extracted rule deck path
        found_items = {}
        data = self._parse_input_files()

        if not violations and data.get('items'):
            # Rule deck path successfully extracted
            item = data['items'][0]
            found_items[item['name']] = {
                'line_number': item.get('line_number', 0),
                'file_path': item.get('file_path', 'N/A')
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
        """Type 2: Rule deck comparison check without waiver support."""
        found_items, missing_items = self._type2_core_logic()

        # Construct diff file path for missing_reason
        res_temp_path = self.rpt_path.parent / f"{self.item_id}_diff.txt"
        missing_reason_with_path = f"{self.MISSING_REASON_TYPE2_3} - see diff file: {res_temp_path}"

        return self.build_complete_output(
            found_items=found_items,
            missing_items=missing_items,
            found_desc=self.FOUND_DESC_TYPE2_3,
            missing_desc=self.MISSING_DESC_TYPE2_3,
            found_reason=self.FOUND_REASON_TYPE2_3,
            missing_reason=missing_reason_with_path
        )

    def _type2_core_logic(self) -> Tuple[Dict[str, Dict], Dict[str, Dict]]:
        """
        Core Type 2 rule deck comparison logic (shared by Type 2 and Type 3).

        Returns:
            Tuple of (found_items, missing_items)
            - found_items: {comparison_key: {'line_number': ..., 'file_path': ...}}
            - missing_items: {comparison_key: {'line_number': ..., 'file_path': ..., 'reason': ...}}
        """
        data = self._parse_input_files()
        items = data.get('items', [])

        requirements = self.item_data.get('requirements', {})
        pattern_items = requirements.get('pattern_items', [])

        found_items = {}
        missing_items = {}

        # Validate pattern_items configuration
        if not pattern_items or len(pattern_items) == 0:
            missing_items['configuration_error'] = {
                'line_number': 0,
                'file_path': 'N/A',
                'reason': 'No golden baseline rule deck path specified in pattern_items'
            }
            return found_items, missing_items

        # Extract golden baseline path from pattern_items[0]
        golden_rule = Path(pattern_items[0])

        # Extract local rule deck path from parsed items
        if not items or len(items) == 0:
            missing_items['parsing_error'] = {
                'line_number': 0,
                'file_path': 'N/A',
                'reason': 'No LVS rule deck path found in log file'
            }
            return found_items, missing_items

        local_rule = Path(items[0]['name'])

        # Validate file existence
        if not golden_rule.exists():
            missing_items['golden_file_missing'] = {
                'line_number': 0,
                'file_path': str(golden_rule),
                'reason': f'Golden baseline rule deck not found: {golden_rule}'
            }
            return found_items, missing_items

        if not local_rule.exists():
            missing_items['local_file_missing'] = {
                'line_number': 0,
                'file_path': str(local_rule),
                'reason': f'Local rule deck not found: {local_rule}'
            }
            return found_items, missing_items

        # Perform file comparison with uncommented lines
        try:
            # Create temporary files with uncommented lines
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.tmp') as golden_tmp:
                golden_tmp_path = Path(golden_tmp.name)
                with open(golden_rule, 'r', encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        # Remove // prefix from //#
                        uncommented_line = re.sub(r'^//#', '', line)
                        golden_tmp.write(uncommented_line)

            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.tmp') as local_tmp:
                local_tmp_path = Path(local_tmp.name)
                with open(local_rule, 'r', encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        # Remove // prefix from //#
                        uncommented_line = re.sub(r'^//#', '', line)
                        local_tmp.write(uncommented_line)

            # Read processed files for comparison
            with open(golden_tmp_path, 'r', encoding='utf-8', errors='ignore') as f:
                golden_lines = f.readlines()

            with open(local_tmp_path, 'r', encoding='utf-8', errors='ignore') as f:
                local_lines = f.readlines()

            # Generate diff using difflib
            diff = list(difflib.unified_diff(
                golden_lines,
                local_lines,
                fromfile=f'Golden: {golden_rule.name}',
                tofile=f'Local: {local_rule.name}',
                lineterm=''
            ))

            # Clean up temporary files
            golden_tmp_path.unlink(missing_ok=True)
            local_tmp_path.unlink(missing_ok=True)

            # Check if differences exist
            if diff:
                # Write diff report to file
                diff_report_path = self.rpt_path.parent / f"{self.item_id}_diff.txt"
                with open(diff_report_path, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(diff))

                # Extract rule deck filename for missing_items key
                rule_deck_name = local_rule.name

                missing_items[rule_deck_name] = {
                    'line_number': 0,
                    'file_path': str(diff_report_path),
                    'reason': f'Rule deck differs from golden baseline'
                }
            else:
                # No differences - files are identical
                comparison_key = f"Local rule deck: {local_rule.name} | Golden rule deck: {golden_rule.name}"
                found_items[comparison_key] = {
                    'line_number': items[0].get('line_number', 0),
                    'file_path': str(local_rule)
                }

        except Exception as e:
            missing_items['comparison_error'] = {
                'line_number': 0,
                'file_path': 'N/A',
                'reason': f'File comparison failed: {str(e)}'
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
        # FIXED: Use waivers.get() instead of get_waive_items()
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)

        # Step 3: Split violations into waived and unwaived
        found_items = {}
        waived_items = {}
        missing_items = {}
        used_waivers = set()

        # Process found_items_base (no waiver needed - files matched)
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

        # Step 5: Construct diff file path for missing_reason
        res_temp_path = self.rpt_path.parent / f"{self.item_id}_diff.txt"
        missing_reason_with_path = f"{self.MISSING_REASON_TYPE2_3} - see diff file: {res_temp_path}"

        # Step 6: Build output
        # FIXED: Pass dict directly, not list(dict.values())
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
            missing_reason=missing_reason_with_path,
            waived_base_reason=self.WAIVED_BASE_REASON,
            unused_waiver_reason=self.UNUSED_WAIVER_REASON
        )


# =========================================================================
# Entry Point
# =========================================================================

def main():
    """Main entry point."""
    checker = Check_2_0_0_07()
    checker.init_checker(Path(__file__))
    result = checker.execute_check()
    checker.write_output(result)
    return 0 if result.is_pass else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())