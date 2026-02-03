################################################################################
# Script Name: IMP-12-0-0-04.py
#
# Purpose:
#   Confirm the "#define CHECK_FLOATING_GATE_BY_PRIMARY_TEXT" DRC option in DRC rule deck is open to check PO.R.19 (input floating issue) in IP level.
#
# Logic:
#   - Parse input files: do_pvs_DRC_pvl.log, do_cmd_3star_DRC_sourceme
#   - Extract #DEFINE CHECK_FLOATING_GATE_BY_PRIMARY_TEXT directive status from both files
#   - Check if directive is enabled (uncommented) in Pegasus PVL log
#   - Check if directive is enabled (uncommented) in Calibre DRC configuration
#   - Validate that the option is active to enable PO.R.19 floating gate checking
#   - Report line numbers and file paths for all findings
#   - Aggregate results from both files to confirm configuration
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
# Refactored: 2026-01-07 (Using checker_templates v1.1.0)
#
# Author: Jingyu Wang
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
class Check_12_0_0_04(InputFileParserMixin, OutputBuilderMixin, WaiverHandlerMixin, BaseChecker):
    """
    IMP-12-0-0-04: Confirm the "#define CHECK_FLOATING_GATE_BY_PRIMARY_TEXT" DRC option in DRC rule deck is open to check PO.R.19 (input floating issue) in IP level.
    
    Checking Types:
    - Type 1: requirements=N/A, pattern_items [], waivers=N/A/0 → Boolean Check
    - Type 2: requirements>0, pattern_items [...], waivers=N/A/0 → Value Check
    - Type 3: requirements>0, pattern_items [...], waivers=N/A/0 → Value Check with Waiver Logic
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
    FOUND_DESC_TYPE1_4 = "CHECK_FLOATING_GATE_BY_PRIMARY_TEXT option is enabled in DRC rule deck"
    MISSING_DESC_TYPE1_4 = "CHECK_FLOATING_GATE_BY_PRIMARY_TEXT option is NOT enabled in DRC rule deck"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_DESC_TYPE2_3 = "CHECK_FLOATING_GATE_BY_PRIMARY_TEXT option is enabled in DRC rule deck"
    MISSING_DESC_TYPE2_3 = "CHECK_FLOATING_GATE_BY_PRIMARY_TEXT option is NOT enabled in DRC rule deck"
    
    # All Types (waiver description unified)
    WAIVED_DESC = "Waived DRC configuration issues"
    
    # ⭐ REASON CONSTANTS - Split by Type semantics (API-025)
    # ALL Types pass found_reason/missing_reason, but use different constants
    
    # Type 1/4: Boolean checks - emphasize "found/not found" (existence)
    FOUND_REASON_TYPE1_4 = "#DEFINE CHECK_FLOATING_GATE_BY_PRIMARY_TEXT directive found and enabled"
    MISSING_REASON_TYPE1_4 = "#DEFINE CHECK_FLOATING_GATE_BY_PRIMARY_TEXT directive not found or disabled (commented out)"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_REASON_TYPE2_3 = "#DEFINE CHECK_FLOATING_GATE_BY_PRIMARY_TEXT directive matched and enabled"
    MISSING_REASON_TYPE2_3 = "#DEFINE CHECK_FLOATING_GATE_BY_PRIMARY_TEXT directive not satisfied or missing"
    
    # Waiver-related (Type 3/4 only)
    WAIVED_BASE_REASON = "DRC configuration issue waived per project requirements"
    UNUSED_WAIVER_REASON = "Waiver defined but no violation matched"
    
    def __init__(self):
        """Initialize the checker."""
        super().__init__(
            check_module="12.0_PHYSICAL_VERIFICATION_CHECK",
            item_id="IMP-12-0-0-04",
            item_desc="Confirm the "#define CHECK_FLOATING_GATE_BY_PRIMARY_TEXT" DRC option in DRC rule deck is open to check PO.R.19 (input floating issue) in IP level."
        )
        # Custom member variables for parsed data
        self._parsed_items: List[Dict[str, Any]] = []
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
        Parse input files to extract #DEFINE CHECK_FLOATING_GATE_BY_PRIMARY_TEXT status.
        
        Parses two files:
        1. do_pvs_DRC_pvl.log - Pegasus PVL rule deck parsing log
        2. do_cmd_3star_DRC_sourceme - Calibre DRC configuration file
        
        Returns:
            Dict with parsed data:
            - 'items': List[Dict] - Enabled directives found (with line_number, file_path)
            - 'metadata': Dict - File metadata (rule_file_path, etc.)
            - 'errors': List - Any parsing errors encountered
        """
        # 1. Validate input files - IMPORTANT: returns tuple (valid_files_list, missing_files_list)
        valid_files, missing_files = self.validate_input_files()
        if missing_files:
            raise ConfigurationError(
                self.create_missing_files_error(missing_files)
            )
        
        # 2. Parse using patterns from file analysis
        all_items = []
        metadata = {}
        errors = []
        
        # Define patterns for both file types
        # Pattern 1: Active #DEFINE CHECK_FLOATING_GATE_BY_PRIMARY_TEXT (Pegasus PVL format)
        pattern_pvl_enabled = re.compile(r'^#DEFINE\s+CHECK_FLOATING_GATE_BY_PRIMARY_TEXT\s*$')
        
        # Pattern 2: Active #DEFINE CHECK_FLOATING_GATE_BY_PRIMARY_TEXT (Calibre format with optional comment)
        pattern_calibre_enabled = re.compile(r'^\s*#DEFINE\s+CHECK_FLOATING_GATE_BY_PRIMARY_TEXT\s*(?://.*)?$')
        
        # Pattern 3: Commented/disabled directive (both formats)
        pattern_disabled = re.compile(r'^\s*(##|//)\s*#?DEFINE\s+CHECK_FLOATING_GATE_BY_PRIMARY_TEXT')
        
        # Pattern 4: Extract rule file path from Pegasus log
        pattern_rule_file = re.compile(r'^Parsing Rule File\s+(.+?)\s+\.\.\.')
        
        for file_path in valid_files:
            file_name = Path(file_path).name
            
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line_num, line in enumerate(f, 1):
                        # Extract rule file path metadata (Pegasus log only)
                        if match := pattern_rule_file.search(line):
                            metadata['rule_file_path'] = match.group(1)
                        
                        # Check for enabled directive (Pegasus PVL format)
                        if pattern_pvl_enabled.search(line):
                            all_items.append({
                                'name': 'CHECK_FLOATING_GATE_BY_PRIMARY_TEXT',
                                'status': 'ENABLED',
                                'file_type': 'Pegasus PVL',
                                'line_number': line_num,
                                'file_path': str(file_path),
                                'line_content': line.strip()
                            })
                        
                        # Check for enabled directive (Calibre format)
                        elif pattern_calibre_enabled.search(line):
                            all_items.append({
                                'name': 'CHECK_FLOATING_GATE_BY_PRIMARY_TEXT',
                                'status': 'ENABLED',
                                'file_type': 'Calibre DRC',
                                'line_number': line_num,
                                'file_path': str(file_path),
                                'line_content': line.strip()
                            })
                        
                        # Check for disabled/commented directive
                        elif pattern_disabled.search(line):
                            errors.append({
                                'name': 'CHECK_FLOATING_GATE_BY_PRIMARY_TEXT',
                                'status': 'DISABLED',
                                'file_type': file_name,
                                'line_number': line_num,
                                'file_path': str(file_path),
                                'line_content': line.strip(),
                                'error': 'Directive is commented out or disabled'
                            })
            
            except Exception as e:
                errors.append({
                    'file_path': str(file_path),
                    'error': f'Failed to parse file: {str(e)}'
                })
        
        # 3. Store frequently reused data on self
        self._parsed_items = all_items
        self._metadata = metadata
        
        # 4. Return aggregated dict with items containing line_number and file_path
        return {
            'items': all_items,
            'metadata': metadata,
            'errors': errors
        }
    
    # =========================================================================
    # Type 1: Boolean Check
    # =========================================================================
    
    def _execute_type1(self) -> CheckResult:
        """
        Type 1: Boolean Check.
        
        Check if CHECK_FLOATING_GATE_BY_PRIMARY_TEXT directive is enabled in DRC rule deck.
        Does NOT use pattern_items for searching.
        
        Use OutputBuilderMixin.build_complete_output() for automatic formatting.
        
        Returns:
            CheckResult with is_pass based on check logic
        """
        # Parse input
        data = self._parse_input_files()
        items = data.get('items', [])
        errors = data.get('errors', [])
        
        # Convert list to dict with metadata for source file/line display
        # Output format: "Info: <name>. In line <N>, <filepath>: <reason>"
        found_items = {}
        for item in items:
            key = f"{item['file_type']}: {item['name']}"
            found_items[key] = {
                'name': key,
                'line_number': item.get('line_number', 0),
                'file_path': item.get('file_path', 'N/A')
            }
        
        # Determine if check passes (at least one enabled directive found)
        missing_items = []
        if not found_items:
            # Check if directive was found but disabled
            if errors:
                for error in errors:
                    if error.get('status') == 'DISABLED':
                        missing_items.append(
                            f"{error.get('file_type', 'Unknown')}: {error.get('name', 'CHECK_FLOATING_GATE_BY_PRIMARY_TEXT')} "
                            f"(commented out at line {error.get('line_number', 'N/A')})"
                        )
            
            # If no disabled directives found, directive is completely missing
            if not missing_items:
                missing_items.append('CHECK_FLOATING_GATE_BY_PRIMARY_TEXT directive not found in any DRC configuration file')
        
        # Use template helper
        # Type 1: Use TYPE1_4 reason (emphasize "found/not found")
        return self.build_complete_output(
            found_items=found_items,
            missing_items=missing_items,
            found_desc=self.FOUND_DESC_TYPE1_4,
            missing_desc=self.MISSING_DESC_TYPE1_4,
            found_reason=self.FOUND_REASON_TYPE1_4,
            missing_reason=self.MISSING_REASON_TYPE1_4
        )
    
    # =========================================================================
    # Type 2: Value Check
    # =========================================================================
    
    def _execute_type2(self) -> CheckResult:
        """
        Type 2: Value Check.
        
        Search pattern_items in input files.
        found_items = patterns found; missing_items = patterns not found.
        PASS/FAIL depends on check purpose (violation check vs requirement check).
        
        Template auto-handles waiver=0 conversions.
        
        Returns:
            CheckResult with is_pass based on value comparison
        """
        # Parse input
        data = self._parse_input_files()
        items = data.get('items', [])
        errors = data.get('errors', [])
        
        # Get requirements
        pattern_items = self.item_data.get('requirements', {}).get('pattern_items', [])
        
        # Convert parsed items to dict for matching
        found_items = {}
        for item in items:
            key = f"{item['file_type']}: {item['name']}"
            found_items[key] = {
                'name': key,
                'line_number': item.get('line_number', 0),
                'file_path': item.get('file_path', 'N/A')
            }
        
        # Find missing patterns
        missing_items = []
        for pattern in pattern_items:
            # Check if pattern exists in found items
            pattern_found = False
            for found_key in found_items.keys():
                if pattern.lower() in found_key.lower():
                    pattern_found = True
                    break
            
            if not pattern_found:
                # Check if pattern was found but disabled
                disabled_found = False
                for error in errors:
                    if error.get('status') == 'DISABLED' and pattern.lower() in error.get('name', '').lower():
                        missing_items.append(
                            f"{pattern} (commented out at line {error.get('line_number', 'N/A')} in {error.get('file_type', 'Unknown')})"
                        )
                        disabled_found = True
                        break
                
                # If not disabled, pattern is completely missing
                if not disabled_found:
                    missing_items.append(f"{pattern} (not found in any DRC configuration file)")
        
        # Use template helper (auto-handles waiver=0)
        # Type 2: Use TYPE2_3 desc+reason (emphasize "matched/satisfied") - API-026
        return self.build_complete_output(
            found_items=found_items,
            missing_items=missing_items,
            found_desc=self.FOUND_DESC_TYPE2_3,
            missing_desc=self.MISSING_DESC_TYPE2_3,
            found_reason=self.FOUND_REASON_TYPE2_3,
            missing_reason=self.MISSING_REASON_TYPE2_3
        )
    
    # =========================================================================
    # Type 3: Value Check with Waiver Logic
    # =========================================================================
    
    def _execute_type3(self) -> CheckResult:
        """
        Type 3: Value check with waiver support.
        
        Same pattern search logic as Type 2, plus waiver classification.
        
        Uses WaiverHandlerMixin for waiver processing:
        - parse_waive_items(waive_items_raw): Parse waiver configuration
        - match_waiver_entry(item, waive_dict): Match item against waivers
        
        Uses OutputBuilderMixin for result construction:
        - build_complete_output(...): Assemble final CheckResult with auto-formatting
        
        Returns:
            CheckResult with FAIL for unwaived, INFO for waived items
        """
        # Parse input
        parsed_data = self._parse_input_files()
        items = parsed_data.get('items', [])
        errors = parsed_data.get('errors', [])
        
        # CORRECT! Use waivers.get() directly to preserve dict format
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # Get requirements
        pattern_items = self.item_data.get('requirements', {}).get('pattern_items', [])
        
        # Convert parsed items to dict for matching
        found_items = {}
        for item in items:
            key = f"{item['file_type']}: {item['name']}"
            found_items[key] = {
                'name': key,
                'line_number': item.get('line_number', 0),
                'file_path': item.get('file_path', 'N/A')
            }
        
        # Find missing patterns and classify as waived/unwaived
        waived_items = {}
        unwaived_items = []
        
        for pattern in pattern_items:
            # Check if pattern exists in found items
            pattern_found = False
            for found_key in found_items.keys():
                if pattern.lower() in found_key.lower():
                    pattern_found = True
                    break
            
            if not pattern_found:
                # Pattern is missing - check if it should be waived
                violation_name = pattern
                
                # Check if pattern was found but disabled
                for error in errors:
                    if error.get('status') == 'DISABLED' and pattern.lower() in error.get('name', '').lower():
                        violation_name = f"{pattern} (commented out at line {error.get('line_number', 'N/A')} in {error.get('file_type', 'Unknown')})"
                        break
                
                # Check waiver match
                if self.match_waiver_entry(pattern, waive_dict):
                    waived_items[pattern] = {
                        'name': violation_name,
                        'line_number': 0,
                        'file_path': 'N/A'
                    }
                else:
                    unwaived_items.append(violation_name)
        
        # Find unused waivers
        used_names = set(waived_items.keys())
        unused_waivers = [name for name in waive_dict.keys() if name not in used_names]
        
        # Use template helper for automatic output formatting (waivers.value>0)
        # Type 3: Use TYPE2_3 desc+reason (emphasize "matched/satisfied") - API-026
        return self.build_complete_output(
            found_items=found_items,
            waived_items=waived_items,
            missing_items=unwaived_items,
            waive_dict=waive_dict,
            unused_waivers=unused_waivers,
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
        Type 4: Boolean check with waiver support (Type 1 + waiver).
        
        Same boolean check as Type 1 (no pattern_items), plus waiver classification.
        
        Use OutputBuilderMixin.build_complete_output() with has_waiver_value=True.
        
        Returns:
            CheckResult with waiver logic applied
        """
        # Parse input
        data = self._parse_input_files()
        items = data.get('items', [])
        errors = data.get('errors', [])
        
        # CORRECT! Use waivers.get() directly to preserve dict format
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # Convert list to dict with metadata for source file/line display
        found_items = {}
        for item in items:
            key = f"{item['file_type']}: {item['name']}"
            found_items[key] = {
                'name': key,
                'line_number': item.get('line_number', 0),
                'file_path': item.get('file_path', 'N/A')
            }
        
        # Classify violations as waived/unwaived
        waived_items = {}
        unwaived_items = []
        
        if not found_items:
            # Directive not found - check if waived
            violation_name = 'CHECK_FLOATING_GATE_BY_PRIMARY_TEXT'
            
            # Check if directive was found but disabled
            for error in errors:
                if error.get('status') == 'DISABLED':
                    violation_name = f"{error.get('name', 'CHECK_FLOATING_GATE_BY_PRIMARY_TEXT')} (commented out at line {error.get('line_number', 'N/A')} in {error.get('file_type', 'Unknown')})"
                    break
            
            # Check waiver match
            if self.match_waiver_entry('CHECK_FLOATING_GATE_BY_PRIMARY_TEXT', waive_dict):
                waived_items['CHECK_FLOATING_GATE_BY_PRIMARY_TEXT'] = {
                    'name': violation_name,
                    'line_number': 0,
                    'file_path': 'N/A'
                }
            else:
                unwaived_items.append(violation_name)
        
        # Find unused waivers
        used_names = set(waived_items.keys())
        unused_waivers = [name for name in waive_dict.keys() if name not in used_names]
        
        # Use template helper for automatic output formatting (waivers.value>0)
        # Type 4: Use TYPE1_4 reason (emphasize "found/not found")
        return self.build_complete_output(
            found_items=found_items,
            waived_items=waived_items,
            missing_items=unwaived_items,
            waive_dict=waive_dict,
            unused_waivers=unused_waivers,
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
    checker = Check_12_0_0_04()
    checker.init_checker(Path(__file__))
    result = checker.execute_check()
    checker.write_output(result)
    return 0 if result.is_pass else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())