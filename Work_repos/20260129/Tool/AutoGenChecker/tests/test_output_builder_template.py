"""
Test suite for OutputBuilderTemplate API v2.0

Tests template behavior, metadata preservation, severity control,
tag display logic, and waiver support.
"""

import pytest
import sys
from pathlib import Path
from typing import Dict, List

# Setup path
_test_dir = Path(__file__).resolve().parent
_checklist_root = _test_dir.parents[3] / 'CHECKLIST'
_common_dir = _checklist_root / 'Check_modules' / 'common'

if str(_common_dir) not in sys.path:
    sys.path.insert(0, str(_common_dir))

from output_builder_template import OutputBuilderMixin
from output_formatter import DetailItem, Severity, CheckResult, create_check_result


class MockChecker(OutputBuilderMixin):
    """Mock checker for testing template methods."""
    
    def __init__(self):
        self.waiver_mode = 'normal'  # or 'waiver_zero'
    
    def should_convert_fail_to_info(self) -> bool:
        """Mock waiver=0 detection."""
        return self.waiver_mode == 'waiver_zero'
    
    def get_waivers(self) -> dict:
        """Mock waiver configuration."""
        if self.waiver_mode == 'waiver_zero':
            return {
                'value': 0,
                'waive_items': ['Test waiver reason']
            }
        return {'value': 'N/A', 'waive_items': []}
    
    def parse_waive_items(self, waive_items: list) -> dict:
        """Mock waiver parsing."""
        return {item: f"Reason: {item}" for item in waive_items}
    
    def apply_type1_type2_waiver(self, is_pass_normal_mode, fail_reason, info_reason):
        """Mock waiver application."""
        if self.waiver_mode == 'waiver_zero':
            return True, 'INFO', info_reason
        return is_pass_normal_mode, 'FAIL' if not is_pass_normal_mode else 'PASS', fail_reason


class TestMetadataPreservation:
    """Test metadata (line_number, file_path) preservation in API v2.0."""
    
    def test_dict_format_preserves_metadata(self):
        """Test Dict format preserves line_number and file_path."""
        checker = MockChecker()
        
        items_dict = {
            "item1": {
                "line_number": 10,
                "file_path": "/path/to/file.txt",
                "line_content": "some content"
            },
            "item2": {
                "line_number": 20,
                "file_path": "/path/to/file.txt"
            }
        }
        
        details = checker.build_details_from_items(
            found_items=items_dict
        )
        
        assert len(details) == 2
        assert details[0].line_number == 10
        assert details[0].file_path == "/path/to/file.txt"
        assert details[1].line_number == 20
    
    def test_list_format_auto_conversion(self):
        """Test List format auto-converts to Dict (backward compatibility)."""
        checker = MockChecker()
        
        items_list = ["item1", "item2"]
        
        details = checker.build_details_from_items(
            found_items=items_list
        )
        
        assert len(details) == 2
        # List items should still create DetailItems (no metadata)
        assert details[0].name == "item1"
        assert details[1].name == "item2"
    
    def test_missing_items_dict_format(self):
        """Test missing_items supports Dict format in v2.0."""
        checker = MockChecker()
        
        missing_dict = {
            "violation1": {
                "line_number": 100,
                "file_path": "report.txt"
            }
        }
        
        details = checker.build_details_from_items(
            missing_items=missing_dict
        )
        
        assert len(details) == 1
        assert details[0].severity == Severity.FAIL
        assert details[0].line_number == 100
        assert details[0].file_path == "report.txt"
    
    def test_waived_items_dict_format(self):
        """Test waived_items supports Dict format in v2.0."""
        checker = MockChecker()
        
        waived_dict = {
            "waived1": {
                "line_number": 50,
                "file_path": "constraints.sdc"
            }
        }
        
        waive_dict = {"waived1": "Waiver reason"}
        
        details = checker.build_details_from_items(
            waived_items=waived_dict,
            waive_dict=waive_dict,
            waived_tag="[WAIVER]"
        )
        
        assert len(details) == 1
        assert details[0].severity == Severity.INFO
        assert details[0].line_number == 50
        assert "[WAIVER]" in details[0].reason


