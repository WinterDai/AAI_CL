################################################################################
# Script Name: IMP-12-0-0-12.py
#
# Purpose:
#   Confirm the MIM related check is clean. (Need to check and Fill N/A if no MIMCAP inserted or no MIM related layers in PHY or SOC level) - If PHY needs to insert MIMCAP. 1. Need to pay attention to the MIMCAP KOZ rule during MIMCAP insertion after check with customer about the SOC die size, substrate layer number and PHY placement/location in SOC level. 2. Pay attention to the option setting related to MIM DRC check like KOZ_High_subst_layer, SHDMIM_KOZ_AP_SPACE_5um(on/off will impact the checking rule) etc in TSMC rule deck(need to align these settings with customer). -If PHY doesn't insert MIMCAP but SOC level inserts MIMCAP. 1. Need to open SHDMIM switching in DRC rule deck. 2. Need to check with customer whether PHY need to meet SHDMIM_KOZ_AP_SPACE_5um rule (if SOC level this DRC switching setting is ON) in PHY area which falls into SOC KOZ area for TSMC process. 3. May need to insert MIM dummy in PHY level to meet SOC level MIM dummy density rule (you can sync with customer whether PHY MIM dummy is needed and the KOZ information on PHY to make sure there is no dummy added in KOZ area on PHY by adding MIM EXCL layer).
#
# Logic:
#   - Parse Calibre/Pegasus DRC reports to extract MIM rule check results
#   - Extract MIM layer statistics to determine if MIMCAP is present
#   - Verify all MIM DRC rules are clean (0 violations)
#   - Support waiver for specific MIM rule violations
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
class Check_12_0_0_12(InputFileParserMixin, OutputBuilderMixin, WaiverHandlerMixin, BaseChecker):
    """
    IMP-12-0-0-12: Confirm the MIM related check is clean. (Need to check and Fill N/A if no MIMCAP inserted or no MIM related layers in PHY or SOC level) - If PHY needs to insert MIMCAP. 1. Need to pay attention to the MIMCAP KOZ rule during MIMCAP insertion after check with customer about the SOC die size, substrate layer number and PHY placement/location in SOC level. 2. Pay attention to the option setting related to MIM DRC check like KOZ_High_subst_layer, SHDMIM_KOZ_AP_SPACE_5um(on/off will impact the checking rule) etc in TSMC rule deck(need to align these settings with customer). -If PHY doesn't insert MIMCAP but SOC level inserts MIMCAP. 1. Need to open SHDMIM switching in DRC rule deck. 2. Need to check with customer whether PHY need to meet SHDMIM_KOZ_AP_SPACE_5um rule (if SOC level this DRC switching setting is ON) in PHY area which falls into SOC KOZ area for TSMC process. 3. May need to insert MIM dummy in PHY level to meet SOC level MIM dummy density rule (you can sync with customer whether PHY MIM dummy is needed and the KOZ information on PHY to make sure there is no dummy added in KOZ area on PHY by adding MIM EXCL layer).
    
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
    FOUND_DESC_TYPE1_4 = "All MIM DRC checks are clean - no violations found in physical verification reports"
    MISSING_DESC_TYPE1_4 = "MIM DRC violations detected in physical verification reports"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_DESC_TYPE2_3 = "All specified MIM rules are clean - no violations detected"
    MISSING_DESC_TYPE2_3 = "MIM rule violations found - specified rules not satisfied"
    
    # All Types (waiver description unified)
    WAIVED_DESC = "MIM DRC violations waived per design team approval"
    
    # ⭐ REASON CONSTANTS - Split by Type semantics (API-025)
    # ALL Types pass found_reason/missing_reason, but use different constants
    
    # Type 1/4: Boolean checks - emphasize "found/not found" (existence)
    FOUND_REASON_TYPE1_4 = "MIM DRC verification complete - all checks passed with 0 violations"
    MISSING_REASON_TYPE1_4 = "MIM DRC check failed - violations found in one or more reports"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_REASON_TYPE2_3 = "All specified MIM rules validated and satisfied - 0 violations across all checks"
    MISSING_REASON_TYPE2_3 = "MIM rule requirements not satisfied - violations detected in specified rules"
    
    # Waiver-related (Type 3/4 only)
    WAIVED_BASE_REASON = "MIM violation waived - approved by physical verification team"
    UNUSED_WAIVER_REASON = "Waiver entry not matched - specified MIM rule has no violations in current reports"
    
    def __init__(self):
        """Initialize the checker."""
        super().__init__(
            check_module="12.0_PHYSICAL_VERIFICATION_CHECK",
            item_id="IMP-12-0-0-12",
            item_desc="Confirm the MIM related check is clean. (Need to check and Fill N/A if no MIMCAP inserted or no MIM related layers in PHY or SOC level) - If PHY needs to insert MIMCAP. 1. Need to pay attention to the MIMCAP KOZ rule during MIMCAP insertion after check with customer about the SOC die size, substrate layer number and PHY placement/location in SOC level. 2. Pay attention to the option setting related to MIM DRC check like KOZ_High_subst_layer, SHDMIM_KOZ_AP_SPACE_5um(on/off will impact the checking rule) etc in TSMC rule deck(need to align these settings with customer). -If PHY doesn't insert MIMCAP but SOC level inserts MIMCAP. 1. Need to open SHDMIM switching in DRC rule deck. 2. Need to check with customer whether PHY need to meet SHDMIM_KOZ_AP_SPACE_5um rule (if SOC level this DRC switching setting is ON) in PHY area which falls into SOC KOZ area for TSMC process. 3. May need to insert MIM dummy in PHY level to meet SOC level MIM dummy density rule (you can sync with customer whether PHY MIM dummy is needed and the KOZ information on PHY to make sure there is no dummy added in KOZ area on PHY by adding MIM EXCL layer)."
        )
        # Custom member variables for parsed data
        self._parsed_items: List[Dict[str, Any]] = []
        self._metadata: Dict[str, str] = {}
        self._mim_layer_present: bool = False
        self._report_type: str = ""  # "Calibre" or "Pegasus"
    
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
        Parse Calibre/Pegasus DRC reports to extract MIM rule check results.
        
        Extracts:
        - MIM layer statistics to determine if MIMCAP is present
        - MIM rule check results with violation counts
        - File metadata (tool version, design name, execution date)
        
        Returns:
            Dict with parsed data:
            - 'items': List[Dict] - MIM rule check results with violation counts
            - 'metadata': Dict - File metadata (tool version, design, date)
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
        mim_layers_found = False
        
        # 3. Parse each input file for MIM DRC information
        for file_path in valid_files:
            try:
                report_type = self._detect_report_type(file_path)
                
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                
                # Extract metadata
                file_metadata = self._extract_metadata(lines, report_type)
                metadata.update(file_metadata)
                
                # Check MIM layer presence
                has_mim_layers = self._check_mim_layer_presence(lines, report_type)
                if has_mim_layers:
                    mim_layers_found = True
                
                # Extract MIM rule violations
                violations = self._extract_mim_violations(lines, report_type, str(file_path))
                items.extend(violations)
                
            except Exception as e:
                errors.append(f"Error parsing {file_path}: {str(e)}")
        
        # 4. Store frequently reused data on self
        self._parsed_items = items
        self._metadata = metadata
        self._mim_layer_present = mim_layers_found
        
        return {
            'items': items,
            'metadata': metadata,
            'errors': errors
        }
    

    # =========================================================================
    # Type 1: Boolean Check
    # =========================================================================

    def _execute_type1(self) -> CheckResult:
        """
        Type 1: Boolean check without waiver support.

        Verifies that all MIM-related DRC checks are clean (0 violations).
        - found_items: MIM rules with 0 violations (clean checks)
        - missing_items: MIM rules with violations (failed checks)

        Returns:
            CheckResult with PASS if all MIM checks are clean, FAIL otherwise.
        """
        violations = self._type1_core_logic()

        # Build found_items from clean MIM checks
        data = self._parse_input_files()
        all_checks = data.get('items', [])

        found_items = {}
        for check in all_checks:
            check_name = check.get('name', 'Unknown')
            violation_count = check.get('violation_count', 0)

            if violation_count == 0:
                found_items[check_name] = {
                    'name': check_name,
                    'line_number': check.get('line_number', 0),
                    'file_path': check.get('file_path', 'N/A'),
                    'violation_count': 0
                }

        # FIXED: Pass violations dict directly (not list)
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

        Parses Calibre/Pegasus DRC reports to extract MIM rule violations.

        Returns:
            Dict of violations: {rule_name: {'line_number': ..., 'file_path': ...,
                                             'reason': ..., 'violation_count': ...}}
            Empty dict if all MIM checks are clean.
        """
        data = self._parse_input_files()
        items = data.get('items', [])
        errors = data.get('errors', [])

        violations = {}

        # Check for parsing errors
        if errors:
            violations['parsing_error'] = {
                'line_number': 0,
                'file_path': 'N/A',
                'reason': f"Failed to parse MIM reports: {'; '.join(errors)}",
                'violation_count': 0
            }
            return violations

        # Check if no MIM checks were found
        if not items:
            violations['no_mim_checks'] = {
                'line_number': 0,
                'file_path': 'N/A',
                'reason': 'No MIM-related DRC checks found in reports',
                'violation_count': 0
            }
            return violations

        # Extract violations from MIM checks
        for check in items:
            check_name = check.get('name', 'Unknown')
            violation_count = check.get('violation_count', 0)

            if violation_count > 0:
                violations[check_name] = {
                    'line_number': check.get('line_number', 0),
                    'file_path': check.get('file_path', 'N/A'),
                    'reason': f"MIM rule {check_name} has {violation_count} violation(s)",
                    'violation_count': violation_count
                }

        return violations

    # =========================================================================
    # Type 4: Boolean Check with Waiver Logic
    # =========================================================================

    def _execute_type4(self) -> CheckResult:
        """
        Type 4: Boolean check with waiver support (reuses Type 1 core logic).

        Verifies MIM DRC checks with waiver support:
        - found_items: MIM rules with 0 violations (clean checks)
        - waived_items: MIM rules with violations that are waived
        - missing_items: MIM rules with violations that are NOT waived (FAIL)
        - unused_waivers: Waiver entries that didn't match any violations

        Returns:
            CheckResult with PASS if all violations are waived, FAIL otherwise.
        """
        # Step 1: Get violations using Type 1's core logic
        violations = self._type1_core_logic()

        # Build found_items from clean MIM checks
        data = self._parse_input_files()
        all_checks = data.get('items', [])

        found_items = {}
        for check in all_checks:
            check_name = check.get('name', 'Unknown')
            violation_count = check.get('violation_count', 0)

            if violation_count == 0:
                found_items[check_name] = {
                    'name': check_name,
                    'line_number': check.get('line_number', 0),
                    'file_path': check.get('file_path', 'N/A'),
                    'violation_count': 0
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
        found_items, missing_items = self._type2_core_logic()

        # FIXED: Pass missing_items dict directly (not list)
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
            - found_items: {rule_name: {'line_number': ..., 'file_path': ..., 'violation_count': ...}}
            - missing_items: {rule_name: {'line_number': ..., 'file_path': ..., 'reason': ...}}
        """
        data = self._parse_input_files()
        items = data.get('items', [])

        requirements = self.item_data.get('requirements', {})
        pattern_items = requirements.get('pattern_items', [])

        found_items = {}
        missing_items = {}

        # Parse all MIM rules from DRC reports
        for item in items:
            rule_name = item.get('name', '')
            violation_count = item.get('violation_count', 0)
            line_number = item.get('line_number', 0)
            file_path = item.get('file_path', 'N/A')

            # Check if this rule matches any required pattern
            matched_pattern = None
            for pattern in pattern_items:
                # Use substring match for rule patterns (e.g., "MIM.A.R.1.1" matches "MIM.A.R.1.1")
                if pattern.lower() in rule_name.lower():
                    matched_pattern = pattern
                    break

            if matched_pattern:
                # Check if rule is clean (0 violations)
                if violation_count == 0:
                    found_items[rule_name] = {
                        'line_number': line_number,
                        'file_path': file_path,
                        'violation_count': violation_count
                    }
                else:
                    # Rule has violations - this is a missing/failed item
                    missing_items[rule_name] = {
                        'line_number': line_number,
                        'file_path': file_path,
                        'violation_count': violation_count,
                        'reason': f'MIM rule {rule_name} has {violation_count} violation(s)'
                    }

        # Check for patterns that were not found at all in the reports
        for pattern in pattern_items:
            pattern_found = False
            for item in items:
                if pattern.lower() in item.get('name', '').lower():
                    pattern_found = True
                    break

            if not pattern_found:
                missing_items[pattern] = {
                    'line_number': 0,
                    'file_path': 'N/A',
                    'reason': f'MIM rule pattern "{pattern}" not found in any DRC report'
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

        # Process found_items_base (clean rules - no waiver needed)
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

    # =========================================================================
    # Helper Methods for Parsing
    # =========================================================================

    def _detect_report_type(self, file_path: Path) -> str:
        """Detect if report is Calibre or Pegasus format."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(2000)  # Read first 2000 chars
                if 'Calibre Version' in content or 'CALIBRE' in content:
                    return 'Calibre'
                elif 'Pegasus VERSION' in content or 'PEGASUS' in content:
                    return 'Pegasus'
        except Exception:
            pass
        return 'Unknown'
    
    def _extract_metadata(self, lines: List[str], report_type: str) -> Dict[str, str]:
        """Extract file metadata from report header."""
        metadata = {}
        
        # Pattern for both Calibre and Pegasus metadata
        metadata_pattern = r'^(Layout Primary Cell|Rule File Pathname|Execution Date/Time|Calibre Version|Execute on Date/Time|Pegasus VERSION|Rule Deck Path):\s+(.+)$'
        
        for line in lines[:50]:  # Check first 50 lines for metadata
            match = re.search(metadata_pattern, line)
            if match:
                key = match.group(1).strip()
                value = match.group(2).strip()
                metadata[key] = value
        
        metadata['report_type'] = report_type
        return metadata
    
    def _check_mim_layer_presence(self, lines: List[str], report_type: str) -> bool:
        """Check if MIM layers are present in the design."""
        if report_type == 'Calibre':
            # Calibre MIM layer pattern
            layer_pattern = r'^LAYER\s+((?:MPC|BPC|MPC_O|BPC_O|TPCDMY_AP2))\s+\.+\s+TOTAL Original Geometry Count\s+=\s+(\d+)\s+\((\d+)\)'
        else:  # Pegasus
            # Pegasus MIM layer pattern
            layer_pattern = r'^LAYER\s+(MPC|TPC|BPC|MPC_O|TPC_O|BPC_O|TPCDMY_AP)\s+\.+\s+Total Original Geometry:\s+(\d+)\s+\(\s*(\d+)\)'
        
        for line in lines:
            match = re.search(layer_pattern, line)
            if match:
                geometry_count = int(match.group(2))
                if geometry_count > 0:
                    return True
        
        return False
    
    def _extract_mim_violations(self, lines: List[str], report_type: str, file_path: str) -> List[Dict[str, Any]]:
        """Extract MIM rule violations from report."""
        violations = []
        
        if report_type == 'Calibre':
            # Calibre RULECHECK pattern
            rulecheck_pattern = r'^RULECHECK\s+(MIM\.[A-Z]\.R\.[\d\.]+(?::[A-Z]+)?)\s+\.+\s+TOTAL Result Count\s+=\s+(\d+)\s+\((\d+)\)'
        else:  # Pegasus
            # Pegasus RULECHECK pattern
            rulecheck_pattern = r'^RULECHECK\s+([\w\.\:]+)\s+\.+\s+Total Result\s+(\d+)\s+\(\s*(\d+)\)'
        
        for line_num, line in enumerate(lines, 1):
            match = re.search(rulecheck_pattern, line)
            if match:
                rule_name = match.group(1)
                violation_count = int(match.group(2))
                
                # Only include MIM-related rules or all rules depending on report type
                if report_type == 'Calibre' or 'MIM' in rule_name or 'A.R.' in rule_name:
                    violations.append({
                        'name': rule_name,
                        'violation_count': violation_count,
                        'line_number': line_num,
                        'file_path': file_path,
                        'report_type': report_type,
                        'type': 'mim_rule'
                    })
        
        return violations


# =========================================================================
# Entry Point
# =========================================================================

def main():
    """Main entry point."""
    checker = Check_12_0_0_12()
    checker.init_checker(Path(__file__))
    result = checker.execute_check()
    checker.write_output(result)
    return 0 if result.is_pass else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())