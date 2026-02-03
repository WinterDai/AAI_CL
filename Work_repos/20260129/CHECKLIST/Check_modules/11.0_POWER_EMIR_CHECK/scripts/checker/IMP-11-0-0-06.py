################################################################################
# Script Name: IMP-11-0-0-06.py
#
# Purpose:
#   Confirm use the proper spice model and spice netlist to generate the PGV views.(check the Note)
#
# Logic:
#   - Parse input files: *.LibGen.log
#   - Extract celltype from set_pg_library_mode command
#   - Skip files with celltype "techonly"
#   - For celltype "macros" or "stdcells", extract SPICE models and subckts paths
#   - Report all extracted SPICE configurations for user verification
#   - No automatic PASS/FAIL determination - informational check only
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
# Refactored: 2026-01-06 (Using checker_templates v1.1.0)
#
# Author: Jing Li
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
class Check_11_0_0_06(InputFileParserMixin, OutputBuilderMixin, WaiverHandlerMixin, BaseChecker):
    """
    IMP-11-0-0-06: Confirm use the proper spice model and spice netlist to generate the PGV views.(check the Note)
    
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
    FOUND_DESC_TYPE1_4 = "SPICE configuration found in LibGen logs"
    MISSING_DESC_TYPE1_4 = "SPICE configuration not found in LibGen logs"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_DESC_TYPE2_3 = "SPICE configuration extracted for verification"
    MISSING_DESC_TYPE2_3 = "SPICE configuration missing or incomplete"
    
    # All Types (waiver description unified)
    WAIVED_DESC = "SPICE configuration reported as informational"
    
    # ⭐ REASON CONSTANTS - Split by Type semantics (API-025)
    # ALL Types pass found_reason/missing_reason, but use different constants
    
    # Type 1/4: Boolean checks - emphasize "found/not found" (existence)
    FOUND_REASON_TYPE1_4 = "SPICE model and netlist paths found in set_pg_library_mode command"
    MISSING_REASON_TYPE1_4 = "set_pg_library_mode command not found or missing SPICE parameters"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_REASON_TYPE2_3 = "SPICE configuration extracted and reported for user verification"
    MISSING_REASON_TYPE2_3 = "SPICE model or netlist path not found in set_pg_library_mode command"
    
    # Waiver-related (Type 3/4 only)
    WAIVED_BASE_REASON = "SPICE configuration waived - informational check only"
    UNUSED_WAIVER_REASON = "Waiver not matched - no corresponding SPICE configuration issue found"
    
    def __init__(self):
        """Initialize the checker."""
        super().__init__(
            check_module="11.0_POWER_EMIR_CHECK",
            item_id="IMP-11-0-0-06",
            item_desc="Confirm use the proper spice model and spice netlist to generate the PGV views.(check the Note)"
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
        Parse input files to extract SPICE model and netlist configuration.
        
        Parse *.LibGen.log files to extract:
        - celltype from set_pg_library_mode command
        - SPICE models path (for macros/stdcells only)
        - SPICE subckts paths (for macros/stdcells only)
        
        Skip files with celltype "techonly".
        
        Returns:
            Dict with parsed data:
            - 'items': List[Dict] - SPICE configuration items with corner info
            - 'metadata': Dict - File metadata
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
            raise ConfigurationError(
                self.create_missing_files_error(["No input files found"])
            )
        
        # 2. Initialize parsing structures
        items = []
        metadata = {}
        errors = []
        
        # 3. Parse each input file for SPICE configuration
        for file_path in valid_files:
            try:
                file_name = file_path.name
                
                # Extract corner name from filename
                # Pattern: [design_]corner_voltage_temp_rc_cc_timing.LibGen.log
                corner_match = re.search(
                    r'([a-z0-9_]+_\d+p\d+v_[\-]?\d+c_\w+_\w+_\w+)\.LibGen\.log',
                    file_name,
                    re.IGNORECASE
                )
                corner_name = corner_match.group(1) if corner_match else file_name.replace('.LibGen.log', '')
                
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    
                    # Find set_pg_library_mode commands
                    # Pattern: set_pg_library_mode -celltype <type> ... -spice_models <path> ... -spice_subckts {<paths>}
                    cmd_pattern = r'set_pg_library_mode\s+.*?(?=\n(?:set_pg_library_mode|<CMD>|$))'
                    commands = re.finditer(cmd_pattern, content, re.DOTALL | re.MULTILINE)
                    
                    for cmd_match in commands:
                        cmd_text = cmd_match.group(0)
                        
                        # Extract celltype
                        celltype_match = re.search(r'-celltype\s+(\S+)', cmd_text)
                        if not celltype_match:
                            continue
                        
                        celltype = celltype_match.group(1)
                        
                        # Skip techonly cells
                        if celltype.lower() == 'techonly':
                            continue
                        
                        # Only process macros and stdcells
                        if celltype.lower() not in ['macros', 'stdcells']:
                            continue
                        
                        # Extract SPICE models path
                        spice_models_match = re.search(r'-spice_models\s+(\S+)', cmd_text)
                        spice_models = spice_models_match.group(1) if spice_models_match else None
                        
                        # Extract SPICE subckts paths
                        spice_subckts_match = re.search(r'-spice_subckts\s+\{([^}]+)\}', cmd_text)
                        spice_subckts = []
                        if spice_subckts_match:
                            # Split by whitespace to get individual paths
                            subckts_text = spice_subckts_match.group(1).strip()
                            spice_subckts = [p.strip() for p in subckts_text.split() if p.strip()]
                        
                        # Get line number for traceability
                        line_number = content[:cmd_match.start()].count('\n') + 1
                        
                        # Create item entry
                        if spice_models or spice_subckts:
                            item_name = f"{corner_name} [{celltype}]"
                            items.append({
                                'name': item_name,
                                'corner': corner_name,
                                'celltype': celltype,
                                'spice_models': spice_models,
                                'spice_subckts': spice_subckts,
                                'line_number': line_number,
                                'file_path': str(file_path),
                                'type': 'spice_config'
                            })
                        
            except Exception as e:
                errors.append(f"Error parsing {file_path}: {str(e)}")
        
        # 4. Store frequently reused data on self
        self._parsed_items = items
        self._metadata = metadata
        
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
        
        Extracts SPICE model and netlist configurations from LibGen logs.
        Reports all findings as INFO for user verification.
        No automatic PASS/FAIL validation - informational check only.
        """
        violations = self._type1_core_logic()
        
        # Build found_items from clean configurations (corners with valid SPICE settings)
        data = self._parse_input_files()
        all_configs = data.get('items', [])
        
        found_items = {}
        for config in all_configs:
            config_name = config.get('name', 'unknown')
            # Only include configs that are NOT violations
            if config_name not in violations:
                found_items[config_name] = {
                    'name': config_name,
                    'line_number': config.get('line_number', 0),
                    'file_path': config.get('file_path', 'N/A')
                }
        
        # FIXED: Convert violations dict to dict format for build_complete_output
        missing_items = violations
        
        return self.build_complete_output(
            found_items=found_items,
            missing_items=missing_items,
            found_desc=self.FOUND_DESC_TYPE1_4,
            missing_desc=self.MISSING_DESC_TYPE1_4,
            found_reason=self.FOUND_REASON_TYPE1_4,
            missing_reason=self.MISSING_REASON_TYPE1_4
        )
    
    def _type1_core_logic(self) -> dict:
        """
        Core Type 1 boolean check logic (shared by Type 1 and Type 4).
        
        Parses LibGen logs to extract SPICE model and netlist configurations.
        Identifies corners with missing or incomplete SPICE settings.
        
        Returns:
            Dict of violations: {corner_name: {'line_number': ..., 'file_path': ..., 'reason': ...}}
            Empty dict if all checks pass (all corners have valid SPICE configs).
        """
        data = self._parse_input_files()
        items = data.get('items', [])
        errors = data.get('errors', [])
        
        violations = {}
        
        # If parsing errors occurred, treat as violations
        for error in errors:
            error_key = f"parsing_error_{len(violations)}"
            violations[error_key] = {
                'line_number': 0,
                'file_path': 'N/A',
                'reason': error
            }
        
        # Check each configuration for completeness
        for item in items:
            corner_name = item.get('name', 'unknown')
            spice_models = item.get('spice_models', '')
            spice_subckts = item.get('spice_subckts', [])
            
            # Violation if SPICE model or netlist is missing
            if not spice_models or not spice_subckts:
                violations[corner_name] = {
                    'line_number': item.get('line_number', 0),
                    'file_path': item.get('file_path', 'N/A'),
                    'reason': 'SPICE model or netlist path not found in set_pg_library_mode command'
                }
        
        return violations
    
    # =========================================================================
    # Type 2: Value Check
    # =========================================================================
    
    def _execute_type2(self) -> CheckResult:
        """Type 2: Pattern/value check without waiver support."""
        found_items, missing_items = self._type2_core_logic()
        
        # FIXED: _type2_core_logic() returns dict[str, dict] for both
        # Pass dict directly to build_complete_output (API-009)
        return self.build_complete_output(
            found_items=found_items,
            missing_items=missing_items,
            found_desc=self.FOUND_DESC_TYPE2_3,
            missing_desc=self.MISSING_DESC_TYPE2_3,
            found_reason=self.FOUND_REASON_TYPE2_3,
            missing_reason=self.MISSING_REASON_TYPE2_3
        )
    
    def _type2_core_logic(self) -> Tuple[Dict[str, dict], Dict[str, dict]]:
        """
        Core Type 2 pattern matching logic (shared by Type 2 and Type 3).
        
        Returns:
            Tuple of (found_items, missing_items)
            - found_items: {spice_path: {'line_number': ..., 'file_path': ...}}
            - missing_items: {pattern: {'line_number': ..., 'file_path': ..., 'reason': ...}}
        """
        data = self._parse_input_files()
        items = data.get('items', [])
        
        requirements = self.item_data.get('requirements', {})
        pattern_items = requirements.get('pattern_items', [])
        
        found_items = {}
        missing_items = {}
        
        # Extract all SPICE paths from parsed items
        for item in items:
            spice_models = item.get('spice_models', '')
            spice_subckts = item.get('spice_subckts', [])
            line_number = item.get('line_number', 0)
            file_path = item.get('file_path', 'N/A')
            
            # Add SPICE model if present
            if spice_models:
                found_items[spice_models] = {
                    'line_number': line_number,
                    'file_path': file_path
                }
            
            # Add SPICE netlists if present
            for subckt in spice_subckts:
                found_items[subckt] = {
                    'line_number': line_number,
                    'file_path': file_path
                }
        
        # Check which pattern_items are missing
        for pattern in pattern_items:
            if pattern not in found_items:
                missing_items[pattern] = {
                    'line_number': 0,
                    'file_path': 'N/A',
                    'reason': f'Expected SPICE path "{pattern}" not found in LibGen logs'
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
        # FIXED: Use waivers.get('waive_items', []) instead of get_waive_items() (API-008, API-016)
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # Step 3: Split violations into waived and unwaived
        found_items = {}
        waived_items = {}
        missing_items = {}
        used_waivers = set()
        
        # Process found_items_base (no waiver needed - these are correct SPICE paths)
        for item_name, item_data in found_items_base.items():
            found_items[item_name] = item_data
        
        # Process violations (missing expected SPICE paths) with waiver matching
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
        # FIXED: Pass dict directly to build_complete_output (API-009)
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
        
        Same SPICE configuration extraction as Type 1, but with waiver support:
        - Clean configurations → found_items (PASS)
        - Waived violations → waived_items (PASS with [WAIVER] tag)
        - Unwaived violations → missing_items (FAIL)
        - Unused waivers → WARN with [WAIVER] tag
        """
        # Step 1: Get violations using Type 1's core logic
        violations = self._type1_core_logic()
        
        # Build found_items from clean configurations
        data = self._parse_input_files()
        all_configs = data.get('items', [])
        
        found_items = {}
        for config in all_configs:
            config_name = config.get('name', 'unknown')
            # Only include configs that are NOT violations
            if config_name not in violations:
                found_items[config_name] = {
                    'name': config_name,
                    'line_number': config.get('line_number', 0),
                    'file_path': config.get('file_path', 'N/A')
                }
        
        # Step 2: Parse waiver configuration
        # FIXED: Use waivers.get('waive_items', []) instead of get_waive_items() (API-008, API-016)
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
        # FIXED: Pass dict directly to build_complete_output (API-009)
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
    checker = Check_11_0_0_06()
    checker.init_checker(Path(__file__))
    result = checker.execute_check()
    checker.write_output(result)
    return 0 if result.is_pass else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())