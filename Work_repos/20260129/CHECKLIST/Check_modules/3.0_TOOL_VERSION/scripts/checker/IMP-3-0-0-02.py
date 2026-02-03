################################################################################
# Script Name: IMP-3-0-0-02.py
#
# Purpose:
#   List Conformal LEC tool version (eg. confrml/241/24.10.100)
#
# Logic:
#   - Parse input files: setup_vars.tcl
#   - Read TCL setup file line by line to find module command definitions
#   - Search for FV (Formal Verification) or CLP (Conformal Low Power) MODULE_CMD variables
#   - Extract quoted module load command string from TCL variable assignments
#   - Parse module load portion to extract confrml/XXX/YYY.YYY version pattern
#   - Format version string as confrml/major_version/full_version
#   - Handle edge cases: commented lines, whitespace variations, multiple module loads
#   - Report INFO01 if confrml version found, ERROR01 if no FV/CLP MODULE_CMD found
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
# Refactored: 2025-12-23 (Using checker_templates v1.1.0)
#
# Author: yyin
# Date: 2025-12-23
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
from checker_templates.input_file_parser_template import InputFileParserMixin


# MANDATORY: Inherit mixins in correct order (InputFileParserMixin first if used)
class Check_3_0_0_02(InputFileParserMixin, OutputBuilderMixin, WaiverHandlerMixin, BaseChecker):
    """
    IMP-3-0-0-02: List Conformal LEC tool version (eg. confrml/241/24.10.100)
    
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
    FOUND_DESC_TYPE1_4 = "Conformal LEC tool version found in setup configuration"
    MISSING_DESC_TYPE1_4 = "Conformal LEC tool version not found in setup configuration"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_DESC_TYPE2_3 = "Required Conformal LEC tool version matched in setup configuration"
    MISSING_DESC_TYPE2_3 = "Expected Conformal LEC tool version pattern not satisfied in setup configuration"
    
    # All Types (waiver description unified)
    WAIVED_DESC = "Waived Conformal LEC tool version violations"
    
    # ⭐ REASON CONSTANTS - Split by Type semantics (API-025)
    # ALL Types pass found_reason/missing_reason, but use different constants
    
    # Type 1/4: Boolean checks - emphasize "found/not found" (existence)
    FOUND_REASON_TYPE1_4 = "Conformal LEC tool version found in MODULE_CMD definition"
    MISSING_REASON_TYPE1_4 = "FV or CLP MODULE_CMD definition not found in setup file"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_REASON_TYPE2_3 = "Conformal LEC tool version matched required pattern"
    MISSING_REASON_TYPE2_3 = "Conformal LEC tool version does not match expected pattern"
    
    # Waiver-related (Type 3/4 only)
    WAIVED_BASE_REASON = "Conformal LEC tool version violation waived per design approval"
    UNUSED_WAIVER_REASON = "Waiver defined but no violation matched"
    
    def __init__(self):
        """Initialize the checker."""
        super().__init__(
            check_module="3.0_TOOL_VERSION",
            item_id="IMP-3-0-0-02",
            item_desc="List Conformal LEC tool version (eg. confrml/241/24.10.100)"
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
        except Exception as e:
            # Handle unexpected errors
            return create_check_result(
                is_pass=False,
                item_id=self.item_id,
                item_desc=self.item_desc,
                details=[DetailItem(
                    severity=Severity.FAIL,
                    description=f"Unexpected error during check execution: {str(e)}",
                    reason="Internal checker error"
                )]
            )
    
    # =========================================================================
    # Input Parsing (Common for All Types)
    # =========================================================================
    
    def _parse_input_files(self) -> Dict[str, Any]:
        """
        Parse input files to extract Conformal LEC tool version information.
        
        Searches for FV (Formal Verification) or CLP (Conformal Low Power) MODULE_CMD
        definitions in TCL setup files and extracts confrml version strings.
        
        Returns:
            Dict with parsed data:
            - 'items': List[Dict] - Conformal tool versions found (with line_number, file_path)
            - 'metadata': Dict - Parsing metadata (total count, files processed)
            - 'errors': List - Any parsing errors encountered
        """
        # 1. Validate input files - IMPORTANT: returns tuple (valid_files_list, missing_files_list)
        valid_files, missing_files = self.validate_input_files()
        
        # Fix LOGIC-001: Explicitly check for empty list
        if missing_files:
            raise ConfigurationError(
                self.create_missing_files_error(missing_files)
            )
        
        if not valid_files or len(valid_files) == 0:
            raise ConfigurationError("No valid input files found")
        
        # 2. Parse using patterns from file analysis
        all_items = []
        errors = []
        
        # Regex patterns for extracting Conformal tool versions
        # Pattern 1: FV module command with confrml version
        fv_pattern = re.compile(r'set\s+FV\(MODULE_CMD\)\s+"[^"]*module\s+load\s+confrml/(\d+)/(\S+)"')
        
        # Pattern 2: CLP module command with confrml version
        clp_pattern = re.compile(r'set\s+CLP\(MODULE_CMD\)\s+"[^"]*module\s+load\s+confrml/(\d+)/(\S+)"')
        
        # Pattern 3: Generic tool module command (for fallback)
        generic_pattern = re.compile(r'set\s+(\w+)\(MODULE_CMD\)\s+"[^"]*module\s+load\s+(\w+)/(\d+)/(\S+)"')
        
        for file_path in valid_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line_num, line in enumerate(f, 1):
                        # Skip commented lines
                        if line.strip().startswith('#'):
                            continue
                        
                        # Try FV pattern first
                        match = fv_pattern.search(line)
                        if match:
                            major_version = match.group(1)
                            full_version = match.group(2).strip('"')
                            version_string = f"confrml/{major_version}/{full_version}"
                            
                            all_items.append({
                                'name': version_string,
                                'tool_variable': 'FV',
                                'major_version': major_version,
                                'full_version': full_version,
                                'line_number': line_num,
                                'file_path': str(file_path),
                                'line_content': line.strip()
                            })
                            continue
                        
                        # Try CLP pattern
                        match = clp_pattern.search(line)
                        if match:
                            major_version = match.group(1)
                            full_version = match.group(2).strip('"')
                            version_string = f"confrml/{major_version}/{full_version}"
                            
                            all_items.append({
                                'name': version_string,
                                'tool_variable': 'CLP',
                                'major_version': major_version,
                                'full_version': full_version,
                                'line_number': line_num,
                                'file_path': str(file_path),
                                'line_content': line.strip()
                            })
                            continue
                        
                        # Try generic pattern for confrml in other tool definitions
                        match = generic_pattern.search(line)
                        if match:
                            tool_var = match.group(1)
                            tool_name = match.group(2)
                            major_version = match.group(3)
                            full_version = match.group(4).strip('"')
                            
                            # Only capture if it's confrml
                            if tool_name.lower() == 'confrml':
                                version_string = f"confrml/{major_version}/{full_version}"
                                
                                all_items.append({
                                    'name': version_string,
                                    'tool_variable': tool_var,
                                    'major_version': major_version,
                                    'full_version': full_version,
                                    'line_number': line_num,
                                    'file_path': str(file_path),
                                    'line_content': line.strip()
                                })
            
            except Exception as e:
                errors.append(f"Error parsing {file_path}: {str(e)}")
        
        # 3. Store frequently reused data on self
        self._parsed_items = all_items
        self._metadata = {
            'total': len(all_items),
            'files_processed': len(valid_files),
            'errors': errors
        }
        
        # 4. Return aggregated dict with items containing line_number and file_path
        return {
            'items': all_items,
            'metadata': self._metadata,
            'errors': errors
        }
    
    # =========================================================================
    # Type 1: Boolean Check
    # =========================================================================
    
    def _execute_type1(self) -> CheckResult:
        """
        Type 1: Boolean Check.
        
        Checks if Conformal LEC tool version exists in setup configuration.
        Does NOT use pattern_items for searching.
        
        Use OutputBuilderMixin.build_complete_output() for automatic formatting.
        
        Returns:
            CheckResult with is_pass based on check logic
        """
        # Parse input
        data = self._parse_input_files()
        items = data.get('items', [])
        errors = data.get('errors', [])
        
        # Handle parsing errors
        if errors:
            return create_check_result(
                is_pass=False,
                item_id=self.item_id,
                item_desc=self.item_desc,
                details=[DetailItem(
                    severity=Severity.FAIL,
                    description=f"Parsing errors encountered: {'; '.join(errors)}",
                    reason="Failed to parse input files"
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
        
        missing_items = [] if found_items else ['Conformal LEC tool version (FV or CLP MODULE_CMD)']
        
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
        PASS/FAIL depends on check purpose (violation check vs requirement check).
        
        Template auto-handles waiver=0 conversions.
        
        Returns:
            CheckResult with is_pass based on value comparison
        """
        # Parse input
        data = self._parse_input_files()
        items = data.get('items', [])
        errors = data.get('errors', [])
        
        # Handle parsing errors
        if errors:
            return create_check_result(
                is_pass=False,
                item_id=self.item_id,
                item_desc=self.item_desc,
                details=[DetailItem(
                    severity=Severity.FAIL,
                    description=f"Parsing errors encountered: {'; '.join(errors)}",
                    reason="Failed to parse input files"
                )]
            )
        
        # Get requirements
        pattern_items = self.item_data.get('requirements', {}).get('pattern_items', [])
        
        # Convert items to dict with metadata
        found_items_dict = {
            item['name']: {
                'name': item['name'],
                'line_number': item.get('line_number', 0),
                'file_path': item.get('file_path', 'N/A')
            }
            for item in items
        }
        
        # Check which pattern items are found vs missing
        found_items = {}
        missing_items = []
        
        for pattern in pattern_items:
            # Check if any found item matches the pattern
            matched = False
            for item_name, item_data in found_items_dict.items():
                # Support wildcard matching
                if self._matches_pattern(item_name, pattern):
                    found_items[item_name] = item_data
                    matched = True
                    break
            
            if not matched:
                missing_items.append(pattern)
        
        # Find extra items (not in pattern_items)
        extra_items = {}
        for item_name, item_data in found_items_dict.items():
            is_extra = True
            for pattern in pattern_items:
                if self._matches_pattern(item_name, pattern):
                    is_extra = False
                    break
            if is_extra:
                extra_items[item_name] = item_data
        
        # Use template helper (auto-handles waiver=0)
        # Type 2: Use TYPE2_3 desc+reason (emphasize "matched/satisfied")
        return self.build_complete_output(
            found_items=found_items,
            missing_items=missing_items,
            extra_items=extra_items,
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
        
        # Handle parsing errors
        if errors:
            return create_check_result(
                is_pass=False,
                item_id=self.item_id,
                item_desc=self.item_desc,
                details=[DetailItem(
                    severity=Severity.FAIL,
                    description=f"Parsing errors encountered: {'; '.join(errors)}",
                    reason="Failed to parse input files"
                )]
            )
        
        # Fix API-016: Use waivers.get() directly to preserve dict format
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # Get requirements
        pattern_items = self.item_data.get('requirements', {}).get('pattern_items', [])
        
        # Convert items to dict with metadata for found_items
        found_items = {
            item['name']: {
                'name': item['name'],
                'line_number': item.get('line_number', 0),
                'file_path': item.get('file_path', 'N/A')
            }
            for item in items
        }
        
        # Find violations (items that don't match required patterns)
        violations = []
        for item_name in found_items.keys():
            matches_pattern = False
            for pattern in pattern_items:
                if self._matches_pattern(item_name, pattern):
                    matches_pattern = True
                    break
            if not matches_pattern:
                violations.append(item_name)
        
        # Also check for missing required patterns
        for pattern in pattern_items:
            matched = False
            for item_name in found_items.keys():
                if self._matches_pattern(item_name, pattern):
                    matched = True
                    break
            if not matched:
                violations.append(f"Missing required pattern: {pattern}")
        
        # Separate waived/unwaived using template helper
        waived_items = []
        unwaived_items = []
        
        for violation in violations:
            if self.match_waiver_entry(violation, waive_dict):
                waived_items.append(violation)
            else:
                unwaived_items.append(violation)
        
        # Fix API-017: waive_dict values are strings (reasons), not dicts
        # Find unused waivers by checking if waiver names were used
        used_names = set(waived_items)
        unused_waivers = [name for name in waive_dict.keys() if name not in used_names]
        
        # Fix API-021: Use missing_items parameter instead of unwaived_items
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
        
        Use OutputBuilderMixin.build_complete_output() with has_waiver_value=True.
        
        Returns:
            CheckResult with waiver logic applied
        """
        # Parse input
        data = self._parse_input_files()
        items = data.get('items', [])
        errors = data.get('errors', [])
        
        # Handle parsing errors
        if errors:
            return create_check_result(
                is_pass=False,
                item_id=self.item_id,
                item_desc=self.item_desc,
                details=[DetailItem(
                    severity=Severity.FAIL,
                    description=f"Parsing errors encountered: {'; '.join(errors)}",
                    reason="Failed to parse input files"
                )]
            )
        
        # Fix API-016: Use waivers.get() directly to preserve dict format
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # Convert items to dict with metadata
        found_items_dict = {
            item['name']: {
                'name': item['name'],
                'line_number': item.get('line_number', 0),
                'file_path': item.get('file_path', 'N/A')
            }
            for item in items
        }
        
        # For Type 4, if no items found, that's a violation (unless waived)
        if not found_items_dict:
            violation = 'Conformal LEC tool version (FV or CLP MODULE_CMD)'
            
            # Check if this violation is waived
            if self.match_waiver_entry(violation, waive_dict):
                waived_items = [violation]
                unwaived_items = []
            else:
                waived_items = []
                unwaived_items = [violation]
            
            # Fix API-017: waive_dict values are strings (reasons), not dicts
            # Find unused waivers by checking if waiver names were used
            unused_waivers = [name for name in waive_dict.keys() if name not in waived_items]
            
            # Fix API-021: Use missing_items parameter instead of unwaived_items
            # Use template helper for automatic output formatting (waivers.value>0)
            # Type 4: Use TYPE1_4 reason (emphasize "found/not found")
            return self.build_complete_output(
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
        
        # Items found - this is a PASS case
        # Use template helper for automatic output formatting (waivers.value>0)
        # Type 4: Use TYPE1_4 reason (emphasize "found/not found")
        return self.build_complete_output(
            found_items=found_items_dict,
            waive_dict=waive_dict,
            unused_waivers=list(waive_dict.keys()),  # All waivers unused since no violations
            found_desc=self.FOUND_DESC_TYPE1_4,
            missing_desc=self.MISSING_DESC_TYPE1_4,
            waived_desc=self.WAIVED_DESC,
            found_reason=self.FOUND_REASON_TYPE1_4,
            missing_reason=self.MISSING_REASON_TYPE1_4,
            waived_base_reason=self.WAIVED_BASE_REASON,
            unused_waiver_reason=self.UNUSED_WAIVER_REASON
        )
    
    # =========================================================================
    # Helper Methods
    # =========================================================================
    
    def _matches_pattern(self, item: str, pattern: str) -> bool:
        """
        Check if item matches pattern (supports wildcards).
        
        Args:
            item: Item to check
            pattern: Pattern to match against (supports * wildcards)
            
        Returns:
            True if item matches pattern
        """
        # Support wildcards
        if '*' in pattern:
            regex_pattern = pattern.replace('*', '.*')
            return bool(re.search(regex_pattern, item, re.IGNORECASE))
        
        # Exact match (case-insensitive)
        return pattern.lower() == item.lower()


# =========================================================================
# Entry Point
# =========================================================================

def main():
    """Main entry point."""
    checker = Check_3_0_0_02()
    checker.init_checker(Path(__file__))
    result = checker.execute_check()
    checker.write_output(result)
    return 0 if result.is_pass else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())