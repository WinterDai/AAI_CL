#!/usr/bin/env python3
"""
DATA_INTERFACE Unified Manager
==============================
统一管理所有DATA_INTERFACE.yaml相关操作的单一脚本

功能子命令:
  run          - 完整流程 (默认): 占位 → 合并 → 解析 (run.ps1调用)
  placeholder  - 生成354个checker占位符
  merge        - 合并模块items到template
  resolve      - 解析template到绝对路径
  sync         - 多用户更新同步
  convert      - 转换绝对路径到template
  backup       - 列出所有备份
  restore      - 从备份恢复

Usage:
    # 默认完整流程 (run.ps1自动调用)
    python data_interface.py run <checklist_root>
    
    # 生成占位符 (开发初期)
    python data_interface.py placeholder <checklist_root>
    
    # 仅合并items (开发中)
    python data_interface.py merge <checklist_root>
    
    # 仅解析路径 (修改template后)
    python data_interface.py resolve <checklist_root>
    
    # 多用户同步 (团队协作)
    python data_interface.py sync <local_root> <reference_root> [--dry-run] [--force]
    
    # 转换到template格式 (发布时)
    python data_interface.py convert <checklist_root>
    
    # 备份管理
    python data_interface.py backup <checklist_root>
    python data_interface.py restore <checklist_root> [backup_file]

Examples:
    # run.ps1中调用
    python data_interface.py run .
    
    # 开发者A同步开发者B的更新
    python data_interface.py sync . C:\\Users\\devB\\CHECKLIST
    
    # 预览同步内容
    python data_interface.py sync . ../other_branch --dry-run

Author: AI Assistant
Date: 2025-11-27
Version: 1.2

Change Log:
  v1.2 (2025-11-27):
    - Enhanced cross-platform compatibility for Linux/Windows
    - Auto-detect CHECKLIST root directory in merge (智能识别路径中的CHECKLIST目录)
    - Auto-detect OS environment in resolve based on path separator (根据路径分隔符自动判断环境)
    - Windows: Uses backslash (\) when checklist_root contains backslash
    - Linux: Uses forward slash (/) when checklist_root contains forward slash
  
  v1.1 (2025-11-26):
    - Fixed is_placeholder() to correctly detect 'TODO:' prefix (was '[TODO]')
    - Added empty description/input_files checks for placeholder detection
    - This fix prevents placeholders from overwriting real configurations during merge
"""

import sys
import os
import yaml
import re
import shutil
from pathlib import Path
from datetime import datetime
from collections import OrderedDict
from typing import Dict, List, Tuple, Set, Any, Optional


# ============================================================================
# YAML 工具函数
# ============================================================================

def represent_ordereddict(dumper, data):
    """YAML保持字典顺序"""
    return dumper.represent_dict(data.items())

yaml.add_representer(OrderedDict, represent_ordereddict)


def load_yaml_ordered(file_path: Path) -> OrderedDict:
    """加载YAML并保持顺序"""
    class OrderedLoader(yaml.SafeLoader):
        pass
    
    def construct_mapping(loader, node):
        loader.flatten_mapping(node)
        return OrderedDict(loader.construct_pairs(node))
    
    OrderedLoader.add_constructor(
        yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
        construct_mapping
    )
    
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.load(f, OrderedLoader)


def dump_yaml_ordered(data: Any, file_path: Path):
    """保存YAML并保持顺序"""
    with open(file_path, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)


# ============================================================================
# 备份管理
# ============================================================================

def create_backup(template_file: Path, backup_dir: Path) -> Tuple[Optional[Path], Optional[Path]]:
    """创建带时间戳和最新版本的备份"""
    if not template_file.exists():
        return None, None
    
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    # 时间戳备份
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    timestamped_backup = backup_dir / f"DATA_INTERFACE.template.yaml.backup_{timestamp}"
    shutil.copy2(template_file, timestamped_backup)
    
    # 最新备份
    latest_backup = backup_dir / "DATA_INTERFACE.template.backup.yaml"
    shutil.copy2(template_file, latest_backup)
    
    return timestamped_backup, latest_backup


def list_backups(backup_dir: Path) -> List[Dict]:
    """列出所有备份文件"""
    if not backup_dir.exists():
        return []
    
    backups = []
    for file in backup_dir.glob("DATA_INTERFACE.template*.backup*"):
        stat = file.stat()
        backups.append({
            'name': file.name,
            'path': file,
            'mtime': datetime.fromtimestamp(stat.st_mtime),
            'size': stat.st_size
        })
    
    backups.sort(key=lambda x: x['mtime'], reverse=True)
    return backups


# ============================================================================
# 路径转换工具
# ============================================================================

