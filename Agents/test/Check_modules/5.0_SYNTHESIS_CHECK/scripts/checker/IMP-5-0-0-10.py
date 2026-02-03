################################################################################
# Script Name: IMP-5-0-0-10.py
#
# Purpose:
#   Confirm don't use cells are not instantiated in synthesis.
#   Parse gates.rpt to identify instantiated gates and check against forbidden 
#   cells list from IMP-1-0-0-02.
#
# Logic:
#   - Forbidden cells from IMP-1-0-0-02 pattern_items (supports regex)
#   - Parse gates.rpt first column as cell names
#   - Match using regex patterns
#   - Type 2/3: "Matched" means violation (found forbidden cells)
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
from typing import List, Dict, Any, Tuple, Union, Optional
import sys
import re
import yaml

# Add common directory to path
_SCRIPT_DIR = Path(__file__).resolve().parent
_CHECK_MODULES_DIR = _SCRIPT_DIR.parents[2]  # Go up to Check_modules/
_COMMON_DIR = _CHECK_MODULES_DIR / 'common'
if str(_COMMON_DIR) not in sys.path:
    sys.path.insert(0, str(_COMMON_DIR))

from base_checker import BaseChecker, CheckResult, ConfigurationError
from output_formatter import DetailItem, Severity, create_check_result


