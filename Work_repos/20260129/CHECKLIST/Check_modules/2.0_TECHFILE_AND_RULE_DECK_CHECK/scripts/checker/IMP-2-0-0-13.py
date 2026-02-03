################################################################################
# Script Name: IMP-2-0-0-13.py
#
# Purpose:
#   List Spice Model used for PGV generation. eg: tsmc3gp.a.4/models/spectre_v1d0_2p6/ir_em.scs
#
# Logic:
#   - Parse command_list.btxt to extract SPICE model path from "spice_models" command
#   - Extract model version identifier from absolute path (substring after "PDK/")
#   - For Type 1/4: Verify SPICE model path exists in command list
#   - For Type 2/3: Compare extracted model version against golden reference from pattern_items
#   - Support waiver for model version mismatches (Type 3/4)
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
# Author: Chenwei Fan
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
class Check_2_0_0_13(InputFileParserMixin, OutputBuilderMixin, WaiverHandlerMixin, BaseChecker):
    """
    IMP-2-0-0-13: List Spice Model used for PGV generation. eg: tsmc3gp.a.4/models/spectre_v1d0_2p6/ir_em.scs
    
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
    FOUND_DESC_TYPE1_4 = "SPICE model version found in command list"
    MISSING_DESC_TYPE1_4 = "SPICE model version not found in command list"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_DESC_TYPE2_3 = "SPICE model version matched expected golden value"
    MISSING_DESC_TYPE2_3 = "SPICE model version does not match expected golden value"
    
    # All Types (waiver description unified)
    WAIVED_DESC = "SPICE model version mismatch waived"
    
    # ⭐ REASON CONSTANTS - Split by Type semantics (API-025)
    # ALL Types pass found_reason/missing_reason, but use different constants
    
    # Type 1/4: Boolean checks - emphasize "found/not found" (existence)
    FOUND_REASON_TYPE1_4 = "SPICE model path successfully extracted from command_list.btxt"
    MISSING_REASON_TYPE1_4 = "SPICE model path not found in command_list.btxt or spice_models command missing"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_REASON_TYPE2_3 = "SPICE model version matched and validated against golden reference"
    MISSING_REASON_TYPE2_3 = "SPICE model version mismatch - actual version does not satisfy expected golden reference"
    
    # Waiver-related (Type 3/4 only)
    WAIVED_BASE_REASON = "SPICE model version mismatch waived per design team approval"
    UNUSED_WAIVER_REASON = "Waiver not matched - no corresponding SPICE model version mismatch found"
    
    def __init__(self):
        """Initialize the checker."""
        super().__init__(
            check_module="2.0_TECHFILE_AND_RULE_DECK_CHECK",
            item_id="IMP-2-0-0-13",
            item_desc="List Spice Model used for PGV generation. eg: tsmc3gp.a.4/models/spectre_v1d0_2p6/ir_em.scs"
        )
        # Custom member variables for parsed data
        self._parsed_items: List[Dict[str, Any]] = []
        self._metadata: Dict[str, str] = {}
        self._spice_model: Optional[str] = None
        self._spice_path: Optional[str] = None
    
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
        Parse command_list.btxt to extract SPICE model path and version.
        
        Extraction Logic:
        1. Search for "spice_models" command in command_list.btxt
        2. Extract absolute SPICE model path after "spice_models" keyword
        3. Extract model version identifier (substring after "PDK/")
        
        Returns:
            Dict with parsed data:
            - 'items': List[Dict] - SPICE model information with metadata
            - 'metadata': Dict - File metadata (spice_path, spice_model)
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
        spice_path = None
        spice_model = None
        
        # 3. Parse each input file for SPICE model information
        for file_path in valid_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line_num, line in enumerate(f, 1):
                        # Pattern 1: Extract SPICE model path from "spice_models" command
                        match = re.search(r'spice_models\s+(.+)', line, re.IGNORECASE)
                        if match:
                            spice_path = match.group(1).strip()
                            
                            # Pattern 2: Extract model version from absolute path (after "PDK/")
                            pdk_match = re.search(r'PDK/(.+)$', spice_path)
                            if pdk_match:
                                spice_model = pdk_match.group(1).strip()
                            else:
                                # If no PDK/ found, use the entire path as model
                                spice_model = spice_path
                            
                            # Store as item with metadata
                            items.append({
                                'name': spice_model,
                                'line_number': line_num,
                                'file_path': str(file_path),
                                'type': 'spice_model',
                                'full_path': spice_path
                            })
                            
                            # Store in metadata for easy access
                            metadata['spice_path'] = spice_path
                            metadata['spice_model'] = spice_model
                            
                            break  # Only need first occurrence
            except Exception as e:
                errors.append(f"Error parsing {file_path}: {str(e)}")
        
        # 4. Store frequently reused data on self
        self._parsed_items = items
        self._metadata = metadata
        self._spice_path = spice_path
        self._spice_model = spice_model
        
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

        Verifies that SPICE model path exists in command_list.btxt.
        PASS if spice_models command is found and model path can be extracted.
        FAIL if spice_models command is missing or path extraction fails.
        """
        violations = self._type1_core_logic()

        # Build found_items from successfully extracted SPICE model paths
        data = self._parse_input_files()
        items = data.get('items', [])

        # ⚠️ CRITICAL: found_items MUST be dict[str, dict], NOT list!
        found_items = {}
        for item in items:
            if item['name'] not in violations:
                found_items[item['name']] = {
                    'line_number': item.get('line_number', 0),
                    'file_path': item.get('file_path', 'N/A')
                }

        # FIXED: missing_items should be dict format {name: metadata}
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

        Parses command_list.btxt to verify SPICE model path exists.

        Returns:
            Dict of violations: {item_name: {'line_number': ..., 'file_path': ..., 'reason': ...}}
            Empty dict if SPICE model path is successfully extracted.
        """
        data = self._parse_input_files()
        items = data.get('items', [])
        errors = data.get('errors', [])

        violations = {}

        # Check for parsing errors (missing spice_models command or extraction failure)
        if errors:
            for error in errors:
                error_key = error.get('name', 'SPICE Model Not Found')
                violations[error_key] = {
                    'line_number': error.get('line_number', 0),
                    'file_path': error.get('file_path', 'N/A'),
                    'reason': error.get('reason', 'spice_models command missing or path extraction failed')
                }

        # If no items found and no specific errors, report generic failure
        if not items and not errors:
            violations['SPICE Model Not Found'] = {
                'line_number': 0,
                'file_path': 'N/A',
                'reason': 'spice_models command missing in command_list.btxt'
            }

        return violations

    # =========================================================================
    # Type 4: Boolean Check with Waiver Logic
    # =========================================================================

    def _execute_type4(self) -> CheckResult:
        """
        Type 4: Boolean check with waiver support (reuses Type 1 core logic).

        Verifies SPICE model path exists in command_list.btxt with waiver support.
        - If model path found → PASS (INFO01)
        - If model path not found and matches waive_items → PASS with [WAIVER] tag
        - If model path not found and NOT in waive_items → FAIL (ERROR01)
        - Unused waivers → WARN with [WAIVER] tag

        PASS if model exists OR all missing models are waived.
        """
        violations = self._type1_core_logic()

        # Build found_items from successfully extracted SPICE model paths
        data = self._parse_input_files()
        items = data.get('items', [])

        # ⚠️ CRITICAL: found_items MUST be dict[str, dict], NOT list!
        found_items = {}
        for item in items:
            if item['name'] not in violations:
                found_items[item['name']] = {
                    'line_number': item.get('line_number', 0),
                    'file_path': item.get('file_path', 'N/A')
                }

        # FIXED: Use waivers.get('waive_items', []) instead of get_waive_items()
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
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

        unused_waivers = [w for w in waive_dict.keys() if w not in used_waivers]

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
            - found_items: {item_name: {'line_number': ..., 'file_path': ...}}
            - missing_items: {item_name: {'line_number': ..., 'file_path': ..., 'reason': ...}}
        """
        data = self._parse_input_files()
        items = data.get('items', [])

        requirements = self.item_data.get('requirements', {})
        pattern_items = requirements.get('pattern_items', [])

        found_items = {}
        missing_items = {}

        # Get golden SPICE model version (expected model path)
        if not pattern_items:
            missing_items['No golden reference'] = {
                'line_number': 0,
                'file_path': 'N/A',
                'reason': 'No golden SPICE model version defined in pattern_items'
            }
            return found_items, missing_items

        golden_spice = pattern_items[0]  # Expected: "tsmc5g.a.12/models/spectre_v1d2_2p5/ir_em.scs"

        # Extract actual SPICE model version from parsed items
        if not items:
            missing_items[golden_spice] = {
                'line_number': 0,
                'file_path': 'N/A',
                'reason': f'SPICE model not found in command_list.btxt (Expected: {golden_spice})'
            }
            return found_items, missing_items

        # Get the extracted SPICE model path from parsed data
        actual_spice = items[0].get('name', '')
        line_number = items[0].get('line_number', 0)
        file_path = items[0].get('file_path', 'N/A')

        # Compare actual vs golden SPICE model version
        if actual_spice.lower() == golden_spice.lower():
            # Match - SPICE model version is correct
            found_items[actual_spice] = {
                'line_number': line_number,
                'file_path': file_path
            }
        else:
            # Mismatch - SPICE model version does not match golden reference
            missing_items[actual_spice] = {
                'line_number': line_number,
                'file_path': file_path,
                'reason': f'SPICE model version mismatch: Found={actual_spice}, Expected={golden_spice}'
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
        # FIXED: Use waivers.get('waive_items', []) instead of get_waive_items()
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)

        # Step 3: Split violations into waived and unwaived
        found_items = {}
        waived_items = {}
        missing_items = {}
        used_waivers = set()

        # Process found_items_base (no waiver needed - already matching golden)
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
    checker = Check_2_0_0_13()
    checker.init_checker(Path(__file__))
    result = checker.execute_check()
    checker.write_output(result)
    return 0 if result.is_pass else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())