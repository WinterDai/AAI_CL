################################################################################
# Script Name: IMP-12-0-0-28.py
#
# Purpose:
#   Confirm ARC check result is clean. (For BRCM project only, for others fill N/A)
#
# Logic:
#   - Parse input files: Calibre_ARC.rep (and optional Pegasus ARC reports)
#   - Detect report format (Calibre vs Pegasus) based on pattern matching
#   - Extract individual ARC rule violations with counts from RULECHECK sections
#   - Extract total violation count from summary section (TOTAL DRC Results)
#   - Aggregate violations across all reports by ARC rule name
#   - For Type 1/4: Check if total violations = 0 across ALL reports
#   - For Type 2/3: Filter violations to monitored rules (pattern_items)
#   - For Type 3/4: Apply waiver logic to classify violations
#   - Generate summary statistics with per-rule and per-report breakdown
#
# Auto Type Detection:
#   Type 1: requirements.value=N/A, waivers.value=N/A/0 → Boolean check
#   Type 2: requirements.value>0, pattern_items exists, waivers.value=N/A/0 → Value comparison
#   Type 3: requirements.value>0, pattern_items exists, waivers.value>0 → Value with waiver logic
#   Type 4: requirements.value=N/A, waivers.value>0 → Boolean with waiver logic
#
# Output Behavior (Type 2/3 - Check README "Output Behavior" section!):
#   status_check: pattern_items = ARC rule names to monitor (only output matched items)
#     - found_items = monitored rules with 0 violations (status correct)
#     - missing_items = monitored rules with violations > 0 (status wrong)
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
class Check_12_0_0_28(InputFileParserMixin, OutputBuilderMixin, WaiverHandlerMixin, BaseChecker):
    """
    IMP-12-0-0-28: Confirm ARC check result is clean. (For BRCM project only, for others fill N/A)
    
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
    FOUND_DESC_TYPE1_4 = "ARC check clean - no violations found in all reports"
    MISSING_DESC_TYPE1_4 = "ARC violations detected in reports"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_DESC_TYPE2_3 = "ARC check clean - all monitored rules satisfied (0 violations)"
    MISSING_DESC_TYPE2_3 = "ARC violations found - monitored rules not satisfied"
    
    # All Types (waiver description unified)
    WAIVED_DESC = "Waived ARC violations (approved exceptions)"
    
    # ⭐ REASON CONSTANTS - Split by Type semantics (API-025)
    # ALL Types pass found_reason/missing_reason, but use different constants
    
    # Type 1/4: Boolean checks - emphasize "found/not found" (existence)
    FOUND_REASON_TYPE1_4 = "All ARC reports show 0 violations (TOTAL DRC Results = 0)"
    MISSING_REASON_TYPE1_4 = "ARC violations found - total violation count > 0"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_REASON_TYPE2_3 = "All monitored ARC rules satisfied with 0 violations across all reports"
    MISSING_REASON_TYPE2_3 = "ARC rule violations not satisfied - violation count > 0"
    
    # Waiver-related (Type 3/4 only)
    WAIVED_BASE_REASON = "ARC violation waived per design team approval"
    UNUSED_WAIVER_REASON = "Waiver not matched - no corresponding ARC violation found in reports"
    
    def __init__(self):
        """Initialize the checker."""
        super().__init__(
            check_module="12.0_PHYSICAL_VERIFICATION_CHECK",
            item_id="IMP-12-0-0-28",
            item_desc="Confirm ARC check result is clean. (For BRCM project only, for others fill N/A)"
        )
        # Custom member variables for parsed data
        self._parsed_items: List[Dict[str, Any]] = []
        self._metadata: Dict[str, str] = {}
        self._total_violations: int = 0
    
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
        Parse input files to extract ARC violations.
        
        Supports two ARC report formats:
        - Calibre: RULECHECK ... TOTAL Result Count = X (Y)
        - Pegasus: RULECHECK ... Total Result X (Y)
        
        Returns:
            Dict with parsed data:
            - 'items': List[Dict] - ARC violations with metadata
            - 'metadata': Dict - Report metadata
            - 'total_violations': int - Total violation count across all reports
        """
        # 1. Validate input files - IMPORTANT: returns tuple (valid_files_list, missing_files_list)
        valid_files, missing_files = self.validate_input_files()
        if not valid_files or len(valid_files) == 0:
            raise ConfigurationError("No valid input files found")
        
        # 2. Parse ARC reports
        all_violations = {}  # Dict[rule_name, Dict[count, line_number, file_path]]
        total_violations = 0
        metadata = {
            'report_count': len(valid_files),
            'reports': []
        }
        
        # Patterns for Calibre format
        calibre_rule_pattern = re.compile(r'^RULECHECK\s+(\S+)\s+\.+\s+TOTAL\s+Result\s+Count\s*=\s*(\d+)\s*\(\d+\)')
        calibre_total_pattern = re.compile(r'^TOTAL\s+DRC\s+Results\s+Generated:\s+(\d+)\s*\(\d+\)')
        
        # Patterns for Pegasus format
        pegasus_rule_pattern = re.compile(r'^RULECHECK\s+(\S+)\s+\.+\s+Total\s+Result\s+(\d+)\s*\(\s*\d+\s*\)')
        pegasus_total_pattern = re.compile(r'^Total\s+DRC\s+Results\s*:\s*(\d+)\s*\(\d+\)')
        
        for file_path in valid_files:
            report_violations = 0
            report_format = 'Unknown'
            
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line_num, line in enumerate(f, 1):
                    # Try Calibre format first
                    match = calibre_rule_pattern.search(line)
                    if match:
                        report_format = 'Calibre'
                        rule_name = match.group(1)
                        violation_count = int(match.group(2))
                        
                        if violation_count > 0:
                            if rule_name in all_violations:
                                # Aggregate violations for same rule across reports
                                all_violations[rule_name]['count'] += violation_count
                            else:
                                all_violations[rule_name] = {
                                    'name': rule_name,
                                    'count': violation_count,
                                    'line_number': line_num,
                                    'file_path': str(file_path)
                                }
                        continue
                    
                    # Try Pegasus format
                    match = pegasus_rule_pattern.search(line)
                    if match:
                        report_format = 'Pegasus'
                        rule_name = match.group(1)
                        violation_count = int(match.group(2))
                        
                        if violation_count > 0:
                            if rule_name in all_violations:
                                all_violations[rule_name]['count'] += violation_count
                            else:
                                all_violations[rule_name] = {
                                    'name': rule_name,
                                    'count': violation_count,
                                    'line_number': line_num,
                                    'file_path': str(file_path)
                                }
                        continue
                    
                    # Try Calibre total pattern
                    match = calibre_total_pattern.search(line)
                    if match:
                        report_violations = int(match.group(1))
                        continue
                    
                    # Try Pegasus total pattern
                    match = pegasus_total_pattern.search(line)
                    if match:
                        report_violations = int(match.group(1))
                        continue
            
            # Update metadata
            metadata['reports'].append({
                'file': str(file_path),
                'format': report_format,
                'violations': report_violations
            })
            total_violations += report_violations
        
        # 3. Convert violations dict to list
        items = list(all_violations.values())
        
        # 4. Store on self
        self._parsed_items = items
        self._metadata = metadata
        self._total_violations = total_violations
        
        # 5. Return aggregated dict
        return {
            'items': items,
            'metadata': metadata,
            'total_violations': total_violations
        }
    
    # =========================================================================
    # Type 1: Boolean Check
    # =========================================================================
    
    def _execute_type1(self) -> CheckResult:
        """
        Type 1: Boolean Check.
        
        Check if total ARC violations = 0 across ALL reports.
        Does NOT use pattern_items for filtering.
        
        Returns:
            CheckResult with is_pass based on total violation count
        """
        # Parse input
        data = self._parse_input_files()
        items = data.get('items', [])
        total_violations = data.get('total_violations', 0)
        metadata = data.get('metadata', {})
        
        # Convert violations to dict with metadata for output
        found_items = {}
        missing_items = []
        
        if total_violations == 0:
            # Clean - no violations
            for report in metadata.get('reports', []):
                report_name = Path(report['file']).name
                found_items[report_name] = {
                    'name': report_name,
                    'line_number': 0,
                    'file_path': report['file']
                }
        else:
            # Violations found
            for item in items:
                violation_key = f"{item['name']}: {item['count']} violations"
                missing_items.append(violation_key)
        
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
        
        Monitor specific ARC rules listed in pattern_items.
        found_items = monitored rules with 0 violations
        missing_items = monitored rules with violations > 0
        
        Returns:
            CheckResult with is_pass based on monitored rules
        """
        # Parse input
        data = self._parse_input_files()
        items = data.get('items', [])
        
        # Get requirements
        pattern_items = self.item_data.get('requirements', {}).get('pattern_items', [])
        
        # Build dict of all violations by rule name
        all_violations = {item['name']: item for item in items}
        
        # status_check mode: Only output items matching pattern_items
        found_items = {}
        missing_items = []
        missing_patterns = []
        
        for pattern in pattern_items:
            matched = False
            for rule_name, violation_data in all_violations.items():
                # Match pattern (case-insensitive substring match)
                if pattern.lower() in rule_name.lower() or pattern == rule_name:
                    matched = True
                    if violation_data['count'] == 0:
                        # Status correct - no violations
                        found_items[rule_name] = {
                            'name': rule_name,
                            'line_number': violation_data.get('line_number', 0),
                            'file_path': violation_data.get('file_path', 'N/A')
                        }
                    else:
                        # Status wrong - has violations
                        violation_key = f"{rule_name}: {violation_data['count']} violations"
                        missing_items.append(violation_key)
                    break
            
            if not matched:
                # Pattern not found in any violations (could be clean or not checked)
                missing_patterns.append(pattern)
        
        # If no violations found for monitored rules, treat as clean
        if not missing_items and missing_patterns:
            # Patterns not matched means they're clean (no violations reported)
            for pattern in missing_patterns:
                found_items[pattern] = {
                    'name': pattern,
                    'line_number': 0,
                    'file_path': 'N/A'
                }
            missing_patterns = []
        
        # Use template helper (auto-handles waiver=0)
        # Type 2: Use TYPE2_3 desc+reason (emphasize "matched/satisfied")
        return self.build_complete_output(
            found_items=found_items,
            missing_items=missing_items if missing_items else missing_patterns,
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
        
        # Parse waiver configuration using template helper
        # CORRECT! Use waivers.get() directly to preserve dict format
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # Get requirements
        pattern_items = self.item_data.get('requirements', {}).get('pattern_items', [])
        
        # Build dict of all violations by rule name
        all_violations = {item['name']: item for item in items}
        
        # status_check mode: Only process items matching pattern_items
        found_items = {}
        waived_items = {}
        unwaived_items = []
        
        for pattern in pattern_items:
            matched = False
            for rule_name, violation_data in all_violations.items():
                # Match pattern (case-insensitive substring match)
                if pattern.lower() in rule_name.lower() or pattern == rule_name:
                    matched = True
                    if violation_data['count'] == 0:
                        # No violations - clean
                        found_items[rule_name] = {
                            'name': rule_name,
                            'line_number': violation_data.get('line_number', 0),
                            'file_path': violation_data.get('file_path', 'N/A')
                        }
                    else:
                        # Has violations - check waiver
                        if self.match_waiver_entry(rule_name, waive_dict):
                            waived_items[rule_name] = {
                                'name': rule_name,
                                'count': violation_data['count'],
                                'line_number': violation_data.get('line_number', 0),
                                'file_path': violation_data.get('file_path', 'N/A')
                            }
                        else:
                            violation_key = f"{rule_name}: {violation_data['count']} violations"
                            unwaived_items.append(violation_key)
                    break
            
            if not matched:
                # Pattern not matched - treat as clean (no violations reported)
                found_items[pattern] = {
                    'name': pattern,
                    'line_number': 0,
                    'file_path': 'N/A'
                }
        
        # Find unused waivers
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
        
        Same boolean check as Type 1 (no pattern_items - checks ALL ARC rules), plus waiver classification.
        
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
        
        # Convert items to dict with metadata
        found_items = {}
        waived_items = {}
        unwaived_items = []
        
        for item in items:
            rule_name = item['name']
            violation_count = item['count']
            
            if violation_count > 0:
                # Has violations - check waiver
                if self.match_waiver_entry(rule_name, waive_dict):
                    waived_items[rule_name] = {
                        'name': rule_name,
                        'count': violation_count,
                        'line_number': item.get('line_number', 0),
                        'file_path': item.get('file_path', 'N/A')
                    }
                else:
                    violation_key = f"{rule_name}: {violation_count} violations"
                    unwaived_items.append(violation_key)
        
        # Find unused waivers
        used_names = set(waived_items.keys())
        unused_waivers = [name for name in waive_dict.keys() if name not in used_names]
        
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
    checker = Check_12_0_0_28()
    checker.init_checker(Path(__file__))
    result = checker.execute_check()
    checker.write_output(result)
    return 0 if result.is_pass else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())