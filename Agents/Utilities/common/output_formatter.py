################################################################################
# Script Name: output_formatter.py (Unified & Refactored Version)
#
# Purpose:
#   Data-driven unified formatter for check result output.
#   Eliminates 10 ResultType branches → Single unified logic.
#
# Key Architecture:
#   - Data-driven: Output format determined by CheckResult fields, not ResultType
#   - Unified logic: Single _write_log_unified() handles all output types
#   - Group ordering: ERROR → WARN → INFO (consistent across all types)
#   - Simplified: ~1200 lines → ~700 lines (-40%)
#
# Usage:
#   from output_formatter import OutputFormatter, CheckResult, create_check_result
#   
#   formatter = OutputFormatter(item_id="IMP-5-0-0-00", item_desc="Library Check")
#   result = create_check_result(value=10, is_pass=True, details=[...])
#   formatter.write_log(result, log_path)
#   formatter.write_report(result, report_path)
#
# Author: yyin
# Date:   2025-11-11 (Refactored)
################################################################################

from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum


class Severity(Enum):
    """Severity levels for check results."""
    INFO = "Info"
    WARN = "Warn"
    FAIL = "Fail"


class ResultType(Enum):
    """
    Types of check results - kept for backward compatibility.
    Note: Output logic no longer depends on these types.
    """
    # ===== Normal Check Flow (1-6) =====
    PASS_WITH_VALUES = 1            # value>0 && pass && waivers:N/A
    FAIL_WITH_VALUES = 2            # value>0 && fail && waivers:N/A
    PASS_WITHOUT_VALUES = 3         # value=0 && pattern_items:[] && waivers:N/A
    INFO_ONLY = 4                   # value=N/A && pattern_items:[]
    PASS_WITH_WAIVERS = 5           # value>0 && pass && waivers:not empty
    FAIL_WITH_WAIVERS = 6           # value>0 && fail && waivers:not empty
    
    # ===== Exception Flow (7-10) =====
    FAIL_WITHOUT_CHECK_VALUES = 7   # value=0 && pattern_items:not empty
    PASS_WITH_FULL_WAIVERS = 8      # value=0 && pattern_items:not empty && waivers:full coverage
    EXECUTION_ERROR = 9             # File not found, parse failure, environment error
    CONFIG_ERROR = 10               # Config contradiction, validation failure


@dataclass
class DetailItem:
    """Represents a single detail item in the check result."""
    severity: Severity
    name: str                 # e.g., library name
    line_number: int          # Line number in source file
    file_path: str           # Source file path
    reason: str              # Reason description
    
    def __post_init__(self):
        """Ensure severity is a Severity enum."""
        if isinstance(self.severity, str):
            self.severity = Severity[self.severity.upper()]


