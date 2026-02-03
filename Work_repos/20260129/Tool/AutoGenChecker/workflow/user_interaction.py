"""User interaction module for README hints collection."""

from __future__ import annotations

import sys
import re
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Tuple


def get_hints_txt_path(module: str) -> Path:
    """获取module级别hints文本文件路径。"""
    return Path(f"Work/phase-1-dev/{module}/hints.txt")


def parse_hints_txt(content: str) -> Dict[str, List[Tuple[str, str]]]:
    """
    解析hints.txt内容。
    
    返回: {item_id: [(timestamp, hints), ...]}  按时间顺序，最后一个是最新
    """
    result = {}
    current_item = None
    current_timestamp = None
    current_lines = []
    
    for line in content.split('\n'):
        # 检测item分隔符: === IMP-16-0-0-01 ===
        item_match = re.match(r'^===\s*(\S+)\s*===$', line)
        if item_match:
            # 保存之前的内容
            if current_item and current_timestamp:
                hints = '\n'.join(current_lines).strip()
                if hints:
                    if current_item not in result:
                        result[current_item] = []
                    result[current_item].append((current_timestamp, hints))
            
            current_item = item_match.group(1)
            current_timestamp = None
            current_lines = []
            continue
        
        # 检测时间戳: [2025-12-26 15:00:00]
        ts_match = re.match(r'^\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\]$', line)
        if ts_match:
            # 保存之前的版本
            if current_item and current_timestamp:
                hints = '\n'.join(current_lines).strip()
                if hints:
                    if current_item not in result:
                        result[current_item] = []
                    result[current_item].append((current_timestamp, hints))
            
            current_timestamp = ts_match.group(1)
            current_lines = []
            continue
        
        # 普通内容行
        if current_item and current_timestamp is not None:
            current_lines.append(line)
    
    # 保存最后一个
    if current_item and current_timestamp:
        hints = '\n'.join(current_lines).strip()
        if hints:
            if current_item not in result:
                result[current_item] = []
            result[current_item].append((current_timestamp, hints))
    
    return result


def load_latest_hints(module: str, item_id: str) -> Optional[dict]:
    """
    Load hints from the txt file for a specific item.
    Returns only the latest version by default, with history metadata.
    Filters out template text patterns.
    
    Args:
        module: Module name (e.g., "1.0_LIBRARY_CHECK")
        item_id: Item ID (e.g., "IMP-1-0-0-00")
        
    Returns:
        Dict with structure:
        {
            'latest': str,      # Latest hints (None if template or not found)
            'history': list,    # List of (timestamp, hints) tuples
            'count': int        # Total number of versions
        }
        Returns None if file doesn't exist or no valid hints found
    """
    # Template patterns to filter out
    TEMPLATE_PATTERNS = [
        "请填写hints",
        "检查目的、关键模式、边界情况",
        "请在此填写",
        "示例：",
        "Example:"
    ]
    
    def is_template_text(text: str) -> bool:
        """Check if text matches template patterns."""
        if not text or len(text.strip()) < 10:
            return True
        for pattern in TEMPLATE_PATTERNS:
            if pattern in text:
                return True
        return False
    
    txt_path = get_hints_txt_path(module)
    if not txt_path.exists():
        return None
    
    try:
        content = txt_path.read_text(encoding='utf-8')
        all_hints = parse_hints_txt(content)
        
        if item_id in all_hints and all_hints[item_id]:
            versions = all_hints[item_id]
            
            # Filter out template versions
            valid_versions = [(ts, hints) for ts, hints in versions if not is_template_text(hints)]
            
            if not valid_versions:
                return None
            
            # Return structured data
            return {
                'latest': valid_versions[-1][1],  # Most recent valid hints
                'history': valid_versions,
                'count': len(valid_versions)
            }
    except Exception as e:
        print(f"⚠️  Failed to load hints: {e}")
    
    return None



