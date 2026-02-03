"""
L2: Parsing Orchestration - Recursive Parsing with DFS Traversal
Plan.txt Section 2, Layer 2
"""

from typing import Dict, Any, List, Tuple, Callable, Set, Optional


class ParseError(Exception):
    """Parsing orchestration error"""
    pass


def orchestrate_parsing(
    input_files: List[str],
    atom_a_func: Callable[[str], List[Dict]],
    io_read_func: Callable[[str], Tuple[str, str]],
    max_depth: int = 5
) -> Tuple[List[Dict], List[str]]:
    """
    解析编排主函数，支持递归和DFS遍历 (Plan.txt Section 2, Layer 2)
    
    输入:
        input_files: 根文件路径列表
        atom_a_func: Atom A函数 (text -> List[ParsedItem])
        io_read_func: IO读取函数 (path -> (content, abs_path))
        max_depth: 最大递归深度（默认5）
        
    输出:
        Tuple[List[ParsedItem], List[str]] - (parsed_items_all, searched_files)
        
    ParsedItem = Dict[str, Any] with keys:
        - 'value': str (mandatory)
        - 'line_number': int | None
        - 'source_file': str
        - 'matched_content': str
        - 'parsed_fields': Dict (可能包含'indirect_reference')
        
    searched_files: 成功读取的所有文件绝对路径（去重+排序）
        
    实现细节:
    - DFS遍历顺序: 根文件顺序 + 递归发现顺序
    - Loop detection: visited_paths集合，重复路径跳过
    - Max depth限制: 超过深度不继续递归
    - Indirect reference normalization: str → List[str]
    - 稳定排序: 文件顺序 → 行号 → 提取顺序
    """
    parsed_items_all = []
    searched_files_set = set()
    visited_paths = set()
    
    # Process root files
    for root_file in input_files:
        _parse_file_recursive(
            file_path=root_file,
            atom_a_func=atom_a_func,
            io_read_func=io_read_func,
            parsed_items_all=parsed_items_all,
            searched_files_set=searched_files_set,
            visited_paths=visited_paths,
            current_depth=0,
            max_depth=max_depth
        )
    
    # Stable sort
    parsed_items_all = stable_sort_parsed_items(parsed_items_all)
    
    # Searched files: dedup + sort
    searched_files = sorted(list(searched_files_set))
    
    return parsed_items_all, searched_files


def _parse_file_recursive(
    file_path: str,
    atom_a_func: Callable,
    io_read_func: Callable,
    parsed_items_all: List[Dict],
    searched_files_set: Set[str],
    visited_paths: Set[str],
    current_depth: int,
    max_depth: int
):
    """
    递归解析单个文件（内部函数）
    
    实现细节:
    - Loop detection: 路径已访问则跳过
    - Max depth: 超过深度则跳过
    - DFS: 立即递归处理indirect references
    """
    # Check max depth
    if current_depth > max_depth:
        return
    
    # Read file
    try:
        content, abs_path = io_read_func(file_path)
    except Exception:
        # File read failed, skip
        return
    
    # Loop detection
    if abs_path in visited_paths:
        return
    
    visited_paths.add(abs_path)
    searched_files_set.add(abs_path)
    
    # Call Atom A
    try:
        parsed_items = atom_a_func(content)
    except Exception:
        # Atom A failed, skip this file
        return
    
    # Add source_file to each item
    for item in parsed_items:
        item['source_file'] = abs_path
        parsed_items_all.append(item)
    
    # Process indirect references (DFS)
    for item in parsed_items:
        indirect_refs = extract_indirect_references(item, abs_path, io_read_func)
        for ref_path in indirect_refs:
            _parse_file_recursive(
                file_path=ref_path,
                atom_a_func=atom_a_func,
                io_read_func=io_read_func,
                parsed_items_all=parsed_items_all,
                searched_files_set=searched_files_set,
                visited_paths=visited_paths,
                current_depth=current_depth + 1,
                max_depth=max_depth
            )


def extract_indirect_references(
    item: Dict,
    current_file_abs_path: str,
    io_read_func: Callable
) -> List[str]:
    """
    提取并规范化indirect references (Plan.txt Section 2, Layer 2)
    
    输入:
        item: ParsedItem字典
        current_file_abs_path: 当前文件的绝对路径
        io_read_func: IO读取函数（用于resolve_indirect_reference）
        
    输出:
        List[str] - 绝对路径列表
        
    实现细节:
    - parsed_fields['indirect_reference'] 可能是 str 或 List[str]
    - str → 转为 List[str]
    - 相对路径基于当前文件所在目录解析
    """
    from pathlib import Path
    
    parsed_fields = item.get('parsed_fields', {})
    if not parsed_fields:
        return []
    
    indirect_ref = parsed_fields.get('indirect_reference')
    if not indirect_ref:
        return []
    
    # Normalize to list
    if isinstance(indirect_ref, str):
        indirect_refs = [indirect_ref]
    elif isinstance(indirect_ref, list):
        indirect_refs = indirect_ref
    else:
        return []
    
    # Resolve each reference to absolute path
    abs_refs = []
    current_dir = str(Path(current_file_abs_path).parent)
    
    for ref in indirect_refs:
        # Resolve relative path
        ref_path = Path(ref)
        if ref_path.is_absolute():
            abs_ref = str(ref_path.resolve())
        else:
            abs_ref = str((Path(current_dir) / ref_path).resolve())
        abs_refs.append(abs_ref)
    
    return abs_refs


def stable_sort_parsed_items(items: List[Dict]) -> List[Dict]:
    """
    稳定排序ParsedItems (Plan.txt Section 2, Layer 2)
    
    排序键:
    1. File Order: source_file插入顺序（保持原DFS顺序）
    2. Line Order: line_number升序（None视为+∞，最后）
    3. Extraction Order: 保持Atom A返回顺序
    
    实现:
    - Python的sort是stable的，保留相等元素的原始顺序
    - 只按line_number排序，其他顺序自然保持
    """
    def sort_key(item):
        line_num = item.get('line_number')
        # None treated as infinity (sort to end)
        if line_num is None:
            return float('inf')
        return line_num
    
    # Group by source_file to maintain file order
    file_order = []
    seen_files = set()
    for item in items:
        source_file = item.get('source_file', '')
        if source_file not in seen_files:
            file_order.append(source_file)
            seen_files.add(source_file)
    
    # Sort items within each file by line_number
    sorted_items = []
    for source_file in file_order:
        file_items = [item for item in items if item.get('source_file') == source_file]
        file_items.sort(key=sort_key)
        sorted_items.extend(file_items)
    
    return sorted_items
