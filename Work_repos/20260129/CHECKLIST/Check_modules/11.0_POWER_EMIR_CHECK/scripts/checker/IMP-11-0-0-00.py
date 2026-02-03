################################################################################
# Script Name: IMP-11-0-0-00.py
#
# Purpose:
#   Confirm input database(netlist/def/lef/spef/lib/pgv/etc) are loaded correctly.
#
# Logic:
#   - Parse Voltus log files (*static*.log, *dynamic*.log, *EM*.log) to extract database loading sections
#   - Extract ERROR messages from 7 loading phases: LEF, View Definition, Hierarchical DEF, Verilog, DEF, SPEF, Cell Libraries for Rail Analysis
#   - Verify each section has no unwaived errors (compare error codes against waiver list)
#   - Support waiver for specific error codes (IMPLF-388, IMPDB-5061, etc.)
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
# Refactored: 2026-01-06 (Using checker_templates v1.1.0)
#
# Author: Jing Li
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
from checker_templates.input_file_parser_template import InputFileParserMixin  # Optional but recommended


# MANDATORY: Inherit mixins in correct order (InputFileParserMixin first if used)
class Check_11_0_0_00(InputFileParserMixin, OutputBuilderMixin, WaiverHandlerMixin, BaseChecker):
    """
    IMP-11-0-0-00: Confirm input database(netlist/def/lef/spef/lib/pgv/etc) are loaded correctly.
    
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
    # ⭐ DESCRIPTION CONSTANTS - Split by Type semantics (API-026)
    # =========================================================================
    # DESC constants are split by Type for semantic clarity (same as REASON split)
    # Type 1/4 emphasize "found/not found", Type 2/3 emphasize "matched/satisfied"
    
    # Type 1/4: Boolean checks - emphasize "found/not found" (existence)
    FOUND_DESC_TYPE1_4 = "All database loading sections completed without unwaived errors"
    MISSING_DESC_TYPE1_4 = "Database loading errors detected in one or more sections"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_DESC_TYPE2_3 = "Database loading section validated successfully (no unwaived errors)"
    MISSING_DESC_TYPE2_3 = "Database loading section failed validation (unwaived errors detected)"
    
    # All Types (waiver description unified)
    WAIVED_DESC = "Database loading errors waived per approved exception list"
    
    # ⭐ REASON CONSTANTS - Split by Type semantics (API-025)
    # ALL Types pass found_reason/missing_reason, but use different constants
    
    # Type 1/4: Boolean checks - Use staticmethod lambda to extract per-item reason from metadata
    # Each item's metadata contains a 'reason' field with section-specific details
    FOUND_REASON_TYPE1_4 = staticmethod(lambda meta: meta.get('reason', 'Database loading section completed without unwaived errors'))
    MISSING_REASON_TYPE1_4 = "Unwaived ERROR messages detected during database loading"
    
    # Type 2/3: Pattern checks - Use staticmethod lambda to extract per-item reason from metadata
    # Each item's metadata contains a 'reason' field with section-specific details
    FOUND_REASON_TYPE2_3 = staticmethod(lambda meta: meta.get('reason', 'Section validated: no ERROR messages found, or all errors matched waiver list'))
    MISSING_REASON_TYPE2_3 = "ERROR detected and not satisfied by waiver list (error code not in waive_items)"
    
    # Waiver-related (Type 3/4 only)
    WAIVED_BASE_REASON = "ERROR message matched waiver list (error code in approved exceptions)"
    UNUSED_WAIVER_REASON = "Waiver defined but no corresponding ERROR found in database loading sections"
    
    def __init__(self):
        """Initialize the checker."""
        super().__init__(
            check_module="11.0_POWER_EMIR_CHECK",
            item_id="IMP-11-0-0-00",
            item_desc="Confirm input database(netlist/def/lef/spef/lib/pgv/etc) are loaded correctly."
        )
        # Custom member variables for parsed data
        self._parsed_items: List[Dict[str, Any]] = []
        self._metadata: Dict[str, str] = {}
        self._section_errors: Dict[str, List[Dict[str, Any]]] = {}
    
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
    
    def _generate_section_reason(self, section_name: str, metadata: dict) -> str:
        """
        Generate section-specific reason message based on metadata.
        
        Args:
            section_name: Name of the section (LEF Loading, View Definition, etc.)
            metadata: Dictionary containing section-specific metadata
        
        Returns:
            Section-specific reason string
        """
        if section_name == 'LEF Loading':
            lib_count = metadata.get('lib_count', 0)
            if lib_count > 0:
                return f"LEF loading completed successfully ({lib_count} libraries loaded)"
            return "LEF loading completed successfully"
        
        elif section_name == 'View Definition':
            view_file = metadata.get('view_file')
            if view_file:
                # Extract just the filename from the path
                import os
                view_name = os.path.basename(view_file)
                return f"View definition loaded: {view_name}"
            return "View definition loaded successfully"
        
        elif section_name == 'Hierarchical DEF Merge':
            merge_count = metadata.get('merge_count', 0)
            if merge_count > 0:
                return f"Hierarchical DEF merge completed ({merge_count} merge operation(s))"
            return "Hierarchical DEF merge completed successfully"
        
        elif section_name == 'Verilog Netlist':
            verilog_count = metadata.get('verilog_count', 0)
            if verilog_count > 0:
                return f"Verilog netlist loading completed ({verilog_count} netlist file(s) loaded)"
            return "Verilog netlist loading completed successfully"
        
        elif section_name == 'DEF Loading':
            def_count = metadata.get('def_count', 0)
            if def_count > 0:
                return f"DEF loading completed ({def_count} DEF file(s) loaded)"
            return "DEF loading completed successfully"
        
        elif section_name == 'SPEF Loading':
            rc_corner = metadata.get('rc_corner')
            spef_count = metadata.get('spef_count', 0)
            if rc_corner and spef_count > 0:
                return f"SPEF files loaded for RC corner '{rc_corner}' ({spef_count} file(s))"
            elif rc_corner:
                return f"SPEF files loaded for RC corner '{rc_corner}'"
            elif spef_count > 0:
                return f"SPEF loading completed ({spef_count} file(s) loaded)"
            return "SPEF loading completed successfully"
        
        elif section_name == 'Cell Libraries for Rail Analysis':
            lib_count = metadata.get('rail_lib_count', 0)
            if lib_count > 0:
                return f"Cell libraries for rail analysis processed successfully ({lib_count} libraries)"
            return "Cell libraries for rail analysis processed successfully"
        
        # Default fallback
        return f"{section_name} completed without errors"
    
    def _parse_input_files(self) -> Dict[str, Any]:
        """
        Parse Voltus log files to extract database loading errors by section.
        
        Parses 7 database loading sections:
        1. LEF Loading (read_lib -lef)
        2. View Definition (read_view_definition)
        3. Hierarchical DEF Merge (merge_hierarchical_def)
        4. Verilog Netlist (read_verilog)
        5. DEF Loading (read_def)
        6. SPEF Loading (SPEF files for RC Corner)
        7. Cell Libraries for Rail Analysis (Begin/Ended Processing Cell Libraries for Rail Analysis)
        
        Returns:
            Dict with parsed data:
            - 'items': List[Dict] - Section validation results with error details
            - 'metadata': Dict - File metadata (tool version, design name)
            - 'errors': List - Parsing errors encountered
            - 'clean_sections': List[Dict] - Sections without errors
        """
        # 1. Validate input files (returns tuple: valid_files, missing_files)
        valid_files, missing_files = self.validate_input_files()
        
        # FIXED: Explicitly check for empty list
        if missing_files and len(missing_files) > 0:
            raise ConfigurationError(
                self.create_missing_files_error(missing_files)
            )
        
        # FIXED: Explicitly check for empty list
        if not valid_files or len(valid_files) == 0:
            raise ConfigurationError("No valid input files found")
        
        # 2. Initialize parsing structures
        items = []
        metadata = {}
        errors = []
        section_errors = {
            'LEF Loading': [],
            'View Definition': [],
            'Hierarchical DEF Merge': [],
            'Verilog Netlist': [],
            'DEF Loading': [],
            'SPEF Loading': [],
            'Cell Libraries for Rail Analysis': []
        }
        
        # Track which sections were actually encountered in the log
        sections_encountered = set()
        
        # 3. Parse each input file for database loading errors and metadata
        section_metadata = {
            'LEF Loading': {'lef_count': 0, 'lib_count': 0},
            'View Definition': {'view_file': None},
            'Hierarchical DEF Merge': {'merge_count': 0},
            'Verilog Netlist': {'verilog_count': 0},
            'DEF Loading': {'def_count': 0},
            'SPEF Loading': {'rc_corner': None, 'spef_count': 0},
            'Cell Libraries for Rail Analysis': {'rail_lib_count': 0}
        }
        
        for file_path in valid_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    current_section = None
                    line_buffer = []
                    
                    for line_num, line in enumerate(f, 1):
                        # Pattern 1: Command section markers
                        cmd_match = re.match(r'^<CMD>\s+(read_lib|read_view_definition|merge_hierarchical_def|read_verilog|read_def|set_\w+)', line)
                        if cmd_match:
                            cmd = cmd_match.group(1)
                            if 'read_lib' in cmd and '-lef' in line:
                                current_section = 'LEF Loading'
                                sections_encountered.add('LEF Loading')
                                section_metadata['LEF Loading']['lef_count'] += 1
                            elif 'read_view_definition' in cmd:
                                current_section = 'View Definition'
                                sections_encountered.add('View Definition')
                            elif 'merge_hierarchical_def' in cmd:
                                current_section = 'Hierarchical DEF Merge'
                                sections_encountered.add('Hierarchical DEF Merge')
                                section_metadata['Hierarchical DEF Merge']['merge_count'] += 1
                            elif 'read_verilog' in cmd:
                                current_section = 'Verilog Netlist'
                                sections_encountered.add('Verilog Netlist')
                            elif 'read_def' in cmd:
                                current_section = 'DEF Loading'
                                sections_encountered.add('DEF Loading')
                                section_metadata['DEF Loading']['def_count'] += 1
                            else:
                                current_section = None
                        
                        # Pattern 2: SPEF loading section marker
                        spef_match = re.match(r'^SPEF files for RC Corner\s+(\S+)', line)
                        if spef_match:
                            current_section = 'SPEF Loading'
                            sections_encountered.add('SPEF Loading')
                            section_metadata['SPEF Loading']['rc_corner'] = spef_match.group(1).rstrip(':')
                        
                        # Pattern 3: Cell Libraries for Rail Analysis section markers
                        rail_begin_match = re.match(r'^Begin Processing Cell Libraries for Rail Analysis', line)
                        if rail_begin_match:
                            current_section = 'Cell Libraries for Rail Analysis'
                            sections_encountered.add('Cell Libraries for Rail Analysis')
                        
                        rail_end_match = re.match(r'^Ended Processing Cell Libraries for Rail Analysis', line)
                        if rail_end_match:
                            if current_section == 'Cell Libraries for Rail Analysis':
                                current_section = None
                        
                        # Capture section-specific metadata
                        if current_section == 'LEF Loading':
                            lib_match = re.search(r'Read (\d+) cells in library', line)
                            if lib_match:
                                section_metadata['LEF Loading']['lib_count'] += 1
                        elif current_section == 'View Definition':
                            view_match = re.search(r'Loading view definition file from (.+)', line)
                            if view_match:
                                section_metadata['View Definition']['view_file'] = view_match.group(1).strip()
                        elif current_section == 'Verilog Netlist':
                            verilog_match = re.search(r"Reading verilog netlist '([^']+)'", line)
                            if verilog_match:
                                section_metadata['Verilog Netlist']['verilog_count'] += 1
                        elif current_section == 'SPEF Loading':
                            spef_file_match = re.search(r"(Sub-block|Top-level) [Ss]pef file", line)
                            if spef_file_match:
                                section_metadata['SPEF Loading']['spef_count'] += 1
                        elif current_section == 'Cell Libraries for Rail Analysis':
                            rail_lib_match = re.search(r'Processing library|Read (\d+) cells', line)
                            if rail_lib_match:
                                section_metadata['Cell Libraries for Rail Analysis']['rail_lib_count'] += 1
                        
                        # Pattern 4: Error detection with Cadence error codes
                        error_match = re.match(r'^\*\*ERROR:\s*(?:\(([A-Z_]+-\d+)\))?\s*(.+)|^ERROR:\s+(.+)', line)
                        if error_match and current_section:
                            error_code = error_match.group(1) if error_match.group(1) else 'UNKNOWN'
                            error_message = error_match.group(2) if error_match.group(2) else error_match.group(3)
                            
                            section_errors[current_section].append({
                                'name': error_code,
                                'error_code': error_code,
                                'error_message': error_message.strip(),
                                'line_number': line_num,
                                'file_path': str(file_path),
                                'section': current_section
                            })
            except Exception as e:
                errors.append(f"Error parsing {file_path}: {str(e)}")
        
        # 4. Store frequently reused data on self
        self._section_errors = section_errors
        
        # Build items list from section errors
        for section_name, error_list in section_errors.items():
            if error_list:
                for error in error_list:
                    items.append({
                        'name': f"{section_name}",
                        'error_code': error['error_code'],
                        'error_message': error['error_message'],
                        'line_number': error['line_number'],
                        'file_path': error['file_path'],
                        'section': section_name
                    })
        
        # Build clean_sections list (sections without errors) with specific reasons
        # CRITICAL: Only include sections that were actually encountered in the log
        clean_sections = []
        for section_name in section_errors.keys():
            # Only report sections that actually appeared in the log
            if section_name in sections_encountered and not section_errors[section_name]:
                # Generate section-specific reason
                reason = self._generate_section_reason(section_name, section_metadata.get(section_name, {}))
                clean_sections.append({
                    'name': section_name,
                    'line_number': 0,
                    'file_path': 'N/A',
                    'reason': reason
                })
        
        self._parsed_items = items
        
        return {
            'items': items,
            'metadata': metadata,
            'errors': errors,
            'clean_sections': clean_sections
        }
    
    # =========================================================================
    # Type 1: Boolean Check
    # =========================================================================
    
    def _execute_type1(self) -> CheckResult:
        """Type 1: Boolean check without waiver support."""
        violations = self._type1_core_logic()
        
        # ⚠️ CRITICAL: found_items MUST be dict[str, dict], NOT list!
        # Build dict from clean sections (sections without errors)
        data = self._parse_input_files()
        clean_sections = data.get('clean_sections', [])
        
        found_items = {}
        for section in clean_sections:
            section_name = section['name']
            found_items[section_name] = {
                'name': section_name,
                'line_number': section.get('line_number', 0),
                'file_path': section.get('file_path', 'N/A'),
                'reason': section.get('reason', f"{section_name} completed without errors")
            }
        
        missing_items = violations
        
        return self.build_complete_output(
            found_items=found_items,
            missing_items=missing_items,
            found_desc=self.FOUND_DESC_TYPE1_4,
            missing_desc=self.MISSING_DESC_TYPE1_4,
            found_reason=self.FOUND_REASON_TYPE1_4,
            missing_reason=self.MISSING_REASON_TYPE1_4
        )
    
    def _type1_core_logic(self) -> dict:
        """
        Core Type 1 boolean check logic (shared by Type 1 and Type 4).
        
        Returns:
            Dict of violations: {section_name: {'line_number': ..., 'file_path': ..., 'reason': ...}}
            Empty dict if all checks pass.
        """
        data = self._parse_input_files()
        section_errors = self._section_errors
        
        violations = {}
        
        # Check each database loading section for unwaived errors
        for section_name, errors in section_errors.items():
            if errors:
                # Section has unwaived errors - this is a violation
                error_summary = '; '.join([
                    f"({err.get('error_code', 'UNKNOWN')}) {err.get('error_message', 'Unknown error')}"
                    for err in errors[:3]  # Show first 3 errors
                ])
                if len(errors) > 3:
                    error_summary += f" ... and {len(errors) - 3} more errors"
                
                violations[section_name] = {
                    'line_number': errors[0].get('line_number', 0),
                    'file_path': errors[0].get('file_path', 'N/A'),
                    'reason': f"Unwaived ERROR messages detected: {error_summary}"
                }
        
        return violations
    
    # =========================================================================
    # Type 2: Value Check
    # =========================================================================
    
    def _execute_type2(self) -> CheckResult:
        """Type 2: Pattern/value check without waiver support."""
        found_items, missing_items = self._type2_core_logic()
        
        return self.build_complete_output(
            found_items=found_items,
            missing_items=missing_items,
            found_desc=self.FOUND_DESC_TYPE2_3,
            missing_desc=self.MISSING_DESC_TYPE2_3,
            found_reason=self.FOUND_REASON_TYPE2_3,
            missing_reason=self.MISSING_REASON_TYPE2_3
        )
    
    def _type2_core_logic(self) -> Tuple[Dict[str, dict], Dict[str, dict]]:
        """
        Core Type 2 pattern matching logic (shared by Type 2 and Type 3).
        
        Returns:
            Tuple of (found_items, missing_items)
            - found_items: {section_name: {'line_number': ..., 'file_path': ...}}
            - missing_items: {section_name: {'line_number': ..., 'file_path': ..., 'reason': ...}}
        """
        data = self._parse_input_files()
        section_errors = self._section_errors
        clean_sections = data.get('clean_sections', [])
        
        # Build a lookup dict for clean sections with their reasons
        clean_section_dict = {section['name']: section for section in clean_sections}
        
        requirements = self.item_data.get('requirements', {})
        pattern_items = requirements.get('pattern_items', [])
        
        found_items = {}
        missing_items = {}
        
        # Check each required database loading section
        for section_name in pattern_items:
            errors = section_errors.get(section_name, [])
            
            if not errors:
                # Section found and validated (no unwaived errors)
                # Get section-specific reason from clean_sections
                clean_section = clean_section_dict.get(section_name, {})
                found_items[section_name] = {
                    'line_number': 0,
                    'file_path': 'N/A',
                    'reason': clean_section.get('reason', f"{section_name} completed without errors")
                }
            else:
                # Section has unwaived errors
                error_summary = '; '.join([
                    f"({err.get('error_code', 'UNKNOWN')}) {err.get('error_message', 'Unknown error')}"
                    for err in errors[:3]
                ])
                if len(errors) > 3:
                    error_summary += f" ... and {len(errors) - 3} more errors"
                
                missing_items[section_name] = {
                    'line_number': errors[0].get('line_number', 0),
                    'file_path': errors[0].get('file_path', 'N/A'),
                    'reason': f'Unwaived ERROR messages detected: {error_summary}'
                }
        
        return found_items, missing_items
    
    # =========================================================================
    # Type 3: Value Check with Waiver Logic
    # =========================================================================
    
    def _execute_type3(self) -> CheckResult:
        """Type 3: Pattern/value check with waiver support (reuses Type 2 core logic)."""
        # Step 1: Get found/missing items using Type 2's core logic
        found_items_base, violations = self._type2_core_logic()
        
        # Step 2: Parse waiver configuration (FIXED: API-008)
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # Step 3: Initialize result collections
        found_items = {}
        waived_items = {}
        missing_items = {}
        used_waivers = set()
        
        # Step 4: Process found_items_base (sections with no errors)
        for item_name, item_data in found_items_base.items():
            found_items[item_name] = item_data
        
        # Step 5: Process violations with waiver matching
        section_errors = self._section_errors
        for viol_name, viol_data in violations.items():
            errors = section_errors.get(viol_name, [])
            all_errors_waived = True
            
            for error in errors:
                error_code = error.get('error_code', '')
                matched_waiver = self.match_waiver_entry(error_code, waive_dict)
                if matched_waiver:
                    used_waivers.add(matched_waiver)
                else:
                    all_errors_waived = False
            
            if all_errors_waived and errors:
                waived_items[viol_name] = viol_data
            else:
                missing_items[viol_name] = viol_data
        
        # Step 6: Find unused waivers
        unused_waivers = [w for w in waive_dict.keys() if w not in used_waivers]
        
        # Step 7: Build output (FIXED: API-009 - pass dict directly)
        return self.build_complete_output(
            found_items=found_items,
            missing_items=missing_items,
            waived_items=waived_items,
            unused_waivers=unused_waivers,
            waive_dict=waive_dict,
            found_desc=self.FOUND_DESC_TYPE2_3,
            missing_desc=self.MISSING_DESC_TYPE2_3,
            waived_desc=self.WAIVED_DESC,
            found_reason=self.FOUND_REASON_TYPE2_3,
            missing_reason=self.MISSING_REASON_TYPE2_3,
            waived_base_reason=self.WAIVED_BASE_REASON,
            unused_waiver_reason=self.UNUSED_WAIVER_REASON
        )
    
    # =========================================================================
    # Type 4: Boolean Check with Waiver Logic
    # =========================================================================
    
    def _execute_type4(self) -> CheckResult:
        """Type 4: Boolean check with waiver support (reuses Type 1 core logic)."""
        violations = self._type1_core_logic()
        
        # ⚠️ CRITICAL: found_items MUST be dict[str, dict], NOT list!
        data = self._parse_input_files()
        clean_sections = data.get('clean_sections', [])
        
        found_items = {}
        for section in clean_sections:
            section_name = section['name']
            found_items[section_name] = {
                'name': section_name,
                'line_number': section.get('line_number', 0),
                'file_path': section.get('file_path', 'N/A'),
                'reason': section.get('reason', f"{section_name} completed without errors")
            }
        
        # FIXED: API-008 - Use waivers.get() instead of get_waive_items()
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        waived_items = {}
        missing_items = {}
        used_waivers = set()
        
        # Process each violation and check against waivers
        section_errors = self._section_errors
        for viol_name, viol_data in violations.items():
            errors = section_errors.get(viol_name, [])
            all_errors_waived = True
            
            for error in errors:
                error_code = error.get('error_code', '')
                matched_waiver = self.match_waiver_entry(error_code, waive_dict)
                if matched_waiver:
                    used_waivers.add(matched_waiver)
                else:
                    all_errors_waived = False
            
            if all_errors_waived and errors:
                waived_items[viol_name] = viol_data
            else:
                missing_items[viol_name] = viol_data
        
        unused_waivers = [w for w in waive_dict.keys() if w not in used_waivers]
        
        # FIXED: API-009 - pass dict directly, not list(dict.values())
        return self.build_complete_output(
            found_items=found_items,
            missing_items=missing_items,
            waived_items=waived_items,
            unused_waivers=unused_waivers,
            waive_dict=waive_dict,
            found_desc=self.FOUND_DESC_TYPE1_4,
            missing_desc=self.MISSING_DESC_TYPE1_4,
            waived_desc=self.WAIVED_DESC,
            found_reason=self.FOUND_REASON_TYPE1_4,
            missing_reason=self.MISSING_REASON_TYPE1_4,
            waived_base_reason=self.WAIVED_BASE_REASON,
            unused_waiver_reason=self.UNUSED_WAIVER_REASON
        )


# =========================================================================
# Entry Point
# =========================================================================

def main():
    """Main entry point."""
    checker = Check_11_0_0_00()
    checker.init_checker(Path(__file__))
    result = checker.execute_check()
    checker.write_output(result)
    return 0 if result.is_pass else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())