################################################################################
# Script Name: IMP-10-0-0-08.py
#
# Purpose:
#   Confirm set the correct clock transition and data transition.
#   Parse constr.rpt (write_sdc output) to verify clock and data path transition settings.
#
# Logic:
#   - Extract set_max_transition commands for each clock
#   - Check: Each clock must have both -clock_path and -data_path settings
#   - Type 1: Boolean check (all clocks must be complete)
#   - Type 2/3: Pattern matching with optional waiver logic
#
# Auto Type Detection:
#   Type 1: requirements.value=N/A, waivers.value=N/A/0 → Boolean check
#   Type 2: requirements.value>0, pattern_items exists, waivers.value=N/A/0 → Pattern matching
#   Type 3: requirements.value>0, pattern_items exists, waivers.value>0 → Pattern with waiver logic
#   Type 4: requirements.value=N/A, waivers.value>0 → Boolean with waiver logic
#
# Author: yyin
# Date: 2025-12-04
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
from output_formatter import DetailItem, Severity, ResultType


class ClockTransitionChecker(BaseChecker):
    """
    Unified checker that auto-detects and handles all 4 checker types.
    
    Check Target: Confirm set the correct clock transition and data transition
    
    Type Detection Logic:
    - Type 1: requirements.value=N/A AND waivers.value=N/A/0
    - Type 2: requirements.value>0 AND pattern_items AND waivers.value=N/A/0
    - Type 3: requirements.value>0 AND pattern_items AND waivers.value>0
    - Type 4: requirements.value=N/A AND waivers.value>0
    """
    
    def __init__(self):
        super().__init__(
            check_module="10.0_STA_DCD_CHECK",
            item_id="IMP-10-0-0-08",
            item_desc="Confirm set the correct clock transition and data transition?"
        )
        self._clocks_transitions: Dict[str, Dict[str, Any]] = {}
        self._pattern_items: List[str] = []
        self._log_lines_override: Optional[List[str]] = None
        self._constr_rpt_path: str = ""

    # =========================================================================
    # Parsing Methods
    # =========================================================================

    def _parse_constr_rpt(self) -> Dict[str, Dict[str, Any]]:
        """Parse constr.rpt to extract clock transition settings."""
        if not self.item_data or 'input_files' not in self.item_data:
            raise ConfigurationError("No input_files specified in configuration")
        
        valid_files, missing_files = self.validate_input_files()
        
        if missing_files:
            missing_list = '\n'.join(f"  - {f}" for f in missing_files)
            raise ConfigurationError(f"Input file(s) not found:\n{missing_list}")
        
        if valid_files:
            self._constr_rpt_path = str(valid_files[0])
        
        clocks_transitions = {}
        
        # Patterns
        pattern_clock = re.compile(r'set_max_transition\s+-clock_path\s+([\d.]+).*get_clocks\s+\{([^}]+)\}', re.IGNORECASE)
        pattern_data = re.compile(r'set_max_transition\s+-data_path\s+([\d.]+).*get_clocks\s+\{([^}]+)\}', re.IGNORECASE)
        
        for file_path in valid_files:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            for line_num, line in enumerate(lines, 1):
                # Match clock_path
                match_clock = pattern_clock.search(line)
                if match_clock:
                    value, clock_name = match_clock.groups()
                    clock_name = clock_name.strip()
                    
                    if clock_name not in clocks_transitions:
                        clocks_transitions[clock_name] = {
                            'clock_path': {},
                            'data_path': {},
                            'all_lines': []
                        }
                    
                    if value not in clocks_transitions[clock_name]['clock_path']:
                        clocks_transitions[clock_name]['clock_path'][value] = []
                    clocks_transitions[clock_name]['clock_path'][value].append(line_num)
                    clocks_transitions[clock_name]['all_lines'].append(line_num)
                
                # Match data_path
                match_data = pattern_data.search(line)
                if match_data:
                    value, clock_name = match_data.groups()
                    clock_name = clock_name.strip()
                    
                    if clock_name not in clocks_transitions:
                        clocks_transitions[clock_name] = {
                            'clock_path': {},
                            'data_path': {},
                            'all_lines': []
                        }
                    
                    if value not in clocks_transitions[clock_name]['data_path']:
                        clocks_transitions[clock_name]['data_path'][value] = []
                    clocks_transitions[clock_name]['data_path'][value].append(line_num)
                    clocks_transitions[clock_name]['all_lines'].append(line_num)
        
        return clocks_transitions

    def _check_pattern_in_log(self, pattern: str) -> Dict[str, Any]:
        """Check if pattern exists in log (case-insensitive, supports regex)."""
        if not self.item_data or 'input_files' not in self.item_data:
            return {'found': False, 'line_number': 0, 'file_path': '', 'value': ''}
        
        valid_files, _ = self.validate_input_files()
        pattern_lower = pattern.lower()
        
        for file_path in valid_files:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            for line_num, line in enumerate(lines, 1):
                line_lower = line.lower()
                
                # Try regex match
                try:
                    if re.search(pattern_lower, line_lower):
                        return {
                            'found': True,
                            'line_number': line_num,
                            'file_path': str(file_path),
                            'value': line.strip()
                        }
                except re.error:
                    pass
                
                # Fallback: Try substring match
                if pattern_lower in line_lower:
                    return {
                        'found': True,
                        'line_number': line_num,
                        'file_path': str(file_path),
                        'value': line.strip()
                    }
        
        return {'found': False, 'line_number': 0, 'file_path': '', 'value': ''}

    # =========================================================================
    # Main Execution
    # =========================================================================

    def execute_check(self) -> CheckResult:
        """Execute check with automatic type detection."""
        if self.root is None:
            raise RuntimeError("Checker not initialized. Call init_checker() first.")
        
        requirements = self.get_requirements()
        self._pattern_items = requirements.get('pattern_items', []) if requirements else []
        
        # Detect checker type
        checker_type = self.detect_checker_type()
        
        # Parse clock transitions for Type 1 and 4
        if checker_type in [1, 4]:
            self._clocks_transitions = self._parse_constr_rpt()
        
        # Execute based on type
        if checker_type == 1:
            return self._execute_type1()
        elif checker_type == 2:
            return self._execute_type2()
        elif checker_type == 3:
            return self._execute_type3()
        else:  # checker_type == 4
            return self._execute_type4()

    # =========================================================================
    # Type 1: Boolean Check
    # =========================================================================

    def _execute_type1(self) -> CheckResult:
        """Type 1: Boolean check - verify all clocks have both clock_path and data_path."""
        # Get waiver configuration
        waivers = self.get_waivers()
        waiver_value = waivers.get('value', 'N/A') if waivers else 'N/A'
        waive_items = waivers.get('waive_items', []) if waivers else []
        is_waiver_zero = (waiver_value == 0)
        
        details = []
        
        if not self._clocks_transitions:
            if is_waiver_zero:
                # waiver=0: 转为 INFO
                details.append(DetailItem(
                    severity=Severity.INFO,
                    name="Clock Transitions",
                    line_number=0,
                    file_path=self._constr_rpt_path,
                    reason="No clock transition settings found in constr.rpt[WAIVED_AS_INFO]"
                ))
                # Add waive_items
                if waive_items:
                    for item in waive_items:
                        details.append(DetailItem(
                            severity=Severity.INFO,
                            name=item,
                            line_number=0,
                            file_path=self._constr_rpt_path,
                            reason="Waive item[WAIVED_INFO]"
                        ))
                self._log_lines_override = [
                    f"{self.item_id}-INFO01: All violations waived:",
                    "  Severity: Info Occurrence: 1",
                    "  - No clock transition settings found in constr.rpt[WAIVED_AS_INFO]"
                ]
                if waive_items:
                    count = len(waive_items)
                    self._log_lines_override.append(f"{self.item_id}-INFO02: Waive items:")
                    self._log_lines_override.append(f"  Severity: Info Occurrence: {count}")
                    for item in waive_items:
                        self._log_lines_override.append(f"  - {item}[WAIVED_INFO]")
                
                return CheckResult(
                    result_type=ResultType.PASS_WITHOUT_CHECK_VALUES,
                    is_pass=True,
                    value='N/A',
                    has_pattern_items=False,
                    has_waiver_value=bool(waive_items),
                    details=details
                )
            else:
                details.append(DetailItem(
                    severity=Severity.FAIL,
                    name="Clock Transitions",
                    line_number=0,
                    file_path=self._constr_rpt_path,
                    reason="No clock transition settings found in constr.rpt"
                ))
                self._log_lines_override = [
                    f"{self.item_id}-ERROR01: No clock transition settings found:",
                    "  Severity: Fail Occurrence: 1",
                    "  - No clock transition settings found in constr.rpt"
                ]
                return CheckResult(
                    result_type=ResultType.FAIL_WITHOUT_CHECK_VALUES,
                    is_pass=False,
                    value='N/A',
                    has_pattern_items=False,
                    has_waiver_value=bool(waive_items),
                    details=details
                )
        
        # Check each clock
        incomplete_clocks = []
        complete_clocks = []
        
        for clock_name, transitions in sorted(self._clocks_transitions.items()):
            clock_paths = transitions.get('clock_path', {})
            data_paths = transitions.get('data_path', {})
            all_lines = transitions.get('all_lines', [])
            
            has_clock = len(clock_paths) > 0
            has_data = len(data_paths) > 0
            
            if has_clock and has_data:
                # Format line range
                if all_lines:
                    line_range = f"{min(all_lines)}-{max(all_lines)}" if len(set(all_lines)) > 1 else str(all_lines[0])
                else:
                    line_range = "N/A"
                
                # Format values
                parts = []
                if len(clock_paths) > 1:
                    parts.append(f"clock_path: {', '.join(clock_paths.keys())}")
                else:
                    parts.append(f"clock_path={list(clock_paths.keys())[0]}")
                
                if len(data_paths) > 1:
                    parts.append(f"data_path: {', '.join(data_paths.keys())}")
                else:
                    parts.append(f"data_path={list(data_paths.keys())[0]}")
                
                reason = f"Transition settings found ({', '.join(parts)})"
                complete_clocks.append((clock_name, reason, line_range))
                
                details.append(DetailItem(
                    severity=Severity.INFO,
                    name=clock_name,
                    line_number=int(line_range.split('-')[0]) if '-' in line_range else (int(line_range) if line_range != "N/A" else 0),
                    file_path=self._constr_rpt_path,
                    reason=reason
                ))
            else:
                # Missing clock_path or data_path
                missing = []
                if not has_clock:
                    missing.append('clock_path')
                if not has_data:
                    missing.append('data_path')
                
                line_num = min(all_lines) if all_lines else 0
                reason = f"Missing {', '.join(missing)}"
                incomplete_clocks.append((clock_name, reason, line_num))
                
                if is_waiver_zero:
                    # waiver=0: 转为 INFO
                    details.append(DetailItem(
                        severity=Severity.INFO,
                        name=clock_name,
                        line_number=line_num,
                        file_path=self._constr_rpt_path,
                        reason=f"{reason}[WAIVED_AS_INFO]"
                    ))
                else:
                    details.append(DetailItem(
                        severity=Severity.FAIL,
                        name=clock_name,
                        line_number=line_num,
                        file_path=self._constr_rpt_path,
                        reason=reason
                    ))
        
        # Add waive_items as INFO (when waiver=0)
        if is_waiver_zero and waive_items:
            for item in waive_items:
                details.append(DetailItem(
                    severity=Severity.INFO,
                    name=item,
                    line_number=0,
                    file_path=self._constr_rpt_path,
                    reason="Waive item[WAIVED_INFO]"
                ))
        
        # Determine overall pass/fail
        if is_waiver_zero:
            is_pass = True  # 强制 PASS
        else:
            is_pass = (len(incomplete_clocks) == 0)
        
        # Build custom log lines
        log_lines = []
        
        if incomplete_clocks and not is_waiver_zero:
            clock_count = len(incomplete_clocks)
            log_lines.append(f"{self.item_id}-ERROR01: Transition settings incomplete ({clock_count} clock{'s' if clock_count > 1 else ''}):")
            log_lines.append(f"  Severity: Fail Occurrence: {clock_count}")
            for clock_name, reason, _ in incomplete_clocks:
                log_lines.append(f"  - {clock_name}: {reason}")
        
        if complete_clocks:
            clock_count = len(complete_clocks)
            if is_waiver_zero:
                status_str = "verified (waived)"
            else:
                status_str = "verified"
            log_lines.append(f"{self.item_id}-INFO01: Transition settings {status_str} ({clock_count} clock{'s' if clock_count > 1 else ''}):")
            log_lines.append(f"  Severity: Info Occurrence: {clock_count}")
            for clock_name, reason, _ in complete_clocks:
                reason_clean = reason.replace("Transition settings found (", "").replace(")", "")
                log_lines.append(f"  - {clock_name}: {reason_clean}")
        
        if is_waiver_zero and incomplete_clocks:
            clock_count = len(incomplete_clocks)
            log_lines.append(f"{self.item_id}-INFO02: All violations waived:")
            log_lines.append(f"  Severity: Info Occurrence: {clock_count}")
            for clock_name, reason, _ in incomplete_clocks:
                log_lines.append(f"  - {clock_name}: {reason}[WAIVED_AS_INFO]")
        
        if is_waiver_zero and waive_items:
            count = len(waive_items)
            log_lines.append(f"{self.item_id}-INFO03: Waive items:")
            log_lines.append(f"  Severity: Info Occurrence: {count}")
            for item in waive_items:
                log_lines.append(f"  - {item}[WAIVED_INFO]")
        
        self._log_lines_override = log_lines
        
        result_type = CheckResult.determine_result_type('N/A', is_pass, False, bool(waive_items))
        
        return CheckResult(
            result_type=result_type,
            is_pass=is_pass,
            value='N/A',
            has_pattern_items=False,
            has_waiver_value=bool(waive_items),
            details=details
        )

    # =========================================================================
    # Type 2: Pattern Matching
    # =========================================================================

    def _execute_type2(self) -> CheckResult:
        """Type 2: Pattern matching - check if specific patterns exist in log."""
        if not self._pattern_items:
            raise ConfigurationError("Type 2 requires pattern_items in requirements")
        
        # Parse all clock transitions to find additional ones
        all_transitions = self._parse_constr_rpt()
        
        # Get waiver configuration
        waivers = self.get_waivers()
        waiver_value = waivers.get('value', 'N/A') if waivers else 'N/A'
        waive_items = waivers.get('waive_items', []) if waivers else []
        is_waiver_zero = (waiver_value == 0)
        
        details = []
        found_count = 0
        missing_patterns = []
        found_patterns = []
        additional_clocks = []
        
        # Extract expected clock names from pattern_items
        expected_clocks = set()
        for pattern in self._pattern_items:
            match = re.search(r'get_clocks\s+\{([^}]+)\}', pattern)
            if match:
                expected_clocks.add(match.group(1).strip())
        
        # Check required patterns
        for pattern in self._pattern_items:
            result = self._check_pattern_in_log(pattern)
            
            if result['found']:
                found_count += 1
                found_patterns.append(pattern)
                
                # Determine reason based on pattern content
                if '-clock_path' in pattern:
                    reason = "clock transition is correct"
                elif '-data_path' in pattern:
                    reason = "data transition is correct"
                else:
                    reason = "Pattern found"
                
                details.append(DetailItem(
                    severity=Severity.INFO,
                    name=pattern,
                    line_number=result['line_number'],
                    file_path=Path(result['file_path']).name if result['file_path'] else "constr.rpt",
                    reason=reason
                ))
            else:
                missing_patterns.append(pattern)
                if is_waiver_zero:
                    # waiver=0: 转为 INFO
                    details.append(DetailItem(
                        severity=Severity.INFO,
                        name=pattern,
                        line_number=0,
                        file_path=self._constr_rpt_path,
                        reason="Pattern not found[WAIVED_AS_INFO]"
                    ))
                else:
                    details.append(DetailItem(
                        severity=Severity.FAIL,
                        name=pattern,
                        line_number=0,
                        file_path=self._constr_rpt_path,
                        reason="Pattern not found"
                    ))
        
        # Find additional clocks not in requirements
        for clock_name, transitions in sorted(all_transitions.items()):
            if clock_name not in expected_clocks:
                clock_paths = transitions.get('clock_path', {})
                data_paths = transitions.get('data_path', {})
                all_lines = transitions.get('all_lines', [])
                
                if clock_paths or data_paths:
                    line_num = min(all_lines) if all_lines else 0
                    
                    # Format transition values
                    parts = []
                    if clock_paths:
                        clock_val = ', '.join(clock_paths.keys())
                        parts.append(f"clock_path={clock_val}")
                    if data_paths:
                        data_val = ', '.join(data_paths.keys())
                        parts.append(f"data_path={data_val}")
                    
                    transition_info = f"{clock_name} ({', '.join(parts)})"
                    additional_clocks.append(transition_info)
                    
                    if is_waiver_zero:
                        # waiver=0: 转为 INFO
                        details.append(DetailItem(
                            severity=Severity.INFO,
                            name=clock_name,
                            line_number=line_num,
                            file_path=self._constr_rpt_path,
                            reason=f"Another clock transition found: {', '.join(parts)}[WAIVED_AS_INFO]"
                        ))
                    else:
                        details.append(DetailItem(
                            severity=Severity.WARN,
                            name=clock_name,
                            line_number=line_num,
                            file_path=self._constr_rpt_path,
                            reason=f"Another clock transition found: {', '.join(parts)}"
                        ))
        
        # Add waive_items as INFO (when waiver=0)
        if is_waiver_zero and waive_items:
            for item in waive_items:
                details.append(DetailItem(
                    severity=Severity.INFO,
                    name=item,
                    line_number=0,
                    file_path=self._constr_rpt_path,
                    reason="Waive item[WAIVED_INFO]"
                ))
        
        # Determine pass/fail
        if is_waiver_zero:
            is_pass = True  # 强制 PASS
        else:
            is_pass = (found_count == len(self._pattern_items) and len(additional_clocks) == 0)
        
        # Build custom log lines
        log_lines = []
        
        if missing_patterns and not is_waiver_zero:
            count = len(missing_patterns)
            log_lines.append(f"{self.item_id}-ERROR01: Transition settings incorrect (pattern not found):")
            log_lines.append(f"  Severity: Fail Occurrence: {count}")
            for p in missing_patterns:
                log_lines.append(f"  - {p}")
        
        if additional_clocks and not is_waiver_zero:
            count = len(additional_clocks)
            log_lines.append(f"{self.item_id}-ERROR02: Another clock transition and data transition found:")
            log_lines.append(f"  Severity: Error Occurrence: {count}")
            for clk_info in additional_clocks:
                log_lines.append(f"  - {clk_info}")
        
        if found_patterns:
            count = len(found_patterns)
            total = len(self._pattern_items)
            if is_waiver_zero:
                status_str = "correct (waived)"
            else:
                status_str = "correct" if is_pass else "partially correct"
            log_lines.append(f"{self.item_id}-INFO01: Transition settings {status_str} ({count}/{total} patterns found):")
            log_lines.append(f"  Severity: Info Occurrence: {count}")
            for p in found_patterns:
                log_lines.append(f"  - {p}")
        
        if is_waiver_zero:
            # 添加所有waived violations
            all_waived = []
            if missing_patterns:
                all_waived.extend(missing_patterns)
            if additional_clocks:
                all_waived.extend(additional_clocks)
            
            if all_waived:
                count = len(all_waived)
                log_lines.append(f"{self.item_id}-INFO02: All violations waived:")
                log_lines.append(f"  Severity: Info Occurrence: {count}")
                for item in all_waived:
                    log_lines.append(f"  - {item}[WAIVED_AS_INFO]")
            
            if waive_items:
                count = len(waive_items)
                log_lines.append(f"{self.item_id}-INFO03: Waive items:")
                log_lines.append(f"  Severity: Info Occurrence: {count}")
                for item in waive_items:
                    log_lines.append(f"  - {item}[WAIVED_INFO]")
        
        self._log_lines_override = log_lines
        
        result_type = CheckResult.determine_result_type(found_count, is_pass, True, bool(waive_items))
        
        return CheckResult(
            result_type=result_type,
            is_pass=is_pass,
            value=found_count,
            has_pattern_items=True,
            has_waiver_value=bool(waive_items),
            details=details
        )

    # =========================================================================
    # Type 3: Pattern Matching + Waiver
    # =========================================================================

    def _execute_type3(self) -> CheckResult:
        """Type 3: Pattern matching with waiver logic."""
        if not self._pattern_items:
            raise ConfigurationError("Type 3 requires pattern_items in requirements")
        
        # Parse all clock transitions to find additional ones
        all_transitions = self._parse_constr_rpt()
        
        # Get waiver configuration
        waivers = self.get_waivers()
        waive_items = waivers.get('waive_items', []) if waivers else []
        
        details = []
        found_count = 0
        missing_patterns = []
        found_patterns = []
        additional_clocks = []
        waived_additional_clocks = []
        unused_waivers = list(waive_items)
        
        # Extract expected clock names from pattern_items
        expected_clocks = set()
        for pattern in self._pattern_items:
            match = re.search(r'get_clocks\s+\{([^}]+)\}', pattern)
            if match:
                expected_clocks.add(match.group(1).strip())
        
        # Check required patterns
        for pattern in self._pattern_items:
            result = self._check_pattern_in_log(pattern)
            
            if result['found']:
                found_count += 1
                found_patterns.append(pattern)
                
                # Determine reason based on pattern content
                if '-clock_path' in pattern:
                    reason = "clock transition is correct"
                elif '-data_path' in pattern:
                    reason = "data transition is correct"
                else:
                    reason = "Pattern found"
                
                details.append(DetailItem(
                    severity=Severity.INFO,
                    name=pattern,
                    line_number=result['line_number'],
                    file_path=Path(result['file_path']).name if result['file_path'] else "constr.rpt",
                    reason=reason
                ))
            else:
                missing_patterns.append(pattern)
                details.append(DetailItem(
                    severity=Severity.FAIL,
                    name=pattern,
                    line_number=0,
                    file_path=self._constr_rpt_path,
                    reason="Pattern not found"
                ))
        
        # Find additional clocks not in requirements
        for clock_name, transitions in sorted(all_transitions.items()):
            if clock_name not in expected_clocks:
                clock_paths = transitions.get('clock_path', {})
                data_paths = transitions.get('data_path', {})
                all_lines = transitions.get('all_lines', [])
                
                if clock_paths or data_paths:
                    line_num = min(all_lines) if all_lines else 0
                    
                    # Format transition values
                    parts = []
                    if clock_paths:
                        clock_val = ', '.join(clock_paths.keys())
                        parts.append(f"clock_path={clock_val}")
                    if data_paths:
                        data_val = ', '.join(data_paths.keys())
                        parts.append(f"data_path={data_val}")
                    
                    transition_info = f"{clock_name} ({', '.join(parts)})"
                    
                    # Check if this clock is waived
                    if clock_name in waive_items:
                        waived_additional_clocks.append(transition_info)
                        if clock_name in unused_waivers:
                            unused_waivers.remove(clock_name)
                        details.append(DetailItem(
                            severity=Severity.INFO,
                            name=clock_name,
                            line_number=line_num,
                            file_path=self._constr_rpt_path,
                            reason=f"Another clock transition found: {', '.join(parts)}[WAIVER]"
                        ))
                    else:
                        additional_clocks.append(transition_info)
                        details.append(DetailItem(
                            severity=Severity.WARN,
                            name=clock_name,
                            line_number=line_num,
                            file_path=self._constr_rpt_path,
                            reason=f"Another clock transition found: {', '.join(parts)}"
                        ))
        
        # Add unused waivers
        for waiver in unused_waivers:
            details.append(DetailItem(
                severity=Severity.WARN,
                name=waiver,
                line_number=0,
                file_path=self._constr_rpt_path,
                reason="Waiver not used[WAIVER]"
            ))
        
        # Determine pass/fail
        is_pass = (found_count == len(self._pattern_items) and len(additional_clocks) == 0)
        is_waived_pass = is_pass and (len(waived_additional_clocks) > 0)
        
        # Build custom log lines
        log_lines = []
        
        if missing_patterns:
            count = len(missing_patterns)
            log_lines.append(f"{self.item_id}-ERROR01: Transition settings incorrect (pattern not found):")
            log_lines.append(f"  Severity: Fail Occurrence: {count}")
            for p in missing_patterns:
                log_lines.append(f"  - {p}")
        
        if additional_clocks:
            count = len(additional_clocks)
            log_lines.append(f"{self.item_id}-ERROR02: Another clock transition and data transition found (not waived):")
            log_lines.append(f"  Severity: Error Occurrence: {count}")
            for clk_info in additional_clocks:
                log_lines.append(f"  - {clk_info}")
        
        if unused_waivers:
            count = len(unused_waivers)
            log_lines.append(f"{self.item_id}-WARN01: Waiver not used:")
            log_lines.append(f"  Severity: Warn Occurrence: {count}")
            for w in unused_waivers:
                log_lines.append(f"  - {w}[WAIVER]")
        
        if found_patterns:
            count = len(found_patterns)
            total = len(self._pattern_items)
            status_str = "correct" if is_pass else "partially correct"
            log_lines.append(f"{self.item_id}-INFO01: Transition settings {status_str} ({count}/{total} patterns found):")
            log_lines.append(f"  Severity: Info Occurrence: {count}")
            for p in found_patterns:
                log_lines.append(f"  - {p}")
        
        if waived_additional_clocks:
            count = len(waived_additional_clocks)
            log_lines.append(f"{self.item_id}-INFO02: Additional clocks waived:")
            log_lines.append(f"  Severity: Info Occurrence: {count}")
            for clk_info in waived_additional_clocks:
                log_lines.append(f"  - {clk_info}[WAIVER]")
        
        self._log_lines_override = log_lines
        
        if is_waived_pass:
            result_type = ResultType.PASS_WITH_FULL_WAIVERS
        elif is_pass:
            result_type = ResultType.PASS_WITH_VALUES
        else:
            result_type = ResultType.FAIL_WITH_VALUES
        
        result = CheckResult(
            result_type=result_type,
            is_pass=is_pass,
            value=found_count,
            has_pattern_items=True,
            has_waiver_value=True,
            details=details
        )
        result._is_waived_pass = is_waived_pass
        return result

    # =========================================================================
    # Type 4: Boolean + Waiver
    # =========================================================================

    def _execute_type4(self) -> CheckResult:
        """Type 4: Boolean check with waiver logic (waiver as notes)."""
        # Get waiver configuration
        waivers = self.get_waivers()
        waive_items = waivers.get('waive_items', []) if waivers else []
        
        details = []
        
        if not self._clocks_transitions:
            details.append(DetailItem(
                severity=Severity.FAIL,
                name="Clock Transitions",
                line_number=0,
                file_path=self._constr_rpt_path,
                reason="No clock transition settings found in constr.rpt"
            ))
            
            # Add waiver notes
            for waiver in waive_items:
                details.append(DetailItem(
                    severity=Severity.WARN,
                    name=waiver,
                    line_number=0,
                    file_path=self._constr_rpt_path,
                    reason="Waiver not used[WAIVER]"
                ))
            
            self._log_lines_override = [
                f"{self.item_id}-ERROR01: No clock transition settings found:",
                "  Severity: Fail Occurrence: 1",
                "  - No clock transition settings found in constr.rpt"
            ]
            if waive_items:
                count = len(waive_items)
                self._log_lines_override.append(f"{self.item_id}-WARN01: Waiver not used ({count} items):")
                self._log_lines_override.append(f"  Severity: Warn Occurrence: {count}")
                for w in waive_items:
                    self._log_lines_override.append(f"  - {w}[WAIVER]")
            
            return CheckResult(
                result_type=ResultType.FAIL_WITHOUT_CHECK_VALUES,
                is_pass=False,
                value='N/A',
                has_pattern_items=False,
                has_waiver_value=True,
                details=details
            )
        
        # Check each clock
        incomplete_clocks = []
        complete_clocks = []
        waived_incomplete_clocks = []
        unused_waivers = list(waive_items)
        
        for clock_name, transitions in sorted(self._clocks_transitions.items()):
            clock_paths = transitions.get('clock_path', {})
            data_paths = transitions.get('data_path', {})
            all_lines = transitions.get('all_lines', [])
            
            has_clock = len(clock_paths) > 0
            has_data = len(data_paths) > 0
            
            if has_clock and has_data:
                # Format line range
                if all_lines:
                    line_range = f"{min(all_lines)}-{max(all_lines)}" if len(set(all_lines)) > 1 else str(all_lines[0])
                else:
                    line_range = "N/A"
                
                # Format values
                parts = []
                if len(clock_paths) > 1:
                    parts.append(f"clock_path: {', '.join(clock_paths.keys())}")
                else:
                    parts.append(f"clock_path={list(clock_paths.keys())[0]}")
                
                if len(data_paths) > 1:
                    parts.append(f"data_path: {', '.join(data_paths.keys())}")
                else:
                    parts.append(f"data_path={list(data_paths.keys())[0]}")
                
                reason = f"Transition settings found ({', '.join(parts)})"
                complete_clocks.append((clock_name, reason, line_range))
                
                details.append(DetailItem(
                    severity=Severity.INFO,
                    name=clock_name,
                    line_number=int(line_range.split('-')[0]) if '-' in line_range else (int(line_range) if line_range != "N/A" else 0),
                    file_path=self._constr_rpt_path,
                    reason=reason
                ))
            else:
                # Missing clock_path or data_path
                missing = []
                if not has_clock:
                    missing.append('clock_path')
                if not has_data:
                    missing.append('data_path')
                
                line_num = min(all_lines) if all_lines else 0
                reason = f"Missing {', '.join(missing)}"
                
                # Check if this clock is waived
                if clock_name in waive_items:
                    waived_incomplete_clocks.append((clock_name, reason, line_num))
                    if clock_name in unused_waivers:
                        unused_waivers.remove(clock_name)
                    details.append(DetailItem(
                        severity=Severity.INFO,
                        name=clock_name,
                        line_number=line_num,
                        file_path=self._constr_rpt_path,
                        reason=f"{reason}[WAIVER]"
                    ))
                else:
                    incomplete_clocks.append((clock_name, reason, line_num))
                    details.append(DetailItem(
                        severity=Severity.FAIL,
                        name=clock_name,
                        line_number=line_num,
                        file_path=self._constr_rpt_path,
                        reason=reason
                    ))
        
        # Add unused waivers
        for waiver in unused_waivers:
            details.append(DetailItem(
                severity=Severity.WARN,
                name=waiver,
                line_number=0,
                file_path=self._constr_rpt_path,
                reason="Waiver not used[WAIVER]"
            ))
        
        # Determine pass/fail
        is_pass = (len(incomplete_clocks) == 0)
        is_waived_pass = is_pass and (len(waived_incomplete_clocks) > 0)
        
        # Build custom log lines
        log_lines = []
        
        if incomplete_clocks:
            clock_count = len(incomplete_clocks)
            log_lines.append(f"{self.item_id}-ERROR01: Transition settings incomplete ({clock_count} clock{'s' if clock_count > 1 else ''}):")
            log_lines.append(f"  Severity: Fail Occurrence: {clock_count}")
            for clock_name, reason, _ in incomplete_clocks:
                log_lines.append(f"  - {clock_name}: {reason}")
        
        if unused_waivers:
            count = len(unused_waivers)
            log_lines.append(f"{self.item_id}-WARN01: Waiver not used ({count} items):")
            log_lines.append(f"  Severity: Warn Occurrence: {count}")
            for w in unused_waivers:
                log_lines.append(f"  - {w}[WAIVER]")
        
        if complete_clocks:
            clock_count = len(complete_clocks)
            log_lines.append(f"{self.item_id}-INFO01: Transition settings verified ({clock_count} clock{'s' if clock_count > 1 else ''}):")
            log_lines.append(f"  Severity: Info Occurrence: {clock_count}")
            for clock_name, reason, _ in complete_clocks:
                reason_clean = reason.replace("Transition settings found (", "").replace(")", "")
                log_lines.append(f"  - {clock_name}: {reason_clean}")
        
        if waived_incomplete_clocks:
            clock_count = len(waived_incomplete_clocks)
            log_lines.append(f"{self.item_id}-INFO02: Incomplete clocks waived:")
            log_lines.append(f"  Severity: Info Occurrence: {clock_count}")
            for clock_name, reason, _ in waived_incomplete_clocks:
                log_lines.append(f"  - {clock_name}: {reason}[WAIVER]")
        
        self._log_lines_override = log_lines
        
        if is_waived_pass:
            result_type = ResultType.PASS_WITH_FULL_WAIVERS
        elif is_pass:
            result_type = ResultType.PASS_WITHOUT_VALUES
        else:
            result_type = ResultType.FAIL_WITHOUT_CHECK_VALUES
        
        result = CheckResult(
            result_type=result_type,
            is_pass=is_pass,
            value='N/A',
            has_pattern_items=False,
            has_waiver_value=True,
            details=details
        )
        result._is_waived_pass = is_waived_pass
        return result
    
    def write_output(self, check_result: CheckResult):
        """Override write_output to use custom log lines if available."""
        if self.formatter is None or self.log_path is None or self.rpt_path is None:
            raise RuntimeError("Checker not initialized. Call init_checker() first.")
        
        # Always write the report using the standard formatter
        self.formatter.write_report(check_result, self.rpt_path, mode='w')
        
        # Custom log formatting when override lines are available
        if self._log_lines_override:
            self.log_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Check if this is a waived pass
            is_waived_pass = hasattr(check_result, '_is_waived_pass') and check_result._is_waived_pass
            
            if check_result.is_pass and is_waived_pass:
                status = "PASS(Waive)"
            else:
                status = "PASS" if check_result.is_pass else "FAIL"
            
            with self.log_path.open('w', encoding='utf-8') as log_file:
                log_file.write(f'{status}:{self.item_id}:{self.item_desc}\n')
                log_output = '\n'.join(str(line) for line in self._log_lines_override)
                log_file.write(log_output + '\n')
        else:
            self.formatter.write_log(check_result, self.log_path, mode='w')
        
        # Cache result using the shared cache manager
        from result_cache_manager import configure_global_cache
        cache = configure_global_cache(
            cache_dir=self.cache_dir,
            max_memory_size=200,
            enable_file_cache=True
        )
        cache.set(self.item_id, check_result)
        
        BaseChecker._result_cache[self.item_id] = check_result


def main():
    """Main entry point."""
    checker = ClockTransitionChecker()
    checker.run()


if __name__ == "__main__":
    main()
