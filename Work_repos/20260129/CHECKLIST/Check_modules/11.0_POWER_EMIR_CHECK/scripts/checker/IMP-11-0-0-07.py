################################################################################
# Script Name: IMP-11-0-0-07.py
#
# Purpose:
#   Confirm all the PGV views are present in the EMIR scripts.
#
# Logic:
#   - Parse missingLibModelCell.out to extract missing PGV cell model names
#   - Extract total count of missing models and individual cell names
#   - Verify all required PGV views have library model definitions
#   - Support waiver for legacy/third-party cells without PGV requirements
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
# Author: Zhongyu Sun
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
class Check_11_0_0_07(InputFileParserMixin, OutputBuilderMixin, WaiverHandlerMixin, BaseChecker):
    """
    IMP-11-0-0-07: Confirm all the PGV views are present in the EMIR scripts.
    
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
    FOUND_DESC_TYPE1_4 = "All PGV views are present in EMIR scripts"
    MISSING_DESC_TYPE1_4 = "Missing PGV views detected in EMIR scripts"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_DESC_TYPE2_3 = "All missing PGV views are covered by waivers"
    MISSING_DESC_TYPE2_3 = "Unwaived missing PGV views found"
    
    # All Types (waiver description unified)
    WAIVED_DESC = "Missing PGV view waived"
    
    # ⭐ REASON CONSTANTS - Split by Type semantics (API-025)
    # ALL Types pass found_reason/missing_reason, but use different constants
    
    # Type 1/4: Boolean checks - emphasize "found/not found" (existence)
    FOUND_REASON_TYPE1_4 = "No missing PGV views found in missingLibModelCell.out report"
    MISSING_REASON_TYPE1_4 = "Missing PGV views found in missingLibModelCell.out report"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_REASON_TYPE2_3 = "All missing PGV cells are waived (general patterns or explicit waivers)"
    MISSING_REASON_TYPE2_3 = "Missing PGV cells not covered by waiver list"
    
    # Waiver-related (Type 3/4 only)
    WAIVED_BASE_REASON = "Missing PGV view waived - No PGV view is required for this type of cell"
    UNUSED_WAIVER_REASON = "Waiver not matched - no corresponding missing PGV cell found in report"
    
    def __init__(self):
        """Initialize the checker."""
        super().__init__(
            check_module="11.0_POWER_EMIR_CHECK",
            item_id="IMP-11-0-0-07",
            item_desc="Confirm all the PGV views are present in the EMIR scripts."
        )
        # Custom member variables for parsed data
        self._parsed_items: List[Dict[str, Any]] = []
        self._metadata: Dict[str, str] = {}
        self._missing_model_count: int = 0
    
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
        Parse missingLibModelCell.out to extract missing PGV cell model information.
        
        Extracts:
        - Total count of missing models
        - Individual cell model names lacking library definitions
        - Cell instance counts missing model definitions
        
        Returns:
            Dict with parsed data:
            - 'items': List[Dict] - Missing cell models with metadata
            - 'metadata': Dict - File metadata (missing count, instance count)
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
        missing_model_count = 0
        instance_count = 0
        in_missing_section = False
        
        # 3. Parse each input file for missing PGV cell model information
        for file_path in valid_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line_num, line in enumerate(f, 1):
                        line_stripped = line.strip()
                        
                        # Pattern 1: Extract total count of missing models
                        # Regex: ^Number of missing models:\s*(\d+)$
                        count_match = re.match(r'^Number of missing models:\s*(\d+)$', line_stripped)
                        if count_match:
                            missing_model_count = int(count_match.group(1))
                            continue
                        
                        # Pattern 3: Extract count of cell instances missing model definition
                        # Regex: ^Number of cell instances that miss model definition from library \(\.cl\):\s*(\d+)$
                        instance_match = re.match(r'^Number of cell instances that miss model definition from library \(\.cl\):\s*(\d+)$', line_stripped)
                        if instance_match:
                            instance_count = int(instance_match.group(1))
                            continue
                        
                        # Pattern 4: Identify section header for missing models list
                        # Regex: ^The following cell models have no definition from library model files:$
                        if re.match(r'^The following cell models have no definition from library model files:$', line_stripped):
                            in_missing_section = True
                            continue
                        
                        # Pattern 2: Extract cell model names that have no definition
                        # Regex: ^([A-Za-z0-9_]+)$
                        # Only extract if we're in the missing models section
                        if in_missing_section:
                            cell_match = re.match(r'^([A-Za-z0-9_]+)$', line_stripped)
                            if cell_match:
                                cell_name = cell_match.group(1)
                                items.append({
                                    'name': cell_name,
                                    'line_number': line_num,
                                    'file_path': str(file_path),
                                    'type': 'missing_pgv_cell'
                                })
            except Exception as e:
                errors.append(f"Error parsing {file_path}: {str(e)}")
        
        # Store metadata
        metadata['missing_model_count'] = missing_model_count
        metadata['instance_count'] = instance_count
        
        # 4. Store frequently reused data on self
        self._parsed_items = items
        self._metadata = metadata
        self._missing_model_count = missing_model_count
        
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

        Checks if any missing PGV views are reported in missingLibModelCell.out.
        - PASS: No missing PGV views found (violations dict is empty)
        - FAIL: Missing PGV views detected (violations dict contains cell names)

        Returns:
            CheckResult with found_items (empty dict) and missing_items (violation cell names)
        """
        violations = self._type1_core_logic()

        # ⚠️ CRITICAL: found_items MUST be dict[str, dict], NOT list!
        # For this check, found_items represents the absence of violations
        # When no violations exist, we have a "clean" state
        found_items = {}
        if not violations:
            # No violations means the check passed - represent as a clean state
            found_items['no_missing_pgv_views'] = {
                'name': 'no_missing_pgv_views',
                'line_number': 0,
                'file_path': 'N/A'
            }

        # FIXED: Convert violations dict to dict format for missing_items
        missing_items = violations

        return self.build_complete_output(
            found_items=found_items,
            missing_items=missing_items,
            found_desc=self.FOUND_DESC_TYPE1_4,
            missing_desc=self.MISSING_DESC_TYPE1_4,
            found_reason=self.FOUND_REASON_TYPE1_4,
            missing_reason=self.MISSING_REASON_TYPE1_4
        )

    def _type1_core_logic(self) -> dict[str, dict]:
        """
        Core Type 1 boolean check logic (shared by Type 1 and Type 4).

        Parses missingLibModelCell.out to extract missing PGV cell model names.
        Each missing cell is treated as a violation.

        Returns:
            Dict of violations: {cell_name: {'line_number': ..., 'file_path': ..., 'reason': ...}}
            Empty dict if no missing PGV views found (all checks pass).
        """
        data = self._parse_input_files()
        items = data.get('items', [])
        metadata = data.get('metadata', {})
        errors = data.get('errors', [])

        violations = {}

        # Check for parsing errors
        if errors:
            # If there are parsing errors, treat as violations
            for idx, error in enumerate(errors):
                error_key = f'parsing_error_{idx + 1}'
                violations[error_key] = {
                    'line_number': 0,
                    'file_path': 'N/A',
                    'reason': error
                }
            return violations

        # Check if any missing PGV cells were found
        if not items:
            # No missing cells found - this is a PASS condition
            return {}

        # Each item represents a missing PGV cell (violation)
        for item in items:
            cell_name = item.get('name', 'unknown_cell')
            violations[cell_name] = {
                'name': cell_name,
                'line_number': item.get('line_number', 0),
                'file_path': item.get('file_path', 'N/A'),
                'reason': f"Missing PGV view for cell: {cell_name}"
            }

        return violations

    # =========================================================================
    # Type 4: Boolean Check with Waiver Logic

    def _execute_type4(self) -> CheckResult:
        """
        Type 4: Boolean check with waiver support (reuses Type 1 core logic).

        Performs the same boolean check as Type 1, but allows violations to be waived.
        - Violations matching waive_items → waived_items (INFO with [WAIVER])
        - Violations not matching waivers → missing_items (FAIL)
        - Unused waivers → unused_waivers (WARN with [WAIVER])
        - PASS if all violations are waived

        Returns:
            CheckResult with found_items, missing_items, waived_items, and unused_waivers
        """
        # Step 1: Get violations using Type 1's core logic
        violations = self._type1_core_logic()

        # ⚠️ CRITICAL: found_items MUST be dict[str, dict], NOT list!
        # For this check, found_items represents the absence of violations
        found_items = {}
        if not violations:
            # No violations means the check passed - represent as a clean state
            found_items['no_missing_pgv_views'] = {
                'name': 'no_missing_pgv_views',
                'line_number': 0,
                'file_path': 'N/A'
            }

        # Step 2: Parse waiver configuration
        # FIXED: Use waivers.get('waive_items', []) instead of get_waive_items()
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

    def _execute_type2(self) -> CheckResult:
        """Type 2: Pattern/value check without waiver support."""
        found_items, missing_items = self._type2_core_logic()

        # FIXED: Pass dict directly, not list(missing_items.keys())
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
            - found_items: {cell_name: {'line_number': ..., 'file_path': ...}}
            - missing_items: {cell_name: {'line_number': ..., 'file_path': ..., 'reason': ...}}
        """
        data = self._parse_input_files()
        items = data.get('items', [])

        found_items = {}
        missing_items = {}

        # Parse all missing PGV cells from the report
        for item in items:
            cell_name = item.get('name', '')
            line_number = item.get('line_number', 0)
            file_path = item.get('file_path', 'N/A')

            # All items in missingLibModelCell.out are missing PGV cells (violations)
            missing_items[cell_name] = {
                'name': cell_name,
                'line_number': line_number,
                'file_path': file_path,
                'reason': f'Missing PGV view for cell: {cell_name}'
            }

        # If no missing cells found, the check passes (all PGV views present)
        if not missing_items:
            found_items['All PGV views present'] = {
                'name': 'All PGV views present',
                'line_number': 1,
                'file_path': data.get('file_path', 'N/A')
            }

        return found_items, missing_items

    # =========================================================================
    # Type 3: Value Check with Waiver Logic

    def _execute_type3(self) -> CheckResult:
        """Type 3: Pattern/value check with waiver support (reuses Type 2 core logic)."""
        # Step 1: Get found/missing items using Type 2's core logic
        found_items_base, violations = self._type2_core_logic()

        # Step 2: Parse waiver configuration
        # FIXED: Use waivers.get('waive_items', []) instead of get_waive_items()
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)

        # Step 3: Split violations into waived and unwaived
        found_items = {}
        waived_items = {}
        missing_items = {}
        used_waivers = set()

        # Process found_items_base (no waiver needed - all PGV views present)
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
        # FIXED: Pass dict directly, not list(missing_items.keys())
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
    checker = Check_11_0_0_07()
    checker.init_checker(Path(__file__))
    result = checker.execute_check()
    checker.write_output(result)
    return 0 if result.is_pass else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())