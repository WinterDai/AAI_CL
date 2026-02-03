################################################################################
# Script Name: IMP-3-0-0-04.py
#
# Purpose:
#   List Voltus power and EMIR signoff tool version (eg. quantus/231/23.11.000)
#
# Logic:
#   - Parse input file: setup_vars.tcl
#   - Scan for MODULE_CMD variable assignments (QRC and VOLTUS)
#   - Extract tool names from set commands (QRC, VOLTUS)
#   - Parse module load commands within quoted strings
#   - Extract module name, major version, and full version string
#   - Handle special cases: QRC uses quantus/qrc module, VOLTUS uses voltus/ssv module
#   - Format output as tool_name/major_version/full_version
#   - Report all discovered tool versions as INFO items
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
class Check_3_0_0_04(InputFileParserMixin, OutputBuilderMixin, WaiverHandlerMixin, BaseChecker):
    """
    IMP-3-0-0-04: List Voltus power and EMIR signoff tool version (eg. quantus/231/23.11.000)
    
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
    FOUND_DESC_TYPE1_4 = "QRC and VOLTUS tool versions found in setup configuration"
    MISSING_DESC_TYPE1_4 = "Required QRC or VOLTUS tool version not found in setup configuration"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_DESC_TYPE2_3 = "All required QRC and VOLTUS tool versions matched in configuration"
    MISSING_DESC_TYPE2_3 = "Expected QRC or VOLTUS tool version pattern not satisfied in configuration"
    
    # All Types (waiver description unified)
    WAIVED_DESC = "Waived tool version mismatches"
    
    # ⭐ REASON CONSTANTS - Split by Type semantics (API-025)
    # ALL Types pass found_reason/missing_reason, but use different constants
    
    # Type 1/4: Boolean checks - emphasize "found/not found" (existence)
    FOUND_REASON_TYPE1_4 = "QRC and VOLTUS tool version information successfully extracted from setup_vars.tcl"
    MISSING_REASON_TYPE1_4 = "Required QRC or VOLTUS MODULE_CMD variable not found in setup_vars.tcl"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_REASON_TYPE2_3 = "Required QRC and VOLTUS tool version patterns matched and validated"
    MISSING_REASON_TYPE2_3 = "Expected QRC or VOLTUS tool version pattern not satisfied or missing from configuration"
    
    # Waiver-related (Type 3/4 only)
    WAIVED_BASE_REASON = "Tool version mismatch waived per design approval"
    UNUSED_WAIVER_REASON = "Waiver defined but no tool version violation matched"
    
    def __init__(self):
        """Initialize the checker."""
        super().__init__(
            check_module="3.0_TOOL_VERSION",
            item_id="IMP-3-0-0-04",
            item_desc="List Voltus power and EMIR signoff tool version (eg. quantus/231/23.11.000)"
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
        Parse input files to extract tool version information.
        
        Parses setup_vars.tcl to extract QRC and VOLTUS tool versions from
        MODULE_CMD variable assignments. Handles both quantus/qrc modules for QRC
        and voltus/ssv modules for VOLTUS.
        
        Returns:
            Dict with parsed data:
            - 'items': List[Dict] - Tool version items with metadata
            - 'metadata': Dict - File metadata
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
        
        # Patterns for extracting tool versions
        # Pattern 1: QRC module command (supports both quantus and qrc modules)
        qrc_pattern = re.compile(
            r'set\s+QRC\(MODULE_CMD\)\s+".*module\s+load\s+(?P<module>quantus|qrc)/(?P<major>\d+)/(?P<version>\S+)"',
            re.IGNORECASE
        )
        
        # Pattern 2: VOLTUS module command (supports both voltus and ssv modules)
        voltus_pattern = re.compile(
            r'set\s+VOLTUS\(MODULE_CMD\)\s+".*module\s+load\s+(?P<module>voltus|ssv)/(?P<major>\d+)/(?P<version>\S+)"',
            re.IGNORECASE
        )
        
        for file_path in valid_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line_num, line in enumerate(f, 1):
                        # Skip empty lines and comments
                        line = line.strip()
                        if not line or line.startswith('#'):
                            continue
                        
                        # Check for QRC module command
                        qrc_match = qrc_pattern.search(line)
                        if qrc_match:
                            module_name = qrc_match.group('module')
                            major_version = qrc_match.group('major')
                            full_version = qrc_match.group('version')
                            
                            # Format: quantus/231/23.10.000 (use module name from pattern)
                            tool_version = f"{module_name}/{major_version}/{full_version}"
                            
                            all_items.append({
                                'name': tool_version,
                                'tool': 'QRC',
                                'module': module_name,
                                'major_version': major_version,
                                'full_version': full_version,
                                'line_number': line_num,
                                'file_path': str(file_path)
                            })
                        
                        # Check for VOLTUS module command
                        voltus_match = voltus_pattern.search(line)
                        if voltus_match:
                            module_name = voltus_match.group('module')
                            major_version = voltus_match.group('major')
                            full_version = voltus_match.group('version')
                            
                            # Format: voltus/202/20.20.000 or ssv/202/20.20.000
                            tool_version = f"{module_name}/{major_version}/{full_version}"
                            
                            all_items.append({
                                'name': tool_version,
                                'tool': 'VOLTUS',
                                'module': module_name,
                                'major_version': major_version,
                                'full_version': full_version,
                                'line_number': line_num,
                                'file_path': str(file_path)
                            })
            
            except Exception as e:
                errors.append(f"Error parsing {file_path}: {str(e)}")
        
        # 3. Store frequently reused data on self
        self._parsed_items = all_items
        self._metadata = {
            'total_versions': len(all_items),
            'qrc_count': sum(1 for item in all_items if item['tool'] == 'QRC'),
            'voltus_count': sum(1 for item in all_items if item['tool'] == 'VOLTUS')
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
        
        Checks if QRC and VOLTUS tool versions exist in setup configuration.
        Does NOT use pattern_items for searching.
        
        Use OutputBuilderMixin.build_complete_output() for automatic formatting.
        
        Returns:
            CheckResult with is_pass based on check logic
        """
        # Parse input
        data = self._parse_input_files()
        items = data.get('items', [])
        errors = data.get('errors', [])
        
        # Check if we found both QRC and VOLTUS versions
        qrc_found = any(item['tool'] == 'QRC' for item in items)
        voltus_found = any(item['tool'] == 'VOLTUS' for item in items)
        
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
        
        # Determine missing items
        missing_items = []
        if not qrc_found:
            missing_items.append('QRC tool version (quantus or qrc module)')
        if not voltus_found:
            missing_items.append('VOLTUS tool version (voltus or ssv module)')
        
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
        
        # Find missing patterns (patterns not found in actual items)
        found_names = set(item['name'] for item in items)
        missing_items = [pattern for pattern in pattern_items if pattern not in found_names]
        
        # Find extra items (items found but not in pattern_items)
        pattern_set = set(pattern_items)
        extra_items = {
            name: metadata
            for name, metadata in found_items.items()
            if name not in pattern_set
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
        
        # Fix API-016: Use waivers.get() directly to preserve dict format
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # Get requirements
        pattern_items = self.item_data.get('requirements', {}).get('pattern_items', [])
        
        # Find violations (patterns not found in actual items)
        found_names = set(item['name'] for item in items)
        violations = [pattern for pattern in pattern_items if pattern not in found_names]
        
        # Separate waived/unwaived using template helper
        waived_items = []
        unwaived_items = []
        
        for violation in violations:
            if self.match_waiver_entry(violation, waive_dict):
                waived_items.append(violation)
            else:
                unwaived_items.append(violation)
        
        # Find unused waivers by checking if waiver names were used
        used_names = set(waived_items)
        unused_waivers = [name for name in waive_dict.keys() if name not in used_names]
        
        # Convert found items to dict with metadata
        found_items = {
            item['name']: {
                'name': item['name'],
                'line_number': item.get('line_number', 0),
                'file_path': item.get('file_path', 'N/A')
            }
            for item in items
        }
        
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
        
        # Fix API-016: Use waivers.get() directly to preserve dict format
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # Check if we found both QRC and VOLTUS versions
        qrc_found = any(item['tool'] == 'QRC' for item in items)
        voltus_found = any(item['tool'] == 'VOLTUS' for item in items)
        
        # Determine violations (missing tool versions)
        violations = []
        if not qrc_found:
            violations.append('QRC tool version (quantus or qrc module)')
        if not voltus_found:
            violations.append('VOLTUS tool version (voltus or ssv module)')
        
        # Separate waived/unwaived violations
        waived_items = []
        unwaived_items = []
        
        for violation in violations:
            if self.match_waiver_entry(violation, waive_dict):
                waived_items.append(violation)
            else:
                unwaived_items.append(violation)
        
        # Find unused waivers
        used_names = set(waived_items)
        unused_waivers = [name for name in waive_dict.keys() if name not in used_names]
        
        # Convert found items to dict with metadata
        found_items = {
            item['name']: {
                'name': item['name'],
                'line_number': item.get('line_number', 0),
                'file_path': item.get('file_path', 'N/A')
            }
            for item in items
        }
        
        # Fix API-021: Use missing_items parameter instead of unwaived_items
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
    checker = Check_3_0_0_04()
    checker.init_checker(Path(__file__))
    result = checker.execute_check()
    checker.write_output(result)
    return 0 if result.is_pass else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())