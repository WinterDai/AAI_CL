################################################################################
# Script Name: IMP-5-0-0-07.py
#
# Purpose:
#   Confirm there are no SDC violations or errors during synthesis.
#   Supports 4 checking types based on requirements and waivers configuration.
#
# Refactoring to BaseChecker:
#   - Migrated from BooleanChecker to unified BaseChecker
#   - Added support for all 4 checking types (Type 1/2/3/4)
#   - Automatic type detection based on requirements.value and waivers.value
#   - Centralized input validation with create_missing_files_error()
#
# Usage:
#   python IMP-5-0-0-07.py [type]
#   type: Optional override (1/2/3/4), default is auto-detect
#
#
# Logic:
#   - Parse synthesis log for SDC read failures
#   - Extract all SDC-related errors and warnings
#   - Verify SDC files are loaded successfully
# Author: yyin
# Date:   2025-11-03
# Updated: 2025-11-26 - Migrated to BaseChecker (All 4 Types)
################################################################################

from pathlib import Path
import re
import sys
from typing import List, Tuple, Dict, Optional

# Add common module to path
_SCRIPT_DIR = Path(__file__).resolve().parent
_COMMON_DIR = _SCRIPT_DIR.parent.parent.parent / 'common'
if str(_COMMON_DIR) not in sys.path:
    sys.path.insert(0, str(_COMMON_DIR))

from base_checker import BaseChecker, ConfigurationError
from output_formatter import CheckResult, Severity, DetailItem, create_check_result


