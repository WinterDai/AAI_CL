################################################################################
# Script Name: IMP-16-0-0-03.py
#
# Purpose:
#   Confirm use IP Type code for PHY - "P" in the slices IPTAG for FIRM PHY delivery.
#
# Logic:
#   - Parse input files: cdn_hs_phy_top.csv
#   - Skip IP_checker tool header line and validate CSV column headers
#   - Parse each data row using CSV reader to handle quoted fields with commas
#   - Extract GDS file, vendor, product, version, metric, instance, and instance_tag
#   - Identify PHY instances by checking product/instance names for PHY keywords (cdn_hs_phy, DDR, _phy_, PHY)
#   - For each PHY instance, validate presence of IP Type code "P" in instance_tag or product fields
#   - Classify results: PASS for PHY instances with "P" code, FAIL for missing "P" code
#   - Aggregate statistics: total instances, unique vendors/products, PHY instances found
#   - Report violations with GDS file, instance name, vendor, and product for remediation
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
class Check_16_0_0_03(InputFileParserMixin, OutputBuilderMixin, WaiverHandlerMixin, BaseChecker):
    """
    IMP-16-0-0-03: Confirm use IP Type code for PHY - "P" in the slices IPTAG for FIRM PHY delivery.
    
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
    # DESCRIPTION & REASON CONSTANTS - COPY FROM README Output Descriptions!
    # =========================================================================
    # Type 1/4: Boolean checks - COPY EXACT VALUES FROM README!
    FOUND_DESC_TYPE1_4 = "PHY instances with IP Type code 'P' found in IPTAG"
    MISSING_DESC_TYPE1_4 = "PHY instances missing IP Type code 'P' in IPTAG"
    FOUND_REASON_TYPE1_4 = "PHY instance contains IP Type code 'P' in IPTAG"
    MISSING_REASON_TYPE1_4 = "PHY instance missing IP Type code 'P' in IPTAG - required for FIRM PHY delivery"
    
    # Type 2/3: Pattern checks - COPY EXACT VALUES FROM README!
    FOUND_DESC_TYPE2_3 = "PHY instances with IP Type code 'P' verified in IPTAG"
    MISSING_DESC_TYPE2_3 = "PHY instances missing required IP Type code 'P' in IPTAG"
    FOUND_REASON_TYPE2_3 = "IP Type code 'P' present in IPTAG"
    MISSING_REASON_TYPE2_3 = "IP Type code 'P' missing in IPTAG - violates FIRM PHY delivery requirement"
    
    # All Types (waiver description) - COPY EXACT VALUES FROM README!
    WAIVED_DESC = "PHY instances with waived IP Type code 'P' violations"
    
    # Waiver parameters (Type 3/4 ONLY) - COPY EXACT VALUES FROM README!
    WAIVED_BASE_REASON = "IP Type code 'P' violation waived for this PHY instance"
    
    def __init__(self):
        """Initialize the checker."""
        super().__init__(
            check_module="16.0_IPTAG_CHECK",
            item_id="IMP-16-0-0-03",
            item_desc="Confirm use IP Type code for PHY - \"P\" in the slices IPTAG for FIRM PHY delivery."
        )
        # Custom member variables for parsed data
        self._parsed_items: List[Dict[str, Any]] = []
        self._phy_instances: List[Dict[str, Any]] = []
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
        Parse input files to extract relevant data.
        
        Parses CSV reports from IP_checker tool containing GDS IP tag information.
        Identifies PHY instances and validates IP Type code "P" presence.
        
        Returns:
            Dict with parsed data:
            - 'items': List[Dict] - All parsed CSV rows with metadata
            - 'phy_instances': List[Dict] - PHY instances identified
            - 'violations': List[Dict] - PHY instances missing "P" code
            - 'metadata': Dict - Statistics (total instances, vendors, products, PHY count)
            - 'errors': List - Any parsing errors encountered
        """
        # 1. Validate input files - IMPORTANT: returns tuple (valid_files_list, missing_files_list)
        valid_files, missing_files = self.validate_input_files()
        if not valid_files or len(valid_files) == 0:
            raise ConfigurationError("No valid input files found")
        
        # 2. Parse CSV files
        all_items = []
        phy_instances = []
        violations = []
        errors = []
        
        # Statistics tracking
        unique_vendors = set()
        unique_products = set()
        total_instances = 0
        
        # PHY identification patterns
        phy_keywords_pattern = re.compile(r'cdn_hs_phy|DDR.*_T5G|_phy_|PHY', re.IGNORECASE)
        ip_type_p_pattern = re.compile(r'\$P\$|_P_|\[P\]|IPType[=:]P', re.IGNORECASE)
        
        for file_path in valid_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                    
                    # Skip IP_checker header line
                    start_idx = 0
                    for idx, line in enumerate(lines):
                        if line.strip().startswith('IP_checker filename'):
                            start_idx = idx + 1
                            break
                    
                    # Find CSV header line
                    header_found = False
                    csv_start_idx = start_idx
                    for idx in range(start_idx, len(lines)):
                        if re.match(r'^GDS\s*,\s*Vendor\s*,\s*Product', lines[idx]):
                            header_found = True
                            csv_start_idx = idx + 1
                            break
                    
                    if not header_found:
                        errors.append(f"CSV header not found in {file_path}")
                        continue
                    
                    # Parse CSV data rows
                    csv_reader = csv.reader(lines[csv_start_idx:])
                    for line_num_offset, row in enumerate(csv_reader, 1):
                        line_num = csv_start_idx + line_num_offset
                        
                        # Skip empty rows
                        if not row or len(row) < 7:
                            continue
                        
                        # Extract fields: GDS, Vendor, Product, Version, Metric, Instance, Instance_tag
                        try:
                            gds_file = row[0].strip()
                            vendor = row[1].strip().strip('"')
                            product = row[2].strip().strip('"')
                            version = row[3].strip().strip('"')
                            metric = row[4].strip()
                            instance = row[5].strip()
                            instance_tag = row[6].strip().strip('"')
                            
                            # Track statistics
                            total_instances += 1
                            unique_vendors.add(vendor)
                            unique_products.add(product)
                            
                            # Create item dict with metadata
                            item = {
                                'name': instance,
                                'gds_file': gds_file,
                                'vendor': vendor,
                                'product': product,
                                'version': version,
                                'metric': metric,
                                'instance': instance,
                                'instance_tag': instance_tag,
                                'line_number': line_num,
                                'file_path': str(file_path)
                            }
                            all_items.append(item)
                            
                            # Check if this is a PHY instance
                            is_phy = (phy_keywords_pattern.search(product) or 
                                     phy_keywords_pattern.search(instance) or
                                     phy_keywords_pattern.search(gds_file))
                            
                            if is_phy:
                                phy_instances.append(item)
                                
                                # Check for IP Type code "P"
                                has_p_code = (ip_type_p_pattern.search(instance_tag) or 
                                            ip_type_p_pattern.search(product))
                                
                                if not has_p_code:
                                    violations.append(item)
                        
                        except (IndexError, ValueError) as e:
                            errors.append(f"Error parsing line {line_num} in {file_path}: {e}")
                            continue
            
            except Exception as e:
                errors.append(f"Error reading file {file_path}: {e}")
                continue
        
        # 3. Store frequently reused data on self
        self._parsed_items = all_items
        self._phy_instances = phy_instances
        self._metadata = {
            'total_instances': total_instances,
            'unique_vendors': len(unique_vendors),
            'unique_products': len(unique_products),
            'phy_count': len(phy_instances),
            'violation_count': len(violations)
        }
        
        # 4. Return aggregated dict
        return {
            'items': all_items,
            'phy_instances': phy_instances,
            'violations': violations,
            'metadata': self._metadata,
            'errors': errors
        }
    
    # =========================================================================
    # Type 1: Boolean Check
    # =========================================================================
    
    def _execute_type1(self) -> CheckResult:
        """
        Type 1: Boolean Check.
        
        Check if PHY instances exist and have IP Type code "P".
        Does NOT use pattern_items for searching.
        
        Returns:
            CheckResult with is_pass based on check logic
        """
        # Parse input
        data = self._parse_input_files()
        phy_instances = data.get('phy_instances', [])
        violations = data.get('violations', [])
        
        # Convert violations to dict with metadata for source file/line display
        found_items = {}
        for phy in phy_instances:
            if phy not in violations:
                item_name = f"{phy['instance']} (GDS: {phy['gds_file']}, Vendor: {phy['vendor']}, Product: {phy['product']})"
                found_items[item_name] = {
                    'name': item_name,
                    'line_number': phy.get('line_number', 0),
                    'file_path': phy.get('file_path', 'N/A')
                }
        
        missing_items = {}
        for violation in violations:
            item_name = f"{violation['instance']} (GDS: {violation['gds_file']}, Vendor: {violation['vendor']}, Product: {violation['product']})"
            missing_items[item_name] = {
                'name': item_name,
                'line_number': violation.get('line_number', 0),
                'file_path': violation.get('file_path', 'N/A')
            }
        
        # Use template helper
        # Type 1: Use TYPE1_4 reason (emphasize "found/not found") - API-025
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
        found_items = patterns matched AND status correct (has "P" code).
        missing_items = patterns matched BUT status wrong (missing "P" code).
        
        Returns:
            CheckResult with is_pass based on value comparison
        """
        # Parse input
        data = self._parse_input_files()
        all_items = {item['instance']: item for item in data.get('items', [])}
        phy_instances = data.get('phy_instances', [])
        violations = data.get('violations', [])
        
        # Get requirements
        pattern_items = self.item_data.get('requirements', {}).get('pattern_items', [])
        
        # status_check mode: Check status of items matching pattern_items
        found_items = {}      # Matched AND has "P" code
        missing_items = {}    # Matched BUT missing "P" code
        missing_patterns = []  # Pattern not matched at all
        
        for pattern in pattern_items:
            matched = False
            for phy in phy_instances:
                instance_name = phy['instance']
                product_name = phy['product']
                
                # Check if pattern matches instance or product name
                if (pattern.lower() in instance_name.lower() or 
                    pattern.lower() in product_name.lower()):
                    matched = True
                    
                    # Check if this PHY has "P" code (status correct)
                    if phy not in violations:
                        item_name = f"{instance_name} (GDS: {phy['gds_file']}, Vendor: {phy['vendor']}, Product: {product_name})"
                        found_items[item_name] = {
                            'name': item_name,
                            'line_number': phy.get('line_number', 0),
                            'file_path': phy.get('file_path', 'N/A')
                        }
                    else:
                        # Status wrong - missing "P" code
                        item_name = f"{instance_name} (GDS: {phy['gds_file']}, Vendor: {phy['vendor']}, Product: {product_name})"
                        missing_items[item_name] = {
                            'name': item_name,
                            'line_number': phy.get('line_number', 0),
                            'file_path': phy.get('file_path', 'N/A')
                        }
                    break
            
            if not matched:
                missing_patterns.append(pattern)
        
        # Convert missing_items dict to list for build_complete_output
        missing_list = list(missing_items.keys()) if missing_items else missing_patterns
        
        # Use template helper (auto-handles waiver=0)
        return self.build_complete_output(
            found_items=found_items,
            missing_items=missing_list,
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
        phy_instances = parsed_data.get('phy_instances', [])
        violations = parsed_data.get('violations', [])
        pattern_items = self.item_data.get('requirements', {}).get('pattern_items', [])
        
        # Parse waiver configuration using template helper
        # CORRECT! Use waivers.get() directly to preserve dict format
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # status_check mode: Check status of items matching pattern_items
        found_items = {}      # Matched AND has "P" code (not waived)
        waived_items = {}     # Matched BUT missing "P" code AND waived
        unwaived_items = {}   # Matched BUT missing "P" code AND not waived
        
        for pattern in pattern_items:
            for phy in phy_instances:
                instance_name = phy['instance']
                product_name = phy['product']
                
                # Check if pattern matches instance or product name
                if (pattern.lower() in instance_name.lower() or 
                    pattern.lower() in product_name.lower()):
                    
                    item_name = f"{instance_name} (GDS: {phy['gds_file']}, Vendor: {phy['vendor']}, Product: {product_name})"
                    
                    # Check if this PHY has "P" code (status correct)
                    if phy not in violations:
                        found_items[item_name] = {
                            'name': item_name,
                            'line_number': phy.get('line_number', 0),
                            'file_path': phy.get('file_path', 'N/A')
                        }
                    else:
                        # Status wrong - missing "P" code, check waiver
                        if self.match_waiver_entry(instance_name, waive_dict):
                            waived_items[item_name] = {
                                'name': item_name,
                                'line_number': phy.get('line_number', 0),
                                'file_path': phy.get('file_path', 'N/A')
                            }
                        else:
                            unwaived_items[item_name] = {
                                'name': item_name,
                                'line_number': phy.get('line_number', 0),
                                'file_path': phy.get('file_path', 'N/A')
                            }
        
        # Find unused waivers
        used_names = set(waived_items.keys())
        unused_waivers = [name for name in waive_dict.keys() if name not in used_names]
        
        # Convert unwaived_items dict to list for build_complete_output
        missing_list = list(unwaived_items.keys())
        
        # Use template helper for automatic output formatting
        return self.build_complete_output(
            found_items=found_items,
            waived_items=waived_items,
            missing_items=missing_list,
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
        
        Same boolean check as Type 1 (no pattern_items), plus waiver classification.
        
        Returns:
            CheckResult with waiver logic applied
        """
        # Parse input
        data = self._parse_input_files()
        phy_instances = data.get('phy_instances', [])
        violations = data.get('violations', [])
        
        # Parse waiver configuration
        # CORRECT! Use waivers.get() directly to preserve dict format
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # Separate waived/unwaived violations
        found_items = {}
        waived_items = {}
        unwaived_items = {}
        
        for phy in phy_instances:
            instance_name = phy['instance']
            item_name = f"{instance_name} (GDS: {phy['gds_file']}, Vendor: {phy['vendor']}, Product: {phy['product']})"
            
            if phy not in violations:
                # Has "P" code - found
                found_items[item_name] = {
                    'name': item_name,
                    'line_number': phy.get('line_number', 0),
                    'file_path': phy.get('file_path', 'N/A')
                }
            else:
                # Missing "P" code - check waiver
                if self.match_waiver_entry(instance_name, waive_dict):
                    waived_items[item_name] = {
                        'name': item_name,
                        'line_number': phy.get('line_number', 0),
                        'file_path': phy.get('file_path', 'N/A')
                    }
                else:
                    unwaived_items[item_name] = {
                        'name': item_name,
                        'line_number': phy.get('line_number', 0),
                        'file_path': phy.get('file_path', 'N/A')
                    }
        
        # Find unused waivers
        used_names = set(waived_items.keys())
        unused_waivers = [name for name in waive_dict.keys() if name not in used_names]
        
        # Convert unwaived_items dict to list for build_complete_output
        missing_list = list(unwaived_items.keys())
        
        # Use template helper (auto-handles waiver=0)
        return self.build_complete_output(
            found_items=found_items,
            waived_items=waived_items,
            missing_items=missing_list,
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
    checker = Check_16_0_0_03()
    checker.init_checker(Path(__file__))
    result = checker.execute_check()
    checker.write_output(result)
    return 0 if result.is_pass else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())