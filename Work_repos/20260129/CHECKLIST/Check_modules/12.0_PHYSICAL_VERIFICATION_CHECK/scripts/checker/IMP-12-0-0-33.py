################################################################################
# Script Name: IMP-12-0-0-33.py
#
# Purpose:
#   Confirm all Warning message in DFM/FLT log files can be waived. (for SEC process, for others fill N/A)
#
# Logic:
#   - Parse Pegasus DFM/FLT verification log files to extract WARNING/[WARN]/Warning messages
#   - Extract warning codes (e.g., GDR-00003), worker IDs, rule names, and message content
#   - Verify all warnings are waivable types for SEC process (worker issues, label conflicts, GDR warnings)
#   - Support waiver for specific warning instances by object name (worker ID, rule name, net name, cell name)
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
class Check_12_0_0_33(InputFileParserMixin, OutputBuilderMixin, WaiverHandlerMixin, BaseChecker):
    """
    IMP-12-0-0-33: Confirm all Warning message in DFM/FLT log files can be waived. (for SEC process, for others fill N/A)
    
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
    FOUND_DESC_TYPE1_4 = "No WARNING messages found in Pegasus verification logs"
    MISSING_DESC_TYPE1_4 = "WARNING messages detected in Pegasus verification logs"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_DESC_TYPE2_3 = "All monitored WARNING patterns validated (0 warnings found)"
    MISSING_DESC_TYPE2_3 = "Monitored WARNING patterns detected in verification logs"
    
    # All Types (waiver description unified)
    WAIVED_DESC = "WARNING messages waived per verification team approval"
    
    # ⭐ REASON CONSTANTS - Split by Type semantics (API-025)
    # ALL Types pass found_reason/missing_reason, but use different constants
    
    # Type 1/4: Boolean checks - emphasize "found/not found" (existence)
    FOUND_REASON_TYPE1_4 = "Pegasus DFM/FLT verification completed without warnings"
    MISSING_REASON_TYPE1_4 = "Pegasus DFM/FLT verification encountered warnings"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_REASON_TYPE2_3 = "Monitored WARNING patterns not detected in verification logs"
    MISSING_REASON_TYPE2_3 = "Monitored WARNING patterns found in verification logs"
    
    # Waiver-related (Type 3/4 only)
    WAIVED_BASE_REASON = "Pegasus verification warnings waived as known issues"
    UNUSED_WAIVER_REASON = "Waiver not matched - no corresponding WARNING found in logs"
    
    def __init__(self):
        """Initialize the checker."""
        super().__init__(
            check_module="12.0_PHYSICAL_VERIFICATION_CHECK",
            item_id="IMP-12-0-0-33",
            item_desc="Confirm all Warning message in DFM/FLT log files can be waived. (for SEC process, for others fill N/A)"
        )
        # Custom member variables for parsed data
        self._parsed_items: List[Dict[str, Any]] = []
        self._metadata: Dict[str, str] = {}
        self._warning_messages: List[Dict[str, Any]] = []
    
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
        Parse Pegasus DFM/FLT verification log files to extract WARNING messages.
        
        Extracts:
        - WARNING: messages (standard format)
        - [WARN] messages (alternative format)
        - Warning: messages (capitalized format)
        - WARNING: CODE (multi-line format with code on next line)
        - Associated context: worker IDs, rule names, net names, cell names
        
        Returns:
            Dict with parsed data:
            - 'items': List[Dict] - Warning messages with metadata
            - 'metadata': Dict - File metadata (log file names)
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
        
        # WARNING pattern regexes (multiple formats)
        warning_patterns = [
            # Standard WARNING: format
            re.compile(r'^WARNING:\s*(.+)$', re.IGNORECASE),
            # [WARN] bracketed format
            re.compile(r'^\[WARN\]\s*(.+)$', re.IGNORECASE),
            # Warning: with Worker context
            re.compile(r'^Warning:\s*(.+?)\s*\(Worker\s+(\d+)\)', re.IGNORECASE),
            # WARNING with warning code
            re.compile(r'^WARNING\s*\(([A-Z]+-\d+)\):\s*(.+)$', re.IGNORECASE),
            # Pattern 5: INPUT WARNING format (if exists)
            re.compile(r'^\[INPUT WARNING\]\s*(.+)$', re.IGNORECASE),
        ]
        
        # Worker ID extraction pattern
        worker_pattern = re.compile(r'Worker\s+(\d+)', re.IGNORECASE)
        # Cell name extraction pattern
        cell_pattern = re.compile(r'[Cc]ell\s+"([^"]+)"', re.IGNORECASE)
        # Warning code extraction pattern
        code_pattern = re.compile(r'(GDR-\d+|[A-Z]+-\d+)', re.IGNORECASE)
        
        # 3. Parse each input file for WARNING messages
        for file_path in valid_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line_num, line in enumerate(f, 1):
                        line_stripped = line.strip()
                        
                        # Check for WARNING messages
                        warning_found = False
                        warning_message = None
                        
                        for pattern in warning_patterns:
                            match = pattern.search(line_stripped)
                            if match:
                                warning_found = True
                                # Extract warning message (handle different group structures)
                                if len(match.groups()) == 1:
                                    warning_message = match.group(1).strip()
                                elif len(match.groups()) == 2:
                                    # Could be Worker context or warning code
                                    if 'Worker' in line:
                                        warning_message = match.group(1).strip()
                                    else:
                                        # Warning code format
                                        warning_message = match.group(2).strip()
                                break
                        
                        if warning_found and warning_message:
                            # Extract source identifier (Worker ID, cell name, or warning code)
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
                            
                            # Try warning code
                            if not source:
                                code_match = code_pattern.search(line_stripped)
                                if code_match:
                                    source = code_match.group(1)
                            
                            # Try extracting from file path (line number context)
                            if not source:
                                source = f"{Path(file_path).name}:line {line_num}"
                            
                            items.append({
                                'name': warning_message,
                                'line_number': line_num,
                                'file_path': str(file_path),
                                'type': 'WARNING',
                                'source': source
                            })
                
                metadata[str(file_path)] = {
                    'total_warnings': len([i for i in items if i['file_path'] == str(file_path)])
                }
                
            except Exception as e:
                errors.append(f"Error parsing {file_path}: {str(e)}")
        
        # 4. Store frequently reused data on self
        self._parsed_items = items
        self._warning_messages = items
        self._metadata = metadata
        
        return {
            'items': items,
            'metadata': metadata,
            'errors': errors
        }
    

    # =========================================================================
    # Type 1: Boolean Check

    def _execute_type1(self) -> CheckResult:
        """
        Type 1: Boolean check without waiver support.

        Verifies no WARNING messages exist in Pegasus DFM/FLT log files.
        PASS if no WARNING messages found in any log file.
        FAIL if any WARNING message detected (regardless of warning type or source).
        """
        violations = self._type1_core_logic()

        # Build found_items from clean log files (files with no warnings)
        data = self._parse_input_files()
        clean_files = data.get('clean_files', [])

        found_items = {}
        for clean_file in clean_files:
            file_name = clean_file['name']
            found_items[file_name] = {
                'name': file_name,
                'line_number': 0,
                'file_path': clean_file.get('file_path', 'N/A')
            }

        missing_items = list(violations.keys()) if violations else []

        return self.build_complete_output(
            found_items=found_items,
            missing_items=missing_items,
            found_desc=self.FOUND_DESC_TYPE1_4,
            missing_desc=self.MISSING_DESC_TYPE1_4,
            found_reason=self.FOUND_REASON_TYPE1_4,
            missing_reason=self.MISSING_REASON_TYPE1_4
        )

    def _type1_core_logic(self) -> dict[str, dict]:
        """
        Core Type 1 boolean check logic (shared by Type 1 and Type 4).

        Parses Pegasus DFM/FLT log files to extract WARNING messages.
        Detects warnings from multiple sources:
        - Worker process warnings (e.g., "Worker 1 killed by external signal")
        - GDR warnings (e.g., "GDR-00003: same label for multiple nets")
        - General warnings (e.g., "Invalid option")

        Returns:
            Dict of violations: {warning_key: {'line_number': ..., 'file_path': ..., 'reason': ...}}
            Empty dict if no warnings found (all checks pass).
        """
        data = self._parse_input_files()
        warnings = data.get('items', [])

        violations = {}

        # Each warning is a violation in Type 1 (no pattern filtering)
        for warning in warnings:
            # Create unique key from warning message and source
            warning_msg = warning.get('name', '')
            warning_source = warning.get('source', 'Unknown')

            # Use message + source as unique identifier
            warning_key = f"{warning_msg} (Source: {warning_source})"

            violations[warning_key] = {
                'name': warning_key,
                'line_number': warning.get('line_number', 0),
                'file_path': warning.get('file_path', 'N/A'),
                'reason': self.MISSING_REASON_TYPE1_4
            }

        return violations

    # =========================================================================
    # Type 4: Boolean Check with Waiver Logic

    def _execute_type4(self) -> CheckResult:
        """
        Type 4: Boolean check with waiver support (reuses Type 1 core logic).

        Detects ANY WARNING message (no pattern filtering), then applies waiver logic:
        - Matches found warnings against waive_items (using dual matching strategy)
        - Unwaived warnings → ERROR
        - Waived warnings → INFO with [WAIVER] tag
        - Unused waivers → WARN with [WAIVER] tag

        PASS if all warnings are waived.

        Waiver Matching Strategy:
        1. Source-based matching: Match against warning source (Worker ID, GDR code, etc.)
        2. Full message regex: Match against complete warning message
        """
        violations = self._type1_core_logic()

        # Build found_items from clean log files (files with no warnings)
        data = self._parse_input_files()
        clean_files = data.get('clean_files', [])

        found_items = {}
        for clean_file in clean_files:
            file_name = clean_file['name']
            found_items[file_name] = {
                'name': file_name,
                'line_number': 0,
                'file_path': clean_file.get('file_path', 'N/A')
            }

        waive_items_raw = self.item_data.get('waivers', {}).get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw=waive_items_raw)
        waived_items = {}
        missing_items = {}
        used_waivers = set()

        for viol_name, viol_data in violations.items():
            # Dual waiver matching: Try source first, then full message
            # Extract source and error message from violation key
            source_match = re.search(r'\(Source:\s*(.+?)\)$', viol_name)
            error_msg_match = re.search(r'^(.+?)\s*\(Source:', viol_name)
            
            source_id = source_match.group(1) if source_match else None
            error_msg = error_msg_match.group(1) if error_msg_match else viol_name
            
            # Strategy 1: Try matching against source (preferred)
            matched_waiver = self.match_waiver_entry(source_id, waive_dict) if source_id else None
            
            # Strategy 2: Fallback to full message matching
            if not matched_waiver:
                matched_waiver = self.match_waiver_entry(error_msg, waive_dict)
            
            # Store matched waiver in metadata for reason lookup
            error_data_with_waiver = viol_data.copy()
            error_data_with_waiver['matched_waiver'] = matched_waiver
            
            if matched_waiver:
                waived_items[viol_name] = error_data_with_waiver
                used_waivers.add(matched_waiver)
            else:
                missing_items[viol_name] = viol_data

        unused_waivers = [w for w in waive_dict.keys() if w not in used_waivers]
        
        # Create waive_dict_by_display mapping for correct reason display
        waive_dict_by_display = {}
        for warning_msg_key, warning_data in waived_items.items():
            matched_waiver_name = warning_data.get('matched_waiver', '')
            if matched_waiver_name and matched_waiver_name in waive_dict:
                waive_dict_by_display[warning_msg_key] = waive_dict[matched_waiver_name]

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
            missing_items=list(missing_items.keys()) if isinstance(missing_items, dict) else missing_items,
            found_desc=self.FOUND_DESC_TYPE2_3,
            missing_desc=self.MISSING_DESC_TYPE2_3,
            found_reason=self.FOUND_REASON_TYPE2_3,
            missing_reason=self.MISSING_REASON_TYPE2_3
        )

    def _type2_core_logic(self) -> tuple[dict[str, dict], dict[str, dict]]:
        """
        Core Type 2 pattern matching logic (shared by Type 2 and Type 3).

        Searches for WARNING messages matching monitored patterns in Pegasus DFM/FLT logs.
        This is a violation check: finding monitored patterns means FAIL.

        Returns:
            Tuple of (found_items, missing_items)
            - found_items: {pattern: {'line_number': ..., 'file_path': ...}} - patterns NOT found (clean)
            - missing_items: {warning_msg: {'line_number': ..., 'file_path': ..., 'reason': ...}} - warnings found (violations)
        """
        data = self._parse_input_files()
        items = data.get('items', [])  # WARNING messages found in logs

        requirements = self.item_data.get('requirements', {})
        pattern_items = requirements.get('pattern_items', [])

        # For this checker: found_items = patterns NOT detected (clean/PASS)
        #                   missing_items = warnings detected (violations/FAIL)
        found_items = {}
        missing_items = {}

        # Track which patterns were matched by warnings
        matched_patterns = set()

        # Check each warning against all patterns
        for item in items:
            warning_msg = item.get('name', '')
            warning_full = item.get('full_message', warning_msg)

            # Try to match warning against any pattern
            for pattern in pattern_items:
                try:
                    if re.search(pattern, warning_full, re.IGNORECASE):
                        # Warning matches pattern - this is a violation
                        matched_patterns.add(pattern)

                        # Create unique key for this warning instance
                        warning_key = f"{warning_msg} (matches: {pattern})"

                        missing_items[warning_key] = {
                            'line_number': item.get('line_number', 0),
                            'file_path': item.get('file_path', 'N/A'),
                            'reason': f'Monitored WARNING pattern found: {pattern}'
                        }
                        break  # One pattern match per warning is enough
                except re.error:
                    # If regex fails, try simple substring match
                    if pattern.lower() in warning_full.lower():
                        matched_patterns.add(pattern)
                        warning_key = f"{warning_msg} (matches: {pattern})"
                        missing_items[warning_key] = {
                            'line_number': item.get('line_number', 0),
                            'file_path': item.get('file_path', 'N/A'),
                            'reason': f'Monitored WARNING pattern found: {pattern}'
                        }
                        break

        # Patterns NOT matched = clean (found_items for Type 2)
        for pattern in pattern_items:
            if pattern not in matched_patterns:
                found_items[pattern] = {
                    'line_number': 0,
                    'file_path': 'N/A'
                }

        return found_items, missing_items

    # =========================================================================
    # Type 3: Value Check with Waiver Logic

    def _execute_type3(self) -> CheckResult:
        """Type 3: Pattern/value check with waiver support (reuses Type 2 core logic)."""
        # Step 1: Get found/missing items using Type 2's core logic
        found_items_base, violations = self._type2_core_logic()

        # Step 2: Parse waiver configuration
        waive_items_raw = self.item_data.get('waivers', {}).get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw=waive_items_raw)

        # Step 3: Initialize result collections
        found_items = {}
        waived_items = {}
        missing_items = {}
        used_waivers = set()

        # Step 4: Process found_items_base (patterns not detected - no waiver needed)
        for item_name, item_data in found_items_base.items():
            found_items[item_name] = item_data

        # Step 5: Process violations with waiver matching
        # Violations are warnings that matched monitored patterns
        for viol_name, viol_data in violations.items():
            # Dual waiver matching: Try source first, then full message
            # Extract source and error message from violation key
            source_match = re.search(r'\(Source:\s*(.+?)\)$', viol_name)
            error_msg_match = re.search(r'^(.+?)\s*\(Source:', viol_name)
            
            source_id = source_match.group(1) if source_match else None
            error_msg = error_msg_match.group(1) if error_msg_match else viol_name
            
            # Strategy 1: Try matching against source (preferred)
            matched_waiver = self.match_waiver_entry(source_id, waive_dict) if source_id else None
            
            # Strategy 2: Fallback to full message matching
            if not matched_waiver:
                matched_waiver = self.match_waiver_entry(error_msg, waive_dict)
            
            # Store matched waiver in metadata for reason lookup
            warning_data_with_waiver = viol_data.copy()
            warning_data_with_waiver['matched_waiver'] = matched_waiver
            
            # Categorize violation
            if matched_waiver:
                waived_items[viol_name] = warning_data_with_waiver
                used_waivers.add(matched_waiver)
            else:
                missing_items[viol_name] = viol_data

        # Step 6: Find unused waivers
        unused_waivers = [w for w in waive_dict.keys() if w not in used_waivers]
        
        # Step 7: Create waive_dict_by_display mapping for correct reason display
        waive_dict_by_display = {}
        for warning_msg_key, warning_data in waived_items.items():
            matched_waiver_name = warning_data.get('matched_waiver', '')
            if matched_waiver_name and matched_waiver_name in waive_dict:
                waive_dict_by_display[warning_msg_key] = waive_dict[matched_waiver_name]

        # Step 8: Build output
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

    def _extract_warning_source(self, warning_text: str, full_line: str = '') -> str:
        """
        Extract source identifier from warning message.
        
        Extracts:
        - Worker IDs (e.g., "Worker 1")
        - Rule names (e.g., "floating.nxwell_float")
        - Net names (e.g., "net x")
        - Cell names (e.g., "Cell pm26")
        - Warning codes (e.g., "GDR-00003")
        
        Args:
            warning_text: The warning message text
            full_line: The full line containing the warning
            
        Returns:
            Source identifier string
        """
        # Check for worker ID
        worker_match = re.search(r'Worker\s+(\d+)', warning_text)
        if worker_match:
            return f"Worker {worker_match.group(1)}"
        
        # Check for rule name
        rule_match = re.search(r'rule\s+([a-zA-Z0-9_.]+)', warning_text)
        if rule_match:
            return rule_match.group(1)
        
        # Check for net name
        net_match = re.search(r'net\s+"?([a-zA-Z0-9_]+)"?', warning_text)
        if net_match:
            return f"net {net_match.group(1)}"
        
        # Check for cell name
        cell_match = re.search(r'[Cc]ell\s+"?([a-zA-Z0-9_]+)"?', warning_text)
        if cell_match:
            return f"Cell {cell_match.group(1)}"
        
        # Check for warning code (e.g., GDR-00003)
        code_match = re.search(r'^([A-Z]+-\d+)', warning_text)
        if code_match:
            return code_match.group(1)
        
        # Default: return first 50 chars of warning text
        return warning_text[:50] if len(warning_text) > 50 else warning_text
    # Helper Methods (Optional - Add as needed)
    # =========================================================================
    
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
    checker = Check_12_0_0_33()
    checker.init_checker(Path(__file__))
    result = checker.execute_check()
    checker.write_output(result)
    return 0 if result.is_pass else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())