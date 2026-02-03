################################################################################
# Script Name: IMP-9-0-0-02.py
#
# Purpose:
#   Confirm SPEF extraction includes NDR rule lef file.
#
# Logic:
#   - Parse input files: do_qrc*.log
#   - Extract NDR LEF file paths from INFO (EXTGRMP-338) messages
#   - Detect version mismatch warnings between tech LEF and NDR LEF (EXTGRMP-728)
#   - Collect other warnings/errors related to NDR file processing
#   - Verify NDR LEF files were successfully loaded
#   - Report any version mismatches or critical errors
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
class Check_9_0_0_02(InputFileParserMixin, OutputBuilderMixin, WaiverHandlerMixin, BaseChecker):
    """
    IMP-9-0-0-02: Confirm SPEF extraction includes NDR rule lef file.
    
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
    FOUND_DESC_TYPE1_4 = "NDR LEF files successfully loaded in SPEF extraction"
    MISSING_DESC_TYPE1_4 = "NDR LEF files not found in SPEF extraction"
    FOUND_REASON_TYPE1_4 = "NDR LEF file loaded successfully"
    MISSING_REASON_TYPE1_4 = "NDR LEF file not found in extraction log"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_DESC_TYPE2_3 = "Required NDR LEF files matched and loaded"
    MISSING_DESC_TYPE2_3 = "Expected NDR LEF files not satisfied"
    FOUND_REASON_TYPE2_3 = "Required NDR LEF file matched and validated"
    MISSING_REASON_TYPE2_3 = "Expected NDR LEF file not satisfied or missing"
    
    # All Types (waiver description unified)
    WAIVED_DESC = "Waived NDR LEF warnings"
    
    # Waiver parameters (Type 3/4 ONLY)
    WAIVED_BASE_REASON = "NDR LEF warning waived per design approval"
    
    def __init__(self):
        """Initialize the checker."""
        super().__init__(
            check_module="9.0_RC_EXTRACTION_CHECK",
            item_id="IMP-9-0-0-02",
            item_desc="Confirm SPEF extraction includes NDR rule lef file."
        )
        # Custom member variables for parsed data
        self._ndr_files: List[Dict[str, Any]] = []
        self._version_mismatches: List[Dict[str, Any]] = []
        self._other_warnings: List[Dict[str, Any]] = []
    
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
        Parse input files to extract relevant data.
        
        Parses Quantus QRC extraction log files to extract:
        1. NDR LEF file paths from INFO (EXTGRMP-338) messages
        2. Version mismatch warnings (EXTGRMP-728)
        3. Other warnings/errors related to NDR files
        
        Returns:
            Dict with parsed data:
            - 'ndr_files': List[Dict] - NDR LEF files found
            - 'version_mismatches': List[Dict] - Version mismatch warnings
            - 'other_warnings': List[Dict] - Other NDR-related warnings
            - 'metadata': Dict - File metadata
            - 'errors': List - Any parsing errors encountered
        """
        # 1. Validate input files (raises ConfigurationError if missing)
        # CRITICAL: validate_input_files() returns TUPLE: (valid_files, missing_files)
        valid_files, missing_files = self.validate_input_files()
        if not valid_files:
            raise ConfigurationError("No valid input files found")
        
        # Initialize storage
        ndr_files = []
        version_mismatches = []
        other_warnings = []
        errors = []
        
        # Define patterns for parsing
        # Pattern 1: NDR LEF file loading confirmation
        pattern_ndr_file = re.compile(r'INFO\s+\(EXTGRMP-338\)\s*:\s*(.+/ndr/[^\s]+\.lef)', re.IGNORECASE)
        
        # Pattern 2: Version mismatch warnings for NDR LEF files
        pattern_version_mismatch = re.compile(
            r'WARNING\s+\(EXTGRMP-728\)\s*:\s*Different version number exists for tech lef\s+"([^"]+)"\s+with version\s+([\d.]+)\s+and macro lef\s+"([^"]+)"\s+with version\s+([\d.]+)',
            re.IGNORECASE
        )
        
        # Pattern 3: General WARNING messages with message codes
        pattern_warning = re.compile(r'WARNING\s+\(([A-Z]+-\d+)\)\s*:\s*(.+)', re.IGNORECASE)
        
        # 2. Parse each file
        for file_path in valid_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line_num, line in enumerate(f, 1):
                        # Check for NDR LEF file loading
                        match_ndr = pattern_ndr_file.search(line)
                        if match_ndr:
                            ndr_file_path = match_ndr.group(1).strip()
                            ndr_files.append({
                                'name': ndr_file_path,
                                'file_path': ndr_file_path,
                                'line_number': line_num,
                                'source_file': str(file_path),
                                'line_content': line.strip()
                            })
                            continue
                        
                        # Check for version mismatch warnings
                        match_version = pattern_version_mismatch.search(line)
                        if match_version:
                            tech_lef = match_version.group(1).strip()
                            tech_version = match_version.group(2).strip()
                            macro_lef = match_version.group(3).strip()
                            macro_version = match_version.group(4).strip()
                            
                            # Only track if macro lef is NDR file
                            if '/ndr/' in macro_lef.lower():
                                version_mismatches.append({
                                    'name': f"{macro_lef} (v{macro_version} vs tech v{tech_version})",
                                    'tech_lef': tech_lef,
                                    'tech_version': tech_version,
                                    'macro_lef': macro_lef,
                                    'macro_version': macro_version,
                                    'line_number': line_num,
                                    'file_path': str(file_path),
                                    'line_content': line.strip()
                                })
                            continue
                        
                        # Check for other warnings related to NDR files
                        match_warning = pattern_warning.search(line)
                        if match_warning and '/ndr/' in line.lower():
                            msg_code = match_warning.group(1).strip()
                            msg_text = match_warning.group(2).strip()
                            
                            # Skip version mismatch warnings (already captured)
                            if msg_code != 'EXTGRMP-728':
                                other_warnings.append({
                                    'name': f"{msg_code}: {msg_text}",
                                    'code': msg_code,
                                    'message': msg_text,
                                    'line_number': line_num,
                                    'file_path': str(file_path),
                                    'line_content': line.strip()
                                })
            except Exception as e:
                errors.append(f"Error parsing {file_path}: {str(e)}")
        
        # 3. Store frequently reused data on self
        self._ndr_files = ndr_files
        self._version_mismatches = version_mismatches
        self._other_warnings = other_warnings
        
        # 4. Return aggregated dict
        return {
            'ndr_files': ndr_files,
            'version_mismatches': version_mismatches,
            'other_warnings': other_warnings,
            'metadata': {
                'total_ndr_files': len(ndr_files),
                'total_version_mismatches': len(version_mismatches),
                'total_other_warnings': len(other_warnings)
            },
            'errors': errors
        }
    
    # =========================================================================
    # Type 1: Boolean Check
    # =========================================================================
    
    def _execute_type1(self) -> CheckResult:
        """
        Type 1: Boolean Check.
        
        Custom boolean validation (NDR LEF files exist in extraction log?).
        Does NOT use pattern_items for searching.
        
        Use OutputBuilderMixin.build_complete_output() for automatic formatting.
        
        Returns:
            CheckResult with is_pass based on check logic
        """
        # Parse input
        data = self._parse_input_files()
        ndr_files = data.get('ndr_files', [])
        version_mismatches = data.get('version_mismatches', [])
        
        # Convert list to dict with metadata for source file/line display
        found_items = {}
        missing_items = []
        
        if ndr_files:
            # NDR files found - create found_items dict
            for ndr_file in ndr_files:
                found_items[ndr_file['name']] = {
                    'name': ndr_file['name'],
                    'line_number': ndr_file.get('line_number', 0),
                    'file_path': ndr_file.get('source_file', 'N/A')
                }
        else:
            # No NDR files found
            missing_items.append('NDR LEF files')
        
        # Add version mismatches as warnings (not failures for Type 1)
        # These will be shown as INFO items
        for mismatch in version_mismatches:
            warning_name = f"Version mismatch: {mismatch['name']}"
            found_items[warning_name] = {
                'name': warning_name,
                'line_number': mismatch.get('line_number', 0),
                'file_path': mismatch.get('file_path', 'N/A')
            }
        
        # Use template helper
        # Type 1: Use TYPE1_4 reason (emphasize "found/not found") - API-025
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
        PASS/FAIL depends on check purpose (violation check vs requirement check).
        
        Template auto-handles waiver=0 conversions.
        
        Returns:
            CheckResult with is_pass based on value comparison
        """
        # Parse input
        data = self._parse_input_files()
        ndr_files = data.get('ndr_files', [])
        
        # Get requirements
        pattern_items = self.item_data.get('requirements', {}).get('pattern_items', [])
        
        # existence_check mode: Check if pattern_items exist in input files
        found_items = {}
        missing_items = []
        
        # Create lookup dict for parsed NDR files
        ndr_files_dict = {ndr['name']: ndr for ndr in ndr_files}
        
        # Check each pattern
        for pattern in pattern_items:
            matched = False
            for ndr_name, ndr_data in ndr_files_dict.items():
                # Check if pattern matches (case-insensitive substring match)
                if pattern.lower() in ndr_name.lower():
                    found_items[ndr_name] = {
                        'name': ndr_name,
                        'line_number': ndr_data.get('line_number', 0),
                        'file_path': ndr_data.get('source_file', 'N/A')
                    }
                    matched = True
                    break
            
            if not matched:
                missing_items.append(pattern)
        
        # Use template helper (auto-handles waiver=0)
        # Type 2: Use TYPE2_3 reason (emphasize "matched/satisfied") - API-026
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
        
        Uses WaiverHandlerMixin for waiver processing:
        - parse_waive_items(waive_items_raw): Parse waiver configuration
        - match_waiver_entry(item, waive_dict): Match item against waivers
        
        Uses OutputBuilderMixin for result construction:
        - build_complete_output(...): Assemble final CheckResult with auto-formatting
        
        Returns:
            CheckResult with FAIL for unwaived, INFO for waived items
        """
        # Parse input
        parsed_data = self._parse_input_files()
        ndr_files = parsed_data.get('ndr_files', [])
        version_mismatches = parsed_data.get('version_mismatches', [])
        
        # FIXED: KNOWN_ISSUE_API-016 - Use waivers.get() directly to preserve dict format
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # Get requirements
        pattern_items = self.item_data.get('requirements', {}).get('pattern_items', [])
        
        # Find violations (missing patterns or version mismatches)
        violations = []
        found_items = {}
        
        # Create lookup dict for parsed NDR files
        ndr_files_dict = {ndr['name']: ndr for ndr in ndr_files}
        
        # Check each pattern
        for pattern in pattern_items:
            matched = False
            for ndr_name, ndr_data in ndr_files_dict.items():
                if pattern.lower() in ndr_name.lower():
                    found_items[ndr_name] = {
                        'name': ndr_name,
                        'line_number': ndr_data.get('line_number', 0),
                        'file_path': ndr_data.get('source_file', 'N/A')
                    }
                    matched = True
                    break
            
            if not matched:
                violations.append(pattern)
        
        # Add version mismatches as violations
        for mismatch in version_mismatches:
            violations.append(mismatch['name'])
        
        # Separate waived/unwaived using template helper
        waived_items = []
        unwaived_items = []
        
        for violation in violations:
            if self.match_waiver_entry(violation, waive_dict):
                waived_items.append(violation)
            else:
                unwaived_items.append(violation)
        
        # Find unused waivers
        used_names = set(waived_items)
        unused_waivers = [name for name in waive_dict.keys() if name not in used_names]
        
        # Use template helper for automatic output formatting
        # Type 3: Use TYPE2_3 reason (emphasize "matched/satisfied") - API-026
        return self.build_complete_output(
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
        
        Use OutputBuilderMixin.build_complete_output() with has_waiver_value=True.
        
        Returns:
            CheckResult with waiver logic applied
        """
        # Parse input
        data = self._parse_input_files()
        ndr_files = data.get('ndr_files', [])
        version_mismatches = data.get('version_mismatches', [])
        other_warnings = data.get('other_warnings', [])
        
        # FIXED: KNOWN_ISSUE_API-016 - Use waivers.get() directly to preserve dict format
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # Collect all items (NDR files found)
        found_items = {}
        for ndr_file in ndr_files:
            found_items[ndr_file['name']] = {
                'name': ndr_file['name'],
                'line_number': ndr_file.get('line_number', 0),
                'file_path': ndr_file.get('source_file', 'N/A')
            }
        
        # Collect violations (version mismatches and other warnings)
        violations = []
        for mismatch in version_mismatches:
            violations.append(mismatch['name'])
        for warning in other_warnings:
            violations.append(warning['name'])
        
        # Separate waived/unwaived
        waived_items = []
        unwaived_items = []
        
        for violation in violations:
            if self.match_waiver_entry(violation, waive_dict):
                waived_items.append(violation)
            else:
                unwaived_items.append(violation)
        
        # Find unused waivers
        used_names = set(waived_items)
        unused_waivers = [name for name in waive_dict.keys() if name not in used_names]
        
        # Use template helper (auto-handles waiver=0)
        # Type 4: Use TYPE1_4 reason (emphasize "found/not found") - API-026
        return self.build_complete_output(
            found_items=found_items,
            waived_items=waived_items,
            missing_items=unwaived_items,
            waive_dict=waive_dict,
            unused_waivers=unused_waivers,
            has_waiver_value=True,
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
    checker = Check_9_0_0_02()
    checker.init_checker(Path(__file__))
    result = checker.execute_check()
    checker.write_output(result)
    return 0 if result.is_pass else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())