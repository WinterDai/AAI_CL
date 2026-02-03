################################################################################
# Script Name: IMP-10-0-0-20.py
#
# Purpose:
#   Confirm no ERROR message in the STA log files or the ERROR messages can be waived.
#
# Logic:
#   - Parse input files: tempus_1.log, tempus_2.log
#   - Extract inline ERROR messages with format **ERROR: (CODE): message
#   - Parse message summary section for error counts and codes
#   - Capture error details: code, message text, file location, line number
#   - Cross-reference detected errors against waiver list
#   - Aggregate results across multiple log files
#   - Determine PASS/FAIL based on unwaived error count
#
# Auto Type Detection:
#   Type 1: requirements.value=N/A, waivers.value=N/A/0 → Boolean check
#   Type 2: requirements.value>0, pattern_items exists, waivers.value=N/A/0 → Value comparison
#   Type 3: requirements.value>0, pattern_items exists, waivers.value>0 → Value with waiver logic
#   Type 4: requirements.value=N/A, waivers.value>0 → Boolean with waiver logic
#
# Waiver Tag Rules:
#   When waivers.value > 0 (Type 3/4):
#     - All waive_items related INFO/FAIL/WARN reason suffix: [WAIVER]
#   When waivers.value = 0 (Type 1/2):
#     - waive_items output as INFO with suffix: [WAIVED_INFO]
#     - FAIL/WARN converted to INFO with suffix: [WAIVED_AS_INFO]
#   All types support value = N/A
#
# Refactored: 2025-12-17 (Using checker_templates v1.1.0)
#
# Author: yyin
# Date: 2025-12-17
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
class Check_10_0_0_20(InputFileParserMixin, OutputBuilderMixin, WaiverHandlerMixin, BaseChecker):
    """
    IMP-10-0-0-20: Confirm no ERROR message in the STA log files or the ERROR messages can be waived.
    
    Checking Types:
    - Type 1: requirements=N/A, waivers=N/A/0 → Informational/Boolean check
    - Type 2: requirements>0, waivers=N/A/0 → Value check without waivers
    - Type 3: requirements>0, waivers>0 → Value check with waiver logic
    - Type 4: requirements=N/A, waivers=>0 → Boolean check with waiver logic
    
    Template Library v1.1.0:
    - Uses InputFileParserMixin for parsing (parse_log_with_patterns, normalize_command)
    - Uses WaiverHandlerMixin for waiver processing (parse_waive_items(waive_items_raw), match_waiver_entry(item, waive_dict))
    - Uses OutputBuilderMixin for result construction (build_complete_output(...))
    """
    
    # =========================================================================
    # UNIFIED DESCRIPTIONS - MUST be identical across ALL Type 1/2/3/4
    # =========================================================================
    FOUND_DESC = "STA log files with no errors"
    FOUND_REASON = "All STA log files completed without errors"
    MISSING_DESC = "ERROR messages detected in STA log files"
    MISSING_REASON = "STA log contains unwaived ERROR messages"
    WAIVED_DESC = "Waived ERROR messages in STA log files"
    WAIVED_BASE_REASON = "ERROR message waived per design approval"
    
    def __init__(self):
        """Initialize the checker."""
        super().__init__(
            check_module="10.0_STA_DCD_CHECK",
            item_id="IMP-10-0-0-20",
            item_desc="Confirm no ERROR message in the STA log files or the ERROR messages can be waived."
        )
        # Store parsed data
        self._parsed_items: List[Dict[str, Any]] = []
        self._total_warnings: int = 0
        self._total_errors: int = 0
    
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
        
        Parses Tempus STA log files to extract ERROR messages using multiple patterns:
        - Pattern 1: Inline ERROR messages with error codes
        - Pattern 2: WARNING messages (for context)
        - Pattern 3: Summary table entries with counts
        - Pattern 4: Final message summary line
        - Pattern 5: Generic ERROR fallback
        
        Returns:
            Dict with parsed data:
            - 'items': List[Dict] - ERROR messages with metadata (line_number, file_path)
            - 'metadata': Dict - Summary statistics (total_warnings, total_errors)
            - 'errors': List - Any parsing errors encountered
        """
        # 1. Validate input files - IMPORTANT: returns tuple (valid_files_list, missing_files_list)
        valid_files, missing_files = self.validate_input_files()
        if missing_files:
            raise ConfigurationError(
                self.create_missing_files_error(missing_files)
            )
        
        # 2. Define patterns for parsing
        # Pattern 1: Inline ERROR messages with error codes
        pattern_error_inline = re.compile(
            r'\*\*ERROR:\s*\(([A-Z0-9-]+)\):\s*(.+?)(?:\(File\s+(.+?),\s+Line\s+(\d+)\))?$'
        )
        
        # Pattern 2: WARNING messages (for context and filtering)
        pattern_warn_inline = re.compile(
            r'\*\*WARN:\s*\(([A-Z0-9-]+)\):\s*(.+?)(?:\(File\s+(.+?),\s+Line\s+(\d+)\))?$'
        )
        
        # Pattern 3: Summary table entries with counts
        pattern_summary_entry = re.compile(
            r'^(WARNING|ERROR)\s+([A-Z0-9-]+)\s+(\d+)\s+(.+)$'
        )
        
        # Pattern 4: Final message summary line
        pattern_message_summary = re.compile(
            r'\*\*\*\s+Message Summary:\s+(\d+)\s+warning\(s\),\s+(\d+)\s+error\(s\)'
        )
        
        # Pattern 5: Generic ERROR fallback (non-standard format)
        pattern_error_generic = re.compile(
            r'^ERROR[:\s]+(.+)$'
        )
        
        # 3. Parse all files
        all_errors = []
        total_warnings = 0
        total_errors = 0
        
        for file_path in valid_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line_num, line in enumerate(f, 1):
                        line = line.rstrip()
                        
                        # Check for message summary line (Pattern 4)
                        match_summary = pattern_message_summary.search(line)
                        if match_summary:
                            total_warnings += int(match_summary.group(1))
                            total_errors += int(match_summary.group(2))
                            continue
                        
                        # Check for inline ERROR messages (Pattern 1)
                        match_error = pattern_error_inline.search(line)
                        if match_error:
                            error_code = match_error.group(1)
                            error_msg = match_error.group(2)
                            error_file = match_error.group(3) if match_error.group(3) else 'N/A'
                            error_line = match_error.group(4) if match_error.group(4) else 'N/A'
                            
                            error_name = f"[{error_code}] {error_msg}"
                            if error_file != 'N/A':
                                error_name += f" (File: {error_file}, Line: {error_line})"
                            
                            all_errors.append({
                                'name': error_name,
                                'error_code': error_code,
                                'message': error_msg,
                                'error_file': error_file,
                                'error_line': error_line,
                                'line_number': line_num,
                                'file_path': str(file_path)
                            })
                            continue
                        
                        # Check for generic ERROR messages (Pattern 5)
                        match_generic = pattern_error_generic.search(line)
                        if match_generic:
                            error_msg = match_generic.group(1)
                            error_name = f"[UNKNOWN] {error_msg}"
                            
                            all_errors.append({
                                'name': error_name,
                                'error_code': 'UNKNOWN',
                                'message': error_msg,
                                'error_file': 'N/A',
                                'error_line': 'N/A',
                                'line_number': line_num,
                                'file_path': str(file_path)
                            })
                            continue
                        
                        # Check for summary table entries (Pattern 3) - for validation
                        match_entry = pattern_summary_entry.search(line)
                        if match_entry:
                            severity = match_entry.group(1)
                            msg_code = match_entry.group(2)
                            count = int(match_entry.group(3))
                            msg_summary = match_entry.group(4)
                            
                            # Only track ERROR entries from summary
                            if severity == 'ERROR':
                                # Check if we already have this error from inline parsing
                                existing = any(e['error_code'] == msg_code for e in all_errors)
                                if not existing:
                                    # Add summary entry as error
                                    error_name = f"[{msg_code}] {msg_summary} (Count: {count})"
                                    all_errors.append({
                                        'name': error_name,
                                        'error_code': msg_code,
                                        'message': msg_summary,
                                        'error_file': 'N/A',
                                        'error_line': 'N/A',
                                        'line_number': line_num,
                                        'file_path': str(file_path)
                                    })
            except Exception as e:
                # Log parsing error but continue
                pass
        
        # 4. Store frequently reused data on self
        self._parsed_items = all_errors
        self._total_warnings = total_warnings
        self._total_errors = total_errors
        
        # 5. Return aggregated dict with items containing line_number and file_path
        return {
            'items': all_errors,
            'metadata': {
                'total_warnings': total_warnings,
                'total_errors': total_errors,
                'total_files': len(valid_files)
            },
            'errors': []
        }
    
    # =========================================================================
    # Type 1: Informational/Boolean Check
    # =========================================================================
    
    def _execute_type1(self) -> CheckResult:
        """
        Type 1: Informational or Boolean check (no waivers).
        
        Use OutputBuilderMixin.build_complete_output() for automatic formatting.
        
        Returns:
            CheckResult with is_pass based on check logic
        """
        # Parse input
        data = self._parse_input_files()
        error_items = data.get('items', [])
        metadata = data.get('metadata', {})
        
        # Build found_items (clean files) and missing_items (files with errors)
        if not error_items:
            # No errors found - all files are clean
            found_items = {}
            input_files_list = self.item_data.get('input_files', [])
            for idx, file_path in enumerate(input_files_list, 1):
                file_name = Path(file_path).name
                found_items[file_name] = {
                    'name': file_name,
                    'line_number': 0,
                    'file_path': str(file_path)
                }
            missing_items = []
        else:
            # Errors found - convert to missing_items
            found_items = {}
            missing_items = []
            for error in error_items:
                missing_items.append(error['name'])
        
        # Use template helper
        return self.build_complete_output(
            found_items=found_items,
            missing_items=missing_items,
            found_desc=self.FOUND_DESC,
            missing_desc=self.MISSING_DESC,
            found_reason=self.FOUND_REASON,
            missing_reason=self.MISSING_REASON
        )
    
    # =========================================================================
    # Type 2: Value comparison
    # =========================================================================
    
    def _execute_type2(self) -> CheckResult:
        """
        Type 2: Value comparison check (no waivers).
        
        Template auto-handles waiver=0 conversions.
        
        Returns:
            CheckResult with is_pass based on value comparison
        """
        # Parse input
        data = self._parse_input_files()
        error_items = data.get('items', [])
        
        # Get requirements
        requirements = self.item_data.get('requirements', {})
        pattern_items = requirements.get('pattern_items', [])
        expected_value = requirements.get('value', 'N/A')
        
        # Match errors against pattern_items (EXACT MATCH for error codes)
        found_items = {}
        missing_patterns = []
        
        for pattern in pattern_items:
            matched = False
            for error in error_items:
                error_code = error.get('error_code', '')
                # EXACT MATCH (case-insensitive) - pattern_items are error codes
                if pattern.lower() == error_code.lower():
                    found_items[error['name']] = {
                        'name': error['name'],
                        'line_number': error.get('line_number', 0),
                        'file_path': error.get('file_path', 'N/A')
                    }
                    matched = True
                    break
            
            if not matched:
                missing_patterns.append(pattern)
        
        actual_count = len(found_items)
        
        # Use template helper (auto-handles waiver=0)
        return self.build_complete_output(
            found_items=found_items,
            missing_items=missing_patterns,
            found_desc=f"{self.FOUND_DESC} ({actual_count}/{expected_value})",
            missing_desc=f"{self.MISSING_DESC} ({len(missing_patterns)} patterns not matched)",
            found_reason=self.FOUND_REASON,
            missing_reason=self.MISSING_REASON
        )
    
    # =========================================================================
    # Type 3: Value Check with Waiver Logic
    # =========================================================================
    
    def _execute_type3(self) -> CheckResult:
        """
        Type 3: Value comparison with waiver support.
        
        Uses WaiverHandlerMixin for waiver processing:
        - parse_waive_items(waive_items_raw): Parse waiver configuration
        - match_waiver_entry(item, waive_dict): Match item against waivers
        
        Uses OutputBuilderMixin for result construction:
        - build_complete_output(...): Assemble final CheckResult with auto-formatting
        
        Returns:
            CheckResult with FAIL for unwaived, INFO for waived items
        """
        # Parse input
        data = self._parse_input_files()
        error_items = data.get('items', [])
        
        # Get requirements and waivers
        requirements = self.item_data.get('requirements', {})
        pattern_items = requirements.get('pattern_items', [])
        
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # Track pattern satisfaction
        found_clean = {}      # Patterns with no errors
        found_waived = {}     # Patterns with waived errors
        missing_patterns = {} # Patterns with unwaived errors
        used_waiver_patterns = set()
        
        # Check each required pattern
        for pattern in pattern_items:
            pattern_has_error = False
            
            # Check if pattern has matching error
            for error in error_items:
                error_code = error.get('error_code', '')
                # EXACT MATCH for error codes
                if pattern.lower() == error_code.lower():
                    pattern_has_error = True
                    error_name = error['name']
                    error_data = {
                        'name': error_name,
                        'line_number': error.get('line_number', 0),
                        'file_path': error.get('file_path', 'N/A')
                    }
                    
                    # Check if waived
                    matched_waiver = None
                    for waiver_pattern in waive_dict.keys():
                        if self.match_waiver_entry(error_name, {waiver_pattern: waive_dict[waiver_pattern]}):
                            matched_waiver = waiver_pattern
                            used_waiver_patterns.add(waiver_pattern)
                            break
                    
                    if matched_waiver:
                        found_waived[error_name] = error_data
                    else:
                        missing_patterns[error_name] = error_data
                    break
            
            # If no error for this pattern, it's clean
            if not pattern_has_error:
                clean_name = f"[{pattern}] No errors detected"
                found_clean[clean_name] = {
                    'name': clean_name,
                    'line_number': 0,
                    'file_path': 'N/A'
                }
        
        # Find unused waivers
        unused_waivers = {
            w: {
                'line_number': 0,
                'file_path': 'N/A',
                'reason': waive_dict[w]
            }
            for w in waive_dict.keys()
            if w not in used_waiver_patterns
        }
        
        # Build output
        return self.build_complete_output(
            found_items=found_clean,
            missing_items=missing_patterns,
            waived_items=found_waived,
            unused_waivers=unused_waivers,
            waive_dict=waive_dict,
            waived_tag="[WAIVER]",
            found_desc=f"Required patterns satisfied: {len(found_clean)}/{len(pattern_items)}",
            missing_desc="Required patterns with unwaived errors",
            waived_desc=self.WAIVED_DESC,
            found_reason=lambda item: "Pattern satisfied (no errors)",
            missing_reason=lambda item: self.MISSING_REASON,
            waived_base_reason=self.WAIVED_BASE_REASON,
            unused_waiver_reason="Waiver defined but no error matched"
        )
    
    # =========================================================================
    # Type 4: Boolean Check with Waiver Logic
    # =========================================================================
    
    def _execute_type4(self) -> CheckResult:
        """
        Type 4: Boolean check with waiver support.
        
        Use OutputBuilderMixin.build_complete_output() with has_waiver_value=True.
        
        Returns:
            CheckResult with waiver logic applied
        """
        # Parse input
        data = self._parse_input_files()
        error_items = data.get('items', [])
        
        # Parse waiver configuration
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # Build found_items (clean files) if no errors
        found_items = {}
        if not error_items:
            input_files_list = self.item_data.get('input_files', [])
            for idx, file_path in enumerate(input_files_list, 1):
                file_name = Path(file_path).name
                found_items[file_name] = {
                    'name': file_name,
                    'line_number': 0,
                    'file_path': str(file_path)
                }
        
        # Apply waivers to errors
        waived_items = {}
        unwaived_items = {}
        used_waiver_patterns = set()
        
        for error in error_items:
            error_name = error['name']
            error_data = {
                'name': error_name,
                'line_number': error.get('line_number', 0),
                'file_path': error.get('file_path', 'N/A')
            }
            
            # Check if this error matches any waiver
            matched_waiver = None
            for waiver_pattern in waive_dict.keys():
                if self.match_waiver_entry(error_name, {waiver_pattern: waive_dict[waiver_pattern]}):
                    matched_waiver = waiver_pattern
                    used_waiver_patterns.add(waiver_pattern)
                    break
            
            if matched_waiver:
                waived_items[error_name] = error_data
            else:
                unwaived_items[error_name] = error_data
        
        # Find unused waivers
        unused_waivers = {
            waiver_name: {
                'line_number': 0,
                'file_path': 'N/A',
                'reason': waive_dict[waiver_name]
            }
            for waiver_name in waive_dict.keys()
            if waiver_name not in used_waiver_patterns
        }
        
        # Use template helper
        return self.build_complete_output(
            found_items=found_items,
            missing_items=unwaived_items,
            waived_items=waived_items,
            unused_waivers=unused_waivers,
            waive_dict=waive_dict,
            found_desc=self.FOUND_DESC,
            missing_desc=self.MISSING_DESC,
            waived_desc=self.WAIVED_DESC,
            found_reason=self.FOUND_REASON,
            missing_reason=self.MISSING_REASON,
            waived_base_reason=self.WAIVED_BASE_REASON
        )


# =========================================================================
# Entry Point
# =========================================================================

def main():
    """Main entry point."""
    checker = Check_10_0_0_20()
    checker.init_checker(Path(__file__))
    result = checker.execute_check()
    checker.write_output(result)
    return 0 if result.is_pass else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())