def save_hints_to_txt(module: str, item_id: str, hints: str) -> bool:
    """
    保存hints到txt文件，追加新版本。
    """
    txt_path = get_hints_txt_path(module)
    txt_path.parent.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # 读取现有内容
    if txt_path.exists():
        content = txt_path.read_text(encoding='utf-8')
        all_hints = parse_hints_txt(content)
    else:
        content = ""
        all_hints = {}
    
    # 检查是否需要添加（内容相同则跳过）
    if item_id in all_hints and all_hints[item_id]:
        latest = all_hints[item_id][-1][1]
        if latest == hints:
            return True  # 内容相同，无需保存
    
    try:
        # 构建新内容：需要在正确位置插入新版本
        new_content_lines = []
        
        if not content:
            # 文件为空，直接创建
            new_content_lines.append(f'=== {item_id} ===\n')
            new_content_lines.append(f'[{timestamp}]\n')
            new_content_lines.append(hints)
            new_content_lines.append('\n')
        elif item_id not in all_hints:
            # 新item，追加到文件末尾
            new_content_lines.append(content)
            if not content.endswith('\n\n'):
                new_content_lines.append('\n')
            new_content_lines.append(f'\n=== {item_id} ===\n')
            new_content_lines.append(f'[{timestamp}]\n')
            new_content_lines.append(hints)
            new_content_lines.append('\n')
        else:
            # 已存在的item，需要在对应section中插入新版本
            lines = content.split('\n')
            current_item = None
            i = 0
            
            while i < len(lines):
                line = lines[i]
                
                # 检测item分隔符
                if line.startswith('=== ') and line.endswith(' ==='):
                    current_item = line[4:-4].strip()
                    new_content_lines.append(line + '\n')
                    i += 1
                    
                    # 如果是目标item，找到section末尾插入新版本
                    if current_item == item_id:
                        # 收集该section的所有内容
                        section_lines = []
                        while i < len(lines):
                            if lines[i].startswith('=== ') and lines[i].endswith(' ==='):
                                # 遇到下一个section，插入新版本后退出
                                break
                            section_lines.append(lines[i])
                            i += 1
                        
                        # 添加原有section内容
                        for sl in section_lines:
                            new_content_lines.append(sl + '\n')
                        
                        # 在section末尾添加新版本（插入到下一个section之前）
                        new_content_lines.append(f'[{timestamp}]\n')
                        new_content_lines.append(hints)
                        new_content_lines.append('\n\n')
                        # 不要增加i，因为已经在while里增加过了
                        continue
                else:
                    new_content_lines.append(line + '\n')
                    i += 1
        
        # 写入新内容
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(''.join(new_content_lines))
        
        return True
    except Exception as e:
        print(f"⚠️  Failed to save hints: {e}")
        return False


