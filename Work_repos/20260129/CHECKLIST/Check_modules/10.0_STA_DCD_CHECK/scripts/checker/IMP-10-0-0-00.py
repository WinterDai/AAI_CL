################################################################################
# Script Name: IMP-10-0-0-00.py
#
# Purpose:
#   Confirm the netlist/spef version is correct.
#
# Logic:
#   - Parse input files: sta_post_syn.log
#   - Extract netlist file path from read_netlist command
#   - Determine SPEF status (read or skipped) from log messages
#   - Open extracted netlist file to capture version timestamp from header (line 3)
#   - Open extracted SPEF file (if present) to capture version timestamp
#   - Verify parasitics mode consistency with SPEF status
#   - Extract tool version and top-level design name for context
#   - Validate that netlist and SPEF versions match expected configuration
#   - Report version information with file paths and timestamps
#
# Auto Type Detection:
#   Type 1: requirements.value=N/A, waivers.value=N/A/0 → Boolean check
#   Type 2: requirements.value>0, pattern_items exists, waivers.value=N/A/0 → Value comparison
#   Type 3: requirements.value>0, pattern_items exists, waivers.value>0 → Value with waiver logic
#   Type 4: requirements.value=N/A, waivers.value>0 → Boolean with waiver logic
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
# Refactored: 2026-01-06 (Using checker_templates v1.1.0)
#
# Author: yyin
# Date: 2026-01-06
################################################################################

