################################################################################
# Script Name: MIG-IMP-8-1-0-00.py
#
# Purpose:
#   Confirm followed the general slice top metal and top routing layer spec. (check the Note)
#
# Logic:
#   - Parse input files: IMP-8-0-0-08.rpt
#   - Extract techLayerList to identify all available metal layers
#   - Determine top metal layer (highest M-number, excluding AP/special layers)
#   - Extract SignalNetLayerList to identify signal routing layers
#   - Determine top signal routing layer (highest M-number in signal list)
#   - Validate that top routing layer is within acceptable range of top metal layer
#   - Apply specification rule: top_routing should be within 1-2 layers of top_metal
#   - Report violations if top routing layer is too far from top metal layer
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
# Refactored: 2025-12-24 (Using checker_templates v1.1.0)
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
from checker_templates.input_file_parser_template import InputFileParserMixin


# MANDATORY: Inherit mixins in correct order (InputFileParserMixin first if used)
class Check_MIG_8_1_0_00(InputFileParserMixin, OutputBuilderMixin, WaiverHandlerMixin, BaseChecker):
    """
    MIG-IMP-8-1-0-00: Confirm followed the general slice top metal and top routing layer spec. (check the Note)
    
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
    # DESCRIPTION & REASON CONSTANTS - Split by Type semantics (API-026)
    # =========================================================================
    # Type 1/4: Boolean checks - emphasize "found/not found" (existence)
    FOUND_DESC_TYPE1_4 = "Routing layer configuration validated"
    MISSING_DESC_TYPE1_4 = "Routing layer specification violations detected"
    FOUND_REASON_TYPE1_4 = "Top routing layer is within acceptable range of top metal layer"
    MISSING_REASON_TYPE1_4 = "Top routing layer does not meet specification requirements"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_DESC_TYPE2_3 = "Layer configuration matches specification"
    MISSING_DESC_TYPE2_3 = "Layer configuration does not satisfy requirements"
    FOUND_REASON_TYPE2_3 = "Routing layer configuration validated against specification"
    MISSING_REASON_TYPE2_3 = "Routing layer specification not satisfied"
    
    # All Types (waiver description unified)
    WAIVED_DESC = "Waived routing layer violations"
    
    # Waiver parameters (Type 3/4 ONLY)
    WAIVED_BASE_REASON = "Routing layer violation waived per design approval"
    
    def __init__(self):
        """Initialize the checker."""
        super().__init__(
            check_module="8.1_PHYSICAL_IMPLEMENTATION_CHECK",
            item_id="MIG-IMP-8-1-0-00",
            item_desc="Confirm followed the general slice top metal and top routing layer spec. (check the Note)"
        )
        # Custom member variables for parsed data
        self._parsed_items: List[Dict[str, Any]] = []
        self._top_metal_layer: Optional[str] = None
        self._top_routing_layer: Optional[str] = None
        self._tech_layers: List[str] = []
        self._signal_layers: List[str] = []
    
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
        
        Extracts:
        - techLayerList: All available metal layers
        - SignalNetLayerList: Routing layers for signal nets
        - PGNetLayerList: Routing layers for PG nets (informational)
        
        Returns:
            Dict with parsed data including:
            - 'items': List[Dict] - Validation results with metadata
            - 'metadata': Dict - Layer configuration metadata
            - 'errors': List - Parsing errors
        """
        # 1. Validate inputs - IMPORTANT: returns tuple (valid_files_list, missing_files_list)
        valid_files, missing_files = self.validate_input_files()
        
        # FIXED: KNOWN_ISSUE_LOGIC-001 - Explicitly check for empty list
        if not valid_files or len(valid_files) == 0:
            raise ConfigurationError(
                self.create_missing_files_error(missing_files if missing_files else ["No valid input files found"])
            )
        
        if missing_files:
            raise ConfigurationError(
                self.create_missing_files_error(missing_files)
            )
        
        # 2. Parse routing layer configuration
        all_items = []
        metadata = {}
        errors = []
        
        # Patterns for parsing
        pattern_tech_layers = re.compile(r'^techLayerList:\s*(.+)$')
        pattern_signal_layers = re.compile(r'^SignalNetLayerList:\s*(.+?)(?:\s*#.*)?$')
        pattern_pg_layers = re.compile(r'^PGNetLayerList:\s*(.+?)(?:\s*#.*)?$')
        pattern_metal_number = re.compile(r'M(\d+)')
        
        for file_path in valid_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line_num, line in enumerate(f, 1):
                        line = line.strip()
                        
                        # Parse technology layer list
                        if match := pattern_tech_layers.search(line):
                            layers_str = match.group(1).strip()
                            self._tech_layers = layers_str.split()
                            
                            # Extract metal layers (exclude AP and special layers)
                            metal_layers = []
                            for layer in self._tech_layers:
                                if m := pattern_metal_number.match(layer):
                                    metal_layers.append((int(m.group(1)), layer))
                            
                            if metal_layers:
                                # Sort by metal number and get highest
                                metal_layers.sort(key=lambda x: x[0])
                                self._top_metal_layer = metal_layers[-1][1]
                                metadata['top_metal_layer'] = self._top_metal_layer
                                metadata['top_metal_number'] = metal_layers[-1][0]
                                metadata['total_tech_layers'] = len(self._tech_layers)
                        
                        # Parse signal net routing layer list
                        elif match := pattern_signal_layers.search(line):
                            layers_str = match.group(1).strip()
                            self._signal_layers = layers_str.split()
                            
                            # Extract metal layers and find highest
                            metal_layers = []
                            for layer in self._signal_layers:
                                if m := pattern_metal_number.match(layer):
                                    metal_layers.append((int(m.group(1)), layer))
                            
                            if metal_layers:
                                # Sort by metal number and get highest
                                metal_layers.sort(key=lambda x: x[0])
                                self._top_routing_layer = metal_layers[-1][1]
                                metadata['top_routing_layer'] = self._top_routing_layer
                                metadata['top_routing_number'] = metal_layers[-1][0]
                                metadata['signal_routing_layers_count'] = len(self._signal_layers)
                        
                        # Parse PG net routing layer list (informational)
                        elif match := pattern_pg_layers.search(line):
                            layers_str = match.group(1).strip()
                            pg_layers = layers_str.split()
                            metadata['pg_routing_layers_count'] = len(pg_layers)
            
            except Exception as e:
                errors.append(f"Error parsing {file_path}: {str(e)}")
        
        # 3. Validate layer configuration
        if not self._top_metal_layer:
            errors.append("Top metal layer not found in techLayerList")
        
        if not self._top_routing_layer:
            errors.append("Top routing layer not found in SignalNetLayerList")
        
        # 4. Check specification compliance
        if self._top_metal_layer and self._top_routing_layer:
            top_metal_num = metadata.get('top_metal_number', 0)
            top_routing_num = metadata.get('top_routing_number', 0)
            
            # Specification: top_routing should be within 1-2 layers of top_metal
            # Rule: top_metal - 2 <= top_routing <= top_metal
            layer_diff = top_metal_num - top_routing_num
            
            if layer_diff < 0 or layer_diff > 2:
                # Violation detected
                violation_name = f"Top routing layer {self._top_routing_layer} (M{top_routing_num}) is {layer_diff} layers from top metal {self._top_metal_layer} (M{top_metal_num})"
                all_items.append({
                    'name': violation_name,
                    'line_number': 0,  # Configuration-level violation
                    'file_path': str(valid_files[0]) if valid_files else 'N/A',
                    'violation_type': 'layer_spacing',
                    'layer_diff': layer_diff,
                    'top_metal': self._top_metal_layer,
                    'top_routing': self._top_routing_layer
                })
            else:
                # Configuration is valid
                valid_name = f"Top routing layer {self._top_routing_layer} is within acceptable range of top metal {self._top_metal_layer} (difference: {layer_diff} layers)"
                all_items.append({
                    'name': valid_name,
                    'line_number': 0,
                    'file_path': str(valid_files[0]) if valid_files else 'N/A',
                    'violation_type': 'valid',
                    'layer_diff': layer_diff,
                    'top_metal': self._top_metal_layer,
                    'top_routing': self._top_routing_layer
                })
        
        # 5. Store on self
        self._parsed_items = all_items
        
        # 6. Return aggregated dict
        return {
            'items': all_items,
            'metadata': metadata,
            'errors': errors
        }
    
    # =========================================================================
    # Type 1: Boolean Check
    # =========================================================================
    
    def _execute_type1(self) -> CheckResult:
        """
        Type 1: Boolean Check.
        
        Validates routing layer configuration exists and meets specifications.
        Does NOT use pattern_items for searching.
        
        Returns:
            CheckResult with is_pass based on check logic
        """
        # Parse input
        data = self._parse_input_files()
        items = data.get('items', [])
        errors = data.get('errors', [])
        
        # Check for parsing errors
        if errors:
            return self.build_complete_output(
                found_items={},
                missing_items=errors,
                found_desc=self.FOUND_DESC_TYPE1_4,
                missing_desc=self.MISSING_DESC_TYPE1_4,
                found_reason=self.FOUND_REASON_TYPE1_4,
                missing_reason=self.MISSING_REASON_TYPE1_4
            )
        
        # Separate valid configurations from violations
        found_items = {}
        missing_items = []
        
        for item in items:
            if item.get('violation_type') == 'valid':
                # Valid configuration
                found_items[item['name']] = {
                    'name': item['name'],
                    'line_number': item.get('line_number', 0),
                    'file_path': item.get('file_path', 'N/A')
                }
            else:
                # Violation detected
                missing_items.append(item['name'])
        
        # Use template helper
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
        found_items = patterns found; missing_items = patterns not found.
        
        Returns:
            CheckResult with is_pass based on value comparison
        """
        # Parse input
        data = self._parse_input_files()
        items = data.get('items', [])
        errors = data.get('errors', [])
        
        # Get requirements
        pattern_items = self.item_data.get('requirements', {}).get('pattern_items', [])
        
        # Check for parsing errors
        if errors:
            return self.build_complete_output(
                found_items={},
                missing_items=errors,
                found_desc=self.FOUND_DESC_TYPE2_3,
                missing_desc=self.MISSING_DESC_TYPE2_3,
                found_reason=self.FOUND_REASON_TYPE2_3,
                missing_reason=self.MISSING_REASON_TYPE2_3
            )
        
        # Separate valid configurations from violations
        found_items = {}
        missing_items = []
        
        for item in items:
            if item.get('violation_type') == 'valid':
                # Valid configuration
                found_items[item['name']] = {
                    'name': item['name'],
                    'line_number': item.get('line_number', 0),
                    'file_path': item.get('file_path', 'N/A')
                }
            else:
                # Violation detected
                missing_items.append(item['name'])
        
        # Use template helper (auto-handles waiver=0)
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
        
        Returns:
            CheckResult with FAIL for unwaived, INFO for waived items
        """
        # Parse input
        parsed_data = self._parse_input_files()
        items = parsed_data.get('items', [])
        errors = parsed_data.get('errors', [])
        
        # FIXED: KNOWN_ISSUE_API-016 - Use waivers.get() directly to preserve dict format
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # Check for parsing errors
        if errors:
            return self.build_complete_output(
                found_items={},
                missing_items=errors,  # FIXED: KNOWN_ISSUE_API-021 - Use missing_items parameter
                waived_items=[],
                waive_dict=waive_dict,
                unused_waivers=[],
                found_desc=self.FOUND_DESC_TYPE2_3,
                missing_desc=self.MISSING_DESC_TYPE2_3,
                waived_desc=self.WAIVED_DESC,
                found_reason=self.FOUND_REASON_TYPE2_3,
                missing_reason=self.MISSING_REASON_TYPE2_3,
                waived_base_reason=self.WAIVED_BASE_REASON
            )
        
        # Separate valid configurations from violations
        found_items = {}
        violations = []
        
        for item in items:
            if item.get('violation_type') == 'valid':
                # Valid configuration
                found_items[item['name']] = {
                    'name': item['name'],
                    'line_number': item.get('line_number', 0),
                    'file_path': item.get('file_path', 'N/A')
                }
            else:
                # Violation detected
                violations.append(item['name'])
        
        # Separate waived/unwaived using template helper
        waived_items = []
        unwaived_items = []
        
        # FIXED: KNOWN_ISSUE_API-017 - waive_dict keys are item names (strings)
        for violation_name in violations:
            if self.match_waiver_entry(violation_name, waive_dict):
                waived_items.append(violation_name)
            else:
                unwaived_items.append(violation_name)
        
        # Find unused waivers - FIXED: KNOWN_ISSUE_API-017 - Use waive_dict.keys() for names
        used_names = set(waived_items)
        unused_waivers = [name for name in waive_dict.keys() if name not in used_names]
        
        # Use template helper for automatic output formatting
        # FIXED: KNOWN_ISSUE_API-021 - Use missing_items parameter instead of unwaived_items
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
            waived_base_reason=self.WAIVED_BASE_REASON
        )
    
    # =========================================================================
    # Type 4: Boolean Check with Waiver Logic
    # =========================================================================
    
    def _execute_type4(self) -> CheckResult:
        """
        Type 4: Boolean check with waiver support (Type 1 + waiver).
        
        Same boolean check as Type 1 (no pattern_items), plus waiver classification.
        
        Returns:
            CheckResult with waiver logic applied
        """
        # Parse input
        data = self._parse_input_files()
        items = data.get('items', [])
        errors = data.get('errors', [])
        
        # FIXED: KNOWN_ISSUE_API-016 - Use waivers.get() directly to preserve dict format
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # Check for parsing errors
        if errors:
            return self.build_complete_output(
                found_items={},
                missing_items=errors,  # FIXED: KNOWN_ISSUE_API-021 - Use missing_items parameter
                waived_items=[],
                waive_dict=waive_dict,
                unused_waivers=[],
                found_desc=self.FOUND_DESC_TYPE1_4,
                missing_desc=self.MISSING_DESC_TYPE1_4,
                waived_desc=self.WAIVED_DESC,
                found_reason=self.FOUND_REASON_TYPE1_4,
                missing_reason=self.MISSING_REASON_TYPE1_4,
                waived_base_reason=self.WAIVED_BASE_REASON
            )
        
        # Separate valid configurations from violations
        found_items = {}
        violations = []
        
        for item in items:
            if item.get('violation_type') == 'valid':
                # Valid configuration
                found_items[item['name']] = {
                    'name': item['name'],
                    'line_number': item.get('line_number', 0),
                    'file_path': item.get('file_path', 'N/A')
                }
            else:
                # Violation detected
                violations.append(item['name'])
        
        # Separate waived/unwaived using template helper
        waived_items = []
        unwaived_items = []
        
        # FIXED: KNOWN_ISSUE_API-017 - waive_dict keys are item names (strings)
        for violation_name in violations:
            if self.match_waiver_entry(violation_name, waive_dict):
                waived_items.append(violation_name)
            else:
                unwaived_items.append(violation_name)
        
        # Find unused waivers - FIXED: KNOWN_ISSUE_API-017 - Use waive_dict.keys() for names
        used_names = set(waived_items)
        unused_waivers = [name for name in waive_dict.keys() if name not in used_names]
        
        # Use template helper (auto-handles waiver=0)
        # FIXED: KNOWN_ISSUE_API-021 - Use missing_items parameter instead of unwaived_items
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
            waived_base_reason=self.WAIVED_BASE_REASON
        )


# =========================================================================
# Entry Point
# =========================================================================

def main():
    """Main entry point."""
    checker = Check_MIG_8_1_0_00()
    checker.init_checker(Path(__file__))
    result = checker.execute_check()
    checker.write_output(result)
    return 0 if result.is_pass else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())