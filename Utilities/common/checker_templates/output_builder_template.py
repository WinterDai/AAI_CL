"""
Output Builder Template - Comprehensive Checker Output Construction

This module provides a unified API for building CheckResult outputs with automatic
metadata preservation, flexible severity control, and waiver support.

═══════════════════════════════════════════════════════════════════════════════
API VERSION: 2.0.0 (December 16, 2025)
═══════════════════════════════════════════════════════════════════════════════

WHAT'S NEW IN v2.0:
------------------
✅ Unified parameter interface: ALL items accept Union[Dict, List]
✅ Automatic List→Dict conversion for backward compatibility
✅ Metadata support for ALL item types (found, missing, waived, unused, extra)
✅ Fixed is_pass calculation bug (now includes extra_items with FAIL severity)
✅ Simplified Tag display logic ([WAIVER], [WAIVED_INFO], [WAIVED_AS_INFO])
✅ Enhanced docstrings with comprehensive examples

BREAKING CHANGES: None - 100% backward compatible with v1.x

═══════════════════════════════════════════════════════════════════════════════
CORE API METHODS
═══════════════════════════════════════════════════════════════════════════════

1. build_complete_output() - ONE-STEP SOLUTION ⭐ RECOMMENDED
   ├─ Use when: You want to build everything in one call
   ├─ Input: Categorized items (found/missing/waived/unused/extra)
   ├─ Output: Complete CheckResult ready to return
   └─ Features: Auto waiver=0 detection, metadata preservation, severity control

2. build_details_from_items() - DETAIL ITEMS ONLY
   ├─ Use when: You need custom group logic
   ├─ Input: Categorized items
   ├─ Output: List[DetailItem] sorted by severity
   └─ Features: Metadata extraction, custom name formatting

3. build_result_groups() - GROUPS ONLY
   ├─ Use when: You already have details, just need groups
   ├─ Input: Categorized items
   ├─ Output: Dict with info_groups, error_groups, warn_groups
   └─ Features: Auto INFO/ERROR/WARN organization, waiver=0 support

═══════════════════════════════════════════════════════════════════════════════
METADATA FORMAT (API v2.0)
═══════════════════════════════════════════════════════════════════════════════

Dict Format (RECOMMENDED for new code):
    items = {
        "item_name": {
            "line_number": 123,              # For source line display
            "file_path": "/path/to/file",    # For source file display
            "line_content": "...",           # Optional, for context
            # Add any custom metadata as needed
        }
    }

List Format (backward compatible):
    items = ["item1", "item2"]  # Auto-converted to Dict internally

═══════════════════════════════════════════════════════════════════════════════
TAG SYSTEM
═══════════════════════════════════════════════════════════════════════════════

[WAIVER]          - Type 3/4 waived items (normal mode)
[WAIVED_INFO]     - Type 1/2 waive_items (waiver=0 mode)
[WAIVED_AS_INFO]  - Auto-converted violations (waiver=0 mode)

Display Logic:
- Log file: Clean item names (tags in reason field, not displayed)
- Report file: Full details with tags visible in reason field

═══════════════════════════════════════════════════════════════════════════════
QUICK START EXAMPLES
═══════════════════════════════════════════════════════════════════════════════

Example 1: Type 1 Simple Check
-------------------------------
return self.build_complete_output(
    found_items={"clean_group": {"line_number": 10, "file_path": "report.txt"}},
    missing_items={"violated_group": {"line_number": 20, "file_path": "report.txt"}},
    found_reason="Group clean",
    missing_reason="Group has violations"
)

Example 2: Type 2 Pattern Check
--------------------------------
return self.build_complete_output(
    found_items=found_dict,          # Items matching pattern_items
    extra_items=extra_dict,          # Items NOT in pattern_items
    extra_severity=Severity.WARN,    # or FAIL if critical
    extra_reason="Unexpected item",
    extra_desc="Items need review"
)

Example 3: Type 3 with Waivers
-------------------------------
return self.build_complete_output(
    found_items=found_dict,
    missing_items=unwaived_dict,     # After waiver filtering
    waived_items=waived_dict,        # Items matched by waivers
    waive_dict=waiver_reasons,       # From parse_waive_items()
    waived_tag="[WAIVER]"            # Type 3/4 use [WAIVER]
)

Example 4: Backward Compatible (List)
--------------------------------------
return self.build_complete_output(
    found_items=["item1", "item2"],        # List auto-converted
    missing_items=["missing1", "missing2"]  # List auto-converted
)

═══════════════════════════════════════════════════════════════════════════════
MIGRATION FROM v1.x TO v2.0
═══════════════════════════════════════════════════════════════════════════════

NO CHANGES REQUIRED! All existing code continues to work.

OPTIONAL ENHANCEMENT: Add metadata for better UX
------------------------------------------------
Old: missing_items = ["item1", "item2"]
New: missing_items = {
         "item1": {"line_number": 10, "file_path": "file.txt"},
         "item2": {"line_number": 20, "file_path": "file.txt"}
     }

See API_V2_MIGRATION_GUIDE.md for detailed migration examples.

═══════════════════════════════════════════════════════════════════════════════

Author: yyin
Date: 2025-12-16
Version: 2.0.0
"""

