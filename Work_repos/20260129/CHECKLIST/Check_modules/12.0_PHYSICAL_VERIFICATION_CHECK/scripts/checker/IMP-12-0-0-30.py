################################################################################
# Script Name: IMP-12-0-0-30.py
#
# Purpose:
#   Confirm DFM check result is clean. (for SEC process, for others fill N/A)
#
# Logic:
#   - Parse Pegasus_DFM.sum to extract total DRC results count and individual rulecheck violations
#   - Extract rulecheck names and violation counts from RULECHECK and nested CELL sections
#   - Verify DFM is clean (Total DRC Results = 0) or identify specific rule violations
#   - Support waiver for specific DFM rulechecks that are acceptable violations
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
# Refactored: 2026-01-06 (Using checker_templates v1.1.0)
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
from checker_templates.input_file_parser_template import InputFileParserMixin  # Optional but recommended


# MANDATORY: Inherit mixins in correct order (InputFileParserMixin first if used)
class Check_12_0_0_30(InputFileParserMixin, OutputBuilderMixin, WaiverHandlerMixin, BaseChecker):
    """
    IMP-12-0-0-30: Confirm DFM check result is clean. (for SEC process, for others fill N/A)
    
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
    FOUND_DESC_TYPE1_4 = "All DFM rules passed with zero violations"
    MISSING_DESC_TYPE1_4 = "DFM violations detected in Pegasus report"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_DESC_TYPE2_3 = "All DFM rules clean (0 violations)"
    MISSING_DESC_TYPE2_3 = "DFM rule violations found (rules with non-zero violations)"
    
    # All Types (waiver description unified)
    WAIVED_DESC = "DFM rule violations waived"
    
    # ⭐ REASON CONSTANTS - Split by Type semantics (API-025)
    # ALL Types pass found_reason/missing_reason, but use different constants
    
    # Type 1/4: Boolean checks - emphasize "found/not found" (existence)
    FOUND_REASON_TYPE1_4 = "All DFM rule checks in Pegasus_DFM.sum report have zero violations"
    MISSING_REASON_TYPE1_4 = "One or more DFM rules have violations in Pegasus_DFM.sum report"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_REASON_TYPE2_3 = "All DFM rule checks validated with zero violations in Pegasus_DFM.sum"
    MISSING_REASON_TYPE2_3 = "DFM rule check failed with violations in Pegasus_DFM.sum"
    
    # Waiver-related (Type 3/4 only)
    WAIVED_BASE_REASON = "DFM rule violations waived per design team approval"
    UNUSED_WAIVER_REASON = "Waiver not matched - no corresponding DFM rule violation found"
    
    def __init__(self):
        """Initialize the checker."""
        super().__init__(
            check_module="12.0_PHYSICAL_VERIFICATION_CHECK",
            item_id="IMP-12-0-0-30",
            item_desc="Confirm DFM check result is clean. (for SEC process, for others fill N/A)"
        )
        # Custom member variables for parsed data
        self._parsed_items: List[Dict[str, Any]] = []
        self._metadata: Dict[str, str] = {}
        self._total_violations: int = 0
        self._rulecheck_violations: Dict[str, int] = {}
    
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
        Parse Pegasus_DFM.sum to extract DFM violation information.
        
        Extracts:
        - Total DRC Results count (primary violation metric)
        - Individual rulecheck violation counts (RULECHECK entries)
        - Cell-level rulecheck violations (nested under CELL)
        - Execution metadata (date, version, user)
        
        Returns:
            Dict with parsed data:
            - 'items': List[Dict] - Rulecheck violations with counts
            - 'metadata': Dict - File metadata (date, version, user)
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
        total_violations = 0
        rulecheck_violations = {}
        
        # 3. Parse each input file for DFM violation information
        for file_path in valid_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line_num, line in enumerate(f, 1):
                        # Pattern 1: Extract total DRC results count
                        # Example: Total DRC Results                 : 580 (580)
                        total_match = re.search(r'^Total DRC Results\s*:\s*(\d+)\s*\((\d+)\)$', line)
                        if total_match:
                            total_violations = int(total_match.group(1))
                            continue
                        
                        # Pattern 2: Extract individual rulecheck violation counts
                        # Example: RULECHECK PM_M2_C_3 .................................... Total Result        579 (       579)
                        rulecheck_match = re.search(r'^RULECHECK\s+(\S+)\s+\.+\s+Total Result\s+(\d+)\s*\(\s*\d+\)$', line)
                        if rulecheck_match:
                            rule_name = rulecheck_match.group(1)
                            violation_count = int(rulecheck_match.group(2))
                            rulecheck_violations[rule_name] = violation_count
                            items.append({
                                'name': rule_name,
                                'count': violation_count,
                                'line_number': line_num,
                                'file_path': str(file_path),
                                'type': 'rulecheck'
                            })
                            continue
                        
                        # Pattern 4: Extract nested cell rulecheck violations (indented under CELL)
                        # Example:     RULECHECK PM_M2_C_3 ................................ Total Result        579 (       579)
                        nested_match = re.search(r'^\s{4}RULECHECK\s+(\S+)\s+\.+\s+Total Result\s+(\d+)\s*\(\s*\d+\)$', line)
                        if nested_match:
                            rule_name = nested_match.group(1)
                            violation_count = int(nested_match.group(2))
                            # Only add if not already captured by pattern 2
                            if rule_name not in rulecheck_violations:
                                rulecheck_violations[rule_name] = violation_count
                                items.append({
                                    'name': rule_name,
                                    'count': violation_count,
                                    'line_number': line_num,
                                    'file_path': str(file_path),
                                    'type': 'nested_rulecheck'
                                })
                            continue
                        
                        # Pattern 5: Extract execution metadata
                        # Example: Execute on Date/Time    : Sat Dec 13 15:27:19 2025
                        metadata_match = re.search(r'^(Execute on Date/Time|Pegasus VERSION|User Name)\s*:\s*(.+)$', line)
                        if metadata_match:
                            key = metadata_match.group(1).strip()
                            value = metadata_match.group(2).strip()
                            metadata[key] = value
                            continue
            except Exception as e:
                errors.append(f"Error parsing {file_path}: {str(e)}")
        
        # 4. Store frequently reused data on self
        self._parsed_items = items
        self._metadata = metadata
        self._total_violations = total_violations
        self._rulecheck_violations = rulecheck_violations
        
        return {
            'items': items,
            'metadata': metadata,
            'errors': errors
        }
    # Helper Methods (Optional - Add as needed)
    

    # =========================================================================
    # Type 1: Boolean Check
    # =========================================================================

    def _execute_type1(self) -> CheckResult:
        """
        Type 1: Boolean check without waiver support.

        Verifies that DFM check results are clean (Total DRC Results = 0).
        - found_items: DFM rules with zero violations (clean rules)
        - missing_items: DFM rules with violations (failing rules)

        Returns:
            CheckResult with PASS if all DFM rules are clean, FAIL otherwise.
        """
        violations = self._type1_core_logic()

        # Parse input to get all items
        data = self._parse_input_files()
        all_items = data.get('items', [])

        # Build found_items from clean rules (count == 0)
        found_items = {}
        for item in all_items:
            if item.get('count', 0) == 0:
                rule_name = item.get('name', 'unknown')
                # Format: "DFM rule: [rule_name] - 0 violations"
                display_name = f"DFM rule: {rule_name} - 0 violations"
                found_items[display_name] = {
                    'name': display_name,
                    'line_number': item.get('line_number', 0),
                    'file_path': item.get('file_path', 'N/A')
                }

        # FIXED: Pass violations dict directly (not list of keys)
        return self.build_complete_output(
            found_items=found_items,
            missing_items=violations,
            found_desc=self.FOUND_DESC_TYPE1_4,
            missing_desc=self.MISSING_DESC_TYPE1_4,
            found_reason=self.FOUND_REASON_TYPE1_4,
            missing_reason=self.MISSING_REASON_TYPE1_4
        )

    def _type1_core_logic(self) -> dict[str, dict]:
        """
        Core Type 1 boolean check logic (shared by Type 1 and Type 4).

        Parses Pegasus_DFM.sum to extract DFM rule violations.
        Checks if Total DRC Results = 0 and identifies specific rule violations.

        Returns:
            Dict of violations: {rule_name: {'line_number': ..., 'file_path': ..., 'reason': ...}}
            Empty dict if all checks pass (Total DRC Results = 0).
        """
        data = self._parse_input_files()

        # Check for parsing errors
        errors = data.get('errors', [])
        if errors:
            # If file not found or parsing failed, treat as violation
            return {
                'parsing_error': {
                    'line_number': 0,
                    'file_path': 'N/A',
                    'reason': '; '.join(errors)
                }
            }

        # Get items (all rulechecks)
        items = data.get('items', [])

        violations = {}

        # Check each rulecheck for violations
        for item in items:
            rule_name = item.get('name', 'unknown_rule')
            count = item.get('count', 0)

            # If count > 0, we have violations
            if count > 0:
                # Format: "DFM rule: [rule_name] - [count] violations"
                display_name = f"DFM rule: {rule_name} - {count} violations"
                violations[display_name] = {
                    'line_number': item.get('line_number', 0),
                    'file_path': item.get('file_path', 'N/A'),
                    'reason': f"DFM rule {rule_name} has {count} violation(s)"
                }

        return violations

    # =========================================================================
    # Type 4: Boolean Check with Waiver Logic
    # =========================================================================

    def _execute_type4(self) -> CheckResult:
        """
        Type 4: Boolean check with waiver support (reuses Type 1 core logic).

        Performs the same DFM check as Type 1, but allows specific rule violations
        to be waived. Violations are matched against waive_items patterns.

        - found_items: DFM rules with zero violations (clean rules)
        - waived_items: DFM rules with violations that match waiver patterns
        - missing_items: DFM rules with violations that are NOT waived (FAIL)
        - unused_waivers: Waiver patterns that didn't match any violations

        Returns:
            CheckResult with PASS if all violations are waived, FAIL otherwise.
        """
        # Step 1: Get violations using Type 1's core logic
        violations = self._type1_core_logic()

        # Parse input to get all items
        data = self._parse_input_files()
        all_items = data.get('items', [])

        # Build found_items from clean rules (count == 0)
        found_items = {}
        for item in all_items:
            if item.get('count', 0) == 0:
                rule_name = item.get('name', 'unknown')
                # Format: "DFM rule: [rule_name] - 0 violations"
                display_name = f"DFM rule: {rule_name} - 0 violations"
                found_items[display_name] = {
                    'name': display_name,
                    'line_number': item.get('line_number', 0),
                    'file_path': item.get('file_path', 'N/A')
                }

        # Step 2: Parse waiver configuration
        # FIXED: Use waivers.get() instead of get_waive_items()
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)

        # Step 3: Split violations into waived and unwaived
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

        # Step 4: Find unused waivers
        unused_waivers = [w for w in waive_dict.keys() if w not in used_waivers]

        # Step 5: Build output
        # FIXED: Pass dicts directly (not list of keys)
        return self.build_complete_output(
            found_items=found_items,
            missing_items=missing_items,
            waived_items=waived_items,
            unused_waivers=unused_waivers,
            waive_dict=waive_dict,
            found_desc=self.FOUND_DESC_TYPE1_4,
            missing_desc=self.MISSING_DESC_TYPE1_4,
            waived_desc=self.WAIVED_DESC,
            found_reason=self.FOUND_REASON_TYPE1_4,
            missing_reason=self.MISSING_REASON_TYPE1_4,
            waived_base_reason=self.WAIVED_BASE_REASON,
            unused_waiver_reason=self.UNUSED_WAIVER_REASON
        )

    # =========================================================================
    # Type 2: Value Check
    # =========================================================================

    def _execute_type2(self) -> CheckResult:
        """Type 2: Pattern/value check without waiver support."""
        found_items, missing_items = self._type2_core_logic()

        # FIXED: Pass dicts directly (not list of keys)
        return self.build_complete_output(
            found_items=found_items,
            missing_items=missing_items,
            found_desc=self.FOUND_DESC_TYPE2_3,
            missing_desc=self.MISSING_DESC_TYPE2_3,
            found_reason=self.FOUND_REASON_TYPE2_3,
            missing_reason=self.MISSING_REASON_TYPE2_3
        )

    def _type2_core_logic(self) -> tuple[dict[str, dict], dict[str, dict]]:
        """
        Core Type 2 pattern matching logic (shared by Type 2 and Type 3).

        Returns:
            Tuple of (found_items, missing_items)
            - found_items: {rule_name: {'line_number': ..., 'file_path': ...}}
            - missing_items: {rule_name: {'line_number': ..., 'file_path': ..., 'reason': ...}}
        """
        data = self._parse_input_files()
        items = data.get('items', [])

        requirements = self.item_data.get('requirements', {})
        pattern_items = requirements.get('pattern_items', [])

        found_items = {}
        missing_items = {}

        # Check each required DFM rule pattern
        for pattern in pattern_items:
            matched = False
            for item in items:
                rule_name = item['name']
                # EXACT MATCH (case-insensitive) - pattern_items are specific DFM rule names
                if pattern.lower() == rule_name.lower():
                    violation_count = item.get('count', 0)
                    if violation_count == 0:
                        # Rule found with zero violations - clean
                        # Format: "DFM rule: [rule_name] - 0 violations"
                        display_name = f"DFM rule: {rule_name} - 0 violations"
                        found_items[display_name] = {
                            'line_number': item.get('line_number', 0),
                            'file_path': item.get('file_path', 'N/A')
                        }
                    else:
                        # Rule found but has violations
                        # Format: "DFM rule: [rule_name] - [count] violations"
                        display_name = f"DFM rule: {rule_name} - {violation_count} violations"
                        missing_items[display_name] = {
                            'line_number': item.get('line_number', 0),
                            'file_path': item.get('file_path', 'N/A'),
                            'reason': f'DFM rule {rule_name} has {violation_count} violations'
                        }
                    matched = True
                    break

            if not matched:
                # Pattern not found in report
                missing_items[pattern] = {
                    'line_number': 0,
                    'file_path': 'N/A',
                    'reason': f'DFM rule "{pattern}" not found in Pegasus_DFM.sum'
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
        # FIXED: Use waivers.get() instead of get_waive_items()
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)

        # Step 3: Split violations into waived and unwaived
        found_items = {}
        waived_items = {}
        missing_items = {}
        used_waivers = set()

        # Process found_items_base (no waiver needed - clean rules)
        for item_name, item_data in found_items_base.items():
            found_items[item_name] = item_data

        # Process violations with waiver matching
        for viol_name, viol_data in violations.items():
            matched_waiver = self.match_waiver_entry(viol_name, waive_dict)
            if matched_waiver:
                waived_items[viol_name] = viol_data
                used_waivers.add(matched_waiver)
            else:
                missing_items[viol_name] = viol_data

        # Step 4: Find unused waivers
        unused_waivers = [w for w in waive_dict.keys() if w not in used_waivers]

        # Step 5: Build output
        # FIXED: Pass dicts directly (not list of keys)
        return self.build_complete_output(
            found_items=found_items,
            missing_items=missing_items,
            waived_items=waived_items,
            unused_waivers=unused_waivers,
            waive_dict=waive_dict,
            found_desc=self.FOUND_DESC_TYPE2_3,
            missing_desc=self.MISSING_DESC_TYPE2_3,
            waived_desc=self.WAIVED_DESC,
            found_reason=self.FOUND_REASON_TYPE2_3,
            missing_reason=self.MISSING_REASON_TYPE2_3,
            waived_base_reason=self.WAIVED_BASE_REASON,
            unused_waiver_reason=self.UNUSED_WAIVER_REASON
        )

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
    checker = Check_12_0_0_30()
    checker.init_checker(Path(__file__))
    result = checker.execute_check()
    checker.write_output(result)
    return 0 if result.is_pass else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())