from pathlib import Path
import re
import sys
import gzip
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
class Check_10_0_0_00(InputFileParserMixin, OutputBuilderMixin, WaiverHandlerMixin, BaseChecker):
    """
    IMP-10-0-0-00: Confirm the netlist/spef version is correct.
    
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
    FOUND_DESC_TYPE1_4 = "Netlist and SPEF version information extracted and verified"
    MISSING_DESC_TYPE1_4 = "Netlist or SPEF version information missing or incomplete"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_DESC_TYPE2_3 = "Required version patterns matched and validated"
    MISSING_DESC_TYPE2_3 = "Expected version patterns not satisfied or missing"
    
    # All Types (waiver description unified)
    WAIVED_DESC = "Version mismatches waived per configuration"
    
    # ⭐ REASON CONSTANTS - Split by Type semantics (API-025)
    # ALL Types pass found_reason/missing_reason, but use different constants
    
    # Type 1/4: Boolean checks - emphasize "found/not found" (existence)
    FOUND_REASON_TYPE1_4 = "Netlist and SPEF version information found in log and file headers"
    MISSING_REASON_TYPE1_4 = "Version information not found in expected locations"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_REASON_TYPE2_3 = "Version pattern matched and timestamp validated"
    MISSING_REASON_TYPE2_3 = "Version pattern not satisfied or timestamp mismatch"
    
    # Waiver-related (Type 3/4 only)
    WAIVED_BASE_REASON = "Version mismatch waived per project configuration"
    UNUSED_WAIVER_REASON = "Waiver defined but no version mismatch matched"
    
    def __init__(self):
        """Initialize the checker."""
        super().__init__(
            check_module="10.0_STA_DCD_CHECK",
            item_id="IMP-10-0-0-00",
            item_desc="Confirm the netlist/spef version is correct."
        )
        # Custom member variables for parsed data
        self._parsed_items: List[Dict[str, Any]] = []
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
        Parse input files to extract netlist and SPEF version information.
        
        Two-step validation process:
        1. Parse STA log to find netlist/SPEF file paths
        2. Open actual files to extract version timestamps (netlist version from line 3)
        
        Returns:
            Dict with parsed data:
            - 'items': List[Dict] - Version information items with metadata
            - 'metadata': Dict - File metadata (tool version, design name, etc.)
            - 'errors': List - Any parsing errors encountered
        """
        # 1. Validate input files (raises ConfigurationError if missing)
        valid_files, missing_files = self.validate_input_files()
        if missing_files:
            raise ConfigurationError(
                self.create_missing_files_error(missing_files)
            )
        
        items = []
        metadata = {}
        errors = []
        
        # 2. Parse STA log file to extract file paths and status
        for file_path in valid_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                    
                netlist_path = None
                spef_path = None
                spef_status = "Unknown"
                parasitics_mode = "Unknown"
                top_design = "Unknown"
                tool_version = "Unknown"
                
                for line_num, line in enumerate(lines, 1):
                    # Pattern 1: Extract netlist file path
                    match_netlist = re.search(r'read_netlist\s+([^\s]+\.v(?:\.gz)?)', line)
                    if match_netlist:
                        netlist_path = match_netlist.group(1)
                        items.append({
                            'name': f"Netlist: {Path(netlist_path).name}",
                            'type': 'netlist_path',
                            'path': netlist_path,
                            'line_number': line_num,
                            'file_path': str(file_path)
                        })
                    
                    # Pattern 2: Check if SPEF was skipped
                    match_spef_skip = re.search(r'\[INFO\]\s+Skipping SPEF reading as (.+)', line)
                    if match_spef_skip:
                        spef_status = f"Skipped: {match_spef_skip.group(1)}"
                        items.append({
                            'name': f"SPEF: {spef_status}",
                            'type': 'spef_status',
                            'status': spef_status,
                            'line_number': line_num,
                            'file_path': str(file_path)
                        })
                    
                    # Pattern 3: Extract SPEF file path if read
                    match_spef_read = re.search(r'read_spef\s+([^\s]+\.spef(?:\.gz)?)', line)
                    if match_spef_read:
                        spef_path = match_spef_read.group(1)
                        spef_status = "Read"
                        items.append({
                            'name': f"SPEF: {Path(spef_path).name}",
                            'type': 'spef_path',
                            'path': spef_path,
                            'line_number': line_num,
                            'file_path': str(file_path)
                        })
                    
                    # Pattern 4: Extract parasitics mode
                    match_parasitics = re.search(r'#\s*Parasitics Mode:\s*(.+)', line)
                    if match_parasitics:
                        parasitics_mode = match_parasitics.group(1).strip()
                        items.append({
                            'name': f"Parasitics Mode: {parasitics_mode}",
                            'type': 'parasitics_mode',
                            'mode': parasitics_mode,
                            'line_number': line_num,
                            'file_path': str(file_path)
                        })
                    
                    # Pattern 5: Extract top-level design name
                    match_top_design = re.search(r'Top level cell is\s+(\S+)', line)
                    if match_top_design:
                        top_design = match_top_design.group(1).rstrip('.')
                        items.append({
                            'name': f"Top Design: {top_design}",
                            'type': 'top_design',
                            'design': top_design,
                            'line_number': line_num,
                            'file_path': str(file_path)
                        })
                    
                    # Pattern 6: Extract tool version
                    match_tool_version = re.search(r'Program version\s*=\s*([\d\.\-\w]+)', line)
                    if match_tool_version:
                        tool_version = match_tool_version.group(1)
                        items.append({
                            'name': f"Tool Version: {tool_version}",
                            'type': 'tool_version',
                            'version': tool_version,
                            'line_number': line_num,
                            'file_path': str(file_path)
                        })
                
                # 3. Extract version information from actual netlist file (line 3)
                if netlist_path:
                    netlist_version = self._extract_file_version(netlist_path, 'netlist')
                    if netlist_version:
                        items.append({
                            'name': f"Netlist Version: {netlist_version}",
                            'type': 'netlist_version',
                            'version': netlist_version,
                            'line_number': 3,  # Netlist version is on line 3
                            'file_path': netlist_path
                        })
                    else:
                        errors.append(f"Could not extract version from netlist line 3: {netlist_path}")
                
                # 4. Extract version information from actual SPEF file
                if spef_path and spef_status == "Read":
                    spef_version = self._extract_file_version(spef_path, 'spef')
                    if spef_version:
                        items.append({
                            'name': f"SPEF Version: {spef_version}",
                            'type': 'spef_version',
                            'version': spef_version,
                            'line_number': 0,  # From external file
                            'file_path': spef_path
                        })
                    else:
                        errors.append(f"Could not extract version from SPEF: {spef_path}")
                
                # Store metadata
                metadata = {
                    'netlist_path': netlist_path,
                    'spef_path': spef_path,
                    'spef_status': spef_status,
                    'parasitics_mode': parasitics_mode,
                    'top_design': top_design,
                    'tool_version': tool_version
                }
                
            except Exception as e:
                errors.append(f"Error parsing {file_path}: {str(e)}")
        
        # 5. Store frequently reused data on self
        self._parsed_items = items
        self._metadata = metadata
        
        return {
            'items': items,
            'metadata': metadata,
            'errors': errors
        }
    
    def _extract_file_version(self, file_path: str, file_type: str) -> Optional[str]:
        """
        Extract version timestamp from netlist or SPEF file header.
        For netlist files, specifically extract from line 3.
        
        Args:
            file_path: Path to the file
            file_type: 'netlist' or 'spef'
            
        Returns:
            Version timestamp string or None if not found
        """
        try:
            # Always try to open as plain text first
            # Files with .gz extension may not actually be gzip compressed
            try:
                f = open(file_path, 'r', encoding='utf-8', errors='ignore')
            except Exception:
                # If plain text fails and file has .gz extension, try gzip
                if file_path.endswith('.gz'):
                    try:
                        f = gzip.open(file_path, 'rt', encoding='utf-8', errors='ignore')
                    except Exception:
                        return None
                else:
                    return None
            
            with f:
                if file_type == 'netlist':
                    # For netlist, extract version from line 3 specifically
                    for i, line in enumerate(f, 1):
                        if i == 3:
                            # Pattern 1: Netlist - "Generated on: Nov 18 2025 15:58:15 IST"
                            match_generated = re.search(r'Generated on:\s*(.+?)\s+\w+\s+\((.+?)\)', line)
                            if match_generated:
                                # Return local time portion (before timezone)
                                return match_generated.group(1).strip()
                            
                            # Pattern 2: Alternative - just "Generated on: <timestamp>"
                            match_simple = re.search(r'Generated on:\s*(.+?)$', line)
                            if match_simple:
                                timestamp = match_simple.group(1).strip()
                                # Remove trailing UTC info if present
                                timestamp = re.sub(r'\s+\([^)]+\)\s*$', '', timestamp)
                                return timestamp
                            
                            # If line 3 doesn't match expected patterns, return None
                            return None
                        elif i > 3:
                            # Stop after line 3 for netlist
                            break
                else:
                    # For SPEF, read first 100 lines to find version info
                    for i, line in enumerate(f, 1):
                        if i > 100:
                            break
                        
                        # Pattern 3: SPEF DATE field
                        match_date = re.search(r'DATE\s+"(.+?)"', line)
                        if match_date:
                            return match_date.group(1).strip()
                        
                        # Pattern 4: SPEF DESIGN_FLOW with timestamp
                        match_flow = re.search(r'DESIGN_FLOW\s+"(.+?)"', line)
                        if match_flow and 'VERSION' in match_flow.group(1):
                            return match_flow.group(1).strip()
            
            return None
            
        except Exception as e:
            # File not found or cannot be read
            return None
    
    # =========================================================================
    # Type 1: Boolean Check
    # =========================================================================
    
    def _execute_type1(self) -> CheckResult:
        """
        Type 1: Boolean Check.
        
        Verify that netlist and SPEF version information exists in the log.
        
        Returns:
            CheckResult with is_pass based on check logic
        """
        # Parse input
        data = self._parse_input_files()
        items = data.get('items', [])
        errors = data.get('errors', [])
        
        # Check if we have the required version information
        has_netlist_path = any(item['type'] == 'netlist_path' for item in items)
        has_spef_status = any(item['type'] in ['spef_status', 'spef_path'] for item in items)
        has_netlist_version = any(item['type'] == 'netlist_version' for item in items)
        
        # Build found_items dict with metadata
        found_items = {}
        missing_items = []
        
        if has_netlist_path and has_spef_status:
            for item in items:
                if item['type'] in ['netlist_path', 'spef_status', 'spef_path', 
                                   'netlist_version', 'spef_version', 'parasitics_mode',
                                   'top_design', 'tool_version']:
                    found_items[item['name']] = {
                        'name': item['name'],
                        'line_number': item.get('line_number', 0),
                        'file_path': item.get('file_path', 'N/A')
                    }
        else:
            if not has_netlist_path:
                missing_items.append('Netlist file path not found in log')
            if not has_spef_status:
                missing_items.append('SPEF status not found in log')
        
        # Add errors to missing items
        if errors:
            missing_items.extend(errors)
        
        # Use template helper (auto-handles waiver=0)
        # Type 1: Use TYPE1_4 reason (emphasize "found/not found")
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
        
        # Get requirements
        pattern_items = self.item_data.get('requirements', {}).get('pattern_items', [])
        
        # existence_check mode: Check if pattern_items exist in parsed items
        found_items = {}
        missing_items = []
        
        for pattern in pattern_items:
            matched = False
            for item in items:
                # Match pattern against item name or type
                if (pattern.lower() in item['name'].lower() or 
                    pattern.lower() in item.get('type', '').lower()):
                    found_items[item['name']] = {
                        'name': item['name'],
                        'line_number': item.get('line_number', 0),
                        'file_path': item.get('file_path', 'N/A')
                    }
                    matched = True
                    break
            
            if not matched:
                missing_items.append(pattern)
        
        # Use template helper (auto-handles waiver=0)
        # Type 2: Use TYPE2_3 desc+reason (emphasize "matched/satisfied")
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
        
        # FIXED: Use waivers.get() directly to preserve dict format (API-016)
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # Get requirements
        pattern_items = self.item_data.get('requirements', {}).get('pattern_items', [])
        
        # existence_check mode: Find patterns in parsed items
        found_items = {}
        violations = []  # Patterns not found (potential violations)
        
        for pattern in pattern_items:
            matched = False
            for item in items:
                if (pattern.lower() in item['name'].lower() or 
                    pattern.lower() in item.get('type', '').lower()):
                    found_items[item['name']] = {
                        'name': item['name'],
                        'line_number': item.get('line_number', 0),
                        'file_path': item.get('file_path', 'N/A')
                    }
                    matched = True
                    break
            
            if not matched:
                violations.append(pattern)
        
        # Separate waived/unwaived using template helper
        waived_items = {}
        unwaived_items = []
        
        for violation in violations:
            if self.match_waiver_entry(violation, waive_dict):
                # Create dict entry for waived item
                waived_items[violation] = {
                    'name': violation,
                    'line_number': 0,
                    'file_path': 'N/A'
                }
            else:
                unwaived_items.append(violation)
        
        # Find unused waivers by checking if waiver names were used
        used_names = set(waived_items.keys())
        unused_waivers = [name for name in waive_dict.keys() if name not in used_names]
        
        # Use template helper for automatic output formatting (waivers.value>0)
        # Type 3: Use TYPE2_3 desc+reason (emphasize "matched/satisfied")
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
            waived_base_reason=self.WAIVED_BASE_REASON,
            unused_waiver_reason=self.UNUSED_WAIVER_REASON
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
        
        # FIXED: Use waivers.get() directly to preserve dict format (API-016)
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # Check for violations (missing version information or errors)
        violations = []
        found_items = {}
        
        has_netlist_path = any(item['type'] == 'netlist_path' for item in items)
        has_spef_status = any(item['type'] in ['spef_status', 'spef_path'] for item in items)
        
        if has_netlist_path and has_spef_status:
            # Build found_items for successful checks
            for item in items:
                if item['type'] in ['netlist_path', 'spef_status', 'spef_path', 
                                   'netlist_version', 'spef_version', 'parasitics_mode',
                                   'top_design', 'tool_version']:
                    found_items[item['name']] = {
                        'name': item['name'],
                        'line_number': item.get('line_number', 0),
                        'file_path': item.get('file_path', 'N/A')
                    }
        else:
            if not has_netlist_path:
                violations.append('Netlist file path not found in log')
            if not has_spef_status:
                violations.append('SPEF status not found in log')
        
        # Add errors to violations
        violations.extend(errors)
        
        # Separate waived/unwaived violations
        waived_items = {}
        unwaived_items = []
        
        for violation in violations:
            if self.match_waiver_entry(violation, waive_dict):
                waived_items[violation] = {
                    'name': violation,
                    'line_number': 0,
                    'file_path': 'N/A'
                }
            else:
                unwaived_items.append(violation)
        
        # Find unused waivers
        used_names = set(waived_items.keys())
        unused_waivers = [name for name in waive_dict.keys() if name not in used_names]
        
        # Use template helper for automatic output formatting (waivers.value>0)
        # Type 4: Use TYPE1_4 reason (emphasize "found/not found")
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
            waived_base_reason=self.WAIVED_BASE_REASON,
            unused_waiver_reason=self.UNUSED_WAIVER_REASON
        )


# =========================================================================
# Entry Point
# =========================================================================

def main():
    """Main entry point."""
    checker = Check_10_0_0_00()
    checker.init_checker(Path(__file__))
    result = checker.execute_check()
    checker.write_output(result)
    return 0 if result.is_pass else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())