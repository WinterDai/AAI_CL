"""
Unit tests for L2: Parsing Orchestration
"""

import pytest
from parsing_orchestrator import (
    orchestrate_parsing,
    extract_indirect_references,
    stable_sort_parsed_items,
    ParseError
)


class TestOrchestrateParsing:
    """测试orchestrate_parsing主函数"""
    
    def test_basic_parsing(self):
        # Mock Atom A
        def mock_atom_a(text, source_file):
            return [
                {'value': 'item1', 'line_number': 10, 'matched_content': 'content1', 'parsed_fields': {}, 'source_file': source_file},
                {'value': 'item2', 'line_number': 20, 'matched_content': 'content2', 'parsed_fields': {}, 'source_file': source_file}
            ]
        
        # Mock IO
        def mock_io_read(path):
            return "file content", "/abs/path/file.rpt"
        
        parsed_items_all, searched_files = orchestrate_parsing(
            input_files=["/path/file.rpt"],
            atom_a_func=mock_atom_a,
            io_read_func=mock_io_read
        )
        
        assert len(parsed_items_all) == 2
        assert parsed_items_all[0]['value'] == 'item1'
        assert parsed_items_all[0]['source_file'] == "/abs/path/file.rpt"
        assert searched_files == ["/abs/path/file.rpt"]
    
    def test_indirect_reference_recursion(self):
        call_count = {'count': 0}
        
        def mock_atom_a(text, source_file):
            call_count['count'] += 1
            if call_count['count'] == 1:
                # First file has indirect reference
                return [
                    {'value': 'root', 'line_number': 1, 'matched_content': 'root',
                     'parsed_fields': {'indirect_reference': 'other.rpt'}, 'source_file': source_file}
                ]
            else:
                # Second file
                return [
                    {'value': 'indirect', 'line_number': 1, 'matched_content': 'indirect', 'parsed_fields': {}, 'source_file': source_file}
                ]
        
        def mock_io_read(path):
            if 'root' in path:
                return "root content", "/abs/root.rpt"
            else:
                return "other content", "/abs/other.rpt"
        
        parsed_items_all, searched_files = orchestrate_parsing(
            input_files=["/abs/root.rpt"],
            atom_a_func=mock_atom_a,
            io_read_func=mock_io_read
        )
        
        assert len(parsed_items_all) == 2
        assert len(searched_files) == 2
        assert "/abs/root.rpt" in searched_files
        assert "/abs/other.rpt" in searched_files
    
    def test_max_depth_limit(self):
        def mock_atom_a(text, source_file):
            # Always return indirect reference
            return [
                {'value': 'item', 'line_number': 1, 'matched_content': 'content',
                 'parsed_fields': {'indirect_reference': 'next.rpt'}, 'source_file': source_file}
            ]
        
        file_counter = {'count': 0}
        
        def mock_io_read(path):
            file_counter['count'] += 1
            return f"content{file_counter['count']}", f"/abs/file{file_counter['count']}.rpt"
        
        parsed_items_all, searched_files = orchestrate_parsing(
            input_files=["/abs/file0.rpt"],
            atom_a_func=mock_atom_a,
            io_read_func=mock_io_read,
            max_depth=2
        )
        
        # Should stop at depth 2: root(0) + 1 + 2 = 3 files
        assert len(searched_files) == 3
    
    def test_loop_detection(self):
        def mock_atom_a(text, source_file):
            # Create circular reference
            return [
                {'value': 'item', 'line_number': 1, 'matched_content': 'content',
                 'parsed_fields': {'indirect_reference': '/abs/root.rpt'}, 'source_file': source_file}  # Loop back
            ]
        
        def mock_io_read(path):
            return "content", "/abs/root.rpt"
        
        parsed_items_all, searched_files = orchestrate_parsing(
            input_files=["/abs/root.rpt"],
            atom_a_func=mock_atom_a,
            io_read_func=mock_io_read
        )
        
        # Should visit root file only once
        assert len(searched_files) == 1
        assert len(parsed_items_all) == 1
    
    def test_searched_files_dedup_and_sort(self):
        def mock_atom_a(text, source_file):
            return [
                {'value': 'item', 'line_number': 1, 'matched_content': 'content', 'parsed_fields': {}, 'source_file': source_file}
            ]
        
        call_order = []
        
        def mock_io_read(path):
            call_order.append(path)
            if 'file1' in path:
                return "content", "/abs/b/file1.rpt"
            elif 'file2' in path:
                return "content", "/abs/a/file2.rpt"
            else:
                return "content", "/abs/c/file3.rpt"
        
        parsed_items_all, searched_files = orchestrate_parsing(
            input_files=["/abs/b/file1.rpt", "/abs/a/file2.rpt", "/abs/c/file3.rpt"],
            atom_a_func=mock_atom_a,
            io_read_func=mock_io_read
        )
        
        # searched_files should be sorted alphabetically
        assert searched_files == ["/abs/a/file2.rpt", "/abs/b/file1.rpt", "/abs/c/file3.rpt"]