class SDCViolationChecker(BaseChecker):
    """
    IMP-5-0-0-07: Confirm that there are no SDC violations or errors?
    
    Parses synthesis log files to detect read_sdc command failures and violations.
    SDC violations can indicate constraint issues and should be investigated.
    
    Checking Types:
    - Type 1: requirements=N/A, waivers=N/A/0 → Always PASS (informational only)
    - Type 2: requirements>0, waivers=N/A/0 → FAIL if any violations found
    - Type 3: requirements>0, waivers>0 → FAIL if unwaived violations found
    - Type 4: requirements=N/A, waivers>0 → FAIL if unwaived violations found
    """
    
    # Priority order for error numbering (from actual log statistics order)
    ERROR_PRIORITY = [
        'all_clocks', 'all_inputs', 'all_outputs', 'create_clock',
        'current_design', 'foreach_in_collection', 'get_cells', 'get_clocks',
        'get_object_name', 'get_pins', 'get_ports', 'remove_from_collection',
        'set_case_analysis', 'set_clock_groups', 'set_clock_uncertainty',
        'set_dont_touch', 'set_false_path', 'set_input_delay',
        'set_input_transition', 'set_load', 'set_max_transition', 'set_output_delay'
    ]
    
    def __init__(self):
        """Initialize the SDC violation checker."""
        super().__init__(
            check_module="5.0_SYNTHESIS_CHECK",
            item_id="IMP-5-0-0-07",
            item_desc="Confirm that there are no other violations or errors (max cap, max transition etc)?"
        )
        # Cache for parsed violations: {error_type: [{error_info, line_num, sdc_path, command}]}
        self.violations_cache: Dict[str, List[Dict]] = {}
    
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
    
    def _parse_input_files(self, input_files: List[Path]) -> Dict[str, int]:
        """
        Parse synthesis log files to extract SDC violations.
        
        Args:
            input_files: List of synthesis log file paths
        
        Returns:
            Dict mapping violation command to count
        """
        if not input_files:
            return {}
        
        # Select appropriate log file (prefer generic)
        log_file = self._select_log_file(input_files)
        
        # Read log content
        lines = self.read_file(log_file)
        if not lines:
            return {}
        
        # Extract violations
        violations_dict, has_violations, has_sections = self._check_read_sdc_violations(lines, log_file)
        
        # Cache violations for detail creation
        self.violations_cache = violations_dict
        
        # Return violation command counts
        violation_counts = {}
        for error_type, error_list in violations_dict.items():
            for error in error_list:
                command = error.get('command', 'N/A')
                violation_counts[command] = violation_counts.get(command, 0) + 1
        
        return violation_counts
    
    # =========================================================================
    # Type 1: Informational Check (requirements=N/A, waivers=N/A/0)
    # =========================================================================
    
    def _execute_type1(self) -> CheckResult:
        """
        Type 1: Informational check only, always PASS.
        
        Returns:
            CheckResult with is_pass=True, INFO message about violation status
        """
        # Validate input files
        valid_files, missing_files = self.validate_input_files()
        
        # Handle missing input files
        if missing_files:
            return self.create_missing_files_error(missing_files)
        
        # Parse logs to extract violations
        violations = self._parse_input_files(valid_files)
        
        # Build details
        details = []
        if violations:
            # Add each violation as INFO
            for error_type, error_list in self.violations_cache.items():
                for error in error_list:
                    command = error.get('command', 'N/A')
                    sdc_path = error.get('sdc_path', 'Unknown')
                    line_num = int(error.get('line_num', '0'))
                    error_info = error.get('error_info', 'Error')
                    
                    details.append(DetailItem(
                        severity=Severity.INFO,
                        name=command,
                        line_number=line_num,
                        file_path=sdc_path,
                        reason=f"{error_type}: {error_info} (informational only)"
                    ))
        else:
            # No violations
            log_path_str = str(valid_files[0].resolve()) if valid_files else "synthesis logs"
            details.append(DetailItem(
                severity=Severity.INFO,
                name="",
                line_number=0,
                file_path="",
                reason=f"No SDC violations found in {log_path_str}"
            ))
        
        # Always PASS for Type 1
        info_groups = {
            "INFO01": {
                "description": "Check result",
                "items": []
            }
        }
        
        return create_check_result(
            value="N/A",
            is_pass=True,
            has_pattern_items=False,
            has_waiver_value=False,
            details=details,
            info_groups=info_groups,
            item_desc=self.item_desc
        )
    
    # =========================================================================
    # Type 2: Value Check (requirements>0, waivers=N/A/0)
    # =========================================================================
    
    def _execute_type2(self) -> CheckResult:
        """
        Type 2: FAIL if violations count > 0, PASS if count == 0.
        
        Returns:
            CheckResult with is_pass based on whether violations exist
        """
        # Validate input files
        valid_files, missing_files = self.validate_input_files()
        
        # Handle missing input files
        if missing_files:
            return self.create_missing_files_error(missing_files)
        
        # Parse logs to extract violations
        violations = self._parse_input_files(valid_files)
        
        # Build details
        details = []
        is_pass = len(violations) == 0
        
        if violations:
            # FAIL: Add each violation as FAIL
            for error_type, error_list in self.violations_cache.items():
                for error in error_list:
                    command = error.get('command', 'N/A')
                    sdc_path = error.get('sdc_path', 'Unknown')
                    line_num = int(error.get('line_num', '0'))
                    error_info = error.get('error_info', 'Error')
                    
                    details.append(DetailItem(
                        severity=Severity.FAIL,
                        name=command,
                        line_number=line_num,
                        file_path=sdc_path,
                        reason=f"{error_type}: {error_info}"
                    ))
            
            # Build error groups with priority numbering
            error_groups = self._create_error_groups(details)
            info_groups = None
        else:
            # PASS: No violations
            log_path_str = str(valid_files[0].resolve()) if valid_files else "synthesis logs"
            details.append(DetailItem(
                severity=Severity.INFO,
                name="",
                line_number=0,
                file_path="",
                reason=f"No SDC violations found in {log_path_str}"
            ))
            info_groups = {
                "INFO01": {
                    "description": "Check result",
                    "items": []
                }
            }
            error_groups = None
        
        return create_check_result(
            value=str(len(violations)),
            is_pass=is_pass,
            has_pattern_items=True,
            has_waiver_value=False,
            details=details,
            error_groups=error_groups,
            info_groups=info_groups,
            item_desc=self.item_desc
        )
    
    # =========================================================================
    # Type 3: Value Check with Waivers (requirements>0, waivers>0)
    # =========================================================================
    
    def _execute_type3(self) -> CheckResult:
        """
        Type 3: FAIL if unwaived violations exist, WAIVED if all are waived.
        
        Returns:
            CheckResult with FAIL/WAIVED/PASS based on waiver coverage
        """
        # Validate input files
        valid_files, missing_files = self.validate_input_files()
        
        # Handle missing input files
        if missing_files:
            return self.create_missing_files_error(missing_files)
        
        # Parse logs to extract violations
        violations = self._parse_input_files(valid_files)
        
        # Get waiver patterns and reasons
        waiver_patterns = self.waivers.pattern_items or []
        waiver_reason_map = self._build_waiver_reason_map()
        
        # Separate waived and unwaived violations
        waived_violations = []
        unwaived_violations = []
        
        for command in violations.keys():
            if self._matches_any_pattern(command, waiver_patterns):
                waived_violations.append(command)
            else:
                unwaived_violations.append(command)
        
        # Check for unused waivers
        used_patterns = set()
        for command in waived_violations:
            for pattern in waiver_patterns:
                if self._matches_pattern(command, pattern):
                    used_patterns.add(pattern)
        
        unused_waivers = [p for p in waiver_patterns if p not in used_patterns]
        
        # Build details
        details = []
        
        # Add unwaived violations as FAIL
        for error_type, error_list in self.violations_cache.items():
            for error in error_list:
                command = error.get('command', 'N/A')
                if command in unwaived_violations:
                    sdc_path = error.get('sdc_path', 'Unknown')
                    line_num = int(error.get('line_num', '0'))
                    error_info = error.get('error_info', 'Error')
                    
                    details.append(DetailItem(
                        severity=Severity.FAIL,
                        name=command,
                        line_number=line_num,
                        file_path=sdc_path,
                        reason=f"{error_type}: {error_info} (not waived)"
                    ))
        
        # Add waived violations as INFO with [WAIVER] tag
        for error_type, error_list in self.violations_cache.items():
            for error in error_list:
                command = error.get('command', 'N/A')
                if command in waived_violations:
                    sdc_path = error.get('sdc_path', 'Unknown')
                    line_num = int(error.get('line_num', '0'))
                    error_info = error.get('error_info', 'Error')
                    reason = waiver_reason_map.get(command, "Waived")
                    
                    details.append(DetailItem(
                        severity=Severity.INFO,
                        name=f"[WAIVER] {command}",
                        line_number=line_num,
                        file_path=sdc_path,
                        reason=f"{error_type}: {reason}"
                    ))
        
        # Add unused waivers as WARN
        for pattern in unused_waivers:
            reason = waiver_reason_map.get(pattern, "Unused waiver pattern")
            details.append(DetailItem(
                severity=Severity.WARN,
                name=pattern,
                line_number=0,
                file_path="",
                reason=reason
            ))
        
        # Determine pass status
        is_pass = len(unwaived_violations) == 0
        
        # Build error/warn/info groups
        error_groups = {}
        warn_groups = {}
        info_groups = {}
        
        if unwaived_violations:
            # Create error groups with priority numbering
            unwaived_details = [d for d in details if d.severity == Severity.FAIL]
            error_groups = self._create_error_groups(unwaived_details)
        
        if waived_violations:
            info_groups["INFO01"] = {
                "description": "SDC violations waived",
                "items": [d.name for d in details if d.severity == Severity.INFO and d.name]
            }
        
        if unused_waivers:
            warn_groups["WARN01"] = {
                "description": "Unused waiver patterns",
                "items": [d.name for d in details if d.severity == Severity.WARN and d.name]
            }
        
        return create_check_result(
            value=str(len(violations)),
            is_pass=is_pass,
            has_pattern_items=True,
            has_waiver_value=True,
            details=details,
            error_groups=error_groups or None,
            warn_groups=warn_groups or None,
            info_groups=info_groups or None,
            item_desc=self.item_desc
        )
    
    # =========================================================================
    # Type 4: Boolean Check with Waivers (requirements=N/A, waivers>0)
    # =========================================================================
    
    def _execute_type4(self) -> CheckResult:
        """
        Type 4: Boolean check - FAIL if unwaived violations exist.
        
        Returns:
            CheckResult with FAIL/WAIVED/PASS based on waiver coverage
        """
        # Validate input files
        valid_files, missing_files = self.validate_input_files()
        
        # Handle missing input files
        if missing_files:
            return self.create_missing_files_error(missing_files)
        
        # Parse logs to extract violations
        violations = self._parse_input_files(valid_files)
        
        # Get waiver patterns and reasons
        waiver_patterns = self.waivers.pattern_items or []
        waiver_reason_map = self._build_waiver_reason_map()
        
        # Separate waived and unwaived violations
        waived_violations = []
        unwaived_violations = []
        
        for command in violations.keys():
            if self._matches_any_pattern(command, waiver_patterns):
                waived_violations.append(command)
            else:
                unwaived_violations.append(command)
        
        # Check for unused waivers
        used_patterns = set()
        for command in waived_violations:
            for pattern in waiver_patterns:
                if self._matches_pattern(command, pattern):
                    used_patterns.add(pattern)
        
        unused_waivers = [p for p in waiver_patterns if p not in used_patterns]
        
        # Build details
        details = []
        
        # Add unwaived violations as FAIL
        for error_type, error_list in self.violations_cache.items():
            for error in error_list:
                command = error.get('command', 'N/A')
                if command in unwaived_violations:
                    sdc_path = error.get('sdc_path', 'Unknown')
                    line_num = int(error.get('line_num', '0'))
                    error_info = error.get('error_info', 'Error')
                    
                    details.append(DetailItem(
                        severity=Severity.FAIL,
                        name=command,
                        line_number=line_num,
                        file_path=sdc_path,
                        reason=f"{error_type}: {error_info} (not waived)"
                    ))
        
        # Add waived violations as INFO with [WAIVER] tag
        for error_type, error_list in self.violations_cache.items():
            for error in error_list:
                command = error.get('command', 'N/A')
                if command in waived_violations:
                    sdc_path = error.get('sdc_path', 'Unknown')
                    line_num = int(error.get('line_num', '0'))
                    error_info = error.get('error_info', 'Error')
                    reason = waiver_reason_map.get(command, "Waived")
                    
                    details.append(DetailItem(
                        severity=Severity.INFO,
                        name=f"[WAIVER] {command}",
                        line_number=line_num,
                        file_path=sdc_path,
                        reason=f"{error_type}: {reason}"
                    ))
        
        # Add unused waivers as WARN
        for pattern in unused_waivers:
            reason = waiver_reason_map.get(pattern, "Unused waiver pattern")
            details.append(DetailItem(
                severity=Severity.WARN,
                name=pattern,
                line_number=0,
                file_path="",
                reason=reason
            ))
        
        # If no violations at all, add INFO message
        if not violations:
            log_path_str = str(valid_files[0].resolve()) if valid_files else "synthesis logs"
            details.append(DetailItem(
                severity=Severity.INFO,
                name="",
                line_number=0,
                file_path="",
                reason=f"No SDC violations found in {log_path_str}"
            ))
        
        # Determine pass status
        is_pass = len(unwaived_violations) == 0
        
        # Build error/warn/info groups
        error_groups = {}
        warn_groups = {}
        info_groups = {}
        
        if unwaived_violations:
            # Create error groups with priority numbering
            unwaived_details = [d for d in details if d.severity == Severity.FAIL]
            error_groups = self._create_error_groups(unwaived_details)
        
        if waived_violations:
            info_groups["INFO01"] = {
                "description": "SDC violations waived",
                "items": [d.name for d in details if d.severity == Severity.INFO and d.name and d.name.startswith("[WAIVER]")]
            }
        elif not violations:
            # No violations case
            info_groups["INFO01"] = {
                "description": "Check result",
                "items": []
            }
        
        if unused_waivers:
            warn_groups["WARN01"] = {
                "description": "Unused waiver patterns",
                "items": [d.name for d in details if d.severity == Severity.WARN and d.name]
            }
        
        return create_check_result(
            value="N/A",
            is_pass=is_pass,
            has_pattern_items=False,
            has_waiver_value=True,
            details=details,
            error_groups=error_groups or None,
            warn_groups=warn_groups or None,
            info_groups=info_groups or None,
            item_desc=self.item_desc
        )
    
    # =========================================================================
    # Helper Methods: Log Parsing
    # =========================================================================
    
    def _select_log_file(self, log_files: List[Path]) -> Path:
        """Select the appropriate log file, preferring 'generic' logs."""
        generic_logs = [f for f in log_files if 'generic' in f.name.lower()]
        return generic_logs[0] if generic_logs else log_files[0]
    
    def _extract_read_sdc_sections(self, lines: List[str]) -> List[Tuple[int, int]]:
        """Extract all read_sdc sections (from '# Reading SDC' to 'read_sdc completed')."""
        sections = []
        start_idx = None
        
        for idx, line in enumerate(lines):
            if '# Reading SDC' in line:
                start_idx = idx
            elif start_idx is not None and 'read_sdc completed in' in line:
                sections.append((start_idx, idx))
                start_idx = None
        
        return sections
    
    def _parse_failed_commands(self, section_lines: List[str]) -> Dict[str, int]:
        """Parse statistics section to find failed commands and their counts."""
        failed_commands = {}
        
        # Pattern: "set_false_path"  - successful 0 , failed 2 (runtime 0.00)
        stat_pattern = re.compile(r'^\s*"([^"]+)"\s*-\s*successful\s+\d+\s*,\s*failed\s+(\d+)')
        
        for line in section_lines:
            match = stat_pattern.match(line)
            if match:
                cmd_name = match.group(1).strip()
                failed_count = int(match.group(2))
                if failed_count > 0:
                    failed_commands[cmd_name] = failed_count
        
        return failed_commands
    
    def _extract_error_details(self, section_lines: List[str], error_type: str, log_file: Path) -> List[Dict[str, str]]:
        """Extract detailed error information for a specific error type."""
        error_details = []
        i = 0
        
        while i < len(section_lines):
            line = section_lines[i]
            
            # Look for Error lines with the error_type tag
            if 'Error' in line and f'[{error_type}]' in line:
                error_match = re.search(r'Error\s*:\s*(.+?)\s*\[' + re.escape(error_type) + r'\]', line)
                if error_match:
                    error_info = error_match.group(1).strip()
                    # Remove error codes like [TUI-61]
                    error_info = re.sub(r'\s*\[[\w-]+\]\s*$', '', error_info).strip()
                    
                    current_error = {'error_info': error_info}
                    
                    # Look ahead for SDC file info
                    j = i + 1
                    while j < len(section_lines) and j < i + 20:
                        next_line = section_lines[j]
                        
                        # Pattern: on line '181' of the SDC file 'sdc_path'
                        warning_match = re.search(r"on line '(\d+)' of the SDC file '([^']+)'", next_line)
                        if warning_match:
                            current_error['line_num'] = warning_match.group(1)
                            current_error['sdc_path'] = warning_match.group(2)
                            
                            # Extract the actual command
                            k = j + 1
                            command_lines = []
                            while k < len(section_lines) and k < j + 10:
                                cmd_line = section_lines[k].strip()
                                if error_type in cmd_line:
                                    command_lines.append(cmd_line)
                                if cmd_line.startswith(('Error', 'Warning')) and k > j + 1:
                                    break
                                k += 1
                            
                            if command_lines:
                                current_error['command'] = ' '.join(command_lines)
                            
                            break
                        j += 1
                    
                    if 'error_info' in current_error:
                        error_details.append(current_error)
            i += 1
        
        return error_details
    
    def _check_read_sdc_violations(self, lines: List[str], log_file: Path) -> Tuple[Dict[str, List[Dict]], bool, bool]:
        """
        Check for read_sdc violations in log.
        
        Returns:
            Tuple of (violations_dict, has_violations, has_sections)
        """
        sections = self._extract_read_sdc_sections(lines)
        
        if not sections:
            return {}, False, False
        
        violations_dict: Dict[str, List[Dict]] = {}
        has_violations = False
        
        for start_idx, end_idx in sections:
            section_lines = lines[start_idx:end_idx + 1]
            
            # Check for "Total failed commands"
            for line in section_lines:
                if 'Total failed commands during read_sdc are' in line:
                    match = re.search(r'Total failed commands during read_sdc are (\d+)', line)
                    if match and int(match.group(1)) > 0:
                        has_violations = True
                    break
            
            # Check if there's a pass indicator
            compressed_line = any('Compressed' in line and 'timing exceptions down to' in line 
                                for line in section_lines)
            
            # Extract details if violations exist and no pass indicator
            if has_violations and not compressed_line:
                failed_commands = self._parse_failed_commands(section_lines)
                for error_type in failed_commands.keys():
                    error_details = self._extract_error_details(section_lines, error_type, log_file)
                    violations_dict.setdefault(error_type, []).extend(error_details)
        
        return violations_dict, has_violations, True
    
    def _create_error_groups(self, details: List[DetailItem]) -> Dict[str, Dict]:
        """
        Group SDC violations by error type with priority-based numbering.
        
        Groups errors by their command type (e.g., set_false_path, get_clocks)
        and assigns ERROR numbers based on predefined priority order.
        
        Returns:
            Dictionary mapping ERROR codes to error group data
        """
        if not details:
            return {}
        
        # Group by error type (extracted from reason field)
        error_type_groups: Dict[str, List[DetailItem]] = {}
        for detail in details:
            # Extract error_type from reason (format: "error_type: description")
            error_type = detail.reason.split(':', 1)[0].strip() if ':' in detail.reason else 'unknown'
            error_type_groups.setdefault(error_type, []).append(detail)
        
        # Assign error numbers based on priority
        error_type_to_num = {}
        for error_type in error_type_groups.keys():
            if error_type in self.ERROR_PRIORITY:
                error_type_to_num[error_type] = self.ERROR_PRIORITY.index(error_type) + 1
            else:
                # Unknown error types get numbers after 22
                error_type_to_num[error_type] = 23 + len([e for e in error_type_groups.keys() 
                                                           if e not in self.ERROR_PRIORITY 
                                                           and list(error_type_groups.keys()).index(e) < list(error_type_groups.keys()).index(error_type)])
        
        # Build error_groups dictionary in the required format
        error_groups = {}
        for error_type, items in error_type_groups.items():
            error_num = error_type_to_num[error_type]
            error_code = f"ERROR{error_num:02d}"
            error_groups[error_code] = {
                "description": error_type,
                "items": [item.name for item in items]
            }
        
        return error_groups


# =============================================================================
# Entry Point
# =============================================================================

if __name__ == '__main__':
    checker = SDCViolationChecker()
    checker.run()
