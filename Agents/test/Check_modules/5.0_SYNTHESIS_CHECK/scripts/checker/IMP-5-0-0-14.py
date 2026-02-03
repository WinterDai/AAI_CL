################################################################################
# Script Name: IMP-5-0-0-14.py
#
# Purpose:
#   Confirm there are no design rule violations (max cap, max transition, etc).
#
# Logic:
#   - Parse design_check_rule.rpt for Max_transition/Max_capacitance/Max_fanout violations
#   - Report violations with pin details
#   - Warn if Max_fanout has no constraints
#   - Type 2/3: Support forbidden rule patterns
#
# Auto Type Detection:
#   Type 1: requirements.value=N/A, waivers.value=N/A/0 → Boolean check
#   Type 2: requirements.value>0, pattern_items exists, waivers.value=N/A/0 → Value comparison
#   Type 3: requirements.value>0, pattern_items exists, waivers.value>0 → Value with waiver logic
#   Type 4: requirements.value=N/A, waivers.value>0 → Boolean with waiver logic
#
# Author: yuyin
# Date: 2025-11-04
# Updated: 2025-11-27 - Refactored to BaseChecker with all 4 types support
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


class DesignRuleChecker(BaseChecker):
    """
    Unified checker that auto-detects and handles all 4 checker types.
    
    Check Target: Confirm there are no design rule violations
                  (max cap, max transition, max fanout)
    
    Type Detection Logic:
    - Type 1: requirements.value=N/A AND waivers.value=N/A/0
    - Type 2: requirements.value>0 AND pattern_items AND waivers.value=N/A/0
    - Type 3: requirements.value>0 AND pattern_items AND waivers.value>0
    - Type 4: requirements.value=N/A AND waivers.value>0
    
    Parsing Logic:
    - Extract violations from design_check_rule.rpt
    - Parse Max_transition, Max_capacitance, Max_fanout design rules
    - Store violation metadata (pin, value, line number)
    - Type 1: Check if any violations exist
    - Type 2/3: Match against rule type patterns
    - Type 3/4: Apply pin-specific waivers
    """
    
    def __init__(self):
        super().__init__(
            check_module="5.0_SYNTHESIS_CHECK",
            item_id="IMP-5-0-0-14",
            item_desc="Confirm that there are no other violations or errors (max cap, max transition etc)?"
        )
        self._violation_metadata: Dict[str, Dict[str, Any]] = {}
        self._forbidden_patterns: List[str] = []
        self._design_rule_report_path: Optional[Path] = None
    
    # =========================================================================
    # Input File Parsing
    # =========================================================================
    
    def _parse_design_rule_rpt(self) -> List[str]:
        """
        Parse design_check_rule.rpt to extract all design rule violations.
        
        Format: 
            Max_transition design rule (violation total = 238)
            Pin               Slew (ps)           Max     Violation
            ---------------------------------------------------------
            UDFF_th1/Q               90            29            61
            ...
            Max_capacitance design rule: no violations.
            Max_fanout design rule: no constraints.
        
        Returns:
            List of all violations (formatted as "rule_type:pin_name")
        """
        if not self.item_data or 'input_files' not in self.item_data:
            return []
        
        # Validate input files using BaseChecker method
        valid_files, missing_files = self.validate_input_files()
        
        # Store missing files for error reporting
        if missing_files:
            self._violation_metadata['_missing_input_files'] = {
                'files': missing_files,
                'count': len(missing_files)
            }
            return []
        
        all_violations = []
        
        for file_path in valid_files:
            if 'design_check' not in file_path.name.lower():
                continue
            
            self._design_rule_report_path = file_path
            
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            # Parse design rules
            rule_results = self._parse_design_rules(lines, file_path)
            
            # Extract violations
            for rule_name, rule_data in rule_results.items():
                if rule_data['has_violations']:
                    # Normalize rule type
                    if 'transition' in rule_name.lower():
                        rule_type = 'max_transition'
                    elif 'capacitance' in rule_name.lower():
                        rule_type = 'max_capacitance'
                    elif 'fanout' in rule_name.lower():
                        rule_type = 'max_fanout'
                    else:
                        rule_type = rule_name.lower().replace(' ', '_')
                    
                    # Store each pin violation
                    for pin_info in rule_data['violations']:
                        formatted_name = f"{rule_type}:{pin_info['pin']}"
                        all_violations.append(formatted_name)
                        self._violation_metadata[formatted_name] = {
                            'rule_type': rule_type,
                            'pin': pin_info['pin'],
                            'violation_value': pin_info.get('violation_value', ''),
                            'line_number': pin_info['line_number'],
                            'file_path': str(file_path)
                        }
                
                elif rule_data['no_constraints']:
                    # Store no_constraints warning for max_fanout
                    rule_type = 'max_fanout'
                    constraint_key = f"_no_constraints_{rule_type}"
                    self._violation_metadata[constraint_key] = {
                        'rule_type': rule_type,
                        'line_number': rule_data['line_number'],
                        'file_path': str(file_path)
                    }
        
        return all_violations
    
    def _parse_design_rules(self, lines: List[str], report_path: Path) -> Dict[str, Dict]:
        """
        Parse design rule report for three design rules.
        
        Returns:
            Dict with rule_name -> {
                'has_violations': bool,
                'no_constraints': bool,
                'violation_count': int,
                'violations': [{'pin': str, 'violation_value': str, 'line_number': int}],
                'line_number': int
            }
        """
        results = {}
        
        # Regex patterns
        violation_pattern = re.compile(
            r'^(Max_\w+\s+design\s+rule)\s*\(violation\s+total\s*=\s*(\d+)\)',
            re.IGNORECASE
        )
        no_violation_pattern = re.compile(
            r'^(Max_\w+\s+design\s+rule):\s*no\s+violations',
            re.IGNORECASE
        )
        no_constraint_pattern = re.compile(
            r'^(Max_\w+\s+design\s+rule):\s*no\s+constraints',
            re.IGNORECASE
        )
        pin_violation_pattern = re.compile(
            r'^([A-Za-z0-9_/\[\]]+)\s+(\d+)\s+(\d+)\s+(\d+)\s*$'
        )
        
        current_rule = None
        current_violations = []
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            
            # Check for violation total
            match = violation_pattern.match(line)
            if match:
                rule_name = match.group(1)
                violation_count = int(match.group(2))
                current_rule = rule_name
                current_violations = []
                results[rule_name] = {
                    'has_violations': violation_count > 0,
                    'no_constraints': False,
                    'violation_count': violation_count,
                    'violations': current_violations,
                    'line_number': line_num
                }
                continue
            
            # Check for no violations
            match = no_violation_pattern.match(line)
            if match:
                rule_name = match.group(1)
                results[rule_name] = {
                    'has_violations': False,
                    'no_constraints': False,
                    'violation_count': 0,
                    'violations': [],
                    'line_number': line_num
                }
                current_rule = None
                continue
            
            # Check for no constraints
            match = no_constraint_pattern.match(line)
            if match:
                rule_name = match.group(1)
                results[rule_name] = {
                    'has_violations': False,
                    'no_constraints': True,
                    'violation_count': 0,
                    'violations': [],
                    'line_number': line_num
                }
                current_rule = None
                continue
            
            # If we're in a rule with violations, extract pin details
            if current_rule and line:
                match = pin_violation_pattern.match(line)
                if match:
                    current_violations.append({
                        'pin': match.group(1),
                        'violation_value': match.group(4),  # Violation column
                        'line_number': line_num
                    })
        
        return results
    
    def _match_forbidden_rule(self, violation_name: str, patterns: List[str]) -> Optional[str]:
        """
        Check if violation's rule type matches any forbidden pattern.
        
        Supports both glob patterns and regex:
        - Glob: *transition* -> matches any rule containing "transition"
        - Exact: max_transition -> matches exact rule type
        
        Args:
            violation_name: Violation name (format: "rule_type:pin")
            patterns: List of patterns (glob or regex)
        
        Returns:
            Matched pattern if found, None otherwise
        """
        # Extract rule type from "rule_type:pin" format
        if ':' not in violation_name:
            return None
        
        rule_type = violation_name.split(':', 1)[0]
        
        for pattern in patterns:
            try:
                # Convert glob pattern to regex if needed
                regex_pattern = pattern
                if '*' in pattern and not pattern.startswith('^'):
                    # Glob pattern: convert * to .*
                    regex_pattern = pattern.replace('*', '.*')
                
                # Use search instead of match to find pattern anywhere in string
                if re.search(regex_pattern, rule_type):
                    return pattern
            except re.error:
                # If pattern is not valid regex, try exact match
                if pattern == rule_type:
                    return pattern
        return None
    
    def _find_violations(self, all_violations: List[str], forbidden_patterns: List[str]) -> List[Tuple[str, str]]:
        """
        Find violations whose rule type matches forbidden patterns.
        
        Args:
            all_violations: All violation names (format: "rule_type:pin")
            forbidden_patterns: Forbidden rule type patterns (regex)
        
        Returns:
            List of (violation_name, matched_pattern) tuples
        """
        violations = []
        
        for violation_name in all_violations:
            matched_pattern = self._match_forbidden_rule(violation_name, forbidden_patterns)
            if matched_pattern:
                violations.append((violation_name, matched_pattern))
        
        return violations
    
    # =========================================================================
    # Main Execution
    # =========================================================================
    
    def execute_check(self) -> CheckResult:
        """
        Execute check with automatic type detection and handling.
        
        Returns:
            CheckResult
        """
        try:
            if self.root is None:
                raise RuntimeError("Checker not initialized. Call init_checker() first.")
            
            # Get forbidden rule type patterns
            requirements = self.get_requirements()
            self._forbidden_patterns = requirements.get('pattern_items', []) if requirements else []
            
            # Detect checker type (use BaseChecker method)
            checker_type = self.detect_checker_type()
            
            # Parse design_check_rule.rpt
            all_violations = self._parse_design_rule_rpt()
            
            # Find violations (violations matching forbidden rule type patterns)
            violations = self._find_violations(all_violations, self._forbidden_patterns)
            
            # Execute based on type
            if checker_type == 1:
                return self._execute_type1(all_violations, violations)
            elif checker_type == 2:
                return self._execute_type2(all_violations, violations)
            elif checker_type == 3:
                return self._execute_type3(all_violations, violations)
            else:  # checker_type == 4
                return self._execute_type4(all_violations, violations)
        except ConfigurationError as e:
            return e.check_result
    
    # =========================================================================
    # Type 1: Boolean Check (No Waiver Logic)
    # =========================================================================
    
    def _execute_type1(self, all_violations: List[str], violations_matched: List[Tuple[str, str]]) -> CheckResult:
        """
        Type 1: requirements.value=N/A, waivers.value=N/A/0
        
        Logic: 
        - Check if any design rule violations exist
        - violations = All design rule violations found
        """
        waivers = self.get_waivers()
        waiver_value = waivers.get('value', 'N/A') if waivers else 'N/A'
        waive_items = waivers.get('waive_items', []) if waivers else []
        
        # Check if waiver=0 (display mode)
        is_waiver_zero = (waiver_value == 0)
        
        # Check for missing input files first
        missing_info = self._violation_metadata.get('_missing_input_files')
        if missing_info:
            return self.create_missing_files_error(missing_info['files'])
        
        details = []
        
        # Check for no_constraints warning
        no_constraints_key = '_no_constraints_max_fanout'
        if no_constraints_key in self._violation_metadata:
            constraint_info = self._violation_metadata[no_constraints_key]
            details.append(DetailItem(
                severity=Severity.WARN,
                name="",
                line_number=constraint_info.get('line_number', ''),
                file_path=constraint_info.get('file_path', ''),
                reason=f"Max_fanout design rule has no constraints"
            ))
        
        # Special case: No violations found - PASS
        if not all_violations:
            details.append(DetailItem(
                severity=Severity.INFO,
                name="",
                line_number=0,
                file_path=str(self._design_rule_report_path) if self._design_rule_report_path else "N/A",
                reason="All design rules clean - no violations found"
            ))
            
            info_groups = {
                "INFO01": {
                    "description": "All design rules clean",
                    "items": []
                }
            }
            
            warn_groups = {}
            if no_constraints_key in self._violation_metadata:
                warn_groups["WARN01"] = {
                    "description": "Max_fanout has no constraints",
                    "items": []
                }
            
            return create_check_result(
                value=0,
                is_pass=True,
                has_pattern_items=False,
                has_waiver_value=bool(waive_items),
                details=details,
                info_groups=info_groups,
                warn_groups=warn_groups if warn_groups else None,
                item_desc=self.item_desc
            )
        
        # Violations found
        if is_waiver_zero:
            # waiver=0: Convert FAIL to INFO
            for violation_name in all_violations:
                metadata = self._violation_metadata.get(violation_name, {})
                rule_type = metadata.get('rule_type', 'unknown')
                pin = metadata.get('pin', violation_name)
                
                reason = f"{self._get_rule_description(rule_type)}[WAIVED_AS_INFO]"
                details.append(DetailItem(
                    severity=Severity.INFO,
                    name=pin,
                    line_number=metadata.get('line_number', ''),
                    file_path=metadata.get('file_path', ''),
                    reason=reason
                ))
            
            # Add waive_items
            for item in waive_items:
                details.append(DetailItem(
                    severity=Severity.INFO,
                    name=item,
                    line_number=0,
                    file_path="N/A",
                    reason="Waiver item[WAIVED_INFO]"
                ))
            
            is_pass = True
        else:
            # Normal mode: Violations = FAIL
            for violation_name in all_violations:
                metadata = self._violation_metadata.get(violation_name, {})
                rule_type = metadata.get('rule_type', 'unknown')
                pin = metadata.get('pin', violation_name)
                
                reason = self._get_rule_description(rule_type)
                details.append(DetailItem(
                    severity=Severity.FAIL,
                    name=pin,
                    line_number=metadata.get('line_number', ''),
                    file_path=metadata.get('file_path', ''),
                    reason=reason
                ))
            
            is_pass = False
        
        # Group by rule type
        error_groups = self._create_rule_type_groups(all_violations, details)
        
        warn_groups = {}
        if no_constraints_key in self._violation_metadata:
            warn_groups["WARN01"] = {
                "description": "Max_fanout has no constraints",
                "items": []
            }
        
        return create_check_result(
            value=len(all_violations),
            is_pass=is_pass,
            has_pattern_items=False,
            has_waiver_value=bool(waive_items),
            details=details,
            error_groups=error_groups if error_groups else None,
            warn_groups=warn_groups if warn_groups else None,
            item_desc=self.item_desc
        )
    
    # =========================================================================
    # Type 2: Value Comparison (No Waiver Logic)
    # =========================================================================
    
    def _execute_type2(self, all_violations: List[str], violations: List[Tuple[str, str]]) -> CheckResult:
        """
        Type 2: requirements.value>0, pattern_items exists, waivers.value=N/A/0
        
        Logic: 
        - violations (matched) = Forbidden rule type violations found (BAD)
        - unmatched patterns = Forbidden patterns not found (GOOD)
        - Expect: violations count == requirements.value
        """
        requirements = self.get_requirements()
        expected_value = requirements.get('value', 0) if requirements else 0
        try:
            expected_value = int(expected_value)
        except:
            expected_value = 0
        
        waivers = self.get_waivers()
        waiver_value = waivers.get('value', 'N/A') if waivers else 'N/A'
        waive_items = waivers.get('waive_items', []) if waivers else []
        is_waiver_zero = (waiver_value == 0)
        
        # Check for missing input files first
        missing_info = self._violation_metadata.get('_missing_input_files')
        if missing_info:
            return self.create_missing_files_error(missing_info['files'])
        
        details = []
        
        # Check for no_constraints warning
        no_constraints_key = '_no_constraints_max_fanout'
        if no_constraints_key in self._violation_metadata:
            constraint_info = self._violation_metadata[no_constraints_key]
            details.append(DetailItem(
                severity=Severity.WARN,
                name="",
                line_number=constraint_info.get('line_number', ''),
                file_path=constraint_info.get('file_path', ''),
                reason=f"Max_fanout design rule has no constraints"
            ))
        
        # Find which patterns were not violated (good)
        violated_patterns = set(pattern for _, pattern in violations)
        unmatched_patterns = [p for p in self._forbidden_patterns if p not in violated_patterns]
        
        # Add violations (forbidden rule type violations found)
        if is_waiver_zero:
            # waiver=0: Convert FAIL to INFO
            for violation_name, pattern in violations:
                metadata = self._violation_metadata.get(violation_name, {})
                rule_type = metadata.get('rule_type', 'unknown')
                pin = metadata.get('pin', violation_name)
                
                reason = f"{self._get_rule_description(rule_type)} (matches pattern: {pattern})[WAIVED_AS_INFO]"
                details.append(DetailItem(
                    severity=Severity.INFO,
                    name=pin,
                    line_number=metadata.get('line_number', ''),
                    file_path=metadata.get('file_path', ''),
                    reason=reason
                ))
            
            # Add waive_items
            for item in waive_items:
                details.append(DetailItem(
                    severity=Severity.INFO,
                    name=item,
                    line_number=0,
                    file_path="N/A",
                    reason="Waiver item[WAIVED_INFO]"
                ))
            
            is_pass = True
        else:
            # Normal mode: violations = FAIL
            for violation_name, pattern in violations:
                metadata = self._violation_metadata.get(violation_name, {})
                rule_type = metadata.get('rule_type', 'unknown')
                pin = metadata.get('pin', violation_name)
                
                reason = f"{self._get_rule_description(rule_type)} (matches pattern: {pattern})"
                details.append(DetailItem(
                    severity=Severity.FAIL,
                    name=pin,
                    line_number=metadata.get('line_number', ''),
                    file_path=metadata.get('file_path', ''),
                    reason=reason
                ))
            
            # Add unmatched patterns as INFO (good - not found)
            for pattern in unmatched_patterns:
                details.append(DetailItem(
                    severity=Severity.INFO,
                    name=pattern,
                    line_number='',
                    file_path='',
                    reason="Forbidden rule type pattern not found (good)"
                ))
            
            is_pass = (len(violations) == expected_value)
        
        warn_groups = {}
        if no_constraints_key in self._violation_metadata:
            warn_groups["WARN01"] = {
                "description": "Max_fanout has no constraints",
                "items": []
            }
        
        return create_check_result(
            value=len(violations),
            is_pass=is_pass,
            has_pattern_items=True,
            has_waiver_value=bool(waive_items),
            details=details,
            warn_groups=warn_groups if warn_groups else None,
            item_desc=self.item_desc,
            default_group_desc="Forbidden rule type violations found"
        )
    
    # =========================================================================
    # Type 3: Value Comparison WITH Waiver Logic
    # =========================================================================
    
    def _execute_type3(self, all_violations: List[str], violations: List[Tuple[str, str]]) -> CheckResult:
        """
        Type 3: requirements.value>0, pattern_items exists, waivers.value>0
        
        Logic: 
        - violations = Forbidden rule type violations found
        - Separate into: unwaived (FAIL), waived (INFO), unused waivers (WARN)
        """
        waivers = self.get_waivers()
        waive_items_dict = self._get_waive_items_with_reasons()
        waive_items = list(waive_items_dict.keys())
        
        # Check for missing input files first
        missing_info = self._violation_metadata.get('_missing_input_files')
        if missing_info:
            return self.create_missing_files_error(missing_info['files'])
        
        # Separate violations into waived/unwaived
        waive_set = set(waive_items)
        unwaived = [(viol, pattern) for viol, pattern in violations if viol not in waive_set]
        waived = [(viol, pattern) for viol, pattern in violations if viol in waive_set]
        
        # Find unused waivers
        violated_items = set(viol for viol, _ in violations)
        unused_waivers = [item for item in waive_items if item not in violated_items]
        
        # Find unmatched patterns (good - not violated)
        violated_patterns = set(pattern for _, pattern in violations)
        unmatched_patterns = [p for p in self._forbidden_patterns if p not in violated_patterns]
        
        details = []
        
        # Check for no_constraints warning
        no_constraints_key = '_no_constraints_max_fanout'
        if no_constraints_key in self._violation_metadata:
            constraint_info = self._violation_metadata[no_constraints_key]
            details.append(DetailItem(
                severity=Severity.WARN,
                name="",
                line_number=constraint_info.get('line_number', ''),
                file_path=constraint_info.get('file_path', ''),
                reason=f"Max_fanout design rule has no constraints"
            ))
        
        # FAIL: Unwaived violations
        for violation_name, pattern in unwaived:
            metadata = self._violation_metadata.get(violation_name, {})
            rule_type = metadata.get('rule_type', 'unknown')
            pin = metadata.get('pin', violation_name)
            
            reason = f"{self._get_rule_description(rule_type)} (matches pattern: {pattern})"
            details.append(DetailItem(
                severity=Severity.FAIL,
                name=pin,
                line_number=metadata.get('line_number', ''),
                file_path=metadata.get('file_path', ''),
                reason=reason
            ))
        
        # INFO: Waived violations
        for violation_name, pattern in waived:
            metadata = self._violation_metadata.get(violation_name, {})
            pin = metadata.get('pin', violation_name)
            waiver_reason = waive_items_dict.get(violation_name, '')
            
            reason = f"Waived: {waiver_reason}[WAIVER]" if waiver_reason else f"Waived[WAIVER]"
            details.append(DetailItem(
                severity=Severity.INFO,
                name=pin,
                line_number=metadata.get('line_number', ''),
                file_path=metadata.get('file_path', ''),
                reason=reason
            ))
        
        # INFO: Unmatched patterns (good - not found)
        for pattern in unmatched_patterns:
            details.append(DetailItem(
                severity=Severity.INFO,
                name=pattern,
                line_number='',
                file_path='',
                reason="Forbidden rule type pattern not found (good)"
            ))
        
        # WARN: Unused waivers
        for item in unused_waivers:
            details.append(DetailItem(
                severity=Severity.WARN,
                name=item,
                line_number='',
                file_path='',
                reason="Waived item not found in check[WAIVER]"
            ))
        
        is_pass = (len(unwaived) == 0)
        
        # Create explicit error groups with rule-type-specific descriptions
        error_groups = {}
        warn_groups = {}
        info_groups = {}
        
        # Group unwaived by rule type
        if unwaived:
            error_groups = self._create_rule_type_error_groups([viol for viol, _ in unwaived])
        
        # Combine waiver-related WARN
        warn_idx = 1
        if no_constraints_key in self._violation_metadata:
            warn_groups[f"WARN{warn_idx:02d}"] = {
                "description": "Max_fanout has no constraints",
                "items": []
            }
            warn_idx += 1
        
        if unused_waivers:
            warn_groups[f"WARN{warn_idx:02d}"] = {
                "description": "Unused waivers (not found in actual violations)",
                "items": unused_waivers
            }
        
        # Combine waived and unmatched into INFO
        info_items = []
        if waived:
            info_items.extend([viol for viol, _ in waived])
        if unmatched_patterns:
            info_items.extend(unmatched_patterns)
        
        if info_items:
            # Group waived by rule type
            waived_by_rule = self._group_by_rule_type([viol for viol, _ in waived])
            info_idx = 1
            for rule_type, viols in sorted(waived_by_rule.items()):
                rule_desc = self._get_rule_description(rule_type)
                info_groups[f"INFO{info_idx:02d}"] = {
                    "description": f"Waived: {rule_desc}",
                    "items": [self._violation_metadata.get(v, {}).get('pin', v) for v in viols]
                }
                info_idx += 1
            
            # Add unmatched patterns
            if unmatched_patterns:
                info_groups[f"INFO{info_idx:02d}"] = {
                    "description": "Unmatched patterns (good)",
                    "items": unmatched_patterns
                }
        
        return create_check_result(
            value=len(violations),
            is_pass=is_pass,
            has_pattern_items=True,
            has_waiver_value=True,
            details=details,
            error_groups=error_groups if error_groups else None,
            warn_groups=warn_groups if warn_groups else None,
            info_groups=info_groups if info_groups else None,
            item_desc=self.item_desc
        )
    
    # =========================================================================
    # Type 4: Boolean WITH Waiver Logic
    # =========================================================================
    
    def _execute_type4(self, all_violations: List[str], violations_matched: List[Tuple[str, str]]) -> CheckResult:
        """
        Type 4: requirements.value=N/A, waivers.value>0
        
        Logic: Boolean check + Waiver separation (FAIL/INFO/WARN)
        """
        waivers = self.get_waivers()
        waive_items_dict = self._get_waive_items_with_reasons()
        waive_items = list(waive_items_dict.keys())
        
        # Check for missing input files first
        missing_info = self._violation_metadata.get('_missing_input_files')
        if missing_info:
            return self.create_missing_files_error(missing_info['files'])
        
        # For Type 4, check all violations
        # Separate into waived/unwaived
        waive_set = set(waive_items)
        unwaived = [viol for viol in all_violations if viol not in waive_set]
        waived = [viol for viol in all_violations if viol in waive_set]
        
        # Find unused waivers
        unused_waivers = [item for item in waive_items if item not in all_violations]
        
        details = []
        
        # Check for no_constraints warning
        no_constraints_key = '_no_constraints_max_fanout'
        if no_constraints_key in self._violation_metadata:
            constraint_info = self._violation_metadata[no_constraints_key]
            details.append(DetailItem(
                severity=Severity.WARN,
                name="",
                line_number=constraint_info.get('line_number', ''),
                file_path=constraint_info.get('file_path', ''),
                reason=f"Max_fanout design rule has no constraints"
            ))
        
        # FAIL: Unwaived violations
        for violation_name in sorted(unwaived):
            metadata = self._violation_metadata.get(violation_name, {})
            rule_type = metadata.get('rule_type', 'unknown')
            pin = metadata.get('pin', violation_name)
            
            reason = self._get_rule_description(rule_type)
            details.append(DetailItem(
                severity=Severity.FAIL,
                name=pin,
                line_number=metadata.get('line_number', ''),
                file_path=metadata.get('file_path', ''),
                reason=reason
            ))
        
        # INFO: Waived violations
        for violation_name in sorted(waived):
            metadata = self._violation_metadata.get(violation_name, {})
            pin = metadata.get('pin', violation_name)
            waiver_reason = waive_items_dict.get(violation_name, '')
            
            reason = f"Waived: {waiver_reason}[WAIVER]" if waiver_reason else "Waived[WAIVER]"
            details.append(DetailItem(
                severity=Severity.INFO,
                name=pin,
                line_number=metadata.get('line_number', ''),
                file_path=metadata.get('file_path', ''),
                reason=reason
            ))
        
        # WARN: Unused waivers
        for item in unused_waivers:
            details.append(DetailItem(
                severity=Severity.WARN,
                name=item,
                line_number='',
                file_path='',
                reason="Waived item not found in check[WAIVER]"
            ))
        
        is_pass = (len(unwaived) == 0)
        
        # Create explicit error groups with rule-type-specific descriptions
        error_groups = {}
        warn_groups = {}
        info_groups = {}
        
        # Group unwaived by rule type
        if unwaived:
            error_groups = self._create_rule_type_error_groups(unwaived)
        
        # Combine waiver-related WARN
        warn_idx = 1
        if no_constraints_key in self._violation_metadata:
            warn_groups[f"WARN{warn_idx:02d}"] = {
                "description": "Max_fanout has no constraints",
                "items": []
            }
            warn_idx += 1
        
        if unused_waivers:
            warn_groups[f"WARN{warn_idx:02d}"] = {
                "description": "Unused waivers (not found in actual violations)",
                "items": unused_waivers
            }
        
        # Group waived by rule type
        if waived:
            waived_by_rule = self._group_by_rule_type(waived)
            info_idx = 1
            for rule_type, viols in sorted(waived_by_rule.items()):
                rule_desc = self._get_rule_description(rule_type)
                info_groups[f"INFO{info_idx:02d}"] = {
                    "description": f"Waived: {rule_desc}",
                    "items": [self._violation_metadata.get(v, {}).get('pin', v) for v in viols]
                }
                info_idx += 1
        
        return create_check_result(
            value="N/A",
            is_pass=is_pass,
            has_pattern_items=False,
            has_waiver_value=True,
            details=details,
            error_groups=error_groups if error_groups else None,
            warn_groups=warn_groups if warn_groups else None,
            info_groups=info_groups if info_groups else None,
            item_desc=self.item_desc
        )
    
    # =========================================================================
    # Helper Methods
    # =========================================================================
    
    def _get_waive_items_with_reasons(self) -> Dict[str, str]:
        """
        Get waive_items with their reasons.
        
        Supports dict format:
        - name: "rule_type:pin_name"
          reason: "Approved by timing team"
        
        Returns:
            Dict mapping "rule_type:pin" to reason string
        """
        waivers = self.get_waivers()
        if not waivers:
            return {}
        
        waive_items = waivers.get('waive_items', [])
        
        waive_map = {}
        for entry in waive_items:
            if isinstance(entry, dict):
                # Standard format: {'name': 'item', 'reason': 'text'}
                name = entry.get('name', '')
                reason = entry.get('reason', '')
                if name:
                    waive_map[name] = reason
            elif isinstance(entry, str):
                # Simple string format
                waive_map[entry] = ''
        
        return waive_map
    
    def _group_by_rule_type(self, violations: List[str]) -> Dict[str, List[str]]:
        """
        Group violations by rule type.
        
        Args:
            violations: List of violation names (format: "rule_type:pin")
        
        Returns:
            Dict mapping rule_type to list of violation names
        """
        by_rule = {}
        for violation_name in violations:
            if ':' in violation_name:
                rule_type = violation_name.split(':', 1)[0]
                if rule_type not in by_rule:
                    by_rule[rule_type] = []
                by_rule[rule_type].append(violation_name)
        return by_rule
    
    def _create_rule_type_groups(self, violations: List[str], details: List[DetailItem]) -> Dict:
        """
        Create error groups organized by rule type.
        
        Used for Type 1 when grouping all violations.
        """
        # Group by rule type
        by_rule = self._group_by_rule_type(violations)
        
        error_groups = {}
        idx = 1
        
        for rule_type, viols in sorted(by_rule.items()):
            rule_desc = self._get_rule_description(rule_type)
            
            # Determine severity from details
            severity_prefix = "ERROR"
            for detail in details:
                if detail.name in [self._violation_metadata.get(v, {}).get('pin', v) for v in viols]:
                    if detail.severity == Severity.INFO:
                        severity_prefix = "INFO"
                    break
            
            error_groups[f"{severity_prefix}{idx:02d}"] = {
                "description": rule_desc,
                "items": [self._violation_metadata.get(v, {}).get('pin', v) for v in viols]
            }
            idx += 1
        
        return error_groups
    
    def _create_rule_type_error_groups(self, unwaived_violations: List[str]) -> Dict:
        """
        Create ERROR groups organized by rule type for unwaived violations.
        
        Used for Type 3/4.
        """
        by_rule = self._group_by_rule_type(unwaived_violations)
        
        error_groups = {}
        idx = 1
        
        for rule_type, viols in sorted(by_rule.items()):
            rule_desc = self._get_rule_description(rule_type)
            error_groups[f"ERROR{idx:02d}"] = {
                "description": rule_desc,
                "items": [self._violation_metadata.get(v, {}).get('pin', v) for v in viols]
            }
            idx += 1
        
        return error_groups
    
    def _get_rule_description(self, rule_type: str) -> str:
        """Get human-readable description for rule type."""
        descriptions = {
            'max_transition': 'Max transition violation',
            'max_capacitance': 'Max capacitance violation',
            'max_fanout': 'Max fanout violation'
        }
        return descriptions.get(rule_type, f'{rule_type} violation')


################################################################################
# Main Entry Point
################################################################################

if __name__ == '__main__':
    checker = DesignRuleChecker()
    checker.run()