class TestExtractIndirectReferences:
    """测试extract_indirect_references函数"""
    
    def test_string_reference(self):
        item = {
            'parsed_fields': {'indirect_reference': 'other.rpt'}
        }
        
        def mock_io_read(path):
            return "", path
        
        refs = extract_indirect_references(item, "/abs/current.rpt", mock_io_read)
        
        assert len(refs) == 1
        assert 'other.rpt' in refs[0]
    
    def test_list_reference(self):
        item = {
            'parsed_fields': {'indirect_reference': ['file1.rpt', 'file2.rpt']}
        }
        
        def mock_io_read(path):
            return "", path
        
        refs = extract_indirect_references(item, "/abs/current.rpt", mock_io_read)
        
        assert len(refs) == 2
    
    def test_no_indirect_reference(self):
        item = {
            'parsed_fields': {}
        }
        
        def mock_io_read(path):
            return "", path
        
        refs = extract_indirect_references(item, "/abs/current.rpt", mock_io_read)
        
        assert len(refs) == 0


class TestStableSortParsedItems:
    """测试stable_sort_parsed_items函数"""
    
    def test_sort_by_line_number(self):
        items = [
            {'source_file': '/a/f.rpt', 'line_number': 30, 'value': 'c'},
            {'source_file': '/a/f.rpt', 'line_number': 10, 'value': 'a'},
            {'source_file': '/a/f.rpt', 'line_number': 20, 'value': 'b'}
        ]
        
        sorted_items = stable_sort_parsed_items(items)
        
        assert sorted_items[0]['value'] == 'a'
        assert sorted_items[1]['value'] == 'b'
        assert sorted_items[2]['value'] == 'c'
    
    def test_none_line_number_last(self):
        items = [
            {'source_file': '/a/f.rpt', 'line_number': 10, 'value': 'a'},
            {'source_file': '/a/f.rpt', 'line_number': None, 'value': 'none'},
            {'source_file': '/a/f.rpt', 'line_number': 20, 'value': 'b'}
        ]
        
        sorted_items = stable_sort_parsed_items(items)
        
        assert sorted_items[0]['value'] == 'a'
        assert sorted_items[1]['value'] == 'b'
        assert sorted_items[2]['value'] == 'none'
    
    def test_preserve_file_order(self):
        items = [
            {'source_file': '/b/f2.rpt', 'line_number': 5, 'value': 'b1'},
            {'source_file': '/a/f1.rpt', 'line_number': 10, 'value': 'a1'},
            {'source_file': '/b/f2.rpt', 'line_number': 15, 'value': 'b2'}
        ]
        
        sorted_items = stable_sort_parsed_items(items)
        
        # Should maintain file insertion order: b, a
        assert sorted_items[0]['source_file'] == '/b/f2.rpt'
        assert sorted_items[0]['value'] == 'b1'
        assert sorted_items[1]['source_file'] == '/b/f2.rpt'
        assert sorted_items[1]['value'] == 'b2'
        assert sorted_items[2]['source_file'] == '/a/f1.rpt'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
