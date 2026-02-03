################################################################################
# Script Name: IMP-16-0-0-05.py
#
# Purpose:
#   Confirm remove the FIRM PHY slices IPTAG if FIRM PHY slices are reused in Hard PHY project.
#
# Logic:
#   - Parse input file: cdn_hs_phy_top.csv (IP_checker CSV report)
#   - Skip metadata header lines and locate CSV header (starts with "GDS")
#   - Parse CSV data rows to extract GDS instances with vendor, product, version, and IPTAG info
#   - Filter Cadence Design Systems instances matching FIRM PHY patterns (HPCFSC_, DDR\d+_, cdn_hs_phy_, cdns_ddr_)
#   - Validate IPTAG removal: Compare instance name vs instance_tag (if equal → PASS, if different → FAIL)
#   - Aggregate statistics: Total instances, Cadence vs TSMC counts, GDS filename
#   - Report PASS items (matching IPTAGs) as INFO01, FAIL items (mismatched IPTAGs) as ERROR01
#
# Auto Type Detection:
#   Type 1: requirements.value=N/A, pattern_items [] (empty), waivers.value=N/A/0 → Boolean Check
#   Type 2: requirements.value>0, pattern_items [...] (defined), waivers.value=N/A/0 → Value Check
#   Type 3: requirements.value>0, pattern_items [...] (defined), waivers.value>0 → Value Check with Waiver Logic
#   Type 4: requirements.value=N/A, pattern_items [] (empty), waivers.value>0 → Boolean Check with Waiver Logic
#   Note: requirements.value indicates number of patterns for config validation (doesn't affect PASS/FAIL)
#
# Output Behavior (Type 2/3):
#   status_check: pattern_items = items to CHECK STATUS (only output matched items)
#     - found_items = patterns matched AND status correct (instance == instance_tag)
#     - missing_items = patterns matched BUT status wrong (instance != instance_tag)
#
# Waiver Tag Rules:
#   When waivers.value > 0 (Type 3/4):
#     - All waive_items related INFO/FAIL/WARN reason suffix: [WAIVER]
#   When waivers.value = 0 (Type 1/2):
#     - waive_items output as INFO with suffix: [WAIVED_INFO]
#     - FAIL/WARN converted to INFO with suffix: [WAIVED_AS_INFO]
#   All types support value = N/A
#
# Refactored: 2025-12-29 (Using checker_templates v1.1.0)
#
# Author: yyin
# Date: 2025-12-18
################################################################################

