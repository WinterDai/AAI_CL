################################################################################
# Script Name: IMP-11-0-0-22.py
#
# Purpose:
#   Confirm no ERROR message in power analysis log files.
#
# Logic:
#   - Parse power analysis log files (.logv) to extract ERROR messages
#   - Extract error code (if present), full error message text, line number, and file path
#   - Verify no ERROR messages exist in any log file
#   - Support waiver for specific error codes if configured
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
class Check_11_0_0_22(InputFileParserMixin, OutputBuilderMixin, WaiverHandlerMixin, BaseChecker):
    """
    IMP-11-0-0-22: Confirm no ERROR message in power analysis log files.
    
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
    FOUND_DESC_TYPE1_4 = "No ERROR messages found in power analysis logs"
    MISSING_DESC_TYPE1_4 = "ERROR messages detected in power analysis logs"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_DESC_TYPE2_3 = "No ERROR messages detected - power analysis completed successfully"
    MISSING_DESC_TYPE2_3 = "ERROR messages found - power analysis validation failed"
    
    # All Types (waiver description unified)
    WAIVED_DESC = "Waived ERROR messages in power analysis logs"
    
    # ⭐ REASON CONSTANTS - Split by Type semantics (API-025)
    # ALL Types pass found_reason/missing_reason, but use different constants
    
    # Type 1/4: Boolean checks - emphasize "found/not found" (existence)
    FOUND_REASON_TYPE1_4 = "No ERROR messages found in power analysis log files"
    MISSING_REASON_TYPE1_4 = "ERROR message detected in power analysis log file"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_REASON_TYPE2_3 = "This power analysis log validated - no ERROR patterns matched"
    MISSING_REASON_TYPE2_3 = "ERROR pattern matched - power analysis contains errors"
    
    # Waiver-related (Type 3/4 only)
    WAIVED_BASE_REASON = "ERROR message waived per design team approval"
    UNUSED_WAIVER_REASON = "Waiver entry not matched - no corresponding ERROR found in logs"
    
    def __init__(self):
        """Initialize the checker."""
        super().__init__(
            check_module="11.0_POWER_EMIR_CHECK",
            item_id="IMP-11-0-0-22",
            item_desc="Confirm no ERROR message in power analysis log files."
        )
        # Custom member variables for parsed data
        self._parsed_items: List[Dict[str, Any]] = []
        self._metadata: Dict[str, str] = {}
        self._error_count: int = 0
        self._warning_count: int = 0
    
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
        Parse power analysis log files to extract ERROR messages.
        
        Scans .logv files for ERROR patterns using multiple regex patterns:
        - Pattern 1: **ERROR: (ERROR_CODE): message
        - Pattern 2: ERROR: message (no code)
        - Pattern 3: Case-insensitive error variations
        
        Also tracks WARNING messages for statistics (not reported as errors).
        
        Returns:
            Dict with parsed data:
            - 'items': List[Dict] - ERROR messages with metadata (name, line_number, file_path, error_code, message)
            - 'metadata': Dict - File metadata (error_count, warning_count, files_processed)
            - 'errors': List - Parsing errors encountered
            - 'clean_files': Dict - Files with no ERROR messages
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
        error_count = 0
        warning_count = 0
        clean_files = {}
        files_with_errors = set()
        
        # Define ERROR patterns (priority order)
        # FIXED: Match all ERROR lines, including those with numbers before them
        error_patterns = [
            # Pattern 1: **ERROR: (ERROR_CODE): message
            (r'\*\*ERROR:\s*\(([A-Z_]+-\d+)\):\s*(.+)', 'coded_error'),
            # Pattern 2: Generic ERROR: message (anywhere in line)
            (r'ERROR:\s+(.+)$', 'generic_error'),
        ]
        
        # Define WARNING patterns (for statistics only)
        warning_patterns = [
            r'\*\*WARN:\s*\(([A-Z_]+-\d+)\):\s*(.+)',
            r'WARNING\s+\(([A-Z_]+-\d+)\):\s*(.+)'
        ]
        
        # 3. Parse each input file for ERROR messages
        for file_path in valid_files:
            file_has_errors = False
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line_num, line in enumerate(f, 1):
                        line_stripped = line.strip()
                        
                        # Check for ERROR patterns
                        error_matched = False
                        for pattern, pattern_type in error_patterns:
                            match = re.search(pattern, line_stripped)
                            if match:
                                error_matched = True
                                error_count += 1
                                file_has_errors = True
                                files_with_errors.add(str(file_path))
                                
                                # Extract error details based on pattern type
                                if pattern_type == 'coded_error':
                                    error_code = match.group(1)
                                    error_message = match.group(2).strip()
                                elif pattern_type == 'generic_error':
                                    error_code = None
                                    error_message = match.group(1).strip()
                                else:  # case_insensitive_error
                                    error_code = None
                                    error_message = match.group(1).strip()
                                
                                # Build item name with full context
                                if error_code:
                                    item_name = f"[{file_path.name}:{line_num}] ERROR ({error_code}): {error_message}"
                                else:
                                    item_name = f"[{file_path.name}:{line_num}] ERROR: {error_message}"
                                
                                items.append({
                                    'name': item_name,
                                    'line_number': line_num,
                                    'file_path': str(file_path),
                                    'error_code': error_code,
                                    'error_message': error_message,
                                    'type': 'error'
                                })
                                break  # Stop after first match
                        
                        # If no ERROR matched, check for WARNING patterns (statistics only)
                        if not error_matched:
                            for pattern in warning_patterns:
                                if re.search(pattern, line_stripped):
                                    warning_count += 1
                                    break
                        
            except Exception as e:
                errors.append(f"Error parsing {file_path}: {str(e)}")
        
        # 4. Build clean_files dict (files with no ERROR messages)
        for file_path in valid_files:
            file_path_str = str(file_path)
            if file_path_str not in files_with_errors:
                file_name = file_path.name
                clean_files[file_name] = {
                    'name': file_name,
                    'line_number': 0,
                    'file_path': file_path_str
                }
        
        # 5. Store frequently reused data on self
        self._parsed_items = items
        self._error_count = error_count
        self._warning_count = warning_count
        self._metadata = {
            'files_processed': len(valid_files),
            'error_count': error_count,
            'warning_count': warning_count
        }
        
        return {
            'items': items,
            'metadata': self._metadata,
            'errors': errors,
            'clean_files': clean_files
        }
    
    # =========================================================================
    # Type 1: Boolean Check
    # =========================================================================
    
    def _execute_type1(self) -> CheckResult:
        """Type 1: Boolean check without waiver support."""
        violations = self._type1_core_logic()
        
        # Build found_items from clean log files (files with no ERROR messages)
        data = self._parse_input_files()
        clean_files = data.get('clean_files', {})
        
        # ⚠️ CRITICAL: found_items MUST be dict[str, dict], NOT list!
        found_items = {}
        for file_name, file_data in clean_files.items():
            found_items[file_name] = {
                'name': file_name,
                'line_number': file_data.get('line_number', 0),
                'file_path': file_data.get('file_path', 'N/A')
            }
        
        # ⚠️ CRITICAL: missing_items MUST be dict[str, dict], NOT list!
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
        
        Returns:
            Dict of violations: {error_key: {'line_number': ..., 'file_path': ..., 'reason': ...}}
            Empty dict if all checks pass (no ERROR messages found).
        """
        data = self._parse_input_files()
        items = data.get('items', [])
        
        violations = {}
        
        # Check for ERROR messages in parsed log files
        for item in items:
            error_code = item.get('error_code', '')
            error_message = item.get('error_message', '')
            line_number = item.get('line_number', 0)
            file_path = item.get('file_path', 'N/A')
            
            # Build unique key for this error (file:line or error_code)
            if error_code:
                error_key = f"[{Path(file_path).name}:{line_number}] ERROR ({error_code}): {error_message}"
            else:
                error_key = f"[{Path(file_path).name}:{line_number}] ERROR: {error_message}"
            
            violations[error_key] = {
                'line_number': line_number,
                'file_path': file_path
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
            - found_items: {file_path: {'line_number': ..., 'file_path': ...}} for files with no ERROR patterns
            - missing_items: {error_key: {'line_number': ..., 'file_path': ..., 'message': ...}} for ERROR patterns found
        """
        data = self._parse_input_files()
        items = data.get('items', [])  # List of ERROR messages found
        
        requirements = self.item_data.get('requirements', {})
        pattern_items = requirements.get('pattern_items', [])
        
        found_items = {}
        missing_items = {}
        
        # Get all input files
        input_files = self.item_data.get('input_files', [])
        
        # Track which files have ERROR patterns
        files_with_errors = set()
        
        # Check each ERROR message against pattern_items
        for item in items:
            error_code = item.get('error_code') or ''
            error_message = item.get('error_message') or ''
            file_path = item.get('file_path', 'N/A')
            line_number = item.get('line_number', 0)
            
            # Check if this ERROR matches any pattern in pattern_items
            matched_pattern = False
            for pattern in pattern_items:
                # Skip None or empty patterns
                if not pattern:
                    continue
                # SUBSTRING MATCH: Check if pattern appears in error code or message
                if pattern.lower() in error_code.lower() or pattern.lower() in error_message.lower():
                    matched_pattern = True
                    break
            
            if matched_pattern:
                # ERROR pattern matched - this is a violation
                files_with_errors.add(file_path)
                # Build error_key with proper format (check if error_code exists)
                if error_code:
                    error_key = f"[{Path(file_path).name}:{line_number}] ERROR ({error_code}): {error_message}"
                else:
                    error_key = f"[{Path(file_path).name}:{line_number}] ERROR: {error_message}"
                missing_items[error_key] = {
                    'line_number': line_number,
                    'file_path': file_path,
                    'message': error_message,
                    'error_code': error_code
                }
        
        # Files without ERROR patterns are found_items (clean files)
        # Re-validate to get actual file paths
        valid_files, _ = self.validate_input_files()
        
        for file_path in valid_files:
            file_path_str = str(file_path)
            
            if file_path_str not in files_with_errors:
                # No ERROR patterns found in this file
                file_name = file_path.name
                found_items[file_name] = {
                    'line_number': 0,
                    'file_path': file_path_str
                }
        
        return found_items, missing_items
    
    # =========================================================================
    # Type 3: Value Check with Waiver Logic
    # =========================================================================
    
    def _execute_type3(self) -> CheckResult:
        """Type 3: Pattern/value check with waiver support (reuses Type 2 core logic)."""
        # Step 1: Get found/missing items using Type 2's core logic
        found_items, violations = self._type2_core_logic()
        
        # Step 2: Parse waiver configuration (FIXED: API-016)
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
        
        # Step 5: Build output (FIXED: API-009 - pass dict directly)
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
        """Type 4: Boolean check with waiver support (reuses Type 1 core logic)."""
        violations = self._type1_core_logic()
        
        # Build found_items from clean log files (files with no ERROR messages)
        data = self._parse_input_files()
        clean_files = data.get('clean_files', {})
        
        # ⚠️ CRITICAL: found_items MUST be dict[str, dict], NOT list!
        found_items = {}
        for file_name, file_data in clean_files.items():
            found_items[file_name] = {
                'name': file_name,
                'line_number': file_data.get('line_number', 0),
                'file_path': file_data.get('file_path', 'N/A')
            }
        
        # Parse waiver configuration (FIXED: API-016)
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # Separate waived/unwaived
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
        
        # Build output with custom waived reason that includes waiver reason
        return self._build_type4_output_with_reasons(
            found_items=found_items,
            missing_items=missing_items,
            waived_items=waived_items,
            unused_waivers=unused_waivers,
            waive_dict=waive_dict
        )
    
    def _build_type4_output_with_reasons(
        self,
        found_items: Dict[str, Dict],
        missing_items: Dict[str, Dict],
        waived_items: Dict[str, Dict],
        unused_waivers: List[str],
        waive_dict: Dict[str, str]
    ) -> CheckResult:
        """
        Build Type 4 output with custom waived reasons that include waiver justification.
        
        This is a custom implementation for Type 4 to append waiver reasons to the base reason.
        """
        details = []
        
        # 1. Add found_items (INFO)
        for item_name, item_data in found_items.items():
            details.append(DetailItem(
                name=item_name,
                severity=Severity.INFO,
                reason=self.FOUND_REASON_TYPE1_4,
                line_number=item_data.get('line_number', 0),
                file_path=item_data.get('file_path', 'N/A')
            ))
        
        # 2. Add missing_items (FAIL)
        for item_name, item_data in missing_items.items():
            details.append(DetailItem(
                name=item_name,
                severity=Severity.FAIL,
                reason=self.MISSING_REASON_TYPE1_4,
                line_number=item_data.get('line_number', 0),
                file_path=item_data.get('file_path', 'N/A')
            ))
        
        # 3. Add waived_items (INFO with [WAIVER] tag and appended reason)
        for item_name, item_data in waived_items.items():
            matched_waiver = self.match_waiver_entry(item_name, waive_dict)
            if matched_waiver and matched_waiver in waive_dict:
                waiver_reason = waive_dict[matched_waiver]
                # Append waiver reason to base reason
                full_reason = f"{self.WAIVED_BASE_REASON}: {waiver_reason} [WAIVER]"
            else:
                full_reason = f"{self.WAIVED_BASE_REASON} [WAIVER]"
            
            details.append(DetailItem(
                name=item_name,
                severity=Severity.INFO,
                reason=full_reason,
                line_number=item_data.get('line_number', 0),
                file_path=item_data.get('file_path', 'N/A')
            ))
        
        # 4. Add unused_waivers (WARN with [WAIVER] tag)
        for waiver_pattern in unused_waivers:
            details.append(DetailItem(
                name=waiver_pattern,
                severity=Severity.WARN,
                reason=f"{self.UNUSED_WAIVER_REASON} [WAIVER]",
                line_number=0,
                file_path='N/A'
            ))
        
        # 5. Determine overall status
        if missing_items:
            is_pass = False
        else:
            is_pass = True
        
        return create_check_result(
            value=0,  # Type 4 is boolean check
            is_pass=is_pass,
            has_waiver_value=True,
            details=details
        )


# =========================================================================
# Entry Point
# =========================================================================

def main():
    """Main entry point."""
    checker = Check_11_0_0_22()
    checker.init_checker(Path(__file__))
    result = checker.execute_check()
    checker.write_output(result)
    return 0 if result.is_pass else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())