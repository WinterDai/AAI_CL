#!/usr/bin/env python3
"""
OutputBuilderMixinRefactored - Extended with Template Method Pattern

This is an extended version of OutputBuilderMixin that adds:
1. execute_boolean_check() - Template Method for Type 1/4
2. execute_value_check() - Template Method for Type 2/3

These methods encapsulate the common patterns found in 18+ Golden files,
reducing code duplication by ~89% (150 lines → 16 lines per Checker).

Key Design:
- Checkers only implement business logic (_parse_input_files, _determine_violations, etc.)
- Framework handles waiver matching, format conversion, output building
- LLM generates minimal code (4 lines per Type method)

Date: 2026-01-02
Author: Refactoring based on Golden code analysis
"""

from pathlib import Path
from typing import List, Dict, Any, Optional, Callable
import sys

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from output_builder_template import OutputBuilderMixin
from base_checker import CheckResult
from output_formatter import DetailItem, Severity, create_check_result


class OutputBuilderMixinRefactored(OutputBuilderMixin):
    """
    Extended OutputBuilderMixin with Template Method pattern.
    
    Adds two Template Methods:
    1. execute_boolean_check(has_waiver) - For Type 1/4
    2. execute_value_check(has_waiver) - For Type 2/3
    
    Usage in Checkers:
    ```python
    def _execute_type1(self):
        netlist_info, spef_info, errors = self._parse_input_files()
        return self.execute_boolean_check(netlist_info, spef_info, errors, has_waiver=False)
    
    def _execute_type3(self):
        netlist_info, spef_info, errors = self._parse_input_files()
        return self.execute_value_check(netlist_info, spef_info, errors, has_waiver=True)
    ```
    """
    
    # =========================================================================
    # Template Method for Type 1/4 (Boolean Check)
    # =========================================================================
    
    def execute_boolean_check(
        self,
        netlist_info: Dict[str, Any],
        spef_info: Dict[str, Any],
        errors: List[str],
        has_waiver: bool = False
    ) -> CheckResult:
        """
        Template Method for Type 1/4 (Boolean check).
        
        This method encapsulates the common pattern found in all Type 1/4 implementations:
        1. Determine found items
        2. Determine violations (missing items)
        3. If has_waiver: classify waived/unwaived
        4. Build output
        
        Args:
            netlist_info: Parsed netlist information
            spef_info: Parsed SPEF information
            errors: List of errors from parsing
            has_waiver: True for Type 4, False for Type 1
            
        Returns:
            CheckResult
        """
        # Step 1: Call business logic (implemented by Checker)
        found_items = self._determine_found_items(netlist_info, spef_info)
        missing_items = self._determine_violations(netlist_info, spef_info, errors)
        
        # Step 2: Get name_extractor (if Checker provides it)
        name_extractor = None
        if hasattr(self, '_build_name_extractor'):
            name_extractor = self._build_name_extractor()
        
        # Step 3: Build output (Framework handles everything)
        return self.build_complete_output(
            found_items=found_items,
            missing_items=missing_items,
            value="N/A",
            has_pattern_items=False,
            has_waiver_value=has_waiver,
            default_file='N/A',
            name_extractor=name_extractor,
            found_reason="Status: Success",
            missing_reason="File loading failed",
            found_desc="Netlist/SPEF files loaded successfully",
            missing_desc="Netlist/SPEF loading issues"
        )
    
    # =========================================================================
    # Template Method for Type 2/3 (Value Check)
    # =========================================================================
    
    def execute_value_check(
        self,
        netlist_info: Dict[str, Any],
        spef_info: Dict[str, Any],
        errors: List[str],
        has_waiver: bool = False
    ) -> CheckResult:
        """
        Template Method for Type 2/3 (Value check with pattern matching).
        
        This method encapsulates the common pattern found in all Type 2/3 implementations:
        1. Get pattern_items from requirements
        2. Match patterns against content
        3. Determine found/missing items
        4. If has_waiver: classify waived/unwaived
        5. Build output
        
        Args:
            netlist_info: Parsed netlist information
            spef_info: Parsed SPEF information
            errors: List of errors from parsing
            has_waiver: True for Type 3, False for Type 2
            
        Returns:
            CheckResult
        """
        # Step 1: Get requirements and pattern_items
        requirements = self.get_requirements()
        pattern_items = requirements.get('pattern_items', []) if requirements else []
        
        # Step 2: Call business logic (implemented by Checker)
        found_items = self._determine_found_items(netlist_info, spef_info)
        matched_patterns = self._determine_pattern_matches(netlist_info, spef_info)
        
        # Step 3: Determine missing patterns
        matched_set = set(matched_patterns)
        missing_patterns = [p for p in pattern_items if p not in matched_set]
        
        # Step 4: If Type 2 (no waiver), use missing_patterns directly
        if not has_waiver:
            # Type 2: Simple value check
            # Get name_extractor
            name_extractor = None
            if hasattr(self, '_build_name_extractor'):
                name_extractor = self._build_name_extractor()
            
            return self.build_complete_output(
                found_items=found_items,
                missing_items=missing_patterns,
                value=len(matched_patterns),
                has_pattern_items=True,
                has_waiver_value=False,
                default_file='N/A',
                name_extractor=name_extractor,
                found_reason="Pattern matched",
                missing_reason="Required pattern not found",
                found_desc="Netlist/SPEF version is correct",
                missing_desc="Netlist/spef version isn't correct"
            )
        
        # Step 5: Type 3 - Waiver classification
        # Get waiver configuration
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # Classify missing patterns
        waived_items = []
        unwaived_items = []
        
        for pattern in missing_patterns:
            if self.match_waiver_entry(pattern, waive_dict):
                waived_items.append(pattern)
            else:
                unwaived_items.append(pattern)
        
        # Find unused waivers
        used_names = set(waived_items)
        unused_waivers = [name for name in waive_dict.keys() if name not in used_names]
        
        # Get name_extractor
        name_extractor = None
        if hasattr(self, '_build_name_extractor'):
            name_extractor = self._build_name_extractor()
        
        # Build output with waiver logic
        return self.build_complete_output(
            found_items=found_items,
            waived_items=waived_items,
            missing_items=unwaived_items,
            waive_dict=waive_dict,
            unused_waivers=unused_waivers,
            value=len(matched_patterns),
            has_pattern_items=True,
            has_waiver_value=True,
            default_file='N/A',
            name_extractor=name_extractor,
            found_desc="Netlist/SPEF version is correct",
            missing_desc="Netlist/spef version isn't correct",
            found_reason="Pattern matched",
            missing_reason="Required pattern not found",
            waived_desc="Netlist/SPEF version check waived",
            waived_base_reason="Required pattern not found",
            unused_waiver_reason="Waived item not used"
        )
    
    # =========================================================================
    # Abstract Methods (Checkers MUST implement these)
    # =========================================================================
    
    def _determine_found_items(self, netlist_info: Dict, spef_info: Dict) -> Dict[str, Dict]:
        """
        Determine found items based on parsed data.
        
        Checkers MUST implement this method to define business logic.
        
        Returns:
            Dict mapping item name to metadata:
            {
                "Netlist: path": {
                    "line_number": 123,
                    "file_path": "/path/to/log",
                    "version": "1.0",
                    "date": "2025-01-01"
                }
            }
        """
        raise NotImplementedError("Checker must implement _determine_found_items()")
    
    def _determine_violations(self, netlist_info: Dict, spef_info: Dict, errors: List[str]) -> List[str]:
        """
        Determine violations (missing items) based on parsed data.
        
        Checkers MUST implement this method to define business logic.
        
        Returns:
            List of violation names/descriptions:
            ["Netlist (Status: Not Found)", "SPEF (Status: Skipped)"]
        """
        raise NotImplementedError("Checker must implement _determine_violations()")
    
    def _determine_pattern_matches(self, netlist_info: Dict, spef_info: Dict) -> List[str]:
        """
        Determine which patterns are matched (for Type 2/3).
        
        Checkers MUST implement this method for Type 2/3 checks.
        
        Returns:
            List of matched pattern names:
            ["Generated on:*2025*", "Genus Synthesis Solution*"]
        """
        # Default implementation for Type 1/4 (no pattern matching)
        if hasattr(self, 'detect_checker_type'):
            checker_type = self.detect_checker_type()
            if checker_type in [1, 4]:
                return []
        
        raise NotImplementedError("Checker must implement _determine_pattern_matches() for Type 2/3")
