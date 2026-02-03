"""
在线主链路: Generator → Gate → Repairer → Publish
==================================================
完整的 item_spec 生成、验证、修复、发布流程

使用方式:
    from agents.common.skills.evaluators.pipeline import ItemSpecPipeline
    
    pipeline = ItemSpecPipeline(llm_client=your_llm_client)
    result = await pipeline.run(task)
"""

import json
import asyncio
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime
from typing import Any, Optional, Callable

from .item_spec_gate import ItemSpecGate, GateResult, check_item_spec
from .item_spec_repairer import ItemSpecRepairer, RepairResult
from .item_spec_evaluator import ItemSpecEvaluator, EvalReport


@dataclass
class PipelineConfig:
    """Pipeline 配置"""
    max_repair_iterations: int = 2  # 最大修复迭代
    enable_repair: bool = True  # 是否启用修复
    enable_rollback: bool = True  # 是否启用回滚
    strict_gate: bool = False  # 严格门禁模式
    save_intermediate: bool = True  # 保存中间结果
    run_offline_eval: bool = False  # 是否运行离线评估


@dataclass
class PipelineResult:
    """Pipeline 执行结果"""
    success: bool
    stage: str  # "generate", "gate", "repair", "publish", "rollback"
    item_spec: dict = None
    gate_result: GateResult = None
    repair_result: RepairResult = None
    eval_report: EvalReport = None
    output_path: str = ""
    rollback_path: str = ""
    error_message: str = ""
    duration_ms: float = 0
    
    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "stage": self.stage,
            "gate_passed": self.gate_result.passed if self.gate_result else None,
            "repair_success": self.repair_result.success if self.repair_result else None,
            "output_path": self.output_path,
            "rollback_path": self.rollback_path,
            "error_message": self.error_message,
            "duration_ms": self.duration_ms,
        }


