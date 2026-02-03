################################################################################
# Script Name: IMP-5-0-0-08.py
#
# Purpose:
#   Confirm multidriven ports/pins/nets are clean in synthesis reports.
#   Supports 4 checking types based on requirements and waivers configuration.
#
# Refactoring to BaseChecker:
#   - Migrated from BooleanChecker to unified BaseChecker
#   - Added support for all 4 checking types (Type 1/2/3/4)
#   - Automatic type detection based on requirements.value and waivers.value
#   - Centralized input validation with create_missing_files_error()
#
# Usage:
#   python IMP-5-0-0-08.py [type]
#   type: Optional override (1/2/3/4), default is auto-detect
#
#
# Logic:
#   - Parse multidriven.rpt for multidriven net violations
#   - Extract all multidriven signal names and locations
#   - Report multidriven nets as violations
# Author: yyin
# Date:   2025-10-31
# Updated: 2025-11-26 - Migrated to BaseChecker (All 4 Types)
################################################################################

import sys
import re
from pathlib import Path
from typing import List, Dict, Tuple

# Add common modules to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'common'))

from base_checker import BaseChecker, ConfigurationError
from output_formatter import CheckResult, Severity, DetailItem, create_check_result


class MultidrivenChecker(BaseChecker):
    """
    IMP-5-0-0-08: Confirm Multidriven Report clean?
    
    Parses multidriven.rpt to detect 5 types of multidriven issues:
    - Combinational pins
    - Sequential pins
    - Hierarchical pins
    - Ports
    - Unloaded nets
    
    Checking Types:
    - Type 1: requirements=N/A, waivers=N/A/0 → Always PASS (informational only)
    - Type 2: requirements>0, waivers=N/A/0 → FAIL if any multidriven found
    - Type 3: requirements>0, waivers>0 → FAIL if unwaived multidriven found
    - Type 4: requirements=N/A, waivers>0 → FAIL if unwaived multidriven found
    """
    
    # Issue type mappings
    ISSUE_TYPES = {
        'combinational': 'Multidriven combinational pin',
        'sequential': 'Multidriven sequential pin',
        'hierarchical': 'Multidriven hierarchical pin',
        'ports': 'Multidriven port',
        'unloaded_nets': 'Multidriven unloaded net'
    }
    
    ERROR_CODES = {
        'combinational': 'ERROR01',
        'sequential': 'ERROR02',
        'hierarchical': 'ERROR03',
        'ports': 'ERROR04',
        'unloaded_nets': 'ERROR05'
    }
    
    def __init__(self):
        """Initialize the multidriven checker."""
        super().__init__(
            check_module="5.0_SYNTHESIS_CHECK",
            item_id="IMP-5-0-0-08",
            item_desc="Confirm Multidriven Report clean?"
        )
        # Cache for parsed multidriven issues: {issue_type: {count, occurrences, line_num}}
        self.multidriven_cache: Dict[str, Dict] = {}
    
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
        Parse multidriven report files to extract issues.
        
        Args:
            input_files: List of multidriven report file paths
        
        Returns:
            Dict mapping issue identifier to count
        """
        all_issues = {}
        
        for report_path in input_files:
            if not report_path.exists():
                continue
            
            lines = self.read_file(report_path)
            if not lines:
                continue
            
            # Parse issues using state machine
            issues_dict = self._parse_multidriven_sections(lines, report_path)
            
            # Cache for detail creation
            self.multidriven_cache.update(issues_dict)
            
            # Build issue counts
            for issue_type, issue_info in issues_dict.items():
                for occurrence in issue_info['occurrences']:
                    all_issues[occurrence] = all_issues.get(occurrence, 0) + 1
        
        return all_issues
    
    # =========================================================================
    # Type 1: Informational Check (requirements=N/A, waivers=N/A/0)
    # =========================================================================
    
    def _execute_type1(self) -> CheckResult:
        """
        Type 1: Informational check only, always PASS.
        
        Returns:
            CheckResult with is_pass=True, INFO message about multidriven status
        """
        # Validate input files
        valid_files, missing_files = self.validate_input_files()
        
        # Handle missing input files
        if missing_files:
            return self.create_missing_files_error(missing_files)
        
        # Parse reports to extract multidriven issues
        issues = self._parse_input_files(valid_files)
        
        # Build details
        details = []
        if issues:
            # Add each multidriven issue as INFO
            for issue_type, issue_info in self.multidriven_cache.items():
                if issue_type not in self.ISSUE_TYPES:
                    continue
                
                issue_desc = self.ISSUE_TYPES[issue_type]
                line_num = issue_info['line_num']
                report_path = str(valid_files[0].resolve())
                
                for occurrence in issue_info['occurrences']:
                    details.append(DetailItem(
                        severity=Severity.INFO,
                        name=occurrence,
                        line_number=line_num,
                        file_path=report_path,
                        reason=f"{issue_desc}"
                    ))
        else:
            # No multidriven issues
            report_path = str(valid_files[0].resolve()) if valid_files else "multidriven reports"
            details.append(DetailItem(
                severity=Severity.INFO,
                name="",
                line_number=0,
                file_path="",
                reason=f"Multidriven Report is clean in {report_path}"
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
        Type 2: FAIL if multidriven count > 0, PASS if count == 0.
        
        Returns:
            CheckResult with is_pass based on whether multidriven issues exist
        """
        # Validate input files
        valid_files, missing_files = self.validate_input_files()
        
        # Handle missing input files
        if missing_files:
            return self.create_missing_files_error(missing_files)
        
        # Parse reports to extract multidriven issues
        issues = self._parse_input_files(valid_files)
        
        # Build details
        details = []
        is_pass = len(issues) == 0
        
        if issues:
            # FAIL: Add each multidriven issue as FAIL
            for issue_type, issue_info in self.multidriven_cache.items():
                if issue_type not in self.ISSUE_TYPES:
                    continue
                
                issue_desc = self.ISSUE_TYPES[issue_type]
                line_num = issue_info['line_num']
                report_path = str(valid_files[0].resolve())
                
                for occurrence in issue_info['occurrences']:
                    details.append(DetailItem(
                        severity=Severity.FAIL,
                        name=occurrence,
                        line_number=line_num,
                        file_path=report_path,
                        reason=issue_desc
                    ))
            
            # Build error groups by issue type
            error_groups = self._create_error_groups(details)
            info_groups = None
        else:
            # PASS: No multidriven issues
            report_path = str(valid_files[0].resolve()) if valid_files else "multidriven reports"
            details.append(DetailItem(
                severity=Severity.INFO,
                name="",
                line_number=0,
                file_path="",
                reason=f"Multidriven Report is clean in {report_path}"
            ))
            info_groups = {
                "INFO01": {
                    "description": "Check result",
                    "items": []
                }
            }
            error_groups = None
        
        return create_check_result(
            value=str(len(issues)),
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
        Type 3: FAIL if unwaived multidriven issues exist, WAIVED if all are waived.
        
        Returns:
            CheckResult with FAIL/WAIVED/PASS based on waiver coverage
        """
        # Validate input files
        valid_files, missing_files = self.validate_input_files()
        
        # Handle missing input files
        if missing_files:
            return self.create_missing_files_error(missing_files)
        
        # Parse reports to extract multidriven issues
        issues = self._parse_input_files(valid_files)
        
        # Get waiver patterns and reasons
        waiver_patterns = self.waivers.pattern_items or []
        waiver_reason_map = self._build_waiver_reason_map()
        
        # Separate waived and unwaived issues
        waived_issues = []
        unwaived_issues = []
        
        for issue in issues.keys():
            if self._matches_any_pattern(issue, waiver_patterns):
                waived_issues.append(issue)
            else:
                unwaived_issues.append(issue)
        
        # Check for unused waivers
        used_patterns = set()
        for issue in waived_issues:
            for pattern in waiver_patterns:
                if self._matches_pattern(issue, pattern):
                    used_patterns.add(pattern)
        
        unused_waivers = [p for p in waiver_patterns if p not in used_patterns]
        
        # Build details
        details = []
        report_path = str(valid_files[0].resolve()) if valid_files else "multidriven reports"
        
        # Add unwaived issues as FAIL
        for issue_type, issue_info in self.multidriven_cache.items():
            if issue_type not in self.ISSUE_TYPES:
                continue
            
            issue_desc = self.ISSUE_TYPES[issue_type]
            line_num = issue_info['line_num']
            
            for occurrence in issue_info['occurrences']:
                if occurrence in unwaived_issues:
                    details.append(DetailItem(
                        severity=Severity.FAIL,
                        name=occurrence,
                        line_number=line_num,
                        file_path=report_path,
                        reason=f"{issue_desc} (not waived)"
                    ))
        
        # Add waived issues as INFO with [WAIVER] tag
        for issue_type, issue_info in self.multidriven_cache.items():
            if issue_type not in self.ISSUE_TYPES:
                continue
            
            issue_desc = self.ISSUE_TYPES[issue_type]
            line_num = issue_info['line_num']
            
            for occurrence in issue_info['occurrences']:
                if occurrence in waived_issues:
                    reason = waiver_reason_map.get(occurrence, "Waived")
                    details.append(DetailItem(
                        severity=Severity.INFO,
                        name=f"[WAIVER] {occurrence}",
                        line_number=line_num,
                        file_path=report_path,
                        reason=f"{issue_desc}: {reason}"
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
        is_pass = len(unwaived_issues) == 0
        
        # Build error/warn/info groups
        error_groups = {}
        warn_groups = {}
        info_groups = {}
        
        if unwaived_issues:
            # Create error groups by issue type
            unwaived_details = [d for d in details if d.severity == Severity.FAIL]
            error_groups = self._create_error_groups(unwaived_details)
        
        if waived_issues:
            info_groups["INFO01"] = {
                "description": "Multidriven issues waived",
                "items": [d.name for d in details if d.severity == Severity.INFO and d.name]
            }
        
        if unused_waivers:
            warn_groups["WARN01"] = {
                "description": "Unused waiver patterns",
                "items": [d.name for d in details if d.severity == Severity.WARN and d.name]
            }
        
        return create_check_result(
            value=str(len(issues)),
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
        Type 4: Boolean check - FAIL if unwaived multidriven issues exist.
        
        Returns:
            CheckResult with FAIL/WAIVED/PASS based on waiver coverage
        """
        # Validate input files
        valid_files, missing_files = self.validate_input_files()
        
        # Handle missing input files
        if missing_files:
            return self.create_missing_files_error(missing_files)
        
        # Parse reports to extract multidriven issues
        issues = self._parse_input_files(valid_files)
        
        # Get waiver patterns and reasons
        waiver_patterns = self.waivers.pattern_items or []
        waiver_reason_map = self._build_waiver_reason_map()
        
        # Separate waived and unwaived issues
        waived_issues = []
        unwaived_issues = []
        
        for issue in issues.keys():
            if self._matches_any_pattern(issue, waiver_patterns):
                waived_issues.append(issue)
            else:
                unwaived_issues.append(issue)
        
        # Check for unused waivers
        used_patterns = set()
        for issue in waived_issues:
            for pattern in waiver_patterns:
                if self._matches_pattern(issue, pattern):
                    used_patterns.add(pattern)
        
        unused_waivers = [p for p in waiver_patterns if p not in used_patterns]
        
        # Build details
        details = []
        report_path = str(valid_files[0].resolve()) if valid_files else "multidriven reports"
        
        # Add unwaived issues as FAIL
        for issue_type, issue_info in self.multidriven_cache.items():
            if issue_type not in self.ISSUE_TYPES:
                continue
            
            issue_desc = self.ISSUE_TYPES[issue_type]
            line_num = issue_info['line_num']
            
            for occurrence in issue_info['occurrences']:
                if occurrence in unwaived_issues:
                    details.append(DetailItem(
                        severity=Severity.FAIL,
                        name=occurrence,
                        line_number=line_num,
                        file_path=report_path,
                        reason=f"{issue_desc} (not waived)"
                    ))
        
        # Add waived issues as INFO with [WAIVER] tag
        for issue_type, issue_info in self.multidriven_cache.items():
            if issue_type not in self.ISSUE_TYPES:
                continue
            
            issue_desc = self.ISSUE_TYPES[issue_type]
            line_num = issue_info['line_num']
            
            for occurrence in issue_info['occurrences']:
                if occurrence in waived_issues:
                    reason = waiver_reason_map.get(occurrence, "Waived")
                    details.append(DetailItem(
                        severity=Severity.INFO,
                        name=f"[WAIVER] {occurrence}",
                        line_number=line_num,
                        file_path=report_path,
                        reason=f"{issue_desc}: {reason}"
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
        
        # If no issues at all, add INFO message
        if not issues:
            details.append(DetailItem(
                severity=Severity.INFO,
                name="",
                line_number=0,
                file_path="",
                reason=f"Multidriven Report is clean in {report_path}"
            ))
        
        # Determine pass status
        is_pass = len(unwaived_issues) == 0
        
        # Build error/warn/info groups
        error_groups = {}
        warn_groups = {}
        info_groups = {}
        
        if unwaived_issues:
            # Create error groups by issue type
            unwaived_details = [d for d in details if d.severity == Severity.FAIL]
            error_groups = self._create_error_groups(unwaived_details)
        
        if waived_issues:
            info_groups["INFO01"] = {
                "description": "Multidriven issues waived",
                "items": [d.name for d in details if d.severity == Severity.INFO and d.name and d.name.startswith("[WAIVER]")]
            }
        elif not issues:
            # No issues case
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
    # Helper Methods: Report Parsing
    # =========================================================================
    
    def _parse_multidriven_sections(self, lines: List[str], report_path: Path) -> Dict[str, Dict]:
        """
        Parse multidriven report sections using state machine.
        
        Returns:
            Dictionary mapping issue_type to {count, occurrences, line_num}
        """
        issues = {}
        in_check_design = False
        in_multidriven_section = False
        current_issue_type = None
        current_occurrences = []
        
        # Patterns
        check_design_pattern = re.compile(r'Check\s+Design\s+Report.*\(c\)', re.IGNORECASE)
        multidriven_header_pattern = re.compile(r'Multidriven\s+Port\(s\)/Pin\(s\)', re.IGNORECASE)
        
        # "No multidriven X" patterns (clean case)
        no_multidriven_patterns = {
            'combinational': re.compile(r"No\s+multidriven\s+combinational\s+pin\s+in\s+'([^']+)'", re.IGNORECASE),
            'sequential': re.compile(r"No\s+multidriven\s+sequential\s+pin\s+in\s+'([^']+)'", re.IGNORECASE),
            'hierarchical': re.compile(r"No\s+multidriven\s+hierarchical\s+pin\s+in\s+'([^']+)'", re.IGNORECASE),
            'ports': re.compile(r"No\s+multidriven\s+ports\s+in\s+'([^']+)'", re.IGNORECASE),
            'unloaded_nets': re.compile(r"No\s+multidriven\s+unloaded\s+nets\s+in\s+'([^']+)'", re.IGNORECASE)
        }
        
        # "The following X are multidriven" patterns (issue found)
        has_multidriven_patterns = {
            'combinational': re.compile(r"The\s+following\s+combination(?:al)?\s+pin\(s\)\s+in\s+'([^']+)'\s+are\s+multidriven", re.IGNORECASE),
            'sequential': re.compile(r"The\s+following\s+sequential\s+pin\(s\)\s+in\s+'([^']+)'\s+are\s+multidriven", re.IGNORECASE),
            'hierarchical': re.compile(r"The\s+following\s+hierarchical\s+pin\(s\)\s+in\s+'([^']+)'\s+are\s+multidriven", re.IGNORECASE),
            'ports': re.compile(r"The\s+following\s+port\(s\)\s+in\s+'([^']+)'\s+are\s+multidriven", re.IGNORECASE),
            'unloaded_nets': re.compile(r"The\s+following\s+unloaded\s+net\(s\)\s+in\s+'([^']+)'\s+are\s+multidriven", re.IGNORECASE)
        }
        
        # Occurrence extraction patterns
        pin_pattern = re.compile(r'^\s*pin:\s*(\S+)', re.IGNORECASE)
        hpin_pattern = re.compile(r'^\s*hpin:\s*(\S+)', re.IGNORECASE)
        port_pattern = re.compile(r'^\s*port:\s*(\S+)', re.IGNORECASE)
        net_pattern = re.compile(r'^\s*net:\s*(\S+)', re.IGNORECASE)
        total_pattern = re.compile(r'^\s*Total.*?:\s*(\d+)', re.IGNORECASE)
        
        for idx, line in enumerate(lines, start=1):
            stripped = line.strip()
            
            # Detect Check Design Report section
            if check_design_pattern.search(line):
                in_check_design = True
                continue
            
            # Detect Multidriven section header
            if in_check_design and multidriven_header_pattern.search(line):
                in_multidriven_section = True
                continue
            
            # Exit when reaching "Done Checking"
            if in_multidriven_section and 'Done Checking the design' in line:
                # Save last issue if any
                if current_issue_type and current_occurrences:
                    if current_issue_type not in issues:
                        issues[current_issue_type] = {
                            'count': len(current_occurrences),
                            'occurrences': current_occurrences,
                            'line_num': idx
                        }
                break
            
            if not in_multidriven_section:
                continue
            
            # Check for "No multidriven" (clean - skip)
            found_no_issue = any(pattern.search(stripped) for pattern in no_multidriven_patterns.values())
            if found_no_issue:
                continue
            
            # Check for "The following ... are multidriven" (issue header)
            for issue_type, pattern in has_multidriven_patterns.items():
                if pattern.search(stripped):
                    # Save previous issue
                    if current_issue_type and current_occurrences:
                        if current_issue_type not in issues:
                            issues[current_issue_type] = {
                                'count': len(current_occurrences),
                                'occurrences': current_occurrences,
                                'line_num': idx
                            }
                    
                    # Start new issue
                    current_issue_type = issue_type
                    current_occurrences = []
                    break
            
            # Extract occurrences for current issue
            if current_issue_type:
                # Match pin/hpin/port/net lines
                if current_issue_type in ['combinational', 'sequential']:
                    pin_match = pin_pattern.match(stripped)
                    if pin_match:
                        current_occurrences.append(f"pin:{pin_match.group(1)}")
                        continue
                
                if current_issue_type == 'hierarchical':
                    hpin_match = hpin_pattern.match(stripped)
                    if hpin_match:
                        current_occurrences.append(f"hpin:{hpin_match.group(1)}")
                        continue
                
                if current_issue_type == 'ports':
                    port_match = port_pattern.match(stripped)
                    if port_match:
                        current_occurrences.append(f"port:{port_match.group(1)}")
                        continue
                
                if current_issue_type == 'unloaded_nets':
                    net_match = net_pattern.match(stripped)
                    if net_match:
                        current_occurrences.append(f"net:{net_match.group(1)}")
                        continue
                
                # Check for Total line (end of current issue section)
                total_match = total_pattern.match(stripped)
                if total_match:
                    total_count = int(total_match.group(1))
                    # Save current issue
                    if current_issue_type not in issues:
                        issues[current_issue_type] = {
                            'count': total_count,
                            'occurrences': current_occurrences,
                            'line_num': idx
                        }
                    # Reset
                    current_issue_type = None
                    current_occurrences = []
        
        return issues
    
    def _create_error_groups(self, details: List[DetailItem]) -> Dict[str, Dict]:
        """
        Group errors by issue type with predefined ERROR codes.
        
        Returns:
            Dictionary mapping ERROR01-ERROR05 to error group data
        """
        if not details:
            return {}
        
        # Group by issue type (extracted from reason field)
        error_type_groups: Dict[str, List[DetailItem]] = {}
        for detail in details:
            # Extract issue type from reason (format: "Multidriven X (not waived)")
            reason = detail.reason
            # Remove "(not waived)" suffix
            clean_reason = reason.replace(" (not waived)", "").strip()
            error_type_groups.setdefault(clean_reason, []).append(detail)
        
        # Build error_groups with predefined codes
        error_groups = {}
        for issue_desc, items in error_type_groups.items():
            # Find matching ERROR code
            error_code = None
            for issue_type, description in self.ISSUE_TYPES.items():
                if issue_desc == description:
                    error_code = self.ERROR_CODES[issue_type]
                    break
            
            if error_code:
                error_groups[error_code] = {
                    "description": f"{issue_desc}(s) exist",
                    "items": [item.name for item in items]
                }
        
        return error_groups


# =============================================================================
# Entry Point
# =============================================================================

if __name__ == '__main__':
    checker = MultidrivenChecker()
    checker.run()
