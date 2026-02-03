################################################################################
# Script Name: IMP-5-0-0-02.py
#
# Purpose:
#   Confirm synthesis is using QRC tech file for RC data.
#   Parse log files and qor.rpt to identify QRC file usage through domain→rc_corner→qrc_tech chain.
#
# Logic:
#   - Extract domains from qor.rpt
#   - Find rc_corner for each domain in log files
#   - Find qrc_tech for each rc_corner in log files
#   - Report QRC file usage or absence (both are valid PASS conditions)
#
# Auto Type Detection:
#   Type 1: requirements.value=N/A, waivers.value=N/A/0 → Boolean check
#   Type 2: requirements.value>0, pattern_items exists, waivers.value=N/A/0 → Value comparison
#   Type 3: requirements.value>0, pattern_items exists, waivers.value>0 → Value with waiver logic
#   Type 4: requirements.value=N/A, waivers.value>0 → Boolean with waiver logic
#
# Author: yuyin
# Date: 2025-11-26
################################################################################

from pathlib import Path
import re
import sys
from typing import List, Tuple, Dict, Any, Optional

# Add common module to path
_SCRIPT_DIR = Path(__file__).resolve().parent
_CHECK_MODULES_DIR = _SCRIPT_DIR.parents[2]  # Go up to Check_modules/
_COMMON_DIR = _CHECK_MODULES_DIR / 'common'
if str(_COMMON_DIR) not in sys.path:
    sys.path.insert(0, str(_COMMON_DIR))

from base_checker import BaseChecker, CheckResult, ConfigurationError
from output_formatter import DetailItem, Severity, create_check_result
from parse_qor import parse_qor


