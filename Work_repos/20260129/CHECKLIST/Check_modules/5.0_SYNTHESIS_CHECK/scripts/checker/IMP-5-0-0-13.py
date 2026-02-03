################################################################################
# Script Name: IMP-5-0-0-13.py
#
# Purpose:
#   Confirm scan is successfully inserted and non-scannable flops have been
#   peer reviewed and waived.
#
# Logic:
#   - Parse dft_chainRegs.rpt to extract non-scannable registers
#   - Categorize registers by DFT issue type (9 categories)
#   - Type 2/3: Check against pattern_items (category patterns)
#   - Type 3/4: Support waiver logic with category-specific reasons
#
# Auto Type Detection:
#   Type 1: requirements.value=N/A, waivers.value=N/A/0 → Boolean check
#   Type 2: requirements.value>0, pattern_items exists, waivers.value=N/A/0 → Value comparison
#   Type 3: requirements.value>0, pattern_items exists, waivers.value>0 → Value with waiver logic
#   Type 4: requirements.value=N/A, waivers.value>0 → Boolean with waiver logic
#
# Author: yuyin
# Date: 2025-11-03
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

# ============================================================================
# DFT Chain Report Configuration
# ============================================================================

# Summary line patterns
SUMMARY_PATTERNS = {
    'fail_dft_rules': re.compile(r'Total registers that fail DFT rules:\s*(\d+)'),
    'preserved_or_dont_scan': re.compile(r'Total registers that are marked preserved or dont-scan:\s*(\d+)'),
    'abstract_segment_dont_scan': re.compile(r'Total registers that are marked Abstract Segment dont-scan:\s*(\d+)'),
    'shift_register_segments': re.compile(r'Total registers that are part of shift register segments:\s*(\d+)'),
    'lockup_elements': re.compile(r'Total registers that are lockup elements:\s*(\d+)'),
    'level_sensitive': re.compile(r'Total registers that are level-sensitive:\s*(\d+)'),
    'misc_non_scan': re.compile(r'Total registers that are misc\. non-scan:\s*(\d+)'),
    'pass_not_in_chains': re.compile(r'Total registers that pass dft rule checks and are not a part of scan chains:\s*(\d+)'),
    'abstract_not_in_chains': re.compile(r'Total abstract segments that pass dft rule checks and are not a part of scan chains:\s*(\d+)')
}

# Section header patterns
SECTION_HEADERS = {
    'fail_dft_rules': r'Reporting registers that fail DFT rules',
    'preserved_or_dont_scan': r'Reporting registers that are preserved or marked dont-scan',
    'abstract_segment_dont_scan': r'Reporting registers that are marked Abstract Segment Dont Scan',
    'shift_register_segments': r'Reporting registers that are part of shift register segments',
    'lockup_elements': r'Reporting registers that are identified as lockup elements',
    'level_sensitive': r'Reporting registers that are level-sensitive elements',
    'misc_non_scan': r'Reporting misc\. non-scan registers',
    'pass_not_in_chains': r'Reporting registers that pass dft rule checks and are not a part of scan chains',
    'abstract_not_in_chains': r'Reporting abstract segments that pass dft rule checks and are not a part of scan chains'
}

# Category descriptions
CATEGORY_DESC = {
    'fail_dft_rules': 'Registers fail DFT rules',
    'preserved_or_dont_scan': 'Registers are marked preserved or dont-scan',
    'abstract_segment_dont_scan': 'Registers are marked Abstract Segment dont-scan',
    'shift_register_segments': 'Registers are part of shift register segments',
    'lockup_elements': 'Registers are lockup elements',
    'level_sensitive': 'Registers are level-sensitive',
    'misc_non_scan': 'Registers are misc. non-scan',
    'pass_not_in_chains': 'Registers pass dft rule checks but are not a part of scan chains',
    'abstract_not_in_chains': 'Abstract segments pass dft rule checks but are not a part of scan chains'
}


