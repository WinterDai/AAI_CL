################################################################################
# Script Name: IMP-14-0-0-02.py
#
# Purpose:
#   Confirm connect the PSO chain correctly. (Fill N/A if no PSO)
#
# Logic:
#   - TODO: Parse [input_file_name] to extract [specific_data/patterns]
#   - TODO: Extract [metadata/settings/constraints] from parsed content
#   - TODO: Verify [condition/existence/consistency] against [requirements/expected_values]
#   - TODO: [Optional] Support waiver for [specific_cases]
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
class Check_14_0_0_02(InputFileParserMixin, OutputBuilderMixin, WaiverHandlerMixin, BaseChecker):
    """
    IMP-14-0-0-02: Confirm connect the PSO chain correctly. (Fill N/A if no PSO)
    
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
    
    def __init__(self):
        """Initialize the checker."""
        super().__init__(
            check_module="14.0_CLP_CHECK",
            item_id="IMP-14-0-0-02",
            item_desc="Confirm connect the PSO chain correctly. (Fill N/A if no PSO)"
        )
        # TODO: Add custom member variables for parsed data
        # Example: self._parsed_data: Dict[str, Any] = {}
        # Example: self._metadata: Dict[str, str] = {}
    
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
        Parse input files to extract relevant data.
        
        TODO: Implement specific parsing logic based on input file format
        
        RECOMMENDED: Use InputFileParserMixin helper methods:
        - parse_log_with_patterns(file, patterns) - Pattern matching (7 modes)
        - extract_file_references(file, extensions) - File reference extraction
        - normalize_command(cmd) - Command normalization for matching
        
        Returns:
            Dict with parsed data, typically includes:
            - 'items': List[Dict] - Main items to check (with metadata: line_number, file_path)
            - 'metadata': Dict - File metadata (tool version, date, design name, etc.)
            - 'errors': List - Any parsing errors encountered
            - 'warnings': List - Any parsing warnings
        
        Example using template helpers:
            valid_files = self.validate_input_files()
            if missing_files:
                raise ConfigurationError(
                    self.create_missing_files_error(missing_files)
                )
            
            items = []
            for file_path in valid_files:
                lines = self.read_file(file_path)
                for line_num, line in enumerate(lines, 1):
                    # Pattern matching example
                    match = re.search(r'ERROR:\s+(.+)', line)
                    if match:
                        items.append({
                            'name': match.group(1),
                            'line_number': line_num,
                            'file_path': str(file_path),
                            'line_content': line.strip()
                        })
            
            return {
                'items': items,
                'metadata': {},
                'errors': []
            }
        """
        # 1. Validate input files (raises ConfigurationError if missing)
        valid_files = self.validate_input_files()
        if not valid_files:
            raise ConfigurationError("No valid input files found")
        
        # TODO: Implement your parsing logic here
        # Template structure
        items = []
        metadata = {}
        errors = []
        
        # 2. Option A: Use parse_log_with_patterns (recommended)
        # patterns = {
        #     'error_pattern': r'\*\*ERROR:\s*\(([A-Z]+-\d+)\)',
        #     'warning_pattern': r'\*\*WARNING:\s*(.+)'
        # }
        # for file_path in valid_files:
        #     result = self.parse_log_with_patterns(file_path, patterns)
        #     items.extend(result.get('error_pattern', []))
        
        # 2. Option B: Manual parsing with normalization
        for file_path in valid_files:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line_num, line in enumerate(f, 1):
                    # TODO: Add your pattern matching logic
                    # match = re.search(r'YOUR_PATTERN', line)
                    # if match:
                    #     items.append({
                    #         'name': match.group(1),
                    #         'line_number': line_num,
                    #         'file_path': str(file_path)
                    #     })
                    pass
        
        # 3. Store frequently reused data on self
        self._parsed_items = items
        
        return {
            'items': items,
            'metadata': metadata,
            'errors': errors
        }
    
    # =========================================================================
    # Type 1: Boolean Check
    # =========================================================================
    
    def _execute_type1(self) -> CheckResult:
        """
        Type 1: Boolean Check.
        
        Custom boolean validation (file exists? config valid?).
        Does NOT use pattern_items for searching.
        
        Use OutputBuilderMixin.build_complete_output() for automatic formatting.
        
        Returns:
            CheckResult with is_pass based on check logic
        """
        # Parse input
        data = self._parse_input_files()
        items = data.get('items', [])
        
        # TODO: Implement your check logic
        # Example: Check if certain items exist
        found_items = items if len(items) > 0 else []
        missing_items = [] if len(items) > 0 else ['Expected item']
        
        # Use template helper for automatic output formatting
        return self.build_complete_output(
            found_items=found_items,
            missing_items=missing_items,
            item_desc=self.item_desc
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
        
        # TODO: Implement check logic - compare actual vs expected
        extra_items = [i for i in items if i not in pattern_items]
        
        # Use template helper (auto-handles waiver=0)
        return self.build_complete_output(
            found_items=items,
            extra_items=extra_items,
            item_desc=self.item_desc
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
        
        # Parse waiver configuration using template helper
        waive_items_raw = self.get_waive_items()
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # TODO: Implement your check logic
        # Example: Find violations/errors in parsed data
        violations = []  # List of violation names
        
        # Separate waived/unwaived using template helper
        waived_items = []
        unwaived_items = []
        
        for violation in violations:
            if self.match_waiver_entry(violation, waive_dict):
                waived_items.append(violation)
            else:
                unwaived_items.append(violation)
        
        # Find unused waivers
        used_names = set(w.get('name') for w in waived_items)
        unused_waivers = [w for w in waive_dict.values() if w['name'] not in used_names]
        
        # Use template helper for automatic output formatting
        return self.build_complete_output(
            waived_items=waived_items,
            unwaived_items=unwaived_items,
            waive_dict=waive_dict,
            unused_waivers=unused_waivers,
            item_desc=self.item_desc
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
        
        # Parse waiver configuration
        waive_items_raw = self.get_waive_items()
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # TODO: Implement boolean check logic
        # Example: Check if violations exist
        
        # Use template helper (auto-handles waiver=0)
        return self.build_complete_output(
            found_items=items,
            waive_dict=waive_dict,
            has_waiver_value=True,
            item_desc=self.item_desc
        )
    
    # =========================================================================
    # Helper Methods (Optional - Add as needed)
    # =========================================================================
    
    def _matches_waiver(self, item: str, waive_patterns: List[str]) -> bool:
        """
        Check if item matches any waiver pattern.
        
        TODO: Optional - Implement waiver matching logic
        
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
    checker = Check_14_0_0_02()
    checker.init_checker(Path(__file__))
    result = checker.execute_check()
    checker.write_output(result)
    return 0 if result.is_pass else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())
