# L1 执行Plan: IO引擎 + 路径解析器

## 1. 层级职责
Layer 1负责所有文件I/O抽象、路径规范化和间接引用解析。Atoms永远不接触文件操作，所有文件读取由L1统一处理。

## 2. 交付物
- `io_engine.py` - 文件读取引擎
- `path_resolver.py` - 路径规范化和解析
- `test_l1.py` - Layer 1单元测试
- `mock_files.py` - 测试用的文件mock工具

## 3. 公开API

### 3.1 File Reader API
```python
from typing import Optional
import gzip

class FileReadError(Exception):
    """文件读取失败时抛出"""
    pass

def read_file_text(file_path: str) -> str:
    """
    读取文件内容为文本 (Plan.txt Section 2, Layer 1)
    
    功能:
    - 自动检测gzip文件 (通过.gz扩展名或magic number)
    - 编码降级策略: utf-8 → latin-1 → ascii
    - 绝对路径规范化
    
    输入:
        file_path: 文件路径 (绝对或相对)
        
    输出:
        文件文本内容 (str)
        
    异常:
        FileReadError - 文件不存在或读取失败
    """
    pass

def is_gzip_file(file_path: str) -> bool:
    """
    检测文件是否为gzip压缩文件
    
    策略:
    1. 检查扩展名是否为.gz
    2. 检查magic number (前两个字节是否为0x1f 0x8b)
    """
    pass

def read_with_encoding_fallback(file_path: str) -> str:
    """
    带编码降级的文件读取
    
    编码尝试顺序: utf-8 → latin-1 → ascii
    """
    pass
```

### 3.2 Path Resolver API
```python
import os
from pathlib import Path

def normalize_to_absolute(file_path: str) -> str:
    """
    规范化路径为绝对路径 (Plan.txt Section 2, Layer 1)
    
    功能:
    - 相对路径 → 绝对路径
    - 路径分隔符统一化 (Windows \ → /)
    - 去除冗余的 . 和 ..
    
    输入:
        file_path: 原始路径
        
    输出:
        绝对路径字符串
    """
    pass

def resolve_indirect_reference(
    current_file: str,
    reference: str
) -> str:
    """
    解析间接引用的相对路径 (Plan.txt Section 2, Layer 1)
    
    规则:
    - 相对路径相对于current_file的目录
    - 解析后必须返回绝对路径
    
    输入:
        current_file: 当前文件的绝对路径
        reference: 间接引用的路径 (可能是相对路径)
        
    输出:
        解析后的绝对路径
        
    示例:
        current_file = "/a/b/c.txt"
        reference = "../d.txt"
        → return "/a/d.txt"
    """
    pass

def get_searched_files_list(visited_paths: set) -> list:
    """
    生成searched_files列表 (Plan.txt Section 2, Layer 2)
    
    规则:
    - 去重
    - 字母序排序
    - 所有路径必须是绝对路径
    
    输入:
        visited_paths: 已访问路径的set
        
    输出:
        排序后的路径列表
    """
    pass
```

## 4. 输入输出Schema

### 4.1 输入Schema
```python
# read_file_text输入
{
    'file_path': str  # 例如: "/path/to/file.txt" 或 "relative/path.gz"
}

# resolve_indirect_reference输入
{
    'current_file': str,  # 例如: "/a/b/current.txt"
    'reference': str      # 例如: "../other.txt" 或 "/abs/path.txt"
}
```

### 4.2 输出Schema
```python
# read_file_text输出
str  # 文件文本内容

# normalize_to_absolute输出
str  # 绝对路径，例如: "/absolute/path/to/file.txt"

# get_searched_files_list输出
List[str]  # 例如: ["/a/file1.txt", "/b/file2.txt"]
```

## 5. 依赖关系

### Mock依赖
- **文件系统**: 使用mock_files.py提供的mock文件系统
- **gzip模块**: 测试时mock gzip压缩文件

### 真实依赖
- Python标准库: `os`, `pathlib`, `gzip`, `io`

## 6. 测试策略

### 6.1 文件读取测试
```python
def test_read_regular_file(mock_fs):
    """测试普通文件读取"""
    mock_fs.create_file("/test.txt", "content")
    result = read_file_text("/test.txt")
    assert result == "content"

def test_read_gzip_file(mock_fs):
    """测试gzip文件读取"""
    # 创建gzip mock
    content = b"compressed content"
    mock_fs.create_gzip("/test.gz", content)
    result = read_file_text("/test.gz")
    assert result == "compressed content"

def test_encoding_fallback(mock_fs):
    """测试编码降级"""
    # UTF-8失败 → latin-1成功
    mock_fs.create_file_with_encoding("/test.txt", b"\xff\xfe", encoding="latin-1")
    result = read_file_text("/test.txt")
    assert isinstance(result, str)

def test_file_not_found():
    """测试文件不存在"""
    with pytest.raises(FileReadError):
        read_file_text("/nonexistent.txt")
```

