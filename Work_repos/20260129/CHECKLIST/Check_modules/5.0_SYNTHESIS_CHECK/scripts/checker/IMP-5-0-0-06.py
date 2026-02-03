################################################################################
# Script Name: IMP-5-0-0-06.py
#
# Purpose:
#   Confirm empty modules in synthesis are either none or properly explained.
#   Supports 4 checking types based on requirements and waivers configuration.
#
# Refactoring to BaseChecker:
#   - Migrated from BooleanCheckerWithWaiverBase to unified BaseChecker
#   - Added support for all 4 checking types (Type 1/2/3/4)
#   - Automatic type detection based on requirements.value and waivers.value
#   - Centralized input validation with create_missing_files_error()
#
# Usage:
#   python IMP-5-0-0-06.py [type]
#   type: Optional override (1/2/3/4), default is auto-detect
#
#
# Logic:
#   - Parse synthesis log for empty module warnings
#   - Extract all empty module instances
#   - Support waiver for explained empty modules
# Author: yyin
# Date:   2025-10-24
# Updated: 2025-11-26 - Migrated to BaseChecker (All 4 Types)
################################################################################

from pathlib import Path
import re
import sys
from typing import List, Dict, Tuple, Optional

# Add common module to path
_SCRIPT_DIR = Path(__file__).resolve().parent
_COMMON_DIR = _SCRIPT_DIR.parent.parent.parent / 'common'
if str(_COMMON_DIR) not in sys.path:
    sys.path.insert(0, str(_COMMON_DIR))

from base_checker import BaseChecker, ConfigurationError
from output_formatter import CheckResult, Severity, DetailItem, create_check_result


