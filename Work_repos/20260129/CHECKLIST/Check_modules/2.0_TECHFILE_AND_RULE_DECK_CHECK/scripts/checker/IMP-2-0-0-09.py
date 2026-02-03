################################################################################
# Script Name: IMP-2-0-0-09.py
#
# Purpose:
#   Confirm BUMP rule deck was not modified? If it was, explain in comments field.
#
# Logic:
#   - Parse BUMP_pvl.log to extract local rule deck path from include statement
#   - For Type 1/4: Verify rule deck path exists
#   - For Type 2/3: Compare local rule deck against golden reference using diff
#   - Remove '//#' comment prefixes before comparison
#   - Generate diff report if modifications detected
#   - Support waiver for approved modifications
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
class Check_2_0_0_09(InputFileParserMixin, OutputBuilderMixin, WaiverHandlerMixin, BaseChecker):
    """
    IMP-2-0-0-09: Confirm BUMP rule deck was not modified? If it was, explain in comments field.
    
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
    FOUND_DESC_TYPE1_4 = "BUMP rule deck path found in PVL log"
    MISSING_DESC_TYPE1_4 = "BUMP rule deck path not found in PVL log"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_DESC_TYPE2_3 = "BUMP rule deck matches golden reference (not modified)"
    MISSING_DESC_TYPE2_3 = "BUMP rule deck has been modified from golden reference"
    
    # All Types (waiver description unified)
    WAIVED_DESC = "BUMP rule deck modification waived"
    
    # ⭐ REASON CONSTANTS - Split by Type semantics (API-025)
    # ALL Types pass found_reason/missing_reason, but use different constants
    
    # Type 1/4: Boolean checks - emphasize "found/not found" (existence)
    FOUND_REASON_TYPE1_4 = "Rule deck include path successfully extracted from BUMP_pvl.log"
    MISSING_REASON_TYPE1_4 = "Rule deck include statement not found in BUMP_pvl.log or path is empty"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_REASON_TYPE2_3 = "Rule deck content validated against golden reference - no modifications detected"
    MISSING_REASON_TYPE2_3 = "Rule deck content differs from golden reference - modifications detected (see diff report)"
    
    # Waiver-related (Type 3/4 only)
    WAIVED_BASE_REASON = "Rule deck modification approved and waived per project requirements"
    UNUSED_WAIVER_REASON = "Waiver entry not matched - specified rule deck name not found in violations"
    
    def __init__(self):
        """Initialize the checker."""
        super().__init__(
            check_module="2.0_TECHFILE_AND_RULE_DECK_CHECK",
            item_id="IMP-2-0-0-09",
            item_desc="Confirm BUMP rule deck was not modified? If it was, explain in comments field."
        )
        # Custom member variables for parsed data
        self._parsed_items: List[Dict[str, Any]] = []
        self._metadata: Dict[str, str] = {}
        self._local_rule_path: Optional[str] = None
        self._diff_report_path: Optional[Path] = None
    
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
        Parse BUMP_pvl.log to extract rule deck include path.
        
        Extracts the absolute path to the BUMP rule deck from the include statement.
        Pattern: include "C:\path\to\ruledeck\PN5_CU_BUMP_030.10_1a"
        
        Returns:
            Dict with parsed data:
            - 'items': List[Dict] - Rule deck information (path, name)
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
        
        # 3. Parse each input file for rule deck include statement
        # Pattern: include "C:\Users\chenweif\Checker_dev\CHECKLIST\CHECKLIST\IP_project_folder\ruledeck\2.0\PN5_CU_BUMP_030.10_1a"
        include_pattern = re.compile(r'^include\s+"([^"]+)"', re.IGNORECASE)
        
        for file_path in valid_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line_num, line in enumerate(f, 1):
                        match = include_pattern.search(line)
                        if match:
                            local_rule_path = match.group(1)
                            # Extract rule deck name from path
                            rule_deck_name = Path(local_rule_path).name
                            
                            items.append({
                                'name': rule_deck_name,
                                'line_number': line_num,
                                'file_path': str(file_path),
                                'full_path': local_rule_path,
                                'type': 'rule_deck'
                            })
                            break  # Only need first include statement
            except Exception as e:
                errors.append(f"Error parsing {file_path}: {str(e)}")
        
        # 4. Store frequently reused data on self
        self._parsed_items = items
        self._local_rule_path = local_rule_path
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
        """
        Type 1: Boolean check without waiver support.

        Verifies that the BUMP rule deck include path can be extracted from
        BUMP_pvl.log. PASS if path is found and non-empty, FAIL otherwise.
        """
        violations = self._type1_core_logic()

        # Build found_items from successfully extracted rule deck paths
        data = self._parse_input_files()
        items = data.get('items', [])
        
        # Convert items to dict with metadata for found_items
        found_items = {
            item['name']: {
                'name': item['name'],
                'line_number': item.get('line_number', 0),
                'file_path': item.get('file_path', 'N/A'),
                'path': item.get('full_path', 'N/A')
            }
            for item in items
        } if items and not violations else {}

        missing_items = violations if violations else {}

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

        Extracts and validates the BUMP rule deck include path from BUMP_pvl.log.

        Returns:
            Dict of violations: {item_name: {'line_number': ..., 'file_path': ..., 'reason': ...}}
            Empty dict if rule deck path is successfully extracted.
        """
        data = self._parse_input_files()
        violations = {}

        # Check for parsing errors
        errors = data.get('errors', [])
        if errors:
            for error in errors:
                violations[error] = {
                    'line_number': 0,
                    'file_path': 'N/A',
                    'reason': error
                }
            return violations

        # Check if rule deck path was extracted
        items = data.get('items', [])
        if not items:
            violations['missing_rule_deck_include'] = {
                'line_number': 0,
                'file_path': 'N/A',
                'reason': 'BUMP_pvl.log does not contain valid rule deck include statement'
            }

        return violations

    # =========================================================================
    # Type 4: Boolean Check with Waiver Logic
    # =========================================================================

    def _execute_type4(self) -> CheckResult:
        """
        Type 4: Boolean check with waiver support (reuses Type 1 core logic).

        Same as Type 1 but allows waiving violations (e.g., missing rule deck
        include statement or specific rule deck modifications).
        """
        # Step 1: Get violations using Type 1's core logic
        violations = self._type1_core_logic()

        # Build found_items from successfully extracted rule deck paths
        data = self._parse_input_files()
        items = data.get('items', [])
        
        # Convert items to dict with metadata for found_items
        found_items = {
            item['name']: {
                'name': item['name'],
                'line_number': item.get('line_number', 0),
                'file_path': item.get('file_path', 'N/A'),
                'path': item.get('full_path', 'N/A')
            }
            for item in items
        } if items and not violations else {}

        # Step 2: Parse waiver configuration
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)

        # Step 3: Split violations into waived and unwaived
        waived_items = {}
        unwaived_items = {}
        used_waivers = set()

        for viol_name, viol_data in violations.items():
            matched_waiver = self.match_waiver_entry(viol_name, waive_dict)
            if matched_waiver:
                waived_items[viol_name] = viol_data
                used_waivers.add(matched_waiver)
            else:
                unwaived_items[viol_name] = viol_data

        # Step 4: Find unused waivers
        unused_waivers = [w for w in waive_dict.keys() if w not in used_waivers]

        # Step 5: Build output
        return self.build_complete_output(
            found_items=found_items,
            missing_items=unwaived_items,
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
            - found_items: {deck_name: {'line_number': ..., 'file_path': ...}} - decks with no modifications
            - missing_items: {deck_name: {'line_number': ..., 'file_path': ..., 'reason': ...}} - decks with modifications
        """
        data = self._parse_input_files()
        items = data.get('items', [])

        requirements = self.item_data.get('requirements', {})
        pattern_items = requirements.get('pattern_items', [])

        if not pattern_items:
            raise ConfigurationError("pattern_items is empty - golden reference rule deck path required")

        golden_rule_path = Path(pattern_items[0])

        found_items = {}
        missing_items = {}

        # Process each extracted rule deck path from BUMP_pvl.log
        for item in items:
            local_rule_path = Path(item.get('full_path', ''))
            deck_name = item['name']

            # Check if local rule deck exists
            if not local_rule_path.exists():
                missing_items[deck_name] = {
                    'line_number': item.get('line_number', 0),
                    'file_path': str(local_rule_path),
                    'reason': f'Local rule deck not found: {local_rule_path}'
                }
                continue

            # Check if golden reference exists
            if not golden_rule_path.exists():
                missing_items[deck_name] = {
                    'line_number': item.get('line_number', 0),
                    'file_path': str(local_rule_path),
                    'reason': f'Golden reference rule deck not found: {golden_rule_path}'
                }
                continue

            # Perform diff comparison
            diff_result = self._compare_rule_decks(str(local_rule_path), str(golden_rule_path), deck_name)

            if diff_result['has_diff']:
                # Rule deck has modifications
                missing_items[deck_name] = {
                    'line_number': item.get('line_number', 0),
                    'file_path': str(local_rule_path),
                    'reason': f"Rule deck modified - diff report: {diff_result['diff_file']}"
                }
            else:
                # Rule deck matches golden reference
                found_items[deck_name] = {
                    'line_number': item.get('line_number', 0),
                    'file_path': str(local_rule_path)
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
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)

        # Step 3: Split violations into waived and unwaived
        found_items = {}
        waived_items = {}
        unwaived_items = {}
        used_waivers = set()

        # Process found_items_base (no waiver needed - clean rule decks)
        for item_name, item_data in found_items_base.items():
            found_items[item_name] = item_data

        # Process violations with waiver matching
        for viol_name, viol_data in violations.items():
            matched_waiver = self.match_waiver_entry(viol_name, waive_dict)
            if matched_waiver:
                waived_items[viol_name] = viol_data
                used_waivers.add(matched_waiver)
            else:
                unwaived_items[viol_name] = viol_data

        # Step 4: Find unused waivers
        unused_waivers = [w for w in waive_dict.keys() if w not in used_waivers]

        # Step 5: Construct diff file path for missing_reason
        res_temp_path = self.rpt_path.parent / f"{self.item_id}_diff.txt"
        missing_reason_with_path = f"{self.MISSING_REASON_TYPE2_3} - see diff file: {res_temp_path}"

        # Step 6: Build output
        return self.build_complete_output(
            found_items=found_items,
            missing_items=unwaived_items,
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
    # Helper Methods
    # =========================================================================

    def _compare_rule_decks(self, local_path: str, golden_path: str, deck_name: str) -> Dict[str, Any]:
        """
        Compare local rule deck with golden reference using diff.
        
        Process:
        1. Copy both files to temporary locations
        2. Remove '//#' comment prefixes (uncomment these lines)
        3. Perform diff comparison
        4. Save diff results to report file
        
        Args:
            local_path: Path to local rule deck
            golden_path: Path to golden reference rule deck
            deck_name: Name of the rule deck (for report naming)
            
        Returns:
            Dict with keys:
            - 'has_diff': bool - True if files differ
            - 'diff_file': str - Path to diff report file
        """
        try:
            # Create temporary directory for comparison
            temp_dir = self.rpt_path.parent / 'temp_rule_deck_compare'
            temp_dir.mkdir(exist_ok=True)
            
            loc_temp = temp_dir / 'local_rule_deck.tmp'
            gold_temp = temp_dir / 'golden_rule_deck.tmp'
            
            # Process local rule deck (remove '//#' prefixes)
            self._process_rule_deck_file(local_path, loc_temp)
            
            # Process golden rule deck (remove '//#' prefixes)
            self._process_rule_deck_file(golden_path, gold_temp)
            
            # Perform diff comparison
            with open(loc_temp, 'r', encoding='utf-8', errors='ignore') as f1:
                local_lines = f1.readlines()
            
            with open(gold_temp, 'r', encoding='utf-8', errors='ignore') as f2:
                golden_lines = f2.readlines()
            
            # Generate unified diff
            diff = list(difflib.unified_diff(
                golden_lines,
                local_lines,
                fromfile='Golden Reference',
                tofile='Local Rule Deck',
                lineterm=''
            ))
            
            # Save diff results
            if diff:
                # Files differ - save diff report
                diff_report_path = self.rpt_path.parent / f'{self.item_id}_diff.txt'
                with open(diff_report_path, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(diff))
                return {
                    'has_diff': True,
                    'diff_file': str(diff_report_path)
                }
            else:
                # Files are identical
                return {
                    'has_diff': False,
                    'diff_file': 'N/A'
                }
                
        except Exception as e:
            # If comparison fails, assume modified
            return {
                'has_diff': True,
                'diff_file': f'Error during comparison: {str(e)}'
            }
    
    def _process_rule_deck_file(self, source_path: str, dest_path: Path) -> None:
        """
        Process rule deck file by removing '//#' comment prefixes.
        
        Lines starting with '//#' are uncommented by removing the prefix.
        
        Args:
            source_path: Source file path
            dest_path: Destination file path
        """
        try:
            with open(source_path, 'r', encoding='utf-8', errors='ignore') as f_in:
                with open(dest_path, 'w', encoding='utf-8') as f_out:
                    for line in f_in:
                        # Remove '//#' prefix if present
                        if line.startswith('//#'):
                            processed_line = line[3:]  # Remove first 3 characters
                        else:
                            processed_line = line
                        f_out.write(processed_line)
        except Exception as e:
            # If processing fails, copy original file
            shutil.copy2(source_path, dest_path)


# =========================================================================
# Entry Point
# =========================================================================

def main():
    """Main entry point."""
    checker = Check_2_0_0_09()
    checker.init_checker(Path(__file__))
    result = checker.execute_check()
    checker.write_output(result)
    return 0 if result.is_pass else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())