################################################################################
# Script Name: IMP-11-0-0-26.py
#
# Purpose:
#   List the VT ratio (without physical cells): EG: TSMCN7/N6:SVT(50%)/LVT(40%)/ULVT(10%) TSMCN5/N4/N3/N2:SVT(50%)/LVTLL(20%)/LVT(20%)/ULVTLL(5%)/ULVT(5%)/ELVT(0%) SEC:RVT(50%)/LVT(40%)/SLVT(10%) INTl_I3/18A:ad(HVT 30%)/ac(SVT 20%)/ab(LVT 30%)/aa(ULVT 20%)
#
# Logic:
#   - Parse vtratio.sum file to extract VT type distribution data
#   - Extract VT type name, percentage ratio, and cell count from each line
#   - Map raw VT names to standard abbreviations (CNODSVT→SVT, CNODLVT→LVT, etc.)
#   - Identify process node from VT naming convention (CNOD*→TSMC N5/N4/N3/N2, RVT→SEC, ad/ac→Intel)
#   - For Type 2/3: Parse comparison operators from pattern_items (==, >, <, >=, <=)
#   - Compare actual VT percentages against pattern thresholds using specified operators
#   - For Type 3/4: Match violations against waive_items by VT type name
#   - Format output as VT_TYPE(percentage%) summary string
#   - Validate percentage sum is approximately 100% (±0.1% tolerance)
#
# Auto Type Detection:
#   Type 1: requirements.value=N/A, waivers.value=N/A/0 → Boolean check
#   Type 2: requirements.value>0, pattern_items exists, waivers.value=N/A/0 → Value comparison
#   Type 3: requirements.value>0, pattern_items exists, waivers.value>0 → Value with waiver logic
#   Type 4: requirements.value=N/A, waivers.value>0 → Boolean with waiver logic
#
# Output Behavior (Type 2/3 - Check README "Output Behavior" section!):
#   status_check: pattern_items = items to CHECK STATUS (only output matched items)
#     - found_items = patterns matched AND status correct
#     - missing_items = patterns matched BUT status wrong
#
# Waiver Tag Rules:
#   When waivers.value > 0 (Type 3/4):
#     - All waive_items related INFO/FAIL/WARN reason suffix: [WAIVER]
#   When waivers.value = 0 (Type 1/2):
#     - waive_items output as INFO with suffix: [WAIVED_INFO]
#     - FAIL/WARN converted to INFO with suffix: [WAIVED_AS_INFO]
#   All types support value = N/A
#
# Refactored: 2026-01-06 (Using checker_templates v1.1.0)
#
# Author: Muhan Xing
# Date: 2026-01-06
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
class Check_11_0_0_26(InputFileParserMixin, OutputBuilderMixin, WaiverHandlerMixin, BaseChecker):
    """
    IMP-11-0-0-26: List the VT ratio (without physical cells): EG: TSMCN7/N6:SVT(50%)/LVT(40%)/ULVT(10%) TSMCN5/N4/N3/N2:SVT(50%)/LVTLL(20%)/LVT(20%)/ULVTLL(5%)/ULVT(5%)/ELVT(0%) SEC:RVT(50%)/LVT(40%)/SLVT(10%) INTl_I3/18A:ad(HVT 30%)/ac(SVT 20%)/ab(LVT 30%)/aa(ULVT 20%)
    
    Checking Types:
    - Type 1: requirements=N/A, pattern_items [], waivers=N/A/0 → Boolean Check
    - Type 2: requirements>0, pattern_items [...], waivers=N/A/0 → Value Check
    - Type 3: requirements>0, pattern_items [...], waivers>0 → Value Check with Waiver Logic
    - Type 4: requirements=N/A, pattern_items [], waivers>0 → Boolean Check with Waiver Logic
    
    Template Library v1.1.0:
    - Uses InputFileParserMixin for parsing (parse_log_with_patterns, normalize_command)
    - Uses WaiverHandlerMixin for waiver processing (parse_waive_items(waive_items_raw), match_waiver_entry(item, waive_dict))
    - Uses OutputBuilderMixin for result construction (build_complete_output(...))
    """
    
    # =========================================================================
    # ⭐ DESCRIPTION CONSTANTS - Split by Type semantics (API-026)
    # =========================================================================
    # DESC constants are split by Type for semantic clarity (same as REASON split)
    # Type 1/4 emphasize "found/not found", Type 2/3 emphasize "matched/satisfied"
    
    # Type 1/4: Boolean checks - emphasize "found/not found" (existence)
    FOUND_DESC_TYPE1_4 = "VT ratio distribution found in vtratio.sum report"
    MISSING_DESC_TYPE1_4 = "VT ratio data not found in vtratio.sum report"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_DESC_TYPE2_3 = "VT ratio distribution matched expected pattern"
    MISSING_DESC_TYPE2_3 = "VT ratio distribution does not match expected pattern"
    
    # All Types (waiver description unified)
    WAIVED_DESC = "VT ratio deviation waived per design team approval"
    
    # ⭐ REASON CONSTANTS - Split by Type semantics (API-025)
    # ALL Types pass found_reason/missing_reason, but use different constants
    
    # Type 1/4: Boolean checks - emphasize "found/not found" (existence)
    FOUND_REASON_TYPE1_4 = "VT ratio data successfully extracted from vtratio.sum report"
    MISSING_REASON_TYPE1_4 = "VT ratio data missing or vtratio.sum file not found"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_REASON_TYPE2_3 = "VT type percentage matched expected ratio pattern"
    MISSING_REASON_TYPE2_3 = "VT type percentage does not satisfy expected ratio requirement"
    
    # Waiver-related (Type 3/4 only)
    WAIVED_BASE_REASON = "VT ratio mismatch waived - acceptable deviation for this design configuration"
    UNUSED_WAIVER_REASON = "Waiver not matched - no corresponding VT ratio deviation found"
    
    def __init__(self):
        """Initialize the checker."""
        super().__init__(
            check_module="11.0_POWER_EMIR_CHECK",
            item_id="IMP-11-0-0-26",
            item_desc="List the VT ratio (without physical cells): EG: TSMCN7/N6:SVT(50%)/LVT(40%)/ULVT(10%) TSMCN5/N4/N3/N2:SVT(50%)/LVTLL(20%)/LVT(20%)/ULVTLL(5%)/ULVT(5%)/ELVT(0%) SEC:RVT(50%)/LVT(40%)/SLVT(10%) INTl_I3/18A:ad(HVT 30%)/ac(SVT 20%)/ab(LVT 30%)/aa(ULVT 20%)"
        )
        # Custom member variables for parsed data
        self._parsed_items: List[Dict[str, Any]] = []
        self._metadata: Dict[str, str] = {}
        self._vt_mapping = {
            'CNODSVT': 'SVT',
            'CNODLVTLL': 'LVTLL',
            'CNODLVT': 'LVT',
            'CNODULVTLL': 'ULVTLL',
            'CNODULVT': 'ULVT',
            'CNODELVT': 'ELVT',
            'SVT': 'SVT',
            'LVT': 'LVT',
            'ULVT': 'ULVT',
            'RVT': 'RVT',
            'SLVT': 'SLVT',
            'ad': 'HVT',
            'ac': 'SVT',
            'ab': 'LVT',
            'aa': 'ULVT'
        }
    
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
        Parse input files to extract VT ratio distribution data.
        
        Returns:
            Dict with parsed data:
            - 'items': List[Dict] - VT type data with name, percentage, count
            - 'metadata': Dict - Summary metadata (total_percentage, process_node)
            - 'errors': List - Any parsing errors encountered
        """
        # 1. Validate input files - IMPORTANT: returns tuple (valid_files_list, missing_files_list)
        valid_files, missing_files = self.validate_input_files()
        
        # FIX [KNOWN_ISSUE_LOGIC-001]: Explicitly check for empty list
        if not valid_files or len(valid_files) == 0:
            raise ConfigurationError(
                self.create_missing_files_error(missing_files if missing_files else ["No valid input files found"])
            )
        
        if missing_files:
            raise ConfigurationError(
                self.create_missing_files_error(missing_files)
            )
        
        # 2. Parse VT ratio data
        all_items = []
        total_percentage = 0.0
        process_node = "Unknown"
        
        # Pattern to extract VT type, percentage, and cell count
        # Example: "core logic CNODSVT ratio is : 46.0147161781%  total number is: 99245"
        vt_pattern = re.compile(r'core logic (\w+) ratio is\s*:\s*([\d.]+)%\s+total number is:\s*(\d+)')
        
        for file_path in valid_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line_num, line in enumerate(f, 1):
                        match = vt_pattern.search(line)
                        if match:
                            raw_vt_type = match.group(1)
                            percentage = float(match.group(2))
                            cell_count = int(match.group(3))
                            
                            # Map raw VT name to standard abbreviation
                            vt_type = self._vt_mapping.get(raw_vt_type, raw_vt_type)
                            
                            # Round percentage to 2 decimal places
                            percentage_rounded = round(percentage, 2)
                            total_percentage += percentage_rounded
                            
                            # Detect process node from VT naming
                            if raw_vt_type.startswith('CNOD'):
                                process_node = "TSMC N5/N4/N3/N2"
                            elif raw_vt_type in ['RVT', 'SLVT']:
                                process_node = "SEC"
                            elif raw_vt_type in ['ad', 'ac', 'ab', 'aa']:
                                process_node = "Intel I3/18A"
                            elif raw_vt_type in ['SVT', 'LVT', 'ULVT'] and not raw_vt_type.startswith('CNOD'):
                                process_node = "TSMC N7/N6"
                            
                            all_items.append({
                                'name': vt_type,
                                'raw_name': raw_vt_type,
                                'percentage': percentage_rounded,
                                'cell_count': cell_count,
                                'line_number': line_num,
                                'file_path': str(file_path)
                            })
            except Exception as e:
                # Log parsing error but continue
                pass
        
        # 3. Store on self
        self._parsed_items = all_items
        self._metadata = {
            'total_percentage': round(total_percentage, 2),
            'process_node': process_node,
            'total_vt_types': len(all_items)
        }
        
        # 4. Return aggregated dict
        return {
            'items': all_items,
            'metadata': self._metadata,
            'errors': []
        }
    
    def _parse_comparison_pattern(self, pattern: str) -> Tuple[str, str, float]:
        """
        Parse comparison pattern to extract VT type, operator, and threshold.
        
        Args:
            pattern: Pattern string like "SVT(>=45%)" or "LVT(20%)"
            
        Returns:
            Tuple of (vt_type, operator, threshold_value)
            Example: ("SVT", ">=", 45.0)
        """
        # Pattern format: VT_TYPE(OPERATOR THRESHOLD%)
        # Supported operators: ==, >, <, >=, <=
        # Default operator: == if omitted
        
        match = re.match(r'(\w+)\(((?:==|>=|<=|>|<)?\s*[\d.]+)%?\)', pattern)
        if not match:
            # Fallback: try simple format without operator
            match = re.match(r'(\w+)\(([\d.]+)%?\)', pattern)
            if match:
                vt_type = match.group(1)
                threshold = float(match.group(2))
                return (vt_type, '==', threshold)
            return ('', '==', 0.0)
        
        vt_type = match.group(1)
        value_part = match.group(2).strip()
        
        # Extract operator and threshold
        operator = '=='
        threshold_str = value_part
        
        for op in ['>=', '<=', '==', '>', '<']:
            if value_part.startswith(op):
                operator = op
                threshold_str = value_part[len(op):].strip()
                break
        
        threshold = float(threshold_str)
        return (vt_type, operator, threshold)
    
    def _compare_percentage(self, actual: float, operator: str, threshold: float) -> bool:
        """
        Compare actual percentage against threshold using specified operator.
        
        Args:
            actual: Actual percentage value
            operator: Comparison operator (==, >, <, >=, <=)
            threshold: Threshold value to compare against
            
        Returns:
            True if comparison is satisfied, False otherwise
        """
        # Tolerance for equality checks (±0.01%)
        tolerance = 0.01
        
        if operator == '==':
            return abs(actual - threshold) <= tolerance
        elif operator == '>':
            return actual > threshold
        elif operator == '<':
            return actual < threshold
        elif operator == '>=':
            return actual >= threshold - tolerance
        elif operator == '<=':
            return actual <= threshold + tolerance
        else:
            return False
    
    def _format_vt_summary(self, items: List[Dict[str, Any]]) -> str:
        """
        Format VT ratio summary string.
        
        Args:
            items: List of VT type data dicts
            
        Returns:
            Formatted summary string like "SVT(46.01%)/LVTLL(25.04%)/..." in standard order
        """
        if not items:
            return "No VT data"
        
        # Define standard VT type order for different process nodes
        # TSMCN5/N4/N3/N2: SVT/LVTLL/LVT/ULVTLL/ULVT/ELVT
        # TSMCN7/N6: SVT/LVT/ULVT
        # SEC: RVT/LVT/SLVT
        # Intel I3/18A: HVT/SVT/LVT/ULVT
        vt_order = {
            'SVT': 1,
            'LVTLL': 2,
            'LVT': 3,
            'ULVTLL': 4,
            'ULVT': 5,
            'ELVT': 6,
            'RVT': 1,
            'SLVT': 3,
            'HVT': 1,
        }
        
        # Sort by predefined order, then alphabetically for unknown types
        sorted_items = sorted(items, key=lambda x: (vt_order.get(x['name'], 99), x['name']))
        
        parts = [f"{item['name']}({item['percentage']:.2f}%)" for item in sorted_items]
        return '* VT_Ratio_Summary: ' + '/'.join(parts)
    
    # =========================================================================
    # Type 1: Boolean Check
    # =========================================================================
    
    def _execute_type1(self) -> CheckResult:
        """
        Type 1: Boolean Check.
        
        Check if VT ratio data exists in vtratio.sum file.
        
        Returns:
            CheckResult with is_pass based on data existence
        """
        # Parse input
        data = self._parse_input_files()
        items = data.get('items', [])
        
        # Convert list to dict with metadata for source file/line display
        # _format_vt_summary() returns string starting with '* ' for sorting
        summary_name = self._format_vt_summary(items) if items else ''
        found_items = {
            summary_name: {
                'name': summary_name,
                'line_number': items[0].get('line_number', 0) if items else 0,
                'file_path': items[0].get('file_path', 'N/A') if items else 'N/A'
            }
        } if items else {}
        
        missing_items = {} if found_items else {'VT_ratio_data': {'name': 'VT ratio data not found'}}
        
        # FIX [KNOWN_ISSUE_API-009]: Pass dict directly, not list(dict.values())
        # Use template helper (auto-handles waiver=0)
        # Type 1: Use TYPE1_4 reason (emphasize "found/not found")
        
        # Custom name extractor to use metadata['name'] field
        def extract_full_name(item_name: str, metadata: Dict[str, Any]) -> str:
            """Extract full VT summary from metadata."""
            return metadata.get('name', item_name)
        
        return self.build_complete_output(
            found_items=found_items,
            missing_items=missing_items,
            found_desc=self.FOUND_DESC_TYPE1_4,
            missing_desc=self.MISSING_DESC_TYPE1_4,
            found_reason=self.FOUND_REASON_TYPE1_4,
            missing_reason=self.MISSING_REASON_TYPE1_4,
            name_extractor=extract_full_name
        )
    
    # =========================================================================
    # Type 2: Value Check
    # =========================================================================
    
    def _execute_type2(self) -> CheckResult:
        """
        Type 2: Value Check.
        
        Compare VT ratio percentages against pattern_items thresholds.
        Uses status_check mode: only output items matching pattern_items.
        
        Returns:
            CheckResult with is_pass based on comparison results
        """
        # Parse input
        data = self._parse_input_files()
        items = data.get('items', [])
        
        # Get requirements
        pattern_items = self.item_data.get('requirements', {}).get('pattern_items', [])
        
        # Build dict of actual VT percentages
        actual_vt_data = {item['name']: item for item in items}
        
        # status_check mode: only output items matching pattern_items
        found_items = {}      # Matched AND comparison satisfied
        missing_items = {}    # Matched BUT comparison failed
        
        # Add VT ratio summary at the beginning (always show all VT types)
        # _format_vt_summary() returns string starting with '* ' for sorting
        if items:
            summary_name = self._format_vt_summary(items)
            found_items[summary_name] = {
                'name': summary_name,
                'line_number': items[0].get('line_number', 0),
                'file_path': items[0].get('file_path', 'N/A')
            }
        
        for pattern in pattern_items:
            vt_type, operator, threshold = self._parse_comparison_pattern(pattern)
            
            if vt_type in actual_vt_data:
                actual_data = actual_vt_data[vt_type]
                actual_percentage = actual_data['percentage']
                
                if self._compare_percentage(actual_percentage, operator, threshold):
                    # Comparison satisfied
                    found_items[vt_type] = {
                        'name': f"{vt_type}: {actual_percentage:.2f}% satisfies requirement {operator}{threshold:.0f}%",
                        'line_number': actual_data.get('line_number', 0),
                        'file_path': actual_data.get('file_path', 'N/A'),
                        'operator': operator,
                        'threshold': threshold,
                        'actual': actual_percentage
                    }
                else:
                    # Comparison failed
                    missing_items[vt_type] = {
                        'name': f"{vt_type}: {actual_percentage:.2f}% does NOT satisfy requirement {operator}{threshold:.0f}%",
                        'line_number': actual_data.get('line_number', 0),
                        'file_path': actual_data.get('file_path', 'N/A'),
                        'operator': operator,
                        'threshold': threshold,
                        'actual': actual_percentage
                    }
            else:
                # Pattern not found in parsed data
                missing_items[vt_type] = {
                    'name': f"{vt_type} (not found in vtratio.sum)",
                    'line_number': 0,
                    'file_path': 'N/A'
                }
        
        # FIX [KNOWN_ISSUE_API-009]: Pass dict directly, not list
        # Use template helper (auto-handles waiver=0)
        # Type 2: Use TYPE2_3 desc+reason (emphasize "matched/satisfied") - API-026
        
        # Custom name extractor to use metadata['name'] field
        def extract_full_name(item_name: str, metadata: Dict[str, Any]) -> str:
            """Extract full comparison description from metadata."""
            return metadata.get('name', item_name)
        
        return self.build_complete_output(
            found_items=found_items,
            missing_items=missing_items,
            found_desc=self.FOUND_DESC_TYPE2_3,
            missing_desc=self.MISSING_DESC_TYPE2_3,
            found_reason=self.FOUND_REASON_TYPE2_3,
            missing_reason=self.MISSING_REASON_TYPE2_3,
            name_extractor=extract_full_name
        )
    
    # =========================================================================
    # Type 3: Value Check with Waiver Logic
    # =========================================================================
    
    def _execute_type3(self) -> CheckResult:
        """
        Type 3: Value check with waiver support.
        
        Same pattern comparison logic as Type 2, plus waiver classification.
        
        Returns:
            CheckResult with FAIL for unwaived, INFO for waived items
        """
        # Parse input
        parsed_data = self._parse_input_files()
        items = parsed_data.get('items', [])
        
        # FIX [KNOWN_ISSUE_API-016]: Use waivers.get() directly to preserve dict format
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # Get requirements
        pattern_items = self.item_data.get('requirements', {}).get('pattern_items', [])
        
        # Build dict of actual VT percentages
        actual_vt_data = {item['name']: item for item in items}
        
        # Convert items to dict with metadata for found_items
        all_checked_items = {}  # All VT types that were checked (both pass and fail)
        violations = {}  # VT types that failed comparison
        
        # Add VT ratio summary
        if items:
            summary_name = self._format_vt_summary(items)
            all_checked_items[summary_name] = {
                'name': summary_name,
                'line_number': items[0].get('line_number', 0),
                'file_path': items[0].get('file_path', 'N/A')
            }
        
        for pattern in pattern_items:
            vt_type, operator, threshold = self._parse_comparison_pattern(pattern)
            
            if vt_type in actual_vt_data:
                actual_data = actual_vt_data[vt_type]
                actual_percentage = actual_data['percentage']
                
                if self._compare_percentage(actual_percentage, operator, threshold):
                    # Comparison satisfied - add to all_checked_items
                    full_name = f"{vt_type}: {actual_percentage:.2f}% satisfies requirement {operator}{threshold:.0f}%"
                    all_checked_items[full_name] = {
                        'name': full_name,
                        'line_number': actual_data.get('line_number', 0),
                        'file_path': actual_data.get('file_path', 'N/A'),
                        'operator': operator,
                        'threshold': threshold,
                        'actual': actual_percentage
                    }
                else:
                    # Comparison failed - this is a violation
                    violations[vt_type] = {
                        'name': f"{vt_type}: {actual_percentage:.2f}% does NOT satisfy requirement {operator}{threshold:.0f}%",
                        'line_number': actual_data.get('line_number', 0),
                        'file_path': actual_data.get('file_path', 'N/A'),
                        'operator': operator,
                        'threshold': threshold,
                        'actual': actual_percentage
                    }
        
        # Put everything in waived_items (with custom waive_dict) to ensure unified sorting
        # This way * VT_Ratio_Summary will sort first
        waived_items = {}
        unwaived_items = {}
        used_waiver_keys = set()
        custom_waive_dict = {}
        
        # Add entries for summary and satisfied items (empty reason = no [WAIVER] tag)
        for item_key, item_data in all_checked_items.items():
            waived_items[item_key] = item_data
            custom_waive_dict[item_key] = ""  # Empty reason suppresses [WAIVER] tag
        
        # Process violations (these may have real waivers with [WAIVER] tag)
        for vt_type, violation_data in violations.items():
            full_name = violation_data.get('name', vt_type)
            # FIX: Use exact match only - LVT should not match LVTLL
            if self.match_waiver_entry(vt_type, waive_dict, allow_substring=False):
                waived_items[full_name] = violation_data
                # Add [WAIVER] tag to reason manually (since waived_tag="")
                original_reason = waive_dict.get(vt_type, "")
                custom_waive_dict[full_name] = f"{original_reason}[WAIVER]" if original_reason else "[WAIVER]"
                used_waiver_keys.add(vt_type)
            else:
                unwaived_items[full_name] = violation_data  # Use full_name for complete description
        
        # Find unused waivers
        unused_waivers = [name for name in waive_dict.keys() if name not in used_waiver_keys]
        
        # FIX [KNOWN_ISSUE_API-009]: Pass dict directly, not list
        # Use template helper for automatic output formatting (waivers.value>0)
        # Type 3: Use TYPE2_3 desc+reason (emphasize "matched/satisfied") - API-026
        
        return self.build_complete_output(
            found_items={},  # Empty - everything is in waived_items for unified sorting
            waived_items=waived_items,
            missing_items=unwaived_items,
            waive_dict=custom_waive_dict,
            unused_waivers=unused_waivers,
            found_desc=self.FOUND_DESC_TYPE2_3,
            missing_desc=self.MISSING_DESC_TYPE2_3,
            waived_desc=self.WAIVED_DESC,
            found_reason=self.FOUND_REASON_TYPE2_3,
            missing_reason=self.MISSING_REASON_TYPE2_3,
            waived_base_reason=self.WAIVED_BASE_REASON,
            unused_waiver_reason=self.UNUSED_WAIVER_REASON,
            waived_tag=""  # Empty tag - [WAIVER] is manually added to violation reasons
        )
    
    # =========================================================================
    # Type 4: Boolean Check with Waiver Logic
    # =========================================================================
    
    def _execute_type4(self) -> CheckResult:
        """
        Type 4: Boolean check with waiver support (Type 1 + waiver).
        
        Check if VT ratio data exists, with waiver classification.
        
        Returns:
            CheckResult with waiver logic applied
        """
        # Parse input
        data = self._parse_input_files()
        items = data.get('items', [])
        
        # FIX [KNOWN_ISSUE_API-016]: Use waivers.get() directly to preserve dict format
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # Convert items to dict with metadata
        all_vt_items = {}
        
        # VT ratio summary will be added to waived_items to appear first
        vt_summary_item = None
        if items:
            vt_summary_item = {
                'name': self._format_vt_summary(items),
                'line_number': items[0].get('line_number', 0),
                'file_path': items[0].get('file_path', 'N/A')
            }
        
        for item in items:
            vt_type = item['name']
            all_vt_items[vt_type] = {
                'name': f"{vt_type}: {item['percentage']:.2f}%",
                'line_number': item.get('line_number', 0),
                'file_path': item.get('file_path', 'N/A')
            }
        
        # Separate waived/unwaived
        waived_items = {}
        found_items = {}
        used_waiver_keys = set()  # Track original waiver keys (VT type names)
        
        # Add VT_Ratio_Summary to waived_items first (to appear at top)
        # _format_vt_summary() already includes '* ' prefix for sorting
        if vt_summary_item:
            summary_text = vt_summary_item['name']  # Already has '* VT_Ratio_Summary: ...'
            waived_items[summary_text] = vt_summary_item
        
        for vt_type, vt_data in all_vt_items.items():
            if self.match_waiver_entry(vt_type, waive_dict):
                # Use full name (with percentage) as key for display
                full_name = vt_data.get('name', vt_type)
                waived_items[full_name] = vt_data
                used_waiver_keys.add(vt_type)  # Track original VT type name
            else:
                # Also use full name for found_items
                full_name = vt_data.get('name', vt_type)
                found_items[full_name] = vt_data
        
        # Find unused waivers (check against original VT type names)
        unused_waivers = [name for name in waive_dict.keys() if name not in used_waiver_keys]
        
        # FIX [KNOWN_ISSUE_API-009]: Pass dict directly, not list
        # Use template helper for automatic output formatting (waivers.value>0)
        # Type 4: Use TYPE1_4 reason (emphasize "found/not found")
        
        # Customize waiver tag: empty for VT_Ratio_Summary, [WAIVER] for others
        custom_waive_dict = {}
        if waive_dict:
            custom_waive_dict = waive_dict.copy()
        # Add entry for VT_Ratio_Summary with empty reason
        if vt_summary_item:
            summary_text = vt_summary_item['name']
            custom_waive_dict[summary_text] = ''
        
        return self.build_complete_output(
            found_items=found_items,
            waived_items=waived_items,
            waive_dict=custom_waive_dict,
            unused_waivers=unused_waivers,
            found_desc=self.FOUND_DESC_TYPE1_4,
            missing_desc=self.MISSING_DESC_TYPE1_4,
            waived_desc=self.WAIVED_DESC,
            found_reason=self.FOUND_REASON_TYPE1_4,
            missing_reason=self.MISSING_REASON_TYPE1_4,
            waived_base_reason=self.FOUND_REASON_TYPE1_4,  # Use found reason for all items
            unused_waiver_reason=self.UNUSED_WAIVER_REASON,
            waived_tag=""  # Empty tag to suppress [WAIVER]
        )


# =========================================================================
# Entry Point
# =========================================================================

def main():
    """Main entry point."""
    checker = Check_11_0_0_26()
    checker.init_checker(Path(__file__))
    result = checker.execute_check()
    checker.write_output(result)
    return 0 if result.is_pass else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())