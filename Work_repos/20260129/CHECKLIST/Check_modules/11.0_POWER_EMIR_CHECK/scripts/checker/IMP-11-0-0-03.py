################################################################################
# Script Name: IMP-11-0-0-03.py
#
# Purpose:
#   Confirm activity file was used? If not, provide default switching activity values in comments field.
#
# Logic:
#   - Parse input files: *static*.log, *dynamic*.log, *EM*.log (Voltus power analysis logs)
#   - Scan for 'read_activity_file' finished successfully pattern
#   - Scan for 'set_default_switching_activity' finished successfully pattern
#   - Extract -input_activity parameter value if default activity command found
#   - Prioritize read_activity_file over set_default_switching_activity
#   - Report activity configuration method found or FAIL if neither is detected
#   - For Type 3/4: Match violations against waive_items and classify as waived/unwaived
#
# Auto Type Detection:
#   Type 1: requirements.value=N/A, waivers.value=N/A/0 → Boolean check
#   Type 2: requirements.value>0, pattern_items exists, waivers.value=N/A/0 → Value comparison
#   Type 3: requirements.value>0, pattern_items exists, waivers.value>0 → Value with waiver logic
#   Type 4: requirements.value=N/A, waivers.value>0 → Boolean with waiver logic
#
# Output Behavior (Type 2/3 - Check README "Output Behavior" section!):
#   status_check: pattern_items = items to CHECK STATUS (only output matched items)
#     - found_items = patterns matched AND status correct
#     - missing_items = patterns matched BUT status wrong
#
# Waiver Tag Rules:
#   When waivers.value > 0 (Type 3/4):
#     - All waive_items related INFO/FAIL/WARN reason suffix: [WAIVER]
#   When waivers.value = 0 (Type 1/2):
#     - waive_items output as INFO with suffix: [WAIVED_INFO]
#     - FAIL/WARN converted to INFO with suffix: [WAIVED_AS_INFO]
#   All types support value = N/A
#
# Refactored: 2026-01-09 (Using checker_templates v1.1.0)
#
# Author: Jing Li
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
from checker_templates.input_file_parser_template import InputFileParserMixin