from typing import Dict, List, Any, Optional, Callable, Union
from pathlib import Path
from output_formatter import DetailItem, Severity, create_check_result, CheckResult


class OutputBuilderMixin:
    """
    Mixin class providing unified API for building CheckResult outputs.
    
    ═══════════════════════════════════════════════════════════════════════════
    USAGE PATTERNS
    ═══════════════════════════════════════════════════════════════════════════
    
    Pattern A: ONE-STEP (RECOMMENDED for most cases)
    ------------------------------------------------
    class MyChecker(BaseChecker, OutputBuilderMixin):
        def execute_check(self):
            # Parse your data
            found, missing = self.parse_data()
            
            # One call builds everything
            return self.build_complete_output(
                found_items=found,
                missing_items=missing
            )
    
    Pattern B: STEP-BY-STEP (For custom group logic)
    -------------------------------------------------
    class MyChecker(BaseChecker, OutputBuilderMixin):
        def execute_check(self):
            # Build details
            details = self.build_details_from_items(
                found_items=found,
                missing_items=missing
            )
            
            # Build groups with custom logic
            groups = self.build_result_groups(
                found_items=found,
                missing_items=missing
            )
            
            # Customize groups if needed
            groups['info_groups']['INFO03'] = {...}
            
            # Assemble result
            return self.build_check_result(
                value=len(found),
                is_pass=len(missing) == 0,
                details=details,
                **groups
            )
    
    Pattern C: HELPER METHODS (For complex parsing)
    ------------------------------------------------
    class MyChecker(BaseChecker, OutputBuilderMixin):
        def execute_check(self):
            # Use helper for metadata extraction
            metadata = self.extract_metadata_from_lines(
                lines=file_lines,
                pattern=r'Item: (\\w+)'
            )
            
            # Build with metadata
            return self.build_complete_output(
                found_items=metadata['found'],
                missing_items=metadata['missing']
            )
    
    ═══════════════════════════════════════════════════════════════════════════
    KEY METHODS (API v2.0)
    ═══════════════════════════════════════════════════════════════════════════
    
    🌟 build_complete_output()
       └─ One-step solution: items → CheckResult
       └─ Features: Auto waiver=0, metadata, severity control
       └─ Returns: Complete CheckResult ready to return
    
    🔧 build_details_from_items()
       └─ Build DetailItem list from categorized items
       └─ Features: Metadata extraction, custom formatting
       └─ Returns: List[DetailItem] sorted by severity
    
    🔧 build_result_groups()
       └─ Build INFO/ERROR/WARN groups
       └─ Features: Auto organization, waiver=0 support
       └─ Returns: Dict with info_groups, error_groups, warn_groups
    
    🔧 build_check_result()
       └─ Assemble CheckResult from components
       └─ Features: Type 1/2/3/4 compatibility
       └─ Returns: CheckResult object
    
    🛠️ extract_metadata_from_lines()
       └─ Helper: Parse file and extract metadata
       └─ Features: Regex pattern matching, line tracking
       └─ Returns: Dict with items and metadata
    
    ═══════════════════════════════════════════════════════════════════════════
    COMPATIBILITY
    ═══════════════════════════════════════════════════════════════════════════
    
    ✅ Type 1: Value/existence checks (with/without waivers)
    ✅ Type 2: Pattern matching checks (pattern_items)
    ✅ Type 3: Item-based waivers (pattern waivers)
    ✅ Type 4: Value-based waivers (waiver values)
    ✅ Backward compatible with v1.x List[str] parameters
    ✅ Forward compatible with v2.0 Dict[str, Dict] parameters
    
    ═══════════════════════════════════════════════════════════════════════════
    """
    
    # =========================================================================
    # Pattern 1: Build Detail Items from Categorized Data
    # =========================================================================
    
    def build_details_from_items(
        self,
        found_items: Optional[Dict[str, Dict[str, Any]]] = None,
        missing_items: Optional[Dict[str, Dict[str, Any]]] = None,
        waived_items: Optional[Dict[str, Dict[str, Any]]] = None,
        unused_waivers: Optional[Dict[str, Dict[str, Any]]] = None,
        waive_dict: Optional[Dict[str, str]] = None,
        default_file: str = "N/A",
        name_extractor: Optional[Callable[[str, Dict[str, Any]], str]] = None,
        found_reason: str = "Item found",
        missing_reason: str = "Item not found",
        missing_severity: Optional[Severity] = None,
        waived_base_reason: str = "Item not found",
        unused_waiver_reason: str = "Waiver defined but no violation matched",
        waived_tag: str = "[WAIVER]",
        convert_to_info: bool = False
    ) -> List[DetailItem]:
        """
        Build DetailItem list from categorized items (found/missing/waived/unused).
        
        **API v2.0 CHANGES:**
        - All item parameters now accept Union[Dict, List] for flexibility
        - Dict format: {item_name: {'line_number': 123, 'file_path': '...', ...}}
          Enables metadata preservation for source_file/line_number display
        - List format: [item_name] - backward compatible, auto-converted to Dict
        - Dict format is RECOMMENDED for new code
        
        This is the most common pattern used across all checker types.
        Automatically creates INFO items for found/waived, FAIL for missing, WARN for unused.
        
        Args:
            found_items: Dict[item_name, metadata] or List[item_name] - Items that passed checks
                metadata should contain: 'line_number', 'file_path', 'line_content' (optional)
            missing_items: Dict[item_name, metadata] or List[item_name] - Items that failed checks (unwaived)
                metadata support added in v2.0 for preserving source file/line info
            waived_items: Dict[item_name, metadata] or List[item_name] - Items that failed but were waived
                metadata support added in v2.0
            unused_waivers: Dict[item_name, metadata] or List[item_name] - Waivers that weren't needed
                metadata support added in v2.0
            waive_dict: Dict[item_name, reason] - Waiver reasons from parse_waive_items()
            default_file: Default file path when metadata missing
            name_extractor: Optional function(item_name, metadata) -> display_name
                Used to extract custom names (e.g., file paths from line_content)
            found_reason: Reason template for found items
            missing_reason: Reason template for missing items (unwaived)
            waived_base_reason: Base reason for waived items (will add [WAIVER] tag)
            unused_waiver_reason: Reason template for unused waivers
        
        Returns:
            List[DetailItem] sorted by severity (INFO, FAIL, WARN) and name
        
        Example:
            # Basic usage with found/missing items
            details = self.build_details_from_items(
                found_items={'clk1': {'line_number': 10, 'file_path': 'log.txt'}},
                missing_items=['clk2'],
                default_file='timing.log'
            )
            
            # With waiver support
            details = self.build_details_from_items(
                found_items=found_dict,
                missing_items=unwaived_list,
                waived_items=waived_list,
                unused_waivers=unused_list,
                waive_dict=waiver_reasons,
                found_reason="Clock found in design",
                missing_reason="Required clock not found",
                waived_base_reason="Clock not found"
            )
            
            # With custom name extractor (e.g., extract report file paths)
            def extract_report_path(name, metadata):
                content = metadata.get('line_content', '')
                if '>' in content:
                    return content.split('>')[-1].strip()
                return name
            
            details = self.build_details_from_items(
                found_items=found_dict,
                name_extractor=extract_report_path
            )
        """
        details = []
        
        # INFO: Waived items first (Type 1/2 waiver=0 or Type 3/4 waivers)
        if waived_items:
            for item_name in sorted(set(waived_items.keys())):
                metadata = waived_items[item_name]
                waiver_reason = waive_dict.get(item_name, '') if waive_dict else ''
                
                # Format reason with tag
                # Priority: format_waiver_reason (Type 3/4) > simple format (Type 1/2)
                if hasattr(self, 'format_waiver_reason') and waived_tag == "[WAIVER]":
                    # Type 3/4: Use WaiverHandlerMixin's formatter
                    reason = self.format_waiver_reason(
                        base_reason=waived_base_reason,
                        waiver_reason=waiver_reason,
                        add_tag=True
                    )
                else:
                    # Type 1/2 or custom tags: Simple format
                    # Pattern: "base_reason: waiver_reason[TAG]" or "base_reason[TAG]"
                    if waiver_reason:
                        reason = f"{waived_base_reason}: {waiver_reason}{waived_tag}"
                    else:
                        reason = f"{waived_base_reason}{waived_tag}" if waived_base_reason else waived_tag
                
                details.append(DetailItem(
                    severity=Severity.INFO,
                    name=item_name,
                    line_number=metadata.get('line_number', 0),
                    file_path=metadata.get('file_path', default_file),
                    reason=reason
                ))
        
        # INFO: Found items
        if found_items:
            for item_name in sorted(found_items.keys()):
                metadata = found_items[item_name]
                # Extract display name
                display_name = item_name
                if name_extractor:
                    display_name = name_extractor(item_name, metadata)
                
                # Support callable reason (lambda) - call it with item metadata
                reason_text = found_reason(metadata) if callable(found_reason) else found_reason
                
                details.append(DetailItem(
                    severity=Severity.INFO,
                    name=display_name,
                    line_number=metadata.get('line_number', 0),
                    file_path=metadata.get('file_path', default_file),
                    reason=reason_text
                ))
        
        # FAIL or INFO: Unwaived missing items (convert to INFO if waiver=0)
        if missing_items:
            # API v2.0: Determine severity (support explicit missing_severity parameter)
            if missing_severity is None:
                final_missing_severity = Severity.INFO if convert_to_info else Severity.FAIL
            else:
                final_missing_severity = Severity.INFO if convert_to_info else missing_severity
            
            for item_name in sorted(missing_items.keys()):
                metadata = missing_items[item_name]
                # Extract display name (v2.0: support name_extractor for missing items too)
                display_name = item_name
                if name_extractor:
                    display_name = name_extractor(item_name, metadata)
                
                # Support callable reason (lambda) - call it with item metadata
                reason_text = missing_reason(metadata) if callable(missing_reason) else missing_reason
                
                details.append(DetailItem(
                    severity=final_missing_severity,
                    name=display_name,
                    line_number=metadata.get('line_number', 0),
                    file_path=metadata.get('file_path', default_file),
                    reason=reason_text
                ))
        
        # WARN or INFO: Unused waivers (convert to INFO if waiver=0)
        if unused_waivers:
            unused_severity = Severity.INFO if convert_to_info else Severity.WARN
            tag = "[WAIVED_AS_INFO]" if convert_to_info else "[WAIVER]"
            
            for item_name in sorted(set(unused_waivers.keys())):
                metadata = unused_waivers[item_name]
                waiver_reason = waive_dict.get(item_name, '') if waive_dict else ''
                
                # Format: "base_reason: waiver_reason[TAG]" or "base_reason[TAG]"
                if waiver_reason:
                    reason = f"{unused_waiver_reason}: {waiver_reason}{tag}"
                else:
                    reason = f"{unused_waiver_reason}{tag}"
                
                details.append(DetailItem(
                    severity=unused_severity,
                    name=item_name,
                    line_number=metadata.get('line_number', 0),
                    file_path=metadata.get('file_path', default_file),
                    reason=reason
                ))
        
        return details
    
    # =========================================================================
    # Pattern 2: Build Result Groups from Categorized Items
    # =========================================================================
    
    def build_result_groups(
        self,
        found_items: Optional[Dict[str, Dict[str, Any]]] = None,
        missing_items: Optional[Dict[str, Dict[str, Any]]] = None,
        waived_items: Optional[Dict[str, Dict[str, Any]]] = None,
        unused_waivers: Optional[Dict[str, Dict[str, Any]]] = None,
        name_extractor: Optional[Callable[[str, Dict[str, Any]], str]] = None,
        found_desc: str = "Items found",
        missing_desc: str = "Items not found",
        waived_desc: str = "Items waived",
        unused_desc: str = "Unused waivers",
        convert_to_info: bool = False
    ) -> Dict[str, Dict[str, Any]]:
        """
        Build result groups (INFO/ERROR/WARN) from categorized items.
        
        **API v2.0 CHANGES:**
        - All item parameters now accept Union[Dict, List] for flexibility
        - Dict format: {item_name: metadata} - preserves metadata (not displayed in groups)
        - List format: [item_name] - backward compatible, auto-converted to Dict
        - Groups only show item names (via .keys()), not metadata
        
        Creates standardized group structure:
        - INFO01: Waived items (if any)
        - INFO02: Found items (if any)
        - ERROR01: Missing items (if any)
        - WARN01: Unused waivers (if any)
        
        Args:
            found_items: Dict[item_name, metadata] or List[item_name] - Successfully found items
            missing_items: Dict[item_name, metadata] or List[item_name] - Unwaived missing items
            waived_items: Dict[item_name, metadata] or List[item_name] - Waived items
            unused_waivers: Dict[item_name, metadata] or List[item_name] - Unused waiver entries
            name_extractor: Optional function to extract display names from found_items
            found_desc: Description for INFO02 group
            missing_desc: Description for ERROR01 group
            waived_desc: Description for INFO01 group
            unused_desc: Description for WARN01 group
        
        Returns:
            Dict with 'info_groups', 'error_groups', 'warn_groups' keys
        
        Example:
            # Basic usage
            groups = self.build_result_groups(
                found_items={'clk1': {...}, 'clk2': {...}},
                missing_items=['clk3'],
                found_desc="Clocks found in design",
                missing_desc="Required clocks not found"
            )
            
            # With waiver support
            groups = self.build_result_groups(
                found_items=found_dict,
                missing_items=unwaived_list,
                waived_items=waived_list,
                unused_waivers=unused_list,
                waived_desc="Missing clocks can be waived",
                unused_desc="Unused clock waivers"
            )
            
            # Use in create_check_result
            result = create_check_result(
                value=len(found_items),
                is_pass=len(missing_items) == 0,  # Works with both Dict and List
                details=details,
                **groups  # Unpacks info_groups, error_groups, warn_groups
            )
        """
        info_groups = {}
        error_groups = {}
        warn_groups = {}
        
        # INFO01: Waived items (always first if present)
        if waived_items:
            # Don't append [WAIVED_INFO] to items - tag is in group description
            # (DetailItem.reason already contains the tag for report display)
            waived_items_for_group = sorted(set(waived_items))
            
            info_groups["INFO01"] = {
                "description": waived_desc,
                "items": waived_items_for_group
            }
        
        # INFO02 (or INFO01 if no waived): Found items (with custom name extraction)
        if found_items:
            found_item_names = []
            for item_name in sorted(found_items.keys()):
                if name_extractor:
                    metadata = found_items[item_name]
                    display_name = name_extractor(item_name, metadata)
                    found_item_names.append(display_name)
                else:
                    found_item_names.append(item_name)
            
            # Use INFO02 if waived_items exist, otherwise INFO01
            group_key = "INFO02" if waived_items else "INFO01"
            info_groups[group_key] = {
                "description": found_desc,
                "items": found_item_names
            }
        
        # Type 1/2 waiver=0 mode: Convert ERROR01 and WARN01 to INFO groups
        if convert_to_info:
            # Missing items become INFO (WAIVED AS INFO)
            if missing_items:
                # Determine next INFO group number
                next_info_num = len(info_groups) + 1
                info_key = f"INFO{next_info_num:02d}"
                info_groups[info_key] = {
                    "description": f"[WAIVED_AS_INFO]: {missing_desc}",
                    "items": sorted(set(missing_items.keys()))
                }
            
            # Unused waivers become INFO (WAIVED AS INFO)
            if unused_waivers:
                next_info_num = len(info_groups) + 1
                info_key = f"INFO{next_info_num:02d}"
                info_groups[info_key] = {
                    "description": f"[WAIVED_AS_INFO]: {unused_desc}",
                    "items": sorted(set(unused_waivers.keys()))
                }
        else:
            # Normal mode: ERROR01 and WARN01
            # ERROR01: Missing items
            if missing_items:
                error_groups["ERROR01"] = {
                    "description": missing_desc,
                    "items": sorted(set(missing_items.keys()))
                }
            
            # WARN01: Unused waivers
            if unused_waivers:
                warn_groups["WARN01"] = {
                    "description": unused_desc,
                    "items": sorted(set(unused_waivers.keys()))
                }
        
        return {
            'info_groups': info_groups,
            'error_groups': error_groups,
            'warn_groups': warn_groups
        }
    
    # =========================================================================
    # Pattern 3: Extract Metadata from Parsing Results
    # =========================================================================
    
    def extract_item_metadata(
        self,
        item_name: str,
        found_items: Dict[str, Dict[str, Any]],
        default_file: str = "N/A"
    ) -> Dict[str, Any]:
        """
        Extract metadata for a single item from parsing results.
        
        Args:
            item_name: Name of the item to extract metadata for
            found_items: Dict from parsing results (e.g., parse_log_with_patterns)
            default_file: Default file path if item not found
        
        Returns:
            Dict with 'line_number', 'file_path', 'line_content' (if available)
        
        Example:
            metadata = self.extract_item_metadata('clk1', found_dict)
            # Returns: {'line_number': 42, 'file_path': '/path/to/log.txt', 'line_content': '...'}
        """
        if item_name in found_items:
            return found_items[item_name]
        
        return {
            'line_number': 0,
            'file_path': default_file,
            'line_content': ''
        }
    
    # =========================================================================
    # Pattern 4: Custom Name Extractors (Common Patterns)
    # =========================================================================
    
    @staticmethod
    def extract_path_after_delimiter(
        item_name: str,
        metadata: Dict[str, Any],
        delimiter: str = '>',
        fallback_to_name: bool = True
    ) -> str:
        """
        Extract path/name from line_content after a delimiter.
        
        Common use case: Extract report file paths from lines like:
        "Generating report > /path/to/report.rpt"
        
        Args:
            item_name: Original item name (used as fallback)
            metadata: Metadata dict with 'line_content' key
            delimiter: Character to split on (default: '>')
            fallback_to_name: Return item_name if extraction fails
        
        Returns:
            Extracted path or item_name
        
        Example:
            # Define extractor for your checker
            def my_name_extractor(name, metadata):
                return OutputBuilderMixin.extract_path_after_delimiter(
                    name, metadata, delimiter='>'
                )
            
            # Use in build_details_from_items
            details = self.build_details_from_items(
                found_items=found_dict,
                name_extractor=my_name_extractor
            )
        """
        line_content = metadata.get('line_content', '')
        if delimiter in line_content:
            parts = line_content.split(delimiter)
            if len(parts) > 1:
                return parts[-1].strip()
        
        return item_name if fallback_to_name else ''
    
    @staticmethod
    def extract_filename_from_path(
        item_name: str,
        metadata: Dict[str, Any],
        use_line_content: bool = True
    ) -> str:
        """
        Extract just the filename from a full path in metadata.
        
        Args:
            item_name: Original item name
            metadata: Metadata dict
            use_line_content: Try to extract from line_content first
        
        Returns:
            Filename without directory path
        
        Example:
            extractor = lambda n, m: OutputBuilderMixin.extract_filename_from_path(n, m)
            details = self.build_details_from_items(
                found_items=found_dict,
                name_extractor=extractor
            )
        """
        # Try line_content first
        if use_line_content:
            line_content = metadata.get('line_content', '')
            if line_content:
                # Handle various path formats
                for delimiter in ['>', ':', '=']:
                    if delimiter in line_content:
                        path_part = line_content.split(delimiter)[-1].strip()
                        return Path(path_part).name
        
        # Fallback to file_path in metadata
        file_path = metadata.get('file_path', item_name)
        return Path(file_path).name
    
    # =========================================================================
    # Pattern 5: Build Complete CheckResult
    # =========================================================================
    
    def build_check_result(
        self,
        value: Any,
        is_pass: bool,
        details: List[DetailItem],
        info_groups: Optional[Dict[str, Dict[str, Any]]] = None,
        error_groups: Optional[Dict[str, Dict[str, Any]]] = None,
        warn_groups: Optional[Dict[str, Dict[str, Any]]] = None,
        has_pattern_items: bool = False,
        has_waiver_value: bool = False
    ) -> CheckResult:
        """
        Build complete CheckResult with all components.
        
        Convenience wrapper around output_formatter.create_check_result()
        with standardized parameter handling.
        
        Args:
            value: Check value (count, status, etc.)
            is_pass: Whether check passed
            details: List of DetailItem objects
            info_groups: INFO group dict
            error_groups: ERROR group dict
            warn_groups: WARN group dict
            has_pattern_items: Type 2/3 indicator
            has_waiver_value: Type 3/4 indicator
        
        Returns:
            CheckResult object
        
        Example:
            # Simple usage (Type 1)
            return self.build_check_result(
                value=len(found_items),
                is_pass=len(missing_items) == 0,  # Works with both Dict and List
                details=details,
                info_groups=groups['info_groups'],
                error_groups=groups['error_groups']
            )
            
            # With waivers (Type 3)
            return self.build_check_result(
                value=len(found_items),
                is_pass=len(unwaived_missing) == 0,  # Works with both Dict and List
                details=details,
                **groups,  # Unpacks all group dicts
                has_pattern_items=True,
                has_waiver_value=True
            )
        """
        return create_check_result(
            value=value,
            is_pass=is_pass,
            has_pattern_items=has_pattern_items,
            has_waiver_value=has_waiver_value,
            details=details,
            info_groups=info_groups or {},
            error_groups=error_groups or {},
            warn_groups=warn_groups or {},
            item_desc=getattr(self, 'item_desc', '')
        )
    
    # =========================================================================
    # Pattern 6: Complete Output Building Pipeline (One-Step Solution)
    # =========================================================================
    
    def build_complete_output(
        self,
        found_items: Optional[Union[Dict[str, Dict[str, Any]], List[str]]] = None,
        missing_items: Optional[Union[Dict[str, Dict[str, Any]], List[str]]] = None,
        waived_items: Optional[Union[Dict[str, Dict[str, Any]], List[str]]] = None,
        unused_waivers: Optional[Union[Dict[str, Dict[str, Any]], List[str]]] = None,
        extra_items: Optional[Dict[str, Dict[str, Any]]] = None,
        waive_dict: Optional[Dict[str, str]] = None,
        value: Any = "N/A",
        has_pattern_items: bool = False,
        has_waiver_value: bool = False,
        default_file: str = "N/A",
        name_extractor: Optional[Callable[[str, Dict[str, Any]], str]] = None,
        found_reason: str = "Item found",
        missing_reason: str = "Item not found",
        missing_severity: Optional[Severity] = None,  # None=auto (FAIL), or specify INFO/WARN/FAIL
        waived_base_reason: str = "Item not found",
        unused_waiver_reason: str = "Waiver defined but no violation matched",
        extra_reason: str = "Unexpected item found",
        extra_severity: Optional[Severity] = None,  # None=auto (WARN for Type2, FAIL for manual)
        waived_tag: str = "[WAIVER]",
        found_desc: str = "Items found",
        missing_desc: str = "Items not found",
        waived_desc: str = "Items waived",
        unused_desc: str = "Unused waivers",
        extra_desc: str = "Unexpected items need review"
    ) -> CheckResult:
        """
        Build complete CheckResult in one step (details + groups + result).
        
        This is the ultimate convenience method that combines:
        1. build_details_from_items()
        2. build_result_groups()
        3. build_check_result()
        
        Perfect for simple checkers where you just want to pass in the data
        and get back a complete CheckResult.
        
        API v2.0 CHANGES:
        - All item parameters now accept Union[Dict, List] for flexibility
        - Dict format: {item_name: {metadata}} - enables metadata (source_file, line_number)
        - List format: [item_name] - backward compatible, auto-converted to Dict
        - Dict format is RECOMMENDED for new code to preserve metadata
        
        Args:
            found_items: Dict[item_name, metadata] or List[item_name] - Found items
            missing_items: Dict[item_name, metadata] or List[item_name] - Unwaived missing items
            waived_items: Dict[item_name, metadata] or List[item_name] - Waived items
            unused_waivers: Dict[item_name, metadata] or List[item_name] - Unused waivers
            extra_items: Dict[item_name, metadata] or List[item_name] - Extra items not in pattern (Type 2 only)
            waive_dict: Dict[item_name, reason] - Waiver reasons
            value: Check value (auto-calculated from found_items if not provided)
            has_pattern_items: Type 2/3 flag
            has_waiver_value: Type 3/4 flag
            default_file: Default file path
            name_extractor: Optional name extraction function
            found_reason: Reason for found items
            missing_reason: Reason for missing items
            waived_base_reason: Base reason for waived items
            unused_waiver_reason: Reason for unused waivers
            extra_reason: Reason for extra items (Type 2)
            waived_tag: Tag for waived items (default: [WAIVER], Type 1/2 use [WAIVED_INFO])
            found_desc: Description for found items group
            missing_desc: Description for missing items group
            waived_desc: Description for waived items group
            unused_desc: Description for unused waivers group
            extra_desc: Description for extra items group (Type 2)
        
        Returns:
            Complete CheckResult ready to return from execute_check()
        
        Example:
            # Type 1: Simple value check
            return self.build_complete_output(
                found_items=found_dict,
                missing_items=missing_list,
                found_reason="Clock domain found",
                missing_reason="Required clock domain not found"
            )
            
            # Type 2: With extra_items (items not in pattern)
            return self.build_complete_output(
                found_items=found_dict,
                missing_items=missing_list,
                extra_items=extra_dict,
                has_pattern_items=True,
                found_reason="Expected command found",
                missing_reason="Required command not found",
                extra_reason="Unexpected command found",
                extra_desc="Unexpected commands need review"
            )
            
            # Type 3: Full usage with waivers
            return self.build_complete_output(
                found_items=found_dict,
                missing_items=unwaived_list,
                waived_items=waived_list,
                unused_waivers=unused_list,
                waive_dict=waiver_reasons,
                has_pattern_items=True,
                has_waiver_value=True,
                name_extractor=lambda n, m: m.get('line_content', n).split('>')[-1].strip(),
                found_reason="Path group found in log",
                missing_reason="Required path group NOT found",
                waived_base_reason="Required path group NOT found",
                found_desc="Path groups found and need verification",
                missing_desc="Missing required path groups",
                waived_desc="Missing path groups can be waived"
            )
        """
        # =====================================================================
        # API v2.0: Automatic Type Conversion (List → Dict for backward compat)
        # =====================================================================
        # Convert List[str] to Dict for unified interface
        def _ensure_dict(items: Optional[Union[Dict, List]]) -> Optional[Dict]:
            """Convert List[str] to Dict[str, Dict] for unified processing."""
            if items is None:
                return None
            if isinstance(items, list):
                # List → Dict with empty metadata
                return {item: {} for item in items}
            return items  # Already Dict
        
        # Apply conversion to all items parameters
        found_items = _ensure_dict(found_items)
        missing_items = _ensure_dict(missing_items)
        waived_items = _ensure_dict(waived_items)
        unused_waivers = _ensure_dict(unused_waivers)
        
        # Auto-calculate value if not provided
        if value == "N/A" and found_items is not None:
            value = len(found_items)
        
        # =====================================================================
        # Type 1/2 Automatic waiver=0 Detection and Handling
        # =====================================================================
        # Check if this is Type 1/2 with waiver=0 (FAIL/WARN→INFO conversion)
        convert_to_info = False
        auto_waived_items = {}  # Dict format for API v2.0
        auto_waive_dict = {}
        
        if hasattr(self, 'should_convert_fail_to_info') and callable(getattr(self, 'should_convert_fail_to_info')):
            convert_to_info = self.should_convert_fail_to_info()
            
            if convert_to_info:
                # Auto-fetch waive_items from config for Type 1/2
                if hasattr(self, 'get_waivers') and callable(getattr(self, 'get_waivers')):
                    waivers = self.get_waivers()
                    if waivers:
                        waive_items_raw = waivers.get('waive_items', [])
                        if waive_items_raw and hasattr(self, 'parse_waive_items'):
                            auto_waive_dict = self.parse_waive_items(waive_items_raw)
                            # Convert to Dict format for API v2.0 compatibility
                            auto_waived_items = {item: {} for item in auto_waive_dict.keys()}
                
                # Override waived_items and waive_dict if auto-detected AND not already provided
                if auto_waived_items and not waived_items:
                    waived_items = auto_waived_items
                    waive_dict = auto_waive_dict
                    waived_tag = "[WAIVED_INFO]"  # Type 1/2 use [WAIVED_INFO]
                    # Auto-adjust waived_desc for Type 1/2 if still using default
                    if waived_desc == "Items waived":
                        waived_desc = "[WAIVED_INFO]: Waived information"
                    # Auto-set waived_base_reason for waiver=0 mode (use waive_items text as reason)
                    # In waiver=0, simple string waive_items have empty reason: {'text': ''}
                    # So we use the item name (the explanatory text) as the base reason
                    if waived_base_reason == "Item not found":
                        # Use first waive_items text as base reason, or keep default
                        waived_base_reason = next(iter(auto_waive_dict.keys())) if auto_waive_dict else waived_base_reason
                
                # Apply waiver logic ONLY to missing_reason (FAIL→INFO conversion)
                # found_reason stays unchanged because found items are already INFO
                is_pass_normal = not missing_items or len(missing_items) == 0
                if hasattr(self, 'apply_type1_type2_waiver') and callable(getattr(self, 'apply_type1_type2_waiver')):
                    is_pass, severity_str, converted_missing_reason = self.apply_type1_type2_waiver(
                        is_pass_normal_mode=is_pass_normal,
                        fail_reason=missing_reason,
                        info_reason=missing_reason  # Use same text for converted INFO
                    )
                    # Only override missing_reason (FAIL→INFO), not found_reason
                    missing_reason = converted_missing_reason
        
        # Calculate pass status
        if convert_to_info:
            is_pass = True  # Type 1/2 waiver=0 forces PASS
        else:
            is_pass = not missing_items or len(missing_items) == 0
            # Also check extra_items if they have FAIL severity
            if is_pass and extra_items and extra_severity == Severity.FAIL:
                is_pass = False  # Extra items with FAIL severity should cause failure
        
        # Build details
        details = self.build_details_from_items(
            found_items=found_items,
            missing_items=missing_items,
            waived_items=waived_items,
            unused_waivers=unused_waivers,
            waive_dict=waive_dict,
            default_file=default_file,
            name_extractor=name_extractor,
            found_reason=found_reason,
            missing_reason=missing_reason,
            waived_base_reason=waived_base_reason,
            unused_waiver_reason=unused_waiver_reason,
            waived_tag=waived_tag,
            convert_to_info=convert_to_info  # Pass waiver=0 flag
        )
        
        # Build groups
        groups = self.build_result_groups(
            found_items=found_items,
            missing_items=missing_items,
            waived_items=waived_items,
            unused_waivers=unused_waivers,
            name_extractor=name_extractor,
            found_desc=found_desc,
            missing_desc=missing_desc,
            waived_desc=waived_desc,
            unused_desc=unused_desc,
            convert_to_info=convert_to_info  # Pass waiver=0 flag
        )
        
        # Handle extra_items (Type 2: items not in pattern_items, or Type 1 violations)
        if extra_items:
            # Determine severity based on waiver=0 mode and explicit extra_severity
            if extra_severity is None:
                # Auto mode: WARN for Type 2, but allow override
                extra_severity_final = Severity.INFO if convert_to_info else Severity.WARN
            else:
                # Explicit severity provided (e.g., FAIL for Type 1 violations)
                extra_severity_final = Severity.INFO if convert_to_info else extra_severity
            
            # Format reason with tag if waiver=0 mode
            extra_reason_text = f"{extra_reason}[WAIVED_AS_INFO]" if convert_to_info else extra_reason
            
            # Insert extra items into details (after waived/found, before missing)
            # Find position after INFO items (before FAIL items)
            insert_pos = len(details)
            for i, detail in enumerate(details):
                if detail.severity == Severity.FAIL:
                    insert_pos = i
                    break
            
            # Create extra detail items
            extra_details = []
            for name in sorted(extra_items.keys()):
                meta = extra_items[name]
                # Support callable reason (lambda) - call it with item metadata
                if callable(extra_reason):
                    reason_text = extra_reason(meta)
                    if convert_to_info:
                        reason_text = f"{reason_text} [WAIVED_AS_INFO]"
                else:
                    reason_text = extra_reason_text
                
                extra_details.append(DetailItem(
                    severity=extra_severity_final,
                    name=name,
                    line_number=meta.get('line_number', 0),
                    file_path=meta.get('file_path', default_file),
                    reason=reason_text
                ))
            
            # Insert extra details at correct position
            details[insert_pos:insert_pos] = extra_details
            
            # Add extra_items to groups (INFO, WARN, or ERROR)
            extra_items_list = list(extra_items.keys())
            if convert_to_info:
                # Add to info_groups as WAIVED AS INFO
                if 'info_groups' not in groups:
                    groups['info_groups'] = {}
                # Determine next INFO group number
                next_info_num = len(groups['info_groups']) + 1
                info_key = f"INFO{next_info_num:02d}"
                # Add [WAIVED_AS_INFO] tag to description if not already present
                desc = f"[WAIVED_AS_INFO]: {extra_desc}" if not extra_desc.startswith("[WAIVED_AS_INFO]") else extra_desc
                groups['info_groups'][info_key] = {
                    "description": desc,
                    "items": extra_items_list
                }
            elif extra_severity_final == Severity.FAIL:
                # Add to error_groups as FAIL
                if 'error_groups' not in groups:
                    groups['error_groups'] = {}
                groups['error_groups']["ERROR01"] = {
                    "description": extra_desc,
                    "items": extra_items_list
                }
            else:
                # Add to warn_groups as WARN (default Type 2 behavior)
                if 'warn_groups' not in groups:
                    groups['warn_groups'] = {}
                groups['warn_groups']["WARN01"] = {
                    "description": extra_desc,
                    "items": extra_items_list
                }
        
        # Build final result
        return self.build_check_result(
            value=value,
            is_pass=is_pass,
            details=details,
            has_pattern_items=has_pattern_items,
            has_waiver_value=has_waiver_value,
            **groups
        )
