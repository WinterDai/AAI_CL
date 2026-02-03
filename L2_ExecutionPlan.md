# L2 执行Plan: 解析编排器

## 1. 层级职责
Layer 2负责协调整个解析过程，包括递归处理间接引用、管理访问过的路径、对ParsedItems进行稳定排序，并生成searched_files列表。

## 2. 交付物
- `parsing_orchestrator.py` - 解析编排主模块
- `recursion_guard.py` - 递归控制和循环检测
- `stable_sorter.py` - 三级稳定排序实现
- `test_l2.py` - Layer 2单元测试

## 3. 公开API

### 3.0 Atom A Interface Specification (Plan_v2.txt Section 1 - Locked)

#### 函数签名
```python
def extract_context(text: str, source_file: str) -> List[ParsedItem]:
    """
    Layer 2 Atom A: Context Extractor
    
    [Locked] 函数名称: extract_context
    [Locked] 参数:
        - text: str - 文件内容（由L1 IO Engine提供）
        - source_file: str - 源文件绝对路径（用于元数据追踪）
    [Locked] 返回: List[ParsedItem]
    
    约束:
    1. NO IO allowed - Atom A不得进行任何文件读取
    2. PR5: 不得根据requirements/waivers过滤结果
    3. Value Type Hard Lock: 所有'value'字段必须转换为str类型
    """
    pass
```

#### Standardization Layer (Plan_v2.txt Section 1 - Locked)

**强制数据接口契约** - 防止Layer 3崩溃

Atom A实现必须包含以下标准化逻辑：

```python
# [Locked] Standardization Layer
standardized_output = []
for item in results:
    # [Critical] Ensure value is string (Gate 1 Requirement)
    safe_value = str(item.get("value", ""))
    
    standardized_item = {
        "value": safe_value,                      # 强制转换为str
        "source_file": source_file,               # 透传元数据
        "line_number": item.get("line_number"),   # 允许None
        "matched_content": str(item.get("matched_content", "")),
        "parsed_fields": item.get("parsed_fields", {})  # 必须是非None字典
    }
    standardized_output.append(standardized_item)
    
return standardized_output
```

**标准化规则 (Locked)**:
1. `value`字段:
   - 如果是None → 转换为 `""`
   - 如果是numeric/bool → 通过 `str()` 转换
   - 必须保证 `isinstance(item['value'], str)` 为True

2. `matched_content`字段:
   - 同样强制转换为str
   - 缺失时默认为 `""`

3. `parsed_fields`字段:
   - 缺失时默认为空字典 `{}`
   - 不得为None

4. `line_number`字段:
   - 允许为None（表示无法定位到具体行）
   - 如果有值，应为int类型

**Gate 1测试要求 (Plan_v2.txt Section 5 - Locked)**:

Atom A实现必须通过以下测试：

1. **Signature Check**: 函数名必须为 `extract_context`，接受 `(text: str, source_file: str)` 参数

2. **Schema Check**: 每个返回的ParsedItem必须包含keys:
   - `value`, `source_file`, `line_number`, `matched_content`, `parsed_fields`

3. **Value Type Safety**: 所有 `item['value']` 必须是str类型
   - 测试: `assert isinstance(item['value'], str), "ParsedItem['value'] must be str"`

### 3.1 Main Orchestrator API
```python
from typing import List, Dict, Callable, Any, Tuple

# Plan.txt Line 25: ParsedItem = Dict[str, Any]
ParsedItem = Dict[str, Any]

def orchestrate_parsing(
    input_files: List[str],
    atom_a_func: Callable[[str, str], List[ParsedItem]]
) -> Tuple[List[ParsedItem], List[str]]:
    """
    解析编排主函数 (Plan.txt Section 2, Layer 2)
    
    流程:
    1. 从input_files开始DFS遍历
    2. 对每个文件调用L1的read_file_text读取 → Atom A解析
    3. 检测indirect_reference → 递归处理
    4. 收集所有ParsedItem和visited_paths
    5. 稳定排序ParsedItems_All
    6. 生成searched_files列表
    
    输入:
        input_files: 根文件列表 (绝对路径)
        atom_a_func: Atom A函数引用
        
    输出:
        Tuple[parsed_items_all, searched_files]
        - parsed_items_all: List[ParsedItem] - 排序后的所有ParsedItem
        - searched_files: List[str] - 去重排序的绝对路径列表
        
    注意: 
    - Plan.txt未定义ParseResult类，使用Tuple返回
    - L2内部直接导入L1的read_file_text函数，L1使用模块函数不是类
    - 从 L1 导入: from l1_io_engine import read_file_text, resolve_indirect_reference
    """
    pass
```

