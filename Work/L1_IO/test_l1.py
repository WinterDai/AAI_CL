"""
Unit tests for L1: IO Engine
"""

import pytest
import tempfile
import gzip
from pathlib import Path
from io_engine import (
    read_file_content,
    normalize_path,
    resolve_indirect_reference,
    IOError
)


class TestReadFileContent:
    """测试read_file_content函数"""
    
    def test_read_plain_text_file(self):
        # Create temp file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("test content\nline 2")
            temp_path = f.name
        
        try:
            content, abs_path = read_file_content(temp_path)
            assert content == "test content\nline 2"
            assert Path(abs_path).is_absolute()
        finally:
            Path(temp_path).unlink()
    
    def test_read_gzip_file(self):
        # Create temp gzip file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.gz') as f:
            temp_path = f.name
        
        with gzip.open(temp_path, 'wt', encoding='utf-8') as f:
            f.write("gzipped content")
        
        try:
            content, abs_path = read_file_content(temp_path)
            assert content == "gzipped content"
            assert abs_path.endswith('.gz')
        finally:
            Path(temp_path).unlink()
    
    def test_file_not_found(self):
        with pytest.raises(IOError, match="File not found"):
            read_file_content("/nonexistent/path/file.txt")
    
    def test_latin1_fallback(self):
        # Create file with latin-1 encoding
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.txt') as f:
            # Write bytes that are valid latin-1 but not utf-8
            f.write(b'\xe9\xe0\xe8')  # é à è in latin-1
            temp_path = f.name
        
        try:
            content, _ = read_file_content(temp_path)
            assert len(content) == 3
        finally:
            Path(temp_path).unlink()


class TestNormalizePath:
    """测试normalize_path函数"""
    
    def test_absolute_path(self):
        if Path('/').exists():  # Unix-like
            result = normalize_path('/home/user/file.txt')
            assert Path(result).is_absolute()
        else:  # Windows
            result = normalize_path('C:\\Users\\file.txt')
            assert Path(result).is_absolute()
    
    def test_relative_path_no_base(self):
        result = normalize_path('file.txt')
        assert Path(result).is_absolute()
    
    def test_relative_path_with_base(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = tmpdir
            result = normalize_path('subdir/file.txt', base_dir=base_dir)
            assert Path(result).is_absolute()
            assert 'subdir' in result
    
    def test_path_with_dots(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = normalize_path('../file.txt', base_dir=tmpdir)
            assert Path(result).is_absolute()


class TestResolveIndirectReference:
    """测试resolve_indirect_reference函数"""
    
    def test_relative_reference(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            current_file = str(Path(tmpdir) / "dir1" / "current.rpt")
            indirect_ref = "../dir2/other.rpt"
            
            result = resolve_indirect_reference(indirect_ref, current_file)
            
            assert Path(result).is_absolute()
            assert 'dir2' in result
    
    def test_absolute_reference(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            current_file = str(Path(tmpdir) / "current.rpt")
            indirect_ref = str(Path(tmpdir) / "other.rpt")
            
            result = resolve_indirect_reference(indirect_ref, current_file)
            
            assert result == str(Path(indirect_ref).resolve())


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
