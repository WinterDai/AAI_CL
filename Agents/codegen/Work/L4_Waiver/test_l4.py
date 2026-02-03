"""
Unit tests for L4: Waiver Engine
"""

import pytest
from waiver_engine import (
    apply_waiver_rules,
    apply_global_waiver,
    apply_selective_waiver,
    match_violation_with_waivers
)


class TestGlobalWaiver:
    """测试Global Waiver (waiver_value = 0)"""
    
    def test_global_waiver_type4(self):
        check_result = {
            'status': 'FAIL',
            'found_items': [],
            'missing_items': [
                {'expected': 'pattern1', 'description': 'desc1'},
                {'expected': 'pattern2', 'description': 'desc2'}
            ]
        }
        
        def mock_atom_b(text, pattern, parsed_fields, default_match, regex_mode):
            return {'is_match': False}
        
        result = apply_waiver_rules(
            check_result=check_result,
            waive_items=['comment1', 'comment2'],
            waiver_value=0,
            type_id=4,
            atom_b_func=mock_atom_b
        )
        
        # Violations remain but modified
        assert len(result['missing_items']) == 2
        assert result['missing_items'][0]['severity'] == 'INFO'
        assert result['missing_items'][0]['tag'] == '[WAIVED_AS_INFO]'
        
        # Status forced to PASS
        assert result['status'] == 'PASS'
        
        # unused_waivers must be empty
        assert result['unused_waivers'] == []
        
        # Waived list contains comments
        assert len(result['waived']) == 2
        assert result['waived'][0]['waiver_pattern'] == 'comment1'
    
    def test_global_waiver_type3(self):
        check_result = {
            'status': 'FAIL',
            'found_items': [],
            'missing_items': [{'expected': 'p1'}],
            'extra_items': [{'value': 'e1'}]
        }
        
        def mock_atom_b(text, pattern, parsed_fields, default_match, regex_mode):
            return {'is_match': False}
        
        result = apply_waiver_rules(
            check_result=check_result,
            waive_items=['global'],
            waiver_value=0,
            type_id=3,
            atom_b_func=mock_atom_b
        )
        
        # Both missing and extra modified
        assert result['missing_items'][0]['severity'] == 'INFO'
        assert result['extra_items'][0]['severity'] == 'INFO'
        assert result['status'] == 'PASS'