class ItemSpecPipeline:
    """
    item_spec 在线主链路
    
    流程:
    1. Generator: 调用外部生成器获取 item_spec
    2. Gate: 门禁检查（L0 结构 + L1 可执行）
    3. Repairer: 定向修复（仅在 Gate 失败时）
    4. Publish: 发布或回滚
    """
    
    def __init__(
        self,
        config: PipelineConfig = None,
        llm_client: Any = None,
        generator_func: Callable = None,
    ):
        """
        Args:
            config: Pipeline 配置
            llm_client: LLM 客户端（用于修复）
            generator_func: 自定义生成器函数（可选）
        """
        self.config = config or PipelineConfig()
        self.llm_client = llm_client
        self.generator_func = generator_func
        
        self.gate = ItemSpecGate(strict_mode=self.config.strict_gate)
        self.repairer = ItemSpecRepairer(
            llm_client=llm_client,
            max_iterations=self.config.max_repair_iterations
        )
        self.evaluator = ItemSpecEvaluator()
    
    async def run(
        self,
        item_spec: dict = None,
        generate_task: dict = None,
        output_dir: str | Path = None,
        previous_spec_path: str | Path = None,
        model_name: str = "unknown"
    ) -> PipelineResult:
        """
        运行完整 Pipeline
        
        Args:
            item_spec: 已生成的 item_spec（如果不提供则调用 generator）
            generate_task: 生成任务参数（用于调用 generator）
            output_dir: 输出目录
            previous_spec_path: 上一个成功的 spec 路径（用于回滚）
            model_name: 模型名称（用于评估报告）
            
        Returns:
            PipelineResult: 执行结果
        """
        import time
        start_time = time.perf_counter()
        
        output_dir = Path(output_dir) if output_dir else None
        
        # Stage 1: Generate（如果未提供 item_spec）
        if item_spec is None:
            if self.generator_func and generate_task:
                try:
                    item_spec = await self.generator_func(generate_task)
                except Exception as e:
                    return PipelineResult(
                        success=False,
                        stage="generate",
                        error_message=f"Generation failed: {e}",
                        duration_ms=(time.perf_counter() - start_time) * 1000
                    )
            else:
                return PipelineResult(
                    success=False,
                    stage="generate",
                    error_message="No item_spec provided and no generator configured",
                    duration_ms=(time.perf_counter() - start_time) * 1000
                )
        
        # 保存原始生成结果
        original_spec = item_spec.copy()
        
        # Stage 2: Gate
        gate_result = self.gate.check(item_spec)
        
        if self.config.save_intermediate and output_dir:
            self._save_intermediate(output_dir, "gate_result.json", gate_result.to_dict())
        
        # Stage 3: Repair（如果 Gate 失败且启用修复）
        repair_result = None
        if not gate_result.passed and self.config.enable_repair:
            repair_result = await self.repairer.repair(item_spec, gate_result.failures)
            item_spec = repair_result.item_spec
            gate_result = repair_result.final_gate_result
            
            if self.config.save_intermediate and output_dir:
                self._save_intermediate(output_dir, "repair_result.json", repair_result.to_dict())
        
        # Stage 4: Publish or Rollback
        if gate_result.passed:
            # 发布
            output_path = ""
            if output_dir:
                output_path = str(output_dir / "item_spec.json")
                self._save_spec(item_spec, output_path)
            
            # 可选：离线评估
            eval_report = None
            if self.config.run_offline_eval:
                eval_report = self.evaluator.evaluate(item_spec, model_name=model_name)
                if output_dir:
                    self._save_intermediate(output_dir, "eval_report.json", eval_report.to_dict())
                    self._save_intermediate(output_dir, "eval_report.md", eval_report.to_markdown())
            
            return PipelineResult(
                success=True,
                stage="publish",
                item_spec=item_spec,
                gate_result=gate_result,
                repair_result=repair_result,
                eval_report=eval_report,
                output_path=output_path,
                duration_ms=(time.perf_counter() - start_time) * 1000
            )
        else:
            # 回滚
            rollback_path = ""
            if self.config.enable_rollback and previous_spec_path:
                previous_path = Path(previous_spec_path)
                if previous_path.exists() and output_dir:
                    rollback_path = str(output_dir / "item_spec.json")
                    shutil.copy(previous_path, rollback_path)
            
            # 保存失败的 spec 供调试
            if output_dir:
                self._save_spec(item_spec, str(output_dir / "item_spec_failed.json"))
            
            return PipelineResult(
                success=False,
                stage="rollback" if rollback_path else "gate",
                item_spec=item_spec,
                gate_result=gate_result,
                repair_result=repair_result,
                rollback_path=rollback_path,
                error_message=f"Gate failed with {len(gate_result.failures)} failures",
                duration_ms=(time.perf_counter() - start_time) * 1000
            )
    
    def _save_spec(self, spec: dict, path: str):
        """保存 spec 到文件"""
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(spec, f, indent=2, ensure_ascii=False)
    
    def _save_intermediate(self, output_dir: Path, filename: str, content: Any):
        """保存中间结果"""
        debug_dir = output_dir / "pipeline_debug"
        debug_dir.mkdir(parents=True, exist_ok=True)
        
        filepath = debug_dir / filename
        if isinstance(content, str):
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
        else:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(content, f, indent=2, ensure_ascii=False)


# 快速运行脚本
async def run_pipeline_on_spec(
    spec_path: str | Path,
    output_dir: str | Path = None,
    enable_repair: bool = True,
    model_name: str = "unknown"
) -> PipelineResult:
    """
    便捷函数：对已有的 item_spec 运行 Pipeline
    
    Args:
        spec_path: item_spec.json 路径
        output_dir: 输出目录（默认同目录）
        enable_repair: 是否启用修复
        model_name: 模型名称
        
    Returns:
        PipelineResult
    """
    spec_path = Path(spec_path)
    output_dir = Path(output_dir) if output_dir else spec_path.parent
    
    with open(spec_path, 'r', encoding='utf-8') as f:
        item_spec = json.load(f)
    
    config = PipelineConfig(
        enable_repair=enable_repair,
        run_offline_eval=True,
    )
    
    pipeline = ItemSpecPipeline(config=config)
    return await pipeline.run(
        item_spec=item_spec,
        output_dir=output_dir,
        model_name=model_name
    )


if __name__ == "__main__":
    import sys
    
    async def main():
        if len(sys.argv) > 1:
            spec_path = sys.argv[1]
            model = sys.argv[2] if len(sys.argv) > 2 else "unknown"
            
            result = await run_pipeline_on_spec(spec_path, model_name=model)
            print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
        else:
            print("Usage: python pipeline.py <path_to_item_spec.json> [model_name]")
    
    asyncio.run(main())
