################################################################################
# Script Name: IMP-7-0-0-00.py
#
# Purpose:
#   Block name (e.g: cdn_hs_phy_data_slice)
#
# Logic:
#   - Parse input files: IMP-7-0-0-00.rpt
#   - Extract block name from report header using pattern matching
#   - Validate block name format (alphanumeric + underscores)
#   - Verify block name exists and is properly formatted
#   - Report PASS if block name found, FAIL if missing or malformed
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
# Refactored: 2025-12-18 (Using checker_templates v1.1.0)
#
# Author: yyin
# Date: 2025-12-18
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
class Check_7_0_0_00(InputFileParserMixin, OutputBuilderMixin, WaiverHandlerMixin, BaseChecker):
    """
    IMP-7-0-0-00: Block name (e.g: cdn_hs_phy_data_slice)
    
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
    # DESCRIPTION & REASON CONSTANTS - Split by Type semantics (API-026)
    # =========================================================================
    # Type 1/4: Boolean checks - emphasize "found/not found" (existence)
    FOUND_DESC_TYPE1_4 = "Block name found in implementation report"
    MISSING_DESC_TYPE1_4 = "Block name not found in implementation report"
    FOUND_REASON_TYPE1_4 = "Block name successfully extracted from report header"
    MISSING_REASON_TYPE1_4 = "Block name header missing or malformed in report file"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_DESC_TYPE2_3 = "Block name pattern matched in report header"
    MISSING_DESC_TYPE2_3 = "Block name pattern not satisfied in report header"
    FOUND_REASON_TYPE2_3 = "Block name pattern matched and validated in report"
    MISSING_REASON_TYPE2_3 = "Block name pattern not satisfied or missing from report"
    
    # All Types (waiver description unified)
    WAIVED_DESC = "Block name validation waived"
    
    # Waiver parameters (Type 3/4 ONLY)
    WAIVED_BASE_REASON = "Block name validation waived per design approval"
    
    def __init__(self):
        """Initialize the checker."""
        super().__init__(
            check_module="7.0_INNOVUS_DESIGN_IN_CHECK",
            item_id="IMP-7-0-0-00",
            item_desc="Block name (e.g: cdn_hs_phy_data_slice)"
        )
        # Custom member variables for parsed data
        self._parsed_items: List[Dict[str, Any]] = []
        self._block_names: List[Dict[str, Any]] = []
    
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
        Parse input files to extract block names from report headers.
        
        Returns:
            Dict with parsed data:
            - 'items': List[Dict] - Block names found with metadata
            - 'metadata': Dict - File metadata
            - 'errors': List - Any parsing errors encountered
        """
        # 1. Validate inputs - IMPORTANT: returns tuple (valid_files_list, missing_files_list)
        valid_files, missing_files = self.validate_input_files()
        if missing_files:
            raise ConfigurationError(
                self.create_missing_files_error(missing_files)
            )
        
        # 2. Parse using patterns from file analysis
        all_items = []
        errors = []
        
        # Pattern for block name extraction
        # Example: "Block name: CDN_104H_cdn_hs_phy_data_slice_EW  # Limit to 10KB"
        block_name_pattern = re.compile(r'^Block\s+name:\s*([A-Za-z0-9_]+)\s*(?:#.*)?$', re.IGNORECASE)
        
        for file_path in valid_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line_num, line in enumerate(f, 1):
                        # Extract block name from header
                        match = block_name_pattern.search(line)
                        if match:
                            block_name = match.group(1)
                            all_items.append({
                                'name': block_name,
                                'line_number': line_num,
                                'file_path': str(file_path),
                                'line_content': line.strip()
                            })
                            # Typically only one block name per file, but continue parsing
            except Exception as e:
                errors.append(f"Error parsing {file_path}: {str(e)}")
        
        # 3. Store on self for reuse
        self._parsed_items = all_items
        self._block_names = all_items
        
        # 4. Return aggregated dict with items containing line_number and file_path
        return {
            'items': all_items,
            'metadata': {'total': len(all_items)},
            'errors': errors
        }
    
    # =========================================================================
    # Type 1: Boolean Check
    # =========================================================================
    
    def _execute_type1(self) -> CheckResult:
        """
        Type 1: Boolean Check.
        
        Custom boolean validation (block name exists in report).
        Does NOT use pattern_items for searching.
        
        Use OutputBuilderMixin.build_complete_output() for automatic formatting.
        
        Returns:
            CheckResult with is_pass based on check logic
        """
        # Parse input
        data = self._parse_input_files()
        items = data.get('items', [])
        errors = data.get('errors', [])
        
        # Check if any parsing errors occurred
        if errors:
            return create_check_result(
                is_pass=False,
                item_id=self.item_id,
                item_desc=self.item_desc,
                details=[DetailItem(
                    severity=Severity.FAIL,
                    message="Parsing errors encountered",
                    reason="; ".join(errors)
                )]
            )
        
        # Convert list to dict with metadata for source file/line display
        # Output format: "Info: <name>. In line <N>, <filepath>: <reason>"
        found_items = {
            item['name']: {
                'name': item['name'],
                'line_number': item.get('line_number', 0),
                'file_path': item.get('file_path', 'N/A')
            }
            for item in items
        } if items else {}
        
        # Use template helper
        # Type 1: Use TYPE1_4 reason (emphasize "found/not found") - API-025
        return self.build_complete_output(
            found_items=found_items,
            missing_items=[] if found_items else ['Block name header'],
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
        
        # Check if any parsing errors occurred
        if errors:
            return create_check_result(
                is_pass=False,
                item_id=self.item_id,
                item_desc=self.item_desc,
                details=[DetailItem(
                    severity=Severity.FAIL,
                    message="Parsing errors encountered",
                    reason="; ".join(errors)
                )]
            )
        
        # Get requirements
        pattern_items = self.item_data.get('requirements', {}).get('pattern_items', [])
        
        # Extract block names from parsed items
        found_block_names = {item['name'] for item in items}
        
        # Find which patterns were matched
        found_items = {}
        missing_items = []
        
        for pattern in pattern_items:
            matched = False
            for item in items:
                # Check if pattern matches block name (support wildcards)
                if self._matches_pattern(item['name'], pattern):
                    found_items[item['name']] = {
                        'name': item['name'],
                        'line_number': item.get('line_number', 0),
                        'file_path': item.get('file_path', 'N/A')
                    }
                    matched = True
                    break
            
            if not matched:
                missing_items.append(pattern)
        
        # Use template helper (auto-handles waiver=0)
        # Type 2: Use TYPE2_3 reason (emphasize "matched/satisfied") - API-026
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
        
        # Check if any parsing errors occurred
        if errors:
            return create_check_result(
                is_pass=False,
                item_id=self.item_id,
                item_desc=self.item_desc,
                details=[DetailItem(
                    severity=Severity.FAIL,
                    message="Parsing errors encountered",
                    reason="; ".join(errors)
                )]
            )
        
        # FIX API-016: Use waivers.get() directly to preserve dict format
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # Get requirements
        pattern_items = self.item_data.get('requirements', {}).get('pattern_items', [])
        
        # Find violations (missing patterns)
        violations = []
        found_items = {}
        
        for pattern in pattern_items:
            matched = False
            for item in items:
                if self._matches_pattern(item['name'], pattern):
                    found_items[item['name']] = {
                        'name': item['name'],
                        'line_number': item.get('line_number', 0),
                        'file_path': item.get('file_path', 'N/A')
                    }
                    matched = True
                    break
            
            if not matched:
                violations.append(pattern)
        
        # Separate waived/unwaived using template helper
        waived_items = []
        unwaived_items = []
        
        for violation in violations:
            if self.match_waiver_entry(violation, waive_dict):
                waived_items.append(violation)
            else:
                unwaived_items.append(violation)
        
        # FIX API-017: waive_dict.keys() are item names (strings)
        used_names = set(waived_items)
        unused_waivers = [name for name in waive_dict.keys() if name not in used_names]
        
        # FIX API-021: Use missing_items parameter instead of unwaived_items
        # Use template helper for automatic output formatting
        # Type 3: Use TYPE2_3 reason (emphasize "matched/satisfied") - API-026
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
            waived_base_reason=self.WAIVED_BASE_REASON
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
        
        # Check if any parsing errors occurred
        if errors:
            return create_check_result(
                is_pass=False,
                item_id=self.item_id,
                item_desc=self.item_desc,
                details=[DetailItem(
                    severity=Severity.FAIL,
                    message="Parsing errors encountered",
                    reason="; ".join(errors)
                )]
            )
        
        # FIX API-016: Use waivers.get() directly to preserve dict format
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # Convert list to dict with metadata
        found_items = {
            item['name']: {
                'name': item['name'],
                'line_number': item.get('line_number', 0),
                'file_path': item.get('file_path', 'N/A')
            }
            for item in items
        } if items else {}
        
        # Check if block name is missing (violation)
        missing_items = [] if found_items else ['Block name header']
        
        # Separate waived/unwaived violations
        waived_items = []
        unwaived_items = []
        
        for missing_item in missing_items:
            if self.match_waiver_entry(missing_item, waive_dict):
                waived_items.append(missing_item)
            else:
                unwaived_items.append(missing_item)
        
        # FIX API-017: waive_dict.keys() are item names (strings)
        used_names = set(waived_items)
        unused_waivers = [name for name in waive_dict.keys() if name not in used_names]
        
        # FIX API-021: Use missing_items parameter instead of unwaived_items
        # Use template helper (auto-handles waiver=0)
        # Type 4: Use TYPE1_4 reason (emphasize "found/not found") - API-026
        return self.build_complete_output(
            found_items=found_items,
            waived_items=waived_items,
            missing_items=unwaived_items,
            waive_dict=waive_dict,
            unused_waivers=unused_waivers,
            has_waiver_value=True,
            found_desc=self.FOUND_DESC_TYPE1_4,
            missing_desc=self.MISSING_DESC_TYPE1_4,
            waived_desc=self.WAIVED_DESC,
            found_reason=self.FOUND_REASON_TYPE1_4,
            missing_reason=self.MISSING_REASON_TYPE1_4,
            waived_base_reason=self.WAIVED_BASE_REASON
        )
    
    # =========================================================================
    # Helper Methods (Optional - Add as needed)
    # =========================================================================
    
    def _matches_pattern(self, item: str, pattern: str) -> bool:
        """
        Check if item matches pattern (supports wildcards).
        
        Args:
            item: Item to check
            pattern: Pattern to match (supports * wildcards)
            
        Returns:
            True if item matches pattern
        """
        # Support wildcards
        if '*' in pattern:
            regex_pattern = pattern.replace('*', '.*')
            return bool(re.search(f'^{regex_pattern}$', item, re.IGNORECASE))
        # Exact match
        return pattern.lower() == item.lower()


# =========================================================================
# Entry Point
# =========================================================================

def main():
    """Main entry point."""
    checker = Check_7_0_0_00()
    checker.init_checker(Path(__file__))
    result = checker.execute_check()
    checker.write_output(result)
    return 0 if result.is_pass else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())