# MANDATORY: Inherit mixins in correct order (InputFileParserMixin first if used)
class Check_11_0_0_03(InputFileParserMixin, OutputBuilderMixin, WaiverHandlerMixin, BaseChecker):
    """
    IMP-11-0-0-03: Confirm activity file was used? If not, provide default switching activity values in comments field.
    
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
    FOUND_DESC_TYPE1_4 = "Activity configuration found in power analysis log"
    MISSING_DESC_TYPE1_4 = "Activity configuration not found in power analysis log"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_DESC_TYPE2_3 = "Activity configuration validated (activity file or defaults set)"
    MISSING_DESC_TYPE2_3 = "No activity configuration detected (neither activity file nor defaults)"
    
    # All Types (waiver description unified)
    WAIVED_DESC = "Activity configuration issue waived"
    
    # ⭐ REASON CONSTANTS - Split by Type semantics (API-025)
    # ALL Types pass found_reason/missing_reason, but use different constants
    
    # Type 1/4: Boolean checks - emphasize "found/not found" (existence)
    FOUND_REASON_TYPE1_4 = "Activity file successfully loaded or default switching activity configured"
    MISSING_REASON_TYPE1_4 = "Neither 'read_activity_file' nor 'set_default_switching_activity' command found in log"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_REASON_TYPE2_3 = "'read_activity_file' finished successfully OR 'set_default_switching_activity' finished successfully"
    MISSING_REASON_TYPE2_3 = "Required activity configuration pattern not satisfied - no valid activity setup detected"
    
    # Waiver-related (Type 3/4 only)
    WAIVED_BASE_REASON = "Activity configuration violation waived per design team approval"
    UNUSED_WAIVER_REASON = "Waiver not matched - no corresponding activity configuration issue found in log"
    
    def __init__(self):
        """Initialize the checker."""
        super().__init__(
            check_module="11.0_POWER_EMIR_CHECK",
            item_id="IMP-11-0-0-03",
            item_desc="Confirm activity file was used? If not, provide default switching activity values in comments field."
        )
        # Custom member variables for parsed data
        self._parsed_items: List[Dict[str, Any]] = []
        self._metadata: Dict[str, str] = {}
        self._activity_file_found: bool = False
        self._default_activity_found: bool = False
        self._input_activity_value: Optional[str] = None
    
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
        Parse input files to extract activity configuration information.
        
        Scans Voltus power analysis log files for:
        1. 'read_activity_file' finished successfully pattern
        2. 'set_default_switching_activity' finished successfully pattern
        3. -input_activity parameter value extraction
        
        Returns:
            Dict with parsed data:
            - 'items': List[Dict] - Activity configuration items found
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
        activity_file_found = False
        default_activity_found = False
        input_activity_value = None
        
        # 3. Parse each input file for activity configuration information
        # Pattern 1: Detect successful read_activity_file command
        activity_file_pattern = re.compile(r"'read_activity_file'\s+finished successfully", re.IGNORECASE)
        
        # Pattern 2: Detect successful set_default_switching_activity command
        default_activity_pattern = re.compile(r"'set_default_switching_activity'\s+finished successfully", re.IGNORECASE)
        
        # Pattern 3: Extract input_activity parameter value
        input_activity_pattern = re.compile(r"set_default_switching_activity\s+.*?-input_activity\s+(\S+)", re.IGNORECASE)
        
        # Pattern 4: Extract activity file path
        activity_file_path_pattern = re.compile(r"read_activity_file\s+(\S+)", re.IGNORECASE)
        
        for file_path in valid_files:
            try:
                file_activity_found = False
                file_default_found = False
                file_input_activity = None
                file_activity_path = None
                activity_line = 0
                default_line = 0
                
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line_num, line in enumerate(f, 1):
                        # Check for read_activity_file success (highest priority)
                        if activity_file_pattern.search(line):
                            file_activity_found = True
                            activity_file_found = True
                            if activity_line == 0:
                                activity_line = line_num
                        
                        # Extract activity file path
                        path_match = activity_file_path_pattern.search(line)
                        if path_match:
                            file_activity_path = path_match.group(1)
                        
                        # Check for set_default_switching_activity success
                        if default_activity_pattern.search(line):
                            file_default_found = True
                            default_activity_found = True
                            if default_line == 0:
                                default_line = line_num
                        
                        # Extract input_activity parameter value
                        match = input_activity_pattern.search(line)
                        if match:
                            file_input_activity = match.group(1)
                            input_activity_value = file_input_activity
                
                # After processing file, create item based on what was found
                file_name = file_path.name
                
                # Report both activity file AND default switching activity if both are present
                if file_activity_found:
                    # Activity file was used
                    item_name = f"{file_name}"
                    item_desc = "'read_activity_file' finished successfully"
                    if file_activity_path:
                        item_desc += f" ({file_activity_path})"
                    
                    # If BOTH activity file and default switching activity exist, combine them
                    if file_default_found and file_input_activity:
                        item_desc += f" + set_default_switching_activity -input_activity {file_input_activity}"
                    elif file_default_found:
                        item_desc += " + 'set_default_switching_activity' finished successfully"
                    
                    items.append({
                        'name': item_name,
                        'line_number': activity_line,
                        'file_path': str(file_path),
                        'type': 'activity_file',
                        'description': item_desc
                    })
                elif file_default_found and file_input_activity:
                    # Only default switching activity was set (no activity file)
                    item_name = f"{file_name}"
                    item_desc = f"set_default_switching_activity -input_activity {file_input_activity}"
                    
                    items.append({
                        'name': item_name,
                        'line_number': default_line,
                        'file_path': str(file_path),
                        'type': 'default_activity',
                        'value': file_input_activity,
                        'description': item_desc
                    })
                elif file_default_found:
                    # Default activity found but no input_activity value extracted
                    item_name = f"{file_name}"
                    item_desc = "'set_default_switching_activity' finished successfully"
                    
                    items.append({
                        'name': item_name,
                        'line_number': default_line,
                        'file_path': str(file_path),
                        'type': 'default_activity',
                        'description': item_desc
                    })
                # If neither found, no item is added for this file
                
            except Exception as e:
                errors.append(f"Error parsing {file_path}: {str(e)}")
        
        # 4. Store frequently reused data on self
        self._parsed_items = items
        self._metadata = metadata
        self._activity_file_found = activity_file_found
        self._default_activity_found = default_activity_found
        self._input_activity_value = input_activity_value
        
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
        # Build dict from clean/passing objects (activity configurations found)
        found_items = {}
        data = self._parse_input_files()
        
        # If no violations, we have a valid activity configuration
        if not violations:
            items = data.get('items', [])
            for item in items:
                item_name = item.get('name', 'activity_configuration')
                found_items[item_name] = {
                    'name': item_name,
                    'line_number': item.get('line_number', 0),
                    'file_path': item.get('file_path', 'N/A'),
                    'reason': item.get('description', self.FOUND_REASON_TYPE1_4)
                }
        
        # FIXED: missing_items should be dict format {name: metadata}
        missing_items = violations
        
        return self.build_complete_output(
            found_items=found_items,
            missing_items=missing_items,
            found_desc=self.FOUND_DESC_TYPE1_4,
            missing_desc=self.MISSING_DESC_TYPE1_4,
            found_reason=lambda meta: meta.get('reason', self.FOUND_REASON_TYPE1_4),
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
        
        # Check if parsing encountered errors
        if errors:
            violations = {}
            for idx, error in enumerate(errors):
                error_key = f"parse_error_{idx + 1}"
                violations[error_key] = {
                    'line_number': 0,
                    'file_path': 'N/A',
                    'reason': error
                }
            return violations
        
        # Get activity configuration data
        items = data.get('items', [])
        
        # Get all input files that were validated
        valid_files, _ = self.validate_input_files()
        
        # Track which files have activity configuration
        files_with_config = set()
        for item in items:
            files_with_config.add(item.get('file_path', ''))
        
        # Check each file for missing activity configuration
        violations = {}
        for file_path in valid_files:
            file_path_str = str(file_path)
            if file_path_str not in files_with_config:
                # This file has no activity configuration
                file_name = file_path.name
                violations[file_name] = {
                    'line_number': 0,
                    'file_path': file_path_str,
                    'reason': "Neither 'read_activity_file' nor 'set_default_switching_activity' command found in log"
                }
        
        return violations
    
    # =========================================================================
    # Type 2: Value Check
    # =========================================================================
    
    def _execute_type2(self) -> CheckResult:
        """Type 2: Pattern/value check without waiver support."""
        found_items, missing_items = self._type2_core_logic()
        
        return self.build_complete_output(
            found_items=found_items,
            missing_items=missing_items,
            found_desc=self.FOUND_DESC_TYPE2_3,
            missing_desc=self.MISSING_DESC_TYPE2_3,
            found_reason=lambda meta: meta.get('reason', self.FOUND_REASON_TYPE2_3),
            missing_reason=self.MISSING_REASON_TYPE2_3
        )
    
    def _type2_core_logic(self) -> Tuple[Dict[str, dict], Dict[str, dict]]:
        """
        Core Type 2 pattern matching logic (shared by Type 2 and Type 3).
        
        Returns:
            Tuple of (found_items, missing_items)
            - found_items: {item_name: {'line_number': ..., 'file_path': ...}}
            - missing_items: {item_name: {'line_number': ..., 'file_path': ..., 'reason': ...}}
        """
        data = self._parse_input_files()
        items = data.get('items', [])
        
        requirements = self.item_data.get('requirements', {})
        pattern_items = requirements.get('pattern_items', [])
        
        found_items = {}
        missing_items = {}
        
        # Track which patterns have been matched
        matched_patterns = set()
        
        # Search for activity configuration patterns in log items
        for item in items:
            item_name = item.get('name', '')
            line_number = item.get('line_number', 0)
            file_path = item.get('file_path', 'N/A')
            description = item.get('description', self.FOUND_REASON_TYPE2_3)
            
            # Check if item matches any required pattern
            for pattern in pattern_items:
                if pattern.lower() in item_name.lower():
                    # Pattern found - add to found_items
                    found_items[item_name] = {
                        'line_number': line_number,
                        'file_path': file_path,
                        'reason': description
                    }
                    matched_patterns.add(pattern)
                    break
        
        # Identify missing patterns (not found in log)
        for pattern in pattern_items:
            if pattern not in matched_patterns:
                missing_items[pattern] = {
                    'line_number': 0,
                    'file_path': 'N/A',
                    'reason': f"Required activity configuration pattern not satisfied - no valid activity setup detected"
                }
        
        return found_items, missing_items
    
    # =========================================================================
    # Type 3: Value Check with Waiver Logic
    # =========================================================================
    
    def _execute_type3(self) -> CheckResult:
        """Type 3: Pattern/value check with waiver support (reuses Type 2 core logic)."""
        # Step 1: Get found/missing items using Type 2's core logic
        found_items_base, violations = self._type2_core_logic()
        
        # Step 2: Parse waiver configuration
        # FIXED: Use waivers.get('waive_items', []) instead of get_waive_items()
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # Step 3: Initialize result collections
        found_items = {}
        waived_items = {}
        missing_items = {}
        used_waivers = set()
        
        # Step 4: Process found_items_base (no waiver needed - already satisfied)
        for item_name, item_data in found_items_base.items():
            found_items[item_name] = item_data
        
        # Step 5: Process violations with waiver matching
        for viol_name, viol_data in violations.items():
            matched_waiver = self.match_waiver_entry(viol_name, waive_dict)
            if matched_waiver:
                waived_items[viol_name] = viol_data
                used_waivers.add(matched_waiver)
            else:
                missing_items[viol_name] = viol_data
        
        # Step 6: Find unused waivers
        unused_waivers = [w for w in waive_dict.keys() if w not in used_waivers]
        
        # Step 7: Build output
        return self.build_complete_output(
            found_items=found_items,
            missing_items=missing_items,
            waived_items=waived_items,
            unused_waivers=unused_waivers,
            waive_dict=waive_dict,
            found_desc=self.FOUND_DESC_TYPE2_3,
            missing_desc=self.MISSING_DESC_TYPE2_3,
            waived_desc=self.WAIVED_DESC,
            found_reason=lambda meta: meta.get('reason', self.FOUND_REASON_TYPE2_3),
            missing_reason=self.MISSING_REASON_TYPE2_3,
            waived_base_reason=self.WAIVED_BASE_REASON,
            unused_waiver_reason=self.UNUSED_WAIVER_REASON
        )
    
    # =========================================================================
    # Type 4: Boolean Check with Waiver Logic
    # =========================================================================
    
    def _execute_type4(self) -> CheckResult:
        """Type 4: Boolean check with waiver support (reuses Type 1 core logic)."""
        violations = self._type1_core_logic()
        
        # ⚠️ CRITICAL: found_items MUST be dict[str, dict], NOT list!
        found_items = {}
        data = self._parse_input_files()
        
        # If no violations, we have a valid activity configuration
        if not violations:
            items = data.get('items', [])
            for item in items:
                item_name = item.get('name', 'activity_configuration')
                found_items[item_name] = {
                    'name': item_name,
                    'line_number': item.get('line_number', 0),
                    'file_path': item.get('file_path', 'N/A'),
                    'reason': item.get('description', self.FOUND_REASON_TYPE1_4)
                }
        
        # FIXED: Use waivers.get('waive_items', []) instead of get_waive_items()
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
            found_reason=lambda meta: meta.get('reason', self.FOUND_REASON_TYPE1_4),
            missing_reason=self.MISSING_REASON_TYPE1_4,
            waived_base_reason=self.WAIVED_BASE_REASON,
            unused_waiver_reason=self.UNUSED_WAIVER_REASON
        )


# =========================================================================
# Entry Point
# =========================================================================

def main():
    """Main entry point."""
    checker = Check_11_0_0_03()
    checker.init_checker(Path(__file__))
    result = checker.execute_check()
    checker.write_output(result)
    return 0 if result.is_pass else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())