class UnifiedDontUseCellChecker(BaseChecker):
    """
    Unified checker that auto-detects and handles all 4 checker types.
    
    Forbidden Cells Source: IMP-1-0-0-02.yaml pattern_items
    
    Type Detection Logic:
    - Type 1: requirements.value=N/A AND waivers.value=N/A/0
    - Type 2: requirements.value>0 AND pattern_items AND waivers.value=N/A/0
    - Type 3: requirements.value>0 AND pattern_items AND waivers.value>0
    - Type 4: requirements.value=N/A AND waivers.value>0
    
    Matching Logic:
    - Use regex to match cell names against forbidden patterns
    - "Matched" = Violation (forbidden cell found)
    - "Unmatched" = Good (forbidden pattern not found)
    """
    
    def __init__(self):
        super().__init__(
            check_module="5.0_SYNTHESIS_CHECK",
            item_id="IMP-5-0-0-10",
            item_desc="Confirm don't use cell list includes forbidden cells specified in IMP-1-0-0-02?"
        )
        self._cell_metadata: Dict[str, Dict[str, Any]] = {}
        self._forbidden_patterns: List[str] = []
    
    # =========================================================================
    # Forbidden Cells Configuration
    # =========================================================================
    
    def _get_forbidden_cells_from_imp_1_0_0_02(self) -> List[str]:
        """
        Get forbidden cell patterns from IMP-1-0-0-02.yaml.
        
        Returns:
            List of forbidden cell patterns (supports regex)
        """
        try:
            # self.root points to CHECKLIST, need to go to Check_modules
            imp_1_path = self.root / "Check_modules" / "1.0_LIBRARY_CHECK" / "inputs" / "items" / "IMP-1-0-0-02.yaml"
            
            if not imp_1_path.exists():
                return []
            
            with open(imp_1_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            if data and 'requirements' in data:
                pattern_items = data['requirements'].get('pattern_items', [])
                return pattern_items if pattern_items else []
            
            return []
        except Exception as e:
            print(f"Warning: Failed to load IMP-1-0-0-02.yaml: {e}")
            return []
    
    # =========================================================================
    # Input File Parsing and Matching
    # =========================================================================
    
    def _parse_gates_rpt(self) -> List[str]:
        """
        Parse gates.rpt to extract instantiated cell names.
        
        Format: First column is cell name
        Example: "INVD1BWP143M117H3P48CPDLVT  3  0.051  library  0"
        
        Returns:
            List of all instantiated cell names
        """
        if not self.item_data or 'input_files' not in self.item_data:
            return []
        
        # Validate input files using BaseChecker method
        valid_files, missing_files = self.validate_input_files()
        
        # Store missing files for error reporting
        if missing_files:
            self._cell_metadata['_missing_input_files'] = {
                'files': missing_files,
                'count': len(missing_files)
            }
            # Return empty list - will be handled in execute methods
            return []
        
        all_cells = []
        
        for file_path in valid_files:
            
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line_num, line in enumerate(f, start=1):
                    # Match format: "CELL_NAME  <number>"
                    # Extract first column as cell name
                    match = re.match(r'^(\S+)\s+\d+', line)
                    if match:
                        cell_name = match.group(1)
                        all_cells.append(cell_name)
                        
                        # Store metadata for later use
                        if cell_name not in self._cell_metadata:
                            self._cell_metadata[cell_name] = {
                                'line_number': line_num,
                                'file_path': str(file_path)
                            }
        
        return all_cells
    
    def _match_forbidden_cell(self, cell_name: str, patterns: List[str]) -> Optional[str]:
        """
        Check if cell name matches any forbidden pattern.
        
        Supports both glob patterns and regex:
        - Glob: *INVD1* -> matches anything containing INVD1
        - Regex: ^INVD1.* -> matches cells starting with INVD1
        
        Args:
            cell_name: Cell name to check
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
                if re.search(regex_pattern, cell_name):
                    return pattern
            except re.error:
                # If pattern is not valid regex, try exact match
                if pattern == cell_name:
                    return pattern
        return None
    
    def _find_violations(self, all_cells: List[str], forbidden_patterns: List[str]) -> List[Tuple[str, str]]:
        """
        Find cells that match forbidden patterns.
        
        Args:
            all_cells: All cell names from gates.rpt
            forbidden_patterns: Forbidden cell patterns (regex)
        
        Returns:
            List of (cell_name, matched_pattern) tuples
        """
        violations = []
        
        for cell_name in all_cells:
            matched_pattern = self._match_forbidden_cell(cell_name, forbidden_patterns)
            if matched_pattern:
                violations.append((cell_name, matched_pattern))
        
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
            
            # Get forbidden cell patterns from IMP-1-0-0-02
            self._forbidden_patterns = self._get_forbidden_cells_from_imp_1_0_0_02()
            
            # Detect checker type (use BaseChecker method with custom requirements from IMP-1-0-0-02)
            # Load IMP-1-0-0-02 requirements for type detection
            try:
                imp_1_path = self.root / "Check_modules" / "1.0_LIBRARY_CHECK" / "inputs" / "items" / "IMP-1-0-0-02.yaml"
                with open(imp_1_path, 'r', encoding='utf-8') as f:
                    imp_1_data = yaml.safe_load(f)
                custom_requirements = imp_1_data.get('requirements', {}) if imp_1_data else {}
            except:
                custom_requirements = {}
            
            checker_type = self.detect_checker_type(custom_requirements=custom_requirements)
            
            # Parse gates.rpt
            all_cells = self._parse_gates_rpt()
            
            # Find violations (cells matching forbidden patterns)
            violations = self._find_violations(all_cells, self._forbidden_patterns)
            
            # Execute based on type
            if checker_type == 1:
                return self._execute_type1(violations)
            elif checker_type == 2:
                return self._execute_type2(violations)
            elif checker_type == 3:
                return self._execute_type3(violations)
            else:  # checker_type == 4
                return self._execute_type4(violations)
        except ConfigurationError as e:
            return e.check_result
    
    # =========================================================================
    # Type 1: Boolean Check (No Waiver Logic)
    # =========================================================================
    
    def _execute_type1(self, violations: List[Tuple[str, str]]) -> CheckResult:
        """
        Type 1: requirements.value=N/A, waivers.value=N/A/0
        
        Logic: 
        - Check if any forbidden cells are instantiated
        - violations = List of (cell_name, matched_pattern)
        """
        waivers = self.get_waivers()
        waiver_value = waivers.get('value', 'N/A') if waivers else 'N/A'
        waive_items = waivers.get('waive_items', []) if waivers else []
        
        # Check if waiver=0 (display mode)
        is_waiver_zero = (waiver_value == 0)
        
        # Check for missing input files first
        missing_info = self._cell_metadata.get('_missing_input_files')
        if missing_info:
            return self.create_missing_files_error(missing_info['files'])
        
        details = []
        
        # Special case: No forbidden patterns configured
        if not self._forbidden_patterns:
            details.append(DetailItem(
                severity=Severity.INFO,
                name="",
                line_number=0,
                file_path="N/A",
                reason="No forbidden cells configured in IMP-1-0-0-02, check passed"
            ))
            return create_check_result(
                value=0,
                is_pass=True,
                has_pattern_items=False,
                has_waiver_value=bool(waive_items),
                details=details,
                item_desc=self.item_desc
            )
        
        if not violations:
            # No violations - PASS
            if waive_items:
                # Show waive_items as INFO (display only)
                for item in waive_items:
                    details.append(DetailItem(
                        severity=Severity.INFO,
                        name=item,
                        line_number=0,
                        file_path="N/A",
                        reason="Waiver"
                    ))
            
            return create_check_result(
                value=0,
                is_pass=True,
                has_pattern_items=False,
                has_waiver_value=bool(waive_items),
                details=details if details else None,
                item_desc=self.item_desc
            )
        
        # Has violations
        if is_waiver_zero:
            # waiver=0: Force PASS, convert FAIL to INFO + show waive_items
            for cell_name, pattern in violations:
                metadata = self._cell_metadata.get(cell_name, {})
                details.append(DetailItem(
                    severity=Severity.INFO,
                    name=cell_name,
                    line_number=metadata.get('line_number', ''),
                    file_path=metadata.get('file_path', ''),
                    reason=f"Forbidden cell found (matches pattern: {pattern})[WAIVED_AS_INFO]"
                ))
            
            # Add waive_items as INFO
            for item in waive_items:
                details.append(DetailItem(
                    severity=Severity.INFO,
                    name=item,
                    line_number=0,
                    file_path="N/A",
                    reason="Waiver item[WAIVED_INFO]"
                ))
            
            return create_check_result(
                value=0,
                is_pass=True,
                has_pattern_items=False,
                has_waiver_value=True,
                details=details,
                item_desc=self.item_desc
            )
        else:
            # Normal FAIL
            for cell_name, pattern in violations:
                metadata = self._cell_metadata.get(cell_name, {})
                details.append(DetailItem(
                    severity=Severity.FAIL,
                    name=cell_name,
                    line_number=metadata.get('line_number', ''),
                    file_path=metadata.get('file_path', ''),
                    reason=f"Forbidden cell found (matches pattern: {pattern})"
                ))
            
            return create_check_result(
                value=len(violations),
                is_pass=False,
                has_pattern_items=False,
                has_waiver_value=False,
                details=details,
                item_desc=self.item_desc,
                default_group_desc="Use cell list includes forbidden cells specified in IMP-1-0-0-02"
            )
    
    # =========================================================================
    # Type 2: Value Comparison (No Waiver Logic)
    # =========================================================================
    
    def _execute_type2(self, violations: List[Tuple[str, str]]) -> CheckResult:
        """
        Type 2: requirements.value>0, pattern_items exists, waivers.value=N/A/0
        
        Logic: 
        - violations (matched) = Forbidden cells found (BAD)
        - unmatched patterns = Forbidden patterns not found (GOOD)
        - Expect: violations count == IMP-1-0-0-02.requirements.value
        """
        # Get expected value from IMP-1-0-0-02.yaml
        try:
            imp_1_path = self.root / "Check_modules" / "1.0_LIBRARY_CHECK" / "inputs" / "items" / "IMP-1-0-0-02.yaml"
            with open(imp_1_path, 'r', encoding='utf-8') as f:
                imp_1_data = yaml.safe_load(f)
            expected_value = imp_1_data.get('requirements', {}).get('value', 0) if imp_1_data else 0
            # Convert to int
            try:
                expected_value = int(expected_value)
            except:
                expected_value = 0
        except:
            expected_value = 0
        
        waivers = self.get_waivers()
        waiver_value = waivers.get('value', 'N/A') if waivers else 'N/A'
        waive_items = waivers.get('waive_items', []) if waivers else []
        is_waiver_zero = (waiver_value == 0)
        
        # Check for missing input files first
        missing_info = self._cell_metadata.get('_missing_input_files')
        if missing_info:
            return self.create_missing_files_error(missing_info['files'])
        
        details = []
        
        # Find which patterns were not violated (good)
        violated_patterns = set(pattern for _, pattern in violations)
        unmatched_patterns = [p for p in self._forbidden_patterns if p not in violated_patterns]
        
        # Add violations (forbidden cells found)
        if is_waiver_zero:
            # waiver=0: Convert FAIL to INFO
            for cell_name, pattern in violations:
                metadata = self._cell_metadata.get(cell_name, {})
                details.append(DetailItem(
                    severity=Severity.INFO,
                    name=cell_name,
                    line_number=metadata.get('line_number', ''),
                    file_path=metadata.get('file_path', ''),
                    reason=f"Forbidden cell found (matches pattern: {pattern})[WAIVED_AS_INFO]"
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
            for cell_name, pattern in violations:
                metadata = self._cell_metadata.get(cell_name, {})
                details.append(DetailItem(
                    severity=Severity.FAIL,
                    name=cell_name,
                    line_number=metadata.get('line_number', ''),
                    file_path=metadata.get('file_path', ''),
                    reason=f"Forbidden cell found (matches pattern: {pattern})"
                ))
            
            # Add unmatched patterns as INFO (good - not found)
            for pattern in unmatched_patterns:
                details.append(DetailItem(
                    severity=Severity.INFO,
                    name=pattern,
                    line_number='',
                    file_path='',
                    reason="Forbidden pattern not found in gates.rpt (good)"
                ))
            
            is_pass = (len(violations) == expected_value)
        
        return create_check_result(
            value=len(violations),
            is_pass=is_pass,
            has_pattern_items=True,
            has_waiver_value=bool(waive_items),
            details=details,
            item_desc=self.item_desc,
            default_group_desc="Use cell list includes forbidden cells specified in IMP-1-0-0-02"
        )
    
    # =========================================================================
    # Type 3: Value Comparison WITH Waiver Logic
    # =========================================================================
    
    def _execute_type3(self, violations: List[Tuple[str, str]]) -> CheckResult:
        """
        Type 3: requirements.value>0, pattern_items exists, waivers.value>0
        
        Logic: 
        - violations = Forbidden cells found
        - Separate into: unwaived (FAIL), waived (INFO), unused waivers (WARN)
        """
        waivers = self.get_waivers()
        waive_items_dict = self._get_waive_items_with_reasons()
        waive_items = list(waive_items_dict.keys())
        
        # Check for missing input files first
        missing_info = self._cell_metadata.get('_missing_input_files')
        if missing_info:
            return self.create_missing_files_error(missing_info['files'])
        
        # Separate violations into waived/unwaived
        waive_set = set(waive_items)
        unwaived = [(cell, pattern) for cell, pattern in violations if cell not in waive_set]
        waived = [(cell, pattern) for cell, pattern in violations if cell in waive_set]
        
        # Find unused waivers
        violated_cells = set(cell for cell, _ in violations)
        unused_waivers = [item for item in waive_items if item not in violated_cells]
        
        # Find unmatched patterns (good - not violated)
        violated_patterns = set(pattern for _, pattern in violations)
        unmatched_patterns = [p for p in self._forbidden_patterns if p not in violated_patterns]
        
        details = []
        
        # FAIL: Unwaived violations
        for cell_name, pattern in unwaived:
            metadata = self._cell_metadata.get(cell_name, {})
            details.append(DetailItem(
                severity=Severity.FAIL,
                name=cell_name,
                line_number=metadata.get('line_number', ''),
                file_path=metadata.get('file_path', ''),
                reason=f"Forbidden cell found (matches pattern: {pattern})"
            ))
        
        # INFO: Waived violations
        for cell_name, pattern in waived:
            metadata = self._cell_metadata.get(cell_name, {})
            waiver_reason = waive_items_dict.get(cell_name, '')
            reason = f"{waiver_reason}[WAIVER]" if waiver_reason else f"Forbidden cell waived[WAIVER]"
            details.append(DetailItem(
                severity=Severity.INFO,
                name=cell_name,
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
                reason="Forbidden pattern not found in gates.rpt (good)"
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
        error_groups = {}
        warn_groups = {}
        info_groups = {}
        
        if unwaived:
            error_groups["ERROR01"] = {
                "description": "Unwaived forbidden cells found",
                "items": [cell for cell, _ in unwaived]
            }
        
        if unused_waivers:
            warn_groups["WARN01"] = {
                "description": "Unused waivers (not found in actual violations)",
                "items": unused_waivers
            }
        
        # Combine waived and unmatched into INFO
        info_items = []
        if waived:
            info_items.extend([cell for cell, _ in waived])
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
    # Type 4: Boolean WITH Waiver Logic
    # =========================================================================
    
    def _execute_type4(self, violations: List[Tuple[str, str]]) -> CheckResult:
        """
        Type 4: requirements.value=N/A, waivers.value>0
        
        Logic: Boolean check + Waiver separation (FAIL/INFO/WARN)
        """
        waivers = self.get_waivers()
        waive_items_dict = self._get_waive_items_with_reasons()
        waive_items = list(waive_items_dict.keys())
        
        # Check for missing input files first
        missing_info = self._cell_metadata.get('_missing_input_files')
        if missing_info:
            return self.create_missing_files_error(missing_info['files'])
        
        # Separate violations into waived/unwaived
        waive_set = set(waive_items)
        unwaived = [(cell, pattern) for cell, pattern in violations if cell not in waive_set]
        waived = [(cell, pattern) for cell, pattern in violations if cell in waive_set]
        
        # Find unused waivers
        violated_cells = set(cell for cell, _ in violations)
        unused_waivers = [item for item in waive_items if item not in violated_cells]
        
        details = []
        
        # FAIL: Unwaived violations
        for cell_name, pattern in sorted(unwaived):
            metadata = self._cell_metadata.get(cell_name, {})
            details.append(DetailItem(
                severity=Severity.FAIL,
                name=cell_name,
                line_number=metadata.get('line_number', ''),
                file_path=metadata.get('file_path', ''),
                reason=f"Forbidden cell found (matches pattern: {pattern})"
            ))
        
        # INFO: Waived violations
        for cell_name, pattern in sorted(waived):
            metadata = self._cell_metadata.get(cell_name, {})
            waiver_reason = waive_items_dict.get(cell_name, '')
            reason = f"{waiver_reason}[WAIVER]" if waiver_reason else f"Forbidden cell waived[WAIVER]"
            details.append(DetailItem(
                severity=Severity.INFO,
                name=cell_name,
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
        
        # Create explicit error groups with different descriptions
        error_groups = {}
        warn_groups = {}
        info_groups = {}
        
        if unwaived:
            error_groups["ERROR01"] = {
                "description": "Unwaived forbidden cells found (Boolean check with waiver)",
                "items": [cell for cell, _ in sorted(unwaived)]
            }
        
        if unused_waivers:
            warn_groups["WARN01"] = {
                "description": "Unused waivers (not found in violations)",
                "items": unused_waivers
            }
        
        if waived:
            info_groups["INFO01"] = {
                "description": "Waived violations (approved exceptions)",
                "items": [cell for cell, _ in sorted(waived)]
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
    checker = UnifiedDontUseCellChecker()
    checker.run()
