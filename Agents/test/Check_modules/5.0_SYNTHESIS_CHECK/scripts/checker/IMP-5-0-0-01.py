################################################################################
# Script Name: IMP-5-0-0-01.py
#
# Purpose:
#   Confirm synthesis is using LEF data for PLE optimization.
#   Parse input files to identify LEF file usage (.lef and .tlef files).
#
# Logic:
#   - Extract all .lef and .tlef file references from input files
#   - Check LEF file usage for PLE optimization
#   - Type 2/3: Support forbidden LEF file patterns
#
# Auto Type Detection:
#   Type 1: requirements.value=N/A, waivers.value=N/A/0 → Boolean check
#   Type 2: requirements.value>0, pattern_items exists, waivers.value=N/A/0 → Value comparison
#   Type 3: requirements.value>0, pattern_items exists, waivers.value>0 → Value with waiver logic
#   Type 4: requirements.value=N/A, waivers.value>0 → Boolean with waiver logic
#
# Author: yuyin
# Date: 2025-11-25
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


class LEFChecker(BaseChecker):
    """
    Unified checker that auto-detects and handles all 4 checker types.
    
    Check Target: Confirm synthesis is using LEF data for PLE optimization
    
    Type Detection Logic:
    - Type 1: requirements.value=N/A AND waivers.value=N/A/0
    - Type 2: requirements.value>0 AND pattern_items AND waivers.value=N/A/0
    - Type 3: requirements.value>0 AND pattern_items AND waivers.value>0
    - Type 4: requirements.value=N/A AND waivers.value>0
    
    Parsing Logic:
    - Extract all .lef and .tlef file references from input files
    - Store LEF file name and line number
    - Type 1: Check if LEF files are being used
    - Type 2/3: Match against forbidden LEF file patterns
    """
    
    def __init__(self):
        super().__init__(
            check_module="5.0_SYNTHESIS_CHECK",
            item_id="IMP-5-0-0-01",
            item_desc="Confirm synthesis is using lef data for PLE optimization?"
        )
        self._lef_metadata: Dict[str, Dict[str, Any]] = {}
        self._forbidden_patterns: List[str] = []
    
    # =========================================================================
    # Input File Parsing
    # =========================================================================
    
    def _parse_input_files(self) -> List[str]:
        """
        Parse input files to extract all .lef and .tlef file references.
        
        Format: Extract LEF file paths from any line
        Example: "read_physical -lef /path/to/file.lef"
                 "set_attribute lef_library {tech.lef macro.tlef}"
        
        Returns:
            List of all LEF file names found
        """
        if not self.item_data or 'input_files' not in self.item_data:
            return []
        
        # Validate input files using BaseChecker method
        valid_files, missing_files = self.validate_input_files()
        
        # Store missing files for error reporting
        if missing_files:
            self._lef_metadata['_missing_input_files'] = {
                'files': missing_files,
                'count': len(missing_files)
            }
            # Return empty list - will be handled in execute methods
            return []
        
        all_lef_files = []
        seen_files = set()
        
        # Pattern to extract .lef and .tlef file paths
        lef_pattern = re.compile(r'(?P<full>[A-Za-z0-9._/\\-]+\.(?:lef|tlef))', re.IGNORECASE)
        
        for file_path in valid_files:
            
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            for line_num, line in enumerate(lines, 1):
                # Extract .lef and .tlef file references
                for match in lef_pattern.finditer(line):
                    lef_file = match.group('full').strip('[](){}",;')
                    
                    # Only add if not already seen
                    if lef_file not in seen_files:
                        seen_files.add(lef_file)
                        all_lef_files.append(lef_file)
                        
                        # Store metadata
                        self._lef_metadata[lef_file] = {
                            'line_number': line_num,
                            'file_path': str(file_path)
                        }
        
        return all_lef_files
    
    def _match_forbidden_pattern(self, lef_file: str, patterns: List[str]) -> Optional[str]:
        """
        Check if LEF file matches any forbidden pattern.
        
        Supports both glob patterns and regex:
        - Glob: *tech_lef* -> matches anything containing tech_lef
        - Regex: ^.*old_version.*\\.lef$ -> matches specific pattern
        
        Args:
            lef_file: LEF file name to check
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
                if re.search(regex_pattern, lef_file, re.IGNORECASE):
                    return pattern
            except re.error:
                # If pattern is not valid regex, try exact match
                if pattern.lower() == lef_file.lower():
                    return pattern
        return None
    
    def _find_violations(self, all_lef_files: List[str], forbidden_patterns: List[str]) -> List[Tuple[str, str]]:
        """
        Find LEF files that match forbidden patterns.
        
        Args:
            all_lef_files: All LEF file names from input files
            forbidden_patterns: Forbidden LEF file patterns (regex)
        
        Returns:
            List of (lef_file, matched_pattern) tuples
        """
        violations = []
        for lef_file in all_lef_files:
            matched_pattern = self._match_forbidden_pattern(lef_file, forbidden_patterns)
            if matched_pattern:
                violations.append((lef_file, matched_pattern))
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
            # Get forbidden LEF file patterns
            requirements = self.get_requirements()
            self._forbidden_patterns = requirements.get('pattern_items', []) if requirements else []
            
            # Detect checker type (use BaseChecker method)
            checker_type = self.detect_checker_type()
            
            # Parse input files to extract LEF files
            all_lef_files = self._parse_input_files()
            
            # Find violations (LEF files matching forbidden patterns)
            violations = []
            if self._forbidden_patterns:
                violations = self._find_violations(all_lef_files, self._forbidden_patterns)
            
            # Execute based on type
            if checker_type == 1:
                return self._execute_type1(all_lef_files, violations)
            elif checker_type == 2:
                return self._execute_type2(all_lef_files, violations)
            elif checker_type == 3:
                return self._execute_type3(all_lef_files, violations)
            else:  # checker_type == 4
                return self._execute_type4(all_lef_files, violations)
        
        except ConfigurationError as e:
            # Return the CheckResult from the exception
            return e.check_result
    
    # =========================================================================
    # Type 1: Boolean Check (No Waiver Logic)
    # =========================================================================
    
    def _execute_type1(self, all_lef_files: List[str], violations: List[Tuple[str, str]]) -> CheckResult:
        """
        Type 1: requirements.value=N/A, waivers.value=N/A/0
        
        Logic: 
        - Check if LEF files are being used for PLE optimization
        - Check lib_lef_consistency_check_enable setting
        - If "false" detected OR no LEF files -> Not using LEF
        - All items shown as INFO
        """
        waivers = self.get_waivers()
        waiver_value = waivers.get('value', 'N/A') if waivers else 'N/A'
        waive_items = waivers.get('waive_items', []) if waivers else []
        
        # Check if waiver=0 (display mode)
        is_waiver_zero = (waiver_value == 0)
        
        # Check for missing input files first
        missing_info = self._lef_metadata.get('_missing_input_files')
        if missing_info:
            return self.create_missing_files_error(missing_info['files'])
        
        details = []
        
        # Check if lib_lef_consistency_check_enable is set to false
        has_false_setting = self._check_lef_consistency_disabled()
        
        # Case 1: lib_lef_consistency_check_enable is explicitly false
        if has_false_setting:
            file_path, line_num = self._find_lef_consistency_setting()
            details.append(DetailItem(
                severity=Severity.INFO,
                name="lib_lef_consistency_check_enable=false",
                line_number=line_num,
                file_path=str(file_path),
                reason="Set to false - Design is NOT using LEF data for PLE optimization"
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
                        "description": "Design is NOT using LEF for PLE optimization (lib_lef_consistency_check_enable = false)",
                        "items": ["lib_lef_consistency_check_enable=false"]
                    }
                }
            )
        
        # Case 2: No LEF files found
        if not all_lef_files:
            details.append(DetailItem(
                severity=Severity.INFO,
                name="No LEF files detected",
                line_number=0,
                file_path="N/A",
                reason="Design may not be using LEF data for PLE optimization"
            ))
            
            return create_check_result(
                value=0,
                is_pass=True,
                has_pattern_items=False,
                has_waiver_value=bool(waive_items),
                details=details,
                item_desc=self.item_desc,
                default_group_desc="No LEF files found"
            )
        
        # Case 3: LEF files detected - Design IS using LEF
        # Show all LEF files as INFO
        for lef_file in all_lef_files:
            metadata = self._lef_metadata.get(lef_file, {})
            details.append(DetailItem(
                severity=Severity.INFO,
                name=lef_file,
                line_number=metadata.get('line_number', ''),
                file_path=metadata.get('file_path', ''),
                reason="LEF file is being used for PLE optimization"
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
                "description": "LEF files detected (design IS using LEF for PLE optimization)",
                "items": all_lef_files
            }
        }
        
        return create_check_result(
            value=len(all_lef_files),
            is_pass=True,
            has_pattern_items=False,
            has_waiver_value=bool(waive_items),
            details=details,
            info_groups=info_groups,
            item_desc=self.item_desc
        )
    
    def _check_lef_consistency_disabled(self) -> bool:
        """
        Check if lib_lef_consistency_check_enable is set to false.
        
        Returns:
            True if found "lib_lef_consistency_check_enable false"
            False otherwise
        """
        if not self.item_data or 'input_files' not in self.item_data:
            return False
        
        input_files = self.item_data['input_files']
        if isinstance(input_files, str):
            input_files = [input_files]
        
        false_pattern = re.compile(r'lib_lef_consistency_check_enable\s+(false)', re.IGNORECASE)
        
        for file_path_str in input_files:
            file_path = Path(file_path_str)
            if not file_path.exists():
                continue
            
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    if false_pattern.search(line):
                        return True
        
        return False
    
    def _find_lef_consistency_setting(self) -> Tuple[Path, int]:
        """
        Find the line where lib_lef_consistency_check_enable is set.
        
        Returns:
            Tuple of (file_path, line_number)
        """
        if not self.item_data or 'input_files' not in self.item_data:
            return (Path("N/A"), 0)
        
        input_files = self.item_data['input_files']
        if isinstance(input_files, str):
            input_files = [input_files]
        
        pattern = re.compile(r'lib_lef_consistency_check_enable\s+(false|true)', re.IGNORECASE)
        
        for file_path_str in input_files:
            file_path = Path(file_path_str)
            if not file_path.exists():
                continue
            
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line_num, line in enumerate(f, 1):
                    if pattern.search(line):
                        return (file_path, line_num)
        
        return (Path(input_files[0]) if input_files else Path("N/A"), 0)
    
    # =========================================================================
    # Type 2: Numeric Comparison (No Waiver Logic)
    # =========================================================================
    
    def _execute_type2(self, all_lef_files: List[str], violations: List[Tuple[str, str]]) -> CheckResult:
        """
        Type 2: requirements.value>0, pattern_items exists, waivers.value=N/A/0
        
        Logic: 
        - Compare violation count against expected value
        - violations = LEF files matching forbidden patterns
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
        missing_info = self._lef_metadata.get('_missing_input_files')
        if missing_info:
            return self.create_missing_files_error(missing_info['files'])
        
        details = []
        
        # Find unmatched patterns (good - not found)
        violated_patterns = set(pattern for _, pattern in violations)
        unmatched_patterns = [p for p in self._forbidden_patterns if p not in violated_patterns]
        
        if is_waiver_zero:
            # waiver=0: Force PASS, all violations become INFO
            for lef_file, pattern in violations:
                metadata = self._lef_metadata.get(lef_file, {})
                details.append(DetailItem(
                    severity=Severity.INFO,
                    name=lef_file,
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
            for lef_file, pattern in violations:
                metadata = self._lef_metadata.get(lef_file, {})
                details.append(DetailItem(
                    severity=Severity.FAIL,
                    name=lef_file,
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
            default_group_desc="Forbidden LEF files found"
        )
    
    # =========================================================================
    # Type 3: Numeric Comparison WITH Waiver Logic
    # =========================================================================
    
    def _execute_type3(self, all_lef_files: List[str], violations: List[Tuple[str, str]]) -> CheckResult:
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
        missing_info = self._lef_metadata.get('_missing_input_files')
        if missing_info:
            return self.create_missing_files_error(missing_info['files'])
        
        # Classify violations
        waive_set = set(waive_items)
        unwaived = [(lef, pattern) for lef, pattern in violations if lef not in waive_set]
        waived = [(lef, pattern) for lef, pattern in violations if lef in waive_set]
        
        # Find unused waivers
        violated_files = set(lef for lef, _ in violations)
        unused_waivers = [item for item in waive_items if item not in violated_files]
        
        # Find unmatched patterns
        violated_patterns = set(pattern for _, pattern in violations)
        unmatched_patterns = [p for p in self._forbidden_patterns if p not in violated_patterns]
        
        details = []
        
        # ERROR: Unwaived violations
        for lef_file, pattern in unwaived:
            metadata = self._lef_metadata.get(lef_file, {})
            details.append(DetailItem(
                severity=Severity.FAIL,
                name=lef_file,
                line_number=metadata.get('line_number', ''),
                file_path=metadata.get('file_path', ''),
                reason=f"Matches forbidden pattern: {pattern}"
            ))
        
        # INFO: Waived violations
        for lef_file, pattern in waived:
            metadata = self._lef_metadata.get(lef_file, {})
            waiver_reason = waive_items_dict.get(lef_file, '')
            reason = f"{waiver_reason}[WAIVER]" if waiver_reason else "Waived[WAIVER]"
            details.append(DetailItem(
                severity=Severity.INFO,
                name=lef_file,
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
                "description": "Unwaived forbidden LEF files",
                "items": [lef for lef, _ in unwaived]
            }
        
        if unused_waivers:
            warn_groups["WARN01"] = {
                "description": "Unused waivers",
                "items": unused_waivers
            }
        
        info_items = []
        if waived:
            info_items.extend([lef for lef, _ in waived])
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
    
    def _execute_type4(self, all_lef_files: List[str], violations: List[Tuple[str, str]]) -> CheckResult:
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
        missing_info = self._lef_metadata.get('_missing_input_files')
        if missing_info:
            return self.create_missing_files_error(missing_info['files'])
        
        # Classify violations
        waive_set = set(waive_items)
        unwaived = [(lef, pattern) for lef, pattern in violations if lef not in waive_set]
        waived = [(lef, pattern) for lef, pattern in violations if lef in waive_set]
        
        # Find unused waivers
        violated_files = set(lef for lef, _ in violations)
        unused_waivers = [item for item in waive_items if item not in violated_files]
        
        details = []
        
        # ERROR: Unwaived violations
        for lef_file, pattern in sorted(unwaived):
            metadata = self._lef_metadata.get(lef_file, {})
            details.append(DetailItem(
                severity=Severity.FAIL,
                name=lef_file,
                line_number=metadata.get('line_number', ''),
                file_path=metadata.get('file_path', ''),
                reason=f"Violation found: {pattern if pattern else 'Not using LEF for PLE'}"
            ))
        
        # INFO: Waived violations
        for lef_file, pattern in sorted(waived):
            metadata = self._lef_metadata.get(lef_file, {})
            waiver_reason = waive_items_dict.get(lef_file, '')
            reason = f"{waiver_reason}[WAIVER]" if waiver_reason else "Waived[WAIVER]"
            details.append(DetailItem(
                severity=Severity.INFO,
                name=lef_file,
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
                "items": [lef for lef, _ in sorted(unwaived)]
            }
        
        if unused_waivers:
            warn_groups["WARN01"] = {
                "description": "Unused waivers",
                "items": unused_waivers
            }
        
        if waived:
            info_groups["INFO01"] = {
                "description": "Waived violations (approved exceptions)",
                "items": [lef for lef, _ in sorted(waived)]
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
        return result


def main():
    """Main entry point for the checker."""
    checker = LEFChecker()
    checker.run()


if __name__ == '__main__':
    main()

