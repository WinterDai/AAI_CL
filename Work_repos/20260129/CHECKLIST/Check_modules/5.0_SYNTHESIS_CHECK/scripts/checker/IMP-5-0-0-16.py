################################################################################
# Script Name: IMP-5-0-0-16.py
#
# Purpose:
#   Confirm CPF/UPF file has passed Conformal LP quality checks pre-synthesis.
#   Parse verify_power_structure_pre_synth.rpt for Severity: Error issues.
#
# Logic:
#   - Parse power structure verification report
#   - Extract ONLY "Severity: Error" issues (ignore Warnings/Infos)
#   - Support pattern matching for specific error types
#   - Support waiver logic for approved errors
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


class PowerStructureChecker(BaseChecker):
    """
    Unified checker for power structure verification that auto-detects and handles all 4 checker types.
    
    Check Target: Confirm CPF/UPF file has passed Conformal LP quality checks
    
    Type Detection Logic:
    - Type 1: requirements.value=N/A AND waivers.value=N/A/0
    - Type 2: requirements.value>0 AND pattern_items AND waivers.value=N/A/0
    - Type 3: requirements.value>0 AND pattern_items AND waivers.value>0
    - Type 4: requirements.value=N/A AND waivers.value>0
    
    Error Format:
    - "issue_name:detail_description"
    - Example: "UPF_DOMAIN_VOLTAGE_MISSING:Power domain PD1 missing voltage specification"
    """
    
    def __init__(self):
        super().__init__(
            check_module="5.0_SYNTHESIS_CHECK",
            item_id="IMP-5-0-0-16",
            item_desc="Confirm CPF/UPF file  has passed Conformal LP quality checks against RTL prior to synthesis?"
        )
        
        # Store error metadata for detailed reporting
        self._error_metadata: Dict[str, Dict[str, Any]] = {}
    
    def execute_check(self) -> CheckResult:
        """
        Main execution logic that automatically detects checker type.
        
        Returns:
            CheckResult object with pass/fail status and details
        """
        try:
            # Parse input files
            all_errors = self._parse_power_structure_report()
            
            if not all_errors:
                # No errors found - always pass
                return create_check_result(
                    value=0,
                    is_pass=True,
                    has_pattern_items=False,
                    has_waiver_value=False,
                    details=[],
                    info_groups={"INFO01": {"description": "CPF/UPF file has passed Conformal LP quality checks", "items": []}},
                    item_desc=self.item_desc
                )
            
            # Auto-detect checker type
            checker_type = self.detect_checker_type()
            
            # Get forbidden patterns if type 2 or 3
            forbidden_patterns = []
            if checker_type in [2, 3]:
                forbidden_patterns = self.item_data.get('requirements', {}).get('pattern_items', [])
            
            # Find errors matching forbidden patterns
            errors_matched = self._find_errors(all_errors, forbidden_patterns)
            
            # Execute based on detected type
            if checker_type == 1:
                return self._execute_type1(all_errors, errors_matched)
            elif checker_type == 2:
                return self._execute_type2(all_errors, errors_matched)
            elif checker_type == 3:
                return self._execute_type3(all_errors, errors_matched)
            elif checker_type == 4:
                return self._execute_type4(all_errors, errors_matched)
            else:
                raise ValueError(f"Unknown checker type: {checker_type}")
        except ConfigurationError as e:
            return e.check_result
    
    def _parse_power_structure_report(self) -> List[str]:
        """
        Parse power structure verification report for Severity: Error issues.
        
        Returns:
            List of error names in format "issue_name:detail_description"
        """
        input_files = self.item_data.get('input_files', [])
        if not input_files:
            return []
        
        all_errors = []
        
        for report_path_str in input_files:
            report_path = Path(report_path_str)
            if not report_path.exists():
                continue
            
            lines = self.read_file(report_path)
            if not lines:
                continue
            
            # Parse errors
            errors = self._parse_error_issues(lines, str(report_path))
            
            # Extract error names and store metadata
            for err in errors:
                error_name = f"{err['issue_name']}:{err['detail']}"
                all_errors.append(error_name)
                
                # Store metadata
                self._error_metadata[error_name] = {
                    'issue_name': err['issue_name'],
                    'issue_desc': err['issue_desc'],
                    'detail': err['detail'],
                    'line_number': err['line_number'],
                    'file_path': str(report_path)
                }
        
        return all_errors
    
    def _parse_error_issues(self, lines: List[str], report_path: str) -> List[Dict]:
        """
        Parse error issues from report lines.
        
        Report Format:
            ISSUE_NAME: Brief description
            Severity: Error  Occurrence: N  Type: TYPE
                1: Detail point 1
                2: Detail point 2
        
        Args:
            lines: Report file lines
            report_path: Path to report file
            
        Returns:
            List of error dicts with keys:
            - issue_name: Issue identifier
            - issue_desc: Issue description
            - detail: Detail point text
            - line_number: Line number in report
        """
        errors = []
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            
            # Match issue header: "ISSUE_NAME: Description"
            name_match = re.match(r'^([A-Z][A-Z0-9_\.]+)\s*:\s*(.+)$', line)
            if name_match:
                issue_name = name_match.group(1)
                issue_desc = name_match.group(2).strip()
                
                # Check next line for severity metadata
                if i + 1 < len(lines):
                    meta_line = lines[i + 1]
                    sev_match = re.search(r'Severity\s*:\s*(\w+)', meta_line, re.IGNORECASE)
                    
                    # Only process "Severity: Error" issues
                    if sev_match and sev_match.group(1).lower() == 'error':
                        # Extract detail points (lines with "N: detail text")
                        j = i + 2
                        found_details = False
                        
                        while j < len(lines):
                            detail_line = lines[j].strip()
                            
                            # Stop at next issue or empty line
                            if not detail_line or re.match(r'^[A-Z][A-Z0-9_\.]+\s*:', detail_line):
                                break
                            
                            # Match detail point: "N: detail text"
                            point_match = re.match(r'^(\d+):\s*(.+)$', detail_line)
                            if point_match:
                                errors.append({
                                    'issue_name': issue_name,
                                    'issue_desc': issue_desc,
                                    'detail': point_match.group(2).strip(),
                                    'line_number': j + 1
                                })
                                found_details = True
                            j += 1
                        
                        # If no detail points found, add issue name itself
                        if not found_details:
                            errors.append({
                                'issue_name': issue_name,
                                'issue_desc': issue_desc,
                                'detail': issue_desc,
                                'line_number': i + 1
                            })
                        
                        i = j - 1  # Skip processed lines
            i += 1
        
        return errors
    
    def _match_forbidden_error(self, error_name: str, patterns: List[str]) -> Optional[str]:
        """
        Check if error matches any forbidden pattern.
        
        Args:
            error_name: Full error name "issue_name:detail"
            patterns: List of patterns to match against
        
        Returns:
            Matched pattern string or None
        """
        return self.match_pattern(error_name, patterns)
    
    def _find_errors(self, all_errors: List[str], 
                    forbidden_patterns: List[str]) -> List[Tuple[str, str]]:
        """
        Find errors matching forbidden patterns.
        
        Args:
            all_errors: All power structure errors
            forbidden_patterns: Patterns to match (for Type 2/3)
        
        Returns:
            List of (error_name, matched_pattern) tuples
        """
        if not forbidden_patterns:
            return []
        
        matched = []
        for error in all_errors:
            pattern_matched = self._match_forbidden_error(error, forbidden_patterns)
            if pattern_matched:
                matched.append((error, pattern_matched))
        
        return matched
    
    def _execute_type1(self, all_errors: List[str], 
                      errors_matched: List[Tuple[str, str]]) -> CheckResult:
        """
        Type 1: Boolean check (no pattern, no waiver).
        
        Args:
            all_errors: All power structure errors found
            errors_matched: Not used in Type 1
        
        Returns:
            CheckResult with PASS/FAIL
        """
        waivers = self.item_data.get('waivers', {})
        waiver_value = waivers.get('value', 'N/A')
        
        # Build details list
        details = []
        for error_name in all_errors:
            metadata = self._error_metadata.get(error_name, {})
            issue_desc = metadata.get('issue_desc', '')
            detail_text = metadata.get('detail', error_name)
            
            # Add [WAIVED_AS_INFO] tag when waiver=0
            reason = f"{issue_desc}[WAIVED_AS_INFO]" if str(waiver_value) == '0' else issue_desc
            
            details.append(DetailItem(
                severity=Severity.FAIL if str(waiver_value) != '0' else Severity.INFO,
                name=detail_text,
                line_number=str(metadata.get('line_number', '')),
                file_path=metadata.get('file_path', ''),
                reason=reason
            ))
        
        # Check for waiver_value = 0 (force pass)
        if str(waiver_value) == '0':
            # All errors become INFO
            info_groups = self._create_issue_info_groups(all_errors, 
                                                         "All errors ignored (waiver=0)")
            return create_check_result(
                value=0,
                is_pass=True,
                has_pattern_items=False,
                has_waiver_value=True,
                details=details,
                info_groups=info_groups,
                item_desc=self.item_desc
            )
        
        # Standard Type 1: any error = FAIL
        if all_errors:
            error_groups = self._create_issue_error_groups(all_errors)
            return create_check_result(
                value=len(all_errors),
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
                info_groups={"INFO01": {"description": "CPF/UPF file has passed Conformal LP quality checks", "items": []}},
                item_desc=self.item_desc
            )
    
    def _execute_type2(self, all_errors: List[str], 
                      errors_matched: List[Tuple[str, str]]) -> CheckResult:
        """
        Type 2: Value comparison (pattern, no waiver).
        
        Args:
            all_errors: All errors found
            errors_matched: List of (error, pattern) tuples
        
        Returns:
            CheckResult with comparison result
        """
        requirements = self.item_data.get('requirements', {})
        expected_value = requirements.get('value', 0)
        
        waivers = self.item_data.get('waivers', {})
        waiver_value = waivers.get('value', 'N/A')
        
        actual_count = len(errors_matched)
        
        # Build details list
        details = []
        for error_name, pattern in errors_matched:
            metadata = self._error_metadata.get(error_name, {})
            issue_desc = metadata.get('issue_desc', '')
            detail_text = metadata.get('detail', error_name)
            
            severity = Severity.FAIL if str(waiver_value) != '0' and actual_count != expected_value else Severity.INFO
            # Add [WAIVED_AS_INFO] tag when waiver=0
            reason = f"{issue_desc}[WAIVED_AS_INFO]" if str(waiver_value) == '0' else issue_desc
            details.append(DetailItem(
                severity=severity,
                name=detail_text,
                line_number=str(metadata.get('line_number', '')),
                file_path=metadata.get('file_path', ''),
                reason=reason
            ))
        
        # Check waiver=0 (force pass, all to INFO)
        if str(waiver_value) == '0':
            info_groups = {}
            if errors_matched:
                info_groups = self._create_issue_info_groups(
                    [e[0] for e in errors_matched],
                    "Errors ignored (waiver=0)"
                )
            else:
                info_groups["INFO01"] = {
                    "description": "No errors found matching patterns (good)",
                    "items": []
                }
            
            return create_check_result(
                value=actual_count,
                is_pass=True,
                has_pattern_items=True,
                has_waiver_value=True,
                details=details,
                info_groups=info_groups,
                item_desc=self.item_desc
            )
        
        # Standard Type 2: compare actual vs expected
        if actual_count == expected_value:
            # PASS: actual matches expected
            info_groups = {}
            if actual_count == 0:
                info_groups["INFO01"] = {
                    "description": "No errors found matching patterns (expected)",
                    "items": []
                }
            else:
                info_groups = self._create_issue_info_groups(
                    [e[0] for e in errors_matched],
                    f"Expected errors (count={expected_value})"
                )
            
            return create_check_result(
                value=actual_count,
                is_pass=True,
                has_pattern_items=True,
                has_waiver_value=False,
                details=details,
                info_groups=info_groups,
                item_desc=self.item_desc
            )
        else:
            # FAIL: mismatch
            error_groups = self._create_issue_error_groups([e[0] for e in errors_matched])
            
            return create_check_result(
                value=actual_count,
                is_pass=False,
                has_pattern_items=True,
                has_waiver_value=False,
                details=details,
                error_groups=error_groups,
                item_desc=self.item_desc
            )
    
    def _execute_type3(self, all_errors: List[str], 
                      errors_matched: List[Tuple[str, str]]) -> CheckResult:
        """
        Type 3: Value comparison with waiver logic.
        
        Args:
            all_errors: All errors found
            errors_matched: List of (error, pattern) tuples
        
        Returns:
            CheckResult with waiver analysis
        """
        requirements = self.item_data.get('requirements', {})
        expected_value = requirements.get('value', 0)
        
        # Get waiver items
        waive_items_dict = self._get_waive_items_with_reasons()
        
        # Separate matched errors into waived and unwaived
        waived_errors = []
        unwaived_errors = []
        
        for error_name, pattern in errors_matched:
            if error_name in waive_items_dict:
                waived_errors.append(error_name)
            else:
                unwaived_errors.append(error_name)
        
        # Check for unused waivers
        used_waivers = set(waived_errors)
        all_waivers = set(waive_items_dict.keys())
        unused_waivers = all_waivers - used_waivers
        
        # Build details list
        details = []
        for error_name, pattern in errors_matched:
            metadata = self._error_metadata.get(error_name, {})
            issue_desc = metadata.get('issue_desc', '')
            detail_text = metadata.get('detail', error_name)
            
            severity = Severity.FAIL if error_name in unwaived_errors else Severity.INFO
            details.append(DetailItem(
                severity=severity,
                name=detail_text,
                line_number=str(metadata.get('line_number', '')),
                file_path=metadata.get('file_path', ''),
                reason=issue_desc
            ))
        
        # Build result
        unwaived_count = len(unwaived_errors)
        
        error_groups = {}
        info_groups = {}
        warn_groups = {}
        
        # Unwaived errors = ERROR
        if unwaived_errors:
            error_groups = self._create_issue_error_groups(unwaived_errors)
        
        # Waived errors = INFO
        if waived_errors:
            info_groups_waived = self._create_issue_info_groups(waived_errors, "Waived")
            for key, value in info_groups_waived.items():
                info_groups[key] = value
        
        # Unmatched patterns (no errors found) = INFO
        if not errors_matched:
            info_groups["INFO99"] = {
                "description": "No errors found matching patterns (good)",
                "items": []
            }
        
        # Unused waivers = WARN
        if unused_waivers:
            warn_groups["WARN01"] = {
                "description": "Unused waivers (not found in actual errors)",
                "items": list(unused_waivers)
            }
        
        # Determine PASS/FAIL
        is_pass = (unwaived_count == 0)
        value = len(errors_matched)
        
        return create_check_result(
            value=value,
            is_pass=is_pass,
            has_pattern_items=True,
            has_waiver_value=True,
            details=details,
            error_groups=error_groups,
            info_groups=info_groups,
            warn_groups=warn_groups,
            item_desc=self.item_desc
        )
    
    def _execute_type4(self, all_errors: List[str], 
                      errors_matched: List[Tuple[str, str]]) -> CheckResult:
        """
        Type 4: Boolean with waiver logic.
        
        Args:
            all_errors: All errors found
            errors_matched: Not used in Type 4
        
        Returns:
            CheckResult with waiver analysis
        """
        # Get waiver items
        waive_items_dict = self._get_waive_items_with_reasons()
        
        # Separate errors into waived and unwaived
        waived_errors = []
        unwaived_errors = []
        
        for error in all_errors:
            if error in waive_items_dict:
                waived_errors.append(error)
            else:
                unwaived_errors.append(error)
        
        # Check for unused waivers
        used_waivers = set(waived_errors)
        all_waivers = set(waive_items_dict.keys())
        unused_waivers = all_waivers - used_waivers
        
        # Build details list
        details = []
        for error_name in all_errors:
            metadata = self._error_metadata.get(error_name, {})
            issue_desc = metadata.get('issue_desc', '')
            detail_text = metadata.get('detail', error_name)
            
            severity = Severity.FAIL if error_name in unwaived_errors else Severity.INFO
            details.append(DetailItem(
                severity=severity,
                name=detail_text,
                line_number=str(metadata.get('line_number', '')),
                file_path=metadata.get('file_path', ''),
                reason=issue_desc
            ))
        
        # Build result
        error_groups = {}
        info_groups = {}
        warn_groups = {}
        
        # Unwaived errors = ERROR
        if unwaived_errors:
            error_groups = self._create_issue_error_groups(unwaived_errors)
        
        # Waived errors = INFO
        if waived_errors:
            info_groups = self._create_issue_info_groups(waived_errors, "Waived")
        
        # No errors at all
        if not all_errors:
            info_groups["INFO01"] = {
                "description": "CPF/UPF file has passed Conformal LP quality checks",
                "items": []
            }
        
        # Unused waivers = WARN
        if unused_waivers:
            warn_groups["WARN01"] = {
                "description": "Unused waivers (not found in actual errors)",
                "items": list(unused_waivers)
            }
        
        # Determine PASS/FAIL
        is_pass = (len(unwaived_errors) == 0)
        value = "N/A"
        
        return create_check_result(
            value=value,
            is_pass=is_pass,
            has_pattern_items=False,
            has_waiver_value=True,
            details=details,
            error_groups=error_groups,
            info_groups=info_groups,
            warn_groups=warn_groups,
            item_desc=self.item_desc
        )
    
    def _get_waive_items_with_reasons(self) -> Dict[str, str]:
        """
        Extract waiver items with their reasons from configuration.
        
        Returns:
            Dictionary mapping error_name -> reason
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
                # String format: "error_name , #reason"
                parts = item.split(',', 1)
                name = parts[0].strip()
                reason = parts[1].strip().lstrip('#').strip() if len(parts) > 1 else 'No reason provided'
                if name:
                    waive_dict[name] = reason
        
        return waive_dict
    
    def _group_by_issue(self, errors: List[str]) -> Dict[str, List[str]]:
        """
        Group errors by issue name.
        
        Args:
            errors: List of error names "issue_name:detail"
        
        Returns:
            Dictionary mapping issue_desc -> list of details
        """
        grouped = {}
        
        for error in errors:
            metadata = self._error_metadata.get(error, {})
            issue_desc = metadata.get('issue_desc', 'Unknown Issue')
            detail = metadata.get('detail', error)
            
            if issue_desc not in grouped:
                grouped[issue_desc] = []
            grouped[issue_desc].append(detail)
        
        return grouped
    
    def _create_issue_error_groups(self, errors: List[str]) -> Dict[str, Dict]:
        """
        Create ERROR groups grouped by issue description.
        
        Args:
            errors: List of error names
        
        Returns:
            Dictionary of error groups
        """
        grouped = self._group_by_issue(errors)
        
        error_groups = {}
        for idx, (issue_desc, details) in enumerate(sorted(grouped.items()), start=1):
            error_code = f"ERROR{idx:02d}"
            error_groups[error_code] = {
                "description": issue_desc,
                "items": details
            }
        
        return error_groups
    
    def _create_issue_info_groups(self, errors: List[str], 
                                  prefix: str = "") -> Dict[str, Dict]:
        """
        Create INFO groups grouped by issue description.
        
        Args:
            errors: List of error names
            prefix: Prefix for description (e.g., "Waived")
        
        Returns:
            Dictionary of info groups
        """
        grouped = self._group_by_issue(errors)
        
        info_groups = {}
        for idx, (issue_desc, details) in enumerate(sorted(grouped.items()), start=1):
            info_code = f"INFO{idx:02d}"
            description = f"{prefix}: {issue_desc}" if prefix else issue_desc
            info_groups[info_code] = {
                "description": description,
                "items": details
            }
        
        return info_groups


def run():
    """Main entry point."""
    checker = PowerStructureChecker()
    checker.init_checker(script_path=Path(__file__))
    result = checker.execute_check()
    checker.write_output(result)


if __name__ == '__main__':
    run()