@dataclass
class CheckResult:
    """
    Represents the complete result of a check operation.
    
    Attributes:
        result_type: Type of result (for backward compatibility)
        is_pass: Whether the check passed
        value: The value found (can be int, 0, or "N/A")
        has_pattern_items: Whether pattern items are provided
        has_waiver_value: Whether waiver value is provided
        details: List of detailed items (libraries, errors, etc.)
        error_groups: Optional grouped errors/warnings for output
                     Format: {"ERROR01": {"description": "xxx", "items": ["item1", "item2"]}}
        info_groups: Optional grouped info for output
                     Format: {"INFO01": {"description": "xxx", "items": ["item1", "item2"]}}
        warn_groups: Optional grouped warnings (legacy, use error_groups instead)
        info_message: Optional info message for display
        basic_errors: Optional list of basic error messages (for execution/config errors)
        item_desc: Optional item description (from BaseChecker.item_desc)
        default_group_desc: Optional default description for auto-generated groups (ERROR01/INFO01)
    """
    result_type: ResultType
    is_pass: bool
    value: Any  # int > 0, 0, or "N/A"
    has_pattern_items: bool = False
    has_waiver_value: bool = False
    details: List[DetailItem] = field(default_factory=list)
    error_groups: Optional[Dict[str, Dict[str, Any]]] = None
    info_groups: Optional[Dict[str, Dict[str, Any]]] = None
    warn_groups: Optional[Dict[str, Dict[str, Any]]] = None
    info_message: Optional[str] = None
    basic_errors: Optional[List[str]] = None
    item_desc: Optional[str] = None
    default_group_desc: Optional[str] = None
    
    def get_summary_data(self) -> Dict[str, Any]:
        """
        Get structured summary data for YAML generation - unified logic.
        
        Extracts data from error_groups/info_groups first, falls back to details.
        Matches items with details to preserve source_line and source_file.
        
        Returns:
            Dictionary with complete YAML data structure matching parse_report() output
        """
        # Initialize data structure
        data = {
            "description": self.item_desc or "",
            "infos": [],
            "failures": [],
            "warnings": []
        }
        
        # Add info_message if present
        if self.info_message:
            data["info_message"] = self.info_message
        
        # Add occurrence counts
        fail_details = [d for d in self.details if d.severity == Severity.FAIL]
        warn_details = [d for d in self.details if d.severity == Severity.WARN]
        info_details = [d for d in self.details if d.severity == Severity.INFO]
        
        if fail_details:
            data["occurrence"] = len(fail_details)
        if warn_details:
            data["warning_occurrence"] = len(warn_details)
        if info_details:
            data["info_occurrence"] = len(info_details)
        
        # Collect warnings from any grouping sources
        collected_warnings: List[Dict[str, Any]] = []

        # Extract from error_groups if available
        if self.error_groups:
            data["failures"] = self._extract_items_from_groups(
                self.error_groups, self.details, 'ERROR', fail_details)
            data["infos"].extend(self._extract_items_from_groups(
                self.error_groups, self.details, 'INFO', info_details))
            warnings_from_errors = self._extract_items_from_groups(
                self.error_groups, self.details, 'WARN', warn_details)
            if warnings_from_errors:
                collected_warnings.extend(warnings_from_errors)
        else:
            # Fallback to details
            data["failures"] = self._extract_items_from_details(fail_details)
        
        # Extract from info_groups if available
        if self.info_groups:
            data["infos"].extend(self._extract_items_from_groups(
                self.info_groups, self.details, 'INFO', info_details))
        elif not self.error_groups:
            # Fallback to details (only if error_groups didn't handle it)
            data["infos"] = self._extract_items_from_details(info_details)
        
        # Extract from warn_groups if available
        if self.warn_groups:
            warnings_from_warn_groups = self._extract_items_from_groups(
                self.warn_groups, self.details, 'WARN', warn_details)
            if warnings_from_warn_groups:
                collected_warnings.extend(warnings_from_warn_groups)

        # Warnings fallback when no group produced data
        if not collected_warnings and warn_details:
            collected_warnings = self._extract_items_from_details(warn_details)

        if collected_warnings:
            data["warnings"] = collected_warnings
        
        return data
    
    def _extract_items_from_groups(self, groups: Dict, details: List[DetailItem], 
                                   prefix: str, fallback_details: List[DetailItem]) -> List[Dict]:
        """
        Extract items from groups (ERROR/INFO/WARN) and match with details.
        
        Args:
            groups: Dict of {"ERROR01": {"description": ..., "items": [...]}}
            details: All DetailItems for matching
            prefix: 'ERROR', 'INFO', or 'WARN'
            fallback_details: Details to use if items list is empty
        
        Returns:
            List of item dicts for YAML
        """
        items = []
        idx = 1
        used_detail_ids = set()

        for code in sorted(groups.keys()):
            if not code.startswith(prefix):
                continue
            
            group_data = groups[code]
            group_items = group_data.get('items', [])
            matched_entries = []

            if group_items:
                for item_name in group_items:
                    # Find matching detail by name first, then by reason (for waive_items)
                    detail = next((d for d in details if d.name == item_name), None)
                    is_waive_item = False
                    if not detail:
                        # Try matching by reason (for waive_items where name="")
                        clean_reason = item_name.strip()
                        detail = next((d for d in details
                                       if d.reason and clean_reason in d.reason.replace('[WAIVED_AS_INFO]', '').replace('[WAIVED_INFO]', '').strip()), None)
                        if detail:
                            is_waive_item = True

                    matched_entries.append((detail, item_name, is_waive_item))
            else:
                # Fall back to provided detail list filtered by severity
                fallback_candidates = list(fallback_details) if fallback_details else []

                if prefix == 'INFO':
                    fallback_candidates = [d for d in fallback_candidates
                                           if not (d.reason and '[WAIVED_INFO]' in d.reason)]

                for detail in fallback_candidates:
                    detail_id = id(detail)
                    if detail_id in used_detail_ids:
                        continue
                    matched_entries.append((detail, detail.name if detail else 'N/A', False))
                    used_detail_ids.add(detail_id)

            for detail, item_name, is_waive_item in matched_entries:
                if detail and detail.reason:
                    reason = detail.reason
                else:
                    reason = group_data.get('description', 'N/A')

                if detail and detail.name:
                    detail_text = detail.name
                elif is_waive_item:
                    detail_text = 'N/A'
                else:
                    detail_text = item_name if item_name else 'N/A'

                source_line = "N/A"
                source_file = "N/A"
                if detail:
                    if detail.line_number:
                        source_line = str(detail.line_number)
                    if detail.file_path:
                        source_file = detail.file_path

                items.append({
                    "index": idx,
                    "detail": detail_text if detail_text else 'N/A',
                    "source_line": source_line,
                    "source_file": source_file,
                    "reason": reason
                })
                idx += 1
        
        return items
    
    def _extract_items_from_details(self, details: List[DetailItem]) -> List[Dict]:
        """
        Fallback: Extract items directly from details (when no groups available).
        
        Args:
            details: DetailItems to extract
        
        Returns:
            List of item dicts for YAML
        """
        items = []
        
        for idx, detail in enumerate(details, 1):
            reason = detail.reason or "N/A"
            
            # Special handling for [WAIVED_AS_INFO] tag
            if "[WAIVED_AS_INFO]" in reason:
                if not detail.name and not detail.file_path:
                    reason = reason.replace("[WAIVED_AS_INFO]", "[WAIVED_REASON]")
            
            items.append({
                "index": idx,
                "detail": detail.name or "N/A",
                "source_line": str(detail.line_number) if detail.line_number else "N/A",
                "source_file": detail.file_path or "N/A",
                "reason": reason
            })
        
        return items
    
    @staticmethod
    def determine_result_type(value: Any, is_pass: bool, 
                            has_pattern_items: bool, 
                            has_waiver_value: bool) -> ResultType:
        """Determine the result type based on conditions."""
        value_is_na = str(value).upper() == "N/A"
        value_is_zero = value == 0
        value_is_positive = isinstance(value, (int, float)) and value > 0
        value_is_error = str(value).upper() == "ERROR"
        
        # Type 9: Execution error
        if value_is_error:
            return ResultType.EXECUTION_ERROR
        
        # Type 4: INFO_ONLY
        if value_is_na and not has_pattern_items and not has_waiver_value:
            if is_pass:
                return ResultType.INFO_ONLY
            else:
                return ResultType.FAIL_WITH_VALUES
        
        # Special case: value=N/A with waivers
        if value_is_na and not has_pattern_items and has_waiver_value:
            return ResultType.PASS_WITH_WAIVERS if is_pass else ResultType.FAIL_WITH_WAIVERS
        
        # Type 3: PASS_WITHOUT_VALUES
        if value_is_zero and not has_pattern_items and not has_waiver_value:
            return ResultType.PASS_WITHOUT_VALUES
        
        # Type 7: FAIL_WITHOUT_CHECK_VALUES
        if value_is_zero and has_pattern_items and not has_waiver_value:
            return ResultType.FAIL_WITHOUT_CHECK_VALUES
        
        # Type 8: PASS_WITH_FULL_WAIVERS
        if value_is_zero and has_pattern_items and has_waiver_value:
            return ResultType.PASS_WITH_FULL_WAIVERS if is_pass else ResultType.FAIL_WITHOUT_CHECK_VALUES
        
        # Type 5 & 6: With waivers
        if value_is_positive and has_waiver_value:
            return ResultType.PASS_WITH_WAIVERS if is_pass else ResultType.FAIL_WITH_WAIVERS
        
        # Type 1 & 2: Simple pass/fail
        if is_pass:
            return ResultType.PASS_WITH_VALUES
        else:
            return ResultType.FAIL_WITH_VALUES


