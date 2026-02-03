#!/usr/bin/env python3
"""
自动部署JEDAI到Continue配置
"""
import os
import shutil
from pathlib import Path

def deploy_continue_config():
    """部署Continue配置"""
    print("=" * 70)
    print("JEDAI Continue配置部署工具")
    print("=" * 70)
    
    # 源配置文件
    source_config = Path("continue_config_jedai.yaml")
    
    # Continue配置目录
    continue_dir = Path.home() / ".continue"
    target_config = continue_dir / "config.yaml"
    
    if not source_config.exists():
        print(f"\n❌ 错误: 源配置文件不存在: {source_config}")
        return False
    
    if not continue_dir.exists():
        print(f"\n❌ 错误: Continue目录不存在: {continue_dir}")
        print("请先在VSCode中安装Continue扩展")
        return False
    
    # 备份现有配置
    if target_config.exists():
        backup_config = continue_dir / f"config.yaml.backup.{int(os.path.getmtime(target_config))}"
        print(f"\n📦 备份现有配置到: {backup_config}")
        shutil.copy2(target_config, backup_config)
    
    # 复制新配置
    print(f"\n📝 部署新配置到: {target_config}")
    shutil.copy2(source_config, target_config)
    
    print("\n✅ 配置部署成功！")
    print("\n" + "=" * 70)
    print("下一步操作：")
    print("=" * 70)
    print("1. 重启VSCode或重新加载Continue扩展")
    print("2. 打开Continue面板（Ctrl+Shift+P → Continue: Open）")
    print("3. 选择模型（推荐：gemini-2.5-pro 或 claude-sonnet-4）")
    print("4. 开始对话测试")
    print("\n⚠️  Token有效期：10小时")
    print("    过期后请运行：python get_jedai_token.py")
    print("=" * 70)
    
    return True

if __name__ == "__main__":
    deploy_continue_config()
