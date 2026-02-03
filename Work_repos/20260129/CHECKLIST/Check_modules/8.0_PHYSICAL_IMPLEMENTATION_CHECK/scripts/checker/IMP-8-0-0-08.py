################################################################################
# Script Name: IMP-8-0-0-08.py
#
# Purpose:
#   Confirm max routing layer is correct. Provide max routing layer value in comment field.
#
# Logic:
#   - Parse input files: IMP-8-0-0-08.rpt
#   - Extract technology layer list (techLayerList) containing all available metal layers
#   - Extract signal net routing layers (SignalNetLayerList) for signal routing
#   - Extract power/ground net routing layers (PGNetLayerList) for PG routing
#   - Strip inline comments (text after #) from layer list lines
#   - Extract all M<number> tokens from each layer list using regex pattern
#   - Convert extracted layer numbers to integers and track maximum across all lists
#   - Validate that signal and PG max layers do not exceed technology max layer
#   - Report overall maximum M-layer number found in comment field
#
# Auto Type Detection:
#   Type 1: requirements.value=N/A, waivers.value=N/A/0 → Boolean check
#   Type 2: requirements.value>0, pattern_items exists, waivers.value=N/A/0 → Value comparison
#   Type 3: requirements.value>0, pattern_items exists, waivers.value>0 → Value with waiver logic
#   Type 4: requirements.value=N/A, waivers.value>0 → Boolean with waiver logic
#
# Output Behavior (Type 2/3 - Check README "Output Behavior" section!):
#   existence_check: pattern_items = items that SHOULD EXIST in input files
#     - found_items = patterns found in file
#     - missing_items = patterns NOT found in file
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
# Refactored: 2025-12-24 (Using checker_templates v1.1.0)
#
# Author: chyao
# Date: 2026-01-15
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
class Check_8_0_0_08(InputFileParserMixin, OutputBuilderMixin, WaiverHandlerMixin, BaseChecker):
    """
    IMP-8-0-0-08: Confirm max routing layer is correct. Provide max routing layer value in comment field.
    
    Checking Types:
    - Type 1: requirements=N/A, pattern_items [], waivers=N/A/0 → Boolean Check
    - Type 2: requirements>0, pattern_items [...], waivers=N/A/0 → Value Check
    - Type 3: requirements>0, pattern_items [...], waivers>0 → Value Check with Waiver Logic
    - Type 4: requirements=N/A, waivers>0 → Boolean Check with Waiver Logic
    
    Template Library v1.1.0:
    - Uses InputFileParserMixin for parsing (parse_log_with_patterns, normalize_command)
    - Uses WaiverHandlerMixin for waiver processing (parse_waive_items(waive_items_raw), match_waiver_entry(item, waive_dict))
    - Uses OutputBuilderMixin for result construction (build_complete_output(...))
    """
    
    # =========================================================================
    # DESCRIPTION & REASON CONSTANTS - Split by Type semantics (API-026)
    # =========================================================================
    # Type 1/4: Boolean checks - emphasize "found/not found" (existence)
    FOUND_DESC_TYPE1_4 = "Max routing layer configuration validated"
    MISSING_DESC_TYPE1_4 = "Max routing layer configuration invalid"
    FOUND_REASON_TYPE1_4 = "Routing layer hierarchy validated: SignalNetLayerList max ≤ PGNetLayerList max ≤ techLayerList max"
    MISSING_REASON_TYPE1_4 = "Routing layer hierarchy violation detected or configuration error"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_DESC_TYPE2_3 = "Max routing layer requirement satisfied"
    MISSING_DESC_TYPE2_3 = "Max routing layer requirement not satisfied"
    FOUND_REASON_TYPE2_3 = "Required max routing layer matched and validated against configuration hierarchy"
    MISSING_REASON_TYPE2_3 = "Required max routing layer not satisfied: pattern_items value exceeds techLayerList max or hierarchy violation"
    
    # All Types (waiver description unified)
    WAIVED_DESC = "Max routing layer configuration issue waived"
    
    # Waiver parameters (Type 3/4 ONLY)
    WAIVED_BASE_REASON = "Routing layer configuration exception waived per design team approval"
    UNUSED_WAIVER_REASON = "Waiver entry not matched - no corresponding routing layer violation found"
    
    def __init__(self):
        """Initialize the checker."""
        super().__init__(
            check_module="8.0_PHYSICAL_IMPLEMENTATION_CHECK",
            item_id="IMP-8-0-0-08",
            item_desc="Confirm max routing layer is correct. Provide max routing layer value in comment field."
        )
        # Custom member variables for parsed data
        self._parsed_items: List[Dict[str, Any]] = []
        self._tech_max_layer: Optional[int] = None
        self._signal_max_layer: Optional[int] = None
        self._pg_max_layer: Optional[int] = None
        self._tech_layers: List[str] = []
        self._signal_layers: List[str] = []
        self._pg_layers: List[str] = []
    
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
        except Exception as e:
            # Handle unexpected errors
            return create_check_result(
                is_pass=False,
                item_id=self.item_id,
                item_desc=self.item_desc,
                details=[DetailItem(
                    severity=Severity.FAIL,
                    message=f"Unexpected error during check execution: {str(e)}",
                    reason="Exception occurred during check execution"
                )]
            )
    
    # =========================================================================
    # Input Parsing (Common for All Types)
    # =========================================================================
    
    def _parse_input_files(self) -> Dict[str, Any]:
        """
        Parse input files to extract routing layer configuration.
        
        Extracts metal layer definitions from:
        - techLayerList: All available metal layers in technology
        - SignalNetLayerList: Layers designated for signal routing
        - PGNetLayerList: Layers designated for power/ground routing
        
        Returns:
            Dict with parsed data:
            - 'items': List[Dict] - Layer information with metadata
            - 'metadata': Dict - Max layer info and sources
            - 'errors': List - Any parsing errors encountered
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
            raise ConfigurationError(
                self.create_missing_files_error(["No input files configured"])
            )
        
        # 2. Initialize parsing structures
        items = []
        metadata = {}
        errors = []
        tech_layers = []
        signal_layers = []
        pg_layers = []
        tech_max = None
        signal_max = None
        pg_max = None
        
        # 3. Parse each input file for routing layer information
        # Patterns for layer list extraction
        tech_layer_pattern = re.compile(r'^techLayerList:\s*(.+)$', re.IGNORECASE)
        signal_layer_pattern = re.compile(r'^SignalNetLayerList:\s*(.+?)(?:#.*)?$', re.IGNORECASE)
        pg_layer_pattern = re.compile(r'^PGNetLayerList:\s*(.+?)(?:#.*)?$', re.IGNORECASE)
        metal_layer_pattern = re.compile(r'M(\d+)')
        non_standard_pattern = re.compile(r'^(AP|VIA\d*|RV)$')
        
        for file_path in valid_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line_num, line in enumerate(f, 1):
                        # Try to match techLayerList
                        match = tech_layer_pattern.search(line)
                        if match:
                            layer_list_str = match.group(1).strip()
                            # Split on whitespace and filter non-standard layers
                            all_layers = layer_list_str.split()
                            tech_layers = [layer for layer in all_layers if not non_standard_pattern.match(layer)]
                            
                            # Extract numeric values from M-layers
                            metal_numbers = []
                            for layer in tech_layers:
                                m_match = metal_layer_pattern.match(layer)
                                if m_match:
                                    metal_numbers.append(int(m_match.group(1)))
                            
                            if metal_numbers:
                                tech_max = max(metal_numbers)
                                items.append({
                                    'name': f"techLayerList: M{tech_max}",
                                    'line_number': line_num,
                                    'file_path': str(file_path),
                                    'type': 'techLayerList',
                                    'max_layer': tech_max,
                                    'layer_count': len(metal_numbers)
                                })
                            continue
                        
                        # Try to match SignalNetLayerList
                        match = signal_layer_pattern.search(line)
                        if match:
                            layer_list_str = match.group(1).strip()
                            # Split on whitespace and filter non-standard layers
                            all_layers = layer_list_str.split()
                            signal_layers = [layer for layer in all_layers if not non_standard_pattern.match(layer)]
                            
                            # Extract numeric values from M-layers
                            metal_numbers = []
                            for layer in signal_layers:
                                m_match = metal_layer_pattern.match(layer)
                                if m_match:
                                    metal_numbers.append(int(m_match.group(1)))
                            
                            if metal_numbers:
                                signal_max = max(metal_numbers)
                                items.append({
                                    'name': f"SignalNetLayerList: M{signal_max}",
                                    'line_number': line_num,
                                    'file_path': str(file_path),
                                    'type': 'SignalNetLayerList',
                                    'max_layer': signal_max,
                                    'layer_count': len(metal_numbers)
                                })
                            continue
                        
                        # Try to match PGNetLayerList
                        match = pg_layer_pattern.search(line)
                        if match:
                            layer_list_str = match.group(1).strip()
                            # Split on whitespace and filter non-standard layers
                            all_layers = layer_list_str.split()
                            pg_layers = [layer for layer in all_layers if not non_standard_pattern.match(layer)]
                            
                            # Extract numeric values from M-layers
                            metal_numbers = []
                            for layer in pg_layers:
                                m_match = metal_layer_pattern.match(layer)
                                if m_match:
                                    metal_numbers.append(int(m_match.group(1)))
                            
                            if metal_numbers:
                                pg_max = max(metal_numbers)
                                items.append({
                                    'name': f"PGNetLayerList: M{pg_max}",
                                    'line_number': line_num,
                                    'file_path': str(file_path),
                                    'type': 'PGNetLayerList',
                                    'max_layer': pg_max,
                                    'layer_count': len(metal_numbers)
                                })
                            continue
            except Exception as e:
                errors.append(f"Error parsing {file_path}: {str(e)}")
        
        # 4. Store frequently reused data on self
        self._parsed_items = items
        self._tech_max_layer = tech_max
        self._signal_max_layer = signal_max
        self._pg_max_layer = pg_max
        self._tech_layers = tech_layers
        self._signal_layers = signal_layers
        self._pg_layers = pg_layers
        
        # Build metadata
        metadata = {
            'tech_max': tech_max,
            'signal_max': signal_max,
            'pg_max': pg_max,
            'total_items': len(items)
        }
        
        return {
            'items': items,
            'metadata': metadata,
            'errors': errors
        }
    
    # =========================================================================
    # Type 1: Boolean Check
    # =========================================================================
    
    def _execute_type1(self) -> CheckResult:
        """Type 1: Boolean check without waiver support.
        
        Validates routing layer hierarchy:
        - Extract max metal layers from techLayerList, SignalNetLayerList, PGNetLayerList
        - Validate: SignalNetLayerList max ≤ PGNetLayerList max ≤ techLayerList max
        - PASS if hierarchy is correct, FAIL if violated
        """
        violations = self._type1_core_logic()
        
        # Build found_items from parsed data (layer configuration summary)
        data = self._parse_input_files()
        metadata = data.get('metadata', {})
        
        found_items = {}
        if not violations:
            # No violations - create summary entry for clean configuration
            summary_key = f"Max routing layer: M{metadata.get('tech_max', 'N/A')}"
            found_items[summary_key] = {
                'name': summary_key,
                'line_number': 1,
                'file_path': str(self.item_data.get('input_files', ['N/A'])[0]) if self.item_data.get('input_files') else 'N/A',
                'tech_max': metadata.get('tech_max', 'N/A'),
                'signal_max': metadata.get('signal_max', 'N/A'),
                'pg_max': metadata.get('pg_max', 'N/A')
            }
        
        missing_items = violations
        
        return self.build_complete_output(
            found_items=found_items,
            missing_items=missing_items,
            found_desc=self.FOUND_DESC_TYPE1_4,
            missing_desc=self.MISSING_DESC_TYPE1_4,
            found_reason=self.FOUND_REASON_TYPE1_4,
            missing_reason=self.MISSING_REASON_TYPE1_4
        )
    
    def _type1_core_logic(self) -> Dict[str, Dict]:
        """Core Type 1 boolean check logic (shared by Type 1 and Type 4).
        
        Validates routing layer hierarchy constraints:
        1. Parse techLayerList, SignalNetLayerList, PGNetLayerList
        2. Extract maximum M-layer numbers from each list
        3. Validate hierarchy: signal_max ≤ pg_max ≤ tech_max
        
        Returns:
            Dict of violations: {item_name: {'line_number': ..., 'file_path': ..., 'reason': ...}}
            Empty dict if all checks pass.
        """
        data = self._parse_input_files()
        errors = data.get('errors', [])
        metadata = data.get('metadata', {})
        
        violations = {}
        
        # Check for parsing errors first
        if errors:
            for error in errors:
                error_key = f"Parse error: {error}"
                violations[error_key] = {
                    'line_number': 0,
                    'file_path': str(self.item_data.get('input_files', ['N/A'])[0]) if self.item_data.get('input_files') else 'N/A',
                    'reason': error
                }
            return violations
        
        # Extract max layer values
        tech_max = metadata.get('tech_max')
        signal_max = metadata.get('signal_max')
        pg_max = metadata.get('pg_max')
        
        # Validate that all required layer lists were found
        if tech_max is None:
            violations['Missing techLayerList'] = {
                'line_number': 0,
                'file_path': str(self.item_data.get('input_files', ['N/A'])[0]) if self.item_data.get('input_files') else 'N/A',
                'reason': 'techLayerList not found in input file'
            }
        
        if signal_max is None:
            violations['Missing SignalNetLayerList'] = {
                'line_number': 0,
                'file_path': str(self.item_data.get('input_files', ['N/A'])[0]) if self.item_data.get('input_files') else 'N/A',
                'reason': 'SignalNetLayerList not found in input file'
            }
        
        if pg_max is None:
            violations['Missing PGNetLayerList'] = {
                'line_number': 0,
                'file_path': str(self.item_data.get('input_files', ['N/A'])[0]) if self.item_data.get('input_files') else 'N/A',
                'reason': 'PGNetLayerList not found in input file'
            }
        
        # If any list is missing, return early
        if violations:
            return violations
        
        # Validate hierarchy: signal_max ≤ pg_max ≤ tech_max
        hierarchy_valid = True
        violation_details = []
        
        if signal_max > pg_max:
            hierarchy_valid = False
            violation_details.append(f"SignalNetLayerList max (M{signal_max}) exceeds PGNetLayerList max (M{pg_max})")
        
        if pg_max > tech_max:
            hierarchy_valid = False
            violation_details.append(f"PGNetLayerList max (M{pg_max}) exceeds techLayerList max (M{tech_max})")
        
        if signal_max > tech_max:
            hierarchy_valid = False
            violation_details.append(f"SignalNetLayerList max (M{signal_max}) exceeds techLayerList max (M{tech_max})")
        
        if not hierarchy_valid:
            violation_key = f"Max routing layer hierarchy violation (techLayerList: M{tech_max}, SignalNetLayerList: M{signal_max}, PGNetLayerList: M{pg_max})"
            violations[violation_key] = {
                'line_number': 1,
                'file_path': str(self.item_data.get('input_files', ['N/A'])[0]) if self.item_data.get('input_files') else 'N/A',
                'reason': '; '.join(violation_details)
            }
        
        return violations
    
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
    
    def _type2_core_logic(self) -> Tuple[Dict[str, Dict], Dict[str, Dict]]:
        """
        Core Type 2 pattern matching logic (shared by Type 2 and Type 3).
        
        Returns:
            Tuple of (found_items, missing_items)
            - found_items: {item_name: {'line_number': ..., 'file_path': ...}}
            - missing_items: {item_name: {'line_number': ..., 'file_path': ..., 'reason': ...}}
        """
        data = self._parse_input_files()
        
        requirements = self.item_data.get('requirements', {})
        pattern_items = requirements.get('pattern_items', [])
        
        found_items = {}
        missing_items = {}
        
        # Extract max layer from pattern_items (e.g., "M13" -> 13)
        if not pattern_items:
            missing_items['No pattern_items'] = {
                'line_number': 0,
                'file_path': 'N/A',
                'reason': 'No pattern_items specified in requirements'
            }
            return found_items, missing_items
        
        # Parse required max layer from pattern_items
        required_max_layer_str = pattern_items[0]  # e.g., "M13"
        match = re.match(r'M(\d+)', required_max_layer_str, re.IGNORECASE)
        if not match:
            missing_items[required_max_layer_str] = {
                'line_number': 0,
                'file_path': 'N/A',
                'reason': f'Invalid pattern format: {required_max_layer_str} (expected M<number>)'
            }
            return found_items, missing_items
        
        required_max_layer = int(match.group(1))
        
        # Extract max layers from parsed data
        tech_max = self._tech_max_layer or 0
        signal_max = self._signal_max_layer or 0
        pg_max = self._pg_max_layer or 0
        
        # Get file path from first input file
        input_files = self.item_data.get('input_files', [])
        file_path = str(input_files[0]) if input_files else 'N/A'
        
        # Validation 1: Check if required max layer exceeds technology max
        if required_max_layer > tech_max:
            missing_items[required_max_layer_str] = {
                'line_number': 1,
                'file_path': file_path,
                'reason': f'pattern_items M{required_max_layer} exceeds techLayerList max M{tech_max}'
            }
            return found_items, missing_items
        
        # Validation 2: Check hierarchy: required >= PG >= Signal
        hierarchy_valid = (required_max_layer >= pg_max >= signal_max)
        
        if hierarchy_valid:
            # All validations passed
            detail_str = f"techLayerList: M{tech_max}, SignalNetLayerList: M{signal_max}, PGNetLayerList: M{pg_max}"
            found_items[required_max_layer_str] = {
                'line_number': 1,
                'file_path': file_path,
                'detail': detail_str
            }
        else:
            # Hierarchy violation
            reason_parts = []
            if required_max_layer < pg_max:
                reason_parts.append(f'pattern_items M{required_max_layer} < PGNetLayerList M{pg_max}')
            if required_max_layer < signal_max:
                reason_parts.append(f'pattern_items M{required_max_layer} < SignalNetLayerList M{signal_max}')
            if pg_max < signal_max:
                reason_parts.append(f'PGNetLayerList M{pg_max} < SignalNetLayerList M{signal_max}')
            
            reason = 'Hierarchy violation: ' + ', '.join(reason_parts)
            missing_items[required_max_layer_str] = {
                'line_number': 1,
                'file_path': file_path,
                'reason': reason
            }
        
        return found_items, missing_items
    
    # =========================================================================
    # Type 3: Value Check with Waiver Logic
    # =========================================================================
    
    def _execute_type3(self) -> CheckResult:
        """Type 3: Pattern/value check with waiver support (reuses Type 2 core logic)."""
        # Step 1: Get found/missing items using Type 2's core logic
        found_items_base, violations = self._type2_core_logic()
        
        # Step 2: Parse waiver configuration (FIXED: Use waivers.get() instead of get_waive_items())
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # Step 3: Initialize result containers
        found_items = {}
        waived_items = {}
        missing_items = {}
        used_waivers = set()
        
        # Step 4: Process found_items_base (no waiver needed - already satisfied)
        for item_name, item_data in found_items_base.items():
            found_items[item_name] = item_data
        
        # Step 5: Process violations with waiver matching
        for viol_name, viol_data in violations.items():
            matched_waiver = self.match_waiver_entry(viol_name, waive_dict)
            if matched_waiver:
                waived_items[viol_name] = viol_data
                used_waivers.add(matched_waiver)
            else:
                missing_items[viol_name] = viol_data
        
        # Step 6: Find unused waivers
        unused_waivers = [w for w in waive_dict.keys() if w not in used_waivers]
        
        # Step 7: Build output
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
    
    # =========================================================================
    # Type 4: Boolean Check with Waiver Logic
    # =========================================================================
    
    def _execute_type4(self) -> CheckResult:
        """Type 4: Boolean check with waiver support (reuses Type 1 core logic).
        
        Same hierarchy validation as Type 1, plus waiver classification:
        - Violations matched against waive_items → waived_items (PASS)
        - Unmatched violations → missing_items (FAIL)
        - Unused waivers → WARN
        """
        violations = self._type1_core_logic()
        
        # Build found_items from parsed data (layer configuration summary)
        data = self._parse_input_files()
        metadata = data.get('metadata', {})
        
        found_items = {}
        if not violations:
            # No violations - create summary entry for clean configuration
            summary_key = f"Max routing layer: M{metadata.get('tech_max', 'N/A')}"
            found_items[summary_key] = {
                'name': summary_key,
                'line_number': 1,
                'file_path': str(self.item_data.get('input_files', ['N/A'])[0]) if self.item_data.get('input_files') else 'N/A',
                'tech_max': metadata.get('tech_max', 'N/A'),
                'signal_max': metadata.get('signal_max', 'N/A'),
                'pg_max': metadata.get('pg_max', 'N/A')
            }
        
        # FIXED: Use waivers.get() instead of get_waive_items()
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
# Entry Point
# =========================================================================

def main():
    """Main entry point."""
    checker = Check_8_0_0_08()
    checker.init_checker(Path(__file__))
    result = checker.execute_check()
    checker.write_output(result)
    return 0 if result.is_pass else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())