################################################################################
# Script Name: IMP-16-0-0-00.py
#
# Purpose:
#   Confirm the IPTAG content and format are correct.(check the Note)
#
# Logic:
#   - Parse input files: phy_iptag.prod
#   - Filter out comment lines (starting with # or ###)
#   - Extract field values in sequential order from non-comment lines
#   - Validate field count matches expected specification (13 fields)
#   - Validate each field value against allowed codes and formats
#   - Verify delimiter positions at fields 7, 9, and 12 (_,_,$)
#   - Confirm End marker presence at file termination
#   - Check for trailing content after End marker
#   - Report validation errors with field name, line number, and file path
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
# Refactored: 2025-12-26 (Using checker_templates v1.1.0)
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
class Check_16_0_0_00(InputFileParserMixin, OutputBuilderMixin, WaiverHandlerMixin, BaseChecker):
    """
    IMP-16-0-0-00: Confirm the IPTAG content and format are correct.(check the Note)
    
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
    FOUND_DESC_TYPE1_4 = "IPTAG fields validated successfully"
    MISSING_DESC_TYPE1_4 = "IPTAG field validation failed"
    FOUND_REASON_TYPE1_4 = "Field conforms to specification"
    MISSING_REASON_TYPE1_4 = "Field validation failed"
    
    # Type 2/3: Pattern checks
    FOUND_DESC_TYPE2_3 = "Required IPTAG fields found and validated"
    MISSING_DESC_TYPE2_3 = "Required IPTAG fields missing or invalid"
    FOUND_REASON_TYPE2_3 = "Field found and value matches specification"
    MISSING_REASON_TYPE2_3 = "Field missing or value does not match specification"
    
    # All Types (waiver description)
    WAIVED_DESC = "IPTAG validation errors waived by configuration"
    
    # Waiver parameters (Type 3/4 ONLY)
    WAIVED_BASE_REASON = "Field validation error waived"
    
    # Field specification based on IPTAG format
    FIELD_SPEC = [
        {'pos': 1, 'name': 'PHY_Architecture', 'width': 'fixed', 'allowed': ['H', 'L', 'U', 'P']},
        {'pos': 2, 'name': 'IP_Type', 'width': 'fixed', 'allowed': ['P']},
        {'pos': 3, 'name': 'IO_Type', 'width': 'fixed', 'allowed': ['C']},
        {'pos': 4, 'name': 'Package', 'width': 'fixed', 'allowed': ['F']},
        {'pos': 5, 'name': 'PLL_Vendor', 'width': 'fixed', 'allowed': ['S']},
        {'pos': 6, 'name': 'PHY_Source', 'width': 'fixed', 'allowed': ['C']},
        {'pos': 7, 'name': 'Delimiter1', 'width': 'fixed', 'allowed': ['_']},
        {'pos': 8, 'name': 'Protocol', 'width': 'variable', 'pattern': r'^[DL][2-5]([DL][2-5])?$'},
        {'pos': 9, 'name': 'Delimiter2', 'width': 'fixed', 'allowed': ['_']},
        {'pos': 10, 'name': 'Process', 'width': 'variable', 'pattern': r'^T\d+[A-Z]+$'},
        {'pos': 11, 'name': 'Release_Date', 'width': 'variable', 'pattern': r'^(CTIME|C\d{12})$'},
        {'pos': 12, 'name': 'Delimiter3', 'width': 'fixed', 'allowed': ['$']},
        {'pos': 13, 'name': 'Configuration', 'width': 'variable', 'pattern': r'^[A-Za-z0-9]+$'}
    ]
    
    def __init__(self):
        """Initialize the checker."""
        super().__init__(
            check_module="16.0_IPTAG_CHECK",
            item_id="IMP-16-0-0-00",
            item_desc="Confirm the IPTAG content and format are correct.(check the Note)"
        )
        self._parsed_items: List[Dict[str, Any]] = []
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
            return create_check_result(
                is_pass=False,
                item_id=self.item_id,
                item_desc=self.item_desc,
                details=[DetailItem(
                    name="Unexpected Error",
                    severity=Severity.FAIL,
                    reason=f"Checker execution failed: {str(e)}",
                    line_number=0,
                    file_path="N/A"
                )],
                pass_reason="",
                fail_reason=f"Checker execution failed: {str(e)}"
            )
    
    # =========================================================================
    # Input Parsing (Common for All Types)
    # =========================================================================
    
    def _parse_input_files(self) -> Dict[str, Any]:
        """
        Parse input files to extract IPTAG field values and validate format.
        
        Returns:
            Dict with parsed data:
            - 'items': List[Dict] - Validated field items with metadata
            - 'errors': List[Dict] - Validation errors with metadata
            - 'metadata': Dict - File metadata
        """
        # 1. Validate input files - IMPORTANT: returns tuple (valid_files_list, missing_files_list)
        valid_files, missing_files = self.validate_input_files()
        
        # FIXED: Explicitly check for empty list
        if not valid_files or len(valid_files) == 0:
            raise ConfigurationError(
                self.create_missing_files_error(missing_files if missing_files else [])
            )
        
        if missing_files:
            raise ConfigurationError(
                self.create_missing_files_error(missing_files)
            )
        
        # 2. Parse IPTAG files
        all_items = []
        all_errors = []
        
        for file_path in valid_files:
            try:
                items, errors = self._parse_iptag_file(file_path)
                all_items.extend(items)
                all_errors.extend(errors)
            except Exception as e:
                all_errors.append({
                    'name': f"File parsing error: {file_path.name}",
                    'line_number': 0,
                    'file_path': str(file_path),
                    'reason': f"Failed to parse file: {str(e)}"
                })
        
        # 3. Store on self
        self._parsed_items = all_items
        self._validation_errors = all_errors
        
        # 4. Return aggregated dict
        return {
            'items': all_items,
            'errors': all_errors,
            'metadata': {
                'total_files': len(valid_files),
                'total_fields': len(all_items),
                'total_errors': len(all_errors)
            }
        }
    
    def _parse_iptag_file(self, file_path: Path) -> Tuple[List[Dict], List[Dict]]:
        """
        Parse a single IPTAG file and validate field values.
        
        Args:
            file_path: Path to IPTAG file
            
        Returns:
            Tuple of (validated_items, validation_errors)
        """
        items = []
        errors = []
        field_values = []
        end_marker_found = False
        end_marker_line = 0
        
        # Read file and extract field values
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line_num, line in enumerate(f, 1):
                # Skip comment lines
                if re.match(r'^\s*#', line) or re.match(r'^\s*###', line):
                    continue
                
                # Check for End marker
                if re.match(r'^End\s*$', line.strip()):
                    end_marker_found = True
                    end_marker_line = line_num
                    continue
                
                # Check for trailing content after End marker
                if end_marker_found and line.strip():
                    errors.append({
                        'name': 'Trailing content after End marker',
                        'line_number': line_num,
                        'file_path': str(file_path),
                        'reason': f"Content found after End marker: {line.strip()}"
                    })
                    continue
                
                # Extract field value (before //)
                match = re.match(r'^([A-Z0-9_$]+)\s*//(.*)', line)
                if match:
                    field_value = match.group(1)
                    field_description = match.group(2).strip()
                    field_values.append({
                        'value': field_value,
                        'description': field_description,
                        'line_number': line_num,
                        'file_path': str(file_path),
                        'line_content': line.strip()
                    })
        
        # Validate End marker presence
        if not end_marker_found:
            errors.append({
                'name': 'Missing End marker',
                'line_number': 0,
                'file_path': str(file_path),
                'reason': 'File must terminate with "End" marker'
            })
        
        # Validate field count
        expected_count = len(self.FIELD_SPEC)
        actual_count = len(field_values)
        if actual_count != expected_count:
            errors.append({
                'name': 'Invalid field count',
                'line_number': 0,
                'file_path': str(file_path),
                'reason': f"Expected {expected_count} fields, found {actual_count}"
            })
            # Continue validation with available fields
        
        # Validate each field
        for idx, field_data in enumerate(field_values):
            if idx >= len(self.FIELD_SPEC):
                errors.append({
                    'name': f'Extra field at position {idx + 1}',
                    'line_number': field_data['line_number'],
                    'file_path': field_data['file_path'],
                    'reason': f"Unexpected field value: {field_data['value']}"
                })
                continue
            
            spec = self.FIELD_SPEC[idx]
            value = field_data['value']
            
            # Validate field value
            is_valid, error_msg = self._validate_field_value(value, spec)
            
            if is_valid:
                items.append({
                    'name': f"{spec['name']}: {field_data.get('description', '')}",
                    'line_number': field_data['line_number'],
                    'file_path': field_data['file_path'],
                    'field_name': spec['name'],
                    'field_value': value,
                    'field_position': spec['pos'],
                    'description': field_data.get('description', '')
                })
            else:
                errors.append({
                    'name': f"{spec['name']}: {field_data.get('description', '')}",
                    'line_number': field_data['line_number'],
                    'file_path': field_data['file_path'],
                    'reason': error_msg
                })
        
        return items, errors
    
    def _validate_field_value(self, value: str, spec: Dict) -> Tuple[bool, str]:
        """
        Validate a field value against its specification.
        
        Args:
            value: Field value to validate
            spec: Field specification dict
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        field_name = spec['name']
        
        # Check fixed-width fields with allowed values
        if spec['width'] == 'fixed' and 'allowed' in spec:
            if value not in spec['allowed']:
                allowed_str = '/'.join(spec['allowed'])
                return False, f"Invalid code '{value}' - must be {allowed_str}"
            return True, ""
        
        # Check variable-width fields with pattern
        if spec['width'] == 'variable' and 'pattern' in spec:
            if not re.match(spec['pattern'], value):
                return False, f"Invalid format '{value}' - does not match required pattern"
            return True, ""
        
        return True, ""
    
    # =========================================================================
    # Type 1: Boolean Check
    # =========================================================================
    
    def _execute_type1(self) -> CheckResult:
        """
        Type 1: Boolean Check.
        
        Validates IPTAG file format and field values.
        PASS if all fields are valid, FAIL if any validation errors.
        Output field descriptions from comments.
        
        Returns:
            CheckResult with is_pass based on validation
        """
        # Parse input
        data = self._parse_input_files()
        items = data.get('items', [])
        errors = data.get('errors', [])
        
        # Convert to dict format with field descriptions
        found_items = {
            item['name']: {
                'name': item['name'],
                'line_number': item.get('line_number', 0),
                'file_path': item.get('file_path', 'N/A')
            }
            for item in items
        }
        
        # Convert errors to missing_items list with descriptions
        missing_items = [error['name'] for error in errors]
        
        # Use template helper - Type 1: Use found_desc and missing_desc
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
        
        Checks if required IPTAG fields (pattern_items) exist and are valid.
        Uses existence_check mode: pattern_items are fields that SHOULD EXIST.
        
        Returns:
            CheckResult with is_pass based on pattern matching
        """
        # Parse input
        data = self._parse_input_files()
        items = data.get('items', [])
        errors = data.get('errors', [])
        
        # Get required patterns
        pattern_items = self.item_data.get('requirements', {}).get('pattern_items', [])
        
        # existence_check mode: Find which patterns exist in parsed items
        found_items = {}
        missing_items = []
        
        for pattern in pattern_items:
            matched = False
            for item in items:
                # Match by field name
                if pattern.lower() in item['field_name'].lower():
                    found_items[item['name']] = {
                        'name': item['name'],
                        'line_number': item.get('line_number', 0),
                        'file_path': item.get('file_path', 'N/A')
                    }
                    matched = True
                    break
            
            if not matched:
                # Check if pattern exists in errors (field found but invalid)
                for error in errors:
                    if pattern.lower() in error['name'].lower():
                        missing_items.append(error['name'])
                        matched = True
                        break
                
                if not matched:
                    missing_items.append(pattern)  # Pattern NOT found in file
        
        # Use template helper - Type 2: Use found_desc and missing_desc
        return self.build_complete_output(
            found_items=found_items,
            missing_items=missing_items,
            found_desc=self.FOUND_DESC_TYPE2_3,
            missing_desc=self.MISSING_DESC_TYPE2_3
        )
    
    # =========================================================================
    # Type 3: Value Check with Waiver Logic
    # =========================================================================
    
    def _execute_type3(self) -> CheckResult:
        """
        Type 3: Value check with waiver support.
        
        Same pattern search logic as Type 2, plus waiver classification.
        Validation errors can be waived by configuration.
        
        Returns:
            CheckResult with FAIL for unwaived, INFO for waived items
        """
        # Parse input
        data = self._parse_input_files()
        items = data.get('items', [])
        errors = data.get('errors', [])
        
        # FIXED: Use waivers.get() directly to preserve dict format
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # Get required patterns
        pattern_items = self.item_data.get('requirements', {}).get('pattern_items', [])
        
        # existence_check mode: Find which patterns exist
        found_items = {}
        waived_items = {}
        unwaived_items = []
        
        for pattern in pattern_items:
            matched = False
            for item in items:
                if pattern.lower() in item['field_name'].lower():
                    found_items[item['name']] = {
                        'name': item['name'],
                        'line_number': item.get('line_number', 0),
                        'file_path': item.get('file_path', 'N/A')
                    }
                    matched = True
                    break
            
            if not matched:
                # Check if pattern exists in errors (field found but invalid)
                for error in errors:
                    if pattern.lower() in error['name'].lower():
                        # Check if error is waived
                        if self.match_waiver_entry(error['name'], waive_dict):
                            waived_items[error['name']] = {
                                'name': error['name'],
                                'line_number': error.get('line_number', 0),
                                'file_path': error.get('file_path', 'N/A'),
                                'reason': error.get('reason', '')
                            }
                        else:
                            unwaived_items.append(error['name'])
                        matched = True
                        break
                
                if not matched:
                    unwaived_items.append(pattern)
        
        # FIXED: waive_dict.keys() returns item names (strings)
        used_names = set(waived_items.keys())
        unused_waivers = [name for name in waive_dict.keys() if name not in used_names]
        
        # Use template helper - Type 3: Use found_desc and missing_desc + waiver params
        return self.build_complete_output(
            found_items=found_items,
            waived_items=waived_items,
            missing_items=unwaived_items,
            waive_dict=waive_dict,
            unused_waivers=unused_waivers,
            found_desc=self.FOUND_DESC_TYPE2_3,
            missing_desc=self.MISSING_DESC_TYPE2_3
        )
    
    # =========================================================================
    # Type 4: Boolean Check with Waiver Logic
    # =========================================================================
    
    def _execute_type4(self) -> CheckResult:
        """
        Type 4: Boolean check with waiver support (Type 1 + waiver).
        
        Same boolean check as Type 1, plus waiver classification.
        Validation errors can be waived by configuration.
        
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
        
        # Convert valid items to dict format
        found_items = {
            item['name']: {
                'name': item['name'],
                'line_number': item.get('line_number', 0),
                'file_path': item.get('file_path', 'N/A')
            }
            for item in items
        }
        
        # Separate waived/unwaived errors
        waived_items = {}
        unwaived_items = []
        
        for error in errors:
            if self.match_waiver_entry(error['name'], waive_dict):
                waived_items[error['name']] = {
                    'name': error['name'],
                    'line_number': error.get('line_number', 0),
                    'file_path': error.get('file_path', 'N/A'),
                    'reason': error.get('reason', '')
                }
            else:
                unwaived_items.append(error['name'])
        
        # FIXED: waive_dict.keys() returns item names (strings)
        used_names = set(waived_items.keys())
        unused_waivers = [name for name in waive_dict.keys() if name not in used_names]
        
        # Use template helper - Type 4: Use found_desc and missing_desc + waiver params
        return self.build_complete_output(
            found_items=found_items,
            waived_items=waived_items,
            missing_items=unwaived_items,
            waive_dict=waive_dict,
            unused_waivers=unused_waivers,
            found_desc=self.FOUND_DESC_TYPE1_4,
            missing_desc=self.MISSING_DESC_TYPE1_4
        )


# =========================================================================
# Entry Point
# =========================================================================

def main():
    """Main entry point."""
    checker = Check_16_0_0_00()
    checker.init_checker(Path(__file__))
    result = checker.execute_check()
    checker.write_output(result)
    return 0 if result.is_pass else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())