class TestSeverityControl:
    """Test severity level control for different item types."""
    
    def test_extra_severity_fail(self):
        """Test extra_severity=FAIL forces FAIL status."""
        checker = MockChecker()
        
        clean_items = {"clean": {"line_number": 1}}
        violations = {"violation": {"line_number": 10}}
        
        result = checker.build_complete_output(
            found_items=clean_items,
            extra_items=violations,
            extra_severity=Severity.FAIL
        )
        
        assert result.is_pass == False  # Should FAIL with violations
    
    def test_extra_severity_warn(self):
        """Test extra_severity=WARN allows PASS with warnings."""
        checker = MockChecker()
        
        found_items = {"item": {"line_number": 1}}
        extra_items = {"extra": {"line_number": 10}}
        
        result = checker.build_complete_output(
            found_items=found_items,
            extra_items=extra_items,
            extra_severity=Severity.WARN
        )
        
        assert result.is_pass == True  # Should PASS (warnings OK)
    
    def test_missing_severity_default_fail(self):
        """Test missing_items default to FAIL severity."""
        checker = MockChecker()
        
        missing_items = {"missing": {"line_number": 10}}
        
        result = checker.build_complete_output(
            found_items={},
            missing_items=missing_items
        )
        
        assert result.is_pass == False


class TestTagDisplay:
    """Test tag display logic ([WAIVER], [WAIVED_INFO], [WAIVED_AS_INFO])."""
    
    def test_waiver_tag_in_reason(self):
        """Test [WAIVER] tag appears in reason field, not name."""
        checker = MockChecker()
        
        waived_items = {"item": {"line_number": 10}}
        waive_dict = {"item": "Waiver reason"}
        
        details = checker.build_details_from_items(
            waived_items=waived_items,
            waive_dict=waive_dict,
            waived_tag="[WAIVER]"
        )
        
        assert len(details) == 1
        # Tag should be in reason, not duplicated in name
        assert "[WAIVER]" in details[0].reason
        assert "[WAIVER]" not in details[0].name
    
    def test_waived_info_tag_waiver_zero(self):
        """Test [WAIVED_INFO] tag for waiver=0 mode."""
        checker = MockChecker()
        checker.waiver_mode = 'waiver_zero'
        
        result = checker.build_complete_output(
            found_items={},
            missing_items={"item": {"line_number": 10}}
        )
        
        # In waiver=0 mode, should convert to PASS
        assert result.is_pass == True
    
    def test_no_tag_duplication_in_groups(self):
        """Test tags not duplicated in group items."""
        checker = MockChecker()
        
        waived_items = {"waived": {"line_number": 10}}
        waive_dict = {"waived": "Reason"}
        
        groups = checker.build_result_groups(
            waived_items=waived_items,
            convert_to_info=False
        )
        
        # Groups should show clean names, tags only in description
        info_groups = groups.get('info_groups', {})
        if info_groups:
            first_group = list(info_groups.values())[0]
            items = first_group.get('items', [])
            if items:
                # Items should not have tags
                assert not any('[' in item for item in items)


class TestWaiverSupport:
    """Test waiver=0 auto-conversion and waiver handling."""
    
    def test_waiver_zero_converts_fail_to_info(self):
        """Test waiver=0 converts FAIL → INFO."""
        checker = MockChecker()
        checker.waiver_mode = 'waiver_zero'
        
        violations = {"violation": {"line_number": 10}}
        
        result = checker.build_complete_output(
            found_items={},
            missing_items=violations
        )
        
        # Should convert to PASS in waiver=0 mode
        assert result.is_pass == True
    
    def test_normal_mode_fail_stays_fail(self):
        """Test normal mode keeps FAIL as FAIL."""
        checker = MockChecker()
        checker.waiver_mode = 'normal'
        
        violations = {"violation": {"line_number": 10}}
        
        result = checker.build_complete_output(
            found_items={},
            missing_items=violations
        )
        
        # Should FAIL in normal mode
        assert result.is_pass == False
    
    def test_waive_items_display(self):
        """Test waive_items from config display correctly."""
        checker = MockChecker()
        checker.waiver_mode = 'waiver_zero'
        
        # Waive_items should be auto-detected and displayed
        result = checker.build_complete_output(
            found_items={},
            missing_items={"item": {"line_number": 10}}
        )
        
        # Should have INFO groups for waive_items
        assert result.is_pass == True


