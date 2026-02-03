################################################################################
# Script Name: IMP-3-0-0-03.py
#
# Purpose:
#   List Tempus timing signoff tool version (eg. ssv/231/23.12-s092_1)
#
# Logic:
#   - Parse input file: setup_vars.tcl
#   - Scan line-by-line for TEMPUS(MODULE_CMD) variable assignment
#   - Extract module load command containing ssv version string
#   - Validate version format matches ssv/{major}/{version} pattern
#   - Extract version components (major number and full version string)
#   - Format output as ssv/{major}/{version} (e.g., ssv/202/20.20.000)
#   - Report ERROR if TEMPUS variable not found or version string malformed
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
class Check_3_0_0_03(InputFileParserMixin, OutputBuilderMixin, WaiverHandlerMixin, BaseChecker):
    """
    IMP-3-0-0-03: List Tempus timing signoff tool version (eg. ssv/231/23.12-s092_1)
    
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
    FOUND_DESC_TYPE1_4 = "Tempus timing signoff tool version found in setup configuration"
    MISSING_DESC_TYPE1_4 = "Tempus timing signoff tool version not found in setup configuration"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_DESC_TYPE2_3 = "Tempus version pattern matched in setup configuration"
    MISSING_DESC_TYPE2_3 = "Expected Tempus version pattern not satisfied in setup configuration"
    
    # All Types (waiver description unified)
    WAIVED_DESC = "Waived Tempus version configuration issues"
    
    # ⭐ REASON CONSTANTS - Split by Type semantics (API-025)
    # ALL Types pass found_reason/missing_reason, but use different constants
    
    # Type 1/4: Boolean checks - emphasize "found/not found" (existence)
    FOUND_REASON_TYPE1_4 = "Tempus timing signoff tool version found in TEMPUS(MODULE_CMD) variable"
    MISSING_REASON_TYPE1_4 = "TEMPUS(MODULE_CMD) variable not found or version string malformed in setup_vars.tcl"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_REASON_TYPE2_3 = "Tempus version pattern matched and validated in setup configuration"
    MISSING_REASON_TYPE2_3 = "Expected Tempus version pattern not satisfied or missing from setup configuration"
    
    # Waiver-related (Type 3/4 only)
    WAIVED_BASE_REASON = "Tempus version configuration issue waived per design approval"
    UNUSED_WAIVER_REASON = "Waiver defined but no Tempus version violation matched"
    
    def __init__(self):
        """Initialize the checker."""
        super().__init__(
            check_module="3.0_TOOL_VERSION",
            item_id="IMP-3-0-0-03",
            item_desc="List Tempus timing signoff tool version (eg. ssv/231/23.12-s092_1)"
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
        Parse input files to extract Tempus version from setup_vars.tcl.
        
        Parsing Strategy:
        1. Validate input files (setup_vars.tcl)
        2. Scan line-by-line for TEMPUS(MODULE_CMD) variable
        3. Extract module load command with ssv version
        4. Parse version string in format ssv/{major}/{version}
        5. Handle edge cases (missing variable, malformed version)
        
        Returns:
            Dict with parsed data:
            - 'items': List[Dict] - Tempus version items with metadata
            - 'metadata': Dict - File metadata
            - 'errors': List - Parsing errors
        """
        # 1. Validate inputs - IMPORTANT: returns tuple (valid_files_list, missing_files_list)
        valid_files, missing_files = self.validate_input_files()
        
        # Fix KNOWN_ISSUE_LOGIC-001: Explicitly check for empty list
        if not valid_files or len(valid_files) == 0:
            raise ConfigurationError(
                self.create_missing_files_error(missing_files if missing_files else ["No input files provided"])
            )
        
        if missing_files:
            raise ConfigurationError(
                self.create_missing_files_error(missing_files)
            )
        
        # 2. Parse using patterns from file analysis
        all_items = []
        errors = []
        metadata = {}
        
        # Define regex patterns for Tempus version extraction
        # Pattern 1: Primary extraction - TEMPUS MODULE_CMD with version string
        pattern1 = re.compile(r'set\s+TEMPUS\(MODULE_CMD\)\s+"[^"]*module\s+load\s+ssv/(\d+)/(\S+)"')
        # Pattern 2: Simplified version path extraction
        pattern2 = re.compile(r'set\s+TEMPUS\(MODULE_CMD\)\s+".*?ssv/([\d]+/[\d\.\-\w]+)"')
        # Pattern 3: Variable existence check
        pattern3 = re.compile(r'set\s+TEMPUS\(MODULE_CMD\)')
        # Pattern 4: Full command extraction for validation
        pattern4 = re.compile(r'set\s+TEMPUS\(MODULE_CMD\)\s+"([^"]+)"')
        # Pattern 5: Fallback - any ssv version string in file
        pattern5 = re.compile(r'ssv/(\d+)/(\S+)')
        
        for file_path in valid_files:
            tempus_found = False
            version_extracted = False
            
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line_num, line in enumerate(f, 1):
                        # Try Pattern 1: Primary extraction with major and version
                        match1 = pattern1.search(line)
                        if match1:
                            major = match1.group(1)
                            version = match1.group(2)
                            version_string = f"ssv/{major}/{version}"
                            
                            all_items.append({
                                'name': version_string,
                                'line_number': line_num,
                                'file_path': str(file_path),
                                'line_content': line.strip(),
                                'major': major,
                                'version': version
                            })
                            tempus_found = True
                            version_extracted = True
                            break  # Stop after first valid match
                        
                        # Try Pattern 2: Simplified version path extraction
                        match2 = pattern2.search(line)
                        if match2 and not version_extracted:
                            version_path = match2.group(1)
                            version_string = f"ssv/{version_path}"
                            
                            # Split to get major and version
                            parts = version_path.split('/', 1)
                            major = parts[0] if len(parts) > 0 else 'unknown'
                            version = parts[1] if len(parts) > 1 else 'unknown'
                            
                            all_items.append({
                                'name': version_string,
                                'line_number': line_num,
                                'file_path': str(file_path),
                                'line_content': line.strip(),
                                'major': major,
                                'version': version
                            })
                            tempus_found = True
                            version_extracted = True
                            break
                        
                        # Check if TEMPUS variable exists (for error reporting)
                        if pattern3.search(line) and not tempus_found:
                            tempus_found = True
                            # Continue to try extracting version
                            
                            # Try Pattern 4: Full command extraction
                            match4 = pattern4.search(line)
                            if match4:
                                full_command = match4.group(1)
                                # Try to find ssv version in the command
                                match5 = pattern5.search(full_command)
                                if match5:
                                    major = match5.group(1)
                                    version = match5.group(2)
                                    version_string = f"ssv/{major}/{version}"
                                    
                                    all_items.append({
                                        'name': version_string,
                                        'line_number': line_num,
                                        'file_path': str(file_path),
                                        'line_content': line.strip(),
                                        'major': major,
                                        'version': version
                                    })
                                    version_extracted = True
                                    break
                
                # Error handling for edge cases
                if not tempus_found:
                    errors.append({
                        'type': 'missing_variable',
                        'message': 'TEMPUS(MODULE_CMD) variable not found in setup_vars.tcl',
                        'file_path': str(file_path)
                    })
                elif not version_extracted:
                    errors.append({
                        'type': 'malformed_version',
                        'message': 'Tempus version string not found in TEMPUS(MODULE_CMD)',
                        'file_path': str(file_path)
                    })
                    
            except Exception as e:
                errors.append({
                    'type': 'parse_error',
                    'message': f'Error parsing file: {str(e)}',
                    'file_path': str(file_path)
                })
        
        # 3. Store frequently reused data on self
        self._parsed_items = all_items
        self._metadata = metadata
        
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
        
        Check if Tempus version exists in setup configuration.
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
        found_items = {
            item['name']: {
                'name': item['name'],
                'line_number': item.get('line_number', 0),
                'file_path': item.get('file_path', 'N/A')
            }
            for item in items
        } if items else {}
        
        # Determine missing items based on errors
        missing_items = []
        if errors:
            for error in errors:
                missing_items.append(error.get('message', 'Unknown error'))
        elif not found_items:
            missing_items = ['Tempus version not found in setup_vars.tcl']
        
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
        
        # Convert items to dict with metadata
        found_items = {
            item['name']: {
                'name': item['name'],
                'line_number': item.get('line_number', 0),
                'file_path': item.get('file_path', 'N/A')
            }
            for item in items
        }
        
        # Check for missing patterns
        missing_items = []
        for pattern in pattern_items:
            pattern_found = False
            for item in items:
                # Check if item matches pattern (support wildcards)
                if self._matches_pattern(item['name'], pattern):
                    pattern_found = True
                    break
            if not pattern_found:
                missing_items.append(pattern)
        
        # Add errors to missing items
        if errors:
            for error in errors:
                missing_items.append(error.get('message', 'Unknown error'))
        
        # Find extra items (items not in pattern_items)
        extra_items = {}
        if pattern_items:
            for item in items:
                is_extra = True
                for pattern in pattern_items:
                    if self._matches_pattern(item['name'], pattern):
                        is_extra = False
                        break
                if is_extra:
                    extra_items[item['name']] = {
                        'name': item['name'],
                        'line_number': item.get('line_number', 0),
                        'file_path': item.get('file_path', 'N/A')
                    }
        
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
        
        # Fix KNOWN_ISSUE_API-016: Use waivers.get() directly to preserve dict format
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
        
        # Find violations (missing patterns or errors)
        violations = []
        
        # Check for missing patterns
        for pattern in pattern_items:
            pattern_found = False
            for item in items:
                if self._matches_pattern(item['name'], pattern):
                    pattern_found = True
                    break
            if not pattern_found:
                violations.append({
                    'name': f"Missing pattern: {pattern}",
                    'line_number': 0,
                    'file_path': 'N/A'
                })
        
        # Add errors as violations
        for error in errors:
            violations.append({
                'name': error.get('message', 'Unknown error'),
                'line_number': 0,
                'file_path': error.get('file_path', 'N/A')
            })
        
        # Separate waived/unwaived using template helper
        waived_items = []
        unwaived_items = []
        
        for violation in violations:
            if self.match_waiver_entry(violation['name'], waive_dict):
                waived_items.append(violation['name'])
            else:
                unwaived_items.append(violation['name'])
        
        # Fix KNOWN_ISSUE_API-017: waive_dict.keys() are item names (strings)
        used_names = set(waived_items)
        unused_waivers = [name for name in waive_dict.keys() if name not in used_names]
        
        # Fix KNOWN_ISSUE_API-021: Use missing_items parameter instead of unwaived_items
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
        
        # Fix KNOWN_ISSUE_API-016: Use waivers.get() directly to preserve dict format
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # Convert items to dict with metadata
        found_items = {
            item['name']: {
                'name': item['name'],
                'line_number': item.get('line_number', 0),
                'file_path': item.get('file_path', 'N/A')
            }
            for item in items
        }
        
        # Determine violations: use found version items for waiver matching
        # Type 4 waives specific versions (e.g., "ssv/202/20.20.000")
        violations = []
        if errors:
            for error in errors:
                violations.append(error.get('message', 'Unknown error'))
        elif not found_items:
            violations.append('Tempus version not found in setup_vars.tcl')
        else:
            # Use found version as violation for waiver matching
            violations.extend(found_items.keys())
        
        # Separate waived/unwaived
        waived_items = []
        unwaived_items = []
        
        for violation in violations:
            if self.match_waiver_entry(violation, waive_dict):
                waived_items.append(violation)
            else:
                unwaived_items.append(violation)
        
        # Fix KNOWN_ISSUE_API-017: waive_dict.keys() are item names (strings)
        used_names = set(waived_items)
        unused_waivers = [name for name in waive_dict.keys() if name not in used_names]
        
        # Fix KNOWN_ISSUE_API-021: Use missing_items parameter instead of unwaived_items
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
    # Helper Methods
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
            return bool(re.search(regex_pattern, item, re.IGNORECASE))
        # Exact match
        return pattern.lower() == item.lower()


# =========================================================================
# Entry Point
# =========================================================================

def main():
    """Main entry point."""
    checker = Check_3_0_0_03()
    checker.init_checker(Path(__file__))
    result = checker.execute_check()
    checker.write_output(result)
    return 0 if result.is_pass else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())