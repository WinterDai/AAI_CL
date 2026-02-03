################################################################################
# Script Name: IMP-12-0-0-26.py
#
# Purpose:
#   Confirm BUMP rule DRC result is clean.
#
# Logic:
#   - Parse input files: Calibre_BUMP.rep, Pegasus_BUMP.rep
#   - Identify DRC report sections: Skip RUNTIME WARNINGS, parse RULECHECK RESULTS
#   - Extract DRC rule violations: Match rule names and violation counts using regex
#   - Aggregate violations across all reports: Combine Calibre and Pegasus results
#   - Classify violations: Separate waived vs unwaived based on waive_items
#   - Determine pass/fail: PASS if total violations == 0 (Type 1/2) or all waived (Type 3/4)
#
# Auto Type Detection:
#   Type 1: requirements.value=N/A, waivers.value=N/A/0 → Boolean check
#   Type 2: requirements.value>0, pattern_items exists, waivers.value=N/A/0 → Value comparison
#   Type 3: requirements.value>0, pattern_items exists, waivers.value>0 → Value with waiver logic
#   Type 4: requirements.value=N/A, waivers.value>0 → Boolean with waiver logic
#
# Output Behavior (Type 2/3 - Check README "Output Behavior" section!):
#   status_check: pattern_items = DRC rules to CHECK STATUS (only output matched items)
#     - found_items = rules matched AND status correct (0 violations)
#     - missing_items = rules matched BUT status wrong (violations > 0)
#
# Waiver Tag Rules:
#   When waivers.value > 0 (Type 3/4):
#     - All waive_items related INFO/FAIL/WARN reason suffix: [WAIVER]
#   When waivers.value = 0 (Type 1/2):
#     - waive_items output as INFO with suffix: [WAIVED_INFO]
#     - FAIL/WARN converted to INFO with suffix: [WAIVED_AS_INFO]
#   All types support value = N/A
#
# Refactored: 2026-01-12 (Using checker_templates v1.1.0)
#
# Author: Jingyu Wang
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
class Check_12_0_0_26(InputFileParserMixin, OutputBuilderMixin, WaiverHandlerMixin, BaseChecker):
    """
    IMP-12-0-0-26: Confirm BUMP rule DRC result is clean.
    
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
    FOUND_DESC_TYPE1_4 = "BUMP DRC verification clean - no violations found in all reports"
    MISSING_DESC_TYPE1_4 = "BUMP DRC violations detected in reports"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_DESC_TYPE2_3 = "All DRC rules passed - zero violations across all checks"
    MISSING_DESC_TYPE2_3 = "DRC rule violations found - design not clean"
    
    # All Types (waiver description unified)
    WAIVED_DESC = "Waived DRC violations (approved exceptions)"
    
    # ⭐ REASON CONSTANTS - Split by Type semantics (API-025)
    # ALL Types pass found_reason/missing_reason, but use different constants
    
    # Type 1/4: Boolean checks - emphasize "found/not found" (existence)
    FOUND_REASON_TYPE1_4 = "All DRC reports show zero violations - design is DRC clean"
    MISSING_REASON_TYPE1_4 = "DRC violations found - total violation count exceeds zero"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_REASON_TYPE2_3 = "All DRC rule checks satisfied with zero violations"
    MISSING_REASON_TYPE2_3 = "DRC rule check not satisfied - violations detected"
    
    # Waiver-related (Type 3/4 only)
    WAIVED_BASE_REASON = "DRC violation waived per design review approval"
    UNUSED_WAIVER_REASON = "Waiver entry not matched to any DRC violation in reports"
    
    def __init__(self):
        """Initialize the checker."""
        super().__init__(
            check_module="12.0_PHYSICAL_VERIFICATION_CHECK",
            item_id="IMP-12-0-0-26",
            item_desc="Confirm BUMP rule DRC result is clean."
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
        Parse input files to extract relevant data.
        
        Parses Calibre and Pegasus DRC reports to extract rule violations.
        
        Uses InputFileParserMixin helper methods:
        - validate_input_files() - Returns (valid_files, missing_files) tuple
        
        Returns:
            Dict with parsed data:
            - 'items': List[Dict] - DRC rule violations with metadata (line_number, file_path)
            - 'metadata': Dict - File metadata (total_violations, report_count)
            - 'errors': List - Any parsing errors encountered
        """
        # 1. Validate input files (raises ConfigurationError if missing)
        valid_files, missing_files = self.validate_input_files()
        if not valid_files or len(valid_files) == 0:
            raise ConfigurationError(
                self.create_missing_files_error(missing_files)
            )
        
        # 2. Parse each DRC report file
        all_violations = []
        total_violations = 0
        
        # Calibre patterns
        calibre_section_header = re.compile(r'^---\s+RULECHECK\s+RESULTS', re.IGNORECASE)
        calibre_rule_result = re.compile(r'^\s*RULECHECK\s+([A-Za-z0-9_.]+)\s+\.+\s+TOTAL\s+Result\s+Count\s+=\s+(\d+)\s*\(', re.IGNORECASE)
        calibre_total = re.compile(r'^\s*TOTAL\s+DRC\s+Results\s+Generated:\s+(\d+)\s*\(', re.IGNORECASE)
        
        # Pegasus patterns
        pegasus_rule_result = re.compile(r'^\s*RULECHECK\s+([A-Za-z0-9_.]+)\s+\.+\s+Total\s+Result\s+(\d+)\s*\(', re.IGNORECASE)
        pegasus_total = re.compile(r'^\s*Total\s+DRC\s+Results\s*:\s+(\d+)\s*\(', re.IGNORECASE)
        
        for file_path in valid_files:
            in_rulecheck_section = False
            
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line_num, line in enumerate(f, 1):
                    # Check for Calibre RULECHECK RESULTS section
                    if calibre_section_header.search(line):
                        in_rulecheck_section = True
                        continue
                    
                    # Parse Calibre rule results
                    calibre_match = calibre_rule_result.search(line)
                    if calibre_match and in_rulecheck_section:
                        rule_name = calibre_match.group(1)
                        violation_count = int(calibre_match.group(2))
                        
                        if violation_count > 0:
                            all_violations.append({
                                'name': rule_name,
                                'violation_count': violation_count,
                                'line_number': line_num,
                                'file_path': str(file_path),
                                'report_type': 'Calibre'
                            })
                        continue
                    
                    # Parse Calibre total
                    calibre_total_match = calibre_total.search(line)
                    if calibre_total_match:
                        total_violations += int(calibre_total_match.group(1))
                        continue
                    
                    # Parse Pegasus rule results
                    pegasus_match = pegasus_rule_result.search(line)
                    if pegasus_match:
                        rule_name = pegasus_match.group(1)
                        violation_count = int(pegasus_match.group(2))
                        
                        if violation_count > 0:
                            all_violations.append({
                                'name': rule_name,
                                'violation_count': violation_count,
                                'line_number': line_num,
                                'file_path': str(file_path),
                                'report_type': 'Pegasus'
                            })
                        continue
                    
                    # Parse Pegasus total
                    pegasus_total_match = pegasus_total.search(line)
                    if pegasus_total_match:
                        total_violations += int(pegasus_total_match.group(1))
                        continue
        
        # 3. Store frequently reused data on self
        self._parsed_items = all_violations
        self._metadata = {
            'total_violations': total_violations,
            'report_count': len(valid_files)
        }
        
        # 4. Return aggregated dict with items containing line_number and file_path
        return {
            'items': all_violations,
            'metadata': self._metadata,
            'errors': []
        }
    
    # =========================================================================
    # Type 1: Boolean Check
    # =========================================================================
    
    def _execute_type1(self) -> CheckResult:
        """
        Type 1: Boolean Check.
        
        Custom boolean validation: Parse all DRC reports and verify total violations == 0.
        Does NOT use pattern_items for searching.
        
        Use OutputBuilderMixin.build_complete_output() for automatic formatting.
        
        Returns:
            CheckResult with is_pass based on check logic
        """
        # Parse input
        data = self._parse_input_files()
        items = data.get('items', [])
        total_violations = data.get('metadata', {}).get('total_violations', 0)
        
        # Convert list to dict with metadata for source file/line display
        found_items = {}
        missing_items = {}
        
        if total_violations == 0:
            # DRC clean - no violations
            found_items = {
                'DRC_CLEAN': {
                    'name': 'DRC_CLEAN',
                    'line_number': 0,
                    'file_path': 'All reports'
                }
            }
        else:
            # DRC violations found
            for item in items:
                violation_key = f"{item['name']} ({item['report_type']})"
                missing_items[violation_key] = {
                    'name': violation_key,
                    'line_number': item.get('line_number', 0),
                    'file_path': item.get('file_path', 'N/A'),
                    'violation_count': item.get('violation_count', 0)
                }
        
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
        This is a status_check: pattern_items are DRC rules to check status.
        found_items = rules matched AND status correct (0 violations)
        missing_items = rules matched BUT status wrong (violations > 0)
        
        Template auto-handles waiver=0 conversions.
        
        Returns:
            CheckResult with is_pass based on value comparison
        """
        # Parse input
        data = self._parse_input_files()
        items = data.get('items', [])
        
        # Get requirements
        pattern_items = self.item_data.get('requirements', {}).get('pattern_items', [])
        
        # Build dict of all violations by rule name
        violations_dict = {}
        for item in items:
            rule_name = item['name']
            if rule_name not in violations_dict:
                violations_dict[rule_name] = []
            violations_dict[rule_name].append(item)
        
        # status_check mode: Check status of items matching pattern_items
        found_items = {}      # Matched AND status correct (0 violations)
        missing_items = {}    # Matched BUT status wrong (violations > 0)
        
        for pattern in pattern_items:
            matched = False
            
            # Check if pattern matches any violation
            for rule_name, rule_violations in violations_dict.items():
                if pattern.lower() == rule_name.lower() or pattern.lower() in rule_name.lower():
                    matched = True
                    # Rule has violations - status wrong
                    violation_key = f"{rule_name}"
                    total_count = sum(v.get('violation_count', 0) for v in rule_violations)
                    # Use first violation for metadata
                    first_violation = rule_violations[0]
                    missing_items[violation_key] = {
                        'name': violation_key,
                        'line_number': first_violation.get('line_number', 0),
                        'file_path': first_violation.get('file_path', 'N/A'),
                        'violation_count': total_count
                    }
                    break
            
            if not matched:
                # Pattern not found in violations - assume rule passed (0 violations)
                found_items[pattern] = {
                    'name': pattern,
                    'line_number': 0,
                    'file_path': 'N/A'
                }
        
        # Use template helper (auto-handles waiver=0)
        # Type 2: Use TYPE2_3 desc+reason (emphasize "matched/satisfied")
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
        
        Same pattern search logic as Type 2 (status_check), plus waiver classification.
        
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
        # CORRECT! Use waivers.get() directly to preserve dict format
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # Get requirements
        pattern_items = self.item_data.get('requirements', {}).get('pattern_items', [])
        
        # Build dict of all violations by rule name
        violations_dict = {}
        for item in items:
            rule_name = item['name']
            if rule_name not in violations_dict:
                violations_dict[rule_name] = []
            violations_dict[rule_name].append(item)
        
        # status_check mode: Check status of items matching pattern_items
        found_items = {}      # Matched AND status correct (0 violations)
        waived_items = {}     # Matched BUT status wrong AND waived
        unwaived_items = {}   # Matched BUT status wrong AND NOT waived
        
        for pattern in pattern_items:
            matched = False
            
            # Check if pattern matches any violation
            for rule_name, rule_violations in violations_dict.items():
                if pattern.lower() == rule_name.lower() or pattern.lower() in rule_name.lower():
                    matched = True
                    # Rule has violations - check if waived
                    total_count = sum(v.get('violation_count', 0) for v in rule_violations)
                    first_violation = rule_violations[0]
                    
                    violation_key = rule_name
                    violation_data = {
                        'name': violation_key,
                        'line_number': first_violation.get('line_number', 0),
                        'file_path': first_violation.get('file_path', 'N/A'),
                        'violation_count': total_count
                    }
                    
                    # Check if waived
                    if self.match_waiver_entry(rule_name, waive_dict):
                        waived_items[violation_key] = violation_data
                    else:
                        unwaived_items[violation_key] = violation_data
                    break
            
            if not matched:
                # Pattern not found in violations - rule passed (0 violations)
                found_items[pattern] = {
                    'name': pattern,
                    'line_number': 0,
                    'file_path': 'N/A'
                }
        
        # Find unused waivers by checking if waiver names were used
        used_names = set(waived_items.keys())
        unused_waivers = [name for name in waive_dict.keys() if name not in used_names]
        
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
        
        # Parse waiver configuration
        # CORRECT! Use waivers.get() directly to preserve dict format
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # Separate waived/unwaived violations
        waived_items = {}
        unwaived_items = {}
        
        for item in items:
            rule_name = item['name']
            violation_key = f"{rule_name} ({item['report_type']})"
            violation_data = {
                'name': violation_key,
                'line_number': item.get('line_number', 0),
                'file_path': item.get('file_path', 'N/A'),
                'violation_count': item.get('violation_count', 0)
            }
            
            # Check if waived
            if self.match_waiver_entry(rule_name, waive_dict):
                waived_items[violation_key] = violation_data
            else:
                unwaived_items[violation_key] = violation_data
        
        # Find unused waivers
        used_names = set()
        for item in items:
            if self.match_waiver_entry(item['name'], waive_dict):
                used_names.add(item['name'])
        unused_waivers = [name for name in waive_dict.keys() if name not in used_names]
        
        # Build found_items for clean status
        found_items = {}
        if not items:
            found_items = {
                'DRC_CLEAN': {
                    'name': 'DRC_CLEAN',
                    'line_number': 0,
                    'file_path': 'All reports'
                }
            }
        
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
    checker = Check_12_0_0_26()
    checker.init_checker(Path(__file__))
    result = checker.execute_check()
    checker.write_output(result)
    return 0 if result.is_pass else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())