################################################################################
# Script Name: IMP-12-0-0-05.py
#
# Purpose:
#   Confirm open the IP_TIGHTEN_DENSITY switch in DRC rule deck.
#
# Logic:
#   - Parse input files: do_pvs_DRC_pvl.log, do_cmd_3star_DRC_sourceme
#   - Validate input files using validate_input_files() which returns (valid_files, missing_files) tuple
#   - Read DRC configuration file line-by-line with line number tracking
#   - Search for IP_TIGHTEN_DENSITY #DEFINE directive using regex patterns
#   - Determine switch state: ENABLED (uncommented #DEFINE), DISABLED (commented //), or MISSING (not found)
#   - Extract inline comments and context for reporting
#   - PASS if IP_TIGHTEN_DENSITY is ENABLED (uncommented #DEFINE found)
#   - FAIL if IP_TIGHTEN_DENSITY is DISABLED (commented out) or MISSING (not found in file)
#   - Handle edge cases: multiple occurrences (last wins), extra whitespace, empty files
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
class Check_12_0_0_05(InputFileParserMixin, OutputBuilderMixin, WaiverHandlerMixin, BaseChecker):
    """
    IMP-12-0-0-05: Confirm open the IP_TIGHTEN_DENSITY switch in DRC rule deck.
    
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
    FOUND_DESC_TYPE1_4 = "IP_TIGHTEN_DENSITY switch is enabled in DRC rule deck"
    MISSING_DESC_TYPE1_4 = "IP_TIGHTEN_DENSITY switch is disabled or missing in DRC rule deck"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_DESC_TYPE2_3 = "IP_TIGHTEN_DENSITY switch is enabled in DRC rule deck"
    MISSING_DESC_TYPE2_3 = "IP_TIGHTEN_DENSITY switch is disabled or missing in DRC rule deck"
    
    # All Types (waiver description unified)
    WAIVED_DESC = "IP_TIGHTEN_DENSITY switch violations waived per configuration"
    
    # ⭐ REASON CONSTANTS - Split by Type semantics (API-025)
    # ALL Types pass found_reason/missing_reason, but use different constants
    
    # Type 1/4: Boolean checks - emphasize "found/not found" (existence)
    FOUND_REASON_TYPE1_4 = "IP_TIGHTEN_DENSITY switch found enabled (uncommented #DEFINE)"
    MISSING_REASON_TYPE1_4 = "IP_TIGHTEN_DENSITY switch not found or commented out - must be enabled for proper density checking"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_REASON_TYPE2_3 = "IP_TIGHTEN_DENSITY switch matched and validated as enabled"
    MISSING_REASON_TYPE2_3 = "IP_TIGHTEN_DENSITY switch pattern not satisfied or disabled - must be uncommented"
    
    # Waiver-related (Type 3/4 only)
    WAIVED_BASE_REASON = "IP_TIGHTEN_DENSITY switch violation waived per project requirements"
    UNUSED_WAIVER_REASON = "Waiver defined but no violation matched"
    
    def __init__(self):
        """Initialize the checker."""
        super().__init__(
            check_module="12.0_PHYSICAL_VERIFICATION_CHECK",
            item_id="IMP-12-0-0-05",
            item_desc="Confirm open the IP_TIGHTEN_DENSITY switch in DRC rule deck."
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
        Parse input files to extract IP_TIGHTEN_DENSITY switch status.
        
        Parses DRC configuration files (Calibre or Pegasus) to locate and validate
        the IP_TIGHTEN_DENSITY switch. Supports both:
        - Calibre: do_cmd_3star_DRC_sourceme (#DEFINE directives)
        - Pegasus: do_pvs_DRC_pvl.log (similar syntax)
        
        Returns:
            Dict with parsed data:
            - 'items': List[Dict] - Switch status items with metadata
            - 'metadata': Dict - File metadata
            - 'errors': List - Any parsing errors encountered
        """
        # 1. Validate input files (raises ConfigurationError if missing)
        # CRITICAL: validate_input_files() returns TUPLE: (valid_files, missing_files)
        valid_files, missing_files = self.validate_input_files()
        
        # FIXED: [KNOWN_ISSUE_LOGIC-001] Explicitly check for empty list
        if not valid_files or len(valid_files) == 0:
            raise ConfigurationError(
                self.create_missing_files_error(missing_files)
            )
        
        # 2. Define patterns for IP_TIGHTEN_DENSITY switch detection
        # Pattern 1: Enabled switch (uncommented #DEFINE)
        pattern_enabled = re.compile(r'^\s*#DEFINE\s+IP_TIGHTEN_DENSITY\s*(?://.*)?$', re.IGNORECASE)
        
        # Pattern 2: Disabled switch (commented out)
        pattern_disabled = re.compile(r'^\s*(?://|#)\s*#?DEFINE\s+IP_TIGHTEN_DENSITY\s*(?://.*)?$', re.IGNORECASE)
        
        # Pattern 3: Extract inline comment
        pattern_comment = re.compile(r'//\s*(.+)$')
        
        # 3. Parse files to find switch status
        items = []
        metadata = {}
        errors = []
        
        for file_path in valid_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line_num, line in enumerate(f, 1):
                        # Check for enabled switch (uncommented #DEFINE)
                        if pattern_enabled.match(line):
                            # Extract inline comment if present
                            comment_match = pattern_comment.search(line)
                            comment = comment_match.group(1).strip() if comment_match else ''
                            
                            items.append({
                                'name': 'IP_TIGHTEN_DENSITY',
                                'state': 'ENABLED',
                                'line_number': line_num,
                                'file_path': str(file_path),
                                'line_content': line.strip(),
                                'comment': comment
                            })
                        
                        # Check for disabled switch (commented out)
                        elif pattern_disabled.match(line) and 'IP_TIGHTEN_DENSITY' in line.upper():
                            # Extract inline comment if present
                            comment_match = pattern_comment.search(line)
                            comment = comment_match.group(1).strip() if comment_match else ''
                            
                            items.append({
                                'name': 'IP_TIGHTEN_DENSITY',
                                'state': 'DISABLED',
                                'line_number': line_num,
                                'file_path': str(file_path),
                                'line_content': line.strip(),
                                'comment': comment
                            })
            
            except Exception as e:
                errors.append(f"Error parsing {file_path}: {str(e)}")
        
        # 4. Determine final switch state (last occurrence wins if multiple found)
        final_state = 'MISSING'
        final_item = None
        
        if items:
            # Last occurrence determines final state
            final_item = items[-1]
            final_state = final_item['state']
        
        # 5. Store frequently reused data on self
        self._parsed_items = items
        self._metadata = {
            'final_state': final_state,
            'total_occurrences': len(items)
        }
        
        # 6. Return aggregated dict
        return {
            'items': items,
            'metadata': metadata,
            'errors': errors,
            'final_state': final_state,
            'final_item': final_item
        }
    
    # =========================================================================
    # Type 1: Boolean Check
    # =========================================================================
    
    def _execute_type1(self) -> CheckResult:
        """
        Type 1: Boolean Check.
        
        Check if IP_TIGHTEN_DENSITY switch is enabled (uncommented #DEFINE found).
        Does NOT use pattern_items for searching.
        
        Returns:
            CheckResult with is_pass based on switch state
        """
        # Parse input
        data = self._parse_input_files()
        final_state = data.get('final_state', 'MISSING')
        final_item = data.get('final_item')
        
        # Determine PASS/FAIL based on switch state
        if final_state == 'ENABLED' and final_item:
            # Switch is enabled - PASS
            found_items = {
                'IP_TIGHTEN_DENSITY': {
                    'name': 'IP_TIGHTEN_DENSITY',
                    'line_number': final_item.get('line_number', 0),
                    'file_path': final_item.get('file_path', 'N/A')
                }
            }
            missing_items = []
        else:
            # Switch is disabled or missing - FAIL
            found_items = {}
            if final_item:
                # Switch found but disabled
                missing_items = [{
                    'name': 'IP_TIGHTEN_DENSITY',
                    'line_number': final_item.get('line_number', 0),
                    'file_path': final_item.get('file_path', 'N/A'),
                    'state': 'DISABLED'
                }]
            else:
                # Switch not found at all
                missing_items = ['IP_TIGHTEN_DENSITY']
        
        # Use template helper (auto-handles waiver=0)
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
        
        Returns:
            CheckResult with is_pass based on value comparison
        """
        # Parse input
        data = self._parse_input_files()
        final_state = data.get('final_state', 'MISSING')
        final_item = data.get('final_item')
        
        # Get requirements
        pattern_items = self.item_data.get('requirements', {}).get('pattern_items', [])
        
        # Check if IP_TIGHTEN_DENSITY is in pattern_items (existence_check mode)
        found_items = {}
        missing_items = []
        
        for pattern in pattern_items:
            if pattern.upper() == 'IP_TIGHTEN_DENSITY':
                if final_state == 'ENABLED' and final_item:
                    # Pattern found and enabled
                    found_items[pattern] = {
                        'name': pattern,
                        'line_number': final_item.get('line_number', 0),
                        'file_path': final_item.get('file_path', 'N/A')
                    }
                else:
                    # Pattern not found or disabled
                    missing_items.append(pattern)
        
        # Use template helper (auto-handles waiver=0)
        # Type 2: Use TYPE2_3 desc+reason (emphasize "matched/satisfied")
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
        
        Returns:
            CheckResult with FAIL for unwaived, INFO for waived items
        """
        # Parse input
        parsed_data = self._parse_input_files()
        final_state = parsed_data.get('final_state', 'MISSING')
        final_item = parsed_data.get('final_item')
        
        # FIXED: [KNOWN_ISSUE_API-016] Use waivers.get() directly to preserve dict format
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # Get pattern_items
        pattern_items = self.item_data.get('requirements', {}).get('pattern_items', [])
        
        # Check patterns and classify into found/waived/unwaived
        found_items = {}
        waived_items = {}
        unwaived_items = []
        
        for pattern in pattern_items:
            if pattern.upper() == 'IP_TIGHTEN_DENSITY':
                if final_state == 'ENABLED' and final_item:
                    # Pattern found and enabled - add to found_items
                    found_items[pattern] = {
                        'name': pattern,
                        'line_number': final_item.get('line_number', 0),
                        'file_path': final_item.get('file_path', 'N/A')
                    }
                else:
                    # Pattern not found or disabled - check waiver
                    if self.match_waiver_entry(pattern, waive_dict):
                        waived_items[pattern] = {
                            'name': pattern,
                            'line_number': final_item.get('line_number', 0) if final_item else 0,
                            'file_path': final_item.get('file_path', 'N/A') if final_item else 'N/A'
                        }
                    else:
                        unwaived_items.append(pattern)
        
        # Find unused waivers
        used_names = set(waived_items.keys())
        unused_waivers = [name for name in waive_dict.keys() if name not in used_names]
        
        # Use template helper for automatic output formatting (waivers.value>0)
        # Type 3: Use TYPE2_3 desc+reason (emphasize "matched/satisfied")
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
        
        Returns:
            CheckResult with waiver logic applied
        """
        # Parse input
        data = self._parse_input_files()
        final_state = data.get('final_state', 'MISSING')
        final_item = data.get('final_item')
        
        # FIXED: [KNOWN_ISSUE_API-016] Use waivers.get() directly to preserve dict format
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # Determine PASS/FAIL with waiver logic
        found_items = {}
        waived_items = {}
        missing_items = []
        
        if final_state == 'ENABLED' and final_item:
            # Switch is enabled - PASS
            found_items = {
                'IP_TIGHTEN_DENSITY': {
                    'name': 'IP_TIGHTEN_DENSITY',
                    'line_number': final_item.get('line_number', 0),
                    'file_path': final_item.get('file_path', 'N/A')
                }
            }
        else:
            # Switch is disabled or missing - check waiver
            switch_name = 'IP_TIGHTEN_DENSITY'
            if self.match_waiver_entry(switch_name, waive_dict):
                waived_items[switch_name] = {
                    'name': switch_name,
                    'line_number': final_item.get('line_number', 0) if final_item else 0,
                    'file_path': final_item.get('file_path', 'N/A') if final_item else 'N/A'
                }
            else:
                missing_items.append(switch_name)
        
        # Find unused waivers
        used_names = set(waived_items.keys()) | set(found_items.keys())
        unused_waivers = [name for name in waive_dict.keys() if name not in used_names]
        
        # Use template helper for automatic output formatting (waivers.value>0)
        # Type 4: Use TYPE1_4 reason (emphasize "found/not found")
        return self.build_complete_output(
            found_items=found_items,
            waived_items=waived_items,
            missing_items=missing_items,
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
    checker = Check_12_0_0_05()
    checker.init_checker(Path(__file__))
    result = checker.execute_check()
    checker.write_output(result)
    return 0 if result.is_pass else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())