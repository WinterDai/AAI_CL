#!/usr/bin/env python3
"""
WaiverHandlerMixin - Reusable Waiver Processing Template

This mixin provides standardized waiver handling patterns extracted from real checkers.
Designed to work with BaseChecker and can be combined with other mixins.

Pattern Coverage (extracted from 15+ checkers):
- Pattern 1: Simple waiver matching (wildcard + exact match)
- Pattern 2: Parse waive_items (list vs dict format)
- Pattern 3: Classify items (waived vs unwaived)
- Pattern 4: Detect unused waivers
- Pattern 5: Format waiver reasons with [WAIVER] tag
- Pattern 6: Get waiver config (BaseChecker integration)
- Pattern 7: Waiver value handling
- Pattern 8: Type 1/2 waiver logic (waiver.value=0 → FAIL to INFO conversion)

Waiver Modes:
- Type 1/2: waiver.value=0 → Convert FAIL to INFO, force PASS [WAIVED_AS_INFO]
- Type 3/4: waiver.value>0, waive_items → Match and waive specific items [WAIVER]

Source Checkers Analyzed:
- IMP-10-0-0-10 (Type 3/4 waiver logic)
- IMP-5-0-0-00 (Type 1/2 waiver.value=0 logic)
- IMP-7-0-0-00/01/02/03/04 (wildcard matching)
- IMP-3-0-0-00/01/02/03 (pattern matching)

Author: yyin
Date: 2025-12-08
"""

import re
from typing import List, Dict, Any, Tuple, Optional


