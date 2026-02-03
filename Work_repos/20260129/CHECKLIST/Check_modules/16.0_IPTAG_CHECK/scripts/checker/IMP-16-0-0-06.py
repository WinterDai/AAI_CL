################################################################################
# Script Name: IMP-16-0-0-06.py
#
# Purpose:
#   Confirm you followed the below document about IPTAG creation. If you have further question, please check with Tobing. HSPHY/HPPHY/DFPHY/GDDR/HBM: https://cadence.sharepoint.com/:w:/r/sites/IPGroup/DesignIP/Quality/_layouts/15/Doc.aspx?sourcedoc=%7B26DAB946-483A-415F-AC0C-C195C0838506%7D&file=IP%20Number%20Format%20-%20DDR%20PHY.docx&wdLOR=cF5835961-1465-461D-BAFD-3F0590F6A7F9&action=default&mobileredirect=true SERDES: https://cadence.sharepoint.com/:w:/r/sites/IPGroup/DesignIP/Quality/IP_Numbers/IP%20Number%20Format%20-%20SerDes.docx?d=wf015c37bca9b4d3d951589cf616333fe&csf=1&web=1
#
# Logic:
#   - Parse input file: phy_iptag.prod
#   - Extract field definitions line-by-line (field value + comment description)
#   - Parse field descriptions to extract format constraints (fixed width, valid codes)
#   - Validate field values against extracted constraints
#   - Check delimiter sequence (underscore between sections, dollar before config)
#   - Validate special fields: CTIME format (C + YYYYMMDDhhmm)
#   - Verify field order and completeness
#   - Report validation results with specific field-level errors
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
from checker_templates.input_file_parser_template import InputFileParserMixin  # Optional but recommended