### 3.2 Recursion Guard API
```python
# NOTE: RecursionGuard is an INTERNAL helper class for L2 implementation.
# Plan.txt does NOT define this class because it's not part of the Layer API contract.
# Plan.txt only specifies behavior: "max_depth = 5" and "visited_paths = set()".
# This class is an implementation choice to manage recursion state.

class RecursionGuard:
    """递归控制器 (Plan.txt Section 2, Layer 2)
    
    注意: 这是L2内部实现细节，不是跨层API
    Plan.txt未定义此类，因为它是内部状态管理工具
    """
    
    def __init__(self, max_depth: int = 5):
        self.max_depth = max_depth
        self.current_depth = 0
        self.visited_paths: set = set()
    
    def can_visit(self, file_path: str) -> bool:
        """
        检查是否可以访问该文件
        
        规则:
        - 当前深度 < max_depth
        - file_path不在visited_paths中
        """
        pass
    
    def enter(self, file_path: str):
        """进入文件（递归深度+1）"""
        pass
    
    def exit(self, file_path: str):
        """退出文件（递归深度-1）"""
        pass
    
    def mark_visited(self, file_path: str):
        """标记路径已访问"""
        pass
```

### 3.3 Indirect Reference Handler API
```python
def normalize_indirect_reference(parsed_fields: Dict) -> List[str]:
    """
    规范化indirect_reference (Plan.txt Section 2, Layer 2)
    
    规则:
    - str → List[str]
    - List[str] → 直接返回
    - 不存在 → 返回空列表
    
    **关键说明 (Locked):**
    相对路径的解析基准是**包含该引用的文件所在目录**，而非工作目录或根输入文件目录。
    
    示例:
    - 当前文件: /project/src/main.c
    - 包含: indirect_reference: "../lib/utils.c"
    - 解析为: /project/lib/utils.c (相对于/project/src/)
    - 而非: /project/../lib/utils.c (相对于工作目录)
    
    实现方式:
    ```python
    base_dir = os.path.dirname(current_file)
    resolved = os.path.join(base_dir, reference)
    return os.path.abspath(resolved)
    ```
    
    输入:
        parsed_fields: ParsedItem的parsed_fields字典
        
    输出:
        List[str]
    """
    pass

def extract_indirect_references(parsed_items: List[ParsedItem]) -> List[str]:
    """
    从ParsedItem列表中提取所有indirect_reference
    
    输入:
        parsed_items: Atom A返回的ParsedItem列表
        
    输出:
        所有indirect_reference的合并列表
    """
    pass
```

### 3.4 Stable Sorter API
```python
def stable_sort_parsed_items(
    parsed_items: List[ParsedItem],
    file_order_map: Dict[str, int]
) -> List[ParsedItem]:
    """
    三级稳定排序 (Plan.txt Section 2, Layer 2 - Locked)
    
    排序规则:
    1. File Order: 使用file_order_map映射
    2. Line Order: 升序，None视为+∞ (排在最后)
    3. Extraction Order: 保持Atom A列表顺序
    
    多个line_number=None的处理:
        当同一个文件有多个line_number=None的items时，
        它们按照Atom A返回的顺序排列（稳定排序的特性）
        
    示例:
        File A, line 5
        File A, line 10
        File A, line None (Atom A返回的第1个None)
        File A, line None (Atom A返回的第2个None)
        File B, line 1
        
    实现:
        使用Python的sorted()，它是稳定排序
        key函数返回 (file_order, line_number_or_inf, original_index)
    
    输入:
        parsed_items: 未排序的ParsedItem列表
        file_order_map: {file_path: order_index}
        
    输出:
        排序后的ParsedItem列表
    """
    pass

def create_file_order_map(traversal_order: List[str]) -> Dict[str, int]:
    """
    根据遍历顺序创建文件顺序映射
    
    遍历顺序:
    - Root files: input_files列表顺序
    - Indirect refs: DFS发现顺序
    
    输入:
        traversal_order: 文件遍历的顺序列表
        
    输出:
        {file_path: index} 映射
    """
    pass
```

## 4. 输入输出Schema

### 4.1 输入Schema
```python
# orchestrate_parsing输入
{
    'input_files': List[str],  # 例如: ["/file1.txt", "/file2.txt"]
    'atom_a_func': Callable,   # Atom A函数
    'io_engine': IOEngine      # L1的IO引擎实例
}
```

### 4.2 输出Schema (ParseResult)
```python
{
    'parsed_items_all': [
        {
            'value': str,
            'source_file': str,        # 绝对路径
            'line_number': int | None,
            'matched_content': str,
            'parsed_fields': {
                'indirect_reference': str | List[str],  # 可选
                ...  # 其他字段
            }
        },
        ...
    ],
    'searched_files': ["/abs/path1.txt", "/abs/path2.txt"]  # 去重排序
}
```