def convert_to_template_format(data: Any, checklist_root: Path) -> Any:
    """将绝对路径转换为${CHECKLIST_ROOT}格式
    
    自动识别路径中的CHECKLIST根目录并替换:
    - Windows: C:\\Users\\xxx\\CHECKLIST → ${CHECKLIST_ROOT}
    - Linux:   /projects/xxx/CHECKLIST → ${CHECKLIST_ROOT}
    """
    if isinstance(data, dict):
        return {k: convert_to_template_format(v, checklist_root) for k, v in data.items()}
    elif isinstance(data, list):
        return [convert_to_template_format(item, checklist_root) for item in data]
    elif isinstance(data, str):
        # 统一转换为正斜杠格式进行匹配和替换
        normalized_data = data.replace('\\', '/')
        
        # 自动识别路径中的CHECKLIST目录
        # 查找 IP_project_folder 前面的路径 (包含CHECKLIST)
        if 'IP_project_folder' in normalized_data or 'Check_modules' in normalized_data or 'Data_interface' in normalized_data:
            # 匹配模式: .../CHECKLIST/...
            import re
            # 提取 CHECKLIST 之前的路径 (贪婪匹配到最后一个CHECKLIST)
            match = re.search(r'(.*/CHECKLIST)/', normalized_data)
            if match:
                checklist_path = match.group(1)
                # 替换为模板变量
                result = normalized_data.replace(checklist_path, '${CHECKLIST_ROOT}')
                return result
        
        return data
    else:
        return data


def resolve_template_placeholders(data: Any, checklist_root: str) -> Any:
    """将${CHECKLIST_ROOT}替换为绝对路径，并根据当前环境自动判断路径分隔符
    
    智能识别:
    - 如果 checklist_root 包含 \\ → Windows环境,使用反斜杠
    - 如果 checklist_root 包含 / → Linux环境,使用正斜杠
    """
    if isinstance(data, dict):
        return {k: resolve_template_placeholders(v, checklist_root) for k, v in data.items()}
    elif isinstance(data, list):
        return [resolve_template_placeholders(item, checklist_root) for item in data]
    elif isinstance(data, str) and '${CHECKLIST_ROOT}' in data:
        # 替换变量
        resolved = data.replace('${CHECKLIST_ROOT}', checklist_root)
        
        # 根据 checklist_root 的路径分隔符判断操作系统
        # Windows: 包含反斜杠 \\
        # Linux:   只包含正斜杠 /
        if '\\' in checklist_root:
            # Windows环境: 统一转换为反斜杠
            resolved = resolved.replace('/', '\\')
        else:
            # Linux环境: 统一转换为正斜杠
            resolved = resolved.replace('\\', '/')
        
        return resolved
    else:
        return data


