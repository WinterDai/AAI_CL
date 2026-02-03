################################################################################
# Script Name: IMP-2-0-0-02.py
#
# Purpose:
#   Confirm latest DRC rule deck(s) was used? List DRC rule deck name in Comments. eg: PLN3ELO_17M_1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2Yx2R_014.11_2a.encrypt PLN3ELO_17M_1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2Yx2R_054_PATCH.11_2a.encrypt
#
# Logic:
#   - Parse DRC_pvl.log to extract rule deck path from include statement
#   - Parse rule deck file to extract document name and version from header
#   - For Type 1/4: Verify all three values (path, document, version) exist
#   - For Type 2/3: Compare extracted document/version against expected pattern_items
#   - Support waiver for version mismatches (Type 3/4)
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
# Author: Chenwei Fan
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
class Check_2_0_0_02(InputFileParserMixin, OutputBuilderMixin, WaiverHandlerMixin, BaseChecker):
    """
    IMP-2-0-0-02: Confirm latest DRC rule deck(s) was used? List DRC rule deck name in Comments. eg: PLN3ELO_17M_1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2Yx2R_014.11_2a.encrypt PLN3ELO_17M_1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2Yx2R_054_PATCH.11_2a.encrypt
    
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
    FOUND_DESC_TYPE1_4 = "DRC rule deck document and version information found in rule deck file"
    MISSING_DESC_TYPE1_4 = "DRC rule deck document or version information not found or extraction failed"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_DESC_TYPE2_3 = "DRC rule deck document and version matched expected values"
    MISSING_DESC_TYPE2_3 = "DRC rule deck document or version does not match expected values"
    
    # All Types (waiver description unified)
    WAIVED_DESC = "DRC rule deck version mismatch waived per project approval"
    
    # ⭐ REASON CONSTANTS - Split by Type semantics (API-025)
    # ALL Types pass found_reason/missing_reason, but use different constants
    
    # Type 1/4: Boolean checks - emphasize "found/not found" (existence)
    FOUND_REASON_TYPE1_4 = "Rule deck path, document name, and version successfully extracted from DRC log and rule deck file"
    MISSING_REASON_TYPE1_4 = "Failed to extract rule deck path from DRC log, or document/version not found in rule deck file header"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_REASON_TYPE2_3 = "Current rule deck document and version matched expected configuration and validated successfully"
    MISSING_REASON_TYPE2_3 = "Current rule deck document or version does not satisfy expected configuration - version mismatch detected"
    
    # Waiver-related (Type 3/4 only)
    WAIVED_BASE_REASON = "Rule deck version difference waived - alternative version approved for this project"
    UNUSED_WAIVER_REASON = "Waiver entry not matched - specified rule deck version not found in actual usage"
    
    def __init__(self):
        """Initialize the checker."""
        super().__init__(
            check_module="2.0_TECHFILE_AND_RULE_DECK_CHECK",
            item_id="IMP-2-0-0-02",
            item_desc="Confirm latest DRC rule deck(s) was used? List DRC rule deck name in Comments. eg: PLN3ELO_17M_1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2Yx2R_014.11_2a.encrypt PLN3ELO_17M_1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2Yx2R_054_PATCH.11_2a.encrypt"
        )
        # Custom member variables for parsed data
        self._parsed_items: List[Dict[str, Any]] = []
        self._metadata: Dict[str, str] = {}
        self._rule_deck_path: Optional[str] = None
        self._current_document: Optional[str] = None
        self._current_version: Optional[str] = None
    
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
        Parse input files to extract DRC rule deck information.
        
        Phase 1: Extract rule deck path from DRC_pvl.log using include pattern
        Phase 2: Parse rule deck file to extract document name and version
        
        Returns:
            Dict with parsed data:
            - 'items': List[Dict] - Rule deck information (path, document, version)
            - 'metadata': Dict - File metadata
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
        rule_deck_path = None
        current_document = None
        current_version = None
        
        # 3. Parse each input file for rule deck information
        # Phase 1: Extract rule deck path from DRC_pvl.log
        include_pattern = re.compile(r'^\s*include\s+"([^"]+)"', re.IGNORECASE)
        
        for file_path in valid_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line_num, line in enumerate(f, 1):
                        # Pattern 1: Extract rule deck path from include statement
                        match = include_pattern.search(line)
                        if match:
                            rule_deck_path = match.group(1)
                            metadata['rule_deck_path'] = rule_deck_path
                            metadata['source_file'] = str(file_path)
                            metadata['source_line'] = line_num
                            break
            except Exception as e:
                errors.append(f"Error parsing {file_path}: {str(e)}")
        
        # Phase 2: Parse rule deck file for document and version
        if rule_deck_path:
            # Convert to Path object - rule deck path is absolute, use directly
            rule_deck_file = Path(rule_deck_path)
            
            if rule_deck_file.exists():
                try:
                    # Pattern 2: Extract document name and version from rule deck header
                    doc_version_pattern = re.compile(
                        r'DRC\s+COMMAND\s+FILE\s+DOCUMENT:\s*(.+?)\s+VER\s+(.+?)(?:\s|$)',
                        re.IGNORECASE
                    )
                    
                    with open(rule_deck_file, 'r', encoding='utf-8', errors='ignore') as f:
                        for line_num, line in enumerate(f, 1):
                            match = doc_version_pattern.search(line)
                            if match:
                                current_document = match.group(1).strip()
                                current_version = match.group(2).strip()
                                metadata['current_document'] = current_document
                                metadata['current_version'] = current_version
                                metadata['rule_deck_line'] = line_num
                                break
                except Exception as e:
                    errors.append(f"Error parsing rule deck file {rule_deck_file}: {str(e)}")
            else:
                errors.append(f"Rule deck file not found: {rule_deck_file}")
        
        # Build items list based on extraction results
        if rule_deck_path and current_document and current_version:
            # Format: ruledeck_path (current_document, current_version)
            item_name = f"{rule_deck_path} ({current_document}, {current_version})"
            items.append({
                'name': item_name,
                'rule_path': rule_deck_path,
                'current_doc': current_document,
                'current_ver': current_version,
                'line_number': metadata.get('source_line', 0),
                'file_path': metadata.get('source_file', 'N/A'),
                'type': 'rule_deck_info'
            })
        
        # 4. Store frequently reused data on self
        self._parsed_items = items
        self._metadata = metadata
        self._rule_deck_path = rule_deck_path
        self._current_document = current_document
        self._current_version = current_version
        
        return {
            'items': items,
            'metadata': metadata,
            'errors': errors
        }
    
    # =========================================================================
    # Type 1: Boolean Check
    # =========================================================================
    
    def _execute_type1(self) -> CheckResult:
        """
        Type 1: Boolean Check.
        
        Custom boolean validation (file exists? config valid?).
        Does NOT use pattern_items for searching.
        
        Use OutputBuilderMixin.build_complete_output() for automatic formatting.
        
        Returns:
            CheckResult with is_pass based on check logic
        """
        # Parse input
        data = self._parse_input_files()
        items = data.get('items', [])
        
        # Type 1: Validate all three values exist and are non-empty
        # - rule_path is not None and not empty
        # - current_doc is not None and not empty
        # - current_ver is not None and not empty
        found_items = {}
        missing_items = {}
        
        if (self._rule_deck_path and 
            self._current_document and 
            self._current_version and
            len(items) > 0):
            # All values successfully extracted - convert to dict
            for item in items:
                item_name = item['name']
                found_items[item_name] = {
                    'name': item_name,
                    'line_number': item.get('line_number', 0),
                    'file_path': item.get('file_path', 'N/A')
                }
        else:
            # Extraction failed - create descriptive missing item
            missing_reason = []
            if not self._rule_deck_path:
                missing_reason.append("rule deck path not found")
            if not self._current_document:
                missing_reason.append("document name not found")
            if not self._current_version:
                missing_reason.append("version not found")
            
            item_name = f"Rule deck extraction failed: {', '.join(missing_reason)}"
            missing_items[item_name] = {
                'name': item_name,
                'line_number': self._metadata.get('source_line', 0),
                'file_path': self._metadata.get('source_file', 'N/A')
            }
        
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
        
        Search pattern_items in input files.
        found_items = patterns found; missing_items = patterns not found.
        PASS/FAIL depends on check purpose (violation check vs requirement check).
        
        Template auto-handles waiver=0 conversions.
        
        Returns:
            CheckResult with is_pass based on value comparison
        """
        # Parse input
        data = self._parse_input_files()
        items = data.get('items', [])
        
        # Get requirements
        pattern_items = self.item_data.get('requirements', {}).get('pattern_items', [])
        
        # Type 2: Compare extracted values against expected
        # pattern_items[0] → latest_doc (expected document name)
        # pattern_items[1] → latest_ver (expected version)
        found_items = {}
        missing_items = {}
        
        if len(pattern_items) >= 2:
            latest_doc = pattern_items[0]
            latest_ver = pattern_items[1]
            
            if (self._current_document and 
                self._current_version and
                len(items) > 0):
                # Check if document and version match
                doc_match = self._current_document == latest_doc
                ver_match = self._current_version == latest_ver
                
                if doc_match and ver_match:
                    # Both match - PASS
                    # Format: ruledeck_path (current_document, current_version), Expect (latest_document, latest_version)
                    item = items[0].copy()
                    item_name = f"{self._rule_deck_path} ({self._current_document}, {self._current_version}), Expect ({latest_doc}, {latest_ver})"
                    found_items[item_name] = {
                        'name': item_name,
                        'line_number': item.get('line_number', 0),
                        'file_path': item.get('file_path', 'N/A')
                    }
                else:
                    # Mismatch - FAIL
                    item_name = f"{self._rule_deck_path} ({self._current_document}, {self._current_version}), Expect ({latest_doc}, {latest_ver})"
                    missing_items[item_name] = {
                        'name': item_name,
                        'line_number': items[0].get('line_number', 0),
                        'file_path': items[0].get('file_path', 'N/A')
                    }
            else:
                # Extraction failed
                item_name = f"Rule deck extraction failed, Expect ({latest_doc}, {latest_ver})"
                missing_items[item_name] = {
                    'name': item_name,
                    'line_number': self._metadata.get('source_line', 0),
                    'file_path': self._metadata.get('source_file', 'N/A')
                }
        else:
            # Invalid configuration
            item_name = "Invalid pattern_items configuration - expected 2 items (document, version)"
            missing_items[item_name] = {
                'name': item_name,
                'line_number': self._metadata.get('source_line', 0),
                'file_path': self._metadata.get('source_file', 'N/A')
            }
        
        # Use template helper (auto-handles waiver=0)
        # Type 2: Use TYPE2_3 desc+reason (emphasize "matched/satisfied") - API-026
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
        
        Uses WaiverHandlerMixin for waiver processing:
        - parse_waive_items(waive_items_raw): Parse waiver configuration
        - match_waiver_entry(item, waive_dict): Match item against waivers
        
        Uses OutputBuilderMixin for result construction:
        - build_complete_output(...): Assemble final CheckResult with auto-formatting
        
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
        
        # Type 3: Same logic as Type 2, plus waiver classification
        found_items = {}
        waived_items = {}
        missing_items = {}
        used_waivers = set()
        
        if len(pattern_items) >= 2:
            latest_doc = pattern_items[0]
            latest_ver = pattern_items[1]
            
            if (self._current_document and 
                self._current_version and
                len(items) > 0):
                # Check if document and version match
                doc_match = self._current_document == latest_doc
                ver_match = self._current_version == latest_ver
                
                if doc_match and ver_match:
                    # Both match - PASS (found_items)
                    item_name = f"{self._rule_deck_path} ({self._current_document}, {self._current_version}), Expect ({latest_doc}, {latest_ver})"
                    found_items[item_name] = {
                        'name': item_name,
                        'line_number': items[0].get('line_number', 0),
                        'file_path': items[0].get('file_path', 'N/A')
                    }
                else:
                    # Mismatch - check waiver
                    item_name = f"{self._rule_deck_path} ({self._current_document}, {self._current_version}), Expect ({latest_doc}, {latest_ver})"
                    
                    # Check if waived (match against rule deck path or full name)
                    matched_waiver = self.match_waiver_entry(self._rule_deck_path, waive_dict)
                    if not matched_waiver:
                        matched_waiver = self.match_waiver_entry(item_name, waive_dict)
                    
                    if matched_waiver:
                        waived_items[item_name] = {
                            'name': item_name,
                            'line_number': items[0].get('line_number', 0),
                            'file_path': items[0].get('file_path', 'N/A')
                        }
                        used_waivers.add(matched_waiver)
                    else:
                        missing_items[item_name] = {
                            'name': item_name,
                            'line_number': items[0].get('line_number', 0),
                            'file_path': items[0].get('file_path', 'N/A')
                        }
            else:
                # Extraction failed - unwaived violation
                item_name = f"Rule deck extraction failed, Expect ({latest_doc}, {latest_ver})"
                missing_items[item_name] = {
                    'name': item_name,
                    'line_number': self._metadata.get('source_line', 0),
                    'file_path': self._metadata.get('source_file', 'N/A')
                }
        else:
            # Invalid configuration
            item_name = "Invalid pattern_items configuration - expected 2 items (document, version)"
            missing_items[item_name] = {
                'name': item_name,
                'line_number': self._metadata.get('source_line', 0),
                'file_path': self._metadata.get('source_file', 'N/A')
            }
        
        # Find unused waivers
        unused_waivers = [name for name in waive_dict.keys() if name not in used_waivers]
        
        # FIXED: Pass dict format directly (API-009)
        # Use template helper for automatic output formatting (waivers.value>0)
        # Type 3: Use TYPE2_3 desc+reason (emphasize "matched/satisfied") - API-026
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
        
        Use OutputBuilderMixin.build_complete_output() with has_waiver_value=True.
        
        Returns:
            CheckResult with waiver logic applied
        """
        # Parse input
        data = self._parse_input_files()
        items = data.get('items', [])
        
        # FIXED: Use waivers.get() directly to preserve dict format (API-016)
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # Type 4: Boolean check with waiver
        found_items = {}
        waived_items = {}
        missing_items = {}
        used_waivers = set()
        
        if (self._rule_deck_path and 
            self._current_document and 
            self._current_version and
            len(items) > 0):
            # All values successfully extracted - PASS
            item_name = items[0]['name']
            found_items[item_name] = {
                'name': item_name,
                'line_number': items[0].get('line_number', 0),
                'file_path': items[0].get('file_path', 'N/A')
            }
        else:
            # Extraction failed - check waiver
            missing_reason = []
            if not self._rule_deck_path:
                missing_reason.append("rule deck path not found")
            if not self._current_document:
                missing_reason.append("document name not found")
            if not self._current_version:
                missing_reason.append("version not found")
            
            item_name = f"Rule deck extraction failed: {', '.join(missing_reason)}"
            
            # Check if waived
            matched_waiver = self.match_waiver_entry(item_name, waive_dict)
            if matched_waiver:
                waived_items[item_name] = {
                    'name': item_name,
                    'line_number': self._metadata.get('source_line', 0),
                    'file_path': self._metadata.get('source_file', 'N/A')
                }
                used_waivers.add(matched_waiver)
            else:
                missing_items[item_name] = {
                    'name': item_name,
                    'line_number': self._metadata.get('source_line', 0),
                    'file_path': self._metadata.get('source_file', 'N/A')
                }
        
        # Find unused waivers
        unused_waivers = [name for name in waive_dict.keys() if name not in used_waivers]
        
        # FIXED: Pass dict format directly (API-009)
        # Use template helper for automatic output formatting (waivers.value>0)
        # Type 4: Use TYPE1_4 reason (emphasize "found/not found")
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
            waived_base_reason=self.WAIVED_BASE_REASON,
            unused_waiver_reason=self.UNUSED_WAIVER_REASON
        )
    
    # =========================================================================
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
    checker = Check_2_0_0_02()
    checker.init_checker(Path(__file__))
    result = checker.execute_check()
    checker.write_output(result)
    return 0 if result.is_pass else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())