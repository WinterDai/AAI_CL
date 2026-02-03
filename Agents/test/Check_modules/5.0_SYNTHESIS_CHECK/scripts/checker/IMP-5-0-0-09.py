################################################################################
# Script Name: IMP-5-0-0-09.py
#
# Purpose:
#   Confirm that latches inferred during synthesis are documented.
#   Supports 4 checking types based on requirements and waivers configuration.
#
# Refactoring to BaseChecker:
#   - Migrated from ValueCheckerBase to unified BaseChecker
#   - Added support for all 4 checking types (Type 1/2/3/4)
#   - Automatic type detection based on requirements.value and waivers.value
#   - Centralized input validation with create_missing_files_error()
#
# Usage:
#   python IMP-5-0-0-09.py [type]
#   type: Optional override (1/2/3/4), default is auto-detect
#
#
# Logic:
#   - Parse latch.rpt for inferred latch warnings
#   - Extract all latch instances and locations
#   - Support waiver for documented/approved latches
# Author: yyin
# Date:   2025-10-31
# Updated: 2025-11-26 - Migrated to BaseChecker (All 4 Types)
################################################################################

import sys
import re
from pathlib import Path
from typing import List, Dict, Set, Tuple

# Add common modules to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'common'))

from base_checker import BaseChecker, ConfigurationError
from output_formatter import CheckResult, Severity, DetailItem, create_check_result