def batch_replace_paths_regex(data: Any) -> Tuple[Any, int]:
    """
    使用正则批量替换路径为${CHECKLIST_ROOT}
    支持各种路径格式自动识别
    """
    count = 0
    
    def replace_in_string(text: str) -> str:
        nonlocal count
        result = text
        
        # 先检测是否已经包含占位符,避免重复替换
        if '${CHECKLIST_ROOT}' in result:
            return result
        
        # Linux/Unix 绝对路径: /path/to/CHECKLIST/
        pattern_linux = r'/(?:[^/]+/)*CHECKLIST/'
        matches_linux = re.findall(pattern_linux, result)
        if matches_linux:
            count += len(matches_linux)
            result = re.sub(pattern_linux, '${CHECKLIST_ROOT}/', result)
            return result
        
        # Windows路径（正斜杠）: C:/.../CHECKLIST/
        pattern_win_forward = r'[A-Za-z]:/(?:[^/]+/)*CHECKLIST/'
        matches_win = re.findall(pattern_win_forward, result)
        if matches_win:
            count += len(matches_win)
            result = re.sub(pattern_win_forward, '${CHECKLIST_ROOT}/', result)
            return result
        
        # Windows路径（反斜杠）: C:\...\CHECKLIST\...
        pattern_win_back = r'[A-Za-z]:\\(?:[^\\]+\\)*CHECKLIST\\'
        matches_back = re.findall(pattern_win_back, result)
        if matches_back:
            count += len(matches_back)
            result = re.sub(pattern_win_back, '${CHECKLIST_ROOT}/', result)
            # 统一转换为正斜杠
            result = result.replace('\\', '/')
            return result
        
        return result
    
    def process_data(obj):
        if isinstance(obj, dict):
            return {k: process_data(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [process_data(item) for item in obj]
        elif isinstance(obj, str):
            return replace_in_string(obj)
        else:
            return obj
    
    processed_data = process_data(data)
    return processed_data, count


# ============================================================================
# 子命令 1: 生成占位符 (placeholder)
# ============================================================================

def load_module_checkers_from_checklist_index(checklist_root: Path) -> Dict[str, Dict[str, str]]:
    """从CheckList_Index.yaml加载所有checker定义
    
    Returns:
        Dict[module_name, Dict[checker_id, description]]
    """
    checklist_index_file = checklist_root / "Project_config" / "prep_config" / "Initial" / "latest" / "CheckList_Index.yaml"
    
    if not checklist_index_file.exists():
        print(f"[ERROR] CheckList_Index.yaml not found: {checklist_index_file}")
        return {}
    
    try:
        # 先读取原始文本以提取#注释中的描述
        descriptions_map = {}
        with open(checklist_index_file, 'r', encoding='utf-8') as f:
            for line in f:
                # 查找格式：- [PREFIX-]IMP-X-Y-Z-NN: #Description
                # 支持: IMP-5-0-0-00, HPP-IMP-8-2-0-00, SRG-IMP-8-3-0-00, MIG-IMP-8-1-0-00 等
                if re.match(r'\s*-\s+[A-Z]+-[A-Z]+-\d+-\d+-\d+-\d+:', line) or re.match(r'\s*-\s+IMP-\d+-\d+-\d+-\d+:', line):
                    parts = line.split(':', 1)
                    if len(parts) == 2:
                        checker_id = parts[0].strip().lstrip('-').strip()
                        # 提取#后面的描述
                        desc_part = parts[1].strip()
                        if desc_part.startswith('#'):
                            description = desc_part[1:].strip()
                            descriptions_map[checker_id] = description
        
        # 然后用yaml.safe_load解析结构
        with open(checklist_index_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        module_checkers = {}
        total_items = 0
        
        for section_name, section_content in data.items():
            if not isinstance(section_content, dict):
                continue
            
            checklist_items = section_content.get('checklist_item', [])
            if not checklist_items:
                continue
            
            checker_info = {}  # {checker_id: description}
            for item in checklist_items:
                if isinstance(item, str):
                    # 字符串格式（已废弃，但兼容）
                    checker_id = item.split(':')[0].strip()
                    description = descriptions_map.get(checker_id, '')
                    if checker_id and checker_id not in checker_info:
                        checker_info[checker_id] = description
                elif isinstance(item, dict):
                    # 字典格式: {checker_id: value}
                    for checker_id in item.keys():
                        if checker_id not in checker_info:
                            # 从原始文本提取的描述
                            description = descriptions_map.get(checker_id, '')
                            checker_info[checker_id] = description
            
            if checker_info:
                module_checkers[section_name] = checker_info
                total_items += len(checker_info)
        
        print(f"[INFO] Loaded {len(module_checkers)} module(s), {total_items} checker(s)")
        return module_checkers
        
    except Exception as e:
        print(f"[ERROR] Failed to load CheckList_Index.yaml: {e}")
        return {}


def create_placeholder_item(description: str = '') -> Dict:
    """创建占位符item结构
    
    Args:
        description: Checker的描述信息（从CheckList_Index.yaml获取）
    """
    # 构建description字段：如果有原始描述，加上TODO前缀
    if description:
        desc_text = f"TODO: {description}"
    else:
        desc_text = "TODO: Checker not yet implemented - awaiting development"
    
    return {
        'description': desc_text,
        'requirements': {
            'value': 'N/A',
            'pattern_items': []
        },
        'input_files': [],
        'waivers': {
            'value': 'N/A',
            'waive_items': []
        },
        '_status': 'placeholder',
        '_note': 'This is a placeholder. Replace with actual checker configuration when implemented.'
    }


def load_existing_items(checklist_root: Path) -> Dict[str, Dict]:
    """加载所有已实现的items（从文件名提取checker_id）"""
    existing_items = {}
    check_modules_dir = checklist_root / "Check_modules"
    
    for module_dir in check_modules_dir.iterdir():
        if not module_dir.is_dir() or module_dir.name == "common":
            continue
        
        items_dir = module_dir / "inputs" / "items"
        if not items_dir.exists():
            continue
        
        module_name = module_dir.name
        if module_name not in existing_items:
            existing_items[module_name] = {}
        
        for item_file in items_dir.glob("*.yaml"):
            try:
                # 从文件名提取 checker_id（去掉 .yaml 扩展名）
                checker_id = item_file.stem
                
                with open(item_file, 'r', encoding='utf-8') as f:
                    item_data = yaml.safe_load(f)
                    if item_data and isinstance(item_data, dict):
                        # 使用文件名作为 key，文件内容作为 value
                        existing_items[module_name][checker_id] = item_data
            except Exception as e:
                print(f"[WARN] Failed to load {item_file}: {e}")
    
    return existing_items


def cmd_placeholder(checklist_root: Path) -> bool:
    """生成完整的带占位符的template（纯占位符，不合并已实现的items）"""
    print("="*80)
    print("Command: Generate Placeholder Template")
    print("="*80)
    print(f"CHECKLIST Root: {checklist_root}")
    print()
    
    output_file = checklist_root / "Data_interface" / "outputs" / "DATA_INTERFACE.template.yaml"
    backup_dir = checklist_root / "Data_interface" / "scripts"
    
    # 加载checker定义
    print("[STEP 1] Loading module checkers from CheckList_Index.yaml...")
    module_checkers = load_module_checkers_from_checklist_index(checklist_root)
    if not module_checkers:
        print("[ERROR] No checker definitions found")
        return False
    print()
    
    # 构建完整sections（全部使用占位符）
    print("[STEP 2] Building complete template with placeholders...")
    sections = {}
    total_checkers = 0
    
    for module_name, checker_info in module_checkers.items():
        if not checker_info:
            continue
        
        sections[module_name] = {}
        
        for checker_id, description in checker_info.items():
            total_checkers += 1
            sections[module_name][checker_id] = create_placeholder_item(description)
    
    print(f"  Total: {total_checkers} checkers (all placeholders)")
    print()
    
    # 创建metadata
    metadata = {
        'schema_version': '5.3-complete-with-placeholders',
        'total_sections': len(sections),
        'total_items': total_checkers,
        'implemented_items': 0,
        'placeholder_items': total_checkers,
        'generated': datetime.now().isoformat(),
        'description': 'Complete template with ${CHECKLIST_ROOT} placeholders and unimplemented checker placeholders',
        'structure': 'sections → items → {description, requirements, input_files, waivers}',
        'design_philosophy': [
            'Extreme simplicity - only essential fields',
            'Input files: relative paths with ${CHECKLIST_ROOT} prefix',
            'Waivers value: N/A (no waiver) | path (waiver file provided)',
            'Placeholders for unimplemented checkers',
            'Multi-user development friendly',
            'High readability, maintainability, and extensibility'
        ],
        'usage_notes': [
            'Placeholders marked with _status: placeholder',
            'When implementing a checker, replace placeholder with actual configuration',
            'Use sync command to merge updates from multiple developers',
            'Template uses ${CHECKLIST_ROOT} for cross-platform compatibility'
        ]
    }
    
    template_data = {
        'metadata': metadata,
        'sections': sections
    }
    
    # 备份并写入
    print("[STEP 3] Writing template file...")
    if output_file.exists():
        create_backup(output_file, backup_dir)
        print(f"  Backup created")
    
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        yaml.dump(template_data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
    
    print(f"[SUCCESS] Template generated: {output_file.name}")
    print()
    print(f"Summary: {total_checkers} checkers (all placeholders, use 'merge' command to add implemented items)")
    return True


# ============================================================================
# 子命令 2: 合并items (merge)
# ============================================================================

def cmd_merge(checklist_root: Path) -> bool:
    """合并模块items到template（保留已有配置，只合并非占位符items）"""
    print("="*80)
    print("Command: Merge Module Items to Template")
    print("="*80)
    print(f"CHECKLIST Root: {checklist_root}")
    print()
    
    check_modules_dir = checklist_root / "Check_modules"
    template_file = checklist_root / "Data_interface" / "outputs" / "DATA_INTERFACE.template.yaml"
    backup_dir = checklist_root / "Data_interface" / "scripts"
    
    if not check_modules_dir.exists():
        print(f"[ERROR] Check_modules not found: {check_modules_dir}")
        return False
    
    if not template_file.exists():
        print(f"[ERROR] Template not found: {template_file}")
        print("[INFO] Run 'placeholder' command first to create template")
        return False
    
    # 加载template
    print("[STEP 1] Loading existing template...")
    template_data = load_yaml_ordered(template_file)
    current_sections = len(template_data.get('sections', {}))
    current_items = sum(len(s) for s in template_data.get('sections', {}).values())
    print(f"  Current: {current_sections} sections, {current_items} items")
    print()
    
    # 加载CheckList_Index.yaml获取完整的checker定义
    print("[STEP 2] Loading complete checker definitions from CheckList_Index.yaml...")
    all_checkers = load_module_checkers_from_checklist_index(checklist_root)
    total_defined = sum(len(ids) for ids in all_checkers.values())
    print(f"  Defined: {len(all_checkers)} modules, {total_defined} checkers")
    print()
    
    # 遍历所有定义的模块（从CheckList_Index）
    print(f"[STEP 3] Processing {len(all_checkers)} module(s) from CheckList_Index...")
    print()
    
    merged_count = 0
    
    for module_name, checker_ids in all_checkers.items():
        if not checker_ids:
            continue
        
        # 尝试加载items目录中的配置
        module_dir = check_modules_dir / module_name
        items_dir = module_dir / "inputs" / "items"
        
        module_items = {}
        if items_dir.exists():
            for item_file in sorted(items_dir.glob("*.yaml")):
                try:
                    # 从文件名提取 checker_id（去掉 .yaml 扩展名）
                    checker_id_from_file = item_file.stem
                    
                    with open(item_file, 'r', encoding='utf-8') as f:
                        item_data = yaml.safe_load(f)
                        if item_data and isinstance(item_data, dict):
                            # 使用文件名作为 key，文件内容作为 value
                            module_items[checker_id_from_file] = item_data
                except Exception as e:
                    print(f"  [WARN] Failed to load {item_file.name}: {e}")
        
        # 确保template中有这个section
        if 'sections' not in template_data:
            template_data['sections'] = {}
        
        if module_name not in template_data['sections']:
            template_data['sections'][module_name] = {}
            print(f"  [NEW] {module_name}")
        
        new_count = 0
        updated_count = 0
        skipped_count = 0
        placeholder_added = 0
        
        # 遍历CheckList_Index中定义的所有checker IDs
        for checker_id in checker_ids:
            # 检查items中是否有这个checker的配置
            if checker_id in module_items:
                item_config = module_items[checker_id]
                # 检查是否为占位符
                if is_placeholder(item_config):
                    # 占位符：保留template中原有的配置（如果存在）
                    if checker_id not in template_data['sections'][module_name]:
                        # template中也没有，才添加占位符
                        template_data['sections'][module_name][checker_id] = item_config
                        placeholder_added += 1
                    else:
                        # template中已有配置，跳过（保留原有）
                        skipped_count += 1
                else:
                    # 非占位符：转换路径为模板格式后合并
                    item_config_with_template = convert_to_template_format(item_config, checklist_root)
                    
                    if checker_id in template_data['sections'][module_name]:
                        updated_count += 1
                    else:
                        new_count += 1
                    template_data['sections'][module_name][checker_id] = item_config_with_template
            else:
                # items中没有这个checker：检查template中是否已有
                if checker_id not in template_data['sections'][module_name]:
                    # template中也没有：添加占位符
                    template_data['sections'][module_name][checker_id] = create_placeholder_item()
                    placeholder_added += 1
                # 否则：template中已有，保留不动
        
        if new_count > 0 or updated_count > 0 or skipped_count > 0 or placeholder_added > 0:
            status_parts = []
            if new_count > 0:
                status_parts.append(f"+{new_count} new")
            if updated_count > 0:
                status_parts.append(f"*{updated_count} updated")
            if placeholder_added > 0:
                status_parts.append(f"□{placeholder_added} placeholder")
            if skipped_count > 0:
                status_parts.append(f"-{skipped_count} skipped")
            print(f"  [MERGE] {module_name}: {', '.join(status_parts)}")
            merged_count += 1
    
    print()
    
    # 更新metadata
    print("[STEP 4] Updating metadata...")
    if 'metadata' not in template_data:
        template_data['metadata'] = {}
    
    metadata = template_data['metadata']
    sections = template_data.get('sections', {})
    
    metadata['total_sections'] = len(sections)
    metadata['total_items'] = sum(len(items) for items in sections.values())
    metadata['generated'] = datetime.now().isoformat()
    
    # 统计占位符和实际配置
    placeholder_count = sum(1 for sec in sections.values() 
                           for item in sec.values() 
                           if isinstance(item, dict) and item.get('_status') == 'placeholder')
    implemented_count = metadata['total_items'] - placeholder_count
    
    metadata['implemented_items'] = implemented_count
    metadata['placeholder_items'] = placeholder_count
    
    print(f"  Total: {metadata['total_items']} items")
    print(f"  Implemented: {implemented_count} ({100*implemented_count//metadata['total_items']}%)")
    print(f"  Placeholders: {placeholder_count} ({100*placeholder_count//metadata['total_items']}%)")
    print()
    
    # 备份并保存
    print("[STEP 5] Saving template...")
    create_backup(template_file, backup_dir)
    dump_yaml_ordered(template_data, template_file)
    
    print(f"[SUCCESS] Template updated: {template_file.name}")
    print(f"  Processed {merged_count} module(s)")
    print(f"  Final: {metadata['total_items']} items (should be 354 from CheckList_Index)")
    return True


# ============================================================================
# 子命令 3: 解析路径 (resolve)
# ============================================================================

def cmd_resolve(checklist_root: Path) -> bool:
    """解析template到绝对路径"""
    print("="*80)
    print("Command: Resolve Template to Absolute Paths")
    print("="*80)
    print(f"CHECKLIST Root: {checklist_root}")
    print()
    
    template_file = checklist_root / "Data_interface" / "outputs" / "DATA_INTERFACE.template.yaml"
    output_file = checklist_root / "Data_interface" / "outputs" / "DATA_INTERFACE.yaml"
    
    if not template_file.exists():
        print(f"[ERROR] Template not found: {template_file}")
        return False
    
    try:
        # 读取template
        print("[STEP 1] Loading template...")
        with open(template_file, 'r', encoding='utf-8') as f:
            template_data = yaml.safe_load(f)
        
        sections_count = len(template_data.get('sections', {}))
        items_count = sum(len(items) for items in template_data.get('sections', {}).values())
        print(f"  Loaded: {sections_count} sections, {items_count} items")
        print()
        
        # 解析路径
        print("[STEP 2] Resolving ${CHECKLIST_ROOT} to absolute paths...")
        # 使用原生路径格式（Windows用反斜杠，Linux用正斜杠）
        checklist_root_str = str(checklist_root)
        print(f"  Target: {checklist_root_str}")
        
        resolved_data = resolve_template_placeholders(template_data, checklist_root_str)
        print()
        
        # 写入输出
        print("[STEP 3] Writing DATA_INTERFACE.yaml...")
        with open(output_file, 'w', encoding='utf-8') as f:
            yaml.dump(resolved_data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
        
        print(f"[SUCCESS] Generated: {output_file}")
        return True
        
    except Exception as e:
        print(f"[ERROR] Failed to resolve: {e}")
        return False


# ============================================================================
# 子命令 4: 多用户同步 (sync)
# ============================================================================

def is_placeholder(item_data: Dict) -> bool:
    """判断是否为占位符
    
    检查条件：
    1. _status字段为'placeholder'
    2. description以'TODO:'开头（占位符标记）
    3. description为空或input_files为空列表（未配置）
    """
    if not isinstance(item_data, dict):
        return True
    
    # 检查_status字段
    if item_data.get('_status') == 'placeholder':
        return True
    
    # 检查description是否以TODO:开头（占位符标记）
    description = item_data.get('description', '')
    if description.startswith('TODO:'):
        return True
    
    # 检查是否为空配置（未实现）
    if not description or not item_data.get('input_files'):
        return True
    
    return False


def is_same_item(item1: Dict, item2: Dict) -> bool:
    """判断两个item是否相同"""
    if not isinstance(item1, dict) or not isinstance(item2, dict):
        return False
    
    key_fields = ['description', 'requirements', 'input_files', 'waivers']
    
    for key in key_fields:
        if item1.get(key) != item2.get(key):
            return False
    
    return True


def cmd_sync(local_root: Path, reference_root: Path, dry_run: bool = False, force: bool = False) -> bool:
    """同步多用户更新"""
    print("="*80)
    print("Command: Sync Multi-User Updates")
    print("="*80)
    print(f"Local:     {local_root}")
    print(f"Reference: {reference_root}")
    print(f"Mode:      {'DRY-RUN' if dry_run else 'FORCE' if force else 'NORMAL'}")
    print()
    
    local_template = local_root / "Data_interface" / "outputs" / "DATA_INTERFACE.template.yaml"
    reference_template = reference_root / "Data_interface" / "outputs" / "DATA_INTERFACE.template.yaml"
    backup_dir = local_root / "Data_interface" / "scripts"
    
    # 加载templates
    try:
        print("[STEP 1] Loading templates...")
        with open(local_template, 'r', encoding='utf-8') as f:
            local_data = yaml.safe_load(f)
        print(f"  Local: {local_template.name}")
        
        with open(reference_template, 'r', encoding='utf-8') as f:
            reference_data = yaml.safe_load(f)
        print(f"  Reference: {reference_template.name}")
        print()
    except FileNotFoundError as e:
        print(f"[ERROR] Template not found: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] Failed to load templates: {e}")
        return False
    
    # 比较templates
    print("[STEP 2] Comparing templates...")
    
    local_sections = local_data.get('sections', {})
    reference_sections = reference_data.get('sections', {})
    
    added_items = []
    updated_items = []
    conflicts = []
    
    for section_name, reference_items in reference_sections.items():
        if section_name not in local_sections:
            local_sections[section_name] = {}
        
        local_items = local_sections[section_name]
        
        for item_id, ref_item in reference_items.items():
            # 跳过reference中的占位符
            if is_placeholder(ref_item):
                continue
            
            if item_id not in local_items:
                # 新增项
                added_items.append((section_name, item_id, ref_item))
            elif is_placeholder(local_items[item_id]):
                # 本地是占位符，reference是实现 → 更新
                updated_items.append((section_name, item_id, ref_item))
            elif not is_same_item(local_items[item_id], ref_item):
                # 都是实现但内容不同 → 冲突
                conflicts.append((section_name, item_id, local_items[item_id], ref_item))
    
    print(f"  Added:    {len(added_items)} item(s)")
    print(f"  Updated:  {len(updated_items)} item(s)")
    print(f"  Conflicts: {len(conflicts)} item(s)")
    print()
    
    # 显示详情
    if added_items:
        print("[ADDED ITEMS]")
        for section, item_id, _ in added_items[:5]:
            print(f"  + {section}/{item_id}")
        if len(added_items) > 5:
            print(f"  ... and {len(added_items) - 5} more")
        print()
    
    if updated_items:
        print("[UPDATED ITEMS]")
        for section, item_id, _ in updated_items[:5]:
            print(f"  * {section}/{item_id}")
        if len(updated_items) > 5:
            print(f"  ... and {len(updated_items) - 5} more")
        print()
    
    if conflicts:
        print("[CONFLICTS]")
        for section, item_id, _, _ in conflicts[:5]:
            print(f"  ! {section}/{item_id}")
        if len(conflicts) > 5:
            print(f"  ... and {len(conflicts) - 5} more")
        print()
        
        if not force:
            print("[ERROR] Conflicts detected. Use --force to overwrite with reference version")
            return False
        else:
            print("[WARN] Force mode: Conflicts will be overwritten with reference version")
            print()
    
    if not added_items and not updated_items and not conflicts:
        print("[INFO] No updates to merge")
        return True
    
    if dry_run:
        print("[DRY-RUN] Changes preview only, not applied")
        return True
    
    # 应用合并
    print("[STEP 3] Applying merge...")
    
    for section, item_id, ref_item in added_items + updated_items:
        local_sections[section][item_id] = ref_item
    
    if force:
        for section, item_id, _, ref_item in conflicts:
            local_sections[section][item_id] = ref_item
    
    # 更新metadata
    if 'metadata' in local_data:
        local_data['metadata']['total_items'] = sum(len(items) for items in local_sections.values())
        local_data['metadata']['generated'] = datetime.now().isoformat()
    
    # 备份并保存
    print("[STEP 4] Saving merged template...")
    create_backup(local_template, backup_dir)
    
    with open(local_template, 'w', encoding='utf-8') as f:
        yaml.dump(local_data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
    
    print(f"[SUCCESS] Merged {len(added_items) + len(updated_items)} update(s)")
    if force:
        print(f"  Overwrote {len(conflicts)} conflict(s)")
    
    return True


# ============================================================================
# 子命令 5: 转换到template (convert)
# ============================================================================

def cmd_convert(checklist_root: Path) -> bool:
    """转换绝对路径到template格式"""
    print("="*80)
    print("Command: Convert to Template Format")
    print("="*80)
    print(f"CHECKLIST Root: {checklist_root}")
    print()
    
    input_file = checklist_root / "Data_interface" / "outputs" / "DATA_INTERFACE.yaml"
    output_file = checklist_root / "Data_interface" / "outputs" / "DATA_INTERFACE.template.yaml"
    backup_dir = checklist_root / "Data_interface" / "scripts"
    
    if not input_file.exists():
        print(f"[ERROR] DATA_INTERFACE.yaml not found: {input_file}")
        return False
    
    try:
        # 读取YAML
        print("[STEP 1] Loading DATA_INTERFACE.yaml...")
        with open(input_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        print()
        
        # 转换路径
        print("[STEP 2] Converting paths to ${CHECKLIST_ROOT}...")
        converted_data, count = batch_replace_paths_regex(data)
        print(f"  Replaced {count} path occurrence(s)")
        print()
        
        # 更新metadata
        if 'metadata' in converted_data:
            converted_data['metadata']['description'] = 'Template version with ${CHECKLIST_ROOT} placeholders'
            if 'design_philosophy' in converted_data['metadata']:
                philosophy = converted_data['metadata']['design_philosophy']
                if isinstance(philosophy, list):
                    for i, item in enumerate(philosophy):
                        if 'Input files' in str(item):
                            philosophy[i] = 'Input files: relative paths with ${CHECKLIST_ROOT} prefix'
        
        # 备份并保存
        print("[STEP 3] Saving template...")
        if output_file.exists():
            create_backup(output_file, backup_dir)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            yaml.dump(converted_data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
        
        print(f"[SUCCESS] Template generated: {output_file.name}")
        print(f"  Converted {count} path(s) to template format")
        return True
        
    except Exception as e:
        print(f"[ERROR] Failed to convert: {e}")
        return False


# ============================================================================
# 子命令 6: 列出备份 (backup)
# ============================================================================

def cmd_backup(checklist_root: Path) -> bool:
    """列出所有备份"""
    print("="*80)
    print("Command: List Template Backups")
    print("="*80)
    
    backup_dir = checklist_root / "Data_interface" / "scripts"
    print(f"Backup Directory: {backup_dir}")
    print()
    
    if not backup_dir.exists():
        print("[INFO] No backup directory found")
        return True
    
    backups = list_backups(backup_dir)
    
    if not backups:
        print("[INFO] No backup files found")
    else:
        print(f"[INFO] Found {len(backups)} backup file(s):")
        print()
        for i, backup in enumerate(backups, 1):
            print(f"  {i}. {backup['name']}")
            print(f"     Modified: {backup['mtime']}")
            print(f"     Size: {backup['size']:,} bytes")
            print()
    
    return True


# ============================================================================
# 子命令 7: 恢复备份 (restore)
# ============================================================================

def cmd_restore(checklist_root: Path, backup_file: Optional[str] = None) -> bool:
    """从备份恢复template"""
    print("="*80)
    print("Command: Restore Template from Backup")
    print("="*80)
    
    backup_dir = checklist_root / "Data_interface" / "scripts"
    template_file = checklist_root / "Data_interface" / "outputs" / "DATA_INTERFACE.template.yaml"
    
    if not backup_dir.exists():
        print(f"[ERROR] Backup directory not found: {backup_dir}")
        return False
    
    # 确定使用哪个备份
    if backup_file:
        backup_path = backup_dir / backup_file
        if not backup_path.exists():
            print(f"[ERROR] Backup file not found: {backup_file}")
            return False
        print(f"[INFO] Using specified backup: {backup_file}")
    else:
        # 使用最新备份
        latest = backup_dir / "DATA_INTERFACE.template.backup.yaml"
        if latest.exists():
            backup_path = latest
            print(f"[INFO] Using latest backup: {latest.name}")
        else:
            backups = list_backups(backup_dir)
            if not backups:
                print("[ERROR] No backup files found")
                return False
            backup_path = backups[0]['path']
            print(f"[INFO] Using newest backup: {backup_path.name}")
    
    print()
    
    # 备份当前template
    if template_file.exists():
        safety_backup = template_file.parent / f"DATA_INTERFACE.template.yaml.before_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.copy2(template_file, safety_backup)
        print(f"[INFO] Current template backed up: {safety_backup.name}")
    
    # 恢复
    try:
        shutil.copy2(backup_path, template_file)
        print(f"[SUCCESS] Template restored!")
        print(f"  From: {backup_path.name}")
        print(f"  To: {template_file}")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to restore: {e}")
        return False


# ============================================================================
# 子命令 8: 完整流程 (run)
# ============================================================================

def cmd_run(checklist_root: Path) -> bool:
    """执行完整流程: 占位 → 合并 (Phase 3 resolve已取消.保留${CHECKLIST_ROOT}变量)"""
    print("="*80)
    print("Command: Run Full Workflow")
    print("="*80)
    print(f"CHECKLIST Root: {checklist_root}")
    print()
    
    success = True
    
    # 1. 生成占位符
    print(">>> Phase 1/2: Generate Placeholder Template")
    print()
    if not cmd_placeholder(checklist_root):
        print("[ERROR] Phase 1 failed")
        success = False
    print()
    
    # 2. 合并items
    print(">>> Phase 2/2: Merge Module Items")
    print()
    if not cmd_merge(checklist_root):
        print("[ERROR] Phase 2 failed")
        success = False
    print()
    
    # 3. 解析路径 (已取消 - 保留${CHECKLIST_ROOT}变量直到checker本地展开)
    # print(">>> Phase 3/3: Resolve Template Paths")
    # print()
    # if not cmd_resolve(checklist_root):
    #     print("[ERROR] Phase 3 failed")
    #     success = False
    # print()
    
    print("="*80)
    if success:
        print("[SUCCESS] Full workflow completed successfully!")
    else:
        print("[WARNING] Some phases failed. Check output above.")
    print("="*80)
    
    return success


# ============================================================================
# 主入口
# ============================================================================

def print_usage():
    """打印使用帮助"""
    print(__doc__)


def main():
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)
    
    command = sys.argv[1]
    
    # 帮助命令
    if command in ['-h', '--help', 'help']:
        print_usage()
        sys.exit(0)
    
    # 需要checklist_root的命令
    if command in ['run', 'placeholder', 'merge', 'resolve', 'convert', 'backup', 'restore']:
        if len(sys.argv) < 3:
            print(f"[ERROR] Missing checklist_root argument")
            print(f"Usage: python data_interface.py {command} <checklist_root>")
            sys.exit(1)
        
        checklist_root = Path(sys.argv[2]).resolve()
        
        if not checklist_root.is_dir():
            print(f"[ERROR] CHECKLIST root not found: {checklist_root}")
            sys.exit(1)
        
        # 执行命令
        if command == 'run':
            success = cmd_run(checklist_root)
        elif command == 'placeholder':
            success = cmd_placeholder(checklist_root)
        elif command == 'merge':
            success = cmd_merge(checklist_root)
        elif command == 'resolve':
            success = cmd_resolve(checklist_root)
        elif command == 'convert':
            success = cmd_convert(checklist_root)
        elif command == 'backup':
            success = cmd_backup(checklist_root)
        elif command == 'restore':
            backup_file = sys.argv[3] if len(sys.argv) > 3 else None
            success = cmd_restore(checklist_root, backup_file)
        
        sys.exit(0 if success else 1)
    
    # sync命令需要两个路径
    elif command == 'sync':
        if len(sys.argv) < 4:
            print("[ERROR] Missing arguments for sync command")
            print("Usage: python data_interface.py sync <local_root> <reference_root> [--dry-run] [--force]")
            sys.exit(1)
        
        local_root = Path(sys.argv[2]).resolve()
        reference_root = Path(sys.argv[3]).resolve()
        
        if not local_root.is_dir():
            print(f"[ERROR] Local root not found: {local_root}")
            sys.exit(1)
        
        if not reference_root.is_dir():
            print(f"[ERROR] Reference root not found: {reference_root}")
            sys.exit(1)
        
        dry_run = '--dry-run' in sys.argv
        force = '--force' in sys.argv
        
        success = cmd_sync(local_root, reference_root, dry_run, force)
        sys.exit(0 if success else 1)
    
    else:
        print(f"[ERROR] Unknown command: {command}")
        print()
        print("Available commands:")
        print("  run, placeholder, merge, resolve, sync, convert, backup, restore")
        print()
        print("Use 'python data_interface.py --help' for detailed usage")
        sys.exit(1)


if __name__ == '__main__':
    main()