class EmptyModulesChecker(BaseChecker):
    """
    IMP-5-0-0-06: Confirm Empty Modules are none or explained?
    
    Parses synthesis log's "Check Design Report" section to detect empty modules.
    Empty modules indicate design quality issues and should be investigated.
    
    Checking Types:
    - Type 1: requirements=N/A, waivers=N/A/0 → Always PASS (informational only)
    - Type 2: requirements>0, waivers=N/A/0 → FAIL if any empty modules found
    - Type 3: requirements>0, waivers>0 → FAIL if unwaived empty modules found
    - Type 4: requirements=N/A, waivers>0 → FAIL if unwaived empty modules found
    """
    
    def __init__(self):
        """Initialize the empty modules checker."""
        super().__init__(
            check_module="5.0_SYNTHESIS_CHECK",
            item_id="IMP-5-0-0-06",
            item_desc="Confirm Empty Modules are none or explained?"
        )
        # Cache for parsed empty modules: {log_file_path: {module_name: line_number}}
        self.module_metadata: Dict[Path, Dict[str, int]] = {}
    
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
    
    def _parse_input_files(self, input_files: List[str]) -> Dict[str, int]:
        """
        Parse synthesis log files to extract empty modules.
        
        Args:
            input_files: List of synthesis log file paths
        
        Returns:
            Dict mapping module names to line numbers where first found
        """
        all_empty_modules: Dict[str, int] = {}
        
        for file_path_str in input_files:
            log_path = Path(file_path_str)
            if not log_path.exists():
                self.logger.warning(f"Synthesis log not found: {log_path}")
                continue
            
            # Extract empty modules from this log
            modules_dict, has_check_design = self._extract_empty_modules_from_log(log_path)
            
            # Cache the metadata
            self.module_metadata[log_path] = modules_dict
            
            # Merge into all_empty_modules (keep first occurrence line number)
            for module_name, line_num in modules_dict.items():
                if module_name not in all_empty_modules:
                    all_empty_modules[module_name] = line_num
        
        return all_empty_modules
    
    # =========================================================================
    # Type 1: Informational Check (requirements=N/A, waivers=N/A/0)
    # =========================================================================
    
    def _execute_type1(self) -> CheckResult:
        """
        Type 1: Informational check only, always PASS.
        
        Returns:
            CheckResult with is_pass=True, INFO message about empty modules status
        """
        # Validate input files
        valid_files, missing_files = self.validate_input_files()
        
        # Handle missing input files
        if missing_files:
            return self.create_missing_files_error(missing_files)
        
        # Parse logs to extract empty modules
        empty_modules = self._parse_input_files([str(f) for f in valid_files])
        
        # Build details
        details = []
        if empty_modules:
            # Add each empty module as INFO
            for module_name, line_num in empty_modules.items():
                # Find which log file contains this module
                log_file = None
                for log_path, modules in self.module_metadata.items():
                    if module_name in modules:
                        log_file = str(log_path.resolve())
                        break
                
                details.append(DetailItem(
                    severity=Severity.INFO,
                    name=module_name,
                    line_number=line_num,
                    file_path=log_file or "",
                    reason="Empty module found (informational only)"
                ))
            
            info_message = f"Found {len(empty_modules)} empty module(s) in synthesis logs (Type 1: informational)"
        else:
            # No empty modules
            log_path_str = str(Path(valid_files[0]).resolve()) if valid_files else "synthesis logs"
            details.append(DetailItem(
                severity=Severity.INFO,
                name="",
                line_number=0,
                file_path="",
                reason=f"No empty modules found in {log_path_str}"
            ))
            #info_message = "No empty modules found in synthesis logs (Type 1: informational)"
        
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
        Type 2: FAIL if empty modules count > 0, PASS if count == 0.
        
        Returns:
            CheckResult with is_pass based on whether empty modules exist
        """
        # Validate input files
        valid_files, missing_files = self.validate_input_files()
        
        # Handle missing input files
        if missing_files:
            return self.create_missing_files_error(missing_files)
        
        # Parse logs to extract empty modules
        empty_modules = self._parse_input_files([str(f) for f in valid_files])
        
        # Build details
        details = []
        is_pass = len(empty_modules) == 0
        
        if empty_modules:
            # FAIL: Add each empty module as FAIL
            for module_name, line_num in empty_modules.items():
                # Find which log file contains this module
                log_file = None
                for log_path, modules in self.module_metadata.items():
                    if module_name in modules:
                        log_file = str(log_path.resolve())
                        break
                
                details.append(DetailItem(
                    severity=Severity.FAIL,
                    name=module_name,
                    line_number=line_num,
                    file_path=log_file or "",
                    reason="Empty module found"
                ))
            
            # Build error groups
            error_groups = {
                "ERROR01": {
                    "description": "Empty modules not explained",
                    "items": [d.name for d in details if d.severity == Severity.FAIL and d.name]
                }
            }
            info_groups = None
        else:
            # PASS: No empty modules
            log_path_str = str(Path(valid_files[0]).resolve()) if valid_files else "synthesis logs"
            details.append(DetailItem(
                severity=Severity.INFO,
                name="",
                line_number=0,
                file_path="",
                reason=f"No empty modules found in {log_path_str}"
            ))
            info_groups = {
                "INFO01": {
                    "description": "Check result",
                    "items": []
                }
            }
            error_groups = None
        
        return create_check_result(
            value=str(len(empty_modules)),
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
        Type 3: FAIL if unwaived empty modules exist, WAIVED if all are waived.
        
        Returns:
            CheckResult with FAIL/WAIVED/PASS based on waiver coverage
        """
        # Validate input files
        valid_files, missing_files = self.validate_input_files()
        
        # Handle missing input files
        if missing_files:
            return self.create_missing_files_error(missing_files)
        
        # Parse logs to extract empty modules
        empty_modules = self._parse_input_files([str(f) for f in valid_files])
        
        # Get waiver patterns and reasons
        waiver_patterns = self.waivers.pattern_items or []
        waiver_reason_map = self._build_waiver_reason_map()
        
        # Separate waived and unwaived empty modules
        waived_modules = []
        unwaived_modules = []
        
        for module_name in empty_modules.keys():
            if self._matches_any_pattern(module_name, waiver_patterns):
                waived_modules.append(module_name)
            else:
                unwaived_modules.append(module_name)
        
        # Check for unused waivers
        used_patterns = set()
        for module_name in waived_modules:
            for pattern in waiver_patterns:
                if self._matches_pattern(module_name, pattern):
                    used_patterns.add(pattern)
        
        unused_waivers = [p for p in waiver_patterns if p not in used_patterns]
        
        # Build details
        details = []
        
        # Add unwaived modules as FAIL
        for module_name in unwaived_modules:
            line_num = empty_modules[module_name]
            log_file = None
            for log_path, modules in self.module_metadata.items():
                if module_name in modules:
                    log_file = str(log_path.resolve())
                    break
            
            details.append(DetailItem(
                severity=Severity.FAIL,
                name=module_name,
                line_number=line_num,
                file_path=log_file or "",
                reason="Empty module found (not waived)"
            ))
        
        # Add waived modules as INFO with [WAIVER] tag
        for module_name in waived_modules:
            line_num = empty_modules[module_name]
            log_file = None
            for log_path, modules in self.module_metadata.items():
                if module_name in modules:
                    log_file = str(log_path.resolve())
                    break
            
            reason = waiver_reason_map.get(module_name, "Waived")
            details.append(DetailItem(
                severity=Severity.INFO,
                name=f"[WAIVER] {module_name}",
                line_number=line_num,
                file_path=log_file or "",
                reason=reason
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
        is_pass = len(unwaived_modules) == 0
        
        # Build error/warn/info groups
        error_groups = {}
        warn_groups = {}
        info_groups = {}
        
        if unwaived_modules:
            error_groups["ERROR01"] = {
                "description": "Empty modules not explained",
                "items": [d.name for d in details if d.severity == Severity.FAIL and d.name]
            }
        
        if waived_modules:
            info_groups["INFO01"] = {
                "description": "Empty modules waived",
                "items": [d.name for d in details if d.severity == Severity.INFO and d.name]
            }
        
        if unused_waivers:
            warn_groups["WARN01"] = {
                "description": "Unused waiver patterns",
                "items": [d.name for d in details if d.severity == Severity.WARN and d.name]
            }
        
        return create_check_result(
            value=str(len(empty_modules)),
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
        Type 4: Boolean check - FAIL if unwaived empty modules exist.
        
        Returns:
            CheckResult with FAIL/WAIVED/PASS based on waiver coverage
        """
        # Validate input files
        valid_files, missing_files = self.validate_input_files()
        
        # Handle missing input files
        if missing_files:
            return self.create_missing_files_error(missing_files)
        
        # Parse logs to extract empty modules
        empty_modules = self._parse_input_files([str(f) for f in valid_files])
        
        # Get waiver patterns and reasons
        waiver_patterns = self.waivers.pattern_items or []
        waiver_reason_map = self._build_waiver_reason_map()
        
        # Separate waived and unwaived empty modules
        waived_modules = []
        unwaived_modules = []
        
        for module_name in empty_modules.keys():
            if self._matches_any_pattern(module_name, waiver_patterns):
                waived_modules.append(module_name)
            else:
                unwaived_modules.append(module_name)
        
        # Check for unused waivers
        used_patterns = set()
        for module_name in waived_modules:
            for pattern in waiver_patterns:
                if self._matches_pattern(module_name, pattern):
                    used_patterns.add(pattern)
        
        unused_waivers = [p for p in waiver_patterns if p not in used_patterns]
        
        # Build details
        details = []
        
        # Add unwaived modules as FAIL
        for module_name in unwaived_modules:
            line_num = empty_modules[module_name]
            log_file = None
            for log_path, modules in self.module_metadata.items():
                if module_name in modules:
                    log_file = str(log_path.resolve())
                    break
            
            details.append(DetailItem(
                severity=Severity.FAIL,
                name=module_name,
                line_number=line_num,
                file_path=log_file or "",
                reason="Empty module found (not waived)"
            ))
        
        # Add waived modules as INFO with [WAIVER] tag
        for module_name in waived_modules:
            line_num = empty_modules[module_name]
            log_file = None
            for log_path, modules in self.module_metadata.items():
                if module_name in modules:
                    log_file = str(log_path.resolve())
                    break
            
            reason = waiver_reason_map.get(module_name, "Waived")
            details.append(DetailItem(
                severity=Severity.INFO,
                name=f"[WAIVER] {module_name}",
                line_number=line_num,
                file_path=log_file or "",
                reason=reason
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
        
        # If no empty modules at all, add INFO message
        if not empty_modules:
            log_path_str = str(Path(valid_files[0]).resolve()) if valid_files else "synthesis logs"
            details.append(DetailItem(
                severity=Severity.INFO,
                name="",
                line_number=0,
                file_path="",
                reason=f"No empty modules found in {log_path_str}"
            ))
        
        # Determine pass status
        is_pass = len(unwaived_modules) == 0
        
        # Build error/warn/info groups
        error_groups = {}
        warn_groups = {}
        info_groups = {}
        
        if unwaived_modules:
            error_groups["ERROR01"] = {
                "description": "Empty modules not explained",
                "items": [d.name for d in details if d.severity == Severity.FAIL and d.name]
            }
        
        if waived_modules:
            info_groups["INFO01"] = {
                "description": "Empty modules waived",
                "items": [d.name for d in details if d.severity == Severity.INFO and d.name and d.name.startswith("[WAIVER]")]
            }
        elif not empty_modules:
            # No empty modules case
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
    # Helper Method: Extract empty modules from single log file
    # =========================================================================
    
    def _extract_empty_modules_from_log(self, log_path: Path) -> Tuple[Dict[str, int], bool]:
        """
        Extract empty modules from a synthesis log file.
        
        Args:
            log_path: Path to synthesis log file
        
        Returns:
            Tuple of (empty_modules_dict, has_check_design)
            - empty_modules_dict: Dict mapping module name to line number
            - has_check_design: True if "Check Design Report" was found
        """
        lines = self.read_file(log_path)
        if not lines:
            return {}, False
        
        empty_modules: Dict[str, int] = {}
        has_check_design = False
        
        # Regex patterns
        check_design_pattern = re.compile(r'Check\s+Design\s+Report.*\(c\)', re.IGNORECASE)
        empty_modules_section_pattern = re.compile(r'Unresolved\s+References.*Empty\s+Modules', re.IGNORECASE)
        no_empty_pattern = re.compile(r'No\s+empty\s+modules\s+in\s+design', re.IGNORECASE)
        has_empty_pattern = re.compile(r'design\s+["\']?(\S+?)["\']?\s+has\s+the\s+following\s+empty\s+module\(s\)', re.IGNORECASE)
        total_empty_pattern = re.compile(r'Total\s+number\s+of\s+empty\s+modules\s+in\s+design.*:\s*(\d+)', re.IGNORECASE)
        
        in_check_design = False
        in_empty_modules_section = False
        current_design_has_empty = False
        
        for idx, line in enumerate(lines, start=1):
            # Detect Check Design Report
            if check_design_pattern.search(line):
                has_check_design = True
                in_check_design = True
                in_empty_modules_section = False
                current_design_has_empty = False
                continue
            
            # Look for empty modules section
            if in_check_design and empty_modules_section_pattern.search(line):
                in_empty_modules_section = True
                continue
            
            # Check for no empty modules
            if in_empty_modules_section and no_empty_pattern.search(line):
                in_empty_modules_section = False
                in_check_design = False
                continue
            
            # Check for design has empty modules
            if in_empty_modules_section and has_empty_pattern.search(line):
                current_design_has_empty = True
                continue
            
            # Extract empty module names
            if in_empty_modules_section and current_design_has_empty:
                # Check for total count (end of empty modules list)
                if total_empty_pattern.search(line):
                    in_empty_modules_section = False
                    in_check_design = False
                    current_design_has_empty = False
                    continue
                
                # Extract module name
                stripped = line.strip()
                if stripped and not line.startswith(' ' * 10):  # Skip heavily indented lines
                    module_match = re.match(r'^(\S+)\s*$', stripped)
                    if module_match:
                        module_name = module_match.group(1).strip()
                        # Avoid capturing section headers or keywords
                        if module_name and module_name not in empty_modules:
                            if not any(kw in module_name.lower() for kw in ['done', 'checking', 'total', 'number']):
                                empty_modules[module_name] = idx
                        continue
            
            # Exit check design section if we hit a new major section
            if in_check_design and line.strip() and line.strip()[0].isupper() and '=' * 5 in line:
                in_check_design = False
                in_empty_modules_section = False
        
        return empty_modules, has_check_design


# =============================================================================
# Entry Point
# =============================================================================

if __name__ == '__main__':
    checker = EmptyModulesChecker()
    checker.run()
