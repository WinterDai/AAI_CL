"""
Unit tests for L3: Check Assembler
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path to import L0
sys.path.insert(0, str(Path(__file__).parent.parent))

from check_assembler import (
    assemble_check,
    check_pattern_requirements,
    check_existence_requirements,
    consume_first_match,
    create_ghost_missing_item
)


class TestCheckPatternRequirements:
    """测试check_pattern_requirements函数"""
    
    def test_type2_all_found(self):
        parsed_items = [
            {'value': 'alpha', 'line_number': 1, 'source_file': '/f.rpt', 
             'matched_content': 'alpha', 'parsed_fields': {}},
            {'value': 'beta', 'line_number': 2, 'source_file': '/f.rpt',
             'matched_content': 'beta', 'parsed_fields': {}}
        ]
        
        def mock_atom_b(text, pattern, parsed_fields, default_match, regex_mode):
            return {'is_match': pattern in text}
        
        result = check_pattern_requirements(
            parsed_items_all=parsed_items,
            pattern_items=['alpha', 'beta'],
            atom_b_func=mock_atom_b,
            description="test desc",
            searched_files=['/f.rpt']
        )
        
        assert result['status'] == 'PASS'
        assert len(result['found_items']) == 2
        assert len(result['missing_items']) == 0
        assert len(result['extra_items']) == 0
        assert result['found_items'][0]['description'] == "test desc"
    
    def test_type2_with_missing(self):
        parsed_items = [
            {'value': 'alpha', 'line_number': 1, 'source_file': '/f.rpt',
             'matched_content': 'alpha', 'parsed_fields': {}}
        ]
        
        def mock_atom_b(text, pattern, parsed_fields, default_match, regex_mode):
            return {'is_match': pattern in text}
        
        result = check_pattern_requirements(
            parsed_items_all=parsed_items,
            pattern_items=['alpha', 'gamma'],  # gamma not found
            atom_b_func=mock_atom_b,
            description="test desc",
            searched_files=['/f.rpt']
        )
        
        assert result['status'] == 'FAIL'
        assert len(result['found_items']) == 1
        assert len(result['missing_items']) == 1
        assert result['missing_items'][0]['expected'] == 'gamma'
        assert result['missing_items'][0]['source_file'] == ""  # Ghost
    
    def test_type2_with_extra(self):
        parsed_items = [
            {'value': 'alpha', 'line_number': 1, 'source_file': '/f.rpt',
             'matched_content': 'alpha', 'parsed_fields': {}},
            {'value': 'extra', 'line_number': 2, 'source_file': '/f.rpt',
             'matched_content': 'extra', 'parsed_fields': {}}
        ]
        
        def mock_atom_b(text, pattern, parsed_fields, default_match, regex_mode):
            return {'is_match': pattern in text}
        
        result = check_pattern_requirements(
            parsed_items_all=parsed_items,
            pattern_items=['alpha'],  # Only 1 pattern, 2 items
            atom_b_func=mock_atom_b,
            description="test desc",
            searched_files=['/f.rpt']
        )
        
        assert result['status'] == 'FAIL'
        assert len(result['found_items']) == 1
        assert len(result['missing_items']) == 0
        assert len(result['extra_items']) == 1
        assert result['extra_items'][0]['value'] == 'extra'
    
    def test_empty_pattern_items(self):
        """边界情况: pattern_items为空"""
        parsed_items = [
            {'value': 'item1', 'line_number': 1, 'source_file': '/f.rpt',
             'matched_content': 'item1', 'parsed_fields': {}}
        ]
        
        def mock_atom_b(text, pattern, parsed_fields, default_match, regex_mode):
            return {'is_match': False}
        
        result = check_pattern_requirements(
            parsed_items_all=parsed_items,
            pattern_items=[],  # Empty
            atom_b_func=mock_atom_b,
            description="test desc",
            searched_files=['/f.rpt']
        )
        
        assert result['status'] == 'FAIL'
        assert len(result['found_items']) == 0
        assert len(result['missing_items']) == 0
        assert len(result['extra_items']) == 1  # All items are extra


class TestCheckExistenceRequirements:
    """测试check_existence_requirements函数"""
    
    def test_type1_existence_pass(self):
        parsed_items = [
            {'value': 'found', 'line_number': 1, 'source_file': '/f.rpt',
             'matched_content': 'found', 'parsed_fields': {}}
        ]
        
        def mock_atom_c(items):
            return {
                'is_match': True,
                'evidence': [items[0]]
            }
        
        result = check_existence_requirements(
            parsed_items_all=parsed_items,
            atom_c_func=mock_atom_c,
            description="test desc",
            searched_files=['/f.rpt']
        )
        
        assert result['status'] == 'PASS'
        assert len(result['found_items']) == 1
        assert len(result['missing_items']) == 0
        assert result['found_items'][0]['description'] == "test desc"
    
    def test_type1_existence_fail(self):
        parsed_items = []
        
        def mock_atom_c(items):
            return {
                'is_match': False,
                'evidence': []
            }
        
        result = check_existence_requirements(
            parsed_items_all=parsed_items,
            atom_c_func=mock_atom_c,
            description="test desc",
            searched_files=['/f.rpt']
        )
        
        assert result['status'] == 'FAIL'
        assert len(result['found_items']) == 0
        assert len(result['missing_items']) == 1
        assert result['missing_items'][0]['expected'] == "Existence check failed"
        assert result['missing_items'][0]['source_file'] == ""  # Ghost


class TestConsumeFirstMatch:
    """测试consume_first_match函数"""
    
    def test_first_match_found(self):
        parsed_items = [
            {'value': 'alpha', 'parsed_fields': {}},
            {'value': 'beta', 'parsed_fields': {}},
            {'value': 'alpha again', 'parsed_fields': {}}
        ]
        
        def mock_atom_b(text, pattern, parsed_fields, default_match, regex_mode):
            return {'is_match': pattern in text}
        
        consumed = set()
        result = consume_first_match(parsed_items, 'alpha', consumed, mock_atom_b)
        
        assert result is not None
        assert result['value'] == 'alpha'
        assert 0 in consumed
    
    def test_skip_consumed(self):
        parsed_items = [
            {'value': 'alpha', 'parsed_fields': {}},
            {'value': 'alpha2', 'parsed_fields': {}}
        ]
        
        def mock_atom_b(text, pattern, parsed_fields, default_match, regex_mode):
            return {'is_match': pattern in text}
        
        consumed = {0}  # First item already consumed
        result = consume_first_match(parsed_items, 'alpha', consumed, mock_atom_b)
        
        assert result is not None
        assert result['value'] == 'alpha2'
        assert 1 in consumed


class TestCreateGhostMissingItem:
    """测试create_ghost_missing_item函数"""
    
    def test_ghost_structure(self):
        ghost = create_ghost_missing_item(
            pattern="test_pattern",
            description="test desc",
            searched_files=['/a.rpt', '/b.rpt']
        )
        
        assert ghost['description'] == "test desc"
        assert ghost['expected'] == "test_pattern"
        assert ghost['searched_files'] == ['/a.rpt', '/b.rpt']
        assert ghost['line_number'] is None
        assert ghost['source_file'] == ""
        assert ghost['matched_content'] == ""
        assert ghost['parsed_fields'] == {}


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
