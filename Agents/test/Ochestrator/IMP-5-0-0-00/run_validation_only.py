"""
示例：只运行ValidationAgent（跳过ContextAgent和CodeGenAgent）

用法：
    python run_validation_only.py

适用场景：
    - 调试ValidationAgent
    - 修改ValidationAgent代码后重新验证
    - 已有checker.py，只想重新验证
"""

import asyncio
import sys
from pathlib import Path

# Setup paths（与run_full_pipeline.py一致）
_SCRIPT_DIR = Path(__file__).resolve().parent
_AGENT_DIR = _SCRIPT_DIR.parents[2]  # test/Ochestrator/IMP-5-0-0-00 -> Agent
if str(_AGENT_DIR) not in sys.path:
    sys.path.insert(0, str(_AGENT_DIR))

from agents.orchestrator.agent import OrchestratorAgent, PipelineConfig


async def main():
    # 输出目录（包含已有的checker.py和item_spec.json）
    output_dir = Path(__file__).parent
    
    # 配置：跳过Context和CodeGen，只运行Validation
    config = PipelineConfig(
        # v1.3: 断点重run配置
        skip_context_agent=True,        # ✓ 跳过ContextAgent，从item_spec.json加载
        skip_codegen_agent=True,        # ✓ 跳过CodeGenAgent，从checker.py加载
        skip_validation_agent=False,    # ✗ 运行ValidationAgent
        
        # 正常配置
        run_context_agent=False,        # 不需要运行（已跳过）
        run_codegen_agent=False,        # 不需要运行（已跳过）
        run_validation_agent=True,      # 需要运行
        
        # Validation配置
        validation_use_real_executor=True,  # 真实执行checker
        
        save_intermediate=True,
        output_dir=str(output_dir),
        debug_mode=True,
    )
    
    # 创建Orchestrator
    orchestrator = OrchestratorAgent(config=config)
    
    # 执行Pipeline
    print(f"[DEBUG] Output directory: {output_dir}")
    print(f"[DEBUG] Config:")
    print(f"  - skip_context_agent: {config.skip_context_agent}")
    print(f"  - skip_codegen_agent: {config.skip_codegen_agent}")
    print(f"  - skip_validation_agent: {config.skip_validation_agent}")
    print(f"  - validation_use_real_executor: {config.validation_use_real_executor}")
    print("\n" + "=" * 60)
    
    result = await orchestrator.process(
        input_data={
            "output_dir": str(output_dir),
        }
    )
    
    # 打印结果
    print("\n" + "=" * 60)
    print(f"[RESULT] Status: {result.status}")
    if result.errors:
        print(f"[RESULT] Errors: {result.errors}")
    if result.warnings:
        print(f"[RESULT] Warnings: {result.warnings}")
    
    # 检查输出文件
    checker_outputs = output_dir / "checker_outputs"
    if checker_outputs.exists():
        print(f"\n[OUTPUT] checker_outputs/ generated:")
        for subdir in ["logs", "reports", "cache"]:
            subdir_path = checker_outputs / subdir
            if subdir_path.exists():
                count = len(list(subdir_path.glob("*")))
                print(f"  - {subdir}/: {count} files")
    
    validation_result = output_dir / "validation_result.json"
    if validation_result.exists():
        print(f"[OUTPUT] validation_result.json: OK")
    
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
