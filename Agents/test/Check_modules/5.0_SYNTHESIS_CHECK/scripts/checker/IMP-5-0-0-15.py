################################################################################
# Script Name: IMP-5-0-0-15.py
#
# Purpose:
#   Confirm all DFT checks pass in synthesis.
#   Parse synthesis log files for DFT rule violations.
#
# Logic:
#   - Parse synthesis log for "Checking DFT rules for" section
#   - Extract DFT violations with error types and violation details
#   - Support pattern matching for specific DFT violation types
#   - Support waiver logic for approved violations
#
# Auto Type Detection:
#   Type 1: requirements.value=N/A, waivers.value=N/A/0 → Boolean check
#   Type 2: requirements.value>0, pattern_items exists, waivers.value=N/A/0 → Value comparison
#   Type 3: requirements.value>0, pattern_items exists, waivers.value>0 → Value with waiver logic
#   Type 4: requirements.value=N/A, waivers.value>0 → Boolean with waiver logic
#
# Author: yyin
# Date: 2025-11-03
# Refactored: 2025-11-27 (Using BaseChecker for all 4 types)
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
from output_formatter import DetailItem, Severity, ResultType, create_check_result


class DFTCheckChecker(BaseChecker):
    """
    Unified checker for DFT violations that auto-detects and handles all 4 checker types.
    
    Check Target: Confirm all DFT checks pass in synthesis
    
    Type Detection Logic:
    - Type 1: requirements.value=N/A AND waivers.value=N/A/0
    - Type 2: requirements.value>0 AND pattern_items AND waivers.value=N/A/0
    - Type 3: requirements.value>0 AND pattern_items AND waivers.value>0
    - Type 4: requirements.value=N/A AND waivers.value>0
    
    Violation Format:
    - "error_type:violation_description"
    - Example: "DFT Async Rule Violation:Asynchronous pin set/reset of sequential cell..."
    """
    
    def __init__(self):
        super().__init__(
            check_module="5.0_SYNTHESIS_CHECK",
            item_id="IMP-5-0-0-15",
            item_desc="Confirm all DFT checks pass?"
        )
        
        # Store violation metadata for detailed reporting
        self._violation_metadata: Dict[str, Dict[str, Any]] = {}
    
    def execute_check(self) -> CheckResult:
        """
        Main execution logic that automatically detects checker type.
        
        Returns:
            CheckResult object with pass/fail status and details
        """
        try:
            # Parse input files
            all_violations = self._parse_dft_log()
            
            if not all_violations:
                # No violations found - always pass
                return create_check_result(
                    value=0,
                    is_pass=True,
                    has_pattern_items=False,
                    has_waiver_value=False,
                    details=[],
                    info_groups={"INFO01": {"description": "All DFT checks pass", "items": []}},
                    item_desc=self.item_desc
                )
            
            # Auto-detect checker type
            checker_type = self.detect_checker_type()
            
            # Get forbidden patterns if type 2 or 3
            forbidden_patterns = []
            if checker_type in [2, 3]:
                forbidden_patterns = self.item_data.get('requirements', {}).get('pattern_items', [])
            
            # Find violations matching forbidden patterns
            violations_matched = self._find_violations(all_violations, forbidden_patterns)
            
            # Execute based on detected type
            if checker_type == 1:
                return self._execute_type1(all_violations, violations_matched)
            elif checker_type == 2:
                return self._execute_type2(all_violations, violations_matched)
            elif checker_type == 3:
                return self._execute_type3(all_violations, violations_matched)
            elif checker_type == 4:
                return self._execute_type4(all_violations, violations_matched)
        except ConfigurationError as e:
            return e.check_result
        else:
            raise ValueError(f"Unknown checker type: {checker_type}")
    
    def _parse_dft_log(self) -> List[str]:
        """
        Parse synthesis log file for DFT violations.
        
        Returns:
            List of violation names in format "error_type:description"
        """
        input_files = self.item_data.get('input_files', [])
        if not input_files:
            return []
        
        # Use first log file
        log_file = Path(input_files[0])
        if not log_file.exists():
            return []
        
        log_lines = self.read_file(log_file)
        if not log_lines:
            return []
        
        # Parse DFT violations
        violations = self._parse_dft_violations(log_lines, str(log_file))
        
        # Extract violation names for matching
        violation_names = []
        for v in violations:
            violation_name = f"{v['error_type']}:{v['error_point']}"
            violation_names.append(violation_name)
            
            # Store metadata for detailed reporting
            self._violation_metadata[violation_name] = {
                'error_type': v['error_type'],
                'description': v['error_point'],
                'vid_id': v.get('vid_id', ''),
                'line_number': v['line_num'],
                'file_path': str(log_file)
            }
        
        return violation_names
    
    def _parse_dft_violations(self, log_lines: List[str], log_path: str) -> List[Dict]:
        """
        Parse DFT violations from log file.
        
        Args:
            log_lines: Lines from synthesis log file
            log_path: Path to log file
            
        Returns:
            List of violation dicts with keys:
            - error_type: Type of DFT violation
            - error_point: Violation description
            - vid_id: vid identifier (optional)
            - line_num: Line number in log file
        """
        violations = []
        in_dft_section = False
        current_error_type = None
        
        # Patterns
        section_start_pattern = re.compile(r'Checking DFT rules for')
        error_pattern = re.compile(r'Error\s*:\s*(DFT\s+\w+\s+Rule\s+Violation)', re.IGNORECASE)
        # Pattern to capture full description after vid
        vid_pattern = re.compile(r':\s*#\s*\d+\s*<(vid\s+\d+_\w+)>:\s*(.+?)(?:\s+\[[\w-]+\])?$')
        
        for line_num, line in enumerate(log_lines, start=1):
            # Detect DFT section start
            if section_start_pattern.search(line):
                in_dft_section = True
                continue
            
            if not in_dft_section:
                continue
            
            # Detect error type
            error_match = error_pattern.search(line)
            if error_match:
                current_error_type = error_match.group(1).strip()
                continue
            
            # Extract vid details with full description
            if current_error_type:
                vid_match = vid_pattern.search(line)
                if vid_match:
                    vid_id = vid_match.group(1).strip()  # e.g., "vid 0_async"
                    description = vid_match.group(2).strip()  # Full description
                    violations.append({
                        'error_type': current_error_type,
                        'error_point': description,  # Use full description
                        'vid_id': vid_id,
                        'line_num': line_num
                    })
        
        return violations
    
    def _match_forbidden_error(self, violation_name: str, patterns: List[str]) -> Optional[str]:
        """
        Check if violation matches any forbidden pattern.
        
        Args:
            violation_name: Full violation name "error_type:description"
            patterns: List of patterns to match against
        
        Returns:
            Matched pattern string or None
        """
        return self.match_pattern(violation_name, patterns)
    
    def _find_violations(self, all_violations: List[str], 
                        forbidden_patterns: List[str]) -> List[Tuple[str, str]]:
        """
        Find violations matching forbidden patterns.
        
        Args:
            all_violations: All DFT violations
            forbidden_patterns: Patterns to match (for Type 2/3)
        
        Returns:
            List of (violation_name, matched_pattern) tuples
        """
        if not forbidden_patterns:
            return []
        
        matched = []
        for violation in all_violations:
            pattern_matched = self._match_forbidden_error(violation, forbidden_patterns)
            if pattern_matched:
                matched.append((violation, pattern_matched))
        
        return matched
    
    def _execute_type1(self, all_violations: List[str], 
                      violations_matched: List[Tuple[str, str]]) -> CheckResult:
        """
        Type 1: Boolean check (no pattern, no waiver).
        
        Args:
            all_violations: All DFT violations found
            violations_matched: Not used in Type 1
        
        Returns:
            CheckResult with PASS/FAIL
        """
        waivers = self.item_data.get('waivers', {})
        waiver_value = waivers.get('value', 'N/A')
        
        # Build details list
        details = []
        for violation_name in all_violations:
            metadata = self._violation_metadata.get(violation_name, {})
            error_type = metadata.get('error_type', 'Unknown DFT Error')
            description = metadata.get('description', violation_name)
            
            # Add [WAIVED_AS_INFO] tag when waiver=0
            reason = f"{error_type}[WAIVED_AS_INFO]" if str(waiver_value) == '0' else error_type
            
            details.append(DetailItem(
                severity=Severity.FAIL if str(waiver_value) != '0' else Severity.INFO,
                name=description,
                line_number=str(metadata.get('line_number', '')),
                file_path=metadata.get('file_path', ''),
                reason=reason
            ))
        
        # Check for waiver_value = 0 (force pass)
        if str(waiver_value) == '0':
            # All violations become INFO
            info_groups = self._create_error_type_info_groups(all_violations, 
                                                               "All DFT violations ignored (waiver=0)")
            return create_check_result(
                value=0,
                is_pass=True,
                has_pattern_items=False,
                has_waiver_value=True,
                details=details,
                info_groups=info_groups,
                item_desc=self.item_desc
            )
        
        # Standard Type 1: any violation = FAIL
        if all_violations:
            error_groups = self._create_error_type_error_groups(all_violations)
            return create_check_result(
                value=len(all_violations),
                is_pass=False,
                has_pattern_items=False,
                has_waiver_value=False,
                details=details,
                error_groups=error_groups,
                item_desc=self.item_desc
            )
        else:
            return create_check_result(
                value=0,
                is_pass=True,
                has_pattern_items=False,
                has_waiver_value=False,
                details=[],
                info_groups={"INFO01": {"description": "All DFT checks pass", "items": []}},
                item_desc=self.item_desc
            )
    
    def _execute_type2(self, all_violations: List[str], 
                      violations_matched: List[Tuple[str, str]]) -> CheckResult:
        """
        Type 2: Value comparison (pattern, no waiver).
        
        Args:
            all_violations: All violations found
            violations_matched: List of (violation, pattern) tuples
        
        Returns:
            CheckResult with comparison result
        """
        requirements = self.item_data.get('requirements', {})
        expected_value = requirements.get('value', 0)
        forbidden_patterns = requirements.get('pattern_items', [])
        
        waivers = self.item_data.get('waivers', {})
        waiver_value = waivers.get('value', 'N/A')
        
        actual_count = len(violations_matched)
        
        # Build details list
        details = []
        for violation_name, pattern in violations_matched:
            metadata = self._violation_metadata.get(violation_name, {})
            error_type = metadata.get('error_type', 'Unknown DFT Error')
            description = metadata.get('description', violation_name)
            
            # Add [WAIVED_AS_INFO] tag when waiver=0
            if str(waiver_value) == '0':
                reason = f"{error_type}[WAIVED_AS_INFO]"
                severity = Severity.INFO
            else:
                reason = error_type
                severity = Severity.FAIL if actual_count != expected_value else Severity.INFO
            
            details.append(DetailItem(
                severity=severity,
                name=description,
                line_number=str(metadata.get('line_number', '')),
                file_path=metadata.get('file_path', ''),
                reason=reason
            ))
        
        # Check waiver=0 (force pass, all to INFO)
        if str(waiver_value) == '0':
            info_groups = {}
            if violations_matched:
                info_groups = self._create_error_type_info_groups(
                    [v[0] for v in violations_matched],
                    "Violations ignored (waiver=0)"
                )
            else:
                info_groups["INFO01"] = {
                    "description": "No violations found matching patterns (good)",
                    "items": []
                }
            
            return create_check_result(
                value=actual_count,
                is_pass=True,
                has_pattern_items=True,
                has_waiver_value=True,
                details=[],
                info_groups=info_groups,
                item_desc=self.item_desc
            )
        
        # Standard Type 2: compare actual vs expected
        if actual_count == expected_value:
            # PASS: actual matches expected
            info_groups = {}
            if actual_count == 0:
                info_groups["INFO01"] = {
                    "description": "No violations found matching patterns (expected)",
                    "items": []
                }
            else:
                info_groups = self._create_error_type_info_groups(
                    [v[0] for v in violations_matched],
                    f"Expected violations (count={expected_value})"
                )
            
            return create_check_result(
                value=actual_count,
                is_pass=True,
                has_pattern_items=True,
                has_waiver_value=False,
                details=[],
                info_groups=info_groups,
                item_desc=self.item_desc
            )
        else:
            # FAIL: mismatch
            error_groups = self._create_error_type_error_groups([v[0] for v in violations_matched])
            
            return create_check_result(
                value=actual_count,
                is_pass=False,
                has_pattern_items=True,
                has_waiver_value=False,
                details=[],
                error_groups=error_groups,
                item_desc=self.item_desc
            )
    
    def _execute_type3(self, all_violations: List[str], 
                      violations_matched: List[Tuple[str, str]]) -> CheckResult:
        """
        Type 3: Value comparison with waiver logic.
        
        Args:
            all_violations: All violations found
            violations_matched: List of (violation, pattern) tuples
        
        Returns:
            CheckResult with waiver analysis
        """
        requirements = self.item_data.get('requirements', {})
        expected_value = requirements.get('value', 0)
        
        # Get waiver items
        waive_items_dict = self._get_waive_items_with_reasons()
        
        # Separate matched violations into waived and unwaived
        waived_violations = []
        unwaived_violations = []
        
        for violation_name, pattern in violations_matched:
            if violation_name in waive_items_dict:
                waived_violations.append(violation_name)
            else:
                unwaived_violations.append(violation_name)
        
        # Check for unused waivers
        used_waivers = set(waived_violations)
        all_waivers = set(waive_items_dict.keys())
        unused_waivers = all_waivers - used_waivers
        
        # Build result
        unwaived_count = len(unwaived_violations)
        
        error_groups = {}
        info_groups = {}
        warn_groups = {}
        
        # Unwaived violations = ERROR
        if unwaived_violations:
            error_groups = self._create_error_type_error_groups(unwaived_violations)
        
        # Waived violations = INFO
        if waived_violations:
            info_groups_waived = self._create_error_type_info_groups(waived_violations, "Waived")
            for key, value in info_groups_waived.items():
                info_groups[key] = value
        
        # Unmatched patterns (no violations found) = INFO
        if not violations_matched:
            info_groups["INFO99"] = {
                "description": "No violations found matching patterns (good)",
                "items": []
            }
        
        # Unused waivers = WARN
        if unused_waivers:
            warn_groups["WARN01"] = {
                "description": "Unused waivers (not found in actual violations)",
                "items": list(unused_waivers)
            }
        
        # Determine PASS/FAIL
        is_pass = (unwaived_count == 0)
        value = len(violations_matched)
        
        return create_check_result(
            value=value,
            is_pass=is_pass,
            has_pattern_items=True,
            has_waiver_value=True,
            details=[],
            error_groups=error_groups,
            info_groups=info_groups,
            warn_groups=warn_groups,
            item_desc=self.item_desc
        )
    
    def _execute_type4(self, all_violations: List[str], 
                      violations_matched: List[Tuple[str, str]]) -> CheckResult:
        """
        Type 4: Boolean with waiver logic.
        
        Args:
            all_violations: All violations found
            violations_matched: Not used in Type 4
        
        Returns:
            CheckResult with waiver analysis
        """
        # Get waiver items
        waive_items_dict = self._get_waive_items_with_reasons()
        
        # Separate violations into waived and unwaived
        waived_violations = []
        unwaived_violations = []
        
        for violation in all_violations:
            if violation in waive_items_dict:
                waived_violations.append(violation)
            else:
                unwaived_violations.append(violation)
        
        # Check for unused waivers
        used_waivers = set(waived_violations)
        all_waivers = set(waive_items_dict.keys())
        unused_waivers = all_waivers - used_waivers
        
        # Build result
        error_groups = {}
        info_groups = {}
        warn_groups = {}
        
        # Unwaived violations = ERROR
        if unwaived_violations:
            error_groups = self._create_error_type_error_groups(unwaived_violations)
        
        # Waived violations = INFO
        if waived_violations:
            info_groups = self._create_error_type_info_groups(waived_violations, "Waived")
        
        # No violations at all
        if not all_violations:
            info_groups["INFO01"] = {
                "description": "All DFT checks pass",
                "items": []
            }
        
        # Unused waivers = WARN
        if unused_waivers:
            warn_groups["WARN01"] = {
                "description": "Unused waivers (not found in actual violations)",
                "items": list(unused_waivers)
            }
        
        # Determine PASS/FAIL
        is_pass = (len(unwaived_violations) == 0)
        value = "N/A"
        
        return create_check_result(
            value=value,
            is_pass=is_pass,
            has_pattern_items=False,
            has_waiver_value=True,
            details=[],
            error_groups=error_groups,
            info_groups=info_groups,
            warn_groups=warn_groups,
            item_desc=self.item_desc
        )
    
    def _get_waive_items_with_reasons(self) -> Dict[str, str]:
        """
        Extract waiver items with their reasons from configuration.
        
        Returns:
            Dictionary mapping violation_name -> reason
        """
        waivers = self.item_data.get('waivers', {})
        waive_items = waivers.get('waive_items', [])
        
        if not waive_items:
            return {}
        
        waive_dict = {}
        
        # Support both dict format and string format
        for item in waive_items:
            if isinstance(item, dict):
                # Dict format: {name: "...", reason: "..."}
                name = item.get('name', '')
                reason = item.get('reason', 'No reason provided')
                if name:
                    waive_dict[name] = reason
            elif isinstance(item, str):
                # String format: "violation_name , #reason"
                parts = item.split(',', 1)
                name = parts[0].strip()
                reason = parts[1].strip().lstrip('#').strip() if len(parts) > 1 else 'No reason provided'
                if name:
                    waive_dict[name] = reason
        
        return waive_dict
    
    def _group_by_error_type(self, violations: List[str]) -> Dict[str, List[str]]:
        """
        Group violations by error type.
        
        Args:
            violations: List of violation names "error_type:description"
        
        Returns:
            Dictionary mapping error_type -> list of descriptions
        """
        grouped = {}
        
        for violation in violations:
            if ':' in violation:
                error_type, description = violation.split(':', 1)
            else:
                error_type = "Unknown DFT Error"
                description = violation
            
            if error_type not in grouped:
                grouped[error_type] = []
            grouped[error_type].append(description)
        
        return grouped
    
    def _create_error_type_error_groups(self, violations: List[str]) -> Dict[str, Dict]:
        """
        Create ERROR groups grouped by error type.
        
        Args:
            violations: List of violation names
        
        Returns:
            Dictionary of error groups
        """
        grouped = self._group_by_error_type(violations)
        
        error_groups = {}
        for idx, (error_type, descriptions) in enumerate(sorted(grouped.items()), start=1):
            error_code = f"ERROR{idx:02d}"
            error_groups[error_code] = {
                "description": error_type,
                "items": descriptions
            }
        
        return error_groups
    
    def _create_error_type_info_groups(self, violations: List[str], 
                                       prefix: str = "") -> Dict[str, Dict]:
        """
        Create INFO groups grouped by error type.
        
        Args:
            violations: List of violation names
            prefix: Prefix for description (e.g., "Waived")
        
        Returns:
            Dictionary of info groups
        """
        grouped = self._group_by_error_type(violations)
        
        info_groups = {}
        for idx, (error_type, descriptions) in enumerate(sorted(grouped.items()), start=1):
            info_code = f"INFO{idx:02d}"
            description = f"{prefix}: {error_type}" if prefix else error_type
            info_groups[info_code] = {
                "description": description,
                "items": descriptions
            }
        
        return info_groups
    
    def format_details(self, result: CheckResult) -> List[str]:
        """
        Format detailed output for report file.
        
        Args:
            result: CheckResult object
        
        Returns:
            List of formatted detail lines
        """
        lines = []
        
        # Use base formatter for most content
        base_lines = super().format_details(result)
        
        # For DFT violations, we want to add metadata details
        for line in base_lines:
            lines.append(line)
            
            # If this is a violation line, add metadata
            if line.strip() and not line.startswith(('PASS:', 'FAIL:', 'Fail Occurrence:', 
                                                      'Info Occurrence:', 'Warn Occurrence:',
                                                      'Value:')):
                # Extract violation name from line
                # Format: "1: Fail: description. In line X, file"
                # or "1: Info: description. ..."
                match = re.search(r'(?:Fail|Info|Warn):\s*(.+?)\.\s+In line', line)
                if match:
                    description = match.group(1).strip()
                    
                    # Find matching metadata
                    for violation_name, metadata in self._violation_metadata.items():
                        if metadata['description'] == description:
                            # Add vid_id if available
                            if metadata.get('vid_id'):
                                lines.append(f"      vid: {metadata['vid_id']}")
                            break
        
        return lines


def run():
    """Main entry point."""
    checker = DFTCheckChecker()
    checker.init_checker(script_path=Path(__file__))
    result = checker.execute_check()
    checker.write_output(result)


if __name__ == '__main__':
    run()

