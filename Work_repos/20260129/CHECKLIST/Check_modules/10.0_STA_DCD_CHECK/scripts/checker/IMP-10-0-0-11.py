################################################################################
# Script Name: IMP-10-0-0-11.py
#
# Purpose:
#   Confirm the timing of all path groups is clean.
#
# Logic:
#   - Parse input files: check_signoff.results
#   - Extract header lines to build column mapping (path groups and timing types)
#   - Parse data rows to extract view names and timing results (slack/violation counts)
#   - Identify violations where slack < 0 and violation count > 0
#   - Aggregate results across all views and path groups
#   - Report violations with view name, path group, timing type, WNS, and count
#   - Apply waiver logic if configured (Type 3/4)
#   - Generate summary statistics (total views, clean views, violated views)
#
# Auto Type Detection:
#   Type 1: requirements.value=N/A, waivers.value=N/A/0 → Boolean check
#   Type 2: requirements.value>0, pattern_items exists, waivers.value=N/A/0 → Value comparison
#   Type 3: requirements.value>0, pattern_items exists, waivers.value>0 → Value with waiver logic
#   Type 4: requirements.value=N/A, waivers.value>0 → Boolean with waiver logic
#
# Waiver Tag Rules:
#   When waivers.value > 0 (Type 3/4):
#     - All waive_items related INFO/FAIL/WARN reason suffix: [WAIVER]
#   When waivers.value = 0 (Type 1/2):
#     - waive_items output as INFO with suffix: [WAIVED_INFO]
#     - FAIL/WARN converted to INFO with suffix: [WAIVED_AS_INFO]
#   All types support value = N/A
#
# Refactored: 2025-12-16 (Using checker_templates v1.1.0)
#
# Author: yyin
# Date: 2025-12-16
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
from output_formatter import DetailItem, Severity, create_check_result

# MANDATORY: Import template mixins (checker_templates v1.1.0)
from checker_templates.waiver_handler_template import WaiverHandlerMixin
from checker_templates.output_builder_template import OutputBuilderMixin
from checker_templates.input_file_parser_template import InputFileParserMixin


