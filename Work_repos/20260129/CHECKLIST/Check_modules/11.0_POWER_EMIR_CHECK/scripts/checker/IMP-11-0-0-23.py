################################################################################
# Script Name: IMP-11-0-0-23.py
#
# Purpose:
#   Confirm all Warning message in power analysis log files can be waived.
#
# Logic:
#   - Parse power analysis log files (.logv) to extract warning messages
#   - Extract warning codes (e.g., IMPLF-378, LEFPARS-2001) and full messages
#   - Handle multi-line warning messages with continuation detection
#   - Compare extracted warnings against approved waiver list
#   - Report unwaived warnings as failures requiring review
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
# Author: Muhan Xing
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
class Check_11_0_0_23(InputFileParserMixin, OutputBuilderMixin, WaiverHandlerMixin, BaseChecker):
    """
    IMP-11-0-0-23: Confirm all Warning message in power analysis log files can be waived.
    
    Checking Types:
    - Type 1: requirements=N/A, pattern_items [], waivers=N/A/0 → Boolean Check
    - Type 2: requirements>0, pattern_items [...], waivers=N/A/0 → Value Check
    - Type 3: requirements>0, pattern_items [...], waivers>0 → Value Check with Waiver Logic
    - Type 4: requirements=N/A, pattern_items [], waivers=N/A/0 → Boolean Check with Waiver Logic
    
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
    FOUND_DESC_TYPE1_4 = "Approved warnings found in power analysis logs"
    MISSING_DESC_TYPE1_4 = "Unwaived warnings found in power analysis logs"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_DESC_TYPE2_3 = "Required warning codes found in power analysis logs"
    MISSING_DESC_TYPE2_3 = "Required warning codes not found in power analysis logs"
    
    # All Types (waiver description unified)
    WAIVED_DESC = "Waived power analysis warnings"
    
    # =========================================================================
    # ⭐ REASON CONSTANTS - Split by Type semantics (API-025)
    # =========================================================================
    # ALL Types pass found_reason/missing_reason, but use different constants
    
    # Type 1/4: Boolean checks - emphasize "found/not found" (existence)
    FOUND_REASON_TYPE1_4 = "Warning found in approved waiver list"
    MISSING_REASON_TYPE1_4 = "Warning not found in approved waiver list - requires review"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_REASON_TYPE2_3 = "Warning code matched and validated against waiver list"
    MISSING_REASON_TYPE2_3 = "Warning code not satisfied by waiver list - requires approval"
    
    # Waiver-related (Type 3/4 only)
    WAIVED_BASE_REASON = "Warning waived per approved waiver list"
    UNUSED_WAIVER_REASON = "Waiver not matched - no corresponding warning found in logs"
    
    def __init__(self):
        """Initialize the checker."""
        super().__init__(
            check_module="11.0_POWER_EMIR_CHECK",
            item_id="IMP-11-0-0-23",
            item_desc="Confirm all Warning message in power analysis log files can be waived."
        )
        # Custom member variables for parsed data
        self._parsed_items: List[Dict[str, Any]] = []
        self._metadata: Dict[str, str] = {}
        self._warning_counts: Dict[str, int] = {}
    
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
        Parse power analysis log files to extract warning messages.
        
        Extracts warnings from Cadence Voltus .logv files with:
        - Warning codes (e.g., IMPLF-378, LEFPARS-2001)
        - Full warning messages (including multi-line continuations)
        - File path and line number context
        - Timestamp metadata
        
        Patterns:
        - **WARN: (CODE): message
        - WARNING (CODE): message
        - Multi-line continuation detection
        
        Returns:
            Dict with parsed data:
            - 'items': List[Dict] - Warning items with code, message, file, line
            - 'metadata': Dict - File metadata (tool version, date, etc.)
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
        warning_counts = {}
        
        # Compile regex patterns for efficiency
        warn_pattern1 = re.compile(r'\*\*WARN:\s*\(([A-Z_]+-\d+)\):\s*(.+)')
        warn_pattern2 = re.compile(r'WARNING\s+\(([A-Z_]+-\d+)\):\s*(.+)')
        timestamp_pattern = re.compile(r'^\[(\d{2}/\d{2})\s+(\d{2}:\d{2}:\d{2})\s+\d+s\]\s*(.+)')
        
        # 3. Parse each input file for warning information
        for file_path in valid_files:
            try:
                current_warning = None
                current_warning_line = 0
                lines_since_warning = 0
                
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line_num, line in enumerate(f, 1):
                        # Extract timestamp and actual content
                        timestamp_match = timestamp_pattern.match(line)
                        if timestamp_match:
                            actual_content = timestamp_match.group(3)
                            
                            # Check for new warning (Pattern 1: **WARN:)
                            warn_match1 = warn_pattern1.match(actual_content)
                            if warn_match1:
                                # Save previous warning if exists
                                if current_warning:
                                    items.append(current_warning)
                                    warning_counts[current_warning['name']] = warning_counts.get(current_warning['name'], 0) + 1
                                
                                # Start new warning
                                warning_code = warn_match1.group(1)
                                warning_message = warn_match1.group(2).strip()
                                current_warning = {
                                    'name': warning_code,
                                    'message': warning_message,
                                    'line_number': line_num,
                                    'file_path': str(file_path),
                                    'type': 'warning'
                                }
                                current_warning_line = line_num
                                lines_since_warning = 0
                                continue
                            
                            # Check for new warning (Pattern 2: WARNING)
                            warn_match2 = warn_pattern2.match(actual_content)
                            if warn_match2:
                                # Save previous warning if exists
                                if current_warning:
                                    items.append(current_warning)
                                    warning_counts[current_warning['name']] = warning_counts.get(current_warning['name'], 0) + 1
                                
                                # Start new warning
                                warning_code = warn_match2.group(1)
                                warning_message = warn_match2.group(2).strip()
                                current_warning = {
                                    'name': warning_code,
                                    'message': warning_message,
                                    'line_number': line_num,
                                    'file_path': str(file_path),
                                    'type': 'warning'
                                }
                                current_warning_line = line_num
                                lines_since_warning = 0
                                continue
                            
                            # Check for continuation line (only within 3 lines of warning start)
                            if current_warning and lines_since_warning < 3:
                                # Only continue if line doesn't start with common non-warning patterns
                                if not any(pattern in actual_content for pattern in [
                                    '**WARN:', 'WARNING (', '**ERROR:', 'ERROR (',
                                    '<CMD>', '**INFO:', 'AAE_INFO:', 'defIn read', 'TimeStamp',
                                    'Reading ', 'Loading ', 'Total ', 'List of', 'End ',
                                    'Summary for', 'Number of', 'Visiting view', 'Honor LEF',
                                    'Start create', 'Set Default', 'Extraction setup',
                                    'Calculated ', 'End delay', 'End Timing'
                                ]):
                                    # This looks like a continuation of the warning message
                                    continuation_text = actual_content.strip()
                                    if continuation_text:
                                        current_warning['message'] += ' ' + continuation_text
                                    lines_since_warning += 1
                                    continue
                            
                            # If we hit a new command or other pattern, finalize current warning
                            if current_warning:
                                lines_since_warning += 1
                                if lines_since_warning >= 3 or any(keyword in actual_content for keyword in [
                                    '<CMD>', '**INFO:', '**ERROR:', 'AAE_INFO:', 'defIn read', 
                                    'TimeStamp', 'End ', 'Start ', 'Honor LEF', 'Set Default'
                                ]):
                                    items.append(current_warning)
                                    warning_counts[current_warning['name']] = warning_counts.get(current_warning['name'], 0) + 1
                                    current_warning = None
                                    lines_since_warning = 0
                
                # Save last warning if exists
                if current_warning:
                    items.append(current_warning)
                    warning_counts[current_warning['name']] = warning_counts.get(current_warning['name'], 0) + 1
                    
            except Exception as e:
                errors.append(f"Error parsing {file_path}: {str(e)}")
        
        # 4. Store frequently reused data on self
        self._parsed_items = items
        self._warning_counts = warning_counts
        
        return {
            'items': items,
            'metadata': metadata,
            'errors': errors
        }
    
    # =========================================================================
    # Type 1: Boolean Check
    # =========================================================================
    
    def _execute_type1(self) -> CheckResult:
        """Type 1: Boolean check without waiver support."""
        violations = self._type1_core_logic()
        
        # Build found_items dict from warnings that ARE approved
        data = self._parse_input_files()
        items = data.get('items', [])
        
        found_items = {}
        for warning in items:
            warning_code = warning.get('name', 'UNKNOWN')
            if self._is_warning_approved(warning_code):
                # This warning is approved - add to found_items with full message
                warning_msg = warning.get('message', '')
                # Use full message as key for better output readability
                item_key = f"{warning_code}: {warning_msg}"
                found_items[item_key] = {
                    'line_number': warning.get('line_number', 0),
                    'file_path': warning.get('file_path', 'N/A')
                }
        
        # Convert violations dict to dict format for missing_items
        missing_items = {}
        for viol_name, viol_data in violations.items():
            missing_items[viol_name] = viol_data
        
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
        
        Returns:
            Dict of violations: {warning_code: {'line_number': ..., 'file_path': ..., 'reason': ...}}
            Empty dict if all checks pass (all warnings in approved list).
        """
        data = self._parse_input_files()
        items = data.get('items', [])
        
        violations = {}
        
        # Check each warning against approved waiver list
        for warning in items:
            warning_code = warning.get('name', 'UNKNOWN')
            warning_msg = warning.get('message', '')
            
            # Check if warning code is in approved waiver list
            if not self._is_warning_approved(warning_code):
                # Warning not in approved list - this is a violation
                # Include full message in violation_key for better output readability
                violation_key = f"{warning_code}: {warning_msg}"
                violations[violation_key] = {
                    'line_number': warning.get('line_number', 0),
                    'file_path': warning.get('file_path', 'N/A')
                }
        
        return violations
    
    def _is_warning_approved(self, warning_code: str) -> bool:
        """
        Check if warning code is in the approved waiver list from config.
        
        Args:
            warning_code: Warning code to check (e.g., 'IMPLF-378', 'LEFPARS-2001')
        
        Returns:
            True if warning is approved (in waive_items), False otherwise
        """
        # Get waive_items from config file (for Type 1/4)
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        
        # Parse waive_items to get approved warning codes
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # Check if warning_code matches any waiver entry (exact or pattern match)
        for waiver_key in waive_dict.keys():
            # Extract warning code from waiver_key (format: "CODE: message" or just "CODE")
            if ':' in waiver_key:
                waiver_code = waiver_key.split(':')[0].strip()
            else:
                waiver_code = waiver_key.strip()
            
            # Exact match or pattern match (case-insensitive)
            if warning_code.upper() == waiver_code.upper():
                return True
        
        return False
    
    # =========================================================================
    # Type 2: Value Check
    # =========================================================================
    
    def _execute_type2(self) -> CheckResult:
        """Type 2: Pattern/value check without waiver support."""
        found_items, missing_items = self._type2_core_logic()
        
        # Define name extractor to use clean display names
        def extract_clean_name(item_name: str, metadata: dict) -> str:
            return metadata.get('display_name', item_name)
        
        return self.build_complete_output(
            found_items=found_items,
            missing_items=missing_items,
            found_desc=self.FOUND_DESC_TYPE2_3,
            missing_desc=self.MISSING_DESC_TYPE2_3,
            found_reason=self.FOUND_REASON_TYPE2_3,
            missing_reason=self.MISSING_REASON_TYPE2_3,
            name_extractor=extract_clean_name
        )
    
    def _type2_core_logic(self) -> Tuple[Dict[str, dict], Dict[str, dict]]:
        """
        Core Type 2 pattern matching logic (shared by Type 2 and Type 3).
        
        For Type 2 (no waiver support):
        - Scans logs for all instances of pattern_items warnings
        - All found instances are returned as missing_items (violations)
        - found_items is empty (no waiver support means nothing can pass)
        
        For Type 3 (with waiver support):
        - Same scanning logic, but caller will split violations based on waiver list
        
        Returns:
            Tuple of (found_items, missing_items)
            - found_items: Always empty for Type 2
            - missing_items: All instances of pattern_items warnings found in logs
        """
        data = self._parse_input_files()
        items = data.get('items', [])
        
        requirements = self.item_data.get('requirements', {})
        pattern_items = requirements.get('pattern_items', [])
        
        found_items = {}  # Empty for Type 2 (no waiver support)
        
        # Create file order mapping based on input_files order
        input_files = self.item_data.get('input_files', [])
        # Resolve environment variables in file paths
        resolved_files = []
        for fpath in input_files:
            # Replace ${CHECKLIST_ROOT} with actual root path
            resolved = fpath.replace('${CHECKLIST_ROOT}', str(self.root))
            # Convert to Path and resolve to absolute path
            resolved_path = Path(resolved).resolve()
            resolved_files.append(str(resolved_path))
        
        # Create order index: {file_path: order_index}
        file_order_map = {fpath: idx for idx, fpath in enumerate(resolved_files)}
        
        # Collect all matching warnings into a list first
        violations_list = []
        
        # Scan logs for all instances of required warning patterns
        for pattern in pattern_items:
            for item in items:
                warning_code = item.get('name', '')
                warning_msg = item.get('message', '')
                file_path = item.get('file_path', 'N/A')
                line_number = item.get('line_number', 0)
                
                # EXACT MATCH: pattern_items are specific warning codes (e.g., "IMPLF-378")
                if pattern.lower() == warning_code.lower():
                    # Get file order (default to 9999 for files not in input_files)
                    file_order = file_order_map.get(file_path, 9999)
                    
                    violations_list.append({
                        'code': warning_code,
                        'message': warning_msg,
                        'file_path': file_path,
                        'line_number': line_number,
                        'file_order': file_order
                    })
        
        # Sort by file order first (based on input_files), then by line_number
        # This groups all warnings from the same file together in input_files order
        violations_list.sort(key=lambda x: (x['file_order'], x['line_number']))
        
        # Build missing_items dict with simple format
        # Use index to ensure unique keys while maintaining clean display format
        missing_items = {}
        for idx, viol in enumerate(violations_list):
            # Simple format: "CODE: message"
            # Append hidden index to ensure uniqueness (zero-width space + index)
            item_key = f"{viol['code']}: {viol['message']}\u200b{idx}"
            
            # Store the clean display name in metadata for extraction
            missing_items[item_key] = {
                'line_number': viol['line_number'],
                'file_path': viol['file_path'],
                'display_name': f"{viol['code']}: {viol['message']}"  # Clean name without index
            }
        
        return found_items, missing_items
    
    # =========================================================================
    # Type 3: Value Check with Waiver Logic
    # =========================================================================
    
    def _execute_type3(self) -> CheckResult:
        """Type 3: Pattern/value check with waiver support (reuses Type 2 core logic)."""
        # Step 1: Get all warning instances from Type 2's core logic
        # For Type 3, we treat the result differently:
        # - found_items_base is empty (Type 2 returns empty for found_items)
        # - violations contains ALL warning instances that need waiver check
        found_items_base, violations = self._type2_core_logic()
        
        # Step 2: Parse waiver configuration
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # Step 3: Split violations into waived and unwaived
        # In Type 3, violations that match waiver list become found_items (pass)
        # Violations that don't match waiver list stay as missing_items (fail)
        found_items = {}  # Warnings that are in waiver list (pass)
        waived_items = {}  # Same as found_items but tracked separately for output
        missing_items = {}  # Warnings not in waiver list (fail)
        used_waivers = set()
        
        for viol_name, viol_data in violations.items():
            # Extract clean display name for waiver matching (without zero-width space and index)
            # This ensures waiver matching uses the clean warning message, not the internal dict key
            clean_name = viol_data.get('display_name', viol_name)
            
            matched_waiver = self.match_waiver_entry(clean_name, waive_dict)
            if matched_waiver:
                # Warning is in waiver list - it passes
                found_items[viol_name] = viol_data
                waived_items[viol_name] = viol_data
                used_waivers.add(matched_waiver)
            else:
                # Warning is NOT in waiver list - it fails
                missing_items[viol_name] = viol_data
        
        # Step 4: Find unused waivers
        unused_waivers = [w for w in waive_dict.keys() if w not in used_waivers]
        
        # Step 5: Define name extractor to use clean display names
        def extract_clean_name(item_name: str, metadata: dict) -> str:
            return metadata.get('display_name', item_name)
        
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
            unused_waiver_reason=self.UNUSED_WAIVER_REASON,
            name_extractor=extract_clean_name
        )
    
    # =========================================================================
    # Type 4: Boolean Check with Waiver Logic
    # =========================================================================
    
    def _execute_type4(self) -> CheckResult:
        """Type 4: Boolean check with waiver support."""
        # Parse all warnings from log files
        data = self._parse_input_files()
        items = data.get('items', [])
        
        # Get waiver configuration
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # Categorize all warnings
        waived_items = {}  # Warnings in waive_items (Info)
        missing_items = {}  # Warnings NOT in waive_items (Fail)
        used_waivers = set()
        
        for warning in items:
            warning_code = warning.get('name', 'UNKNOWN')
            warning_msg = warning.get('message', '')
            item_key = f"{warning_code}: {warning_msg}"
            
            metadata = {
                'line_number': warning.get('line_number', 0),
                'file_path': warning.get('file_path', 'N/A')
            }
            
            # Check if this warning matches any waiver
            matched_waiver = self.match_waiver_entry(warning_code, waive_dict)
            if matched_waiver:
                # Warning is in waive_items - it passes
                waived_items[item_key] = metadata
                used_waivers.add(matched_waiver)
            else:
                # Warning is NOT in waive_items - it fails
                missing_items[item_key] = metadata
        
        # Find unused waivers (waivers with no matching warnings in logs)
        unused_waivers = [w for w in waive_dict.keys() if w not in used_waivers]
        
        return self.build_complete_output(
            found_items={},  # Type 4 has no "found_items" concept (all warnings are either waived or failures)
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
    checker = Check_11_0_0_23()
    checker.init_checker(Path(__file__))
    result = checker.execute_check()
    checker.write_output(result)
    return 0 if result.is_pass else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())