# MANDATORY: Inherit mixins in correct order (InputFileParserMixin first if used)
class Check_16_0_0_06(InputFileParserMixin, OutputBuilderMixin, WaiverHandlerMixin, BaseChecker):
    """
    IMP-16-0-0-06: Confirm you followed the below document about IPTAG creation. If you have further question, please check with Tobing. HSPHY/HPPHY/DFPHY/GDDR/HBM: https://cadence.sharepoint.com/:w:/r/sites/IPGroup/DesignIP/Quality/_layouts/15/Doc.aspx?sourcedoc=%7B26DAB946-483A-415F-AC0C-C195C0838506%7D&file=IP%20Number%20Format%20-%20DDR%20PHY.docx&wdLOR=cF5835961-1465-461D-BAFD-3F0590F6A7F9&action=default&mobileredirect=true SERDES: https://cadence.sharepoint.com/:w:/r/sites/IPGroup/DesignIP/Quality/IP_Numbers/IP%20Number%20Format%20-%20SerDes.docx?d=wf015c37bca9b4d3d951589cf616333fe&csf=1&web=1
    
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
    FOUND_DESC_TYPE1_4 = "IPTAG configuration file validated successfully"
    MISSING_DESC_TYPE1_4 = "IPTAG configuration validation failed"
    FOUND_REASON_TYPE1_4 = "IPTAG file found and all fields conform to IP Number Format standards"
    MISSING_REASON_TYPE1_4 = "IPTAG file not found or contains format violations"
    
    # Type 2/3: Pattern checks
    FOUND_DESC_TYPE2_3 = "IPTAG fields validated successfully"
    MISSING_DESC_TYPE2_3 = "IPTAG field validation failed"
    FOUND_REASON_TYPE2_3 = "Field conforms to IP Number Format standards"
    MISSING_REASON_TYPE2_3 = "Field does not conform to IP Number Format standards"
    
    # All Types (waiver description)
    WAIVED_DESC = "IPTAG validation errors waived"
    
    # Waiver parameters (Type 3/4 ONLY)
    WAIVED_BASE_REASON = "IPTAG validation error waived per configuration"
    
    def __init__(self):
        """Initialize the checker."""
        super().__init__(
            check_module="16.0_IPTAG_CHECK",
            item_id="IMP-16-0-0-06",
            item_desc="Confirm you followed the below document about IPTAG creation. If you have further question, please check with Tobing. HSPHY/HPPHY/DFPHY/GDDR/HBM: https://cadence.sharepoint.com/:w:/r/sites/IPGroup/DesignIP/Quality/_layouts/15/Doc.aspx?sourcedoc=%7B26DAB946-483A-415F-AC0C-C195C0838506%7D&file=IP%20Number%20Format%20-%20DDR%20PHY.docx&wdLOR=cF5835961-1465-461D-BAFD-3F0590F6A7F9&action=default&mobileredirect=true SERDES: https://cadence.sharepoint.com/:w:/r/sites/IPGroup/DesignIP/Quality/IP_Numbers/IP%20Number%20Format%20-%20SerDes.docx?d=wf015c37bca9b4d3d951589cf616333fe&csf=1&web=1"
        )
        # Custom member variables for parsed data
        self._parsed_items: List[Dict[str, Any]] = []
        self._field_definitions: Dict[str, Dict[str, Any]] = {}
        self._validation_errors: List[Dict[str, Any]] = []
    
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
        except Exception as e:
            # Handle unexpected errors
            return create_check_result(
                is_pass=False,
                item_id=self.item_id,
                item_desc=self.item_desc,
                details=[
                    DetailItem(
                        name="Unexpected Error",
                        severity=Severity.FAIL,
                        reason=f"Checker execution failed: {str(e)}",
                        line_number=0,
                        file_path="N/A"
                    )
                ]
            )
    
    # =========================================================================
    # Input Parsing (Common for All Types)
    # =========================================================================
    
    def _parse_input_files(self) -> Dict[str, Any]:
        """
        Parse input files to extract IPTAG field definitions and validate format.
        
        Returns:
            Dict with parsed data:
            - 'items': List[Dict] - Validated fields with metadata
            - 'errors': List[Dict] - Validation errors with line numbers
            - 'metadata': Dict - File metadata
        """
        # 1. Validate input files - IMPORTANT: returns tuple (valid_files_list, missing_files_list)
        valid_files, missing_files = self.validate_input_files()
        
        # FIXED: Explicitly check for empty list
        if missing_files:
            raise ConfigurationError(
                self.create_missing_files_error(missing_files)
            )
        
        if not valid_files or len(valid_files) == 0:
            raise ConfigurationError("No valid input files found")
        
        # 2. Parse IPTAG file
        all_items = []
        all_errors = []
        field_definitions = {}
        
        # Patterns for parsing
        field_pattern = re.compile(r'^([A-Z0-9_$]+)\s*//\s*(.+)$')
        fixed_width_pattern = re.compile(r'Fixed width \[(\d+)\]')
        valid_codes_pattern = re.compile(r'Codes?:\s*([A-Z]\s*=\s*[^,]+(?:,\s*[A-Z]\s*=\s*[^,]+)*)')
        delimiter_pattern = re.compile(r'^([_$])\s*//\s*(.+delimiter.+)$')
        variable_width_pattern = re.compile(r'Variable width', re.IGNORECASE)
        ctime_pattern = re.compile(r'^C\d{12}$')
        
        for file_path in valid_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    field_index = 0
                    for line_num, line in enumerate(f, 1):
                        # Skip comment lines
                        if line.strip().startswith('#') or not line.strip():
                            continue
                        
                        # Parse field definition
                        match = field_pattern.match(line)
                        if match:
                            field_value = match.group(1).strip()
                            field_desc = match.group(2).strip()
                            
                            # Extract field constraints
                            fixed_width_match = fixed_width_pattern.search(field_desc)
                            valid_codes_match = valid_codes_pattern.search(field_desc)
                            is_variable_width = variable_width_pattern.search(field_desc) is not None
                            is_delimiter = delimiter_pattern.match(line) is not None
                            
                            # Build field definition
                            field_def = {
                                'index': field_index,
                                'value': field_value,
                                'description': field_desc,
                                'line_number': line_num,
                                'file_path': str(file_path),
                                'is_delimiter': is_delimiter,
                                'is_variable_width': is_variable_width,
                                'fixed_width': int(fixed_width_match.group(1)) if fixed_width_match else None,
                                'valid_codes': valid_codes_match.group(1) if valid_codes_match else None
                            }
                            
                            # Validate field
                            validation_result = self._validate_field(field_def, ctime_pattern)
                            
                            if validation_result['is_valid']:
                                all_items.append({
                                    'name': f"Field {field_index}: {field_value}",
                                    'value': field_value,
                                    'description': field_desc,
                                    'line_number': line_num,
                                    'file_path': str(file_path)
                                })
                            else:
                                all_errors.append({
                                    'name': f"Field {field_index}: {field_value}",
                                    'error': validation_result['error'],
                                    'line_number': line_num,
                                    'file_path': str(file_path)
                                })
                            
                            field_definitions[f"field_{field_index}"] = field_def
                            field_index += 1
            
            except Exception as e:
                all_errors.append({
                    'name': f"File parsing error: {file_path.name}",
                    'error': f"Failed to parse file: {str(e)}",
                    'line_number': 0,
                    'file_path': str(file_path)
                })
        
        # 3. Store frequently reused data on self
        self._parsed_items = all_items
        self._field_definitions = field_definitions
        self._validation_errors = all_errors
        
        # 4. Return aggregated dict
        return {
            'items': all_items,
            'errors': all_errors,
            'metadata': {
                'total_fields': len(all_items),
                'total_errors': len(all_errors)
            }
        }
    
    def _validate_field(self, field_def: Dict[str, Any], ctime_pattern: re.Pattern) -> Dict[str, Any]:
        """
        Validate a single IPTAG field against format constraints.
        
        Args:
            field_def: Field definition with constraints
            ctime_pattern: Regex pattern for CTIME validation
            
        Returns:
            Dict with validation result: {'is_valid': bool, 'error': str}
        """
        field_value = field_def['value']
        
        # Skip validation for delimiters
        if field_def['is_delimiter']:
            if field_value not in ['_', '$']:
                return {
                    'is_valid': False,
                    'error': f"Invalid delimiter - Expected: '_' or '$', Found: '{field_value}'"
                }
            return {'is_valid': True, 'error': ''}
        
        # Check fixed width constraint
        if field_def['fixed_width'] is not None:
            if len(field_value) != field_def['fixed_width']:
                return {
                    'is_valid': False,
                    'error': f"Invalid field width - Expected: {field_def['fixed_width']}, Found: {len(field_value)}"
                }
        
        # Check valid codes constraint
        if field_def['valid_codes']:
            # Extract valid code letters
            valid_code_letters = re.findall(r'([A-Z])\s*=', field_def['valid_codes'])
            if field_value not in valid_code_letters:
                return {
                    'is_valid': False,
                    'error': f"Invalid code - Expected one of: {', '.join(valid_code_letters)}, Found: '{field_value}'"
                }
        
        # Check CTIME format
        if 'CTIME' in field_def['description']:
            if not ctime_pattern.match(field_value):
                return {
                    'is_valid': False,
                    'error': f"Invalid CTIME format - Expected: C + YYYYMMDDhhmm (12 digits), Found: '{field_value}'"
                }
        
        return {'is_valid': True, 'error': ''}
    
    # =========================================================================
    # Type 1: Boolean Check
    # =========================================================================
    
    def _execute_type1(self) -> CheckResult:
        """
        Type 1: Boolean Check.
        
        Check if IPTAG file exists and is valid (no format violations).
        
        Returns:
            CheckResult with is_pass based on validation
        """
        # Parse input
        data = self._parse_input_files()
        items = data.get('items', [])
        errors = data.get('errors', [])
        
        # Convert to dict format with metadata
        found_items = {}
        if not errors:
            # File is valid - include all validated fields
            for item in items:
                found_items[item['name']] = {
                    'name': item['name'],
                    'line_number': item.get('line_number', 0),
                    'file_path': item.get('file_path', 'N/A')
                }
        
        missing_items = {}
        if errors:
            # File has validation errors
            for err in errors:
                missing_items[err['name']] = {
                    'name': err['name'],
                    'line_number': err.get('line_number', 0),
                    'file_path': err.get('file_path', 'N/A'),
                    'reason': err.get('error', '')
                }
        
        # FIXED: Use dict format, not list
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
        
        Search pattern_items in IPTAG fields and validate their format.
        
        Returns:
            CheckResult with is_pass based on value comparison
        """
        # Parse input
        data = self._parse_input_files()
        items = data.get('items', [])
        errors = data.get('errors', [])
        
        # Get requirements
        pattern_items = self.item_data.get('requirements', {}).get('pattern_items', [])
        
        # existence_check mode: Check if pattern_items exist in parsed fields
        found_items = {}
        missing_items = {}
        
        for pattern in pattern_items:
            matched = False
            for item in items:
                # Match pattern against field name or value
                if pattern.lower() in item['name'].lower() or pattern.lower() in item.get('value', '').lower():
                    found_items[item['name']] = {
                        'name': item['name'],
                        'line_number': item.get('line_number', 0),
                        'file_path': item.get('file_path', 'N/A')
                    }
                    matched = True
                    break
            
            if not matched:
                # Check if pattern matches any error
                for err in errors:
                    if pattern.lower() in err['name'].lower():
                        missing_items[err['name']] = {
                            'name': err['name'],
                            'line_number': err.get('line_number', 0),
                            'file_path': err.get('file_path', 'N/A'),
                            'reason': err.get('error', '')
                        }
                        matched = True
                        break
                
                if not matched:
                    missing_items[f"Pattern not found: {pattern}"] = {
                        'name': f"Pattern not found: {pattern}",
                        'line_number': 0,
                        'file_path': 'N/A',
                        'reason': f"Pattern '{pattern}' not found in IPTAG fields"
                    }
        
        # FIXED: Use dict format, not list
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
        
        # FIXED: Use waivers.get() directly to preserve dict format
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # Get requirements
        pattern_items = self.item_data.get('requirements', {}).get('pattern_items', [])
        
        # Find violations (errors from validation)
        violations = {}
        for err in errors:
            violations[err['name']] = {
                'name': err['name'],
                'line_number': err.get('line_number', 0),
                'file_path': err.get('file_path', 'N/A'),
                'reason': err.get('error', '')
            }
        
        # Separate waived/unwaived using template helper
        waived_items = {}
        unwaived_items = {}
        
        for viol_name, viol_data in violations.items():
            if self.match_waiver_entry(viol_name, waive_dict):
                waived_items[viol_name] = viol_data
            else:
                unwaived_items[viol_name] = viol_data
        
        # Find validated items (found_items)
        found_items = {}
        for item in items:
            # Only include items that match pattern_items
            for pattern in pattern_items:
                if pattern.lower() in item['name'].lower() or pattern.lower() in item.get('value', '').lower():
                    found_items[item['name']] = {
                        'name': item['name'],
                        'line_number': item.get('line_number', 0),
                        'file_path': item.get('file_path', 'N/A')
                    }
                    break
        
        # Find unused waivers
        used_names = set(waived_items.keys())
        unused_waivers = [name for name in waive_dict.keys() if name not in used_names]
        
        # FIXED: Use dict format, not list
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
        
        Same boolean check as Type 1 (file exists and valid), plus waiver classification.
        
        Returns:
            CheckResult with waiver logic applied
        """
        # Parse input
        data = self._parse_input_files()
        items = data.get('items', [])
        errors = data.get('errors', [])
        
        # FIXED: Use waivers.get() directly to preserve dict format
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # Find violations (errors from validation)
        violations = {}
        for err in errors:
            violations[err['name']] = {
                'name': err['name'],
                'line_number': err.get('line_number', 0),
                'file_path': err.get('file_path', 'N/A'),
                'reason': err.get('error', '')
            }
        
        # Separate waived/unwaived
        waived_items = {}
        unwaived_items = {}
        
        for viol_name, viol_data in violations.items():
            if self.match_waiver_entry(viol_name, waive_dict):
                waived_items[viol_name] = viol_data
            else:
                unwaived_items[viol_name] = viol_data
        
        # Found items (validated fields)
        found_items = {}
        for item in items:
            found_items[item['name']] = {
                'name': item['name'],
                'line_number': item.get('line_number', 0),
                'file_path': item.get('file_path', 'N/A')
            }
        
        # Find unused waivers
        used_names = set(waived_items.keys())
        unused_waivers = [name for name in waive_dict.keys() if name not in used_names]
        
        # FIXED: Use dict format, not list
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
    checker = Check_16_0_0_06()
    checker.init_checker(Path(__file__))
    result = checker.execute_check()
    checker.write_output(result)
    return 0 if result.is_pass else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())