# ========== Data Preprocessing Class ==========

class DetailItemClassifier:
    """Centralized logic for classifying and filtering DetailItems."""
    
    @staticmethod
    def classify_info_items(info_items: List[DetailItem]) -> Dict[str, List]:
        """
        Classify INFO items into waive_tags, info_tags, and info_list.
        
        Returns:
            {
                'waive_tags': [str, ...],      # For [WAIVED_INFO]: format
                'info_tags': [DetailItem, ...], # For [INFO]: format (no location)
                'info_list': [DetailItem, ...]  # For list format (with location)
            }
        """
        waive_tags = []
        info_tags = []
        info_list = []
        
        for detail in info_items:
            if DetailItemClassifier.is_waive_tag(detail):
                clean_reason = detail.reason.replace('[WAIVED_AS_INFO]', '').strip()
                waive_tags.append(clean_reason)
            elif DetailItemClassifier.has_location_info(detail):
                info_list.append(detail)
            else:
                info_tags.append(detail)
        
        return {
            'waive_tags': waive_tags,
            'info_tags': info_tags,
            'info_list': info_list
        }
    
    @staticmethod
    def is_waive_tag(detail: DetailItem) -> bool:
        """Check if DetailItem is a waive tag."""
        return (
            detail.name in ["", "N/A"] and
            detail.reason.endswith('[WAIVED_AS_INFO]') and
            detail.file_path in ["", "N/A"] and
            detail.line_number in [0, "0", ""]
        )
    
    @staticmethod
    def has_location_info(detail: DetailItem) -> bool:
        """Check if DetailItem has file location information."""
        return (
            detail.file_path not in ["", "N/A"] and
            detail.line_number not in ["", "N/A", 0, "0"]
        )
    
    @staticmethod
    def group_by_severity(details: List[DetailItem]) -> Dict[str, List[DetailItem]]:
        """Group details by severity level."""
        fail_items = [d for d in details if d.severity == Severity.FAIL]
        warn_items = [d for d in details if d.severity == Severity.WARN]
        info_items = [d for d in details if d.severity == Severity.INFO]
        
        return {
            'fail_items': fail_items,
            'warn_items': warn_items,
            'info_items': info_items
        }