## 5. 依赖关系

### Mock依赖
- **Atom A函数**: Mock为返回预定义ParsedItem列表
- **IO Engine**: Mock读取返回预定义文本

### 真实依赖
- **L1 IO Engine**: 用于文件读取和路径解析

## 6. 测试策略

### 6.1 单文件解析测试
```python
def test_single_file_parsing(mock_io, mock_atom_a):
    """测试单文件解析"""
    mock_io.read_file_text.return_value = "text"
    mock_atom_a.return_value = [
        {'value': 'val1', 'source_file': '/f1', 'line_number': 1, 
         'matched_content': 'line1', 'parsed_fields': {}}
    ]
    
    # orchestrate_parsing returns Tuple[List[ParsedItem], List[str]]
    parsed_items_all, searched_files = orchestrate_parsing(["/f1"], mock_atom_a)
    
    assert len(parsed_items_all) == 1
    assert searched_files == ["/f1"]
```

### 6.2 递归解析测试
```python
def test_indirect_reference_recursion(mock_io, mock_atom_a):
    """测试indirect_reference递归"""
    # File1 引用 File2
    def atom_a_side_effect(text, source_file):
        if source_file == "/file1":
            return [{
                'value': 'v1',
                'source_file': '/file1',
                'line_number': 1,
                'matched_content': 'ref',
                'parsed_fields': {'indirect_reference': '/file2'}
            }]
        elif source_file == "/file2":
            return [{
                'value': 'v2',
                'source_file': '/file2',
                'line_number': 1,
                'matched_content': 'data',
                'parsed_fields': {}
            }]
        return []
    
    mock_atom_a.side_effect = atom_a_side_effect
    
    # orchestrate_parsing returns Tuple
    parsed_items_all, searched_files = orchestrate_parsing(["/file1"], mock_atom_a)
    
    assert len(parsed_items_all) == 2
    assert set(searched_files) == {"/file1", "/file2"}
```

### 6.3 递归深度限制测试
```python
def test_max_depth_limit(mock_io, mock_atom_a):
    """测试max_depth=5限制"""
    # 创建6层递归链
    def atom_a_side_effect(text, source_file):
        level = int(source_file.split("file")[1])
        if level < 7:
            return [{
                'value': f'v{level}',
                'source_file': source_file,
                'line_number': 1,
                'matched_content': 'ref',
                'parsed_fields': {'indirect_reference': f'/file{level+1}'}
            }]
        return []
    
    mock_atom_a.side_effect = atom_a_side_effect
    
    parsed_items_all, searched_files = orchestrate_parsing(["/file1"], mock_atom_a)
    
    # 应该只有5层 (file1-file5)
    assert len(searched_files) <= 5
```

### 6.4 循环检测测试
```python
def test_loop_detection(mock_io, mock_atom_a):
    """测试循环引用检测"""
    # File1 → File2 → File1 (循环)
    def atom_a_side_effect(text, source_file):
        if source_file == "/file1":
            return [{
                'value': 'v1',
                'source_file': '/file1',
                'line_number': 1,
                'matched_content': 'ref',
                'parsed_fields': {'indirect_reference': '/file2'}
            }]
        elif source_file == "/file2":
            return [{
                'value': 'v2',
                'source_file': '/file2',
                'line_number': 1,
                'matched_content': 'ref',
                'parsed_fields': {'indirect_reference': '/file1'}  # 循环
            }]
        return []
    
    mock_atom_a.side_effect = atom_a_side_effect
    
    parsed_items_all, searched_files = orchestrate_parsing(["/file1"], mock_atom_a)
    
    # 应该只访问两个文件，不进入无限循环
    assert len(searched_files) == 2
```

