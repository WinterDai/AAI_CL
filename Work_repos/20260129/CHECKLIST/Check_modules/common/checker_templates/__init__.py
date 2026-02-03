"""
Checker Templates - Reusable Components for Building Checkers

This package provides reusable mixin classes and utilities for building checkers.
All templates are extracted from proven, battle-tested implementations.

Available Templates:
- InputFileParserMixin: Parse input files (logs, reports, etc.) with pattern matching and file path extraction
- WaiverHandlerMixin: Handle waiver logic for Type 3/4 checkers
- OutputBuilderMixin: Build CheckResult outputs with standardized patterns

Usage:
    from checker_templates import InputFileParserMixin, WaiverHandlerMixin, OutputBuilderMixin
    
    class MyChecker(BaseChecker, InputFileParserMixin, WaiverHandlerMixin, OutputBuilderMixin):
        def execute_check(self):
            # Parse input files
            results = self.parse_log_with_patterns(...)
            # Handle waivers
            waive_dict = self.parse_waive_items(...)
            waived, unwaived = self.classify_items_by_waiver(...)
            # Build output in one step
            return self.build_complete_output(
                found_items=results['found'],
                missing_items=unwaived,
                waived_items=waived,
                waive_dict=waive_dict
            )
"""

from .input_file_parser_template import InputFileParserMixin
from .waiver_handler_template import WaiverHandlerMixin
from .output_builder_template import OutputBuilderMixin

__version__ = '1.0.0'
__all__ = [
    'InputFileParserMixin',
    'WaiverHandlerMixin',
    'OutputBuilderMixin',
]
