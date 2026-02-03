"""
Unit tests for L6: Report Generator
"""

import pytest
import tempfile
from pathlib import Path
from log_formatter import (
    generate_log_file,
    generate_summary_dict,
    _format_item_detail,
    _format_waived_item,
    _summarize_violation
)
from yaml_generator import generate_summary_yaml, append_to_summary_yaml


class TestGenerateLogFile:
    """测试generate_log_file函数"""
    
    def test_type1_pass_log(self):
        l5_output = {
            'status': 'PASS',
            'found_items': [
                {
                    'value': 'found1',
                    'description': 'test desc',
                    'source_file': '/path/file.rpt',
                    'line_number': 10,
                    'matched_content': 'content',
                    'parsed_fields': {}
                }
            ],
            'missing_items': []
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.log"
            
            generate_log_file(
                l5_output=l5_output,
                type_id=1,
                item_id="TEST-01",
                item_desc="Test checker",
                output_path=output_path
            )
            
            assert output_path.exists()
            content = output_path.read_text(encoding='utf-8')
            
            assert "TEST-01" in content
            assert "Status: PASS" in content
            assert "Found Items (1)" in content
            assert "found1" in content
    
    def test_type2_with_missing_and_extra(self):
        l5_output = {
            'status': 'FAIL',
            'found_items': [],
            'missing_items': [
                {
                    'expected': 'missing_pattern',
                    'description': 'desc',
                    'source_file': '',  # Ghost
                    'line_number': None,
                    'matched_content': '',
                    'parsed_fields': {},
                    'searched_files': ['/file1.rpt', '/file2.rpt']
                }
            ],
            'extra_items': [
                {
                    'value': 'extra_item',
                    'description': 'desc',
                    'source_file': '/file.rpt',
                    'line_number': 5,
                    'matched_content': 'extra',
                    'parsed_fields': {}
                }
            ]
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.log"
            
            generate_log_file(
                l5_output=l5_output,
                type_id=2,
                item_id="TEST-02",
                item_desc="Test checker",
                output_path=output_path
            )
            
            content = output_path.read_text(encoding='utf-8')
            
            assert "Status: FAIL" in content
            assert "Missing Items (1)" in content
            assert "missing_pattern" in content
            assert "Extra Items (1)" in content
            assert "extra_item" in content
    
    def test_type3_with_waived(self):
        l5_output = {
            'status': 'PASS',
            'found_items': [],
            'missing_items': [],
            'extra_items': [],
            'waived': [
                {
                    'expected': 'waived_pattern',
                    'description': 'desc',
                    'waiver_pattern': 'pattern1',
                    'waiver_reason': 'Test reason',
                    'tag': '[WAIVER]'
                }
            ],
            'unused_waivers': [
                {'pattern': 'unused1', 'reason': 'Not matched'}
            ]
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.log"
            
            generate_log_file(
                l5_output=l5_output,
                type_id=3,
                item_id="TEST-03",
                item_desc="Test checker",
                output_path=output_path
            )
            
            content = output_path.read_text(encoding='utf-8')
            
            assert "Waived Items (1)" in content
            assert "Waiver Pattern: pattern1" in content
            assert "Unused Waivers (1)" in content
            assert "unused1" in content


class TestGenerateSummaryDict:
    """测试generate_summary_dict函数"""
    
    def test_pass_with_no_violations(self):
        l5_output = {
            'status': 'PASS',
            'found_items': [{'value': 'found'}],
            'missing_items': []
        }
        
        summary = generate_summary_dict(
            l5_output=l5_output,
            type_id=1,
            item_id="TEST-01",
            item_desc="Test desc"
        )
        
        assert summary['executed'] is True
        assert summary['status'] == 'PASS'
        assert summary['description'] == "Test desc"
        assert len(summary['failures']) == 0
        assert len(summary['warnings']) == 0
    
    def test_fail_with_missing(self):
        l5_output = {
            'status': 'FAIL',
            'found_items': [],
            'missing_items': [
                {
                    'expected': 'pattern1',
                    'source_file': '/file.rpt',
                    'line_number': 10
                }
            ]
        }
        
        summary = generate_summary_dict(
            l5_output=l5_output,
            type_id=2,
            item_id="TEST-02",
            item_desc="Test desc"
        )
        
        assert summary['status'] == 'FAIL'
        assert len(summary['failures']) == 1
        assert summary['failures'][0]['kind'] == 'MISSING'
        assert 'pattern1' in summary['failures'][0]['detail']
    
    def test_warnings_vs_failures(self):
        l5_output = {
            'status': 'PASS',
            'found_items': [],
            'missing_items': [
                {'expected': 'fail', 'source_file': '/f.rpt'},
                {'expected': 'warn', 'source_file': '/f.rpt', 'severity': 'INFO'}
            ]
        }
        
        summary = generate_summary_dict(
            l5_output=l5_output,
            type_id=2,
            item_id="TEST-03",
            item_desc="Test desc"
        )
        
        assert len(summary['failures']) == 1
        assert len(summary['warnings']) == 1
        assert 'fail' in summary['failures'][0]['detail']
        assert 'warn' in summary['warnings'][0]['detail']


class TestYAMLGenerator:
    """测试YAML生成函数"""
    
    def test_generate_summary_yaml(self):
        summary_dict = {
            'executed': True,
            'status': 'PASS',
            'description': 'Test',
            'failures': [],
            'warnings': []
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            yaml_path = Path(tmpdir) / "summary.yaml"
            
            generate_summary_yaml(summary_dict, "TEST-01", yaml_path)
            
            assert yaml_path.exists()
            content = yaml_path.read_text(encoding='utf-8')
            
            assert "TEST-01" in content
            assert "status: PASS" in content
    
    def test_append_to_summary_yaml(self):
        summary1 = {
            'executed': True,
            'status': 'PASS',
            'description': 'Test1',
            'failures': [],
            'warnings': []
        }
        
        summary2 = {
            'executed': True,
            'status': 'FAIL',
            'description': 'Test2',
            'failures': [{'kind': 'MISSING', 'detail': 'x'}],
            'warnings': []
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            yaml_path = Path(tmpdir) / "summary.yaml"
            
            # First append
            append_to_summary_yaml(summary1, "TEST-01", yaml_path)
            
            # Second append
            append_to_summary_yaml(summary2, "TEST-02", yaml_path)
            
            content = yaml_path.read_text(encoding='utf-8')
            
            assert "TEST-01" in content
            assert "TEST-02" in content


class TestFormatItemDetail:
    """测试_format_item_detail函数"""
    
    def test_full_item_format(self):
        item = {
            'description': 'test desc',
            'value': 'test_value',
            'source_file': '/path/file.rpt',
            'line_number': 42,
            'matched_content': 'content',
            'parsed_fields': {'key': 'val'}
        }
        
        lines = _format_item_detail(item, 1)
        
        text = '\n'.join(lines)
        assert '[1]' in text
        assert 'test desc' in text
        assert 'test_value' in text
        assert '/path/file.rpt' in text
        assert '42' in text
    
    def test_ghost_item_format(self):
        item = {
            'expected': 'missing_pattern',
            'source_file': '',  # Ghost
            'line_number': None
        }
        
        lines = _format_item_detail(item, 1)
        
        text = '\n'.join(lines)
        assert 'missing_pattern' in text
        assert '(ghost)' in text
        assert 'N/A' in text


class TestSummarizeViolation:
    """测试_summarize_violation函数"""
    
    def test_summarize_missing(self):
        item = {
            'expected': 'pattern1',
            'source_file': '/file.rpt',
            'line_number': 10
        }
        
        summary = _summarize_violation(item, 'MISSING')
        
        assert summary['kind'] == 'MISSING'
        assert 'pattern1' in summary['detail']
        assert summary['source_file'] == '/file.rpt'
        assert summary['line_number'] == 10
    
    def test_summarize_extra(self):
        item = {
            'value': 'extra_value',
            'source_file': '/file.rpt',
            'line_number': 5
        }
        
        summary = _summarize_violation(item, 'EXTRA')
        
        assert summary['kind'] == 'EXTRA'
        assert 'extra_value' in summary['detail']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
