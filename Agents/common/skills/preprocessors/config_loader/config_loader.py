"""
Config Loader Preprocessor

Preprocessor: 无条件执行，纯数据提取
职责: 解析 YAML 配置，检测 Type (1-4)

版本: 2.0.0 (集成 shared 工具库)
v2.0 变更: 使用 shared/type_rules.py::get_type_by_config() 判定 Type
"""

import os
import yaml
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field

# 导入 shared 工具库 (v2.0 新增)
try:
    from shared import get_type_by_config, CheckerType
    SHARED_AVAILABLE = True
except ImportError:
    # Fallback: shared 包不可用时使用本地实现
    SHARED_AVAILABLE = False
    CheckerType = None


# ============================================================================
# 本地数据类 (与 models.py 保持兼容)
# ============================================================================

@dataclass
class FileInfo:
    """单个文件信息"""
    path: str
    exists: bool
    size: int = 0
    
    def to_dict(self) -> dict:
        return {"path": self.path, "exists": self.exists, "size": self.size}


@dataclass 
class ConfigSummary:
    """配置摘要"""
    item_id: str
    description: str
    input_files: List[FileInfo]
    file_count: int
    aggregation_needed: bool
    requirements: Dict[str, Any]
    pattern_items: List[str]
    waivers: Dict[str, Any]
    detected_type: int
    
    def to_prompt_text(self) -> str:
        """转换为 Prompt 可读的文本格式"""
        files_text = "\n".join(
            f"  - {f.path} ({'exists' if f.exists else 'MISSING'}, {f.size} bytes)"
            for f in self.input_files
        )
        return f"""Item ID: {self.item_id}
Description: {self.description}
Detected Type: {self.detected_type}
File Count: {self.file_count}
Aggregation Needed: {self.aggregation_needed}

Input Files:
{files_text}

Requirements: {self.requirements}
Pattern Items: {self.pattern_items}
Waivers: {self.waivers}"""


# ============================================================================
# 主函数
# ============================================================================


def load_config(config_path: str) -> ConfigSummary:
    """
    加载并解析 checker 配置文件
    
    Preprocessor 职责 (纯数据提取):
    ✓ 解析 YAML 格式
    ✓ 检查文件是否存在
    ✓ 计算 file_count
    ✓ 检测 Type (基于规则，非语义)
    
    Args:
        config_path: item.yaml 文件的绝对路径
        
    Returns:
        ConfigSummary: 结构化配置摘要
        
    Raises:
        FileNotFoundError: 配置文件不存在
    """
    config_path = Path(config_path)
    
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # 提取基本信息
    item_id = config.get('item_id', config_path.stem)
    description = config.get('description', '')
    
    # 解析 input_files
    raw_input_files = config.get('input_files', [])
    config_dir = config_path.parent
    
    # 推断 CHECKLIST_ROOT: config_path 向上找到包含 Check_modules 或 inputs 的目录
    checklist_root = _infer_checklist_root(config_path)
    
    input_files = []
    for file_path in raw_input_files:
        # 1. 展开环境变量 (支持 ${CHECKLIST_ROOT} 等)
        file_path = os.path.expandvars(file_path)
        
        # 2. 如果仍包含 ${CHECKLIST_ROOT}，使用推断的路径替换
        if '${CHECKLIST_ROOT}' in file_path and checklist_root:
            file_path = file_path.replace('${CHECKLIST_ROOT}', str(checklist_root))
        
        # 3. 解析相对路径
        if not os.path.isabs(file_path):
            full_path = (config_dir / file_path).resolve()
        else:
            full_path = Path(file_path)
        
        exists = full_path.exists()
        size = full_path.stat().st_size if exists else 0
        
        input_files.append(FileInfo(
            path=str(full_path),
            exists=exists,
            size=size
        ))
    
    # 提取配置值
    requirements = config.get('requirements', {'value': 'N/A'})
    pattern_items = config.get('pattern_items', [])
    waivers = config.get('waivers', {'value': 'N/A'})
    
    # 自动检测 Type
    # v2.0: 优先使用 shared 包的统一判定逻辑
    if SHARED_AVAILABLE:
        waivers_value = waivers.get('value', 'N/A')
        checker_type_enum = get_type_by_config(pattern_items, waivers_value)
        detected_type = int(checker_type_enum)  # CheckerType enum -> int
    else:
        # Fallback: 使用本地实现
        detected_type = _detect_checker_type(requirements, pattern_items, waivers)
    
    return ConfigSummary(
        item_id=item_id,
        description=description,
        input_files=input_files,
        file_count=len(input_files),
        aggregation_needed=len(input_files) > 1,
        requirements=requirements,
        pattern_items=pattern_items if pattern_items else [],
        waivers=waivers,
        detected_type=detected_type
    )


