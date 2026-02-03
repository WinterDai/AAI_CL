"""
Unit tests for L0: Config Validator
"""

import pytest
from config_validator import (
    validate_and_normalize_config,
    normalize_value,
    validate_domain,
    determine_type,
    ConfigError
)


class TestNormalizeValue:
    """测试normalize_value函数"""
    
    def test_none_to_na(self):
        assert normalize_value(None) == 'N/A'
    
    def test_na_string(self):
        assert normalize_value("N/A") == 'N/A'
        assert normalize_value(" N/A ") == 'N/A'
    
    def test_integer_zero(self):
        assert normalize_value(0) == 0
    
    def test_integer_positive(self):
        assert normalize_value(5) == 5
    
    def test_string_number(self):
        assert normalize_value("0") == 0
        assert normalize_value("2") == 2
        assert normalize_value(" 10 ") == 10
    
    def test_invalid_string(self):
        assert normalize_value("abc") == 'N/A'
        assert normalize_value("") == 'N/A'


class TestValidateDomain:
    """测试validate_domain函数"""
    
    def test_valid_combinations(self):
        # Should not raise
        validate_domain('N/A', 'N/A')
        validate_domain(1, 'N/A')
        validate_domain(5, 0)
        validate_domain('N/A', 2)
    
    def test_invalid_req_value(self):
        with pytest.raises(ConfigError, match="req.value must be"):
            validate_domain(0, 'N/A')
        
        with pytest.raises(ConfigError, match="req.value must be"):
            validate_domain(-1, 'N/A')
    
    def test_invalid_waiver_value(self):
        with pytest.raises(ConfigError, match="waiver.value must be"):
            validate_domain('N/A', -1)


class TestDetermineType:
    """测试determine_type函数"""
    
    def test_type1(self):
        assert determine_type('N/A', 'N/A') == 1
    
    def test_type2(self):
        assert determine_type(1, 'N/A') == 2
        assert determine_type(10, 'N/A') == 2
    
    def test_type3(self):
        assert determine_type(1, 0) == 3
        assert determine_type(5, 2) == 3
    
    def test_type4(self):
        assert determine_type('N/A', 0) == 4
        assert determine_type('N/A', 5) == 4


class TestValidateAndNormalizeConfig:
    """测试validate_and_normalize_config主函数"""
    
    def test_full_config_type1(self):
        requirements = {'value': None, 'pattern_items': ['p1', 'p2']}
        waivers = {'value': None, 'waive_items': []}
        input_files = ['/path/file.rpt']
        
        result = validate_and_normalize_config(requirements, waivers, input_files, "test desc")
        
        assert result['req_value'] == 'N/A'
        assert result['waiver_value'] == 'N/A'
        assert result['pattern_items'] == ['p1', 'p2']
        assert result['waive_items'] == []
        assert result['input_files'] == ['/path/file.rpt']
        assert result['description'] == "test desc"
    
    def test_missing_optional_fields(self):
        requirements = {'value': 2}
        waivers = {'value': 0}
        input_files = ['/path/file.rpt']
        
        result = validate_and_normalize_config(requirements, waivers, input_files)
        
        assert result['req_value'] == 2
        assert result['waiver_value'] == 0
        assert result['pattern_items'] == []  # Default empty list
        assert result['waive_items'] == []    # Default empty list
        assert result['description'] == ""    # Default empty string
    
    def test_string_value_normalization(self):
        requirements = {'value': "3", 'pattern_items': ['p1']}
        waivers = {'value': "N/A", 'waive_items': ['w1']}
        input_files = ['/path/file.rpt']
        
        result = validate_and_normalize_config(requirements, waivers, input_files)
        
        assert result['req_value'] == 3
        assert result['waiver_value'] == 'N/A'
    
    def test_invalid_config_raises_error(self):
        requirements = {'value': 0}  # Invalid: req must be >= 1
        waivers = {'value': 'N/A'}
        input_files = ['/path/file.rpt']
        
        with pytest.raises(ConfigError):
            validate_and_normalize_config(requirements, waivers, input_files)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