def load_item_yaml(item_id: str, module: str) -> dict:
    """Load item YAML configuration."""
    import yaml
    try:
        from utils.paths import discover_project_paths
    except ImportError:
        from AutoGenChecker.utils.paths import discover_project_paths
    
    # Get absolute path to Check_modules directory
    paths = discover_project_paths()
    check_modules_root = paths.check_modules_root
    
    if not check_modules_root:
        return {}
    
    # Try inputs/items first
    yaml_path = check_modules_root / module / "inputs" / "items" / f"{item_id}.yaml"
    if not yaml_path.exists():
        # Try test_inputs
        yaml_path = check_modules_root / module / "test_inputs" / "items" / f"{item_id}.yaml"
    
    if yaml_path.exists():
        with open(yaml_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    
    return {}


def prompt_user_for_hints(item_id: str, module: str) -> Optional[str]:
    """
    Interactive prompt to collect user hints for README generation.
    
    Args:
        item_id: Checker item ID
        module: Module name
        
    Returns:
        User hints string or None if skipped
    """
    # Add visual separation before Step 3
    print("\n" + "─"*80)
    print("[Step 3/9] 📝 Generating README")
    print("─"*80)
    
    # Display item information (integrated into Step 3 header)
    try:
        item_data = load_item_yaml(item_id, module)
        if item_data:
            print(f"Item: {item_id}")
            print(f"Description: {item_data.get('description', 'N/A')}")
            
            input_files = item_data.get('input_files', [])
            if input_files:
                print(f"Input files:")
                for f in input_files:
                    print(f"  - {f}")
        else:
            print(f"Item: {item_id}")
            print(f"⚠️  No item YAML found")
    except Exception as e:
        print(f"Item: {item_id}")
        print(f"⚠️  Failed to load item data: {e}")
    
    # 2. Load latest hints from txt file
    hints_data = load_latest_hints(module, item_id)
    
    # 3. Main interaction loop (allow retry on Ctrl+C during input)
    while True:
        # Display saved hints and present options
        if hints_data:
            latest_hints = hints_data['latest']
            history_count = hints_data['count']
            
            print(f"\n💡 Saved hints (latest version) for {item_id}:")
            print(f"   {'-'*56}")
            for line in latest_hints.split('\n'):
                print(f"   • {line}")
            print(f"   {'-'*56}")
            
            if history_count > 1:
                print(f"\n📚 {history_count} versions available")
            
            print(f"\n📝 Choose action:")
            print(f"   [U]se     - Use saved hints (latest version)")
            if history_count > 1:
                print(f"   [H]istory - View and select from all {history_count} versions")
            print(f"   [N]ew     - Add a new version (multi-line input)")
            print(f"   [S]kip    - Skip hints (AI auto-generation)")
            
            # Get user choice
            default_choice = 'U'
            if history_count > 1:
                choice_options = "U/H/N/S"
            else:
                choice_options = "U/N/S"
            
            try:
                choice = input(f"\nYour choice [{choice_options}, default={default_choice}]: ").strip().upper()
                if not choice:
                    choice = default_choice
            except KeyboardInterrupt:
                print("\n✓ Using saved hints")
                return latest_hints
            
            # Handle choice
            if choice == 'U':
                # Use latest hints
                print(f"\n" + "="*60)
                print(f"✅ Using saved hints ({len(latest_hints)} characters)")
                print(f"="*60)
                return latest_hints
            
            elif choice == 'H' and history_count > 1:
                # View history and select
                print("\n" + "="*60)
                print("📚 Hints History:")
                print("="*60)
                for i, (timestamp, hints) in enumerate(hints_data['history'], 1):
                    print(f"\n[{i}] {timestamp}")
                    print("-" * 60)
                    for hint_line in hints.split('\n'):
                        print(f"  • {hint_line}")
                    print()
                
                print("="*60)
                version_choice = input(f"Select version (1-{len(hints_data['history'])}) or press Enter for latest: ").strip()
                
                if not version_choice:
                    print(f"\n✅ Using latest version ({len(latest_hints)} chars)")
                    return latest_hints
                
                try:
                    version_idx = int(version_choice) - 1
                    if 0 <= version_idx < len(hints_data['history']):
                        selected_hints = hints_data['history'][version_idx][1]
                        print(f"\n✅ Using version {version_choice} ({len(selected_hints)} chars)")
                        return selected_hints
                    else:
                        print(f"⚠️  Invalid version number. Using latest.")
                        return latest_hints
                except (ValueError, EOFError):
                    print(f"⚠️  Invalid input. Using latest.")
                    return latest_hints
            
            elif choice == 'N':
                # Add new version - multi-line input
                print(f"\n💬 Enter new hints (press Enter twice to finish, Ctrl+C to go back):")
                print("   " + "-" * 56)
                lines = []
                empty_count = 0
                
                try:
                    while True:
                        try:
                            line = input()
                        except EOFError:
                            break
                        
                        if not line:
                            empty_count += 1
                            if empty_count >= 2:
                                break
                        else:
                            empty_count = 0
                            lines.append(line)
                    
                    hints = "\n".join(lines).strip()
                    if hints:
                        print(f"\n✓ Hints received ({len(hints)} characters)")
                        if save_hints_to_txt(module, item_id, hints):
                            print(f"💾 Saved to Work/phase-1-dev/{module}/hints.txt")
                        return hints
                    else:
                        print(f"\n⚠️  No hints entered. Using saved hints.")
                        return latest_hints
                
                except KeyboardInterrupt:
                    print("\n✓ Cancelled input, returning to menu...")
                    continue  # Return to menu
            
            elif choice == 'S':
                # Skip - use AI auto-generation
                print(f"\n✓ Skipped hints (using AI auto-generation)")
                return None
            
            else:
                print(f"⚠️  Invalid choice. Using saved hints.")
                return latest_hints
        
        else:
            # No saved hints
            print(f"\n📝 Hints Examples for {item_id}:")
            print("  • 特殊的PASS/FAIL判断逻辑")
            print("  • 需要提取的特定字段")
            print("  • 输出格式要求")
            
            print(f"\n📝 Choose action:")
            print(f"   [N]ew  - Enter new hints (multi-line input)")
            print(f"   [S]kip - Skip hints (AI auto-generation)")
            
            try:
                choice = input(f"\nYour choice [N/S, default=S]: ").strip().upper()
                if not choice:
                    choice = 'S'
            except KeyboardInterrupt:
                print("\n✓ Skipped hints (using AI auto-generation)")
                return None
            
            if choice == 'N':
                # Add new hints - multi-line input
                print(f"\n💬 Enter your hints (press Enter twice to finish, Ctrl+C to cancel):")
                print("   " + "-" * 56)
                lines = []
                empty_count = 0
                
                try:
                    while True:
                        try:
                            line = input()
                        except EOFError:
                            break
                        
                        if not line:
                            empty_count += 1
                            if empty_count >= 2:
                                break
                        else:
                            empty_count = 0
                            lines.append(line)
                    
                    hints = "\n".join(lines).strip()
                    if hints:
                        print(f"\n✓ Hints received ({len(hints)} characters)")
                        if save_hints_to_txt(module, item_id, hints):
                            print(f"💾 Saved to Work/phase-1-dev/{module}/hints.txt")
                        return hints
                    else:
                        print(f"\n✓ No hints provided (using AI auto-generation)")
                        return None
                
                except KeyboardInterrupt:
                    print("\n✓ Cancelled input")
                    print(f"✓ Skipped hints (using AI auto-generation)")
                    return None
            
            else:  # 'S' or anything else
                print(f"\n✓ Skipped hints (using AI auto-generation)")
                return None