# ========== Reusable Output Components ==========

class OutputComponents:
    """Reusable building blocks for output formatting."""
    
    @staticmethod
    def write_tags(f, messages: List[str], tag_type: str):
        """
        Write tag format: [TAG]:message
        
        Args:
            messages: List of messages to write
            tag_type: INFO/WARN/ERROR/WAIVED_INFO/CONFIG_ERROR
        """
        for message in messages:
            f.write(f'[{tag_type}]:{message}\n')
    
    @staticmethod
    def write_error_group_log(f, item_id: str, error_code: str, description: str,
                              items: List[DetailItem], severity_text: str):
        """
        Write grouped format (Log):
        IMP-5-0-0-00-ERROR01: description:
          Severity: Fail Occurrence: 3
          - item1
          - item2
        """
        f.write(f'{item_id}-{error_code}: {description}:\n')
        f.write(f'  Severity: {severity_text} Occurrence: {len(items)}\n')
        for detail in items:
            # Support empty name - use reason instead
            if detail.name:
                f.write(f'  - {detail.name}\n')
            elif detail.reason:
                f.write(f'  - {detail.reason}\n')
            else:
                f.write(f'  - N/A\n')


# ========== Main OutputFormatter Class ==========

class OutputFormatter:
    """Unified formatter for log and report outputs - fully data-driven."""
    
    def __init__(self, item_id: str, item_desc: str):
        """
        Initialize the formatter.
        
        Args:
            item_id: Item identifier (e.g., "IMP-5-0-0-00")
            item_desc: Item description (e.g., "Library Check")
        """
        self.item_id = item_id
        self.item_desc = item_desc
    
    def write_log(self, result: CheckResult, log_path: Path, mode: str = 'a') -> None:
        """
        Write log output - unified logic for all result types.
        
        Output format is driven by CheckResult data structure:
        - error_groups/info_groups: Grouped output
        - details: Fallback for ungrouped output
        - is_pass: PASS/FAIL prefix
        """
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        with log_path.open(mode, encoding='utf-8') as f:
            self._write_log_unified(f, result)
    
    def _write_log_unified(self, f, result: CheckResult) -> None:
        """
        Unified log writer - replaces 10 separate write_log methods.
        
        Logic (Data-Driven):
        1. Write PASS/FAIL/ERROR prefix based on data
        2. Write info_message if present
        3. Write basic_errors if present (execution/config errors)
        4. Write groups (ERROR → WARN → INFO) from error_groups
        5. Write groups from info_groups
        6. Fallback: Write ungrouped details
        """
        # Step 1: Write status prefix
        # Check if this is an execution/config error by looking at basic_errors structure
        if result.basic_errors and not result.error_groups and not result.info_groups:
            # This is an execution error or config error
            # Determine type by checking error message content
            is_config_error = any('[CONFIG_ERROR]' in str(err) for err in result.basic_errors)
            
            if is_config_error:
                f.write(f'[CONFIG_ERROR]:{self.item_id}:{self.item_desc}\n')
                tag = "CONFIG_ERROR"
            else:
                f.write(f'FAIL:{self.item_id}:{self.item_desc}\n')
                tag = "ERROR"
            
            # Write basic errors
            for err in result.basic_errors:
                f.write(f'[{tag}]:{err}\n')
            f.write('\n')
            return
        
        # Normal flow: PASS or FAIL
        status = "PASS" if result.is_pass else "FAIL"
        f.write(f'{status}:{self.item_id}:{self.item_desc}\n')
        
        # Step 2: Write info_message
        if result.info_message:
            f.write(f'[INFO]:{result.info_message}\n')
        
        # Step 2.5: Write [WAIVED_INFO] tags for waive_items (name="")
        # Extract waive_items from details
        waive_items = [d for d in result.details 
                      if d.severity == Severity.INFO 
                      and (not d.name or d.name in ["", "N/A"])
                      and d.reason and '[WAIVED_INFO]' in d.reason]
        
        if waive_items:
            for item in waive_items:
                # Remove [WAIVED_INFO] tag from reason
                waive_reason = item.reason.replace('[WAIVED_INFO]', '').strip()
                f.write(f'[WAIVED_INFO]:{waive_reason}\n')
        
        # Step 3: Write groups in order: ERROR → WARN → INFO
        if result.error_groups:
            self._write_groups_ordered(f, result.error_groups, result.details)
        
        if result.warn_groups:
            self._write_groups_ordered(f, result.warn_groups, result.details)
        
        if result.info_groups:
            self._write_groups_ordered(f, result.info_groups, result.details)
        
        # Step 4: Fallback for ungrouped details (legacy support)
        if not result.error_groups and not result.warn_groups and not result.info_groups and result.details:
            self._write_ungrouped_details(f, result.details, result.default_group_desc)
        
        f.write('\n')
    
    def _write_groups_ordered(self, f, groups: Dict[str, Dict], details: List[DetailItem]) -> None:
        """
        Write groups in proper order: ERROR → WARN → INFO.
        
        Args:
            f: File handle
            groups: Dict of {"ERROR01": {"description": ..., "items": [...]}}
            details: List of DetailItem for matching
        """
        # Order: ERROR, WARN, INFO
        for prefix in ['ERROR', 'WARN', 'INFO']:
            for code in sorted(groups.keys()):
                if not code.startswith(prefix):
                    continue
                
                group_data = groups[code]
                description = group_data.get('description', 'N/A')
                items = group_data.get('items', [])
                
                # Match items with details
                if items:
                    # Non-empty items list: match by name
                    # Deduplicate by name to match template's sorted(set(...)) deduplication
                    seen_names = set()
                    matched = []
                    for d in details:
                        if d.name in items and d.name not in seen_names:
                            matched.append(d)
                            seen_names.add(d.name)
                else:
                    # Empty items list: extract from details by severity
                    severity_name = prefix if prefix != 'ERROR' else 'FAIL'
                    matched = [d for d in details 
                              if d.severity.name.upper() == severity_name.upper()]
                
                # For INFO groups (except INFO01), filter out waive items
                # INFO01 is specifically for waived items, so don't filter it
                if prefix == 'INFO' and code != 'INFO01':
                    matched = [d for d in matched 
                              if not (d.reason and '[WAIVED_INFO]' in d.reason)]
                
                if not matched:
                    continue
                
                # Write group
                severity_text = 'Fail' if prefix == 'ERROR' else prefix.capitalize()
                OutputComponents.write_error_group_log(
                    f, self.item_id, code, description, matched, severity_text
                )
    
    def _write_ungrouped_details(self, f, details: List[DetailItem], default_desc: Optional[str] = None) -> None:
        """
        Fallback: Write details without grouping (legacy format).
        Used when error_groups and info_groups are both None.
        """
        # Helper to deduplicate by name
        def dedupe_by_name(items):
            seen = set()
            result = []
            for item in items:
                if item.name not in seen:
                    result.append(item)
                    seen.add(item.name)
            return result
        
        # Group by severity and deduplicate
        fail_items = dedupe_by_name([d for d in details if d.severity == Severity.FAIL])
        warn_items = dedupe_by_name([d for d in details if d.severity == Severity.WARN])
        info_items = dedupe_by_name([d for d in details if d.severity == Severity.INFO])
        
        # Write FAIL items as ERROR01
        if fail_items:
            # Use custom description if provided, otherwise use default
            fail_desc = default_desc if default_desc else 'Check failed'
            OutputComponents.write_error_group_log(
                f, self.item_id, 'ERROR01', fail_desc, fail_items, 'Fail'
            )
        
        # Write WARN items as WARN01
        if warn_items:
            # Use custom description if provided, otherwise use default
            warn_desc = default_desc if default_desc else 'Warnings'
            OutputComponents.write_error_group_log(
                f, self.item_id, 'WARN01', warn_desc, warn_items, 'Warn'
            )
        
        # Write INFO items as INFO01
        if info_items:
            # Filter out waive items (those with [WAIVED_INFO] tag)
            non_waive_info_items = [d for d in info_items 
                                    if not (d.reason and '[WAIVED_INFO]' in d.reason)]
            
            if non_waive_info_items:
                # Use custom description if provided, otherwise use default
                info_desc = default_desc if default_desc else 'Items found in check'
                OutputComponents.write_error_group_log(
                    f, self.item_id, 'INFO01', info_desc, non_waive_info_items, 'Info'
                )
    
    def write_report(self, result: CheckResult, report_path: Path, mode: str = 'a') -> None:
        """
        Write report output - simplified format without group codes.
        
        Report format differs from log:
        - Has status line: PASS/FAIL:item_id:item_desc
        - Shows Occurrence sections without group codes (ERROR01, INFO01, etc.)
        - More concise than log format
        """
        report_path.parent.mkdir(parents=True, exist_ok=True)
        
        with report_path.open(mode, encoding='utf-8') as f:
            self._write_report_unified(f, result)
        
        # Note: Memory cache is used instead of file cache (see BaseChecker._result_cache)
        # No need to generate .cache.json files
    
    def _write_report_unified(self, f, result: CheckResult) -> None:
        """
        Unified report writer - simplified format for all result types.
        
        Report format:
        1. Write status line (PASS/FAIL:item_id:desc)
        2. Write [INFO] tags if info_message exists
        3. Write [WAIVED_INFO] tags if exist
        4. Write Occurrence sections (Fail/Warn/Info) without group codes
        """
        # Step 1: Write status line
        if result.basic_errors and not result.error_groups and not result.info_groups:
            # Execution/config error
            is_config_error = any('[CONFIG_ERROR]' in str(err) for err in result.basic_errors)
            
            if is_config_error:
                f.write(f'[CONFIG_ERROR]:{self.item_id}:{self.item_desc}\n')
                tag = "CONFIG_ERROR"
            else:
                f.write(f'FAIL:{self.item_id}:{self.item_desc}\n')
                tag = "ERROR"
            
            # Write basic errors
            for err in result.basic_errors:
                f.write(f'[{tag}]:{err}\n')
            return
        
        # Normal flow
        status = "PASS" if result.is_pass else "FAIL"
        f.write(f'{status}:{self.item_id}:{self.item_desc}\n')
        
        # Step 2: Write info_message as [INFO] tag
        if result.info_message:
            f.write(f'[INFO]:{result.info_message}\n')
        
        # Step 3: Group details by severity
        fail_items = [d for d in result.details if d.severity == Severity.FAIL]
        warn_items = [d for d in result.details if d.severity == Severity.WARN]
        info_items = [d for d in result.details if d.severity == Severity.INFO]
        
        # Separate INFO items: waive_items (name="") vs actual waived items (name!="")
        waive_item_tags = []  # Only for waive_items config (name="" AND has [WAIVED_INFO] tag)
        info_occurrence_items = []  # All other INFO items (including waived items with actual names)
        
        for item in info_items:
            # waive_items from config have name="" AND reason contains [WAIVED_INFO] tag
            if ((not item.name or item.name in ["", "N/A"]) and 
                item.reason and '[WAIVED_INFO]' in item.reason):
                waive_item_tags.append(item)
            else:
                info_occurrence_items.append(item)
        
        # Write [WAIVED_INFO] tags (only for waive_items config)
        if waive_item_tags:
            for item in waive_item_tags:
                # Remove both [WAIVED_AS_INFO] and [WAIVED_INFO] tags from reason
                waive_reason = item.reason.replace('[WAIVED_AS_INFO]', '').replace('[WAIVED_INFO]', '').strip()
                f.write(f'[WAIVED_INFO]:{waive_reason}\n')
        
        # Step 4: Write Occurrence sections (without group codes)
        # Write Fail Occurrence
        if fail_items:
            f.write(f'Fail Occurrence: {len(fail_items)}\n')
            for idx, item in enumerate(fail_items, 1):
                self._write_report_item(f, idx, item, 'Fail')
        
        # Write Warn Occurrence  
        if warn_items:
            f.write(f'Warn Occurrence: {len(warn_items)}\n')
            for idx, item in enumerate(warn_items, 1):
                self._write_report_item(f, idx, item, 'Warn')
        
        # Write Info Occurrence
        if info_occurrence_items:
            f.write(f'Info Occurrence: {len(info_occurrence_items)}\n')
            for idx, item in enumerate(info_occurrence_items, 1):
                self._write_report_item(f, idx, item, 'Info')
    
    def _write_report_item(self, f, index: int, item: DetailItem, severity: str) -> None:
        """Write a single report item in standard format."""
        # Build the item line
        if item.name and item.name not in ["", "N/A"]:
            detail_text = item.name
        else:
            detail_text = item.reason
        
        # Add location info if available (skip if line=0 or file=N/A)
        location = ""
        has_location = (item.file_path and item.file_path not in ["", "N/A"] and 
                       item.line_number and item.line_number not in [0, "0", ""])
        
        if has_location:
            location = f" In line {item.line_number}, {item.file_path}"
        
        # Build reason text if different from detail
        # Keep [WAIVED_AS_INFO] tag in reason for report output
        if item.reason and item.reason not in ["", "N/A"] and item.reason != detail_text:
            # Use different separator based on whether location exists
            if has_location:
                # Has location: name.location: reason
                f.write(f'{index}: {severity}: {detail_text}.{location}: {item.reason}\n')
            else:
                # No location: name: reason (no dot before colon)
                f.write(f'{index}: {severity}: {detail_text}: {item.reason}\n')
        else:
            # No reason, just detail_text and optional location
            if has_location:
                f.write(f'{index}: {severity}: {detail_text}.{location}\n')
            else:
                f.write(f'{index}: {severity}: {detail_text}\n')


