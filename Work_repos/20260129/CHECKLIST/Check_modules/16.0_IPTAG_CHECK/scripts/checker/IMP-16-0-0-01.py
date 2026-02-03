################################################################################
# Script Name: IMP-16-0-0-01.py
#
# Purpose:
#   Confirm add TAG information to PHY.(TC/Controller don't need IPTAG)
#
# Logic:
#   - Parse phy_iptag.prod to extract golden IPTAG string by concatenating non-comment tokens
#   - Parse cdn_hs_phy_top.csv to extract check IPTAG from PHY instance lines
#   - Skip comment lines (#), END markers, empty lines, and "}" lines in .prod file
#   - Extract first token from each valid line in .prod file and join to form golden IPTAG
#   - Search for lines containing "phy_name","phy_name" pattern in CSV file
#   - Extract 4th field (index 3) from matched CSV lines as check IPTAG
#   - Compare golden IPTAG with check IPTAG for exact match
#   - Report PASS if IPTAGs match, FAIL if mismatch or parsing errors occur
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
# Refactored: 2025-12-18 (Using checker_templates v1.1.0)
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
from checker_templates.input_file_parser_template import InputFileParserMixin  # Optional but recommended


# MANDATORY: Inherit mixins in correct order (InputFileParserMixin first if used)
class Check_16_0_0_01(InputFileParserMixin, OutputBuilderMixin, WaiverHandlerMixin, BaseChecker):
    """
    IMP-16-0-0-01: Confirm add TAG information to PHY.(TC/Controller don't need IPTAG)
    
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
    FOUND_DESC_TYPE1_4 = "IPTAG verification completed - golden and check IPTAGs match"
    MISSING_DESC_TYPE1_4 = "IPTAG mismatch detected between golden and check IPTAGs"
    FOUND_REASON_TYPE1_4 = "IPTAG matched successfully"
    MISSING_REASON_TYPE1_4 = "IPTAG mismatch or parsing error"
    
    # Type 2/3: Pattern checks
    FOUND_DESC_TYPE2_3 = "IPTAG verification completed - golden and check IPTAGs match"
    MISSING_DESC_TYPE2_3 = "IPTAG mismatch detected between golden and check IPTAGs"
    FOUND_REASON_TYPE2_3 = "IPTAG matched successfully"
    MISSING_REASON_TYPE2_3 = "IPTAG mismatch or parsing error"
    
    # All Types (waiver description)
    WAIVED_DESC = "Waived IPTAG mismatches"
    
    # Waiver parameters (Type 3/4 ONLY)
    WAIVED_BASE_REASON = "IPTAG mismatch waived by configuration"
    
    def __init__(self):
        """Initialize the checker."""
        super().__init__(
            check_module="16.0_IPTAG_CHECK",
            item_id="IMP-16-0-0-01",
            item_desc="Confirm add TAG information to PHY.(TC/Controller don't need IPTAG)"
        )
        # Custom member variables for parsed data
        self._golden_iptag: str = ""
        self._check_iptag: str = ""
        self._prod_file_path: str = ""
        self._csv_file_path: str = ""
        self._prod_line_number: int = 0
        self._csv_line_number: int = 0
    
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
        
        Parses:
        1. phy_iptag.prod - Extract golden IPTAG by concatenating non-comment tokens
        2. cdn_hs_phy_top.csv - Extract check IPTAG from PHY instance lines
        
        Returns:
            Dict with parsed data:
            - 'golden_iptag': Golden IPTAG string from .prod file
            - 'check_iptag': Check IPTAG string from .csv file
            - 'prod_file_path': Path to .prod file
            - 'csv_file_path': Path to .csv file
            - 'prod_line_number': Line number where golden IPTAG was extracted
            - 'csv_line_number': Line number where check IPTAG was extracted
            - 'errors': List of parsing errors
        """
        # 1. Validate input files (raises ConfigurationError if missing)
        valid_files, missing_files = self.validate_input_files()
        if not valid_files or len(valid_files) == 0:
            raise ConfigurationError(
                self.create_missing_files_error(missing_files)
            )
        
        # Initialize parsing results
        golden_iptag = ""
        check_iptag = ""
        prod_file_path = ""
        csv_file_path = ""
        prod_line_number = 0
        csv_line_number = 0
        errors = []
        
        # 2. Parse each input file
        for file_path in valid_files:
            file_name = Path(file_path).name
            
            # Parse phy_iptag.prod file
            if file_name.endswith('.prod'):
                try:
                    golden_iptag, prod_line_number = self._parse_prod_file(file_path)
                    prod_file_path = str(file_path)
                except Exception as e:
                    errors.append(f"Error parsing {file_path}: {str(e)}")
            
            # Parse cdn_hs_phy_top.csv file
            elif file_name.endswith('.csv'):
                try:
                    check_iptag, csv_line_number = self._parse_csv_file(file_path)
                    csv_file_path = str(file_path)
                except Exception as e:
                    errors.append(f"Error parsing {file_path}: {str(e)}")
        
        # 3. Store frequently reused data on self
        self._golden_iptag = golden_iptag
        self._check_iptag = check_iptag
        self._prod_file_path = prod_file_path
        self._csv_file_path = csv_file_path
        self._prod_line_number = prod_line_number
        self._csv_line_number = csv_line_number
        
        return {
            'golden_iptag': golden_iptag,
            'check_iptag': check_iptag,
            'prod_file_path': prod_file_path,
            'csv_file_path': csv_file_path,
            'prod_line_number': prod_line_number,
            'csv_line_number': csv_line_number,
            'errors': errors
        }
    
    def _parse_prod_file(self, file_path: Path) -> Tuple[str, int]:
        """
        Parse phy_iptag.prod file to extract golden IPTAG.
        
        Logic:
        - Skip comment lines (starting with #)
        - Skip END marker lines
        - Skip empty lines
        - Skip lines starting with "}"
        - Extract first non-whitespace token from each valid line
        - Concatenate all tokens to form golden IPTAG
        
        Args:
            file_path: Path to .prod file
            
        Returns:
            Tuple of (golden_iptag_string, last_line_number)
        """
        tokens = []
        last_line_number = 0
        end_marker_found = False
        
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line_num, line in enumerate(f, 1):
                # Stop processing after END marker
                if re.match(r'^\s*END\s*$', line, re.IGNORECASE):
                    end_marker_found = True
                    break
                
                # Skip comment lines
                if re.match(r'^\s*#', line):
                    continue
                
                # Skip empty lines
                if re.match(r'^\s*$', line):
                    continue
                
                # Skip lines starting with "}"
                if re.match(r'^\s*"?}', line):
                    continue
                
                # Extract first token (non-whitespace sequence before //)
                match = re.match(r'^(\S+)\s*(?://.*)?$', line)
                if match:
                    token = match.group(1)
                    tokens.append(token)
                    last_line_number = line_num
        
        golden_iptag = ''.join(tokens)
        return golden_iptag, last_line_number
    
    def _parse_csv_file(self, file_path: Path) -> Tuple[str, int]:
        """
        Parse cdn_hs_phy_top.csv file to extract check IPTAG.
        
        Logic:
        - Skip first line (IP_checker metadata)
        - Use CSV reader to properly parse fields with commas and quotes
        - Search for lines where last two fields are the same (Instance,Instance_tag pattern)
        - Look for PHY top-level instance (e.g., "cdn_hs_phy_top","cdn_hs_phy_top")
        - Extract 3rd field (index 2) as check IPTAG from Product column
        
        Args:
            file_path: Path to .csv file
            
        Returns:
            Tuple of (check_iptag_string, line_number)
        """
        check_iptag = ""
        iptag_line_number = 0
        
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            csv_reader = csv.reader(f)
            for line_num, fields in enumerate(csv_reader, 1):
                # Skip first line (metadata)
                if line_num == 1:
                    continue
                
                # Search for PHY instance line with pattern: last two fields are identical
                # Format: GDS,Vendor,Product,Version,Metric,Instance,Instance_tag
                # Looking for lines where Instance == Instance_tag (PHY top level)
                if len(fields) >= 7:
                    instance = fields[5].strip()
                    instance_tag = fields[6].strip()
                    
                    # Check if this is PHY top level (instance name matches tag)
                    # and contains "phy" or matches known PHY patterns
                    if instance == instance_tag and ('phy' in instance.lower() or 'cdn_hs_phy_top' in instance.lower()):
                        # Extract Product field (index 2) as IPTAG
                        check_iptag = fields[2].strip()
                        iptag_line_number = line_num
                        break
        
        return check_iptag, iptag_line_number
    
    # =========================================================================
    # Type 1: Boolean Check
    # =========================================================================
    
    def _execute_type1(self) -> CheckResult:
        """
        Type 1: Boolean Check.
        
        Compare golden IPTAG from .prod file with check IPTAG from .csv file.
        PASS if they match exactly, FAIL if mismatch or parsing errors.
        
        Returns:
            CheckResult with is_pass based on IPTAG comparison
        """
        # Parse input
        data = self._parse_input_files()
        
        golden_iptag = data.get('golden_iptag', '')
        check_iptag = data.get('check_iptag', '')
        errors = data.get('errors', [])
        
        # Check for parsing errors
        if errors:
            error_msg = '; '.join(errors)
            missing_items = {
                'parsing_error': {
                    'name': 'parsing_error',
                    'line_number': 0,
                    'file_path': 'N/A',
                    'reason': error_msg
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
        
        # Check if IPTAGs were extracted
        if not golden_iptag or not check_iptag:
            missing_name = f"Golden: {'<empty>' if not golden_iptag else golden_iptag} | Check: {'<empty>' if not check_iptag else check_iptag}"
            missing_items = [missing_name]
            return self.build_complete_output(
                found_items={},
                missing_items=missing_items,
                found_desc=self.FOUND_DESC_TYPE1_4,
                missing_desc=self.MISSING_DESC_TYPE1_4,
                found_reason=self.FOUND_REASON_TYPE1_4,
                missing_reason=self.MISSING_REASON_TYPE1_4
            )
        
        # Compare IPTAGs
        if golden_iptag == check_iptag:
            # PASS: IPTAGs match
            found_items = {
                'iptag_match': {
                    'name': f"IPTAG: {golden_iptag}",
                    'line_number': data.get('csv_line_number', 0),
                    'file_path': data.get('csv_file_path', 'N/A')
                }
            }
            return self.build_complete_output(
                found_items=found_items,
                missing_items={},
                found_desc=self.FOUND_DESC_TYPE1_4,
                missing_desc=self.MISSING_DESC_TYPE1_4,
                found_reason=self.FOUND_REASON_TYPE1_4,
                missing_reason=self.MISSING_REASON_TYPE1_4
            )
        else:
            # FAIL: IPTAGs mismatch
            mismatch_name = f"Golden: {golden_iptag} | Check: {check_iptag}"
            missing_items = [mismatch_name]
            return self.build_complete_output(
                found_items={},
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
        
        Compare golden IPTAG with check IPTAG (same logic as Type 1).
        
        Returns:
            CheckResult with is_pass based on IPTAG comparison
        """
        # Parse input
        data = self._parse_input_files()
        
        golden_iptag = data.get('golden_iptag', '')
        check_iptag = data.get('check_iptag', '')
        errors = data.get('errors', [])
        
        # Check for parsing errors
        if errors:
            error_msg = '; '.join(errors)
            missing_items = {
                'parsing_error': {
                    'name': 'parsing_error',
                    'line_number': 0,
                    'file_path': 'N/A',
                    'reason': error_msg
                }
            }
            return self.build_complete_output(
                found_items={},
                missing_items=missing_items,
                found_desc=self.FOUND_DESC_TYPE2_3,
                missing_desc=self.MISSING_DESC_TYPE2_3,
                found_reason=self.FOUND_REASON_TYPE2_3,
                missing_reason=self.MISSING_REASON_TYPE2_3
            )
        
        # Check if IPTAGs were extracted
        if not golden_iptag or not check_iptag:
            missing_name = f"Golden: {'<empty>' if not golden_iptag else golden_iptag} | Check: {'<empty>' if not check_iptag else check_iptag}"
            missing_items = [missing_name]
            return self.build_complete_output(
                found_items={},
                missing_items=missing_items,
                found_desc=self.FOUND_DESC_TYPE2_3,
                missing_desc=self.MISSING_DESC_TYPE2_3,
                found_reason=self.FOUND_REASON_TYPE2_3,
                missing_reason=self.MISSING_REASON_TYPE2_3
            )
        
        # Compare IPTAGs
        if golden_iptag == check_iptag:
            # PASS: IPTAGs match
            found_items = {
                'iptag_match': {
                    'name': f"IPTAG: {golden_iptag}",
                    'line_number': data.get('csv_line_number', 0),
                    'file_path': data.get('csv_file_path', 'N/A')
                }
            }
            return self.build_complete_output(
                found_items=found_items,
                missing_items={},
                found_desc=self.FOUND_DESC_TYPE2_3,
                missing_desc=self.MISSING_DESC_TYPE2_3,
                found_reason=self.FOUND_REASON_TYPE2_3,
                missing_reason=self.MISSING_REASON_TYPE2_3
            )
        else:
            # FAIL: IPTAGs mismatch
            mismatch_name = f"Golden: {golden_iptag} | Check: {check_iptag}"
            missing_items = [mismatch_name]
            return self.build_complete_output(
                found_items={},
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
        
        Same IPTAG comparison logic as Type 2, plus waiver classification.
        
        Returns:
            CheckResult with FAIL for unwaived, INFO for waived items
        """
        # Parse input
        data = self._parse_input_files()
        
        golden_iptag = data.get('golden_iptag', '')
        check_iptag = data.get('check_iptag', '')
        errors = data.get('errors', [])
        
        # Parse waiver configuration - FIXED: Use waivers.get() directly
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # Check for parsing errors
        if errors:
            error_msg = '; '.join(errors)
            # Check if error is waived
            if self.match_waiver_entry('parsing_error', waive_dict):
                waived_items = {
                    'parsing_error': {
                        'name': 'parsing_error',
                        'line_number': 0,
                        'file_path': 'N/A',
                        'reason': error_msg
                    }
                }
                used_names = set(waived_items.keys())
                unused_waivers = [name for name in waive_dict.keys() if name not in used_names]
                
                return self.build_complete_output(
                    found_items={},
                    waived_items=waived_items,
                    missing_items={},
                    waive_dict=waive_dict,
                    unused_waivers=unused_waivers,
                    found_desc=self.FOUND_DESC_TYPE2_3,
                    missing_desc=self.MISSING_DESC_TYPE2_3,
                    waived_desc=self.WAIVED_DESC,
                    found_reason=self.FOUND_REASON_TYPE2_3,
                    missing_reason=self.MISSING_REASON_TYPE2_3,
                    waived_base_reason=self.WAIVED_BASE_REASON
                )
            else:
                missing_items = {
                    'parsing_error': {
                        'name': 'parsing_error',
                        'line_number': 0,
                        'file_path': 'N/A',
                        'reason': error_msg
                    }
                }
                unused_waivers = list(waive_dict.keys())
                
                return self.build_complete_output(
                    found_items={},
                    waived_items={},
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
        
        # Check if IPTAGs were extracted
        if not golden_iptag or not check_iptag:
            # Check if missing IPTAG is waived
            if self.match_waiver_entry('missing_iptag', waive_dict):
                waived_items = {
                    'missing_iptag': {
                        'name': 'missing_iptag',
                        'line_number': 0,
                        'file_path': 'N/A',
                        'reason': f"Golden IPTAG: {'empty' if not golden_iptag else golden_iptag}, Check IPTAG: {'empty' if not check_iptag else check_iptag}"
                    }
                }
                used_names = set(waived_items.keys())
                unused_waivers = [name for name in waive_dict.keys() if name not in used_names]
                
                return self.build_complete_output(
                    found_items={},
                    waived_items=waived_items,
                    missing_items={},
                    waive_dict=waive_dict,
                    unused_waivers=unused_waivers,
                    found_desc=self.FOUND_DESC_TYPE2_3,
                    missing_desc=self.MISSING_DESC_TYPE2_3,
                    waived_desc=self.WAIVED_DESC,
                    found_reason=self.FOUND_REASON_TYPE2_3,
                    missing_reason=self.MISSING_REASON_TYPE2_3,
                    waived_base_reason=self.WAIVED_BASE_REASON
                )
            else:
                missing_items = {
                    'missing_iptag': {
                        'name': 'missing_iptag',
                        'line_number': 0,
                        'file_path': 'N/A',
                        'reason': f"Golden IPTAG: {'empty' if not golden_iptag else golden_iptag}, Check IPTAG: {'empty' if not check_iptag else check_iptag}"
                    }
                }
                unused_waivers = list(waive_dict.keys())
                
                return self.build_complete_output(
                    found_items={},
                    waived_items={},
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
        
        # Compare IPTAGs
        if golden_iptag == check_iptag:
            # PASS: IPTAGs match
            found_items = {
                'iptag_match': {
                    'name': f"IPTAG: {golden_iptag}",
                    'line_number': data.get('csv_line_number', 0),
                    'file_path': data.get('csv_file_path', 'N/A')
                }
            }
            used_names = set(found_items.keys())
            unused_waivers = [name for name in waive_dict.keys() if name not in used_names]
            
            return self.build_complete_output(
                found_items=found_items,
                waived_items={},
                missing_items={},
                waive_dict=waive_dict,
                unused_waivers=unused_waivers,
                found_desc=self.FOUND_DESC_TYPE2_3,
                missing_desc=self.MISSING_DESC_TYPE2_3,
                waived_desc=self.WAIVED_DESC,
                found_reason=self.FOUND_REASON_TYPE2_3,
                missing_reason=self.MISSING_REASON_TYPE2_3,
                waived_base_reason=self.WAIVED_BASE_REASON
            )
        else:
            # FAIL: IPTAGs mismatch - check if waived
            mismatch_name = 'iptag_mismatch'
            if self.match_waiver_entry(mismatch_name, waive_dict):
                waived_items = {
                    mismatch_name: {
                        'name': mismatch_name,
                        'line_number': data.get('csv_line_number', 0),
                        'file_path': data.get('csv_file_path', 'N/A'),
                        'reason': f"Golden: {golden_iptag}, Check: {check_iptag}"
                    }
                }
                used_names = set(waived_items.keys())
                unused_waivers = [name for name in waive_dict.keys() if name not in used_names]
                
                return self.build_complete_output(
                    found_items={},
                    waived_items=waived_items,
                    missing_items={},
                    waive_dict=waive_dict,
                    unused_waivers=unused_waivers,
                    found_desc=self.FOUND_DESC_TYPE2_3,
                    missing_desc=self.MISSING_DESC_TYPE2_3,
                    waived_desc=self.WAIVED_DESC,
                    found_reason=self.FOUND_REASON_TYPE2_3,
                    missing_reason=self.MISSING_REASON_TYPE2_3,
                    waived_base_reason=self.WAIVED_BASE_REASON
                )
            else:
                missing_items = {
                    mismatch_name: {
                        'name': mismatch_name,
                        'line_number': data.get('csv_line_number', 0),
                        'file_path': data.get('csv_file_path', 'N/A'),
                        'reason': f"Golden: {golden_iptag}, Check: {check_iptag}"
                    }
                }
                unused_waivers = list(waive_dict.keys())
                
                return self.build_complete_output(
                    found_items={},
                    waived_items={},
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
        
        Same IPTAG comparison logic as Type 1, plus waiver classification.
        
        Returns:
            CheckResult with waiver logic applied
        """
        # Parse input
        data = self._parse_input_files()
        
        golden_iptag = data.get('golden_iptag', '')
        check_iptag = data.get('check_iptag', '')
        errors = data.get('errors', [])
        
        # Parse waiver configuration - FIXED: Use waivers.get() directly
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # Check for parsing errors
        if errors:
            error_msg = '; '.join(errors)
            # Check if error is waived
            if self.match_waiver_entry('parsing_error', waive_dict):
                waived_items = {
                    'parsing_error': {
                        'name': 'parsing_error',
                        'line_number': 0,
                        'file_path': 'N/A',
                        'reason': error_msg
                    }
                }
                used_names = set(waived_items.keys())
                unused_waivers = [name for name in waive_dict.keys() if name not in used_names]
                
                return self.build_complete_output(
                    found_items={},
                    waived_items=waived_items,
                    missing_items={},
                    waive_dict=waive_dict,
                    unused_waivers=unused_waivers,
                    found_desc=self.FOUND_DESC_TYPE1_4,
                    missing_desc=self.MISSING_DESC_TYPE1_4,
                    waived_desc=self.WAIVED_DESC,
                    found_reason=self.FOUND_REASON_TYPE1_4,
                    missing_reason=self.MISSING_REASON_TYPE1_4,
                    waived_base_reason=self.WAIVED_BASE_REASON
                )
            else:
                missing_items = {
                    'parsing_error': {
                        'name': 'parsing_error',
                        'line_number': 0,
                        'file_path': 'N/A',
                        'reason': error_msg
                    }
                }
                unused_waivers = list(waive_dict.keys())
                
                return self.build_complete_output(
                    found_items={},
                    waived_items={},
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
        
        # Check if IPTAGs were extracted
        if not golden_iptag or not check_iptag:
            # Check if missing IPTAG is waived
            if self.match_waiver_entry('missing_iptag', waive_dict):
                waived_items = {
                    'missing_iptag': {
                        'name': 'missing_iptag',
                        'line_number': 0,
                        'file_path': 'N/A',
                        'reason': f"Golden IPTAG: {'empty' if not golden_iptag else golden_iptag}, Check IPTAG: {'empty' if not check_iptag else check_iptag}"
                    }
                }
                used_names = set(waived_items.keys())
                unused_waivers = [name for name in waive_dict.keys() if name not in used_names]
                
                return self.build_complete_output(
                    found_items={},
                    waived_items=waived_items,
                    missing_items={},
                    waive_dict=waive_dict,
                    unused_waivers=unused_waivers,
                    found_desc=self.FOUND_DESC_TYPE1_4,
                    missing_desc=self.MISSING_DESC_TYPE1_4,
                    waived_desc=self.WAIVED_DESC,
                    found_reason=self.FOUND_REASON_TYPE1_4,
                    missing_reason=self.MISSING_REASON_TYPE1_4,
                    waived_base_reason=self.WAIVED_BASE_REASON
                )
            else:
                missing_items = {
                    'missing_iptag': {
                        'name': 'missing_iptag',
                        'line_number': 0,
                        'file_path': 'N/A',
                        'reason': f"Golden IPTAG: {'empty' if not golden_iptag else golden_iptag}, Check IPTAG: {'empty' if not check_iptag else check_iptag}"
                    }
                }
                unused_waivers = list(waive_dict.keys())
                
                return self.build_complete_output(
                    found_items={},
                    waived_items={},
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
        
        # Compare IPTAGs
        if golden_iptag == check_iptag:
            # PASS: IPTAGs match
            found_items = {
                'iptag_match': {
                    'name': f"IPTAG: {golden_iptag}",
                    'line_number': data.get('csv_line_number', 0),
                    'file_path': data.get('csv_file_path', 'N/A')
                }
            }
            used_names = set(found_items.keys())
            unused_waivers = [name for name in waive_dict.keys() if name not in used_names]
            
            return self.build_complete_output(
                found_items=found_items,
                waived_items={},
                missing_items={},
                waive_dict=waive_dict,
                unused_waivers=unused_waivers,
                found_desc=self.FOUND_DESC_TYPE1_4,
                missing_desc=self.MISSING_DESC_TYPE1_4,
                waived_desc=self.WAIVED_DESC,
                found_reason=self.FOUND_REASON_TYPE1_4,
                missing_reason=self.MISSING_REASON_TYPE1_4,
                waived_base_reason=self.WAIVED_BASE_REASON
            )
        else:
            # FAIL: IPTAGs mismatch - check if waived
            mismatch_name = 'iptag_mismatch'
            if self.match_waiver_entry(mismatch_name, waive_dict):
                waived_items = {
                    mismatch_name: {
                        'name': mismatch_name,
                        'line_number': data.get('csv_line_number', 0),
                        'file_path': data.get('csv_file_path', 'N/A'),
                        'reason': f"Golden: {golden_iptag}, Check: {check_iptag}"
                    }
                }
                used_names = set(waived_items.keys())
                unused_waivers = [name for name in waive_dict.keys() if name not in used_names]
                
                return self.build_complete_output(
                    found_items={},
                    waived_items=waived_items,
                    missing_items={},
                    waive_dict=waive_dict,
                    unused_waivers=unused_waivers,
                    found_desc=self.FOUND_DESC_TYPE1_4,
                    missing_desc=self.MISSING_DESC_TYPE1_4,
                    waived_desc=self.WAIVED_DESC,
                    found_reason=self.FOUND_REASON_TYPE1_4,
                    missing_reason=self.MISSING_REASON_TYPE1_4,
                    waived_base_reason=self.WAIVED_BASE_REASON
                )
            else:
                missing_items = {
                    mismatch_name: {
                        'name': mismatch_name,
                        'line_number': data.get('csv_line_number', 0),
                        'file_path': data.get('csv_file_path', 'N/A'),
                        'reason': f"Golden: {golden_iptag}, Check: {check_iptag}"
                    }
                }
                unused_waivers = list(waive_dict.keys())
                
                return self.build_complete_output(
                    found_items={},
                    waived_items={},
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
    checker = Check_16_0_0_01()
    checker.init_checker(Path(__file__))
    result = checker.execute_check()
    checker.write_output(result)
    return 0 if result.is_pass else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())