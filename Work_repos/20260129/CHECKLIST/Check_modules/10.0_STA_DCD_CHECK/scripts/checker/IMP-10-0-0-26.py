################################################################################
# Script Name: IMP-10-0-0-26.py
#
# Purpose:
#   Confirm check_design report has no issue.
#
# Logic:
#   - Parse input files: check_design_func.rpt
#   - Identify main sections delimited by "=============================="
#   - Extract subsections delimited by "------------------------------"
#   - Parse 16 violation categories with their counts/percentages
#   - Extract violation details (port names, net names, instance paths)
#   - Classify results: count=0 or 100% coverage → clean, count>0 or <100% → violations
#   - Determine PASS/FAIL: PASS if all 16 categories clean, FAIL if any violations
#
# Auto Type Detection:
#   Type 1: requirements.value=N/A, waivers.value=N/A/0 → Boolean check
#   Type 2: requirements.value>0, pattern_items exists, waivers.value=N/A/0 → Value comparison
#   Type 3: requirements.value>0, pattern_items exists, waivers.value>0 → Value with waiver logic
#   Type 4: requirements.value=N/A, waivers.value>0 → Boolean with waiver logic
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
# Date: 2025-12-17
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
class Check_10_0_0_26(InputFileParserMixin, OutputBuilderMixin, WaiverHandlerMixin, BaseChecker):
    """
    IMP-10-0-0-26: Confirm check_design report has no issue.
    
    Checking Types:
    - Type 1: requirements=N/A, waivers=N/A/0 → Informational/Boolean check
    - Type 2: requirements>0, waivers=N/A/0 → Value check without waivers
    - Type 3: requirements>0, waivers>0 → Value check with waiver logic
    - Type 4: requirements=N/A, waivers=>0 → Boolean check with waiver logic
    
    Template Library v1.1.0:
    - Uses InputFileParserMixin for parsing (parse_log_with_patterns, normalize_command)
    - Uses WaiverHandlerMixin for waiver processing (parse_waive_items(waive_items_raw), match_waiver_entry(item, waive_dict))
    - Uses OutputBuilderMixin for result construction (build_complete_output(...))
    """
    
    # =========================================================================
    # UNIFIED DESCRIPTIONS - MUST be identical across ALL Type 1/2/3/4
    # =========================================================================
    FOUND_DESC = "Physical design verification clean"
    MISSING_DESC = "Physical design verification failed"
    WAIVED_DESC = "Waived check_design violations"
    FOUND_REASON = "All check_design categories passed with no violations"
    MISSING_REASON = "check_design violations detected in one or more categories"
    WAIVED_BASE_REASON = "check_design violation waived per design team approval"
    
    # 16 violation categories to check
    VIOLATION_CATEGORIES = [
        "Cells with missing Timing data",
        "Annotation to Verilog Netlist",
        "Annotation to Physical Netlist",
        "Floating Ports",
        "Ports Connect to multiple Pads",
        "Output pins connected to Power Ground net",
        "Floating Instance terminals",
        "Tie Hi/Lo output terms floating",
        "Output term shorted to Power Ground net",
        "Nets with tri-state driver",
        "Nets with parallel drivers",
        "Nets with multiple drivers",
        "Nets with no driver (No FanIn)",
        "Tie Hi/Lo instances connected to output",
        "Verilog nets with multiple drivers",
        "Dont use cells in design"
    ]
    
    def __init__(self):
        """Initialize the checker."""
        super().__init__(
            check_module="10.0_STA_DCD_CHECK",
            item_id="IMP-10-0-0-26",
            item_desc="Confirm check_design report has no issue."
        )
        # Store parsed category results
        self._category_results: Dict[str, Dict[str, Any]] = {}
        self._default_file: str = "N/A"
    
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
        Parse check_design report to extract violation categories and counts.
        
        Returns:
            Dict with parsed data:
            - 'clean_items': Dict[str, Dict] - Categories with no violations
            - 'violations': Dict[str, Dict] - Categories with violations
            - 'metadata': Dict - File metadata
            - 'default_file': str - Default file path for reporting
        """
        # 1. Validate input files - IMPORTANT: returns tuple (valid_files_list, missing_files_list)
        valid_files, missing_files = self.validate_input_files()
        
        # Fix: Explicitly check for empty list
        if not valid_files or len(valid_files) == 0:
            raise ConfigurationError(
                self.create_missing_files_error(missing_files if missing_files else ["No input files configured"])
            )
        
        if missing_files:
            raise ConfigurationError(
                self.create_missing_files_error(missing_files)
            )
        
        # 2. Parse check_design report
        clean_items = {}
        violations = {}
        
        for file_path in valid_files:
            self._default_file = str(file_path)
            
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                
                # Parse using state machine to track sections
                current_section = None
                current_subsection = None
                line_num = 0
                
                i = 0
                while i < len(lines):
                    line = lines[i]
                    line_num = i + 1
                    
                    # Detect main section headers (==============================)
                    if re.match(r'^={30,}\s*$', line):
                        if i + 2 < len(lines):
                            section_name = lines[i + 1].strip()
                            # Only treat as section if next line is also ====== AND
                            # the middle line doesn't look like a metric (has : followed by number)
                            is_metric_line = re.match(r'.+:\s*\d+', section_name)
                            if section_name and re.match(r'^={30,}\s*$', lines[i + 2]) and not is_metric_line:
                                current_section = section_name
                                i += 2
                                continue
                    
                    # Detect subsection headers (-------------------------------)
                    if re.match(r'^\s+-{30,}\s*$', line):
                        if i + 2 < len(lines):
                            subsection_name = lines[i + 1].strip()
                            if subsection_name and re.match(r'^\s+-{30,}\s*$', lines[i + 2]):
                                current_subsection = subsection_name
                                i += 2
                                continue
                    
                    # Parse metric lines for violation counts
                    # Pattern 1: "Category name: count" or "Category name: percentage%"
                    metric_match = re.match(r'^\s*([A-Za-z][A-Za-z0-9 /()-]+?):\s*(\d+%?|\d+\.\d+%)', line.strip())
                    # Pattern 2: "Category name  count" (two or more spaces before number, no colon)
                    metric_nocolon_match = re.match(r'^\s*([A-Za-z][A-Za-z0-9 /()-]+?)\s{2,}(\d+)', line.strip())
                    
                    category = None
                    value_str = None
                    
                    if metric_match:
                        category = metric_match.group(1).strip()
                        value_str = metric_match.group(2).strip()
                    elif metric_nocolon_match:
                        category = metric_nocolon_match.group(1).strip()
                        value_str = metric_nocolon_match.group(2).strip()
                    
                    if category and value_str:
                        # Check if this is one of our tracked categories
                        if category in self.VIOLATION_CATEGORIES:
                            # Parse count or percentage
                            if '%' in value_str:
                                # Percentage check (e.g., "100%" = clean, "<100%" = violation)
                                percentage = float(value_str.rstrip('%'))
                                count = 0 if percentage == 100.0 else 1
                                display_value = value_str
                            else:
                                # Count check
                                count = int(value_str)
                                display_value = f"{count} occurrences"
                            
                            item_name = f"{category} ({display_value})"
                            item_data = {
                                'name': item_name,
                                'category': category,
                                'count': count,
                                'line_number': line_num,
                                'file_path': str(file_path)
                            }
                            
                            # Classify as clean or violation
                            if count == 0:
                                clean_items[item_name] = item_data
                            else:
                                violations[item_name] = item_data
                    
                    i += 1
                
            except Exception as e:
                raise ConfigurationError(f"Error parsing {file_path}: {str(e)}")
        
        # 3. Store on self
        self._category_results = {
            'clean_items': clean_items,
            'violations': violations
        }
        
        # 4. Return aggregated dict
        return {
            'clean_items': clean_items,
            'violations': violations,
            'metadata': {
                'total_categories': len(clean_items) + len(violations),
                'clean_count': len(clean_items),
                'violation_count': len(violations)
            },
            'default_file': self._default_file
        }
    
    # =========================================================================
    # Type 1: Informational/Boolean Check
    # =========================================================================
    
    def _execute_type1(self) -> CheckResult:
        """
        Type 1: Boolean check - all categories must be clean (no waivers).
        
        Returns:
            CheckResult with is_pass based on check logic
        """
        # Parse input
        data = self._parse_input_files()
        clean_items = data.get('clean_items', {})
        violations = data.get('violations', {})
        
        # Type 1: violations are missing_items (semantic failures)
        return self.build_complete_output(
            found_items=clean_items,
            missing_items=violations,
            found_desc=self.FOUND_DESC,
            missing_desc=self.MISSING_DESC,
            found_reason=self.FOUND_REASON,
            missing_reason=self.MISSING_REASON
        )
    
    # =========================================================================
    # Type 2: Value comparison
    # =========================================================================
    
    def _execute_type2(self) -> CheckResult:
        """
        Type 2: Value comparison check - match specific categories (no waivers).
        
        Returns:
            CheckResult with is_pass based on value comparison
        """
        # Parse input
        data = self._parse_input_files()
        clean_items = data.get('clean_items', {})
        violations = data.get('violations', {})
        
        # Get requirements
        requirements = self.item_data.get('requirements', {})
        pattern_items = requirements.get('pattern_items', [])
        expected_value = requirements.get('value', 'N/A')
        
        # Match patterns against clean items using EXACT MATCH strategy
        # (pattern_items contain exact category names to verify)
        found_items = {}
        missing_patterns = {}
        
        for pattern in pattern_items:
            matched = False
            
            # First check clean items
            for item_name, item_data in clean_items.items():
                category = item_data.get('category', '')
                # EXACT MATCH (case-insensitive)
                if pattern.lower() == category.lower():
                    found_items[item_name] = item_data
                    matched = True
                    break
            
            # If not found in clean, check violations
            if not matched:
                for item_name, item_data in violations.items():
                    category = item_data.get('category', '')
                    if pattern.lower() == category.lower():
                        missing_patterns[item_name] = item_data
                        matched = True
                        break
            
            # If still not found, add as missing
            if not matched:
                missing_patterns[pattern] = {
                    'name': pattern,
                    'line_number': 0,
                    'file_path': data.get('default_file', 'N/A')
                }
        
        actual_count = len(found_items)
        
        return self.build_complete_output(
            found_items=found_items,
            missing_items=missing_patterns,
            found_desc=f"{self.FOUND_DESC} ({actual_count}/{expected_value})",
            missing_desc=f"{self.MISSING_DESC} ({len(missing_patterns)} patterns not clean)",
            found_reason=self.FOUND_REASON,
            missing_reason=self.MISSING_REASON
        )
    
    # =========================================================================
    # Type 3: Value Check with Waiver Logic
    # =========================================================================
    
    def _execute_type3(self) -> CheckResult:
        """
        Type 3: Value comparison with waiver support.
        
        Uses WaiverHandlerMixin for waiver processing.
        Uses OutputBuilderMixin for result construction.
        
        Returns:
            CheckResult with FAIL for unwaived, INFO for waived items
        """
        # Parse input
        data = self._parse_input_files()
        clean_items = data.get('clean_items', {})
        violations = data.get('violations', {})
        
        # Get requirements and waivers
        requirements = self.item_data.get('requirements', {})
        pattern_items = requirements.get('pattern_items', [])
        
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # Track pattern satisfaction
        found_clean = {}      # Patterns satisfied by clean items
        found_waived = {}     # Patterns satisfied by waived violations
        missing_patterns = {} # Patterns with unwaived violations
        other_waived = {}     # Waived violations NOT in pattern_items (for info)
        used_waiver_patterns = set()
        
        # Check each required pattern
        for pattern in pattern_items:
            pattern_satisfied = False
            
            # Check if pattern has clean match
            for item_name, item_data in clean_items.items():
                category = item_data.get('category', '')
                # EXACT MATCH (case-insensitive)
                if pattern.lower() == category.lower():
                    found_clean[item_name] = item_data
                    pattern_satisfied = True
                    break
            
            # If not clean, check if pattern has waived violation
            if not pattern_satisfied:
                for item_name, item_data in violations.items():
                    category = item_data.get('category', '')
                    if pattern.lower() == category.lower():
                        # Check if waived
                        matched_waiver = None
                        for waiver_pattern in waive_dict.keys():
                            if self.match_waiver_entry(item_name, {waiver_pattern: waive_dict[waiver_pattern]}):
                                matched_waiver = waiver_pattern
                                used_waiver_patterns.add(waiver_pattern)
                                break
                        
                        if matched_waiver:
                            found_waived[item_name] = item_data
                            pattern_satisfied = True
                        else:
                            missing_patterns[item_name] = item_data
                        break
        
        # Track other waived violations (not in pattern_items, for info only)
        for item_name, item_data in violations.items():
            category = item_data.get('category', '')
            is_pattern_violation = any(pattern.lower() == category.lower() for pattern in pattern_items)
            
            if not is_pattern_violation:
                for waiver_pattern in waive_dict.keys():
                    if self.match_waiver_entry(item_name, {waiver_pattern: waive_dict[waiver_pattern]}):
                        used_waiver_patterns.add(waiver_pattern)
                        other_waived[item_name] = item_data
                        break
        
        # Find unused waivers
        unused_waivers = {
            w: {
                'name': w,
                'line_number': 0,
                'file_path': data.get('default_file', 'N/A'),
                'reason': waive_dict[w]
            }
            for w in waive_dict.keys()
            if w not in used_waiver_patterns
        }
        
        # Build output
        all_waived = {**found_waived, **other_waived}
        
        return self.build_complete_output(
            found_items=found_clean,
            missing_items=missing_patterns,
            waived_items=all_waived,
            unused_waivers=unused_waivers,
            waive_dict=waive_dict,
            found_desc=f"Required patterns satisfied: {len(found_clean)}/{len(pattern_items)}",
            missing_desc="Required patterns with unwaived violations",
            waived_desc=self.WAIVED_DESC,
            found_reason=self.FOUND_REASON,
            missing_reason=self.MISSING_REASON,
            waived_base_reason=self.WAIVED_BASE_REASON
        )
    
    # =========================================================================
    # Type 4: Boolean Check with Waiver Logic
    # =========================================================================
    
    def _execute_type4(self) -> CheckResult:
        """
        Type 4: Boolean check with waiver support.
        
        Global check of all violations with waiver logic:
        - Clean items → found_items
        - Waived violations → waived_items
        - Unwaived violations → missing_items (FAIL)
        
        Returns:
            CheckResult with waiver logic applied
        """
        # Parse input
        data = self._parse_input_files()
        clean_items = data.get('clean_items', {})
        all_violations = data.get('violations', {})
        
        # Parse waivers
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # Apply waivers to violations
        waived_items = {}
        unwaived_items = {}
        used_waiver_patterns = set()
        
        for item_name, item_data in all_violations.items():
            # Check if this violation matches any waiver
            matched_waiver = None
            for waiver_pattern in waive_dict.keys():
                if self.match_waiver_entry(item_name, {waiver_pattern: waive_dict[waiver_pattern]}):
                    matched_waiver = waiver_pattern
                    used_waiver_patterns.add(waiver_pattern)
                    break
            
            if matched_waiver:
                waived_items[item_name] = item_data
            else:
                unwaived_items[item_name] = item_data
        
        # Find unused waivers
        unused_waivers = {
            waiver_name: {
                'name': waiver_name,
                'line_number': 0,
                'file_path': data.get('default_file', 'N/A'),
                'reason': waive_dict[waiver_name]
            }
            for waiver_name in waive_dict.keys()
            if waiver_name not in used_waiver_patterns
        }
        
        # Build output
        return self.build_complete_output(
            found_items=clean_items,
            missing_items=unwaived_items,
            waived_items=waived_items,
            unused_waivers=unused_waivers,
            waive_dict=waive_dict,
            found_desc=self.FOUND_DESC,
            missing_desc=self.MISSING_DESC,
            waived_desc=self.WAIVED_DESC,
            found_reason=self.FOUND_REASON,
            missing_reason=self.MISSING_REASON,
            waived_base_reason=self.WAIVED_BASE_REASON
        )


# =========================================================================
# Entry Point
# =========================================================================

def main():
    """Main entry point."""
    checker = Check_10_0_0_26()
    checker.init_checker(Path(__file__))
    result = checker.execute_check()
    checker.write_output(result)
    return 0 if result.is_pass else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())