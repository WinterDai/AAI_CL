################################################################################
# Script Name: IMP-12-0-0-32.py
#
# Purpose:
#   Confirm no ERROR message in DFM/FLT log files. (for SEC process, for others fill N/A)
#
# Logic:
#   - Parse Pegasus DFM/FLT log files to extract ERROR messages
#   - Extract ERROR source identifiers (Worker ID, cell name, error code)
#   - Verify no ERROR messages exist in verification logs
#   - Support waiver for known ERROR sources (workers, cells, error codes)
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
# Author: Jingyu Wang
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
class Check_12_0_0_32(InputFileParserMixin, OutputBuilderMixin, WaiverHandlerMixin, BaseChecker):
    """
    IMP-12-0-0-32: Confirm no ERROR message in DFM/FLT log files. (for SEC process, for others fill N/A)
    
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
    FOUND_DESC_TYPE1_4 = "No ERROR messages found in Pegasus verification logs"
    MISSING_DESC_TYPE1_4 = "ERROR messages detected in Pegasus verification logs"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_DESC_TYPE2_3 = "All monitored ERROR patterns validated (0 errors found)"
    MISSING_DESC_TYPE2_3 = "Monitored ERROR patterns detected in verification logs"
    
    # All Types (waiver description unified)
    WAIVED_DESC = "ERROR messages waived per verification team approval"
    
    # ⭐ REASON CONSTANTS - Split by Type semantics (API-025)
    # ALL Types pass found_reason/missing_reason, but use different constants
    
    # Type 1/4: Boolean checks - emphasize "found/not found" (existence)
    FOUND_REASON_TYPE1_4 = "Pegasus DFM/FLT verification completed without errors"
    MISSING_REASON_TYPE1_4 = "Pegasus DFM/FLT verification encountered critical errors"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_REASON_TYPE2_3 = "Monitored ERROR patterns not detected in verification logs"
    MISSING_REASON_TYPE2_3 = "Monitored ERROR patterns found in verification logs"
    
    # Waiver-related (Type 3/4 only)
    WAIVED_BASE_REASON = "Pegasus verification errors waived as known issues"
    UNUSED_WAIVER_REASON = "Waiver not matched - no corresponding ERROR found in logs"
    
    def __init__(self):
        """Initialize the checker."""
        super().__init__(
            check_module="12.0_PHYSICAL_VERIFICATION_CHECK",
            item_id="IMP-12-0-0-32",
            item_desc="Confirm no ERROR message in DFM/FLT log files. (for SEC process, for others fill N/A)"
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
        Parse Pegasus DFM/FLT log files to extract ERROR messages.
        
        Extracts ERROR messages with multiple formats:
        - Standard ERROR: prefix
        - [ERROR] bracketed format
        - Error: with Worker context
        - ERROR with error codes (ERROR (CODE):)
        
        Returns:
            Dict with parsed data:
            - 'items': List[Dict] - ERROR messages with source identifiers
            - 'metadata': Dict - File metadata (completion status, warnings)
            - 'errors': List - Parsing errors
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
        
        # ERROR pattern regexes (multiple formats)
        error_patterns = [
            # Standard ERROR: format
            re.compile(r'^ERROR:\s*(.+)$', re.IGNORECASE),
            # [ERROR] bracketed format
            re.compile(r'^\[ERROR\]\s*(.+)$', re.IGNORECASE),
            # Error: with Worker context
            re.compile(r'^Error:\s*(.+?)\s*\(Worker\s+(\d+)\)', re.IGNORECASE),
            # ERROR with error code
            re.compile(r'^ERROR\s*\(([A-Z]+-\d+)\):\s*(.+)$', re.IGNORECASE),
            # Pattern 5: INPUT ERROR format
            re.compile(r'^\[INPUT ERROR\]\s*(.+)$', re.IGNORECASE),
        ]
        
        # Worker ID extraction pattern
        worker_pattern = re.compile(r'\(Worker\s+(\d+)\)', re.IGNORECASE)
        # Cell name extraction pattern
        cell_pattern = re.compile(r'cell\s+"([^"]+)"', re.IGNORECASE)
        # Error code extraction pattern
        code_pattern = re.compile(r'ERROR\s*\(([A-Z]+-\d+)\)', re.IGNORECASE)
        
        # 3. Parse each input file for ERROR messages
        for file_path in valid_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line_num, line in enumerate(f, 1):
                        line_stripped = line.strip()
                        
                        # Check for ERROR messages
                        error_found = False
                        error_message = None
                        
                        for pattern in error_patterns:
                            match = pattern.search(line_stripped)
                            if match:
                                error_found = True
                                # Extract error message (handle different group structures)
                                if len(match.groups()) == 1:
                                    error_message = match.group(1).strip()
                                elif len(match.groups()) == 2:
                                    # Could be Worker context or error code
                                    if 'Worker' in line:
                                        error_message = match.group(1).strip()
                                    else:
                                        # Error code format
                                        error_message = match.group(2).strip()
                                break
                        
                        if error_found and error_message:
                            # Extract source identifier (Worker ID, cell name, or error code)
                            source = None
                            
                            # Try Worker ID
                            worker_match = worker_pattern.search(line_stripped)
                            if worker_match:
                                source = f"Worker {worker_match.group(1)}"
                            
                            # Try cell name
                            if not source:
                                cell_match = cell_pattern.search(line_stripped)
                                if cell_match:
                                    source = cell_match.group(1)
                            
                            # Try error code
                            if not source:
                                code_match = code_pattern.search(line_stripped)
                                if code_match:
                                    source = code_match.group(1)
                            
                            # Default source if none found
                            if not source:
                                source = f"{file_path.name}:line {line_num}"
                            
                            items.append({
                                'name': error_message,
                                'line_number': line_num,
                                'file_path': str(file_path),
                                'line_content': line_stripped,
                                'source': source,
                                'type': 'ERROR'
                            })
                        
                        # Extract completion status for metadata
                        if 'Pegasus finished normally' in line_stripped:
                            metadata['completion_status'] = 'normal'
                        elif 'ERROR: Run completed with errors' in line_stripped:
                            metadata['completion_status'] = 'error'
                        elif 'Pegasus failed' in line_stripped or 'Pegasus aborted' in line_stripped:
                            metadata['completion_status'] = 'failed'
                        
            except Exception as e:
                errors.append(f"Error parsing {file_path}: {str(e)}")
        
        # 4. Store frequently reused data on self
        self._parsed_items = items
        self._metadata = metadata
        
        return {
            'items': items,
            'metadata': metadata,
            'errors': errors
        }
    # Helper Methods (Optional - Add as needed)
    

    # =========================================================================
    # Type 1: Boolean Check

    def _execute_type1(self) -> CheckResult:
        """
        Type 1: Boolean check without waiver support.

        Verifies no ERROR messages exist in Pegasus DFM/FLT log files.
        PASS if no ERROR messages found in any log file.
        FAIL if any ERROR message detected (regardless of error type or source).
        """
        violations = self._type1_core_logic()

        # For Type 1, found_items can be empty (no files are "clean" when ANY error exists)
        # Just pass violations as missing_items
        found_items = {}

        return self.build_complete_output(
            found_items=found_items,
            missing_items=violations,
            found_desc=self.FOUND_DESC_TYPE1_4,
            missing_desc=self.MISSING_DESC_TYPE1_4,
            found_reason=self.FOUND_REASON_TYPE1_4,
            missing_reason=self.MISSING_REASON_TYPE1_4
        )

    def _type1_core_logic(self) -> dict[str, dict]:
        """
        Core Type 1 boolean check logic (shared by Type 1 and Type 4).

        Scans Pegasus DFM/FLT log files for ERROR messages and extracts:
        - Error message text
        - Source identifier (Worker ID, cell name, error code)
        - Line number and file path

        Returns:
            Dict of violations: {error_key: {'line_number': ..., 'file_path': ..., 'reason': ...}}
            Empty dict if no ERROR messages found.
        """
        data = self._parse_input_files()
        items = data.get('items', [])

        violations = {}

        # Each item represents an ERROR message with extracted source
        for item in items:
            error_msg = item.get('name', 'Unknown error')
            source = item.get('source', 'Unknown source')
            line_number = item.get('line_number', 0)
            file_path = item.get('file_path', 'N/A')

            # Create unique key combining error message and source
            error_key = f"{error_msg} (Source: {source})"

            violations[error_key] = {
                'line_number': line_number,
                'file_path': file_path,
                'reason': self.MISSING_REASON_TYPE1_4
            }

        return violations

    # =========================================================================
    # Type 4: Boolean Check with Waiver Logic

    def _execute_type4(self) -> CheckResult:
        """
        Type 4: Boolean check with waiver support (reuses Type 1 core logic).

        Same boolean check as Type 1 (scans ALL ERROR messages), plus waiver classification:
        1. Scan for ANY ERROR message in log files (no pattern filtering)
        2. Extract source objects from all ERRORs (Worker ID, cell name, error code)
        3. Match source objects against waive_items.name using regex
        4. Classify as:
           - Unwaived violations → ERROR (FAIL)
           - Waived violations → INFO with [WAIVER] tag
           - Unused waivers → WARN with [WAIVER] tag

        PASS if all violations are waived.
        """
        violations = self._type1_core_logic()

        # For Type 4, found_items can be empty (no pattern-specific "found" items)
        found_items = {}

        # Parse waiver items from configuration
        waivers = self.item_data.get('waivers', {})
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        waived_items = {}
        missing_items = {}
        used_waivers = set()

        # Match violations against waivers
        # Waiver matching supports TWO strategies:
        # 1. Match SOURCE identifier (Worker ID, cell name, error code)
        # 2. Match FULL ERROR MESSAGE using regex (fallback if source match fails)
        for viol_name, viol_data in violations.items():
            # Extract source and error message from violation key
            # Format: "error_msg (Source: source_id)"
            source_match = re.search(r'\(Source:\s*(.+?)\)$', viol_name)
            source_id = source_match.group(1) if source_match else ''
            
            # Extract error message (without Source suffix)
            error_msg_match = re.search(r'^(.+?)\s*\(Source:', viol_name)
            error_msg = error_msg_match.group(1).strip() if error_msg_match else viol_name

            # Try matching source first (preferred method)
            matched_waiver = self.match_waiver_entry(source_id, waive_dict) if source_id else None
            
            # If source match fails, try matching full error message (fallback)
            if not matched_waiver:
                matched_waiver = self.match_waiver_entry(error_msg, waive_dict)
            
            if matched_waiver:
                # Store matched waiver name in metadata for reason lookup
                viol_data_with_waiver = viol_data.copy()
                viol_data_with_waiver['matched_waiver'] = matched_waiver
                waived_items[viol_name] = viol_data_with_waiver
                used_waivers.add(matched_waiver)
            else:
                missing_items[viol_name] = viol_data

        unused_waivers = {w: {'line_number': 0, 'file_path': 'N/A'} for w in waive_dict.keys() if w not in used_waivers}

        # Create waive_dict_by_display: map error message keys to waiver reasons
        # This allows output_builder to find the correct reason for each waived item
        waive_dict_by_display = {}
        for error_msg_key, error_data in waived_items.items():
            matched_waiver_name = error_data.get('matched_waiver', '')
            if matched_waiver_name and matched_waiver_name in waive_dict:
                waive_dict_by_display[error_msg_key] = waive_dict[matched_waiver_name]

        return self.build_complete_output(
            found_items=found_items,
            missing_items=missing_items,
            waived_items=waived_items,
            unused_waivers=unused_waivers,
            waive_dict=waive_dict_by_display,
            found_desc=self.FOUND_DESC_TYPE1_4,
            missing_desc=self.MISSING_DESC_TYPE1_4,
            waived_desc=self.WAIVED_DESC,
            found_reason=self.FOUND_REASON_TYPE1_4,
            missing_reason=self.MISSING_REASON_TYPE1_4,
            waived_base_reason=self.WAIVED_BASE_REASON,
            unused_waiver_reason=self.UNUSED_WAIVER_REASON
        )

    # =========================================================================
    # Type 2: Value Check

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

    def _type2_core_logic(self) -> tuple[dict[str, dict], dict[str, dict]]:
        """
        Core Type 2 pattern matching logic (shared by Type 2 and Type 3).

        Searches for ERROR messages matching pattern_items in Pegasus DFM/FLT log files.
        This is a violation check: finding monitored ERROR patterns means FAIL.

        Returns:
            Tuple of (found_items, missing_items)
            - found_items: {error_msg: {'line_number': ..., 'file_path': ..., 'source': ...}}
                          ERROR messages that matched pattern_items (violations found)
            - missing_items: {pattern: {'line_number': 0, 'file_path': 'N/A', 'reason': ...}}
                            Patterns from pattern_items that were not found (clean)
        """
        data = self._parse_input_files()
        error_messages = data.get('items', [])  # List of ERROR messages from logs

        requirements = self.item_data.get('requirements', {})
        pattern_items = requirements.get('pattern_items', [])

        found_items = {}      # ERROR messages matching patterns (violations)
        missing_items = {}    # Patterns not found (clean state)

        # Check each pattern against ERROR messages
        for pattern in pattern_items:
            pattern_matched = False

            # Search for ERROR messages matching this pattern
            for error in error_messages:
                error_msg = error.get('name', '')

                # Use regex matching for pattern flexibility
                try:
                    if re.search(pattern, error_msg, re.IGNORECASE):
                        # Extract source identifier (Worker ID, cell name, error code)
                        source = error.get('source', '')
                        if not source:
                            source = self._extract_error_source(error_msg)

                        # Create unique key with source info
                        item_key = f"{error_msg} (Source: {source})" if source else error_msg

                        found_items[item_key] = {
                            'line_number': error.get('line_number', 0),
                            'file_path': error.get('file_path', 'N/A'),
                            'source': source,
                            'pattern': pattern
                        }
                        pattern_matched = True
                        break  # One match per pattern is sufficient
                except re.error:
                    # If regex fails, fall back to substring match
                    if pattern.lower() in error_msg.lower():
                        source = error.get('source', '')
                        if not source:
                            source = self._extract_error_source(error_msg)
                        item_key = f"{error_msg} (Source: {source})" if source else error_msg

                        found_items[item_key] = {
                            'line_number': error.get('line_number', 0),
                            'file_path': error.get('file_path', 'N/A'),
                            'source': source,
                            'pattern': pattern
                        }
                        pattern_matched = True
                        break

            # If pattern not found, add to missing_items (clean state)
            if not pattern_matched:
                missing_items[pattern] = {
                    'line_number': 0,
                    'file_path': 'N/A',
                    'reason': f'Pattern "{pattern}" not found'
                }

        return found_items, missing_items

    # =========================================================================
    # Type 3: Value Check with Waiver Logic

    def _execute_type3(self) -> CheckResult:
        """Type 3: Pattern/value check with waiver support (reuses Type 2 core logic)."""
        # Step 1: Get found/missing items using Type 2's core logic
        found_items_base, violations = self._type2_core_logic()

        # Step 2: Parse waiver configuration
        waivers = self.item_data.get('waivers', {})
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)

        # Step 3: Split violations into waived and unwaived
        found_items = {}
        waived_items = {}
        missing_items = {}
        used_waivers = set()

        # Process found_items_base (ERROR messages found - these are violations)
        for error_msg_key, error_data in found_items_base.items():
            source = error_data.get('source', '')
            
            # Extract clean error message (without Source suffix)
            # Format: "error_msg (Source: source_id)"
            clean_msg_match = re.search(r'^(.+?)\s*\(Source:', error_msg_key)
            clean_msg = clean_msg_match.group(1).strip() if clean_msg_match else error_msg_key

            # Match waiver using TWO strategies:
            # 1. Match SOURCE identifier (Worker ID, cell name, error code) - preferred
            # 2. Match FULL ERROR MESSAGE using regex - fallback
            matched_waiver = None
            if source:
                matched_waiver = self.match_waiver_entry(source, waive_dict)
            
            # If source match fails, try matching full error message
            if not matched_waiver:
                matched_waiver = self.match_waiver_entry(clean_msg, waive_dict)

            if matched_waiver:
                # ERROR is waived - store matched waiver name in metadata
                error_data_with_waiver = error_data.copy()
                error_data_with_waiver['matched_waiver'] = matched_waiver
                waived_items[error_msg_key] = error_data_with_waiver
                used_waivers.add(matched_waiver)
            else:
                # ERROR not waived - this is a real violation
                missing_items[error_msg_key] = error_data

        # Process violations dict (patterns not found - these are clean)
        # In Type 3, clean patterns go to found_items
        for pattern, pattern_data in violations.items():
            found_items[pattern] = pattern_data

        # Step 4: Find unused waivers
        unused_waivers = {w: {'line_number': 0, 'file_path': 'N/A'} for w in waive_dict.keys() if w not in used_waivers}

        # Create waive_dict_by_display: map error message keys to waiver reasons
        # This allows output_builder to find the correct reason for each waived item
        waive_dict_by_display = {}
        for error_msg_key, error_data in waived_items.items():
            matched_waiver_name = error_data.get('matched_waiver', '')
            if matched_waiver_name and matched_waiver_name in waive_dict:
                waive_dict_by_display[error_msg_key] = waive_dict[matched_waiver_name]

        # Step 5: Build output
        return self.build_complete_output(
            found_items=found_items,
            missing_items=missing_items,
            waived_items=waived_items,
            unused_waivers=unused_waivers,
            waive_dict=waive_dict_by_display,
            found_desc=self.FOUND_DESC_TYPE2_3,
            missing_desc=self.MISSING_DESC_TYPE2_3,
            waived_desc=self.WAIVED_DESC,
            found_reason=self.FOUND_REASON_TYPE2_3,
            missing_reason=self.MISSING_REASON_TYPE2_3,
            waived_base_reason=self.WAIVED_BASE_REASON,
            unused_waiver_reason=self.UNUSED_WAIVER_REASON
        )

    def _extract_error_source(self, error_msg: str) -> str:
        """
        Extract error source identifier from ERROR message.

        Searches for:
        - Worker ID: (Worker N) pattern
        - Cell name: cell "name" or Cell name is referenced patterns
        - Error code: (CODE-NNNN) pattern

        Args:
            error_msg: ERROR message text

        Returns:
            Source identifier string (Worker ID, cell name, or error code)
            Empty string if no source found
        """
        # Try to extract Worker ID
        worker_match = re.search(r'\(Worker\s+(\d+)\)', error_msg, re.IGNORECASE)
        if worker_match:
            return f"Worker {worker_match.group(1)}"

        # Try to extract cell name from 'cell "name"' pattern
        cell_match = re.search(r'cell\s+"([^"]+)"', error_msg, re.IGNORECASE)
        if cell_match:
            return cell_match.group(1)

        # Try to extract cell name from 'Cell name is referenced' pattern
        cell_ref_match = re.search(r'Cell\s+(\S+)\s+is\s+referenced', error_msg, re.IGNORECASE)
        if cell_ref_match:
            return cell_ref_match.group(1)

        # Try to extract error code
        code_match = re.search(r'\(([A-Z]+-\d+)\)', error_msg)
        if code_match:
            return code_match.group(1)

        return ''
    def _matches_waiver(self, item: str, waive_patterns: List[str]) -> bool:
        """
        Check if item matches any waiver pattern.
        
        TODO: Optional - Implement waiver matching logic
        
        Args:
            item: Item to check
            waive_patterns: List of waiver patterns
            
        Returns:
            True if item matches any pattern
        """
        for pattern in waive_patterns:
            # Support wildcards
            if '*' in pattern:
                regex_pattern = pattern.replace('*', '.*')
                if re.search(regex_pattern, item, re.IGNORECASE):
                    return True
            # Exact match
            elif pattern.lower() == item.lower():
                return True
        return False


# =========================================================================
# Entry Point
# =========================================================================

def main():
    """Main entry point."""
    checker = Check_12_0_0_32()
    checker.init_checker(Path(__file__))
    result = checker.execute_check()
    checker.write_output(result)
    return 0 if result.is_pass else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())