def _infer_checklist_root(config_path: Path) -> Optional[Path]:
    """
    从 config_path 推断 CHECKLIST_ROOT
    
    目录结构约定:
    - {CHECKLIST_ROOT}/Check_modules/{module}/inputs/items/{item}.yaml
    - {CHECKLIST_ROOT}/IP_project_folder/logs/...
    
    Args:
        config_path: item.yaml 的路径
        
    Returns:
        Optional[Path]: 推断的 CHECKLIST_ROOT，失败返回 None
    """
    try:
        resolved = config_path.resolve()
        # 向上查找包含 Check_modules 或 IP_project_folder 的父目录
        for parent in resolved.parents:
            # 检查是否是 CHECKLIST_ROOT (包含关键子目录)
            if (parent / "Check_modules").exists() or (parent / "IP_project_folder").exists():
                return parent
            # 也检查 inputs 目录的父级
            if parent.name == "inputs" and (parent.parent / "scripts").exists():
                # 这是 module 目录，再向上一级是 Check_modules，再上一级是 CHECKLIST_ROOT
                return parent.parent.parent.parent
        return None
    except Exception:
        return None


def _detect_checker_type(
    requirements: dict, 
    pattern_items: list, 
    waivers: dict
) -> int:
    """
    根据 DEVELOPER_TASK_PROMPTS.md 规则检测 Type
    
    Type 分类规则:
    - Type 1: requirements.value N/A, pattern_items [] (empty), waivers N/A/0
    - Type 2: requirements.value > 0, pattern_items [...] (defined), waivers N/A/0
    - Type 3: requirements.value > 0, pattern_items [...] (defined), waivers > 0
    - Type 4: requirements.value N/A, pattern_items [] (empty), waivers > 0
    
    Args:
        requirements: requirements 配置
        pattern_items: pattern_items 列表
        waivers: waivers 配置
        
    Returns:
        int: Type 编号 (1, 2, 3, 4)
    """
    # 检测是否有 pattern_items
    has_patterns = bool(pattern_items) and len(pattern_items) > 0
    
    # 检测是否有 waivers
    waiver_value = waivers.get('value', 'N/A')
    has_waivers = _check_waiver_value(waiver_value)
    
    # 根据组合确定 Type
    if has_patterns and has_waivers:
        return 3  # Value Check + Waiver
    elif has_patterns:
        return 2  # Value Check
    elif has_waivers:
        return 4  # Boolean Check + Waiver
    else:
        return 1  # Boolean Check


def _check_waiver_value(waiver_value) -> bool:
    """
    检查 waiver value 是否表示有 waiver
    
    Args:
        waiver_value: waivers.value 的值
        
    Returns:
        bool: True 表示有 waiver
    """
    # N/A 或 0 表示没有 waiver
    if waiver_value in ['N/A', 0, '0', 'N/A/0', None]:
        return False
    
    # 数字 > 0 表示有 waiver
    if isinstance(waiver_value, (int, float)) and waiver_value > 0:
        return True
    
    # 字符串数字 > 0 表示有 waiver
    if isinstance(waiver_value, str) and waiver_value.isdigit() and int(waiver_value) > 0:
        return True
    
    return False


# ============================================================================
# 便捷函数
# ============================================================================

def get_type_description(detected_type: int) -> str:
    """获取 Type 的描述"""
    descriptions = {
        1: "Boolean Check (存在性检查)",
        2: "Value Check (值匹配检查)", 
        3: "Value Check + Waiver (值匹配检查 + 豁免)",
        4: "Boolean Check + Waiver (存在性检查 + 豁免)"
    }
    return descriptions.get(detected_type, "Unknown Type")


if __name__ == "__main__":
    # 测试用例
    import sys
    if len(sys.argv) > 1:
        config = load_config(sys.argv[1])
        print(f"Item ID: {config.item_id}")
        print(f"Description: {config.description}")
        print(f"Detected Type: {config.detected_type} - {get_type_description(config.detected_type)}")
        print(f"File Count: {config.file_count}")
        print(f"Aggregation Needed: {config.aggregation_needed}")
