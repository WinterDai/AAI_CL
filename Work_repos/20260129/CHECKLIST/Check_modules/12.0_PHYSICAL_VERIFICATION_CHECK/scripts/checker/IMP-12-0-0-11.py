################################################################################
# Script Name: IMP-12-0-0-11.py
#
# Purpose:
#   Confirm the DRC check result is clean. (fill the confidence level of not touching floorplan again in comment if fill no, for example, 90%~100%)
#
# Logic:
#   - Parse input files: Calibre_DRC.rep, Pegasus_DRC.rep
#   - Extract DRC rule violations with rule names and violation counts
#   - Detect report type (Calibre vs Pegasus) by parsing format patterns
#   - Aggregate total violation count across all reports
#   - For Type 3/4: Match violations against waive_items by rule name and count
#   - Classify violations as waived/unwaived based on waiver configuration
#   - Determine DRC clean status: PASS if total violations = 0 or all waived
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
class Check_12_0_0_11(InputFileParserMixin, OutputBuilderMixin, WaiverHandlerMixin, BaseChecker):
    """
    IMP-12-0-0-11: Confirm the DRC check result is clean. (fill the confidence level of not touching floorplan again in comment if fill no, for example, 90%~100%)
    
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
    FOUND_DESC_TYPE1_4 = "DRC clean - no violations found in all reports"
    MISSING_DESC_TYPE1_4 = "DRC violations detected - design not clean"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_DESC_TYPE2_3 = "All DRC rules validated - no violations detected"
    MISSING_DESC_TYPE2_3 = "DRC rule violations detected - requirements not satisfied"
    
    # All Types (waiver description unified)
    WAIVED_DESC = "Waived DRC violations"
    
    # ⭐ REASON CONSTANTS - Split by Type semantics (API-025)
    # ALL Types pass found_reason/missing_reason, but use different constants
    
    # Type 1/4: Boolean checks - emphasize "found/not found" (existence)
    FOUND_REASON_TYPE1_4 = "All DRC reports show zero violations (DRC clean)"
    MISSING_REASON_TYPE1_4 = "DRC violations found in reports - design requires fixes"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_REASON_TYPE2_3 = "All specified DRC rules validated with zero violations"
    MISSING_REASON_TYPE2_3 = "DRC rule violations detected - design rules not satisfied"
    
    # Waiver-related (Type 3/4 only)
    WAIVED_BASE_REASON = "DRC violation waived per design approval"
    UNUSED_WAIVER_REASON = "Waiver entry not matched - no corresponding DRC violation found in reports"
    
    def __init__(self):
        """Initialize the checker."""
        super().__init__(
            check_module="12.0_PHYSICAL_VERIFICATION_CHECK",
            item_id="IMP-12-0-0-11",
            item_desc="Confirm the DRC check result is clean. (fill the confidence level of not touching floorplan again in comment if fill no, for example, 90%~100%)"
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
        Parse input files to extract DRC violations.
        
        Parses both Calibre and Pegasus DRC report formats:
        - Calibre: RULECHECK <rule> ... TOTAL Result Count = <count> (<secondary>)
        - Pegasus: RULECHECK <rule> ... Total Result <count> (<secondary>)
        
        Returns:
            Dict with parsed data:
            - 'items': List[Dict] - DRC violations with rule name, count, metadata
            - 'metadata': Dict - Report metadata (total count, report type)
            - 'errors': List - Any parsing errors encountered
        """
        # 1. Validate input files - IMPORTANT: returns tuple (valid_files_list, missing_files_list)
        valid_files, missing_files = self.validate_input_files()
        if not valid_files or len(valid_files) == 0:
            raise ConfigurationError(
                self.create_missing_files_error(missing_files)
            )
        
        # 2. Parse DRC reports
        all_violations = []
        total_count = 0
        
        # Calibre patterns
        calibre_rule_pattern = re.compile(r'^\s*RULECHECK\s+(\S+)\s+\.+\s+TOTAL\s+Result\s+Count\s+=\s+(\d+)\s+\((\d+)\)', re.IGNORECASE)
        calibre_total_pattern = re.compile(r'^\s*TOTAL\s+DRC\s+Results\s+Generated:\s+(\d+)\s+\((\d+)\)', re.IGNORECASE)
        
        # Pegasus patterns
        pegasus_rule_pattern = re.compile(r'^\s*RULECHECK\s+(\S+)\s+\.+\s+Total\s+Result\s+(\d+)\s+\(\s*(\d+)\s*\)', re.IGNORECASE)
        pegasus_total_pattern = re.compile(r'^\s*Total\s+DRC\s+Results\s*:\s*(\d+)\s+\(\s*(\d+)\s*\)', re.IGNORECASE)
        
        for file_path in valid_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line_num, line in enumerate(f, 1):
                        # Try Calibre format first
                        match = calibre_rule_pattern.search(line)
                        if match:
                            rule_name = match.group(1)
                            violation_count = int(match.group(2))
                            
                            # Only add if violation count > 0
                            if violation_count > 0:
                                all_violations.append({
                                    'name': f"{rule_name}: {violation_count}",
                                    'rule_name': rule_name,
                                    'count': violation_count,
                                    'line_number': line_num,
                                    'file_path': str(file_path)
                                })
                            continue
                        
                        # Try Pegasus format
                        match = pegasus_rule_pattern.search(line)
                        if match:
                            rule_name = match.group(1)
                            violation_count = int(match.group(2))
                            
                            # Only add if violation count > 0
                            if violation_count > 0:
                                all_violations.append({
                                    'name': f"{rule_name}: {violation_count}",
                                    'rule_name': rule_name,
                                    'count': violation_count,
                                    'line_number': line_num,
                                    'file_path': str(file_path)
                                })
                            continue
                        
                        # Check for total count (Calibre)
                        match = calibre_total_pattern.search(line)
                        if match:
                            total_count += int(match.group(1))
                            continue
                        
                        # Check for total count (Pegasus)
                        match = pegasus_total_pattern.search(line)
                        if match:
                            total_count += int(match.group(1))
                            continue
            
            except Exception as e:
                # Log parsing error but continue with other files
                pass
        
        # 3. Store on self
        self._parsed_items = all_violations
        self._metadata = {
            'total_count': total_count,
            'violation_count': len(all_violations)
        }
        
        # 4. Return aggregated dict
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
        
        Boolean DRC clean validation across all provided reports.
        - Parses all Calibre and Pegasus DRC reports
        - Aggregates total violation count across all reports
        - PASS if total violations = 0 (DRC clean)
        - FAIL if total violations > 0 (DRC not clean)
        
        Returns:
            CheckResult with is_pass based on check logic
        """
        # Parse input
        data = self._parse_input_files()
        items = data.get('items', [])
        metadata = data.get('metadata', {})
        total_count = metadata.get('total_count', 0)
        
        # Convert list to dict with metadata for source file/line display
        found_items = {}
        missing_items = []
        
        if total_count == 0:
            # DRC clean - create summary item
            found_items['DRC_CLEAN'] = {
                'name': 'DRC_CLEAN',
                'line_number': 0,
                'file_path': 'All reports'
            }
        else:
            # DRC not clean - add all violations
            for item in items:
                missing_items.append(item['name'])
        
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
        found_items = patterns found with expected counts (0 violations)
        missing_items = patterns found with non-zero counts
        PASS if all pattern_items have zero violations.
        
        Returns:
            CheckResult with is_pass based on value comparison
        """
        # Parse input
        data = self._parse_input_files()
        items = data.get('items', [])
        
        # Get requirements
        pattern_items = self.item_data.get('requirements', {}).get('pattern_items', [])
        
        # Build dict of all violations by rule name
        violations_by_rule = {}
        for item in items:
            rule_name = item['rule_name']
            violations_by_rule[rule_name] = item
        
        # Check each pattern
        found_items = {}
        missing_items = []
        
        for pattern in pattern_items:
            # Pattern format: "RuleName: ExpectedCount"
            parts = pattern.split(':')
            if len(parts) != 2:
                continue
            
            rule_name = parts[0].strip()
            expected_count = int(parts[1].strip())
            
            # Check if rule exists in violations
            if rule_name in violations_by_rule:
                violation = violations_by_rule[rule_name]
                actual_count = violation['count']
                
                if actual_count == expected_count:
                    # Status correct
                    found_items[violation['name']] = {
                        'name': violation['name'],
                        'line_number': violation['line_number'],
                        'file_path': violation['file_path']
                    }
                else:
                    # Status wrong
                    missing_items.append(violation['name'])
            else:
                # Rule not found - check if expected count is 0
                if expected_count == 0:
                    # This is correct - no violations for this rule
                    found_items[f"{rule_name}: 0"] = {
                        'name': f"{rule_name}: 0",
                        'line_number': 0,
                        'file_path': 'N/A'
                    }
                else:
                    # Expected violations but none found
                    missing_items.append(pattern)
        
        # Use template helper
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
        
        Same pattern search logic as Type 2, plus waiver classification.
        - Parse all DRC reports and extract rule violations
        - Match found violations against waive_items by rule name and count
        - Classify violations:
          - Unwaived: Violations not in waive_items → ERROR
          - Waived: Violations matching waive_items → INFO with [WAIVER] tag
          - Unused waivers: waive_items not matching any violation → WARN with [WAIVER] tag
        - PASS if all violations are waived (total unwaived = 0)
        - FAIL if any unwaived violations exist
        
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
        
        # Convert items to dict with metadata for found_items
        found_items = {}
        waived_items = {}
        missing_items = []
        
        # Process each violation
        for item in items:
            violation_name = item['name']
            
            # Check if this violation is waived
            if self.match_waiver_entry(violation_name, waive_dict):
                waived_items[violation_name] = {
                    'name': violation_name,
                    'line_number': item.get('line_number', 0),
                    'file_path': item.get('file_path', 'N/A')
                }
            else:
                # Unwaived violation
                missing_items.append(violation_name)
        
        # Find unused waivers
        used_names = set(waived_items.keys())
        unused_waivers = [name for name in waive_dict.keys() if name not in used_names]
        
        # Use template helper for automatic output formatting (waivers.value>0)
        # Type 3: Use TYPE2_3 desc+reason (emphasize "matched/satisfied")
        return self.build_complete_output(
            found_items=found_items,
            waived_items=waived_items,
            missing_items=missing_items,
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
        - Parse all DRC reports and extract all violations
        - Match violations against waive_items by rule name and count
        - Classify violations:
          - Unwaived: Violations not in waive_items → ERROR
          - Waived: Violations matching waive_items → INFO with [WAIVER] tag
          - Unused waivers: waive_items not matching any violation → WARN with [WAIVER] tag
        - PASS if all violations are waived (total unwaived = 0)
        - FAIL if any unwaived violations exist
        
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
        
        # Classify violations
        found_items = {}
        waived_items = {}
        missing_items = []
        
        for item in items:
            violation_name = item['name']
            
            # Check if this violation is waived
            if self.match_waiver_entry(violation_name, waive_dict):
                waived_items[violation_name] = {
                    'name': violation_name,
                    'line_number': item.get('line_number', 0),
                    'file_path': item.get('file_path', 'N/A')
                }
            else:
                # Unwaived violation
                missing_items.append(violation_name)
        
        # Find unused waivers
        used_names = set(waived_items.keys())
        unused_waivers = [name for name in waive_dict.keys() if name not in used_names]
        
        # Use template helper for automatic output formatting (waivers.value>0)
        # Type 4: Use TYPE1_4 reason (emphasize "found/not found")
        return self.build_complete_output(
            found_items=found_items,
            waived_items=waived_items,
            missing_items=missing_items,
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
    checker = Check_12_0_0_11()
    checker.init_checker(Path(__file__))
    result = checker.execute_check()
    checker.write_output(result)
    return 0 if result.is_pass else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())