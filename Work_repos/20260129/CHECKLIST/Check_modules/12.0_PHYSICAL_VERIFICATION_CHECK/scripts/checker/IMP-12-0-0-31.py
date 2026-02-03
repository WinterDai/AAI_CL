################################################################################
# Script Name: IMP-12-0-0-31.py
#
# Purpose:
#   Confirm FLT check result is clean. (for SEC process, for others fill N/A)
#
# Logic:
#   - Parse Pegasus_FLT.sum to extract total DRC results count and individual rule results
#   - Extract RULECHECK lines with rule names and violation counts
#   - Verify total DRC results count is 0 (clean FLT check)
#   - Support waiver for specific FLT rules that are allowed to have violations
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
class Check_12_0_0_31(InputFileParserMixin, OutputBuilderMixin, WaiverHandlerMixin, BaseChecker):
    """
    IMP-12-0-0-31: Confirm FLT check result is clean. (for SEC process, for others fill N/A)
    
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
    FOUND_DESC_TYPE1_4 = "FLT check result is clean - all rules have 0 violations"
    MISSING_DESC_TYPE1_4 = "FLT check has violations - one or more rules failed"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_DESC_TYPE2_3 = "FLT check result is clean - all rules have 0 violations"
    MISSING_DESC_TYPE2_3 = "FLT check has violations - one or more rules failed"
    
    # All Types (waiver description unified)
    WAIVED_DESC = "FLT rule violation waived"
    
    # ⭐ REASON CONSTANTS - Split by Type semantics (API-025)
    # ALL Types pass found_reason/missing_reason, but use different constants
    
    # Type 1/4: Boolean checks - emphasize "found/not found" (existence)
    FOUND_REASON_TYPE1_4 = "All FLT rules passed with 0 violations in Pegasus_FLT.sum"
    MISSING_REASON_TYPE1_4 = "FLT rule violations detected in Pegasus_FLT.sum"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_REASON_TYPE2_3 = "All FLT rules passed with 0 violations in Pegasus_FLT.sum"
    MISSING_REASON_TYPE2_3 = "FLT rule violations detected in Pegasus_FLT.sum"
    
    # Waiver-related (Type 3/4 only)
    WAIVED_BASE_REASON = "FLT rule violation waived per design team approval"
    UNUSED_WAIVER_REASON = "Waiver not matched - no corresponding FLT rule violation found"
    
    def __init__(self):
        """Initialize the checker."""
        super().__init__(
            check_module="12.0_PHYSICAL_VERIFICATION_CHECK",
            item_id="IMP-12-0-0-31",
            item_desc="Confirm FLT check result is clean. (for SEC process, for others fill N/A)"
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
        Parse Pegasus_FLT.sum to extract FLT check results.
        
        Extracts:
        - Total DRC Results count (primary violation indicator)
        - Individual RULECHECK results (rule name and violation count)
        - Pegasus execution metadata (version, timestamp)
        - Layout primary cell name (design identifier)
        
        Returns:
            Dict with parsed data:
            - 'items': List[Dict] - FLT rule results with violation counts
            - 'metadata': Dict - File metadata (version, cell name)
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
        
        # 3. Parse each input file for FLT check results
        for file_path in valid_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line_num, line in enumerate(f, 1):
                        # Extract total DRC results count
                        total_match = re.search(r'^Total DRC Results\s*:\s*(\d+)\s*\(\d+\)\s*$', line)
                        if total_match:
                            total_violations = int(total_match.group(1))
                            metadata['total_violations'] = total_violations
                            metadata['total_line_number'] = line_num
                            continue
                        
                        # Extract individual rulecheck results
                        rule_match = re.search(r'^RULECHECK\s+([\w\.]+)\s+\.+\s+Total Result\s+(\d+)\s*\(\s*(\d+)\s*\)\s*$', line)
                        if rule_match:
                            rule_name = rule_match.group(1)
                            result_count = int(rule_match.group(2))
                            items.append({
                                'name': rule_name,
                                'violation_count': result_count,
                                'line_number': line_num,
                                'file_path': str(file_path),
                                'type': 'flt_rule'
                            })
                            continue
                        
                        # Extract Pegasus version
                        version_match = re.search(r'^Pegasus VERSION\s*:\s*(.+)$', line)
                        if version_match:
                            metadata['pegasus_version'] = version_match.group(1).strip()
                            continue
                        
                        # Extract layout primary cell
                        cell_match = re.search(r'^Layout Primary Cell\s*:\s*(.+)$', line)
                        if cell_match:
                            metadata['primary_cell'] = cell_match.group(1).strip()
                            continue
            except Exception as e:
                errors.append(f"Error parsing {file_path}: {str(e)}")
        
        # 4. Store frequently reused data on self
        self._parsed_items = items
        self._metadata = metadata
        self._total_violations = total_violations
        
        return {
            'items': items,
            'metadata': metadata,
            'errors': errors
        }
    # Helper Methods (Optional - Add as needed)
    

    # =========================================================================
    # Type 1: Boolean Check

    def _execute_type1(self) -> CheckResult:
        """
        Type 1: Boolean check without waiver support.

        Verifies that FLT check result is clean (total DRC results count = 0).
        Any FLT rule violations will cause FAIL.

        Returns:
            CheckResult with found_items (clean status) and missing_items (violations)
        """
        violations, metadata = self._type1_core_logic()
        input_file = self.item_data.get('input_files', ['N/A'])[0]
        total_line_num = metadata.get('total_line_number', 1)

        # Build found_items from clean status (if no violations)
        # For FLT check, found_items represents the clean check result
        found_items = {}
        if not violations:
            # FLT check is clean - add a summary entry
            found_items['FLT_CHECK_CLEAN'] = {
                'name': 'FLT check result is clean - all rules have 0 violations',
                'line_number': total_line_num,
                'file_path': input_file
            }

        # missing_items should be the violations dict (not a list of keys)
        missing_items = violations if violations else {}

        return self.build_complete_output(
            found_items=found_items,
            missing_items=missing_items,
            found_desc=self.FOUND_DESC_TYPE1_4,
            missing_desc=self.MISSING_DESC_TYPE1_4,
            found_reason=self.FOUND_REASON_TYPE1_4,
            missing_reason=self.MISSING_REASON_TYPE1_4
        )

    def _type1_core_logic(self) -> tuple[dict[str, dict], dict]:
        """
        Core Type 1 boolean check logic (shared by Type 1 and Type 4).

        Parses Pegasus_FLT.sum file and extracts FLT rule violations.
        Returns violations as a dict for waiver processing in Type 4.

        Returns:
            Tuple of (violations_dict, metadata_dict)
            violations_dict: {rule_name: {'line_number': ..., 'file_path': ..., 'reason': ...}}
            metadata_dict: {'total_violations': int, 'total_line_number': int}
        """
        data = self._parse_input_files()
        items = data.get('items', [])
        metadata = data.get('metadata', {})
        errors = data.get('errors', [])

        violations = {}

        # Check for parsing errors
        if errors:
            for error in errors:
                violations[f'PARSE_ERROR_{len(violations)}'] = {
                    'line_number': 0,
                    'file_path': self.input_files[0] if self.input_files else 'N/A',
                    'reason': error
                }
            return violations

        # Check total DRC results count
        total_count = metadata.get('total_violations', None)
        total_line_num = metadata.get('total_line_number', 0)
        input_file = self.item_data.get('input_files', ['N/A'])[0]

        if total_count is None:
            # Could not find total DRC results count
            violations['TOTAL_DRC_COUNT_NOT_FOUND'] = {
                'line_number': 0,
                'file_path': input_file,
                'reason': 'Could not find total DRC results count in Pegasus_FLT.sum'
            }
            return violations

        # If total count is not 0, FLT check is not clean
        if total_count != 0:
            # Extract individual rule violations from items
            for item in items:
                rule_name = item.get('name', 'UNKNOWN_RULE')
                violation_count = item.get('violation_count', 0)

                if violation_count > 0:
                    display_name = f"FLT rule: {rule_name} - {violation_count} violations"
                    violations[display_name] = {
                        'name': rule_name,  # Store original rule name for waiver matching
                        'line_number': item.get('line_number', 0),
                        'file_path': item.get('file_path', input_file),
                        'reason': f'FLT rule: {rule_name} - {violation_count} violations'
                    }

        # If no violations found but total count > 0, add a generic violation
        if total_count > 0 and not violations:
            violations['TOTAL_DRC_NONZERO'] = {
                'line_number': total_line_num,
                'file_path': input_file,
                'reason': f'Total DRC results count is {total_count} (expected 0)'
            }

        return violations, metadata

    # =========================================================================
    # Type 4: Boolean Check with Waiver Logic

    def _execute_type4(self) -> CheckResult:
        """
        Type 4: Boolean check with waiver support (reuses Type 1 core logic).

        Verifies that FLT check result is clean, with support for waiving specific
        FLT rule violations. Unwaived violations will cause FAIL.

        Waiver matching:
        - Exact match: rule name matches waive_items entry exactly
        - Pattern match: supports wildcards in waive_items

        Returns:
            CheckResult with found_items, missing_items (unwaived), waived_items, and unused_waivers
        """
        # Step 1: Get violations using Type 1's core logic
        violations, metadata = self._type1_core_logic()
        input_file = self.item_data.get('input_files', ['N/A'])[0]
        total_line_num = metadata.get('total_line_number', 1)

        # Build found_items from clean status (if no violations)
        found_items = {}
        if not violations:
            # FLT check is clean - add a summary entry
            found_items['FLT_CHECK_CLEAN'] = {
                'name': 'FLT check result is clean - all rules have 0 violations',
                'line_number': total_line_num,
                'file_path': input_file
            }

        # Step 2: Parse waiver configuration
        waivers = self.item_data.get('waivers', {})
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)

        # Step 3: Split violations into waived and unwaived
        waived_items = {}
        missing_items = {}
        used_waivers = set()
        # Create a waive_dict mapped by display name for output_builder
        waive_dict_by_display = {}

        for viol_name, viol_data in violations.items():
            # Extract rule name from metadata for waiver matching
            rule_name = viol_data.get('name', viol_name)
            matched_waiver = self.match_waiver_entry(rule_name, waive_dict)
            if matched_waiver:
                waived_items[viol_name] = viol_data
                used_waivers.add(matched_waiver)
                # Store waiver reason mapped by display name
                waive_dict_by_display[viol_name] = waive_dict.get(matched_waiver, '')
            else:
                missing_items[viol_name] = viol_data

        # Step 4: Find unused waivers
        # Build dict with metadata for unused waivers
        unused_waivers = {}
        for w in waive_dict.keys():
            if w not in used_waivers:
                unused_waivers[w] = {
                    'line_number': 0,
                    'file_path': input_file
                }

        # Step 5: Build output
        return self.build_complete_output(
            found_items=found_items,
            missing_items=missing_items,
            waived_items=waived_items,
            unused_waivers=unused_waivers,
            waive_dict=waive_dict_by_display,  # Use display-name-mapped dict
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

    def _execute_type2(self) -> CheckResult:
        """Type 2: Pattern/value check without waiver support."""
        found_items, missing_items = self._type2_core_logic()

        # ⚠️ _type2_core_logic() returns dict[str, dict] for both found_items and missing_items
        # Convert missing_items dict to list of keys for build_complete_output
        return self.build_complete_output(
            found_items=found_items,
            missing_items=list(missing_items.keys()) if isinstance(missing_items, dict) else missing_items,
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

        # Check each required FLT rule pattern
        for pattern in pattern_items:
            matched = False
            for item in items:
                rule_name = item.get('name', '')  # Fixed: use 'name' instead of 'rule_name'
                # EXACT MATCH: pattern_items are specific FLT rule names
                if pattern.lower() == rule_name.lower():
                    violation_count = item.get('violation_count', 0)
                    if violation_count == 0:
                        # Rule found with 0 violations (clean)
                        found_items[rule_name] = {
                            'line_number': item.get('line_number', 0),
                            'file_path': item.get('file_path', 'N/A')
                        }
                    else:
                        # Rule found but has violations
                        missing_items[rule_name] = {
                            'line_number': item.get('line_number', 0),
                            'file_path': item.get('file_path', 'N/A'),
                            'reason': f'FLT rule {rule_name} has {violation_count} violations'
                        }
                    matched = True
                    break

            if not matched:
                # Pattern not found in file
                missing_items[pattern] = {
                    'line_number': 0,
                    'file_path': 'N/A',
                    'reason': f'FLT rule "{pattern}" not found in Pegasus_FLT.sum'
                }

        return found_items, missing_items

    # =========================================================================
    # Type 3: Value Check with Waiver Logic

    def _execute_type3(self) -> CheckResult:
        """Type 3: Pattern/value check with waiver support (reuses Type 2 core logic)."""
        # Step 1: Get found/missing items using Type 2's core logic
        found_items_base, violations = self._type2_core_logic()
        input_file = self.item_data.get('input_files', ['N/A'])[0]

        # Step 2: Parse waiver configuration
        waivers = self.item_data.get('waivers', {})
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)

        # Step 3: Split violations into waived and unwaived
        found_items = {}
        waived_items = {}
        missing_items = {}
        used_waivers = set()
        # Create a waive_dict mapped by display name for output_builder
        waive_dict_by_display = {}

        # Process found_items_base (clean rules, no waiver needed)
        for item_name, item_data in found_items_base.items():
            found_items[item_name] = item_data

        # Process violations with waiver matching
        for viol_name, viol_data in violations.items():
            matched_waiver = self.match_waiver_entry(viol_name, waive_dict)
            if matched_waiver:
                waived_items[viol_name] = viol_data
                used_waivers.add(matched_waiver)
                # Store waiver reason mapped by rule name
                waive_dict_by_display[viol_name] = waive_dict.get(matched_waiver, '')
            else:
                missing_items[viol_name] = viol_data

        # Step 4: Find unused waivers
        # Build dict with metadata for unused waivers
        unused_waivers = {}
        for w in waive_dict.keys():
            if w not in used_waivers:
                unused_waivers[w] = {
                    'line_number': 0,
                    'file_path': input_file
                }

        # Step 5: Build output
        return self.build_complete_output(
            found_items=found_items,
            missing_items=missing_items,
            waived_items=waived_items,
            unused_waivers=unused_waivers,
            waive_dict=waive_dict_by_display,  # Use display-name-mapped dict
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
    checker = Check_12_0_0_31()
    checker.init_checker(Path(__file__))
    result = checker.execute_check()
    checker.write_output(result)
    return 0 if result.is_pass else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())