class LatchChecker(BaseChecker):
    """
    IMP-5-0-0-09: Confirm Latches Inferred documented?
    
    Parses latch.rpt to extract inferred latch cells and validates they are documented.
    
    Checking Types:
    - Type 1: requirements=N/A, waivers=N/A/0 → Always PASS (informational only)
    - Type 2: requirements>0, waivers=N/A/0 → FAIL if undocumented latches exist
    - Type 3: requirements>0, waivers>0 → FAIL if unwaived latches exist
    - Type 4: requirements=N/A, waivers>0 → FAIL if unwaived latches exist
    """
    
    def __init__(self):
        """Initialize the latch checker."""
        super().__init__(
            check_module="5.0_SYNTHESIS_CHECK",
            item_id="IMP-5-0-0-09",
            item_desc="Confirm Latches Inferred documented?"
        )
        # Track metadata: {latch_name: {'line': first_line, 'file': file_path, 'count': occurrence_count}}
        self.latch_metadata: Dict[str, dict] = {}
    
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
    
    def _parse_input_files(self, input_files: List[Path]) -> List[str]:
        """
        Extract latch cell names from latch.rpt.
        
        Format: inst:<instance_path> <libset>/<library>/<LATCH_CELL_NAME>
        Example: inst:path/to/inst libset_ssgnp/tcbn03e_base_lvt/CKLNQD1BWP143
        
        Args:
            input_files: List of input file paths
            
        Returns:
            List of unique latch cell names found
        """
        # Find latch.rpt
        latch_rpt_path = None
        for path in input_files:
            if 'latch' in path.name.lower() and path.suffix.lower() == '.rpt':
                latch_rpt_path = path
                break
        
        if not latch_rpt_path:
            return []
        
        # Read file
        lines = self.read_file(latch_rpt_path)
        if not lines:
            return []
        
        # Extract latch cells
        latch_cells, cell_line_map = self._extract_latch_cells_with_lines(lines, latch_rpt_path)
        
        # Store metadata for each latch
        for cell_name in latch_cells:
            line_nums = cell_line_map.get(cell_name, [])
            self.latch_metadata[cell_name] = {
                'line': line_nums[0] if line_nums else 0,
                'file': latch_rpt_path,
                'count': len(line_nums)
            }
        
        return sorted(latch_cells)
    
    def _extract_latch_cells_with_lines(
        self,
        lines: List[str],
        file_path: Path
    ) -> Tuple[Set[str], Dict[str, List[int]]]:
        """
        Extract unique latch cell names from latch.rpt lines.
        
        Returns:
            Tuple of (latch_cells_set, cell_line_map)
        """
        latch_cells: Set[str] = set()
        cell_line_map: Dict[str, List[int]] = {}
        
        # Pattern: inst:<instance_path> <anything>/<LATCH_CELL_NAME>
        pattern = re.compile(r'^inst:(\S+)\s+(.+)/([A-Z0-9_]+)\s*$', re.IGNORECASE)
        
        for line_num, line in enumerate(lines, 1):
            stripped = line.strip()
            if not stripped:
                continue
            
            match = pattern.match(stripped)
            if match:
                latch_cell_name = match.group(3)
                latch_cells.add(latch_cell_name)
                
                if latch_cell_name not in cell_line_map:
                    cell_line_map[latch_cell_name] = []
                cell_line_map[latch_cell_name].append(line_num)
        
        return latch_cells, cell_line_map
    
    # =========================================================================
    # Type 1: Informational Check (requirements=N/A, waivers=N/A/0)
    # =========================================================================
    
    def _execute_type1(self) -> CheckResult:
        """
        Type 1: Informational check only, always PASS.
        
        Returns:
            CheckResult with is_pass=True, INFO message about latch status
        """
        # Validate input files
        valid_files, missing_files = self.validate_input_files()
        
        # Handle missing input files
        if missing_files:
            return self.create_missing_files_error(missing_files)
        
        # Parse reports to extract latch cells
        latch_cells = self._parse_input_files(valid_files)
        
        # Build details
        details = []
        if latch_cells:
            # Add each latch as INFO
            for latch_name in latch_cells:
                meta = self.latch_metadata.get(latch_name, {})
                details.append(DetailItem(
                    severity=Severity.INFO,
                    name=latch_name,
                    line_number=meta.get('line', 0),
                    file_path=str(meta.get('file', Path()).resolve()),
                    reason=f"Latch cell inferred (count: {meta.get('count', 0)})"
                ))
        else:
            # No latches found
            details.append(DetailItem(
                severity=Severity.INFO,
                name="",
                line_number=0,
                file_path="",
                reason="No latches inferred in design"
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
        Type 2: FAIL if undocumented latches exist, PASS if all are documented.
        
        Returns:
            CheckResult with is_pass based on documentation coverage
        """
        # Validate input files
        valid_files, missing_files = self.validate_input_files()
        
        # Handle missing input files
        if missing_files:
            return self.create_missing_files_error(missing_files)
        
        # Parse reports to extract latch cells
        latch_cells = self._parse_input_files(valid_files)
        
        # Get expected documented latches from pattern_items
        documented_latches = self.requirements.pattern_items or []
        
        # Build details
        details = []
        
        # Case 1: No latches found
        if not latch_cells:
            details.append(DetailItem(
                severity=Severity.INFO,
                name="",
                line_number=0,
                file_path="",
                reason="No latches inferred in design"
            ))
            
            info_groups = {
                "INFO01": {
                    "description": "Check result",
                    "items": []
                }
            }
            
            return create_check_result(
                value="0",
                is_pass=True,
                has_pattern_items=True,
                has_waiver_value=False,
                details=details,
                info_groups=info_groups,
                item_desc=self.item_desc
            )
        
        # Case 2: Latches found but no documented list configured
        if not documented_latches:
            # WARN: Should document the found latches
            details.append(DetailItem(
                severity=Severity.WARN,
                name="",
                line_number=0,
                file_path="",
                reason="Golden value expected but not provided"
            ))
            
            for latch_name in latch_cells:
                meta = self.latch_metadata.get(latch_name, {})
                details.append(DetailItem(
                    severity=Severity.INFO,
                    name=latch_name,
                    line_number=meta.get('line', 0),
                    file_path=str(meta.get('file', Path()).resolve()),
                    reason=f"Latch cell used and golden value expected but not provided and total count is {meta.get('count', 0)}"
                ))
            
            warn_groups = {
                "WARN01": {
                    "description": "Configuration Warning",
                    "items": []
                }
            }
            
            info_groups = {
                "INFO01": {
                    "description": "Latches Inferred",
                    "items": latch_cells
                }
            }
            
            return create_check_result(
                value="0",
                is_pass=True,
                has_pattern_items=False,
                has_waiver_value=False,
                details=details,
                warn_groups=warn_groups,
                info_groups=info_groups,
                item_desc=self.item_desc
            )
        
        # Case 3: Both latches and documented list exist - compare
        undocumented_latches = [latch for latch in latch_cells if latch not in documented_latches]
        documented_found = [latch for latch in latch_cells if latch in documented_latches]
        
        # Add undocumented latches as FAIL
        for latch_name in undocumented_latches:
            meta = self.latch_metadata.get(latch_name, {})
            details.append(DetailItem(
                severity=Severity.FAIL,
                name=latch_name,
                line_number=meta.get('line', 0),
                file_path=str(meta.get('file', Path()).resolve()),
                reason="Latch cell used in design but not documented"
            ))
        
        # Add documented latches as INFO
        for latch_name in documented_found:
            meta = self.latch_metadata.get(latch_name, {})
            details.append(DetailItem(
                severity=Severity.INFO,
                name=latch_name,
                line_number=meta.get('line', 0),
                file_path=str(meta.get('file', Path()).resolve()),
                reason=f"Latch cell documented (count: {meta.get('count', 0)})"
            ))
        
        # Determine pass status
        is_pass = len(undocumented_latches) == 0
        
        # Build error/info groups
        if undocumented_latches:
            error_groups = {
                "ERROR01": {
                    "description": "Undocumented latch cells",
                    "items": undocumented_latches
                }
            }
            info_groups = None
        else:
            error_groups = None
            info_groups = {
                "INFO01": {
                    "description": "Latches Inferred",
                    "items": documented_found
                }
            }
        
        return create_check_result(
            value=str(len(undocumented_latches)),
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
        Type 3: FAIL if unwaived undocumented latches exist, WAIVED if all are waived.
        
        Returns:
            CheckResult with FAIL/WAIVED/PASS based on waiver coverage
        """
        # Validate input files
        valid_files, missing_files = self.validate_input_files()
        
        # Handle missing input files
        if missing_files:
            return self.create_missing_files_error(missing_files)
        
        # Parse reports to extract latch cells
        latch_cells = self._parse_input_files(valid_files)
        
        # Get expected documented latches from pattern_items
        documented_latches = self.requirements.pattern_items or []
        
        # Get waiver patterns and reasons
        waiver_patterns = self.waivers.pattern_items or []
        waiver_reason_map = self._build_waiver_reason_map()
        
        # Find undocumented latches
        undocumented_latches = [latch for latch in latch_cells if latch not in documented_latches]
        documented_found = [latch for latch in latch_cells if latch in documented_latches]
        
        # Separate waived and unwaived undocumented latches
        waived_latches = []
        unwaived_latches = []
        
        for latch in undocumented_latches:
            if self._matches_any_pattern(latch, waiver_patterns):
                waived_latches.append(latch)
            else:
                unwaived_latches.append(latch)
        
        # Check for unused waivers
        used_patterns = set()
        for latch in waived_latches:
            for pattern in waiver_patterns:
                if self._matches_pattern(latch, pattern):
                    used_patterns.add(pattern)
        
        unused_waivers = [p for p in waiver_patterns if p not in used_patterns]
        
        # Build details
        details = []
        
        # Add unwaived undocumented latches as FAIL
        for latch_name in unwaived_latches:
            meta = self.latch_metadata.get(latch_name, {})
            details.append(DetailItem(
                severity=Severity.FAIL,
                name=latch_name,
                line_number=meta.get('line', 0),
                file_path=str(meta.get('file', Path()).resolve()),
                reason="Latch cell used in design but not documented (not waived)"
            ))
        
        # Add waived undocumented latches as INFO with [WAIVER] tag
        for latch_name in waived_latches:
            meta = self.latch_metadata.get(latch_name, {})
            reason = waiver_reason_map.get(latch_name, "Waived")
            details.append(DetailItem(
                severity=Severity.INFO,
                name=f"[WAIVER] {latch_name}",
                line_number=meta.get('line', 0),
                file_path=str(meta.get('file', Path()).resolve()),
                reason=f"Latch cell undocumented: {reason}"
            ))
        
        # Add documented latches as INFO
        for latch_name in documented_found:
            meta = self.latch_metadata.get(latch_name, {})
            details.append(DetailItem(
                severity=Severity.INFO,
                name=latch_name,
                line_number=meta.get('line', 0),
                file_path=str(meta.get('file', Path()).resolve()),
                reason=f"Latch cell documented (count: {meta.get('count', 0)})"
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
        
        # Handle no latches case
        if not latch_cells:
            details.append(DetailItem(
                severity=Severity.INFO,
                name="",
                line_number=0,
                file_path="",
                reason="No latches inferred in design"
            ))
        
        # Determine pass status
        is_pass = len(unwaived_latches) == 0
        
        # Build error/warn/info groups
        error_groups = {}
        warn_groups = {}
        info_groups = {}
        
        if unwaived_latches:
            error_groups["ERROR01"] = {
                "description": "Undocumented latch cells (not waived)",
                "items": unwaived_latches
            }
        
        if waived_latches:
            info_groups["INFO01"] = {
                "description": "Undocumented latches waived",
                "items": [f"[WAIVER] {latch}" for latch in waived_latches]
            }
        
        if documented_found and not waived_latches:
            info_groups["INFO01"] = {
                "description": "Latches Inferred",
                "items": documented_found
            }
        elif documented_found and waived_latches:
            info_groups["INFO02"] = {
                "description": "Documented latches",
                "items": documented_found
            }
        
        if unused_waivers:
            warn_groups["WARN01"] = {
                "description": "Unused waiver patterns",
                "items": unused_waivers
            }
        
        if not latch_cells and not (error_groups or warn_groups):
            info_groups["INFO01"] = {
                "description": "Check result",
                "items": []
            }
        
        return create_check_result(
            value=str(len(undocumented_latches)),
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
        Type 4: Boolean check - FAIL if unwaived undocumented latches exist.
        
        Returns:
            CheckResult with FAIL/WAIVED/PASS based on waiver coverage
        """
        # Validate input files
        valid_files, missing_files = self.validate_input_files()
        
        # Handle missing input files
        if missing_files:
            return self.create_missing_files_error(missing_files)
        
        # Parse reports to extract latch cells
        latch_cells = self._parse_input_files(valid_files)
        
        # Get waiver patterns and reasons
        waiver_patterns = self.waivers.pattern_items or []
        waiver_reason_map = self._build_waiver_reason_map()
        
        # Separate waived and unwaived latches
        waived_latches = []
        unwaived_latches = []
        
        for latch in latch_cells:
            if self._matches_any_pattern(latch, waiver_patterns):
                waived_latches.append(latch)
            else:
                unwaived_latches.append(latch)
        
        # Check for unused waivers
        used_patterns = set()
        for latch in waived_latches:
            for pattern in waiver_patterns:
                if self._matches_pattern(latch, pattern):
                    used_patterns.add(pattern)
        
        unused_waivers = [p for p in waiver_patterns if p not in used_patterns]
        
        # Build details
        details = []
        
        # Add unwaived latches as FAIL
        for latch_name in unwaived_latches:
            meta = self.latch_metadata.get(latch_name, {})
            details.append(DetailItem(
                severity=Severity.FAIL,
                name=latch_name,
                line_number=meta.get('line', 0),
                file_path=str(meta.get('file', Path()).resolve()),
                reason=f"Latch cell inferred (count: {meta.get('count', 0)}, not waived)"
            ))
        
        # Add waived latches as INFO with [WAIVER] tag
        for latch_name in waived_latches:
            meta = self.latch_metadata.get(latch_name, {})
            reason = waiver_reason_map.get(latch_name, "Waived")
            details.append(DetailItem(
                severity=Severity.INFO,
                name=f"[WAIVER] {latch_name}",
                line_number=meta.get('line', 0),
                file_path=str(meta.get('file', Path()).resolve()),
                reason=f"Latch cell inferred: {reason}"
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
        
        # If no latches at all, add INFO message
        if not latch_cells:
            details.append(DetailItem(
                severity=Severity.INFO,
                name="",
                line_number=0,
                file_path="",
                reason="No latches inferred in design"
            ))
        
        # Determine pass status
        is_pass = len(unwaived_latches) == 0
        
        # Build error/warn/info groups
        error_groups = {}
        warn_groups = {}
        info_groups = {}
        
        if unwaived_latches:
            error_groups["ERROR01"] = {
                "description": "Unwaived latch cells",
                "items": unwaived_latches
            }
        
        if waived_latches:
            info_groups["INFO01"] = {
                "description": "Latch cells waived",
                "items": [f"[WAIVER] {latch}" for latch in waived_latches]
            }
        elif not latch_cells:
            # No latches case
            info_groups["INFO01"] = {
                "description": "Check result",
                "items": []
            }
        
        if unused_waivers:
            warn_groups["WARN01"] = {
                "description": "Unused waiver patterns",
                "items": unused_waivers
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


# =============================================================================
# Entry Point
# =============================================================================

if __name__ == '__main__':
    checker = LatchChecker()
    checker.run()
