"""
Unit tests for L5: Output Controller
"""

import pytest
from output_controller import (
    filter_output_keys,
    validate_cr5_output,
    get_missing_keys,
    get_extra_keys,
    initialize_internal_result,
    TYPE_KEYS
)


class TestFilterOutputKeys:
    """测试filter_output_keys函数"""
    
    def test_type1_filtering(self):
        internal_result = {
            'status': 'PASS',
            'found_items': [{'item': 1}],
            'missing_items': [],
            'extra_items': [{'extra': 1}],  # Should be filtered out
            'waived': [],  # Should be filtered out
            'unused_waivers': []  # Should be filtered out
        }
        
        output = filter_output_keys(internal_result, type_id=1)
        
        assert set(output.keys()) == {'status', 'found_items', 'missing_items'}
        assert 'extra_items' not in output
        assert 'waived' not in output
    
    def test_type2_filtering(self):
        internal_result = {
            'status': 'FAIL',
            'found_items': [],
            'missing_items': [{'m': 1}],
            'extra_items': [{'e': 1}],
            'waived': [{'w': 1}],  # Should be filtered out
        }
        
        output = filter_output_keys(internal_result, type_id=2)
        
        assert set(output.keys()) == {'status', 'found_items', 'missing_items', 'extra_items'}
        assert 'waived' not in output
    
    def test_type3_all_keys(self):
        internal_result = {
            'status': 'PASS',
            'found_items': [],
            'missing_items': [],
            'extra_items': [],
            'waived': [{'w': 1}],
            'unused_waivers': [{'pattern': 'p1'}]
        }
        
        output = filter_output_keys(internal_result, type_id=3)
        
        assert set(output.keys()) == TYPE_KEYS[3]
        assert len(output['waived']) == 1
    
    def test_type4_keys(self):
        internal_result = {
            'status': 'PASS',
            'found_items': [],
            'missing_items': [],
            'extra_items': [{'e': 1}],  # Should be filtered out for Type 4
            'waived': [],
            'unused_waivers': []
        }
        
        output = filter_output_keys(internal_result, type_id=4)
        
        assert set(output.keys()) == TYPE_KEYS[4]
        assert 'extra_items' not in output
    
    def test_missing_keys_get_defaults(self):
        internal_result = {
            'status': 'PASS',
            'found_items': [{'item': 1}]
            # missing_items not present
        }
        
        output = filter_output_keys(internal_result, type_id=1)
        
        # Missing keys should get empty list default
        assert output['missing_items'] == []
        assert output['status'] == 'PASS'
    
    def test_invalid_type_id(self):
        internal_result = {'status': 'PASS'}
        
        with pytest.raises(ValueError, match="Invalid type_id"):
            filter_output_keys(internal_result, type_id=5)


class TestValidateCR5Output:
    """测试validate_cr5_output函数"""
    
    def test_valid_type1_output(self):
        output = {
            'status': 'PASS',
            'found_items': [],
            'missing_items': []
        }
        
        assert validate_cr5_output(output, type_id=1) is True
    
    def test_invalid_missing_keys(self):
        output = {
            'status': 'PASS',
            'found_items': []
            # missing_items missing
        }
        
        assert validate_cr5_output(output, type_id=1) is False
    
    def test_invalid_extra_keys(self):
        output = {
            'status': 'PASS',
            'found_items': [],
            'missing_items': [],
            'extra_key': 'should not be here'
        }
        
        assert validate_cr5_output(output, type_id=1) is False
    
    def test_valid_type3_output(self):
        output = {
            'status': 'PASS',
            'found_items': [],
            'missing_items': [],
            'extra_items': [],
            'waived': [],
            'unused_waivers': []
        }
        
        assert validate_cr5_output(output, type_id=3) is True


class TestGetMissingKeys:
    """测试get_missing_keys函数"""
    
    def test_no_missing_keys(self):
        output = {
            'status': 'PASS',
            'found_items': [],
            'missing_items': []
        }
        
        missing = get_missing_keys(output, type_id=1)
        
        assert len(missing) == 0
    
    def test_some_missing_keys(self):
        output = {
            'status': 'PASS'
        }
        
        missing = get_missing_keys(output, type_id=1)
        
        assert 'found_items' in missing
        assert 'missing_items' in missing


class TestGetExtraKeys:
    """测试get_extra_keys函数"""
    
    def test_no_extra_keys(self):
        output = {
            'status': 'PASS',
            'found_items': [],
            'missing_items': []
        }
        
        extra = get_extra_keys(output, type_id=1)
        
        assert len(extra) == 0
    
    def test_some_extra_keys(self):
        output = {
            'status': 'PASS',
            'found_items': [],
            'missing_items': [],
            'extra_items': [],
            'waived': []
        }
        
        extra = get_extra_keys(output, type_id=1)
        
        assert 'extra_items' in extra
        assert 'waived' in extra


class TestInitializeInternalResult:
    """测试initialize_internal_result函数"""
    
    def test_initialization(self):
        result = initialize_internal_result()
        
        # All list keys should be empty lists
        assert result['status'] == 'FAIL'
        assert result['found_items'] == []
        assert result['missing_items'] == []
        assert result['extra_items'] == []
        assert result['waived'] == []
        assert result['unused_waivers'] == []


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
