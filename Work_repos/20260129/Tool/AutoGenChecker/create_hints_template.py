"""
为module创建hints模板（TXT格式）

使用方法：
1. 运行: python create_hints_template.py 16.0_IPTAG_CHECK IMP-16-0-0-01 IMP-16-0-0-02
2. 编辑生成的 Work/phase-1-dev/16.0_IPTAG_CHECK/hints.txt
3. 填写每个checker的hints
4. 运行生成命令，hints会自动使用

TXT格式说明：
=== IMP-16-0-0-01 ===
[2025-12-26 14:00:00]
hints内容（可多行）

[2025-12-26 16:00:00]
更新后的hints（系统自动读取最新版）
"""

import sys
from pathlib import Path
from datetime import datetime


def create_hints_template(module: str, item_ids: list = None):
    """
    为module创建hints模板（TXT格式）。
    
    Args:
        module: 模块名称（如：16.0_IPTAG_CHECK）
        item_ids: Checker ID列表（可选）
    """
    # 创建目录
    config_dir = Path(f"Work/phase-1-dev/{module}")
    config_dir.mkdir(parents=True, exist_ok=True)
    
    hints_file = config_dir / "hints.txt"
    
    # 如果已存在，不覆盖
    if hints_file.exists():
        print(f"⚠️  Hints文件已存在: {hints_file}")
        print(f"   如需重新创建，请先删除或重命名")
        return
    
    # 默认模板
    if not item_ids:
        item_ids = ["IMP-XX-X-X-01", "IMP-XX-X-X-02", "IMP-XX-X-X-03"]
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # 生成TXT内容
    lines = []
    for item_id in item_ids:
        lines.append(f"=== {item_id} ===")
        lines.append(f"[{timestamp}]")
        lines.append("请填写hints：检查目的、关键模式、边界情况等")
        lines.append("")
    
    content = "\n".join(lines)
    
    # 保存TXT文件
    with open(hints_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"\n✅ Hints模板已创建: {hints_file}")
    print(f"\n📝 文件格式:")
    print(f"   === IMP-XX-X-X-01 ===")
    print(f"   [时间戳]")
    print(f"   hints内容（可多行）")
    print(f"\n下一步:")
    print(f"1. 编辑 hints.txt，填写每个checker的hints")
    print(f"2. 运行生成命令:")
    print(f"   python cli.py generate --ai-agent --item-id <item_id> --module {module}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python create_hints_template.py <module> [item_id1] [item_id2] ...")
        print("示例: python create_hints_template.py 16.0_IPTAG_CHECK IMP-16-0-0-01 IMP-16-0-0-02")
        sys.exit(1)
    
    module = sys.argv[1]
    item_ids = sys.argv[2:] if len(sys.argv) > 2 else None
    
    create_hints_template(module, item_ids)