# MANDATORY: Inherit mixins in correct order (InputFileParserMixin first if used)
class Check_10_0_0_11(InputFileParserMixin, OutputBuilderMixin, WaiverHandlerMixin, BaseChecker):
    """
    IMP-10-0-0-11: Confirm the timing of all path groups is clean.
    
    Checking Types:
    - Type 1: requirements=N/A, waivers=N/A/0 → Informational/Boolean check
    - Type 2: requirements>0, waivers=N/A/0 → Value check without waivers
    - Type 3: requirements>0, waivers>0 → Value check with waiver logic
    - Type 4: requirements=N/A, waivers=>0 → Boolean check with waiver logic
    
    Template Library v1.1.0:
    - Uses InputFileParserMixin for parsing (parse_log_with_patterns, normalize_command)
    - Uses WaiverHandlerMixin for waiver processing (parse_waive_items, match_waiver_entry)
    - Uses OutputBuilderMixin for result construction (build_complete_output)
    """
    
    # =========================================================================
    # UNIFIED DESCRIPTIONS - MUST be identical across ALL Type 1/2/3/4
    # =========================================================================
    FOUND_DESC = "Clean timing path groups"
    MISSING_DESC = "Timing violations detected"
    WAIVED_DESC = "Waived timing violations"
    UNUSED_DESC = "Unused waiver entries"
    FOUND_REASON = "Path group meets timing requirements"
    MISSING_REASON = "Timing violation detected"
    WAIVED_BASE_REASON = "Timing violation waived per design approval"
    UNUSED_WAIVER_REASON = "Waiver entry not matched"
    
    def __init__(self):
        """Initialize the checker."""
        super().__init__(
            check_module="10.0_STA_DCD_CHECK",
            item_id="IMP-10-0-0-11",
            item_desc="Confirm the timing of all path groups is clean."
        )
        # Store parsed data for reuse
        self._parsed_items: List[Dict[str, Any]] = []
        self._column_map: Dict[int, Tuple[str, str]] = {}
        self._total_views: int = 0
        self._clean_views: int = 0
    
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
    
    def _parse_input_files(self) -> Dict[str, Any]:
        """
        Parse input files to extract timing violations.
        
        Parses MCMM timing signoff summary reports with tabular format:
        - Header line: path group names
        - Sub-header line: timing types (setup/hold)
        - Data rows: view names with slack(violation_count) per column
        
        Returns:
            Dict with parsed data:
            - 'items': List[Dict] - Violations with metadata (line_number, file_path)
            - 'metadata': Dict - Summary statistics
            - 'errors': List - Parsing errors
        """
        # 1. Validate input files - CRITICAL: returns TUPLE (valid_files, missing_files)
        valid_files, missing_files = self.validate_input_files()
        
        # FIXED: Explicitly check for empty list to ensure proper error handling
        if missing_files and len(missing_files) > 0:
            raise ConfigurationError(
                self.create_missing_files_error(missing_files)
            )
        
        # FIXED: Explicitly check for empty list to ensure proper error handling
        if not valid_files or len(valid_files) == 0:
            raise ConfigurationError(
                self.create_error_result(
                    "No valid input files found",
                    "Configuration Error"
                )
            )
        
        # 2. Parse all files
        all_violations = []
        all_clean_items = []
        total_views = 0
        clean_views_count = 0
        errors = []
        
        for file_path in valid_files:
            try:
                violations, clean_items, views_analyzed, clean_count = self._parse_single_file(file_path)
                all_violations.extend(violations)
                all_clean_items.extend(clean_items)
                total_views += views_analyzed
                clean_views_count += clean_count
            except Exception as e:
                errors.append(f"Error parsing {file_path}: {str(e)}")
        
        # 3. Store frequently reused data on self
        self._parsed_items = all_violations
        self._total_views = total_views
        self._clean_views = clean_views_count
        
        return {
            'items': all_violations,
            'clean_items': all_clean_items,
            'metadata': {
                'total_views': total_views,
                'clean_views': clean_views_count,
                'violated_views': total_views - clean_views_count
            },
            'errors': errors
        }
    
    def _parse_single_file(self, file_path: Path) -> Tuple[List[Dict], List[Dict], int, int]:
        """
        Parse a single timing signoff file.
        
        Args:
            file_path: Path to the file to parse
            
        Returns:
            Tuple of (violations, clean_items, total_views, clean_views)
        """
        violations = []
        clean_items = []
        column_map = {}
        path_groups = []
        timing_types = []
        views_analyzed = 0
        clean_views = 0
        
        # Patterns for parsing
        pattern_cell = re.compile(r'(---|\-?\d+\.\d+)\(\s*(\d+)\)')
        
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            
            # State machine for parsing
            header_parsed = False
            subheader_parsed = False
            
            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                if not line:
                    continue
                
                # Parse header line (path groups)
                if not header_parsed and ',' in line and 'View' not in line:
                    parts = [p.strip() for p in line.split(',')]
                    if len(parts) > 1:
                        # Extract path group names from header
                        for i, part in enumerate(parts[1:], 1):
                            # Extract path group name (e.g., "reg2reg()" -> "reg2reg")
                            match = re.search(r'(\w+)\(\)', part)
                            if match:
                                path_groups.append(match.group(1))
                        header_parsed = True
                        continue
                
                # Parse sub-header line (timing types)
                if header_parsed and not subheader_parsed and line.startswith('View'):
                    parts = [p.strip() for p in line.split(',')]
                    if len(parts) > 1:
                        # Extract timing types (setup/hold)
                        for i, part in enumerate(parts[1:], 1):
                            match = re.search(r'(setup|hold)', part)
                            if match:
                                timing_types.append(match.group(1))
                        
                        # Build column map: {column_index: (path_group, timing_type)}
                        if len(path_groups) == len(timing_types):
                            for i in range(len(path_groups)):
                                column_map[i] = (path_groups[i], timing_types[i])
                        
                        subheader_parsed = True
                        continue
                
                # Parse data rows
                if header_parsed and subheader_parsed and ',' in line:
                    parts = [p.strip() for p in line.split(',')]
                    if len(parts) < 2:
                        continue
                    
                    view_name = parts[0]
                    if not view_name or view_name == 'View':
                        continue
                    
                    views_analyzed += 1
                    view_has_violations = False
                    
                    # Parse each column
                    for col_idx, cell in enumerate(parts[1:]):
                        if col_idx not in column_map:
                            continue
                        
                        path_group, timing_type = column_map[col_idx]
                        
                        # Extract slack and violation count
                        match = pattern_cell.search(cell)
                        if not match:
                            continue
                        
                        slack_str = match.group(1)
                        vio_count_str = match.group(2)
                        
                        # Skip "---" entries (not applicable)
                        if slack_str == '---':
                            continue
                        
                        try:
                            slack = float(slack_str)
                            vio_count = int(vio_count_str)
                        except ValueError:
                            continue
                        
                        # Check for violations (negative slack with non-zero count)
                        if slack < 0 and vio_count > 0:
                            view_has_violations = True
                            violation_name = f"{view_name}: {path_group} ({timing_type})"
                            violations.append({
                                'name': violation_name,
                                'view': view_name,
                                'path_group': path_group,
                                'timing_type': timing_type,
                                'wns': slack,
                                'violation_count': vio_count,
                                'line_number': line_num,
                                'file_path': str(file_path)
                            })
                        elif slack >= 0 or vio_count == 0:
                            # Clean timing for this path group
                            clean_name = f"{view_name}: {path_group} ({timing_type})"
                            clean_items.append({
                                'name': clean_name,
                                'view': view_name,
                                'path_group': path_group,
                                'timing_type': timing_type,
                                'slack': slack,
                                'line_number': line_num,
                                'file_path': str(file_path)
                            })
                    
                    if not view_has_violations:
                        clean_views += 1
        
        return violations, clean_items, views_analyzed, clean_views
    
    # =========================================================================
    # Type 1: Informational/Boolean Check
    # =========================================================================
    
    def _execute_type1(self) -> CheckResult:
        """
        Type 1: Informational or Boolean check (no waivers).
        
        Use OutputBuilderMixin.build_complete_output() for automatic formatting.
        
        Returns:
            CheckResult with is_pass based on check logic
        """
        # Parse input
        data = self._parse_input_files()
        violations = data.get('items', [])
        clean_items = data.get('clean_items', [])
        metadata = data.get('metadata', {})
        
        # Build found_items dict with metadata for clean path groups
        found_items = {}
        for item in clean_items:
            found_items[item['name']] = {
                'name': item['name'],
                'line_number': item.get('line_number', 0),
                'file_path': item.get('file_path', 'N/A')
            }
        
        # Build missing_items list for violations
        missing_items = []
        for violation in violations:
            vio_name = f"{violation['view']}: {violation['path_group']} ({violation['timing_type']}) WNS={violation['wns']:.4f}ns ({violation['violation_count']} violations)"
            missing_items.append(vio_name)
        
        # Use template helper for automatic output formatting
        # UNIFIED DESCRIPTIONS: Use class constants for consistency across all Types
        return self.build_complete_output(
            found_items=found_items,
            missing_items=missing_items,
            found_desc=self.FOUND_DESC,
            missing_desc=self.MISSING_DESC,
            found_reason=self.FOUND_REASON,
            missing_reason=self.MISSING_REASON
        )
    
    # =========================================================================
    # Type 2: Value comparison
    # =========================================================================
    
    def _execute_type2(self) -> CheckResult:
        """
        Type 2: Value comparison check (pattern matching).
        
        Searches clean_items for entries matching pattern_items.
        PASS only if len(matched) == requirements.value.
        
        Returns:
            CheckResult with is_pass based on value comparison
        """
        # Parse input
        data = self._parse_input_files()
        clean_items = data.get('clean_items', [])
        metadata = data.get('metadata', {})
        
        # Get requirements
        requirements = self.item_data.get('requirements', {})
        pattern_items = requirements.get('pattern_items', [])
        expected_value = requirements.get('value', 'N/A')
        
        # Match each pattern against clean_items (pattern matching)
        found_items = {}
        missing_patterns = []
        
        for pattern in pattern_items:
            matched = False
            for item in clean_items:
                # Build item string for pattern matching
                item_str = f"View '{item['view']}' path_group '{item['path_group']}' {item['timing_type']}"
                
                # Pattern matching: check if pattern is contained in item_str
                if pattern in item_str:
                    item_name = f"{item['view']}: {item['path_group']} ({item['timing_type']})"
                    found_items[item_name] = {
                        'name': item_name,
                        'slack': item['slack'],  # clean_items use 'slack', not 'wns'
                        'line_number': item.get('line_number', 0),
                        'file_path': item.get('file_path', 'N/A')
                    }
                    matched = True
                    break  # Found match for this pattern
            
            if not matched:
                missing_patterns.append(pattern)
        
        # Compare count vs value
        actual_count = len(found_items)
        
        # UNIFIED DESCRIPTIONS: Use class constants for consistency across all Types
        if expected_value != 'N/A' and actual_count != expected_value:
            # FAIL: Count mismatch
            return self.build_complete_output(
                found_items=found_items,
                missing_items=missing_patterns,
                found_desc=self.FOUND_DESC,
                missing_desc=self.MISSING_DESC,
                found_reason=self.FOUND_REASON,
                missing_reason=self.MISSING_REASON
            )
        else:
            # PASS: All patterns found
            return self.build_complete_output(
                found_items=found_items,
                found_desc=self.FOUND_DESC,
                found_reason=self.FOUND_REASON
            )
    
    # =========================================================================
    # Type 3: Value Check with Waiver Logic
    # =========================================================================
    
    def _execute_type3(self) -> CheckResult:
        """
        Type 3: Pattern matching with waiver support (Type 2 + waivers).
        
        Logic:
        1. ONLY check patterns in pattern_items (ignore other violations)
        2. For each required pattern:
           - Clean (no violation) → satisfied ✅
           - Has violation but waived → satisfied ✅
           - Has violation but NOT waived → unsatisfied ❌
        3. PASS if: ALL required patterns are satisfied (clean or waived)
        
        Returns:
            CheckResult with missing_items for unsatisfied patterns only
        """
        # Parse input
        data = self._parse_input_files()
        clean_items = data.get('clean_items', [])
        violations = data.get('items', [])
        metadata = data.get('metadata', {})
        
        # Get requirements
        requirements = self.item_data.get('requirements', {})
        pattern_items = requirements.get('pattern_items', [])
        expected_value = requirements.get('value', 'N/A')
        
        # Get waivers
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # Track pattern satisfaction status
        found_clean = {}           # Patterns satisfied by clean items
        found_waived = {}          # Patterns satisfied by waived violations
        missing_patterns = {}      # Patterns with unwaived violations
        other_waived = {}          # Waived violations NOT in pattern_items
        unused_waivers = {}        # Waiver entries not used
        used_waiver_patterns = set()
        
        # Step 1: Check each required pattern
        for pattern in pattern_items:
            pattern_satisfied = False
            
            # Check if pattern has clean match
            for item in clean_items:
                item_str = f"View '{item['view']}' path_group '{item['path_group']}' {item['timing_type']}"
                
                if pattern in item_str:
                    # Pattern is clean - satisfied!
                    item_name = f"View '{item['view']}' path_group '{item['path_group']}' {item['timing_type']}: WNS={item['slack']:.4f}ns (0 violations)"
                    found_clean[item_name] = {
                        'name': item_name,
                        'slack': item['slack'],
                        'line_number': item.get('line_number', 0),
                        'file_path': item.get('file_path', 'N/A')
                    }
                    pattern_satisfied = True
                    break
            
            # If not clean, check if pattern has waived violation
            if not pattern_satisfied:
                for violation in violations:
                    vio_str = f"View '{violation['view']}' path_group '{violation['path_group']}' {violation['timing_type']}"
                    
                    if pattern in vio_str:
                        # Found violation for this pattern
                        vio_name = f"View '{violation['view']}' path_group '{violation['path_group']}' {violation['timing_type']}: WNS={violation['wns']:.4f}ns ({violation['violation_count']} violations)"
                        vio_data = {
                            'name': vio_name,
                            'wns': violation['wns'],
                            'violation_count': violation['violation_count'],
                            'line_number': violation.get('line_number', 0),
                            'file_path': violation.get('file_path', 'N/A')
                        }
                        
                        # Check if this violation is waived
                        matched_waiver = None
                        for waiver_pattern in waive_dict.keys():
                            if self.match_waiver_entry(vio_name, {waiver_pattern: waive_dict[waiver_pattern]}):
                                matched_waiver = waiver_pattern
                                used_waiver_patterns.add(waiver_pattern)
                                break
                        
                        if matched_waiver:
                            # Pattern satisfied by waived violation
                            found_waived[vio_name] = vio_data
                            pattern_satisfied = True
                        else:
                            # Pattern has unwaived violation - NOT satisfied!
                            missing_patterns[vio_name] = vio_data
                        break  # Only process first violation for each pattern
        
        # Step 2: Classify other violations (not in pattern_items) - for reporting only
        for violation in violations:
            vio_str = f"View '{violation['view']}' path_group '{violation['path_group']}' {violation['timing_type']}"
            
            # Skip if already processed as pattern violation
            is_pattern_violation = any(pattern in vio_str for pattern in pattern_items)
            if is_pattern_violation:
                continue
            
            # This violation is NOT in pattern_items
            vio_name = f"View '{violation['view']}' path_group '{violation['path_group']}' {violation['timing_type']}: WNS={violation['wns']:.4f}ns ({violation['violation_count']} violations)"
            vio_data = {
                'name': vio_name,
                'wns': violation['wns'],
                'violation_count': violation['violation_count'],
                'line_number': violation.get('line_number', 0),
                'file_path': violation.get('file_path', 'N/A')
            }
            
            # Check if waived (for info only)
            for waiver_pattern in waive_dict.keys():
                if self.match_waiver_entry(vio_name, {waiver_pattern: waive_dict[waiver_pattern]}):
                    used_waiver_patterns.add(waiver_pattern)
                    other_waived[vio_name] = vio_data
                    break
        
        # Step 3: Find unused waivers
        unused_waivers = {
            waiver_name: {
                'line_number': 0,
                'file_path': 'N/A',
                'reason': waive_dict[waiver_name]
            }
            for waiver_name in waive_dict.keys()
            if waiver_name not in used_waiver_patterns
        }
        
        # Step 4: Build output
        # Combine clean and waived for found_items
        all_found = {**found_clean, **found_waived}
        all_waived = {**found_waived, **other_waived}
        
        # UNIFIED DESCRIPTIONS: Use class constants for consistency across all Types
        return self.build_complete_output(
            found_items=found_clean,
            missing_items=missing_patterns,
            waived_items=all_waived,
            unused_waivers=unused_waivers,
            waive_dict=waive_dict,
            found_desc=self.FOUND_DESC,
            missing_desc=self.MISSING_DESC,
            waived_desc=self.WAIVED_DESC,
            found_reason=self.FOUND_REASON,
            missing_reason=self.MISSING_REASON,
            waived_base_reason=self.WAIVED_BASE_REASON
        )
    
    # =========================================================================
    # Type 4: Boolean Check with Waiver Logic
    # =========================================================================
    
    def _execute_type4(self) -> CheckResult:
        """
        Type 4: Boolean check with waiver support.
        
        Global check of all violations with waiver logic:
        - Clean items → found_items
        - Waived violations → waived_items
        - Unwaived violations → missing_items (FAIL)
        
        Returns:
            CheckResult with waiver logic applied
        """
        # Parse input
        data = self._parse_input_files()
        violations = data.get('items', [])
        clean_items = data.get('clean_items', [])
        metadata = data.get('metadata', {})
        
        # Parse waiver configuration
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # Build found_items dict with metadata for clean path groups
        found_items = {}
        for item in clean_items:
            found_items[item['name']] = {
                'name': item['name'],
                'slack': item['slack'],
                'line_number': item.get('line_number', 0),
                'file_path': item.get('file_path', 'N/A')
            }
        
        # Apply waivers to violations
        waived_items = {}
        unwaived_items = {}
        used_waiver_patterns = set()
        
        for violation in violations:
            # Format violation name to match waiver format from README:
            # "View 'view_name' path_group 'path_group' timing_type: WNS=Xns (Y violations)"
            vio_name = f"View '{violation['view']}' path_group '{violation['path_group']}' {violation['timing_type']}: WNS={violation['wns']:.4f}ns ({violation['violation_count']} violations)"
            vio_data = {
                'name': vio_name,
                'wns': violation['wns'],
                'violation_count': violation['violation_count'],
                'line_number': violation.get('line_number', 0),
                'file_path': violation.get('file_path', 'N/A')
            }
            
            # Check if this violation matches any waiver
            matched_waiver = None
            for waiver_pattern in waive_dict.keys():
                if self.match_waiver_entry(vio_name, {waiver_pattern: waive_dict[waiver_pattern]}):
                    matched_waiver = waiver_pattern
                    used_waiver_patterns.add(waiver_pattern)
                    break
            
            if matched_waiver:
                waived_items[vio_name] = vio_data
            else:
                unwaived_items[vio_name] = vio_data
        
        # Find unused waivers
        # Unused waivers: waiver patterns that didn't match any violation
        # Must be dict {name: metadata} format!
        unused_waivers = {
            waiver_name: {
                'line_number': 0,
                'file_path': 'N/A',
                'reason': waive_dict[waiver_name]
            }
            for waiver_name in waive_dict.keys()
            if waiver_name not in used_waiver_patterns
        }
        
        # Build output
        # Note: Items must be dict {name: metadata}, not list!
        # UNIFIED DESCRIPTIONS: Use class constants for consistency across all Types
        return self.build_complete_output(
            found_items=found_items,
            missing_items=unwaived_items,
            waived_items=waived_items,
            unused_waivers=unused_waivers,
            waive_dict=waive_dict,
            found_desc=self.FOUND_DESC,
            missing_desc=self.MISSING_DESC,
            waived_desc=self.WAIVED_DESC,
            found_reason=self.FOUND_REASON,
            missing_reason=self.MISSING_REASON,
            waived_base_reason=self.WAIVED_BASE_REASON
        )


# =========================================================================
# Entry Point
# =========================================================================

def main():
    """Main entry point."""
    checker = Check_10_0_0_11()
    checker.init_checker(Path(__file__))
    result = checker.execute_check()
    checker.write_output(result)
    return 0 if result.is_pass else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())