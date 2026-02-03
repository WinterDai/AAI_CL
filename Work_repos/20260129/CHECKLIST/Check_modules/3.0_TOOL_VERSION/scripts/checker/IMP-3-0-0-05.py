################################################################################
# Script Name: IMP-3-0-0-05.py
#
# Purpose:
#   List Pegasus physical signoff tool version (eg. pegasus/232/23.25.000)
#
# Logic:
#   - Parse input file: setup_vars.tcl
#   - Extract MODULE_CMD variable definitions for PVS, PEGASUS, and MVS tools
#   - Search for 'module load pegasus/XXX/YY.YY.YYY' patterns within MODULE_CMD strings
#   - Extract Pegasus version path components (major version and full version)
#   - Validate version string format matches pegasus/XXX/YY.YY.YYY pattern
#   - Check consistency if Pegasus appears in multiple MODULE_CMD contexts
#   - Report extracted version information with source file and line number
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
class Check_3_0_0_05(InputFileParserMixin, OutputBuilderMixin, WaiverHandlerMixin, BaseChecker):
    """
    IMP-3-0-0-05: List Pegasus physical signoff tool version (eg. pegasus/232/23.25.000)
    
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
    FOUND_DESC_TYPE1_4 = "Pegasus tool version found in setup configuration"
    MISSING_DESC_TYPE1_4 = "Pegasus tool version not found in setup configuration"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_DESC_TYPE2_3 = "Pegasus version pattern matched in MODULE_CMD"
    MISSING_DESC_TYPE2_3 = "Expected Pegasus version pattern not satisfied"
    
    # All Types (waiver description unified)
    WAIVED_DESC = "Waived Pegasus version configuration"
    
    # ⭐ REASON CONSTANTS - Split by Type semantics (API-025)
    # ALL Types pass found_reason/missing_reason, but use different constants
    
    # Type 1/4: Boolean checks - emphasize "found/not found" (existence)
    FOUND_REASON_TYPE1_4 = "Pegasus tool version found in MODULE_CMD configuration"
    MISSING_REASON_TYPE1_4 = "Pegasus tool version not found in setup_vars.tcl"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_REASON_TYPE2_3 = "Pegasus version pattern matched and validated"
    MISSING_REASON_TYPE2_3 = "Expected Pegasus version pattern not satisfied or missing"
    
    # Waiver-related (Type 3/4 only)
    WAIVED_BASE_REASON = "Pegasus version configuration waived per design approval"
    UNUSED_WAIVER_REASON = "Waiver defined but no violation matched"
    
    def __init__(self):
        """Initialize the checker."""
        super().__init__(
            check_module="3.0_TOOL_VERSION",
            item_id="IMP-3-0-0-05",
            item_desc="List Pegasus physical signoff tool version (eg. pegasus/232/23.25.000)"
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
        Parse input files to extract Pegasus version information.
        
        Parses setup_vars.tcl to find MODULE_CMD definitions containing
        'module load pegasus/XXX/YY.YY.YYY' patterns.
        
        Returns:
            Dict with parsed data:
            - 'items': List[Dict] - Pegasus version entries with metadata
            - 'metadata': Dict - Parsing metadata (total count, contexts found)
            - 'errors': List - Any parsing errors encountered
        """
        # 1. Validate input files (returns TUPLE: valid_files, missing_files)
        valid_files, missing_files = self.validate_input_files()
        
        # Fix LOGIC-001: Explicitly check for empty list
        if not valid_files or len(valid_files) == 0:
            raise ConfigurationError(
                self.create_missing_files_error(missing_files if missing_files else ["No input files configured"])
            )
        
        if missing_files:
            raise ConfigurationError(
                self.create_missing_files_error(missing_files)
            )
        
        # 2. Parse files for Pegasus version patterns
        items = []
        contexts_found = set()
        errors = []
        
        # Patterns to match MODULE_CMD definitions with Pegasus versions
        # Pattern matches: set TOOL(MODULE_CMD) "...module load pegasus/XXX/YY.YY.YYY..."
        patterns = {
            'pvs_module': r'set\s+PVS\(MODULE_CMD\)\s+"([^"]*module\s+load\s+pegasus/\d+/\S+[^"]*)"',
            'pegasus_module': r'set\s+PEGASUS\(MODULE_CMD\)\s+"([^"]*module\s+load\s+pegasus/\d+/\S+[^"]*)"',
            'mvs_module': r'set\s+MVS\(MODULE_CMD\)\s+"([^"]*module\s+load\s+pegasus/\d+/\S+[^"]*)"'
        }
        
        # Version extraction pattern (within MODULE_CMD strings)
        version_pattern = r'module\s+load\s+pegasus/(\d+)/(\S+)'
        
        for file_path in valid_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line_num, line in enumerate(f, 1):
                        # Skip comments and empty lines
                        stripped_line = line.strip()
                        if not stripped_line or stripped_line.startswith('#'):
                            continue
                        
                        # Check each MODULE_CMD pattern
                        for context, pattern in patterns.items():
                            match = re.search(pattern, line)
                            if match:
                                module_cmd_string = match.group(1)
                                
                                # Extract version from module load command
                                version_match = re.search(version_pattern, module_cmd_string)
                                if version_match:
                                    major_version = version_match.group(1)
                                    full_version = version_match.group(2)
                                    version_path = f"pegasus/{major_version}/{full_version}"
                                    
                                    # Determine context name
                                    context_name = context.replace('_module', '').upper()
                                    contexts_found.add(context_name)
                                    
                                    items.append({
                                        'name': version_path,
                                        'context': context_name,
                                        'major_version': major_version,
                                        'full_version': full_version,
                                        'line_number': line_num,
                                        'file_path': str(file_path),
                                        'line_content': line.strip()
                                    })
            except Exception as e:
                errors.append(f"Error parsing {file_path}: {str(e)}")
        
        # 3. Store frequently reused data on self
        self._parsed_items = items
        self._metadata = {
            'total_versions': len(items),
            'contexts_found': list(contexts_found),
            'unique_versions': len(set(item['name'] for item in items))
        }
        
        return {
            'items': items,
            'metadata': self._metadata,
            'errors': errors
        }
    
    # =========================================================================
    # Type 1: Boolean Check
    # =========================================================================
    
    def _execute_type1(self) -> CheckResult:
        """
        Type 1: Boolean Check.
        
        Checks if Pegasus version exists in setup configuration.
        Does NOT use pattern_items for searching.
        
        Returns:
            CheckResult with is_pass based on version existence
        """
        # Parse input
        data = self._parse_input_files()
        items = data.get('items', [])
        errors = data.get('errors', [])
        
        # Check if any Pegasus version was found
        if items:
            # Convert to dict format with metadata for output
            found_items = {}
            for item in items:
                key = f"{item['context']}: {item['name']}"
                found_items[key] = {
                    'name': key,
                    'line_number': item['line_number'],
                    'file_path': item['file_path']
                }
            
            missing_items = []
        else:
            found_items = {}
            missing_items = ['Pegasus version in MODULE_CMD']
        
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
            CheckResult with is_pass based on pattern matching
        """
        # Parse input
        data = self._parse_input_files()
        items = data.get('items', [])
        
        # Get requirements
        pattern_items = self.item_data.get('requirements', {}).get('pattern_items', [])
        
        # Extract found version paths
        found_versions = set(item['name'] for item in items)
        
        # Compare against expected patterns
        found_items = {}
        missing_items = []
        
        for pattern in pattern_items:
            # Check if pattern matches any found version
            matched = False
            for item in items:
                if self._matches_pattern(item['name'], pattern):
                    key = f"{item['context']}: {item['name']}"
                    found_items[key] = {
                        'name': key,
                        'line_number': item['line_number'],
                        'file_path': item['file_path']
                    }
                    matched = True
                    break
            
            if not matched:
                missing_items.append(pattern)
        
        # Check for extra items not in pattern_items
        extra_items = {}
        for item in items:
            if not any(self._matches_pattern(item['name'], pattern) for pattern in pattern_items):
                key = f"{item['context']}: {item['name']}"
                extra_items[key] = {
                    'name': key,
                    'line_number': item['line_number'],
                    'file_path': item['file_path']
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
        
        # Convert items to dict with metadata for found_items
        found_items = {
            item['name']: {
                'name': item['name'],
                'line_number': item.get('line_number', 0),
                'file_path': item.get('file_path', 'N/A')
            }
            for item in items
        }
        
        # Find missing patterns (violations)
        missing_patterns = []
        for pattern in pattern_items:
            matched = False
            for item in items:
                if self._matches_pattern(item['name'], pattern):
                    matched = True
                    break
            if not matched:
                missing_patterns.append(pattern)
        
        # Separate waived/unwaived using template helper
        waived_items = []
        unwaived_items = []
        
        for pattern in missing_patterns:
            if self.match_waiver_entry(pattern, waive_dict):
                waived_items.append(pattern)
            else:
                unwaived_items.append(pattern)
        
        # Find unused waivers
        used_names = set(waived_items)
        unused_waivers = [name for name in waive_dict.keys() if name not in used_names]
        
        # Fix API-021: Use missing_items parameter instead of unwaived_items
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
        items = data.get('items', [])
        
        # Fix API-016: Use waivers.get() directly to preserve dict format
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # Check if Pegasus version exists
        if items:
            # Convert to dict format
            found_items = {}
            for item in items:
                key = f"{item['context']}: {item['name']}"
                found_items[key] = {
                    'name': key,
                    'line_number': item['line_number'],
                    'file_path': item['file_path']
                }
            
            waived_items = []
            unwaived_items = []
        else:
            # No version found - check if waived
            violation = 'Pegasus version not found'
            if self.match_waiver_entry(violation, waive_dict):
                waived_items = [violation]
                unwaived_items = []
            else:
                waived_items = []
                unwaived_items = [violation]
            
            found_items = {}
        
        # Find unused waivers
        used_names = set(waived_items)
        unused_waivers = [name for name in waive_dict.keys() if name not in used_names]
        
        # Fix API-021: Use missing_items parameter instead of unwaived_items
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
    
    def _matches_pattern(self, version: str, pattern: str) -> bool:
        """
        Check if version matches pattern (supports wildcards).
        
        Args:
            version: Version string to check (e.g., "pegasus/232/23.25.000")
            pattern: Pattern to match against (supports * wildcards)
            
        Returns:
            True if version matches pattern
        """
        # Support wildcards
        if '*' in pattern:
            regex_pattern = pattern.replace('*', '.*')
            return bool(re.search(f'^{regex_pattern}$', version, re.IGNORECASE))
        
        # Exact match
        return pattern.lower() == version.lower()


# =========================================================================
# Entry Point
# =========================================================================

def main():
    """Main entry point."""
    checker = Check_3_0_0_05()
    checker.init_checker(Path(__file__))
    result = checker.execute_check()
    checker.write_output(result)
    return 0 if result.is_pass else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())