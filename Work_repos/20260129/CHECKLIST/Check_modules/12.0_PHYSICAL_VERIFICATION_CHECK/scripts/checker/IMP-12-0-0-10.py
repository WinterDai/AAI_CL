################################################################################
# Script Name: IMP-12-0-0-10.py
#
# Purpose:
#   Confirm turn-off the VIRTUAL_CONNECT in LVS setting.
#
# Logic:
#   - Parse input files: do_pvs_LVS_pvl.log (Pegasus), do_cmd_3star_LVS_sourceme (Calibre)
#   - Detect file type (Pegasus .pvl log vs Calibre sourceme command file)
#   - Search for VIRTUAL_CONNECT setting using tool-specific patterns
#   - Extract setting value and line number for traceability
#   - Verify VIRTUAL_CONNECT is disabled (-COLON NO for Pegasus, COLON NO for Calibre)
#   - Report PASS if disabled, FAIL if enabled or not found
#   - Support waiver logic for Type 3/4 if configured
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
class Check_12_0_0_10(InputFileParserMixin, OutputBuilderMixin, WaiverHandlerMixin, BaseChecker):
    """
    IMP-12-0-0-10: Confirm turn-off the VIRTUAL_CONNECT in LVS setting.
    
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
    FOUND_DESC_TYPE1_4 = "VIRTUAL_CONNECT is properly disabled in LVS settings"
    MISSING_DESC_TYPE1_4 = "VIRTUAL_CONNECT is enabled or not found in LVS settings"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_DESC_TYPE2_3 = "VIRTUAL_CONNECT setting matched expected disabled state"
    MISSING_DESC_TYPE2_3 = "VIRTUAL_CONNECT setting does not match expected disabled state"
    
    # All Types (waiver description unified)
    WAIVED_DESC = "VIRTUAL_CONNECT violations waived by configuration"
    
    # ⭐ REASON CONSTANTS - Split by Type semantics (API-025)
    # ALL Types pass found_reason/missing_reason, but use different constants
    
    # Type 1/4: Boolean checks - emphasize "found/not found" (existence)
    FOUND_REASON_TYPE1_4 = "VIRTUAL_CONNECT is disabled (setting found and verified)"
    MISSING_REASON_TYPE1_4 = "VIRTUAL_CONNECT is enabled or setting not found in file"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_REASON_TYPE2_3 = "VIRTUAL_CONNECT setting matched expected pattern and is disabled"
    MISSING_REASON_TYPE2_3 = "VIRTUAL_CONNECT setting does not satisfy disabled state requirement"
    
    # Waiver-related (Type 3/4 only)
    WAIVED_BASE_REASON = "VIRTUAL_CONNECT violation waived per configuration"
    UNUSED_WAIVER_REASON = "Waiver defined but no violation matched"
    
    def __init__(self):
        """Initialize the checker."""
        super().__init__(
            check_module="12.0_PHYSICAL_VERIFICATION_CHECK",
            item_id="IMP-12-0-0-10",
            item_desc="Confirm turn-off the VIRTUAL_CONNECT in LVS setting."
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
        Parse input files to extract VIRTUAL_CONNECT settings.
        
        Parses both Pegasus LVS log files (.pvl) and Calibre LVS command files (sourceme).
        Searches for VIRTUAL_CONNECT setting and extracts its state (enabled/disabled).
        
        Returns:
            Dict with parsed data:
            - 'items': List[Dict] - VIRTUAL_CONNECT settings found (with metadata: line_number, file_path)
            - 'metadata': Dict - File metadata (tool type, design name, etc.)
            - 'errors': List - Any parsing errors encountered
            - 'warnings': List - Any parsing warnings
        """
        # 1. Validate inputs - IMPORTANT: returns tuple (valid_files_list, missing_files_list)
        valid_files, missing_files = self.validate_input_files()
        
        # FIX [KNOWN_ISSUE_LOGIC-001]: Explicitly check for empty list
        if missing_files:
            raise ConfigurationError(
                self.create_missing_files_error(missing_files)
            )
        if not valid_files or len(valid_files) == 0:
            raise ConfigurationError("No valid input files found")
        
        # 2. Parse using patterns from file analysis
        all_items = []
        metadata = {}
        errors = []
        warnings = []
        
        # Define patterns for both Pegasus and Calibre formats
        # Pegasus pattern: VIRTUAL_CONNECT -COLON NO/YES;
        pegasus_pattern = re.compile(
            r'^\s*VIRTUAL_CONNECT\s+-COLON\s+(NO|YES)\s*;?\s*$',
            re.IGNORECASE
        )
        
        # Calibre pattern: VIRTUAL CONNECT COLON NO/YES
        calibre_pattern = re.compile(
            r'^\s*VIRTUAL\s+CONNECT\s+COLON\s+(YES|NO)\s*$',
            re.IGNORECASE
        )
        
        # Alternative Pegasus command format: lvs_virtual_connect -colon no/yes
        pegasus_alt_pattern = re.compile(
            r'^\s*lvs_virtual_connect\s+-colon\s+(no|yes)\s*$',
            re.IGNORECASE
        )
        
        # Comment pattern to skip commented lines
        comment_pattern = re.compile(r'^\s*(#|//).*VIRTUAL')
        
        # Design name pattern for metadata
        design_pattern = re.compile(
            r'^\s*(LAYOUT|SOURCE|SCHEMATIC)_PRIMARY\s+"?([^"\s;]+)"?\s*;?',
            re.IGNORECASE
        )
        
        for file_path in valid_files:
            file_type = self._detect_file_type(file_path)
            metadata['file_type'] = file_type
            
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line_num, line in enumerate(f, 1):
                    # Skip comment lines
                    if comment_pattern.match(line):
                        continue
                    
                    # Extract design name for metadata
                    design_match = design_pattern.match(line)
                    if design_match:
                        metadata['design_name'] = design_match.group(2)
                    
                    # Check for VIRTUAL_CONNECT settings
                    setting_value = None
                    setting_type = None
                    
                    # Try Pegasus pattern
                    pegasus_match = pegasus_pattern.match(line)
                    if pegasus_match:
                        setting_value = pegasus_match.group(1).upper()
                        setting_type = 'Pegasus'
                    
                    # Try Calibre pattern
                    if not pegasus_match:
                        calibre_match = calibre_pattern.match(line)
                        if calibre_match:
                            setting_value = calibre_match.group(1).upper()
                            setting_type = 'Calibre'
                    
                    # Try alternative Pegasus pattern
                    if not pegasus_match and not calibre_match:
                        pegasus_alt_match = pegasus_alt_pattern.match(line)
                        if pegasus_alt_match:
                            setting_value = pegasus_alt_match.group(1).upper()
                            setting_type = 'Pegasus_alt'
                    
                    # If VIRTUAL_CONNECT setting found, add to items
                    if setting_value:
                        is_disabled = (setting_value == 'NO')
                        # Use the actual pattern format for the name
                        if setting_type == 'Pegasus' or setting_type == 'Pegasus_alt':
                            item_name = f"VIRTUAL_CONNECT -COLON {setting_value}"
                        else:  # Calibre
                            item_name = f"VIRTUAL CONNECT COLON {setting_value}"
                        
                        all_items.append({
                            'name': item_name,
                            'setting_value': setting_value,
                            'is_disabled': is_disabled,
                            'setting_type': setting_type,
                            'line_number': line_num,
                            'file_path': str(file_path),
                            'line_content': line.strip()
                        })
        
        # Check if VIRTUAL_CONNECT was found at all
        if not all_items:
            warnings.append("VIRTUAL_CONNECT setting not found in any input file (may default to ON)")
        
        # 3. Store on self
        self._parsed_items = all_items
        self._metadata = metadata
        
        # 4. Return aggregated dict with items containing line_number and file_path
        return {
            'items': all_items,
            'metadata': metadata,
            'errors': errors,
            'warnings': warnings
        }
    
    def _detect_file_type(self, file_path: Path) -> str:
        """
        Detect if file is Pegasus (.pvl log) or Calibre (sourceme) format.
        
        Args:
            file_path: Path to the file
            
        Returns:
            'Pegasus' or 'Calibre'
        """
        file_name = file_path.name.lower()
        
        # Check file extension and name patterns
        if 'pvl.log' in file_name or file_name.endswith('.pvl'):
            return 'Pegasus'
        elif 'sourceme' in file_name or 'lvs' in file_name:
            return 'Calibre'
        
        # If unclear from name, check file content
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                first_lines = ''.join([f.readline() for _ in range(10)])
                if 'Parsing Rule File' in first_lines or 'PEGASUS' in first_lines:
                    return 'Pegasus'
                elif 'LAYOUT PRIMARY' in first_lines or 'SOURCE PRIMARY' in first_lines:
                    return 'Calibre'
        except Exception:
            pass
        
        # Default to Calibre if uncertain
        return 'Calibre'
    
    # =========================================================================
    # Type 1: Boolean Check
    # =========================================================================
    
    def _execute_type1(self) -> CheckResult:
        """
        Type 1: Boolean Check.
        
        Check if VIRTUAL_CONNECT is disabled in LVS settings.
        Does NOT use pattern_items for searching.
        
        Use OutputBuilderMixin.build_complete_output() for automatic formatting.
        
        Returns:
            CheckResult with is_pass based on check logic
        """
        # Parse input
        data = self._parse_input_files()
        items = data.get('items', [])
        warnings = data.get('warnings', [])
        
        # Check if VIRTUAL_CONNECT is disabled
        # If multiple settings found, use the last one (last one wins)
        found_items = {}
        missing_items = []
        
        if items:
            # Use last occurrence
            last_item = items[-1]
            if last_item['is_disabled']:
                # VIRTUAL_CONNECT is disabled - PASS
                found_items[last_item['name']] = {
                    'name': last_item['name'],
                    'line_number': last_item.get('line_number', 0),
                    'file_path': last_item.get('file_path', 'N/A'),
                    'reason': f"{self.FOUND_REASON_TYPE1_4} (Line {last_item.get('line_number', 0)} in {last_item.get('file_path', 'N/A')})"
                }
            else:
                # VIRTUAL_CONNECT is enabled - FAIL
                missing_items.append({
                    'name': f"VIRTUAL_CONNECT is {last_item['setting_value']} (should be NO)",
                    'line_number': last_item.get('line_number', 0),
                    'file_path': last_item.get('file_path', 'N/A')
                })
        else:
            # VIRTUAL_CONNECT not found - FAIL
            missing_items.append({
                'name': 'VIRTUAL_CONNECT setting not found (may default to ON)',
                'line_number': 0,
                'file_path': 'N/A'
            })
        
        # Convert missing_items to include line/file info in reason
        formatted_missing = []
        for item in missing_items:
            if isinstance(item, dict):
                line_num = item.get('line_number', 0)
                file_path = item.get('file_path', 'N/A')
                if line_num > 0:
                    formatted_missing.append(f"{item['name']} (Line {line_num} in {file_path})")
                else:
                    formatted_missing.append(item['name'])
            else:
                formatted_missing.append(item)
        
        # Use template helper (auto-handles waiver=0)
        # Type 1: Use TYPE1_4 reason (emphasize "found/not found")
        return self.build_complete_output(
            found_items=found_items,
            missing_items=formatted_missing,
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
        items = data.get('items', [])
        
        # Get requirements
        pattern_items = self.item_data.get('requirements', {}).get('pattern_items', [])
        
        # For this checker, pattern_items would be expected VIRTUAL_CONNECT states
        # e.g., ["VIRTUAL_CONNECT -COLON NO"] for Pegasus or ["VIRTUAL CONNECT COLON NO"] for Calibre
        
        found_items = {}
        missing_items = []
        
        if items:
            # Use last occurrence (last one wins)
            last_item = items[-1]
            item_name = last_item['name']
            
            # Check if this matches any pattern
            matched = False
            for pattern in pattern_items:
                # Normalize both pattern and item_name for comparison (case-insensitive, whitespace-normalized)
                normalized_pattern = ' '.join(pattern.upper().split())
                normalized_item = ' '.join(item_name.upper().split())
                if normalized_pattern == normalized_item or pattern.upper() in item_name.upper():
                    matched = True
                    break
            
            if matched:
                # Pattern matched - add to found_items
                line_num = last_item.get('line_number', 0)
                file_path = last_item.get('file_path', 'N/A')
                found_items[item_name] = {
                    'name': item_name,
                    'line_number': line_num,
                    'file_path': file_path,
                    'reason': f"{self.FOUND_REASON_TYPE2_3} (Line {line_num} in {file_path})"
                }
            else:
                # Pattern not matched - add to missing_items
                line_num = last_item.get('line_number', 0)
                file_path = last_item.get('file_path', 'N/A')
                missing_items.append(f"Expected pattern not found, got {item_name} (Line {line_num} in {file_path})")
        else:
            # No VIRTUAL_CONNECT found
            missing_items.extend(pattern_items)
        
        # Use template helper (auto-handles waiver=0)
        # Type 2: Use TYPE2_3 desc+reason (emphasize "matched/satisfied") - API-026
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
        items = parsed_data.get('items', [])
        
        # FIX [KNOWN_ISSUE_API-016]: Use waivers.get() directly to preserve dict format
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # Get requirements
        pattern_items = self.item_data.get('requirements', {}).get('pattern_items', [])
        
        # Find violations (items that don't match expected patterns)
        found_items = {}
        violations = []
        
        if items:
            # Use last occurrence (last one wins)
            last_item = items[-1]
            item_name = last_item['name']
            
            # Check if this matches any expected pattern
            matched = False
            for pattern in pattern_items:
                # Normalize both pattern and item_name for comparison
                normalized_pattern = ' '.join(pattern.upper().split())
                normalized_item = ' '.join(item_name.upper().split())
                if normalized_pattern == normalized_item or pattern.upper() in item_name.upper():
                    matched = True
                    break
            
            if matched:
                # Pattern matched - add to found_items
                line_num = last_item.get('line_number', 0)
                file_path = last_item.get('file_path', 'N/A')
                found_items[item_name] = {
                    'name': item_name,
                    'line_number': line_num,
                    'file_path': file_path,
                    'reason': f"{self.FOUND_REASON_TYPE2_3} (Line {line_num} in {file_path})"
                }
            else:
                # Pattern not matched - this is a violation
                violations.append({
                    'name': item_name,
                    'line_number': last_item.get('line_number', 0),
                    'file_path': last_item.get('file_path', 'N/A')
                })
        else:
            # No VIRTUAL_CONNECT found - violation
            violations.append({
                'name': 'VIRTUAL_CONNECT_NOT_FOUND',
                'line_number': 0,
                'file_path': 'N/A'
            })
        
        # Separate waived/unwaived using template helper
        waived_items = {}
        unwaived_items = []
        
        for violation in violations:
            violation_name = violation['name'] if isinstance(violation, dict) else violation
            if self.match_waiver_entry(violation_name, waive_dict):
                # Get the item data for waived items
                if isinstance(violation, dict):
                    line_num = violation.get('line_number', 0)
                    file_path = violation.get('file_path', 'N/A')
                    waived_items[violation_name] = {
                        'name': violation_name,
                        'line_number': line_num,
                        'file_path': file_path,
                        'reason': f"{self.WAIVED_BASE_REASON} (Line {line_num} in {file_path})"
                    }
                else:
                    waived_items[violation_name] = {
                        'name': violation_name,
                        'line_number': 0,
                        'file_path': 'N/A'
                    }
            else:
                # Format unwaived items with line/file info
                if isinstance(violation, dict):
                    line_num = violation.get('line_number', 0)
                    file_path = violation.get('file_path', 'N/A')
                    if line_num > 0:
                        unwaived_items.append(f"{violation_name} (Line {line_num} in {file_path})")
                    else:
                        unwaived_items.append(violation_name)
                else:
                    unwaived_items.append(violation_name)
        
        # Find unused waivers by checking if waiver names were used
        used_names = set(waived_items.keys())
        unused_waivers = [name for name in waive_dict.keys() if name not in used_names]
        
        # Use template helper for automatic output formatting (waivers.value>0)
        # Type 3: Use TYPE2_3 desc+reason (emphasize "matched/satisfied") - API-026
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
            waived_base_reason=self.WAIVED_BASE_REASON,
            unused_waiver_reason=self.UNUSED_WAIVER_REASON
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
        items = data.get('items', [])
        
        # FIX [KNOWN_ISSUE_API-016]: Use waivers.get() directly to preserve dict format
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # Check if VIRTUAL_CONNECT is disabled
        found_items = {}
        violations = []
        
        if items:
            # Use last occurrence
            last_item = items[-1]
            if last_item['is_disabled']:
                # VIRTUAL_CONNECT is disabled - PASS
                line_num = last_item.get('line_number', 0)
                file_path = last_item.get('file_path', 'N/A')
                found_items[last_item['name']] = {
                    'name': last_item['name'],
                    'line_number': line_num,
                    'file_path': file_path,
                    'reason': f"{self.FOUND_REASON_TYPE1_4} (Line {line_num} in {file_path})"
                }
            else:
                # VIRTUAL_CONNECT is enabled - violation
                violations.append({
                    'name': last_item['name'],
                    'line_number': last_item.get('line_number', 0),
                    'file_path': last_item.get('file_path', 'N/A')
                })
        else:
            # VIRTUAL_CONNECT not found - violation
            violations.append({
                'name': 'VIRTUAL_CONNECT_NOT_FOUND',
                'line_number': 0,
                'file_path': 'N/A'
            })
        
        # Separate waived/unwaived using template helper
        waived_items = {}
        unwaived_items = []
        
        for violation in violations:
            violation_name = violation['name'] if isinstance(violation, dict) else violation
            if self.match_waiver_entry(violation_name, waive_dict):
                # Get the item data for waived items
                if isinstance(violation, dict):
                    line_num = violation.get('line_number', 0)
                    file_path = violation.get('file_path', 'N/A')
                    waived_items[violation_name] = {
                        'name': violation_name,
                        'line_number': line_num,
                        'file_path': file_path,
                        'reason': f"{self.WAIVED_BASE_REASON} (Line {line_num} in {file_path})"
                    }
                else:
                    waived_items[violation_name] = {
                        'name': violation_name,
                        'line_number': 0,
                        'file_path': 'N/A'
                    }
            else:
                # Format unwaived items with line/file info
                if isinstance(violation, dict):
                    line_num = violation.get('line_number', 0)
                    file_path = violation.get('file_path', 'N/A')
                    if line_num > 0:
                        unwaived_items.append(f"{violation_name} (Line {line_num} in {file_path})")
                    else:
                        unwaived_items.append(violation_name)
                else:
                    unwaived_items.append(violation_name)
        
        # Find unused waivers
        used_names = set(waived_items.keys())
        unused_waivers = [name for name in waive_dict.keys() if name not in used_names]
        
        # Use template helper for automatic output formatting (waivers.value>0)
        # Type 4: Use TYPE1_4 reason (emphasize "found/not found")
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
            waived_base_reason=self.WAIVED_BASE_REASON,
            unused_waiver_reason=self.UNUSED_WAIVER_REASON
        )
    
    # =========================================================================
    # Helper Methods (Optional - Add as needed)
    # =========================================================================
    
    def _matches_waiver(self, item: str, waive_patterns: List[str]) -> bool:
        """
        Check if item matches any waiver pattern.
        
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
    checker = Check_12_0_0_10()
    checker.init_checker(Path(__file__))
    result = checker.execute_check()
    checker.write_output(result)
    return 0 if result.is_pass else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())