class DFTScanChecker(BaseChecker):
    """
    Unified checker that auto-detects and handles all 4 checker types.
    
    Check Target: Confirm scan is successfully inserted and non-scannable flops
                  have been peer reviewed and waived
    
    Type Detection Logic:
    - Type 1: requirements.value=N/A AND waivers.value=N/A/0
    - Type 2: requirements.value>0 AND pattern_items AND waivers.value=N/A/0
    - Type 3: requirements.value>0 AND pattern_items AND waivers.value>0
    - Type 4: requirements.value=N/A AND waivers.value>0
    
    Parsing Logic:
    - Extract all non-scannable registers from dft_chainRegs.rpt
    - Categorize by DFT issue type (9 categories)
    - Store register metadata (category, line number, file path)
    - Type 1: Check if any non-scannable registers exist
    - Type 2/3: Match against category patterns
    - Type 3/4: Apply category-specific waivers
    """
    
    def __init__(self):
        super().__init__(
            check_module="5.0_SYNTHESIS_CHECK",
            item_id="IMP-5-0-0-13",
            item_desc="Confirm scan is successfully inserted and non-scannable flops have been peer reviewed and waived?"
        )
        self._reg_metadata: Dict[str, Dict[str, Any]] = {}
        self._forbidden_patterns: List[str] = []
        self._dft_report_path: Optional[Path] = None
    
    # =========================================================================
    # Input File Parsing
    # =========================================================================
    
    def _parse_dft_chain_rpt(self) -> List[str]:
        """
        Parse dft_chainRegs.rpt to extract all non-scannable registers.
        
        Format: Multiple sections for different DFT categories
        Example: 
            "Reporting registers that fail DFT rules"
            "reg_name"
        
        Returns:
            List of all register names (formatted as "category:register_name")
        """
        if not self.item_data or 'input_files' not in self.item_data:
            return []
        
        # Validate input files using BaseChecker method
        valid_files, missing_files = self.validate_input_files()
        
        # Store missing files for error reporting
        if missing_files:
            self._reg_metadata['_missing_input_files'] = {
                'files': missing_files,
                'count': len(missing_files)
            }
            return []
        
        all_registers = []
        
        for file_path in valid_files:
            if 'dft_chain' not in file_path.name.lower():
                continue
            
            self._dft_report_path = file_path
            
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            # Extract summary to know which categories have issues
            summary = self._extract_summary(lines)
            
            # Extract registers from all categories
            for category_key, count in summary.items():
                if count == 0:
                    continue
                
                # Extract registers for this category
                registers, start_line = self._extract_registers_for_section(lines, category_key)
                
                # Store metadata and format as "category:register_name"
                for reg in registers:
                    formatted_name = f"{category_key}:{reg}"
                    all_registers.append(formatted_name)
                    self._reg_metadata[formatted_name] = {
                        'category': category_key,
                        'register': reg,
                        'line_number': start_line,
                        'file_path': str(file_path)
                    }
        
        return all_registers
    
    def _match_forbidden_category(self, reg_name: str, patterns: List[str]) -> Optional[str]:
        """
        Check if register's category matches any forbidden pattern.
        
        Supports both glob patterns and regex:
        - Glob: *fail* -> matches any category containing "fail"
        - Exact: fail_dft_rules -> matches exact category name
        
        Args:
            reg_name: Register name (format: "category:register")
            patterns: List of patterns (glob or regex)
        
        Returns:
            Matched pattern if found, None otherwise
        """
        # Extract category from "category:register" format
        if ':' not in reg_name:
            return None
        
        category = reg_name.split(':', 1)[0]
        
        for pattern in patterns:
            try:
                # Convert glob pattern to regex if needed
                regex_pattern = pattern
                if '*' in pattern and not pattern.startswith('^'):
                    # Glob pattern: convert * to .*
                    regex_pattern = pattern.replace('*', '.*')
                
                # Use search instead of match to find pattern anywhere in string
                if re.search(regex_pattern, category):
                    return pattern
            except re.error:
                # If pattern is not valid regex, try exact match
                if pattern == category:
                    return pattern
        return None
    
    def _find_violations(self, all_registers: List[str], forbidden_patterns: List[str]) -> List[Tuple[str, str]]:
        """
        Find registers whose category matches forbidden patterns.
        
        Args:
            all_registers: All register names (format: "category:register")
            forbidden_patterns: Forbidden category patterns (regex)
        
        Returns:
            List of (register_name, matched_pattern) tuples
        """
        violations = []
        
        for reg_name in all_registers:
            matched_pattern = self._match_forbidden_category(reg_name, forbidden_patterns)
            if matched_pattern:
                violations.append((reg_name, matched_pattern))
        
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
            
            # Get forbidden category patterns
            requirements = self.get_requirements()
            self._forbidden_patterns = requirements.get('pattern_items', []) if requirements else []
            
            # Detect checker type (use BaseChecker method)
            checker_type = self.detect_checker_type()
            
            # Parse dft_chainRegs.rpt
            all_registers = self._parse_dft_chain_rpt()
            
            # Find violations (registers matching forbidden category patterns)
            violations = self._find_violations(all_registers, self._forbidden_patterns)
            
            # Execute based on type
            if checker_type == 1:
                return self._execute_type1(all_registers, violations)
            elif checker_type == 2:
                return self._execute_type2(all_registers, violations)
            elif checker_type == 3:
                return self._execute_type3(all_registers, violations)
            else:  # checker_type == 4
                return self._execute_type4(all_registers, violations)
        except ConfigurationError as e:
            return e.check_result
    
    # =========================================================================
    # Type 1: Boolean Check (No Waiver Logic)
    # =========================================================================
    
    def _execute_type1(self, all_registers: List[str], violations: List[Tuple[str, str]]) -> CheckResult:
        """
        Type 1: requirements.value=N/A, waivers.value=N/A/0
        
        Logic: 
        - Check if all registers are scannable (no non-scannable registers)
        - violations = Non-scannable registers found
        """
        waivers = self.get_waivers()
        waiver_value = waivers.get('value', 'N/A') if waivers else 'N/A'
        waive_items = waivers.get('waive_items', []) if waivers else []
        
        # Check if waiver=0 (display mode)
        is_waiver_zero = (waiver_value == 0)
        
        # Check for missing input files first
        missing_info = self._reg_metadata.get('_missing_input_files')
        if missing_info:
            return self.create_missing_files_error(missing_info['files'])
        
        details = []
        
        # Special case: No non-scannable registers found - PASS
        if not all_registers:
            details.append(DetailItem(
                severity=Severity.INFO,
                name="",
                line_number=0,
                file_path=str(self._dft_report_path) if self._dft_report_path else "N/A",
                reason="All registers are scannable - no DFT issues found"
            ))
            
            info_groups = {
                "INFO01": {
                    "description": "All registers are scannable",
                    "items": []
                }
            }
            
            return create_check_result(
                value=0,
                is_pass=True,
                has_pattern_items=False,
                has_waiver_value=bool(waive_items),
                details=details,
                info_groups=info_groups,
                item_desc=self.item_desc
            )
        
        # Non-scannable registers found
        if is_waiver_zero:
            # waiver=0: Convert FAIL to INFO
            for reg_name in all_registers:
                metadata = self._reg_metadata.get(reg_name, {})
                category = metadata.get('category', '')
                category_desc = CATEGORY_DESC.get(category, 'Non-scannable register')
                details.append(DetailItem(
                    severity=Severity.INFO,
                    name=reg_name,
                    line_number=metadata.get('line_number', ''),
                    file_path=metadata.get('file_path', ''),
                    reason=f"{category_desc}[WAIVED_AS_INFO]"
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
            # Normal mode: Non-scannable registers = FAIL
            for reg_name in all_registers:
                metadata = self._reg_metadata.get(reg_name, {})
                category = metadata.get('category', '')
                category_desc = CATEGORY_DESC.get(category, 'Non-scannable register')
                details.append(DetailItem(
                    severity=Severity.FAIL,
                    name=reg_name,
                    line_number=metadata.get('line_number', ''),
                    file_path=metadata.get('file_path', ''),
                    reason=category_desc
                ))
            
            is_pass = False
        
        # Group by category
        error_groups = self._create_category_groups(all_registers, details)
        
        return create_check_result(
            value=len(all_registers),
            is_pass=is_pass,
            has_pattern_items=False,
            has_waiver_value=bool(waive_items),
            details=details,
            error_groups=error_groups if error_groups else None,
            item_desc=self.item_desc
        )
    
    # =========================================================================
    # Type 2: Value Comparison (No Waiver Logic)
    # =========================================================================
    
    def _execute_type2(self, all_registers: List[str], violations: List[Tuple[str, str]]) -> CheckResult:
        """
        Type 2: requirements.value>0, pattern_items exists, waivers.value=N/A/0
        
        Logic: 
        - violations (matched) = Forbidden category registers found (BAD)
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
        missing_info = self._reg_metadata.get('_missing_input_files')
        if missing_info:
            return self.create_missing_files_error(missing_info['files'])
        
        details = []
        
        # Find which patterns were not violated (good)
        violated_patterns = set(pattern for _, pattern in violations)
        unmatched_patterns = [p for p in self._forbidden_patterns if p not in violated_patterns]
        
        # Add violations (forbidden category registers found)
        if is_waiver_zero:
            # waiver=0: Convert FAIL to INFO
            for reg_name, pattern in violations:
                metadata = self._reg_metadata.get(reg_name, {})
                category = metadata.get('category', '')
                category_desc = CATEGORY_DESC.get(category, 'Non-scannable register')
                details.append(DetailItem(
                    severity=Severity.INFO,
                    name=reg_name,
                    line_number=metadata.get('line_number', ''),
                    file_path=metadata.get('file_path', ''),
                    reason=f"{category_desc} (matches pattern: {pattern})[WAIVED_AS_INFO]"
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
            for reg_name, pattern in violations:
                metadata = self._reg_metadata.get(reg_name, {})
                category = metadata.get('category', '')
                category_desc = CATEGORY_DESC.get(category, 'Non-scannable register')
                details.append(DetailItem(
                    severity=Severity.FAIL,
                    name=reg_name,
                    line_number=metadata.get('line_number', ''),
                    file_path=metadata.get('file_path', ''),
                    reason=f"{category_desc} (matches pattern: {pattern})"
                ))
            
            # Add unmatched patterns as INFO (good - not found)
            for pattern in unmatched_patterns:
                details.append(DetailItem(
                    severity=Severity.INFO,
                    name=pattern,
                    line_number='',
                    file_path='',
                    reason="Forbidden category pattern not found (good)"
                ))
            
            is_pass = (len(violations) == expected_value)
        
        return create_check_result(
            value=len(violations),
            is_pass=is_pass,
            has_pattern_items=True,
            has_waiver_value=bool(waive_items),
            details=details,
            item_desc=self.item_desc,
            default_group_desc="Forbidden category registers found"
        )
    
    # =========================================================================
    # Type 3: Value Comparison WITH Waiver Logic
    # =========================================================================
    
    def _execute_type3(self, all_registers: List[str], violations: List[Tuple[str, str]]) -> CheckResult:
        """
        Type 3: requirements.value>0, pattern_items exists, waivers.value>0
        
        Logic: 
        - violations = Forbidden category registers found
        - Separate into: unwaived (FAIL), waived (INFO), unused waivers (WARN)
        """
        waivers = self.get_waivers()
        waive_items_dict = self._get_waive_items_with_reasons()
        waive_items = list(waive_items_dict.keys())
        
        # Check for missing input files first
        missing_info = self._reg_metadata.get('_missing_input_files')
        if missing_info:
            return self.create_missing_files_error(missing_info['files'])
        
        # Separate violations into waived/unwaived
        waive_set = set(waive_items)
        unwaived = [(reg, pattern) for reg, pattern in violations if reg not in waive_set]
        waived = [(reg, pattern) for reg, pattern in violations if reg in waive_set]
        
        # Find unused waivers
        violated_regs = set(reg for reg, _ in violations)
        unused_waivers = [item for item in waive_items if item not in violated_regs]
        
        # Find unmatched patterns (good - not violated)
        violated_patterns = set(pattern for _, pattern in violations)
        unmatched_patterns = [p for p in self._forbidden_patterns if p not in violated_patterns]
        
        details = []
        
        # FAIL: Unwaived violations
        for reg_name, pattern in unwaived:
            metadata = self._reg_metadata.get(reg_name, {})
            category = metadata.get('category', '')
            category_desc = CATEGORY_DESC.get(category, 'Non-scannable register')
            details.append(DetailItem(
                severity=Severity.FAIL,
                name=reg_name,
                line_number=metadata.get('line_number', ''),
                file_path=metadata.get('file_path', ''),
                reason=f"{category_desc} (matches pattern: {pattern})"
            ))
        
        # INFO: Waived violations
        for reg_name, pattern in waived:
            metadata = self._reg_metadata.get(reg_name, {})
            waiver_reason = waive_items_dict.get(reg_name, '')
            # Clean up reason (remove leading #)
            if waiver_reason:
                waiver_reason = waiver_reason.replace('#', '').strip()
            reason = f"Waived: {waiver_reason}[WAIVER]" if waiver_reason else f"Waived[WAIVER]"
            details.append(DetailItem(
                severity=Severity.INFO,
                name=reg_name,
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
                reason="Forbidden category pattern not found (good)"
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
        
        # Create explicit error groups with category-specific descriptions
        error_groups = {}
        warn_groups = {}
        info_groups = {}
        
        # Group unwaived by category
        if unwaived:
            error_groups = self._create_category_error_groups([reg for reg, _ in unwaived])
        
        if unused_waivers:
            warn_groups["WARN01"] = {
                "description": "Unused waivers (not found in actual violations)",
                "items": unused_waivers
            }
        
        # Combine waived and unmatched into INFO
        info_items = []
        if waived:
            info_items.extend([reg for reg, _ in waived])
        if unmatched_patterns:
            info_items.extend(unmatched_patterns)
        
        if info_items:
            # Group waived by category
            waived_by_category = self._group_by_category([reg for reg, _ in waived])
            info_idx = 1
            for category, regs in sorted(waived_by_category.items()):
                category_desc = CATEGORY_DESC.get(category, category)
                info_groups[f"INFO{info_idx:02d}"] = {
                    "description": f"Waived: {category_desc}",
                    "items": regs
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
    
    def _execute_type4(self, all_registers: List[str], violations: List[Tuple[str, str]]) -> CheckResult:
        """
        Type 4: requirements.value=N/A, waivers.value>0
        
        Logic: Boolean check + Waiver separation (FAIL/INFO/WARN)
        """
        waivers = self.get_waivers()
        waive_items_dict = self._get_waive_items_with_reasons()
        waive_items = list(waive_items_dict.keys())
        
        # Check for missing input files first
        missing_info = self._reg_metadata.get('_missing_input_files')
        if missing_info:
            return self.create_missing_files_error(missing_info['files'])
        
        # For Type 4, check all non-scannable registers
        # Separate into waived/unwaived
        waive_set = set(waive_items)
        unwaived = [reg for reg in all_registers if reg not in waive_set]
        waived = [reg for reg in all_registers if reg in waive_set]
        
        # Find unused waivers
        unused_waivers = [item for item in waive_items if item not in all_registers]
        
        details = []
        
        # FAIL: Unwaived non-scannable registers
        for reg_name in sorted(unwaived):
            metadata = self._reg_metadata.get(reg_name, {})
            category = metadata.get('category', '')
            category_desc = CATEGORY_DESC.get(category, 'Non-scannable register')
            details.append(DetailItem(
                severity=Severity.FAIL,
                name=reg_name,
                line_number=metadata.get('line_number', ''),
                file_path=metadata.get('file_path', ''),
                reason=category_desc
            ))
        
        # INFO: Waived non-scannable registers
        for reg_name in sorted(waived):
            metadata = self._reg_metadata.get(reg_name, {})
            waiver_reason = waive_items_dict.get(reg_name, '')
            # Clean up reason (remove leading #)
            if waiver_reason:
                waiver_reason = waiver_reason.replace('#', '').strip()
            reason = f"Waived: {waiver_reason}[WAIVER]" if waiver_reason else "Waived[WAIVER]"
            details.append(DetailItem(
                severity=Severity.INFO,
                name=reg_name,
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
        
        # Create explicit error groups with category-specific descriptions
        error_groups = {}
        warn_groups = {}
        info_groups = {}
        
        # Group unwaived by category
        if unwaived:
            error_groups = self._create_category_error_groups(unwaived)
        
        if unused_waivers:
            warn_groups["WARN01"] = {
                "description": "Unused waivers (not found in actual violations)",
                "items": unused_waivers
            }
        
        # Group waived by category
        if waived:
            waived_by_category = self._group_by_category(waived)
            info_idx = 1
            for category, regs in sorted(waived_by_category.items()):
                category_desc = CATEGORY_DESC.get(category, category)
                info_groups[f"INFO{info_idx:02d}"] = {
                    "description": f"Waived: {category_desc}",
                    "items": regs
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
        
        Supports two formats:
        1. Dict format (standard):
           - name: "category:register_name"
             reason: "Approved by architect"
        
        2. String format (legacy):
           "category:register , #reason"
        
        Returns:
            Dict mapping "category:register" to reason string
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
                # Legacy format: "category:register , #reason"
                parts = entry.split(',', 1)
                reg_part = parts[0].strip()
                reason = parts[1].strip() if len(parts) > 1 else ""
                if reg_part:
                    waive_map[reg_part] = reason
        
        return waive_map
    
    def _group_by_category(self, registers: List[str]) -> Dict[str, List[str]]:
        """
        Group registers by category.
        
        Args:
            registers: List of register names (format: "category:register")
        
        Returns:
            Dict mapping category to list of register names
        """
        by_category = {}
        for reg_name in registers:
            if ':' in reg_name:
                category = reg_name.split(':', 1)[0]
                if category not in by_category:
                    by_category[category] = []
                by_category[category].append(reg_name)
        return by_category
    
    def _create_category_groups(self, registers: List[str], details: List[DetailItem]) -> Dict:
        """
        Create error groups organized by category.
        
        Used for Type 1 when grouping all registers.
        """
        # Group by category
        by_category = self._group_by_category(registers)
        
        error_groups = {}
        idx = 1
        
        for category, regs in sorted(by_category.items()):
            category_desc = CATEGORY_DESC.get(category, category)
            
            # Determine severity from details
            severity_prefix = "ERROR"
            for detail in details:
                if detail.name in regs:
                    if detail.severity == Severity.INFO:
                        severity_prefix = "INFO"
                    break
            
            error_groups[f"{severity_prefix}{idx:02d}"] = {
                "description": category_desc,
                "items": regs
            }
            idx += 1
        
        return error_groups
    
    def _create_category_error_groups(self, unwaived_regs: List[str]) -> Dict:
        """
        Create ERROR groups organized by category for unwaived registers.
        
        Used for Type 3/4.
        """
        by_category = self._group_by_category(unwaived_regs)
        
        error_groups = {}
        idx = 1
        
        for category, regs in sorted(by_category.items()):
            category_desc = CATEGORY_DESC.get(category, category)
            error_groups[f"ERROR{idx:02d}"] = {
                "description": category_desc,
                "items": regs
            }
            idx += 1
        
        return error_groups
    
    # =========================================================================
    # DFT Report Parsing Methods
    # =========================================================================
    
    def _extract_summary(self, lines: List[str]) -> Dict[str, int]:
        """Extract summary statistics from dft_chainRegs.rpt."""
        summary = {}
        in_summary = False
        
        for line in lines:
            if 'Summary:' in line:
                in_summary = True
                continue
            
            if in_summary:
                for key, pattern in SUMMARY_PATTERNS.items():
                    match = pattern.search(line)
                    if match:
                        summary[key] = int(match.group(1))
        
        return summary
    
    def _extract_registers_for_section(self, lines: List[str], section_key: str) -> Tuple[List[str], int]:
        """
        Extract register list for a specific section.
        
        Returns:
            (list of registers, start_line_number)
        """
        registers = []
        header_pattern = SECTION_HEADERS.get(section_key)
        if not header_pattern:
            return registers, 0
        
        in_section = False
        start_line = 0
        
        for i, line in enumerate(lines, 1):
            if re.search(header_pattern, line):
                in_section = True
                start_line = i
                continue
            
            if in_section:
                # Exit section when we hit next section header or Summary
                if any(re.search(pattern, line) for pattern in SECTION_HEADERS.values() if pattern != header_pattern):
                    break
                if 'Summary:' in line:
                    break
                
                # Extract register names
                stripped = line.strip()
                if stripped and not line.startswith('Reporting'):
                    reg_name = stripped.split()[0] if stripped else ''
                    if reg_name:
                        registers.append(reg_name)
        
        return registers, start_line


################################################################################
# Main Entry Point
################################################################################

if __name__ == '__main__':
    checker = DFTScanChecker()
    checker.run()

