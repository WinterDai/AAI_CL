################################################################################
# Script Name: IMP-10-0-0-10.py
#
# Purpose:
#   Confirm check full path group timing reports (in2out/in2reg/reg2out/reg2out/reg2reg/default/cgdefault).
#
#
# Logic:
#   - Parse STA log to check for path group timing report commands
#   - Verify all 6 path groups exist: in2out/in2reg/reg2out/reg2reg/default/cgdefault
#   - Report missing path groups as violations
# Auto Type Detection:
#   Type 1: requirements.value=N/A, waivers.value=N/A/0 â†’ Boolean check
#   Type 2: requirements.value>0, pattern_items exists, waivers.value=N/A/0 â†’ Value comparison
#   Type 3: requirements.value>0, pattern_items exists, waivers.value>0 â†’ Value with waiver logic
#   Type 4: requirements.value=N/A, waivers.value>0 â†’ Boolean with waiver logic
#
# Author: yyin
# Date: 2025-12-08
# Refactored: 2025-12-08 (Using InputFileParserMixin template)
################################################################################

from pathlib import Path
import re
import sys
from typing import Dict, Any, List


# Add common module to path
_SCRIPT_DIR = Path(__file__).resolve().parent
_CHECK_MODULES_DIR = _SCRIPT_DIR.parents[2]  # Go up to Check_modules/
_COMMON_DIR = _CHECK_MODULES_DIR / 'common'
if str(_COMMON_DIR) not in sys.path:
    sys.path.insert(0, str(_COMMON_DIR))

from base_checker import BaseChecker, CheckResult, ConfigurationError
from output_formatter import DetailItem, Severity, create_check_result
from checker_templates.input_file_parser_template import InputFileParserMixin
from checker_templates.waiver_handler_template import WaiverHandlerMixin
from checker_templates.output_builder_template import OutputBuilderMixin