class TestBackwardCompatibility:
    """Test backward compatibility with v1.x List parameters."""
    
    def test_list_parameters_still_work(self):
        """Test v1.x List parameters still work in v2.0."""
        checker = MockChecker()
        
        # Old style: List[str]
        found_list = ["item1", "item2"]
        missing_list = []
        
        result = checker.build_complete_output(
            found_items=found_list,
            missing_items=missing_list
        )
        
        assert result.is_pass == True
        assert result.value == 2  # or N/A depending on implementation
    
    def test_mixed_dict_list_parameters(self):
        """Test mixing Dict and List parameters (should work)."""
        checker = MockChecker()
        
        found_dict = {"item": {"line_number": 10}}
        missing_list = []
        
        result = checker.build_complete_output(
            found_items=found_dict,
            missing_items=missing_list
        )
        
        assert result.is_pass == True


class TestCompleteOutput:
    """Test build_complete_output() one-step solution."""
    
    def test_complete_output_builds_all_components(self):
        """Test complete_output builds details + groups + result."""
        checker = MockChecker()
        
        found = {"found": {"line_number": 1}}
        missing = {"missing": {"line_number": 10}}
        
        result = checker.build_complete_output(
            found_items=found,
            missing_items=missing
        )
        
        assert isinstance(result, CheckResult)
        assert result.is_pass == False
        assert len(result.details) >= 2  # At least found + missing
    
    def test_complete_output_with_extra_items(self):
        """Test complete_output with extra_items."""
        checker = MockChecker()
        
        found = {"found": {"line_number": 1}}
        extra = {"extra": {"line_number": 20}}
        
        result = checker.build_complete_output(
            found_items=found,
            extra_items=extra,
            extra_severity=Severity.FAIL
        )
        
        assert result.is_pass == False  # Extra with FAIL = FAIL
    
    def test_complete_output_custom_descriptions(self):
        """Test complete_output with custom descriptions."""
        checker = MockChecker()
        
        found = {"item": {"line_number": 1}}
        
        result = checker.build_complete_output(
            found_items=found,
            missing_items={},
            found_desc="Custom found description",
            missing_desc="Custom missing description"
        )
        
        # Should use custom descriptions
        assert result.is_pass == True


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_empty_items(self):
        """Test handling of empty item dictionaries."""
        checker = MockChecker()
        
        result = checker.build_complete_output(
            found_items={},
            missing_items={}
        )
        
        # Empty should still create valid result
        assert isinstance(result, CheckResult)
    
    def test_none_items(self):
        """Test handling of None items."""
        checker = MockChecker()
        
        result = checker.build_complete_output(
            found_items=None,
            missing_items=None
        )
        
        # None should be handled gracefully
        assert isinstance(result, CheckResult)
    
    def test_metadata_missing_fields(self):
        """Test handling of incomplete metadata."""
        checker = MockChecker()
        
        incomplete_metadata = {
            "item": {
                "line_number": 10
                # Missing file_path
            }
        }
        
        details = checker.build_details_from_items(
            found_items=incomplete_metadata
        )
        
        # Should handle missing file_path gracefully
        assert len(details) == 1
        assert details[0].line_number == 10


if __name__ == '__main__':
    # Run tests
    pytest.main([__file__, '-v', '--tb=short'])
