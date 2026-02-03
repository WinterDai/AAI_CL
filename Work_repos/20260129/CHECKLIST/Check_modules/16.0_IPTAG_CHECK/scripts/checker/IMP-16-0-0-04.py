################################################################################
# Script Name: IMP-16-0-0-04.py
#
# Purpose:
#   Confirm update the IPTAG if FIRM PHY slices are reused as FIRM PHY delivery for another project.
#
# Logic:
#   - Parse input file: cdn_hs_phy_top.csv (IP_checker CSV report)
#   - Validate CSV structure and extract GDS instance records
#   - Identify block-level IPTAG: Search for cdn_hs_phy_top instance with Cadence vendor
#   - Identify PHY-level IPTAG: Extract Product field containing FIRM PHY configuration
#   - Verify both IPTAGs exist: Instance_tag populated and Product contains HPCFSC string
#   - Return PASS if both IPTAGs found, FAIL if either missing
#
# Auto Type Detection:
#   Type 1: requirements.value=N/A, pattern_items [] (empty), waivers.value=N/A/0 → Boolean Check
#   Type 2: requirements.value>0, pattern_items [...] (defined), waivers.value=N/A/0 → Value Check
#   Type 3: requirements.value>0, pattern_items [...] (defined), waivers.value>0 → Value Check with Waiver Logic
#   Type 4: requirements.value=N/A, pattern_items [] (empty), waivers.value>0 → Boolean Check with Waiver Logic
#   Note: requirements.value indicates number of patterns for config validation (doesn't affect PASS/FAIL)
#
# Output Behavior (Type 2/3 - Check README "Output Behavior" section!):
#   existence_check: pattern_items = items that SHOULD EXIST in input files
#     - found_items = patterns found in file
#     - missing_items = patterns NOT found in file
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
class Check_16_0_0_04(InputFileParserMixin, OutputBuilderMixin, WaiverHandlerMixin, BaseChecker):
    """
    IMP-16-0-0-04: Confirm update the IPTAG if FIRM PHY slices are reused as FIRM PHY delivery for another project.
    
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
    # Type 1/4: Boolean checks - COPY EXACT VALUES FROM README!
    FOUND_DESC_TYPE1_4 = "IPTAG verification completed - both block-level and PHY-level IPTAGs found"
    MISSING_DESC_TYPE1_4 = "IPTAG verification failed - missing required IPTAGs"
    FOUND_REASON_TYPE1_4 = "Both block IPTAG (cdn_hs_phy_top instance) and PHY IPTAG (FIRM PHY product) found in IP_checker report"
    MISSING_REASON_TYPE1_4 = "Required IPTAG not found in IP_checker report - verify IPTAG update for FIRM PHY reuse"
    
    # Type 2/3: Pattern checks - COPY EXACT VALUES FROM README!
    FOUND_DESC_TYPE2_3 = "Required IPTAGs found in IP_checker report"
    MISSING_DESC_TYPE2_3 = "Required IPTAGs missing from IP_checker report"
    FOUND_REASON_TYPE2_3 = "IPTAG pattern matched in cdn_hs_phy_top.csv"
    MISSING_REASON_TYPE2_3 = "IPTAG pattern not found - verify IPTAG configuration for FIRM PHY reuse"
    
    # All Types (waiver description) - COPY EXACT VALUES FROM README!
    WAIVED_DESC = "IPTAGs waived per project requirements"
    
    # Waiver parameters (Type 3/4 ONLY) - COPY EXACT VALUES FROM README!
    WAIVED_BASE_REASON = "IPTAG requirement waived for this project configuration"
    
    def __init__(self):
        """Initialize the checker."""
        super().__init__(
            check_module="16.0_IPTAG_CHECK",
            item_id="IMP-16-0-0-04",
            item_desc="Confirm update the IPTAG if FIRM PHY slices are reused as FIRM PHY delivery for another project."
        )
        # Custom member variables for parsed data
        self._parsed_items: List[Dict[str, Any]] = []
        self._block_iptag: Optional[Dict[str, Any]] = None
        self._phy_iptag: Optional[Dict[str, Any]] = None
    
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
        Parse input files to extract IPTAG information from IP_checker CSV report.
        
        Parses cdn_hs_phy_top.csv to identify:
        1. Block-level IPTAG: cdn_hs_phy_top instance with Instance_tag field
        2. PHY-level IPTAG: Product field containing FIRM PHY configuration (HPCFSC_*)
        
        Returns:
            Dict with parsed data:
            - 'items': List[Dict] - All IPTAG records found
            - 'block_iptag': Dict - Block-level IPTAG record (cdn_hs_phy_top)
            - 'phy_iptag': Dict - PHY-level IPTAG record (FIRM PHY product)
            - 'metadata': Dict - File metadata
            - 'errors': List - Parsing errors
        """
        # 1. Validate input files - IMPORTANT: returns tuple (valid_files_list, missing_files_list)
        valid_files, missing_files = self.validate_input_files()
        if missing_files:
            raise ConfigurationError(
                self.create_missing_files_error(missing_files)
            )
        
        # 2. Parse CSV files to extract IPTAG records
        all_items = []
        block_iptag = None
        phy_iptag = None
        errors = []
        
        # Pattern for block-level IPTAG (cdn_hs_phy_top instance)
        pattern_block = re.compile(
            r'^[^,]+,"Cadence Design Systems, Inc\.",[^,]+,"R\d+",[^,]+,cdn_hs_phy_top,"([^"]+)"'
        )
        
        # Pattern for PHY-level IPTAG (FIRM PHY product with HPCFSC configuration)
        pattern_phy = re.compile(
            r'^[^,]+,"Cadence Design Systems, Inc\.",(HPCFSC_[^,]+),"(R\d+)",[^,]+,cdn_hs_phy_top,"([^"]+)"'
        )
        
        for file_path in valid_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    # Skip comment lines and find CSV header
                    lines = f.readlines()
                    csv_start = 0
                    for i, line in enumerate(lines):
                        if line.strip().startswith('GDS') and 'Vendor' in line:
                            csv_start = i
                            break
                    
                    # Parse CSV data
                    csv_reader = csv.DictReader(lines[csv_start:])
                    for line_num, row in enumerate(csv_reader, start=csv_start + 2):
                        # Clean field names (remove whitespace)
                        row = {k.strip(): v.strip().strip('"') for k, v in row.items()}
                        
                        # Check if this is cdn_hs_phy_top instance
                        if row.get('Instance', '') == 'cdn_hs_phy_top':
                            vendor = row.get('Vendor', '')
                            product = row.get('Product', '')
                            instance_tag = row.get('Instance_tag', '')
                            
                            # Verify it's Cadence vendor
                            if 'Cadence' in vendor:
                                # Store block-level IPTAG
                                if not block_iptag:
                                    block_iptag = {
                                        'name': f"Block IPTAG: {instance_tag}",
                                        'instance_tag': instance_tag,
                                        'line_number': line_num,
                                        'file_path': str(file_path)
                                    }
                                    all_items.append(block_iptag)
                                
                                # Check if product contains FIRM PHY configuration
                                if product.startswith('HPCFSC_'):
                                    if not phy_iptag:
                                        phy_iptag = {
                                            'name': f"PHY IPTAG: {product}",
                                            'product': product,
                                            'version': row.get('Version', ''),
                                            'line_number': line_num,
                                            'file_path': str(file_path)
                                        }
                                        all_items.append(phy_iptag)
            
            except Exception as e:
                errors.append(f"Error parsing {file_path}: {str(e)}")
        
        # 3. Store frequently reused data on self
        self._parsed_items = all_items
        self._block_iptag = block_iptag
        self._phy_iptag = phy_iptag
        
        return {
            'items': all_items,
            'block_iptag': block_iptag,
            'phy_iptag': phy_iptag,
            'metadata': {
                'total_items': len(all_items),
                'has_block_iptag': block_iptag is not None,
                'has_phy_iptag': phy_iptag is not None
            },
            'errors': errors
        }
    
    # =========================================================================
    # Type 1: Boolean Check
    # =========================================================================
    
    def _execute_type1(self) -> CheckResult:
        """
        Type 1: Boolean Check.
        
        Verify that both block-level and PHY-level IPTAGs exist in the IP_checker report.
        This is a boolean check - either both IPTAGs are present (PASS) or not (FAIL).
        
        Returns:
            CheckResult with is_pass based on IPTAG existence
        """
        # Parse input
        data = self._parse_input_files()
        block_iptag = data.get('block_iptag')
        phy_iptag = data.get('phy_iptag')
        
        # Build found_items dict with metadata
        found_items = {}
        missing_items = {}
        
        if block_iptag:
            found_items[block_iptag['name']] = {
                'name': block_iptag['name'],
                'line_number': block_iptag.get('line_number', 0),
                'file_path': block_iptag.get('file_path', 'N/A')
            }
        else:
            missing_name = 'Block IPTAG (cdn_hs_phy_top instance)'
            missing_items[missing_name] = {
                'name': missing_name,
                'line_number': 0,
                'file_path': 'N/A'
            }
        
        if phy_iptag:
            found_items[phy_iptag['name']] = {
                'name': phy_iptag['name'],
                'line_number': phy_iptag.get('line_number', 0),
                'file_path': phy_iptag.get('file_path', 'N/A')
            }
        else:
            missing_name = 'PHY IPTAG (FIRM PHY product configuration)'
            missing_items[missing_name] = {
                'name': missing_name,
                'line_number': 0,
                'file_path': 'N/A'
            }
        
        # Use template helper - Type 1: Use TYPE1_4 reason (emphasize "found/not found")
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
        
        Search pattern_items (required IPTAG types) in input files.
        This is an existence_check: verify that required IPTAG patterns exist.
        
        Returns:
            CheckResult with is_pass based on pattern matching
        """
        # Parse input
        data = self._parse_input_files()
        items = data.get('items', [])
        
        # Get requirements - pattern_items contains IPTAG types to verify
        pattern_items = self.item_data.get('requirements', {}).get('pattern_items', [])
        
        # Build items dict for lookup
        items_dict = {item['name']: item for item in items}
        
        # existence_check mode: Check if pattern_items exist in parsed items
        found_items = {}
        missing_items = {}
        
        for pattern in pattern_items:
            matched = False
            for item_name, item_data in items_dict.items():
                # Match pattern against item name (case-insensitive substring match)
                if pattern.lower() in item_name.lower():
                    found_items[item_name] = {
                        'name': item_name,
                        'line_number': item_data.get('line_number', 0),
                        'file_path': item_data.get('file_path', 'N/A')
                    }
                    matched = True
                    break
            
            if not matched:
                missing_items[pattern] = {
                    'name': pattern,
                    'line_number': 0,
                    'file_path': 'N/A'
                }
        
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
        
        Same pattern search logic as Type 2 (existence_check), plus waiver classification.
        
        Returns:
            CheckResult with FAIL for unwaived, INFO for waived items
        """
        # Parse input
        data = self._parse_input_files()
        items = data.get('items', [])
        
        # Parse waiver configuration using template helper
        # CORRECT! Use waivers.get() directly to preserve dict format
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # Get requirements - pattern_items contains IPTAG types to verify
        pattern_items = self.item_data.get('requirements', {}).get('pattern_items', [])
        
        # Build items dict for lookup
        items_dict = {item['name']: item for item in items}
        
        # existence_check mode: Check if pattern_items exist in parsed items
        found_items = {}
        waived_items = {}
        unwaived_items = {}
        
        for pattern in pattern_items:
            matched = False
            for item_name, item_data in items_dict.items():
                # Match pattern against item name (case-insensitive substring match)
                if pattern.lower() in item_name.lower():
                    found_items[item_name] = {
                        'name': item_name,
                        'line_number': item_data.get('line_number', 0),
                        'file_path': item_data.get('file_path', 'N/A')
                    }
                    matched = True
                    break
            
            if not matched:
                # Pattern not found - check if waived
                if self.match_waiver_entry(pattern, waive_dict):
                    waived_items[pattern] = {
                        'name': pattern,
                        'line_number': 0,
                        'file_path': 'N/A'
                    }
                else:
                    unwaived_items[pattern] = {
                        'name': pattern,
                        'line_number': 0,
                        'file_path': 'N/A'
                    }
        
        # Find unused waivers
        used_names = set(waived_items.keys())
        used_names.update(found_items.keys())
        unused_waivers = [name for name in waive_dict.keys() if name not in used_names]
        
        # Use template helper - Type 3: Use TYPE2_3 reason + waiver params
        return self.build_complete_output(
            found_items=found_items,
            waived_items=waived_items,
            missing_items=unwaived_items,
            waive_dict=waive_dict,
            unused_waivers=unused_waivers,
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
        
        Same boolean check as Type 1 (verify both IPTAGs exist), plus waiver classification.
        
        Returns:
            CheckResult with waiver logic applied
        """
        # Parse input
        data = self._parse_input_files()
        block_iptag = data.get('block_iptag')
        phy_iptag = data.get('phy_iptag')
        
        # Parse waiver configuration
        # CORRECT! Use waivers.get() directly to preserve dict format
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # Build found_items and missing_items
        found_items = {}
        waived_items = {}
        unwaived_items = {}
        
        # Check block IPTAG
        if block_iptag:
            found_items[block_iptag['name']] = {
                'name': block_iptag['name'],
                'line_number': block_iptag.get('line_number', 0),
                'file_path': block_iptag.get('file_path', 'N/A')
            }
        else:
            missing_name = 'Block IPTAG (cdn_hs_phy_top instance)'
            if self.match_waiver_entry(missing_name, waive_dict):
                waived_items[missing_name] = {
                    'name': missing_name,
                    'line_number': 0,
                    'file_path': 'N/A'
                }
            else:
                unwaived_items[missing_name] = {
                    'name': missing_name,
                    'line_number': 0,
                    'file_path': 'N/A'
                }
        
        # Check PHY IPTAG
        if phy_iptag:
            found_items[phy_iptag['name']] = {
                'name': phy_iptag['name'],
                'line_number': phy_iptag.get('line_number', 0),
                'file_path': phy_iptag.get('file_path', 'N/A')
            }
        else:
            missing_name = 'PHY IPTAG (FIRM PHY product configuration)'
            if self.match_waiver_entry(missing_name, waive_dict):
                waived_items[missing_name] = {
                    'name': missing_name,
                    'line_number': 0,
                    'file_path': 'N/A'
                }
            else:
                unwaived_items[missing_name] = {
                    'name': missing_name,
                    'line_number': 0,
                    'file_path': 'N/A'
                }
        
        # Find unused waivers
        used_names = set(waived_items.keys())
        used_names.update(found_items.keys())
        unused_waivers = [name for name in waive_dict.keys() if name not in used_names]
        
        # Use template helper - Type 4: Use TYPE1_4 reason + waiver params
        return self.build_complete_output(
            found_items=found_items,
            waived_items=waived_items,
            missing_items=unwaived_items,
            waive_dict=waive_dict,
            unused_waivers=unused_waivers,
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
    checker = Check_16_0_0_04()
    checker.init_checker(Path(__file__))
    result = checker.execute_check()
    checker.write_output(result)
    return 0 if result.is_pass else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())