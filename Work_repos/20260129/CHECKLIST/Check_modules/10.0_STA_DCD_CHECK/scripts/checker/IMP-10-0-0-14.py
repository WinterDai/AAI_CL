################################################################################
# Script Name: IMP-10-0-0-14.py
#
# Purpose:
#   Confirm the noise/glitch check result is clean.
#
# Logic:
#   - Parse input files: noise_1.rpt, noise_2.rpt
#   - Extract header metadata (design name, view name) from each report
#   - Parse "Glitch Violations Summary" section to extract violation counts:
#     * DC tolerance violations (VH + VL)
#     * Receiver output peak violations (VH + VL)
#     * Total problem noise nets (primary pass/fail indicator)
#   - Aggregate results across all views/corners
#   - Classify views as clean (0 violations) or with violations
#   - For Type 3/4: Apply waiver logic to views with violations
#   - PASS if all views are clean or waived, FAIL if any unwaived violations exist
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
# Refactored: 2025-12-18 (Using checker_templates v1.1.0)
#
# Author: yyin
# Date: 2025-12-17
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
from checker_templates.input_file_parser_template import InputFileParserMixin  # Optional but recommended


# MANDATORY: Inherit mixins in correct order (InputFileParserMixin first if used)
class Check_10_0_0_14(InputFileParserMixin, OutputBuilderMixin, WaiverHandlerMixin, BaseChecker):
    """
    IMP-10-0-0-14: Confirm the noise/glitch check result is clean.
    
    Checking Types:
    - Type 1: requirements=N/A, waivers=N/A/0 → Informational/Boolean check
    - Type 2: requirements>0, waivers=N/A/0 → Value check without waivers
    - Type 3: requirements>0, waivers>0 → Value check with waiver logic
    - Type 4: requirements=N/A, waivers=>0 → Boolean check with waiver logic
    
    Template Library v1.1.0:
    - Uses InputFileParserMixin for parsing (parse_log_with_patterns, normalize_command)
    - Uses WaiverHandlerMixin for waiver processing (parse_waive_items(waive_items_raw), match_waiver_entry(item, waive_dict))
    - Uses OutputBuilderMixin for result construction (build_complete_output(...))
    """
    
    # =========================================================================
    # UNIFIED DESCRIPTIONS - MUST be identical across ALL Type 1/2/3/4
    # =========================================================================
    FOUND_DESC = "Noise/glitch analysis verification passed"
    MISSING_DESC = "Noise/glitch analysis verification failed"
    WAIVED_DESC = "Waived noise/glitch violations"
    FOUND_REASON = "All noise/glitch analysis views are clean (0 violations)"
    MISSING_REASON = "Noise/glitch violations detected in one or more views"
    WAIVED_BASE_REASON = "Noise/glitch violations waived per design team approval"
    
    def __init__(self):
        """Initialize the checker."""
        super().__init__(
            check_module="10.0_STA_DCD_CHECK",
            item_id="IMP-10-0-0-14",
            item_desc="Confirm the noise/glitch check result is clean."
        )
        # Custom member variables for parsed data
        self._parsed_views: List[Dict[str, Any]] = []
        self._metadata: Dict[str, str] = {}
    
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
        Parse input files to extract relevant data.
        
        Parses noise/glitch analysis reports to extract:
        - Design name and view name from header
        - Violation counts (DC tolerance, receiver output peak, total problem nets)
        - Classifies views as clean or with violations
        
        Returns:
            Dict with parsed data:
            - 'clean_items': List[Dict] - Views with 0 violations
            - 'items': List[Dict] - Views with violations (with metadata: line_number, file_path)
            - 'metadata': Dict - File metadata (design name, etc.)
            - 'errors': List - Any parsing errors encountered
        """
        # 1. Validate input files (raises ConfigurationError if missing)
        # CRITICAL: validate_input_files() returns TUPLE: (valid_files, missing_files)
        valid_files, missing_files = self.validate_input_files()
        if not valid_files or len(valid_files) == 0:
            raise ConfigurationError(
                self.create_missing_files_error(missing_files)
            )
        
        # 2. Parse each noise report file
        clean_items = []
        violation_items = []
        errors = []
        metadata = {}
        
        # Patterns for parsing noise reports
        design_pattern = re.compile(r'^#\s+Design:\s+(\S+)')
        view_pattern = re.compile(r'^#\s+View:\s+(.+)$')
        dc_violation_pattern = re.compile(r'^Number of DC tolerance violations \(VH \+ VL\)\s*=\s*(\d+)')
        peak_violation_pattern = re.compile(r'^Number of Receiver Output Peak violations \(VH \+ VL\)\s*=\s*(\d+)')
        total_problem_pattern = re.compile(r'^Number of total problem noise nets\s*=\s*(\d+)')
        
        for file_path in valid_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    current_design = None
                    current_view = None
                    dc_violations = None
                    peak_violations = None
                    total_problem_nets = None
                    
                    # Track line numbers for metadata
                    design_line = 0
                    view_line = 0
                    summary_line = 0
                    
                    for line_num, line in enumerate(f, 1):
                        # Extract design name
                        if match := design_pattern.search(line):
                            current_design = match.group(1)
                            design_line = line_num
                            if not metadata.get('design_name'):
                                metadata['design_name'] = current_design
                        
                        # Extract view name
                        elif match := view_pattern.search(line):
                            current_view = match.group(1).strip()
                            view_line = line_num
                        
                        # Extract DC tolerance violations count
                        elif match := dc_violation_pattern.search(line):
                            dc_violations = int(match.group(1))
                            summary_line = line_num
                        
                        # Extract receiver output peak violations count
                        elif match := peak_violation_pattern.search(line):
                            peak_violations = int(match.group(1))
                            if not summary_line:
                                summary_line = line_num
                        
                        # Extract total problem noise nets count (primary indicator)
                        elif match := total_problem_pattern.search(line):
                            total_problem_nets = int(match.group(1))
                            if not summary_line:
                                summary_line = line_num
                    
                    # Validate that we extracted all required data
                    if current_view is None:
                        errors.append(f"Missing view name in {file_path}")
                        continue
                    
                    if total_problem_nets is None:
                        errors.append(f"Missing violation summary in {file_path}")
                        continue
                    
                    # Set defaults for missing counts
                    if dc_violations is None:
                        dc_violations = 0
                    if peak_violations is None:
                        peak_violations = 0
                    
                    # Build item name with occurrence count format
                    if total_problem_nets == 0:
                        item_name = (
                            f"View: {current_view} - CLEAN "
                            f"(DC violations: {dc_violations}, "
                            f"Peak violations: {peak_violations}, "
                            f"Total problem nets: {total_problem_nets})"
                        )
                        clean_items.append({
                            'name': item_name,
                            'view': current_view,
                            'dc_violations': dc_violations,
                            'peak_violations': peak_violations,
                            'total_problem_nets': total_problem_nets,
                            'line_number': summary_line,
                            'file_path': str(file_path)
                        })
                    else:
                        item_name = (
                            f"View: {current_view} - VIOLATIONS DETECTED "
                            f"(DC violations: {dc_violations}, "
                            f"Peak violations: {peak_violations}, "
                            f"Total problem nets: {total_problem_nets})"
                        )
                        violation_items.append({
                            'name': item_name,
                            'view': current_view,
                            'dc_violations': dc_violations,
                            'peak_violations': peak_violations,
                            'total_problem_nets': total_problem_nets,
                            'line_number': summary_line,
                            'file_path': str(file_path)
                        })
            
            except Exception as e:
                errors.append(f"Error parsing {file_path}: {str(e)}")
        
        # 3. Store frequently reused data on self
        self._parsed_views = clean_items + violation_items
        self._metadata = metadata
        
        return {
            'clean_items': clean_items,
            'items': violation_items,
            'metadata': metadata,
            'errors': errors
        }
    
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
        clean_items = data.get('clean_items', [])
        violation_items = data.get('items', [])
        errors = data.get('errors', [])
        
        # Check for parsing errors
        if errors:
            error_msg = "; ".join(errors)
            raise ConfigurationError(f"Parsing errors: {error_msg}")
        
        # Convert clean items to dict with metadata
        found_items = {
            item['name']: {
                'name': item['name'],
                'line_number': item.get('line_number', 0),
                'file_path': item.get('file_path', 'N/A')
            }
            for item in clean_items
        }
        
        # Convert violation items to dict with metadata
        missing_items = {
            item['name']: {
                'name': item['name'],
                'line_number': item.get('line_number', 0),
                'file_path': item.get('file_path', 'N/A')
            }
            for item in violation_items
        }
        
        # Use template helper for automatic output formatting
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
        Type 2: Value comparison check (no waivers).
        
        Template auto-handles waiver=0 conversions.
        When waiver=0: All missing_items converted to INFO with [WAIVED_AS_INFO] tag.
        
        Returns:
            CheckResult with is_pass based on value comparison
        """
        # Parse input
        data = self._parse_input_files()
        clean_items = data.get('clean_items', [])
        violation_items = data.get('items', [])
        errors = data.get('errors', [])
        
        # Check for parsing errors
        if errors:
            error_msg = "; ".join(errors)
            raise ConfigurationError(f"Parsing errors: {error_msg}")
        
        # Get requirements
        requirements = self.item_data.get('requirements', {})
        pattern_items = requirements.get('pattern_items', [])
        expected_value = requirements.get('value', 'N/A')
        
        # Match patterns against clean and violation items
        # Pattern matching strategy: SUBSTRING MATCH (based on view name patterns)
        found_items = {}
        missing_items = {}
        
        all_items = clean_items + violation_items
        
        for pattern in pattern_items:
            matched = False
            for item in all_items:
                # Build searchable string from item
                item_str = f"View: {item['view']}"
                # SUBSTRING MATCH - pattern describes view characteristics
                if pattern.lower() in item_str.lower():
                    found_items[item['name']] = {
                        'name': item['name'],
                        'line_number': item.get('line_number', 0),
                        'file_path': item.get('file_path', 'N/A')
                    }
                    matched = True
                    break
            
            if not matched:
                # Missing pattern - use pattern name as item key
                missing_items[pattern] = {
                    'name': pattern,
                    'line_number': 0,
                    'file_path': 'N/A'
                }
        
        actual_count = len(found_items)
        
        # Use template helper (auto-handles waiver=0)
        return self.build_complete_output(
            found_items=found_items,
            missing_items=missing_items,
            found_desc=f"{self.FOUND_DESC} ({actual_count}/{expected_value})",
            missing_desc=f"{self.MISSING_DESC} ({len(missing_items)} patterns not matched)",
            found_reason=self.FOUND_REASON,
            missing_reason=self.MISSING_REASON
        )
    
    # =========================================================================
    # Type 3: Value Check with Waiver Logic
    # =========================================================================
    
    def _execute_type3(self) -> CheckResult:
        """
        Type 3: Value comparison with waiver support.
        
        Uses WaiverHandlerMixin for waiver processing:
        - parse_waive_items(waive_items_raw): Parse waiver configuration
        - match_waiver_entry(item, waive_dict): Match item against waivers
        
        Uses OutputBuilderMixin for result construction:
        - build_complete_output(...): Assemble final CheckResult with auto-formatting
        
        Returns:
            CheckResult with FAIL for unwaived, INFO for waived items
        """
        # Parse input
        parsed_data = self._parse_input_files()
        clean_items = parsed_data.get('clean_items', [])
        violation_items = parsed_data.get('items', [])
        errors = parsed_data.get('errors', [])
        
        # Check for parsing errors
        if errors:
            error_msg = "; ".join(errors)
            raise ConfigurationError(f"Parsing errors: {error_msg}")
        
        # Get requirements and waivers
        requirements = self.item_data.get('requirements', {})
        pattern_items = requirements.get('pattern_items', [])
        
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # Track pattern satisfaction
        found_clean = {}      # Patterns satisfied by clean items
        found_waived = {}     # Patterns satisfied by waived violations
        missing_patterns = {} # Patterns with unwaived violations
        other_waived = {}     # Waived violations NOT in pattern_items (for info)
        used_waiver_patterns = set()
        
        # Check each required pattern
        for pattern in pattern_items:
            pattern_satisfied = False
            
            # Check if pattern has clean match
            for item in clean_items:
                item_str = f"View: {item['view']}"
                if pattern.lower() in item_str.lower():
                    found_clean[item['name']] = {
                        'name': item['name'],
                        'line_number': item.get('line_number', 0),
                        'file_path': item.get('file_path', 'N/A')
                    }
                    pattern_satisfied = True
                    break
            
            # If not clean, check if pattern has waived violation
            if not pattern_satisfied:
                for violation in violation_items:
                    vio_str = f"View: {violation['view']}"
                    if pattern.lower() in vio_str.lower():
                        vio_name = violation['name']
                        vio_data = {
                            'name': vio_name,
                            'line_number': violation.get('line_number', 0),
                            'file_path': violation.get('file_path', 'N/A')
                        }
                        
                        # Check if waived
                        matched_waiver = None
                        for waiver_pattern in waive_dict.keys():
                            if self.match_waiver_entry(vio_name, {waiver_pattern: waive_dict[waiver_pattern]}):
                                matched_waiver = waiver_pattern
                                used_waiver_patterns.add(waiver_pattern)
                                break
                        
                        if matched_waiver:
                            found_waived[vio_name] = vio_data
                            pattern_satisfied = True
                        else:
                            missing_patterns[vio_name] = vio_data
                        break
        
        # Track other waived violations (not in pattern_items, for info only)
        for violation in violation_items:
            vio_str = f"View: {violation['view']}"
            is_pattern_violation = any(pattern.lower() in vio_str.lower() for pattern in pattern_items)
            if not is_pattern_violation:
                vio_name = violation['name']
                for waiver_pattern in waive_dict.keys():
                    if self.match_waiver_entry(vio_name, {waiver_pattern: waive_dict[waiver_pattern]}):
                        used_waiver_patterns.add(waiver_pattern)
                        other_waived[vio_name] = {
                            'name': vio_name,
                            'line_number': violation.get('line_number', 0),
                            'file_path': violation.get('file_path', 'N/A')
                        }
                        break
        
        # Find unused waivers
        unused_waivers = {
            w: {
                'line_number': 0,
                'file_path': 'N/A',
                'reason': waive_dict[w]
            }
            for w in waive_dict.keys()
            if w not in used_waiver_patterns
        }
        
        # Build output
        all_waived = {**found_waived, **other_waived}
        
        return self.build_complete_output(
            found_items=found_clean,
            missing_items=missing_patterns,
            waived_items=all_waived,
            unused_waivers=unused_waivers,
            waive_dict=waive_dict,
            found_desc=f"{self.FOUND_DESC} - Required patterns satisfied: {len(found_clean)}/{len(pattern_items)}",
            missing_desc=f"{self.MISSING_DESC} - Required patterns with unwaived violations",
            waived_desc=f"{self.WAIVED_DESC} (may include non-pattern violations for info)",
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
        
        Use OutputBuilderMixin.build_complete_output() with has_waiver_value=True.
        
        Returns:
            CheckResult with waiver logic applied
        """
        # Parse input
        data = self._parse_input_files()
        clean_items = data.get('clean_items', [])
        all_violations = data.get('items', [])
        errors = data.get('errors', [])
        
        # Check for parsing errors
        if errors:
            error_msg = "; ".join(errors)
            raise ConfigurationError(f"Parsing errors: {error_msg}")
        
        # Parse waiver configuration
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # Build found_items from clean items
        found_items = {}
        for item in clean_items:
            item_name = item.get('name', str(item))
            found_items[item_name] = {
                'name': item_name,
                'line_number': item.get('line_number', 0),
                'file_path': item.get('file_path', 'N/A')
            }
        
        # Apply waivers to violations
        waived_items = {}
        unwaived_items = {}
        used_waiver_patterns = set()
        
        for violation in all_violations:
            vio_name = violation.get('name', str(violation))
            vio_data = {
                'name': vio_name,
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
        unused_waivers = {
            waiver_name: {
                'line_number': 0,
                'file_path': 'N/A',
                'reason': waive_dict[waiver_name]
            }
            for waiver_name in waive_dict.keys()
            if waiver_name not in used_waiver_patterns
        }
        
        # Use template helper (auto-handles waiver=0)
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
    checker = Check_10_0_0_14()
    checker.init_checker(Path(__file__))
    result = checker.execute_check()
    checker.write_output(result)
    return 0 if result.is_pass else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())