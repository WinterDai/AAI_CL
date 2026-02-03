################################################################################
# Script Name: IMP-2-0-0-03.py
#
# Purpose:
#   Confirm DRC rule deck was not modified? If it was, explain in comments field.
#
# Logic:
#   - Parse DRC_pvl.log to extract local rule deck path from include directive
#   - For Type 1/4: Verify rule deck path exists
#   - For Type 2/3: Compare local rule deck against golden baseline
#   - Create temporary files with normalized content (remove // from //#)
#   - Use difflib.unified_diff() to detect modifications
#   - Generate diff report file under rpt_path.parent
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
import tempfile
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
class Check_2_0_0_03(InputFileParserMixin, OutputBuilderMixin, WaiverHandlerMixin, BaseChecker):
    """
    IMP-2-0-0-03: Confirm DRC rule deck was not modified? If it was, explain in comments field.
    
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
    FOUND_DESC_TYPE1_4 = "DRC rule deck path found in log file"
    MISSING_DESC_TYPE1_4 = "DRC rule deck path not found in log file"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_DESC_TYPE2_3 = "DRC rule deck matches golden baseline (unmodified)"
    MISSING_DESC_TYPE2_3 = "DRC rule deck modified from golden baseline"
    
    # All Types (waiver description unified)
    WAIVED_DESC = "DRC rule deck modification waived"
    
    # ⭐ REASON CONSTANTS - Split by Type semantics (API-025)
    # ALL Types pass found_reason/missing_reason, but use different constants
    
    # Type 1/4: Boolean checks - emphasize "found/not found" (existence)
    FOUND_REASON_TYPE1_4 = "Rule deck path successfully extracted from DRC log"
    MISSING_REASON_TYPE1_4 = "Rule deck path not found in DRC log file - cannot verify integrity"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_REASON_TYPE2_3 = "Rule deck content matches golden baseline - no modifications detected"
    MISSING_REASON_TYPE2_3 = "Rule deck content differs from golden baseline - modifications detected"
    
    # Waiver-related (Type 3/4 only)
    WAIVED_BASE_REASON = "Rule deck modification waived per project approval"
    UNUSED_WAIVER_REASON = "Waiver entry not matched - no corresponding rule deck modification found"
    
    def __init__(self):
        """Initialize the checker."""
        super().__init__(
            check_module="2.0_TECHFILE_AND_RULE_DECK_CHECK",
            item_id="IMP-2-0-0-03",
            item_desc="Confirm DRC rule deck was not modified? If it was, explain in comments field."
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
        Parse DRC_pvl.log to extract local rule deck path from include directive.
        
        Searches for pattern: include "path/to/rule_deck.pvl"
        Extracts the absolute path to the local DRC rule deck file.
        
        Returns:
            Dict with parsed data:
            - 'items': List[Dict] - Rule deck information (path, existence)
            - 'metadata': Dict - File metadata (log file path)
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
        
        # Pattern to match: include "path/to/file.pvl"
        include_pattern = re.compile(r'^include\s+"([^"]+)"')
        
        # 3. Parse each input file for rule deck include directive
        for file_path in valid_files:
            try:
                metadata['log_file'] = str(file_path)
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line_num, line in enumerate(f, 1):
                        match = include_pattern.search(line)
                        if match:
                            local_rule_path = match.group(1)
                            # Check if file exists
                            rule_deck_file = Path(local_rule_path)
                            exists = rule_deck_file.exists()
                            
                            items.append({
                                'name': local_rule_path,
                                'line_number': line_num,
                                'file_path': str(file_path),
                                'type': 'rule_deck',
                                'exists': exists
                            })
                            break  # Found the include directive
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
        """Type 1: Boolean check without waiver support."""
        violations = self._type1_core_logic()
        
        # ⚠️ CRITICAL: found_items MUST be dict[str, dict], NOT list!
        # Build dict from clean/passing objects (rule deck path successfully extracted)
        found_items = {}
        data = self._parse_input_files()
        items = data.get('items', [])
        
        if items and not violations:
            # Rule deck path successfully extracted and exists
            item = items[0]
            found_items[item['name']] = {
                'name': item['name'],
                'line_number': item.get('line_number', 0),
                'file_path': item.get('file_path', 'N/A')
            }
        
        # FIXED: Pass dict directly, not list
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
        errors = data.get('errors', [])
        items = data.get('items', [])
        
        violations = {}
        
        # Check for parsing errors
        if errors:
            for error in errors:
                violations['DRC_pvl.log'] = {
                    'line_number': 0,
                    'file_path': 'N/A',
                    'reason': error
                }
            return violations
        
        # Check if rule deck path was extracted
        if not items or len(items) == 0:
            violations['DRC_pvl.log'] = {
                'line_number': 0,
                'file_path': data.get('metadata', {}).get('log_file', 'N/A'),
                'reason': 'Rule deck path not found in DRC log file - cannot verify integrity'
            }
        else:
            # Check if file exists
            item = items[0]
            if not item.get('exists', False):
                violations[item['name']] = {
                    'line_number': item.get('line_number', 0),
                    'file_path': item.get('file_path', 'N/A'),
                    'reason': f'Rule deck file not found: {item["name"]}'
                }
        
        return violations
    
    # =========================================================================
    # Type 4: Boolean Check with Waiver Logic
    # =========================================================================
    
    def _execute_type4(self) -> CheckResult:
        """Type 4: Boolean check with waiver support (reuses Type 1 core logic)."""
        # Step 1: Get violations using Type 1's core logic
        violations = self._type1_core_logic()
        
        # ⚠️ CRITICAL: found_items MUST be dict[str, dict], NOT list!
        # Build dict from clean/passing objects (rule deck path successfully extracted)
        found_items = {}
        data = self._parse_input_files()
        items = data.get('items', [])
        
        if items and not violations:
            # Rule deck path successfully extracted and exists
            item = items[0]
            found_items[item['name']] = {
                'name': item['name'],
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
        """Type 2: Rule deck comparison check without waiver support."""
        found_items, missing_items = self._type2_core_logic()
        
        # Construct diff file path for missing_reason
        res_temp_path = self.rpt_path.parent / f"{self.item_id}_diff.txt"
        missing_reason_with_path = f"{self.MISSING_REASON_TYPE2_3} - see diff file: {res_temp_path}"
        
        # FIXED: Pass dict directly, not list
        return self.build_complete_output(
            found_items=found_items,
            missing_items=missing_items,
            found_desc=self.FOUND_DESC_TYPE2_3,
            missing_desc=self.MISSING_DESC_TYPE2_3,
            found_reason=self.FOUND_REASON_TYPE2_3,
            missing_reason=missing_reason_with_path
        )
    
    def _type2_core_logic(self) -> Tuple[Dict[str, dict], Dict[str, dict]]:
        """
        Core Type 2 rule deck comparison logic (shared by Type 2 and Type 3).
        
        Returns:
            Tuple of (found_items, missing_items)
            - found_items: {rule_deck_name: {'line_number': ..., 'file_path': ...}}
            - missing_items: {rule_deck_name: {'line_number': ..., 'file_path': ..., 'reason': ...}}
        """
        data = self._parse_input_files()
        items = data.get('items', [])
        
        requirements = self.item_data.get('requirements', {})
        pattern_items = requirements.get('pattern_items', [])
        
        found_items = {}
        missing_items = {}
        
        # pattern_items[0] contains the golden rule deck path
        if not pattern_items:
            raise ConfigurationError("pattern_items must contain golden rule deck path")
        
        golden_rule_deck = Path(pattern_items[0])
        
        # Check if golden rule deck exists
        if not golden_rule_deck.exists():
            missing_items['golden_rule_deck'] = {
                'line_number': 0,
                'file_path': str(golden_rule_deck),
                'reason': f'Golden rule deck not found: {golden_rule_deck}'
            }
            return found_items, missing_items
        
        # Process each local rule deck found in DRC log
        for item in items:
            local_rule_deck = Path(item['name'])
            line_number = item.get('line_number', 0)
            file_path = item.get('file_path', 'N/A')
            
            # Check if local rule deck exists
            if not local_rule_deck.exists():
                missing_items[item['name']] = {
                    'line_number': line_number,
                    'file_path': file_path,
                    'reason': f'Local rule deck not found: {local_rule_deck}'
                }
                continue
            
            # Compare local rule deck against golden baseline
            try:
                # Create temporary normalized files (remove // from //#)
                with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='_golden') as golden_temp:
                    with open(golden_rule_deck, 'r', encoding='utf-8', errors='ignore') as f:
                        golden_content = f.read()
                        # Normalize: remove // from //#
                        normalized_golden = re.sub(r'^//\s*#', '#', golden_content, flags=re.MULTILINE)
                        golden_temp.write(normalized_golden)
                        golden_temp_path = golden_temp.name
                
                with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='_local') as local_temp:
                    with open(local_rule_deck, 'r', encoding='utf-8', errors='ignore') as f:
                        local_content = f.read()
                        # Normalize: remove // from //#
                        normalized_local = re.sub(r'^//\s*#', '#', local_content, flags=re.MULTILINE)
                        local_temp.write(normalized_local)
                        local_temp_path = local_temp.name
                
                # Read normalized content for comparison
                with open(golden_temp_path, 'r', encoding='utf-8', errors='ignore') as f:
                    golden_lines = f.readlines()
                with open(local_temp_path, 'r', encoding='utf-8', errors='ignore') as f:
                    local_lines = f.readlines()
                
                # Generate unified diff
                diff = list(difflib.unified_diff(
                    golden_lines,
                    local_lines,
                    fromfile='golden_rule',
                    tofile='local_rule',
                    lineterm=''
                ))
                
                # Clean up temporary files
                os.unlink(golden_temp_path)
                os.unlink(local_temp_path)
                
                # Check if there are differences
                if diff:
                    # Write diff to report file
                    diff_file_path = self.rpt_path.parent / f"{self.item_id}_diff.txt"
                    with open(diff_file_path, 'w', encoding='utf-8') as diff_file:
                        diff_file.write('\n'.join(diff))
                    
                    missing_items[item['name']] = {
                        'line_number': line_number,
                        'file_path': file_path,
                        'reason': f'Rule deck content differs from golden baseline - modifications detected'
                    }
                else:
                    # No differences - rule deck matches golden
                    found_items[item['name']] = {
                        'line_number': line_number,
                        'file_path': file_path
                    }
            
            except Exception as e:
                missing_items[item['name']] = {
                    'line_number': line_number,
                    'file_path': file_path,
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
        # FIXED: Use waivers.get() instead of get_waive_items()
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
        
        # Step 5: Construct diff file path for missing_reason
        res_temp_path = self.rpt_path.parent / f"{self.item_id}_diff.txt"
        missing_reason_with_path = f"{self.MISSING_REASON_TYPE2_3} - see diff file: {res_temp_path}"
        
        # Step 6: Build output
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
            missing_reason=missing_reason_with_path,
            waived_base_reason=self.WAIVED_BASE_REASON,
            unused_waiver_reason=self.UNUSED_WAIVER_REASON
        )
    
    # =========================================================================
    # Helper Methods (Optional - Add as needed)
    # =========================================================================
    
    def _compare_rule_decks(self, local_path: str, golden_path: str) -> Dict[str, Any]:
        """
        Compare local rule deck against golden baseline.
        
        Creates temporary files with normalized content (remove // from //#),
        uses difflib.unified_diff() to detect differences, and saves diff report.
        
        Args:
            local_path: Path to local rule deck file
            golden_path: Path to golden rule deck file
            
        Returns:
            Dict with comparison results:
            - 'has_diff': bool - True if differences found
            - 'diff_file': str - Path to diff report file
        """
        try:
            # Read and normalize local rule deck
            local_content = self._normalize_rule_deck(local_path)
            
            # Read and normalize golden rule deck
            golden_content = self._normalize_rule_deck(golden_path)
            
            # Compare using difflib
            diff = list(difflib.unified_diff(
                golden_content,
                local_content,
                fromfile=f'golden: {golden_path}',
                tofile=f'local: {local_path}',
                lineterm=''
            ))
            
            # Save diff report
            diff_file_path = None
            if self.rpt_path and self.rpt_path.parent:
                diff_file_path = self.rpt_path.parent / 'rule_deck_diff.txt'
                with open(diff_file_path, 'w', encoding='utf-8') as f:
                    if diff:
                        f.write('\n'.join(diff))
                    else:
                        f.write('No differences found - rule deck matches golden baseline\n')
                self._diff_report_path = diff_file_path
            
            return {
                'has_diff': len(diff) > 0,
                'diff_file': str(diff_file_path) if diff_file_path else None
            }
            
        except Exception as e:
            # If comparison fails, assume difference exists
            return {
                'has_diff': True,
                'diff_file': None,
                'error': str(e)
            }
    
    def _normalize_rule_deck(self, file_path: str) -> List[str]:
        """
        Normalize rule deck content by removing // from lines starting with //#.
        
        Args:
            file_path: Path to rule deck file
            
        Returns:
            List of normalized lines
        """
        normalized_lines = []
        
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                # Remove // from lines starting with //#
                if line.strip().startswith('//#'):
                    line = line.replace('//', '', 1)
                normalized_lines.append(line.rstrip('\n'))
        
        return normalized_lines


# =========================================================================
# Entry Point
# =========================================================================

def main():
    """Main entry point."""
    checker = Check_2_0_0_03()
    checker.init_checker(Path(__file__))
    result = checker.execute_check()
    checker.write_output(result)
    return 0 if result.is_pass else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())