### 6.2 路径规范化测试
```python
def test_absolute_path():
    """测试绝对路径规范化"""
    assert normalize_to_absolute("/a/b/c.txt") == "/a/b/c.txt"

def test_relative_path():
    """测试相对路径转绝对路径"""
    # 依赖当前工作目录
    result = normalize_to_absolute("relative/path.txt")
    assert os.path.isabs(result)
    assert "relative/path.txt" in result

def test_path_with_dots():
    """测试路径中的.和.."""
    result = normalize_to_absolute("/a/b/../c/./d.txt")
    assert result == "/a/c/d.txt"

def test_windows_backslash():
    """测试Windows反斜杠"""
    # 在Windows上
    result = normalize_to_absolute("C:\\Users\\test\\file.txt")
    assert "\\" not in result or os.name != 'nt'  # 统一为正斜杠或保持平台格式
```

### 6.3 间接引用解析测试
```python
def test_resolve_relative_reference():
    """测试相对路径解析"""
    current = "/a/b/c.txt"
    reference = "../d.txt"
    result = resolve_indirect_reference(current, reference)
    assert result == "/a/d.txt"

def test_resolve_absolute_reference():
    """测试绝对路径引用"""
    current = "/a/b/c.txt"
    reference = "/x/y/z.txt"
    result = resolve_indirect_reference(current, reference)
    assert result == "/x/y/z.txt"

def test_resolve_same_directory():
    """测试同目录引用"""
    current = "/a/b/c.txt"
    reference = "d.txt"
    result = resolve_indirect_reference(current, reference)
    assert result == "/a/b/d.txt"
```

### 6.4 searched_files生成测试
```python
def test_searched_files_deduplication():
    """测试去重"""
    visited = {"/a.txt", "/b.txt", "/a.txt"}  # 重复
    result = get_searched_files_list(visited)
    assert len(result) == 2
    assert "/a.txt" in result
    assert "/b.txt" in result

def test_searched_files_sorting():
    """测试字母序排序"""
    visited = {"/z.txt", "/a.txt", "/m.txt"}
    result = get_searched_files_list(visited)
    assert result == ["/a.txt", "/m.txt", "/z.txt"]

def test_searched_files_absolute_paths():
    """测试所有路径为绝对路径"""
    visited = {"/a.txt", "/b/c.txt"}
    result = get_searched_files_list(visited)
    for path in result:
        assert os.path.isabs(path)
```

### 6.5 边界条件测试
```python
def test_empty_file():
    """测试空文件"""
    mock_fs.create_file("/empty.txt", "")
    result = read_file_text("/empty.txt")
    assert result == ""

def test_large_file():
    """测试大文件"""
    content = "x" * (10 * 1024 * 1024)  # 10MB
    mock_fs.create_file("/large.txt", content)
    result = read_file_text("/large.txt")
    assert len(result) == len(content)

def test_binary_file():
    """测试二进制文件"""
    # 编码降级应该能处理
    mock_fs.create_binary_file("/binary.dat", b"\x00\x01\x02")
    result = read_file_text("/binary.dat")
    assert isinstance(result, str)
```

## 7. 关键实现要求 (Plan.txt提取)

### 7.1 文件I/O抽象 (Locked)
> **Plan.txt Section 2, Layer 1: IO Engine (Locked)**
> - Handles open, gzip, encoding fallback, absolute path normalization
> - Supplies text to Atom A; Atoms never see file I/O

### 7.2 间接引用解析
> **Plan.txt Section 2, Layer 1**
> - Indirect Reference Resolution: Resolve relative paths against current file directory, normalize to absolute

### 7.3 searched_files规则
> **Plan.txt Section 2, Layer 2: searched_files Source (Locked)**
> - searched_files MUST include all successfully read absolute paths in parsing traversal (root + indirect refs)
> - then be deduplicated and sorted alphabetically

## 8. 验收标准

### 必须通过的测试
- [ ] 普通文件读取成功
- [ ] gzip文件自动解压并读取
- [ ] 编码降级策略正确 (utf-8 → latin-1 → ascii)
- [ ] 绝对路径规范化正确
- [ ] 相对路径正确解析
- [ ] 间接引用解析正确 (相对于当前文件目录)
- [ ] searched_files去重和排序正确
- [ ] FileReadError在文件不存在时正确抛出

### 代码质量要求
- [ ] 类型注解完整
- [ ] 单元测试覆盖率 >= 95%
- [ ] 跨平台兼容 (Windows/Linux/Mac)

### 性能要求
- [ ] 小文件读取 (<1MB) < 10ms
- [ ] 路径规范化 < 1ms

## 9. 调试提示

### 常见错误
1. **gzip文件读取失败**: 检查magic number判断逻辑
2. **Windows路径问题**: 使用pathlib或os.path确保跨平台
3. **编码错误**: 确保fallback顺序正确

### 调试日志建议
```python
import logging
logger = logging.getLogger(__name__)

logger.debug(f"Reading file: {file_path}")
logger.debug(f"Is gzip: {is_gzip_file(file_path)}")
logger.debug(f"Resolved path: {normalize_to_absolute(file_path)}")
```

## 10. 文件结构
```
L1/
├── io_engine.py        # 文件读取实现
├── path_resolver.py    # 路径解析实现
├── test_l1.py          # 单元测试
├── mock_files.py       # 文件系统mock工具
└── README.md           # L1使用文档
```