class Check_10_0_0_10(BaseChecker, InputFileParserMixin, WaiverHandlerMixin, OutputBuilderMixin):
    """
    IMP-10-0-0-10: Confirm check full path group timing reports (in2out/in2reg/reg2out/reg2reg/default/cgdefault).
    
    Checking Types:
    - Type 1: requirements=N/A, waivers=N/A/0 â†’ Informational/Boolean check
    - Type 2: requirements>0, waivers=N/A/0 â†’ Value check without waivers
    - Type 3: requirements>0, waivers>0 â†’ Value check with waiver logic
    - Type 4: requirements=N/A, waivers>0 â†’ Boolean check with waiver logic
    
    Uses InputFileParserMixin for log file parsing.
    Uses WaiverHandlerMixin for waiver processing.
    Uses OutputBuilderMixin for result construction.
    """
    
    def __init__(self):
        """Initialize the checker."""
        super().__init__(
            check_module="10.0_STA_DCD_CHECK",
            item_id="IMP-10-0-0-10",
            item_desc="Confirm check full path group timing reports (in2out/in2reg/reg2out/reg2reg/default/cgdefault)."
        )
        # Store parsed data and metadata
        self._path_groups_found: Dict[str, Dict[str, Any]] = {}
        self._required_groups = ['in2out', 'in2reg', 'reg2out', 'reg2reg', 'default', 'cgdefault']
    
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
        Parse STA log file to find path group timing report references.
        Uses InputFileParserMixin template for pattern matching.
        
        Returns:
            Dict with:
                - 'found_groups': Dict[group_name, metadata]
                - 'missing_groups': List[group_name]
                - 'log_file': Path to log file
        """
        # Validate input files
        valid_files, missing_files = self.validate_input_files()
        
        # Handle missing files
        if missing_files:
            raise ConfigurationError(
                self.create_missing_files_error(missing_files)
            )
        
        log_file = valid_files[0] if valid_files else None
        
        if not log_file:
            return {
                'found_groups': {},
                'missing_groups': self._required_groups.copy(),
                'log_file': None
            }
        
        # Use template method to parse path groups
        # Define patterns for each path group using template Pattern 1
        patterns = {}
        for group in self._required_groups:
            # Pattern: *_<group>_* or timing_<group> or -group <group>
            patterns[group] = rf'_{group}_|timing_{group}|-group\s+{group}|group\s+{group}|{group}\.(?:tar)?rpt'
        
        # Parse using template method (pass as string since template handles both)
        results = self.parse_log_with_patterns(
            log_file=log_file,  # Pass Path object directly
            patterns=patterns,
            extract_paths=True
        )
        
        # Convert to internal format
        self._path_groups_found = results['found']
        
        return {
            'found_groups': self._path_groups_found,
            'missing_groups': results['missing'],
            'log_file': str(log_file)
        }
    
    # =========================================================================
    # Type 1: Informational/Boolean Check
    # =========================================================================
    
    def _execute_type1(self) -> CheckResult:
        """
        Type 1: Informational check - verify all path groups exist in log.
        Uses OutputBuilderMixin for simplified output construction.
        
        Returns:
            CheckResult with PASS if all 6 groups found, FAIL otherwise
        """
        # Parse input
        data = self._parse_input_files()
        found_groups = data['found_groups']
        missing_groups = data['missing_groups']
        
        # Define name extractor
        def extract_report_path(name, metadata):
            return self.extract_path_after_delimiter(name, metadata, delimiter='>')
        
        # Determine description based on whether all groups found
        found_desc = "All path group reports mentioned in log need to be checked" if not missing_groups else "Required path group reports found and need to be checked"
        
        # Use OutputBuilderMixin to build complete result in one call
        return self.build_complete_output(
            found_items=found_groups,
            missing_items=missing_groups,
            value=len(found_groups),
            has_pattern_items=False,
            has_waiver_value=False,
            default_file=data.get('log_file', 'N/A'),
            name_extractor=extract_report_path,
            found_reason="Path group timing reports found in log",
            missing_reason="Path group timing reports NOT found in log",
            found_desc=found_desc,
            missing_desc="Missing reports required to be checked"
        )
    
    # =========================================================================
    # Type 2: Value Check (No Waivers)
    # =========================================================================
    
    def _execute_type2(self) -> CheckResult:
        """
        Type 2: Value check - verify specific path groups from pattern_items.
        Uses OutputBuilderMixin for simplified output construction.
        
        Returns:
            CheckResult comparing found count vs requirements.value
        """
        # Parse input
        data = self._parse_input_files()
        found_groups = data['found_groups']
        
        # Get requirements
        requirements = self.get_requirements()
        pattern_items = requirements.get('pattern_items', [])
        
        # Filter to only check pattern_items
        groups_to_check = pattern_items if pattern_items else self._required_groups
        
        # Filter found groups to only those in groups_to_check
        found_in_check = {k: v for k, v in found_groups.items() if k in groups_to_check}
        
        # Find missing groups
        missing_in_check = [g for g in groups_to_check if g not in found_groups]
        
        # Define name extractor
        def extract_report_path(name, metadata):
            return self.extract_path_after_delimiter(name, metadata, delimiter='>')
        
        # Use OutputBuilderMixin to build complete result in one call
        return self.build_complete_output(
            found_items=found_in_check,
            missing_items=missing_in_check,
            value=len(found_in_check),
            has_pattern_items=True,
            has_waiver_value=False,
            default_file=data.get('log_file', 'N/A'),
            name_extractor=extract_report_path,
            found_reason="Required path group reports found and need to be checked",
            missing_reason="Required Path group timing reports NOT found in log",
            found_desc="Required path group reports found and need to be checked",
            missing_desc="Missing reports required to be checked"
        )
    
    # =========================================================================
    # Type 3: Value Check with Waiver Logic
    # =========================================================================
    
    def _execute_type3(self) -> CheckResult:
        """
        Type 3: Value check with waiver support.
        Uses OutputBuilderMixin for simplified output construction.
        
        Returns:
            CheckResult with waiver logic - missing groups can be waived
        """
        # Parse input
        data = self._parse_input_files()
        found_groups = data['found_groups']
        
        # Get requirements and waivers
        requirements = self.get_requirements()
        waiver_config = self.get_waiver_config()
        pattern_items = requirements.get('pattern_items', [])
        waive_items_raw = waiver_config.get('waive_items', [])
        
        # Parse waivers
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # Groups to check
        groups_to_check = pattern_items if pattern_items else self._required_groups
        
        # Filter found groups to only those in groups_to_check
        found_in_check = {k: v for k, v in found_groups.items() if k in groups_to_check}
        
        # Classify missing groups
        missing_groups = [g for g in groups_to_check if g not in found_groups]
        waived_missing, unwaived_missing = self.classify_items_by_waiver(
            all_items=missing_groups,
            waive_dict=waive_dict
        )
        
        # Find unused waivers
        unused_waivers = self.find_unused_waivers(
            waive_dict=waive_dict,
            items_found=missing_groups
        )
        
        # Define name extractor for report file paths
        def extract_report_path(name, metadata):
            return self.extract_path_after_delimiter(name, metadata, delimiter='>')
        
        # Use OutputBuilderMixin to build complete result in one call
        return self.build_complete_output(
            found_items=found_in_check,
            missing_items=unwaived_missing,
            waived_items=waived_missing,
            unused_waivers=unused_waivers,
            waive_dict=waive_dict,
            value=len(found_in_check),
            has_pattern_items=True,
            has_waiver_value=True,
            default_file=data.get('log_file', 'N/A'),
            name_extractor=extract_report_path,
            found_reason="Path group found in log",
            missing_reason="Required Path group timing reports NOT found in log (not waived)",
            waived_base_reason="Required Path group timing reports NOT found in log",
            unused_waiver_reason="Waived but Path group timing reports found in log",
            found_desc="Required path group reports found and need to be checked",
            missing_desc="Missing reports required to be checked",
            waived_desc="The missing reports can be waived",
            unused_desc="Unused waivers currently"
        )
    
    # =========================================================================
    # Type 4: Boolean Check with Waiver Logic
    # =========================================================================
    
    def _execute_type4(self) -> CheckResult:
        """
        Type 4: Boolean check with waiver support.
        Uses OutputBuilderMixin for simplified output construction.
        
        Returns:
            CheckResult with waiver logic applied
        """
        # Parse input
        data = self._parse_input_files()
        found_groups = data['found_groups']
        missing_groups = data['missing_groups']
        
        # Get waivers
        waiver_config = self.get_waiver_config()
        waive_items_raw = waiver_config.get('waive_items', [])
        
        # Parse waivers
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # Classify missing groups
        waived_missing, unwaived_missing = self.classify_items_by_waiver(
            all_items=missing_groups,
            waive_dict=waive_dict
        )
        
        # Find unused waivers
        unused_waivers = self.find_unused_waivers(
            waive_dict=waive_dict,
            items_found=missing_groups
        )
        
        # Define name extractor
        def extract_report_path(name, metadata):
            return self.extract_path_after_delimiter(name, metadata, delimiter='>')
        
        # Use OutputBuilderMixin to build complete result in one call
        return self.build_complete_output(
            found_items=found_groups,
            missing_items=unwaived_missing,
            waived_items=waived_missing,
            unused_waivers=unused_waivers,
            waive_dict=waive_dict,
            value="N/A",
            has_pattern_items=False,
            has_waiver_value=True,
            default_file=data.get('log_file', 'N/A'),
            name_extractor=extract_report_path,
            found_reason="Required path group reports found and need to be checked",
            missing_reason="Path group timing reports NOT found in log (not waived)",
            waived_base_reason="Path group timing reports NOT found in log",
            unused_waiver_reason="Waived but Required path group reports found and need to be checked",
            found_desc="Required path group reports found and need to be checked",
            missing_desc="Missing reports required to be checked",
            waived_desc="The missing reports can be waived",
            unused_desc="Unused waivers currently"
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
    checker = Check_10_0_0_10()
    checker.init_checker(Path(__file__))
    result = checker.execute_check()
    checker.write_output(result)
    return 0 if result.is_pass else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())

