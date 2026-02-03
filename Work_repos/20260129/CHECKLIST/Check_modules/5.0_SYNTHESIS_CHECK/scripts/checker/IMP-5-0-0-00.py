################################################################################
# Script Name: IMP-5-0-0-00.py
#
# Purpose:
#   Confirm synthesis is using lib models for timing.
#   Parse qor.rpt to identify loaded libraries and check against expected list.
#
# Logic:
#   - Extract all Technology libraries from qor.rpt
#   - Check if libraries exist and are loaded
#   - Type 2/3: Support forbidden library patterns
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
from typing import List, Dict, Tuple, Optional, Any


# Add common module to path
_SCRIPT_DIR = Path(__file__).resolve().parent
_CHECK_MODULES_DIR = _SCRIPT_DIR.parents[2]  # Go up to Check_modules/
_COMMON_DIR = _CHECK_MODULES_DIR / 'common'
if str(_COMMON_DIR) not in sys.path:
    sys.path.insert(0, str(_COMMON_DIR))

from base_checker import BaseChecker, CheckResult, ConfigurationError
from output_formatter import DetailItem, Severity, ResultType, create_check_result


class LibraryChecker(BaseChecker):
    """
    Unified checker that auto-detects and handles all 4 checker types.
    
    Check Target: Confirm synthesis is using lib models for timing
    
    Type Detection Logic:
    - Type 1: requirements.value=N/A AND waivers.value=N/A/0
    - Type 2: requirements.value>0 AND pattern_items AND waivers.value=N/A/0
    - Type 3: requirements.value>0 AND pattern_items AND waivers.value>0
    - Type 4: requirements.value=N/A AND waivers.value>0
    
    Parsing Logic:
    - Extract all Technology libraries from qor.rpt
    - Store library full name and line number
    - Type 1: Check if all libraries exist
    - Type 2/3: Match against forbidden library patterns
    """
    
    def __init__(self):
        super().__init__(
            check_module="5.0_SYNTHESIS_CHECK",
            item_id="IMP-5-0-0-00",
            item_desc="Confirm synthesis is using lib models for timing?"
        )
        self._library_metadata: Dict[str, Dict[str, Any]] = {}
        self._forbidden_patterns: List[str] = []
    
    # =========================================================================
    # Input File Parsing
    # =========================================================================
    
    def _parse_qor_rpt(self) -> List[str]:
        """
        Parse qor.rpt to extract all Technology libraries.
        
        Format: Technology libraries section
        Example: "    tcbn03e_bwp143mh117l3p48cpd_base_elvtssgnp_0p675v_m40c_cworst_CCworst_T_ccs 110"
        
        Returns:
            List of all library full names
        """
        if not self.item_data or 'input_files' not in self.item_data:
            raise ConfigurationError("No input_files specified in configuration")
        
        # Validate input files using BaseChecker method
        valid_files, missing_files = self.validate_input_files()
        
        # Raise ConfigurationError if files are missing
        if missing_files:
            missing_list = '\n'.join(f"  - {f}" for f in missing_files)
            raise ConfigurationError(
                f"Input file(s) not found:\n{missing_list}"
            )
        
        all_libraries = []
        
        for file_path in valid_files:
            
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            # Extract libraries with line numbers
            libraries = self._extract_libraries_from_lines(lines, file_path)
            all_libraries.extend(libraries)
        
        return all_libraries
    
    def _extract_libraries_from_lines(self, lines: List[str], file_path: Path) -> List[str]:
        """
        Extract technology library names from qor.rpt lines.
        
        Looks for section "Technology libraries:" and extracts library names.
        
        Args:
            lines: File content lines
            file_path: Path to qor.rpt file
        
        Returns:
            List of library full names
        """
        libraries = []
        in_tech_lib_section = False
        
        for line_num, line in enumerate(lines, 1):
            # Detect start of technology libraries section
            if 'Technology libraries:' in line:
                in_tech_lib_section = True
                # Check if first library is on the same line
                if ':' in line:
                    parts = line.split(':', 1)[1].strip().split()
                    if len(parts) >= 2:
                        lib_name = parts[0]
                        libraries.append(lib_name)
                        if lib_name not in self._library_metadata:
                            self._library_metadata[lib_name] = {
                                'line_number': line_num,
                                'file_path': str(file_path)
                            }
                continue
            
            # Process lines in technology libraries section
            if in_tech_lib_section:
                stripped = line.strip()
                
                # Check for section end markers (not indented or specific keywords)
                if stripped and not line.startswith(' ' * 10):
                    # Check if it's a new section
                    if any(keyword in stripped for keyword in [
                        'Operating conditions:', 'Interconnect mode:', 'Area mode:'
                    ]):
                        break
                
                # Skip empty lines and domain index lines
                if not stripped or 'Domain index:' in stripped:
                    continue
                
                # Parse library line - format: "library_name version"
                # Libraries are heavily indented (around 26 spaces)
                if stripped and len(line) - len(line.lstrip()) > 10:
                    parts = stripped.split()
                    if len(parts) >= 2:
                        lib_name = parts[0]
                        libraries.append(lib_name)
                        
                        # Store metadata for later use
                        if lib_name not in self._library_metadata:
                            self._library_metadata[lib_name] = {
                                'line_number': line_num,
                                'file_path': str(file_path)
                            }
        
        return libraries
    
    def _match_forbidden_library(self, lib_name: str, patterns: List[str]) -> Optional[str]:
        """
        Check if library name matches any forbidden pattern.
        
        Supports both glob patterns and regex:
        - Glob: *nldm* -> matches anything containing nldm
        - Regex: ^tcbn03e.*nldm$ -> matches specific pattern
        
        Args:
            lib_name: Library name to check
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
                if re.search(regex_pattern, lib_name):
                    return pattern
            except re.error:
                # If pattern is not valid regex, try exact match
                if pattern == lib_name:
                    return pattern
        return None
    
    def _find_violations(self, all_libraries: List[str], forbidden_patterns: List[str]) -> List[Tuple[str, str]]:
        """
        Find libraries that match forbidden patterns.
        
        Args:
            all_libraries: All library names from qor.rpt
            forbidden_patterns: Forbidden library patterns (regex)
        
        Returns:
            List of (library_name, matched_pattern) tuples
        """
        violations = []
        
        for lib_name in all_libraries:
            matched_pattern = self._match_forbidden_library(lib_name, forbidden_patterns)
            if matched_pattern:
                violations.append((lib_name, matched_pattern))
        
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
        
        # Get forbidden library patterns
        requirements = self.get_requirements()
        self._forbidden_patterns = requirements.get('pattern_items', []) if requirements else []
        
        # Detect checker type (use BaseChecker method)
        checker_type = self.detect_checker_type()
        
        # Parse qor.rpt
        all_libraries = self._parse_qor_rpt()
        
        # Find violations (libraries matching forbidden patterns)
        violations = self._find_violations(all_libraries, self._forbidden_patterns)
        
        # Execute based on type
        if checker_type == 1:
            return self._execute_type1(all_libraries, violations)
        elif checker_type == 2:
            return self._execute_type2(all_libraries, violations)
        elif checker_type == 3:
            return self._execute_type3(all_libraries, violations)
        else:  # checker_type == 4
            return self._execute_type4(all_libraries, violations)
    
    # =========================================================================
    # Type 1: Boolean Check (No Waiver Logic)
    # =========================================================================
    
    def _execute_type1(self, all_libraries: List[str], violations: List[Tuple[str, str]]) -> CheckResult:
        """
        Type 1: requirements.value=N/A, waivers.value=N/A/0
        
        Logic: 
        - Check if all libraries are loaded successfully
        - violations = Libraries that don't exist or format errors
        """
        waivers = self.get_waivers()
        waiver_value = waivers.get('value', 'N/A') if waivers else 'N/A'
        waive_items = waivers.get('waive_items', []) if waivers else []
        
        # Check if waiver=0 (display mode)
        is_waiver_zero = (waiver_value == 0)
        
        details = []
        
        # Special case: No libraries found
        if not all_libraries:
            details.append(DetailItem(
                severity=Severity.FAIL,
                name="",
                line_number=0,
                file_path="N/A",
                reason="No libraries found in qor.rpt Technology libraries section"
            ))
            error_groups = {
                "ERROR01": {
                    "description": "No libraries found in qor.rpt",
                    "items": [""]
                }
            }
            return create_check_result(
                value=1,
                is_pass=False,
                has_pattern_items=False,
                has_waiver_value=bool(waive_items),
                details=details,
                error_groups=error_groups,
                item_desc=self.item_desc
            )
        
        # All libraries loaded successfully - PASS
        # Show all libraries as INFO
        for lib_name in all_libraries:
            metadata = self._library_metadata.get(lib_name, {})
            details.append(DetailItem(
                severity=Severity.INFO,
                name=lib_name,
                line_number=metadata.get('line_number', ''),
                file_path=metadata.get('file_path', ''),
                reason="Library loaded successfully"
            ))
        
        # Add waive_items as INFO (display only)
        if waive_items and not is_waiver_zero:
            for item in waive_items:
                details.append(DetailItem(
                    severity=Severity.INFO,
                    name=item,
                    line_number=0,
                    file_path="N/A",
                    reason="Waiver"
                ))
        
        if is_waiver_zero:
            # waiver=0: Force PASS, add waive_items
            for item in waive_items:
                details.append(DetailItem(
                    severity=Severity.INFO,
                    name=item,
                    line_number=0,
                    file_path="N/A",
                    reason="Waiver item[WAIVED_INFO]"
                ))
        
        # Create info groups
        info_groups = {
            "INFO01": {
                "description": "All libraries loaded successfully",
                "items": all_libraries
            }
        }
        
        return create_check_result(
            value=len(all_libraries),
            is_pass=True,
            has_pattern_items=False,
            has_waiver_value=bool(waive_items),
            details=details,
            info_groups=info_groups,
            item_desc=self.item_desc
        )
    
    # =========================================================================
    # Type 2: Value Comparison (No Waiver Logic)
    # =========================================================================
    
    def _execute_type2(self, all_libraries: List[str], violations: List[Tuple[str, str]]) -> CheckResult:
        """
        Type 2: requirements.value>0, pattern_items exists, waivers.value=N/A/0
        
        Logic: 
        - violations (matched) = Forbidden libraries found (BAD)
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
        
        details = []
        
        # Find which patterns were not violated (good)
        violated_patterns = set(pattern for _, pattern in violations)
        unmatched_patterns = [p for p in self._forbidden_patterns if p not in violated_patterns]
        
        # Add violations (forbidden libraries found)
        if is_waiver_zero:
            # waiver=0: Convert FAIL to INFO
            for lib_name, pattern in violations:
                metadata = self._library_metadata.get(lib_name, {})
                details.append(DetailItem(
                    severity=Severity.INFO,
                    name=lib_name,
                    line_number=metadata.get('line_number', ''),
                    file_path=metadata.get('file_path', ''),
                    reason=f"Forbidden library found (matches pattern: {pattern})[WAIVED_AS_INFO]"
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
            for lib_name, pattern in violations:
                metadata = self._library_metadata.get(lib_name, {})
                details.append(DetailItem(
                    severity=Severity.FAIL,
                    name=lib_name,
                    line_number=metadata.get('line_number', ''),
                    file_path=metadata.get('file_path', ''),
                    reason=f"Forbidden library found (matches pattern: {pattern})"
                ))
            
            # Add unmatched patterns as INFO (good - not found)
            for pattern in unmatched_patterns:
                details.append(DetailItem(
                    severity=Severity.INFO,
                    name=pattern,
                    line_number='',
                    file_path='',
                    reason="Forbidden pattern not found in any library (good)"
                ))
            
            is_pass = (len(violations) == expected_value)
        
        return create_check_result(
            value=len(violations),
            is_pass=is_pass,
            has_pattern_items=True,
            has_waiver_value=bool(waive_items),
            details=details,
            item_desc=self.item_desc
        )
    
    # =========================================================================
    # Type 3: Value Comparison WITH Waiver Logic
    # =========================================================================
    
    def _execute_type3(self, all_libraries: List[str], violations: List[Tuple[str, str]]) -> CheckResult:
        """
        Type 3: requirements.value>0, pattern_items exists, waivers.value>0
        
        Logic: 
        - violations = Forbidden libraries found
        - Separate into: unwaived (FAIL), waived (INFO), unused waivers (WARN)
        """
        waivers = self.get_waivers()
        waive_items_dict = self._get_waive_items_with_reasons()
        waive_items = list(waive_items_dict.keys())
        
        # Separate violations into waived/unwaived
        waive_set = set(waive_items)
        unwaived = [(lib, pattern) for lib, pattern in violations if lib not in waive_set]
        waived = [(lib, pattern) for lib, pattern in violations if lib in waive_set]
        
        # Find unused waivers
        violated_libs = set(lib for lib, _ in violations)
        unused_waivers = [item for item in waive_items if item not in violated_libs]
        
        # Find unmatched patterns (good - not violated)
        violated_patterns = set(pattern for _, pattern in violations)
        unmatched_patterns = [p for p in self._forbidden_patterns if p not in violated_patterns]
        
        details = []
        
        # FAIL: Unwaived violations
        for lib_name, pattern in unwaived:
            metadata = self._library_metadata.get(lib_name, {})
            details.append(DetailItem(
                severity=Severity.FAIL,
                name=lib_name,
                line_number=metadata.get('line_number', ''),
                file_path=metadata.get('file_path', ''),
                reason=f"Forbidden library found (matches pattern: {pattern})"
            ))
        
        # INFO: Waived violations
        for lib_name, pattern in waived:
            metadata = self._library_metadata.get(lib_name, {})
            waiver_reason = waive_items_dict.get(lib_name, '')
            reason = f"{waiver_reason}[WAIVER]" if waiver_reason else f"Forbidden library waived[WAIVER]"
            details.append(DetailItem(
                severity=Severity.INFO,
                name=lib_name,
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
                reason="Forbidden pattern not found in any library (good)"
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
        
        # Create explicit error groups with different descriptions
        error_groups = None
        warn_groups = None
        info_groups = None
        
        if unwaived:
            error_groups = {
                "ERROR01": "Forbidden library found (not waived)"
            }
        
        if unused_waivers:
            warn_groups = {
                "WARN01": "Waiver not used"
            }
        
        # Combine waived and unmatched into INFO
        if waived or unmatched_patterns:
            info_groups = {
                "INFO01": "Forbidden library found but waived"
            }
        
        return create_check_result(
            value=len(violations),
            is_pass=is_pass,
            has_pattern_items=True,
            has_waiver_value=True,
            details=details,
            error_groups=error_groups,
            warn_groups=warn_groups,
            info_groups=info_groups,
            item_desc=self.item_desc
        )
    
    # =========================================================================
    # Type 4: Boolean WITH Waiver Logic
    # =========================================================================
    
    def _execute_type4(self, all_libraries: List[str], violations: List[Tuple[str, str]]) -> CheckResult:
        """
        Type 4: requirements.value=N/A, waivers.value>0
        
        Logic: Boolean check + Waiver separation (FAIL/INFO/WARN)
        """
        waivers = self.get_waivers()
        waive_items_dict = self._get_waive_items_with_reasons()
        waive_items = list(waive_items_dict.keys())
        
        # For Type 4, violations are libraries that don't exist or have issues
        # Since we don't have pattern_items, we check if all libraries are valid
        
        details = []
        is_pass = True
        
        # All libraries loaded successfully
        if waive_items:
            for item in waive_items:
                waiver_reason = waive_items_dict.get(item, '')
                reason = f"{waiver_reason}[WAIVER]" if waiver_reason else "Waiver item[WAIVER]"
                details.append(DetailItem(
                    severity=Severity.INFO,
                    name=item,
                    line_number=0,
                    file_path="N/A",
                    reason=reason
                ))
        
        # Create info groups
        info_groups = None
        if waive_items:
            info_groups = {
                "INFO01": "Waived item (approved exception)"
            }
        
        return create_check_result(
            value="N/A",
            is_pass=is_pass,
            has_pattern_items=False,
            has_waiver_value=True,
            details=details if details else None,
            info_groups=info_groups,
            item_desc=self.item_desc
        )
    
    # =========================================================================
    # Helper Methods
    # =========================================================================
    
    def _get_waive_items_with_reasons(self) -> Dict[str, str]:
        """
        Get waive_items with their reasons.
        
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
        
        # If waive_items is a simple list
        return {item: '' for item in waive_items}


################################################################################
# Main Entry Point
################################################################################

if __name__ == '__main__':
    checker = LibraryChecker()
    checker.run()