class WaiverHandlerMixin:
    """
    Mixin providing reusable waiver handling patterns.
    
    Design:
    - Standalone methods (no BaseChecker dependency required)
    - Optional integration with BaseChecker.get_waivers()
    - Support multiple waive_items formats (list/dict)
    - Wildcard and regex pattern matching
    - Unused waiver detection
    
    Usage Patterns:
    
    Pattern 1: Simple wildcard matching
        matched = self.matches_waiver_pattern(
            item='my_module/submodule',
            waive_patterns=['my_module/*', 'other_*']
        )
    
    Pattern 2: Parse waive_items from YAML
        waive_dict = self.parse_waive_items(waive_items_raw)
        # Handles both: ['item1', 'item2'] and [{'name': 'item1', 'reason': '...'}]
    
    Pattern 3: Classify items (waived vs unwaived)
        waived, unwaived = self.classify_items_by_waiver(
            all_items=['item1', 'item2', 'item3'],
            waive_dict={'item1': 'Known issue', 'item2': ''}
        )
        # waived = ['item1', 'item2']
        # unwaived = ['item3']
    
    Pattern 4: Detect unused waivers
        unused = self.find_unused_waivers(
            waive_dict={'item1': '', 'item2': '', 'item3': ''},
            items_found=['item1']
        )
        # unused = ['item2', 'item3']
    
    Pattern 5: Format waiver reason
        reason = self.format_waiver_reason(
            base_reason='Missing in log',
            waiver_reason='Known limitation',
            add_tag=True
        )
        # reason = 'Missing in log: Known limitation[WAIVER]'
    """
    
    # =========================================================================
    # Pattern 1: Waiver Pattern Matching
    # =========================================================================
    
    def matches_waiver_pattern(
        self, 
        item: str, 
        waive_patterns: List[str],
        case_sensitive: bool = False
    ) -> bool:
        """
        Check if item matches any waiver pattern.
        
        Supports:
        - Exact string matching
        - Wildcard patterns (e.g., 'module/*', '*_test')
        - Regex patterns (when pattern starts with 'regex:')
        
        Args:
            item: Item name to check
            waive_patterns: List of waiver patterns
            case_sensitive: Whether matching is case-sensitive (default: False)
        
        Returns:
            True if item matches any pattern, False otherwise
        
        Example:
            # Wildcard matching
            self.matches_waiver_pattern('lib/std_cell', ['lib/*'])  # True
            
            # Exact matching
            self.matches_waiver_pattern('cgdefault', ['cgdefault', 'default'])  # True
            
            # Regex matching
            self.matches_waiver_pattern('module_123', ['regex:module_\\d+'])  # True
        """
        for pattern in waive_patterns:
            # Handle regex patterns (explicit prefix)
            if pattern.startswith('regex:'):
                regex = pattern[6:]  # Remove 'regex:' prefix
                flags = 0 if case_sensitive else re.IGNORECASE
                if re.search(regex, item, flags):
                    return True
            
            # Handle wildcard patterns
            elif '*' in pattern or '?' in pattern:
                # Convert shell wildcard to regex
                regex_pattern = pattern.replace('.', r'\.')  # Escape dots
                regex_pattern = regex_pattern.replace('*', '.*')  # * -> .*
                regex_pattern = regex_pattern.replace('?', '.')   # ? -> .
                regex_pattern = f'^{regex_pattern}$'  # Anchor to full match
                
                flags = 0 if case_sensitive else re.IGNORECASE
                if re.match(regex_pattern, item, flags):
                    return True
            
            # Exact match
            else:
                if case_sensitive:
                    if pattern == item:
                        return True
                else:
                    if pattern.lower() == item.lower():
                        return True
        
        return False
    
    # =========================================================================
    # Pattern 2: Parse Waive Items
    # =========================================================================
    
    def parse_waive_items(
        self, 
        waive_items_raw: List[Any],
        name_key: str = 'name',
        reason_key: str = 'reason'
    ) -> Dict[str, str]:
        """
        Parse waive_items from YAML configuration.
        
        Handles two formats:
        1. Simple list: ['item1', 'item2']
        2. Dict list: [{'name': 'item1', 'reason': 'why'}, ...]
        
        Args:
            waive_items_raw: Raw waive_items from YAML
            name_key: Key for item name in dict format (default: 'name')
            reason_key: Key for reason in dict format (default: 'reason')
        
        Returns:
            Dict mapping item names to reasons (empty string if no reason)
        
        Example:
            # Simple list
            result = self.parse_waive_items(['cgdefault', 'default'])
            # result = {'cgdefault': '', 'default': ''}
            
            # Dict list
            items = [
                {'name': 'cgdefault', 'reason': 'No clock gating'},
                {'name': 'default', 'reason': 'Not used'}
            ]
            result = self.parse_waive_items(items)
            # result = {'cgdefault': 'No clock gating', 'default': 'Not used'}
        """
        if not waive_items_raw:
            return {}
        
        waive_dict = {}
        
        # Check first item to determine format
        if isinstance(waive_items_raw[0], dict):
            # Dict format: [{'name': 'item1', 'reason': '...'}, ...]
            for item in waive_items_raw:
                name = item.get(name_key, '')
                reason = item.get(reason_key, '')
                if name:
                    waive_dict[name] = reason
        else:
            # Simple list format: ['item1', 'item2', ...]
            for item in waive_items_raw:
                waive_dict[str(item)] = ''
        
        return waive_dict
    
    # =========================================================================
    # Pattern 3: Classify Items by Waiver Status
    # =========================================================================
    
    def classify_items_by_waiver(
        self,
        all_items: List[str],
        waive_dict: Dict[str, str],
        use_pattern_matching: bool = False,
        case_sensitive: bool = False
    ) -> Tuple[List[str], List[str]]:
        """
        Classify items into waived and unwaived groups.
        
        Args:
            all_items: All items to classify
            waive_dict: Dict of waiver patterns/names to reasons
            use_pattern_matching: If True, use matches_waiver_pattern()
                                 If False, use exact key matching (default)
            case_sensitive: For pattern matching (default: False)
        
        Returns:
            Tuple of (waived_items, unwaived_items)
        
        Example:
            # Exact matching
            waived, unwaived = self.classify_items_by_waiver(
                all_items=['in2out', 'in2reg', 'cgdefault'],
                waive_dict={'cgdefault': 'No CG cells'}
            )
            # waived = ['cgdefault']
            # unwaived = ['in2out', 'in2reg']
            
            # Pattern matching
            waived, unwaived = self.classify_items_by_waiver(
                all_items=['lib1/cell1', 'lib1/cell2', 'lib2/cell1'],
                waive_dict={'lib1/*': 'Vendor lib'},
                use_pattern_matching=True
            )
            # waived = ['lib1/cell1', 'lib1/cell2']
            # unwaived = ['lib2/cell1']
        """
        waived_items = []
        unwaived_items = []
        
        for item in all_items:
            if use_pattern_matching:
                # Use pattern matching
                waive_patterns = list(waive_dict.keys())
                if self.matches_waiver_pattern(item, waive_patterns, case_sensitive):
                    waived_items.append(item)
                else:
                    unwaived_items.append(item)
            else:
                # Use exact key matching
                if item in waive_dict:
                    waived_items.append(item)
                else:
                    unwaived_items.append(item)
        
        return waived_items, unwaived_items
    
    # =========================================================================
    # Pattern 4: Find Unused Waivers
    # =========================================================================
    
    def find_unused_waivers(
        self,
        waive_dict: Dict[str, str],
        items_found: List[str],
        use_pattern_matching: bool = False,
        case_sensitive: bool = False
    ) -> List[str]:
        """
        Find waiver entries that don't match any found items.
        
        Useful for detecting unnecessary waivers in configuration.
        
        Args:
            waive_dict: Dict of waiver patterns/names to reasons
            items_found: List of items actually found/present
            use_pattern_matching: If True, check if waiver pattern matches any item
                                 If False, check exact key presence (default)
            case_sensitive: For pattern matching (default: False)
        
        Returns:
            List of unused waiver names/patterns
        
        Example:
            # Exact matching
            unused = self.find_unused_waivers(
                waive_dict={'cgdefault': '', 'default': '', 'unknown': ''},
                items_found=['cgdefault', 'default']
            )
            # unused = ['unknown']
            
            # Pattern matching
            unused = self.find_unused_waivers(
                waive_dict={'lib1/*': '', 'lib2/*': ''},
                items_found=['lib1/cell1'],
                use_pattern_matching=True
            )
            # unused = ['lib2/*']
        """
        unused = []
        
        for waiver_name in waive_dict.keys():
            if use_pattern_matching:
                # Check if pattern matches any item
                matched = any(
                    self.matches_waiver_pattern(item, [waiver_name], case_sensitive)
                    for item in items_found
                )
                if not matched:
                    unused.append(waiver_name)
            else:
                # Check exact presence
                if waiver_name not in items_found:
                    unused.append(waiver_name)
        
        return unused

    # =========================================================================
    # Pattern 4.1: Find Matching Waiver Entry
    # =========================================================================

    def match_waiver_entry(
        self,
        item: str,
        waive_dict: Dict[str, str],
        normalizer: Optional[Any] = None,
        case_sensitive: bool = False,
        allow_substring: bool = True
    ) -> Optional[str]:
        """
        Find the first waiver entry that matches the given item.

        Matching order (mirrors legacy checker behavior):
        1. Normalized exact match
        2. Wildcard pattern match (using matches_waiver_pattern)
        3. Substring containment (optional)

        Args:
            item: Item name to match
            waive_dict: Waiver mapping (name/pattern -> reason)
            normalizer: Optional callable to normalize both item and waiver key
            case_sensitive: Whether matching respects case
            allow_substring: Whether to consider substring containment as match

        Returns:
            The waiver key that matches the item, or None if no match found.
        """
        if not waive_dict:
            return None

        item_processed = normalizer(item) if normalizer else item
        item_cmp = item_processed if case_sensitive else item_processed.lower()

        for waiver_key in waive_dict.keys():
            if not waiver_key:
                continue

            waiver_processed = normalizer(waiver_key) if normalizer else waiver_key
            waiver_cmp = waiver_processed if case_sensitive else waiver_processed.lower()

            # 1. Exact match
            if item_cmp == waiver_cmp:
                return waiver_key

            # 2. Wildcard match
            if self.matches_waiver_pattern(
                item_processed,
                [waiver_processed],
                case_sensitive=case_sensitive
            ):
                return waiver_key

            # 3. Substring containment (both directions)
            if allow_substring:
                if waiver_cmp in item_cmp or item_cmp in waiver_cmp:
                    return waiver_key

        return None

    # =========================================================================
    # Pattern 4.2: Word-Level Waiver Matching (Golden Pattern)
    # =========================================================================
    
    def match_waiver_word_level(
        self,
        item: str,
        waive_dict: Dict[str, str],
        case_sensitive: bool = False
    ) -> Optional[str]:
        """
        Word-level waiver matching (extracted from Golden IMP-10-0-0-00).
        
        More flexible than substring matching - checks if all words in waiver
        appear in the item text, regardless of order or additional words.
        
        Matching strategies (in order):
        1. Word-level: All words in waiver appear in item (waiver_words ⊆ item_words)
        2. Substring: Either waiver in item or item in waiver
        
        Args:
            item: Item text to check (e.g., "SPEF Reading was skipped")
            waive_dict: Waiver mapping (name/pattern -> reason)
            case_sensitive: Whether matching respects case (default: False)
        
        Returns:
            The waiver key that matches the item, or None if no match found
        
        Example:
            # Word-level matching
            waive_dict = {'SPEF skipped': 'Design has no parasitics'}
            item = 'SPEF Reading was skipped'
            
            result = self.match_waiver_word_level(item, waive_dict)
            # result = 'SPEF skipped'
            # Because {'spef', 'skipped'} ⊆ {'spef', 'reading', 'was', 'skipped'}
            
            # Substring fallback
            waive_dict = {'Reading was skipped': 'Known issue'}
            result = self.match_waiver_word_level(item, waive_dict)
            # result = 'Reading was skipped'  (substring match)
        """
        if not waive_dict:
            return None
        
        item_cmp = item if case_sensitive else item.lower()
        item_words = set(item_cmp.split())
        
        for waiver_key in waive_dict.keys():
            if not waiver_key:
                continue
            
            waiver_cmp = waiver_key if case_sensitive else waiver_key.lower()
            waiver_words = set(waiver_cmp.split())
            
            # 1. Word-level match: all waiver words must appear in item
            if waiver_words.issubset(item_words):
                return waiver_key
            
            # 2. Substring containment (bidirectional fallback)
            if waiver_cmp in item_cmp or item_cmp in waiver_cmp:
                return waiver_key
        
        return None
    
    def is_item_waived_word_level(
        self,
        item: str,
        waive_dict: Dict[str, str],
        case_sensitive: bool = False
    ) -> Tuple[bool, Optional[str], str]:
        """
        Check if item is waived using word-level matching.
        
        Convenience wrapper around match_waiver_word_level that returns
        structured result including the waiver reason.
        
        Args:
            item: Item text to check
            waive_dict: Waiver mapping (name/pattern -> reason)
            case_sensitive: Whether matching respects case
        
        Returns:
            Tuple of (is_waived, matched_waiver_key, waiver_reason)
        
        Example:
            is_waived, waiver_key, reason = self.is_item_waived_word_level(
                item='SPEF Reading was skipped',
                waive_dict={'SPEF skipped': 'Design has no parasitics'}
            )
            # is_waived = True
            # waiver_key = 'SPEF skipped'
            # reason = 'Design has no parasitics'
        """
        matched_key = self.match_waiver_word_level(item, waive_dict, case_sensitive)
        
        if matched_key:
            return True, matched_key, waive_dict.get(matched_key, '')
        
        return False, None, ''

    # =========================================================================
    # Pattern 5: Format Waiver Reason
    # =========================================================================
    
    def format_waiver_reason(
        self,
        base_reason: str,
        waiver_reason: Optional[str] = None,
        add_tag: bool = True,
        separator: str = ': '
    ) -> str:
        """
        Format a reason string with optional waiver reason and [WAIVER] tag.
        
        Args:
            base_reason: Base reason message
            waiver_reason: Optional waiver-specific reason from config
            add_tag: Whether to append '[WAIVER]' tag (default: True)
            separator: Separator between base and waiver reason (default: ': ')
        
        Returns:
            Formatted reason string
        
        Example:
            # With waiver reason
            reason = self.format_waiver_reason(
                base_reason='Path group not found',
                waiver_reason='Design has no clock gating',
                add_tag=True
            )
            # reason = 'Path group not found: Design has no clock gating[WAIVER]'
            
            # Without waiver reason
            reason = self.format_waiver_reason(
                base_reason='Path group not found',
                add_tag=True
            )
            # reason = 'Path group not found[WAIVER]'
        """
        result = base_reason
        
        # Add waiver reason if provided
        if waiver_reason:
            result = f"{result}{separator}{waiver_reason}"
        
        # Add [WAIVER] tag if requested
        if add_tag:
            result = f"{result}[WAIVER]"
        
        return result
    
    # =========================================================================
    # Pattern 6: Get Waiver Config (Optional Integration)
    # =========================================================================
    
    def get_waiver_config(self) -> Dict[str, Any]:
        """
        Get waiver configuration from BaseChecker.
        
        This is an optional convenience method that integrates with BaseChecker.
        If self.get_waivers() exists (from BaseChecker), uses it.
        Otherwise returns empty dict.
        
        Returns:
            Dict with keys: 'value', 'waive_items', etc.
            Empty dict if get_waivers() not available
        
        Example:
            # In a checker class that inherits from BaseChecker and WaiverHandlerMixin
            waiver_config = self.get_waiver_config()
            waive_items_raw = waiver_config.get('waive_items', [])
            waive_dict = self.parse_waive_items(waive_items_raw)
        """
        if hasattr(self, 'get_waivers') and callable(getattr(self, 'get_waivers')):
            waivers = self.get_waivers()
            return waivers if waivers else {}
        return {}
    
    # =========================================================================
    # Pattern 7: Waiver Value Handling
    # =========================================================================
    
    def get_waiver_value(self, default: Any = 'N/A') -> Any:
        """
        Get waiver value from configuration.
        
        This is an optional convenience method for checkers using waiver.value.
        
        Args:
            default: Default value if not found (default: 'N/A')
        
        Returns:
            Waiver value or default
        
        Example:
            waiver_value = self.get_waiver_value(default=0)
            if waiver_value == 0:
                # Convert FAIL to INFO
        """
        waiver_config = self.get_waiver_config()
        return waiver_config.get('value', default)
    
    def is_waiver_zero(self) -> bool:
        """
        Check if waiver value is 0 (common pattern for FAIL->INFO conversion).
        
        Returns:
            True if waiver.value == 0, False otherwise
        
        Example:
            if self.is_waiver_zero():
                # Convert FAIL severity to INFO
                severity = Severity.INFO
            else:
                severity = Severity.FAIL
        """
        waiver_value = self.get_waiver_value(default='N/A')
        return waiver_value == 0 or waiver_value == '0'
    
    # =========================================================================
    # Pattern 8: Type 1/2 Waiver Logic (waiver.value=0)
    # =========================================================================
    
    def should_convert_fail_to_info(self) -> bool:
        """
        Check if FAIL should be converted to INFO (Type 1/2 waiver=0 logic).
        
        Type 1/2 common logic:
        - waiver.value = 0: Convert all FAIL to INFO, force PASS (display mode)
        - waiver.value = N/A: Normal mode
        
        Returns:
            True if waiver=0 (should convert FAIL to INFO)
            False otherwise
        
        Example:
            # Type 1 or Type 2 checker
            if self.should_convert_fail_to_info():
                severity = Severity.INFO
                reason += "[WAIVED_AS_INFO]"
                is_pass = True
            else:
                severity = Severity.FAIL
                is_pass = check_condition()
        """
        return self.is_waiver_zero()
    
    def apply_type1_type2_waiver(
        self,
        is_pass_normal_mode: bool,
        fail_reason: str = "",
        info_reason: str = "",
        waiver_tag: str = "[WAIVED_AS_INFO]"
    ) -> Tuple[bool, str, str]:
        """
        Apply Type 1/2 waiver logic: waiver=0 converts FAIL→INFO and forces PASS.
        
        Type 1 and Type 2 use the same waiver.value=0 handling logic:
        - waiver=0: Convert all FAIL to INFO, force PASS, add [WAIVED_AS_INFO] tag
        - waiver=N/A: Normal mode, judge PASS/FAIL based on actual condition
        
        Args:
            is_pass_normal_mode: PASS/FAIL determination result in normal mode
            fail_reason: Reason description for FAIL status
            info_reason: Reason description for INFO status (use fail_reason if empty)
            waiver_tag: Tag to add when waiver=0 (default: "[WAIVED_AS_INFO]")
        
        Returns:
            Tuple of (is_pass, severity, reason):
            - is_pass: True if check passes
            - severity: 'INFO' if waiver=0, 'FAIL' or 'INFO' otherwise
            - reason: Formatted reason with waiver tag if applicable
        
        Example - Type 1:
            # Type 1: Show all items as INFO
            is_pass, severity, reason = self.apply_type1_type2_waiver(
                is_pass_normal_mode=True,  # Type 1 usually PASS
                fail_reason="No libraries found",
                info_reason="Library loaded successfully"
            )
            # If waiver=0: (True, 'INFO', "Library loaded successfully[WAIVED_AS_INFO]")
            # If normal: (True, 'INFO', "Library loaded successfully")
        
        Example - Type 2:
            # Type 2: violations count check
            violations = ['lib1_nldm', 'lib2_nldm']
            expected = 2
            is_pass_normal = (len(violations) == expected)
            
            is_pass, severity, reason = self.apply_type1_type2_waiver(
                is_pass_normal_mode=is_pass_normal,
                fail_reason=f"Forbidden library found (pattern: {pattern})",
                info_reason=f"Forbidden library found (pattern: {pattern})"
            )
            
            # If waiver=0:
            #   → (True, 'INFO', "Forbidden library found...[WAIVED_AS_INFO]")
            # If normal and PASS:
            #   → (True, 'INFO', "Forbidden library found...")
            # If normal and FAIL:
            #   → (False, 'FAIL', "Forbidden library found...")
        """
        if self.should_convert_fail_to_info():
            # waiver=0: Force PASS, convert to INFO
            reason = info_reason if info_reason else fail_reason
            if waiver_tag and waiver_tag not in reason:
                reason = f"{reason}{waiver_tag}"
            return True, 'INFO', reason
        else:
            # Normal mode
            if is_pass_normal_mode:
                reason = info_reason if info_reason else fail_reason
                return True, 'INFO', reason
            else:
                return False, 'FAIL', fail_reason
    
    def get_waiver_display_mode(self) -> str:
        """
        Get current waiver display mode.
        
        Returns:
            'DISPLAY_ONLY' if waiver=0 (Type 1/2 - FAIL→INFO conversion)
            'WAIVER_ENABLED' if waiver>0 (Type 3/4 - waive_items matching)
            'NORMAL' if waiver=N/A
        
        Example:
            mode = self.get_waiver_display_mode()
            if mode == 'DISPLAY_ONLY':
                tag = '[WAIVED_AS_INFO]'  # Type 1/2
            elif mode == 'WAIVER_ENABLED':
                tag = '[WAIVER]'  # Type 3/4
            else:
                tag = ''
        """
        waiver_value = self.get_waiver_value(default='N/A')
        
        if waiver_value == 0 or waiver_value == '0':
            return 'DISPLAY_ONLY'
        elif waiver_value != 'N/A':
            try:
                if int(waiver_value) > 0:
                    return 'WAIVER_ENABLED'
            except (ValueError, TypeError):
                pass
        
        return 'NORMAL'