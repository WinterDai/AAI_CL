################################################################################
# Script Name: IMP-10-0-0-04.py
#
# Purpose:
#   Confirm the SDC has no ideal clock networks.
#   Parse check_timing.rpt to identify clocks with ideal waveforms.
#
# Logic:
#   - Parse check_timing.rpt Summary section for ideal_clock_waveform count
#   - Parse TIMING CHECK IDEAL CLOCKS detail section for specific clock names
#   - Use detail list as primary source (more reliable than summary count)
#   - Validate Summary count matches Detail list length
#   - Support exact matching for pattern_items and waive_items
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
# Author: yyin
# Date: 2025-12-02
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


class IdealClockNetworkChecker(BaseChecker):
    """
    Unified checker that auto-detects and handles all 4 checker types.
    
    Check Target: Confirm the SDC has no ideal clock networks
    
    Type Detection Logic:
    - Type 1: requirements.value=N/A AND waivers.value=N/A/0
    - Type 2: requirements.value>0 AND pattern_items AND waivers.value=N/A/0
    - Type 3: requirements.value>0 AND pattern_items AND waivers.value>0
    - Type 4: requirements.value=N/A AND waivers.value>0
    """
    
    def __init__(self):
        super().__init__(
            check_module="10.0_STA_DCD_CHECK",
            item_id="IMP-10-0-0-04",
            item_desc="Confirm the SDC has no ideal clock networks"
        )
        self._ideal_clocks: List[Dict[str, Any]] = []
        self._summary_count: int = 0
    
    def _parse_ideal_clocks(self, file_path: Path) -> Tuple[int, List[Dict[str, Any]]]:
        """
        Parse check_timing.rpt to extract ideal clock information.
        
        Args:
            file_path: Path to check_timing.rpt
            
        Returns:
            Tuple of (summary_count, list of ideal clock dicts)
        """
        summary_count = 0
        ideal_clocks = []
        in_detail_section = False
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line_num, line in enumerate(f, 1):
                    # Parse Summary section
                    if 'ideal_clock_waveform' in line:
                        match = re.search(r'ideal_clock_waveform\s+.*?\s+(\d+)\s*$', line)
                        if match:
                            summary_count = int(match.group(1))
                    
                    # Parse Detail section header
                    if 'TIMING CHECK IDEAL CLOCKS' in line:
                        in_detail_section = True
                        continue
                    
                    # Parse Detail section content
                    if in_detail_section:
                        # Stop at next section
                        if line.strip().startswith('TIMING CHECK') and 'IDEAL CLOCKS' not in line:
                            in_detail_section = False
                            continue
                        
                        if line.strip() == '' and ideal_clocks:
                            in_detail_section = False
                            continue
                        
                        # Skip separator lines
                        if line.strip().startswith('-') or line.strip() == '':
                            continue
                        
                        # Skip header line (e.g., "Clock Waveform")
                        if 'Clock Waveform' in line or 'Clock' in line and 'Waveform' in line:
                            continue
                        
                        # Extract clock name
                        tokens = line.strip().split()
                        if tokens:
                            clock_name = tokens[0]
                            ideal_clocks.append({
                                'name': clock_name,
                                'line_number': line_num
                            })
        
        except Exception as e:
            raise ConfigurationError(f"Failed to parse {file_path.name}: {e}")
        
        # Validation
        if summary_count != len(ideal_clocks):
            print(f"Warning: Summary count ({summary_count}) doesn't match detail list length ({len(ideal_clocks)}). Using detail list.")
        
        return summary_count, ideal_clocks
    
    def execute_check(self) -> CheckResult:
        """Execute the ideal clock network check based on detected type."""
        # Validate configuration
        if not self.item_data or 'input_files' not in self.item_data:
            raise ConfigurationError("No input_files specified in configuration")
        
        input_files = self.item_data.get('input_files', '')
        if not input_files:
            raise ConfigurationError("input_files is empty in configuration")
        
        if isinstance(input_files, str):
            input_files = [input_files]
        
        if not input_files:
            raise ConfigurationError("input_files list is empty after conversion")
        
        # Parse input file
        file_path = Path(input_files[0])
        if not file_path.exists():
            raise ConfigurationError(f"Input file not found: {file_path}")
        
        # Parse ideal clocks
        self._summary_count, self._ideal_clocks = self._parse_ideal_clocks(file_path)
        
        # Execute based on checker type
        checker_type = self.detect_checker_type()
        
        if checker_type == 1:
            return self._execute_type1(file_path)
        elif checker_type == 2:
            return self._execute_type2(file_path)
        elif checker_type == 3:
            return self._execute_type3(file_path)
        elif checker_type == 4:
            return self._execute_type4(file_path)
        else:
            raise ConfigurationError(f"Unknown checker type: {checker_type}")
    
    def _execute_type1(self, file_path: Path) -> CheckResult:
        """Type 1: Boolean check - no ideal clocks should exist."""
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', []) if waivers else []
        waiver_value = waivers.get('value', 'N/A') if waivers else 'N/A'
        
        # Check if waiver=0 (force PASS mode)
        is_waiver_zero = (waiver_value == 0)
        
        details = []
        
        if not self._ideal_clocks:
            # PASS: No ideal clocks
            details.append(DetailItem(
                severity=Severity.INFO,
                name="No ideal clock networks found",
                line_number=0,
                file_path=str(file_path),
                reason="Check passed"
            ))
            is_pass = True
        else:
            # Ideal clocks found
            if is_waiver_zero:
                # waiver=0: Convert FAIL to INFO with [WAIVED_AS_INFO]
                for clock in self._ideal_clocks:
                    details.append(DetailItem(
                        severity=Severity.INFO,
                        name=clock['name'],
                        line_number=clock['line_number'],
                        file_path=str(file_path),
                        reason="Ideal clock network detected[WAIVED_AS_INFO]"
                    ))
                is_pass = True
            else:
                # Normal mode: FAIL
                for clock in self._ideal_clocks:
                    details.append(DetailItem(
                        severity=Severity.FAIL,
                        name=clock['name'],
                        line_number=clock['line_number'],
                        file_path=str(file_path),
                        reason="Ideal clock network detected"
                    ))
                is_pass = False
        
        # Add waive_items as INFO with [WAIVED_INFO] if waiver=0
        if is_waiver_zero and waive_items_raw:
            for item in waive_items_raw:
                item_name = item.get('name', str(item)) if isinstance(item, dict) else str(item)
                details.append(DetailItem(
                    severity=Severity.INFO,
                    name=item_name,
                    line_number=0,
                    file_path="N/A",
                    reason="Waive item[WAIVED_INFO]"
                ))
        
        return create_check_result(
            value=len(self._ideal_clocks),
            is_pass=is_pass,
            has_pattern_items=False,
            has_waiver_value=bool(waive_items_raw),
            details=details,
            item_desc=self.item_desc,
            default_group_desc="Ideal clock network check"
        )
    
    def _execute_type2(self, file_path: Path) -> CheckResult:
        """Type 2: Pattern matching - specific ideal clocks expected."""
        requirements = self.get_requirements()
        waivers = self.get_waivers()
        
        pattern_items = requirements.get('pattern_items', []) if requirements else []
        waive_items_raw = waivers.get('waive_items', []) if waivers else []
        waiver_value = waivers.get('value', 'N/A') if waivers else 'N/A'
        
        # Check if waiver=0 (force PASS mode)
        is_waiver_zero = (waiver_value == 0)
        
        details = []
        found_clocks = {clock['name'] for clock in self._ideal_clocks}
        expected_clocks = set(pattern_items)
        
        matched = expected_clocks & found_clocks
        missing = expected_clocks - found_clocks
        extra = found_clocks - expected_clocks
        
        if is_waiver_zero:
            # waiver=0: All items as INFO, FAIL/WARN → INFO with [WAIVED_AS_INFO]
            # Matched clocks
            for clock in self._ideal_clocks:
                if clock['name'] in matched:
                    details.append(DetailItem(
                        severity=Severity.INFO,
                        name=clock['name'],
                        line_number=clock['line_number'],
                        file_path=str(file_path),
                        reason="Expected ideal clock found[WAIVED_AS_INFO]"
                    ))
            
            # Missing expected clocks (would be FAIL, now INFO)
            for clock_name in sorted(missing):
                details.append(DetailItem(
                    severity=Severity.INFO,
                    name=clock_name,
                    line_number=0,
                    file_path=str(file_path),
                    reason="Expected ideal clock not found[WAIVED_AS_INFO]"
                ))
            
            # Extra unexpected clocks (would be FAIL, now INFO)
            for clock in self._ideal_clocks:
                if clock['name'] in extra:
                    details.append(DetailItem(
                        severity=Severity.INFO,
                        name=clock['name'],
                        line_number=clock['line_number'],
                        file_path=str(file_path),
                        reason="Unexpected ideal clock[WAIVED_AS_INFO]"
                    ))
            
            # Add waive_items as INFO with [WAIVED_INFO]
            if waive_items_raw:
                for item in waive_items_raw:
                    item_name = item.get('name', str(item)) if isinstance(item, dict) else str(item)
                    details.append(DetailItem(
                        severity=Severity.INFO,
                        name=item_name,
                        line_number=0,
                        file_path="N/A",
                        reason="Waive item[WAIVED_INFO]"
                    ))
            
            is_pass = True
        else:
            # Normal mode
            # Matched clocks
            for clock in self._ideal_clocks:
                if clock['name'] in matched:
                    details.append(DetailItem(
                        severity=Severity.INFO,
                        name=clock['name'],
                        line_number=clock['line_number'],
                        file_path=str(file_path),
                        reason="Expected ideal clock found"
                    ))
            
            # Missing expected clocks
            for clock_name in sorted(missing):
                details.append(DetailItem(
                    severity=Severity.FAIL,
                    name=clock_name,
                    line_number=0,
                    file_path=str(file_path),
                    reason="Expected ideal clock not found"
                ))
            
            # Extra unexpected clocks
            for clock in self._ideal_clocks:
                if clock['name'] in extra:
                    details.append(DetailItem(
                        severity=Severity.FAIL,
                        name=clock['name'],
                        line_number=clock['line_number'],
                        file_path=str(file_path),
                        reason="Unexpected ideal clock"
                    ))
            
            is_pass = (not missing and not extra)
        
        return create_check_result(
            value=len(matched),
            is_pass=is_pass,
            has_pattern_items=True,
            has_waiver_value=bool(waive_items_raw),
            details=details,
            item_desc=self.item_desc,
            default_group_desc="Ideal clock pattern matching"
        )
    
    def _execute_type3(self, file_path: Path) -> CheckResult:
        """Type 3: Pattern matching with waivers."""
        requirements = self.get_requirements()
        waivers = self.get_waivers()
        
        pattern_items = requirements.get('pattern_items', []) if requirements else []
        waive_items_raw = waivers.get('waive_items', []) if waivers else []
        waiver_value = waivers.get('value', 'N/A') if waivers else 'N/A'
        
        # Determine waiver tag based on waivers.value
        # Rule: Type 3 has waivers.value > 0 → all waive-related use [WAIVER]
        waived_tag = '[WAIVER]'
        unused_waiver_tag = '[WAIVER]'
        
        # Extract waive names
        waive_names = []
        for item in waive_items_raw:
            if isinstance(item, dict):
                waive_names.append(item.get('name', ''))
            else:
                waive_names.append(str(item))
        
        details = []
        found_clocks = {clock['name'] for clock in self._ideal_clocks}
        expected_clocks = set(pattern_items)
        waived_clocks = set(waive_names)
        
        matched_expected = expected_clocks & found_clocks
        matched_waived = waived_clocks & found_clocks
        missing_expected = expected_clocks - found_clocks
        unused_waivers = waived_clocks - found_clocks
        unexpected = found_clocks - expected_clocks - waived_clocks
        
        # Matched expected clocks
        for clock in self._ideal_clocks:
            if clock['name'] in matched_expected:
                details.append(DetailItem(
                    severity=Severity.INFO,
                    name=clock['name'],
                    line_number=clock['line_number'],
                    file_path=str(file_path),
                    reason="Expected ideal clock found"
                ))
        
        # Matched waived clocks
        for clock in self._ideal_clocks:
            if clock['name'] in matched_waived:
                reason = f"Ideal clock waived{waived_tag}" if waived_tag else "Ideal clock waived"
                details.append(DetailItem(
                    severity=Severity.INFO,
                    name=clock['name'],
                    line_number=clock['line_number'],
                    file_path=str(file_path),
                    reason=reason
                ))
        
        # Missing expected clocks
        for clock_name in sorted(missing_expected):
            details.append(DetailItem(
                severity=Severity.FAIL,
                name=clock_name,
                line_number=0,
                file_path=str(file_path),
                reason="Expected ideal clock not found"
            ))
        
        # Unexpected clocks
        for clock in self._ideal_clocks:
            if clock['name'] in unexpected:
                details.append(DetailItem(
                    severity=Severity.FAIL,
                    name=clock['name'],
                    line_number=clock['line_number'],
                    file_path=str(file_path),
                    reason="Unexpected ideal clock"
                ))
        
        # Unused waivers
        for clock_name in sorted(unused_waivers):
            reason = f"Waiver not used{unused_waiver_tag}" if unused_waiver_tag else "Waiver not used"
            details.append(DetailItem(
                severity=Severity.WARN,
                name=clock_name,
                line_number=0,
                file_path=str(file_path),
                reason=reason
            ))
        
        is_pass = (not missing_expected and not unexpected)
        
        # Build custom group descriptions
        error_groups = {}
        info_groups = {}
        warn_groups = {}
        
        if matched_expected:
            info_groups['INFO02'] = {
                'description': 'Expected ideal clocks found',
                'items': sorted(matched_expected)
            }
        
        if matched_waived:
            info_groups['INFO03'] = {
                'description': 'Ideal clocks waived',
                'items': sorted(matched_waived)
            }
        
        if missing_expected:
            error_groups['ERROR01'] = {
                'description': 'Expected ideal clocks missing',
                'items': sorted(missing_expected)
            }
        
        if unexpected:
            error_groups['ERROR02'] = {
                'description': 'Unexpected ideal clocks',
                'items': sorted(unexpected)
            }
        
        if unused_waivers:
            warn_groups['WARN01'] = {
                'description': 'Configured waivers not used',
                'items': sorted(unused_waivers)
            }
        
        return create_check_result(
            value=len(matched_expected),
            is_pass=is_pass,
            has_pattern_items=True,
            has_waiver_value=True,
            details=details,
            error_groups=error_groups if error_groups else None,
            info_groups=info_groups if info_groups else None,
            warn_groups=warn_groups if warn_groups else None,
            item_desc=self.item_desc
        )
    
    def _execute_type4(self, file_path: Path) -> CheckResult:
        """Type 4: Boolean check with waivers."""
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', []) if waivers else []
        waiver_value = waivers.get('value', 'N/A') if waivers else 'N/A'
        
        # Determine waiver tag based on waivers.value
        # Rule: Type 4 has waivers.value > 0 → all waive-related use [WAIVER]
        waived_tag = '[WAIVER]'
        unused_waiver_tag = '[WAIVER]'
        
        # Extract waive names
        waive_names = []
        for item in waive_items_raw:
            if isinstance(item, dict):
                waive_names.append(item.get('name', ''))
            else:
                waive_names.append(str(item))
        
        details = []
        found_clocks = {clock['name'] for clock in self._ideal_clocks}
        waived_clocks = set(waive_names)
        
        matched_waived = waived_clocks & found_clocks
        non_waived = found_clocks - waived_clocks
        unused_waivers = waived_clocks - found_clocks
        
        if not self._ideal_clocks:
            # No ideal clocks
            details.append(DetailItem(
                severity=Severity.INFO,
                name="No ideal clock networks found",
                line_number=0,
                file_path=str(file_path),
                reason="Check passed"
            ))
            
            # Report unused waivers
            for clock_name in sorted(waive_names):
                reason = f"Waiver not used{unused_waiver_tag}" if unused_waiver_tag else "Waiver not used"
                details.append(DetailItem(
                    severity=Severity.WARN,
                    name=clock_name,
                    line_number=0,
                    file_path=str(file_path),
                    reason=reason
                ))
            
            is_pass = True
        else:
            # Waived clocks
            for clock in self._ideal_clocks:
                if clock['name'] in matched_waived:
                    reason = f"Ideal clock waived{waived_tag}" if waived_tag else "Ideal clock waived"
                    details.append(DetailItem(
                        severity=Severity.INFO,
                        name=clock['name'],
                        line_number=clock['line_number'],
                        file_path=str(file_path),
                        reason=reason
                    ))
            
            # Non-waived clocks
            for clock in self._ideal_clocks:
                if clock['name'] in non_waived:
                    details.append(DetailItem(
                        severity=Severity.FAIL,
                        name=clock['name'],
                        line_number=clock['line_number'],
                        file_path=str(file_path),
                        reason="Ideal clock not waived"
                    ))
            
            # Unused waivers
            for clock_name in sorted(unused_waivers):
                reason = f"Waiver not used{unused_waiver_tag}" if unused_waiver_tag else "Waiver not used"
                details.append(DetailItem(
                    severity=Severity.WARN,
                    name=clock_name,
                    line_number=0,
                    file_path=str(file_path),
                    reason=reason
                ))
            
            is_pass = (not non_waived)
        
        # Build custom group descriptions
        error_groups = {}
        info_groups = {}
        warn_groups = {}
        
        if not self._ideal_clocks:
            info_groups['INFO01'] = {
                'description': 'No ideal clocks found',
                'items': []
            }
        
        if matched_waived:
            info_groups['INFO03'] = {
                'description': 'Ideal clocks waived',
                'items': sorted(matched_waived)
            }
        
        if non_waived:
            error_groups['ERROR01'] = {
                'description': 'Ideal clocks not waived',
                'items': sorted(non_waived)
            }
        
        if unused_waivers:
            warn_groups['WARN01'] = {
                'description': 'Configured waivers not used',
                'items': sorted(unused_waivers)
            }
        
        return create_check_result(
            value='N/A',
            is_pass=is_pass,
            has_pattern_items=False,
            has_waiver_value=True,
            details=details,
            error_groups=error_groups if error_groups else None,
            info_groups=info_groups if info_groups else None,
            warn_groups=warn_groups if warn_groups else None,
            item_desc=self.item_desc
        )


def get_checker_class():
    """Return the checker class for dynamic loading."""
    return IdealClockNetworkChecker


if __name__ == '__main__':
    checker = IdealClockNetworkChecker()
    checker.run()
