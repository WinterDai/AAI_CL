################################################################################
# Script Name: IMP-16-0-0-07.py
#
# Purpose:
#   Confirm the Final GDS have the IPTAG information?
#
# Logic:
#   - Parse input file: cdn_hs_phy_top.csv (IP_CHECKER tool output)
#   - Extract IP_checker tool path/version from metadata line
#   - Validate CSV header structure (GDS,Vendor,Product,Version,Metric,Instance,Instance_tag)
#   - Parse IPTAG data rows to extract vendor, product, version, and instance information
#   - Aggregate statistics: count unique GDS files, vendors, products, and tagged instances
#   - Detect violations: missing IPTAG data, malformed CSV entries, instances without proper tags
#   - Generate summary output with per-GDS statistics and error reporting
#
# Auto Type Detection:
#   Type 1: requirements.value=N/A, pattern_items [] (empty), waivers.value=N/A/0 → Boolean Check
#   Type 2: requirements.value>0, pattern_items [...] (defined), waivers.value=N/A/0 → Value Check
#   Type 3: requirements.value>0, pattern_items [...] (defined), waivers.value>0 → Value Check with Waiver Logic
#   Type 4: requirements.value=N/A, pattern_items [] (empty), waivers.value>0 → Boolean Check with Waiver Logic
#   Note: requirements.value indicates number of patterns for config validation (doesn't affect PASS/FAIL)
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
class Check_16_0_0_07(InputFileParserMixin, OutputBuilderMixin, WaiverHandlerMixin, BaseChecker):
    """
    IMP-16-0-0-07: Confirm the Final GDS have the IPTAG information?
    
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
    # Type 1/4: Boolean checks
    FOUND_DESC_TYPE1_4 = "GDS files with complete IPTAG information"
    MISSING_DESC_TYPE1_4 = "GDS files with missing or incomplete IPTAG information"
    FOUND_REASON_TYPE1_4 = "IPTAG information found and verified"
    MISSING_REASON_TYPE1_4 = "IPTAG information not found or incomplete"
    
    # Type 2/3: Pattern checks
    FOUND_DESC_TYPE2_3 = "Required IP blocks with valid IPTAG entries"
    MISSING_DESC_TYPE2_3 = "Required IP blocks with missing or invalid IPTAG entries"
    FOUND_REASON_TYPE2_3 = "IPTAG entry matched and validated"
    MISSING_REASON_TYPE2_3 = "IPTAG entry missing or validation failed"
    
    # All Types (waiver description)
    WAIVED_DESC = "IP blocks with waived IPTAG validation issues"
    
    # Waiver parameters (Type 3/4 ONLY)
    WAIVED_BASE_REASON = "IPTAG validation issue waived per configuration"
    
    def __init__(self):
        """Initialize the checker."""
        super().__init__(
            check_module="16.0_IPTAG_CHECK",
            item_id="IMP-16-0-0-07",
            item_desc="Confirm the Final GDS have the IPTAG information?"
        )
        # Custom member variables for parsed data
        self._parsed_items: List[Dict[str, Any]] = []
        self._metadata: Dict[str, str] = {}
        self._gds_stats: Dict[str, Dict[str, Any]] = {}
    
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
        Parse input files to extract IPTAG information from CSV.
        
        Returns:
            Dict with parsed data:
            - 'items': List[Dict] - IPTAG entries with metadata
            - 'metadata': Dict - Tool version and file info
            - 'errors': List - Parsing errors
            - 'gds_stats': Dict - Per-GDS statistics
        """
        # 1. Validate input files - IMPORTANT: returns tuple (valid_files_list, missing_files_list)
        valid_files, missing_files = self.validate_input_files()
        
        # Fix LOGIC-001: Explicitly check for empty list
        if missing_files:
            raise ConfigurationError(
                self.create_missing_files_error(missing_files)
            )
        
        if not valid_files or len(valid_files) == 0:
            raise ConfigurationError("No valid input files found")
        
        # 2. Parse CSV files
        all_items = []
        metadata = {}
        errors = []
        gds_stats = {}
        
        # Patterns for parsing
        tool_pattern = re.compile(r'^IP_checker filename\s*:\s*(.+?)\s*$')
        header_pattern = re.compile(r'^GDS\s*,\s*Vendor\s*,\s*Product\s*,\s*Version\s*,\s*Metric\s*,\s*Instance\s*,\s*Instance_tag')
        data_pattern = re.compile(r'^([^,]+\.gds),"([^"]+)","?([^"]+)"?,"?([^"]+)"?,([0-9.]+),([^,]+),"?([^"]+)"?\s*$')
        
        for file_path in valid_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    header_found = False
                    
                    for line_num, line in enumerate(f, 1):
                        line = line.rstrip('\n\r')
                        
                        # Skip empty lines and comments
                        if not line.strip() or line.strip().startswith('#'):
                            continue
                        
                        # Extract tool version
                        tool_match = tool_pattern.match(line)
                        if tool_match:
                            metadata['tool_path'] = tool_match.group(1)
                            continue
                        
                        # Validate header
                        header_match = header_pattern.match(line)
                        if header_match:
                            header_found = True
                            continue
                        
                        # Parse data rows
                        if header_found:
                            data_match = data_pattern.match(line)
                            if data_match:
                                gds_file = data_match.group(1)
                                vendor = data_match.group(2)
                                product = data_match.group(3)
                                version = data_match.group(4)
                                metric = data_match.group(5)
                                instance = data_match.group(6)
                                instance_tag = data_match.group(7)
                                
                                # Create item entry
                                item = {
                                    'name': f"{gds_file}:{vendor}:{product}:{instance}",
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
                                
                                # Update GDS statistics
                                if gds_file not in gds_stats:
                                    gds_stats[gds_file] = {
                                        'vendors': set(),
                                        'products': set(),
                                        'instances': []
                                    }
                                gds_stats[gds_file]['vendors'].add(vendor)
                                gds_stats[gds_file]['products'].add(product)
                                gds_stats[gds_file]['instances'].append(instance)
                            else:
                                # Malformed data row
                                if line.strip():  # Not empty
                                    errors.append({
                                        'name': f"Malformed CSV entry at line {line_num}",
                                        'line_number': line_num,
                                        'file_path': str(file_path),
                                        'line_content': line.strip()
                                    })
                    
                    # Check if header was found
                    if not header_found:
                        errors.append({
                            'name': f"Missing CSV header in {file_path.name}",
                            'line_number': 0,
                            'file_path': str(file_path),
                            'line_content': 'N/A'
                        })
            
            except Exception as e:
                errors.append({
                    'name': f"Error parsing {file_path.name}: {str(e)}",
                    'line_number': 0,
                    'file_path': str(file_path),
                    'line_content': 'N/A'
                })
        
        # 3. Store frequently reused data on self
        self._parsed_items = all_items
        self._metadata = metadata
        self._gds_stats = gds_stats
        
        # 4. Return aggregated dict
        return {
            'items': all_items,
            'metadata': metadata,
            'errors': errors,
            'gds_stats': gds_stats
        }
    
    # =========================================================================
    # Type 1: Boolean Check
    # =========================================================================
    
    def _execute_type1(self) -> CheckResult:
        """
        Type 1: Boolean Check.
        
        Check if IPTAG information exists in the GDS files.
        Does NOT use pattern_items for searching.
        
        Returns:
            CheckResult with is_pass based on check logic
        """
        # Parse input
        data = self._parse_input_files()
        items = data.get('items', [])
        errors = data.get('errors', [])
        gds_stats = data.get('gds_stats', {})
        
        # Convert to dict format with field descriptions
        found_items = {}
        missing_items = {}
        
        if items and not errors:
            # IPTAG information found - create summary entries per GDS file
            for gds_file, stats in gds_stats.items():
                vendor_count = len(stats['vendors'])
                product_count = len(stats['products'])
                instance_count = len(stats['instances'])
                
                # Find first occurrence line number for this GDS
                first_item = next((item for item in items if item['gds_file'] == gds_file), None)
                
                found_items[gds_file] = {
                    'name': gds_file,
                    'line_number': first_item['line_number'] if first_item else 0,
                    'file_path': first_item['file_path'] if first_item else 'N/A',
                    'vendors': vendor_count,
                    'products': product_count,
                    'instances': instance_count
                }
        else:
            # IPTAG information missing or errors found
            if errors:
                for error in errors:
                    missing_items[error['name']] = {
                        'name': error['name'],
                        'line_number': error.get('line_number', 0),
                        'file_path': error.get('file_path', 'N/A')
                    }
            else:
                missing_items['no_iptag_data'] = {
                    'name': 'No IPTAG data found in CSV file',
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
        
        Search pattern_items in input files (existence_check mode).
        found_items = patterns found; missing_items = patterns not found.
        
        Returns:
            CheckResult with is_pass based on value comparison
        """
        # Parse input
        data = self._parse_input_files()
        items = data.get('items', [])
        errors = data.get('errors', [])
        
        # Get requirements
        pattern_items = self.item_data.get('requirements', {}).get('pattern_items', [])
        
        # existence_check mode: Check if pattern_items exist in parsed items
        found_items = {}
        missing_items = {}
        
        for pattern in pattern_items:
            matched = False
            for item in items:
                # Match against vendor, product, or instance name
                if (pattern.lower() in item['vendor'].lower() or
                    pattern.lower() in item['product'].lower() or
                    pattern.lower() in item['instance'].lower()):
                    
                    found_items[item['name']] = {
                        'name': item['name'],
                        'line_number': item.get('line_number', 0),
                        'file_path': item.get('file_path', 'N/A'),
                        'vendor': item['vendor'],
                        'product': item['product'],
                        'instance': item['instance']
                    }
                    matched = True
                    break
            
            if not matched:
                missing_items[pattern] = {
                    'name': pattern,
                    'line_number': 0,
                    'file_path': 'N/A'
                }
        
        # Add parsing errors to missing items
        for error in errors:
            missing_items[error['name']] = {
                'name': error['name'],
                'line_number': error.get('line_number', 0),
                'file_path': error.get('file_path', 'N/A')
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
        
        Same pattern search logic as Type 2, plus waiver classification.
        
        Returns:
            CheckResult with FAIL for unwaived, INFO for waived items
        """
        # Parse input
        parsed_data = self._parse_input_files()
        items = parsed_data.get('items', [])
        errors = parsed_data.get('errors', [])
        
        # Fix API-016: Use waivers.get() directly to preserve dict format
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # Get requirements
        pattern_items = self.item_data.get('requirements', {}).get('pattern_items', [])
        
        # existence_check mode: Check if pattern_items exist in parsed items
        found_items = {}
        violations = []
        
        for pattern in pattern_items:
            matched = False
            for item in items:
                # Match against vendor, product, or instance name
                if (pattern.lower() in item['vendor'].lower() or
                    pattern.lower() in item['product'].lower() or
                    pattern.lower() in item['instance'].lower()):
                    
                    found_items[item['name']] = {
                        'name': item['name'],
                        'line_number': item.get('line_number', 0),
                        'file_path': item.get('file_path', 'N/A'),
                        'vendor': item['vendor'],
                        'product': item['product'],
                        'instance': item['instance']
                    }
                    matched = True
                    break
            
            if not matched:
                violations.append({
                    'name': pattern,
                    'line_number': 0,
                    'file_path': 'N/A',
                    'reason': 'Required IP block not found in IPTAG data'
                })
        
        # Add parsing errors to violations
        for error in errors:
            violations.append({
                'name': error['name'],
                'line_number': error.get('line_number', 0),
                'file_path': error.get('file_path', 'N/A'),
                'reason': 'CSV parsing error'
            })
        
        # Separate waived/unwaived using template helper
        waived_items = {}
        missing_items = {}
        
        for violation in violations:
            if self.match_waiver_entry(violation['name'], waive_dict):
                waived_items[violation['name']] = {
                    'name': violation['name'],
                    'line_number': violation.get('line_number', 0),
                    'file_path': violation.get('file_path', 'N/A'),
                    'reason': violation.get('reason', '')
                }
            else:
                missing_items[violation['name']] = {
                    'name': violation['name'],
                    'line_number': violation.get('line_number', 0),
                    'file_path': violation.get('file_path', 'N/A')
                }
        
        # Find unused waivers
        used_names = set(waived_items.keys())
        used_names.update(found_items.keys())
        unused_waivers = [name for name in waive_dict.keys() if name not in used_names]
        
        # Use template helper - Type 3: Use TYPE2_3 reason + waiver params
        return self.build_complete_output(
            found_items=found_items,
            waived_items=waived_items,
            missing_items=missing_items,
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
        items = data.get('items', [])
        errors = data.get('errors', [])
        gds_stats = data.get('gds_stats', {})
        
        # Fix API-016: Use waivers.get() directly to preserve dict format
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # Check if IPTAG data exists
        found_items = {}
        violations = []
        
        if items and not errors:
            # IPTAG information found - create summary entries per GDS file
            for gds_file, stats in gds_stats.items():
                vendor_count = len(stats['vendors'])
                product_count = len(stats['products'])
                instance_count = len(stats['instances'])
                
                # Find first occurrence line number for this GDS
                first_item = next((item for item in items if item['gds_file'] == gds_file), None)
                
                found_items[gds_file] = {
                    'name': gds_file,
                    'line_number': first_item['line_number'] if first_item else 0,
                    'file_path': first_item['file_path'] if first_item else 'N/A',
                    'vendors': vendor_count,
                    'products': product_count,
                    'instances': instance_count
                }
        else:
            # IPTAG information missing or errors found
            if errors:
                for error in errors:
                    violations.append({
                        'name': error['name'],
                        'line_number': error.get('line_number', 0),
                        'file_path': error.get('file_path', 'N/A'),
                        'reason': 'CSV parsing error'
                    })
            else:
                violations.append({
                    'name': 'No IPTAG data found in CSV file',
                    'line_number': 0,
                    'file_path': 'N/A',
                    'reason': 'Empty or missing IPTAG data'
                })
        
        # Separate waived/unwaived using template helper
        waived_items = {}
        missing_items = {}
        
        for violation in violations:
            if self.match_waiver_entry(violation['name'], waive_dict):
                waived_items[violation['name']] = {
                    'name': violation['name'],
                    'line_number': violation.get('line_number', 0),
                    'file_path': violation.get('file_path', 'N/A'),
                    'reason': violation.get('reason', '')
                }
            else:
                missing_items[violation['name']] = {
                    'name': violation['name'],
                    'line_number': violation.get('line_number', 0),
                    'file_path': violation.get('file_path', 'N/A')
                }
        
        # Find unused waivers
        used_names = set(waived_items.keys())
        used_names.update(found_items.keys())
        unused_waivers = [name for name in waive_dict.keys() if name not in used_names]
        
        # Use template helper - Type 4: Use TYPE1_4 reason + waiver params
        return self.build_complete_output(
            found_items=found_items,
            waived_items=waived_items,
            missing_items=missing_items,
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
    checker = Check_16_0_0_07()
    checker.init_checker(Path(__file__))
    result = checker.execute_check()
    checker.write_output(result)
    return 0 if result.is_pass else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())