class QRCChecker(BaseChecker):
    """
    Unified checker that auto-detects and handles all 4 checker types.
    
    Check Target: Confirm synthesis is using QRC tech file for RC data
    
    Type Detection Logic:
    - Type 1: requirements.value=N/A AND waivers.value=N/A/0
    - Type 2: requirements.value>0 AND pattern_items AND waivers.value=N/A/0
    - Type 3: requirements.value>0 AND pattern_items AND waivers.value>0
    - Type 4: requirements.value=N/A AND waivers.value>0
    
    Parsing Logic:
    - Extract domains from qor.rpt
    - Find rc_corner for each domain (from create_delay_corner in log files)
    - Find qrc_tech for each rc_corner (from create_rc_corner in log files)
    - Store QRC file paths and line numbers
    - Type 1: Report QRC usage (both usage and non-usage are PASS)
    - Type 2/3: Match against forbidden QRC file patterns
    """
    
    def __init__(self):
        super().__init__(
            check_module="5.0_SYNTHESIS_CHECK",
            item_id="IMP-5-0-0-02",
            item_desc="Confirm synthesis is using qrc tech file for RC data?"
        )
        self._qrc_metadata: Dict[str, Dict[str, Any]] = {}
        self._forbidden_patterns: List[str] = []
    
    # =========================================================================
    # Input File Parsing
    # =========================================================================
    
    def _parse_input_files(self) -> List[str]:
        """
        Parse input files to extract QRC tech files using domain→rc_corner→qrc_tech chain.
        
        Process:
        1. Extract domains from qor.rpt
        2. For each domain, find rc_corner from log files (create_delay_corner)
        3. For each rc_corner, find qrc_tech from log files (create_rc_corner)
        
        Returns:
            List of all QRC tech file paths found
        """
        if not self.item_data or 'input_files' not in self.item_data:
            return []
        
        # Validate input files using BaseChecker method
        valid_files, missing_files = self.validate_input_files()
        
        # Store missing files for error reporting
        if missing_files:
            self._qrc_metadata['_missing_input_files'] = {
                'files': missing_files,
                'count': len(missing_files)
            }
            # Return empty list - will be handled in execute methods
            return []
        
        # Separate log files and qor.rpt
        log_files = [f for f in valid_files if f.suffix.lower() == '.log']
        qor_path = None
        for f in valid_files:
            if f.name.lower() == 'qor.rpt':
                qor_path = f
                break
        
        # If no qor.rpt or no log files, return empty (will be reported as INFO)
        if not qor_path or not log_files:
            return []
        
        # Extract QRC files through domain→rc_corner→qrc_tech chain
        qrc_files = self._extract_qrc_files(log_files, qor_path)
        
        return qrc_files
    
    def _extract_qrc_files(self, log_files: List[Path], qor_path: Path) -> List[str]:
        """
        Extract QRC files using domain→rc_corner→qrc_tech chain.
        
        Args:
            log_files: List of log file paths
            qor_path: Path to qor.rpt file
        
        Returns:
            List of QRC tech file paths
        """
        qrc_files: List[str] = []
        
        # Parse qor.rpt to get domains
        try:
            qor_info = parse_qor(qor_path)
            domains = [d.get("domain") for d in qor_info.get("domains", []) if d.get("domain")]
        except Exception:
            return []
        
        if not domains:
            return []
        
        # For each domain, find rc_corner→qrc_tech chain
        for domain in domains:
            # Find rc_corner for this domain
            rc_corner = None
            for log_file in log_files:
                rc_corner = self._extract_rc_corner_from_log(log_file, domain)
                if rc_corner:
                    break
            
            if not rc_corner:
                continue
            
            # Find qrc_tech for this rc_corner
            for log_file in log_files:
                qrc_tech = self._extract_qrc_tech_from_log(log_file, rc_corner)
                if qrc_tech and qrc_tech not in self._qrc_metadata:
                    qrc_files.append(qrc_tech)
                    # Store metadata
                    line_num = self._find_qrc_line_number(log_file, qrc_tech)
                    self._qrc_metadata[qrc_tech] = {
                        'line_number': line_num,
                        'file_path': str(log_file),
                        'domain': domain,
                        'rc_corner': rc_corner
                    }
                    break
        
        return qrc_files
    
    def _extract_rc_corner_from_log(self, log_file: Path, domain: str) -> Optional[str]:
        """
        Find rc_corner for a given domain from create_delay_corner command.
        
        Args:
            log_file: Path to log file
            domain: Domain name to search for
        
        Returns:
            rc_corner name if found, None otherwise
        """
        try:
            content = self.read_file(log_file)
            if not content:
                return None
            
            content_str = '\n'.join(content)
            # Extract create_delay_corner blocks
            delay_corner_blocks = re.findall(r'create_delay_corner[^@]*?(?=@|\Z)', content_str, re.DOTALL)
            
            for block in delay_corner_blocks:
                if domain in block:
                    rc_match = re.search(r'-rc_corner\s+(\S+)', block)
                    if rc_match:
                        return rc_match.group(1)
        except Exception:
            pass
        return None
    
    def _extract_qrc_tech_from_log(self, log_file: Path, rc_corner: str) -> Optional[str]:
        """
        Find qrc_tech path for a given rc_corner from create_rc_corner command.
        
        Args:
            log_file: Path to log file
            rc_corner: RC corner name to search for
        
        Returns:
            qrc_tech file path if found, None otherwise
        """
        try:
            content = self.read_file(log_file)
            if not content:
                return None
            
            content_str = '\n'.join(content)
            # Extract create_rc_corner blocks
            rc_corner_blocks = re.findall(r'create_rc_corner[^@]*?(?=@|\Z)', content_str, re.DOTALL)
            
            for block in rc_corner_blocks:
                name_match = re.search(r'-name\s+(\S+)', block)
                if name_match and name_match.group(1) == rc_corner:
                    qrc_match = re.search(r'-qrc_tech\s+(\S+)', block)
                    if qrc_match:
                        return qrc_match.group(1)
        except Exception:
            pass
        return None
    
    def _find_qrc_line_number(self, log_file: Path, qrc_tech: str) -> int:
        """
        Find line number where qrc_tech is referenced.
        
        Args:
            log_file: Path to log file
            qrc_tech: QRC tech file path to search for
        
        Returns:
            Line number (1-based), or 0 if not found
        """
        try:
            lines = self.read_file(log_file)
            if not lines:
                return 0
            
            for line_num, line in enumerate(lines, 1):
                if qrc_tech in line and '-qrc_tech' in line:
                    return line_num
        except Exception:
            pass
        return 0
    
    def _match_forbidden_pattern(self, qrc_file: str, patterns: List[str]) -> Optional[str]:
        """
        Check if QRC file matches any forbidden pattern.
        
        Supports both glob patterns and regex:
        - Glob: *old_qrc* -> matches anything containing old_qrc
        - Regex: ^.*deprecated.*\\.qrc$ -> matches specific pattern
        
        Args:
            qrc_file: QRC file path to check
            patterns: List of patterns (glob or regex)
        
        Returns:
            Matched pattern if found, None otherwise
        """
        for pattern in patterns:
            try:
                # Convert glob pattern to regex if needed
                regex_pattern = pattern
                if '*' in pattern and not pattern.startswith('^'):
                    # Glob pattern: convert * to .*
                    regex_pattern = pattern.replace('*', '.*')
                
                # Use search instead of match to find pattern anywhere in string
                if re.search(regex_pattern, qrc_file, re.IGNORECASE):
                    return pattern
            except re.error:
                # If pattern is not valid regex, try exact match
                if pattern.lower() == qrc_file.lower():
                    return pattern
        return None
    
    def _find_violations(self, all_qrc_files: List[str], forbidden_patterns: List[str]) -> List[Tuple[str, str]]:
        """
        Find QRC files that match forbidden patterns.
        
        Args:
            all_qrc_files: All QRC file paths from input files
            forbidden_patterns: Forbidden QRC file patterns (regex)
        
        Returns:
            List of (qrc_file, matched_pattern) tuples
        """
        violations = []
        for qrc_file in all_qrc_files:
            matched_pattern = self._match_forbidden_pattern(qrc_file, forbidden_patterns)
            if matched_pattern:
                violations.append((qrc_file, matched_pattern))
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
        if self.root is None:
            raise RuntimeError("Checker not initialized. Call init_checker() first.")
        
        try:
            # Get forbidden QRC file patterns
            requirements = self.get_requirements()
            self._forbidden_patterns = requirements.get('pattern_items', []) if requirements else []
            
            # Detect checker type (use BaseChecker method)
            checker_type = self.detect_checker_type()
            
            # Parse input files to extract QRC files
            all_qrc_files = self._parse_input_files()
            
            # Find violations (QRC files matching forbidden patterns)
            violations = []
            if self._forbidden_patterns:
                violations = self._find_violations(all_qrc_files, self._forbidden_patterns)
            
            # Execute based on type
            if checker_type == 1:
                return self._execute_type1(all_qrc_files, violations)
            elif checker_type == 2:
                return self._execute_type2(all_qrc_files, violations)
            elif checker_type == 3:
                return self._execute_type3(all_qrc_files, violations)
            else:  # checker_type == 4
                return self._execute_type4(all_qrc_files, violations)
        
        except ConfigurationError as e:
            # Return the CheckResult from the exception
            return e.check_result
    
    # =========================================================================
    # Type 1: Boolean Check (No Waiver Logic)
    # =========================================================================
    
    def _execute_type1(self, all_qrc_files: List[str], violations: List[Tuple[str, str]]) -> CheckResult:
        """
        Type 1: requirements.value=N/A, waivers.value=N/A/0
        
        Logic: 
        - Check if QRC tech files are being used for RC data
        - Both QRC usage and non-usage are valid PASS conditions
        - All items shown as INFO
        """
        waivers = self.get_waivers()
        waiver_value = waivers.get('value', 'N/A') if waivers else 'N/A'
        waive_items = waivers.get('waive_items', []) if waivers else []
        
        # Check if waiver=0 (display mode)
        is_waiver_zero = (waiver_value == 0)
        
        # Check for missing input files first
        missing_info = self._qrc_metadata.get('_missing_input_files')
        if missing_info:
            return self.create_missing_files_error(missing_info['files'])
        
        details = []
        
        # Case 1: No QRC files found - synthesis isn't using QRC (PASS)
        if not all_qrc_files:
            details.append(DetailItem(
                severity=Severity.INFO,
                name="No QRC tech files detected",
                line_number=0,
                file_path="N/A",
                reason="synthesis isn't using qrc tech file for RC data"
            ))
            
            return create_check_result(
                value=0,
                is_pass=True,
                has_pattern_items=False,
                has_waiver_value=bool(waive_items),
                details=details,
                item_desc=self.item_desc,
                info_groups={
                    "INFO01": {
                        "description": "Synthesis is NOT using QRC tech files for RC data",
                        "items": ["No QRC tech files detected"]
                    }
                }
            )
        
        # Case 2: QRC files detected - Design IS using QRC (PASS)
        # Show all QRC files as INFO
        for qrc_file in all_qrc_files:
            metadata = self._qrc_metadata.get(qrc_file, {})
            details.append(DetailItem(
                severity=Severity.INFO,
                name=qrc_file,
                line_number=metadata.get('line_number', ''),
                file_path=metadata.get('file_path', ''),
                reason="synthesis is using qrc tech file for RC data"
            ))
        
        # Add waive_items as INFO (display only)
        if waive_items and not is_waiver_zero:
            for item in waive_items:
                details.append(DetailItem(
                    severity=Severity.INFO,
                    name=str(item),
                    line_number=0,
                    file_path="N/A",
                    reason="Waiver"
                ))
        
        if is_waiver_zero:
            # waiver=0: Force PASS, add waive_items
            for item in waive_items:
                details.append(DetailItem(
                    severity=Severity.INFO,
                    name=str(item),
                    line_number=0,
                    file_path="N/A",
                    reason="Waiver item[WAIVED_INFO]"
                ))
        
        # Create info groups
        info_groups = {
            "INFO01": {
                "description": "QRC tech files detected (design IS using QRC for RC data)",
                "items": all_qrc_files
            }
        }
        
        return create_check_result(
            value=len(all_qrc_files),
            is_pass=True,
            has_pattern_items=False,
            has_waiver_value=bool(waive_items),
            details=details,
            info_groups=info_groups,
            item_desc=self.item_desc
        )
    
    # =========================================================================
    # Type 2: Numeric Comparison (No Waiver Logic)
    # =========================================================================
    
    def _execute_type2(self, all_qrc_files: List[str], violations: List[Tuple[str, str]]) -> CheckResult:
        """
        Type 2: requirements.value>0, pattern_items exists, waivers.value=N/A/0
        
        Logic: 
        - Compare violation count against expected value
        - violations = QRC files matching forbidden patterns
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
        
        # Check if waiver=0 (display mode)
        is_waiver_zero = (waiver_value == 0)
        
        # Check for missing input files first
        missing_info = self._qrc_metadata.get('_missing_input_files')
        if missing_info:
            return self.create_missing_files_error(missing_info['files'])
        
        details = []
        
        # Find unmatched patterns (good - not found)
        violated_patterns = set(pattern for _, pattern in violations)
        unmatched_patterns = [p for p in self._forbidden_patterns if p not in violated_patterns]
        
        if is_waiver_zero:
            # waiver=0: Force PASS, all violations become INFO
            for qrc_file, pattern in violations:
                metadata = self._qrc_metadata.get(qrc_file, {})
                details.append(DetailItem(
                    severity=Severity.INFO,
                    name=qrc_file,
                    line_number=metadata.get('line_number', ''),
                    file_path=metadata.get('file_path', ''),
                    reason=f"Matches pattern: {pattern}[WAIVED_AS_INFO]"
                ))
            
            for item in waive_items:
                details.append(DetailItem(
                    severity=Severity.INFO,
                    name=str(item),
                    line_number=0,
                    file_path="N/A",
                    reason="Waiver item[WAIVED_INFO]"
                ))
            
            is_pass = True
        else:
            # Normal mode: violations = FAIL
            for qrc_file, pattern in violations:
                metadata = self._qrc_metadata.get(qrc_file, {})
                details.append(DetailItem(
                    severity=Severity.FAIL,
                    name=qrc_file,
                    line_number=metadata.get('line_number', ''),
                    file_path=metadata.get('file_path', ''),
                    reason=f"Matches forbidden pattern: {pattern}"
                ))
            
            # Unmatched patterns = INFO (good)
            for pattern in unmatched_patterns:
                details.append(DetailItem(
                    severity=Severity.INFO,
                    name=pattern,
                    line_number='',
                    file_path='',
                    reason="Pattern not found (good)"
                ))
            
            is_pass = (len(violations) == expected_value)
        
        return create_check_result(
            value=len(violations),
            is_pass=is_pass,
            has_pattern_items=True,
            has_waiver_value=bool(waive_items),
            details=details,
            item_desc=self.item_desc,
            default_group_desc="Forbidden QRC files found"
        )
    
    # =========================================================================
    # Type 3: Numeric Comparison WITH Waiver Logic
    # =========================================================================
    
    def _execute_type3(self, all_qrc_files: List[str], violations: List[Tuple[str, str]]) -> CheckResult:
        """
        Type 3: requirements.value>0, pattern_items exists, waivers.value>0
        
        Logic: 
        - Classify violations into waived/unwaived
        - PASS if all violations are waived
        - FAIL if unwaived violations exist
        - WARN for unused waivers
        """
        waivers = self.get_waivers()
        waive_items_dict = self._get_waive_items_with_reasons()
        waive_items = list(waive_items_dict.keys())
        
        # Check for missing input files first
        missing_info = self._qrc_metadata.get('_missing_input_files')
        if missing_info:
            return self.create_missing_files_error(missing_info['files'])
        
        # Classify violations
        waive_set = set(waive_items)
        unwaived = [(qrc, pattern) for qrc, pattern in violations if qrc not in waive_set]
        waived = [(qrc, pattern) for qrc, pattern in violations if qrc in waive_set]
        
        # Find unused waivers
        violated_files = set(qrc for qrc, _ in violations)
        unused_waivers = [item for item in waive_items if item not in violated_files]
        
        # Find unmatched patterns
        violated_patterns = set(pattern for _, pattern in violations)
        unmatched_patterns = [p for p in self._forbidden_patterns if p not in violated_patterns]
        
        details = []
        
        # ERROR: Unwaived violations
        for qrc_file, pattern in unwaived:
            metadata = self._qrc_metadata.get(qrc_file, {})
            details.append(DetailItem(
                severity=Severity.FAIL,
                name=qrc_file,
                line_number=metadata.get('line_number', ''),
                file_path=metadata.get('file_path', ''),
                reason=f"Matches forbidden pattern: {pattern}"
            ))
        
        # INFO: Waived violations
        for qrc_file, pattern in waived:
            metadata = self._qrc_metadata.get(qrc_file, {})
            waiver_reason = waive_items_dict.get(qrc_file, '')
            reason = f"{waiver_reason}[WAIVER]" if waiver_reason else "Waived[WAIVER]"
            details.append(DetailItem(
                severity=Severity.INFO,
                name=qrc_file,
                line_number=metadata.get('line_number', ''),
                file_path=metadata.get('file_path', ''),
                reason=reason
            ))
        
        # INFO: Unmatched patterns
        for pattern in unmatched_patterns:
            details.append(DetailItem(
                severity=Severity.INFO,
                name=pattern,
                line_number='',
                file_path='',
                reason="Pattern not found (good)"
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
        
        # Create groups
        error_groups = {}
        warn_groups = {}
        info_groups = {}
        
        if unwaived:
            error_groups["ERROR01"] = {
                "description": "Unwaived forbidden QRC files",
                "items": [qrc for qrc, _ in unwaived]
            }
        
        if unused_waivers:
            warn_groups["WARN01"] = {
                "description": "Unused waivers",
                "items": unused_waivers
            }
        
        info_items = []
        if waived:
            info_items.extend([qrc for qrc, _ in waived])
        if unmatched_patterns:
            info_items.extend(unmatched_patterns)
        
        if info_items:
            info_groups["INFO01"] = {
                "description": "Waived violations and unmatched patterns (good)",
                "items": info_items
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
    # Type 4: Boolean Check WITH Waiver Logic
    # =========================================================================
    
    def _execute_type4(self, all_qrc_files: List[str], violations: List[Tuple[str, str]]) -> CheckResult:
        """
        Type 4: requirements.value=N/A, waivers.value>0
        
        Logic: 
        - Boolean determination with waiver classification
        - PASS if all violations are waived
        - FAIL if unwaived violations exist
        - WARN for unused waivers
        """
        waivers = self.get_waivers()
        waive_items_dict = self._get_waive_items_with_reasons()
        waive_items = list(waive_items_dict.keys())
        
        # Check for missing input files first
        missing_info = self._qrc_metadata.get('_missing_input_files')
        if missing_info:
            return self.create_missing_files_error(missing_info['files'])
        
        # Classify violations
        waive_set = set(waive_items)
        unwaived = [(qrc, pattern) for qrc, pattern in violations if qrc not in waive_set]
        waived = [(qrc, pattern) for qrc, pattern in violations if qrc in waive_set]
        
        # Find unused waivers
        violated_files = set(qrc for qrc, _ in violations)
        unused_waivers = [item for item in waive_items if item not in violated_files]
        
        details = []
        
        # ERROR: Unwaived violations
        for qrc_file, pattern in sorted(unwaived):
            metadata = self._qrc_metadata.get(qrc_file, {})
            details.append(DetailItem(
                severity=Severity.FAIL,
                name=qrc_file,
                line_number=metadata.get('line_number', ''),
                file_path=metadata.get('file_path', ''),
                reason=f"Violation found: {pattern if pattern else 'Not using QRC for RC'}"
            ))
        
        # INFO: Waived violations
        for qrc_file, pattern in sorted(waived):
            metadata = self._qrc_metadata.get(qrc_file, {})
            waiver_reason = waive_items_dict.get(qrc_file, '')
            reason = f"{waiver_reason}[WAIVER]" if waiver_reason else "Waived[WAIVER]"
            details.append(DetailItem(
                severity=Severity.INFO,
                name=qrc_file,
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
        
        # Create groups
        error_groups = {}
        warn_groups = {}
        info_groups = {}
        
        if unwaived:
            error_groups["ERROR01"] = {
                "description": "Unwaived violations",
                "items": [qrc for qrc, _ in sorted(unwaived)]
            }
        
        if unused_waivers:
            warn_groups["WARN01"] = {
                "description": "Unused waivers",
                "items": unused_waivers
            }
        
        if waived:
            info_groups["INFO01"] = {
                "description": "Waived violations (approved exceptions)",
                "items": [qrc for qrc, _ in sorted(waived)]
            }
        
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
        Get waive items with their reasons.
        
        Supports both formats:
        - List of dicts: [{"name": "item", "reason": "why"}]
        - List of strings: ["item ; # reason", "item, # reason"]
        
        Returns:
            Dict mapping waive_item to reason string
        """
        waivers = self.get_waivers()
        if not waivers:
            return {}
        
        waive_items = waivers.get('waive_items', [])
        
        # If waive_items is a list of dicts with 'name' and 'reason'
        if waive_items and isinstance(waive_items[0], dict):
            return {item['name']: item.get('reason', '') for item in waive_items}
        
        # If waive_items is a simple list of strings
        result = {}
        for item in waive_items:
            item_str = str(item).strip()
            # Support both comma and semicolon separators
            if ';' in item_str:
                parts = item_str.split(';', 1)
                name = parts[0].strip()
                reason = parts[1].strip() if len(parts) > 1 else ""
                if reason.startswith('#'):
                    reason = reason[1:].strip()
                result[name] = reason
            elif ',' in item_str:
                parts = item_str.split(',', 1)
                name = parts[0].strip()
                reason = parts[1].strip() if len(parts) > 1 else ""
                if reason.startswith('#'):
                    reason = reason[1:].strip()
                result[name] = reason
            else:
                result[item_str] = ""
        
        return result


def main():
    """Main entry point for the checker."""
    checker = QRCChecker()
    checker.run()


if __name__ == '__main__':
    main()