### 6.5 稳定排序测试
```python
def test_stable_sort_file_order():
    """测试文件顺序排序"""
    items = [
        {'value': 'v2', 'source_file': '/file2', 'line_number': 1, 
         'matched_content': '', 'parsed_fields': {}},
        {'value': 'v1', 'source_file': '/file1', 'line_number': 1, 
         'matched_content': '', 'parsed_fields': {}}
    ]
    file_order = {'/file1': 0, '/file2': 1}
    
    sorted_items = stable_sort_parsed_items(items, file_order)
    
    assert sorted_items[0]['source_file'] == '/file1'
    assert sorted_items[1]['source_file'] == '/file2'

def test_stable_sort_line_order():
    """测试行号排序"""
    items = [
        {'value': 'v3', 'source_file': '/f1', 'line_number': None, 
         'matched_content': '', 'parsed_fields': {}},
        {'value': 'v2', 'source_file': '/f1', 'line_number': 10, 
         'matched_content': '', 'parsed_fields': {}},
        {'value': 'v1', 'source_file': '/f1', 'line_number': 5, 
         'matched_content': '', 'parsed_fields': {}}
    ]
    file_order = {'/f1': 0}
    
    sorted_items = stable_sort_parsed_items(items, file_order)
    
    assert sorted_items[0]['line_number'] == 5
    assert sorted_items[1]['line_number'] == 10
    assert sorted_items[2]['line_number'] is None  # None在最后

def test_stable_sort_extraction_order():
    """测试提取顺序保持"""
    items = [
        {'value': 'v2', 'source_file': '/f1', 'line_number': 1, 
         'matched_content': '', 'parsed_fields': {}},
        {'value': 'v1', 'source_file': '/f1', 'line_number': 1, 
         'matched_content': '', 'parsed_fields': {}}
    ]
    file_order = {'/f1': 0}
    
    sorted_items = stable_sort_parsed_items(items, file_order)
    
    # 同文件同行号，保持原始顺序
    assert sorted_items[0]['value'] == 'v2'
    assert sorted_items[1]['value'] == 'v1'
```

### 6.6 searched_files测试
```python
def test_searched_files_dedup_and_sort(mock_io, mock_atom_a):
    """测试searched_files去重和排序"""
    # 多个item引用相同文件
    mock_atom_a.return_value = [
        {'value': 'v1', 'source_file': '/file2', 'line_number': 1, 
         'matched_content': '', 'parsed_fields': {}},
        {'value': 'v2', 'source_file': '/file1', 'line_number': 1, 
         'matched_content': '', 'parsed_fields': {}}
    ]
    
    parsed_items_all, searched_files = orchestrate_parsing(["/file1"], mock_atom_a)
    
    # 应该去重并按字母序排序
    assert searched_files == ["/file1", "/file2"]
```

## 7. 关键实现要求 (Plan.txt提取)

### 7.1 indirect_reference规范化
> **Plan.txt Section 2, Layer 2: Indirect Reference Normalization**
> - If parsed_fields["indirect_reference"] is str → convert to List[str]
> - If List[str] → use as is

### 7.2 递归守卫
> **Plan.txt Section 2, Layer 2: Recursion Guard**
> - max_depth = 5
> - visited_paths = set() loop detection: revisiting a path MUST skip recursion (no infinite loop)

### 7.3 遍历顺序
> **Plan.txt Section 2, Layer 2: Traversal Order (Locked)**
> - Root files follow input_files list order (insertion order)
> - Indirect refs follow DFS discovery order

### 7.4 稳定排序
> **Plan.txt Section 2, Layer 2: Stable Sort Order (Locked)**
> - File Order: insertion + DFS recursion discovery order
> - Line Order: ascending line_number (None treated as +∞, last)
> - Extraction Order: preserve Atom A list order for same file & same line

### 7.5 searched_files
> **Plan.txt Section 2, Layer 2: searched_files Source (Locked)**
> - MUST include all successfully read absolute paths in parsing traversal (root + indirect refs)
> - then be deduplicated and sorted alphabetically

## 8. 验收标准

### 必须通过的测试
- [ ] 单文件解析正确
- [ ] indirect_reference递归正确
- [ ] max_depth=5限制生效
- [ ] 循环引用检测成功（不死循环）
- [ ] 三级稳定排序正确 (File>Line>Extraction)
- [ ] None line_number排在最后
- [ ] searched_files去重和字母序排序
- [ ] DFS遍历顺序正确

### 代码质量要求
- [ ] 类型注解完整
- [ ] 单元测试覆盖率 >= 95%
- [ ] 递归实现清晰（或使用显式栈）

### 性能要求
- [ ] 100个文件解析 < 1s
- [ ] 稳定排序 < 100ms

## 9. 调试提示

### 常见错误
1. **无限循环**: 检查visited_paths是否正确更新
2. **排序错误**: 确保sort key的优先级正确
3. **深度超限**: 检查recursion guard的enter/exit逻辑

### 调试日志建议
```python
import logging
logger = logging.getLogger(__name__)

logger.debug(f"Visiting file: {file_path}, depth: {guard.current_depth}")
logger.debug(f"Found indirect refs: {refs}")
logger.debug(f"Visited paths: {guard.visited_paths}")
```

## 10. 文件结构
```
L2/
├── parsing_orchestrator.py  # 解析编排主逻辑
├── recursion_guard.py        # 递归控制
├── stable_sorter.py          # 稳定排序实现
├── test_l2.py                # 单元测试
└── README.md                 # L2使用文档
```
