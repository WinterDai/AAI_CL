################################################################################
# Script Name: IMP-10-0-0-21.py
#
# Purpose:
#   Confirm all Warning message in the STA log files can be waived.
#
# Logic:
#   - Parse input files: tempus_1.log, tempus_2.log
#   - Extract warning messages from inline **WARN: entries and summary tables
#   - Aggregate warning counts by message ID across all log files
#   - Track total warning/error counts and execution statistics
#   - Verify all warnings are either acceptable or explicitly waived
#   - Report unwaived warnings as failures requiring review
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
# Refactored: 2025-12-18 (Using checker_templates v1.1.0)
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
class Check_10_0_0_21(InputFileParserMixin, OutputBuilderMixin, WaiverHandlerMixin, BaseChecker):
    """
    IMP-10-0-0-21: Confirm all Warning message in the STA log files can be waived.
    
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
    FOUND_DESC = "STA log files with no warnings"
    MISSING_DESC = "STA warnings requiring review"
    WAIVED_DESC = "Waived STA warnings"
    FOUND_REASON = "All STA log files are clean with no warnings"
    MISSING_REASON = "STA warnings detected that require waiver review"
    WAIVED_BASE_REASON = "STA warning waived per design review"
    
    def __init__(self):
        """Initialize the checker."""
        super().__init__(
            check_module="10.0_STA_DCD_CHECK",
            item_id="IMP-10-0-0-21",
            item_desc="Confirm all Warning message in the STA log files can be waived."
        )
        # Store parsed data
        self._parsed_warnings: Dict[str, Dict[str, Any]] = {}
        self._total_warnings: int = 0
        self._total_errors: int = 0
        self._execution_stats: Dict[str, str] = {}
    
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
        
        Parses Tempus STA log files using state machine approach to extract:
        - Inline warning messages with file location
        - Summary table warning entries
        - Overall message summary totals
        - Execution statistics
        
        Returns:
            Dict with parsed data:
            - 'items': List[Dict] - Warning items with metadata (line_number, file_path)
            - 'metadata': Dict - File metadata (total_warnings, total_errors, execution_stats)
            - 'errors': List - Any parsing errors encountered
        """
        # 1. Validate input files (raises ConfigurationError if missing)
        valid_files, missing_files = self.validate_input_files()
        if missing_files:
            raise ConfigurationError(
                self.create_missing_files_error(missing_files)
            )
        
        # 2. Initialize aggregation structures
        warnings_by_id: Dict[str, Dict[str, Any]] = {}  # Key: warning_id, Value: {count, summary, files}
        total_warnings = 0
        total_errors = 0
        execution_stats = {}
        errors = []
        
        # 3. Define parsing patterns
        pattern_inline_warning = re.compile(
            r'^\*\*WARN:\s*\(([A-Z0-9-]+)\):\s*(.+?)(?:\s*\(File\s+(.+?),\s*Line\s+(\d+)\))?$'
        )
        pattern_summary_warning = re.compile(
            r'^(WARNING|ERROR)\s+(\S+)\s+(\d+)\s+(.+?)\s*$'
        )
        pattern_message_summary = re.compile(
            r'\*\*\* Message Summary:\s*(\d+)\s+warning\(s\),\s*(\d+)\s+error\(s\)'
        )
        pattern_summary_header = re.compile(
            r'^\*\*\* Summary of all messages that are not suppressed in this session:'
        )
        pattern_execution_stats = re.compile(
            r'--- Ending "(.+?)"\s+\(totcpu=([^,]+),\s*real=([^,]+),\s*mem=([^)]+)\)'
        )
        
        # 4. Parse each log file sequentially
        for file_path in valid_files:
            in_summary_section = False
            
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line_num, line in enumerate(f, 1):
                        line = line.rstrip()
                        
                        # Check for summary section header
                        if pattern_summary_header.search(line):
                            in_summary_section = True
                            continue
                        
                        # Parse inline warnings (before summary section)
                        if not in_summary_section:
                            match = pattern_inline_warning.search(line)
                            if match:
                                warning_id = match.group(1)
                                message_text = match.group(2)
                                file_ref = match.group(3) if match.group(3) else 'N/A'
                                line_ref = match.group(4) if match.group(4) else '0'
                                
                                if warning_id not in warnings_by_id:
                                    warnings_by_id[warning_id] = {
                                        'warning_id': warning_id,
                                        'count': 0,
                                        'summary': message_text[:100],  # Truncate long messages
                                        'files': set(),
                                        'line_number': line_num,
                                        'file_path': str(file_path)
                                    }
                                warnings_by_id[warning_id]['count'] += 1
                                warnings_by_id[warning_id]['files'].add(str(file_path))
                        
                        # Parse summary table entries
                        if in_summary_section:
                            match = pattern_summary_warning.search(line)
                            if match:
                                severity = match.group(1)
                                warning_id = match.group(2)
                                count = int(match.group(3))
                                summary_text = match.group(4)
                                
                                if warning_id not in warnings_by_id:
                                    warnings_by_id[warning_id] = {
                                        'warning_id': warning_id,
                                        'count': 0,
                                        'summary': summary_text,
                                        'files': set(),
                                        'line_number': line_num,
                                        'file_path': str(file_path)
                                    }
                                # Aggregate counts from summary table
                                warnings_by_id[warning_id]['count'] += count
                                warnings_by_id[warning_id]['files'].add(str(file_path))
                        
                        # Parse overall message summary
                        match = pattern_message_summary.search(line)
                        if match:
                            total_warnings += int(match.group(1))
                            total_errors += int(match.group(2))
                            in_summary_section = False  # Exit summary section
                        
                        # Parse execution statistics
                        match = pattern_execution_stats.search(line)
                        if match:
                            execution_stats = {
                                'tool_name': match.group(1),
                                'cpu_time': match.group(2),
                                'real_time': match.group(3),
                                'memory_usage': match.group(4)
                            }
            
            except Exception as e:
                errors.append(f"Error parsing {file_path}: {str(e)}")
        
        # 5. Convert warnings to list format with metadata
        items = []
        for warning_id, data in warnings_by_id.items():
            # Convert set to list for JSON serialization
            data['files'] = list(data['files'])
            
            # Create item name with count and summary
            item_name = f"{warning_id} (Count: {data['count']}): {data['summary']}"
            
            items.append({
                'name': item_name,
                'warning_id': warning_id,
                'count': data['count'],
                'summary': data['summary'],
                'line_number': data['line_number'],
                'file_path': data['file_path']
            })
        
        # 6. Store frequently reused data on self
        self._parsed_warnings = warnings_by_id
        self._total_warnings = total_warnings
        self._total_errors = total_errors
        self._execution_stats = execution_stats
        
        return {
            'items': items,
            'metadata': {
                'total_warnings': total_warnings,
                'total_errors': total_errors,
                'execution_stats': execution_stats,
                'unique_warning_ids': len(warnings_by_id)
            },
            'errors': errors
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
        items = data.get('items', [])
        metadata = data.get('metadata', {})
        
        # Type 1: Check if warnings exist
        # Clean = no warnings, Violations = warnings found
        if len(items) == 0:
            # No warnings - clean, build found_items for each log file
            found_items = {}
            input_files_list = self.item_data.get('input_files', [])
            for file_path in input_files_list:
                file_name = Path(file_path).name
                found_items[file_name] = {
                    'name': f"{file_name} - Total: 0 warnings, 0 errors",
                    'line_number': 0,
                    'file_path': str(file_path)
                }
            missing_items = []
        else:
            # Warnings found - violations
            found_items = {}
            missing_items = []
            
            for item in items:
                item_name = item['name']
                missing_items.append(item_name)
        
        # Use template helper for automatic output formatting
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
        items = data.get('items', [])
        
        # Get requirements
        requirements = self.item_data.get('requirements', {})
        pattern_items = requirements.get('pattern_items', [])
        expected_value = requirements.get('value', 'N/A')
        
        # Match warnings against pattern_items (EXACT MATCH by warning ID)
        # Type 2: Found warnings in pattern_items should be shown as missing_items (violations)
        found_items = {}
        missing_items = []
        
        for pattern in pattern_items:
            for item in items:
                warning_id = item.get('warning_id', '')
                # EXACT MATCH (case-insensitive) - pattern_items are warning IDs
                if pattern.lower() == warning_id.lower():
                    # Found in pattern = this warning exists = violation
                    missing_items.append(item['name'])
                    break
        
        # Use template helper (auto-handles waiver=0)
        return self.build_complete_output(
            found_items=found_items,
            missing_items=missing_items,
            found_desc=self.FOUND_DESC,
            missing_desc=self.MISSING_DESC,
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
        parsed_data = self._parse_input_files()
        items = parsed_data.get('items', [])
        
        # Parse waiver configuration using template helper
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # Get requirements
        requirements = self.item_data.get('requirements', {})
        pattern_items = requirements.get('pattern_items', [])
        
        # Track items: found=clean, missing=unwaived warnings, waived=waived warnings
        found_items = {}      # Clean logs (no warnings in pattern_items)
        missing_items = {}    # Unwaived warnings from pattern_items
        waived_items = {}     # Waived warnings
        used_waiver_patterns = set()
        
        # Check each required pattern
        for pattern in pattern_items:
            found_warning = False
            
            # Check if pattern has matching warning
            for item in items:
                warning_id = item.get('warning_id', '')
                # EXACT MATCH by warning ID
                if pattern.lower() == warning_id.lower():
                    found_warning = True
                    item_name = item['name']
                    item_data = {
                        'name': item_name,
                        'line_number': item.get('line_number', 0),
                        'file_path': item.get('file_path', 'N/A')
                    }
                    
                    # Check if waived
                    matched_waiver = None
                    for waiver_pattern in waive_dict.keys():
                        if self.match_waiver_entry(warning_id, {waiver_pattern: waive_dict[waiver_pattern]}):
                            matched_waiver = waiver_pattern
                            used_waiver_patterns.add(waiver_pattern)
                            break
                    
                    if matched_waiver:
                        waived_items[item_name] = item_data
                    else:
                        missing_items[item_name] = item_data
                    break
            
            # If no warning found for this pattern, it's clean
            if not found_warning:
                found_items[f"{pattern}"] = {
                    'name': f"{pattern} - No warnings detected",
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
            found_items=found_items,
            missing_items=missing_items,
            waived_items=waived_items,
            unused_waivers=unused_waivers,
            waive_dict=waive_dict,
            waived_tag="[WAIVER]",
            found_desc=self.FOUND_DESC,
            missing_desc=self.MISSING_DESC,
            waived_desc=self.WAIVED_DESC,
            found_reason=self.FOUND_REASON,
            missing_reason=self.MISSING_REASON,
            waived_base_reason=self.WAIVED_BASE_REASON,
            unused_waiver_reason="Waiver defined but no warning matched"
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
        all_warnings = data.get('items', [])
        
        # Parse waiver configuration
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # Build found_items (clean logs - no warnings)
        found_items = {}
        if len(all_warnings) == 0:
            # No warnings - build found_items for each log file
            input_files_list = self.item_data.get('input_files', [])
            for file_path in input_files_list:
                file_name = Path(file_path).name
                found_items[file_name] = {
                    'name': f"{file_name} - Total: 0 warnings, 0 errors",
                    'line_number': 0,
                    'file_path': str(file_path)
                }
        
        # Apply waivers to warnings
        waived_items = {}
        unwaived_items = {}
        used_waiver_patterns = set()
        
        for warning in all_warnings:
            warning_name = warning.get('name', str(warning))
            warning_data = {
                'name': warning_name,
                'line_number': warning.get('line_number', 0),
                'file_path': warning.get('file_path', 'N/A')
            }
            
            # Check if this warning matches any waiver
            matched_waiver = None
            for waiver_pattern in waive_dict.keys():
                if self.match_waiver_entry(warning_name, {waiver_pattern: waive_dict[waiver_pattern]}):
                    matched_waiver = waiver_pattern
                    used_waiver_patterns.add(waiver_pattern)
                    break
            
            if matched_waiver:
                waived_items[warning_name] = warning_data
            else:
                unwaived_items[warning_name] = warning_data
        
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
        
        # Use template helper (auto-handles waiver logic)
        return self.build_complete_output(
            found_items=found_items,
            missing_items=unwaived_items,
            waived_items=waived_items,
            unused_waivers=unused_waivers,
            waive_dict=waive_dict,
            waived_tag="[WAIVER]",
            
            found_desc=self.FOUND_DESC,
            missing_desc=self.MISSING_DESC,
            waived_desc=self.WAIVED_DESC,
            
            found_reason=self.FOUND_REASON,
            missing_reason=self.MISSING_REASON,
            waived_base_reason=self.WAIVED_BASE_REASON,
            unused_waiver_reason="Waiver defined but no warning matched"
        )


# =========================================================================
# Entry Point
# =========================================================================

def main():
    """Main entry point."""
    checker = Check_10_0_0_21()
    checker.init_checker(Path(__file__))
    result = checker.execute_check()
    checker.write_output(result)
    return 0 if result.is_pass else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())