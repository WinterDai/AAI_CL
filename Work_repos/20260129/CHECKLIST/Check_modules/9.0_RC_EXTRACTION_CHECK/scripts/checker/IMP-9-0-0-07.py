################################################################################
# Script Name: IMP-9-0-0-07.py
#
# Purpose:
#   Confirm all Warning message in QRC log files can be waived.
#
# Logic:
#   - Parse input files: do_qrc*.log
#   - Extract all WARNING messages with message codes (EXTGRMP-XXX, EXTSNZ-XXX, LEFPARS-XXX)
#   - Parse warning summary table to get occurrence counts for each warning code
#   - Aggregate warnings across all log files and group by message code
#   - For each unique warning code, create one entry with total occurrence count
#   - Validate that all warnings can be waived (either auto-waived or matched by waive_items)
#   - Generate summary statistics (INFO01) and detailed warning list (ERROR01)
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
# Refactored: 2025-12-25 (Using checker_templates v1.1.0)
#
# Author: yyin
# Date: 2025-12-18
################################################################################

from pathlib import Path
import re
import sys
from typing import List, Dict, Tuple, Optional, Any
from collections import defaultdict


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
class Check_9_0_0_07(InputFileParserMixin, OutputBuilderMixin, WaiverHandlerMixin, BaseChecker):
    """
    IMP-9-0-0-07: Confirm all Warning message in QRC log files can be waived.
    
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
    FOUND_DESC_TYPE1_4 = "QRC extraction completed with no WARNING messages found"
    MISSING_DESC_TYPE1_4 = "WARNING messages found in QRC extraction logs"
    FOUND_REASON_TYPE1_4 = "No WARNING messages found in QRC extraction logs"
    MISSING_REASON_TYPE1_4 = "WARNING messages found in QRC extraction logs - require waiver"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_DESC_TYPE2_3 = "QRC extraction log validated - no WARNING messages detected"
    MISSING_DESC_TYPE2_3 = "QRC extraction validation failed - WARNING messages detected"
    FOUND_REASON_TYPE2_3 = "QRC extraction log validated successfully - no WARNING patterns matched"
    MISSING_REASON_TYPE2_3 = "QRC extraction validation failed - WARNING patterns detected in logs"
    
    # All Types (waiver description unified)
    WAIVED_DESC = "QRC extraction WARNING messages waived"
    
    # Waiver parameters (Type 3/4 ONLY)
    WAIVED_BASE_REASON = "QRC extraction WARNING waived per design team approval"
    
    def __init__(self):
        """Initialize the checker."""
        super().__init__(
            check_module="9.0_RC_EXTRACTION_CHECK",
            item_id="IMP-9-0-0-07",
            item_desc="Confirm all Warning message in QRC log files can be waived."
        )
        # Store parsed warnings data
        self._parsed_warnings: Dict[str, Dict[str, Any]] = {}
        self._warning_summary: Dict[str, int] = {}
    
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
        
        Parses QRC log files to extract WARNING messages with codes and occurrence counts.
        
        Returns:
            Dict with parsed data:
            - 'items': List[Dict] - Warning items with metadata (line_number, file_path)
            - 'metadata': Dict - Summary statistics
            - 'errors': List - Any parsing errors encountered
        """
        # 1. Validate input files - IMPORTANT: returns tuple (valid_files_list, missing_files_list)
        valid_files, missing_files = self.validate_input_files()
        # FIX [KNOWN_ISSUE_LOGIC-001]: Explicitly check for empty list
        if not valid_files or len(valid_files) == 0:
            raise ConfigurationError("No valid input files found")
        
        # 2. Parse using patterns from file analysis
        all_warnings = defaultdict(lambda: {'count': 0, 'message': '', 'files': [], 'line_numbers': []})
        errors = []
        
        # Pattern 1: Individual WARNING messages with message codes
        warning_pattern = re.compile(
            r'WARNING\s+\(([A-Z]+-\d+)\)\s*:\s*(.+?)(?=\n(?:WARNING|INFO|\n|$))',
            re.MULTILINE | re.DOTALL
        )
        
        # Pattern 2: Warning summary table entries
        summary_pattern = re.compile(
            r'^([A-Z]+-\d+)\s+(\d+)\s+(.+?)$',
            re.MULTILINE
        )
        
        for file_path in valid_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    
                    # Extract individual WARNING messages
                    for match in warning_pattern.finditer(content):
                        warning_code = match.group(1)
                        warning_msg = match.group(2).strip()
                        
                        # Find line number
                        line_num = content[:match.start()].count('\n') + 1
                        
                        # Store warning details
                        if not all_warnings[warning_code]['message']:
                            all_warnings[warning_code]['message'] = warning_msg
                        all_warnings[warning_code]['count'] += 1
                        all_warnings[warning_code]['files'].append(str(file_path))
                        all_warnings[warning_code]['line_numbers'].append(line_num)
                    
                    # Parse warning summary table if present
                    # Look for the summary section header
                    summary_header_match = re.search(
                        r'Message Code\(ID\)\s+Count\s+Message\s*\n=+\|=+\|=+',
                        content
                    )
                    
                    if summary_header_match:
                        # Extract everything after the header until TOTAL or end
                        summary_start = summary_header_match.end()
                        summary_end_match = re.search(r'\nTOTAL\s+WARNINGS', content[summary_start:])
                        if summary_end_match:
                            summary_text = content[summary_start:summary_start + summary_end_match.start()]
                        else:
                            summary_text = content[summary_start:]
                        
                        # Parse each warning entry from summary table
                        # Pattern: CODE  COUNT  MESSAGE (possibly multi-line until next CODE or separator)
                        summary_entry_pattern = re.compile(
                            r'^([A-Z]+-\d+)\s+(\d+)\s+(.+?)(?=\n-{20,}|\n[A-Z]+-\d+\s+\d+|\Z)',
                            re.MULTILINE | re.DOTALL
                        )
                        
                        for match in summary_entry_pattern.finditer(summary_text):
                            warning_code = match.group(1)
                            count = int(match.group(2))
                            # Get first line of message only
                            brief_desc = match.group(3).strip().split('\n')[0].strip()
                            
                            # Update count from summary if available
                            if warning_code in all_warnings:
                                # Use summary count as authoritative
                                all_warnings[warning_code]['summary_count'] = count
                                if not all_warnings[warning_code]['message']:
                                    all_warnings[warning_code]['message'] = brief_desc
                            else:
                                # Warning in summary but not found in log body - ADD IT
                                all_warnings[warning_code]['summary_count'] = count
                                all_warnings[warning_code]['message'] = brief_desc
                                all_warnings[warning_code]['count'] = count
                                all_warnings[warning_code]['files'].append(str(file_path))
                                all_warnings[warning_code]['line_numbers'].append(0)
                
            except Exception as e:
                errors.append(f"Error parsing {file_path}: {str(e)}")
        
        # 3. Convert to items list with proper metadata
        items = []
        for warning_code, warning_data in all_warnings.items():
            # Use summary count if available, otherwise use actual count
            total_count = warning_data.get('summary_count', warning_data['count'])
            
            # Get first occurrence for line number and file path
            line_num = warning_data['line_numbers'][0] if warning_data['line_numbers'] else 0
            file_path = warning_data['files'][0] if warning_data['files'] else 'N/A'
            
            # Clean up message: only take first line, remove trailing separators
            message = warning_data['message']
            if message:
                # Take only first line of message
                message = message.split('\n')[0].strip()
                # Remove trailing dashes or separators
                message = re.sub(r'\s*-{3,}\s*$', '', message)
            
            # Format: [WARNING_CODE](Occurrence: [total_number]): message_text
            item_name = f"[{warning_code}](Occurrence: {total_count}): {message}"
            
            items.append({
                'name': item_name,
                'warning_code': warning_code,
                'count': total_count,
                'message': message,
                'line_number': line_num,
                'file_path': file_path
            })
        
        # 4. Store frequently reused data on self
        self._parsed_warnings = {item['warning_code']: item for item in items}
        self._warning_summary = {item['warning_code']: item['count'] for item in items}
        
        return {
            'items': items,
            'metadata': {
                'total_warnings': len(items),
                'total_occurrences': sum(self._warning_summary.values())
            },
            'errors': errors
        }
    
    # =========================================================================
    # Type 1: Boolean Check
    # =========================================================================
    
    def _execute_type1(self) -> CheckResult:
        """
        Type 1: Boolean Check.
        
        Check if any WARNING messages exist in QRC log files.
        PASS if no WARNINGs found, FAIL if any WARNINGs exist.
        
        Returns:
            CheckResult with is_pass based on check logic
        """
        # Parse input
        data = self._parse_input_files()
        items = data.get('items', [])
        metadata = data.get('metadata', {})
        
        # Convert warning items to dict with metadata for source file/line display
        if items:
            # Found WARNING messages - FAIL case
            # FIXED: KNOWN_ISSUE_API-009 - Pass dict format {name: metadata}, not list
            missing_items = {}
            for item in items:
                missing_items[item['name']] = {
                    'line_number': item.get('line_number', 0),
                    'file_path': item.get('file_path', 'N/A')
                }
            
            # Use template helper - Type 1: Use TYPE1_4 reason (emphasize "found/not found")
            return self.build_complete_output(
                found_items={},
                missing_items=missing_items,
                found_desc=self.FOUND_DESC_TYPE1_4,
                missing_desc=self.MISSING_DESC_TYPE1_4,
                found_reason=self.FOUND_REASON_TYPE1_4,
                missing_reason=self.MISSING_REASON_TYPE1_4
            )
        else:
            # No WARNING messages - PASS case
            # Create summary info item
            total_warnings = metadata.get('total_warnings', 0)
            summary_name = f"QRC extraction summary: {total_warnings} WARNING messages found"
            found_items = {
                summary_name: {
                    'line_number': 0,
                    'file_path': 'Summary'
                }
            }
            
            return self.build_complete_output(
                found_items=found_items,
                missing_items={},
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
        This is a status_check mode - check if WARNING messages exist.
        
        Returns:
            CheckResult with is_pass based on value comparison
        """
        # Parse input
        data = self._parse_input_files()
        items = data.get('items', [])
        metadata = data.get('metadata', {})
        
        # Get requirements
        pattern_items = self.item_data.get('requirements', {}).get('pattern_items', [])
        
        # FIXED: KNOWN_ISSUE_API-009 - Convert warning items to dict with metadata
        missing_items = {}
        for item in items:
            missing_items[item['name']] = {
                'line_number': item.get('line_number', 0),
                'file_path': item.get('file_path', 'N/A')
            }
        
        if items:
            # Found WARNING messages - FAIL case
            return self.build_complete_output(
                found_items={},
                missing_items=missing_items,
                found_desc=self.FOUND_DESC_TYPE2_3,
                missing_desc=self.MISSING_DESC_TYPE2_3,
                found_reason=self.FOUND_REASON_TYPE2_3,
                missing_reason=self.MISSING_REASON_TYPE2_3
            )
        else:
            # No WARNING messages - PASS case
            total_warnings = metadata.get('total_warnings', 0)
            summary_name = f"QRC extraction summary: {total_warnings} WARNING messages found"
            found_items = {
                summary_name: {
                    'line_number': 0,
                    'file_path': 'Summary'
                }
            }
            
            return self.build_complete_output(
                found_items=found_items,
                missing_items={},
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
        
        # status_check mode: Check if warnings match expected patterns
        # found_items = warnings that match patterns (acceptable, no waiver needed)
        # waived_items = warnings that don't match patterns but have waivers
        # unwaived_items = warnings that don't match patterns and have no waivers
        
        found_items = {}
        waived_items = {}
        unwaived_items = {}
        
        for item in items:
            warning_code = item['warning_code']
            item_name = item['name']
            matched_pattern = False
            
            # Check if warning code matches any pattern
            for pattern in pattern_items:
                if pattern in warning_code or pattern in item['message']:
                    matched_pattern = True
                    break
            
            if matched_pattern:
                # Warning matches expected pattern - acceptable
                found_items[item_name] = {
                    'name': item_name,
                    'line_number': item.get('line_number', 0),
                    'file_path': item.get('file_path', 'N/A')
                }
            else:
                # Warning doesn't match pattern - check waiver
                # Try matching by warning code or full message
                if self.match_waiver_entry(warning_code, waive_dict) or self.match_waiver_entry(item_name, waive_dict):
                    waived_items[item_name] = {
                        'name': item_name,
                        'line_number': item.get('line_number', 0),
                        'file_path': item.get('file_path', 'N/A')
                    }
                else:
                    unwaived_items[item_name] = {
                        'name': item_name,
                        'line_number': item.get('line_number', 0),
                        'file_path': item.get('file_path', 'N/A')
                    }
        
        # Find unused waivers
        used_names = set(waived_items.keys())
        used_names.update(found_items.keys())
        unused_waivers = [name for name in waive_dict.keys() if name not in used_names]
        
        # FIX [KNOWN_ISSUE_API-009]: Pass dict directly, not list(dict.values())
        # Use template helper for automatic output formatting
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
        
        # Separate waived/unwaived warnings
        waived_items = {}
        unwaived_items = {}
        
        for item in items:
            warning_code = item['warning_code']
            item_name = item['name']
            
            # Check if warning matches any waiver
            if self.match_waiver_entry(warning_code, waive_dict) or self.match_waiver_entry(item_name, waive_dict):
                waived_items[item_name] = {
                    'name': item_name,
                    'line_number': item.get('line_number', 0),
                    'file_path': item.get('file_path', 'N/A')
                }
            else:
                unwaived_items[item_name] = {
                    'name': item_name,
                    'line_number': item.get('line_number', 0),
                    'file_path': item.get('file_path', 'N/A')
                }
        
        # Find unused waivers
        used_names = set(waived_items.keys())
        unused_waivers = [name for name in waive_dict.keys() if name not in used_names]
        
        # FIX [KNOWN_ISSUE_API-009]: Pass dict directly, not list(dict.values())
        # Use template helper (auto-handles waiver=0)
        return self.build_complete_output(
            found_items={},
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
    checker = Check_9_0_0_07()
    checker.init_checker(Path(__file__))
    result = checker.execute_check()
    checker.write_output(result)
    return 0 if result.is_pass else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())