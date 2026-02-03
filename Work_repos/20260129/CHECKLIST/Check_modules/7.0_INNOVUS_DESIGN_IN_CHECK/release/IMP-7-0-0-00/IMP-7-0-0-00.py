################################################################################
# Script Name: IMP-7-0-0-00.py
#
# Purpose:
#   Block name (e.g: cdn_hs_phy_data_slice)
#
# Logic:
#   - Parse block identification report to extract block name information
#   - Extract block name identifier, prefix component, and core block type
#   - Verify block name presence and format against requirements
#   - Support waiver for specific block name exemptions
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
class Check_7_0_0_00(InputFileParserMixin, OutputBuilderMixin, WaiverHandlerMixin, BaseChecker):
    """
    IMP-7-0-0-00: Block name (e.g: cdn_hs_phy_data_slice)
    
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
    
    # Output description constants
    ITEM_DESC = "Block name (e.g: cdn_hs_phy_data_slice)"
    FOUND_DESC_TYPE1_4 = "Block name found in implementation report"
    FOUND_DESC_TYPE2_3 = "Required block name pattern matched requirements"
    FOUND_REASON_TYPE1_4 = "Block name entry found and validated in implementation report"
    FOUND_REASON_TYPE2_3 = "Required block name pattern matched and validated in report"
    MISSING_DESC_TYPE1_4 = "Block name not found in implementation report"
    MISSING_DESC_TYPE2_3 = "Expected block name pattern not satisfied (1/2 missing)"
    MISSING_REASON_TYPE1_4 = "Block name entry not found or invalid format in implementation report"
    MISSING_REASON_TYPE2_3 = "Expected block name pattern not satisfied or missing from report"
    WAIVED_DESC = "Block name check waived"
    WAIVED_BASE_REASON = "Block name verification waived per design team approval"
    UNUSED_DESC = "Unused block name waiver entries"
    UNUSED_WAIVER_REASON = "Waiver not matched - no corresponding block name issue found"
    
    def __init__(self):
        """Initialize the checker."""
        super().__init__(
            check_module="7.0_INNOVUS_DESIGN_IN_CHECK",
            item_id="IMP-7-0-0-00",
            item_desc="Block name (e.g: cdn_hs_phy_data_slice)"
        )
        # Domain-specific member variables for parsed data
        self._parsed_items: List[Dict[str, Any]] = []
        self._block_names: List[str] = []
        self._block_metadata: Dict[str, str] = {}
    
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
        Parse block identification report to extract block name information.
        
        Extracts block name identifier, prefix component, and core block type
        from implementation report using three base patterns:
        1. Full block name identifier: ^Block name:\s*(.+)$
        2. Block prefix component: ^Block name:\s*(\w+)_.*$
        3. Core block type component: ^Block name:\s*.*_(cdn_hs_phy_data_slice)_.*$
        
        Returns:
            Dict with parsed data:
            - 'items': List[Dict] - Block name entries with metadata
            - 'metadata': Dict - File metadata (design info, tool version)
            - 'errors': List - Parsing errors encountered
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
        block_names = []
        block_prefixes = []
        core_block_types = []
        
        # 3. Parse each input file for block name information
        for file_path in valid_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line_num, line in enumerate(f, 1):
                        line = line.strip()
                        
                        # Pattern 1: Extract full block name identifier
                        block_name_match = re.search(r'^Block name:\s*(.+)$', line)
                        if block_name_match:
                            block_name = block_name_match.group(1).strip()
                            items.append({
                                'name': block_name,
                                'line_number': line_num,
                                'file_path': str(file_path),
                                'type': 'block_name',
                                'line_content': line
                            })
                            block_names.append(block_name)
                            
                            # Pattern 2: Extract block prefix component
                            prefix_match = re.search(r'^Block name:\s*(\w+)_.*$', line)
                            if prefix_match:
                                prefix = prefix_match.group(1)
                                block_prefixes.append(prefix)
                                items.append({
                                    'name': prefix,
                                    'line_number': line_num,
                                    'file_path': str(file_path),
                                    'type': 'block_prefix',
                                    'line_content': line
                                })
                            
                            # Pattern 3: Extract core block type component
                            core_type_match = re.search(r'^Block name:\s*.*_(cdn_hs_phy_data_slice)_.*$', line)
                            if core_type_match:
                                core_type = core_type_match.group(1)
                                core_block_types.append(core_type)
                                items.append({
                                    'name': core_type,
                                    'line_number': line_num,
                                    'file_path': str(file_path),
                                    'type': 'core_block_type',
                                    'line_content': line
                                })
                        
            except Exception as e:
                errors.append(f"Error parsing {file_path}: {str(e)}")
        
        # 4. Store frequently reused data on self
        self._parsed_items = items
        self._block_names = block_names
        self._block_metadata = {
            'block_prefixes': block_prefixes,
            'core_block_types': core_block_types
        }
        
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
        """Type 1: Boolean check without waiver support."""
        # Core boolean logic
        violations = self._type1_core_logic()

        # Get parsed data to build found_items from valid block names
        data = self._parse_input_files()
        items = data.get('items', [])

        # Build found_items from valid block names (those that passed validation)
        # Convert list to dict with metadata
        found_items = {}
        for item in items:
            item_name = item.get('name', str(item))
            if item_name not in violations:
                found_items[item_name] = {
                    'name': item_name,
                    'line_number': item.get('line_number', 0),
                    'file_path': item.get('file_path', 'N/A')
                }

        # Convert violations to missing_items dict format
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

        Returns:
            Dict of violations: {item_name: {'line_number': ..., 'file_path': ..., 'reason': ...}}
            Empty dict if all checks pass.
        """
        data = self._parse_input_files()
        items = data.get('items', [])
        errors = data.get('errors', [])

        violations = {}

        # Check for parsing errors first
        if errors:
            violations['block_name_report'] = {
                'line_number': 0,
                'file_path': 'N/A',
                'reason': f"Report parsing failed: {'; '.join(errors)}"
            }
            return violations

        # If no items found, this is a violation (no block name information)
        if not items:
            violations['block_name'] = {
                'line_number': 0,
                'file_path': 'N/A',
                'reason': 'Block name entry not found or invalid format in implementation report'
            }
            return violations

        # Validate each block name entry
        for item in items:
            item_name = item.get('name', '')
            line_number = item.get('line_number', 0)
            file_path = item.get('file_path', 'N/A')

            # Check if block name is empty or invalid
            if not item_name or item_name.strip() == '':
                violations['empty_block_name'] = {
                    'line_number': line_number,
                    'file_path': file_path,
                    'reason': 'Empty or missing block name identifier'
                }
                continue

            # Validate block name format (should contain meaningful identifiers)
            # Block names typically follow patterns like: cdn_hs_phy_data_slice, CDN_104H_cdn_hs_phy_data_slice_EW
            if len(item_name.strip()) < 3:
                violations[item_name] = {
                    'line_number': line_number,
                    'file_path': file_path,
                    'reason': 'Block name too short or invalid format'
                }
                continue

            # Check for invalid characters (block names should be alphanumeric with underscores)
            if not re.match(r'^[a-zA-Z0-9_]+$', item_name.strip()):
                violations[item_name] = {
                    'line_number': line_number,
                    'file_path': file_path,
                    'reason': 'Block name contains invalid characters (only alphanumeric and underscore allowed)'
                }
                continue

        return violations

    # =========================================================================
    # Type 4: Boolean Check with Waiver Logic
    # =========================================================================

    def _execute_type4(self) -> CheckResult:
        """Type 4: Boolean check with waiver support (reuses Type 1 core logic)."""
        # Step 1: Get violations using Type 1's core logic
        violations = self._type1_core_logic()

        # found_items: objects that PASS the check (same semantics as Type 1)
        data = self._parse_input_files()
        items = data.get('items', [])

        # Build found_items from valid block names (those that passed validation)
        # Convert list to dict with metadata
        found_items = {}
        for item in items:
            item_name = item.get('name', str(item))
            if item_name not in violations:
                found_items[item_name] = {
                    'name': item_name,
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
        # Core pattern matching logic
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

        # Block name pattern matching - use EXACT MATCH for block names
        for pattern in pattern_items:
            matched = False
            for item in items:
                item_name = item.get('name', '')
                # EXACT MATCH (case-insensitive) for block name patterns
                if pattern.lower() == item_name.lower():
                    # Convert list to dict with metadata
                    found_items[item_name] = {
                        'name': item_name,
                        'line_number': item.get('line_number', 0),
                        'file_path': item.get('file_path', 'N/A')
                    }
                    matched = True
                    break

            if not matched:
                missing_items[pattern] = {
                    'line_number': 0,
                    'file_path': 'N/A',
                    'reason': f'Block name pattern "{pattern}" not found in report'
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

        # Step 3: Process found items (no waiver needed)
        found_items = {}
        for item_name, item_data in found_items_base.items():
            found_items[item_name] = item_data

        # Step 4: Split violations into waived and unwaived
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

        # Step 5: Find unused waivers
        unused_waivers = [w for w in waive_dict.keys() if w not in used_waivers]

        # Step 6: Build output
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
    checker = Check_7_0_0_00()
    checker.init_checker(Path(__file__))
    result = checker.execute_check()
    checker.write_output(result)
    return 0 if result.is_pass else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())