class TestSelectiveWaiver:
    """测试Selective Waiver (waiver_value > 0)"""
    
    def test_selective_waiver_exact_match(self):
        check_result = {
            'status': 'FAIL',
            'found_items': [],
            'missing_items': [
                {'expected': 'pattern1', 'description': 'desc1'},
                {'expected': 'pattern2', 'description': 'desc2'}
            ]
        }
        
        def mock_atom_b(text, pattern, parsed_fields, default_match, regex_mode):
            # Check policy injection
            assert default_match == "exact"
            assert regex_mode == "match"
            assert parsed_fields is None
            return {'is_match': text == pattern}
        
        result = apply_waiver_rules(
            check_result=check_result,
            waive_items=['pattern1'],  # Only waive first
            waiver_value=1,
            type_id=4,
            atom_b_func=mock_atom_b
        )
        
        # pattern1 moved to waived
        assert len(result['missing_items']) == 1
        assert result['missing_items'][0]['expected'] == 'pattern2'
        
        assert len(result['waived']) == 1
        assert result['waived'][0]['expected'] == 'pattern1'
        assert result['waived'][0]['waiver_pattern'] == 'pattern1'
        assert result['waived'][0]['tag'] == '[WAIVER]'
        
        # Status still FAIL (missing not empty)
        assert result['status'] == 'FAIL'
    
    def test_selective_waiver_all_matched_type4(self):
        check_result = {
            'status': 'FAIL',
            'found_items': [],
            'missing_items': [
                {'expected': 'p1'},
                {'expected': 'p2'}
            ]
        }
        
        def mock_atom_b(text, pattern, parsed_fields, default_match, regex_mode):
            return {'is_match': True}  # Match all
        
        result = apply_waiver_rules(
            check_result=check_result,
            waive_items=['.*'],  # Regex matches all
            waiver_value=1,
            type_id=4,
            atom_b_func=mock_atom_b
        )
        
        # All violations moved
        assert len(result['missing_items']) == 0
        assert len(result['waived']) == 2
        
        # Status becomes PASS (missing empty)
        assert result['status'] == 'PASS'
        
        # No unused waivers
        assert len(result['unused_waivers']) == 0
    
    def test_selective_waiver_unused_patterns(self):
        check_result = {
            'status': 'FAIL',
            'missing_items': [
                {'expected': 'found_pattern'}
            ]
        }
        
        def mock_atom_b(text, pattern, parsed_fields, default_match, regex_mode):
            return {'is_match': pattern == 'found_pattern'}
        
        result = apply_waiver_rules(
            check_result=check_result,
            waive_items=['found_pattern', 'unused1', 'unused2'],
            waiver_value=2,
            type_id=4,
            atom_b_func=mock_atom_b
        )
        
        # unused_waivers contains patterns with zero matches
        assert len(result['unused_waivers']) == 2
        assert result['unused_waivers'][0]['pattern'] == 'unused1'
        assert result['unused_waivers'][0]['reason'] == "Not matched"
        assert result['unused_waivers'][1]['pattern'] == 'unused2'
    
    def test_selective_waiver_type3_missing_and_extra(self):
        check_result = {
            'status': 'FAIL',
            'found_items': [],
            'missing_items': [{'expected': 'm1'}],
            'extra_items': [{'value': 'e1'}]
        }
        
        def mock_atom_b(text, pattern, parsed_fields, default_match, regex_mode):
            return {'is_match': pattern in text}
        
        result = apply_waiver_rules(
            check_result=check_result,
            waive_items=['m1', 'e1'],
            waiver_value=2,
            type_id=3,
            atom_b_func=mock_atom_b
        )
        
        # Both missing and extra can be waived
        assert len(result['missing_items']) == 0
        assert len(result['extra_items']) == 0
        assert len(result['waived']) == 2
    
    def test_selective_waiver_order_stability(self):
        """验证剩余violations保持原顺序"""
        check_result = {
            'status': 'FAIL',
            'missing_items': [
                {'expected': 'keep1'},
                {'expected': 'waive'},
                {'expected': 'keep2'}
            ]
        }
        
        def mock_atom_b(text, pattern, parsed_fields, default_match, regex_mode):
            return {'is_match': text == pattern}
        
        result = apply_waiver_rules(
            check_result=check_result,
            waive_items=['waive'],
            waiver_value=1,
            type_id=4,
            atom_b_func=mock_atom_b
        )
        
        # Remaining items maintain order
        assert len(result['missing_items']) == 2
        assert result['missing_items'][0]['expected'] == 'keep1'
        assert result['missing_items'][1]['expected'] == 'keep2'


class TestMatchViolationWithWaivers:
    """测试match_violation_with_waivers函数"""
    
    def test_match_expected_field(self):
        violation = {'expected': 'test_pattern', 'value': 'other'}
        
        def mock_atom_b(text, pattern, parsed_fields, default_match, regex_mode):
            return {'is_match': text == pattern}
        
        result = match_violation_with_waivers(
            violation,
            ['test_pattern', 'unused'],
            mock_atom_b
        )
        
        assert result == 'test_pattern'
    
    def test_match_value_field_fallback(self):
        violation = {'value': 'test_value', 'description': 'desc'}
        
        def mock_atom_b(text, pattern, parsed_fields, default_match, regex_mode):
            return {'is_match': text == pattern}
        
        result = match_violation_with_waivers(
            violation,
            ['test_value'],
            mock_atom_b
        )
        
        assert result == 'test_value'
    
    def test_first_match_wins(self):
        violation = {'expected': 'test'}
        
        def mock_atom_b(text, pattern, parsed_fields, default_match, regex_mode):
            return {'is_match': True}  # All match
        
        result = match_violation_with_waivers(
            violation,
            ['pattern1', 'pattern2'],
            mock_atom_b
        )
        
        # Should return first pattern
        assert result == 'pattern1'
    
    def test_no_match(self):
        violation = {'expected': 'test'}
        
        def mock_atom_b(text, pattern, parsed_fields, default_match, regex_mode):
            return {'is_match': False}
        
        result = match_violation_with_waivers(
            violation,
            ['no_match'],
            mock_atom_b
        )
        
        assert result is None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
