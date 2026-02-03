################################################################################
# Script Name: IMP-3-0-0-00.py
#
# Purpose:
#   List Innovus implementation tool version (eg. innovus/221/22.11-s119_1)
#
# Logic:
#   - Parse input file: setup_vars.tcl
#   - Read file line by line, skipping comments and empty lines
#   - Search for INNOVUS(MODULE_CMD) variable definition
#   - Extract version string from module load command using regex
#   - Construct full version path (innovus/<version>)
#   - Return version as INFO01 if found, ERROR01 if not found
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
class Check_3_0_0_00(InputFileParserMixin, OutputBuilderMixin, WaiverHandlerMixin, BaseChecker):
    """
    IMP-3-0-0-00: List Innovus implementation tool version (eg. innovus/221/22.11-s119_1)
    
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
    # UNIFIED DESCRIPTIONS - MUST be identical across ALL Type 1/2/3/4
    # =========================================================================
    FOUND_DESC = "Innovus version information retrieved"
    MISSING_DESC = "Failed to extract Innovus version information"
    WAIVED_DESC = "Waived version extraction issues"
    # Type 2/3: MUST use pattern matching terminology
    FOUND_REASON = "Required version pattern matched in setup_vars.tcl"
    MISSING_REASON = "Expected version pattern not satisfied or missing from configuration"
    WAIVED_BASE_REASON = "Version extraction failure waived"
    UNUSED_DESC = "Unused waiver entries"
    UNUSED_REASON = "Waiver not matched - version was successfully extracted"
    
    def __init__(self):
        """Initialize the checker."""
        super().__init__(
            check_module="3.0_TOOL_VERSION",
            item_id="IMP-3-0-0-00",
            item_desc="List Innovus implementation tool version (eg. innovus/221/22.11-s119_1)"
        )
        # Store parsed version information
        self._parsed_items: List[Dict[str, Any]] = []
        self._version_found: bool = False
    
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
                check_module=self.check_module,
                item_id=self.item_id,
                item_desc=self.item_desc,
                is_pass=False,
                details=[DetailItem(
                    severity=Severity.FAIL,
                    reason=f"Unexpected error during check execution: {str(e)}"
                )]
            )
    
    # =========================================================================
    # Input Parsing (Common for All Types)
    # =========================================================================
    
    def _parse_input_files(self) -> Dict[str, Any]:
        """
        Parse input files to extract Innovus version from setup_vars.tcl.
        
        Parsing Strategy:
        1. Read setup_vars.tcl line by line
        2. Skip comment lines (starting with #) and empty lines
        3. Search for INNOVUS(MODULE_CMD) variable definition
        4. Extract version string from module load command
        5. Construct full version path (innovus/<version>)
        
        Returns:
            Dict with parsed data:
            - 'items': List[Dict] - Version information with metadata
            - 'metadata': Dict - Parsing metadata
            - 'errors': List - Any parsing errors encountered
        """
        # 1. Validate input files - IMPORTANT: returns tuple (valid_files_list, missing_files_list)
        valid_files, missing_files = self.validate_input_files()
        
        # Fix KNOWN_ISSUE_LOGIC-001: Explicitly check for empty list
        if not valid_files or len(valid_files) == 0:
            raise ConfigurationError(
                self.create_missing_files_error(missing_files if missing_files else ["No input files configured"])
            )
        
        if missing_files:
            raise ConfigurationError(
                self.create_missing_files_error(missing_files)
            )
        
        # 2. Parse files to extract version
        items = []
        errors = []
        
        # Regex patterns for version extraction
        # Pattern 1: Primary pattern with full module load command
        pattern1 = re.compile(r'set\s+INNOVUS\(MODULE_CMD\)\s+"[^"]*module\s+load\s+innovus/([^\s"]+)')
        # Pattern 2: Alternative pattern for different spacing
        pattern2 = re.compile(r'set\s+INNOVUS\(MODULE_CMD\).*?innovus/(\S+)')
        # Pattern 3: Comment lines to skip
        comment_pattern = re.compile(r'^\s*#')
        # Pattern 4: Empty lines to skip
        empty_pattern = re.compile(r'^\s*$')
        
        for file_path in valid_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line_num, line in enumerate(f, 1):
                        # Skip comments and empty lines
                        if comment_pattern.match(line) or empty_pattern.match(line):
                            continue
                        
                        # Try primary pattern first
                        match = pattern1.search(line)
                        if not match:
                            # Try alternative pattern
                            match = pattern2.search(line)
                        
                        if match:
                            version = match.group(1)
                            # Construct full version path
                            full_version = f"innovus/{version}"
                            
                            items.append({
                                'name': full_version,
                                'line_number': line_num,
                                'file_path': str(file_path),
                                'line_content': line.strip()
                            })
                            # Early exit - return first match
                            break
                    
                    # If we found a version in this file, stop processing other files
                    if items:
                        break
                        
            except Exception as e:
                errors.append(f"Error reading {file_path}: {str(e)}")
        
        # 3. Store frequently reused data on self
        self._parsed_items = items
        self._version_found = len(items) > 0
        
        # 4. Return aggregated dict
        return {
            'items': items,
            'metadata': {
                'total': len(items),
                'version_found': self._version_found
            },
            'errors': errors
        }
    
    # =========================================================================
    # Type 1: Boolean Check
    # =========================================================================
    
    def _execute_type1(self) -> CheckResult:
        """
        Type 1: Boolean Check.
        
        Check if Innovus version can be extracted from setup_vars.tcl.
        PASS if version found, FAIL if not found.
        
        Returns:
            CheckResult with is_pass based on version extraction success
        """
        # Parse input
        data = self._parse_input_files()
        items = data.get('items', [])
        errors = data.get('errors', [])
        
        # Convert list to dict with metadata for source file/line display
        found_items = {}
        if items:
            for item in items:
                found_items[item['name']] = {
                    'name': item['name'],
                    'line_number': item.get('line_number', 0),
                    'file_path': item.get('file_path', 'N/A')
                }
        
        # Determine missing items
        missing_items = []
        if not found_items:
            missing_items = ['Innovus version']
        
        # Add parsing errors to missing items if any
        if errors:
            missing_items.extend(errors)
        
        # Use template helper for automatic output formatting
        # ❌ Type 1: DO NOT pass found_reason/missing_reason (API-024)
        return self.build_complete_output(
            found_items=found_items,
            missing_items=missing_items,
            found_desc=self.FOUND_DESC,
            missing_desc=self.MISSING_DESC
            # Uses default: "Item found" / "Item not found"
        )
    
    # =========================================================================
    # Type 2: Value Check
    # =========================================================================
    
    def _execute_type2(self) -> CheckResult:
        """
        Type 2: Value Check.
        
        Search pattern_items in input files.
        Compare extracted version against expected patterns.
        
        Returns:
            CheckResult with is_pass based on value comparison
        """
        # Parse input
        data = self._parse_input_files()
        items = data.get('items', [])
        
        # Get requirements
        pattern_items = self.item_data.get('requirements', {}).get('pattern_items', [])
        
        # Convert items to dict with metadata
        found_items = {}
        for item in items:
            found_items[item['name']] = {
                'name': item['name'],
                'line_number': item.get('line_number', 0),
                'file_path': item.get('file_path', 'N/A')
            }
        
        # Find missing patterns (expected but not found)
        missing_items = []
        for pattern in pattern_items:
            if pattern not in found_items:
                missing_items.append(pattern)
        
        # Find extra items (found but not in pattern_items)
        extra_items = {}
        for name, metadata in found_items.items():
            if name not in pattern_items:
                extra_items[name] = metadata
        
        # Use template helper (auto-handles waiver=0)
        # ✅ Type 2: MUST pass found_reason/missing_reason (API-024)
        return self.build_complete_output(
            found_items=found_items,
            missing_items=missing_items,
            found_desc=self.FOUND_DESC,
            missing_desc=self.MISSING_DESC,
            found_reason=self.FOUND_REASON,      # ✅ REQUIRED for Type 2!
            missing_reason=self.MISSING_REASON   # ✅ REQUIRED for Type 2!
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
        items = parsed_data.get('items', [])
        
        # Fix KNOWN_ISSUE_API-016: Use waivers.get() directly to preserve dict format
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # Get requirements
        pattern_items = self.item_data.get('requirements', {}).get('pattern_items', [])
        
        # Find missing patterns (violations)
        violations = [p for p in pattern_items if p not in [i['name'] for i in items]]
        
        # Separate waived/unwaived using template helper
        waived_items = []
        unwaived_items = []
        
        for violation in violations:
            if self.match_waiver_entry(violation, waive_dict):
                waived_items.append(violation)
            else:
                unwaived_items.append(violation)
        
        # Convert found items to dict with metadata
        found_items = {}
        for item in items:
            found_items[item['name']] = {
                'name': item['name'],
                'line_number': item.get('line_number', 0),
                'file_path': item.get('file_path', 'N/A')
            }
        
        # Fix KNOWN_ISSUE_API-017: waive_dict values are strings (reasons), not dicts
        # Find unused waivers - check if waiver name was used
        used_names = set(waived_items)
        unused_waivers = [name for name in waive_dict.keys() if name not in used_names]
        
        # Fix KNOWN_ISSUE_API-021: Use missing_items parameter instead of unwaived_items
        # ✅ Type 3: MUST pass found_reason/missing_reason + all waiver params (API-024)
        return self.build_complete_output(
            found_items=found_items,
            waived_items=waived_items,
            missing_items=unwaived_items,
            waive_dict=waive_dict,
            unused_waivers=unused_waivers,
            found_desc=self.FOUND_DESC,
            missing_desc=self.MISSING_DESC,
            found_reason=self.FOUND_REASON,              # ✅ REQUIRED for Type 3!
            missing_reason=self.MISSING_REASON,          # ✅ REQUIRED for Type 3!
            waived_desc=self.WAIVED_DESC,                # ✅ REQUIRED for Type 3!
            waived_base_reason=self.WAIVED_BASE_REASON,  # ✅ REQUIRED for Type 3!
            unused_waiver_reason=self.UNUSED_REASON      # ✅ REQUIRED for Type 3!
        )
    
    # =========================================================================
    # Type 4: Boolean Check with Waiver Logic
    # =========================================================================
    
    def _execute_type4(self) -> CheckResult:
        """
        Type 4: Boolean check with waiver support (Type 1 + waiver).
        
        Check if version exists, with waiver support for missing version.
        
        Returns:
            CheckResult with waiver logic applied
        """
        # Parse input
        data = self._parse_input_files()
        items = data.get('items', [])
        
        # Fix KNOWN_ISSUE_API-016: Use waivers.get() directly to preserve dict format
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # Convert items to dict with metadata
        found_items = {}
        for item in items:
            found_items[item['name']] = {
                'name': item['name'],
                'line_number': item.get('line_number', 0),
                'file_path': item.get('file_path', 'N/A')
            }
        
        # Determine violations (missing version)
        violations = []
        if not found_items:
            violations = ['Innovus version']
        
        # Separate waived/unwaived
        waived_items = []
        unwaived_items = []
        
        for violation in violations:
            if self.match_waiver_entry(violation, waive_dict):
                waived_items.append(violation)
            else:
                unwaived_items.append(violation)
        
        # Fix KNOWN_ISSUE_API-017: waive_dict values are strings (reasons), not dicts
        # Find unused waivers - check if waiver name was used
        used_names = set(waived_items)
        unused_waivers = [name for name in waive_dict.keys() if name not in used_names]
        
        # Fix KNOWN_ISSUE_API-021: Use missing_items parameter instead of unwaived_items
        # ✅ Type 4: MUST pass waiver params, DO NOT pass found_reason/missing_reason (API-024)
        return self.build_complete_output(
            found_items=found_items,
            waived_items=waived_items,
            missing_items=unwaived_items,
            waive_dict=waive_dict,
            unused_waivers=unused_waivers,
            found_desc=self.FOUND_DESC,
            missing_desc=self.MISSING_DESC,
            waived_desc=self.WAIVED_DESC,                # ✅ REQUIRED for Type 4!
            waived_base_reason=self.WAIVED_BASE_REASON,  # ✅ REQUIRED for Type 4!
            unused_waiver_reason=self.UNUSED_REASON      # ✅ REQUIRED for Type 4!
            # ❌ Type 4: NO found_reason/missing_reason
        )
    
    # =========================================================================
    # Helper Methods (Optional - Add as needed)
    # =========================================================================
    
    def _matches_waiver(self, item: str, waive_patterns: List[str]) -> bool:
        """
        Check if item matches any waiver pattern.
        
        Args:
            item: Item to check
            waive_patterns: List of waiver patterns
            
        Returns:
            True if item matches any pattern
        """
        for pattern in waive_patterns:
            # Support wildcards
            if '*' in pattern:
                regex_pattern = pattern.replace('*', '.*')
                if re.search(regex_pattern, item, re.IGNORECASE):
                    return True
            # Exact match
            elif pattern.lower() == item.lower():
                return True
        return False


# =========================================================================
# Entry Point
# =========================================================================

def main():
    """Main entry point."""
    checker = Check_3_0_0_00()
    checker.init_checker(Path(__file__))
    result = checker.execute_check()
    checker.write_output(result)
    return 0 if result.is_pass else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())