from pathlib import Path
import re
import sys
import csv
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
class Check_16_0_0_05(InputFileParserMixin, OutputBuilderMixin, WaiverHandlerMixin, BaseChecker):
    """
    IMP-16-0-0-05: Confirm remove the FIRM PHY slices IPTAG if FIRM PHY slices are reused in Hard PHY project.
    
    Checking Types:
    - Type 1: requirements=N/A, pattern_items [], waivers=N/A/0 → Boolean Check
    - Type 2: requirements>0, pattern_items [...], waivers=N/A/0 → Value Check
    - Type 3: requirements>0, pattern_items [...], waivers=N/A/0 → Value Check with Waiver Logic
    - Type 4: requirements=N/A, pattern_items [], waivers>0 → Boolean Check with Waiver Logic
    
    Template Library v1.1.0:
    - Uses InputFileParserMixin for parsing (parse_log_with_patterns, normalize_command)
    - Uses WaiverHandlerMixin for waiver processing (parse_waive_items(waive_items_raw), match_waiver_entry(item, waive_dict))
    - Uses OutputBuilderMixin for result construction (build_complete_output(...))
    """
    
    # =========================================================================
    # DESCRIPTION & REASON CONSTANTS - COPY FROM README Output Descriptions!
    # =========================================================================
    # Type 1/4: Boolean checks
    FOUND_DESC_TYPE1_4 = "PHY and Block IPTAGs are consistent"
    MISSING_DESC_TYPE1_4 = "PHY and Block IPTAGs do not match"
    FOUND_REASON_TYPE1_4 = "PHY IPTAG equals Block IPTAG"
    MISSING_REASON_TYPE1_4 = "PHY IPTAG does not equal Block IPTAG"
    
    # Type 2/3: Pattern checks (unused for this checker)
    FOUND_DESC_TYPE2_3 = "PHY and Block IPTAGs are consistent"
    MISSING_DESC_TYPE2_3 = "PHY and Block IPTAGs do not match"
    FOUND_REASON_TYPE2_3 = "PHY IPTAG equals Block IPTAG"
    MISSING_REASON_TYPE2_3 = "PHY IPTAG does not equal Block IPTAG"
    
    # All Types (waiver description)
    WAIVED_DESC = "IPTAG consistency violations waived per configuration"
    
    # Waiver parameters (Type 3/4 ONLY)
    WAIVED_BASE_REASON = "IPTAG mismatch violation waived"
    
    def __init__(self):
        """Initialize the checker."""
        super().__init__(
            check_module="16.0_IPTAG_CHECK",
            item_id="IMP-16-0-0-05",
            item_desc="Confirm remove the FIRM PHY slices IPTAG if FIRM PHY slices are reused in Hard PHY project."
        )
        # Custom member variables for parsed data
        self._parsed_items: List[Dict[str, Any]] = []
        self._metadata: Dict[str, Any] = {}
    
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
        Parse input files to extract PHY and Block IPTAGs for comparison.
        
        Logic per hints.txt:
        1. Check if both PHY IPTAG and Block IPTAG exist (IMP-16-0-0-04 result)
        2. If yes, compare PHY IPTAG == Block IPTAG
        3. If no, return N/A
        
        Returns:
            Dict with parsed data:
            - 'phy_iptag': str - PHY IPTAG from Product column
            - 'block_iptag': str - Block IPTAG from Product column
            - 'both_exist': bool - Whether both IPTAGs exist
            - 'iptags_match': bool - Whether IPTAGs are equal
            - 'errors': List - Any parsing errors
        """
        import csv
        
        valid_files, missing_files = self.validate_input_files()
        if not valid_files or len(valid_files) == 0:
            raise ConfigurationError(
                self.create_missing_files_error(missing_files)
            )
        
        phy_iptag = None
        block_iptag = None
        errors = []
        
        for file_path in valid_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    reader = csv.reader(f)
                    header = None
                    
                    for line_num, row in enumerate(reader, 1):
                        if not row or all(not cell.strip() for cell in row):
                            continue
                        
                        if header is None and any('Instance' in cell for cell in row):
                            header = [cell.strip() for cell in row]
                            continue
                        
                        if header is None or len(row) < 7:
                            continue
                        
                        instance = row[5].strip().lower()
                        product = row[2].strip()
                        
                        # 查找 PHY IPTAG
                        if phy_iptag is None and 'phy' in instance:
                            phy_iptag = product
                        
                        # 查找 Block IPTAG
                        if block_iptag is None and 'block' in instance:
                            block_iptag = product
                    
                    if header is None:
                        errors.append(f"CSV header not found in {file_path}")
            
            except Exception as e:
                errors.append(f"Error parsing {file_path}: {str(e)}")
        
        # 判断是否都存在以及是否相等
        both_exist = (phy_iptag is not None and block_iptag is not None)
        iptags_match = (phy_iptag == block_iptag) if both_exist else False
        
        return {
            'phy_iptag': phy_iptag,
            'block_iptag': block_iptag,
            'both_exist': both_exist,
            'iptags_match': iptags_match,
            'errors': errors
        }
    
    # =========================================================================
    # Type 1: Boolean Check
    # =========================================================================
    
    def _execute_type1(self) -> CheckResult:
        """
        Type 1: Boolean Check.
        
        Logic per hints.txt:
        - If IMP-16-0-0-04 == yes (both IPTAGs exist):
          * If PHY IPTAG == Block IPTAG → PASS
          * If PHY IPTAG != Block IPTAG → FAIL
        - If IMP-16-0-0-04 == no (at least one missing) → PASS (N/A)
        
        Returns:
            CheckResult with is_pass based on check logic
        """
        data = self._parse_input_files()
        both_exist = data.get('both_exist', False)
        iptags_match = data.get('iptags_match', False)
        phy_iptag = data.get('phy_iptag')
        block_iptag = data.get('block_iptag')
        errors = data.get('errors', [])
        
        # 处理解析错误
        if errors:
            error_msg = '; '.join(errors)
            missing_items = {
                'parsing_error': {
                    'name': f'Parsing error: {error_msg}',
                    'line_number': 0,
                    'file_path': 'N/A'
                }
            }
            return self.build_complete_output(
                found_items={},
                missing_items=missing_items,
                found_desc=self.FOUND_DESC_TYPE1_4,
                missing_desc=self.MISSING_DESC_TYPE1_4,
                found_reason=self.FOUND_REASON_TYPE1_4,
                missing_reason=self.MISSING_REASON_TYPE1_4
            )
        
        found_items = {}
        missing_items = {}
        
        # 情况 1: 两个 IPTAG 都不存在 → N/A，跳过检查
        if not both_exist:
            phy_status = phy_iptag if phy_iptag else 'NOT FOUND'
            block_status = block_iptag if block_iptag else 'NOT FOUND'
            item_key = f'Check N/A - PHY: {phy_status[:20]}..., Block: {block_status[:20]}...'
            found_items[item_key] = {
                'name': f'Check N/A: IMP-16-0-0-04 prerequisite not met - PHY IPTAG: {phy_status}, Block IPTAG: {block_status}',
                'line_number': 0,
                'file_path': 'N/A'
            }
            return self.build_complete_output(
                found_items=found_items,
                missing_items=missing_items,
                found_desc=self.FOUND_DESC_TYPE1_4,
                missing_desc=self.MISSING_DESC_TYPE1_4,
                found_reason=self.FOUND_REASON_TYPE1_4,
                missing_reason=self.MISSING_REASON_TYPE1_4
            )
        
        # 情况 2: 两个 IPTAG 都存在，比较是否相等
        if iptags_match:
            # PASS: IPTAGs 相等
            found_items['iptag_match'] = {
                'name': f'PHY IPTAG equals Block IPTAG: {phy_iptag}',
                'line_number': 0,
                'file_path': 'N/A'
            }
        else:
            # FAIL: IPTAGs 不相等
            missing_items['phy_iptag'] = {
                'name': f'PHY IPTAG: {phy_iptag}',
                'line_number': 0,
                'file_path': 'N/A'
            }
            missing_items['block_iptag'] = {
                'name': f'Block IPTAG: {block_iptag}',
                'line_number': 0,
                'file_path': 'N/A'
            }
        
        return self.build_complete_output(
            found_items=found_items,
            missing_items=missing_items,
            found_desc=self.FOUND_DESC_TYPE1_4,
            missing_desc=self.MISSING_DESC_TYPE1_4,
            found_reason=self.FOUND_REASON_TYPE1_4,
            missing_reason=self.MISSING_REASON_TYPE1_4
        )
    
    # =========================================================================
    # Type 2: Value Check
    # =========================================================================
    
    def _execute_type2(self) -> CheckResult:
        """
        Type 2: Value Check.
        
        Search pattern_items in input files (status_check mode).
        found_items = patterns matched AND status correct (instance == instance_tag).
        missing_items = patterns matched BUT status wrong (instance != instance_tag).
        
        Returns:
            CheckResult with is_pass based on value comparison
        """
        # Parse input
        data = self._parse_input_files()
        all_items = {item['name']: item for item in data.get('items', [])}
        
        # Get requirements
        pattern_items = self.item_data.get('requirements', {}).get('pattern_items', [])
        
        # status_check mode: Check status of items matching pattern_items
        found_items = {}      # Matched AND status correct (instance == instance_tag)
        missing_items = {}    # Matched BUT status wrong (instance != instance_tag)
        missing_patterns = []  # Pattern not matched at all
        
        for pattern in pattern_items:
            matched = False
            for item_name, item_data in all_items.items():
                # Pattern matching (case-insensitive substring match)
                if pattern.lower() in item_name.lower() or pattern.lower() in item_data.get('product', '').lower():
                    matched = True
                    
                    if item_data['iptag_match']:
                        # Status correct: instance == instance_tag
                        found_items[item_name] = {
                            'name': item_name,
                            'line_number': item_data.get('line_number', 0),
                            'file_path': item_data.get('file_path', 'N/A'),
                            'product': item_data.get('product', ''),
                            'version': item_data.get('version', '')
                        }
                    else:
                        # Status wrong: instance != instance_tag
                        missing_items[item_name] = {
                            'name': item_name,
                            'line_number': item_data.get('line_number', 0),
                            'file_path': item_data.get('file_path', 'N/A'),
                            'instance_tag': item_data.get('instance_tag', '')
                        }
                    break
            
            if not matched:
                missing_patterns.append(pattern)
        
        # Add missing patterns to missing_items dict
        for pattern in missing_patterns:
            missing_items[pattern] = {'name': pattern}
        
        # Use template helper - Type 2: Use TYPE2_3 reason (emphasize "matched/satisfied")
        return self.build_complete_output(
            found_items=found_items,
            missing_items=missing_items,
            found_desc=self.FOUND_DESC_TYPE2_3,
            missing_desc=self.MISSING_DESC_TYPE2_3,
            found_reason=self.FOUND_REASON_TYPE2_3,
            missing_reason=self.MISSING_REASON_TYPE2_3
        )
    
    # =========================================================================
    # Type 3: Value Check with Waiver Logic
    # =========================================================================
    
    def _execute_type3(self) -> CheckResult:
        """
        Type 3: Value check with waiver support.
        
        Same pattern search logic as Type 2 (status_check mode), plus waiver classification.
        
        Returns:
            CheckResult with FAIL for unwaived, INFO for waived items
        """
        # Parse input
        parsed_data = self._parse_input_files()
        all_items = {item['name']: item for item in parsed_data.get('items', [])}
        
        # Parse waiver configuration using template helper
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # Get requirements
        pattern_items = self.item_data.get('requirements', {}).get('pattern_items', [])
        
        # status_check mode: Check status of items matching pattern_items
        found_items = {}      # Matched AND status correct (instance == instance_tag)
        waived_items = {}     # Matched BUT status wrong AND waived
        unwaived_items = {}   # Matched BUT status wrong AND NOT waived
        missing_patterns = []  # Pattern not matched at all
        
        for pattern in pattern_items:
            matched = False
            for item_name, item_data in all_items.items():
                # Pattern matching (case-insensitive substring match)
                if pattern.lower() in item_name.lower() or pattern.lower() in item_data.get('product', '').lower():
                    matched = True
                    
                    if item_data['iptag_match']:
                        # Status correct: instance == instance_tag
                        found_items[item_name] = {
                            'name': item_name,
                            'line_number': item_data.get('line_number', 0),
                            'file_path': item_data.get('file_path', 'N/A'),
                            'product': item_data.get('product', ''),
                            'version': item_data.get('version', '')
                        }
                    else:
                        # Status wrong: instance != instance_tag
                        # Check if waived
                        if self.match_waiver_entry(item_name, waive_dict):
                            waived_items[item_name] = {
                                'name': item_name,
                                'line_number': item_data.get('line_number', 0),
                                'file_path': item_data.get('file_path', 'N/A'),
                                'instance_tag': item_data.get('instance_tag', '')
                            }
                        else:
                            unwaived_items[item_name] = {
                                'name': item_name,
                                'line_number': item_data.get('line_number', 0),
                                'file_path': item_data.get('file_path', 'N/A'),
                                'instance_tag': item_data.get('instance_tag', '')
                            }
                    break
            
            if not matched:
                missing_patterns.append(pattern)
        
        # Add missing patterns to unwaived_items dict
        for pattern in missing_patterns:
            unwaived_items[pattern] = {'name': pattern}
        
        # Find unused waivers
        used_names = set(waived_items.keys())
        unused_waivers = [name for name in waive_dict.keys() if name not in used_names]
        
        # Use template helper - Type 3: Use TYPE2_3 reason + waiver params
        return self.build_complete_output(
            found_items=found_items,
            waived_items=waived_items,
            missing_items=unwaived_items,
            unused_waivers=unused_waivers,
            waive_dict=waive_dict,
            found_desc=self.FOUND_DESC_TYPE2_3,
            missing_desc=self.MISSING_DESC_TYPE2_3,
            waived_desc=self.WAIVED_DESC,
            found_reason=self.FOUND_REASON_TYPE2_3,
            missing_reason=self.MISSING_REASON_TYPE2_3,
            waived_base_reason=self.WAIVED_BASE_REASON
        )
    
    # =========================================================================
    # Type 4: Boolean Check with Waiver Logic
    # =========================================================================
    
    def _execute_type4(self) -> CheckResult:
        """
        Type 4: Boolean check with waiver support (Type 1 + waiver).
        
        Same boolean check as Type 1 (no pattern_items), plus waiver classification.
        
        Returns:
            CheckResult with waiver logic applied
        """
        # Parse input
        data = self._parse_input_files()
        items = data.get('items', [])
        
        # Parse waiver configuration
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # Separate items by IPTAG match status and waiver
        found_items = {}  # IPTAG properly removed (instance == instance_tag)
        waived_items = {}  # IPTAG mismatch BUT waived
        unwaived_items = {}  # IPTAG mismatch AND NOT waived
        
        for item in items:
            if item['iptag_match']:
                # PASS: IPTAG properly removed
                found_items[item['name']] = {
                    'name': item['name'],
                    'line_number': item.get('line_number', 0),
                    'file_path': item.get('file_path', 'N/A'),
                    'product': item.get('product', ''),
                    'version': item.get('version', '')
                }
            else:
                # FAIL: IPTAG mismatch - check if waived
                if self.match_waiver_entry(item['name'], waive_dict):
                    waived_items[item['name']] = {
                        'name': item['name'],
                        'line_number': item.get('line_number', 0),
                        'file_path': item.get('file_path', 'N/A'),
                        'instance_tag': item.get('instance_tag', '')
                    }
                else:
                    unwaived_items[item['name']] = {
                        'name': item['name'],
                        'line_number': item.get('line_number', 0),
                        'file_path': item.get('file_path', 'N/A'),
                        'instance_tag': item.get('instance_tag', '')
                    }
        
        # Find unused waivers
        used_names = set(waived_items.keys())
        unused_waivers = [name for name in waive_dict.keys() if name not in used_names]
        
        # Use template helper - Type 4: Use TYPE1_4 reason + waiver params
        return self.build_complete_output(
            found_items=found_items,
            waived_items=waived_items,
            missing_items=unwaived_items,
            unused_waivers=unused_waivers,
            waive_dict=waive_dict,
            found_desc=self.FOUND_DESC_TYPE1_4,
            missing_desc=self.MISSING_DESC_TYPE1_4,
            waived_desc=self.WAIVED_DESC,
            found_reason=self.FOUND_REASON_TYPE1_4,
            missing_reason=self.MISSING_REASON_TYPE1_4,
            waived_base_reason=self.WAIVED_BASE_REASON
        )


# =========================================================================
# Entry Point
# =========================================================================

def main():
    """Main entry point."""
    checker = Check_16_0_0_05()
    checker.init_checker(Path(__file__))
    result = checker.execute_check()
    checker.write_output(result)
    return 0 if result.is_pass else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())