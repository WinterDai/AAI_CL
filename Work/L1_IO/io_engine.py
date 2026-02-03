"""
L1: IO Engine - File Reading and Path Resolution
Plan.txt Section 2, Layer 1
"""

import gzip
from pathlib import Path
from typing import Optional, Tuple


class IOError(Exception):
    """IO operation error"""
    pass


def read_file_content(file_path: str) -> Tuple[str, str]:
    """
    读取文件内容，支持gzip和编码fallback (Plan.txt Section 2, Layer 1)
    
    输入:
        file_path: 文件路径（相对或绝对）
        
    输出:
        Tuple[str, str] - (file_content, absolute_path)
        
    异常:
        IOError - 文件不存在或读取失败
        
    实现细节:
    1. 规范化路径为绝对路径
    2. 检测.gz扩展名自动使用gzip
    3. 编码fallback: utf-8 → latin-1 → 错误
    """
    # Normalize to absolute path
    abs_path = normalize_path(file_path)
    
    # Check file exists
    path_obj = Path(abs_path)
    if not path_obj.exists():
        raise IOError(f"File not found: {abs_path}")
    
    if not path_obj.is_file():
        raise IOError(f"Not a file: {abs_path}")
    
    # Read with gzip if needed
    is_gzipped = abs_path.endswith('.gz')
    
    try:
        if is_gzipped:
            content = _read_gzip_with_fallback(abs_path)
        else:
            content = _read_text_with_fallback(abs_path)
        
        return content, abs_path
    
    except Exception as e:
        raise IOError(f"Failed to read file {abs_path}: {str(e)}")


def normalize_path(path: str, base_dir: Optional[str] = None) -> str:
    """
    路径规范化为绝对路径 (Plan.txt Section 2, Layer 1)
    
    输入:
        path: 相对或绝对路径
        base_dir: 相对路径的基准目录（用于indirect reference解析）
        
    输出:
        str - 绝对路径
        
    实现细节:
    - 相对路径: 使用base_dir或当前工作目录
    - 绝对路径: 直接返回
    - 路径解析: 使用Path.resolve()处理 .. 和 .
    """
    path_obj = Path(path)
    
    # Already absolute
    if path_obj.is_absolute():
        return str(path_obj.resolve())
    
    # Relative path
    if base_dir:
        base_path = Path(base_dir)
        full_path = base_path / path_obj
    else:
        full_path = path_obj
    
    return str(full_path.resolve())


def resolve_indirect_reference(
    indirect_ref: str,
    current_file_path: str
) -> str:
    """
    解析indirect reference为绝对路径 (Plan.txt Section 2, Layer 1)
    
    输入:
        indirect_ref: 相对或绝对路径
        current_file_path: 当前文件的绝对路径
        
    输出:
        str - indirect reference的绝对路径
        
    实现细节:
    - 相对路径基于当前文件所在目录
    - 绝对路径直接返回
    """
    current_dir = str(Path(current_file_path).parent)
    return normalize_path(indirect_ref, base_dir=current_dir)


def _read_text_with_fallback(file_path: str) -> str:
    """
    读取文本文件，编码fallback
    
    尝试顺序: utf-8 → latin-1
    """
    # Try utf-8 first
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        pass
    
    # Fallback to latin-1
    try:
        with open(file_path, 'r', encoding='latin-1') as f:
            return f.read()
    except Exception as e:
        raise IOError(f"Failed to decode file with utf-8 and latin-1: {str(e)}")


def _read_gzip_with_fallback(file_path: str) -> str:
    """
    读取gzip文件，编码fallback
    
    尝试顺序: utf-8 → latin-1
    """
    # Try utf-8 first
    try:
        with gzip.open(file_path, 'rt', encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        pass
    
    # Fallback to latin-1
    try:
        with gzip.open(file_path, 'rt', encoding='latin-1') as f:
            return f.read()
    except Exception as e:
        raise IOError(f"Failed to decode gzip file with utf-8 and latin-1: {str(e)}")