# ========== Helper Functions ==========

def create_check_result(value: Any,
                       is_pass: bool,
                       has_pattern_items: bool = False,
                       has_waiver_value: bool = False,
                       details: Optional[List[DetailItem]] = None,
                       error_groups: Optional[Dict[str, Dict[str, Any]]] = None,
                       info_groups: Optional[Dict[str, Dict[str, Any]]] = None,
                       warn_groups: Optional[Dict[str, Dict[str, Any]]] = None,
                       info_message: Optional[str] = None,
                       basic_errors: Optional[List[str]] = None,
                       item_desc: Optional[str] = None,
                       default_group_desc: Optional[str] = None) -> CheckResult:
    """Convenience function to create a CheckResult with automatic type determination."""
    result_type = CheckResult.determine_result_type(
        value, is_pass, has_pattern_items, has_waiver_value
    )
    
    return CheckResult(
        result_type=result_type,
        is_pass=is_pass,
        value=value,
        has_pattern_items=has_pattern_items,
        has_waiver_value=has_waiver_value,
        details=details or [],
        error_groups=error_groups,
        info_groups=info_groups,
        warn_groups=warn_groups,
        info_message=info_message,
        basic_errors=basic_errors,
        item_desc=item_desc,
        default_group_desc=default_group_desc
    )
